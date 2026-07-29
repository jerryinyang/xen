"""Fenced vectorised catalog reads + clock aggregation (design §0).

TRAIN-only. Max upper bound = train_end_utc. Catalog fixed-point decode as SPDR-012/013.
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

from config import BAR_TYPE_SUFFIX, CATALOG_BAR_DIR, CLOCKS, NS

FIXED_POINT_SCALE = 1e16
_TWO64 = float(2**64)
_OHLCV = ("open", "high", "low", "close", "volume")


def symbol_dir(symbol: str) -> Path:
    return CATALOG_BAR_DIR / f"{symbol}{BAR_TYPE_SUFFIX}"


def available_symbols() -> list[str]:
    out = []
    for p in sorted(CATALOG_BAR_DIR.iterdir()):
        if p.is_dir() and p.name.endswith(BAR_TYPE_SUFFIX):
            out.append(p.name[: -len(BAR_TYPE_SUFFIX)])
    return out


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
    m = manifest or load_fence_manifest()
    assert_within_fence(m, start, end, band=band)

    d = symbol_dir(symbol)
    schema = {
        "ts_event": pl.Int64,
        "open": pl.Float64, "high": pl.Float64, "low": pl.Float64,
        "close": pl.Float64, "volume": pl.Float64,
    }
    if not d.exists():
        return pl.DataFrame(schema=schema)

    start_ns = int(start.timestamp() * NS)
    end_ns = int(end.timestamp() * NS)

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
    return out


def aggregate_clock(minutes: pl.DataFrame, clock: str) -> pl.DataFrame:
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
