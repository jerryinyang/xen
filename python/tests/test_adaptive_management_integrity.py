from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import polars as pl
import pytest

from xen.adaptive_management.contracts import (
    build_management_lattice,
    build_native_lattice,
)
from xen.adaptive_management.integrity import (
    INTEGRITY_ARTIFACTS,
    derange_component_times,
    future_shift_tripwire,
    magnitude_matched_controls,
    run_integrity_checks,
)


def _feature_fixture() -> pl.DataFrame:
    start = datetime(2023, 1, 1, tzinfo=timezone.utc)
    return pl.DataFrame(
        {
            "symbol": ["SYN"] * 6,
            "ts": [start + timedelta(hours=i) for i in range(6)],
            "magnitude_bps": [10.0, 12.0, 21.0, 23.0, 31.0, 34.0],
        }
    )


def test_derangement_has_zero_fixed_points():
    features = _feature_fixture()
    out = derange_component_times(features, seed=240730)
    assert out.height == features.height
    assert out["source_ts"].n_unique() == features["ts"].n_unique()
    assert (out["source_ts"] == out["ts"]).sum() == 0


def test_future_shift_changes_mapping_without_changing_rows():
    features = _feature_fixture()
    out = future_shift_tripwire(features)
    assert out["row_count_before"] == out["row_count_after"]
    assert out["unchanged_fraction"] < 1.0


