"""Descriptive analysis for the SPDR-021/022/023 adaptive-management runs.

Native parameters are compared on the complete common-origin ledger. Management devices are
compared on identical filled episodes. Every declared arm is retained, including no-event and
unfilled native origins; uncertainty and MDE are informative fields, never result labels.
"""

from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
import shutil
from typing import Any
import uuid

import numpy as np
import polars as pl

from xen.adaptive_management.contracts import (
    build_management_lattice,
    build_native_lattice,
)

ANALYSIS_ARTIFACTS = (
    "per_stratum_estimates.parquet",
    "native_parameter_origins.parquet",
    "native_parameter_shared_trades.parquet",
    "native_parameter_selected_excluded.parquet",
    "device_target.parquet",
    "device_stop.parquet",
    "device_trail.parquet",
    "device_hold.parquet",
    "device_size.parquet",
    "state_sections.parquet",
    "selection_checks.parquet",
    "controls.parquet",
    "analysis_summary.json",
)

_IDENTITY_COLUMNS = (
    "experiment_id",
    "universe",
    "symbol",
    "entry_variant",
    "arm_id",
    "arm_class",
    "component",
    "device",
    "setting",
    "comparator_id",
    "state",
)
_NON_EVENT_STATES = {
    "NO_EVENT",
    "NO_FEATURE",
    "EVENT_UNDECIDED",
    "INCOMPLETE",
    "CENSORED",
    "BLOCKED_ACTIVE",
    "REJECTED",
    "DENIED",
}


def target_metrics(frame: pl.DataFrame) -> dict[str, float]:
    """Return target-native measures for one arm population."""
    return {
        "reach_rate": _rate(frame, "target_reached"),
        "realised_capture_bps": _mean(frame, "realised_capture_bps"),
        "missed_excess_bps": _mean(frame, "missed_excess_bps"),
        "time_to_target": _mean(frame, "time_to_target"),
    }


def stop_metrics(frame: pl.DataFrame) -> dict[str, float]:
    """Return protective-stop-native measures for one arm population."""
    stopped = _subset_true(frame, "stop_reached")
    return {
        "adverse_excursion_bps": _mean(frame, "adverse_excursion_bps"),
        "stop_rate": _rate(frame, "stop_reached"),
        "loss_severity_bps": _mean(stopped, "outcome_bps"),
        "recovery_after_stop_bps": _mean(stopped, "recovery_after_stop_bps"),
    }


def trail_metrics(frame: pl.DataFrame) -> dict[str, float]:
    """Return trailing-stop-native measures for one arm population."""
    outcomes = _array(frame, "outcome_bps")
    return {
        "peak_giveback_bps": _mean(frame, "peak_giveback_bps"),
        "favourable_excursion_captured": _mean(
            frame, "favourable_excursion_captured"
        ),
        "loss_tail_bps": _quantile(outcomes, 0.05),
    }


def hold_metrics(frame: pl.DataFrame) -> dict[str, float]:
    """Return holding-period-native measures for one arm population."""
    return {
        "outcome_by_time_bps": _mean(frame, "outcome_bps"),
        "decay_bps": _mean(frame, "decay_bps"),
        "holding_efficiency": _mean(frame, "holding_efficiency"),
        "opportunity_duration": _mean(frame, "opportunity_duration"),
    }


def size_metrics(frame: pl.DataFrame) -> dict[str, float]:
    """Return risk-only size measures; mean expectancy is deliberately excluded."""
    outcome = _array(frame, "outcome_bps")
    size = _array(frame, "risk_size")
    n = min(len(outcome), len(size))
    sized = outcome[:n] * size[:n] if n else np.array([], dtype=float)
    cumulative = np.cumsum(sized)
    drawdown = cumulative - np.maximum.accumulate(cumulative) if n else sized
    losses = np.abs(sized[sized < 0])
    absolute = np.abs(sized)
    concentration = (
        float(absolute.max() / absolute.sum()) if absolute.size and absolute.sum() else 0.0
    )
    return {
        "risk_dispersion": float(np.std(sized, ddof=1)) if n > 1 else 0.0 if n else np.nan,
        "drawdown_bps": float(drawdown.min()) if n else np.nan,
        "tail_loss_bps": _quantile(losses, 0.95),
        "concentration": concentration,
    }


def paired_estimates(
    results: pl.DataFrame,
    block_bars: int = 24,
    *,
    n_boot: int = 2_000,
) -> pl.DataFrame:
    """Estimate adaptive-minus-fixed-device outcomes on identical episodes."""
    if results.is_empty():
        return _empty_estimates()
    frame = _with_columns(
        results,
        {
            "experiment_id": "",
            "universe": "",
            "symbol": "",
            "entry_variant": "",
            "arm_class": "",
            "component": None,
            "device": "NONE",
            "setting": "",
            "state": "ALL",
            "outcome_bps": 0.0,
        },
    )
    adaptive = frame.filter(pl.col("arm_id") != pl.col("comparator_id"))
    fixed = frame.select(
        "experiment_id",
        "universe",
        "symbol",
        "entry_variant",
        "episode_id",
        pl.col("arm_id").alias("comparator_id"),
        pl.col("outcome_bps").alias("fixed_outcome_bps"),
    )
    join_keys = [
        "experiment_id",
        "universe",
        "symbol",
        "entry_variant",
        "episode_id",
        "comparator_id",
    ]
    paired = adaptive.join(fixed, on=join_keys, how="inner").with_columns(
        (pl.col("outcome_bps") - pl.col("fixed_outcome_bps")).alias("_delta")
    )
    if paired.is_empty():
        return _empty_estimates()
    group_columns = [column for column in _IDENTITY_COLUMNS if column in paired.columns]
    rows = []
    for key, group in paired.group_by(group_columns, maintain_order=True):
        identity = dict(zip(group_columns, _as_tuple(key), strict=True))
        stats = _clustered_interval(
            group,
            "_delta",
            block_bars=block_bars,
            n_boot=n_boot,
        )
        rows.append(
            {
                **identity,
                "metric_name": "outcome_bps",
                "estimate": stats["estimate"],
                "ci_low": stats["ci_low"],
                "ci_high": stats["ci_high"],
                "mde": stats["mde"],
                "paired_n": group.height,
                "effective_n": stats["effective_n"],
            }
        )
    return pl.from_dicts(rows, infer_schema_length=None)


