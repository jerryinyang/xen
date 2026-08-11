"""Bounded I/O and memory safety primitives for Nautilus emissions."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import pyarrow as pa
import pytest

from xen.nautilus.emission import (
    StreamingEmissionSource,
    load_emission_v1,
    write_emission_v1_from_paths,
)
from xen.nautilus.streaming import (
    BoundedJsonlWriter,
    BoundedParquetWriter,
    MemoryBudgetExceeded,
    MemoryGuard,
    OversizedRowError,
)


def test_parquet_writer_flushes_and_releases_completed_batch(tmp_path: Path) -> None:
    writer = BoundedParquetWriter(
        tmp_path / "rows.parquet",
        pa.schema([("i", pa.int64())]),
        max_rows=2,
        max_bytes=1024,
    )
    writer.append({"i": 1})
    assert writer.pending_rows == 1
    writer.append({"i": 2})
    assert writer.pending_rows == 0
    assert writer.rows_written == 2
    writer.close()
    assert pl.read_parquet(tmp_path / "rows.parquet")["i"].to_list() == [1, 2]


def test_memory_guard_raises_before_partial_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("xen.nautilus.streaming.rss_bytes", lambda: 101)
    guard = MemoryGuard(
        limit_bytes=100,
        sample_every=1,
        incomplete_path=tmp_path / "cell.parquet",
        cell_identity={"cell": "synthetic"},
    )
    with pytest.raises(MemoryBudgetExceeded, match="RSS limit"):
        guard.observe(
            10,
            pending_rows=0,
            open_levels=1,
            open_raids=0,
            state_bytes=20,
            last_timestamp="2024-01-01T00:00:00Z",
        )


def test_configured_memory_guard_requires_abort_context() -> None:
    with pytest.raises(ValueError, match="incomplete_path"):
        MemoryGuard(limit_bytes=100)


def test_parquet_writer_rejects_oversized_row_before_retaining_it(tmp_path: Path) -> None:
    writer = BoundedParquetWriter(
        tmp_path / "rows.parquet", pa.schema([("value", pa.string())]), max_bytes=32
    )
    with pytest.raises(OversizedRowError):
        writer.append({"value": "x" * 1_000})
    assert writer.pending_rows == 0
    assert writer.rows_written == 0
    writer.close()
    assert (tmp_path / "rows.parquet").exists()


def test_pending_encoded_staging_bytes_never_exceed_limit(tmp_path: Path) -> None:
    writer = BoundedParquetWriter(
        tmp_path / "rows.parquet", pa.schema([("i", pa.int64())]), max_bytes=10
    )
    writer.append({"i": 1})
    writer.append({"i": 2})
    assert writer.pending_staging_bytes <= 10
    assert writer.rows_written == 1
    writer.close()


def test_parquet_write_error_keeps_only_temp_and_incomplete_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    writer = BoundedParquetWriter(
        tmp_path / "rows.parquet", pa.schema([("i", pa.int64())]), max_rows=1
    )
    writer.append({"i": 1})
    writer.flush()
    assert writer._writer is not None
    monkeypatch.setattr(writer._writer, "close", lambda: (_ for _ in ()).throw(OSError("close boom")))
    with pytest.raises(OSError, match="close boom"):
        writer.close()
    assert not (tmp_path / "rows.parquet").exists()
    assert writer.temp_path.exists()
    marker = tmp_path / "rows.parquet.incomplete.json"
    assert marker.exists()
    assert json.loads(marker.read_text())["error"]


def test_memory_guard_writes_required_abort_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("xen.nautilus.streaming.rss_bytes", lambda: 101)
    marker_base = tmp_path / "cell-output.parquet"
    guard = MemoryGuard(
        limit_bytes=100,
        sample_every=1,
        incomplete_path=marker_base,
        cell_identity={"cell": "synthetic"},
    )
    with pytest.raises(MemoryBudgetExceeded):
        guard.observe(
            10,
            pending_rows=0,
            open_levels=1,
            open_raids=0,
            state_bytes=20,
            last_timestamp="2024-01-01T00:00:00Z",
        )
    marker = json.loads((tmp_path / "cell-output.parquet.incomplete.json").read_text())
    assert marker["cell_identity"] == {"cell": "synthetic"}
    assert marker["last_timestamp"] == "2024-01-01T00:00:00Z"
    assert marker["limit_bytes"] == 100
    assert marker["peak_rss_bytes"] == 101


def test_jsonl_writer_is_compact_and_sorted(tmp_path: Path) -> None:
    writer = BoundedJsonlWriter(tmp_path / "events.jsonl")
    writer.append({"z": 1, "a": "two"})
    writer.close()
    assert (tmp_path / "events.jsonl").read_text() == '{"a":"two","z":1}\n'
    assert writer.rows_written == 1


def test_path_finalizer_copies_tables_and_uses_supplied_counts(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    empty_schema = pa.schema([("value", pa.int64())])
    BoundedParquetWriter(source_dir / "fills.parquet", empty_schema).close()
    BoundedParquetWriter(source_dir / "orders.parquet", empty_schema).close()
    BoundedParquetWriter(source_dir / "positions.parquet", empty_schema).close()
    bars = BoundedParquetWriter(
        source_dir / "bars.parquet", pa.schema([("value", pa.int64())]), max_rows=1
    )
    bars.append({"value": 7})
    bars.append({"value": 8})
    bars.close()
    events = BoundedJsonlWriter(source_dir / "events.jsonl")
    events.append({"kind": "bar", "n": 1})
    events.close()

    source = StreamingEmissionSource(
        fills=source_dir / "fills.parquet",
        orders=source_dir / "orders.parquet",
        positions_ledger=source_dir / "positions.parquet",
        bar_marks=source_dir / "bars.parquet",
        event_log=source_dir / "events.jsonl",
        row_counts={"fills": 0, "orders": 0, "positions": 3, "bar_marks": 2},
    )
    paths = write_emission_v1_from_paths(
        tmp_path / "run",
        source=source,
        instrument_id_map={"TEST": "TEST.SYNTH"},
        run_config={"cell": "synthetic"},
        catalog_version=None,
        catalog_path=None,
        fence={"status": "TEST"},
        nautilus_version="1.230.0",
        platform="test",
    )
    assert pl.read_parquet(paths.bar_marks)["value"].to_list() == [7, 8]
    metadata = json.loads(paths.run_metadata.read_text())
    assert metadata["n_bar_marks"] == 2
    assert metadata["n_positions"] == 3
    assert load_emission_v1(paths.root).event_log_text == '{"kind":"bar","n":1}\n'
