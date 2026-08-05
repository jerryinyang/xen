from __future__ import annotations

import json
import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

import polars as pl
import pytest

from xen.adaptive_management.contracts import (
    build_management_lattice,
    build_native_lattice,
)

ROOT = Path(__file__).resolve().parents[1]


def _origins() -> pl.DataFrame:
    start = datetime(2023, 1, 1, tzinfo=timezone.utc)
    return pl.DataFrame(
        {
            "origin_id": ["O1", "O2", "O3"],
            "symbol": ["SYN"] * 3,
            "decision_ts": [start + timedelta(hours=i) for i in range(3)],
            "entry_variant": ["BREAKOUT"] * 3,
        }
    ).with_columns(pl.col("decision_ts").cast(pl.Datetime("ns", "UTC")))


def _native_episodes() -> pl.DataFrame:
    rows = []
    states = {
        "FIXED_NATIVE_BREAKOUT": ["FILLED", "NO_EVENT", "FILLED"],
        "NAT_BREAKOUT_RANGE_SCALE_BREAKOUT_THRESHOLD_DIRECT": [
            "FILLED",
            "FILLED",
            "NO_EVENT",
        ],
        "NAT_BREAKOUT_RANGE_SCALE_BREAKOUT_THRESHOLD_REVERSE": [
            "NO_EVENT",
            "NO_EVENT",
            "FILLED",
        ],
    }
    metadata = {
        "FIXED_NATIVE_BREAKOUT": ("FIXED_NATIVE", "FIXED", None),
        "NAT_BREAKOUT_RANGE_SCALE_BREAKOUT_THRESHOLD_DIRECT": (
            "NATIVE",
            "DIRECT",
            None,
        ),
        "NAT_BREAKOUT_RANGE_SCALE_BREAKOUT_THRESHOLD_REVERSE": (
            "NATIVE",
            "REVERSE",
            None,
        ),
    }
    for arm_id, arm_states in states.items():
        arm_class, orientation, orientation_pair = metadata[arm_id]
        for origin_id, state in zip(["O1", "O2", "O3"], arm_states, strict=True):
            rows.append(
                {
                    "origin_id": origin_id,
                    "symbol": "SYN",
                    "entry_variant": "BREAKOUT",
                    "arm_id": arm_id,
                    "arm_class": arm_class,
                    "component": "RANGE_SCALE" if arm_class != "FIXED_NATIVE" else None,
                    "parameter": "BREAKOUT_THRESHOLD",
                    "orientation": orientation,
                    "orientation_pair": orientation_pair,
                    "comparator_id": "FIXED_NATIVE_BREAKOUT",
                    "state": state,
                    "event_ts": datetime(2023, 1, 2, tzinfo=timezone.utc)
                    if state != "NO_EVENT"
                    else None,
                    "entry_ts": datetime(2023, 1, 2, 1, tzinfo=timezone.utc)
                    if state == "FILLED"
                    else None,
                    "outcome_bps": 4.0 if state == "FILLED" else 0.0,
                }
            )
    for pair in (
        "DIRECT_DIRECT",
        "DIRECT_REVERSE",
        "REVERSE_DIRECT",
        "REVERSE_REVERSE",
    ):
        for origin_id in ("O1", "O2", "O3"):
            rows.append(
                {
                    "origin_id": origin_id,
                    "symbol": "SYN",
                    "entry_variant": "BREAKOUT",
                    "arm_id": f"NATCOMB_{pair}",
                    "arm_class": "NATIVE_COMBINATION",
                    "component": "RANGE_SCALE",
                    "parameter": "BREAKOUT_THRESHOLD+PENDING_EXPIRY",
                    "orientation": None,
                    "orientation_pair": pair,
                    "comparator_id": "FIXED_NATIVE_BREAKOUT",
                    "state": "NO_EVENT",
                    "event_ts": None,
                    "entry_ts": None,
                    "outcome_bps": 0.0,
                }
            )
    return pl.from_dicts(rows, infer_schema_length=None)


def _paired_results() -> pl.DataFrame:
    rows = []
    for episode_id, fixed, adaptive in (("E1", 2.0, 5.0), ("E2", -3.0, -1.0)):
        timestamp = 1 if episode_id == "E1" else 2
        common = {
            "experiment_id": "SPDR-021",
            "universe": "crypto",
            "symbol": "SYN",
            "entry_variant": "BREAKOUT",
            "episode_id": episode_id,
            "component": "RANGE_SCALE",
            "device": "TARGET",
            "setting": "M1.00",
            "state": "ALL",
            "_entry_ns": timestamp,
            "_exit_ns": timestamp + 10,
        }
        rows.extend(
            [
                {
                    **common,
                    "arm_id": "FIXED_TARGET_M1.00",
                    "arm_class": "FIXED_MANAGEMENT",
                    "comparator_id": "FIXED_TARGET_M1.00",
                    "outcome_bps": fixed,
                },
                {
                    **common,
                    "arm_id": "POL_RANGE_TARGET_M1.00",
                    "arm_class": "MANAGEMENT",
                    "comparator_id": "FIXED_TARGET_M1.00",
                    "outcome_bps": adaptive,
                },
            ]
        )
    return pl.DataFrame(rows)