def origin_estimates(
    origins: pl.DataFrame,
    episodes: pl.DataFrame,
    block_bars: int = 24,
    *,
    n_boot: int = 2_000,
) -> pl.DataFrame:
    """Describe every native arm on the complete common-origin population."""
    if origins.is_empty() or episodes.is_empty():
        return pl.DataFrame()
    origins = _origins_for_episodes(origins, episodes)
    origin_keys = ["origin_id", "symbol", "entry_variant"]
    decision = origins.select(
        *origin_keys,
        pl.col("decision_ts").alias("_origin_decision_ts"),
    )
    frame = episodes.join(decision, on=origin_keys, how="left").with_columns(
        pl.col("outcome_bps").fill_null(0.0)
        if "outcome_bps" in episodes.columns
        else pl.lit(0.0).alias("outcome_bps")
    )
    fixed = frame.filter(pl.col("arm_class") == "FIXED_NATIVE").select(
        *origin_keys,
        pl.col("outcome_bps").alias("_fixed_outcome_bps"),
    )
    frame = frame.join(fixed, on=origin_keys, how="left").with_columns(
        pl.col("_fixed_outcome_bps").fill_null(0.0),
        pl.col("_origin_decision_ts").alias("decision_ts"),
    )
    group_columns = [
        column
        for column in (
            "experiment_id",
            "universe",
            "symbol",
            "entry_variant",
            "arm_id",
            "arm_class",
            "component",
            "parameter",
            "orientation",
            "orientation_pair",
            "comparator_id",
        )
        if column in frame.columns
    ]
    rows: list[dict[str, Any]] = []
    for key, arm in frame.group_by(group_columns, maintain_order=True):
        identity = dict(zip(group_columns, _as_tuple(key), strict=True))
        if identity.get("arm_class") == "FIXED_NATIVE":
            identity["orientation"] = "FIXED"
        rows.append(_origin_row(identity, arm, "ALL", block_bars, n_boot))
        for state in arm["state"].drop_nulls().unique(maintain_order=True):
            rows.append(
                _origin_row(
                    identity,
                    arm.filter(pl.col("state") == state),
                    str(state),
                    block_bars,
                    n_boot,
                    eligible_origins=arm.height,
                )
            )
    return pl.from_dicts(rows, infer_schema_length=None)


def validate_full_reporting(
    experiment_id: str,
    origins: pl.DataFrame,
    native_schedule: pl.DataFrame,
    policy_schedule: pl.DataFrame,
) -> None:
    """Reject missing, duplicate, dropped-origin, or cross-grid analysis inputs."""
    origins = _origins_for_episodes(origins, native_schedule)
    cross = policy_schedule.filter(
        pl.col("native_arm_id").is_not_null()
        & ~pl.col("native_arm_id").cast(pl.Utf8).is_in(["", "None"])
        & pl.col("policy_id").is_not_null()
        & ~pl.col("policy_id").cast(pl.Utf8).is_in(["", "NONE", "None"])
    )
    if cross.height:
        raise ValueError("native parameter and management cross is forbidden")

    expected_native = {arm.native_arm_id for arm in build_native_lattice(experiment_id)}
    actual_native = set(native_schedule["arm_id"].cast(pl.Utf8))
    missing_native = sorted(expected_native - actual_native)
    if missing_native:
        raise ValueError(f"missing native arms: {missing_native}")
    unexpected_native = sorted(actual_native - expected_native)
    if unexpected_native:
        raise ValueError(f"unexpected native arms: {unexpected_native}")

    expected_policy = {
        arm.combination_id
        if arm.combination_id and arm.combination_id.startswith("DC_")
        else arm.policy_id
        for arm in build_management_lattice(experiment_id)
    }
    actual_policy = set(policy_schedule["policy_id"].cast(pl.Utf8))
    missing_policy = sorted(expected_policy - actual_policy)
    if missing_policy:
        raise ValueError(f"missing management arms: {missing_policy}")
    unexpected_policy = sorted(actual_policy - expected_policy)
    if unexpected_policy:
        raise ValueError(f"unexpected management arms: {unexpected_policy}")

    policy_identities = policy_schedule.select(
        "entry_variant", "arm_id", "comparator_id"
    ).unique()
    orphans = policy_identities.join(
        policy_identities.select(
            "entry_variant", pl.col("arm_id").alias("comparator_id")
        ).unique(),
        on=["entry_variant", "comparator_id"],
        how="anti",
    )
    if orphans.height:
        first = orphans.row(0, named=True)
        raise ValueError(
            "missing fixed comparator "
            f"{first['comparator_id']} for {first['arm_id']}"
        )

    for label, frame in (
        ("native", native_schedule),
        ("management", policy_schedule),
    ):
        keys = ["origin_id", "entry_variant", "arm_id"]
        if frame.select(keys).is_duplicated().any():
            raise ValueError(f"duplicate {label} reporting keys")

    expected = (
        origins.select(
            "entry_variant",
            pl.col("origin_id").cast(pl.Utf8),
        )
        .unique()
        .lazy()
    )
    expected_counts = expected.group_by("entry_variant").len().rename({"len": "_want"})
    for label, frame in (
        ("native", native_schedule),
        ("management", policy_schedule),
    ):
        # Restricted to the variants the origin ledger carries, matching the
        # per-variant loop this replaces: a variant absent from origins was never
        # checked, so it must not start failing here.
        observed = (
            frame.lazy()
            .select(
                "entry_variant",
                "arm_id",
                pl.col("origin_id").cast(pl.Utf8),
            )
            .unique()
            .join(expected.select("entry_variant").unique(), on="entry_variant")
        )
        # An arm's origin set differs from the variant's iff it holds an origin the
        # ledger lacks, or it holds fewer distinct origins than the ledger has.
        unexpected = observed.join(
            expected, on=["entry_variant", "origin_id"], how="anti"
        )
        short = (
            observed.group_by("entry_variant", "arm_id")
            .len()
            .join(expected_counts, on="entry_variant")
            .filter(pl.col("len") != pl.col("_want"))
        )
        offenders = pl.concat(
            [unexpected.select("arm_id"), short.select("arm_id")], how="vertical"
        ).collect()
        if offenders.height:
            raise ValueError(
                f"dropped origins in {label} arm {offenders.item(0, 'arm_id')}"
            )
    if not origins.height:
        raise ValueError("origin ledger is empty")


