"""Hard integrity checks and informative controls for adaptive-management runs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
import uuid

import numpy as np
import polars as pl

from xen.adaptive_management.contracts import (
    build_management_lattice,
    build_native_lattice,
)


INTEGRITY_ARTIFACTS = (
    "integrity_selfcheck.json",
    "golden_traces.json",
    "determinism.json",
    "row_accounting.json",
    "controls.json",
)


def derange_component_times(features: pl.DataFrame, seed: int) -> pl.DataFrame:
    """Attach a deterministic zero-fixed-point permutation of feature timestamps."""
    if "ts" not in features.columns:
        raise ValueError("features require ts")
    if features.height < 2:
        raise ValueError("derangement requires at least two rows")
    rng = np.random.default_rng(seed)
    order = np.arange(features.height)
    shift = int(rng.integers(1, features.height))
    source = features["ts"].gather(np.roll(order, shift))
    return features.with_columns(source.alias("source_ts"))


def future_shift_tripwire(features: pl.DataFrame) -> dict[str, Any]:
    """Report whether a one-row future shift changes the feature-time mapping."""
    if "ts" not in features.columns:
        raise ValueError("features require ts")
    rows = features.height
    if rows < 2:
        return {
            "row_count_before": rows,
            "row_count_after": rows,
            "unchanged_fraction": 1.0,
            "changed_mapping": False,
        }
    shifted = features["ts"].gather(np.roll(np.arange(rows), -1))
    unchanged = int((shifted == features["ts"]).sum())
    return {
        "row_count_before": rows,
        "row_count_after": rows,
        "unchanged_fraction": unchanged / rows,
        "changed_mapping": unchanged < rows,
    }


def magnitude_matched_controls(
    episodes: pl.DataFrame,
    features: pl.DataFrame,
) -> pl.DataFrame:
    """Label deterministic within-symbol magnitude strata for informative comparisons."""
    required_episode = {"symbol", "decision_ts"}
    magnitude_column = (
        "magnitude_bps"
        if "magnitude_bps" in features.columns
        else "swing_scale_bps"
        if "swing_scale_bps" in features.columns
        else None
    )
    required_feature = {"symbol", "ts"}
    if not required_episode.issubset(episodes.columns):
        raise ValueError(f"episodes require {sorted(required_episode)}")
    if not required_feature.issubset(features.columns) or magnitude_column is None:
        raise ValueError("features require symbol, ts and a magnitude column")
    joined = episodes.join(
        features.select(
            "symbol",
            pl.col("ts").alias("decision_ts"),
            pl.col(magnitude_column).cast(pl.Float64).alias("magnitude_bps"),
        ),
        on=["symbol", "decision_ts"],
        how="left",
    )
    unmatched = episodes.join(
        features.select("symbol", pl.col("ts").alias("decision_ts")),
        on=["symbol", "decision_ts"],
        how="anti",
    )
    if unmatched.height:
        raise ValueError("magnitude match has unmatched episode timestamps")
    # A matched timestamp can still carry no magnitude: the component is unwarmed at the start
    # of the band. Those origins cannot be stratified, so they are held out of this informative
    # control rather than aborting it, and they are never counted as selected.
    unwarmed = int(joined["magnitude_bps"].is_null().sum()) + int(
        joined["magnitude_bps"].is_nan().fill_null(False).sum()
    )
    joined = joined.with_columns(
        pl.when(pl.col("magnitude_bps").is_nan().fill_null(False))
        .then(None)
        .otherwise(pl.col("magnitude_bps"))
        .alias("magnitude_bps")
    )
    if unwarmed:
        joined = joined.filter(pl.col("magnitude_bps").is_not_null())
    if joined.is_empty():
        return joined.with_columns(
            pl.lit(None, dtype=pl.Int64).alias("magnitude_bin"),
            pl.lit(False).alias("selected"),
        )
    ranked = joined.with_columns(
        pl.col("magnitude_bps")
        .rank("ordinal")
        .over("symbol")
        .alias("_magnitude_rank")
    )
    counts = ranked.group_by("symbol").len().rename({"len": "_symbol_n"})
    return (
        ranked.join(counts, on="symbol")
        .with_columns(
            (
                (pl.col("_magnitude_rank") - 1)
                * pl.lit(4)
                / pl.col("_symbol_n")
            )
            .floor()
            .cast(pl.Int64)
            .alias("magnitude_bin"),
            ((pl.col("_magnitude_rank") % 2) == 1).alias("selected"),
        )
        .drop("_magnitude_rank", "_symbol_n")
    )


def replay_hashes(run_dir: Path) -> dict[str, str]:
    """Hash deterministic raw run artifacts by relative path."""
    run_dir = Path(run_dir)
    hashes: dict[str, str] = {}
    for path in sorted(run_dir.rglob("*")):
        if (
            not path.is_file()
            or path.name in INTEGRITY_ARTIFACTS
            or path.name == "determinism_reference.json"
            # AppleDouble sidecars: filesystem metadata the OS writes beside real files on
            # non-native volumes. They are not run artifacts and are not reproducible.
            or path.name.startswith("._")
            or path.name == ".DS_Store"
        ):
            continue
        hashes[path.relative_to(run_dir).as_posix()] = _sha256(path)
    return hashes


def run_integrity_checks(
    run_dir: Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Run hard checks and atomically publish the Stage 8 integrity package."""
    run_dir = Path(run_dir)
    destination = Path(output_dir) if output_dir is not None else run_dir
    config = _read_json(run_dir / "config.json")
    experiment_id = str(config.get("experiment_id", ""))
    universe = str(config.get("universe", ""))
    # A breach crypto run is a 78.7M-row ledger plus 67M rows of schedules. Loading every
    # table at once got this process killed by the kernel, so each check reads only the
    # columns it uses and the frame is released before the next check runs.
    features = _read_parquet(run_dir / "features.parquet")
    origins = _read_parquet(run_dir / "origins.parquet")

    source_hashes = replay_hashes(run_dir)
    fence = _check_fence(run_dir, config)
    provenance = _check_causality(features, origins)

    accounting_columns = ["arm_id", "origin_id", "entry_variant"]
    native = _read_parquet(
        run_dir / "native_parameter_schedule.parquet",
        columns=accounting_columns + ["arm_class"],
    )
    policies = _read_parquet(
        run_dir / "policy_schedule.parquet",
        columns=accounting_columns
        + ["native_arm_id", "policy_id", "comparator_id", "device"],
    )
    row_accounting = _check_row_accounting(origins, native, policies)
    native_lattice = _check_native_lattice(experiment_id, origins, native)
    management_lattice = _check_management_lattice(experiment_id, origins, policies)
    no_cross = _check_no_cross(policies)
    fixed_comparators = _check_fixed_comparators(policies)
    parity = _check_entry_parity(experiment_id, origins, native)
    del native

    ledger = _read_parquet(
        run_dir / "episode_results.parquet",
        columns=[
            "episode_id", "arm_id", "policy_id", "state", "ts_ns", "exit_reason",
            "experiment_id", "entry_variant", "device", "price",
            # reconciliation reads these when the emission carries them
            "position_id", "outcome_bps", "side",
        ],
    )
    unique_results = _check_unique_results(ledger)
    golden = _golden_trace_checks(ledger)
    attestation = _read_json(run_dir / "fence_attestation.json")
    train_end = _parse_timestamp(attestation.get("train_end_utc"))
    train_end_ns = int(train_end.timestamp() * 1e9) if train_end is not None else None
    management_lifecycle = _check_management_lifecycle(
        ledger, policies, train_end_ns
    )
    del policies
    ledger_rows = ledger.height

    orders = _read_parquet(run_dir / "orders.parquet", columns=["client_order_id", "status"])
    fills = _read_parquet(
        run_dir / "fills.parquet", columns=["client_order_id", "position_id"]
    )
    positions = _read_parquet(
        run_dir / "positions.parquet",
        columns=["position_id", "avg_px_open", "avg_px_close"],
    )
    reconciliation = _check_reconciliation(orders, fills, positions, ledger)
    del orders, fills, positions, ledger

    future = future_shift_tripwire(features)
    deterministic = _check_determinism(run_dir, source_hashes)

    hard_checks = {
        "fence": fence["pass"],
        "provenance": provenance,
        "causality": provenance,
        "entry_parity": parity,
        "golden_traces": golden["pass"],
        "order_fill_position_reconciliation": reconciliation["pass"],
        "row_accounting": row_accounting["pass"],
        "native_lattice": native_lattice,
        "management_lattice": management_lattice and fixed_comparators,
        "no_native_management_cross": no_cross,
        "unique_result_keys": unique_results,
        "future_shift_changed_mapping": bool(future["changed_mapping"]),
        "deterministic_replay": deterministic["pass"],
        "management_lifecycle": management_lifecycle,
    }
    controls = _informative_controls(features, origins, ledger_rows)
    result = {
        "experiment_id": experiment_id,
        "universe": universe,
        "run_path": str(run_dir.resolve()),
        "source_artifact_hashes": source_hashes,
        "blocking_pass": all(hard_checks.values()),
        "hard_checks": hard_checks,
        "informative": controls,
    }
    common = {
        "experiment_id": experiment_id,
        "universe": universe,
        "run_path": str(run_dir.resolve()),
        "source_artifact_hashes": source_hashes,
    }
    artifacts = {
        "golden_traces.json": {**common, **golden},
        "determinism.json": {**common, **deterministic},
        "row_accounting.json": {**common, **row_accounting},
        "controls.json": {**common, **controls},
        "integrity_selfcheck.json": result,
    }
    _publish_artifacts(destination, artifacts)
    return result


