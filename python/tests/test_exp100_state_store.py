from __future__ import annotations

from pathlib import Path

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
