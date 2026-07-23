"""Q4: rebuild the L1 net column from canonical xen.evaluation cost functions."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl

from xen.evaluation import (
    bybit_round_trip_cost_bps,
    count_bybit_funding_stamps,
    verify_chapter05_spread_quarantine,
)

ROOT = Path(__file__).resolve().parents[4]
a = pl.read_parquet(ROOT / "data/nautilus_runs/SPDR-011/artifact-bundle/design.parquet")

print("spread quarantine:", verify_chapter05_spread_quarantine())

d = a.filter(pl.col("4h_available"))
rows = d.select(
    "event_id", "symbol", "entry_ts", "exit_ts", "entry_open", "funding_stamps",
    "fee_rt_bps", "funding_rt_bps", "total_bps", "liquidity",
    "gross_signed_4h_bps", "partial_net_0bps", "partial_net_2bps", "partial_net_5bps",
).to_dicts()

bad_stamps = bad_cost = bad_net = 0
worst_cost = worst_net = 0.0
for r in rows:
    stamps = count_bybit_funding_stamps(r["entry_ts"], r["exit_ts"])
    if stamps != r["funding_stamps"]:
        bad_stamps += 1
    rt = bybit_round_trip_cost_bps(
        r["symbol"], entry_price=r["entry_open"], liquidity=r["liquidity"],
        funding_bps_per_8h=1.0, funding_stamps=stamps,
    )
    total = rt["total_bps"] if isinstance(rt, dict) else rt.total_bps
    worst_cost = max(worst_cost, abs(total - r["total_bps"]))
    if abs(total - r["total_bps"]) > 1e-9:
        bad_cost += 1
    for allow, col in ((0.0, "partial_net_0bps"), (2.0, "partial_net_2bps"), (5.0, "partial_net_5bps")):
        expect = r["gross_signed_4h_bps"] - total - allow
        worst_net = max(worst_net, abs(expect - r[col]))
        if abs(expect - r[col]) > 1e-9:
            bad_net += 1

print(f"n legs checked                 : {len(rows)}")
print(f"funding-stamp mismatches       : {bad_stamps}")
print(f"round-trip cost mismatches     : {bad_cost}  (max abs diff {worst_cost:.3e} bps)")
print(f"partial_net_{{0,2,5}} mismatches : {bad_net}  (max abs diff {worst_net:.3e} bps)")
print()
print("cost composition (bps):")
print(d.select(
    pl.col("fee_rt_bps").mean().alias("fee_rt_mean"),
    pl.col("funding_rt_bps").mean().alias("funding_rt_mean"),
    pl.col("total_bps").mean().alias("total_mean"),
    pl.col("total_bps").min().alias("total_min"),
    pl.col("total_bps").max().alias("total_max"),
    pl.col("funding_stamps").mean().alias("stamps_mean"),
).to_dicts()[0])
