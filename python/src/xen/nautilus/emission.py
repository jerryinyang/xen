"""Nautilus emission contract v1 (INFR-010 Phase B).

Nautilus equivalent of ``data/strategy_runs/<ID>/``. This is the artifact set that
``xen.estimand_validation`` v2 (Phase C) will gate and that
:mod:`xen.nautilus.adjudication_shim` maps into :mod:`xen.adjudication`.

Layout under ``data/nautilus_runs/<run_id>/``::

    run_metadata.json       # config hash, catalog version, fence, instrument map, pin
    fills.parquet           # order fills (economic + timestamps)
    orders.parquet          # order lifecycle rows
    positions_ledger.parquet  # closed/open position legs (→ cis_trades)
    bar_marks.parquet       # bar marks + optional net position (→ positions)
    event_log.jsonl         # UUID-stripped deterministic event log (one JSON object/line)
    instrument_id_map.json  # archive_symbol ↔ InstrumentId
    fence_attestation.json  # analysis_end_utc + catalog fence hash (may be stub pre-INFR-011)

``init_id`` / process-ephemeral UUIDs are stripped from ``event_log.jsonl`` so that
identical config + data yields byte-identical logs across process restarts (INFR-007
one-platform rule still applies for floating-point).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl

EMISSION_CONTRACT_VERSION = "nautilus-emission-v1"

# Columns kept in the deterministic event log (no process-ephemeral UUIDs).
_FILL_LOG_COLS = (
    "client_order_id",
    "instrument_id",
    "side",
    "quantity",
    "filled_qty",
    "avg_px",
    "status",
    "liquidity_side",
    "ts_init",
    "ts_last",
    "commissions",
)
_ORDER_LOG_COLS = _FILL_LOG_COLS
_POS_LOG_COLS = (
    "instrument_id",
    "entry",
    "side",
    "quantity",
    "peak_qty",
    "avg_px_open",
    "avg_px_close",
    "realized_return",
    "realized_pnl",
    "ts_opened",
    "ts_closed",
    "duration_ns",
    "commissions",
)


@dataclass(frozen=True)
class EmissionPaths:
    """Resolved paths for one emission directory."""

    root: Path

    @property
    def run_metadata(self) -> Path:
        return self.root / "run_metadata.json"

    @property
    def fills(self) -> Path:
        return self.root / "fills.parquet"

    @property
    def orders(self) -> Path:
        return self.root / "orders.parquet"

    @property
    def positions_ledger(self) -> Path:
        return self.root / "positions_ledger.parquet"

    @property
    def bar_marks(self) -> Path:
        return self.root / "bar_marks.parquet"

    @property
    def event_log(self) -> Path:
        return self.root / "event_log.jsonl"

    @property
    def instrument_id_map(self) -> Path:
        return self.root / "instrument_id_map.json"

    @property
    def fence_attestation(self) -> Path:
        return self.root / "fence_attestation.json"


@dataclass(frozen=True)
class StreamingEmissionSource:
    """Finalized source files produced by bounded cell writers."""

    fills: Path | None
    orders: Path | None
    positions_ledger: Path | None
    bar_marks: Path
    event_log: Path
    row_counts: dict[str, int]


_EMPTY_TABLE_SCHEMAS = {
    "fills": {column: pl.Utf8 for column in _FILL_LOG_COLS},
    "orders": {column: pl.Utf8 for column in _ORDER_LOG_COLS},
    "positions_ledger": {column: pl.Utf8 for column in _POS_LOG_COLS},
}


def _copy_file(source: Path, destination: Path) -> str:
    """Copy a finalized file in bounded chunks and return its SHA-256."""
    with source.open("rb") as src, destination.open("wb") as dst:
        import shutil

        shutil.copyfileobj(src, dst, length=1024 * 1024)
    return _sha256_file(destination)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _count(source: StreamingEmissionSource, name: str) -> int:
    if name in source.row_counts:
        return int(source.row_counts[name])
    return int(source.row_counts.get(f"n_{name}", 0))


def write_emission_v1_from_paths(
    run_dir: str | Path,
    *,
    source: StreamingEmissionSource,
    instrument_id_map: dict[str, str],
    run_config: dict[str, Any],
    catalog_version: str | None,
    catalog_path: str | None,
    fence: dict[str, Any],
    nautilus_version: str,
    platform: str,
    extra_metadata: dict[str, Any] | None = None,
) -> EmissionPaths:
    """Finalize bounded writer outputs without loading any table into memory."""
    root = Path(run_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = EmissionPaths(root)
    table_sources: dict[str, Path | None] = {
        "fills": source.fills,
        "orders": source.orders,
        "positions_ledger": source.positions_ledger,
        "bar_marks": source.bar_marks,
    }
    table_destinations = {
        "fills": paths.fills,
        "orders": paths.orders,
        "positions_ledger": paths.positions_ledger,
        "bar_marks": paths.bar_marks,
    }
    for name, destination in table_destinations.items():
        origin = table_sources[name]
        if origin is not None:
            if Path(origin).resolve() != destination.resolve():
                _copy_file(Path(origin), destination)
        else:
            if name == "bar_marks":
                raise FileNotFoundError("bar_marks source is required")
            empty = pl.DataFrame(schema=_EMPTY_TABLE_SCHEMAS[name])
            empty.write_parquet(destination)

    _copy_file(Path(source.event_log), paths.event_log)
    event_log_sha256 = _sha256_file(paths.event_log)
    paths.instrument_id_map.write_text(
        json.dumps(instrument_id_map, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    paths.fence_attestation.write_text(
        json.dumps(fence, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    meta = {
        "emission_contract_version": EMISSION_CONTRACT_VERSION,
        "generated_utc": datetime.now(UTC).isoformat(),
        "config_hash": config_hash(run_config),
        "run_config": run_config,
        "catalog_version": catalog_version,
        "catalog_path": catalog_path,
        "nautilus_version": nautilus_version,
        "platform": platform,
        "instrument_id_map": instrument_id_map,
        "fence_attestation_path": paths.fence_attestation.name,
        "event_log_sha256": event_log_sha256,
        "n_fills": _count(source, "fills"),
        "n_orders": _count(source, "orders"),
        "n_positions": _count(source, "positions_ledger"),
        "n_bar_marks": _count(source, "bar_marks"),
    }
    if extra_metadata:
        meta.update(extra_metadata)
    paths.run_metadata.write_text(
        json.dumps(meta, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    return paths


def _df_or_empty(df: pl.DataFrame | None, columns: list[str] | None = None) -> pl.DataFrame:
    if df is None or df.height == 0:
        return pl.DataFrame(schema={c: pl.Utf8 for c in (columns or [])}) if columns else pl.DataFrame()
    return df


def _records_for_log(df: pl.DataFrame, cols: tuple[str, ...]) -> list[dict[str, Any]]:
    if df.height == 0:
        return []
    present = [c for c in cols if c in df.columns]
    if not present:
        return []
    # Stable string forms for byte-identity (lists → json-ish joined text).
    casts = []
    for c in present:
        dtype = df.schema[c]
        if dtype == pl.List or str(dtype).startswith("List("):
            casts.append(
                pl.col(c)
                .list.eval(pl.element().cast(pl.Utf8))
                .list.join(",")
                .alias(c)
            )
        elif dtype == pl.Utf8:
            casts.append(pl.col(c))
        else:
            casts.append(pl.col(c).cast(pl.Utf8))
    out = df.select(present).with_columns(casts)
    return out.to_dicts()


def config_hash(payload: dict[str, Any]) -> str:
    """Stable sha256 of a JSON-serialisable config payload."""
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def write_emission_v1(
    run_dir: str | Path,
    *,
    fills: pl.DataFrame | None,
    orders: pl.DataFrame | None,
    positions_ledger: pl.DataFrame | None,
    bar_marks: pl.DataFrame | None,
    instrument_id_map: dict[str, str],
    run_config: dict[str, Any],
    catalog_version: str | None = None,
    catalog_path: str | None = None,
    fence: dict[str, Any] | None = None,
    nautilus_version: str,
    platform: str,
    extra_metadata: dict[str, Any] | None = None,
) -> EmissionPaths:
    """Write a complete emission-contract-v1 directory.

    Parameters
    ----------
    run_dir :
        Destination directory (created).
    fills, orders, positions_ledger, bar_marks :
        Tables captured from a Nautilus backtest (already converted to polars).
    instrument_id_map :
        ``{archive_symbol: instrument_id_str}`` for every instrument in the run.
    run_config :
        Strategy/venue/data config used for the run (hashed into metadata).
    catalog_version, catalog_path :
        Catalog identity (may be ``None`` for synthetic smokes).
    fence :
        Fence attestation payload; default stub until INFR-011 fence is pinned.
    nautilus_version, platform :
        Pin record (one-platform rule).
    extra_metadata :
        Optional additional metadata fields.
    """
    root = Path(run_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = EmissionPaths(root)

    fills_df = _df_or_empty(fills)
    orders_df = _df_or_empty(orders)
    pos_df = _df_or_empty(positions_ledger)
    bars_df = _df_or_empty(bar_marks)

    fills_df.write_parquet(paths.fills)
    orders_df.write_parquet(paths.orders)
    pos_df.write_parquet(paths.positions_ledger)
    bars_df.write_parquet(paths.bar_marks)

    paths.instrument_id_map.write_text(
        json.dumps(instrument_id_map, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    fence_payload = fence or {
        "status": "STUB",
        "analysis_end_utc": None,
        "note": "Fence pin lands in INFR-011 Phase A6; stub for Phase B foundation only.",
    }
    paths.fence_attestation.write_text(
        json.dumps(fence_payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    # Deterministic event log (UUID-stripped).
    log_lines = [
        json.dumps({"kind": "fill", **rec}, sort_keys=True, separators=(",", ":"))
        for rec in _records_for_log(fills_df, _FILL_LOG_COLS)
    ]
    log_lines += [
        json.dumps({"kind": "order", **rec}, sort_keys=True, separators=(",", ":"))
        for rec in _records_for_log(orders_df, _ORDER_LOG_COLS)
    ]
    log_lines += [
        json.dumps({"kind": "position", **rec}, sort_keys=True, separators=(",", ":"))
        for rec in _records_for_log(pos_df, _POS_LOG_COLS)
    ]
    log_body = "\n".join(log_lines) + ("\n" if log_lines else "")
    paths.event_log.write_text(log_body, encoding="utf-8")
    event_log_sha256 = hashlib.sha256(log_body.encode()).hexdigest()

    meta = {
        "emission_contract_version": EMISSION_CONTRACT_VERSION,
        "generated_utc": datetime.now(UTC).isoformat(),
        "config_hash": config_hash(run_config),
        "run_config": run_config,
        "catalog_version": catalog_version,
        "catalog_path": catalog_path,
        "nautilus_version": nautilus_version,
        "platform": platform,
        "instrument_id_map": instrument_id_map,
        "fence_attestation_path": paths.fence_attestation.name,
        "event_log_sha256": event_log_sha256,
        "n_fills": fills_df.height,
        "n_orders": orders_df.height,
        "n_positions": pos_df.height,
        "n_bar_marks": bars_df.height,
    }
    if extra_metadata:
        meta.update(extra_metadata)
    paths.run_metadata.write_text(
        json.dumps(meta, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    return paths


@dataclass(frozen=True)
class LoadedEmission:
    paths: EmissionPaths
    metadata: dict[str, Any]
    fills: pl.DataFrame
    orders: pl.DataFrame
    positions_ledger: pl.DataFrame
    bar_marks: pl.DataFrame
    instrument_id_map: dict[str, str]
    fence: dict[str, Any]
    event_log_text: str


def load_emission_v1(run_dir: str | Path) -> LoadedEmission:
    """Load an emission-contract-v1 directory."""
    paths = EmissionPaths(Path(run_dir))
    if not paths.run_metadata.exists():
        raise FileNotFoundError(f"not a nautilus emission v1 dir: {paths.root}")
    metadata = json.loads(paths.run_metadata.read_text(encoding="utf-8"))
    instrument_id_map = json.loads(paths.instrument_id_map.read_text(encoding="utf-8"))
    fence = json.loads(paths.fence_attestation.read_text(encoding="utf-8"))
    return LoadedEmission(
        paths=paths,
        metadata=metadata,
        fills=pl.read_parquet(paths.fills),
        orders=pl.read_parquet(paths.orders),
        positions_ledger=pl.read_parquet(paths.positions_ledger),
        bar_marks=pl.read_parquet(paths.bar_marks),
        instrument_id_map=instrument_id_map,
        fence=fence,
        event_log_text=paths.event_log.read_text(encoding="utf-8"),
    )