def test_target_metrics_are_device_native():
    from xen.adaptive_management.analysis import target_metrics

    metrics = target_metrics(
        pl.DataFrame(
            {
                "target_reached": [True, False],
                "realised_capture_bps": [8.0, -2.0],
                "missed_excess_bps": [1.0, 5.0],
                "time_to_target": [2.0, None],
            }
        )
    )
    assert {
        "reach_rate",
        "realised_capture_bps",
        "missed_excess_bps",
        "time_to_target",
    }.issubset(metrics)


def test_size_metrics_never_claim_expectancy_improvement():
    from xen.adaptive_management.analysis import size_metrics

    metrics = size_metrics(
        pl.DataFrame(
            {
                "outcome_bps": [10.0, -5.0, 2.0],
                "risk_size": [0.5, 2.0, 1.0],
            }
        )
    )
    assert {
        "risk_dispersion",
        "drawdown_bps",
        "tail_loss_bps",
        "concentration",
    }.issubset(metrics)
    assert "expectancy_improvement" not in metrics


def _kernel_reference_frame() -> pl.DataFrame:
    """A device population carrying nulls, NaNs, all-false flags and negative sizes."""
    return pl.DataFrame(
        {
            "target_reached": [True, False, None, True, False],
            "stop_reached": [False, True, True, None, False],
            "realised_capture_bps": [8.0, -2.0, None, float("nan"), 3.5],
            "missed_excess_bps": [1.0, 5.0, 2.0, None, 0.0],
            "time_to_target": [2.0, None, None, 1.5, float("nan")],
            "adverse_excursion_bps": [4.0, 9.0, None, 2.0, 1.0],
            "outcome_bps": [10.0, -5.0, 2.0, None, -1.5],
            "recovery_after_stop_bps": [None, 3.0, 7.0, 1.0, None],
            "peak_giveback_bps": [0.5, 4.0, None, 2.0, float("nan")],
            "favourable_excursion_captured": [0.9, None, 0.2, 0.4, 1.0],
            "decay_bps": [1.0, 2.0, None, 4.0, 5.0],
            "holding_efficiency": [0.8, 0.1, None, 0.5, 0.3],
            "opportunity_duration": [0.25, 1.0, 2.0, None, 0.75],
            "risk_size": [0.5, 2.0, 1.0, None, 1.5],
        }
    )


@pytest.mark.parametrize("device", ["TARGET", "STOP", "TRAIL", "HOLD", "SIZE"])
@pytest.mark.parametrize(
    "rows",
    [
        [0, 1, 2, 3, 4],
        [4, 3, 2, 1, 0],
        [0, 0, 1, 1, 4, 4],
        [2],
        [],
    ],
)
def test_metric_kernels_reproduce_the_polars_metric_functions(device, rows):
    """The bootstrap kernels must equal the reference metric functions row-for-row."""
    import numpy as np

    from xen.adaptive_management import analysis as module

    frame = _kernel_reference_frame()
    columns = module._DEVICE_METRIC_COLUMNS[device]
    reference = {
        "TARGET": module.target_metrics,
        "STOP": module.stop_metrics,
        "TRAIL": module.trail_metrics,
        "HOLD": module.hold_metrics,
        "SIZE": module.size_metrics,
    }[device]
    kernel = module._METRIC_KERNELS[device]

    gathered = frame[rows] if rows else frame.head(0)
    expected = reference(gathered)
    observed = kernel(
        module._metric_arrays(frame, columns),
        np.asarray(rows, dtype=np.int64),
    )

    assert set(observed) == set(expected)
    for name, value in expected.items():
        other = observed[name]
        if value is None or (isinstance(value, float) and np.isnan(value)):
            assert other is None or np.isnan(other), name
        else:
            assert other == value, name


def test_block_summary_kernel_matches_the_row_reference_exactly():
    import numpy as np

    from xen.adaptive_management.analysis import _block_interval, _clustered_interval

    start = datetime(2023, 1, 1, tzinfo=timezone.utc)
    frame = pl.DataFrame(
        {
            "decision_ts": [
                start,
                start + timedelta(hours=1),
                start + timedelta(days=1),
                start + timedelta(days=2),
                start + timedelta(days=2, hours=1),
            ],
            "value": [1.0, 2.0, None, 4.0, 5.0],
        }
    )
    expected = _clustered_interval(frame, "value", block_bars=24, n_boot=100)
    observed = _block_interval(frame, "value", block_bars=24, n_boot=100)
    assert set(observed) == set(expected)
    for key, value in expected.items():
        if isinstance(value, float) and np.isnan(value):
            assert np.isnan(observed[key])
        else:
            assert observed[key] == value


