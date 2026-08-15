"""Reusable contrast-adapter mechanics; experiment definitions stay in their entry points."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys
from typing import Any, Hashable, Sequence

import numpy as np
import polars as pl

from xen.liqswp_analysis.contract import IntegrityStatus
from xen.liqswp_analysis.destroy import (
    DestroySpec,
    future_destroy_attestation,
    stream_destroy_control,
)
from xen.liqswp_analysis.source import SourceSpec, scan_train_columns, validate_source_contract
from xen.liqswp_analysis.statistics import (
    PopulationView,
    block_sensitivity,
    clustered_contrast_bootstrap,
)

PROJECT_ROOT = Path(__file__).resolve().parents[4]
TRAIN_END_NS = 1_700_611_200 * 1_000_000_000
CHANNELS = (
    "swing_price",
    "swing_bps",
    "swing_atr",
    "swing_duration_ns",
    "strong_move",
)
NULL_COLUMNS = CHANNELS
BASE_COLUMNS = (
    "raid_id",
    "level_id",
    "source_configuration",
    "archive_symbol",
    "timeframe",
    "config",
    "side",
    "sweep_ts_ns",
    "return_ts_ns",
    "confirmation_ts_ns",
    "endpoint_ts_ns",
    "confirmation_method",
    "confirmation_reference",
    "primary_attribution",
    "primary_completed",
    "status",
    "prior_raid_count",
    "profile_generation",
    "profile_undefined_reason",
    "raid_regime",
    "confirmation_regime",
    "endpoint_regime",
    "duration_ns",
    *CHANNELS,
)


def _finite(value: Any) -> bool:
    if value is None:
        return False
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def _jsonable_key(value: Hashable) -> str:
    return str(value).lower() if isinstance(value, bool) else str(value)


def make_fixture_frame(labels: Sequence[Hashable], *, label_column: str) -> pl.DataFrame:
    """Create a deterministic multi-cluster fixture with literal arm effects."""
    rows: list[dict[str, Any]] = []
    for label_index, label in enumerate(labels):
        for index in range(200):
            base = float(index % 11) / 100.0
            offset = float(label_index) * 0.5
            strong_fraction = min(0.15 + 0.05 * label_index, 0.85)
            row = {
                "raid_id": f"R-{label_index}-{index}",
                "level_id": f"L-{label_index}-{index}",
                "source_configuration": "FIXTURE_CONFIG",
                "archive_symbol": "EURUSD",
                "timeframe": "15m",
                "config": "FIXTURE_CONFIG",
                "side": "HIGH",
                "sweep_ts_ns": 100 + index * 10,
                "return_ts_ns": 110 + index * 10,
                "confirmation_ts_ns": 120 + index * 10,
                "endpoint_ts_ns": 130 + index * 10,
                "confirmation_method": "BREAKOUT_BAR",
                "confirmation_reference": "1H",
                "primary_attribution": True,
                "primary_completed": True,
                "status": "COMPLETED",
                "prior_raid_count": label_index,
                "profile_undefined_reason": None,
                "raid_regime": label if label in {"LOW", "MID", "HIGH"} else "MID",
                "confirmation_regime": "MID",
                "endpoint_regime": "MID",
                "duration_ns": 3_600_000_000_000 + offset * 1_000_000_000,
                "swing_price": 100.0 + base + offset,
                "swing_bps": 10.0 + base + offset,
                "swing_atr": 1.0 + base + offset,
                "swing_duration_ns": 3_600_000_000_000 + offset * 1_000_000_000,
                "strong_move": index < int(200 * strong_fraction),
                "fixture": True,
                label_column: label,
            }
            rows.append(row)
    return pl.DataFrame(rows)


class BaseContrastAdapter:
    """Shared integrity/statistics flow for one explicit experiment adapter."""

    experiment = ""
    label_column = ""
    contrasts: tuple[tuple[Hashable, Hashable], ...] = ()
    channels: tuple[str, ...] = CHANNELS
    control_channels: tuple[str, ...] = (
        "swing_atr",
        "swing_duration_ns",
        "strong_move",
    )
    control_group_columns: tuple[str, ...] = ()
    control_null_columns: tuple[str, ...] = NULL_COLUMNS
    required_columns: tuple[str, ...] = BASE_COLUMNS
    stratum_columns: tuple[str, ...] = (
        "archive_symbol",
        "timeframe",
        "confirmation_method",
        "confirmation_reference",
        "side",
        "config",
    )

    def __init__(
        self,
        *,
        n_boot: int = 10_000,
        n_destroy: int = 2_000,
        seeds: Sequence[int] = tuple(range(5)),
    ) -> None:
        self.n_boot = int(n_boot)
        self.n_destroy = int(n_destroy)
        self.seeds = tuple(int(seed) for seed in seeds)
        self._control_records: list[dict[str, Any]] = []
        self._extra_integrity_evidence: dict[str, Any] = {}
        self._control_status: dict[tuple[Any, ...], bool] = {}
        self._live_mode = False

    def fixture_frame(self) -> pl.DataFrame:
        raise NotImplementedError

    def prepare_frame(self, frame: pl.DataFrame) -> pl.DataFrame:
        return frame

    def extra_integrity(self, frame: pl.DataFrame) -> IntegrityStatus:
        return IntegrityStatus(True)

    def source_spec(self, source_root: Path, gate_path: Path) -> SourceSpec:
        return SourceSpec(
            root=source_root,
            family_gate=gate_path,
            cell_gate_dir=PROJECT_ROOT / "python/experiments/EXP-100/results/execution/full",
            expected_cells=264,
            table="raids.parquet",
            required_columns=self.required_columns,
            object_id_column="raid_id",
            train_end_column="endpoint_ts_ns",
            train_end_ns=TRAIN_END_NS,
        )

    def live_frame(
        self, source_root: Path, gate_path: Path
    ) -> tuple[pl.DataFrame, dict[str, Any], IntegrityStatus]:
        self._live_mode = True
        attestation = validate_source_contract(self.source_spec(source_root, gate_path))
        source = {
            "mode": "live",
            "root": str(source_root),
            "gate": str(gate_path),
            "attestation": attestation.evidence,
        }
        if not attestation.integrity.blocking_pass:
            return pl.DataFrame(), source, attestation.integrity
        lazy = scan_train_columns(
            attestation.paths,
            columns=self.required_columns,
            train_end_column="endpoint_ts_ns",
            train_end_ns=TRAIN_END_NS,
        )
        frame = lazy.collect(engine="streaming")
        return self.prepare_frame(frame), source, attestation.integrity

    def _channel_frame(self, frame: pl.DataFrame, channel: str) -> pl.DataFrame:
        eligible = frame.filter(
            (pl.col("status") == "COMPLETED")
            & pl.col("primary_attribution").fill_null(False)
            & pl.col("primary_completed").fill_null(False)
        )
        if channel in {"swing_atr", "strong_move"}:
            eligible = eligible.filter(
                pl.col("profile_undefined_reason").fill_null("") != "ATR_UNDEFINED"
            )
        return eligible

    def _progress(self, phase: str, stratum: dict[str, Any], arm: Hashable, channel: str) -> None:
        if self._live_mode:
            identity = "/".join(str(stratum[column]) for column in self.stratum_columns)
            print(
                f"{self.experiment} {phase}: {identity} {arm} {channel}",
                file=sys.stderr,
                flush=True,
            )

    def _population_view(
        self,
        frame: pl.DataFrame,
        *,
        arm: Hashable,
        comparator: Hashable,
        channel: str,
    ) -> tuple[pl.DataFrame, PopulationView]:
        population = self._channel_frame(frame, channel).filter(
            pl.col(self.label_column).is_in([arm, comparator])
        )
        values = population[channel].cast(pl.Float64).to_numpy()
        stratum_id = "/".join(
            str(population[column][0]) if population.height else "EMPTY"
            for column in self.stratum_columns
        )
        view = PopulationView(
            population_id=(
                f"{self.experiment}:{stratum_id}:{_jsonable_key(arm)}-vs-"
                f"{_jsonable_key(comparator)}:{channel}"
            ),
            labels=population[self.label_column].to_numpy(),
            arm=arm,
            comparator=comparator,
            cluster_ids=population["level_id"].to_numpy(),
            values=values,
        )
        return population, view

    def _strata(self, frame: pl.DataFrame) -> tuple[tuple[dict[str, Any], pl.DataFrame], ...]:
        if frame.is_empty():
            return ()
        partitions = frame.partition_by(
            list(self.stratum_columns), maintain_order=True, as_dict=True
        )
        rows: list[tuple[dict[str, Any], pl.DataFrame]] = []
        for raw_key, partition in partitions.items():
            key = raw_key if isinstance(raw_key, tuple) else (raw_key,)
            rows.append((dict(zip(self.stratum_columns, key, strict=True)), partition))
        return tuple(rows)

    def integrity(self, frame: pl.DataFrame) -> IntegrityStatus:
        frame = self.prepare_frame(frame)
        extra_status = self.extra_integrity(frame)
        reasons = list(extra_status.reasons)
        common_evidence: dict[str, Any] = {}
        if {"duration_ns", "swing_duration_ns"} <= set(frame.columns):
            duration_mismatches = frame.filter(
                pl.col("duration_ns").is_not_null()
                & pl.col("swing_duration_ns").is_not_null()
                & (pl.col("duration_ns") != pl.col("swing_duration_ns"))
            ).height
            common_evidence["duration_alias_mismatches"] = duration_mismatches
            if duration_mismatches:
                reasons.append("VOID_DURATION_ALIAS")
        control_records: list[dict[str, Any]] = []
        control_status: dict[tuple[Any, ...], bool] = {}
        destroy_seeds = tuple(range(self.n_destroy))
        for stratum, stratum_frame in self._strata(frame):
            for arm, comparator in self.contrasts:
                for channel in self.control_channels:
                    self._progress("integrity", stratum, arm, channel)
                    population, view = self._population_view(
                        stratum_frame, arm=arm, comparator=comparator, channel=channel
                    )
                    columns = {
                        column: population[column].to_numpy()
                        for column in set(
                            (*self.control_group_columns, *self.control_null_columns, channel)
                        )
                    }
                    destroy_run = stream_destroy_control(
                        view,
                        columns,
                        DestroySpec(
                            self.control_group_columns,
                            self.control_null_columns,
                            (channel,),
                        ),
                        seeds=destroy_seeds,
                        batch_size=8,
                    )
                    mappings = destroy_run.summary
                    raw_boot = clustered_contrast_bootstrap(
                        view, block_length=5, n_boot=self.n_boot, seeds=self.seeds
                    )
                    destroyed_average_view = PopulationView(
                        population_id=view.population_id,
                        labels=view.labels,
                        arm=view.arm,
                        comparator=view.comparator,
                        cluster_ids=view.cluster_ids,
                        values=destroy_run.average_values,
                    )
                    destroyed_boot = clustered_contrast_bootstrap(
                        destroyed_average_view,
                        block_length=5,
                        n_boot=self.n_boot,
                        seeds=self.seeds,
                    )
                    destroyed_mapping_se = (
                        float(np.std(destroy_run.estimates, ddof=1))
                        / np.sqrt(len(destroy_run.estimates))
                        if len(destroy_run.estimates) > 1
                        else float("nan")
                    )
                    destroyed_data_se = float(destroyed_boot.get("bootstrap_se", float("nan")))
                    destroyed_outer_se = (
                        float(np.hypot(destroyed_data_se, destroyed_mapping_se))
                        if np.isfinite(destroyed_data_se) and np.isfinite(destroyed_mapping_se)
                        else float("nan")
                    )
                    status = future_destroy_attestation(
                        view,
                        mappings,
                        se_population_id=destroyed_average_view.population_id,
                        raw_bootstrap_se=float(raw_boot.get("bootstrap_se", float("nan"))),
                        destroyed_estimates=destroy_run.estimates,
                        destroyed_bootstrap_se=destroyed_outer_se,
                    )
                    status_key = (
                        *(stratum[column] for column in self.stratum_columns),
                        arm,
                        comparator,
                        channel,
                    )
                    control_status[status_key] = status.blocking_pass
                    record = {
                        "stratum": stratum,
                        "arm": arm,
                        "comparator": comparator,
                        "channel": channel,
                        "blocking_pass": status.blocking_pass,
                        "reasons": list(status.reasons),
                        **status.evidence,
                        "population_match": len(
                            {
                                view.population_id,
                                mappings.population_id,
                                destroyed_average_view.population_id,
                            }
                        )
                        == 1,
                        "max_materialized_mappings": destroy_run.max_materialized_mappings,
                        "destroyed_mapping_monte_carlo_se": destroyed_mapping_se,
                        "destroyed_data_bootstrap_se": destroyed_data_se,
                    }
                    control_records.append(record)
        self._control_records = control_records
        self._control_status = control_status
        self._extra_integrity_evidence = dict(extra_status.evidence)
        if not control_records or not any(control_status.values()):
            reasons.append("VOID_NO_VALID_POPULATION")
        unique_reasons = tuple(dict.fromkeys(reasons))
        return IntegrityStatus(
            blocking_pass=not unique_reasons,
            reasons=unique_reasons,
            evidence={
                "controls": control_records,
                "experiment": dict(extra_status.evidence),
                "common": common_evidence,
            },
        )

    def analyze(self, frame: pl.DataFrame) -> tuple[dict[str, Any], ...]:
        frame = self.prepare_frame(frame)
        rows: list[dict[str, Any]] = []
        for stratum, stratum_frame in self._strata(frame):
            for arm, comparator in self.contrasts:
                for channel in self.channels:
                    self._progress("analysis", stratum, arm, channel)
                    status_key = (
                        *(stratum[column] for column in self.stratum_columns),
                        arm,
                        comparator,
                        channel,
                    )
                    if (
                        channel in self.control_channels
                        and self._control_status
                        and not self._control_status.get(status_key, False)
                    ):
                        continue
                    _, view = self._population_view(
                        stratum_frame, arm=arm, comparator=comparator, channel=channel
                    )
                    sensitivities = block_sensitivity(
                        view,
                        lengths=(2, 5, 10),
                        n_boot=self.n_boot,
                        seeds=self.seeds,
                    )
                    values = np.asarray(view.values, dtype=float)
                    arm_values = values[(view.labels == arm) & np.isfinite(values)]
                    comparator_values = values[(view.labels == comparator) & np.isfinite(values)]
                    medians = {
                        "arm": float(np.median(arm_values)) if arm_values.size else None,
                        "comparator": (
                            float(np.median(comparator_values)) if comparator_values.size else None
                        ),
                        "contrast": (
                            float(np.median(arm_values) - np.median(comparator_values))
                            if arm_values.size and comparator_values.size
                            else None
                        ),
                    }
                    rows.append(
                        {
                            "population_id": view.population_id,
                            "stratum": stratum,
                            "arm": arm,
                            "comparator": comparator,
                            "channel": channel,
                            "observed": sensitivities["5"],
                            "medians": medians,
                            "ideal": "direct arm-minus-fixed-comparator estimate with uncertainty",
                            "interpretation": "operator judges; no machine value label",
                            "sensitivities": sensitivities,
                        }
                    )
        return tuple(rows)

    def population(self, frame: pl.DataFrame) -> dict[str, Any]:
        prepared = self.prepare_frame(frame)
        return {
            "rows": prepared.height,
            "labels": {
                str(row[self.label_column]): int(row["len"])
                for row in prepared.group_by(self.label_column).len().to_dicts()
            },
        }

    def census(self, frame: pl.DataFrame) -> dict[str, Any]:
        prepared = self.prepare_frame(frame)
        status = Counter(str(value) for value in prepared["status"].to_list())
        missing = {channel: int(prepared[channel].null_count()) for channel in self.channels}
        by_stratum_arm = []
        grouping = (*self.stratum_columns, self.label_column)
        for group in prepared.partition_by(list(grouping), maintain_order=True):
            identity = {column: group[column][0] for column in grouping}
            by_stratum_arm.append(
                {
                    **identity,
                    "rows": group.height,
                    "status": dict(Counter(str(value) for value in group["status"].to_list())),
                    "missingness": {
                        channel: int(group[channel].null_count()) for channel in self.channels
                    },
                    "atr_undefined": group.filter(
                        pl.col("profile_undefined_reason").fill_null("") == "ATR_UNDEFINED"
                    ).height,
                }
            )
        return {
            "status": dict(status),
            "missingness": missing,
            "by_stratum_arm": by_stratum_arm,
        }

    def extra(self, frame: pl.DataFrame) -> dict[str, Any]:
        controls = self._control_records
        summary = {
            "fixed_points": sum(int(row["fixed_points"]) for row in controls),
            "population_match": all(bool(row["population_match"]) for row in controls),
            "records": controls,
        }
        return {
            "control": summary,
            "void_populations": [row for row in controls if not bool(row.get("blocking_pass"))],
            "census": self.census(frame),
            "integrity_evidence": dict(self._extra_integrity_evidence),
        }
