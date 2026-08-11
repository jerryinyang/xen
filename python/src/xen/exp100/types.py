"""Small immutable records passed between EXP-100 streaming components."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BarRecord:
    """A completed OHLCV bar and its source-bar count."""

    ts_event_ns: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    source_bars: int
