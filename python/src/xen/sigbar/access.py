"""Safe analytical access to the Chapter-04 mean-price-skew storage field."""
from __future__ import annotations

from pathlib import Path

import polars as pl

from xen.evaluation import load_chapter05_cost_pins

MEAN_PRICE_SKEW_COLUMN = "MeanPriceSkewBps"
MEAN_PRICE_SKEW_STATUS_COLUMN = "MeanPriceSkewStatus"
UNUSABLE_AS_SPREAD = "UNUSABLE_AS_SPREAD"
_STORAGE_COLUMNS = ("SpreadBps", "spread_feature")


def quarantine_mean_price_skew(
    frame: pl.DataFrame,
    *,
    column_pins_path: str | Path | None = None,
) -> pl.DataFrame:
    """Rename the storage field and attach its verified unusable-as-spread status."""
    present = [column for column in _STORAGE_COLUMNS if column in frame.columns]
    if len(present) != 1:
        raise ValueError(
            "expected exactly one mean-price-skew storage column "
            f"from {_STORAGE_COLUMNS}, found {present}"
        )
    if MEAN_PRICE_SKEW_COLUMN in frame.columns:
        raise ValueError(f"output column {MEAN_PRICE_SKEW_COLUMN!r} already exists")
    pins = load_chapter05_cost_pins(column_pins_path)
    if pins["stored_column_status"] != "UNUSABLE":
        raise ValueError("mean-price-skew storage field is not pinned UNUSABLE")
    return frame.rename({present[0]: MEAN_PRICE_SKEW_COLUMN}).with_columns(
        pl.lit(UNUSABLE_AS_SPREAD).alias(MEAN_PRICE_SKEW_STATUS_COLUMN)
    )