def test_batched_clustered_intervals_match_independent_draws_exactly():
    import numpy as np

    from xen.adaptive_management.analysis import (
        _clustered_interval,
        _clustered_intervals,
    )

    start = datetime(2023, 1, 1, tzinfo=timezone.utc)
    frame = pl.DataFrame(
        {
            "decision_ts": [
                start,
                start + timedelta(hours=1),
                start + timedelta(days=1),
                start + timedelta(days=2),
                start + timedelta(days=2, hours=1),
            ],
            "all_delta": [1.0, -2.0, float("nan"), 4.0, 5.0],
            "selected_delta": [1.0, 0.0, 0.0, 4.0, 0.0],
            "excluded_delta": [0.0, -2.0, float("nan"), 0.0, 5.0],
        }
    )
    columns = ("all_delta", "selected_delta", "excluded_delta")
    expected = {
        column: _clustered_interval(
            frame,
            column,
            block_bars=24,
            n_boot=100,
        )
        for column in columns
    }
    observed = _clustered_intervals(
        frame,
        columns,
        block_bars=24,
        n_boot=100,
    )

    assert observed.keys() == expected.keys()
    for column in columns:
        for key, value in expected[column].items():
            other = observed[column][key]
            if isinstance(value, float) and np.isnan(value):
                assert np.isnan(other), (column, key)
            else:
                assert other == value, (column, key)


def test_native_states_share_one_bootstrap_pass_per_arm(monkeypatch):
    from xen.adaptive_management import analysis as module

    calls: list[tuple[str, ...]] = []
    original = module._clustered_intervals

    def tracked(frame, value_columns, *, block_bars, n_boot):
        calls.append(tuple(value_columns))
        return original(
            frame,
            value_columns,
            block_bars=block_bars,
            n_boot=n_boot,
        )

    monkeypatch.setattr(module, "_clustered_intervals", tracked)
    module.origin_estimates(_origins(), _native_episodes(), block_bars=24, n_boot=20)

    assert len(calls) == _native_episodes()["arm_id"].n_unique()
    assert all(len(columns) >= 2 for columns in calls)


def test_ledger_origin_filter_preserves_exact_membership_and_order():
    from xen.adaptive_management.analysis import _ledger_origin_filter

    origin_ids = pl.Series("origin_id", ["BTC-01", "BTC-ff"])
    frame = pl.DataFrame(
        {
            "origin_id": ["AAA-ff", "BTC-01", "BTC-80", "BTC-ff", "ZZZ-00", None],
            "row": [0, 1, 2, 3, 4, 5],
        }
    )
    expected = frame.filter(pl.col("origin_id").is_in(origin_ids.implode()))
    observed = frame.filter(_ledger_origin_filter(origin_ids))

    assert observed.equals(expected)
    assert observed["row"].to_list() == [1, 3]


def test_every_adaptive_row_has_a_paired_fixed_device_delta():
    from xen.adaptive_management.analysis import paired_estimates

    table = paired_estimates(_paired_results(), block_bars=24, n_boot=100)
    assert table["paired_n"].min() > 0
    assert table["comparator_id"].str.starts_with("FIXED_").all()
    assert table["estimate"].to_list() == [2.5]
    assert {"ci_low", "ci_high", "effective_n", "mde"}.issubset(table.columns)
    assert table["common_fill_n"].to_list() == [2]
    assert table["common_close_n"].to_list() == [2]
    assert table["effective_trade_blocks"].to_list() == table["effective_n"].to_list()
    assert table["eligible_origin_n"].null_count() == table.height


def test_scheduled_nonfills_do_not_inflate_trade_level_counts():
    from xen.adaptive_management.analysis import paired_estimates

    rows = _paired_results()
    unfilled = rows.filter(pl.col("episode_id") == "E1").with_columns(
        pl.lit("E3").alias("episode_id"),
        pl.lit(None, dtype=pl.Int64).alias("_entry_ns"),
        pl.lit(None, dtype=pl.Int64).alias("_exit_ns"),
    )
    table = paired_estimates(
        pl.concat([rows, unfilled]), block_bars=24, n_boot=20
    )
    assert table["entry_fill_n"].to_list() == [2]
    assert table["close_n"].to_list() == [2]
    assert table["common_fill_n"].to_list() == [2]
    assert table["common_close_n"].to_list() == [2]


def test_device_tables_exclude_ineligible_policy_rows():
    from xen.adaptive_management.analysis import _device_table

    paired = _paired_results().with_columns(
        pl.lit(True).alias("eligible"),
        pl.lit(False).alias("target_reached"),
        pl.col("outcome_bps").alias("realised_capture_bps"),
        pl.lit(None, dtype=pl.Float64).alias("missed_excess_bps"),
        pl.lit(None, dtype=pl.Float64).alias("time_to_target"),
    )
    ineligible = paired.filter(pl.col("arm_id") != pl.col("comparator_id")).head(1).with_columns(
        pl.lit("E3").alias("episode_id"),
        pl.lit("NO_FEATURE").alias("state"),
        pl.lit(False).alias("eligible"),
        pl.lit(None, dtype=pl.Int64).alias("_entry_ns"),
        pl.lit(None, dtype=pl.Int64).alias("_exit_ns"),
    )

    table = _device_table(
        pl.concat([paired, ineligible]), "TARGET", block_bars=24, n_boot=20
    )

    assert set(table["state"]) == {"ALL"}
    assert table["common_close_n"].unique().to_list() == [2]


