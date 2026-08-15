"""EXP-102 adapter: prior-raid count and later-swing outcome contrasts."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import polars as pl

from xen.liqswp_analysis.adapter import BaseContrastAdapter, make_fixture_frame
from xen.liqswp_analysis.contract import IntegrityStatus
from xen.liqswp_analysis.destroy import (
    DestroySpec,
    apply_destroy_mappings,
    build_destroy_mappings,
    derange_indices as _derange_indices,
)
from xen.liqswp_analysis.runtime import run_fixture as _run_fixture
from xen.liqswp_analysis.runtime import run_live
from xen.liqswp_analysis.source import validate_causal_order
from xen.liqswp_analysis.statistics import PopulationView

EXPERIMENT = "EXP-102"
LABEL_COLUMN = "count_band"
LENGTHS = (2, 5, 10)
SEEDS = tuple(range(5))
DEFAULT_N_BOOT = 10_000
DEFAULT_DESTROYS = 2_000
FIXTURE_N_BOOT = 10
TRAIN_START_NS = 1_622_592_060_000_000_000
TRAIN_END_NS = 1_700_611_200_000_000_000
PROJECT_ROOT = Path(__file__).resolve().parents[4]
AUTHORITATIVE_GATE = PROJECT_ROOT / "python/experiments/EXP-100/results/estimand_validation.json"
DEFAULT_SOURCE_ROOT = PROJECT_ROOT / "data/nautilus_runs/EXP-100/full"
REQUIRED_OUTCOME = (
    "swing_price",
    "swing_bps",
    "swing_atr",
    "swing_duration_ns",
    "duration_ns",
    "strong_move",
)
CONTROL_GROUP_COLUMNS = (
    "archive_symbol",
    "timeframe",
    "confirmation_method",
    "confirmation_reference",
    "side",
    "config",
    "status",
    "primary_completed",
)
CONTROL_NULL_COLUMNS = (
    "swing_price",
    "swing_bps",
    "swing_atr",
    "swing_duration_ns",
    "strong_move",
)


def derange_indices(n: int, seed: int) -> np.ndarray:
    return _derange_indices(n, np.random.default_rng(seed))


def classify_count_band(prior_raid_count: Any) -> str:
    """Return the frozen 0/1/2+ analysis band."""
    if isinstance(prior_raid_count, bool) or not isinstance(prior_raid_count, (int, np.integer)):
        raise ValueError("prior_raid_count must be a non-negative integer")
    count = int(prior_raid_count)
    if count < 0:
        raise ValueError("prior_raid_count must be a non-negative integer")
    if count == 0:
        return "0"
    if count == 1:
        return "1"
    return "2+"


def with_count_band(row: dict[str, Any]) -> dict[str, Any]:
    """Derive the analysis label without mutating the source row."""
    return {**row, LABEL_COLUMN: classify_count_band(row.get("prior_raid_count", 0))}


class Adapter(BaseContrastAdapter):
    experiment = EXPERIMENT
    label_column = LABEL_COLUMN
    contrasts = (("1", "0"), ("2+", "0"))
    control_group_columns = CONTROL_GROUP_COLUMNS
    control_null_columns = CONTROL_NULL_COLUMNS

    def fixture_frame(self) -> pl.DataFrame:
        rows = make_fixture_frame(("0", "1"), label_column=LABEL_COLUMN).to_dicts()
        for row in rows:
            band = int(row[LABEL_COLUMN])
            index = int(str(row["raid_id"]).rsplit("-", 1)[1])
            first_timestamp = 1_700_000_000_000_000_000 + index * 900_000_000_000
            row.update(
                prior_raid_count=band,
                level_id=f"FIXTURE-{band}-level-{index:04d}",
                first_raid_timestamp=first_timestamp,
                sweep_ts_ns=first_timestamp,
                return_ts_ns=first_timestamp + 1,
                confirmation_ts_ns=first_timestamp + 2,
                endpoint_ts_ns=first_timestamp + 3,
                swing_atr=(0.9 if index % 2 == 0 else 1.1) + 0.5 * band,
                swing_duration_ns=(
                    (3_000_000_000_000 if index % 2 == 0 else 4_200_000_000_000)
                    + 3_600_000_000_000 * band
                ),
                strong_move=index < (50 if band == 0 else 100),
                profile_generation="DEFINED",
            )
            row["duration_ns"] = row["swing_duration_ns"]
        permutation = np.random.default_rng(4).permutation(len(rows))
        permuted = [rows[int(index)] for index in permutation]
        for position, row in enumerate(permuted):
            row["raid_id"] = f"fixture-raid-{position:04d}"
        return pl.DataFrame(permuted).sort("first_raid_timestamp", "level_id")

    def prepare_frame(self, frame: pl.DataFrame) -> pl.DataFrame:
        integer_count = pl.col("prior_raid_count").cast(pl.Int64, strict=False)
        prepared = frame.with_columns(
            pl.when(integer_count == 0)
            .then(pl.lit("0"))
            .when(integer_count == 1)
            .then(pl.lit("1"))
            .when(integer_count >= 2)
            .then(pl.lit("2+"))
            .otherwise(pl.lit("__INVALID__"))
            .alias(LABEL_COLUMN)
        )
        cluster_columns = (*self.stratum_columns, "level_id")
        return (
            prepared.with_columns(
                pl.col("sweep_ts_ns").min().over(cluster_columns).alias("__first_raid_timestamp")
            )
            .sort((*self.stratum_columns, "__first_raid_timestamp", "level_id"))
            .drop("__first_raid_timestamp")
        )

    def _population_view(
        self,
        frame: pl.DataFrame,
        *,
        arm: Any,
        comparator: Any,
        channel: str,
    ) -> tuple[pl.DataFrame, PopulationView]:
        """Keep every count band in the registered destroy/bootstrap donor population."""
        population = self._channel_frame(frame, channel)
        stratum_id = "/".join(
            str(population[column][0]) if population.height else "EMPTY"
            for column in self.stratum_columns
        )
        return population, PopulationView(
            population_id=f"{EXPERIMENT}:{stratum_id}:{arm}-vs-{comparator}:{channel}",
            labels=population[LABEL_COLUMN].to_numpy(),
            arm=arm,
            comparator=comparator,
            cluster_ids=population["level_id"].to_numpy(),
            values=population[channel].cast(pl.Float64).to_numpy(),
        )

    def extra_integrity(self, frame: pl.DataFrame):
        reasons: list[str] = []
        evidence: dict[str, Any] = {}
        counts = frame["prior_raid_count"].to_list()
        invalid_counts = 0
        for count in counts:
            try:
                classify_count_band(count)
            except ValueError:
                invalid_counts += 1
        evidence["invalid_prior_raid_count_rows"] = invalid_counts
        if invalid_counts:
            reasons.append("VOID_PRIOR_RAID_COUNT")

        duplicate_raids = frame.select(pl.col("raid_id").is_duplicated().sum()).item()
        evidence["duplicate_raid_ids"] = int(duplicate_raids)
        if duplicate_raids:
            reasons.append("VOID_DUPLICATE_RAID_ID")

        is_fixture = "fixture" in frame.columns and frame["fixture"].fill_null(False).all()
        if not is_fixture:
            timestamp_columns = (
                "sweep_ts_ns",
                "return_ts_ns",
                "confirmation_ts_ns",
                "endpoint_ts_ns",
            )
            before_train = 0
            after_train = 0
            for column in timestamp_columns:
                before_train += frame.filter(
                    pl.col(column).is_not_null() & (pl.col(column) < TRAIN_START_NS)
                ).height
                after_train += frame.filter(
                    pl.col(column).is_not_null() & (pl.col(column) > TRAIN_END_NS)
                ).height
            evidence.update(before_train_rows=before_train, after_train_rows=after_train)
            if before_train:
                reasons.append("VOID_BEFORE_TRAIN")
            if after_train:
                reasons.append("VOID_AFTER_TRAIN")
            causal = validate_causal_order(
                frame,
                (
                    ("sweep_ts_ns", "return_ts_ns"),
                    ("return_ts_ns", "confirmation_ts_ns"),
                    ("sweep_ts_ns", "confirmation_ts_ns"),
                    ("confirmation_ts_ns", "endpoint_ts_ns"),
                ),
            )
            evidence["causal_failures"] = causal
            if causal:
                reasons.append("VOID_CAUSAL_ORDER")

            sequence_failures = 0
            for group in frame.partition_by(
                [*self.stratum_columns, "level_id"], maintain_order=True
            ):
                ordered = group.sort("sweep_ts_ns")["prior_raid_count"].to_list()
                if ordered != list(range(len(ordered))):
                    sequence_failures += 1
            evidence["level_count_sequence_failures"] = sequence_failures
            if sequence_failures:
                reasons.append("VOID_LEVEL_COUNT_SEQUENCE")

        unique_reasons = tuple(dict.fromkeys(reasons))
        return IntegrityStatus(not unique_reasons, unique_reasons, evidence)

    def census(self, frame: pl.DataFrame) -> dict[str, Any]:
        prepared = self.prepare_frame(frame)
        census = super().census(prepared)
        census["count_band"] = dict(
            Counter(str(value) for value in prepared[LABEL_COLUMN].to_list())
        )
        census["exact_prior_raid_count"] = dict(
            Counter(str(value) for value in prepared["prior_raid_count"].to_list())
        )
        census["censor_status"] = dict(
            Counter(str(value) for value in prepared["status"].to_list())
        )
        return census


def _fixture_rows() -> list[dict[str, Any]]:
    return Adapter(n_boot=40, n_destroy=20, seeds=(0, 1)).fixture_frame().to_dicts()


def future_destroy(
    rows: Sequence[dict[str, Any]], label: str, seed: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    frame = pl.DataFrame(rows)
    columns = {
        column: frame[column].to_numpy()
        for column in (*CONTROL_GROUP_COLUMNS, *CONTROL_NULL_COLUMNS)
    }
    mappings = build_destroy_mappings(
        columns,
        DestroySpec(CONTROL_GROUP_COLUMNS, CONTROL_NULL_COLUMNS, CONTROL_NULL_COLUMNS),
        seeds=(seed,),
        population_id=f"fixture:{label}",
    )
    destroyed = [dict(row) for row in rows]
    for channel in CONTROL_NULL_COLUMNS:
        moved = apply_destroy_mappings(frame[channel].to_numpy(), mappings)[0]
        for index, value in enumerate(moved.tolist()):
            destroyed[index][channel] = value
    return destroyed, {
        "fixed_points": mappings.fixed_points,
        "mapped_rows": mappings.moved_rows,
        "reasons": list(mappings.reasons),
    }


def run_fixture(
    *,
    n_destroy: int = DEFAULT_DESTROYS,
    seeds: Sequence[int] = SEEDS,
    output: Path | None = None,
    n_boot: int = FIXTURE_N_BOOT,
) -> dict[str, Any]:
    destination = output or Path(__file__).resolve().parents[1] / "results/fixture_integrity.json"
    return _run_fixture(Adapter(n_boot=n_boot, n_destroy=n_destroy, seeds=seeds), destination)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fixture", "--fixture-only", "--smoke", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--source-root", "--root", type=Path)
    parser.add_argument("--gate", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    experiment_root = Path(__file__).resolve().parents[1]
    if args.live:
        fixture_payload = _run_fixture(
            Adapter(n_boot=FIXTURE_N_BOOT, n_destroy=DEFAULT_DESTROYS, seeds=SEEDS),
            experiment_root / "results/fixture_integrity.json",
        )
        if not fixture_payload["integrity"]["blocking_pass"]:
            raise RuntimeError("EXP-102 fixture integrity failed; live source was not opened")
        adapter = Adapter(
            n_boot=DEFAULT_N_BOOT,
            n_destroy=DEFAULT_DESTROYS,
            seeds=SEEDS,
        )
        source = args.source_root or DEFAULT_SOURCE_ROOT
        gate = args.gate or AUTHORITATIVE_GATE
        run_live(
            adapter, source, gate, args.output or experiment_root / "results/analysis_results.json"
        )
    else:
        _run_fixture(
            Adapter(n_boot=FIXTURE_N_BOOT, n_destroy=DEFAULT_DESTROYS, seeds=SEEDS),
            args.output or experiment_root / "results/fixture_integrity.json",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
