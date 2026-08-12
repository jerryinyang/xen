from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest

from xen.exp100.state_store import Exp100StateStore


class _CountingConnection:
    """Delegate to a real SQLite connection while counting write API calls."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.execute_calls = 0
        self.executemany_calls = 0

    def execute(
        self, sql: str, parameters: tuple[object, ...] = ()
    ) -> sqlite3.Cursor:
        self.execute_calls += 1
        return self.connection.execute(sql, parameters)

    def executemany(
        self, sql: str, parameters: Iterable[tuple[object, ...]]
    ) -> sqlite3.Cursor:
        self.executemany_calls += 1
        return self.connection.executemany(sql, parameters)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.connection, name)


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


def test_source_bar_transaction_commits_mutations_together(tmp_path: Path) -> None:
    """Level and raid changes from one source bar become visible together."""
    path = tmp_path / "state.sqlite"
    with Exp100StateStore(path) as store, sqlite3.connect(path) as observer:
        with store.source_bar_transaction():
            store.insert_level({"level_id": "L1", "price": 100.0, "active": 1})
            store.insert_raid({"raid_id": "R1", "level_id": "L1", "active": 1})

            assert observer.execute("SELECT COUNT(*) FROM levels").fetchone()[0] == 0
            assert observer.execute("SELECT COUNT(*) FROM raids").fetchone()[0] == 0

        assert observer.execute("SELECT COUNT(*) FROM levels").fetchone()[0] == 1
        assert observer.execute("SELECT COUNT(*) FROM raids").fetchone()[0] == 1


def test_source_bar_transaction_rolls_back_nested_profile_mutations(
    tmp_path: Path,
) -> None:
    """A failed source minute leaves no partial raid or profile state."""
    path = tmp_path / "state.sqlite"
    with Exp100StateStore(path) as store:
        with pytest.raises(RuntimeError, match="injected"):
            with store.source_bar_transaction():
                store.insert_raid({"raid_id": "R1", "level_id": "L1", "active": 1})
                generation = store.start_profile_generation("R1", 1, 0.1)
                store.increment_profile_bin_range("R1", generation, 0, 2)
                raise RuntimeError("injected")

        assert list(store.iter_active_raids()) == []
        assert store.current_profile_generation("R1") is None
        assert list(store.iter_profile_bins("R1", 1)) == []


def test_standalone_mutation_remains_immediately_committed(tmp_path: Path) -> None:
    """Callers outside source processing retain the existing auto-commit contract."""
    path = tmp_path / "state.sqlite"
    with Exp100StateStore(path) as store, sqlite3.connect(path) as observer:
        store.insert_level({"level_id": "L1", "price": 100.0, "active": 1})

        assert observer.execute("SELECT COUNT(*) FROM levels").fetchone()[0] == 1


def test_profile_range_uses_one_streaming_bulk_call(tmp_path: Path) -> None:
    """A bin range crosses Python's SQLite boundary once without changing counts."""
    store = Exp100StateStore(tmp_path / "state.sqlite")
    try:
        generation = store.start_profile_generation("R1", 1, 0.1)
        counting = _CountingConnection(store._connection)
        store._connection = counting

        store.increment_profile_bin_range("R1", generation, -2, 3)

        assert counting.executemany_calls == 1
        assert counting.execute_calls == 2
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
        }
    finally:
        store.close()


def test_count_active_raids_reports_only_active_rows(tmp_path: Path) -> None:
    """Operational raid counts use the active flag without decoding each payload."""
    with Exp100StateStore(tmp_path / "state.sqlite") as store:
        store.insert_raid({"raid_id": "R1", "level_id": "L1", "active": 1})
        store.insert_raid({"raid_id": "R2", "level_id": "L1", "active": 0})

        assert store.count_active_raids() == 1
