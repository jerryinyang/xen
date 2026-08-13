"""Focused causal processor tests for EXP-100."""

from __future__ import annotations

import json
from collections.abc import Iterator
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
    # Default 1m observation so unit tests exercise raid lifecycle one-for-one
    # with fed bars. Production cells use 15/30/60; raid lifecycle follows that TF.
    observation_minutes: int = 1,
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
        confirmation_reference=(
            "1H" if observation_minutes in {1, 15, 30} else "4H"
        ),
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


def test_processor_keeps_same_bar_cross_and_return_as_live_raid(tmp_path: Path) -> None:
    """AMENDMENT-13: same-bar beyond+return starts a live raid, not AMBIGUOUS."""
    processor, sinks = make_processor(tmp_path)
    processor.seed_level("L1", price=100.0, side="HIGH")
    processor.on_one_minute_bar(BarRecord(0, 100.0, 101.0, 99.0, 100.0, 1.0, 1))

    live = list(processor.state.iter_active_raids())
    assert len(live) == 1
    assert live[0]["sweep_ts_ns"] == 0
    assert live[0]["return_ts_ns"] == 0
    assert live[0]["confirmation_ts_ns"] is None
    assert sinks.raids.rows == []

    processor.finish(0)
    assert len(sinks.raids.rows) == 1
    row = sinks.raids.rows[0]
    assert row["status"] == "RIGHT_CENSORED_CONFIRMATION"
    assert row["primary_completed"] is False
    assert row["sweep_ts_ns"] == 0
    assert row["return_ts_ns"] == 0


def test_processor_uses_later_bar_for_inclusive_return_and_censors_unconfirmed_state(
    tmp_path: Path,
) -> None:
    """A strict 1m raid returns only on a later inclusive 1m bar."""
    processor, sinks = make_processor(tmp_path)
    processor.seed_level("L1", price=100.0, side="HIGH")
    processor.on_one_minute_bar(BarRecord(0, 100.8, 101.0, 100.5, 100.8, 1.0, 1))
    processor.on_one_minute_bar(
        BarRecord(MINUTE_NS, 100.8, 101.1, 100.0, 100.2, 1.0, 1)
    )
    processor.finish(MINUTE_NS)

    assert len(sinks.raids.rows) == 1
    row = sinks.raids.rows[0]
    assert row["return_ts_ns"] == MINUTE_NS
    assert row["status"] == "RIGHT_CENSORED_CONFIRMATION"


def test_processor_censors_open_state_and_emits_level_before_deletion(tmp_path: Path) -> None:
    """End-of-input censors all remaining state rather than dropping it."""
    processor, sinks = make_processor(tmp_path)
    processor.seed_level("L1", price=100.0, side="LOW")
    processor.on_one_minute_bar(BarRecord(0, 99.8, 99.8, 99.0, 99.5, 1.0, 1))
    processor.finish(0)

    assert sinks.raids.rows[0]["status"] == "RIGHT_CENSORED_EXCURSION"
    assert sinks.levels.rows[0]["status"] == "RIGHT_CENSORED"
    assert processor.snapshot()["open_raids"] == 0
    assert processor.snapshot()["open_levels"] == 0


def test_processor_replay_is_deterministic_and_leaves_no_terminal_state(tmp_path: Path) -> None:
    """The same completed bars emit the same terminal rows from fresh state."""
    def replay(path: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int]]:
        processor, sinks = make_processor(path)
        processor.seed_level("L1", price=100.0, side="HIGH")
        processor.on_one_minute_bar(BarRecord(0, 100.8, 101.0, 100.5, 100.8, 1.0, 1))
        processor.on_one_minute_bar(
            BarRecord(MINUTE_NS, 100.8, 101.1, 100.0, 100.2, 1.0, 1)
        )
        processor.finish(MINUTE_NS)
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


def test_processor_source_minute_creates_raid_under_transaction(tmp_path: Path) -> None:
    """One source minute applies level/raid mutations through the bar transaction."""
    processor, _ = make_processor(tmp_path)
    processor.seed_level("L1", price=100.0, side="HIGH")

    processor.on_one_minute_bar(
        BarRecord(0, 100.8, 101.0, 100.5, 100.8, 1.0, 1)
    )

    assert processor.state._transaction_depth == 0
    assert next(processor.state.iter_active_raids())["raid_id"] == "L1:raid:1"


