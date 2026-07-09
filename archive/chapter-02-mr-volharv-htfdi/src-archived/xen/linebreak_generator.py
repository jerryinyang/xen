from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import polars as pl


LINEBREAK_COLUMNS = [
    "OpenTime",
    "CloseTime",
    "Open",
    "High",
    "Low",
    "Close",
    "Direction",
    "Level",
    "SourceCount",
    "SourceCloseTime",
]


@dataclass
class LineBreakGenerator:
    """Stateful Line Break generator using completed source closes only."""

    level: int = 3
    lines: list[dict[str, Any]] = field(default_factory=list)
    pending_count: int = 0

    def __post_init__(self) -> None:
        if self.level < 1:
            raise ValueError("level must be >= 1")

    def update(
        self,
        open_time: Any,
        close_time: Any,
        open_price: float,
        close: float,
    ) -> list[dict[str, Any]]:
        self.pending_count += 1

        if not self.lines:
            return [
                self._append_line(
                    open_time,
                    close_time,
                    close,
                    close,
                    1 if close >= open_price else -1,
                )
            ]

        last = self.lines[-1]
        direction = int(last["Direction"])

        if direction >= 0 and close > float(last["Close"]):
            return [
                self._append_line(
                    open_time,
                    close_time,
                    float(last["Close"]),
                    close,
                    1,
                )
            ]
        if direction <= 0 and close < float(last["Close"]):
            return [
                self._append_line(
                    open_time,
                    close_time,
                    float(last["Close"]),
                    close,
                    -1,
                )
            ]

        reversal_window = self.lines[-self.level :]
        reversal_high = max(float(line["High"]) for line in reversal_window)
        reversal_low = min(float(line["Low"]) for line in reversal_window)

        if close > reversal_high:
            return [
                self._append_line(
                    open_time,
                    close_time,
                    float(last["Close"]),
                    close,
                    1,
                )
            ]
        if close < reversal_low:
            return [
                self._append_line(
                    open_time,
                    close_time,
                    float(last["Close"]),
                    close,
                    -1,
                )
            ]

        return []

    def _append_line(
        self,
        open_time: Any,
        close_time: Any,
        open_price: float,
        close_price: float,
        direction: int,
    ) -> dict[str, Any]:
        line = {
            "OpenTime": open_time,
            "CloseTime": close_time,
            "Open": open_price,
            "High": max(open_price, close_price),
            "Low": min(open_price, close_price),
            "Close": close_price,
            "Direction": direction,
            "Level": self.level,
            "SourceCount": self.pending_count,
            "SourceCloseTime": close_time,
        }
        self.lines.append(line)
        self.pending_count = 0
        return line


def generate_linebreak(time_bars: pl.DataFrame, level: int = 3) -> pl.DataFrame:
    """Generate confirmed Line Break bars from completed time bars.

    ``time_bars`` must be sorted by ``CloseTime`` (non-decreasing); the generator
    is sequential and does not reorder input. Unsorted input raises ``ValueError``.
    """
    _validate_time_bars(time_bars)
    generator = LineBreakGenerator(level=level)
    rows: list[dict[str, Any]] = []
    source_rows = time_bars.select(
        ["OpenTime", "CloseTime", "Open", "Close"]
    )
    for open_time, close_time, open_price, close_price in source_rows.iter_rows():
        rows.extend(
            generator.update(
                open_time,
                close_time,
                float(open_price),
                float(close_price),
            )
        )
    return _frame(rows, LINEBREAK_COLUMNS)


def _validate_time_bars(time_bars: pl.DataFrame) -> None:
    required = {"OpenTime", "CloseTime", "Open", "High", "Low", "Close"}
    missing = required.difference(time_bars.columns)
    if missing:
        raise ValueError(f"Missing required time-bar columns: {sorted(missing)}")
    if not time_bars.get_column("CloseTime").is_sorted():
        raise ValueError(
            "time_bars must be sorted by CloseTime (non-decreasing) before generation; "
            "the generator is sequential and does not reorder input."
        )


def _frame(rows: list[dict[str, Any]], columns: list[str]) -> pl.DataFrame:
    if not rows:
        return pl.DataFrame({column: [] for column in columns})
    return pl.DataFrame(rows).select(columns).with_columns(
        pl.col("Direction").cast(pl.Int32),
        pl.col("Level").cast(pl.Int32),
        pl.col("SourceCount").cast(pl.Int32),
    )
