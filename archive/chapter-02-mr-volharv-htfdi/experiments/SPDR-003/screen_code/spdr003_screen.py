"""SPDR-003 — HTF-context screen on CTRL-03 naive-reversion LTF LIMIT entries (TRAIN-only).

Lane: SPDR speed-run (docs/references/spdr-lane.md). Leg 3/3 (final). TRAIN-only, no disposition
(the CTRL-01/02/03 series verdict is the operator's, after this leg). Design:
python/experiments/SPDR-003/design.md. Analysed BLIND of SPDR-001/002 results — this module only
replicates their causal methodology.

Signal (per mtf.md): a TRAILING LIMIT reversion control. Buy-limit rests at min(Low[t-3..t-1]),
sell-limit at max(High[t-3..t-1]); a new signal each bar resets the limit to the current extreme
(trailing). Because the limit trails every bar, each LTF bar is an independent fill opportunity at
its own 3-bar extreme — the fill (touch) resolves within that bar. THE NEW/HEAVY PIECE: the fill is
simulated causally on the 1-minute base bars — buy fills at the first m1 bar (within the LTF bar)
whose Low <= limit; fill price = limit if the m1 Opened above it, else the m1 Open (gapped through =
conservative, never better than market). H is measured FROM the fill bar. HTF context anchors at the
FILL bar's open (B-4 — conditions on the touch, not a signal). Controls: A unfiltered-reversion
baseline (lift, base-confounded lens), B matched-random-timing limit twin with the SAME fill sim,
C HTF phase-shift future-destroy.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import polars as pl
from numpy.lib.stride_tricks import sliding_window_view
from tqdm import tqdm

EXP_DIR = Path(__file__).resolve().parents[1]
RESULTS = EXP_DIR / "results"
SPDR001_CODE = EXP_DIR.parent / "SPDR-001" / "screen_code"
sys.path.insert(0, str(SPDR001_CODE))
import spdr001_screen as S1                                                   # noqa: E402
from xen.evaluation import block_bootstrap_ci, trimmed_mean                   # noqa: E402

INSTRUMENTS = S1.INSTRUMENTS
DOMAIN_PAIRS = S1.DOMAIN_PAIRS
HOLD_MULTS = S1.HOLD_MULTS
N_SEEDS = S1.N_SEEDS
PHASE_SHIFT_HTF_BARS = S1.PHASE_SHIFT_HTF_BARS
LOOKBACK = 3                                  # 3-bar extreme (prior bars, exclusive of forming bar)
N_BOOT_SCREEN = 2000                          # coarse stage-3 CI (stage-5 analyst does the full L-20)
N_SEEDS_CI = 2


# --------------------------------------------------------------------------- #
# Causal m1 limit-fill table (HTF-independent -> precompute once per inst/domain)
# --------------------------------------------------------------------------- #
def build_fill_table(ctx, train_1m: pl.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Per LTF bar b: fill_side[b] in {-1,0,+1} and fill_price[b] under the trailing-limit model.
    buy_limit[b]=min(Low[b-3..b-1]); a touch is resolved on b's OWN 1-minute bars (first m1 whose
    Low<=limit / High>=limit). Gap-through (m1 Open past the limit) fills at the m1 Open. Side tie
    broken by earlier m1 timestamp. Causal: uses only bars <= b and m1 rows inside bar b."""
    n = ctx.n
    lo, hi = ctx._ltf_low, ctx._ltf_high
    fill_side = np.zeros(n, dtype=np.int8)
    fill_price = np.full(n, np.nan)
    if n < LOOKBACK + 1:
        return fill_side, fill_price
    # trailing limits from the 3 prior bars (b-3,b-2,b-1)
    win_lo = sliding_window_view(lo, LOOKBACK)[:-1]           # rows 0..n-LOOKBACK-1 span [i..i+L-1]
    win_hi = sliding_window_view(hi, LOOKBACK)[:-1]
    buy_lim = np.full(n, np.nan); sell_lim = np.full(n, np.nan)
    buy_lim[LOOKBACK:] = win_lo.min(axis=1)[: n - LOOKBACK]   # bar b uses window ending at b-1
    sell_lim[LOOKBACK:] = win_hi.max(axis=1)[: n - LOOKBACK]
    touch_buy = np.isfinite(buy_lim) & (lo <= buy_lim)
    touch_sell = np.isfinite(sell_lim) & (hi >= sell_lim)
    cand = np.nonzero(touch_buy | touch_sell)[0]

    m_open_t = train_1m["OpenTime"].to_numpy().astype("datetime64[ns]").astype("int64")
    m_open = train_1m["Open"].to_numpy().astype(float)
    m_low = train_1m["Low"].to_numpy().astype(float)
    m_high = train_1m["High"].to_numpy().astype(float)
    lt = ctx._ltf_open_time                                   # LTF open times (int64 ns)

    for b in cand:
        start = lt[b]
        end = lt[b + 1] if b + 1 < n else start + (lt[b] - lt[b - 1] if b > 0 else 1)
        j0 = int(np.searchsorted(m_open_t, start, "left"))
        j1 = int(np.searchsorted(m_open_t, end, "left"))
        if j1 <= j0:
            continue
        mo = m_open[j0:j1]; ml = m_low[j0:j1]; mh = m_high[j0:j1]
        bt = -1; b_price = np.nan; st = -1; s_price = np.nan
        if touch_buy[b]:
            jj = np.nonzero(ml <= buy_lim[b])[0]
            if jj.size:
                k = jj[0]; bt = k
                b_price = mo[k] if mo[k] <= buy_lim[b] else buy_lim[b]   # gap-through -> m1 Open
        if touch_sell[b]:
            jj = np.nonzero(mh >= sell_lim[b])[0]
            if jj.size:
                k = jj[0]; st = k
                s_price = mo[k] if mo[k] >= sell_lim[b] else sell_lim[b]
        if bt >= 0 and (st < 0 or bt <= st):
            fill_side[b] = 1; fill_price[b] = b_price
        elif st >= 0:
            fill_side[b] = -1; fill_price[b] = s_price
    return fill_side, fill_price


