"""Q20: what would make the +9.37 bps headline wrong? Executed probes."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[4]
a = pl.read_parquet(ROOT / "data/nautilus_runs/SPDR-011/artifact-bundle/design.parquet")
high = a.filter(pl.col("4h_available") & (pl.col("vol_tercile") == "HIGH"))
x = high["partial_net_2bps"].to_numpy()

print("P1. Event-weighted vs date-weighted (dependence: 394 events on 74 dates)")
per_date = high.group_by("trade_day").agg(pl.col("partial_net_2bps").mean().alias("m"))["m"].to_numpy()
print(f"   event-weighted mean {x.mean():8.2f} bps  (n=394)")
print(f"   date-weighted  mean {per_date.mean():8.2f} bps  (n=74 dates)  <- sign flips")

print("\nP2. Chronological split-half (does the first half predict the second?)")
h = high.sort("entry_ts")
mid = h.height // 2
for name, part in [("first half ", h.head(mid)), ("second half", h.tail(h.height - mid))]:
    arr = part["partial_net_2bps"].to_numpy()
    print(f"   {name}: mean {arr.mean():8.2f}  median {np.median(arr):8.2f}  n={len(arr)}  "
          f"dates {part['trade_day'].n_unique()}")

print("\nP3. Winsorise the tail at q01/q99 (keeps every leg, caps the extremes)")
lo, hi = np.percentile(x, 1), np.percentile(x, 99)
w = np.clip(x, lo, hi)
print(f"   raw mean {x.mean():8.2f} -> winsorised mean {w.mean():8.2f}  (cap [{lo:.0f}, {hi:.0f}])")

print("\nP4. Does any single date carry the pooled sign?")
by_date = (high.group_by("trade_day")
           .agg(pl.col("partial_net_2bps").sum().alias("s"))
           .sort("s", descending=True))
tot = x.sum()
print(f"   pooled total {tot:.0f} bps")
print(f"   top date {by_date['trade_day'][0]} contributes {by_date['s'][0]:.0f} "
      f"({by_date['s'][0]/tot*100:.0f}% of total)")
drop1 = high.filter(pl.col("trade_day") != by_date["trade_day"][0])["partial_net_2bps"].to_numpy()
print(f"   without that one date: mean {drop1.mean():8.2f} bps (n={len(drop1)})")

print("\nP5. Sign test on legs (distribution-free, ignores magnitude)")
pos, n = int((x > 0).sum()), len(x)
print(f"   {pos}/{n} legs positive = {pos/n:.3f}; a coin flip would give 0.500")
print(f"   deficit vs coin flip: {(pos/n - 0.5)*100:+.1f} pp")

print("\nP6. Is the tail symmetric? (large moves both ways, or genuinely skewed up?)")
print(f"   n legs >  +500 bps: {(x > 500).sum():3d}   sum {x[x>500].sum():9.0f}")
print(f"   n legs <  -500 bps: {(x < -500).sum():3d}   sum {x[x<-500].sum():9.0f}")
print(f"   net of those tails: {x[np.abs(x)>500].sum():9.0f} bps")
print(f"   body only (|x|<=500): mean {x[np.abs(x)<=500].mean():8.2f}  n={(np.abs(x)<=500).sum()}")
