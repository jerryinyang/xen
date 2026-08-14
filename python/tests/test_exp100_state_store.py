from __future__ import annotations

from pathlib import Path

import pytest

from xen.exp100.state_store import Exp100StateStore


def test_state_store_iterates_active_levels_without_materializing_all_rows(tmp_path: Path) -> None:
    store = Exp100StateStore(tmp_path / "state.sqlite")
    try:
        for i in range(10_000):
            store.insert_level(
                {
                    "level_id": f"L{i}",
                    "price": 100.0 + i,
                    "side": "HIGH",
                    "active": 1,
                }
            )

        rows = store.iter_active_levels()
        assert not isinstance(rows, list)
        assert next(rows)["level_id"] == "L0"
        assert store.prior_raid_count("L0") == 0
    finally:
        store.close()


def test_profile_generation_replaces_active_bins_without_python_history(tmp_path: Path) -> None:
    store = Exp100StateStore(tmp_path / "state.sqlite")
    try:
        store.insert_raid({"raid_id": "R1", "level_id": "L1", "active": 1})
        first = store.start_profile_generation("R1", 1, 0.1)
        store.upsert_profile_bins("R1", first, {0: 2, 1: 1})
        second = store.reset_profile_generation("R1", 2, 0.1)
        store.upsert_profile_bins("R1", second, {3: 4})

        assert list(store.iter_profile_bins("R1", first)) == []
        assert list(store.iter_profile_bins("R1", second)) == [(3, 4)]
    finally:
        store.close()


def test_clear_profile_state_is_atomic_and_idempotent(tmp_path: Path) -> None:
    """Terminal cleanup removes all profile rows and accepts a second call."""
    store = Exp100StateStore(tmp_path / "state.sqlite")
    try:
        generation = store.start_profile_generation("R1", 1, 0.1)
        store.increment_profile_bin_range("R1", generation, 0, 1)
        store.clear_profile_state("R1")
        store.clear_profile_state("R1")

        assert store.current_profile_generation("R1") is None
        assert store.get_profile_state("R1", generation) is None
        assert list(store.iter_profile_bins("R1", generation)) == []
        assert list(store.iter_profile_gap_bins("R1", generation)) == []
    finally:
        store.close()


def test_legacy_profile_generation_entry_point_rejects_unsafe_use(
    tmp_path: Path,
) -> None:
    store = Exp100StateStore(tmp_path / "state.sqlite")
    try:
        with pytest.raises(ValueError, match="start_profile_generation.*reset_profile_generation"):
            store.new_profile_generation("R1")
    finally:
        store.close()


def test_state_store_rejects_level_identity_changes(tmp_path: Path) -> None:
    store = Exp100StateStore(tmp_path / "state.sqlite")
    try:
        store.insert_level({"level_id": "L1", "price": 100.0, "active": 1})
        with pytest.raises(ValueError, match="immutable"):
            store.update_level("L1", {"level_id": "L2"})
        assert next(store.iter_active_levels())["level_id"] == "L1"
    finally:
        store.close()


def test_state_store_rejects_raid_and_level_identity_changes(tmp_path: Path) -> None:
    store = Exp100StateStore(tmp_path / "state.sqlite")
    try:
        store.insert_raid({"raid_id": "R1", "level_id": "L1", "active": 1})
        with pytest.raises(ValueError, match="immutable"):
            store.update_raid("R1", {"raid_id": "R2"})
        with pytest.raises(ValueError, match="immutable"):
            store.update_raid("R1", {"level_id": "L2"})
        assert next(store.iter_active_raids())["raid_id"] == "R1"
        assert next(store.iter_active_raids())["level_id"] == "L1"
    finally:
        store.close()


def test_state_store_rejects_textual_active_flag(tmp_path: Path) -> None:
    store = Exp100StateStore(tmp_path / "state.sqlite")
    try:
        with pytest.raises(ValueError, match="active"):
            store.insert_level({"level_id": "L0", "active": "0"})
    finally:
        store.close()