def _fwd(ctx, ent, side, price, hold):
    return side * (ctx.ltf_open[ent + hold] - price) / ctx.ltf_atr_prev[ent]


# --------------------------------------------------------------------------- #
# Arm evaluation
# --------------------------------------------------------------------------- #
def eval_arm(ctx, fill_side, fill_price, spec, hold) -> dict:
    n = ctx.n
    regime = spec["mask"](ctx)
    elig = ctx.valid & regime & (fill_side != 0) & (np.arange(n) + hold < n)
    if spec["dir"]:
        elig &= (fill_side == ctx.htf_dir)                   # HTF-direction confirmation
    idx = np.nonzero(elig)[0]
    if idx.size == 0:
        return {"n": 0, "mean": np.nan, "std": np.nan, "hitrate": np.nan, "ci": [np.nan, np.nan],
                "mde": np.nan, "trimmed": np.nan, "returns": np.array([])}
    ent = S1.greedy_entries(idx, hold)
    r = _fwd(ctx, ent, fill_side[ent].astype(float), fill_price[ent], hold)
    r = r[np.isfinite(r)]
    if r.size < 2:
        return {"n": int(r.size), "mean": float(np.mean(r)) if r.size else np.nan, "std": np.nan,
                "hitrate": np.nan, "ci": [np.nan, np.nan], "mde": np.nan, "trimmed": np.nan,
                "returns": r}
    bb = block_bootstrap_ci(r, np.mean, n_boot=N_BOOT_SCREEN, n_seeds=N_SEEDS_CI)
    m = float(bb["stat"])
    return {"n": int(r.size), "mean": m, "std": float(np.std(r)), "hitrate": float(np.mean(r > 0)),
            "ci": bb["ci"], "mde": float(m - bb["ci"][0]), "trimmed": float(trimmed_mean(r)),
            "returns": r}


def random_twin(ctx, fill_side, fill_price, regime_mask, n_target, hold) -> dict:
    """Control B: >=25-seed random-timing limit twin using the SAME fill outcomes, random side +
    matched fill count in the regime pool. Percentile/rank read (L-19)."""
    n = ctx.n
    pool = np.nonzero(ctx.valid & regime_mask & (fill_side != 0) & (np.arange(n) + hold < n))[0]
    if pool.size == 0 or n_target == 0:
        return {"battery_mean": np.nan, "seed_ci": [np.nan, np.nan]}
    means = np.empty(N_SEEDS)
    for k in range(N_SEEDS):
        rng = np.random.default_rng(20_000 + k)
        take = min(n_target, pool.size)
        ent = np.sort(rng.choice(pool, size=take, replace=False))
        side = rng.choice(np.array([-1, 1], np.int8), size=take).astype(float)
        r = _fwd(ctx, ent, side, fill_price[ent], hold)
        r = r[np.isfinite(r)]
        means[k] = float(np.mean(r)) if r.size else np.nan
    good = means[np.isfinite(means)]
    if good.size < 2:
        return {"battery_mean": float(np.nanmean(means)) if good.size else np.nan,
                "seed_ci": [np.nan, np.nan]}
    return {"battery_mean": float(np.mean(good)),
            "seed_ci": [float(np.percentile(good, 2.5)), float(np.percentile(good, 97.5))]}