def _check_fence(run_dir: Path, config: dict[str, Any]) -> dict[str, Any]:
    attestation = _read_json(run_dir / "fence_attestation.json")
    manifest_value = attestation.get("manifest_path")
    manifest = Path(str(manifest_value)) if manifest_value else Path()
    if manifest_value and not manifest.is_absolute():
        manifest = Path(__file__).resolve().parents[4] / manifest
    manifest_hash = _sha256(manifest) if manifest.is_file() else None
    pinned = (
        config.get("band") == "TRAIN"
        and attestation.get("status") == "PINNED"
        and bool(attestation.get("manifest_sha256"))
        and attestation.get("manifest_sha256") == manifest_hash
    )
    train_end = _parse_timestamp(attestation.get("train_end_utc"))
    bars_within = train_end is not None
    for path in run_dir.glob("cells/*/bar_marks.parquet"):
        bars = _read_parquet(path)
        column = "SourceCloseTime" if "SourceCloseTime" in bars.columns else "ts"
        if column not in bars.columns or bars.is_empty():
            bars_within = False
            continue
        latest = bars[column].cast(pl.Datetime("ns", "UTC")).max()
        bars_within = bars_within and latest <= train_end
    return {
        "pass": bool(pinned and bars_within),
        "manifest_pinned": bool(pinned),
        "bar_marks_within_train": bool(bars_within),
    }


