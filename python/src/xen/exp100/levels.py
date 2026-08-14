"""Causal production level catalogue for one EXP-100 cell configuration.

Each cell processes exactly one frozen ``level_config``. The catalogue creates
previous-period, previous-session, or rolling observation levels online from
completed source minutes and completed observation bars. It never looks ahead.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Iterator
from zoneinfo import ZoneInfo

from .features import StreamingOHLC
from .types import BarRecord

MINUTE_NS = 60_000_000_000

PERIOD_MINUTES: dict[str, int] = {
    "PREVIOUS_1H": 60,
    "PREVIOUS_4H": 240,
}

TRADING_PERIODS: dict[str, str] = {
    "PREVIOUS_1D": "DAY",
    "PREVIOUS_1W": "WEEK",
}

SESSION_WINDOWS: dict[str, tuple[str, int, int]] = {
    "PREVIOUS_ASIA": ("Asia/Tokyo", 9, 18),
    "PREVIOUS_EUROPE": ("Europe/London", 8, 17),
    "PREVIOUS_AMERICA": ("America/New_York", 8, 17),
}

ROLLING_PERIODS: dict[str, int] = {
    "ROLLING_7": 7,
    "ROLLING_14": 14,
    "ROLLING_22": 22,
    "ROLLING_252": 252,
}


@dataclass(frozen=True, slots=True)
class LevelSpec:
    """One newly created catalogue level ready for insertion into live state."""

    level_id: str
    side: str
    price: float
    creation_ts_ns: int
    anchor_key: str


class LevelCatalogue:
    """Create approved previous-period, session, or rolling levels for one cell."""

    def __init__(self, level_config: str, observation_minutes: int) -> None:
        if observation_minutes <= 0:
            raise ValueError("observation_minutes must be positive")
        self.level_config = level_config
        self.observation_minutes = observation_minutes
        self._period_minutes = PERIOD_MINUTES.get(level_config)
        self._trading_period = TRADING_PERIODS.get(level_config)
        self._session = SESSION_WINDOWS.get(level_config)
        self._rolling_period = ROLLING_PERIODS.get(level_config)
        if (
            self._period_minutes is None
            and self._trading_period is None
            and self._session is None
            and self._rolling_period is None
        ):
            raise ValueError(f"unsupported level_config: {level_config!r}")

        self._period_aggregator: StreamingOHLC | None = None
        if self._period_minutes is not None:
            self._period_aggregator = StreamingOHLC(self._period_minutes)

        self._trading_key: date | None = None
        self._trading_open = 0.0
        self._trading_high = 0.0
        self._trading_low = 0.0
        self._trading_close = 0.0
        self._trading_zone = (
            ZoneInfo("America/New_York") if self._trading_period is not None else None
        )

        self._session_zone: ZoneInfo | None = None
        self._session_start_hour = 0
        self._session_end_hour = 0
        self._session_key: tuple[int, int, int] | None = None
        self._session_open = 0.0
        self._session_high = 0.0
        self._session_low = 0.0
        self._session_close = 0.0
        self._session_started = False
        if self._session is not None:
            zone_name, start_hour, end_hour = self._session
            self._session_zone = ZoneInfo(zone_name)
            self._session_start_hour = start_hour
            self._session_end_hour = end_hour

        self._rolling_highs: deque[float] | None = None
        self._rolling_lows: deque[float] | None = None
        self._active_high_anchor: str | None = None
        self._active_low_anchor: str | None = None
        if self._rolling_period is not None:
            self._rolling_highs = deque(maxlen=self._rolling_period)
            self._rolling_lows = deque(maxlen=self._rolling_period)

    def on_source_minute(self, bar: BarRecord) -> list[LevelSpec]:
        """Update period/session catalogues from one completed source minute."""
        if self._period_aggregator is not None:
            completed = self._period_aggregator.update(bar)
            if completed is None:
                return []
            return list(self._levels_from_completed_period(completed))
        if self._trading_period is not None:
            return self._update_trading_period(bar)
        if self._session is not None:
            return list(self._update_session(bar))
        return []

    def on_observation_bar(self, bar: BarRecord) -> list[LevelSpec]:
        """Update rolling catalogues from one completed observation bar."""
        if self._rolling_highs is None or self._rolling_lows is None:
            return []
        assert self._rolling_period is not None
        self._rolling_highs.append(bar.high)
        self._rolling_lows.append(bar.low)
        if len(self._rolling_highs) < self._rolling_period:
            return []
        high_price = max(self._rolling_highs)
        low_price = min(self._rolling_lows)
        anchor = f"{bar.ts_event_ns}|{self._rolling_period}"
        created: list[LevelSpec] = []
        if self._active_high_anchor != anchor:
            self._active_high_anchor = anchor
            created.append(
                LevelSpec(
                    level_id=f"{self.level_config}|HIGH|{anchor}",
                    side="HIGH",
                    price=high_price,
                    creation_ts_ns=bar.ts_event_ns,
                    anchor_key=anchor,
                )
            )
        if self._active_low_anchor != anchor:
            self._active_low_anchor = anchor
            created.append(
                LevelSpec(
                    level_id=f"{self.level_config}|LOW|{anchor}",
                    side="LOW",
                    price=low_price,
                    creation_ts_ns=bar.ts_event_ns,
                    anchor_key=anchor,
                )
            )
        return created

    def _levels_from_completed_period(self, bar: BarRecord) -> Iterator[LevelSpec]:
        anchor = str(bar.ts_event_ns)
        yield LevelSpec(
            level_id=f"{self.level_config}|HIGH|{anchor}",
            side="HIGH",
            price=bar.high,
            creation_ts_ns=bar.ts_event_ns,
            anchor_key=anchor,
        )
        yield LevelSpec(
            level_id=f"{self.level_config}|LOW|{anchor}",
            side="LOW",
            price=bar.low,
            creation_ts_ns=bar.ts_event_ns,
            anchor_key=anchor,
        )

    def _update_trading_period(self, bar: BarRecord) -> list[LevelSpec]:
        """Build NY-17:00 trading-day or Monday-Friday week levels online."""
        assert self._trading_period is not None
        assert self._trading_zone is not None
        local = datetime.fromtimestamp(
            bar.ts_event_ns / 1_000_000_000, tz=timezone.utc
        ).astimezone(self._trading_zone)
        day_key = self._trading_day_key(local)
        if day_key is None:
            if self._trading_key is None:
                return []
            created = self._emit_trading_period(bar.ts_event_ns)
            self._trading_key = None
            return created

        key = (
            day_key
            if self._trading_period == "DAY"
            else day_key - timedelta(days=day_key.weekday())
        )
        if self._trading_key is None:
            self._trading_key = key
            self._trading_open = bar.open
            self._trading_high = bar.high
            self._trading_low = bar.low
            self._trading_close = bar.close
            return []
        if key != self._trading_key:
            created = self._emit_trading_period(bar.ts_event_ns)
            self._trading_key = key
            self._trading_open = bar.open
            self._trading_high = bar.high
            self._trading_low = bar.low
            self._trading_close = bar.close
            return created

        self._trading_high = max(self._trading_high, bar.high)
        self._trading_low = min(self._trading_low, bar.low)
        self._trading_close = bar.close
        return []

    @staticmethod
    def _trading_day_key(local: datetime) -> date | None:
        """Return the weekday label for the active NY-17:00 trading book."""
        current = local.date()
        weekday = current.weekday()
        if weekday in {5, 6} and not (weekday == 6 and local.hour >= 17):
            return None
        if weekday == 6:
            return current + timedelta(days=1)
        if local.hour >= 17:
            next_day = current + timedelta(days=1)
            return next_day if next_day.weekday() < 5 else None
        return current

    def _emit_trading_period(self, end_ts_ns: int) -> list[LevelSpec]:
        if self._trading_key is None:
            return []
        anchor = self._trading_key.isoformat()
        return [
            LevelSpec(
                level_id=f"{self.level_config}|HIGH|{anchor}",
                side="HIGH",
                price=self._trading_high,
                creation_ts_ns=end_ts_ns,
                anchor_key=anchor,
            ),
            LevelSpec(
                level_id=f"{self.level_config}|LOW|{anchor}",
                side="LOW",
                price=self._trading_low,
                creation_ts_ns=end_ts_ns,
                anchor_key=anchor,
            ),
        ]

    def _update_session(self, bar: BarRecord) -> Iterator[LevelSpec]:
        assert self._session_zone is not None
        local = datetime.fromtimestamp(bar.ts_event_ns / 1_000_000_000, tz=timezone.utc).astimezone(
            self._session_zone
        )
        in_session = self._session_start_hour <= local.hour < self._session_end_hour
        session_key = (local.year, local.month, local.day)
        if in_session:
            if not self._session_started or self._session_key != session_key:
                if self._session_started and self._session_key != session_key:
                    yield from self._emit_completed_session()
                self._session_key = session_key
                self._session_started = True
                self._session_open = bar.open
                self._session_high = bar.high
                self._session_low = bar.low
                self._session_close = bar.close
            else:
                self._session_high = max(self._session_high, bar.high)
                self._session_low = min(self._session_low, bar.low)
                self._session_close = bar.close
            return
        if self._session_started:
            yield from self._emit_completed_session(end_ts_ns=bar.ts_event_ns)
            self._session_started = False
            self._session_key = None

    def _emit_completed_session(self, end_ts_ns: int | None = None) -> Iterator[LevelSpec]:
        if self._session_key is None:
            return
        year, month, day = self._session_key
        # Anchor at local session end on the session calendar day, converted to UTC ns.
        assert self._session_zone is not None
        local_end = datetime(
            year, month, day, self._session_end_hour, 0, tzinfo=self._session_zone
        )
        creation_ts_ns = (
            end_ts_ns
            if end_ts_ns is not None
            else int(local_end.astimezone(timezone.utc).timestamp() * 1_000_000_000)
        )
        # Align creation to the minute of the last in-session bar when available.
        if end_ts_ns is None and creation_ts_ns % MINUTE_NS != 0:
            creation_ts_ns = (creation_ts_ns // MINUTE_NS) * MINUTE_NS
        anchor = f"{year:04d}-{month:02d}-{day:02d}"
        yield LevelSpec(
            level_id=f"{self.level_config}|HIGH|{anchor}",
            side="HIGH",
            price=self._session_high,
            creation_ts_ns=creation_ts_ns,
            anchor_key=anchor,
        )
        yield LevelSpec(
            level_id=f"{self.level_config}|LOW|{anchor}",
            side="LOW",
            price=self._session_low,
            creation_ts_ns=creation_ts_ns,
            anchor_key=anchor,
        )