def test_native_analysis_retains_no_event_and_unfilled_origins():
    from xen.adaptive_management.analysis import origin_estimates

    table = origin_estimates(_origins(), _native_episodes(), block_bars=24, n_boot=100)
    all_rows = table.filter(pl.col("state") == "ALL")
    assert all_rows["eligible_origins"].unique().to_list() == [3]
    assert all_rows["eligible_origin_n"].unique().to_list() == [3]
    assert all_rows["event_count"].unique().to_list() == [3]
    assert all_rows["estimate_source"].unique().to_list() == [
        "COMMON_ORIGIN_OCCUPANCY_INCLUSIVE"
    ]
    assert all_rows["common_fill_n"].null_count() == all_rows.height
    assert all_rows["effective_origin_blocks"].to_list() == all_rows[
        "effective_n"
    ].to_list()
    assert {
        "signal_rate",
        "event_rate",
        "fill_rate",
        "exposure_per_origin",
    }.issubset(table.columns)


def test_native_analysis_emits_both_orientations_and_all_four_pairs():
    from xen.adaptive_management.analysis import origin_estimates

    rows = origin_estimates(_origins(), _native_episodes(), block_bars=24, n_boot=100)
    all_rows = rows.filter(pl.col("state") == "ALL")
    assert set(all_rows["orientation"].drop_nulls()) >= {"FIXED", "DIRECT", "REVERSE"}
    assert set(
        all_rows.filter(pl.col("arm_class") == "NATIVE_COMBINATION")[
            "orientation_pair"
        ]
    ) == {
        "DIRECT_DIRECT",
        "DIRECT_REVERSE",
        "REVERSE_DIRECT",
        "REVERSE_REVERSE",
    }


def _shared_fill_fixture(
    *,
    entry_variant: str,
    planned_entry,
    adaptive_entry_ns: int | None,
    fixed_entry_ns: int | None,
    adaptive_exit_ns: int | None = 20,
    fixed_exit_ns: int | None = 21,
) -> pl.DataFrame:
    common = {
        "experiment_id": "SPDR-021" if entry_variant == "BREAKOUT" else "SPDR-022",
        "universe": "crypto",
        "symbol": "SYN",
        "entry_variant": entry_variant,
        "origin_id": "O1",
        "decision_ts": datetime(2023, 1, 1, tzinfo=timezone.utc),
        "entry_ts": planned_entry,
        "comparator_id": "FIXED_NATIVE",
    }
    return pl.from_dicts(
        [
            {
                **common,
                "arm_id": "FIXED_NATIVE",
                "arm_class": "FIXED_NATIVE",
                "outcome_bps": 2.0,
                "_entry_ns": fixed_entry_ns,
                "_exit_ns": fixed_exit_ns,
            },
            {
                **common,
                "arm_id": "ADAPTIVE_NATIVE",
                "arm_class": "NATIVE",
                "outcome_bps": 5.0,
                "_entry_ns": adaptive_entry_ns,
                "_exit_ns": adaptive_exit_ns,
            },
        ],
        infer_schema_length=None,
    )


def test_shared_fill_uses_actual_breakout_fills_not_planned_entry_time():
    from xen.adaptive_management.analysis import _shared_trade_diagnostics

    shared = _shared_trade_diagnostics(
        _shared_fill_fixture(
            entry_variant="BREAKOUT",
            planned_entry=None,
            adaptive_entry_ns=10,
            fixed_entry_ns=11,
        )
    )
    assert shared.height == 1
    assert shared["paired_outcome_delta_bps"].to_list() == [3.0]


@pytest.mark.parametrize(
    ("adaptive_entry_ns", "fixed_entry_ns"),
    [(None, 11), (10, None), (None, None)],
)
def test_shared_fill_excludes_scheduled_breach_nonfills(
    adaptive_entry_ns, fixed_entry_ns
):
    from xen.adaptive_management.analysis import _shared_trade_diagnostics

    shared = _shared_trade_diagnostics(
        _shared_fill_fixture(
            entry_variant="E_TOUCH",
            planned_entry=datetime(2023, 1, 1, 1, tzinfo=timezone.utc),
            adaptive_entry_ns=adaptive_entry_ns,
            fixed_entry_ns=fixed_entry_ns,
        )
    )
    assert shared.is_empty()


def test_shared_fill_requires_actual_closes_for_the_outcome_lens():
    from xen.adaptive_management.analysis import _shared_trade_diagnostics

    shared = _shared_trade_diagnostics(
        _shared_fill_fixture(
            entry_variant="BREAKOUT",
            planned_entry=None,
            adaptive_entry_ns=10,
            fixed_entry_ns=11,
            adaptive_exit_ns=None,
        )
    )
    assert shared.is_empty()