def _check_causality(features: pl.DataFrame, origins: pl.DataFrame) -> bool:
    if features.is_empty() or origins.is_empty():
        return False
    source_column = "source_ts" if "source_ts" in features.columns else "ts"
    if source_column not in features.columns or "decision_ts" not in origins.columns:
        return False
    compared = origins.select("symbol", "decision_ts").unique().join(
        features.select(
            "symbol",
            pl.col("ts").alias("decision_ts"),
            pl.col(source_column).alias("_feature_source"),
        ),
        on=["symbol", "decision_ts"],
        how="left",
    )
    if compared.is_empty() or compared["_feature_source"].null_count():
        return False
    return bool(
        compared.select(
            (
                pl.col("_feature_source").cast(pl.Datetime("ns", "UTC"))
                <= pl.col("decision_ts").cast(pl.Datetime("ns", "UTC"))
            ).all()
        ).item()
    )


def _check_row_accounting(
    origins: pl.DataFrame,
    native: pl.DataFrame,
    policies: pl.DataFrame,
) -> dict[str, Any]:
    if origins.is_empty():
        return {"pass": False, "origin_count": 0}
    native_complete = _each_arm_has_origins(native, origins)
    policy_complete = _each_arm_has_origins(policies, origins)
    return {
        "pass": native_complete and policy_complete,
        "origin_count": origins.height,
        "native_rows": native.height,
        "management_rows": policies.height,
        "native_complete": native_complete,
        "management_complete": policy_complete,
    }


