"""Gate-first, projected TRAIN source validation for liquidity-sweep analyses."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import polars as pl

from xen.liqswp_analysis.contract import IntegrityStatus


@dataclass(frozen=True)
class SourceSpec:
    """Pinned source facts required before any experiment estimator runs."""

    root: Path
    family_gate: Path
    cell_gate_dir: Path
    expected_cells: int
    table: str
    required_columns: tuple[str, ...]
    object_id_column: str
    train_end_column: str
    train_end_ns: int
    # New: UTC fence timestamp for human-readable validation
    train_end_utc: str | None = None


@dataclass(frozen=True)
class SourceAttestation:
    """Source integrity status and complete reconciliation evidence."""

    integrity: IntegrityStatus
    evidence: dict[str, Any]
    paths: tuple[Path, ...] = ()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_train_columns(
    paths: Sequence[Path],
    *,
    columns: Sequence[str],
    train_end_column: str,
    train_end_ns: int,
) -> pl.LazyFrame:
    """Scan only requested columns and only rows inside the pinned TRAIN boundary."""
    requested = list(dict.fromkeys((*columns, train_end_column)))
    return (
        pl.scan_parquet([str(path) for path in paths])
        .select(requested)
        .filter(
            pl.col(train_end_column).is_null() | (pl.col(train_end_column) <= int(train_end_ns))
        )
        .select(list(columns))
    )


def validate_causal_order(
    frame: pl.DataFrame, pairs: Sequence[tuple[str, str]]
) -> list[dict[str, Any]]:
    """Return every timestamp pair that violates earlier <= later on non-null rows."""
    failures: list[dict[str, Any]] = []
    for earlier, later in pairs:
        if earlier not in frame.columns or later not in frame.columns:
            continue
        invalid = frame.filter(
            pl.col(earlier).is_not_null()
            & pl.col(later).is_not_null()
            & (pl.col(earlier) > pl.col(later))
        ).height
        if invalid:
            failures.append({"earlier": earlier, "later": later, "rows": invalid})
    return failures


def _metadata_identity_failures(frame: pl.DataFrame, metadata: dict[str, Any]) -> list[str]:
    cell = metadata.get("run_config", {}).get("cell", {})
    expected = {
        "archive_symbol": cell.get("archive_symbol"),
        "timeframe": (
            f"{int(cell['observation_minutes'])}m"
            if cell.get("observation_minutes") is not None
            else None
        ),
        "confirmation_method": cell.get("confirmation_method"),
        "confirmation_reference": cell.get("confirmation_reference"),
        "config": cell.get("level_config"),
    }
    failures = []
    for column, value in expected.items():
        if value is None or column not in frame.columns:
            continue
        if frame.filter(pl.col(column) != value).height:
            failures.append(f"VOID_ROW_IDENTITY_{column.upper()}")
    return failures


def _validate_utc_fence(train_end_ns: int, train_end_utc: str | None) -> list[str]:
    """Validate that train_end_ns matches the declared UTC fence."""
    reasons = []
    if train_end_utc is not None:
        # Parse UTC string and convert to ns
        # Expected format: "2023-11-22T00:00:00Z" or similar ISO format
        import datetime
        try:
            dt = datetime.datetime.fromisoformat(train_end_utc.replace("Z", "+00:00"))
            expected_ns = int(dt.timestamp() * 1_000_000_000)
            if expected_ns != train_end_ns:
                reasons.append(f"VOID_UTC_FENCE_MISMATCH: expected {expected_ns}, got {train_end_ns}")
        except (ValueError, AttributeError):
            reasons.append("VOID_UTC_FENCE_PARSE_ERROR")
    return reasons


def _validate_composite_uniqueness(
    frame: pl.DataFrame,
    source_cell: str,
    object_id_column: str,
) -> tuple[int, list[str]]:
    """Validate composite (source_cell, raid_id) uniqueness."""
    reasons = []
    # Add source_cell column if not present
    if "source_cell" not in frame.columns:
        frame = frame.with_columns(pl.lit(source_cell).alias("source_cell"))

    # Check composite key uniqueness
    composite_key = ["source_cell", object_id_column]
    duplicates = (
        frame.group_by(composite_key)
        .len()
        .filter(pl.col("len") > 1)
        .select(pl.col("len").sum().fill_null(0))
        .item()
    )
    if duplicates:
        reasons.append("VOID_COMPOSITE_DUPLICATE_OBJECT_ID")
    return int(duplicates), reasons


def validate_source_contract(spec: SourceSpec) -> SourceAttestation:
    """Validate gates, hashes, identities, counts, fence, and causality before analysis."""
    reasons: list[str] = []
    evidence: dict[str, Any] = {
        "expected_cells": int(spec.expected_cells),
        "cells": 0,
        "rows": 0,
        "duplicate_object_ids": 0,
        "composite_duplicate_object_ids": 0,
        "causal_failures": [],
    }

    # UTC fence validation
    reasons.extend(_validate_utc_fence(spec.train_end_ns, spec.train_end_utc))

    if not spec.family_gate.exists():
        return SourceAttestation(IntegrityStatus(False, ("VOID_MISSING_FAMILY_GATE",)), evidence)
    family_gate = _read_json(spec.family_gate)
    if not family_gate.get("blocking_pass"):
        reasons.append("VOID_FAMILY_GATE")
    if int(family_gate.get("n_cells", -1)) != spec.expected_cells:
        reasons.append("VOID_FAMILY_GATE_COUNT")
    cell_dirs = sorted(path for path in spec.root.iterdir() if path.is_dir())
    gate_paths = sorted(spec.cell_gate_dir.glob("*.json"))
    evidence["cells"] = len(cell_dirs)
    evidence["cell_gates"] = len(gate_paths)
    if len(cell_dirs) != spec.expected_cells:
        reasons.append("VOID_SOURCE_CELL_COUNT")
    if len(gate_paths) != spec.expected_cells:
        reasons.append("VOID_CELL_GATE_COUNT")
    gates_by_name = {path.stem: _read_json(path) for path in gate_paths}
    family_by_name = {
        Path(str(cell.get("run_dir", ""))).name: cell for cell in family_gate.get("cells", [])
    }
    if set(family_by_name) != set(gates_by_name):
        reasons.append("VOID_GATE_RECONCILIATION")
    else:
        for name, gate in gates_by_name.items():
            family_cell = family_by_name[name]
            if (
                family_cell.get("blocking_pass") != gate.get("blocking_pass")
                or family_cell.get("catalog_attestation", {}).get("config_hash")
                != gate.get("catalog_attestation", {}).get("config_hash")
                or family_cell.get("no_cost_charged", {}).get("ok")
                != gate.get("no_cost_charged", {}).get("ok")
            ):
                reasons.append("VOID_GATE_RECONCILIATION")
    table_paths: list[Path] = []
    for cell_dir in cell_dirs:
        gate = gates_by_name.get(cell_dir.name)
        if gate is None:
            continue
        if not gate.get("blocking_pass"):
            reasons.append("VOID_CELL_GATE")
        if Path(str(gate.get("run_dir", ""))).resolve() != cell_dir.resolve():
            reasons.append("VOID_GATE_RUN_DIR")
        metadata_path = cell_dir / "run_metadata.json"
        event_path = cell_dir / "event_log.jsonl"
        fence_path = cell_dir / "fence_attestation.json"
        table_path = cell_dir / spec.table
        if not all(path.exists() for path in (metadata_path, event_path, fence_path, table_path)):
            reasons.append("VOID_MISSING_SOURCE_ARTIFACT")
            continue
        metadata = _read_json(metadata_path)
        fence = _read_json(fence_path)
        gate_hash = gate.get("catalog_attestation", {}).get("config_hash")
        if metadata.get("config_hash") != gate_hash:
            reasons.append("VOID_CONFIG_HASH_MISMATCH")
        if metadata.get("event_log_sha256") != _sha256(event_path):
            reasons.append("VOID_EVENT_HASH_MISMATCH")
        if metadata.get("cost_model") != "NO_COST_CHARGED" or not gate.get(
            "no_cost_charged", {}
        ).get("ok"):
            reasons.append("VOID_ZERO_COST")
        if fence.get("status") != "PINNED":
            reasons.append("VOID_FENCE_STATUS")
        # The pinned fence declares train_end_utc; train_end_ns is validated
        # only when present (older receipts carry the UTC fence only).
        if spec.train_end_utc is not None and fence.get("train_end_utc") != spec.train_end_utc:
            reasons.append("VOID_FENCE_BOUNDARY")
        if "train_end_ns" in fence and int(fence["train_end_ns"]) != int(spec.train_end_ns):
            reasons.append("VOID_FENCE_BOUNDARY")
        available = set(pl.scan_parquet(table_path).collect_schema().names())
        missing = [column for column in spec.required_columns if column not in available]
        if missing:
            reasons.append("VOID_SCHEMA")
            continue
        lazy = pl.scan_parquet(table_path).select(spec.required_columns)
        row_count = lazy.select(pl.len()).collect(engine="streaming").item()
        evidence["rows"] += int(row_count)
        if "source_configuration" in available and "config" in available:
            mismatch = (
                lazy.select((pl.col("source_configuration") != pl.col("config")).sum())
                .collect(engine="streaming")
                .item()
            )
            if mismatch:
                reasons.append("VOID_SOURCE_CONFIGURATION_MISMATCH")
        identity_frame = (
            lazy.select(
                column
                for column in (
                    "archive_symbol",
                    "timeframe",
                    "confirmation_method",
                    "confirmation_reference",
                    "config",
                )
                if column in available
            )
            .unique()
            .collect(engine="streaming")
        )
        reasons.extend(_metadata_identity_failures(identity_frame, metadata))
        expected_rows = metadata.get(f"n_{Path(spec.table).stem}")
        if expected_rows is not None and int(expected_rows) != row_count:
            reasons.append("VOID_ROW_COUNT_MISMATCH")
        if (
            lazy.select((pl.col(spec.train_end_column) > int(spec.train_end_ns)).sum())
            .collect(engine="streaming")
            .item()
        ):
            reasons.append("VOID_AFTER_TRAIN")
        causal_failures = []
        for earlier, later in (
            ("raid_ts_ns", "sweep_ts_ns"),
            ("sweep_ts_ns", "return_ts_ns"),
            ("return_ts_ns", "confirmation_ts_ns"),
            ("sweep_ts_ns", "confirmation_ts_ns"),
            ("confirmation_ts_ns", "endpoint_ts_ns"),
        ):
            if earlier not in available or later not in available:
                continue
            invalid = (
                lazy.select(
                    (
                        pl.col(earlier).is_not_null()
                        & pl.col(later).is_not_null()
                        & (pl.col(earlier) > pl.col(later))
                    ).sum()
                )
                .collect(engine="streaming")
                .item()
            )
            if invalid:
                causal_failures.append({"earlier": earlier, "later": later, "rows": int(invalid)})
        if causal_failures:
            reasons.append("VOID_CAUSAL_ORDER")
            evidence["causal_failures"].extend(causal_failures)
        # Within-cell object-id uniqueness (cell-scoped identities in the frozen
        # emission); cross-cell identity is covered by the composite check below.
        cell_duplicates = (
            lazy.group_by(spec.object_id_column)
            .len()
            .filter(pl.col("len") > 1)
            .select(pl.col("len").sum().fill_null(0))
            .collect(engine="streaming")
            .item()
        )
        evidence["duplicate_object_ids"] += int(cell_duplicates)
        if cell_duplicates:
            reasons.append("VOID_DUPLICATE_OBJECT_ID")
        table_paths.append(table_path)

    # Object-id uniqueness is cell-scoped in the frozen emission (level and raid
    # identities repeat across instruments/timeframes); the authoritative check
    # is the composite (source_cell, raid_id) uniqueness below.

    # New: Check composite (source_cell, raid_id) uniqueness across all cells
    # This requires loading the data with source_cell column
    composite_duplicates_total = 0
    for cell_dir in cell_dirs:
        gate = gates_by_name.get(cell_dir.name)
        if gate is None or not gate.get("blocking_pass"):
            continue
        table_path = cell_dir / spec.table
        if not table_path.exists():
            continue
        # Load with source_cell
        lazy = pl.scan_parquet(table_path).select([spec.object_id_column])
        lazy = lazy.with_columns(pl.lit(cell_dir.name).alias("source_cell"))
        composite_duplicates, comp_reasons = _validate_composite_uniqueness(
            lazy.collect(engine="streaming"), cell_dir.name, spec.object_id_column
        )
        composite_duplicates_total += composite_duplicates
        reasons.extend(comp_reasons)
    evidence["composite_duplicate_object_ids"] = composite_duplicates_total
    evidence["duplicate_object_ids"] = composite_duplicates_total

    unique_reasons = tuple(dict.fromkeys(reasons))
    return SourceAttestation(
        integrity=IntegrityStatus(
            blocking_pass=not unique_reasons,
            reasons=unique_reasons,
            evidence=evidence,
        ),
        evidence=evidence,
        paths=tuple(table_paths),
    )


def join_profiles_left(
    raids: pl.DataFrame, profiles: pl.DataFrame, *, key: str
) -> tuple[pl.DataFrame, dict[str, int]]:
    """Left-join profiles while retaining duplicate and unmatched evidence."""
    duplicate_profiles = profiles.select(pl.col(key).is_duplicated().sum()).item()
    marked = profiles.with_columns(pl.lit(True).alias("__profile_match"))
    joined = raids.join(marked, on=key, how="left")
    matched = joined.filter(pl.col("__profile_match") == True).height  # noqa: E712
    joined = joined.drop("__profile_match")
    return joined, {
        "raid_rows": raids.height,
        "profile_rows": profiles.height,
        "matched_rows": matched,
        "unmatched_raids": raids.height - matched,
        "duplicate_profile_keys": int(duplicate_profiles),
    }