def test_processor_skips_level_writes_when_beyond_flag_is_unchanged(
    tmp_path: Path,
) -> None:
    """Unchanged beyond state must not rewrite the level row every source minute."""
    processor, _ = make_processor(tmp_path)
    processor.seed_level("L1", price=100.0, side="HIGH")
    # Establish beyond=true once.
    processor.on_one_minute_bar(BarRecord(0, 100.8, 101.0, 100.5, 100.8, 1.0, 1))
    updates: list[tuple[str, dict[str, Any]]] = []
    original = processor.state.update_level

    def counted(level_id: str, fields: dict[str, Any]) -> None:
        updates.append((level_id, dict(fields)))
        original(level_id, fields)

    processor.state.update_level = counted  # type: ignore[method-assign]

    # Still beyond without a return; beyond flag is unchanged.
    processor.on_one_minute_bar(
        BarRecord(MINUTE_NS, 100.9, 101.2, 100.6, 101.0, 1.0, 1)
    )

    assert updates == []
    raid = next(processor.state.iter_active_raids())
    assert raid["return_ts_ns"] is None
    assert next(processor.state.iter_active_levels())["beyond"] is True


def test_processor_scans_active_raids_for_tpo_and_observation_lifecycle(
    tmp_path: Path,
) -> None:
    """1m TPO pass and observation-TF return pass each stream active raids once."""
    processor, _ = make_processor(tmp_path)
    processor.seed_level("L1", price=100.0, side="HIGH")
    processor.on_one_minute_bar(BarRecord(0, 100.8, 101.0, 100.5, 100.8, 1.0, 1))
    original = processor.state.iter_active_raids
    calls = 0

    def counted() -> Iterator[dict[str, Any]]:
        nonlocal calls
        calls += 1
        yield from original()

    processor.state.iter_active_raids = counted
    processor.on_one_minute_bar(
        BarRecord(MINUTE_NS, 100.9, 101.2, 100.6, 101.0, 1.0, 1)
    )

    # observation_minutes=1 collapses both passes onto the same bar.
    assert calls == 2
    raid = next(original())
    assert raid["raid_id"] == "L1:raid:1"
    assert raid["return_ts_ns"] is None


def test_profile_receives_every_source_minute_after_its_first_excursion(
    tmp_path: Path,
) -> None:
    """Each source minute after the first excursion contributes one TPO bracket."""
    processor, sinks = make_processor(tmp_path)
    # Warm ATR with completed observation bars that do not raid.
    start = 0
    for _ in range(15):
        feed_complete_observation_window(
            processor, start_ts_ns=start, high=100.0, low=99.0, close=99.5
        )
        start += OBSERVATION_MINUTES * MINUTE_NS

    processor.seed_level("L1", price=100.0, side="HIGH")
    # 15 beyond-without-return minutes + 3 more = 18 brackets.
    for minute in range(18):
        processor.on_one_minute_bar(
            BarRecord(
                start + minute * MINUTE_NS,
                100.8,
                101.0,
                100.5,
                100.8,
                1.0,
                1,
            )
        )
    processor.finish(start + 17 * MINUTE_NS)

    profile = sinks.tpo_profiles.rows[0]
    assert profile["bracket_count"] == 18
    assert profile["tpo_total"] > 18
    assert profile.get("gap_span_atr") is not None or profile["profile_status"] != "DEFINED"
    if profile["profile_status"] == "DEFINED":
        assert profile["gap_span_va"] is not None


def test_processor_confirms_all_eligible_raids_and_keeps_only_latest_primary(
    tmp_path: Path,
) -> None:
    """Close-all-eligible: earlier raids settle non-primary; latest stays primary."""
    processor, sinks = make_processor(tmp_path)
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

    live = list(processor.state.iter_active_raids())
    assert len(live) == 1
    assert live[0]["raid_id"] == "R2"
    assert live[0]["confirmation_ts_ns"] == 120
    assert live[0]["primary_attribution"] is True
    assert sinks.raids.rows[0]["raid_id"] == "R1"
    assert sinks.raids.rows[0]["status"] == "CONFIRMED_NON_PRIMARY"
    assert sinks.raids.rows[0]["primary_attribution"] is False


def test_processor_retains_repeated_raids_after_a_return(tmp_path: Path) -> None:
    """An earlier live raid must not suppress a later strict crossing transition."""
    processor, sinks = make_processor(tmp_path)
    processor.seed_level("L1", price=100.0, side="HIGH")
    processor.on_one_minute_bar(BarRecord(0, 100.8, 101.0, 100.5, 100.8, 1.0, 1))
    processor.on_one_minute_bar(
        BarRecord(MINUTE_NS, 99.8, 100.0, 99.0, 99.5, 1.0, 1)
    )
    processor.on_one_minute_bar(
        BarRecord(2 * MINUTE_NS, 100.8, 101.0, 100.5, 100.8, 1.0, 1)
    )
    processor.finish(2 * MINUTE_NS)

    assert [row["prior_raid_count"] for row in sinks.raids.rows] == [0, 1]