def test_magnitude_match_preserves_named_strata():
    features = _feature_fixture()
    episodes = pl.DataFrame(
        {
            "episode_id": [f"E{i}" for i in range(6)],
            "symbol": ["SYN"] * 6,
            "decision_ts": features["ts"],
            "entry_variant": ["BREAKOUT"] * 6,
        }
    )
    out = magnitude_matched_controls(episodes, features)
    assert out["symbol"].null_count() == 0
    assert out["magnitude_bin"].null_count() == 0
    assert out["selected"].any()
    assert (~out["selected"]).any()


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _valid_run(root: Path, experiment_id: str = "SPDR-021") -> Path:
    run = root / "run"
    run.mkdir()
    start = datetime(2023, 1, 1, tzinfo=timezone.utc)
    times = [start + timedelta(hours=i) for i in range(4)]
    manifest = root / "manifest.json"
    manifest.write_text('{"frozen":true}\n', encoding="utf-8")
    manifest_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()
    _write_json(
        run / "config.json",
        {
            "experiment_id": experiment_id,
            "universe": "crypto",
            "band": "TRAIN",
        },
    )
    _write_json(
        run / "fence_attestation.json",
        {
            "status": "PINNED",
            "manifest_path": str(manifest),
            "manifest_sha256": manifest_hash,
            "train_end_utc": (start + timedelta(days=1)).isoformat(),
        },
    )
    features = pl.DataFrame(
        {
            "symbol": ["SYN"] * 4,
            "ts": times,
            "source_ts": times,
            "swing_scale_bps": [10.0, 20.0, 30.0, 40.0],
        }
    )
    origins = pl.DataFrame(
        {
            "origin_id": [f"O{i}" for i in range(4)],
            "symbol": ["SYN"] * 4,
            "decision_ts": times,
            "entry_variant": ["BREAKOUT"] * 4
            if experiment_id == "SPDR-021"
            else ["E_TOUCH", "E_CLOSE", "E_TOUCH", "E_CLOSE"],
        }
    )
    native = pl.from_dicts(
        [
            {
                "origin_id": origin_id,
                "entry_variant": arm.entry_variant,
                "arm_id": arm.native_arm_id,
                "arm_class": "FIXED_NATIVE" if not arm.is_adaptive else "NATIVE",
                "native_arm_id": arm.native_arm_id,
                "policy_id": "NONE",
                "comparator_id": arm.comparator_id,
            }
            for arm in build_native_lattice(experiment_id)
            for origin_id in origins.filter(
                pl.col("entry_variant") == arm.entry_variant
            )["origin_id"]
        ]
    )
    logical_policies = {}
    for policy in build_management_lattice(experiment_id):
        policy_id = (
            policy.combination_id
            if policy.combination_id and policy.combination_id.startswith("DC_")
            else policy.policy_id
        )
        logical_policies.setdefault(policy_id, policy)
    variants = (
        ["BREAKOUT"] if experiment_id == "SPDR-021" else ["E_TOUCH", "E_CLOSE"]
    )
    policies = pl.from_dicts(
        [
            {
                "origin_id": origin_id,
                "entry_variant": variant,
                "arm_id": policy_id,
                "arm_class": "FIXED_MANAGEMENT"
                if not policy.is_adaptive
                else "MANAGEMENT",
                "native_arm_id": None,
                "policy_id": policy_id,
                "comparator_id": policy.comparator_id,
            }
            for policy_id, policy in logical_policies.items()
            for variant in variants
            for origin_id in origins.filter(pl.col("entry_variant") == variant)[
                "origin_id"
            ]
        ],
        infer_schema_length=None,
    )
    features.write_parquet(run / "features.parquet")
    origins.write_parquet(run / "origins.parquet")
    native.write_parquet(run / "native_parameter_schedule.parquet")
    policies.write_parquet(run / "policy_schedule.parquet")
    pl.DataFrame(
        {
            "client_order_id": ["ENTRY", "EXIT"],
            "status": ["FILLED", "FILLED"],
        }
    ).write_parquet(run / "orders.parquet")
    pl.DataFrame(
        {
            "client_order_id": ["ENTRY", "EXIT"],
            "position_id": ["P1", "P1"],
            "price": [100.0, 102.0],
        }
    ).write_parquet(run / "fills.parquet")
    pl.DataFrame(
        {
            "position_id": ["P1"],
            "avg_px_open": [100.0],
            "avg_px_close": [102.0],
        }
    ).write_parquet(run / "positions.parquet")
    pl.from_dicts(
        [
            {
                "episode_id": "E1",
                "arm_id": "FIXED_TARGET_M1.00",
                "position_id": "P1",
                "state": "ORDER_CREATED",
                "ts_ns": 1,
                "price": None,
                "side": 1,
                "outcome_bps": None,
                "exit_reason": None,
            },
            {
                "episode_id": "E1",
                "arm_id": "FIXED_TARGET_M1.00",
                "position_id": "P1",
                "state": "FILLED",
                "ts_ns": 2,
                "price": 100.0,
                "side": 1,
                "outcome_bps": None,
                "exit_reason": None,
            },
            {
                "episode_id": "E1",
                "arm_id": "FIXED_TARGET_M1.00",
                "position_id": "P1",
                "state": "CLOSED",
                "ts_ns": 3,
                "price": 102.0,
                "side": 1,
                "outcome_bps": 200.0,
                "exit_reason": "TARGET",
            },
        ],
        infer_schema_length=None,
    ).write_parquet(run / "episode_results.parquet")
    cells = run / "cells" / "SYN"
    cells.mkdir(parents=True)
    pl.DataFrame(
        {
            "SourceCloseTime": times,
            "RealOpen": [100.0] * 4,
            "RealHigh": [101.0] * 4,
            "RealLow": [99.0] * 4,
            "RealClose": [100.0] * 4,
        }
    ).write_parquet(cells / "bar_marks.parquet")
    return run


def test_two_arms_closing_one_episode_is_not_a_golden_trace_failure(tmp_path):
    # Every management arm closes its own leg of the same episode. Only a second close for
    # the same arm means an exit was rewritten after the first closing fill.
    run = _valid_run(tmp_path)
    path = run / "episode_results.parquet"
    frame = pl.read_parquet(path)
    closed = frame.filter(pl.col("state") == "CLOSED")
    sibling = closed.with_columns(
        pl.lit("SIBLING_ARM").alias("arm_id"),
        pl.lit("SIBLING_POLICY").alias("policy_id"),
    )
    pl.concat([frame, sibling], how="diagonal_relaxed").write_parquet(path)
    result = run_integrity_checks(run)
    assert result["hard_checks"]["golden_traces"] is True


