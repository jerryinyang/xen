from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

import polars as pl


RENKO_COLUMNS = [
    "OpenTime",
    "CloseTime",
    "Open",
    "High",
    "Low",
    "Close",
    "Direction",
    "BrickSize",
    "ATRPeriod",
    "SourceCount",
    "SourceCloseTime",
]


@dataclass
class RenkoGenerator:
    """Stateful close-based ATR Renko generator for completed source bars."""

    atr_period: int = 14
    anchor_close: float | None = None
    previous_close: float | None = None
    true_ranges: deque[float] = field(default_factory=deque)
    pending_count: int = 0

    def __post_init__(self) -> None:
        if self.atr_period < 1:
            raise ValueError("atr_period must be >= 1")

    def update(self, row: dict[str, Any]) -> list[dict[str, Any]]:
        close = float(row["Close"])
        high = float(row["High"])
        low = float(row["Low"])
        self.pending_count += 1

        if self.anchor_close is None:
            self.anchor_close = close

        true_range = self._true_range(high, low)
        self.true_ranges.append(true_range)
        if len(self.true_ranges) > self.atr_period:
            self.true_ranges.popleft()
        self.previous_close = close

        if len(self.true_ranges) < self.atr_period:
            return []

        brick_size = sum(self.true_ranges) / self.atr_period
        if brick_size <= 0:
            return []

        rows: list[dict[str, Any]] = []
        while self.anchor_close is not None and close >= self.anchor_close + brick_size:
            rows.append(self._append_brick(row, self.anchor_close, self.anchor_close + brick_size, brick_size, 1))
        while self.anchor_close is not None and close <= self.anchor_close - brick_size:
            rows.append(self._append_brick(row, self.anchor_close, self.anchor_close - brick_size, brick_size, -1))
        return rows

    def _true_range(self, high: float, low: float) -> float:
        if self.previous_close is None:
            return high - low
        return max(high - low, abs(high - self.previous_close), abs(low - self.previous_close))

    def _append_brick(
        self,
        row: dict[str, Any],
        open_price: float,
        close_price: float,
        brick_size: float,
        direction: int,
    ) -> dict[str, Any]:
        brick = {
            "OpenTime": row["OpenTime"],
            "CloseTime": row["CloseTime"],
            "Open": open_price,
            "High": max(open_price, close_price),
            "Low": min(open_price, close_price),
            "Close": close_price,
            "Direction": direction,
            "BrickSize": brick_size,
            "ATRPeriod": self.atr_period,
            "SourceCount": self.pending_count,
            "SourceCloseTime": row["CloseTime"],
        }
        self.anchor_close = close_price
        self.pending_count = 0
        return brick


def generate_renko(time_bars: pl.DataFrame, atr_period: int = 14) -> pl.DataFrame:
    """Generate close-based ATR Renko bricks from completed time bars."""
    _validate_time_bars(time_bars)
    generator = RenkoGenerator(atr_period=atr_period)
    rows: list[dict[str, Any]] = []
    for row in time_bars.sort("CloseTime").iter_rows(named=True):
        rows.extend(generator.update(row))
    return _frame(rows, RENKO_COLUMNS)


def _validate_time_bars(time_bars: pl.DataFrame) -> None:
    required = {"OpenTime", "CloseTime", "Open", "High", "Low", "Close"}
    missing = required.difference(time_bars.columns)
    if missing:
        raise ValueError(f"Missing required time-bar columns: {sorted(missing)}")


def _frame(rows: list[dict[str, Any]], columns: list[str]) -> pl.DataFrame:
    if not rows:
        return pl.DataFrame({column: [] for column in columns})
    return pl.DataFrame(rows).select(columns).with_columns(
        pl.col("Direction").cast(pl.Int32),
        pl.col("ATRPeriod").cast(pl.Int32),
        pl.col("SourceCount").cast(pl.Int32),
    )