def analyse_run(
    run_dir: Path,
    output_dir: Path,
    *,
    block_bars: int = 24,
    n_boot: int = 2_000,
) -> None:
    """Analyse one completed TRAIN run and atomically publish descriptive tables."""
    run_dir = Path(run_dir)
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite analysis: {output_dir}")
    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    if config.get("band") != "TRAIN":
        raise ValueError("adaptive-management analysis accepts TRAIN runs only")
    experiment_id = str(config["experiment_id"])
    universe = str(config["universe"])
    origins = pl.read_parquet(run_dir / "origins.parquet")
    native = pl.read_parquet(run_dir / "native_parameter_schedule.parquet")
    policies = pl.read_parquet(run_dir / "policy_schedule.parquet")
    # The ledger is the largest artifact (tens of millions of rows on the breach crypto
    # cells) and is only ever consumed as the two aggregates _attach_results builds, so
    # it is read column-projected and released before the estimate stages allocate.
    ledger = pl.read_parquet(
        run_dir / "episode_results.parquet",
        columns=[
            "episode_id",
            "arm_id",
            "policy_id",
            "state",
            "ts_ns",
            "price",
            "exit_reason",
        ],
    )
    validate_full_reporting(experiment_id, origins, native, policies)

    native = _attach_native_contract(experiment_id, native)
    native_results = _attach_path_diagnostics(
        _attach_results(native, ledger, universe), run_dir
    )
    policy_results = _attach_path_diagnostics(
        _attach_results(policies, ledger, universe), run_dir
    )
    del ledger
    native_table = origin_estimates(
        origins,
        native_results,
        block_bars,
        n_boot=n_boot,
    )
    paired = paired_estimates(
        policy_results,
        block_bars,
        n_boot=n_boot,
    )
    device_tables = {
        device: _device_table(
            policy_results,
            device,
            block_bars=block_bars,
            n_boot=n_boot,
        )
        for device in ("TARGET", "STOP", "TRAIL", "HOLD", "SIZE")
    }
    selected_excluded = _selected_excluded(native_results)
    selection_checks = _selection_checks(selected_excluded)
    state_sections = _state_sections(native_results, policy_results)
    controls = _control_inventory(experiment_id, universe)
    per_stratum = pl.concat(
        [
            _tag_estimate_source(native_table, "COMMON_ORIGIN"),
            _tag_estimate_source(paired, "PAIRED_EPISODE"),
        ],
        how="diagonal_relaxed",
    )
    per_stratum = _attach_common_context(
        per_stratum,
        pl.concat([native_results, policy_results], how="diagonal_relaxed"),
        config,
    )

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    workspace = output_dir.parent / f".{output_dir.name}.tmp-{uuid.uuid4().hex}"
    workspace.mkdir()
    try:
        tables = {
            "per_stratum_estimates": per_stratum,
            "native_parameter_origins": native_table,
            "native_parameter_shared_trades": _shared_trade_diagnostics(native_results),
            "native_parameter_selected_excluded": selected_excluded,
            "device_target": device_tables["TARGET"],
            "device_stop": device_tables["STOP"],
            "device_trail": device_tables["TRAIL"],
            "device_hold": device_tables["HOLD"],
            "device_size": device_tables["SIZE"],
            "state_sections": state_sections,
            "selection_checks": selection_checks,
            "controls": controls,
        }
        for name, table in tables.items():
            _atomic_parquet(table, workspace / f"{name}.parquet")
        _atomic_json(
            {
                "experiment_id": experiment_id,
                "universe": universe,
                "band": "TRAIN",
                "interpretation": "DESCRIPTIVE_ONLY",
                "block_bars": max(24, int(block_bars)),
                "native_rows": native_table.height,
                "paired_rows": paired.height,
                "artifacts": list(ANALYSIS_ARTIFACTS),
            },
            workspace / "analysis_summary.json",
        )
        workspace.replace(output_dir)
    except BaseException:
        shutil.rmtree(workspace, ignore_errors=True)
        raise


def _origin_row(
    identity: dict[str, Any],
    frame: pl.DataFrame,
    state: str,
    block_bars: int,
    n_boot: int,
    *,
    eligible_origins: int | None = None,
) -> dict[str, Any]:
    event = (
        frame["event_ts"].is_not_null().sum()
        if "event_ts" in frame.columns
        else (~frame["state"].is_in(_NON_EVENT_STATES)).sum()
    )
    filled = (
        frame["entry_ts"].is_not_null().sum()
        if "entry_ts" in frame.columns
        else (frame["state"] == "FILLED").sum()
    )
    signal = (~frame["state"].is_in(_NON_EVENT_STATES)).sum()
    stats_frame = frame.with_columns(
        (pl.col("outcome_bps") - pl.col("_fixed_outcome_bps")).alias("_delta")
    )
    stats = _clustered_interval(
        stats_frame,
        "_delta",
        block_bars=block_bars,
        n_boot=n_boot,
    )
    denominator = eligible_origins if eligible_origins is not None else frame.height
    return {
        **identity,
        "state": state,
        "eligible_origins": denominator,
        "signal_count": int(signal),
        "event_count": int(event),
        "fill_count": int(filled),
        "signal_rate": float(signal / denominator) if denominator else np.nan,
        "event_rate": float(event / denominator) if denominator else np.nan,
        "fill_rate": float(filled / denominator) if denominator else np.nan,
        "exposure_per_origin": float(frame["outcome_bps"].sum() / denominator)
        if denominator
        else np.nan,
        "estimate": stats["estimate"],
        "ci_low": stats["ci_low"],
        "ci_high": stats["ci_high"],
        "mde": stats["mde"],
        "effective_n": stats["effective_n"],
    }


def _origins_for_episodes(
    origins: pl.DataFrame,
    episodes: pl.DataFrame,
) -> pl.DataFrame:
    if "entry_variant" in origins.columns:
        return origins
    variants = episodes.select("entry_variant").unique(maintain_order=True)
    return origins.join(variants, how="cross")


def _attach_native_contract(
    experiment_id: str,
    schedule: pl.DataFrame,
) -> pl.DataFrame:
    rows = []
    for arm in build_native_lattice(experiment_id):
        rows.append(
            {
                "arm_id": arm.native_arm_id,
                "_contract_component": str(arm.component) if arm.component else None,
                "_contract_parameter": "+".join(map(str, arm.parameters))
                if arm.parameters
                else None,
                "_contract_orientation": str(arm.orientation)
                if arm.orientation
                else "FIXED"
                if not arm.is_adaptive
                else None,
                "_contract_orientation_pair": "_".join(map(str, arm.orientation_pair))
                if arm.orientation_pair
                else None,
                "_contract_comparator_id": arm.comparator_id,
            }
        )
    frame = schedule.join(pl.from_dicts(rows), on="arm_id", how="left")
    expressions = []
    for output, contract in (
        ("component", "_contract_component"),
        ("parameter", "_contract_parameter"),
        ("orientation", "_contract_orientation"),
        ("orientation_pair", "_contract_orientation_pair"),
        ("comparator_id", "_contract_comparator_id"),
    ):
        expressions.append(
            pl.coalesce([pl.col(contract), pl.col(output)]).alias(output)
            if output in frame.columns
            else pl.col(contract).alias(output)
        )
    return frame.with_columns(expressions).drop(
        column for column in frame.columns if column.startswith("_contract_")
    )


