"""SPDR-002 fresh-context re-derivation (data-analyst, stage 5).

Re-derives per-TRADE forward-return series for every cell from the causal primitives
(SPDR-001 build_domain_ctx / momentum_signal, reused as METHODOLOGY only, blind of SPDR-001
findings), then computes the rich facets the coarse screen aggregate cannot:
  - proper 5-seed block-bootstrap CIs (mean + dispersion) with block sensitivity
  - two-sample lift CI (filtered - unfiltered baseline) by block bootstrap of both arms
  - three dispersion reads (ATR[t-1]-norm, raw-bps, fixed-long-window-ATR) — normaliser guard
  - dose-response: Spearman rank of return & |return| vs continuous ADX and ATR-percentile
  - horizon (hold) curves; per-stratum heterogeneity; tails/skew; occupancy
  - Control B random-timing 25-seed percentile; Control C phase-shift collapse fraction
All emissions -> results/ ; nothing here imports SPDR-001 numbers.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import polars as pl

EXP = Path(__file__).resolve().parents[1]
RES = EXP / "results"
sys.path.insert(0, str(EXP.parent / "SPDR-001" / "screen_code"))
sys.path.insert(0, str(EXP / "screen_code"))
import spdr001_screen as S1
import spdr002_screen as S2
from xen.evaluation import block_bootstrap_ci, block_sensitivity, trimmed_mean, mde
from xen.zigzag import wilder_atr

INSTR = S1.INSTRUMENTS
DOMAINS = S1.DOMAIN_PAIRS
HOLD_MULTS = S1.HOLD_MULTS
N_SEEDS = S1.N_SEEDS
PHASE = S1.PHASE_SHIFT_HTF_BARS
RNG_MEAN = np.mean


# ---- continuous HTF conditioners mapped to LTF (mirror build_domain_ctx mapping) --------- #
def continuous_htf(name, htf_min, ltf_min, train, ctx):
    """Return (adx_cont, atr_pct_cont) per LTF bar, last-closed HTF bar, causal."""
    htf = S1._agg(train, htf_min).sort("CloseTime")
    hh, hl, hc = (htf[c].to_numpy().astype(float) for c in ("High", "Low", "Close"))
    adx, pdi, mdi = S1.wilder_adx_di(hh, hl, hc, S1.ADX_PERIOD)
    atr = wilder_atr(hh, hl, hc, S1.ATR_PERIOD)
    # trailing percentile of ATR over window 50 (causal, matches vol_regime convention)
    w = 50
    apct = np.full(len(atr), np.nan)
    for i in range(len(atr)):
        if i >= w and np.isfinite(atr[i]):
            win = atr[i - w:i]
            win = win[np.isfinite(win)]
            if win.size:
                apct[i] = (win < atr[i]).mean()
    hct = htf["CloseTime"].to_numpy().astype("datetime64[ns]").astype("int64")
    lot = ctx._ltf_open_time
    m = S1.map_htf_to_ltf(lot, hct)
    ok = m >= 0
    mm = np.where(ok, m, 0)
    adx_l = np.where(ok, adx[mm], np.nan)
    apct_l = np.where(ok, apct[mm], np.nan)
    return adx_l, apct_l


def fixed_long_atr(ctx):
    """Fixed long-window (100) ATR on LTF, lagged t-1 — normaliser-artifact guard."""
    atr = wilder_atr(ctx._ltf_high, ctx._ltf_low, ctx._ltf_close, 100)
    return np.concatenate([[np.nan], atr[:-1]])


def spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    good = np.isfinite(x) & np.isfinite(y)
    x, y = x[good], y[good]
    if x.size < 10:
        return np.nan, 0
    rx = np.argsort(np.argsort(x)); ry = np.argsort(np.argsort(y))
    return float(np.corrcoef(rx, ry)[0, 1]), int(x.size)


def spearman_ci(x, y, nb=800, seed=0):
    rho, n = spearman(x, y)
    if not np.isfinite(rho):
        return rho, [np.nan, np.nan], n
    rng = np.random.default_rng(seed)
    xs = np.asarray(x, float); ys = np.asarray(y, float)
    good = np.isfinite(xs) & np.isfinite(ys); xs, ys = xs[good], ys[good]
    rs = np.empty(nb)
    for b in range(nb):
        idx = rng.integers(0, xs.size, xs.size)
        r, _ = spearman(xs[idx], ys[idx]); rs[b] = r
    return rho, [float(np.nanpercentile(rs, 2.5)), float(np.nanpercentile(rs, 97.5))], n


def two_sample_lift_ci(rf, rb, block=5, nb=2000, seed=0):
    """Difference of means (filtered - baseline) via independent circular block bootstrap."""
    def boot(x):
        n = len(x); eb = max(1, min(block, n - 1)); nbk = int(np.ceil(n / eb))
        rng = np.random.default_rng(seed + 7)
        out = np.empty(nb)
        for b in range(nb):
            starts = rng.integers(0, n, nbk)
            idx = (starts[:, None] + np.arange(eb)).ravel() % n
            out[b] = x[idx][:n].mean()
        return out
    if len(rf) < 2 or len(rb) < 2:
        return np.nan, [np.nan, np.nan]
    d = boot(rf) - boot(rb)
    return float(rf.mean() - rb.mean()), [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]


def arm_returns(ctx, sig, spec, hold, flatr, adx_l, apct_l):
    """Per-trade returns for one arm + aligned conditioners. Three normalisations."""
    n = ctx.n
    regime = spec["mask"](ctx)
    elig = ctx.valid & regime & (sig != 0) & (np.arange(n) + hold < n)
    if spec["dir"]:
        elig &= (sig == ctx.htf_dir)
    idx = np.nonzero(elig)[0]
    if idx.size == 0:
        return None
    ent = S1.greedy_entries(idx, hold)
    s = sig[ent]
    move = ctx.ltf_open[ent + hold] - ctx.ltf_open[ent]
    r_atr = s * move / ctx.ltf_atr_prev[ent]
    r_bps = s * move / ctx.ltf_open[ent] * 1e4
    fl = flatr[ent]
    r_flatr = np.where(np.isfinite(fl) & (fl > 0), s * move / fl, np.nan)
    return {"ent": ent, "r_atr": r_atr, "r_bps": r_bps, "r_flatr": r_flatr,
            "adx": adx_l[ent], "apct": apct_l[ent]}


def bb(x, block=5):
    r = block_bootstrap_ci(np.asarray(x, float), np.mean, block=block, n_boot=3000, n_seeds=5)
    return r


def run():
    specs = S2.variant_specs() if hasattr(S2, "variant_specs") else S1.variant_specs()
    rows, dose, horizon, pertrade_sample = [], [], [], []
    for sym in INSTR:
        train = S1.load_train_1m(sym)
        for name, htf_min, ltf_min, ratio in DOMAINS:
            ctx = S1.build_domain_ctx(name, htf_min, ltf_min, train, shift_htf=0)
            ctx_sh = S1.build_domain_ctx(name, htf_min, ltf_min, train, shift_htf=PHASE)
            sig = S2.momentum_signal(ctx)
            flatr = fixed_long_atr(ctx)
            adx_l, apct_l = continuous_htf(name, htf_min, ltf_min, train, ctx)
            print(f"  {sym} {name} ...", flush=True)
            holds = [ratio * m for m in HOLD_MULTS]
            for m, hold in zip(HOLD_MULTS, holds):
                base = arm_returns(ctx, sig, specs[0], hold, flatr, adx_l, apct_l)
                for spec in specs:
                    a = arm_returns(ctx, sig, spec, hold, flatr, adx_l, apct_l)
                    if a is None:
                        rows.append({"instrument": sym, "domain": name, "hold_mult": m,
                                     "hold_bars": hold, "variant": spec["name"], "n": 0})
                        continue
                    r = a["r_atr"]
                    b5 = bb(r, 5)
                    bs = block_sensitivity(r, [max(1, 5 // 2), 5, 10], n_boot=1200, n_seeds=3)
                    row = {"instrument": sym, "domain": name, "hold_mult": m, "hold_bars": hold,
                           "variant": spec["name"], "uses_htf": spec["name"] != "none",
                           "di": spec["dir"], "n": int(r.size),
                           "mean_atr": float(r.mean()), "std_atr": float(r.std()),
                           "hitrate": float((r > 0).mean()),
                           "skew": float(_skew(r)), "trimmed": trimmed_mean(r),
                           "median": float(np.median(r)),
                           "q05": float(np.percentile(r, 5)), "q95": float(np.percentile(r, 95)),
                           "q01": float(np.percentile(r, 1)), "q99": float(np.percentile(r, 99)),
                           "ci_lo": b5["ci"][0], "ci_hi": b5["ci"][1],
                           "ci_lo_seedrange": b5["ci_low_seed_range"],
                           "mde": mde(r), "std_bps": float(np.nanstd(a["r_bps"])),
                           "mean_bps": float(np.nanmean(a["r_bps"])),
                           "std_flatr": float(np.nanstd(a["r_flatr"])),
                           "mean_flatr": float(np.nanmean(a["r_flatr"])),
                           "block_frag": bool(np.sign(bs[0]["ci"][0]) != np.sign(bs[2]["ci"][0])),
                           "baseline_admit_frac": r.size / base["r_atr"].size if base else np.nan}
                    # dispersion CI (std) via bootstrap
                    ds = block_bootstrap_ci(r, np.std, block=5, n_boot=1200, n_seeds=3)
                    row["std_ci_lo"], row["std_ci_hi"] = ds["ci"][0], ds["ci"][1]
                    if spec["name"] != "none":
                        lift, lci = two_sample_lift_ci(r, base["r_atr"])
                        row["lift"] = lift; row["lift_ci_lo"], row["lift_ci_hi"] = lci
                        # dispersion lift
                        row["disp_lift"] = float(r.std() - base["r_atr"].std())
                        # Control B: 25-seed random-timing battery, momentum percentile
                        tw = random_twin(ctx, spec["mask"](ctx), r.size, hold, flatr)
                        row["twin_mean"] = tw["mean"]; row["twin_p975"] = tw["p975"]
                        row["twin_p025"] = tw["p025"]
                        row["mom_pctile_in_twin"] = float((tw["seeds"] < r.mean()).mean())
                        if spec["dir"]:
                            ash = arm_returns(ctx_sh, sig, spec, hold, flatr, adx_l, apct_l)
                            if ash is not None:
                                lift_sh, _ = two_sample_lift_ci(ash["r_atr"], base["r_atr"])
                                row["phase_lift"] = lift_sh
                                row["collapse_frac"] = (lift_sh / lift) if lift not in (0, None) and np.isfinite(lift) and lift != 0 else np.nan
                    rows.append(row)
                    # dose-response on the unfiltered baseline only (continuous, hold-level)
                    if spec["name"] == "none":
                        for cond, cn in [(a["adx"], "adx"), (a["apct"], "atr_pct")]:
                            rho_m, ci_m, nn = spearman_ci(cond, r)
                            rho_d, ci_d, _ = spearman_ci(cond, np.abs(r))
                            dose.append({"instrument": sym, "domain": name, "hold_mult": m,
                                         "cond": cn, "rho_mean": rho_m, "rho_mean_ci": ci_m,
                                         "rho_absdisp": rho_d, "rho_absdisp_ci": ci_d, "n": nn})
                        # horizon curve point
                        horizon.append({"instrument": sym, "domain": name, "hold_mult": m,
                                        "hold_bars": hold, "mean_atr": float(r.mean()),
                                        "std_atr": float(r.std()), "hitrate": float((r > 0).mean()),
                                        "ci_lo": b5["ci"][0], "ci_hi": b5["ci"][1], "n": int(r.size)})
            del ctx, ctx_sh
    pl.DataFrame(rows, strict=False).write_parquet(RES / "rederived_cells.parquet")
    pl.DataFrame(dose, strict=False).write_parquet(RES / "dose_response.parquet")
    pl.DataFrame(horizon, strict=False).write_parquet(RES / "horizon.parquet")
    print("wrote", len(rows), "cells,", len(dose), "dose,", len(horizon), "horizon")


def _skew(x):
    x = np.asarray(x, float); m = x.mean(); s = x.std()
    return np.mean(((x - m) / s) ** 3) if s > 0 else np.nan


def random_twin(ctx, regime_mask, n_target, hold, flatr):
    n = ctx.n
    pool = np.nonzero(ctx.valid & regime_mask & (np.arange(n) + hold < n))[0]
    if pool.size == 0 or n_target == 0:
        return {"mean": np.nan, "p975": np.nan, "p025": np.nan, "seeds": np.array([np.nan])}
    means = np.empty(N_SEEDS)
    for k in range(N_SEEDS):
        rng = np.random.default_rng(10_000 + k)
        take = min(n_target, pool.size)
        ent = np.sort(rng.choice(pool, size=take, replace=False))
        sign = rng.choice(np.array([-1, 1], np.int8), size=take)
        move = ctx.ltf_open[ent + hold] - ctx.ltf_open[ent]
        means[k] = float(np.mean(sign * move / ctx.ltf_atr_prev[ent]))
    return {"mean": float(means.mean()), "p975": float(np.percentile(means, 97.5)),
            "p025": float(np.percentile(means, 2.5)), "seeds": means}


if __name__ == "__main__":
    run()
