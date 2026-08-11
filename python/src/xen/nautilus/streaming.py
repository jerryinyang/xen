"""Bounded-memory output and resource guards for Nautilus cells."""

from __future__ import annotations

import json
import os
import resource
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import pyarrow as pa
import pyarrow.parquet as pq


def rss_bytes() -> int:
    """Return the process high-water RSS in bytes on macOS and Linux."""
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


class MemoryBudgetExceeded(RuntimeError):
    def __init__(self, processed_bars: int, peak_rss_bytes: int, limit_bytes: int) -> None:
        self.processed_bars = processed_bars
        self.peak_rss_bytes = peak_rss_bytes
        self.limit_bytes = limit_bytes
        super().__init__(
            f"RSS limit exceeded: {peak_rss_bytes} > {limit_bytes} bytes "
            f"after {processed_bars} bars"
        )


class OversizedRowError(ValueError):
    """Raised when one row cannot fit within a writer's working-byte budget."""

    def __init__(self, estimated_bytes: int, limit_bytes: int) -> None:
        self.estimated_bytes = estimated_bytes
        self.limit_bytes = limit_bytes
        super().__init__(f"row requires {estimated_bytes} bytes; limit is {limit_bytes} bytes")


@dataclass(frozen=True)
class MemorySample:
    processed_bars: int
    rss_bytes: int
    peak_rss_bytes: int
    pending_rows: int
    open_levels: int
    open_raids: int
    state_bytes: int


class MemoryGuard:
    def __init__(
        self,
        limit_bytes: int | None,
        sample_every: int = 10_000,
        *,
        incomplete_path: Path | None = None,
        cell_identity: Mapping[str, Any] | str | None = None,
        last_timestamp: Any = None,
    ) -> None:
        if sample_every <= 0:
            raise ValueError("sample_every must be positive")
        if limit_bytes is not None and limit_bytes <= 0:
            raise ValueError("limit_bytes must be positive or None")
        self.limit_bytes = limit_bytes
        self.sample_every = sample_every
        self._peak_rss_bytes = 0
        self._next_sample = 0
        self._has_sample = False
        self._last_sample = MemorySample(0, 0, 0, 0, 0, 0, 0)
        self.incomplete_path = Path(incomplete_path) if incomplete_path is not None else None
        self.cell_identity = cell_identity
        self.last_timestamp = last_timestamp

    @property
    def peak_rss_bytes(self) -> int:
        return self._peak_rss_bytes

    def observe(
        self,
        processed_bars: int,
        *,
        pending_rows: int,
        open_levels: int,
        open_raids: int,
        state_bytes: int,
        force: bool = False,
    ) -> MemorySample:
        if processed_bars < 0:
            raise ValueError("processed_bars must be non-negative")
        if not force and processed_bars < self._next_sample and self._has_sample:
            return self._last_sample
        current = rss_bytes()
        self._peak_rss_bytes = max(self._peak_rss_bytes, current)
        sample = MemorySample(
            processed_bars,
            current,
            self._peak_rss_bytes,
            pending_rows,
            open_levels,
            open_raids,
            state_bytes,
        )
        self._last_sample = sample
        self._has_sample = True
        self._next_sample = processed_bars + self.sample_every
        if self.limit_bytes is not None and self._peak_rss_bytes > self.limit_bytes:
            if self.incomplete_path is not None:
                write_incomplete_marker(
                    self.incomplete_path,
                    cell_identity=self.cell_identity,
                    last_timestamp=self.last_timestamp,
                    limit_bytes=self.limit_bytes,
                    peak_rss_bytes=self._peak_rss_bytes,
                    processed_bars=processed_bars,
                )
            raise MemoryBudgetExceeded(processed_bars, self._peak_rss_bytes, self.limit_bytes)
        return sample