def test_shared_fill_rejects_duplicate_declared_origin_identity():
    from xen.adaptive_management.analysis import _shared_trade_diagnostics

    frame = _shared_fill_fixture(
        entry_variant="BREAKOUT",
        planned_entry=None,
        adaptive_entry_ns=10,
        fixed_entry_ns=11,
    )
    duplicate = pl.concat(
        [frame, frame.filter(pl.col("arm_class") == "FIXED_NATIVE")]
    )
    with pytest.raises(ValueError, match="duplicate fixed.*origin identity"):
        _shared_trade_diagnostics(duplicate)


def test_breach_origins_are_retained_for_both_entry_variants():
    from xen.adaptive_management.analysis import origin_estimates

    origins = _origins().drop("entry_variant").head(2)
    rows = []
    for variant in ("E_TOUCH", "E_CLOSE"):
        for origin_id in ("O1", "O2"):
            rows.append(
                {
                    "origin_id": origin_id,
                    "symbol": "SYN",
                    "entry_variant": variant,
                    "arm_id": f"FIXED_NATIVE_BAND_{variant}",
                    "arm_class": "FIXED_NATIVE",
                    "component": None,
                    "parameter": None,
                    "orientation": "FIXED",
                    "orientation_pair": None,
                    "comparator_id": f"FIXED_NATIVE_BAND_{variant}",
                    "state": "NO_EVENT",
                    "event_ts": None,
                    "entry_ts": None,
                    "outcome_bps": 0.0,
                }
            )
    estimates = origin_estimates(
        origins, pl.from_dicts(rows), block_bars=24, n_boot=20
    ).filter(pl.col("state") == "ALL")
    assert set(estimates["entry_variant"]) == {"E_TOUCH", "E_CLOSE"}
    assert estimates["eligible_origins"].to_list() == [2, 2]


def test_full_reporting_rejects_missing_arms_and_native_management_cross():
    from xen.adaptive_management.analysis import validate_full_reporting

    native = pl.DataFrame(
        {
            "origin_id": ["O1"],
            "entry_variant": ["BREAKOUT"],
            "arm_id": ["FIXED_NATIVE_BREAKOUT"],
            "native_arm_id": ["FIXED_NATIVE_BREAKOUT"],
            "policy_id": ["NONE"],
        }
    )
    policies = pl.DataFrame(
        {
            "origin_id": ["O1"],
            "entry_variant": ["BREAKOUT"],
            "arm_id": ["CROSS"],
            "native_arm_id": ["NATIVE"],
            "policy_id": ["POLICY"],
        }
    )
    with pytest.raises(ValueError, match="native.*management"):
        validate_full_reporting("SPDR-021", _origins().head(1), native, policies)

    policies = policies.with_columns(pl.lit(None, dtype=pl.Utf8).alias("native_arm_id"))
    with pytest.raises(ValueError, match="missing native arms"):
        validate_full_reporting("SPDR-021", _origins().head(1), native, policies)


