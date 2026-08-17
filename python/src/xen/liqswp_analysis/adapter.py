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
    draw_destroy_contrasts,
    future_destroy_attestation,
    nested_destroy_bootstrap,
)
from xen.liqswp_analysis.source import SourceSpec, scan_train_columns, validate_source_contract
from xen.liqswp_analysis.statistics import (
    PopulationView,
    block_sensitivity,
    clustered_contrast_bootstrap,
)

PROJECT_ROOT = Path(__file__).resolve().parents[4]
TRAIN_END_NS = 1_700_611_200 * 1_000_000_000
TRAIN_END_UTC = "2023-11-22T00:00:00Z"
CHANNELS = (
    "swing_price",
    "swing_bps",
    "swing_atr",
    "swing_duration_ns",
    "strong_move",
)
# Registered 5-bit nullness class: duration_ns is the declared alias of
# swing_duration_ns (asserted byte-equal before grouping).
CONTROL_NULL_COLUMNS = (
    "swing_price",
    "swing_bps",
    "swing_atr",
    "duration_ns",
    "strong_move",
)
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
    *CHANNELS,
    "duration_ns",
)

FIXTURE_ROWS_PER_ARM = 200
FIXTURE_TIMESTAMP_BASE = 1_700_000_000_000_000_000
FIXTURE_TIMESTAMP_STEP = 900_000_000_000
FIXTURE_PERMUTATION_SEED = 4


def _finite(value: Any) -> bool:
    if value is None:
        return False
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def _jsonable_key(value: Hashable) -> str:
    return str(value).lower() if isinstance(value, bool) else str(value)


