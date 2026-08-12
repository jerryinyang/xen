"""Disk-backed live state for one EXP-100 cell.

The store deliberately keeps JSON payloads behind keyed SQLite rows.  The
active iterators yield one decoded row at a time; no method materializes the
active state or profile history in Python.
"""

from __future__ import annotations

import json
import hashlib
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping


SCHEMA_VERSION = 1


class Exp100StateStore:
    """SQLite state store with cursor-based active-state iteration."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path)
        self._connection.row_factory = sqlite3.Row
        self._transaction_depth = 0
        self._connection.execute("PRAGMA journal_mode=DELETE")
        self._connection.execute("PRAGMA synchronous=NORMAL")
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS levels (
                level_id TEXT PRIMARY KEY,
                active INTEGER NOT NULL,
                event_identity TEXT,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS raids (
                raid_id TEXT PRIMARY KEY,
                level_id TEXT NOT NULL,
                active INTEGER NOT NULL,
                event_identity TEXT,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS raid_history (
                raid_id TEXT PRIMARY KEY,
                level_id TEXT NOT NULL,
                event_identity TEXT
            );
            CREATE TABLE IF NOT EXISTS profile_meta (
                raid_id TEXT PRIMARY KEY,
                generation INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS profile_bins (
                raid_id TEXT NOT NULL,
                generation INTEGER NOT NULL,
                bin_index INTEGER NOT NULL,
                count INTEGER NOT NULL,
                PRIMARY KEY (raid_id, generation, bin_index)
            );
            CREATE TABLE IF NOT EXISTS profile_state (
                raid_id TEXT PRIMARY KEY,
                generation INTEGER NOT NULL,
                profile_start_ts_ns INTEGER NOT NULL,
                bin_width REAL NOT NULL,
                bracket_count INTEGER NOT NULL,
                expected_tpo_total INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS profile_gap_bins (
                raid_id TEXT NOT NULL,
                generation INTEGER NOT NULL,
                bin_index INTEGER NOT NULL,
                PRIMARY KEY (raid_id, generation, bin_index)
            );
            CREATE INDEX IF NOT EXISTS levels_active_idx ON levels(active, level_id);
            CREATE INDEX IF NOT EXISTS levels_event_idx ON levels(event_identity);
            CREATE INDEX IF NOT EXISTS raids_active_idx ON raids(active, raid_id);
            CREATE INDEX IF NOT EXISTS raids_level_idx ON raids(level_id, raid_id);
            CREATE INDEX IF NOT EXISTS raids_event_idx ON raids(event_identity);
            CREATE INDEX IF NOT EXISTS history_level_idx ON raid_history(level_id, raid_id);
            """
        )
        cursor = self._connection.execute(
            "SELECT value FROM schema_meta WHERE key = 'schema_version'"
        )
        row = cursor.fetchone()
        cursor.close()
        if row is not None and int(row[0]) != SCHEMA_VERSION:
            self._connection.close()
            raise RuntimeError(f"unsupported EXP-100 state schema version: {row[0]}")
        self._connection.execute(
            "INSERT OR REPLACE INTO schema_meta(key, value) "
            "VALUES('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        self._connection.commit()
        self._closed = False

    @staticmethod
    def _payload(
        row: Mapping[str, Any], identifier_key: str
    ) -> tuple[str, str | None, int, str]:
        data = dict(row)
        identifier = data.get(identifier_key)
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("state rows require a non-empty level_id or raid_id")
        active_value = data.get("active", 1)
        if isinstance(active_value, bool):
            active = int(active_value)
        elif isinstance(active_value, int) and active_value in {0, 1}:
            active = active_value
        else:
            raise ValueError("active must be a bool or integer 0/1")
        event_identity = data.get("event_identity")
        if event_identity is not None and not isinstance(event_identity, str):
            event_identity = str(event_identity)
        return identifier, event_identity, active, json.dumps(
            data, sort_keys=True, separators=(",", ":"), default=str
        )

    @staticmethod
    def _decode(payload: str) -> dict[str, Any]:
        value = json.loads(payload)
        if not isinstance(value, dict):
            raise RuntimeError("state payload is not an object")
        return value

    @contextmanager
    def source_bar_transaction(self) -> Iterator[None]:
        """Commit all SQLite mutations for one source minute together."""
        with self._transaction(immediate=True):
            yield

    @contextmanager
    def _transaction(self, *, immediate: bool) -> Iterator[None]:
        outer = self._transaction_depth == 0
        if outer:
            self._connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
        self._transaction_depth += 1
        try:
            yield
        except Exception:
            self._transaction_depth -= 1
            if outer:
                self._connection.rollback()
            raise
        else:
            self._transaction_depth -= 1
            if outer:
                self._connection.commit()

    def _commit_if_standalone(self) -> None:
        if self._transaction_depth == 0:
            self._connection.commit()

    def iter_active_levels(self) -> Iterator[dict[str, Any]]:
        cursor = self._connection.execute(
            "SELECT payload FROM levels WHERE active = 1 ORDER BY level_id"
        )
        try:
            for row in cursor:
                yield self._decode(row[0])
        finally:
            if not self._closed:
                cursor.close()

    def insert_level(self, row: Mapping[str, Any]) -> None:
        level_id, event_identity, active, payload = self._payload(row, "level_id")
        self._connection.execute(
            """
            INSERT INTO levels(level_id, active, event_identity, payload)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(level_id) DO UPDATE SET
                active = excluded.active,
                event_identity = excluded.event_identity,
                payload = excluded.payload
            """,
            (level_id, active, event_identity, payload),
        )
        self._commit_if_standalone()

    def update_level(self, level_id: str, fields: Mapping[str, Any]) -> None:
        if "level_id" in fields:
            raise ValueError("level_id is immutable")
        self._update_state("levels", "level_id", level_id, fields)

    def delete_level(self, level_id: str) -> None:
        self._connection.execute("DELETE FROM levels WHERE level_id = ?", (level_id,))
        self._commit_if_standalone()

    def iter_active_raids(self) -> Iterator[dict[str, Any]]:
        cursor = self._connection.execute(
            "SELECT payload FROM raids WHERE active = 1 ORDER BY raid_id"
        )
        try:
            for row in cursor:
                yield self._decode(row[0])
        finally:
            if not self._closed:
                cursor.close()

    def count_active_raids(self) -> int:
        """Return the active-raid count without decoding JSON payloads."""
        cursor = self._connection.execute("SELECT COUNT(*) FROM raids WHERE active = 1")
        row = cursor.fetchone()
        cursor.close()
        return int(row[0]) if row is not None else 0

    def insert_raid(self, row: Mapping[str, Any]) -> None:
        raid_id, event_identity, active, payload = self._payload(row, "raid_id")
        level_id = row.get("level_id")
        if not isinstance(level_id, str) or not level_id:
            raise ValueError("raid rows require a non-empty level_id")
        self._connection.execute(
            """
            INSERT INTO raids(raid_id, level_id, active, event_identity, payload)
            VALUES(?, ?, ?, ?, ?)
            ON CONFLICT(raid_id) DO UPDATE SET
                level_id = excluded.level_id,
                active = excluded.active,
                event_identity = excluded.event_identity,
                payload = excluded.payload
            """,
            (raid_id, level_id, active, event_identity, payload),
        )
        self._connection.execute(
            """
            INSERT OR IGNORE INTO raid_history(raid_id, level_id, event_identity)
            VALUES(?, ?, ?)
            """,
            (raid_id, level_id, event_identity),
        )
        self._commit_if_standalone()

    def update_raid(self, raid_id: str, fields: Mapping[str, Any]) -> None:
        if "raid_id" in fields:
            raise ValueError("raid_id is immutable")
        if "level_id" in fields:
            raise ValueError("raid level_id is immutable")
        self._update_state("raids", "raid_id", raid_id, fields)

    def delete_raid(self, raid_id: str) -> None:
        self._connection.execute("DELETE FROM raids WHERE raid_id = ?", (raid_id,))
        self._commit_if_standalone()

    def prior_raid_count(self, level_id: str) -> int:
        cursor = self._connection.execute(
            "SELECT COUNT(*) FROM raid_history WHERE level_id = ?", (level_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        return int(row[0]) if row is not None else 0

    def upsert_profile_bins(
        self, raid_id: str, generation: int, counts: Mapping[int, int]
    ) -> None:
        if generation <= 0:
            raise ValueError("profile generation must be positive")
        for bin_index, count in counts.items():
            index = int(bin_index)
            value = int(count)
            if value < 0:
                raise ValueError("profile bin counts cannot be negative")
            if value == 0:
                self._connection.execute(
                    "DELETE FROM profile_bins WHERE raid_id = ? AND generation = ? AND bin_index = ?",
                    (raid_id, generation, index),
                )
            else:
                self._connection.execute(
                    """
                    INSERT INTO profile_bins(raid_id, generation, bin_index, count)
                    VALUES(?, ?, ?, ?)
                    ON CONFLICT(raid_id, generation, bin_index) DO UPDATE SET
                        count = excluded.count
                    """,
                    (raid_id, generation, index, value),
                )
        self._commit_if_standalone()

    def iter_profile_bins(self, raid_id: str, generation: int) -> Iterator[tuple[int, int]]:
        cursor = self._connection.execute(
            """
            SELECT bin_index, count FROM profile_bins
            WHERE raid_id = ? AND generation = ?
            ORDER BY bin_index
            """,
            (raid_id, generation),
        )
        try:
            for row in cursor:
                yield int(row[0]), int(row[1])
        finally:
            cursor.close()

    def iter_profile_bins_by_density(
        self, raid_id: str, generation: int, low_bin_index: int, high_bin_index: int
    ) -> Iterator[tuple[int, int]]:
        """Yield stored bins in deterministic low-density order."""
        cursor = self._connection.execute(
            """
            SELECT bin_index, count FROM profile_bins
            WHERE raid_id = ? AND generation = ?
              AND bin_index BETWEEN ? AND ?
            ORDER BY count, bin_index
            """,
            (raid_id, generation, low_bin_index, high_bin_index),
        )
        try:
            for row in cursor:
                yield int(row[0]), int(row[1])
        finally:
            cursor.close()

    def iter_profile_gap_bins(self, raid_id: str, generation: int) -> Iterator[int]:
        """Yield the exact persisted gap-bin indexes in ascending order."""
        cursor = self._connection.execute(
            """
            SELECT bin_index FROM profile_gap_bins
            WHERE raid_id = ? AND generation = ?
            ORDER BY bin_index
            """,
            (raid_id, generation),
        )
        try:
            for row in cursor:
                yield int(row[0])
        finally:
            cursor.close()

    def replace_profile_gap_mask(
        self, raid_id: str, generation: int, bin_indexes: Iterable[int]
    ) -> tuple[int, int | None, int | None, str]:
        """Persist selected bins and return fixed-size count, bounds, and digest."""
        with self._transaction(immediate=True):
            self._connection.execute(
                "DELETE FROM profile_gap_bins WHERE raid_id = ? AND generation = ?",
                (raid_id, generation),
            )
            selected_count = 0
            outer_low: int | None = None
            outer_high: int | None = None
            for raw_bin_index in bin_indexes:
                bin_index = int(raw_bin_index)
                self._connection.execute(
                    """
                    INSERT INTO profile_gap_bins(raid_id, generation, bin_index)
                    VALUES(?, ?, ?)
                    """,
                    (raid_id, generation, bin_index),
                )
                selected_count += 1
                outer_low = (
                    bin_index
                    if outer_low is None
                    else min(outer_low, bin_index)
                )
                outer_high = (
                    bin_index
                    if outer_high is None
                    else max(outer_high, bin_index)
                )
            digest = self._profile_gap_digest(raid_id, generation)
        return selected_count, outer_low, outer_high, digest

    def _profile_gap_digest(self, raid_id: str, generation: int) -> str:
        digest = hashlib.sha256()
        cursor = self._connection.execute(
            """
            SELECT bin_index FROM profile_gap_bins
            WHERE raid_id = ? AND generation = ?
            ORDER BY bin_index
            """,
            (raid_id, generation),
        )
        try:
            for row in cursor:
                digest.update(f"{int(row[0])}\n".encode("ascii"))
        finally:
            cursor.close()
        return digest.hexdigest()

    def get_profile_state(self, raid_id: str, generation: int) -> dict[str, int | float] | None:
        """Return one current-generation profile row without scanning bins."""
        cursor = self._connection.execute(
            """
            SELECT profile_start_ts_ns, bin_width, bracket_count, expected_tpo_total
            FROM profile_state WHERE raid_id = ? AND generation = ?
            """,
            (raid_id, generation),
        )
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            return None
        return {
            "profile_start_ts_ns": int(row[0]),
            "bin_width": float(row[1]),
            "bracket_count": int(row[2]),
            "expected_tpo_total": int(row[3]),
        }

    def current_profile_generation(self, raid_id: str) -> int | None:
        """Return the current profile generation with one keyed query."""
        cursor = self._connection.execute(
            "SELECT generation FROM profile_meta WHERE raid_id = ?", (raid_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        return int(row[0]) if row is not None else None

    def clear_profile_state(self, raid_id: str) -> None:
        """Atomically delete all live profile rows for one terminal raid.

        Deleting an already-cleared profile is deliberately a no-op so a caller
        can safely resume terminal cleanup after an interrupted output path.
        """
        with self._transaction(immediate=True):
            self._connection.execute("DELETE FROM profile_bins WHERE raid_id = ?", (raid_id,))
            self._connection.execute(
                "DELETE FROM profile_gap_bins WHERE raid_id = ?", (raid_id,)
            )
            self._connection.execute("DELETE FROM profile_state WHERE raid_id = ?", (raid_id,))
            self._connection.execute("DELETE FROM profile_meta WHERE raid_id = ?", (raid_id,))

    def increment_profile_bin_range(
        self, raid_id: str, generation: int, low_bin_index: int, high_bin_index: int
    ) -> None:
        """Increment each inclusive profile bin and its durable conservation totals."""
        if low_bin_index > high_bin_index:
            raise ValueError("profile bin range is inverted")
        with self._transaction(immediate=False):
            self._connection.executemany(
                """
                INSERT INTO profile_bins(raid_id, generation, bin_index, count)
                VALUES(?, ?, ?, 1)
                ON CONFLICT(raid_id, generation, bin_index) DO UPDATE SET
                    count = profile_bins.count + 1
                """,
                (
                    (raid_id, generation, bin_index)
                    for bin_index in range(low_bin_index, high_bin_index + 1)
                ),
            )
            cursor = self._connection.execute(
                """
                UPDATE profile_state
                SET bracket_count = bracket_count + 1,
                    expected_tpo_total = expected_tpo_total + ?
                WHERE raid_id = ? AND generation = ?
                """,
                (high_bin_index - low_bin_index + 1, raid_id, generation),
            )
            if cursor.rowcount != 1:
                raise KeyError((raid_id, generation))

    def profile_bin_count(
        self, raid_id: str, generation: int, bin_index: int
    ) -> int | None:
        """Return a single bin count for cursor-safe value-area expansion."""
        cursor = self._connection.execute(
            """
            SELECT count FROM profile_bins
            WHERE raid_id = ? AND generation = ? AND bin_index = ?
            """,
            (raid_id, generation, bin_index),
        )
        row = cursor.fetchone()
        cursor.close()
        return int(row[0]) if row is not None else None

    def start_profile_generation(
        self, raid_id: str, profile_start_ts_ns: int, bin_width: float
    ) -> int:
        """Atomically create generation one for a previously unseen raid."""
        with self._transaction(immediate=True):
            cursor = self._connection.execute(
                "SELECT generation FROM profile_meta WHERE raid_id = ?", (raid_id,)
            )
            row = cursor.fetchone()
            cursor.close()
            if row is not None:
                raise ValueError(f"profile for raid {raid_id} already exists")

            generation = 1
            self._connection.execute(
                "DELETE FROM profile_bins WHERE raid_id = ?", (raid_id,)
            )
            self._connection.execute(
                "DELETE FROM profile_gap_bins WHERE raid_id = ?", (raid_id,)
            )
            self._connection.execute(
                """
                INSERT OR REPLACE INTO profile_state(
                    raid_id, generation, profile_start_ts_ns, bin_width,
                    bracket_count, expected_tpo_total
                ) VALUES(?, ?, ?, ?, 0, 0)
                """,
                (raid_id, generation, profile_start_ts_ns, bin_width),
            )
            self._connection.execute(
                "INSERT INTO profile_meta(raid_id, generation) VALUES(?, ?)",
                (raid_id, generation),
            )
        return generation

    def reset_profile_generation(
        self, raid_id: str, profile_start_ts_ns: int, bin_width: float
    ) -> int:
        """Atomically publish the next generation while retaining rollback safety."""
        with self._transaction(immediate=True):
            cursor = self._connection.execute(
                "SELECT generation FROM profile_meta WHERE raid_id = ?", (raid_id,)
            )
            row = cursor.fetchone()
            cursor.close()
            if row is None:
                raise KeyError(raid_id)
            generation = int(row[0]) + 1

            self._connection.execute(
                """
                INSERT OR REPLACE INTO profile_state(
                    raid_id, generation, profile_start_ts_ns, bin_width,
                    bracket_count, expected_tpo_total
                ) VALUES(?, ?, ?, ?, 0, 0)
                """,
                (raid_id, generation, profile_start_ts_ns, bin_width),
            )
            self._connection.execute(
                "DELETE FROM profile_bins WHERE raid_id = ?", (raid_id,)
            )
            self._connection.execute(
                "DELETE FROM profile_gap_bins WHERE raid_id = ?", (raid_id,)
            )
            self._connection.execute(
                "UPDATE profile_meta SET generation = ? WHERE raid_id = ?",
                (generation, raid_id),
            )
        return generation

    def new_profile_generation(self, raid_id: str) -> int:
        raise ValueError(
            "new_profile_generation() is unsafe; use "
            "start_profile_generation() or reset_profile_generation()"
        )

    def _update_state(
        self, table: str, id_column: str, identifier: str, fields: Mapping[str, Any]
    ) -> None:
        if not fields:
            return
        if table not in {"levels", "raids"}:
            raise ValueError(f"unsupported state table: {table}")
        cursor = self._connection.execute(
            f"SELECT payload FROM {table} WHERE {id_column} = ?", (identifier,)
        )
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            raise KeyError(identifier)
        data = self._decode(row[0])
        data.update(fields)
        _, event_identity, active, payload = self._payload(data, "level_id" if table == "levels" else "raid_id")
        self._connection.execute(
            f"UPDATE {table} SET active = ?, event_identity = ?, payload = ? "
            f"WHERE {id_column} = ?",
            (active, event_identity, payload, identifier),
        )
        self._commit_if_standalone()

    def close(self) -> None:
        if not self._closed:
            self._connection.close()
            self._closed = True

    def __enter__(self) -> "Exp100StateStore":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()