def _clustered_interval(
    frame: pl.DataFrame,
    value_column: str,
    *,
    block_bars: int,
    n_boot: int,
) -> dict[str, float | int]:
    values = _array(frame, value_column)
    if not len(values):
        return {
            "estimate": np.nan,
            "ci_low": np.nan,
            "ci_high": np.nan,
            "mde": np.nan,
            "effective_n": 0,
        }
    block_bars = max(24, int(block_bars))
    if "decision_ts" in frame.columns and frame["decision_ts"].null_count() < frame.height:
        rows_per_block = (
            frame.with_row_index("_row")
            .with_columns(
                pl.col("decision_ts")
                .cast(pl.Datetime("ns", "UTC"))
                .dt.truncate(f"{block_bars}h")
                .alias("_block")
            )
            .group_by("_block", maintain_order=True)
            .agg(pl.col("_row"))
        )["_row"].to_list()
        cast = frame[value_column].cast(pl.Float64, strict=False)
        column_values = cast.fill_null(np.nan).to_numpy().astype(float)
        column_valid = cast.is_not_null().to_numpy()
        samples = []
        for block in rows_per_block:
            rows = np.asarray(block, dtype=np.int64)
            block_values = column_values[rows][column_valid[rows]]
            if len(block_values):
                samples.append(block_values)
    else:
        samples = [np.asarray([value], dtype=float) for value in values]
    estimate = float(np.mean(values))
    if len(samples) < 2:
        return {
            "estimate": estimate,
            "ci_low": estimate,
            "ci_high": estimate,
            "mde": np.nan,
            "effective_n": len(samples),
        }
    rng = np.random.default_rng(240730)
    draws = np.empty(max(1, int(n_boot)))
    for index in range(len(draws)):
        chosen = rng.integers(0, len(samples), size=len(samples))
        draws[index] = np.mean(np.concatenate([samples[item] for item in chosen]))
    low, high = np.quantile(draws, [0.025, 0.975])
    return {
        "estimate": estimate,
        "ci_low": float(low),
        "ci_high": float(high),
        "mde": float(estimate - low),
        "effective_n": len(samples),
    }


def _attach_results(
    schedule: pl.DataFrame,
    ledger: pl.DataFrame,
    universe: str,
) -> pl.DataFrame:
    frame = _with_columns(
        schedule,
        {
            "experiment_id": "",
            "arm_id": "",
            "policy_id": "NONE",
            "native_arm_id": None,
            "component": None,
            "device": "NONE",
            "setting": "",
            "comparator_id": "",
            "risk_size": 1.0,
            "side": 0,
        },
    ).with_columns(
        pl.lit(universe).alias("universe"),
        pl.lit("ALL").alias("analysis_state"),
    )
    if ledger.is_empty():
        return frame.with_columns(
            pl.lit(0.0).alias("outcome_bps"),
            pl.lit(False).alias("target_reached"),
            pl.lit(False).alias("stop_reached"),
            pl.lit(None, dtype=pl.Float64).alias("_entry_price"),
            pl.lit(None, dtype=pl.Int64).alias("_entry_ns"),
            pl.lit(None, dtype=pl.Float64).alias("_exit_price"),
            pl.lit(None, dtype=pl.Int64).alias("_exit_ns"),
            pl.lit(None, dtype=pl.Utf8).alias("_exit_reason"),
            pl.lit(None, dtype=pl.Float64).alias("realised_capture_bps"),
            pl.lit(None, dtype=pl.Float64).alias("missed_excess_bps"),
            pl.lit(None, dtype=pl.Float64).alias("time_to_target"),
            pl.lit(None, dtype=pl.Float64).alias("partial_cost_bps"),
        )
    keys = ["episode_id", "arm_id", "policy_id"]
    entry = ledger.filter(pl.col("state") == "FILLED").group_by(keys).agg(
        pl.col("price").drop_nulls().first().cast(pl.Float64).alias("_entry_price"),
        pl.col("ts_ns").first().cast(pl.Int64).alias("_entry_ns"),
    )
    closed = ledger.filter(pl.col("state") == "CLOSED").group_by(keys).agg(
        pl.col("price").drop_nulls().last().cast(pl.Float64).alias("_exit_price"),
        pl.col("ts_ns").last().cast(pl.Int64).alias("_exit_ns"),
        pl.col("exit_reason").drop_nulls().last().alias("_exit_reason"),
    )
    frame = frame.join(entry, on=keys, how="left").join(closed, on=keys, how="left")
    outcome = (
        pl.col("side")
        * (pl.col("_exit_price") - pl.col("_entry_price"))
        / pl.col("_entry_price")
        * 1e4
    )
    return frame.with_columns(
        outcome.fill_null(0.0).alias("outcome_bps"),
        (pl.col("_exit_reason") == "TARGET").fill_null(False).alias("target_reached"),
        (pl.col("_exit_reason") == "STOP").fill_null(False).alias("stop_reached"),
        pl.when(pl.col("_entry_price").is_not_null())
        .then(outcome)
        .otherwise(None)
        .alias("realised_capture_bps"),
        pl.lit(None, dtype=pl.Float64).alias("missed_excess_bps"),
        pl.when(pl.col("_exit_reason") == "TARGET")
        .then((pl.col("_exit_ns") - pl.col("_entry_ns")) / 3_600_000_000_000)
        .otherwise(None)
        .alias("time_to_target"),
        pl.lit(None, dtype=pl.Float64).alias("partial_cost_bps"),
    )


