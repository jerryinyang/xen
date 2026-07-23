"""Physicality, cost sensitivity, power and CI fragility for L1."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from xen.evaluation import block_sensitivity, cost_sensitivity, mde, powered_label

ROOT = Path(__file__).resolve().parents[4]
a = pl.read_parquet(ROOT / "data/nautilus_runs/SPDR-011/artifact-bundle/design.parquet")
high = a.filter(pl.col("4h_available") & (pl.col("vol_tercile") == "HIGH"))
x = high["partial_net_2bps"].to_numpy()
g = high["gross_signed_4h_bps"].to_numpy()

print("== occupancy / physicality (HIGH arm as specified) ==")
span_days = (high["exit_ts"].max() - high["entry_ts"].min()).total_seconds() / 86400
hours_in_mkt = high.height * 4.0
# concurrency: episodes overlap across symbols, so also report per-symbol occupancy
print(f"  events {high.height}, each 4h, window {span_days:.0f} days")
print(f"  gross time in market (summed across symbols): {hours_in_mkt:.0f}h "
      f"of {span_days*24:.0f}h wall-clock x5 symbols = {hours_in_mkt/(span_days*24*5):.3f} occupancy")
for s in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]:
    k = high.filter(pl.col("symbol") == s).height
    print(f"    {s:9s} {k:4d} episodes -> {k*4/(span_days*24):.3f} of its own wall clock")

print("\n== cost sensitivity: where does the gross edge die? ==")
for r in cost_sensitivity(g, [0.0, 5.0, 11.45, 13.45, 20.0, 30.0]):
    print(f"  round-trip {r['cost_bps']:6.2f} bps -> net mean {r['stat']:8.2f}  "
          f"CI [{r['ci'][0]:8.2f}, {r['ci'][1]:8.2f}]")
print("  frozen cost map: fees 11.00 + funding mean 0.45 = 11.45; +2 allowance = 13.45 bps")
print("  NOTE: spread is NOT in any of these numbers — true cost is strictly higher.")

print("\n== power ==")
for name, arr in [("POOLED HIGH", x)] + [
    (s, high.filter(pl.col("symbol") == s)["partial_net_2bps"].to_numpy())
    for s in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]
]:
    p = powered_label(arr, plausible_effect=10.0)
    print(f"  {name:11s} n={len(arr):4d}  MDE={p['mde']:8.2f} bps  "
          f"powered for a 10-bps effect: {p['powered']}")

print("\n== CI fragility: block sensitivity + seed band (pooled HIGH, event-level) ==")
for r in block_sensitivity(x, [3, 5, 10]):
    print(f"  block {r['block']:2d}: mean {r['stat']:8.2f}  CI [{r['ci'][0]:8.2f}, {r['ci'][1]:8.2f}]  "
          f"ci_low_seed_range {tuple(round(v,2) for v in r['ci_low_seed_range'])}")

print("\n== homogeneity: is pooling legitimate? ==")
means = {s: float(high.filter(pl.col("symbol") == s)["partial_net_2bps"].mean())
         for s in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]}
print("  per-symbol means:", {k: round(v, 1) for k, v in means.items()})
print(f"  spread across symbols: {max(means.values()) - min(means.values()):.1f} bps "
      f"(min {min(means.values()):.1f}, max {max(means.values()):.1f})")
print(f"  pooled mean {x.mean():.2f} sits {'inside' if min(means.values()) < x.mean() < max(means.values()) else 'outside'} the per-symbol range")

print("\n== median / trimmed per symbol (is any stratum positive on a robust stat?) ==")
from xen.evaluation import trimmed_mean
for s in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]:
    arr = high.filter(pl.col("symbol") == s)["partial_net_2bps"].to_numpy()
    print(f"  {s:9s} mean {arr.mean():8.2f}  median {np.median(arr):8.2f}  "
          f"trim20 {trimmed_mean(arr, trim=0.2):8.2f}  win-rate {(arr>0).mean():.3f}")