def test_level_close_uses_higher_degree_levels_not_raid_price(tmp_path: Path) -> None:
    """LEVEL_CLOSE must confirm against previous reference extremes, not raid prices."""
    processor, _ = make_processor(tmp_path, confirmation_method="LEVEL_CLOSE")
    for raid_id, price, sweep_ts_ns in (("R1", 100.0, 10), ("R2", 50.0, 20)):
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
                "max_excursion": 1.0,
                "profile_generation": None,
                "profile_finalized": False,
                "active": 1,
            }
        )
    # previous reference high/low = 101/99; close 90 is beyond the low → expected.
    # Both raids share that confirmation level; latest stays primary, earlier closes.
    processor._previous_reference = BarRecord(60, 100.0, 101.0, 99.0, 100.0, 1.0, 1)
    processor._on_reference_bar(BarRecord(120, 95.0, 95.0, 90.0, 90.0, 1.0, 1))

    live = list(processor.state.iter_active_raids())
    assert len(live) == 1
    assert live[0]["raid_id"] == "R2"
    assert live[0]["confirmation_ts_ns"] == 120
    assert live[0]["confirmation_level_high"] == 101.0
    assert live[0]["confirmation_level_low"] == 99.0
    assert live[0]["confirmation_level_low"] != live[0]["level_price"]


def test_level_close_endpoint_uses_higher_degree_levels(tmp_path: Path) -> None:
    """Endpoint opposing events also use higher-degree levels, not raid prices."""
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
                "max_excursion": 1.0,
                "profile_generation": None,
                "profile_finalized": True,
                "active": 1,
            }
        )
    processor._previous_reference = BarRecord(120, 99.0, 100.0, 98.0, 99.0, 1.0, 1)
    processor._on_reference_bar(BarRecord(180, 105.0, 106.0, 104.0, 105.0, 1.0, 1))

    # close 105 > previous.high 100 → opposing for HIGH; every primary completes.
    completed = {row["raid_id"]: row["status"] for row in sinks.raids.rows}
    assert completed == {"R1": "COMPLETED", "R2": "COMPLETED"}
    assert list(processor.state.iter_active_raids()) == []


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

    live = list(processor.state.iter_active_raids())
    assert len(live) == 1
    assert live[0]["raid_id"] == "R1"
    assert live[0]["confirmation_ts_ns"] == 120
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
    processor.on_one_minute_bar(
        BarRecord(0, first["open"], first["high"], first["low"], first["close"], 1.0, 1)
    )
    processor.on_one_minute_bar(
        BarRecord(
            MINUTE_NS,
            returned["open"],
            returned["high"],
            returned["low"],
            returned["close"],
            1.0,
            1,
        )
    )
    processor.on_one_minute_bar(
        BarRecord(
            2 * MINUTE_NS,
            recross["open"],
            recross["high"],
            recross["low"],
            recross["close"],
            1.0,
            1,
        )
    )
    processor.finish(2 * MINUTE_NS)

    assert [row["prior_raid_count"] for row in sinks.raids.rows] == [0, 1]


def test_processor_accepts_market_closure_gaps_but_rejects_non_increasing_chronology(
    tmp_path: Path,
) -> None:
    """Observed market bars may skip closed minutes but cannot duplicate or reverse time."""
    processor, _ = make_processor(tmp_path)
    with pytest.raises(ValueError, match="source_bars"):
        processor.on_one_minute_bar(BarRecord(0, 100.0, 100.0, 100.0, 100.0, 1.0, 2))
    with pytest.raises(ValueError, match="aligned"):
        processor.on_one_minute_bar(BarRecord(1, 100.0, 100.0, 100.0, 100.0, 1.0, 1))
    processor.on_one_minute_bar(BarRecord(0, 100.0, 100.0, 100.0, 100.0, 1.0, 1))
    processor.on_one_minute_bar(
        BarRecord(2 * MINUTE_NS, 100.0, 100.0, 100.0, 100.0, 1.0, 1)
    )
    with pytest.raises(ValueError, match="strictly increasing"):
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
    generation, _bin_width = processor._profiles.start(
        "R1", 1, excursion_price=101.0, atr_unit=1.0
    )
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


