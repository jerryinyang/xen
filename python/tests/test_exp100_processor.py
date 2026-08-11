"""Focused causal processor tests for EXP-100."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from xen.exp100.config import Exp100CellConfig
from xen.exp100.processor import Exp100Processor, Exp100Sinks
from xen.exp100.state_store import Exp100StateStore
from xen.exp100.types import BarRecord
from xen.nautilus.streaming import MemoryBudgetExceeded, MemoryGuard

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


@dataclass
class PersistingWriter:
    """Test sink that persists each append without retaining emitted rows."""

    path: Path

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("")

    @property
    def pending_rows(self) -> int:
        return 0

    def append(self, row: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), default=str))
            handle.write("\n")


def make_processor(
    tmp_path: Path,
    *,
    observation_minutes: int = OBSERVATION_MINUTES,
    confirmation_method: str = "BREAKOUT_BAR",
    memory_guard: MemoryGuard | None = None,
    sinks: Exp100Sinks | None = None,
) -> tuple[Exp100Processor, Exp100Sinks]:
    config = Exp100CellConfig(
        venue="BYBIT",
        archive_symbol="BTCUSDT",
        instrument_id="BTCUSDT-LINEAR.BYBIT",
        observation_minutes=observation_minutes,
        confirmation_method=confirmation_method,
        confirmation_reference="1H" if observation_minutes in {15, 30} else "1D",
        level_config="PREVIOUS_1H",
    )
    if sinks is None:
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
        memory_guard or MemoryGuard(None, sample_every=1),
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
    return feed_complete_window(
        processor,
        start_ts_ns=start_ts_ns,
        minutes=OBSERVATION_MINUTES,
        open=open,
        high=high,
        low=low,
        close=close,
    )


def feed_complete_window(
    processor: Exp100Processor,
    *,
    start_ts_ns: int,
    minutes: int,
    open: float,
    high: float,
    low: float,
    close: float,
) -> int:
    """Feed one complete real-minute window without retaining source history."""
    for minute in range(minutes):
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
    return start_ts_ns + (minutes - 1) * MINUTE_NS


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


def test_profile_receives_every_source_minute_after_its_first_excursion(
    tmp_path: Path,
) -> None:
    """Replacing minute updates with an aggregate bar changes TPO bracket count."""
    processor, sinks = make_processor(tmp_path)
    start = 0
    for _ in range(15):
        feed_complete_observation_window(
            processor, start_ts_ns=start, high=101.0, low=99.0, close=100.0
        )
        start += OBSERVATION_MINUTES * MINUTE_NS

    processor.seed_level("L1", price=100.0, side="HIGH")
    last_ts = feed_complete_observation_window(
        processor,
        start_ts_ns=start,
        open=100.8,
        high=101.0,
        low=100.5,
        close=100.8,
    )
    for minute in range(3):
        processor.on_one_minute_bar(
            BarRecord(
                last_ts + (minute + 1) * MINUTE_NS,
                100.8,
                101.0,
                100.5,
                100.8,
                1.0,
                1,
            )
        )
    processor.finish(last_ts + 3 * MINUTE_NS)

    profile = sinks.tpo_profiles.rows[0]
    assert profile["bracket_count"] == 18
    assert profile["tpo_total"] > 18


def test_processor_selects_only_latest_resolvable_raid_for_one_reference_event(
    tmp_path: Path,
) -> None:
    """Confirming every active raid would duplicate one reference outcome."""
    processor, _ = make_processor(tmp_path)
    for raid_id, level_id, sweep_ts_ns in (("R1", "L1", 10), ("R2", "L2", 20)):
        processor.state.insert_raid(
            {
                "raid_id": raid_id,
                "level_id": level_id,
                "event_identity": raid_id,
                "side": "HIGH",
                "level_price": 100.0,
                "sweep_ts_ns": sweep_ts_ns,
                "return_ts_ns": sweep_ts_ns + 1,
                "confirmation_ts_ns": None,
                "max_price": 101.0,
                "profile_generation": None,
                "profile_finalized": False,
                "active": 1,
            }
        )
    processor._previous_reference = BarRecord(60, 100.0, 101.0, 100.0, 100.5, 1.0, 1)
    processor._on_reference_bar(BarRecord(120, 100.0, 100.0, 99.0, 99.5, 1.0, 1))

    rows = {row["raid_id"]: row for row in processor.state.iter_active_raids()}
    assert rows["R1"]["confirmation_ts_ns"] is None
    assert rows["R2"]["confirmation_ts_ns"] == 120


def test_processor_retains_repeated_raids_after_a_return(tmp_path: Path) -> None:
    """An earlier live raid must not suppress a later strict crossing transition."""
    processor, sinks = make_processor(tmp_path)
    processor.seed_level("L1", price=100.0, side="HIGH")
    feed_complete_observation_window(
        processor, start_ts_ns=0, open=100.8, high=101.0, low=100.5, close=100.8
    )
    feed_complete_observation_window(
        processor,
        start_ts_ns=OBSERVATION_MINUTES * MINUTE_NS,
        open=99.8,
        high=100.0,
        low=99.0,
        close=99.5,
    )
    last_ts = feed_complete_observation_window(
        processor,
        start_ts_ns=2 * OBSERVATION_MINUTES * MINUTE_NS,
        open=100.8,
        high=101.0,
        low=100.5,
        close=100.8,
    )
    processor.finish(last_ts)

    assert [row["prior_raid_count"] for row in sinks.raids.rows] == [0, 1]


def test_reference_selects_older_expected_raid_when_newer_price_is_unresolvable(
    tmp_path: Path,
) -> None:
    """Selecting before event predicates lets an unresolvable newer raid block confirmation."""
    processor, _ = make_processor(tmp_path, confirmation_method="LEVEL_CLOSE")
    for raid_id, price, sweep_ts_ns in (("R1", 100.0, 10), ("R2", 90.0, 20)):
        processor.state.insert_raid(
            {
                "raid_id": raid_id,
                "level_id": raid_id,
                "event_identity": raid_id,
                "side": "HIGH",
                "level_price": price,
                "sweep_ts_ns": sweep_ts_ns,
                "return_ts_ns": sweep_ts_ns + 1,
                "confirmation_ts_ns": None,
                "max_price": price + 1.0,
                "profile_generation": None,
                "profile_finalized": False,
                "active": 1,
            }
        )
    processor._previous_reference = BarRecord(60, 100.0, 101.0, 99.0, 100.0, 1.0, 1)
    processor._on_reference_bar(BarRecord(120, 95.0, 95.0, 90.0, 90.0, 1.0, 1))

    rows = {row["raid_id"]: row for row in processor.state.iter_active_raids()}
    assert rows["R1"]["confirmation_ts_ns"] == 120
    assert rows["R2"]["confirmation_ts_ns"] is None


def test_reference_selects_older_endpoint_when_newer_price_is_unresolvable(
    tmp_path: Path,
) -> None:
    """Endpoint selection must also filter by the current opposing event first."""
    processor, sinks = make_processor(tmp_path, confirmation_method="LEVEL_CLOSE")
    for raid_id, price, sweep_ts_ns in (("R1", 100.0, 10), ("R2", 110.0, 20)):
        processor.state.insert_raid(
            {
                "raid_id": raid_id,
                "level_id": raid_id,
                "event_identity": raid_id,
                "side": "HIGH",
                "level_price": price,
                "sweep_ts_ns": sweep_ts_ns,
                "return_ts_ns": sweep_ts_ns + 1,
                "confirmation_ts_ns": 50,
                "primary_attribution": True,
                "max_price": price + 1.0,
                "profile_generation": None,
                "profile_finalized": True,
                "active": 1,
            }
        )
    processor._previous_reference = BarRecord(120, 99.0, 100.0, 98.0, 99.0, 1.0, 1)
    processor._on_reference_bar(BarRecord(180, 105.0, 106.0, 104.0, 105.0, 1.0, 1))

    assert sinks.raids.rows[0]["raid_id"] == "R1"
    assert sinks.raids.rows[0]["status"] == "COMPLETED"
    assert next(processor.state.iter_active_raids())["raid_id"] == "R2"


def test_mixed_side_reference_processes_expected_and_opposing_candidates_independently(
    tmp_path: Path,
) -> None:
    """A newer opposite-side failure must not prevent the older expected confirmation."""
    processor, sinks = make_processor(tmp_path)
    for raid_id, side, sweep_ts_ns in (("R1", "HIGH", 10), ("R2", "LOW", 20)):
        processor.state.insert_raid(
            {
                "raid_id": raid_id,
                "level_id": raid_id,
                "event_identity": raid_id,
                "side": side,
                "level_price": 100.0,
                "sweep_ts_ns": sweep_ts_ns,
                "return_ts_ns": sweep_ts_ns + 1,
                "confirmation_ts_ns": None,
                "max_price": 101.0 if side == "HIGH" else 99.0,
                "profile_generation": None,
                "profile_finalized": False,
                "active": 1,
            }
        )
    processor._previous_reference = BarRecord(60, 100.0, 101.0, 100.0, 100.5, 1.0, 1)
    processor._on_reference_bar(BarRecord(120, 100.0, 100.0, 99.0, 99.5, 1.0, 1))

    assert next(processor.state.iter_active_raids())["raid_id"] == "R1"
    assert next(processor.state.iter_active_raids())["confirmation_ts_ns"] == 120
    assert sinks.raids.rows[0]["raid_id"] == "R2"
    assert sinks.raids.rows[0]["status"] == "FAILED_BREAKOUT"


@pytest.mark.parametrize(
    ("side", "first", "returned", "recross"),
    [
        (
            "HIGH",
            {"open": 100.8, "high": 101.0, "low": 100.5, "close": 100.8},
            {"open": 100.8, "high": 101.0, "low": 100.0, "close": 100.2},
            {"open": 100.8, "high": 101.0, "low": 100.5, "close": 100.8},
        ),
        (
            "LOW",
            {"open": 99.2, "high": 99.5, "low": 99.0, "close": 99.2},
            {"open": 99.2, "high": 100.0, "low": 99.0, "close": 99.8},
            {"open": 99.2, "high": 99.5, "low": 99.0, "close": 99.2},
        ),
    ],
)
def test_returning_while_still_beyond_rearms_level_for_next_crossing(
    tmp_path: Path,
    side: str,
    first: dict[str, float],
    returned: dict[str, float],
    recross: dict[str, float],
) -> None:
    """A return bar may still be beyond; the following crossing must become a new raid."""
    processor, sinks = make_processor(tmp_path)
    processor.seed_level("L1", price=100.0, side=side)
    feed_complete_observation_window(processor, start_ts_ns=0, **first)
    feed_complete_observation_window(
        processor, start_ts_ns=OBSERVATION_MINUTES * MINUTE_NS, **returned
    )
    last_ts = feed_complete_observation_window(
        processor, start_ts_ns=2 * OBSERVATION_MINUTES * MINUTE_NS, **recross
    )
    processor.finish(last_ts)

    assert [row["prior_raid_count"] for row in sinks.raids.rows] == [0, 1]


def test_processor_rejects_non_minute_and_non_contiguous_source_chronology(
    tmp_path: Path,
) -> None:
    """Aggregation must not silently reset when the declared source is invalid."""
    processor, _ = make_processor(tmp_path)
    with pytest.raises(ValueError, match="source_bars"):
        processor.on_one_minute_bar(BarRecord(0, 100.0, 100.0, 100.0, 100.0, 1.0, 2))
    with pytest.raises(ValueError, match="aligned"):
        processor.on_one_minute_bar(BarRecord(1, 100.0, 100.0, 100.0, 100.0, 1.0, 1))
    processor.on_one_minute_bar(BarRecord(0, 100.0, 100.0, 100.0, 100.0, 1.0, 1))
    with pytest.raises(ValueError, match="contiguous"):
        processor.on_one_minute_bar(
            BarRecord(2 * MINUTE_NS, 100.0, 100.0, 100.0, 100.0, 1.0, 1)
        )


def test_processor_supplies_marker_timestamp_to_configured_memory_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An RSS abort must publish its incomplete marker before raising."""
    monkeypatch.setattr("xen.nautilus.streaming.rss_bytes", lambda: 2)
    output_path = tmp_path / "output.parquet"
    guard = MemoryGuard(
        1,
        sample_every=1,
        incomplete_path=output_path,
        cell_identity={"cell": "processor-test"},
    )
    processor, _ = make_processor(tmp_path, memory_guard=guard)

    with pytest.raises(MemoryBudgetExceeded):
        processor.on_one_minute_bar(BarRecord(0, 100.0, 100.0, 100.0, 100.0, 1.0, 1))

    marker = json.loads(output_path.with_suffix(".parquet.incomplete.json").read_text())
    assert marker["last_timestamp"] == 0