def paired_lift(filt, base) -> dict:
    if not np.isfinite(filt["mean"]) or not np.isfinite(base["mean"]):
        return {"lift": np.nan, "lift_ci": [np.nan, np.nan]}
    lo = filt["ci"][0] - base["ci"][1]; hi = filt["ci"][1] - base["ci"][0]
    return {"lift": float(filt["mean"] - base["mean"]), "lift_ci": [float(lo), float(hi)]}


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run() -> None:
    RESULTS.mkdir(exist_ok=True)
    specs = S1.variant_specs()
    rows: list[dict] = []
    integrity: list[dict] = []

    for sym in tqdm(INSTRUMENTS, desc="instruments"):
        train = S1.load_train_1m(sym)
        for name, htf_min, ltf_min, ratio in DOMAIN_PAIRS:
            ctx = S1.build_domain_ctx(name, htf_min, ltf_min, train, shift_htf=0)
            ctx_sh = S1.build_domain_ctx(name, htf_min, ltf_min, train, shift_htf=PHASE_SHIFT_HTF_BARS)
            fside, fprice = build_fill_table(ctx, train)     # HTF-independent, once per inst/domain
            n_sig = int(np.sum(fside != 0))
            holds = [ratio * m for m in HOLD_MULTS]
            ig = S1.integrity_checks(train, ctx, max(holds))
            ig.update({"instrument": sym, "domain": name,
                       "fill_rate": float(np.mean(fside != 0))})
            integrity.append(ig)
            for m, hold in zip(HOLD_MULTS, holds):
                base = eval_arm(ctx, fside, fprice, specs[0], hold)
                for spec in specs:
                    a = eval_arm(ctx, fside, fprice, spec, hold)
                    row = {"instrument": sym, "domain": name, "htf_ltf_ratio": ratio,
                           "hold_mult": m, "hold_bars": hold, "variant": spec["name"],
                           "uses_htf": spec["name"] != "none", "di_confirm": spec["dir"],
                           "n": a["n"], "mean": a["mean"], "std": a["std"], "hitrate": a["hitrate"],
                           "ci": a["ci"], "mde": a["mde"], "trimmed": a["trimmed"],
                           "baseline_admit_frac": (a["n"] / base["n"]) if base["n"] else np.nan}
                    if spec["name"] != "none":
                        row.update(paired_lift(a, base))
                        tw = random_twin(ctx, fside, fprice, spec["mask"](ctx), a["n"], hold)
                        row["rand_twin_mean"] = tw["battery_mean"]
                        row["rand_twin_ci"] = tw["seed_ci"]
                        if spec["dir"]:
                            ash = eval_arm(ctx_sh, fside, fprice, spec, hold)
                            row["phaseshift_mean"] = ash["mean"]
                            row["phaseshift_ci_low"] = ash["ci"][0]
                    rows.append(row)
            del ctx, ctx_sh, fside, fprice

    df = pl.DataFrame(rows, strict=False)
    df.write_parquet(RESULTS / "cells.parquet")
    Path(RESULTS / "integrity.json").write_text(json.dumps(integrity, indent=2))
    _write_summary(df, integrity)
    print(f"[SPDR-003] wrote {df.height} cells -> {RESULTS/'cells.parquet'}")


def _write_summary(df: pl.DataFrame, integrity: list[dict]) -> None:
    htf = df.filter(pl.col("uses_htf"))
    summ = {
        "integrity_all_pass": all(x["all_pass"] for x in integrity),
        "fill_rate_by_domain": {x["instrument"] + "/" + x["domain"]: round(x["fill_rate"], 4)
                                for x in integrity},
        "n_cells": df.height, "n_htf_cells": htf.height,
        "n_baseline_cells": int((~df["uses_htf"]).sum()),
        "median_htf_n": float(np.nanmedian(htf["n"].to_numpy())),
    }
    Path(RESULTS / "summary.json").write_text(json.dumps(summ, indent=2, default=str))
    print(json.dumps({k: v for k, v in summ.items() if k != "fill_rate_by_domain"}, indent=2))


if __name__ == "__main__":
    run()