def test_processor_uses_closed_one_hour_and_four_hour_references(tmp_path: Path) -> None:
    """A 1H/4H event is unavailable until its completed reference closes."""
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

    four_hour, _ = make_processor(tmp_path / "four_hour", observation_minutes=60)
    four_hour.state.insert_raid(
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
    four_hour._previous_reference = BarRecord(240, 100.0, 101.0, 100.0, 100.5, 1.0, 240)
    four_hour._on_reference_bar(BarRecord(480, 100.0, 100.0, 99.0, 99.5, 1.0, 240))
    assert next(four_hour.state.iter_active_raids())["confirmation_ts_ns"] == 480


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


def test_strong_move_compares_post_confirmation_swing_to_excursion(
    tmp_path: Path,
) -> None:
    """strong_move uses post-confirmation swing vs max excursion, both in ATR units."""
    processor, sinks = make_processor(tmp_path)
    processor._atr._atr = 1.0
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
            "confirmation_ts_ns": 50,
            "primary_attribution": True,
            "max_price": 101.0,
            "max_excursion": 1.0,
            "raid_atr": 1.0,
            "swing_extreme": 97.0,
            "profile_generation": None,
            "profile_finalized": True,
            "active": 1,
        }
    )
    processor._terminal_raid(
        next(processor.state.iter_active_raids()),
        "COMPLETED",
        endpoint_ts_ns=180,
    )
    row = sinks.raids.rows[0]
    assert row["max_excursion_atr"] == 1.0
    assert row["max_excursion_bps"] == 100.0
    assert row["swing_price"] == 3.0
    assert row["swing_bps"] == 300.0
    assert row["swing_atr"] == 3.0
    assert row["strong_move"] is True


def test_raid_start_and_return_use_source_one_minute_bars(tmp_path: Path) -> None:
    """Golden T1: separate 1m excursion and later 1m return form a completed raid."""
    processor, sinks = make_processor(tmp_path)
    processor.seed_level("L1", price=100.0, side="HIGH")
    # First source minute: strict high excursion only.
    processor.on_one_minute_bar(BarRecord(0, 100.5, 101.2, 100.5, 101.0, 1.0, 1))
    open_raids = list(processor.state.iter_active_raids())
    assert len(open_raids) == 1
    assert open_raids[0]["return_ts_ns"] is None
    assert open_raids[0]["max_excursion"] == pytest.approx(1.2)
    # Later source minute: inclusive return.
    processor.on_one_minute_bar(BarRecord(MINUTE_NS, 100.5, 100.5, 100.0, 100.0, 1.0, 1))
    open_raids = list(processor.state.iter_active_raids())
    assert len(open_raids) == 1
    assert open_raids[0]["return_ts_ns"] == MINUTE_NS
    processor.finish(MINUTE_NS)
    assert sinks.raids.rows[0]["status"] == "RIGHT_CENSORED_CONFIRMATION"
    assert sinks.raids.rows[0]["prior_raid_count"] == 0


def test_processor_creates_previous_period_levels_without_seed(tmp_path: Path) -> None:
    """Production catalogue must create PREVIOUS_1H levels after a completed hour."""
    processor, sinks = make_processor(tmp_path)
    for minute in range(60):
        processor.on_one_minute_bar(
            BarRecord(minute * MINUTE_NS, 100.0, 101.0, 99.0, 100.0, 1.0, 1)
        )
    active = list(processor.state.iter_active_levels())
    assert len(active) == 2
    sides = {row["side"]: row for row in active}
    assert sides["HIGH"]["price"] == 101.0
    assert sides["LOW"]["price"] == 99.0
    assert all(row["source_configuration"] == "PREVIOUS_1H" for row in active)
    assert any(
        event["event_type"] == "LEVEL_CREATED" for event in sinks.event_log.rows
    )


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
        processor.on_one_minute_bar(BarRecord(0, 100.8, 101.0, 100.5, 100.8, 1.0, 1))
        processor.on_one_minute_bar(
            BarRecord(MINUTE_NS, 99.8, 100.0, 99.0, 99.5, 1.0, 1)
        )
        processor.finish(MINUTE_NS)
        return {
            name: (path / f"{name}.jsonl").read_bytes()
            for name in ("bar_marks", "levels", "raids", "tpo_profiles", "event_log")
        }, processor.snapshot()

    first_outputs, first_snapshot = replay(tmp_path / "first")
    second_outputs, second_snapshot = replay(tmp_path / "second")

    assert first_outputs == second_outputs
    assert first_snapshot["open_levels"] == second_snapshot["open_levels"] == 0
    assert first_snapshot["open_raids"] == second_snapshot["open_raids"] == 0
