"""Focused tests for the EXP-100 production level catalogue."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from xen.exp100.config import Exp100CellConfig
from xen.exp100.levels import LevelCatalogue
from xen.exp100.processor import Exp100Processor, Exp100Sinks
from xen.exp100.state_store import Exp100StateStore
from xen.exp100.types import BarRecord
from xen.nautilus.streaming import MemoryGuard

MINUTE_NS = 60_000_000_000


def _bar(ts_ns: int, high: float, low: float, close: float | None = None) -> BarRecord:
    mid = (high + low) / 2.0
    return BarRecord(ts_ns, mid, high, low, close if close is not None else mid, 1.0, 1)


def test_previous_1h_levels_created_after_completed_period() -> None:
    catalogue = LevelCatalogue("PREVIOUS_1H", observation_minutes=15)
    created = []
    for minute in range(60):
        created.extend(
            catalogue.on_source_minute(_bar(minute * MINUTE_NS, 101.0 + minute * 0.01, 99.0))
        )
    assert len(created) == 2
    sides = {spec.side: spec for spec in created}
    assert sides["HIGH"].price == 101.0 + 59 * 0.01
    assert sides["LOW"].price == 99.0
    assert sides["HIGH"].creation_ts_ns == 59 * MINUTE_NS


def test_rolling_levels_require_full_window(tmp_path: Path) -> None:
    class Collect:
        def __init__(self) -> None:
            self.rows: list[dict] = []

        @property
        def pending_rows(self) -> int:
            return 0

        def append(self, row: dict) -> None:
            self.rows.append(dict(row))

    config = Exp100CellConfig(
        venue="BYBIT",
        archive_symbol="BTCUSDT",
        instrument_id="BTCUSDT-LINEAR.BYBIT",
        observation_minutes=15,
        confirmation_method="BREAKOUT_BAR",
        confirmation_reference="1H",
        level_config="ROLLING_16",
    )
    sinks = Exp100Sinks(
        bar_marks=Collect(),
        levels=Collect(),
        raids=Collect(),
        tpo_profiles=Collect(),
        event_log=Collect(),
    )
    processor = Exp100Processor(
        config,
        Exp100StateStore(tmp_path / "state.sqlite"),
        sinks,
        MemoryGuard(None, sample_every=1),
    )
    for observation in range(16):
        start = observation * 15 * MINUTE_NS
        for minute in range(15):
            processor.on_one_minute_bar(
                _bar(start + minute * MINUTE_NS, 100.0 + observation, 90.0 + observation)
            )
    active_high = [
        level for level in processor.state.iter_active_levels() if level["side"] == "HIGH"
    ]
    assert len(active_high) == 1
    assert active_high[0]["price"] == 100.0 + 15
    assert active_high[0]["source_configuration"] == "ROLLING_16"


def test_session_levels_emit_after_local_session_close() -> None:
    catalogue = LevelCatalogue("PREVIOUS_ASIA", observation_minutes=15)
    tokyo = ZoneInfo("Asia/Tokyo")
    # 2023-01-04 09:00-18:00 Asia/Tokyo session.
    start_local = datetime(2023, 1, 4, 9, 0, tzinfo=tokyo)
    created = []
    for minute in range(9 * 60):  # 09:00 through 17:59
        local = start_local.replace(hour=9 + minute // 60, minute=minute % 60)
        ts_ns = int(local.astimezone(timezone.utc).timestamp() * 1_000_000_000)
        created.extend(catalogue.on_source_minute(_bar(ts_ns, 110.0, 100.0)))
    assert created == []
    # First bar after 18:00 local closes the session catalogue.
    end_local = datetime(2023, 1, 4, 18, 0, tzinfo=tokyo)
    end_ts = int(end_local.astimezone(timezone.utc).timestamp() * 1_000_000_000)
    created = catalogue.on_source_minute(_bar(end_ts, 105.0, 104.0))
    assert len(created) == 2
    sides = {spec.side: spec for spec in created}
    assert sides["HIGH"].price == 110.0
    assert sides["LOW"].price == 100.0