def write_incomplete_marker(
    path: str | Path,
    *,
    cell_identity: Mapping[str, Any] | str | None = None,
    last_timestamp: Any = None,
    limit_bytes: int | None = None,
    peak_rss_bytes: int | None = None,
    **payload: Any,
) -> Path:
    """Write an invalid-cell marker beside a temporary output path."""
    marker = Path(path).with_suffix(Path(path).suffix + ".incomplete.json")
    body = {
        "cell_identity": cell_identity,
        "last_timestamp": last_timestamp,
        "limit_bytes": limit_bytes,
        "peak_rss_bytes": peak_rss_bytes,
        **payload,
    }
    marker.write_text(
        json.dumps(body, sort_keys=True, separators=(",", ":"), default=str) + "\n",
        encoding="utf-8",
    )
    return marker


class BoundedParquetWriter:
    def __init__(
        self,
        path: Path,
        schema: pa.Schema,
        *,
        max_rows: int = 8192,
        max_bytes: int = 8_000_000,
    ) -> None:
        if max_rows <= 0 or max_bytes <= 0:
            raise ValueError("writer limits must be positive")
        self.path = Path(path)
        self.schema = schema
        self.max_rows = max_rows
        self.max_bytes = max_bytes
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._rows: list[Mapping[str, Any]] = []
        self._working_bytes = 0
        self._rows_written = 0
        self._writer: pq.ParquetWriter | None = None
        self._closed = False
        self._temp_path = self.path.with_name(f".{self.path.name}.tmp")

    @property
    def temp_path(self) -> Path:
        return self._temp_path

    @property
    def rows_written(self) -> int:
        return self._rows_written

    @property
    def pending_rows(self) -> int:
        return len(self._rows)

    def append(self, row: Mapping[str, Any]) -> None:
        if self._closed:
            raise RuntimeError("writer is closed")
        if set(row) - set(self.schema.names):
            raise ValueError(f"row contains columns outside schema: {sorted(set(row) - set(self.schema.names))}")
        encoded = json.dumps(dict(row), sort_keys=True, default=str, separators=(",", ":")).encode()
        # The budget includes the encoded mapping, Python container allowance,
        # and a conservative Arrow conversion allowance for the pending batch.
        estimated = len(encoded) * 2 + 64
        if estimated > self.max_bytes:
            raise OversizedRowError(estimated, self.max_bytes)
        if self._working_bytes + estimated > self.max_bytes:
            self.flush()
        self._rows.append(row)
        self._working_bytes += estimated
        if len(self._rows) >= self.max_rows or self._working_bytes >= self.max_bytes:
            self.flush()

    def flush(self) -> None:
        if not self._rows:
            return
        table = pa.Table.from_pylist([dict(row) for row in self._rows], schema=self.schema)
        if self._writer is None:
            self._writer = pq.ParquetWriter(self._temp_path, self.schema)
        try:
            self._writer.write_table(table, row_group_size=table.num_rows)
        except Exception as exc:
            write_incomplete_marker(self.path, error=repr(exc), rows_written=self._rows_written)
            raise
        self._rows_written += table.num_rows
        self._rows.clear()
        self._working_bytes = 0

    def close(self) -> None:
        if self._closed:
            return
        try:
            self.flush()
            if self._writer is None:
                pq.write_table(pa.Table.from_pylist([], schema=self.schema), self._temp_path)
            else:
                self._writer.close()
            os.replace(self._temp_path, self.path)
        except Exception as exc:
            write_incomplete_marker(
                self.path,
                error=repr(exc),
                rows_written=self._rows_written,
                temp_path=str(self._temp_path),
            )
            raise
        finally:
            self._closed = True


class BoundedJsonlWriter:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("w", encoding="utf-8")
        self._rows_written = 0
        self._closed = False

    @property
    def rows_written(self) -> int:
        return self._rows_written

    def append(self, payload: Mapping[str, Any]) -> None:
        if self._closed:
            raise RuntimeError("writer is closed")
        self._file.write(json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), default=str))
        self._file.write("\n")
        self._rows_written += 1

    def flush(self) -> None:
        if not self._closed:
            self._file.flush()

    def close(self) -> None:
        if not self._closed:
            self._file.close()
            self._closed = True
