"""SPDR-001 operator reframe: Facet A (null base arm) + Facet B (HTF's own conditional effect
on a null base). Reuses screen_code primitives. TRAIN-only, per-stratum, magnitudes + CIs."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import polars as pl

EXP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXP / "screen_code")); sys.path.insert(0, str(EXP / "analysis_code"))
import spdr001_screen as S            # noqa: E402
from emit_rich import _fast_block_ci_mean  # noqa: E402
RES = EXP / "results"


def blkidx(n, block=5, n_boot=1500, seed=0):
    eff = max(1, min(block, n - 1)); nb = int(np.ceil(n / eff))
    st = np.random.default_rng(seed).integers(0, n, size=(n_boot, nb))
    return (st[:, :, None] + np.arange(eff)[None, None, :]).reshape(n_boot, -1)[:, :n] % n


def run():
    fa, fb = [], []
    for sym in S.INSTRUMENTS:
        train = S.load_train_1m(sym)
        for name, htf_min, ltf_min, ratio in S.DOMAIN_PAIRS:
            ctx = S.build_domain_ctx(name, htf_min, ltf_min, train)
            n = ctx.n; idx = np.arange(n)
            for hmult in S.HOLD_MULTS:
                hold = ratio * hmult
                inb = idx + hold < n; ii = idx[inb]
                move = np.full(n, np.nan)
                move[ii] = (ctx.ltf_open[ii + hold] - ctx.ltf_open[ii]) / ctx.ltf_atr_prev[ii]
                raw = np.full(n, np.nan)
                raw[ii] = (ctx.ltf_open[ii + hold] - ctx.ltf_open[ii]) / ctx.ltf_open[ii] * 1e4
                base = ctx.valid & inb & np.isfinite(move)
                sel = np.nonzero(base)[0]
                if sel.size < 200:
                    continue
                m = move[sel]; rb = raw[sel]; hd = ctx.htf_dir[sel].astype(float)

                # ---- FACET A: null (random) base arm distribution, seed battery ----
                battery = []
                for k in range(S.N_SEEDS):
                    s = S.draw_sign(n, k)[sel]
                    nz = s != 0
                    if nz.sum() > 0:
                        battery.append(float((s[nz] * m[nz]).mean()))
                battery = np.array(battery)
                # per-trade signed pool over the seed battery (for shape of the null object)
                pool = np.concatenate([S.draw_sign(n, k)[sel][S.draw_sign(n, k)[sel] != 0] *
                                       m[S.draw_sign(n, k)[sel] != 0] for k in range(5)])
                zsk = (pool - pool.mean()) / (pool.std() + 1e-30)
                # availability-vs-random percentile: rank of the base mean within its own seed
                # battery recentred — for a random arm this is ~0.5 by construction (the null anchor)
                avail_pct = float((battery < battery.mean()).mean())
                # random-side hit-rate on the signed pool (directional edge of the null) ~0.5
                base_dir_hit = float((pool > 0).mean())
                fa.append(dict(instrument=sym, domain=name, hold_bars=hold, n=int(sel.size),
                    base_signed_mean=float(battery.mean()),
                    base_seed_lo=float(np.percentile(battery, 2.5)),
                    base_seed_hi=float(np.percentile(battery, 97.5)),
                    base_signed_median=float(np.median(pool)),
                    base_signed_mean_bps=float(battery.mean() * rb.std() / (m.std() + 1e-30)),
                    base_disp_std=float(m.std()), base_disp_std_bps=float(rb.std()),
                    base_skew=float((zsk**3).mean()),
                    base_tail_gt2atr=float((np.abs(pool) > 2).mean()),
                    base_dir_hit_rate=base_dir_hit,          # ~0.5: no directional edge (null)
                    base_fwd_up_rate=float((m > 0).mean()),  # unconditional up-rate of the fwd move
                    base_avail_percentile=avail_pct))        # ~0.5: base IS the random reference

                # ---- FACET B: HTF's own conditional effect on the null base ----
                pos = hd > 0; neg = hd < 0
                if pos.sum() < 50 or neg.sum() < 50:
                    continue
                mp, mn = m[pos], m[neg]
                gap = float(mp.mean() - mn.mean())                 # between-HTF-dir conditional-mean shift
                bi = blkidx(sel.size)
                gaps = np.array([m[bi[b]][hd[bi[b]] > 0].mean() - m[bi[b]][hd[bi[b]] < 0].mean()
                                 for b in range(bi.shape[0])])
                gaps = gaps[np.isfinite(gaps)]
                # HTF sign-prediction magnitude: P(sign(m)==htf_dir) - 0.5
                hit = float((np.sign(m) == hd).mean())
                _, h_lo, h_hi = _fast_block_ci_mean((np.sign(m) == hd).astype(float))
                # dispersion modulation across ATR regime, guarded (raw bps): high vs low
                reg = ctx.atr_reg[sel]
                def _std(msk, a):
                    return float(a[msk].std()) if msk.sum() > 50 else np.nan
                sr_lo14 = _std(reg == 0, m); sr_hi14 = _std(reg == 2, m)
                sr_lo_bps = _std(reg == 0, rb); sr_hi_bps = _std(reg == 2, rb)
                fb.append(dict(instrument=sym, domain=name, hold_bars=hold, n=int(sel.size),
                    dir_mean_pos=float(mp.mean()), dir_mean_neg=float(mn.mean()),
                    dir_gap=gap, dir_gap_lo=float(np.percentile(gaps, 2.5)),
                    dir_gap_hi=float(np.percentile(gaps, 97.5)),
                    sign_hit=hit, sign_hit_lo=h_lo, sign_hit_hi=h_hi,
                    sign_excess=hit - 0.5,
                    disp_hi_over_lo_atr14=(sr_hi14 / sr_lo14) if sr_lo14 else np.nan,
                    disp_hi_over_lo_rawbps=(sr_hi_bps / sr_lo_bps) if sr_lo_bps else np.nan))
            print("  facet", sym, name, flush=True)
    pl.DataFrame(fa).write_parquet(RES / "facet_a_null_base.parquet")
    pl.DataFrame(fb).write_parquet(RES / "facet_b_htf_conditional.parquet")
    print("[emit_facets] wrote facet_a_null_base / facet_b_htf_conditional")


if __name__ == "__main__":
    run()
