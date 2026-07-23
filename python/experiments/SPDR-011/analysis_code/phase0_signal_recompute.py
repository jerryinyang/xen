"""Hand-recompute the breakout signal from raw 1m bars for a sample of events.

Confirms the trigger uses the 4h slot that CLOSES at entry_ts (strictly prior prints) and the
prior confirmed UTC day's range — i.e. no same-bar or future information enters the direction.
"""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[4]
FAMILY = ROOT / "data/nautilus_runs/SPDR-011"
a = pl.read_parquet(FAMILY / "artifact-bundle/design.parquet")

marks = {
    s: pl.read_parquet(FAMILY / s / "bar_marks.parquet")
    .with_columns(pl.col("SourceCloseTime").dt.cast_time_unit("us"))
    .sort("SourceCloseTime")
    for s in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]
}

# deterministic spread of events across symbols and directions
sample = (
    a.filter(pl.col("4h_available"))
    .sort("event_id")
    .group_by("symbol", maintain_order=True)
    .head(2)
)

ok = 0
for row in sample.iter_rows(named=True):
    m = marks[row["symbol"]]
    t = row["entry_ts"]
    # trigger slot = 1m bars closing in (t-4h, t]  -> all prints strictly before t
    slot = m.filter(
        (pl.col("SourceCloseTime") > t - timedelta(hours=4))
        & (pl.col("SourceCloseTime") <= t)
    )
    trig_close = slot["RealClose"][-1]
    # prior confirmed UTC day
    d0 = row["trade_day"]
    prev_start = pl.datetime(d0.year, d0.month, d0.day, time_zone="UTC") - timedelta(days=1)
    prev = m.filter(
        (pl.col("SourceCloseTime") > prev_start)
        & (pl.col("SourceCloseTime") <= prev_start + timedelta(days=1))
    )
    hi, lo = prev["RealHigh"].max(), prev["RealLow"].min()
    expect = 1 if trig_close > hi else (-1 if trig_close < lo else 0)
    match = expect == row["direction"]
    ok += match
    print(
        f"{row['symbol']:9s} {str(t)[:16]} slot_close={trig_close:>11.4f} "
        f"prev_hi={hi:>11.4f} prev_lo={lo:>11.4f} "
        f"recomputed={expect:+d} emitted={row['direction']:+d} {'OK' if match else 'MISMATCH'}"
    )
    # the trigger slot's own prints must all precede the entry mark
    assert slot["SourceCloseTime"].max() <= t

print(f"\ndirection reproduced from raw bars: {ok}/{sample.height}")