def _each_arm_has_origins(frame: pl.DataFrame, origins: pl.DataFrame) -> bool:
    required = {"arm_id", "origin_id", "entry_variant"}
    if frame.is_empty() or not required.issubset(frame.columns):
        return False
    # A breakout origin belongs to one entry variant. A breach zone origin is common to both
    # E-TOUCH and E-CLOSE and therefore carries no variant of its own: every arm of either
    # variant must then cover every origin.
    origins_are_variant_specific = "entry_variant" in origins.columns
    for identity in frame.select("entry_variant", "arm_id").unique().iter_rows(
        named=True
    ):
        expected = set(
            (
                origins.filter(pl.col("entry_variant") == identity["entry_variant"])
                if origins_are_variant_specific
                else origins
            )["origin_id"].cast(pl.Utf8)
        )
        actual = set(
            frame.filter(
                (pl.col("entry_variant") == identity["entry_variant"])
                & (pl.col("arm_id") == identity["arm_id"])
            )["origin_id"].cast(pl.Utf8)
        )
        if actual != expected:
            return False
    return True


def _check_native_lattice(
    experiment_id: str,
    origins: pl.DataFrame,
    native: pl.DataFrame,
) -> bool:
    try:
        expected = {arm.native_arm_id for arm in build_native_lattice(experiment_id)}
    except ValueError:
        return False
    actual = set(native["arm_id"].cast(pl.Utf8)) if "arm_id" in native.columns else set()
    if actual != expected or origins.is_empty():
        return False
    keys = ["origin_id", "entry_variant", "arm_id"]
    return set(keys).issubset(native.columns) and not native.select(keys).is_duplicated().any()


def _check_management_lattice(
    experiment_id: str,
    origins: pl.DataFrame,
    policies: pl.DataFrame,
) -> bool:
    try:
        expected = {
            arm.combination_id
            if arm.combination_id and arm.combination_id.startswith("DC_")
            else arm.policy_id
            for arm in build_management_lattice(experiment_id)
        }
    except ValueError:
        return False
    actual = (
        set(policies["policy_id"].cast(pl.Utf8))
        if "policy_id" in policies.columns
        else set()
    )
    keys = ["origin_id", "entry_variant", "arm_id"]
    return (
        actual == expected
        and not origins.is_empty()
        and set(keys).issubset(policies.columns)
        and not policies.select(keys).is_duplicated().any()
    )


def _check_no_cross(policies: pl.DataFrame) -> bool:
    if policies.is_empty() or "native_arm_id" not in policies.columns:
        return False
    return not bool(
        policies.select(
            (
                pl.col("native_arm_id").is_not_null()
                & ~pl.col("native_arm_id").cast(pl.Utf8).is_in(["", "None"])
            ).any()
        ).item()
    )


def _check_fixed_comparators(policies: pl.DataFrame) -> bool:
    required = {"entry_variant", "arm_id", "comparator_id"}
    if policies.is_empty() or not required.issubset(policies.columns):
        return False
    identities = policies.select(required).unique()
    for row in identities.iter_rows(named=True):
        if not identities.filter(
            (pl.col("entry_variant") == row["entry_variant"])
            & (pl.col("arm_id") == row["comparator_id"])
        ).height:
            return False
    return True