def _complete_schedules() -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    start = datetime(2023, 1, 1, tzinfo=timezone.utc)
    origin = pl.DataFrame(
        {
            "origin_id": ["O1", "O2", "O3", "O4"],
            "symbol": ["SYN"] * 4,
            "decision_ts": [start + timedelta(days=i) for i in range(4)],
            "entry_variant": ["BREAKOUT"] * 4,
        }
    ).with_columns(pl.col("decision_ts").cast(pl.Datetime("ns", "UTC")))
    origin_states = {
        "O1": "FILLED",
        "O2": "NO_EVENT",
        "O3": "EXPIRED",
        "O4": "BLOCKED_ACTIVE",
    }
    native_rows = []
    for arm in build_native_lattice("SPDR-021"):
        for origin_row in origin.iter_rows(named=True):
            origin_id = origin_row["origin_id"]
            state = origin_states[origin_id]
            native_rows.append(
                {
                    "origin_id": origin_id,
                    "symbol": "SYN",
                    "experiment_id": "SPDR-021",
                    "entry_variant": "BREAKOUT",
                    "arm_id": arm.native_arm_id,
                    "native_arm_id": arm.native_arm_id,
                    "policy_id": "NONE",
                    "arm_class": "FIXED_NATIVE"
                    if not arm.is_adaptive
                    else "NATIVE_COMBINATION"
                    if arm.combination_id
                    else "NATIVE",
                    "component": str(arm.component) if arm.component else None,
                    "parameter": str(arm.parameter) if arm.parameter else None,
                    "orientation": str(arm.orientation) if arm.orientation else "FIXED",
                    "orientation_pair": "_".join(map(str, arm.orientation_pair))
                    if arm.orientation_pair
                    else None,
                    "comparator_id": arm.comparator_id,
                    "episode_id": f"N-{origin_id}-{arm.native_arm_id}",
                    "decision_ts": origin_row["decision_ts"],
                    "state": state,
                    "event_ts": origin_row["decision_ts"]
                    if state in {"FILLED", "EXPIRED"}
                    else None,
                    "entry_ts": origin_row["decision_ts"] + timedelta(minutes=1)
                    if state == "FILLED"
                    else None,
                    "risk_size": 1.0,
                    "side": 1,
                    "device": "NONE",
                }
            )
    policy_rows = []
    seen_device_combinations = set()
    for policy in build_management_lattice("SPDR-021"):
        if policy.combination_id and policy.combination_id.startswith("DC_"):
            if policy.combination_id in seen_device_combinations:
                continue
            seen_device_combinations.add(policy.combination_id)
            policy_id = policy.combination_id
            device = policy.combination_id.removeprefix("DC_").replace("_", "+")
        else:
            policy_id = policy.policy_id
            device = str(policy.device)
        for origin_row in origin.iter_rows(named=True):
            origin_id = origin_row["origin_id"]
            policy_rows.append(
                {
                    "origin_id": origin_id,
                    "symbol": "SYN",
                    "experiment_id": "SPDR-021",
                    "entry_variant": "BREAKOUT",
                    "arm_id": policy_id,
                    "native_arm_id": None,
                    "policy_id": policy_id,
                    "arm_class": "FIXED_MANAGEMENT"
                    if not policy.is_adaptive
                    else "MANAGEMENT_DEVICE_COMBINATION"
                    if policy.combination_id
                    and policy.combination_id.startswith("DC_")
                    else "MANAGEMENT_COMPONENT_COMBINATION"
                    if policy.combination_id
                    else "MANAGEMENT",
                    "component": str(policy.component) if policy.component else None,
                    "setting": policy.setting,
                    "comparator_id": policy.comparator_id,
                    "episode_id": f"P-{origin_id}",
                    "decision_ts": origin_row["decision_ts"],
                    "state": "ORDER_CREATED"
                    if origin_id in {"O1", "O2"}
                    else origin_states[origin_id],
                    "event_ts": origin_row["decision_ts"]
                    if origin_id in {"O1", "O2"}
                    else None,
                    "entry_ts": origin_row["decision_ts"] + timedelta(minutes=1)
                    if origin_id in {"O1", "O2"}
                    else None,
                    "risk_size": 0.5 if str(policy.device) == "SIZE" else 1.0,
                    "side": 1,
                    "hold_bars": 4,
                    "device": device,
                }
            )
    return origin, pl.from_dicts(native_rows), pl.from_dicts(policy_rows)


def test_full_reporting_rejects_missing_fixed_comparator():
    from xen.adaptive_management.analysis import validate_full_reporting

    origins, native, policies = _complete_schedules()
    adaptive_arm = policies.filter(
        pl.col("arm_id") != pl.col("comparator_id")
    )["arm_id"][0]
    policies = policies.with_columns(
        pl.when(pl.col("arm_id") == adaptive_arm)
        .then(pl.lit("FIXED_MISSING"))
        .otherwise(pl.col("comparator_id"))
        .alias("comparator_id")
    )

    with pytest.raises(ValueError, match="missing fixed comparator"):
        validate_full_reporting("SPDR-021", origins, native, policies)


def test_full_reporting_rejects_dropped_or_unexpected_management_rows():
    from xen.adaptive_management.analysis import validate_full_reporting

    origins, native, policies = _complete_schedules()
    dropped = policies.slice(1)
    with pytest.raises(ValueError, match="dropped origins in management arm"):
        validate_full_reporting("SPDR-021", origins, native, dropped)

    unexpected = pl.concat(
        [
            policies,
            policies.head(1).with_columns(
                pl.lit("UNDECLARED").alias("arm_id"),
                pl.lit("UNDECLARED").alias("policy_id"),
                pl.lit("UNDECLARED").alias("comparator_id"),
            ),
        ]
    )
    with pytest.raises(ValueError, match="unexpected management arms"):
        validate_full_reporting("SPDR-021", origins, native, unexpected)


