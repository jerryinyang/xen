"""Focused causal processor tests for EXP-100."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from xen.exp100.config import Exp100CellConfig
from xen.exp100.processor import Exp100Processor, Exp100Sinks
from xen.exp100.state_store import Exp100StateStore
from xen.exp100.types import BarRecord
from xen.nautilus.streaming import MemoryGuard

MINUTE_NS = 60_000_000_000
OBSERVATION_MINUTES = 15
FIRST_WINDOW_END_TS = (OBSERVATION_MINUTES - 1) * MINUTE_NS
SECOND_WINDOW_END_TS = (2 * OBSERVATION_MINUTES - 1) * MINUTE_NS


@dataclass
class CollectingWriter:
    rows: list[dict[str, Any]] = field(default_factory=list)

    @property
    def pending_rows(self) -> int:
        return 0

    def append(self, row: dict[str, Any]) -> None:
        self.rows.append(dict(row))


def make_processor(tmp_path: Path) -> tuple[Exp100Processor, Exp100Sinks]:
    config = Exp100CellConfig(
        venue="BYBIT",
        archive_symbol="BTCUSDT",
        instrument_id="BTCUSDT-LINEAR.BYBIT",
        observation_minutes=15,
        confirmation_method="BREAKOUT_BAR",
        confirmation_reference="1H",
        level_config="PREVIOUS_1H",
    )
    sinks = Exp100Sinks(
        bar_marks=CollectingWriter(),
        levels=CollectingWriter(),
        raids=CollectingWriter(),
        tpo_profiles=CollectingWriter(),
        event_log=CollectingWriter(),
    )
    processor = Exp100Processor(
        config,
        Exp100StateStore(tmp_path / "state.sqlite"),
        sinks,
        MemoryGuard(None, sample_every=1),
    )
    return processor, sinks


def feed_complete_observation_window(
    processor: Exp100Processor,
    *,
    start_ts_ns: int,
    open: float = 100.0,
    high: float,
    low: float,
    close: float,
) -> int:
    """Feed one complete clock-aligned 15-minute observation window."""
    for minute in range(OBSERVATION_MINUTES):
        processor.on_one_minute_bar(
            BarRecord(
                start_ts_ns + minute * MINUTE_NS,
                open,
                high,
                low,
                close,
                1.0,
                1,
            )
        )
    return start_ts_ns + FIRST_WINDOW_END_TS


def test_processor_keeps_ambiguous_same_bar_raid_out_of_primary_result(tmp_path: Path) -> None:
    """A same-bar cross and return is retained but cannot become primary."""
    processor, sinks = make_processor(tmp_path)
    processor.seed_level("L1", price=100.0, side="HIGH")
    last_ts = feed_complete_observation_window(
        processor, start_ts_ns=0, high=101.0, low=99.0, close=100.0
    )
    processor.finish(last_ts)

    assert len(sinks.bar_marks.rows) == 1
    assert sinks.bar_marks.rows[0]["source_bars"] == OBSERVATION_MINUTES
    assert len(sinks.raids.rows) == 1
    row = sinks.raids.rows[0]
    assert row["status"] == "AMBIGUOUS_INTRABAR"
    assert row["primary_completed"] is False


def test_processor_uses_later_bar_for_inclusive_return_and_censors_unconfirmed_state(
    tmp_path: Path,
) -> None:
    """A strict raid returns only on a later inclusive observation bar."""
    processor, sinks = make_processor(tmp_path)
    processor.seed_level("L1", price=100.0, side="HIGH")
    feed_complete_observation_window(
        processor, start_ts_ns=0, high=101.0, low=100.5, close=100.8
    )
    last_ts = feed_complete_observation_window(
        processor,
        start_ts_ns=OBSERVATION_MINUTES * MINUTE_NS,
        high=101.1,
        low=100.0,
        close=100.2,
    )
    processor.finish(last_ts)

    assert len(sinks.raids.rows) == 1
    row = sinks.raids.rows[0]
    assert row["return_ts_ns"] == SECOND_WINDOW_END_TS
    assert row["status"] == "RIGHT_CENSORED_CONFIRMATION"


def test_processor_censors_open_state_and_emits_level_before_deletion(tmp_path: Path) -> None:
    """End-of-input censors all remaining state rather than dropping it."""
    processor, sinks = make_processor(tmp_path)
    processor.seed_level("L1", price=100.0, side="LOW")
    feed_complete_observation_window(
        processor, start_ts_ns=0, open=99.8, high=99.8, low=99.0, close=99.5
    )
    processor.finish(FIRST_WINDOW_END_TS)

    assert sinks.raids.rows[0]["status"] == "RIGHT_CENSORED_EXCURSION"
    assert sinks.levels.rows[0]["status"] == "RIGHT_CENSORED"
    assert processor.snapshot()["open_raids"] == 0
    assert processor.snapshot()["open_levels"] == 0


def test_processor_replay_is_deterministic_and_leaves_no_terminal_state(tmp_path: Path) -> None:
    """The same completed bars emit the same terminal rows from fresh state."""
    def replay(path: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int]]:
        processor, sinks = make_processor(path)
        processor.seed_level("L1", price=100.0, side="HIGH")
        feed_complete_observation_window(
            processor, start_ts_ns=0, high=101.0, low=100.5, close=100.8
        )
        last_ts = feed_complete_observation_window(
            processor,
            start_ts_ns=OBSERVATION_MINUTES * MINUTE_NS,
            high=101.1,
            low=100.0,
            close=100.2,
        )
        processor.finish(last_ts)
        rows = {
            "bar_marks": sinks.bar_marks.rows,
            "levels": sinks.levels.rows,
            "raids": sinks.raids.rows,
            "tpo_profiles": sinks.tpo_profiles.rows,
            "event_log": sinks.event_log.rows,
        }
        return rows, processor.snapshot()

    first_rows, first_snapshot = replay(tmp_path / "first")
    second_rows, second_snapshot = replay(tmp_path / "second")

    assert first_rows == second_rows
    assert first_snapshot["open_levels"] == 0
    assert first_snapshot["open_raids"] == 0
    assert second_snapshot["open_levels"] == 0
    assert second_snapshot["open_raids"] == 0