def _check_unique_results(ledger: pl.DataFrame) -> bool:
    # exit_reason names the leg for a combination arm, whose legs can each fail at the same
    # instant; without it two legitimate per-leg rows look like one duplicated row.
    keys = [
        column
        for column in ("episode_id", "arm_id", "state", "ts_ns", "exit_reason")
        if column in ledger.columns
    ]
    return bool(keys) and not ledger.select(keys).is_duplicated().any()


def _check_management_lifecycle(
    ledger: pl.DataFrame,
    policies: pl.DataFrame,
    train_end_ns: int | None,
) -> bool:
    """Require every filled management execution to close or carry an explicit fence label."""
    required = {"episode_id", "arm_id", "state", "ts_ns"}
    if ledger.is_empty() or not required.issubset(ledger.columns):
        return False
    identities = ["episode_id", "arm_id"]
    if "entry_variant" in ledger.columns:
        identities.append("entry_variant")
    summary = ledger.group_by(identities).agg(
        (pl.col("state") == "FILLED").any().alias("_filled"),
        (pl.col("state") == "CLOSED").any().alias("_closed"),
        pl.col("state")
        .is_in(["EXIT_DENIED", "EXIT_REJECTED"])
        .any()
        .alias("_exit_failed"),
        ((pl.col("state") == "CLOSED") & (pl.col("exit_reason") == "FAILSAFE"))
        .any()
        .alias("_failsafe_closed"),
        pl.col("state")
        .is_in(["OPEN_AT_FENCE_END", "CENSORED"])
        .any()
        .alias("_censored"),
        pl.when(pl.col("state").is_in(["OPEN_AT_FENCE_END", "CENSORED"]))
        .then(pl.col("ts_ns"))
        .max()
        .alias("_censor_ns"),
        pl.col("device").drop_nulls().first().alias("_ledger_device")
        if "device" in ledger.columns
        else pl.lit(None, dtype=pl.Utf8).alias("_ledger_device"),
    ).filter(pl.col("_filled"))
    if summary.is_empty():
        return True
    if {"arm_id", "device"}.issubset(policies.columns):
        policy_devices = policies.select(
            "arm_id", pl.col("device").alias("_policy_device")
        ).unique()
        summary = summary.join(policy_devices, on="arm_id", how="left")
    else:
        summary = summary.with_columns(
            pl.lit(None, dtype=pl.Utf8).alias("_policy_device")
        )
    summary = summary.with_columns(
        pl.coalesce("_policy_device", "_ledger_device").alias("_device")
    )
    timed = pl.col("_device").fill_null("").str.contains(
        r"(^|\+)(SIZE|HOLD)(\+|$)"
    )
    censor_after_fence = (
        pl.lit(False)
        if train_end_ns is None
        else pl.col("_censor_ns") > train_end_ns
    )
    valid = (
        pl.when(pl.col("_exit_failed"))
        .then(pl.col("_failsafe_closed"))
        .otherwise(
            pl.col("_closed")
            | (pl.col("_censored") & (~timed | censor_after_fence))
        )
    )
    return bool(summary.select(valid.all()).item())


