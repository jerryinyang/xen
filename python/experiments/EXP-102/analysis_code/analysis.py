"""EXP-102 adapter: prior-raid count and later-swing outcome contrasts."""

from __future__ import annotations

import argparse
import os
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
# 5 bits: duration_ns is the declared alias of swing_duration_ns (not duplicated)
CONTROL_NULL_COLUMNS = (
    "swing_price",
    "swing_bps",
    "swing_atr",
    "duration_ns",
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
    # EXP-102: joint resampling (default independent_arms=False)

    def fixture_frame(self) -> pl.DataFrame:
        return make_fixture_frame(
            (("0", "1"),),
            label_column=LABEL_COLUMN,
            config_value="FIXTURE_CONFIG",
        ).with_columns(pl.col(LABEL_COLUMN).cast(pl.Int64).alias("prior_raid_count"))

    def prepare_frame(self, frame: pl.DataFrame) -> pl.DataFrame:
        frame = super().prepare_frame(frame)
        # Fail-closed: the registered design declares no coercion rules for
        # prior_raid_count, so any malformed value aborts rather than being
        # silently mapped to an analysis band.
        bands: list[str] = []
        for value in frame["prior_raid_count"].to_list():
            try:
                bands.append(classify_count_band(value))
            except ValueError as error:
                raise ValueError(
                    "prior_raid_count must be a non-negative integer; "
                    f"got {value!r} (fail-closed: no coercion rules are declared)"
                ) from error
        prepared = frame.with_columns(pl.Series(LABEL_COLUMN, bands))
        cluster_columns = (*self.stratum_columns, "level_id")
        return (
            prepared.with_columns(
                pl.col("sweep_ts_ns").min().over(cluster_columns).alias("__first_raid_timestamp")
            )
            .sort((*self.stratum_columns, "__first_raid_timestamp", "level_id"))
            .drop("__first_raid_timestamp")
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

        # Raid identity is cell-scoped. BREAKOUT_BAR and LEVEL_CLOSE cells share
        # raid_id values by EXP-100 construction; uniqueness is per cell, not global.
        if "source_cell" in frame.columns:
            identity = ["source_cell", "raid_id"]
        else:
            identity = [
                column
                for column in (
                    "archive_symbol",
                    "timeframe",
                    "confirmation_method",
                    "confirmation_reference",
                    "config",
                    "raid_id",
                )
                if column in frame.columns
            ]
        duplicate_raids = int(frame.select(pl.struct(identity).is_duplicated().sum()).item())
        evidence["duplicate_raid_ids"] = duplicate_raids
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

            # Count sequence reconciliation: the completed-raid subsequence must
            # be strictly increasing in sweep order on each level. This is the
            # property shared by the design text (count of earlier completed
            # raids) and the frozen emission (sequential raid index per level);
            # it deliberately does not demand contiguity across non-completed
            # raids, which the emission is not required to provide.
            sequence_failures = 0
            completed_raids = frame.filter(
                (pl.col("status") == "COMPLETED")
                & pl.col("primary_completed").fill_null(False)
            )
            for group in completed_raids.partition_by(
                [*self.stratum_columns, "level_id"], maintain_order=True
            ):
                ordered = group.sort("sweep_ts_ns")["prior_raid_count"].to_list()
                if any(later <= earlier for earlier, later in zip(ordered, ordered[1:])):
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
    return Adapter(n_boot=FIXTURE_N_BOOT, n_destroy=DEFAULT_DESTROYS, seeds=SEEDS).fixture_frame().to_dicts()


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
        n_destroy=1,
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
            workers=int(os.environ.get("XEN_WORKERS", "1")),
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