def test_valid_run_passes_and_writes_complete_integrity_package(tmp_path):
    run = _valid_run(tmp_path)
    result = run_integrity_checks(run)
    assert result["blocking_pass"] is True
    assert set(result["hard_checks"]) == {
        "fence",
        "provenance",
        "causality",
        "entry_parity",
        "golden_traces",
        "order_fill_position_reconciliation",
        "row_accounting",
        "native_lattice",
        "management_lattice",
        "no_native_management_cross",
        "unique_result_keys",
        "future_shift_changed_mapping",
        "deterministic_replay",
    }
    assert set(INTEGRITY_ARTIFACTS).issubset(
        {path.name for path in run.iterdir()}
    )
    for artifact in INTEGRITY_ARTIFACTS:
        payload = json.loads((run / artifact).read_text(encoding="utf-8"))
        assert payload["experiment_id"] == "SPDR-021"
        assert payload["universe"] == "crypto"
        assert payload["source_artifact_hashes"]
        assert "verdict" not in json.dumps(payload).lower()


@pytest.mark.parametrize(
    ("target", "mutation"),
    [
        ("fence", "stub_manifest"),
        ("fence", "bar_after_train"),
        ("causality", "future_source"),
        ("native_lattice", "missing_native"),
        ("management_lattice", "missing_policy"),
        ("management_lattice", "missing_comparator"),
        ("no_native_management_cross", "cross"),
        ("unique_result_keys", "duplicate_result"),
        ("order_fill_position_reconciliation", "open_order"),
        ("order_fill_position_reconciliation", "fill_without_order"),
        ("order_fill_position_reconciliation", "closed_with_one_fill"),
        ("order_fill_position_reconciliation", "wrong_close_price"),
        ("entry_parity", "wrong_entry_variant"),
        ("golden_traces", "second_close"),
        ("deterministic_replay", "wrong_replay_hash"),
    ],
)
def test_each_hard_integrity_failure_is_named(tmp_path, target, mutation):
    run = _valid_run(tmp_path)
    if mutation == "stub_manifest":
        payload = json.loads((run / "fence_attestation.json").read_text())
        payload["status"] = "STUB"
        _write_json(run / "fence_attestation.json", payload)
    elif mutation == "bar_after_train":
        path = run / "cells" / "SYN" / "bar_marks.parquet"
        bars = pl.read_parquet(path).with_columns(
            pl.when(pl.int_range(pl.len()) == 0)
            .then(pl.lit(datetime(2023, 1, 3, tzinfo=timezone.utc)))
            .otherwise(pl.col("SourceCloseTime"))
            .alias("SourceCloseTime")
        )
        bars.write_parquet(path)
    elif mutation == "future_source":
        path = run / "features.parquet"
        pl.read_parquet(path).with_columns(
            (pl.col("source_ts") + pl.duration(hours=1)).alias("source_ts")
        ).write_parquet(path)
    elif mutation == "missing_native":
        path = run / "native_parameter_schedule.parquet"
        frame = pl.read_parquet(path)
        missing = frame["arm_id"][0]
        frame.filter(pl.col("arm_id") != missing).write_parquet(path)
    elif mutation == "missing_policy":
        path = run / "policy_schedule.parquet"
        frame = pl.read_parquet(path)
        missing = frame["policy_id"][0]
        frame.filter(pl.col("policy_id") != missing).write_parquet(path)
    elif mutation == "missing_comparator":
        path = run / "policy_schedule.parquet"
        frame = pl.read_parquet(path)
        adaptive = frame.filter(pl.col("arm_id") != pl.col("comparator_id"))["arm_id"][0]
        frame.with_columns(
            pl.when(pl.col("arm_id") == adaptive)
            .then(pl.lit("FIXED_MISSING"))
            .otherwise(pl.col("comparator_id"))
            .alias("comparator_id")
        ).write_parquet(path)
    elif mutation == "cross":
        path = run / "policy_schedule.parquet"
        pl.read_parquet(path).with_columns(
            pl.lit("NATIVE").alias("native_arm_id")
        ).write_parquet(path)
    elif mutation == "duplicate_result":
        path = run / "episode_results.parquet"
        frame = pl.read_parquet(path)
        pl.concat([frame, frame.head(1)]).write_parquet(path)
    elif mutation == "open_order":
        path = run / "orders.parquet"
        pl.read_parquet(path).with_columns(pl.lit("OPEN").alias("status")).write_parquet(
            path
        )
    elif mutation == "fill_without_order":
        path = run / "fills.parquet"
        pl.read_parquet(path).with_columns(
            pl.lit("MISSING").alias("client_order_id")
        ).write_parquet(path)
    elif mutation == "wrong_close_price":
        path = run / "positions.parquet"
        pl.read_parquet(path).with_columns(
            pl.lit(103.0).alias("avg_px_close")
        ).write_parquet(path)
    elif mutation == "closed_with_one_fill":
        path = run / "fills.parquet"
        pl.read_parquet(path).head(1).write_parquet(path)
    elif mutation == "wrong_entry_variant":
        path = run / "origins.parquet"
        pl.read_parquet(path).with_columns(
            pl.lit("E_TOUCH").alias("entry_variant")
        ).write_parquet(path)
    elif mutation == "second_close":
        path = run / "episode_results.parquet"
        frame = pl.read_parquet(path)
        extra = frame.filter(pl.col("state") == "CLOSED").with_columns(
            pl.lit(4, dtype=pl.Int64).alias("ts_ns")
        )
        pl.concat([frame, extra]).write_parquet(path)
    elif mutation == "wrong_replay_hash":
        _write_json(run / "determinism_reference.json", {"replay_hashes": {}})
    result = run_integrity_checks(run)
    assert result["hard_checks"][target] is False
    assert result["blocking_pass"] is False


