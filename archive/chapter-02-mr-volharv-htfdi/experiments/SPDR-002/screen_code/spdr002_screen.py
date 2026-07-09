"""SPDR-002 — HTF-context screen on CTRL-02 naive-momentum LTF entries (TRAIN-only availability).

Lane: SPDR speed-run (docs/references/spdr-lane.md). Leg 2/3. TRAIN-only, disposition-only
(deferred to post-SPDR-003 series verdict). Design: python/experiments/SPDR-002/design.md.
Analysed BLIND of SPDR-001 results — this module only replicates SPDR-001's causal methodology.

Signal (deterministic, replaces CTRL-01's random draw): at entry bar t, using the last CLOSED
LTF bar t-1, LONG if Close[t-1] > max(High[t-2..t-4]); SHORT if Close[t-1] < min(Low[t-2..t-4]).
Act at Open(t); open-to-open ATR-normalised forward return over hold H. HTF context = last HTF bar
with CloseTime < Open(t) (reused anti-lookahead map). Every filter variant is a real test (the
signal is informative); `none` = unfiltered-momentum baseline; DI = HTF-direction confirmation
(keep trade only if sig == htf_dir); gating = regime subset. Controls: A unfiltered baseline (lift),
B matched-random-timing seed battery, C HTF phase-shift future-destroy.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import polars as pl
from tqdm import tqdm

EXP_DIR = Path(__file__).resolve().parents[1]
RESULTS = EXP_DIR / "results"
SPDR001_CODE = EXP_DIR.parent / "SPDR-001" / "screen_code"
sys.path.insert(0, str(SPDR001_CODE))
# Reuse SPDR-001 causal primitives VERBATIM (single source of causal truth).
import spdr001_screen as S1                                                   # noqa: E402
from xen.evaluation import block_bootstrap_ci, trimmed_mean                  # noqa: E402

INSTRUMENTS = S1.INSTRUMENTS
DOMAIN_PAIRS = S1.DOMAIN_PAIRS
HOLD_MULTS = S1.HOLD_MULTS
N_SEEDS = S1.N_SEEDS                        # random-timing twin battery (L-19)
PHASE_SHIFT_HTF_BARS = S1.PHASE_SHIFT_HTF_BARS
FWER_Q = S1.FWER_Q
BREAKOUT_LOOKBACK = 3                        # "last 3 bars" (prior, exclusive of the breakout bar)
# Stage-3 screen CI is COARSE (aggregate emission only); the L-20 full seed battery / block
# sensitivity is the fresh-context stage-5 analyst's job.
N_BOOT_SCREEN = 2000
N_SEEDS_CI = 2


# --------------------------------------------------------------------------- #
# Momentum signal (causal: uses only bars <= t-1)
# --------------------------------------------------------------------------- #
def momentum_signal(ctx) -> np.ndarray:
    """Per LTF bar t: +1 if Close[t-1] > max(High[t-2..t-1-L]); -1 if Close[t-1] < min(Low[...]);
    else 0. Uses only closed bars <= t-1 -> action at Open(t) is causal."""
    from numpy.lib.stride_tricks import sliding_window_view
    n = ctx.n
    hi, lo, cl = ctx._ltf_high, ctx._ltf_low, ctx._ltf_close
    sig = np.zeros(n, dtype=np.int8)
    L = BREAKOUT_LOOKBACK
    if n < L + 2:
        return sig
    # rmax[j] = max(hi[j..j+L-1]); at bar t the prior-3-bar window is hi[t-1-L .. t-2] = rmax[t-1-L]
    rmax = sliding_window_view(hi, L).max(axis=1)   # len n-L+1, index j
    rmin = sliding_window_view(lo, L).min(axis=1)
    t = np.arange(L + 1, n)
    prior_hi = rmax[t - 1 - L]
    prior_lo = rmin[t - 1 - L]
    c = cl[t - 1]
    sig[t[c > prior_hi]] = 1
    sig[t[c < prior_lo]] = -1
    return sig


def _fwd(ctx, ent: np.ndarray, sign: np.ndarray, hold: int) -> np.ndarray:
    move = ctx.ltf_open[ent + hold] - ctx.ltf_open[ent]
    return sign * move / ctx.ltf_atr_prev[ent]


# --------------------------------------------------------------------------- #
# Arm evaluation
# --------------------------------------------------------------------------- #
def eval_arm(ctx, sig: np.ndarray, spec: dict, hold: int) -> dict:
    """One momentum arm (deterministic). Greedy active-hold over eligible breakout bars."""
    n = ctx.n
    regime = spec["mask"](ctx)
    elig = ctx.valid & regime & (sig != 0) & (np.arange(n) + hold < n)
    if spec["dir"]:
        elig &= (sig == ctx.htf_dir)                # HTF-direction confirmation
    elig_idx = np.nonzero(elig)[0]
    if elig_idx.size == 0:
        return {"n": 0, "mean": np.nan, "std": np.nan, "hitrate": np.nan, "ci": [np.nan, np.nan],
                "mde": np.nan, "trimmed": np.nan, "returns": np.array([])}
    ent = S1.greedy_entries(elig_idx, hold)
    r = _fwd(ctx, ent, sig[ent], hold)
    bb = block_bootstrap_ci(r, np.mean, n_boot=N_BOOT_SCREEN, n_seeds=N_SEEDS_CI)   # one bootstrap
    m = float(bb["stat"])
    return {"n": int(ent.size), "mean": m, "std": float(np.std(r)),
            "hitrate": float(np.mean(r > 0)), "ci": bb["ci"],
            "mde": float(m - bb["ci"][0]),                       # half-width, no extra bootstrap
            "trimmed": float(trimmed_mean(r)), "returns": r}


def random_timing_twin(ctx, regime_mask: np.ndarray, n_target: int, hold: int) -> dict:
    """Control B: >=25-seed random-timing battery in the same regime pool, matched entry count.
    Returns battery mean + percentile band (rank read, L-19)."""
    n = ctx.n
    pool = np.nonzero(ctx.valid & regime_mask & (np.arange(n) + hold < n))[0]
    if pool.size == 0 or n_target == 0:
        return {"battery_mean": np.nan, "seed_ci": [np.nan, np.nan]}
    means = np.empty(N_SEEDS)
    for k in range(N_SEEDS):
        rng = np.random.default_rng(10_000 + k)
        take = min(n_target, pool.size)
        ent = np.sort(rng.choice(pool, size=take, replace=False))
        sign = rng.choice(np.array([-1, 1], np.int8), size=take)   # random direction
        means[k] = float(np.mean(_fwd(ctx, ent, sign, hold)))
    return {"battery_mean": float(np.mean(means)),
            "seed_ci": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]}


def paired_lift_ci(filt: dict, base: dict) -> dict:
    """Filtered − baseline lift; difference CI from the two stored arm CIs (conservative
    independent-arm quantile combination — no re-bootstrap)."""
    if not np.isfinite(filt["mean"]) or not np.isfinite(base["mean"]):
        return {"lift": np.nan, "lift_ci": [np.nan, np.nan]}
    lo = filt["ci"][0] - base["ci"][1]; hi = filt["ci"][1] - base["ci"][0]
    return {"lift": float(filt["mean"] - base["mean"]), "lift_ci": [float(lo), float(hi)]}


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run() -> None:
    RESULTS.mkdir(exist_ok=True)
    specs = S1.variant_specs()                       # same 20-variant grid; 'sig'->'dir' semantics reused
    rows: list[dict] = []
    integrity: list[dict] = []

    for sym in tqdm(INSTRUMENTS, desc="instruments"):
        train = S1.load_train_1m(sym)
        for name, htf_min, ltf_min, ratio in DOMAIN_PAIRS:
            ctx = S1.build_domain_ctx(name, htf_min, ltf_min, train, shift_htf=0)
            ctx_sh = S1.build_domain_ctx(name, htf_min, ltf_min, train, shift_htf=PHASE_SHIFT_HTF_BARS)
            sig = momentum_signal(ctx)               # HTF-independent; identical for all arms
            holds = [ratio * m for m in HOLD_MULTS]
            ig = S1.integrity_checks(train, ctx, max(holds))
            ig.update({"instrument": sym, "domain": name,
                       "breakout_rate": float(np.mean(sig != 0))})
            integrity.append(ig)
            n_breakouts = int(np.sum(sig != 0))
            for m, hold in zip(HOLD_MULTS, holds):
                base = eval_arm(ctx, sig, specs[0], hold)      # 'none' baseline
                for spec in specs:
                    a = eval_arm(ctx, sig, spec, hold)
                    row = {"instrument": sym, "domain": name, "htf_ltf_ratio": ratio,
                           "hold_mult": m, "hold_bars": hold, "variant": spec["name"],
                           "uses_htf": spec["name"] != "none", "di_confirm": spec["dir"],
                           "n": a["n"], "mean": a["mean"], "std": a["std"], "hitrate": a["hitrate"],
                           "ci": a["ci"], "mde": a["mde"], "trimmed": a["trimmed"],
                           "baseline_admit_frac": (a["n"] / base["n"]) if base["n"] else np.nan}
                    if spec["name"] != "none":
                        row.update(paired_lift_ci(a, base))
                        twin = random_timing_twin(ctx, spec["mask"](ctx), a["n"], hold)
                        row["rand_twin_mean"] = twin["battery_mean"]
                        row["rand_twin_ci"] = twin["seed_ci"]
                        if spec["dir"]:                        # Control C on HTF-alignment arms
                            ash = eval_arm(ctx_sh, sig, spec, hold)
                            row["phaseshift_mean"] = ash["mean"]
                            row["phaseshift_ci_low"] = ash["ci"][0]
                    rows.append(row)
            del ctx, ctx_sh, sig

    df = pl.DataFrame(rows, strict=False)
    df.write_parquet(RESULTS / "cells.parquet")
    Path(RESULTS / "integrity.json").write_text(json.dumps(integrity, indent=2))
    _write_summary(df, integrity)
    print(f"[SPDR-002] wrote {df.height} cells -> {RESULTS/'cells.parquet'}")


def _write_summary(df: pl.DataFrame, integrity: list[dict]) -> None:
    htf = df.filter(pl.col("uses_htf"))
    summ = {
        "integrity_all_pass": all(x["all_pass"] for x in integrity),
        "breakout_rate_by_domain": {x["instrument"] + "/" + x["domain"]: round(x["breakout_rate"], 4)
                                    for x in integrity},
        "n_cells": df.height, "n_htf_cells": htf.height,
        "n_baseline_cells": int((~df["uses_htf"]).sum()),
        "median_htf_n": float(np.median(htf["n"].to_numpy())),
        "n_lift_ci_excl_zero_pos": int(htf.filter(
            pl.col("lift_ci").list.get(0) > 0).height) if "lift_ci" in htf.columns else 0,
        "n_lift_ci_excl_zero_neg": int(htf.filter(
            pl.col("lift_ci").list.get(1) < 0).height) if "lift_ci" in htf.columns else 0,
    }
    Path(RESULTS / "summary.json").write_text(json.dumps(summ, indent=2, default=str))
    print(json.dumps({k: v for k, v in summ.items() if k != "breakout_rate_by_domain"}, indent=2))


if __name__ == "__main__":
    run()