def test_profile_is_emitted_before_public_cleanup_and_terminal_raid_is_refreshed(
    tmp_path: Path,
) -> None:
    """A sink failure must not erase a profile before its terminal row is appended."""
    processor, sinks = make_processor(tmp_path)
    generation = processor._profiles.start("R1", 1, excursion_price=101.0, atr_unit=1.0)
    processor._profiles.add_bar(
        "R1", generation, BarRecord(2, 100.0, 101.0, 100.0, 100.5, 1.0, 1)
    )
    raid = {
        "raid_id": "R1",
        "level_id": "L1",
        "event_identity": "R1",
        "side": "HIGH",
        "level_price": 100.0,
        "sweep_ts_ns": 1,
        "return_ts_ns": 2,
        "confirmation_ts_ns": None,
        "max_price": 101.0,
        "profile_generation": generation,
        "profile_finalized": False,
        "active": 1,
    }
    processor.state.insert_raid(raid)

    class InspectingWriter(CollectingWriter):
        def append(self, row: dict[str, Any]) -> None:
            assert processor.state.current_profile_generation("R1") == generation
            super().append(row)

    sinks.tpo_profiles = InspectingWriter()
    processor._terminal_raid(raid, status="RIGHT_CENSORED_ENDPOINT", endpoint_ts_ns=3)

    assert processor.state.current_profile_generation("R1") is None
    assert sinks.raids.rows[0]["profile_finalized"] is True