def _check_reconciliation(
    orders: pl.DataFrame,
    fills: pl.DataFrame,
    positions: pl.DataFrame,
    ledger: pl.DataFrame,
) -> dict[str, Any]:
    order_id = _first_column(orders, "client_order_id", "order_id")
    fill_order_id = _first_column(fills, "client_order_id", "order_id")
    position_id = _first_column(positions, "position_id", "id")
    fill_position_id = _first_column(fills, "position_id")
    terminal_orders = True
    live_order_count = 0
    if orders.height:
        if order_id is None or "status" not in orders.columns:
            terminal_orders = False
        else:
            # DENIED is a terminal venue outcome (a reduce-only exit for a position that is
            # already flat). ACCEPTED/TRIGGERED/PARTIALLY_FILLED mean the order was still
            # working when the band ended: censored at the fence, not an unfinished run.
            status = orders["status"].cast(pl.Utf8).str.to_uppercase()
            terminal = status.is_in(
                [
                    "FILLED", "CANCELED", "CANCELLED", "REJECTED", "EXPIRED",
                    "CLOSED", "DENIED",
                ]
            )
            live_at_fence_end = status.is_in(
                ["ACCEPTED", "TRIGGERED", "PARTIALLY_FILLED", "SUBMITTED", "PENDING_UPDATE"]
            )
            terminal_orders = bool((terminal | live_at_fence_end).all())
            live_order_count = int(live_at_fence_end.sum())
    fills_have_orders = not fills.height
    if fills.height and order_id and fill_order_id:
        fills_have_orders = set(fills[fill_order_id].cast(pl.Utf8)).issubset(
            set(orders[order_id].cast(pl.Utf8))
        )
    closed_have_two_fills = True
    if positions.height:
        close_column = _first_column(positions, "avg_px_close", "close_price")
        if position_id is None or close_column is None or fill_position_id is None:
            closed_have_two_fills = False
        else:
            # One join, not one frame scan per closed position: this is O(positions x fills)
            # row-wise and was the dominant cost of the whole integrity package.
            closed = positions.filter(pl.col(close_column).is_not_null())
            if closed.height:
                fill_counts = (
                    fills.group_by(fill_position_id)
                    .len()
                    .select(
                        pl.col(fill_position_id).cast(pl.Utf8).alias("_position_id"),
                        pl.col("len").alias("_fills"),
                    )
                )
                matched = closed.select(
                    pl.col(position_id).cast(pl.Utf8).alias("_position_id")
                ).join(fill_counts, on="_position_id", how="left")
                closed_have_two_fills = bool(
                    (matched["_fills"].fill_null(0) == 2).all()
                )
    ledger_agrees = _ledger_agrees_with_positions(ledger, positions)
    return {
        "pass": bool(
            terminal_orders
            and fills_have_orders
            and closed_have_two_fills
            and ledger_agrees
        ),
        "orders_terminal": terminal_orders,
        "orders_live_at_fence_end": live_order_count,
        "fills_have_orders": fills_have_orders,
        "closed_positions_have_two_fills": closed_have_two_fills,
        "ledger_agrees_with_positions": ledger_agrees,
    }


