"""Fenced vectorised catalog reads + clock aggregation (design §3.1, §7.1-§7.2).

The SPDR lane runs vectorised Python on the fenced catalog (design §0). Bar-read
windows are validated against the INFR-011 A6 hash-pinned fence manifest through
``xen.nautilus.catalog_fence`` before any parquet touch, and every returned frame is
hard-filtered to the requested window. HOLDOUT is unreachable by construction: the
maximum admissible upper bound in this screen is ``train_end_utc``.

Catalog storage note: Nautilus 1.230 writes OHLCV as ``fixed_size_binary[16]`` little-endian
i128 raw fixed-point with scale 1e16 (verified against BTCUSDT 2022-07-15 closes).
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


# ------------------------------------------------------------------ io ----


def symbol_dir(symbol: str) -> Path:
    return CATALOG_BAR_DIR / f"{symbol}{BAR_TYPE_SUFFIX}"


def available_symbols() -> list[str]:
    out = []
    for p in sorted(CATALOG_BAR_DIR.iterdir()):
        if p.is_dir() and p.name.endswith(BAR_TYPE_SUFFIX):
            out.append(p.name[: -len(BAR_TYPE_SUFFIX)])
    return out


def _decode_i128(arr) -> np.ndarray:
    """Decode a ``fixed_size_binary[16]`` column to float64 real units.

    Values are non-negative price/quantity raws; float64 carries ~16 significant digits,
    so the relative decode error is ~1e-16 — far below any reported precision.
    """
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
    """Fenced 1m OHLCV for ``symbol`` on ``[start, end)``.

    Parameters
    ----------
    symbol : str
        Bybit USDT perp symbol, e.g. ``"BTCUSDT"``.
    start, end : datetime
        UTC bounds; ``end`` exclusive. Validated against the pinned fence manifest.
    band : str
        Sanctioned band — ``"TRAIN"`` only for this screen.
    manifest : FenceManifest | None
        Pre-loaded manifest (avoids re-hashing per symbol).

    Returns
    -------
    pl.DataFrame
        Columns ``ts_event`` (Int64 ns, bar close), ``open``/``high``/``low``/``close``/
        ``volume`` (Float64). Empty frame with the same schema when the symbol has no
        catalog data inside the window.
    """
    m = manifest or load_fence_manifest()
    assert_within_fence(m, start, end, band=band)

    d = symbol_dir(symbol)
    schema = {
        "ts_event": pl.Int64,
        "open": pl.Float64,
        "high": pl.Float64,
        "low": pl.Float64,
        "close": pl.Float64,
        "volume": pl.Float64,
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
    # §7.1/§7.2 belt-and-braces: no row may sit outside the requested fenced window.
    if out.height:
        assert int(out["ts_event"].min()) >= start_ns, f"{symbol}: row before fence start"
        assert int(out["ts_event"].max()) < end_ns, f"{symbol}: row at/after fence end"
    return out


# ------------------------------------------------------------- clocks ----


def aggregate_clock(minutes: pl.DataFrame, clock: str) -> pl.DataFrame:
    """Aggregate fenced 1m bars to a clock bar frame (design §3.1).

    ``open_ts = ts_event - 1m``; slots are ``open_ts.truncate(clock)``. A bar is
    ``complete`` only when its last print lands exactly on ``slot_end`` and minute
    coverage clears the per-clock floor. Incomplete bars are RETAINED (counted) and
    excluded from forecasts downstream.

    Parameters
    ----------
    minutes : pl.DataFrame
        Output of :func:`load_minute_bars`.
    clock : str
        ``"H1"`` or ``"M15"``.

    Returns
    -------
    pl.DataFrame
        One row per clock slot: ``slot_start``, ``slot_end``, OHLC, ``volume``,
        ``n_minutes``, ``last_ts``, ``complete``.
    """
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