def test_processor_uses_closed_one_hour_and_one_day_references(tmp_path: Path) -> None:
    """A 1H/1D event is unavailable until its completed reference closes."""
    hourly, _ = make_processor(tmp_path / "hourly")
    hourly.state.insert_raid(
        {
            "raid_id": "R1",
            "level_id": "L1",
            "event_identity": "R1",
            "side": "HIGH",
            "level_price": 100.0,
            "sweep_ts_ns": 1,
            "return_ts_ns": 2,
            "confirmation_ts_ns": None,
            "max_price": 101.0,
            "profile_generation": None,
            "profile_finalized": False,
            "active": 1,
        }
    )
    hourly._previous_reference = BarRecord(60, 100.0, 101.0, 100.0, 100.5, 1.0, 60)
    hourly._on_reference_bar(BarRecord(120, 100.0, 100.0, 99.0, 99.5, 1.0, 60))
    assert next(hourly.state.iter_active_raids())["confirmation_ts_ns"] == 120

    daily, _ = make_processor(tmp_path / "daily", observation_minutes=60)
    daily.state.insert_raid(
        {
            "raid_id": "R1",
            "level_id": "L1",
            "event_identity": "R1",
            "side": "HIGH",
            "level_price": 100.0,
            "sweep_ts_ns": 1,
            "return_ts_ns": 2,
            "confirmation_ts_ns": None,
            "max_price": 101.0,
            "profile_generation": None,
            "profile_finalized": False,
            "active": 1,
        }
    )
    daily._previous_reference = BarRecord(1_440, 100.0, 101.0, 100.0, 100.5, 1.0, 1_440)
    daily._on_reference_bar(BarRecord(2_880, 100.0, 100.0, 99.0, 99.5, 1.0, 1_440))
    assert next(daily.state.iter_active_raids())["confirmation_ts_ns"] == 2_880


