"""EXP-102 adapter: prior-raid count and later-swing outcome contrasts."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import polars as pl

from xen.liqswp_analysis.adapter import BaseContrastAdapter, make_fixture_frame
from xen.liqswp_analysis.destroy import (
    DestroySpec,
    apply_destroy_mappings,
    build_destroy_mappings,
    derange_indices as _derange_indices,
)
from xen.liqswp_analysis.runtime import run_fixture as _run_fixture
from xen.liqswp_analysis.runtime import run_live

EXPERIMENT = "EXP-102"
LABEL_COLUMN = "count_band"
LENGTHS = (2, 5, 10)
SEEDS = tuple(range(5))
DEFAULT_N_BOOT = 10_000
DEFAULT_DESTROYS = 2_000
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
    count = int(prior_raid_count)
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
        frame = make_fixture_frame(("0", "1", "2+"), label_column=LABEL_COLUMN)
        return frame.with_columns(
            pl.when(pl.col(LABEL_COLUMN) == "0")
            .then(pl.lit(0))
            .when(pl.col(LABEL_COLUMN) == "1")
            .then(pl.lit(1))
            .otherwise(pl.lit(2))
            .alias("prior_raid_count")
        )

    def prepare_frame(self, frame: pl.DataFrame) -> pl.DataFrame:
        if LABEL_COLUMN in frame.columns:
            return frame
        return frame.with_columns(
            pl.when(pl.col("prior_raid_count") == 0)
            .then(pl.lit("0"))
            .when(pl.col("prior_raid_count") == 1)
            .then(pl.lit("1"))
            .otherwise(pl.lit("2+"))
            .alias(LABEL_COLUMN)
        )

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
    n_boot: int = 200,
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
    adapter = Adapter()
    if args.live:
        source = args.source_root or experiment_root.parents[2] / "data/nautilus_runs/EXP-100/full"
        gate = args.gate or experiment_root / "results/estimand_validation.json"
        run_live(
            adapter, source, gate, args.output or experiment_root / "results/analysis_results.json"
        )
    else:
        _run_fixture(
            adapter,
            args.output or experiment_root / "results/fixture_integrity.json",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
