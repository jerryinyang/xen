from __future__ import annotations

import hashlib
import json
from pathlib import Path

import polars as pl

from xen.liqswp_analysis.source import (
    SourceSpec,
    join_profiles_left,
    scan_train_columns,
    validate_causal_order,
    validate_source_contract,
)


TRAIN_END_NS = 1_000


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _source_tree(tmp_path: Path) -> SourceSpec:
    root = tmp_path / "emission"
    gate_dir = tmp_path / "cell_gates"
    family_cells = []
    for index in range(2):
        cell_name = f"cell-{index}"
        cell = root / cell_name
        cell.mkdir(parents=True)
        event_bytes = f"event-{index}\n".encode()
        (cell / "event_log.jsonl").write_bytes(event_bytes)
        config_hash = f"hash-{index}"
        metadata = {
            "config_hash": config_hash,
            "event_log_sha256": hashlib.sha256(event_bytes).hexdigest(),
            "cost_model": "NO_COST_CHARGED",
            "n_raids": 1,
            "run_config": {
                "cell": {
                    "archive_symbol": "EURUSD",
                    "observation_minutes": 15,
                    "confirmation_method": "BREAKOUT_BAR",
                    "confirmation_reference": "1H",
                    "level_config": f"CONFIG_{index}",
                }
            },
        }
        _write_json(cell / "run_metadata.json", metadata)
        _write_json(
            cell / "fence_attestation.json",
            {"status": "PINNED", "train_end_ns": TRAIN_END_NS},
        )
        pl.DataFrame(
            {
                "raid_id": [f"R{index}"],
                "config": [f"CONFIG_{index}"],
                "source_configuration": [f"CONFIG_{index}"],
                "archive_symbol": ["EURUSD"],
                "timeframe": ["15m"],
                "confirmation_method": ["BREAKOUT_BAR"],
                "confirmation_reference": ["1H"],
                "raid_ts_ns": [100],
                "sweep_ts_ns": [200],
                "confirmation_ts_ns": [200],
                "endpoint_ts_ns": [300],
                "unused": [99],
            }
        ).write_parquet(cell / "raids.parquet")
        cell_gate = {
            "blocking_pass": True,
            "run_dir": str(cell),
            "catalog_attestation": {"config_hash": config_hash},
            "no_cost_charged": {"ok": True, "cost_model": "NO_COST_CHARGED"},
        }
        _write_json(gate_dir / f"{cell_name}.json", cell_gate)
        family_cells.append(cell_gate)
    family_gate = tmp_path / "family_gate.json"
    _write_json(
        family_gate,
        {"blocking_pass": True, "n_cells": 2, "cells": family_cells},
    )
    return SourceSpec(
        root=root,
        family_gate=family_gate,
        cell_gate_dir=gate_dir,
        expected_cells=2,
        table="raids.parquet",
        required_columns=(
            "raid_id",
            "config",
            "source_configuration",
            "archive_symbol",
            "timeframe",
            "confirmation_method",
            "confirmation_reference",
            "raid_ts_ns",
            "sweep_ts_ns",
            "confirmation_ts_ns",
            "endpoint_ts_ns",
        ),
        object_id_column="raid_id",
        train_end_column="endpoint_ts_ns",
        train_end_ns=TRAIN_END_NS,
    )


def test_source_contract_reconciles_all_cell_authorities(tmp_path: Path) -> None:
    result = validate_source_contract(_source_tree(tmp_path))
    assert result.integrity.blocking_pass
    assert result.evidence["cells"] == 2
    assert result.evidence["rows"] == 2
    assert result.evidence["duplicate_object_ids"] == 0


def test_missing_cell_gate_fails_closed(tmp_path: Path) -> None:
    spec = _source_tree(tmp_path)
    (spec.cell_gate_dir / "cell-1.json").unlink()
    result = validate_source_contract(spec)
    assert not result.integrity.blocking_pass
    assert "VOID_CELL_GATE_COUNT" in result.integrity.reasons


def test_config_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    spec = _source_tree(tmp_path)
    gate_path = spec.cell_gate_dir / "cell-1.json"
    gate = json.loads(gate_path.read_text())
    gate["catalog_attestation"]["config_hash"] = "wrong"
    _write_json(gate_path, gate)
    result = validate_source_contract(spec)
    assert not result.integrity.blocking_pass
    assert "VOID_CONFIG_HASH_MISMATCH" in result.integrity.reasons