def test_confirmation_and_endpoint_capture_causal_feature_state(tmp_path: Path) -> None:
    """Dropping transition-time ATR/regime fields makes event outcomes unauditable."""
    processor, sinks = make_processor(tmp_path)
    processor._atr._atr = 1.25
    processor._last_regime = "MID"
    processor.state.insert_raid(
        {
            "raid_id": "R1",
            "level_id": "L1",
            "event_identity": "R1",
            "side": "HIGH",
            "level_price": 100.0,
            "sweep_ts_ns": 1,
            "return_ts_ns": 2,
            "confirmation_ts_ns": None,
            "max_price": 101.0,
            "profile_generation": None,
            "profile_finalized": False,
            "active": 1,
        }
    )
    processor._previous_reference = BarRecord(60, 100.0, 101.0, 100.0, 100.5, 1.0, 1)
    processor._on_reference_bar(BarRecord(120, 100.0, 100.0, 99.0, 99.5, 1.0, 1))
    confirmed = next(processor.state.iter_active_raids())
    assert confirmed["confirmation_atr"] == 1.25
    assert confirmed["confirmation_regime"] == "MID"

    processor._previous_reference = BarRecord(120, 100.0, 100.0, 99.0, 99.5, 1.0, 1)
    processor._on_reference_bar(BarRecord(180, 99.5, 102.0, 99.5, 102.0, 1.0, 1))
    assert sinks.raids.rows[0]["endpoint_atr"] == 1.25
    assert sinks.raids.rows[0]["endpoint_regime"] == "MID"


