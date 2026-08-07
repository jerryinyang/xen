"""L-29 anchor: entry/exit marks must be the first-minute RealOpen at the boundary, not the
trigger bar's own close. Verified against raw bar_marks, independent of experiment code."""
from __future__ import annotations

from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[4]
FAMILY = ROOT / "data/nautilus_runs/SPDR-011"
a = pl.read_parquet(FAMILY / "artifact-bundle/design.parquet")

marks = pl.concat(
    [
        pl.read_parquet(FAMILY / s / "bar_marks.parquet").with_columns(
            pl.lit(s).alias("symbol")
        )
        for s in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]
    ]
).select(
    "symbol",
    pl.col("SourceCloseTime").dt.cast_time_unit("us").alias("SourceCloseTime"),
    "RealOpen",
)

print("bar_marks rows:", marks.height)
print("trigger_ts == entry_ts on all rows:",
      a.filter(pl.col("trigger_ts") != pl.col("entry_ts")).height == 0)

# entry_open must equal RealOpen of the minute bar whose close is entry_ts + 1m
ent = (
    a.filter(pl.col("4h_available"))
    .select("event_id", "symbol", "entry_ts", "exit_ts", "entry_open", "open_4h")
    .with_columns(
        (pl.col("entry_ts") + pl.duration(minutes=1)).alias("SourceCloseTime")
    )
    .join(marks, on=["symbol", "SourceCloseTime"], how="left")
    .rename({"RealOpen": "mark_entry_open"})
)
miss = ent.filter(pl.col("mark_entry_open").is_null()).height
bad = ent.filter(
    (pl.col("mark_entry_open") - pl.col("entry_open")).abs() > 1e-9
).height
print(f"entry_open == first-minute RealOpen at entry_ts: mismatches={bad}, unmatched={miss}, n={ent.height}")

ex = (
    a.filter(pl.col("4h_available"))
    .select("event_id", "symbol", "exit_ts", "open_4h")
    .with_columns((pl.col("exit_ts") + pl.duration(minutes=1)).alias("SourceCloseTime"))
    .join(marks, on=["symbol", "SourceCloseTime"], how="left")
    .rename({"RealOpen": "mark_exit_open"})
)
miss_x = ex.filter(pl.col("mark_exit_open").is_null()).height
bad_x = ex.filter((pl.col("mark_exit_open") - pl.col("open_4h")).abs() > 1e-9).height
print(f"open_4h   == first-minute RealOpen at exit_ts:  mismatches={bad_x}, unmatched={miss_x}, n={ex.height}")

# outcome must be reconstructible from those two marks alone
chk = (
    a.filter(pl.col("4h_available"))
    .select("event_id", "direction", "entry_open", "open_4h", "gross_signed_4h_bps")
    .with_columns(
        (
            pl.col("direction")
            * (pl.col("open_4h") - pl.col("entry_open"))
            / pl.col("entry_open")
            * 1e4
        ).alias("recomputed")
    )
    .with_columns((pl.col("recomputed") - pl.col("gross_signed_4h_bps")).abs().alias("d"))
)
print(f"gross_signed_4h_bps recomputed from marks: max abs diff = {chk['d'].max():.3e}, n={chk.height}")
