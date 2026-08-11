from __future__ import annotations

import sqlite3
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
        first = store.new_profile_generation("R1")
        store.upsert_profile_bins("R1", first, {0: 2, 1: 1})
        second = store.new_profile_generation("R1")
        store.upsert_profile_bins("R1", second, {3: 4})

        assert list(store.iter_profile_bins("R1", first)) == []
        assert list(store.iter_profile_bins("R1", second)) == [(3, 4)]
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


def test_profile_generation_reset_rolls_back_to_old_state_on_failure(
    tmp_path: Path,
) -> None:
    """A failed reset leaves the old generation and bins usable."""
    store = Exp100StateStore(tmp_path / "state.sqlite")
    try:
        first = store.start_profile_generation("R1", 1, 0.1)
        store.increment_profile_bin_range("R1", first, 0, 0)
        store._connection.execute(
            """
            CREATE TRIGGER fail_new_profile_state
            BEFORE INSERT ON profile_state
            WHEN NEW.generation = 2
            BEGIN
                SELECT RAISE(ABORT, 'injected profile reset failure');
            END;
            """
        )
        store._connection.commit()

        with pytest.raises(sqlite3.IntegrityError, match="injected"):
            store.reset_profile_generation("R1", 2, 0.1)

        assert store.current_profile_generation("R1") == first
        assert list(store.iter_profile_bins("R1", first)) == [(0, 1)]
        assert store.get_profile_state("R1", first) == {
            "profile_start_ts_ns": 1,
            "bin_width": 0.1,
            "bracket_count": 1,
            "expected_tpo_total": 1,
        }
    finally:
        store.close()