def test_breach_fixed_entry_parity_drift_is_blocking(tmp_path):
    run = _valid_run(tmp_path, "SPDR-022")
    native_path = run / "native_parameter_schedule.parquet"
    native = pl.read_parquet(native_path)
    fixed_touch = native.filter(
        (pl.col("arm_class") == "FIXED_NATIVE")
        & (pl.col("entry_variant") == "E_TOUCH")
    )
    remove_origin = fixed_touch["origin_id"][0]
    native.filter(
        ~(
            (pl.col("arm_class") == "FIXED_NATIVE")
            & (pl.col("entry_variant") == "E_TOUCH")
            & (pl.col("origin_id") == remove_origin)
        )
    ).write_parquet(native_path)
    result = run_integrity_checks(run)
    assert result["hard_checks"]["entry_parity"] is False
    assert result["blocking_pass"] is False


def test_failed_publish_never_exposes_complete_selfcheck(monkeypatch, tmp_path):
    from xen.adaptive_management import integrity

    run = _valid_run(tmp_path)
    real_write = integrity._atomic_json
    calls = 0

    def fail_during_publish(payload, path):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError("injected write failure")
        real_write(payload, path)

    monkeypatch.setattr(integrity, "_atomic_json", fail_during_publish)
    with pytest.raises(OSError, match="injected write failure"):
        run_integrity_checks(run)
    assert not (run / "integrity_selfcheck.json").exists()
    assert not any(run.glob(".integrity.tmp-*"))


