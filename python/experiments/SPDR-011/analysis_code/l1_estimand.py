"""L1 primary estimand: HIGH-state partial net over one fixed 4h episode.

Inference follows design §9: UTC-date blocks retaining every symbol/event on sampled dates,
10,000 circular resamples per seed, seeds 101/211/307/401/503, block lengths 1/3/7 dates.
Accounting is NOT recomputed here — `partial_net_*` is taken from the emission and was verified
against canonical xen.evaluation cost functions in l1_cost_verify.py (0 mismatches).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from xen.evaluation import mde, trimmed_mean

ROOT = Path(__file__).resolve().parents[4]
a = pl.read_parquet(ROOT / "data/nautilus_runs/SPDR-011/artifact-bundle/design.parquet")

SEEDS = [101, 211, 307, 401, 503]
N_BOOT = 10_000
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]


def date_block_ci(df: pl.DataFrame, col: str, *, block: int = 3,
                  stat=np.mean, seeds=SEEDS, n_boot=N_BOOT, alpha=0.05) -> dict:
    """Circular date-block bootstrap retaining every event on each sampled date (design §9)."""
    if df.height == 0:
        return {"n": 0, "n_dates": 0, "stat": float("nan"),
                "ci": (float("nan"), float("nan")), "ci_low_seed_range": (float("nan"),) * 2}
    dates = np.array(sorted(df["trade_day"].unique().to_list()))
    idx_by_date = {d: g[col].to_numpy() for d, g in
                   zip(df["trade_day"].unique(maintain_order=False).to_list(),
                       df.partition_by("trade_day"))}
    # rebuild deterministically keyed by date
    idx_by_date = {}
    for g in df.partition_by("trade_day"):
        idx_by_date[g["trade_day"][0]] = g[col].to_numpy()
    n_dates = len(dates)
    point = float(stat(df[col].to_numpy()))
    lows, highs = [], []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        n_blocks = int(np.ceil(n_dates / block))
        draws = np.empty(n_boot)
        starts_all = rng.integers(0, n_dates, size=(n_boot, n_blocks))
        for b in range(n_boot):
            picked = []
            for s in starts_all[b]:
                for k in range(block):
                    picked.append(dates[(s + k) % n_dates])
            picked = picked[:n_dates]
            vals = np.concatenate([idx_by_date[d] for d in picked])
            draws[b] = stat(vals)
        lows.append(float(np.quantile(draws, alpha / 2)))
        highs.append(float(np.quantile(draws, 1 - alpha / 2)))
    return {
        "n": df.height, "n_dates": n_dates, "stat": point,
        "ci": (float(np.mean(lows)), float(np.mean(highs))),
        "ci_low_seed_range": (min(lows), max(lows)),
        "ci_high_seed_range": (min(highs), max(highs)),
    }


def label(mean_v: float, ci_low: float, ci_high: float, mde_v: float) -> str:
    if mde_v > 20.0:
        return "UNPOWERED"
    if mean_v >= 10.0 and ci_low > 0:
        return "SUPPORTED"
    if mean_v <= -10.0 and ci_high < 0:
        return "CONTRADICTED"
    if abs(mean_v) < 10.0:
        return "WASH"
    return "INDETERMINATE (|mean|>=10 but CI does not clear)"


high = a.filter(pl.col("4h_available") & (pl.col("vol_tercile") == "HIGH"))
out = {"strata": {}}

print("=" * 108)
print("L1 — HIGH state, partial net after fees + funding + 2 bps allowance (spread NOT charged)")
print("=" * 108)
print(f"{'stratum':10s} {'n':>5s} {'dates':>6s} {'mean':>8s} {'median':>8s} {'trim20':>8s} "
      f"{'CI low':>9s} {'CI high':>9s} {'MDE':>8s}  label")

for name, df in [(s, high.filter(pl.col("symbol") == s)) for s in SYMBOLS] + [("POOLED", high)]:
    x = df["partial_net_2bps"].to_numpy()
    r = date_block_ci(df, "partial_net_2bps")
    m = mde(x) if len(x) > 2 else float("nan")
    lab = label(r["stat"], r["ci"][0], r["ci"][1], m)
    out["strata"][name] = {**r, "median": float(np.median(x)),
                           "trimmed_mean20": float(trimmed_mean(x, trim=0.2)),
                           "mde": float(m), "label": lab}
    print(f"{name:10s} {r['n']:5d} {r['n_dates']:6d} {r['stat']:8.2f} "
          f"{np.median(x):8.2f} {trimmed_mean(x, trim=0.2):8.2f} "
          f"{r['ci'][0]:9.2f} {r['ci'][1]:9.2f} {m:8.2f}  {lab}")

print()
print("allowance sensitivity (pooled HIGH):")
for col, allow in [("partial_net_0bps", 0), ("partial_net_2bps", 2), ("partial_net_5bps", 5)]:
    r = date_block_ci(high, col)
    print(f"  allowance {allow} bps: mean {r['stat']:7.2f}  CI [{r['ci'][0]:7.2f}, {r['ci'][1]:7.2f}]")

print()
print("gross (before any cost), pooled HIGH:")
rg = date_block_ci(high, "gross_signed_4h_bps")
print(f"  mean {rg['stat']:7.2f}  CI [{rg['ci'][0]:7.2f}, {rg['ci'][1]:7.2f}]  "
      f"| mean total cost {high['total_bps'].mean():.2f} bps + 2 allowance")

Path(ROOT / "python/experiments/SPDR-011/results/l1_estimand.json").write_text(
    json.dumps(out, indent=2, default=str))
