"""Heiken Ashi harami detector (core signal of ``CF-HA-HARAMI-001``).

Computed on Heiken Ashi candles (see ``xen.heiken_ashi_generator``). Detection
is **independent** of the ZigZag trend substrate.

For adjacent HA candles ``HA_1`` (previous) and ``HA_0`` (latest), with
``BODY_MAX = max(HAOpen, HAClose)`` and ``BODY_MIN = min(HAOpen, HAClose)``, a
harami is::

    BODY_MAX_1 > BODY_MAX_0  AND  BODY_MIN_1 < BODY_MIN_0

i.e. the latest HA body is strictly inside the prior HA body. A degenerate prior
body (``BODY_MAX_1 == BODY_MIN_1``) yields no harami (the strict inequalities
cannot both hold).

**Construction-derived reduction.** Because the HA generator pins
``HAOpen_0 = (HAOpen_1 + HAClose_1) / 2`` — the exact centre of the prior body —
one endpoint of the latest body is engulfed by construction, so the harami
condition reduces to the single binding constraint
``BODY_MIN_1 < HAClose_0 < BODY_MAX_1``. The detector emits both the original
predicate result and ``ReducedOK`` so an experiment can verify they agree (a
disagreement flags an HA-generator/detector inconsistency).

The detection uses only the current and immediately prior HA candle, so the
one-row-shift vectorized form below is causally identical to a sequential pass
(no look-ahead). Output is computed on HA (synthetic) prices for *detection
only*; every outcome metric downstream is computed on real prices.
"""
from __future__ import annotations

import polars as pl


HARAMI_COLUMNS = [
    "HA1Time",
    "HA0Time",
    "HA1Direction",
    "HA0Direction",
    "PrevBodyMin",
    "PrevBodyMax",
    "BodyMin",
    "BodyMax",
    "HAClose0",
    "ReducedOK",
]


def detect_ha_harami(ha_candles: pl.DataFrame) -> pl.DataFrame:
    """Detect HA harami events from a Heiken Ashi candle frame.

    Parameters
    ----------
    ha_candles : pl.DataFrame
        Heiken Ashi candles with at least ``CloseTime``, ``HAOpen``,
        ``HAClose``, ``Direction``; sorted by ``CloseTime`` (non-decreasing).
        Unsorted input raises ``ValueError``.

    Returns
    -------
    pl.DataFrame
        One row per harami event (``HARAMI_COLUMNS``), ordered by ``HA0Time``.
        ``ReducedOK`` is the reduced-form predicate
        ``PrevBodyMin < HAClose0 < PrevBodyMax`` and must equal the original
        harami predicate on every row. Empty when no event is detected.
    """
    _validate_ha(ha_candles)
    if ha_candles.height < 2:
        return _empty_frame()

    framed = ha_candles.select(
        pl.col("CloseTime"),
        pl.col("Direction").cast(pl.Int32),
        pl.max_horizontal("HAOpen", "HAClose").alias("BodyMax"),
        pl.min_horizontal("HAOpen", "HAClose").alias("BodyMin"),
        pl.col("HAClose").alias("HAClose0"),
    ).with_columns(
        pl.col("CloseTime").shift(1).alias("HA1Time"),
        pl.col("Direction").shift(1).alias("HA1Direction"),
        pl.col("BodyMax").shift(1).alias("PrevBodyMax"),
        pl.col("BodyMin").shift(1).alias("PrevBodyMin"),
    )

    original = (pl.col("PrevBodyMax") > pl.col("BodyMax")) & (
        pl.col("PrevBodyMin") < pl.col("BodyMin")
    )
    reduced = (pl.col("PrevBodyMin") < pl.col("HAClose0")) & (
        pl.col("HAClose0") < pl.col("PrevBodyMax")
    )

    events = (
        framed.with_columns(
            original.alias("_Harami"),
            reduced.alias("ReducedOK"),
        )
        .filter(pl.col("_Harami") & pl.col("PrevBodyMax").is_not_null())
        .select(
            pl.col("HA1Time"),
            pl.col("CloseTime").alias("HA0Time"),
            pl.col("HA1Direction"),
            pl.col("Direction").alias("HA0Direction"),
            pl.col("PrevBodyMin"),
            pl.col("PrevBodyMax"),
            pl.col("BodyMin"),
            pl.col("BodyMax"),
            pl.col("HAClose0"),
            pl.col("ReducedOK"),
        )
        .sort("HA0Time")
    )
    return events


def _validate_ha(ha_candles: pl.DataFrame) -> None:
    required = {"CloseTime", "HAOpen", "HAClose", "Direction"}
    missing = required.difference(ha_candles.columns)
    if missing:
        raise ValueError(f"Missing required HA columns: {sorted(missing)}")
    if ha_candles.height and not ha_candles.get_column("CloseTime").is_sorted():
        raise ValueError(
            "ha_candles must be sorted by CloseTime (non-decreasing); "
            "the detector aligns each event to the immediately prior candle."
        )


def _empty_frame() -> pl.DataFrame:
    schema = {
        "HA1Time": pl.Datetime,
        "HA0Time": pl.Datetime,
        "HA1Direction": pl.Int32,
        "HA0Direction": pl.Int32,
        "PrevBodyMin": pl.Float64,
        "PrevBodyMax": pl.Float64,
        "BodyMin": pl.Float64,
        "BodyMax": pl.Float64,
        "HAClose0": pl.Float64,
        "ReducedOK": pl.Boolean,
    }
    return pl.DataFrame({name: [] for name in HARAMI_COLUMNS}, schema=schema)