def _reference_ledger_agrees(ledger: pl.DataFrame, positions: pl.DataFrame) -> bool:
    """The original row-wise implementation, kept as the semantics reference."""
    import numpy as np

    from xen.adaptive_management.integrity import _derived_position_id, _first_column

    needed = {"state", "price"}
    if ledger.is_empty() or positions.is_empty() or not needed.issubset(ledger.columns):
        return False
    if "position_id" not in ledger.columns:
        identity = {"experiment_id", "arm_id", "entry_variant", "episode_id", "policy_id"}
        if not identity.issubset(ledger.columns):
            return False
        ledger = ledger.with_columns(
            pl.struct(sorted(identity))
            .map_elements(_derived_position_id, return_dtype=pl.Utf8)
            .alias("position_id")
        )
    position_id = _first_column(positions, "position_id", "id")
    open_column = _first_column(positions, "avg_px_open", "open_price")
    close_column = _first_column(positions, "avg_px_close", "close_price")
    if not position_id or not open_column or not close_column:
        return False
    for position in positions.iter_rows(named=True):
        rows = ledger.filter(
            pl.col("position_id").cast(pl.Utf8) == str(position[position_id])
        )
        filled = rows.filter(pl.col("state") == "FILLED")
        closed = rows.filter(pl.col("state") == "CLOSED")
        if closed.height:
            if filled.height != 1 or closed.height != 1:
                return False
            if not np.isclose(float(filled["price"][0]), float(position[open_column])):
                return False
            if not np.isclose(float(closed["price"][0]), float(position[close_column])):
                return False
            if "outcome_bps" in closed.columns:
                side = float(closed["side"][0]) if "side" in closed.columns else 1.0
                expected = side * (
                    float(position[close_column]) / float(position[open_column]) - 1.0
                ) * 1e4
                if not np.isclose(float(closed["outcome_bps"][0]), expected):
                    return False
    return True


def _ledger_rows(entries):
    rows = []
    for position_id, state, price in entries:
        rows.append(
            {
                "position_id": position_id,
                "state": state,
                "price": price,
                "episode_id": position_id,
            }
        )
    return pl.DataFrame(rows)


@pytest.mark.parametrize(
    ("name", "ledger_entries", "position_rows"),
    [
        (
            "agreeing",
            [("P1", "FILLED", 100.0), ("P1", "CLOSED", 102.0)],
            [{"position_id": "P1", "avg_px_open": 100.0, "avg_px_close": 102.0}],
        ),
        (
            "open position is skipped",
            [("P1", "FILLED", 100.0)],
            [{"position_id": "P1", "avg_px_open": 100.0, "avg_px_close": None}],
        ),
        (
            "wrong close price",
            [("P1", "FILLED", 100.0), ("P1", "CLOSED", 105.0)],
            [{"position_id": "P1", "avg_px_open": 100.0, "avg_px_close": 102.0}],
        ),
        (
            "missing filled row",
            [("P1", "CLOSED", 102.0)],
            [{"position_id": "P1", "avg_px_open": 100.0, "avg_px_close": 102.0}],
        ),
        (
            "two closed rows",
            [("P1", "FILLED", 100.0), ("P1", "CLOSED", 102.0), ("P1", "CLOSED", 103.0)],
            [{"position_id": "P1", "avg_px_open": 100.0, "avg_px_close": 102.0}],
        ),
        (
            "many positions, one wrong",
            [
                ("P1", "FILLED", 100.0), ("P1", "CLOSED", 102.0),
                ("P2", "FILLED", 50.0), ("P2", "CLOSED", 49.0),
                ("P3", "FILLED", 10.0), ("P3", "CLOSED", 11.0),
            ],
            [
                {"position_id": "P1", "avg_px_open": 100.0, "avg_px_close": 102.0},
                {"position_id": "P2", "avg_px_open": 50.0, "avg_px_close": 49.5},
                {"position_id": "P3", "avg_px_open": 10.0, "avg_px_close": 11.0},
            ],
        ),
    ],
)
def test_vectorised_ledger_agreement_matches_the_row_wise_reference(
    name, ledger_entries, position_rows
):
    from xen.adaptive_management.integrity import _ledger_agrees_with_positions

    ledger = _ledger_rows(ledger_entries)
    positions = pl.DataFrame(position_rows)
    assert _ledger_agrees_with_positions(ledger, positions) == _reference_ledger_agrees(
        ledger, positions
    ), name
