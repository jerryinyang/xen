"""In-memory live state for one EXP-100 cell.

Keeps the same public API as the earlier SQLite store, but holds active levels,
raids, and sparse TPO bins in process memory.  Hot-path TPO updates no longer
cross the Python↔SQLite boundary every source minute.

The store still supports nested source-bar transactions with outer rollback so
processor exception paths remain atomic.
"""

from __future__ import annotations

import hashlib
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping


SCHEMA_VERSION = 1


class Exp100StateStore:
    """In-memory state store with cursor-style active-state iteration."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Keep a durable marker so runners that inspect the path still work.
        if not self.path.exists():
            self.path.write_bytes(b"exp100-memory-state\n")
        self._closed = False
        self._transaction_depth = 0

        self._levels: dict[str, dict[str, Any]] = {}
        self._raids: dict[str, dict[str, Any]] = {}
        self._active_level_ids: set[str] = set()
        self._active_raid_ids: set[str] = set()
        self._raid_history: dict[str, tuple[str, str | None]] = {}
        self._history_by_level: dict[str, set[str]] = {}

        self._profile_meta: dict[str, int] = {}
        self._profile_state: dict[str, dict[str, Any]] = {}
        self._profile_bins: dict[str, dict[int, int]] = {}
        self._profile_gap_bins: dict[str, set[int]] = {}
        self._bytes_estimate = 64

    @staticmethod
    def _active_flag(data: Mapping[str, Any]) -> int:
        active_value = data.get("active", True)
        if isinstance(active_value, bool):
            return 1 if active_value else 0
        if isinstance(active_value, int) and active_value in {0, 1}:
            return active_value
        raise ValueError("active must be a bool or integer 0/1")

    @staticmethod
    def _event_identity(data: Mapping[str, Any]) -> str | None:
        event_identity = data.get("event_identity")
        if event_identity is not None and not isinstance(event_identity, str):
            return str(event_identity)
        return event_identity if isinstance(event_identity, str) or event_identity is None else str(
            event_identity
        )

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("state store is closed")

    def _touch_bytes(self, delta: int = 0) -> None:
        self._bytes_estimate = max(64, self._bytes_estimate + int(delta))

    @contextmanager
    def source_bar_transaction(self) -> Iterator[None]:
        """Group one source minute's mutations.

        The memory backend does not snapshot/rollback live state.  A failed
        cell is discarded; cloning every open raid and bin map each minute was
        the dominant cost after the SQLite→memory move.
        """
        with self._transaction(immediate=True):
            yield

    @contextmanager
    def _transaction(self, *, immediate: bool) -> Iterator[None]:
        del immediate  # memory backend has no lock mode
        self._require_open()
        self._transaction_depth += 1
        try:
            yield
        finally:
            self._transaction_depth -= 1

    def _commit_if_standalone(self) -> None:
        return None

    def iter_active_levels(self) -> Iterator[dict[str, Any]]:
        self._require_open()
        for level_id in sorted(self._active_level_ids):
            yield self._levels[level_id]

    def insert_level(self, row: Mapping[str, Any]) -> None:
        self._require_open()
        level_id = row.get("level_id")
        if not isinstance(level_id, str) or not level_id:
            raise ValueError("level rows require a non-empty level_id")
        active = self._active_flag(row)
        data = dict(row)
        data["level_id"] = level_id
        data["active"] = active
        if "event_identity" in row:
            data["event_identity"] = self._event_identity(row)
        existed = level_id in self._levels
        self._levels[level_id] = data
        if active:
            self._active_level_ids.add(level_id)
        else:
            self._active_level_ids.discard(level_id)
        if not existed:
            self._touch_bytes(256)
        self._commit_if_standalone()

    def update_level(self, level_id: str, fields: Mapping[str, Any]) -> None:
        if "level_id" in fields:
            raise ValueError("level_id is immutable")
        self._update_entity(self._levels, self._active_level_ids, level_id, fields)

    def delete_level(self, level_id: str) -> None:
        self._require_open()
        self._levels.pop(level_id, None)
        self._active_level_ids.discard(level_id)
        self._touch_bytes(-128)
        self._commit_if_standalone()

    def iter_active_raids(self) -> Iterator[dict[str, Any]]:
        self._require_open()
        for raid_id in sorted(self._active_raid_ids):
            yield self._raids[raid_id]

    def count_active_raids(self) -> int:
        self._require_open()
        return len(self._active_raid_ids)

    def count_active_levels(self) -> int:
        self._require_open()
        return len(self._active_level_ids)

    def insert_raid(self, row: Mapping[str, Any]) -> None:
        self._require_open()
        raid_id = row.get("raid_id")
        if not isinstance(raid_id, str) or not raid_id:
            raise ValueError("raid rows require a non-empty raid_id")
        level_id = row.get("level_id")
        if not isinstance(level_id, str) or not level_id:
            raise ValueError("raid rows require a non-empty level_id")
        active = self._active_flag(row)
        data = dict(row)
        data["raid_id"] = raid_id
        data["level_id"] = level_id
        data["active"] = active
        if "event_identity" in row:
            data["event_identity"] = self._event_identity(row)
        existed = raid_id in self._raids
        self._raids[raid_id] = data
        if active:
            self._active_raid_ids.add(raid_id)
        else:
            self._active_raid_ids.discard(raid_id)
        if raid_id not in self._raid_history:
            event_identity = data.get("event_identity")
            identity = event_identity if isinstance(event_identity, str) else None
            self._raid_history[raid_id] = (level_id, identity)
            self._history_by_level.setdefault(level_id, set()).add(raid_id)
            self._touch_bytes(64)
        if not existed:
            self._touch_bytes(512)
        self._commit_if_standalone()

    def update_raid(self, raid_id: str, fields: Mapping[str, Any]) -> None:
        if "raid_id" in fields:
            raise ValueError("raid_id is immutable")
        if "level_id" in fields:
            raise ValueError("raid level_id is immutable")
        self._update_entity(self._raids, self._active_raid_ids, raid_id, fields)

    def delete_raid(self, raid_id: str) -> None:
        self._require_open()
        self._raids.pop(raid_id, None)
        self._active_raid_ids.discard(raid_id)
        self._touch_bytes(-256)
        self._commit_if_standalone()

    def prior_raid_count(self, level_id: str) -> int:
        self._require_open()
        return len(self._history_by_level.get(level_id, ()))

    def upsert_profile_bins(
        self, raid_id: str, generation: int, counts: Mapping[int, int]
    ) -> None:
        self._require_open()
        if generation <= 0:
            raise ValueError("profile generation must be positive")
        current = self._profile_meta.get(raid_id)
        if current != generation:
            # Only the live generation retains bins; foreign generations stay empty.
            self._commit_if_standalone()
            return
        bins = self._profile_bins.setdefault(raid_id, {})
        for bin_index, count in counts.items():
            index = int(bin_index)
            value = int(count)
            if value < 0:
                raise ValueError("profile bin counts cannot be negative")
            if value == 0:
                if bins.pop(index, None) is not None:
                    self._touch_bytes(-16)
            else:
                if index not in bins:
                    self._touch_bytes(16)
                bins[index] = value
        self._commit_if_standalone()

    def iter_profile_bins(self, raid_id: str, generation: int) -> Iterator[tuple[int, int]]:
        self._require_open()
        if self._profile_meta.get(raid_id) != generation:
            return
            yield  # pragma: no cover
        bins = self._profile_bins.get(raid_id, {})
        for bin_index in sorted(bins):
            yield bin_index, bins[bin_index]

    def iter_profile_bins_by_density(
        self, raid_id: str, generation: int, low_bin_index: int, high_bin_index: int
    ) -> Iterator[tuple[int, int]]:
        """Yield stored bins in deterministic low-density order."""
        self._require_open()
        if self._profile_meta.get(raid_id) != generation:
            return
            yield  # pragma: no cover
        bins = self._profile_bins.get(raid_id, {})
        selected = [
            (bin_index, count)
            for bin_index, count in bins.items()
            if low_bin_index <= bin_index <= high_bin_index
        ]
        selected.sort(key=lambda item: (item[1], item[0]))
        yield from selected

    def iter_profile_gap_bins(self, raid_id: str, generation: int) -> Iterator[int]:
        """Yield the exact persisted gap-bin indexes in ascending order."""
        self._require_open()
        if self._profile_meta.get(raid_id) != generation:
            return
            yield  # pragma: no cover
        for bin_index in sorted(self._profile_gap_bins.get(raid_id, ())):
            yield bin_index

    def replace_profile_gap_mask(
        self, raid_id: str, generation: int, bin_indexes: Iterable[int]
    ) -> tuple[int, int | None, int | None, str]:
        """Persist selected bins and return fixed-size count, bounds, and digest."""
        self._require_open()
        if self._profile_meta.get(raid_id) != generation:
            # Still accept write only for the live generation.
            pass
        selected: list[int] = []
        for raw in bin_indexes:
            selected.append(int(raw))
        selected_set = set(selected)
        self._profile_gap_bins[raid_id] = selected_set
        outer_low = min(selected_set) if selected_set else None
        outer_high = max(selected_set) if selected_set else None
        digest = self._profile_gap_digest(raid_id, generation)
        self._touch_bytes(len(selected_set) * 8)
        return len(selected_set), outer_low, outer_high, digest

    def _profile_gap_digest(self, raid_id: str, generation: int) -> str:
        del generation
        digest = hashlib.sha256()
        for bin_index in sorted(self._profile_gap_bins.get(raid_id, ())):
            digest.update(f"{int(bin_index)}\n".encode("ascii"))
        return digest.hexdigest()

    def get_profile_state(self, raid_id: str, generation: int) -> dict[str, int | float] | None:
        """Return one current-generation profile row without scanning bins."""
        self._require_open()
        state = self._profile_state.get(raid_id)
        if state is None or int(state["generation"]) != generation:
            return None
        return {
            "profile_start_ts_ns": int(state["profile_start_ts_ns"]),
            "bin_width": float(state["bin_width"]),
            "bracket_count": int(state["bracket_count"]),
            "expected_tpo_total": int(state["expected_tpo_total"]),
            "start_index": None,
        }

    def current_profile_generation(self, raid_id: str) -> int | None:
        """Return the current profile generation with one keyed lookup."""
        self._require_open()
        return self._profile_meta.get(raid_id)

    def clear_profile_state(self, raid_id: str) -> None:
        """Delete all live profile rows for one terminal raid (idempotent)."""
        self._require_open()
        self._profile_meta.pop(raid_id, None)
        self._profile_state.pop(raid_id, None)
        bins = self._profile_bins.pop(raid_id, None)
        gaps = self._profile_gap_bins.pop(raid_id, None)
        freed = 0
        if bins is not None:
            freed += len(bins) * 16
        if gaps is not None:
            freed += len(gaps) * 8
        self._touch_bytes(-freed)
        self._commit_if_standalone()

    def increment_profile_bin_range(
        self, raid_id: str, generation: int, low_bin_index: int, high_bin_index: int
    ) -> None:
        """Increment each inclusive profile bin and its conservation totals."""
        self.bulk_increment_profile_bin_ranges(
            ((raid_id, generation, low_bin_index, high_bin_index),)
        )

    def bulk_increment_profile_bin_ranges(
        self, ranges: Iterable[tuple[str, int, int, int]]
    ) -> None:
        """Increment inclusive bin ranges for multiple profiles atomically."""
        self._require_open()
        rows = tuple(ranges)
        for raid_id, generation, low_bin_index, high_bin_index in rows:
            if low_bin_index > high_bin_index:
                raise ValueError("profile bin range is inverted")
            if generation <= 0:
                raise ValueError("profile generation must be positive")
            if not raid_id:
                raise ValueError("raid_id must be non-empty")
        for raid_id, generation, low_bin_index, high_bin_index in rows:
            if self._profile_meta.get(raid_id) != generation:
                raise KeyError((raid_id, generation))
            state = self._profile_state.get(raid_id)
            if state is None or int(state["generation"]) != generation:
                raise KeyError((raid_id, generation))
            bins = self._profile_bins.setdefault(raid_id, {})
            for bin_index in range(low_bin_index, high_bin_index + 1):
                if bin_index not in bins:
                    self._touch_bytes(16)
                bins[bin_index] = bins.get(bin_index, 0) + 1
            state["bracket_count"] = int(state["bracket_count"]) + 1
            state["expected_tpo_total"] = int(state["expected_tpo_total"]) + (
                high_bin_index - low_bin_index + 1
            )
        self._commit_if_standalone()

    def estimated_bytes(self) -> int:
        """Return a monotonic O(1) live-state size estimate."""
        self._require_open()
        return int(self._bytes_estimate)

    def profile_bin_count(
        self, raid_id: str, generation: int, bin_index: int
    ) -> int | None:
        """Return a single bin count for cursor-safe value-area expansion."""
        self._require_open()
        if self._profile_meta.get(raid_id) != generation:
            return None
        bins = self._profile_bins.get(raid_id)
        if bins is None:
            return None
        value = bins.get(int(bin_index))
        return None if value is None else int(value)

    def start_profile_generation(
        self, raid_id: str, profile_start_ts_ns: int, bin_width: float
    ) -> int:
        """Create generation one for a previously unseen raid."""
        self._require_open()
        if raid_id in self._profile_meta:
            raise ValueError(f"profile for raid {raid_id} already exists")
        generation = 1
        self._profile_bins.pop(raid_id, None)
        self._profile_gap_bins.pop(raid_id, None)
        self._profile_state[raid_id] = {
            "generation": generation,
            "profile_start_ts_ns": int(profile_start_ts_ns),
            "bin_width": float(bin_width),
            "bracket_count": 0,
            "expected_tpo_total": 0,
        }
        self._profile_meta[raid_id] = generation
        self._profile_bins[raid_id] = {}
        self._touch_bytes(128)
        return generation

    def reset_profile_generation(
        self, raid_id: str, profile_start_ts_ns: int, bin_width: float
    ) -> int:
        """Publish the next generation and drop prior sparse bins."""
        self._require_open()
        current = self._profile_meta.get(raid_id)
        if current is None:
            raise KeyError(raid_id)
        generation = int(current) + 1
        old_bins = self._profile_bins.pop(raid_id, None)
        old_gaps = self._profile_gap_bins.pop(raid_id, None)
        freed = 0
        if old_bins is not None:
            freed += len(old_bins) * 16
        if old_gaps is not None:
            freed += len(old_gaps) * 8
        self._touch_bytes(-freed)
        self._profile_state[raid_id] = {
            "generation": generation,
            "profile_start_ts_ns": int(profile_start_ts_ns),
            "bin_width": float(bin_width),
            "bracket_count": 0,
            "expected_tpo_total": 0,
        }
        self._profile_meta[raid_id] = generation
        self._profile_bins[raid_id] = {}
        return generation

    def new_profile_generation(self, raid_id: str) -> int:
        raise ValueError(
            "new_profile_generation() is unsafe; use "
            "start_profile_generation() or reset_profile_generation()"
        )

    def _update_entity(
        self,
        table: dict[str, dict[str, Any]],
        active_ids: set[str],
        identifier: str,
        fields: Mapping[str, Any],
    ) -> None:
        self._require_open()
        if not fields:
            return
        data = table.get(identifier)
        if data is None:
            raise KeyError(identifier)
        data.update(fields)
        if "active" in fields:
            active = self._active_flag(data)
            data["active"] = active
            if active:
                active_ids.add(identifier)
            else:
                active_ids.discard(identifier)
        if "event_identity" in fields:
            data["event_identity"] = self._event_identity(data)
        self._commit_if_standalone()

    def close(self) -> None:
        self._closed = True

    def __enter__(self) -> "Exp100StateStore":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()