def _attach_path_diagnostics(frame: pl.DataFrame, run_dir: Path) -> pl.DataFrame:
    """Measure excursions around engine-decided entries/exits without adjudicating exits.

    Values live in preallocated float64 arrays with a per-column written mask, so an
    unwritten row stays null (as an unfilled Python list entry did) while a written NaN
    stays NaN. A boxed-object row loop would cost roughly fifty bytes a row per column
    on runs of tens of millions of rows.
    """
    names = (
        "mfe_bps",
        "mae_bps",
        "missed_excess_bps",
        "adverse_excursion_bps",
        "recovery_after_stop_bps",
        "peak_giveback_bps",
        "favourable_excursion_captured",
        "decay_bps",
        "holding_efficiency",
        "opportunity_duration",
    )
    values = {name: np.full(frame.height, np.nan) for name in names}
    written = {name: np.zeros(frame.height, dtype=bool) for name in names}

    def _emit() -> pl.DataFrame:
        columns = []
        for name in names:
            series = pl.Series(name, values[name], dtype=pl.Float64)
            missing = np.flatnonzero(~written[name])
            if missing.size:
                series = series.scatter(missing, None)
            columns.append(series)
        return frame.with_columns(columns)

    if frame.is_empty() or "_entry_ns" not in frame.columns:
        return _emit()
    symbols = frame["symbol"].to_numpy()
    entry_ns_column = frame["_entry_ns"].to_numpy(allow_copy=True)
    exit_ns_column = frame["_exit_ns"].to_numpy(allow_copy=True)
    entry_valid = frame["_entry_ns"].is_not_null().to_numpy()
    exit_valid = frame["_exit_ns"].is_not_null().to_numpy()
    entry_price_column = frame["_entry_price"].to_numpy(allow_copy=True)
    exit_price_column = frame["_exit_price"].to_numpy(allow_copy=True)
    side_column = frame["side"].to_numpy(allow_copy=True)
    outcome_column = frame["outcome_bps"].to_numpy(allow_copy=True)
    exit_reason_column = frame["_exit_reason"].to_numpy()
    if "hold_bars" in frame.columns:
        hold_column = frame["hold_bars"].fill_null(0).to_numpy(allow_copy=True)
    else:
        hold_column = np.zeros(frame.height, dtype=np.int64)
    for symbol in frame["symbol"].unique():
        path = run_dir / "cells" / str(symbol) / "bar_marks.parquet"
        if not path.exists():
            continue
        bars = pl.read_parquet(path).sort("SourceCloseTime")
        times = (
            bars["SourceCloseTime"]
            .cast(pl.Datetime("ns", "UTC"))
            .dt.epoch("ns")
            .to_numpy()
        )
        highs = bars["RealHigh"].cast(pl.Float64).to_numpy()
        lows = bars["RealLow"].cast(pl.Float64).to_numpy()
        candidates = np.flatnonzero(
            (symbols == symbol) & entry_valid & exit_valid
        )
        for index in candidates:
            entry_ns = int(entry_ns_column[index])
            exit_ns = int(exit_ns_column[index])
            # A null or zero hold falls back to four bars, as the row-dict form did.
            hold_ns = int(hold_column[index] or 4) * 3_600_000_000_000
            horizon_ns = max(exit_ns, entry_ns + hold_ns)
            start = int(np.searchsorted(times, entry_ns, side="left"))
            stop = int(np.searchsorted(times, exit_ns, side="right"))
            horizon = int(np.searchsorted(times, horizon_ns, side="right"))
            if stop <= start:
                continue
            entry = float(entry_price_column[index])
            side = int(side_column[index])
            favourable = (
                (highs[start:stop] - entry) / entry * 1e4
                if side > 0
                else (entry - lows[start:stop]) / entry * 1e4
            )
            adverse = (
                (entry - lows[start:stop]) / entry * 1e4
                if side > 0
                else (highs[start:stop] - entry) / entry * 1e4
            )
            future_favourable = (
                (highs[start:horizon] - entry) / entry * 1e4
                if side > 0
                else (entry - lows[start:horizon]) / entry * 1e4
            )
            mfe = float(np.max(favourable))
            mae = float(np.max(adverse))
            outcome = float(outcome_column[index])
            time_to_peak = float(np.argmax(favourable) / 60.0)
            for name, value in (
                ("mfe_bps", mfe),
                ("mae_bps", mae),
                (
                    "missed_excess_bps",
                    max(0.0, float(np.max(future_favourable)) - outcome),
                ),
                ("adverse_excursion_bps", mae),
                ("peak_giveback_bps", max(0.0, mfe - outcome)),
                ("favourable_excursion_captured", _safe_ratio(outcome, mfe)),
                ("decay_bps", mfe - outcome),
                ("holding_efficiency", _safe_ratio(outcome, mfe)),
                ("opportunity_duration", time_to_peak),
            ):
                values[name][index] = value
                written[name][index] = True
            if exit_reason_column[index] == "STOP" and horizon > stop:
                exit_price = float(exit_price_column[index])
                recovery = (
                    (np.max(highs[stop:horizon]) - exit_price) / exit_price * 1e4
                    if side > 0
                    else (exit_price - np.min(lows[stop:horizon])) / exit_price * 1e4
                )
                values["recovery_after_stop_bps"][index] = float(recovery)
                written["recovery_after_stop_bps"][index] = True
    return _emit().with_columns(
        pl.when(pl.col("_exit_reason") == "TARGET")
        .then(pl.col("outcome_bps"))
        .otherwise(pl.col("realised_capture_bps"))
        .alias("realised_capture_bps")
    )


def _attach_common_context(
    estimates: pl.DataFrame,
    results: pl.DataFrame,
    config: dict[str, Any],
) -> pl.DataFrame:
    contexts = _common_context(results)
    keys = [
        "experiment_id",
        "universe",
        "symbol",
        "entry_variant",
        "arm_id",
        "state",
    ]
    frame = estimates.join(contexts, on=keys, how="left")
    return frame.with_columns(
        pl.coalesce(
            [
                pl.col("parameter") if "parameter" in frame.columns else pl.lit(None),
                pl.col("device") if "device" in frame.columns else pl.lit(None),
            ]
        ).alias("parameter_or_device"),
        pl.coalesce(
            [
                pl.col("orientation_pair")
                if "orientation_pair" in frame.columns
                else pl.lit(None),
                pl.col("orientation") if "orientation" in frame.columns else pl.lit(None),
                pl.col("setting") if "setting" in frame.columns else pl.lit(None),
            ]
        ).alias("orientation_or_setting"),
        pl.lit(config.get("spread_cost_status")).alias("spread_cost_status"),
        pl.lit(config.get("spread_rt_bps"), dtype=pl.Float64).alias("spread_rt_bps"),
        pl.lit(config.get("cost_scope")).alias("cost_scope"),
    )


def _common_context(results: pl.DataFrame) -> pl.DataFrame:
    keys = ["experiment_id", "universe", "symbol", "entry_variant", "arm_id"]
    rows: list[dict[str, Any]] = []
    for key, arm in results.group_by(keys, maintain_order=True):
        identity = dict(zip(keys, _as_tuple(key), strict=True))
        rows.append(_common_context_row(identity, arm, "ALL"))
        for state in arm["state"].drop_nulls().unique(maintain_order=True):
            rows.append(
                _common_context_row(
                    identity,
                    arm.filter(pl.col("state") == state),
                    str(state),
                )
            )
    return pl.from_dicts(rows, infer_schema_length=None)


def _common_context_row(
    identity: dict[str, Any],
    frame: pl.DataFrame,
    state: str,
) -> dict[str, Any]:
    trades = frame.filter(pl.col("_exit_price").is_not_null())
    gross = _array(trades, "outcome_bps")
    costs = _array(trades, "partial_cost_bps")
    net = gross - costs if len(gross) and len(costs) == len(gross) else np.array([])
    wins = gross[gross > 0]
    losses = gross[gross < 0]
    mean_win = float(np.mean(wins)) if len(wins) else np.nan
    mean_loss = float(np.mean(losses)) if len(losses) else np.nan
    win_share = float(np.mean(gross > 0)) if len(gross) else np.nan
    reasons = (
        trades["_exit_reason"].drop_nulls().value_counts(sort=True)
        if "_exit_reason" in trades.columns
        else pl.DataFrame()
    )
    reason_text = None
    reason_share = np.nan
    if reasons.height:
        count_column = next(column for column in reasons.columns if column != "_exit_reason")
        total = int(reasons[count_column].sum())
        reason_text = "|".join(
            f"{row['_exit_reason']}={row[count_column] / total:.6f}"
            for row in reasons.iter_rows(named=True)
        )
        reason_share = float(reasons[count_column].max() / total)
    return {
        **identity,
        "state": state,
        "trade_count": len(gross),
        "gross_mean_bps": float(np.mean(gross)) if len(gross) else np.nan,
        "gross_median_bps": float(np.median(gross)) if len(gross) else np.nan,
        "gross_trimmed_mean_bps": _trimmed_mean(gross),
        "partial_cost_mean_bps": float(np.mean(net)) if len(net) else np.nan,
        "win_share": win_share,
        "mean_win_bps": mean_win,
        "mean_loss_bps": mean_loss,
        "win_loss_ratio": _safe_ratio(mean_win, abs(mean_loss)),
        "breakeven_win_share_net": _safe_ratio(abs(mean_loss), mean_win + abs(mean_loss)),
        "edge_bps": (
            win_share * mean_win + (1.0 - win_share) * mean_loss
            if np.isfinite(win_share)
            and np.isfinite(mean_win)
            and np.isfinite(mean_loss)
            else np.nan
        ),
        "mfe_bps": _mean(trades, "mfe_bps"),
        "mae_bps": _mean(trades, "mae_bps"),
        "exit_reason": reason_text,
        "exit_reason_share": reason_share,
    }


