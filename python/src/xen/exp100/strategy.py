"""Nautilus adapter for one streaming EXP-100 cell."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pyarrow as pa
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.trading.config import StrategyConfig
from nautilus_trader.trading.strategy import Strategy

from xen.nautilus.streaming import (
    BoundedJsonlWriter,
    BoundedParquetWriter,
    MemoryBudgetExceeded,
    MemoryGuard,
)

from .config import Exp100CellConfig
from .processor import Exp100Processor, Exp100Sinks
from .state_store import Exp100StateStore
from .types import BarRecord

DEFAULT_WRITER_MAX_ROWS = 8192
DEFAULT_WRITER_MAX_BYTES = 8_000_000
DEFAULT_MEMORY_SAMPLE_EVERY = 10_000


class Exp100StrategyConfig(StrategyConfig, frozen=True):
    """Serialized configuration for one memory-bounded EXP-100 strategy."""

    instrument_id: InstrumentId
    bar_type: BarType
    cell_config_json: str
    state_path: str
    output_staging_path: str
    writer_max_rows: int = DEFAULT_WRITER_MAX_ROWS
    writer_max_bytes: int = DEFAULT_WRITER_MAX_BYTES
    rss_limit_bytes: int | None = None
    memory_sample_every: int = DEFAULT_MEMORY_SAMPLE_EVERY


class _TypedWriter:
    """Normalize processor dictionaries before passing them to a bounded writer."""

    def __init__(self, writer: BoundedParquetWriter) -> None:
        self._writer = writer

    @property
    def pending_rows(self) -> int:
        return self._writer.pending_rows

    @property
    def rows_written(self) -> int:
        return self._writer.rows_written

    def append(self, row: dict[str, Any]) -> None:
        normalized = {
            field.name: _coerce_value(row.get(field.name), field.type)
            for field in self._writer.schema
        }
        self._writer.append(normalized)

    def close(self) -> None:
        self._writer.close()

    def discard(self) -> None:
        """Close only the temporary Parquet handle, never promote its partial file."""
        try:
            parquet_writer = self._writer._writer
            if parquet_writer is not None:
                parquet_writer.close()
        finally:
            self._writer._writer = None
            self._writer._rows.clear()


class _BarMarkWriter:
    """Map processor bar marks to the canonical emission column names."""

    def __init__(self, writer: _TypedWriter) -> None:
        self._writer = writer

    @property
    def pending_rows(self) -> int:
        return self._writer.pending_rows

    @property
    def rows_written(self) -> int:
        return self._writer.rows_written

    def append(self, row: dict[str, Any]) -> None:
        self._writer.append(
            {
                "SourceCloseTime": row["source_ts_event_ns"],
                "RealOpen": row["real_open"],
                "RealHigh": row["real_high"],
                "RealLow": row["real_low"],
                "RealClose": row["real_close"],
                "Volume": row["real_volume"],
                "ts_event_ns": row["ts_event_ns"],
                "source_bars": row["source_bars"],
                "atr": row["atr"],
                "regime": row["regime"],
                "processed_source_bars": row["processed_source_bars"],
                "completed_observations": row["completed_observations"],
                "open_levels": row["open_levels"],
                "open_raids": row["open_raids"],
                "state_bytes": row["state_bytes"],
            }
        )

    def close(self) -> None:
        self._writer.close()

    def discard(self) -> None:
        self._writer.discard()


def _coerce_value(value: Any, data_type: pa.DataType) -> Any:
    if value is None:
        return None
    if pa.types.is_string(data_type):
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
        return str(value)
    if pa.types.is_boolean(data_type):
        return bool(value)
    if pa.types.is_integer(data_type):
        return int(value)
    if pa.types.is_floating(data_type):
        return float(value)
    raise TypeError(f"unsupported EXP-100 output type: {data_type}")


def _schema(fields: list[tuple[str, pa.DataType]]) -> pa.Schema:
    return pa.schema([pa.field(name, data_type, nullable=True) for name, data_type in fields])


def _level_schema() -> pa.Schema:
    return _schema(
        [
            ("level_id", pa.string()),
            ("event_identity", pa.string()),
            ("source_configuration", pa.string()),
            ("side", pa.string()),
            ("price", pa.float64()),
            ("creation_ts_ns", pa.int64()),
            ("anchor_key", pa.string()),
            ("beyond", pa.bool_()),
            ("active", pa.bool_()),
            ("last_observation_ts_ns", pa.int64()),
            ("status", pa.string()),
            ("endpoint_ts_ns", pa.int64()),
            ("censor_ts_ns", pa.int64()),
        ]
    )


def _raid_schema() -> pa.Schema:
    return _schema(
        [
            ("raid_id", pa.string()),
            ("level_id", pa.string()),
            ("event_identity", pa.string()),
            ("source_configuration", pa.string()),
            ("archive_symbol", pa.string()),
            ("timeframe", pa.string()),
            ("config", pa.string()),
            ("side", pa.string()),
            ("level_price", pa.float64()),
            ("level_creation_ts_ns", pa.int64()),
            ("sweep_ts_ns", pa.int64()),
            ("first_excursion_ts_ns", pa.int64()),
            ("return_ts_ns", pa.int64()),
            ("confirmation_ts_ns", pa.int64()),
            ("endpoint_ts_ns", pa.int64()),
            ("censor_ts_ns", pa.int64()),
            ("max_price", pa.float64()),
            ("max_excursion", pa.float64()),
            ("max_excursion_bps", pa.float64()),
            ("max_excursion_atr", pa.float64()),
            ("prior_raid_count", pa.int64()),
            ("raid_atr", pa.float64()),
            ("raid_regime", pa.string()),
            ("excursion_ts_ns", pa.int64()),
            ("excursion_atr", pa.float64()),
            ("excursion_regime", pa.string()),
            ("confirmation_atr", pa.float64()),
            ("confirmation_regime", pa.string()),
            ("endpoint_atr", pa.float64()),
            ("endpoint_regime", pa.string()),
            ("profile_generation", pa.int64()),
            ("profile_finalized", pa.bool_()),
            ("profile_undefined_reason", pa.string()),
            ("confirmation_method", pa.string()),
            ("confirmation_reference", pa.string()),
            ("primary_attribution", pa.bool_()),
            ("active", pa.bool_()),
            ("status", pa.string()),
            ("primary_completed", pa.bool_()),
            ("confirmation_level_high", pa.float64()),
            ("confirmation_level_low", pa.float64()),
            ("confirmation_price", pa.float64()),
            ("swing_extreme", pa.float64()),
            ("swing_price", pa.float64()),
            ("swing_bps", pa.float64()),
            ("swing_atr", pa.float64()),
            ("strong_move", pa.bool_()),
            ("duration_ns", pa.int64()),
        ]
    )


def _profile_schema() -> pa.Schema:
    return _schema(
        [
            ("raid_id", pa.string()),
            ("profile_generation", pa.int64()),
            ("profile_start_ts_ns", pa.int64()),
            ("profile_end_ts_ns", pa.int64()),
            ("bin_width", pa.float64()),
            ("atr_unit", pa.float64()),
            ("bracket_count", pa.int64()),
            ("poc", pa.float64()),
            ("val", pa.float64()),
            ("vah", pa.float64()),
            ("va_count", pa.int64()),
            ("va_mass", pa.float64()),
            ("va_mask", pa.string()),
            ("gap_mask", pa.string()),
            ("gap_span", pa.float64()),
            ("gap_span_atr", pa.float64()),
            ("gap_span_va", pa.float64()),
            ("va_width", pa.float64()),
            ("tight_gap", pa.bool_()),
            ("tpo_total", pa.int64()),
            ("tpo_conservation_ok", pa.bool_()),
            ("profile_status", pa.string()),
            ("undefined_reason", pa.string()),
            ("raid_status", pa.string()),
            ("endpoint_ts_ns", pa.int64()),
        ]
    )


def _bar_mark_schema() -> pa.Schema:
    return _schema(
        [
            ("SourceCloseTime", pa.int64()),
            ("RealOpen", pa.float64()),
            ("RealHigh", pa.float64()),
            ("RealLow", pa.float64()),
            ("RealClose", pa.float64()),
            ("Volume", pa.float64()),
            ("ts_event_ns", pa.int64()),
            ("source_bars", pa.int64()),
            ("atr", pa.float64()),
            ("regime", pa.string()),
            ("processed_source_bars", pa.int64()),
            ("completed_observations", pa.int64()),
            ("open_levels", pa.int64()),
            ("open_raids", pa.int64()),
            ("state_bytes", pa.int64()),
        ]
    )


def _build_sinks(config: Exp100StrategyConfig) -> tuple[Exp100Sinks, dict[str, Any]]:
    staging = Path(config.output_staging_path)
    staging.mkdir(parents=True, exist_ok=True)

    def parquet(name: str, schema: pa.Schema) -> _TypedWriter:
        return _TypedWriter(
            BoundedParquetWriter(
                staging / f"{name}.parquet",
                schema,
                max_rows=config.writer_max_rows,
                max_bytes=config.writer_max_bytes,
            )
        )

    bar_marks = _BarMarkWriter(parquet("bar_marks", _bar_mark_schema()))
    levels = parquet("levels", _level_schema())
    raids = parquet("raids", _raid_schema())
    tpo_profiles = parquet("tpo_profiles", _profile_schema())
    event_log = BoundedJsonlWriter(staging / "event_log.jsonl")
    sinks = Exp100Sinks(
        bar_marks=bar_marks,
        levels=levels,
        raids=raids,
        tpo_profiles=tpo_profiles,
        event_log=event_log,
    )
    writers = {
        "bar_marks": bar_marks,
        "levels": levels,
        "raids": raids,
        "tpo_profiles": tpo_profiles,
        "event_log": event_log,
    }
    return sinks, writers


class Exp100Strategy(Strategy):
    """Feed one external one-minute bar stream into the causal processor."""

    def __init__(self, config: Exp100StrategyConfig) -> None:
        super().__init__(config)
        self._state: Exp100StateStore | None = None
        self._processor: Exp100Processor | None = None
        self._guard: MemoryGuard | None = None
        self._writers: dict[str, Any] = {}
        self._last_ts_ns: int | None = None
        self._aborted = False
        self._closed = False

    def on_start(self) -> None:
        """Open cell-local state and subscribe to exactly the configured bar type."""
        config = self.config
        cell = Exp100CellConfig(**json.loads(config.cell_config_json))
        cell.validate()
        state = Exp100StateStore(Path(config.state_path))
        staging = Path(config.output_staging_path)
        guard = MemoryGuard(
            config.rss_limit_bytes,
            sample_every=config.memory_sample_every,
            incomplete_path=staging / "cell",
            cell_identity=cell.to_dict(),
        )
        sinks, writers = _build_sinks(config)
        self._state = state
        self._guard = guard
        self._writers = writers
        self._processor = Exp100Processor(cell, state, sinks, guard)
        self.subscribe_bars(config.bar_type)

    def on_bar(self, bar: Bar) -> None:
        """Convert one confirmed Nautilus bar and pass it to the processor."""
        if self._processor is None:
            raise RuntimeError("EXP-100 strategy has not started")
        if bar.bar_type != self.config.bar_type:
            raise ValueError(f"unexpected bar type {bar.bar_type}; expected {self.config.bar_type}")
        record = BarRecord(
            ts_event_ns=int(bar.ts_event),
            open=float(bar.open),
            high=float(bar.high),
            low=float(bar.low),
            close=float(bar.close),
            volume=float(bar.volume),
            source_bars=1,
        )
        self._last_ts_ns = record.ts_event_ns
        try:
            self._processor.on_one_minute_bar(record)
        except MemoryBudgetExceeded:
            self._aborted = True
            self._discard_outputs()
            raise
        except Exception:
            self._aborted = True
            self._discard_outputs()
            raise

    def on_stop(self) -> None:
        """Finish causal state and atomically finalize the cell-local streams."""
        if self._closed or self._aborted:
            return
        if self._processor is None or self._state is None:
            return
        self._processor.finish(self._last_ts_ns)
        snapshot = self._processor.snapshot()
        for writer in self._writers.values():
            writer.close()
        self._state.close()
        self._closed = True
        self._write_stream_manifest(snapshot)

    def dispose(self) -> None:
        """Release resources without promoting partial output on failure."""
        if not self._closed:
            self._discard_outputs()
        super().dispose()

    def _discard_outputs(self) -> None:
        if self._closed:
            return
        for name, writer in self._writers.items():
            try:
                if name == "event_log":
                    writer.flush()
                    writer.close()
                else:
                    writer.discard()
            except Exception:
                pass
        if self._state is not None:
            try:
                self._state.close()
            except Exception:
                pass
        self._closed = True

    def _write_stream_manifest(self, snapshot: dict[str, int]) -> None:
        guard = self._guard
        manifest = {
            "row_counts": {
                name: int(writer.rows_written) for name, writer in self._writers.items()
            },
            "snapshot": snapshot,
            "peak_rss_bytes": guard.peak_rss_bytes if guard is not None else 0,
        }
        path = Path(self.config.output_staging_path) / "stream_manifest.json"
        path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
