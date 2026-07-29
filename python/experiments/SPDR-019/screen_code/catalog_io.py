"""Fenced catalog reads + clock aggregation (TRAIN-only, design §10).

Mirrors SPDR-015/014 catalog_io so aggregation is identical. Never queries past TRAIN end
or the global holdout.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow.parquet as pq

from xen.nautilus.catalog_fence import (
    FenceManifest,
    assert_within_fence,
    load_fence_manifest,
)

from config import (
    BAR_TYPE_SUFFIX,
    CATALOG_BAR_DIR,
    CLOCKS,
    CONFIRM_END,
    DESIGN_START,
    HOLDOUT_START_NS,
    NS,
    TRAIN_END_NS,
)

FIXED_POINT_SCALE = 1e16
_TWO64 = float(2**64)
_OHLCV = ("open", "high", "low", "close", "volume")


def symbol_dir(symbol: str) -> Path:
    return CATALOG_BAR_DIR / f"{symbol}{BAR_TYPE_SUFFIX}"


def _decode_i128(arr) -> np.ndarray:
    buf = np.frombuffer(arr.buffers()[1], dtype=np.uint64)
    n = len(arr)
    off = arr.offset * 2
    lo = buf[off : off + 2 * n : 2].astype(np.float64)
    hi = buf[off + 1 : off + 2 * n : 2].astype(np.float64)
    return (lo + hi * _TWO64) / FIXED_POINT_SCALE


def load_minute_bars(
    symbol: str,
    start: datetime,
    end: datetime,
    *,
    band: str = "TRAIN",
    manifest: FenceManifest | None = None,
) -> pl.DataFrame:
    """Fenced 1m OHLCV for ``symbol`` on ``[start, end)``. TRAIN only."""
    m = manifest or load_fence_manifest()
    assert_within_fence(m, start, end, band=band)
    end_ns = int(end.timestamp() * NS)
    if end_ns > TRAIN_END_NS:
        raise AssertionError(f"query end {end} past TRAIN fence")
    if end_ns > HOLDOUT_START_NS:
        raise AssertionError("query approaches global holdout")

    d = symbol_dir(symbol)
    schema = {
        "ts_event": pl.Int64,
        "open": pl.Float64, "high": pl.Float64, "low": pl.Float64,
        "close": pl.Float64, "volume": pl.Float64,
    }
    if not d.exists():
        return pl.DataFrame(schema=schema)

    start_ns = int(start.timestamp() * NS)
    frames: list[pl.DataFrame] = []
    for f in sorted(d.glob("*.parquet")):
        tbl = pq.read_table(f, columns=["ts_event", *_OHLCV])
        if tbl.num_rows == 0:
            continue
        ts = tbl.column("ts_event").combine_chunks().to_numpy().astype(np.int64)
        keep = (ts >= start_ns) & (ts < end_ns)
        if not keep.any():
            continue
        cols = {"ts_event": ts[keep]}
        for name in _OHLCV:
            cols[name] = _decode_i128(tbl.column(name).combine_chunks())[keep]
        frames.append(pl.DataFrame(cols, schema=schema))

    if not frames:
        return pl.DataFrame(schema=schema)
    out = pl.concat(frames).sort("ts_event")
    if out.height:
        assert int(out["ts_event"].min()) >= start_ns
        assert int(out["ts_event"].max()) < end_ns
        assert int(out["ts_event"].max()) < TRAIN_END_NS
        assert int(out["ts_event"].max()) < HOLDOUT_START_NS
    return out


def load_train_minutes(symbol: str, *, manifest: FenceManifest | None = None) -> pl.DataFrame:
    return load_minute_bars(symbol, DESIGN_START, CONFIRM_END, band="TRAIN", manifest=manifest)


def aggregate_clock(minutes: pl.DataFrame, clock: str) -> pl.DataFrame:
    """Aggregate fenced 1m bars to a clock bar frame (SPDR-015 definition)."""
    spec = CLOCKS[clock]
    schema = {
        "slot_start": pl.Int64, "slot_end": pl.Int64,
        "open": pl.Float64, "high": pl.Float64, "low": pl.Float64, "close": pl.Float64,
        "volume": pl.Float64, "n_minutes": pl.UInt32, "last_ts": pl.Int64,
        "complete": pl.Boolean,
    }
    if minutes.height == 0:
        return pl.DataFrame(schema=schema)

    span_ns = spec["minutes"] * 60 * NS
    df = minutes.with_columns(
        ((pl.col("ts_event") - 60 * NS) // span_ns * span_ns).alias("slot_start")
    )
    agg = (
        df.group_by("slot_start")
        .agg(
            pl.col("open").sort_by("ts_event").first().alias("open"),
            pl.col("high").max().alias("high"),
            pl.col("low").min().alias("low"),
            pl.col("close").sort_by("ts_event").last().alias("close"),
            pl.col("volume").sum().alias("volume"),
            pl.len().cast(pl.UInt32).alias("n_minutes"),
            pl.col("ts_event").max().alias("last_ts"),
        )
        .sort("slot_start")
        .with_columns((pl.col("slot_start") + span_ns).alias("slot_end"))
    )
    agg = agg.with_columns(
        (
            (pl.col("last_ts") == pl.col("slot_end"))
            & (pl.col("n_minutes") >= spec["min_minutes"])
        ).alias("complete")
    )
    return agg.select(list(schema.keys()))


def minutes_to_arrays(minutes: pl.DataFrame) -> dict[str, np.ndarray]:
    """M1 arrays for fill resolution — one load per symbol, shared across variants."""
    if minutes.height == 0:
        return {
            "ts": np.empty(0, dtype=np.int64),
            "open": np.empty(0, dtype=float),
            "high": np.empty(0, dtype=float),
            "low": np.empty(0, dtype=float),
            "close": np.empty(0, dtype=float),
        }
    return {
        "ts": minutes["ts_event"].to_numpy().astype(np.int64),
        "open": minutes["open"].to_numpy().astype(float),
        "high": minutes["high"].to_numpy().astype(float),
        "low": minutes["low"].to_numpy().astype(float),
        "close": minutes["close"].to_numpy().astype(float),
    }
