from __future__ import annotations

import polars as pl


TIMESTAMP_COLUMN_NAMES = {
    "CloseTime",
    "OpenTime",
    "SourceCloseTime",
    "ReversalTime",
    "timestamp",
    "timestamp_backward",
    "timestamp_forward",
}


def normalize_timestamp_columns(
    df: pl.DataFrame,
    columns: list[str] | tuple[str, ...],
) -> pl.DataFrame:
    """Normalize timestamp columns used for joins to microsecond datetimes."""
    casts: list[pl.Expr] = []
    for column in columns:
        if column not in df.columns:
            continue
        dtype = df.schema[column]
        if column in TIMESTAMP_COLUMN_NAMES or isinstance(
            dtype, (pl.Datetime, pl.Date)
        ):
            casts.append(pl.col(column).cast(pl.Datetime("us")))
    if not casts:
        return df
    return df.with_columns(casts)
