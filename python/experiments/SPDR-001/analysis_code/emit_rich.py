"""SPDR-001 data-analyst rich re-emission (neutral quantification of HTF->LTF effect).

Reuses the VETTED causal primitives from screen_code (build_domain_ctx / map_htf_to_ltf /
wilder_adx_di / regime_labels / wilder_atr / _agg) — no causality is rebuilt. It records the
FULLER per-trade / per-regime distribution the mean-only aggregate `results/cells.parquet`
discards, to MEASURE the magnitude and shape of the HTF-context effect (not adjudicate worth).

Key reframe on the estimand:
  The DI arm's model return per selected bar is  htf_dir_i * m_i  with  m_i = move_norm.
  The random symmetric sign only THINS the sample (agrees ~half the time) — an unbiased random
  subset. So the full-sample seed-free estimand  E[htf_dir*m | regime]  IS what the DI battery
  estimates, at higher power and with no L-19 seed noise. We report the full-sample population
  estimand as primary; the seed battery only governs the greedy exposure / trade-count axis.

Drift vs timing split (the operator's core ask):
  edge  = mean(htf_dir * m)                     over regime-valid bars
  d     = mean(m)                               unconditional fwd drift (normalised)
  tau   = mean(htf_dir)                          net directional tilt (long-short frac)
  drift = tau * d                                what a direction-matched coin-flip earns
  timing= edge - tau*d = Cov(htf_dir, m)         genuine HTF alignment value
  The phase-shift null (Control B) preserves htf_dir's marginal but breaks its alignment ->
  its edge should ~ drift (empirical check of the analytic split).

All CIs from xen.evaluation.block_bootstrap_ci (block bootstrap over the time-ordered per-bar
series). No local P&L accounting (L-18). TRAIN-only by construction (primitives fence it).
"""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np
import polars as pl

EXP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXP / "screen_code"))
import spdr001_screen as S  # noqa: E402
from xen.evaluation import block_bootstrap_ci  # noqa: E402
from xen.vol_regime import wilder_atr  # noqa: E402

RES = EXP / "results"
BLOCK = 5
NBOOT = 1500  # lighter than default 10k for the big grid; stable for CI reads on these n


def moments(x: np.ndarray) -> dict:
    x = x[np.isfinite(x)]
    n = x.size
    if n < 2:
        return dict(n=n, mean=np.nan, std=np.nan, skew=np.nan, kurt=np.nan, mabs=np.nan,
                    p05=np.nan, p25=np.nan, p50=np.nan, p75=np.nan, p95=np.nan, hit=np.nan)
    mu = x.mean(); sd = x.std(ddof=1)
    z = (x - mu) / (sd + 1e-30)
    return dict(n=int(n), mean=float(mu), std=float(sd),
                skew=float((z**3).mean()), kurt=float((z**4).mean() - 3.0),
                mabs=float(np.abs(x).mean()),
                p05=float(np.percentile(x, 5)), p25=float(np.percentile(x, 25)),
                p50=float(np.percentile(x, 50)), p75=float(np.percentile(x, 75)),
                p95=float(np.percentile(x, 95)), hit=float((x > 0).mean()))


def _fast_block_ci_mean(x: np.ndarray, block: int = BLOCK, n_boot: int = NBOOT,
                        alpha: float = 0.05, seed: int = 0) -> tuple[float, float, float]:
    """Vectorized circular-block bootstrap CI of the MEAN — identical semantics to
    xen.evaluation.block_bootstrap_ci (block capped to [1,n-1], full circular start range),
    but done in numpy for speed on the 15k-row per-bar series. Validated against the canonical
    fn on a sample cell (see analysis.md integrity note)."""
    n = x.size
    eff = max(1, min(int(block), n - 1))
    nblk = int(np.ceil(n / eff))
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n, size=(n_boot, nblk))
    idx = (starts[:, :, None] + np.arange(eff)[None, None, :]).reshape(n_boot, -1)[:, :n] % n
    stats = x[idx].mean(axis=1)
    return float(x.mean()), float(np.quantile(stats, alpha / 2)), float(np.quantile(stats, 1 - alpha / 2))