def _write_complete_run(run_dir: Path) -> None:
    origins, native, policies = _complete_schedules()
    run_dir.mkdir()
    origins.write_parquet(run_dir / "origins.parquet")
    native.write_parquet(run_dir / "native_parameter_schedule.parquet")
    policies.write_parquet(run_dir / "policy_schedule.parquet")
    origins.select("symbol", pl.col("decision_ts").alias("ts")).with_columns(
        pl.Series("magnitude_bps", [10.0, 20.0, 30.0, 40.0])
    ).write_parquet(run_dir / "features.parquet")
    ledger_rows = []
    for row in pl.concat([native, policies], how="diagonal_relaxed").iter_rows(named=True):
        if row["origin_id"] not in {"O1", "O2"} or row["entry_ts"] is None:
            continue
        entry_ns = int(row["entry_ts"].timestamp() * 1e9)
        device = str(row["device"])
        exit_reason = (
            "TARGET"
            if "TARGET" in device
            else "STOP"
            if "STOP" in device
            else "TRAIL"
            if "TRAIL" in device
            else "HOLD"
        )
        exit_price = 102.0 if exit_reason == "TARGET" else 99.0
        common = {
            "episode_id": row["episode_id"],
            "origin_id": row["origin_id"],
            "arm_id": row["arm_id"],
            "arm_class": row["arm_class"],
            "experiment_id": "SPDR-021",
            "native_arm_id": row["native_arm_id"],
            "policy_id": row["policy_id"],
            "device": device,
            "entry_variant": "BREAKOUT",
        }
        ledger_rows.extend(
            [
                {
                    **common,
                    "state": "FILLED",
                    "ts_ns": entry_ns,
                    "price": 100.0,
                    "exit_reason": None,
                },
                {
                    **common,
                    "state": "CLOSED",
                    "ts_ns": entry_ns + 120_000_000_000,
                    "price": exit_price,
                    "exit_reason": exit_reason,
                },
            ]
        )
    pl.from_dicts(ledger_rows, infer_schema_length=None).write_parquet(
        run_dir / "episode_results.parquet"
    )
    cells = run_dir / "cells" / "SYN"
    cells.mkdir(parents=True)
    bars = []
    for decision_ts in origins["decision_ts"]:
        for minute, (high, low, close) in enumerate(
            (
                (101.0, 99.0, 100.5),
                (103.0, 98.0, 102.0),
                (104.0, 97.0, 103.0),
                (105.0, 98.0, 104.0),
                (106.0, 99.0, 105.0),
            ),
            start=1,
        ):
            bars.append(
                {
                    "SourceCloseTime": decision_ts + timedelta(minutes=minute),
                    "RealOpen": 100.0,
                    "RealHigh": high,
                    "RealLow": low,
                    "RealClose": close,
                }
            )
    pl.from_dicts(bars).write_parquet(cells / "bar_marks.parquet")
    (run_dir / "config.json").write_text(
        json.dumps(
            {
                "experiment_id": "SPDR-021",
                "universe": "crypto",
                "band": "TRAIN",
                "spread_cost_status": "UNAVAILABLE_NOT_CHARGED",
                "spread_rt_bps": None,
                "cost_scope": "PARTIAL_FEES_FUNDING_ONLY",
            }
        )
    )


def test_analyse_run_accepts_a_breach_origin_ledger_without_entry_variant(tmp_path):
    """SPDR-022/023 zone origins are common to both entry variants and carry no
    `entry_variant` column; the schedule supplies it. Analysis must not require it."""
    from xen.adaptive_management.analysis import ANALYSIS_ARTIFACTS, analyse_run

    run_dir = tmp_path / "run"
    _write_complete_run(run_dir)
    breach_origins = pl.read_parquet(run_dir / "origins.parquet").drop("entry_variant")
    assert "entry_variant" not in breach_origins.columns
    breach_origins.write_parquet(run_dir / "origins.parquet")

    output_dir = tmp_path / "analysis"
    analyse_run(run_dir, output_dir, n_boot=20)
    assert set(ANALYSIS_ARTIFACTS).issubset(
        {path.name for path in output_dir.iterdir()}
    )