def _trimmed_mean(values: np.ndarray, trim: float = 0.2) -> float:
    if not len(values):
        return np.nan
    ordered = np.sort(values)
    cut = int(np.floor(len(ordered) * trim))
    core = ordered[cut : len(ordered) - cut] if len(ordered) - 2 * cut else ordered
    return float(np.mean(core))


def _device_table(
    results: pl.DataFrame,
    device: str,
    *,
    block_bars: int,
    n_boot: int,
) -> pl.DataFrame:
    frame = results.filter(pl.col("device").cast(pl.Utf8).str.contains(device))
    if frame.is_empty():
        return pl.DataFrame()
    metric_function: Callable[[pl.DataFrame], dict[str, float]] = {
        "TARGET": target_metrics,
        "STOP": stop_metrics,
        "TRAIL": trail_metrics,
        "HOLD": hold_metrics,
        "SIZE": size_metrics,
    }[device]
    group_columns = [column for column in _IDENTITY_COLUMNS if column in frame.columns]
    comparator_keys = ["arm_id", "symbol", "entry_variant", "state"]
    comparators = results.filter(
        pl.col("arm_id").is_in(frame["comparator_id"].unique().implode())
    ).partition_by(comparator_keys, as_dict=True, maintain_order=True)
    arm_rows: list[dict[str, Any]] = []
    for key, group in frame.group_by(group_columns, maintain_order=True):
        identity = dict(zip(group_columns, _as_tuple(key), strict=True))
        comparator = comparators.get(
            (
                identity["comparator_id"],
                identity["symbol"],
                identity["entry_variant"],
                identity["state"],
            ),
            frame.head(0),
        )
        if comparator.is_empty():
            raise ValueError(
                f"missing paired comparator {identity['comparator_id']} "
                f"for {identity['arm_id']}"
            )
        paired_left, paired_right = _pair_episode_rows(group, comparator)
        if paired_left.is_empty():
            raise ValueError(
                f"no shared episodes for {identity['arm_id']} "
                f"and {identity['comparator_id']}"
            )
        observed_metrics = metric_function(paired_left)
        comparator_metrics = metric_function(paired_right)
        for metric_name, observed in observed_metrics.items():
            stats = _paired_metric_interval(
                paired_left,
                paired_right,
                metric_function,
                metric_name,
                device=device,
                block_bars=block_bars,
                n_boot=n_boot,
            )
            arm_rows.append(
                {
                    **identity,
                    "metric_name": metric_name,
                    "observed": observed,
                    "comparator_observed": comparator_metrics[metric_name],
                    "estimate": stats["estimate"],
                    "ci_low": stats["ci_low"],
                    "ci_high": stats["ci_high"],
                    "mde": stats["mde"],
                    "episode_n": paired_left.height,
                    "effective_n": stats["effective_n"],
                }
            )
    return pl.from_dicts(arm_rows, infer_schema_length=None)


_DEVICE_METRIC_COLUMNS = {
    "TARGET": (
        "target_reached",
        "realised_capture_bps",
        "missed_excess_bps",
        "time_to_target",
    ),
    "STOP": (
        "adverse_excursion_bps",
        "stop_reached",
        "outcome_bps",
        "recovery_after_stop_bps",
    ),
    "TRAIL": ("peak_giveback_bps", "favourable_excursion_captured", "outcome_bps"),
    "HOLD": ("outcome_bps", "decay_bps", "holding_efficiency", "opportunity_duration"),
    "SIZE": ("outcome_bps", "risk_size"),
}
_BOOLEAN_METRIC_COLUMNS = frozenset({"target_reached", "stop_reached"})


def _metric_arrays(frame: pl.DataFrame, columns: tuple[str, ...]) -> dict[str, Any]:
    """Extract one NumPy view per metric column, keeping polars null semantics.

    Float columns become ``(values, valid)`` where ``valid`` marks non-null rows, so a
    gathered subset can reproduce ``_array``'s drop-nulls-but-keep-NaN behaviour exactly.
    Boolean columns become a null-as-False array, matching ``_rate``/``_subset_true``.
    """
    arrays: dict[str, Any] = {}
    for column in columns:
        if column not in frame.columns:
            arrays[column] = None
            continue
        series = frame[column]
        if column in _BOOLEAN_METRIC_COLUMNS:
            arrays[column] = (
                series.cast(pl.Boolean, strict=False).fill_null(False).to_numpy()
            )
        else:
            cast = series.cast(pl.Float64, strict=False)
            arrays[column] = (
                cast.fill_null(np.nan).to_numpy().astype(float),
                cast.is_not_null().to_numpy(),
            )
    return arrays


def _kernel_values(arrays: dict[str, Any], column: str, rows: np.ndarray) -> np.ndarray:
    """Reproduce ``_array`` on a gathered subset: drop nulls, keep NaN, keep order."""
    entry = arrays.get(column)
    if entry is None or not len(rows):
        return np.array([], dtype=float)
    values, valid = entry
    selected = values[rows]
    return selected[valid[rows]]


def _kernel_mean(arrays: dict[str, Any], column: str, rows: np.ndarray) -> float:
    values = _kernel_values(arrays, column, rows)
    return float(np.mean(values)) if len(values) else np.nan


def _kernel_rate(arrays: dict[str, Any], column: str, rows: np.ndarray) -> float:
    entry = arrays.get(column)
    if entry is None or not len(rows):
        return np.nan
    return float(np.mean(entry[rows]))


def _kernel_true_rows(
    arrays: dict[str, Any], column: str, rows: np.ndarray
) -> np.ndarray:
    entry = arrays.get(column)
    if entry is None:
        return rows[:0]
    return rows[entry[rows]]