def make_fixture_frame(
    pairs: Sequence[tuple[Hashable, Hashable]],
    *,
    label_column: str,
    rows_per_arm: int = FIXTURE_ROWS_PER_ARM,
    config_value: Hashable | None = "FIXTURE_CONFIG",
) -> pl.DataFrame:
    """Build the registered two-arm pre-read fixture with the explicit plants.

    Each (baseline, arm) pair contributes `rows_per_arm` rows per arm. The
    registered FIXTURE-TOPOLOGY and tripwire plants are applied exactly:

      swing_atr:        baseline 0.90/1.10 alternating, arm 1.40/1.60 (+0.50)
      swing_duration_ns: baseline 3e12/4.2e12, arm 6.6e12/7.8e12 (+3.6e12 ns)
      strong_move:      baseline true at 1/4 of positions, arm at 1/2 (+0.25)

    level_id=FIXTURE-{arm}-level-{i:04d};
    first_raid_timestamp=1_700_000_000_000_000_000 + i*900_000_000_000;
    deterministic row permutation seed=4, then raid_id=fixture-raid-{position:04d};
    ordering is (first_raid_timestamp, level_id); no source row is read. All
    status/nullness/fixed fields are identical except the declared arm label and
    the planted outcome values; there are no nulls.
    """
    rows: list[dict[str, Any]] = []
    for baseline_label, arm_label in pairs:
        for arm_index, (label, arm_flag) in enumerate(
            ((baseline_label, False), (arm_label, True))
        ):
            for index in range(int(rows_per_arm)):
                even = index % 2 == 0
                first_raid_timestamp = FIXTURE_TIMESTAMP_BASE + index * FIXTURE_TIMESTAMP_STEP
                if arm_flag:
                    swing_atr = 1.40 if even else 1.60
                    duration = 6_600_000_000_000 if even else 7_800_000_000_000
                    strong = index < int(rows_per_arm / 2)
                else:
                    swing_atr = 0.90 if even else 1.10
                    duration = 3_000_000_000_000 if even else 4_200_000_000_000
                    strong = index < int(rows_per_arm / 4)
                rows.append(
                    {
                        "raid_id": "",  # assigned after the deterministic permutation
                        "level_id": f"FIXTURE-{label}-level-{index:04d}",
                        "source_configuration": "FIXTURE_CONFIG",
                        "archive_symbol": "EURUSD",
                        "timeframe": "15m",
                        "config": label if config_value is None else config_value,
                        "side": "HIGH",
                        "sweep_ts_ns": first_raid_timestamp,
                        "return_ts_ns": first_raid_timestamp + 1,
                        "confirmation_ts_ns": first_raid_timestamp + 2,
                        "endpoint_ts_ns": first_raid_timestamp + 3,
                        "confirmation_method": "BREAKOUT_BAR",
                        "confirmation_reference": "1H",
                        "primary_attribution": True,
                        "primary_completed": True,
                        "status": "COMPLETED",
                        "prior_raid_count": 0,
                        "profile_undefined_reason": None,
                        "raid_regime": "MID",
                        "confirmation_regime": "MID",
                        "endpoint_regime": "MID",
                        "swing_price": 100.0 + (0.5 if arm_flag else 0.0),
                        "swing_bps": 10.0 + (0.5 if arm_flag else 0.0),
                        "swing_atr": swing_atr,
                        "swing_duration_ns": duration,
                        "duration_ns": duration,
                        "strong_move": strong,
                        "fixture": True,
                        label_column: label,
                    }
                )
    permutation = np.random.default_rng(FIXTURE_PERMUTATION_SEED).permutation(len(rows))
    permuted = [rows[int(index)] for index in permutation]
    for position, row in enumerate(permuted):
        row["raid_id"] = f"fixture-raid-{position:04d}"
    return pl.DataFrame(permuted).sort(
        pl.col("sweep_ts_ns"),
        pl.col("level_id"),
    )


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
    control_null_columns: tuple[str, ...] = CONTROL_NULL_COLUMNS
    required_columns: tuple[str, ...] = BASE_COLUMNS
    stratum_columns: tuple[str, ...] = (
        "archive_symbol",
        "timeframe",
        "confirmation_method",
        "confirmation_reference",
        "side",
        "config",
    )
    # EXP-101 uses independent arm resampling; EXP-102/103/104 use joint
    independent_arms: bool = False
    # primary block length for the nested outer bootstrap (the §4 default)
    nested_block_length: int = 5

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
            train_end_utc=TRAIN_END_UTC,
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
        # Registered §4 ordering: clusters are complete level_id histories sorted
        # by (first_raid_timestamp, level_id); rows keep their order within a
        # selected cluster.
        population = population.sort(
            pl.col("sweep_ts_ns").min().over("level_id"),
            "level_id",
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

        # Duration alias nullness/value mismatch check (asserted alias).
        if {"duration_ns", "swing_duration_ns"} <= set(frame.columns):
            duration_null_xor = frame.filter(
                (pl.col("duration_ns").is_null() != pl.col("swing_duration_ns").is_null())
            ).height
            common_evidence["duration_alias_nullness_mismatch"] = duration_null_xor
            if duration_null_xor:
                reasons.append("VOID_DURATION_ALIAS_NULLNESS_MISMATCH")
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

        for stratum, stratum_frame in self._strata(frame):
            for arm, comparator in self.contrasts:
                for channel in self.control_channels:
                    self._progress("integrity", stratum, arm, channel)
                    donor_population = self._channel_frame(stratum_frame, channel)
                    population, view = self._population_view(
                        stratum_frame, arm=arm, comparator=comparator, channel=channel
                    )
                    spec = DestroySpec(
                        self.control_group_columns,
                        self.control_null_columns,
                        (channel,),
                    )
                    donor_columns = {
                        column: donor_population[column].to_numpy()
                        for column in set(
                            (*self.control_group_columns, *self.control_null_columns, channel)
                        )
                    }
                    donor_labels = donor_population[self.label_column].to_numpy()
                    donor_run = draw_destroy_contrasts(
                        f"{view.population_id}|donor",
                        donor_columns,
                        donor_labels,
                        arm=arm,
                        comparator=comparator,
                        channel=channel,
                        spec=spec,
                        n_destroy=self.n_destroy,
                        batch_size=8,
                    )
                    view_columns = {
                        column: population[column].to_numpy()
                        for column in set(
                            (*self.control_group_columns, *self.control_null_columns, channel)
                        )
                    }
                    nested = nested_destroy_bootstrap(
                        view,
                        view_columns,
                        spec,
                        channel=channel,
                        outer_seeds=self.seeds,
                        n_boot=self.n_boot,
                        block_length=self.nested_block_length,
                        n_destroy=self.n_destroy,
                        independent_arms=self.independent_arms,
                    )
                    status = future_destroy_attestation(
                        view,
                        donor_run=donor_run,
                        nested=nested,
                    )
                    status_key = (
                        *(stratum[column] for column in self.stratum_columns),
                        arm,
                        comparator,
                        channel,
                    )
                    control_status[status_key] = status.blocking_pass

                    raw_boot = clustered_contrast_bootstrap(
                        view,
                        block_length=self.nested_block_length,
                        n_boot=self.n_boot,
                        seeds=self.seeds,
                        independent_arms=self.independent_arms,
                    )
                    donor_contrast_rows = donor_population.filter(
                        pl.col(self.label_column).is_in([arm, comparator])
                    ).height
                    record = {
                        "stratum": stratum,
                        "arm": arm,
                        "comparator": comparator,
                        "channel": channel,
                        "blocking_pass": status.blocking_pass,
                        "reasons": list(status.reasons),
                        **status.evidence,
                        "population_match": population.height == donor_contrast_rows,
                        "raw_bootstrap_interval": raw_boot.get("interval"),
                        "raw_bootstrap_seed_rows": raw_boot.get("seeds"),
                    }
                    control_records.append(record)

        self._control_records = control_records
        self._control_status = control_status
        self._extra_integrity_evidence = dict(extra_status.evidence)

        # Failed-control propagation: individual failed controls enter overall reasons
        failed_control_reasons = set()
        for record in control_records:
            if not record["blocking_pass"]:
                failed_control_reasons.update(record["reasons"])
        reasons.extend(failed_control_reasons)

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
                        independent_arms=self.independent_arms,
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
                    source_fields: dict[str, dict[str, Any]] = {}
                    for source_channel in ("swing_price", "swing_bps"):
                        source_view = self._population_view(
                            stratum_frame,
                            arm=arm,
                            comparator=comparator,
                            channel=source_channel,
                        )[1]
                        source_values = np.asarray(source_view.values, dtype=float)
                        arm_source = source_values[
                            (source_view.labels == arm) & np.isfinite(source_values)
                        ]
                        comparator_source = source_values[
                            (source_view.labels == comparator) & np.isfinite(source_values)
                        ]
                        source_fields[source_channel] = {
                            "arm": {
                                "n": int(arm_source.size),
                                "non_null": int(arm_source.size),
                                "mean": float(arm_source.mean()) if arm_source.size else None,
                                "median": (
                                    float(np.median(arm_source)) if arm_source.size else None
                                ),
                            },
                            "comparator": {
                                "n": int(comparator_source.size),
                                "non_null": int(comparator_source.size),
                                "mean": (
                                    float(comparator_source.mean())
                                    if comparator_source.size
                                    else None
                                ),
                                "median": (
                                    float(np.median(comparator_source))
                                    if comparator_source.size
                                    else None
                                ),
                            },
                        }
                    rows.append(
                        {
                            "population_id": view.population_id,
                            "stratum": stratum,
                            "arm": arm,
                            "comparator": comparator,
                            "channel": channel,
                            "observed": sensitivities["5"],
                            "observed_L2": sensitivities["2"],
                            "observed_L5": sensitivities["5"],
                            "observed_L10": sensitivities["10"],
                            "medians": medians,
                            "source_field_summaries": source_fields,
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