def test_active_iterators_yield_live_rows(tmp_path: Path) -> None:
    """Hot iterators expose live rows; writers still go through update_*."""
    with Exp100StateStore(tmp_path / "state.sqlite") as store:
        store.insert_level({"level_id": "L1", "price": 100.0, "beyond": False, "active": 1})
        store.insert_raid({"raid_id": "R1", "level_id": "L1", "active": 1})
        level = next(store.iter_active_levels())
        raid = next(store.iter_active_raids())
        store.update_level("L1", {"beyond": True})
        store.update_raid("R1", {"return_ts_ns": 99})
        assert level["beyond"] is True
        assert raid["return_ts_ns"] == 99


def test_profile_range_increments_membership_and_conservation(tmp_path: Path) -> None:
    """A bin range updates sparse membership and conservation counters once."""
    store = Exp100StateStore(tmp_path / "state.sqlite")
    try:
        generation = store.start_profile_generation("R1", 1, 0.1)
        store.increment_profile_bin_range("R1", generation, -2, 3)

        assert list(store.iter_profile_bins("R1", generation)) == [
            (-2, 1),
            (-1, 1),
            (0, 1),
            (1, 1),
            (2, 1),
            (3, 1),
        ]
        assert store.get_profile_state("R1", generation) == {
            "profile_start_ts_ns": 1,
            "bin_width": 0.1,
            "bracket_count": 1,
            "expected_tpo_total": 6,
            "start_index": None,
        }
    finally:
        store.close()


def test_count_active_raids_reports_only_active_rows(tmp_path: Path) -> None:
    """Operational raid counts use the active flag without decoding each payload."""
    with Exp100StateStore(tmp_path / "state.sqlite") as store:
        store.insert_raid({"raid_id": "R1", "level_id": "L1", "active": 1})
        store.insert_raid({"raid_id": "R2", "level_id": "L1", "active": 0})

        assert store.count_active_raids() == 1


def test_count_active_levels_reports_only_active_rows(tmp_path: Path) -> None:
    """Operational level counts use the active flag without decoding each payload."""
    with Exp100StateStore(tmp_path / "state.sqlite") as store:
        store.insert_level({"level_id": "L1", "active": 1})
        store.insert_level({"level_id": "L2", "active": 0})

        assert store.count_active_levels() == 1


def test_bulk_profile_ranges_match_repeated_single_increments(tmp_path: Path) -> None:
    """Multi-raid bulk bin writes preserve per-raid membership and conservation."""
    with Exp100StateStore(tmp_path / "state.sqlite") as store:
        first = store.start_profile_generation("R1", 1, 0.1)
        second = store.start_profile_generation("R2", 1, 0.1)
        store.bulk_increment_profile_bin_ranges(
            (
                ("R1", first, 0, 2),
                ("R2", second, -1, 0),
            )
        )

        assert list(store.iter_profile_bins("R1", first)) == [(0, 1), (1, 1), (2, 1)]
        assert list(store.iter_profile_bins("R2", second)) == [(-1, 1), (0, 1)]
        assert store.get_profile_state("R1", first) == {
            "profile_start_ts_ns": 1,
            "bin_width": 0.1,
            "bracket_count": 1,
            "expected_tpo_total": 3,
            "start_index": None,
        }
        assert store.get_profile_state("R2", second) == {
            "profile_start_ts_ns": 1,
            "bin_width": 0.1,
            "bracket_count": 1,
            "expected_tpo_total": 2,
            "start_index": None,
        }


def test_estimated_bytes_is_non_negative_page_estimate(tmp_path: Path) -> None:
    """Hot-path telemetry must stay O(1); it reports allocated page bytes."""
    with Exp100StateStore(tmp_path / "state.marker") as store:
        before = store.estimated_bytes()
        assert before >= 0
        generation = store.start_profile_generation("R1", 1, 0.1)
        store.increment_profile_bin_range("R1", generation, 0, 99)
        after = store.estimated_bytes()
        assert after >= before