def bb(x: np.ndarray) -> dict:
    x = x[np.isfinite(x)]
    if x.size < 2:
        return dict(stat=np.nan, ci_lo=np.nan, ci_hi=np.nan, ci_lo_srng=np.nan)
    st, lo, hi = _fast_block_ci_mean(x)
    return dict(stat=st, ci_lo=lo, ci_hi=hi, ci_lo_srng=np.nan)


def htf_continuous(train_1m, htf_min, ltf_min):
    """Continuous per-LTF-bar HTF conditioners via the SAME causal map as build_domain_ctx:
    adx value and ATR trailing-percentile of the last-closed HTF bar."""
    htf = S._agg(train_1m, htf_min).sort("CloseTime")
    ltf = S._agg(train_1m, ltf_min).sort("CloseTime")
    hh = htf["High"].to_numpy().astype(float); hl = htf["Low"].to_numpy().astype(float)
    hc = htf["Close"].to_numpy().astype(float)
    adx, pdi, mdi = S.wilder_adx_di(hh, hl, hc, S.ADX_PERIOD)
    # continuous trailing ATR percentile (same window/def as regime_labels)
    from numpy.lib.stride_tricks import sliding_window_view
    atr = wilder_atr(hh, hl, hc, S.ATR_PERIOD)
    win = 50
    pct = np.full(atr.shape[0], np.nan)
    if atr.shape[0] >= win:
        sw = sliding_window_view(atr, win)
        cur = atr[win - 1:]
        fin = np.all(np.isfinite(sw), axis=1) & np.isfinite(cur)
        less = np.where(np.isfinite(sw), sw < cur[:, None], False).sum(axis=1) / win
        p = np.full(cur.shape[0], np.nan); p[fin] = less[fin]
        pct[win - 1:] = p
    hct = htf["CloseTime"].to_numpy().astype("datetime64[ns]").astype("int64")
    lot = ltf["OpenTime"].to_numpy().astype("datetime64[ns]").astype("int64")
    m = S.map_htf_to_ltf(lot, hct)
    ok = m >= 0; mm = np.where(ok, m, 0)
    adx_l = np.where(ok, adx[mm], np.nan)
    pct_l = np.where(ok, pct[mm], np.nan)
    return adx_l, pct_l


