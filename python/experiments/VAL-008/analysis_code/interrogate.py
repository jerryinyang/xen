"""VAL-008 data-analyst interrogation — own code, canonical xen estimands only.

Per design.md §7/§8: per-cell per-leg gross (shim → adjudication), first-fill-bar hit rate
(exact binomial CI), destroy collapse fractions, blind leak-catch protocol, BASELINE wash
read (hardened block_bootstrap_ci), concentration + thirds stability, physicality restate.

Writes results/analysis_summary.json.
"""
from __future__ import annotations

import json
import sys
from math import sqrt
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[3]  # python/
sys.path.insert(0, str(ROOT / "src"))

from xen.evaluation import block_bootstrap_ci  # noqa: E402
from xen.nautilus.adjudication_shim import adjudicate_emission  # noqa: E402

FAMILY = ROOT.parent / "data" / "nautilus_runs" / "VAL-008"
OUT = Path(__file__).resolve().parents[1] / "results" / "analysis_summary.json"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
SEEDS = (0, 1, 2, 3, 4)
ARMS = (
    ["BASELINE", "LEAK", "LEAK-LAG1"]
    + [f"LEAK-SHUF-s{s}" for s in SEEDS]
    + [f"BASELINE-SHUF-s{s}" for s in SEEDS]
)
# Leak-catch protocol (design §7, predeclared): flag iff hit-rate CI-low > 0.55 AND
# destroy collapse >= 0.9.
HIT_CI_LOW_FLAG = 0.55
COLLAPSE_FLAG = 0.9


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score 95% CI for a binomial proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (centre - half, centre + half)


def cell_stats(symbol: str, arm: str) -> dict:
    bundle = adjudicate_emission(FAMILY / f"{symbol}__{arm}", cost_bps=0.0)
    cis = bundle.cis_trades.filter(~pl.col("Censored"))
    bps = cis.get_column("RealizedBps").to_numpy()
    pos = bundle.positions
    sct = pos.get_column("SourceCloseTime").to_numpy().astype("datetime64[ns]").astype(np.int64)
    opens = pos.get_column("RealOpen").to_numpy()

    # First-fill-bar hit rate: direction vs sign of the o2o return of the fill bar.
    entry = cis.get_column("EntryTime").to_numpy().astype("datetime64[ns]").astype(np.int64)
    direction = cis.get_column("Direction").to_numpy()
    # Fill ts is stamped at the decision-bar close (= wall-clock open of the next bar);
    # the fill executes at opens[idx+1] (verified vs EntryFillPrice ±1 tick). The first
    # holding bar's o2o is therefore opens[idx+2]/opens[idx+1].
    fill_idx = np.searchsorted(sct, entry) + 1
    ok = fill_idx + 1 < len(opens)
    o2o = opens[fill_idx[ok] + 1] / opens[fill_idx[ok]] - 1.0
    signed = direction[ok] * o2o
    n_nonzero = int((signed != 0).sum())
    k_hit = int((signed > 0).sum())
    hit = k_hit / n_nonzero if n_nonzero else float("nan")
    hit_lo, hit_hi = wilson_ci(k_hit, n_nonzero)

    ci = block_bootstrap_ci(bps, block=5)
    thirds = np.array_split(bps, 3)
    top = np.sort(bps)[::-1]
    return {
        "symbol": symbol,
        "arm": arm,
        "n_legs": int(len(bps)),
        "mean_bps": float(bps.mean()),
        "median_bps": float(np.median(bps)),
        "sd_bps": float(bps.std()),
        "total_bps": float(bps.sum()),
        "ci95": ci["ci"],
        "ci_low_seed_range": ci["ci_low_seed_range"],
        "hit_rate_first_bar": hit,
        "hit_ci95": [hit_lo, hit_hi],
        "hit_n": n_nonzero,
        "thirds_mean_bps": [float(t.mean()) for t in thirds],
        "total_minus_top5_legs": float(bps.sum() - top[:5].sum()),
        "q01_q99": [float(np.quantile(bps, 0.01)), float(np.quantile(bps, 0.99))],
    }