def _kernel_target(arrays: dict[str, Any], rows: np.ndarray) -> dict[str, float]:
    return {
        "reach_rate": _kernel_rate(arrays, "target_reached", rows),
        "realised_capture_bps": _kernel_mean(arrays, "realised_capture_bps", rows),
        "missed_excess_bps": _kernel_mean(arrays, "missed_excess_bps", rows),
        "time_to_target": _kernel_mean(arrays, "time_to_target", rows),
    }


def _kernel_stop(arrays: dict[str, Any], rows: np.ndarray) -> dict[str, float]:
    stopped = _kernel_true_rows(arrays, "stop_reached", rows)
    return {
        "adverse_excursion_bps": _kernel_mean(arrays, "adverse_excursion_bps", rows),
        "stop_rate": _kernel_rate(arrays, "stop_reached", rows),
        "loss_severity_bps": _kernel_mean(arrays, "outcome_bps", stopped),
        "recovery_after_stop_bps": _kernel_mean(
            arrays, "recovery_after_stop_bps", stopped
        ),
    }


def _kernel_trail(arrays: dict[str, Any], rows: np.ndarray) -> dict[str, float]:
    outcomes = _kernel_values(arrays, "outcome_bps", rows)
    return {
        "peak_giveback_bps": _kernel_mean(arrays, "peak_giveback_bps", rows),
        "favourable_excursion_captured": _kernel_mean(
            arrays, "favourable_excursion_captured", rows
        ),
        "loss_tail_bps": _quantile(outcomes, 0.05),
    }


def _kernel_hold(arrays: dict[str, Any], rows: np.ndarray) -> dict[str, float]:
    return {
        "outcome_by_time_bps": _kernel_mean(arrays, "outcome_bps", rows),
        "decay_bps": _kernel_mean(arrays, "decay_bps", rows),
        "holding_efficiency": _kernel_mean(arrays, "holding_efficiency", rows),
        "opportunity_duration": _kernel_mean(arrays, "opportunity_duration", rows),
    }


def _kernel_size(arrays: dict[str, Any], rows: np.ndarray) -> dict[str, float]:
    outcome = _kernel_values(arrays, "outcome_bps", rows)
    size = _kernel_values(arrays, "risk_size", rows)
    n = min(len(outcome), len(size))
    sized = outcome[:n] * size[:n] if n else np.array([], dtype=float)
    cumulative = np.cumsum(sized)
    drawdown = cumulative - np.maximum.accumulate(cumulative) if n else sized
    losses = np.abs(sized[sized < 0])
    absolute = np.abs(sized)
    concentration = (
        float(absolute.max() / absolute.sum())
        if absolute.size and absolute.sum()
        else 0.0
    )
    return {
        "risk_dispersion": float(np.std(sized, ddof=1))
        if n > 1
        else 0.0
        if n
        else np.nan,
        "drawdown_bps": float(drawdown.min()) if n else np.nan,
        "tail_loss_bps": _quantile(losses, 0.95),
        "concentration": concentration,
    }


_METRIC_KERNELS: dict[str, Callable[[dict[str, Any], np.ndarray], dict[str, float]]] = {
    "TARGET": _kernel_target,
    "STOP": _kernel_stop,
    "TRAIL": _kernel_trail,
    "HOLD": _kernel_hold,
    "SIZE": _kernel_size,
}