def run():
    dist_rows, edge_rows, dose_rows, expo_rows = [], [], [], []
    for sym in S.INSTRUMENTS:
        train = S.load_train_1m(sym)
        for name, htf_min, ltf_min, ratio in S.DOMAIN_PAIRS:
            ctx = S.build_domain_ctx(name, htf_min, ltf_min, train, shift_htf=0)
            ctx_sh = S.build_domain_ctx(name, htf_min, ltf_min, train,
                                        shift_htf=S.PHASE_SHIFT_HTF_BARS)
            adx_c, atr_pct_c = htf_continuous(train, htf_min, ltf_min)
            n = ctx.n
            idx = np.arange(n)
            holds = [ratio * m for m in S.HOLD_MULTS]
            open_ = ctx.ltf_open; atrp = ctx.ltf_atr_prev
            for hmult, hold in zip(S.HOLD_MULTS, holds):
                inb = idx + hold < n
                ii = idx[inb]
                move = np.full(n, np.nan)
                move[ii] = (open_[ii + hold] - open_[ii]) / atrp[ii]
                base_valid = ctx.valid & inb & np.isfinite(move)
                # ---- iterate the 20 variants: build the regime mask, seed-free ----
                for spec in S.variant_specs():
                    mask = spec["mask"](ctx) & base_valid
                    sel = np.nonzero(mask)[0]
                    if sel.size == 0:
                        continue
                    m = move[sel]
                    d = float(m.mean())
                    hd = ctx.htf_dir[sel].astype(float)
                    signed = hd * m if spec["dir"] else None
                    # ---- distribution (unsigned fwd-move) : the SHAPE axis ----
                    dm = moments(m)
                    dist_rows.append(dict(instrument=sym, domain=name, hold_mult=hmult,
                                          hold_bars=hold, variant=spec["name"],
                                          is_signal=spec["sig"], drift_d=d, **dm))
                    # ---- exposure (greedy non-overlap, seed battery on the thinning) ----
                    occ = []
                    ntr = []
                    for k in range(S.N_SEEDS):
                        s = S.draw_sign(n, k)
                        elig = mask & (s != 0)
                        if spec["dir"]:
                            elig &= (s == ctx.htf_dir)
                        ei = np.nonzero(elig)[0]
                        if ei.size == 0:
                            continue
                        ent = S.greedy_entries(ei, hold)
                        ntr.append(ent.size)
                        occ.append(ent.size * hold / float(n))
                    expo_rows.append(dict(instrument=sym, domain=name, hold_mult=hmult,
                                          hold_bars=hold, variant=spec["name"],
                                          is_signal=spec["sig"],
                                          n_elig_bars=int(sel.size),
                                          n_trades_med=float(np.median(ntr)) if ntr else np.nan,
                                          occupancy=float(np.median(occ)) if occ else np.nan))
                    # ---- signed edge + drift/timing split (DI variants only) ----
                    if spec["dir"]:
                        tau = float(hd.mean())
                        drift = tau * d
                        edge_bb = bb(signed)
                        # timing per-bar surrogate: (hd-tau)*(m-d), mean == Cov == timing
                        timing_series = (hd - tau) * (m - d)
                        tim_bb = bb(timing_series)
                        # phase-shift empirical drift null
                        hd_sh = ctx_sh.htf_dir[sel].astype(float)
                        ps = float((hd_sh * m).mean())
                        edge_rows.append(dict(instrument=sym, domain=name, hold_mult=hmult,
                            hold_bars=hold, variant=spec["name"], twin=spec["twin"],
                            n=int(sel.size), edge=edge_bb["stat"], edge_lo=edge_bb["ci_lo"],
                            edge_hi=edge_bb["ci_hi"], edge_lo_srng=edge_bb["ci_lo_srng"],
                            drift_d=d, tau=tau, drift_comp=drift,
                            timing=tim_bb["stat"], timing_lo=tim_bb["ci_lo"],
                            timing_hi=tim_bb["ci_hi"],
                            timing_frac=(tim_bb["stat"] / edge_bb["stat"])
                                if edge_bb["stat"] not in (0, None) and np.isfinite(edge_bb["stat"])
                                and abs(edge_bb["stat"]) > 1e-12 else np.nan,
                            phaseshift_edge=ps,
                            phaseshift_frac=(ps / edge_bb["stat"])
                                if edge_bb["stat"] and abs(edge_bb["stat"]) > 1e-12 else np.nan))
                # ---- dose-response: bin by continuous ADX / ATR-pct (DI edge + dispersion) ----
                av = adx_c[base_valid]; pv = atr_pct_c[base_valid]
                mv = move[base_valid]; hv = ctx.htf_dir[base_valid].astype(float)
                for tag, cond in (("adx", av), ("atrpct", pv)):
                    cc = cond.copy()
                    good = np.isfinite(cc) & np.isfinite(mv)
                    if good.sum() < 200:
                        continue
                    cg = cc[good]; mg = mv[good]; hg = hv[good]
                    # decile bins on the conditioner
                    qs = np.quantile(cg, np.linspace(0, 1, 11))
                    qs[-1] += 1e-9
                    binid = np.clip(np.searchsorted(qs, cg, side="right") - 1, 0, 9)
                    for b in range(10):
                        bm = binid == b
                        if bm.sum() < 30:
                            continue
                        mb = mg[bm]; hb = hg[bm]
                        dose_rows.append(dict(instrument=sym, domain=name, hold_mult=hmult,
                            hold_bars=hold, conditioner=tag, decile=b,
                            cond_lo=float(qs[b]), cond_hi=float(qs[b + 1]), n=int(bm.sum()),
                            move_mean=float(mb.mean()), move_std=float(mb.std(ddof=1)),
                            move_mabs=float(np.abs(mb).mean()),
                            di_edge=float((hb * mb).mean()), tau=float(hb.mean())))
            print(f"  done {sym} {name}", flush=True)
    RES.mkdir(exist_ok=True)
    pl.DataFrame(dist_rows).write_parquet(RES / "rich_dist.parquet")
    pl.DataFrame(edge_rows).write_parquet(RES / "rich_edge.parquet")
    pl.DataFrame(dose_rows).write_parquet(RES / "rich_dose.parquet")
    pl.DataFrame(expo_rows).write_parquet(RES / "rich_expo.parquet")
    print("[emit_rich] wrote rich_dist/edge/dose/expo.parquet")


if __name__ == "__main__":
    run()