def test_row_identity_and_duplicate_ids_fail_closed(tmp_path: Path) -> None:
    spec = _source_tree(tmp_path)
    cell = spec.root / "cell-1"
    frame = pl.read_parquet(cell / "raids.parquet").with_columns(
        pl.lit("WRONG").alias("source_configuration"),
        pl.lit("R0").alias("raid_id"),
    )
    # Object ids are cell-scoped in the frozen emission (level/raid identities
    # repeat across instruments and timeframes), so the duplicate check is
    # within-cell; two rows sharing a raid_id in one cell must fail closed.
    frame = pl.concat([frame, frame], how="vertical_relaxed")
    frame.write_parquet(cell / "raids.parquet")
    result = validate_source_contract(spec)
    assert not result.integrity.blocking_pass
    assert "VOID_SOURCE_CONFIGURATION_MISMATCH" in result.integrity.reasons
    assert "VOID_DUPLICATE_OBJECT_ID" in result.integrity.reasons


def test_timestamp_after_train_and_causal_inversion_fail_closed(tmp_path: Path) -> None:
    spec = _source_tree(tmp_path)
    cell = spec.root / "cell-1"
    frame = pl.read_parquet(cell / "raids.parquet").with_columns(
        pl.lit(1_001).alias("endpoint_ts_ns"),
        pl.lit(50).alias("confirmation_ts_ns"),
    )
    frame.write_parquet(cell / "raids.parquet")
    result = validate_source_contract(spec)
    assert not result.integrity.blocking_pass
    assert "VOID_AFTER_TRAIN" in result.integrity.reasons
    assert "VOID_CAUSAL_ORDER" in result.integrity.reasons


def test_projected_scan_exposes_only_requested_columns(tmp_path: Path) -> None:
    spec = _source_tree(tmp_path)
    collected = scan_train_columns(
        sorted(spec.root.glob("*/raids.parquet")),
        columns=("raid_id", "endpoint_ts_ns"),
        train_end_column="endpoint_ts_ns",
        train_end_ns=TRAIN_END_NS,
    ).collect()
    assert collected.columns == ["raid_id", "endpoint_ts_ns"]
    assert collected.height == 2


def test_projected_scan_retains_null_censored_endpoint(tmp_path: Path) -> None:
    spec = _source_tree(tmp_path)
    path = spec.root / "cell-0" / "raids.parquet"
    frame = pl.read_parquet(path).with_columns(pl.lit(None, dtype=pl.Int64).alias("endpoint_ts_ns"))
    frame.write_parquet(path)
    collected = scan_train_columns(
        [path],
        columns=("raid_id", "endpoint_ts_ns"),
        train_end_column="endpoint_ts_ns",
        train_end_ns=TRAIN_END_NS,
    ).collect()
    assert collected.height == 1
    assert collected["endpoint_ts_ns"].null_count() == 1


def test_missing_required_column_fails_closed_without_read_error(tmp_path: Path) -> None:
    spec = _source_tree(tmp_path)
    path = spec.root / "cell-1" / "raids.parquet"
    pl.read_parquet(path).drop("confirmation_reference").write_parquet(path)
    result = validate_source_contract(spec)
    assert not result.integrity.blocking_pass
    assert "VOID_SCHEMA" in result.integrity.reasons


def test_gate_run_directory_mismatch_fails_closed(tmp_path: Path) -> None:
    spec = _source_tree(tmp_path)
    gate_path = spec.cell_gate_dir / "cell-1.json"
    gate = json.loads(gate_path.read_text())
    gate["run_dir"] = str(spec.root / "cell-0")
    _write_json(gate_path, gate)
    result = validate_source_contract(spec)
    assert not result.integrity.blocking_pass
    assert "VOID_GATE_RUN_DIR" in result.integrity.reasons


def test_family_and_cell_gate_disagreement_fails_closed(tmp_path: Path) -> None:
    spec = _source_tree(tmp_path)
    family = json.loads(spec.family_gate.read_text())
    family["cells"][1]["catalog_attestation"]["config_hash"] = "different"
    _write_json(spec.family_gate, family)
    result = validate_source_contract(spec)
    assert not result.integrity.blocking_pass
    assert "VOID_GATE_RECONCILIATION" in result.integrity.reasons


def test_causal_order_returns_named_failed_pair() -> None:
    frame = pl.DataFrame({"raid": [10], "confirm": [9], "end": [11]})
    failures = validate_causal_order(frame, (("raid", "confirm"), ("confirm", "end")))
    assert failures == [{"earlier": "raid", "later": "confirm", "rows": 1}]


def test_profile_left_join_keeps_unmatched_evidence() -> None:
    raids = pl.DataFrame({"raid_id": ["R0", "R1"], "value": [1, 2]})
    profiles = pl.DataFrame({"raid_id": ["R0"], "profile_status": ["DEFINED"]})
    joined, evidence = join_profiles_left(raids, profiles, key="raid_id")
    assert joined.height == 2
    assert evidence == {
        "raid_rows": 2,
        "profile_rows": 1,
        "matched_rows": 1,
        "unmatched_raids": 1,
        "duplicate_profile_keys": 0,
    }