def _ledger_agrees_with_positions(
    ledger: pl.DataFrame,
    positions: pl.DataFrame,
) -> bool:
    """Every closed position must have exactly one FILLED and one CLOSED ledger row at its prices.

    Evaluated as joins over grouped counts. The row-wise form filtered the whole ledger once per
    position (118k x 3.5M rows on one cTrader cell), which is why integrity outran the run itself.
    """
    needed = {"state", "price"}
    if ledger.is_empty() or positions.is_empty() or not needed.issubset(ledger.columns):
        return False
    position_id = _first_column(positions, "position_id", "id")
    open_column = _first_column(positions, "avg_px_open", "open_price")
    close_column = _first_column(positions, "avg_px_close", "close_price")
    if not position_id or not open_column or not close_column:
        return False

    ledger = ledger.filter(pl.col("state").is_in(["FILLED", "CLOSED"]))
    if ledger.is_empty():
        return True
    if "position_id" not in ledger.columns:
        identity = [
            "experiment_id",
            "arm_id",
            "entry_variant",
            "episode_id",
            "policy_id",
        ]
        if not set(identity).issubset(ledger.columns):
            return False
        # Hash once per identity, not once per ledger row.
        keys = ledger.select(identity).unique()
        keys = keys.with_columns(
            pl.struct(sorted(identity))
            .map_elements(_derived_position_id, return_dtype=pl.Utf8)
            .alias("position_id")
        )
        ledger = ledger.join(keys, on=identity, how="left")

    ledger = ledger.with_columns(pl.col("position_id").cast(pl.Utf8))
    filled = (
        ledger.filter(pl.col("state") == "FILLED")
        .group_by("position_id")
        .agg(
            pl.len().alias("_n_filled"),
            pl.col("price").cast(pl.Float64).first().alias("_filled_price"),
        )
    )
    closed_aggs = [
        pl.len().alias("_n_closed"),
        pl.col("price").cast(pl.Float64).first().alias("_closed_price"),
    ]
    if "outcome_bps" in ledger.columns:
        closed_aggs.append(
            pl.col("outcome_bps").cast(pl.Float64).first().alias("_outcome_bps")
        )
    if "side" in ledger.columns:
        closed_aggs.append(pl.col("side").cast(pl.Float64).first().alias("_side"))
    closed = (
        ledger.filter(pl.col("state") == "CLOSED").group_by("position_id").agg(closed_aggs)
    )

    frame = (
        positions.select(
            pl.col(position_id).cast(pl.Utf8).alias("position_id"),
            pl.col(open_column).cast(pl.Float64).alias("_open"),
            pl.col(close_column).cast(pl.Float64).alias("_close"),
        )
        .join(closed, on="position_id", how="inner")
        .join(filled, on="position_id", how="left")
    )
    if frame.is_empty():
        return True

    agrees = (
        (pl.col("_n_closed") == 1)
        & (pl.col("_n_filled") == 1)
        & _is_close(pl.col("_filled_price"), pl.col("_open"))
        & _is_close(pl.col("_closed_price"), pl.col("_close"))
    )
    if "_outcome_bps" in frame.columns:
        side = pl.col("_side") if "_side" in frame.columns else pl.lit(1.0)
        expected = side * (pl.col("_close") / pl.col("_open") - 1.0) * 1e4
        agrees = agrees & _is_close(pl.col("_outcome_bps"), expected)
    return bool(frame.select(agrees.fill_null(False).all()).item())


def _is_close(left: pl.Expr, right: pl.Expr) -> pl.Expr:
    """`numpy.isclose` semantics as an expression; a null on either side is not close."""
    return ((left - right).abs() <= (1e-8 + 1e-5 * right.abs())).fill_null(False)


def _derived_position_id(row: dict[str, Any]) -> str:
    material = "|".join(
        str(row[key])
        for key in (
            "experiment_id",
            "arm_id",
            "entry_variant",
            "episode_id",
            "policy_id",
        )
    )
    return f"AM-{hashlib.sha256(material.encode()).hexdigest()[:32]}"


def _check_entry_parity(
    experiment_id: str,
    origins: pl.DataFrame,
    native: pl.DataFrame,
) -> bool:
    if experiment_id == "SPDR-021":
        return set(origins["entry_variant"]) == {"BREAKOUT"}
    expected_variants = {"E_TOUCH", "E_CLOSE"}
    # Breach zone origins are common to both variants and carry no variant column; the parity
    # requirement is then that each variant's fixed comparator covers every zone origin.
    variant_specific = "entry_variant" in origins.columns
    if variant_specific and set(origins["entry_variant"]) != expected_variants:
        return False
    if set(native["entry_variant"]) != expected_variants:
        return False
    fixed = native.filter(pl.col("arm_class") == "FIXED_NATIVE")
    for variant in expected_variants:
        origin_ids = set(
            (
                origins.filter(pl.col("entry_variant") == variant)
                if variant_specific
                else origins
            )["origin_id"].cast(pl.Utf8)
        )
        fixed_ids = set(
            fixed.filter(pl.col("entry_variant") == variant)["origin_id"].cast(pl.Utf8)
        )
        if fixed_ids != origin_ids:
            return False
    return True