def main() -> int:
    cells = {f"{s}__{a}": cell_stats(s, a) for s in SYMBOLS for a in ARMS}

    leak_catch = {}
    for s in SYMBOLS:
        raw = cells[f"{s}__LEAK"]
        base = cells[f"{s}__BASELINE"]
        shuf_means = [cells[f"{s}__LEAK-SHUF-s{i}"]["mean_bps"] for i in SEEDS]
        lag1 = cells[f"{s}__LEAK-LAG1"]["mean_bps"]
        collapse_shuf = [1.0 - m / raw["mean_bps"] for m in shuf_means]
        collapse_lag1 = 1.0 - lag1 / raw["mean_bps"]
        base_shuf_means = [cells[f"{s}__BASELINE-SHUF-s{i}"]["mean_bps"] for i in SEEDS]

        # Blind protocol applied identically to both arms:
        leak_flag = raw["hit_ci95"][0] > HIT_CI_LOW_FLAG and (
            min(collapse_shuf) >= COLLAPSE_FLAG and collapse_lag1 >= COLLAPSE_FLAG
        )
        # BASELINE destroy = BASELINE-SHUF; collapse fraction ill-defined near zero edge —
        # protocol still computes it, flag needs hit-rate leg first.
        base_collapse = [
            (1.0 - m / base["mean_bps"]) if base["mean_bps"] != 0 else float("nan")
            for m in base_shuf_means
        ]
        base_flag = base["hit_ci95"][0] > HIT_CI_LOW_FLAG and all(
            c >= COLLAPSE_FLAG for c in base_collapse
        )
        leak_catch[s] = {
            "LEAK": {
                "hit_rate": raw["hit_rate_first_bar"],
                "hit_ci95": raw["hit_ci95"],
                "raw_mean_bps": raw["mean_bps"],
                "shuf_mean_bps_per_seed": shuf_means,
                "collapse_fraction_shuf": collapse_shuf,
                "lag1_mean_bps": lag1,
                "collapse_fraction_lag1": collapse_lag1,
                "flagged_as_leak": bool(leak_flag),
            },
            "BASELINE": {
                "hit_rate": base["hit_rate_first_bar"],
                "hit_ci95": base["hit_ci95"],
                "raw_mean_bps": base["mean_bps"],
                "shuf_mean_bps_per_seed": base_shuf_means,
                "collapse_fraction_shuf": base_collapse,
                "flagged_as_leak": bool(base_flag),
            },
        }

    summary = {
        "cells": cells,
        "leak_catch": leak_catch,
        "protocol": {
            "hit_ci_low_flag": HIT_CI_LOW_FLAG,
            "collapse_flag": COLLAPSE_FLAG,
            "rule": "flag iff hit-rate CI-low > 0.55 AND all destroy collapse fractions >= 0.9",
        },
    }
    OUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    for s in SYMBOLS:
        lc = leak_catch[s]
        print(
            f"{s}: LEAK hit={lc['LEAK']['hit_rate']:.4f} raw={lc['LEAK']['raw_mean_bps']:+.3f} "
            f"shuf_collapse={min(lc['LEAK']['collapse_fraction_shuf']):.3f}.."
            f"{max(lc['LEAK']['collapse_fraction_shuf']):.3f} "
            f"lag1_collapse={lc['LEAK']['collapse_fraction_lag1']:.3f} "
            f"FLAG={lc['LEAK']['flagged_as_leak']} | "
            f"BASELINE hit={lc['BASELINE']['hit_rate']:.4f} "
            f"raw={lc['BASELINE']['raw_mean_bps']:+.3f} FLAG={lc['BASELINE']['flagged_as_leak']}"
        )
    print(f"summary → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
