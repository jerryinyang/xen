"""EXP-101 adapter: level configuration and later-swing outcome contrasts."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Sequence

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
from xen.liqswp_analysis.statistics import (
    PopulationView,
    circular_cluster_indices,
    estimate_contrast as _estimate_view,
)

EXPERIMENT = "EXP-101"
LABEL_COLUMN = "config"
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


def _finite(value: Any) -> bool:
    try:
        return value is not None and bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def control_null_class(row: dict[str, Any]) -> tuple[bool, ...]:
    """Return the exact five-bit registered outcome-nullness class."""
    return tuple(not _finite(row.get(column)) for column in CONTROL_NULL_COLUMNS)


def derange_indices(n: int, seed: int) -> np.ndarray:
    """Compatibility wrapper over the canonical derangement implementation."""
    return _derange_indices(n, np.random.default_rng(seed))


def block_bootstrap(values: np.ndarray, block_length: int, n_boot: int, seed: int) -> np.ndarray:
    """Compatibility helper returning circular-block sampled values."""
    array = np.asarray(values)
    rng = np.random.default_rng(seed)
    return np.asarray(
        [array[circular_cluster_indices(len(array), block_length, rng)] for _ in range(n_boot)]
    )


def _eligible_rows(rows: Iterable[dict[str, Any]], channel: str) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if not (
            channel in {"swing_atr", "strong_move"}
            and row.get("profile_undefined_reason") == "ATR_UNDEFINED"
        )
    ]


def estimate_contrast(
    rows: Sequence[dict[str, Any]],
    label: str,
    arm: Any,
    comparator: Any,
    channel: str,
) -> dict[str, Any]:
    """Compatibility estimator with explicit ATR-undefined exclusion count."""
    eligible = _eligible_rows(rows, channel)
    view = PopulationView(
        population_id=f"compat:{label}:{arm}-vs-{comparator}:{channel}",
        labels=np.asarray([row.get(label) for row in eligible], dtype=object),
        arm=arm,
        comparator=comparator,
        cluster_ids=np.asarray(
            [row.get("level_id", f"row-{index}") for index, row in enumerate(eligible)],
            dtype=object,
        ),
        values=np.asarray([row.get(channel, np.nan) for row in eligible], dtype=float),
    )
    result = _estimate_view(view)
    result["excluded_atr_undefined"] = len(rows) - len(eligible)
    return result


class Adapter(BaseContrastAdapter):
    """Explicit EXP-101 populations and fixed comparator."""

    experiment = EXPERIMENT
    label_column = LABEL_COLUMN
    contrasts = (
        ("PREVIOUS_4H", "PREVIOUS_1H"),
        ("PREVIOUS_1D", "PREVIOUS_1H"),
        ("PREVIOUS_1W", "PREVIOUS_1H"),
        ("PREVIOUS_EUROPE", "PREVIOUS_ASIA"),
        ("PREVIOUS_AMERICA", "PREVIOUS_ASIA"),
        ("ROLLING_14", "ROLLING_7"),
        ("ROLLING_22", "ROLLING_7"),
        ("ROLLING_252", "ROLLING_7"),
    )
    stratum_columns = (
        "archive_symbol",
        "timeframe",
        "confirmation_method",
        "confirmation_reference",
        "side",
    )
    control_group_columns = CONTROL_GROUP_COLUMNS
    control_null_columns = CONTROL_NULL_COLUMNS

    def fixture_frame(self) -> pl.DataFrame:
        frame = make_fixture_frame(
            (
                "PREVIOUS_1H",
                "PREVIOUS_4H",
                "PREVIOUS_1D",
                "PREVIOUS_1W",
                "PREVIOUS_ASIA",
                "PREVIOUS_EUROPE",
                "PREVIOUS_AMERICA",
                "ROLLING_7",
                "ROLLING_14",
                "ROLLING_22",
                "ROLLING_252",
            ),
            label_column=LABEL_COLUMN,
        )
        return frame.with_columns(pl.col("config").alias("source_configuration"))

    def census(self, frame: pl.DataFrame) -> dict[str, Any]:
        census = super().census(frame)
        counts = Counter(str(value) for value in frame["config"].to_list())
        census.update(arm=sum(counts[arm] for arm, _ in self.contrasts))
        census.update(comparator=sum(counts[comparator] for _, comparator in self.contrasts))
        census["config"] = dict(counts)
        return census


def _fixture_rows() -> list[dict[str, Any]]:
    return Adapter(n_boot=40, n_destroy=20, seeds=(0, 1)).fixture_frame().to_dicts()


def future_destroy(
    rows: Sequence[dict[str, Any]], label: str, seed: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fixture compatibility wrapper using the canonical exact grouping."""
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
    n_boot: int = 10,
) -> dict[str, Any]:
    """Run the fixture through the production integrity/runtime path."""
    destination = output or Path(__file__).resolve().parents[1] / "results/fixture_integrity.json"
    return _run_fixture(
        Adapter(n_boot=n_boot, n_destroy=n_destroy, seeds=seeds),
        destination,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fixture", "--fixture-only", "--smoke", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--source-root", "--root", type=Path)
    parser.add_argument("--gate", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    experiment_root = Path(__file__).resolve().parents[1]
    output = args.output or experiment_root / "results/analysis_results.json"
    adapter = Adapter()
    if args.live:
        source = args.source_root or experiment_root.parents[2] / "data/nautilus_runs/EXP-100/full"
        gate = args.gate or (
            experiment_root.parent / "EXP-100/results/estimand_validation.json"
        )
        run_live(adapter, source, gate, output)
    else:
        run_fixture(output=args.output or experiment_root / "results/fixture_integrity.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