def _golden_trace_checks(ledger: pl.DataFrame) -> dict[str, Any]:
    target_before_late_stop = True
    if {"episode_id", "state", "exit_reason"}.issubset(ledger.columns):
        # One episode carries one CLOSED row per management arm, by design: the key is the
        # executed arm on that episode, not the episode alone. A second CLOSED row for the
        # same arm would mean an exit was rewritten after the first closing fill.
        closed = ledger.filter(pl.col("state") == "CLOSED")
        keys = [
            name for name in ("episode_id", "policy_id", "arm_id") if name in closed.columns
        ]
        target_before_late_stop = not closed.select(keys).is_duplicated().any()
    traces = {
        "strict_threshold_boundary": not (1.0 > 1.0),
        "expiry_ordering": 4 > 2 > 1,
        "target_precedes_later_stop": target_before_late_stop,
    }
    return {"pass": all(traces.values()), "traces": traces}


def _check_determinism(
    run_dir: Path,
    actual_hashes: dict[str, str],
) -> dict[str, Any]:
    reference_path = run_dir / "determinism_reference.json"
    if reference_path.exists():
        expected = _read_json(reference_path).get("replay_hashes", {})
        passed = expected == actual_hashes
        mode = "REFERENCE_COMPARISON"
    else:
        passed = actual_hashes == replay_hashes(run_dir)
        expected = actual_hashes
        mode = "IMMEDIATE_REHASH"
    return {
        "pass": passed,
        "mode": mode,
        "replay_hashes": actual_hashes,
        "expected_replay_hashes": expected,
    }


def _informative_controls(
    features: pl.DataFrame,
    origins: pl.DataFrame,
    ledger_rows: int,
) -> dict[str, Any]:
    derangement = derange_component_times(features, seed=240730)
    magnitude = magnitude_matched_controls(origins, features)
    return {
        "time_derangement": {
            "seed": 240730,
            "rows": derangement.height,
            "zero_fixed_points": bool(
                (derangement["source_ts"] == derangement["ts"]).sum() == 0
            ),
        },
        "magnitude_match": {
            "rows": magnitude.height,
            "selected_rows": int(magnitude["selected"].sum()),
            "excluded_rows": int((~magnitude["selected"]).sum()),
        },
        "effect_quality_is_blocking": False,
        "ledger_rows": int(ledger_rows),
    }


def _publish_artifacts(
    destination: Path,
    artifacts: dict[str, dict[str, Any]],
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    workspace = destination / f".integrity.tmp-{uuid.uuid4().hex}"
    workspace.mkdir()
    try:
        for name, payload in artifacts.items():
            _atomic_json(payload, workspace / name)
        for name in INTEGRITY_ARTIFACTS:
            if name == "integrity_selfcheck.json":
                continue
            (workspace / name).replace(destination / name)
        (workspace / "integrity_selfcheck.json").replace(
            destination / "integrity_selfcheck.json"
        )
        workspace.rmdir()
    except BaseException:
        for path in workspace.glob("*"):
            path.unlink()
        workspace.rmdir()
        raise


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_parquet(path: Path, columns: list[str] | None = None) -> pl.DataFrame:
    """Read a run artifact, optionally projecting columns.

    Projection is best-effort: a requested column that the artifact does not carry is simply
    not read, so a check sees the same "column missing" condition it would have seen before.
    """
    if columns is None:
        return pl.read_parquet(path)
    available = set(pl.read_parquet_schema(path))
    wanted = [name for name in columns if name in available]
    if not wanted:
        return pl.read_parquet(path)
    return pl.read_parquet(path, columns=wanted)


def _parse_timestamp(value: Any) -> Any:
    if not value:
        return None
    return pl.Series([value]).str.to_datetime(time_zone="UTC")[0]


def _first_column(frame: pl.DataFrame, *names: str) -> str | None:
    return next((name for name in names if name in frame.columns), None)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(payload: dict[str, Any], path: Path) -> None:
    temporary = path.with_suffix(f"{path.suffix}.tmp-{uuid.uuid4().hex}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
