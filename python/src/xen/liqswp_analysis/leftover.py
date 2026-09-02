"""Attach a confirmation-set leftover to every eligible raid on the frozen emission."""

from __future__ import annotations

import polars as pl

SWING_COLUMNS = (
    "swing_price",
    "swing_bps",
    "swing_atr",
    "swing_duration_ns",
    "duration_ns",
    "strong_move",
)
PRIMARY_COPIED_COLUMNS = (
    *SWING_COLUMNS,
    "confirmation_ts_ns",
    "endpoint_ts_ns",
    "confirmation_method",
    "confirmation_reference",
)


def attach_shared_leftover(frame: pl.DataFrame) -> pl.DataFrame:
    """Copy the primary leftover onto CONFIRMED_NON_PRIMARY raids in the same set.

    A set is (source_cell, side, confirmation time). Non-primary rows store that
    confirmation time on endpoint_ts_ns. Each raid keeps its own first push;
    strong_move is recomputed as leftover ATR > own max_excursion_atr.
    """
    if "status" not in frame.columns:
        return frame
    if frame.filter(pl.col("status") == "CONFIRMED_NON_PRIMARY").is_empty():
        return frame
    if "source_cell" not in frame.columns:
        raise ValueError("source_cell is required to attach leftovers without mixing cells")

    keys = ["source_cell", "side"]
    copied = [column for column in PRIMARY_COPIED_COLUMNS if column in frame.columns]
    primaries = frame.filter(
        (pl.col("status") == "COMPLETED")
        & pl.col("primary_attribution").fill_null(False)
        & pl.col("primary_completed").fill_null(False)
        & pl.col("confirmation_ts_ns").is_not_null()
        & pl.col("swing_atr").is_not_null()
    )
    donor = primaries.select(
        *keys,
        pl.col("confirmation_ts_ns").alias("set_ts_ns"),
        *[pl.col(column).alias(f"__donor_{column}") for column in copied],
    )
    others = frame.filter(pl.col("status") != "CONFIRMED_NON_PRIMARY")
    non_primary = frame.filter(pl.col("status") == "CONFIRMED_NON_PRIMARY").join(
        donor,
        left_on=[*keys, "endpoint_ts_ns"],
        right_on=[*keys, "set_ts_ns"],
        how="left",
    )
    attached = non_primary
    for column in copied:
        donor_name = f"__donor_{column}"
        attached = attached.with_columns(
            pl.coalesce([pl.col(donor_name), pl.col(column)]).alias(column)
        )
    attached = attached.drop([f"__donor_{column}" for column in copied])
    if {"swing_atr", "max_excursion_atr"} <= set(attached.columns):
        attached = attached.with_columns(
            pl.when(
                pl.col("swing_atr").is_finite() & pl.col("max_excursion_atr").is_finite()
            )
            .then(pl.col("swing_atr") > pl.col("max_excursion_atr"))
            .otherwise(pl.col("strong_move"))
            .alias("strong_move")
        )
    return pl.concat([others, attached], how="diagonal_relaxed")