def test_processor_replay_is_deterministic_across_persisted_output_directories(
    tmp_path: Path,
) -> None:
    """Fresh state and output paths must produce byte-identical terminal streams."""
    def replay(path: Path) -> tuple[dict[str, bytes], dict[str, int]]:
        sinks = Exp100Sinks(
            **{
                name: PersistingWriter(path / f"{name}.jsonl")
                for name in ("bar_marks", "levels", "raids", "tpo_profiles", "event_log")
            }
        )
        processor, _ = make_processor(path / "state", sinks=sinks)
        processor.seed_level("L1", price=100.0, side="HIGH")
        feed_complete_observation_window(
            processor, start_ts_ns=0, open=100.8, high=101.0, low=100.5, close=100.8
        )
        last_ts = feed_complete_observation_window(
            processor,
            start_ts_ns=OBSERVATION_MINUTES * MINUTE_NS,
            open=99.8,
            high=100.0,
            low=99.0,
            close=99.5,
        )
        processor.finish(last_ts)
        return {
            name: (path / f"{name}.jsonl").read_bytes()
            for name in ("bar_marks", "levels", "raids", "tpo_profiles", "event_log")
        }, processor.snapshot()

    first_outputs, first_snapshot = replay(tmp_path / "first")
    second_outputs, second_snapshot = replay(tmp_path / "second")

    assert first_outputs == second_outputs
    assert first_snapshot["open_levels"] == second_snapshot["open_levels"] == 0
    assert first_snapshot["open_raids"] == second_snapshot["open_raids"] == 0
