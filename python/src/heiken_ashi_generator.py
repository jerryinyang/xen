from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl


HA_COLUMNS = [
    "OpenTime",
    "CloseTime",
    "HAOpen",
    "HAHigh",
    "HALow",
    "HAClose",
    "RealOpen",
    "RealHigh",
    "RealLow",
    "RealClose",
    "Direction",
    "SourceCount",
]


@dataclass
class HeikenAshiGenerator:
    """Stateful Heiken Ashi generator for completed source bars."""

    previous_ha_open: float | None = None
    previous_ha_close: float | None = None

    def update(
        self,
        open_time: Any,
        close_time: Any,
        real_open: float,
        real_high: float,
        real_low: float,
        real_close: float,
    ) -> dict[str, Any]:
        ha_close = (real_open + real_high + real_low + real_close) / 4.0

        if self.previous_ha_open is None or self.previous_ha_close is None:
            ha_open = (real_open + real_close) / 2.0
        else:
            ha_open = (self.previous_ha_open + self.previous_ha_close) / 2.0

        ha_high = max(real_high, ha_open, ha_close)
        ha_low = min(real_low, ha_open, ha_close)

        self.previous_ha_open = ha_open
        self.previous_ha_close = ha_close

        return {
            "OpenTime": open_time,
            "CloseTime": close_time,
            "HAOpen": ha_open,
            "HAHigh": ha_high,
            "HALow": ha_low,
            "HAClose": ha_close,
            "RealOpen": real_open,
            "RealHigh": real_high,
            "RealLow": real_low,
            "RealClose": real_close,
            "Direction": 1 if ha_close >= ha_open else -1,
            "SourceCount": 1,
        }


def generate_heiken_ashi(time_bars: pl.DataFrame) -> pl.DataFrame:
    """Generate Heiken Ashi candles from completed time bars."""
    _validate_time_bars(time_bars)
    generator = HeikenAshiGenerator()
    source_rows = time_bars.select(
        ["OpenTime", "CloseTime", "Open", "High", "Low", "Close"]
    )
    rows = [
        generator.update(
            open_time,
            close_time,
            float(open_price),
            float(high),
            float(low),
            float(close),
        )
        for open_time, close_time, open_price, high, low, close in source_rows.iter_rows()
    ]
    return _frame(rows, HA_COLUMNS)


def _validate_time_bars(time_bars: pl.DataFrame) -> None:
    required = {"OpenTime", "CloseTime", "Open", "High", "Low", "Close"}
    missing = required.difference(time_bars.columns)
    if missing:
        raise ValueError(f"Missing required time-bar columns: {sorted(missing)}")


def _frame(rows: list[dict[str, Any]], columns: list[str]) -> pl.DataFrame:
    if not rows:
        return pl.DataFrame({column: [] for column in columns})
    return pl.DataFrame(rows).select(columns).with_columns(pl.col("Direction").cast(pl.Int32), pl.col("SourceCount").cast(pl.Int32))
