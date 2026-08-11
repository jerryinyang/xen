"""Streaming OHLC aggregation and causal volatility features."""

from __future__ import annotations

import math
from collections import deque

from .types import BarRecord

MINUTE_NS = 60_000_000_000


class StreamingOHLC:
    """Aggregate complete, contiguous one-minute bars into fixed windows."""

    def __init__(self, period_minutes: int) -> None:
        if period_minutes <= 0:
            raise ValueError("period_minutes must be positive")
        self.period_minutes = period_minutes
        self._bucket_key: int | None = None
        self._last_minute: int | None = None
        self._source_bars = 0
        self._open = 0.0
        self._high = 0.0
        self._low = 0.0
        self._close = 0.0
        self._volume = 0.0
        self._synthetic_clock = False

    def update(self, one_minute_bar: BarRecord) -> BarRecord | None:
        minute = self._minute_index(one_minute_bar.ts_event_ns)
        bucket = minute // self.period_minutes
        if self._bucket_key is None:
            self._synthetic_clock = abs(one_minute_bar.ts_event_ns) < MINUTE_NS
            self._bucket_key = bucket
            self._last_minute = minute
            self._start(one_minute_bar)
            return None

        expected_minute = (self._last_minute or 0) + 1
        if minute != expected_minute or (not self._synthetic_clock and bucket != self._bucket_key):
            self._reset()
            self._bucket_key = bucket
            self._last_minute = minute
            self._start(one_minute_bar)
            return None

        self._last_minute = minute
        if self._synthetic_clock:
            bucket = self._bucket_key
        elif bucket != self._bucket_key:
            completed = self._finish(one_minute_bar.ts_event_ns)
            self._bucket_key = bucket
            self._start(one_minute_bar)
            self._last_minute = minute
            return completed

        self._high = max(self._high, one_minute_bar.high)
        self._low = min(self._low, one_minute_bar.low)
        self._close = one_minute_bar.close
        self._volume += one_minute_bar.volume
        self._source_bars += one_minute_bar.source_bars
        if self._source_bars == self.period_minutes:
            return self._finish(one_minute_bar.ts_event_ns)
        return None

    @staticmethod
    def _minute_index(ts_event_ns: int) -> int:
        if abs(ts_event_ns) < MINUTE_NS:
            return ts_event_ns
        return ts_event_ns // MINUTE_NS

    def _start(self, bar: BarRecord) -> None:
        self._open = bar.open
        self._high = bar.high
        self._low = bar.low
        self._close = bar.close
        self._volume = bar.volume
        self._source_bars = bar.source_bars

    def _finish(self, ts_event_ns: int) -> BarRecord:
        completed = BarRecord(
            ts_event_ns=ts_event_ns,
            open=self._open,
            high=self._high,
            low=self._low,
            close=self._close,
            volume=self._volume,
            source_bars=self._source_bars,
        )
        self._reset()
        return completed

    def _reset(self) -> None:
        self._bucket_key = None
        self._last_minute = None
        self._source_bars = 0


class CausalWilderATR:
    """Wilder ATR updated only when a completed observation bar arrives."""

    def __init__(self, period: int = 14) -> None:
        if period <= 0:
            raise ValueError("period must be positive")
        self.period = period
        self._previous_close: float | None = None
        self._warmup_true_ranges: deque[float] = deque(maxlen=period)
        self._atr: float | None = None

    @property
    def value(self) -> float | None:
        return self._atr

    def update(self, bar: BarRecord) -> float | None:
        values = (bar.high, bar.low, bar.close)
        if not all(math.isfinite(value) for value in values):
            return None
        if self._previous_close is None:
            self._previous_close = bar.close
            return None
        true_range = max(
            bar.high - bar.low,
            abs(bar.high - self._previous_close),
            abs(bar.low - self._previous_close),
        )
        self._previous_close = bar.close
        if not math.isfinite(true_range) or true_range < 0:
            return None
        if self._atr is None:
            self._warmup_true_ranges.append(true_range)
            if len(self._warmup_true_ranges) < self.period:
                return None
            self._atr = sum(self._warmup_true_ranges) / self.period
            self._warmup_true_ranges.clear()
            return self._atr
        self._atr = ((self._atr * (self.period - 1)) + true_range) / self.period
        return self._atr


class CausalVolatilityRegime:
    """Rank completed ATR/close values against a bounded trailing window."""

    ATR_UNDEFINED = "ATR_UNDEFINED"
    REGIME_WARMUP = "REGIME_WARMUP"
    LOW = "LOW"
    MID = "MID"
    HIGH = "HIGH"

    def __init__(self, window: int = 252) -> None:
        if window <= 0:
            raise ValueError("window must be positive")
        self.window = window
        self._values: deque[float] = deque(maxlen=window)

    @property
    def retained_values(self) -> int:
        return len(self._values)

    def update(self, value: float | None) -> str:
        if value is None or not math.isfinite(value) or value <= 0:
            return self.ATR_UNDEFINED
        self._values.append(value)
        if len(self._values) < self.window:
            return self.REGIME_WARMUP
        ordered = sorted(self._values)
        low_boundary = self._percentile(ordered, 0.33)
        high_boundary = self._percentile(ordered, 0.67)
        if value < low_boundary:
            return self.LOW
        if value > high_boundary:
            return self.HIGH
        return self.MID

    @staticmethod
    def _percentile(ordered: list[float], fraction: float) -> float:
        if len(ordered) == 1:
            return ordered[0]
        position = (len(ordered) - 1) * fraction
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        weight = position - lower
        return ordered[lower] + (ordered[upper] - ordered[lower]) * weight
