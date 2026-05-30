"""Deterministic OHLC resampling from 1-minute time bars.

Used by the Phase 004A pre-phase experiments (EXP-029, EXP-030, EXP-031) to
produce synthetic 15-minute (or any N-minute) bars from 1-minute base bars.

The aggregation is clock-aligned: 15-minute windows start at minute boundaries
divisible by 15 (00, 15, 30, 45). Partial trailing windows that do not contain
a full N 1-minute bars are dropped. The aggregator is a pure function: identical
input plus identical period produces identical output.

This module is deliberately scope-narrow and stateless. Holdout exclusion must
already have been applied to the 1-minute input before aggregation; this module
does not enforce or check that — callers are responsible.
"""
from __future__ import annotations

import math

import polars as pl


SECONDS_PER_MINUTE = 60


def aggregate_ohlc(
    bars_1m: pl.DataFrame,
    period_minutes: int = 15,
    min_coverage: float | None = None,
) -> pl.DataFrame:
    """Resample 1-minute OHLC bars to N-minute clock-aligned OHLC bars.

    Aggregation rule per N-minute window:
        Open       = first 1-minute Open
        High       = max 1-minute High
        Low        = min 1-minute Low
        Close      = last 1-minute Close
        TickVolume = sum 1-minute TickVolume (when present)

    The window boundary is set by truncating each bar's `CloseTime` to the
    period grid. Window retention is governed by ``min_coverage``:

    - ``min_coverage is None`` (default): a window is retained only when it
      contains exactly ``period_minutes`` 1-minute bars. This is the original,
      strict behavior and is preserved bit-for-bit for callers that do not pass
      the argument (EXP-029/030/031/033).
    - ``0 < min_coverage <= 1``: a window is retained when it contains at least
      ``ceil(min_coverage * period_minutes)`` 1-minute bars. This tolerant mode
      keeps substantially-complete windows that the strict rule would drop
      around session gaps and low-liquidity periods. Partial windows have
      understated High/Low; callers must account for the coverage/feature
      trade-off (see EXP-034 §"Coverage feature-interaction stability").

    Partial windows at the tail that fall below the retention threshold are
    dropped in both modes.

    Parameters
    ----------
    bars_1m : pl.DataFrame
        1-minute time bars. Must include the columns `Symbol`, `OpenTime`,
        `CloseTime`, `Open`, `High`, `Low`, `Close`. `TickVolume` is optional
        and is summed when present.
    period_minutes : int, default 15
        Number of source minutes per aggregated bar. Must be at least 2.
    min_coverage : float or None, default None
        Minimum source-bar coverage fraction for window retention. ``None``
        means exactly ``period_minutes`` bars (strict). A value in ``(0, 1]``
        retains windows with at least ``ceil(min_coverage * period_minutes)``
        bars.

    Returns
    -------
    pl.DataFrame
        Aggregated OHLC frame sorted by `CloseTime`. Columns:
        `Symbol`, `OpenTime`, `CloseTime`, `Open`, `High`, `Low`, `Close`,
        `TickVolume` (if `TickVolume` was present in input), `SourceBars`.
    """
    if period_minutes < 2:
        raise ValueError(f"period_minutes must be >= 2, got {period_minutes}")
    if min_coverage is not None and not (0.0 < min_coverage <= 1.0):
        raise ValueError(
            f"min_coverage must be in (0, 1] or None, got {min_coverage}"
        )
    if bars_1m.is_empty():
        return bars_1m.clear()

    required = {"Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close"}
    missing = required - set(bars_1m.columns)
    if missing:
        raise ValueError(f"bars_1m is missing required columns: {sorted(missing)}")

    has_volume = "TickVolume" in bars_1m.columns

    period_seconds = period_minutes * SECONDS_PER_MINUTE
    sorted_bars = bars_1m.sort("CloseTime")

    bucketed = sorted_bars.with_columns(
        (
            (pl.col("CloseTime").dt.epoch("s") - 1) // period_seconds
        ).alias("_Bucket")
    )

    agg_exprs = [
        pl.first("Symbol").alias("Symbol"),
        pl.first("OpenTime").alias("OpenTime"),
        pl.last("CloseTime").alias("CloseTime"),
        pl.first("Open").alias("Open"),
        pl.max("High").alias("High"),
        pl.min("Low").alias("Low"),
        pl.last("Close").alias("Close"),
        pl.len().alias("SourceBars"),
    ]
    if has_volume:
        agg_exprs.append(pl.sum("TickVolume").alias("TickVolume"))

    if min_coverage is None:
        retained = pl.col("SourceBars") == period_minutes
    else:
        min_bars = max(2, math.ceil(min_coverage * period_minutes))
        retained = pl.col("SourceBars") >= min_bars

    aggregated = (
        bucketed.group_by("_Bucket")
        .agg(agg_exprs)
        .filter(retained)
        .drop("_Bucket")
        .sort("CloseTime")
    )

    output_cols = ["Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close"]
    if has_volume:
        output_cols.append("TickVolume")
    output_cols.append("SourceBars")
    return aggregated.select(output_cols)


def coverage_summary(
    bars_1m: pl.DataFrame,
    aggregated: pl.DataFrame,
    period_minutes: int = 15,
) -> dict[str, int]:
    """Return source/aggregated bar counts for diagnostic reporting.

    Parameters
    ----------
    bars_1m : pl.DataFrame
        The 1-minute input frame that was aggregated.
    aggregated : pl.DataFrame
        The output of :func:`aggregate_ohlc` for the same input.
    period_minutes : int, default 15
        The aggregation period used.

    Returns
    -------
    dict[str, int]
        `source_bars_in`, `aggregated_bars_out`, `expected_full_windows`,
        `dropped_partial_window_bars`.
    """
    source_rows = int(bars_1m.height)
    agg_rows = int(aggregated.height)
    expected = source_rows // period_minutes
    dropped_bars = source_rows - agg_rows * period_minutes
    return {
        "source_bars_in": source_rows,
        "aggregated_bars_out": agg_rows,
        "expected_full_windows": expected,
        "dropped_partial_window_bars": dropped_bars,
    }