def test_analyse_run_writes_every_declared_table_without_verdicts(tmp_path):
    from xen.adaptive_management.analysis import ANALYSIS_ARTIFACTS, analyse_run

    run_dir = tmp_path / "run"
    output_dir = tmp_path / "analysis"
    _write_complete_run(run_dir)
    schedule = pl.concat(
        [
            pl.read_parquet(run_dir / "native_parameter_schedule.parquet"),
            pl.read_parquet(run_dir / "policy_schedule.parquet"),
        ],
        how="diagonal_relaxed",
    )
    assert {
        "FIXED_NATIVE",
        "NATIVE",
        "NATIVE_COMBINATION",
        "FIXED_MANAGEMENT",
        "MANAGEMENT",
        "MANAGEMENT_COMPONENT_COMBINATION",
        "MANAGEMENT_DEVICE_COMBINATION",
    }.issubset(set(schedule["arm_class"]))
    assert {"FILLED", "NO_EVENT", "EXPIRED", "BLOCKED_ACTIVE"}.issubset(
        set(schedule["state"])
    )

    analyse_run(run_dir, output_dir, n_boot=50)
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        analyse_run(run_dir, output_dir, n_boot=1)

    assert set(ANALYSIS_ARTIFACTS).issubset(
        {path.name for path in output_dir.iterdir()}
    )
    for path in output_dir.glob("*.parquet"):
        assert not {"verdict", "supported", "winner", "pass"}.intersection(
            pl.read_parquet(path).columns
        )
    target = pl.read_parquet(output_dir / "device_target.parquet")
    assert {
        "metric_name",
        "comparator_id",
        "estimate",
        "ci_low",
        "ci_high",
        "effective_n",
        "mde",
    }.issubset(target.columns)
    population_columns = {
        "eligible_origin_n",
        "entry_fill_n",
        "close_n",
        "common_fill_n",
        "common_close_n",
        "effective_origin_blocks",
        "effective_trade_blocks",
    }
    assert population_columns.issubset(target.columns)
    device_metrics = {
        name: set(
            pl.read_parquet(output_dir / f"device_{name}.parquet")["metric_name"]
        )
        for name in ("target", "stop", "trail", "hold", "size")
    }
    assert device_metrics["target"] >= {
        "reach_rate",
        "realised_capture_bps",
        "missed_excess_bps",
        "time_to_target",
    }
    assert device_metrics["stop"] >= {
        "adverse_excursion_bps",
        "stop_rate",
        "loss_severity_bps",
        "recovery_after_stop_bps",
    }
    assert device_metrics["trail"] >= {
        "peak_giveback_bps",
        "favourable_excursion_captured",
        "loss_tail_bps",
    }
    assert device_metrics["hold"] >= {
        "outcome_by_time_bps",
        "decay_bps",
        "holding_efficiency",
        "opportunity_duration",
    }
    assert device_metrics["size"] >= {
        "risk_dispersion",
        "drawdown_bps",
        "tail_loss_bps",
        "concentration",
    }
    assert "expectancy_improvement" not in device_metrics["size"]
    for name in ("target", "stop", "trail", "hold", "size"):
        table = pl.read_parquet(output_dir / f"device_{name}.parquet")
        assert table.group_by("metric_name").agg(
            pl.col("observed").is_finite().any().alias("has_measure")
        )["has_measure"].all()
    per_stratum = pl.read_parquet(output_dir / "per_stratum_estimates.parquet")
    assert population_columns.issubset(per_stratum.columns)
    assert "COMMON_ORIGIN_OCCUPANCY_INCLUSIVE" in set(
        per_stratum["estimate_source"]
    )
    row_key = [
        "experiment_id",
        "universe",
        "symbol",
        "entry_variant",
        "arm_id",
        "state",
        "metric_name",
        "estimate_source",
    ]
    assert not per_stratum.select(row_key).is_duplicated().any()
    assert {
        "DC_TARGET_STOP",
        "DC_TRAIL_HOLD",
        "DC_TARGET_STOP_HOLD",
    }.issubset(set(per_stratum["arm_id"]))
    assert {
        "parameter_or_device",
        "orientation_or_setting",
        "trade_count",
        "gross_mean_bps",
        "gross_median_bps",
        "gross_trimmed_mean_bps",
        "partial_cost_mean_bps",
        "win_share",
        "mean_win_bps",
        "mean_loss_bps",
        "win_loss_ratio",
        "breakeven_win_share_net",
        "edge_bps",
        "mfe_bps",
        "mae_bps",
        "exit_reason",
        "exit_reason_share",
    }.issubset(per_stratum.columns)
    assert per_stratum["trade_count"].max() > 0
    controls = pl.read_parquet(output_dir / "controls.parquet")
    assert set(controls["control"]) >= {"TIME_DERANGEMENT", "MAGNITUDE_MATCH"}
    assert set(controls["analysis_stage"]) == {"COMPUTED"}
    assert {
        "population",
        "comparator",
        "estimate",
        "ci_low",
        "ci_high",
        "count",
        "effective_count",
        "undefined_reason",
    }.issubset(controls.columns)
    informative = controls.filter(
        pl.col("control").is_in(["TIME_DERANGEMENT", "MAGNITUDE_MATCH"])
    )
    assert informative.height > 0
    assert (
        informative["estimate"].is_not_null()
        | informative["undefined_reason"].is_not_null()
    ).all()
    summary = json.loads((output_dir / "analysis_summary.json").read_text())
    assert summary["experiment_id"] == "SPDR-021"
    assert summary["interpretation"] == "DESCRIPTIVE_ONLY"
    assert set(summary["count_definitions"]) >= population_columns

    replay_dir = tmp_path / "analysis-replay"
    analyse_run(run_dir, replay_dir, n_boot=50)
    for artifact in (
        "native_parameter_selected_excluded.parquet",
        "state_sections.parquet",
        "selection_checks.parquet",
    ):
        assert (output_dir / artifact).read_bytes() == (replay_dir / artifact).read_bytes()


def test_each_analysis_wrapper_invokes_only_its_own_run(monkeypatch, tmp_path):
    from xen.adaptive_management import analysis

    seen = []
    monkeypatch.setattr(
        analysis,
        "analyse_run",
        lambda run_dir, output_dir, **kwargs: seen.append(
            (Path(run_dir), Path(output_dir))
        ),
    )
    for experiment_id in ("SPDR-021", "SPDR-022", "SPDR-023"):
        path = (
            ROOT
            / "experiments"
            / experiment_id
            / "analysis_code"
            / "analyse.py"
        )
        module_spec = importlib.util.spec_from_file_location(
            f"analyse_{experiment_id}", path
        )
        assert module_spec is not None and module_spec.loader is not None
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        run = tmp_path / experiment_id / "run"
        output = tmp_path / experiment_id / "analysis"
        run.mkdir(parents=True)
        (run / "config.json").write_text(
            json.dumps({"experiment_id": experiment_id})
        )
        module.main(["--run", str(run), "--output", str(output)])
    assert seen == [
        (tmp_path / experiment_id / "run", tmp_path / experiment_id / "analysis")
        for experiment_id in ("SPDR-021", "SPDR-022", "SPDR-023")
    ]
