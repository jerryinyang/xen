"""Concentration, stability and dependence probes for L1."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[4]
a = pl.read_parquet(ROOT / "data/nautilus_runs/SPDR-011/artifact-bundle/design.parquet")
high = a.filter(pl.col("4h_available") & (pl.col("vol_tercile") == "HIGH"))
x = high["partial_net_2bps"].to_numpy()
n = len(x)

print("== distribution, pooled HIGH (bps) ==")
qs = [1, 5, 25, 50, 75, 95, 99]
print("  mean %.2f  std %.2f  min %.2f  max %.2f" % (x.mean(), x.std(ddof=1), x.min(), x.max()))
print("  " + "  ".join(f"q{q:02d}={np.percentile(x,q):8.2f}" for q in qs))
print(f"  share of legs > 0: {(x>0).mean():.3f}  ({(x>0).sum()}/{n})")

print("\n== concentration: drop top winners (pooled HIGH) ==")
order = np.argsort(x)[::-1]
for k in (0, 1, 3, 5, 10):
    keep = np.ones(n, bool)
    keep[order[:k]] = False
    print(f"  drop top {k:2d}: mean {x[keep].mean():8.2f}  total {x[keep].sum():10.1f}  n={keep.sum()}")

print("\n== top contributors ==")
top = high.sort("partial_net_2bps", descending=True).head(5).select(
    "symbol", "trade_day", "direction", "gross_signed_4h_bps", "partial_net_2bps")
print(top)
tot = x.sum()
print(f"  pooled total {tot:.1f} bps; top-5 legs contribute {x[order[:5]].sum():.1f} "
      f"({x[order[:5]].sum()/tot*100:.0f}% of total)")
dec = int(np.ceil(n * 0.1))
print(f"  top decile ({dec} legs) contributes {x[order[:dec]].sum():.1f} "
      f"({x[order[:dec]].sum()/tot*100:.0f}% of total)")

print("\n== leave-one-symbol-out (pooled HIGH mean) ==")
for s in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]:
    sub = high.filter(pl.col("symbol") != s)["partial_net_2bps"].to_numpy()
    print(f"  without {s:9s}: mean {sub.mean():8.2f}  n={len(sub)}")

print("\n== leave-one-effective-third-out (design §9 thirds) ==")
thirds = [("T1 2022-09-14..11-09", "2022-09-14", "2022-11-09"),
          ("T2 2022-11-09..2023-01-04", "2022-11-09", "2023-01-04"),
          ("T3 2023-01-04..03-01", "2023-01-04", "2023-03-01")]
for name, lo, hi in thirds:
    inn = high.filter((pl.col("trade_day") >= pl.lit(lo).str.to_date()) &
                      (pl.col("trade_day") < pl.lit(hi).str.to_date()))
    out_ = high.filter(~((pl.col("trade_day") >= pl.lit(lo).str.to_date()) &
                         (pl.col("trade_day") < pl.lit(hi).str.to_date())))
    print(f"  {name:26s} in: mean {inn['partial_net_2bps'].mean():8.2f} n={inn.height:4d} "
          f"| without it: mean {out_['partial_net_2bps'].mean():8.2f} n={out_.height:4d}")

print("\n== dependence structure ==")
print(f"  events {high.height}, unique dates {high['trade_day'].n_unique()}, "
      f"unique weeks {high['utc_week'].n_unique()}")
clusters = high.group_by("entry_ts").len().rename({"len": "k"})
print("  same-timestamp cluster sizes:",
      clusters.group_by("k").len().sort("k").to_dicts())
per_date = high.group_by("trade_day").agg(pl.col("partial_net_2bps").mean().alias("m"))
print(f"  date-level mean of means: {per_date['m'].mean():.2f} bps over {per_date.height} dates")

print("\n== the 4 events with no 4h outcome ==")
miss = a.filter(~pl.col("4h_available"))
print(miss.select("symbol", "trade_day", "vol_tercile", "outcome_unavailable_reason").to_dicts())
