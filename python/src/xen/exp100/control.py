"""Disk-backed future-destroy control for EXP-100."""

from __future__ import annotations

import hashlib
import json
import pickle
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from xen.nautilus.streaming import BoundedParquetWriter


_BATCH_SIZE = 4_096
_WRITER_MAX_BYTES = 8_000_000


def _group_key(row: dict[str, Any], columns: tuple[str, ...]) -> str:
    return json.dumps(
        [row[column] for column in columns],
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _direction(seed: int, group_key: str) -> str:
    """Choose a deterministic cycle direction without holding a group in RAM."""
    digest = hashlib.sha256(f"{int(seed)}:{group_key}".encode("utf-8")).digest()
    return "ASC" if digest[0] % 2 == 0 else "DESC"


def _validate_columns(
    schema_names: set[str],
    *,
    group_columns: tuple[str, ...],
    value_columns: tuple[str, ...],
) -> None:
    if not group_columns:
        raise ValueError("group_columns must not be empty")
    if not value_columns:
        raise ValueError("value_columns must not be empty")
    required = set(group_columns) | set(value_columns) | {"raid_id"}
    missing = sorted(required - schema_names)
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    if len(set(group_columns)) != len(group_columns):
        raise ValueError("group_columns must not contain duplicates")
    if len(set(value_columns)) != len(value_columns):
        raise ValueError("value_columns must not contain duplicates")


def _eligible(row: dict[str, Any], has_confirmation: bool) -> bool:
    return not has_confirmation or row["confirmation_ts_ns"] is not None


def _stage_rows(
    source: pq.ParquetFile,
    connection: sqlite3.Connection,
    *,
    group_columns: tuple[str, ...],
    value_columns: tuple[str, ...],
    has_confirmation: bool,
) -> int:
    """Stage row identity, grouping, and values using bounded Arrow batches."""
    insert_sql = (
        "INSERT INTO source_rows(row_id, group_key, raid_id, values_blob) "
        "VALUES (?, ?, ?, ?)"
    )
    next_row_id = 0
    for batch in source.iter_batches(batch_size=_BATCH_SIZE):
        staged: list[tuple[int, str, str, bytes]] = []
        for row in batch.to_pylist():
            if _eligible(row, has_confirmation):
                raid_id = row.get("raid_id")
                if raid_id is None:
                    raise ValueError("raid_id must be non-null")
                staged.append(
                    (
                        next_row_id,
                        _group_key(row, group_columns),
                        str(raid_id),
                        pickle.dumps(
                            tuple(row[column] for column in value_columns),
                            protocol=pickle.HIGHEST_PROTOCOL,
                        ),
                    )
                )
            next_row_id += 1
        if staged:
            connection.executemany(insert_sql, staged)
            connection.commit()
    return next_row_id


def _build_mapping(connection: sqlite3.Connection, *, seed: int) -> dict[str, int]:
    """Create a one-step cyclic mapping per group with cursor-only traversal."""
    connection.execute("DELETE FROM mapping")
    groups = 0
    rows = 0
    fixed_points = 0
    for group_key, group_size in connection.execute(
        "SELECT group_key, COUNT(*) FROM source_rows GROUP BY group_key ORDER BY group_key"
    ):
        group_size = int(group_size)
        if group_size == 1:
            raise ValueError(f"singleton group cannot be deranged: {group_key}")
        groups += 1
        rows += group_size
        direction = _direction(seed, str(group_key))
        cursor = connection.execute(
            "SELECT row_id FROM source_rows WHERE group_key=? "
            f"ORDER BY raid_id {direction}, row_id {direction}",
            (group_key,),
        )
        first = cursor.fetchone()
        if first is None:
            raise RuntimeError("group disappeared while building destroy mapping")
        first_id = int(first[0])
        previous_id = first_id
        for (current_id,) in cursor:
            current_id = int(current_id)
            connection.execute(
                "INSERT INTO mapping(row_id, source_row_id) VALUES (?, ?)",
                (previous_id, current_id),
            )
            if previous_id == current_id:
                fixed_points += 1
            previous_id = current_id
        connection.execute(
            "INSERT INTO mapping(row_id, source_row_id) VALUES (?, ?)",
            (previous_id, first_id),
        )
        if previous_id == first_id:
            fixed_points += 1
    connection.commit()
    return {"groups": groups, "rows": rows, "fixed_points": fixed_points}


def _mapped_values(
    connection: sqlite3.Connection,
    start_row_id: int,
    end_row_id: int,
) -> dict[int, tuple[Any, ...]]:
    values: dict[int, tuple[Any, ...]] = {}
    cursor = connection.execute(
        "SELECT mapping.row_id, source_rows.values_blob "
        "FROM mapping JOIN source_rows "
        "ON source_rows.row_id = mapping.source_row_id "
        "WHERE mapping.row_id >= ? AND mapping.row_id < ? "
        "ORDER BY mapping.row_id",
        (start_row_id, end_row_id),
    )
    for row_id, values_blob in cursor:
        values[int(row_id)] = tuple(pickle.loads(values_blob))
    return values


def destroy_post_confirmation(
    source: Path,
    destination: Path,
    *,
    group_columns: tuple[str, ...],
    value_columns: tuple[str, ...],
    seed: int,
) -> dict[str, int | float]:
    """Derange post-confirmation values within each declared group.

    The source is read twice in bounded Arrow batches. SQLite stores only the
    eligible row identity, grouping key, and serialized outcome tuple; the
    mapping itself is built with ordered cursors. Each group is mapped to the
    next row in a deterministic cycle, with the direction derived from the
    supplied seed and group key. Consequently no row maps to itself, while
    group membership and the multiset of outcome values are preserved.
    """
    source = Path(source)
    destination = Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError("destroy destination must not overwrite source")
    if not source.exists():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)

    parquet = pq.ParquetFile(source)
    schema_names = set(parquet.schema_arrow.names)
    _validate_columns(
        schema_names,
        group_columns=group_columns,
        value_columns=value_columns,
    )
    has_confirmation = "confirmation_ts_ns" in schema_names

    with tempfile.TemporaryDirectory(
        prefix=f".{destination.name}.", dir=str(destination.parent)
    ) as temporary:
        database_path = Path(temporary) / "control.sqlite"
        connection = sqlite3.connect(database_path)
        try:
            connection.execute("PRAGMA journal_mode=DELETE")
            connection.execute("PRAGMA synchronous=NORMAL")
            connection.executescript(
                """
                CREATE TABLE source_rows(
                    row_id INTEGER PRIMARY KEY,
                    group_key TEXT NOT NULL,
                    raid_id TEXT NOT NULL,
                    values_blob BLOB NOT NULL
                );
                CREATE INDEX source_rows_group_order
                    ON source_rows(group_key, raid_id, row_id);
                CREATE TABLE mapping(
                    row_id INTEGER PRIMARY KEY,
                    source_row_id INTEGER NOT NULL
                );
                """
            )
            _stage_rows(
                parquet,
                connection,
                group_columns=group_columns,
                value_columns=value_columns,
                has_confirmation=has_confirmation,
            )
            report = _build_mapping(connection, seed=int(seed))
            if report["fixed_points"] != 0:
                raise RuntimeError("destroy mapping contains fixed points")

            writer = BoundedParquetWriter(
                destination,
                parquet.schema_arrow,
                max_rows=_BATCH_SIZE,
                max_bytes=_WRITER_MAX_BYTES,
            )
            changed_rows = 0
            source_row_id = 0
            try:
                for batch in parquet.iter_batches(batch_size=_BATCH_SIZE):
                    rows = batch.to_pylist()
                    mapped = _mapped_values(
                        connection,
                        source_row_id,
                        source_row_id + len(rows),
                    )
                    for offset, row in enumerate(rows):
                        current_id = source_row_id + offset
                        replacement = mapped.get(current_id)
                        if replacement is not None:
                            original = tuple(row[column] for column in value_columns)
                            if replacement != original:
                                changed_rows += 1
                            row = dict(row)
                            row.update(dict(zip(value_columns, replacement, strict=True)))
                        writer.append(row)
                    source_row_id += len(rows)
                writer.close()
            except Exception:
                if not writer._closed:
                    writer._closed = True
                raise
            report["changed_rows"] = changed_rows
            eligible_rows = int(report["rows"])
            report["contrast_ratio"] = (
                float(changed_rows) / float(eligible_rows) if eligible_rows else 0.0
            )
            return report
        finally:
            connection.close()
