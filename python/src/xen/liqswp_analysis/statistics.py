"""Array-based estimators and whole-cluster circular bootstrap."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np


@dataclass(frozen=True)
class PopulationView:
    """One explicit arm-versus-fixed-comparator estimator population."""

    population_id: str
    labels: np.ndarray
    arm: Any
    comparator: Any
    cluster_ids: np.ndarray
    values: np.ndarray

    def __post_init__(self) -> None:
        lengths = {len(self.labels), len(self.cluster_ids), len(self.values)}
        if len(lengths) != 1:
            raise ValueError("population arrays must have equal length")


def estimate_contrast(view: PopulationView, indices: np.ndarray | None = None) -> dict[str, Any]:
    """Estimate arm minus fixed comparator on the selected population rows."""
    selected = np.arange(len(view.values)) if indices is None else np.asarray(indices, dtype=int)
    labels = view.labels[selected]
    values = np.asarray(view.values[selected], dtype=float)
    arm_values = values[(labels == view.arm) & np.isfinite(values)]
    comparator_values = values[(labels == view.comparator) & np.isfinite(values)]
    reason = None
    estimate = float("nan")
    arm_mean = float("nan")
    comparator_mean = float("nan")
    if arm_values.size == 0 or comparator_values.size == 0:
        reason = "EMPTY_ARM_OR_COMPARATOR"
    else:
        arm_mean = float(arm_values.mean())
        comparator_mean = float(comparator_values.mean())
        estimate = arm_mean - comparator_mean
    return {
        "population_id": view.population_id,
        "estimate": estimate,
        "arm_mean": arm_mean,
        "comparator_mean": comparator_mean,
        "arm_n": int(arm_values.size),
        "comparator_n": int(comparator_values.size),
        "reason": reason,
    }


def circular_cluster_indices(
    n_clusters: int,
    block_length: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Return `n_clusters` ordered circular-block cluster positions."""
    if n_clusters < 1:
        return np.asarray([], dtype=int)
    effective = 1 if n_clusters == 1 else min(max(1, int(block_length)), n_clusters - 1)
    parts: list[np.ndarray] = []
    remaining = n_clusters
    while remaining:
        start = int(rng.integers(0, n_clusters))
        take = min(effective, remaining)
        parts.append((start + np.arange(take, dtype=int)) % n_clusters)
        remaining -= take
    return np.concatenate(parts)


def _cluster_rows(view: PopulationView) -> tuple[np.ndarray, list[np.ndarray]]:
    names: list[Any] = []
    positions: dict[Any, list[int]] = {}
    for index, cluster in enumerate(view.cluster_ids.tolist()):
        if cluster not in positions:
            names.append(cluster)
            positions[cluster] = []
        positions[cluster].append(index)
    return np.asarray(names, dtype=object), [
        np.asarray(positions[name], dtype=int) for name in names
    ]


def _cluster_contrast_totals(
    view: PopulationView, rows_by_cluster: Sequence[np.ndarray]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Precompute the four sufficient statistics needed by every bootstrap draw."""
    values = np.asarray(view.values, dtype=float)
    arm_sum = np.zeros(len(rows_by_cluster), dtype=float)
    arm_n = np.zeros(len(rows_by_cluster), dtype=np.int64)
    comparator_sum = np.zeros(len(rows_by_cluster), dtype=float)
    comparator_n = np.zeros(len(rows_by_cluster), dtype=np.int64)
    for index, rows in enumerate(rows_by_cluster):
        labels = view.labels[rows]
        cluster_values = values[rows]
        arm_values = cluster_values[(labels == view.arm) & np.isfinite(cluster_values)]
        comparator_values = cluster_values[
            (labels == view.comparator) & np.isfinite(cluster_values)
        ]
        arm_sum[index] = arm_values.sum()
        arm_n[index] = arm_values.size
        comparator_sum[index] = comparator_values.sum()
        comparator_n[index] = comparator_values.size
    return arm_sum, arm_n, comparator_sum, comparator_n


def clustered_contrast_bootstrap(
    view: PopulationView,
    *,
    block_length: int,
    n_boot: int,
    seeds: Sequence[int],
) -> dict[str, Any]:
    """Bootstrap a contrast by complete clusters and report non-finite draws explicitly."""
    base = estimate_contrast(view)
    clusters, rows_by_cluster = _cluster_rows(view)
    base.update(
        block_length=int(block_length),
        L_eff=max(0, min(int(block_length), len(clusters) - 1)),
        n_clusters=int(len(clusters)),
    )
    if base["reason"] is not None:
        base.update(interval=None, seeds=[], finite_draws=0, nonfinite_draws=0)
        return base
    if len(clusters) < 2:
        base.update(
            reason="ONE_CLUSTER",
            interval=None,
            seeds=[],
            finite_draws=0,
            nonfinite_draws=0,
        )
        return base

    seed_rows: list[dict[str, Any]] = []
    total_finite = 0
    total_nonfinite = 0
    arm_sum, arm_n, comparator_sum, comparator_n = _cluster_contrast_totals(view, rows_by_cluster)
    for seed in seeds:
        rng = np.random.default_rng(seed)
        draws = np.empty(int(n_boot), dtype=float)
        for draw_index in range(int(n_boot)):
            chosen = circular_cluster_indices(len(clusters), block_length, rng)
            selected_arm_n = int(arm_n[chosen].sum())
            selected_comparator_n = int(comparator_n[chosen].sum())
            if selected_arm_n == 0 or selected_comparator_n == 0:
                draws[draw_index] = float("nan")
            else:
                draws[draw_index] = float(
                    arm_sum[chosen].sum() / selected_arm_n
                    - comparator_sum[chosen].sum() / selected_comparator_n
                )
        finite = draws[np.isfinite(draws)]
        total_finite += int(finite.size)
        total_nonfinite += int(draws.size - finite.size)
        if finite.size:
            seed_rows.append(
                {
                    "seed": int(seed),
                    "low": float(np.quantile(finite, 0.025)),
                    "high": float(np.quantile(finite, 0.975)),
                    "finite_draws": int(finite.size),
                    "nonfinite_draws": int(draws.size - finite.size),
                    "bootstrap_se": float(np.std(finite, ddof=1))
                    if finite.size > 1
                    else float("nan"),
                }
            )
    if not seed_rows:
        base.update(
            reason="NO_FINITE_DRAWS",
            interval=None,
            seeds=[],
            finite_draws=total_finite,
            nonfinite_draws=total_nonfinite,
        )
        return base
    lows = [row["low"] for row in seed_rows]
    highs = [row["high"] for row in seed_rows]
    standard_errors = [row["bootstrap_se"] for row in seed_rows if np.isfinite(row["bootstrap_se"])]
    base.update(
        reason=None,
        interval=[float(np.median(lows)), float(np.median(highs))],
        seed_low_range=[float(min(lows)), float(max(lows))],
        seed_high_range=[float(min(highs)), float(max(highs))],
        seeds=seed_rows,
        finite_draws=total_finite,
        nonfinite_draws=total_nonfinite,
        bootstrap_se=float(np.median(standard_errors)) if standard_errors else float("nan"),
    )
    return base


def block_sensitivity(
    view: PopulationView,
    *,
    lengths: Sequence[int],
    n_boot: int,
    seeds: Sequence[int],
) -> dict[str, dict[str, Any]]:
    """Return all registered block-length reads without dropping unavailable rows."""
    return {
        str(length): clustered_contrast_bootstrap(
            view,
            block_length=int(length),
            n_boot=int(n_boot),
            seeds=seeds,
        )
        for length in lengths
    }