def _pair_episode_rows(
    adaptive: pl.DataFrame,
    comparator: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    common = (
        adaptive.select("episode_id")
        .unique()
        .join(comparator.select("episode_id").unique(), on="episode_id", how="inner")
    )
    left = adaptive.join(common, on="episode_id", how="inner").sort("episode_id")
    right = comparator.join(common, on="episode_id", how="inner").sort("episode_id")
    if left.select("episode_id").is_duplicated().any():
        raise ValueError("duplicate adaptive episode in device comparison")
    if right.select("episode_id").is_duplicated().any():
        raise ValueError("duplicate comparator episode in device comparison")
    return left, right


def _paired_metric_interval(
    adaptive: pl.DataFrame,
    comparator: pl.DataFrame,
    metric_function: Callable[[pl.DataFrame], dict[str, float]],
    metric_name: str,
    *,
    device: str,
    block_bars: int,
    n_boot: int,
) -> dict[str, float | int]:
    observed = metric_function(adaptive)[metric_name]
    fixed = metric_function(comparator)[metric_name]
    estimate = float(observed - fixed)
    if adaptive.height < 2:
        return {
            "estimate": estimate,
            "ci_low": estimate,
            "ci_high": estimate,
            "mde": np.nan,
            "effective_n": adaptive.height,
        }
    block_bars = max(24, int(block_bars))
    indexed = adaptive.with_row_index("_row")
    if "decision_ts" in indexed.columns:
        partitions = (
            indexed.with_columns(
                pl.col("decision_ts")
                .cast(pl.Datetime("ns", "UTC"))
                .dt.truncate(f"{block_bars}h")
                .alias("_block")
            )
            .group_by("_block", maintain_order=True)
            .agg(pl.col("_row"))
        )["_row"].to_list()
    else:
        partitions = [[index] for index in range(adaptive.height)]
    if len(partitions) < 2:
        return {
            "estimate": estimate,
            "ci_low": estimate,
            "ci_high": estimate,
            "mde": np.nan,
            "effective_n": len(partitions),
        }
    blocks = [np.asarray(block, dtype=np.int64) for block in partitions]
    columns = _DEVICE_METRIC_COLUMNS[device]
    kernel = _METRIC_KERNELS[device]
    left_arrays = _metric_arrays(adaptive, columns)
    right_arrays = _metric_arrays(comparator, columns)
    rng = np.random.default_rng(240730)
    draws = []
    for _ in range(max(1, int(n_boot))):
        chosen = rng.integers(0, len(partitions), size=len(partitions))
        rows = np.concatenate([blocks[block] for block in chosen])
        left_metric = kernel(left_arrays, rows)[metric_name]
        right_metric = kernel(right_arrays, rows)[metric_name]
        if np.isfinite(left_metric) and np.isfinite(right_metric):
            draws.append(left_metric - right_metric)
    if not draws:
        low = high = np.nan
    else:
        low, high = np.quantile(np.asarray(draws), [0.025, 0.975])
    return {
        "estimate": estimate,
        "ci_low": float(low),
        "ci_high": float(high),
        "mde": float(estimate - low) if np.isfinite(low) else np.nan,
        "effective_n": len(partitions),
    }


def _shared_trade_diagnostics(results: pl.DataFrame) -> pl.DataFrame:
    if results.is_empty():
        return pl.DataFrame()
    fixed = results.filter(pl.col("arm_class") == "FIXED_NATIVE").select(
        "origin_id",
        "symbol",
        "entry_variant",
        pl.col("outcome_bps").alias("fixed_outcome_bps"),
        pl.col("entry_ts").alias("fixed_entry_ts")
        if "entry_ts" in results.columns
        else pl.lit(None).alias("fixed_entry_ts"),
    )
    adaptive = results.filter(pl.col("arm_class") != "FIXED_NATIVE")
    return (
        adaptive.join(fixed, on=["origin_id", "symbol", "entry_variant"], how="inner")
        .filter(
            pl.col("entry_ts").is_not_null() & pl.col("fixed_entry_ts").is_not_null()
            if "entry_ts" in adaptive.columns
            else pl.lit(False)
        )
        .with_columns(
            (pl.col("outcome_bps") - pl.col("fixed_outcome_bps")).alias(
                "paired_outcome_delta_bps"
            )
        )
    )


def _selected_excluded(results: pl.DataFrame) -> pl.DataFrame:
    if results.is_empty():
        return pl.DataFrame()
    return results.select(
        *[
            column
            for column in (
                "experiment_id",
                "universe",
                "symbol",
                "entry_variant",
                "arm_id",
                "arm_class",
                "component",
                "origin_id",
                "state",
                "outcome_bps",
            )
            if column in results.columns
        ],
        pl.when(pl.col("state").is_in(["NO_EVENT", "NO_FEATURE", "BLOCKED_ACTIVE"]))
        .then(pl.lit("EXCLUDED"))
        .otherwise(pl.lit("SELECTED"))
        .alias("selection"),
    )


def _selection_checks(frame: pl.DataFrame) -> pl.DataFrame:
    if frame.is_empty():
        return pl.DataFrame()
    group_columns = [
        column
        for column in (
            "experiment_id",
            "universe",
            "symbol",
            "entry_variant",
            "arm_id",
            "component",
        )
        if column in frame.columns
    ]
    rows = []
    for key, group in frame.group_by(group_columns, maintain_order=True):
        identity = dict(zip(group_columns, _as_tuple(key), strict=True))
        selected = _array(group.filter(pl.col("selection") == "SELECTED"), "outcome_bps")
        excluded = _array(group.filter(pl.col("selection") == "EXCLUDED"), "outcome_bps")
        rows.append(
            {
                **identity,
                "payoff_scale_ratio": _safe_ratio(
                    np.mean(np.abs(selected)) if len(selected) else np.nan,
                    np.mean(np.abs(excluded)) if len(excluded) else np.nan,
                ),
                "sign_share_difference": _positive_share(selected)
                - _positive_share(excluded),
                "excluded_mean_median_gap": float(np.mean(excluded) - np.median(excluded))
                if len(excluded)
                else np.nan,
                "selected_n": len(selected),
                "excluded_n": len(excluded),
            }
        )
    return pl.from_dicts(rows, infer_schema_length=None)


def _state_sections(native: pl.DataFrame, policies: pl.DataFrame) -> pl.DataFrame:
    frame = pl.concat([native, policies], how="diagonal_relaxed")
    if frame.is_empty():
        return pl.DataFrame()
    return (
        frame.group_by(
            [
                column
                for column in (
                    "experiment_id",
                    "universe",
                    "symbol",
                    "entry_variant",
                    "arm_id",
                    "component",
                    "state",
                )
                if column in frame.columns
            ]
        )
        .agg(
            pl.len().alias("row_n"),
            pl.col("outcome_bps").mean().alias("mean_outcome_bps"),
        )
        .sort(["symbol", "entry_variant", "arm_id", "state"])
    )


def _control_inventory(experiment_id: str, universe: str) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "experiment_id": [experiment_id] * 4,
            "universe": [universe] * 4,
            "control": [
                "FIXED_DEVICE",
                "FIXED_NATIVE_PARAMETER",
                "TIME_DERANGEMENT",
                "MAGNITUDE_MATCH",
            ],
            "analysis_stage": [
                "COMPUTED",
                "COMPUTED",
                "DEFERRED_TO_STAGE_8",
                "DEFERRED_TO_STAGE_8",
            ],
        }
    )


def _tag_estimate_source(frame: pl.DataFrame, source: str) -> pl.DataFrame:
    if frame.is_empty():
        return frame
    expressions = [pl.lit(source).alias("estimate_source")]
    if "metric_name" not in frame.columns:
        expressions.append(pl.lit("outcome_bps").alias("metric_name"))
    return frame.with_columns(expressions)


def _empty_estimates() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "experiment_id": pl.Utf8,
            "universe": pl.Utf8,
            "symbol": pl.Utf8,
            "entry_variant": pl.Utf8,
            "arm_id": pl.Utf8,
            "arm_class": pl.Utf8,
            "component": pl.Utf8,
            "device": pl.Utf8,
            "setting": pl.Utf8,
            "comparator_id": pl.Utf8,
            "metric_name": pl.Utf8,
            "estimate": pl.Float64,
            "ci_low": pl.Float64,
            "ci_high": pl.Float64,
            "mde": pl.Float64,
            "paired_n": pl.Int64,
            "effective_n": pl.Int64,
        }
    )


def _with_columns(frame: pl.DataFrame, defaults: dict[str, Any]) -> pl.DataFrame:
    expressions = [
        pl.lit(value).alias(column)
        for column, value in defaults.items()
        if column not in frame.columns
    ]
    return frame.with_columns(expressions) if expressions else frame


def _array(frame: pl.DataFrame, column: str) -> np.ndarray:
    if column not in frame.columns or frame.is_empty():
        return np.array([], dtype=float)
    return (
        frame[column]
        .cast(pl.Float64, strict=False)
        .drop_nulls()
        .to_numpy()
        .astype(float)
    )


def _mean(frame: pl.DataFrame, column: str) -> float:
    values = _array(frame, column)
    return float(np.mean(values)) if len(values) else np.nan


def _rate(frame: pl.DataFrame, column: str) -> float:
    if column not in frame.columns or frame.is_empty():
        return np.nan
    return float(frame[column].cast(pl.Boolean, strict=False).fill_null(False).mean())


def _quantile(values: np.ndarray, quantile: float) -> float:
    return float(np.quantile(values, quantile)) if len(values) else np.nan


def _subset_true(frame: pl.DataFrame, column: str) -> pl.DataFrame:
    if column not in frame.columns:
        return frame.head(0)
    return frame.filter(pl.col(column).cast(pl.Boolean, strict=False).fill_null(False))


def _positive_share(values: np.ndarray) -> float:
    return float(np.mean(values > 0)) if len(values) else np.nan


def _safe_ratio(numerator: float, denominator: float) -> float:
    return (
        float(numerator / denominator)
        if np.isfinite(numerator) and np.isfinite(denominator) and denominator != 0
        else np.nan
    )


def _as_tuple(value: Any) -> tuple[Any, ...]:
    return value if isinstance(value, tuple) else (value,)


def _atomic_parquet(frame: pl.DataFrame, path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.write_parquet(temporary)
    temporary.replace(path)


def _atomic_json(payload: dict[str, Any], path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
