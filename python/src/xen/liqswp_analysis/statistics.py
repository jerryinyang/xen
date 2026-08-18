"""Array-based estimators and whole-cluster circular bootstrap."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterator, Sequence

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


def _circular_block_selections(
    n_clusters: int,
    block_length: int,
    starts: np.ndarray,
    effective: int,
) -> np.ndarray:
    """Assemble circular-block selections from batched start positions."""
    parts_per_draw = int(math.ceil(n_clusters / effective))
    n_draws = starts.size // parts_per_draw
    blocks = (
        starts.reshape(n_draws, parts_per_draw)[:, :, None] + np.arange(effective, dtype=int)
    ) % n_clusters
    return blocks.reshape(n_draws, parts_per_draw * effective)[:, :n_clusters]


def _selection_chunks(
    n_clusters: int,
    block_length: int,
    n_boot: int,
    rng: np.random.Generator,
    *,
    chunk: int = 256,
) -> Iterator[np.ndarray]:
    """Yield (C, n_clusters) joint circular-block selections in draw order.

    Consumes exactly ceil(n_clusters / L_eff) integers per draw from the
    generator — the same stream values as the registered per-draw
    ``circular_cluster_indices`` path — so every selection is bit-identical
    to the per-draw form.
    """
    if n_clusters < 1:
        return
    effective = 1 if n_clusters == 1 else min(max(1, int(block_length)), n_clusters - 1)
    parts_per_draw = int(math.ceil(n_clusters / effective))
    remaining = int(n_boot)
    while remaining:
        chunk_now = min(chunk, remaining)
        starts = rng.integers(0, n_clusters, size=chunk_now * parts_per_draw)
        yield _circular_block_selections(n_clusters, block_length, starts, effective)
        remaining -= chunk_now


def _independent_selection_chunks(
    n_arm_clusters: int,
    n_comparator_clusters: int,
    block_length: int,
    n_boot: int,
    rng: np.random.Generator,
    *,
    chunk: int = 256,
) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Yield (arm_sel, comp_sel) pairs for independent arm/comparator resampling.

    Arm starts for the whole chunk are consumed before comparator starts; the
    per-draw interleaved stream is not preserved, so independent-arm draws are
    a fresh deterministic realization of the registered procedure.
    """
    if n_arm_clusters < 1 or n_comparator_clusters < 1:
        return
    eff_arm = 1 if n_arm_clusters == 1 else min(max(1, int(block_length)), n_arm_clusters - 1)
    eff_comp = (
        1
        if n_comparator_clusters == 1
        else min(max(1, int(block_length)), n_comparator_clusters - 1)
    )
    parts_arm = int(math.ceil(n_arm_clusters / eff_arm))
    parts_comp = int(math.ceil(n_comparator_clusters / eff_comp))
    remaining = int(n_boot)
    while remaining:
        chunk_now = min(chunk, remaining)
        arm_starts = rng.integers(0, n_arm_clusters, size=chunk_now * parts_arm)
        comp_starts = rng.integers(0, n_comparator_clusters, size=chunk_now * parts_comp)
        yield (
            _circular_block_selections(n_arm_clusters, block_length, arm_starts, eff_arm),
            _circular_block_selections(
                n_comparator_clusters, block_length, comp_starts, eff_comp
            ),
        )
        remaining -= chunk_now


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


def _split_arm_comparator_clusters(
    view: PopulationView,
) -> tuple[np.ndarray, list[np.ndarray], np.ndarray, list[np.ndarray]]:
    """Split clusters into arm and comparator populations for independent resampling.
    Returns cluster names and row indices into the ORIGINAL arrays.
    """
    arm_mask = (view.labels == view.arm) & np.isfinite(view.values)
    comparator_mask = (view.labels == view.comparator) & np.isfinite(view.values)

    arm_indices = np.where(arm_mask)[0]
    comparator_indices = np.where(comparator_mask)[0]

    arm_cluster_ids = view.cluster_ids[arm_indices]
    comparator_cluster_ids = view.cluster_ids[comparator_indices]

    # Get unique clusters and their ORIGINAL row indices for arm
    arm_names: list[Any] = []
    arm_positions: dict[Any, list[int]] = {}
    for idx, orig_idx in enumerate(arm_indices):
        cluster = arm_cluster_ids[idx]
        if cluster not in arm_positions:
            arm_names.append(cluster)
            arm_positions[cluster] = []
        arm_positions[cluster].append(orig_idx)
    arm_cluster_names = np.asarray(arm_names, dtype=object)
    arm_rows_by_cluster = [
        np.asarray(arm_positions[name], dtype=int) for name in arm_names
    ]

    # Get unique clusters and their ORIGINAL row indices for comparator
    comparator_names: list[Any] = []
    comparator_positions: dict[Any, list[int]] = {}
    for idx, orig_idx in enumerate(comparator_indices):
        cluster = comparator_cluster_ids[idx]
        if cluster not in comparator_positions:
            comparator_names.append(cluster)
            comparator_positions[cluster] = []
        comparator_positions[cluster].append(orig_idx)
    comparator_cluster_names = np.asarray(comparator_names, dtype=object)
    comparator_rows_by_cluster = [
        np.asarray(comparator_positions[name], dtype=int) for name in comparator_names
    ]

    return (
        arm_cluster_names, arm_rows_by_cluster,
        comparator_cluster_names, comparator_rows_by_cluster
    )

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


def _cluster_arm_totals(
    cluster_names: np.ndarray,
    rows_by_cluster: Sequence[np.ndarray],
    values: np.ndarray,
    labels: np.ndarray,
    arm_label: Any,
) -> tuple[np.ndarray, np.ndarray]:
    """Precompute arm sum and count per cluster."""
    arm_sum = np.zeros(len(rows_by_cluster), dtype=float)
    arm_n = np.zeros(len(rows_by_cluster), dtype=np.int64)
    for index, rows in enumerate(rows_by_cluster):
        cluster_labels = labels[rows]
        cluster_values = values[rows]
        arm_values = cluster_values[(cluster_labels == arm_label) & np.isfinite(cluster_values)]
        arm_sum[index] = arm_values.sum()
        arm_n[index] = arm_values.size
    return arm_sum, arm_n


def clustered_contrast_bootstrap(
    view: PopulationView,
    *,
    block_length: int,
    n_boot: int,
    seeds: Sequence[int],
    independent_arms: bool = False,
) -> dict[str, Any]:
    """Bootstrap a contrast by complete clusters and report non-finite draws explicitly.

    Args:
        view: Population view with arm and comparator labels.
        block_length: Circular block length for cluster resampling.
        n_boot: Number of bootstrap draws per seed.
        seeds: Seed sequence for reproducibility.
        independent_arms: If True, resample arm and comparator clusters independently
            (EXP-101 design). If False, resample jointly (EXP-102/103 design).
    """
    base = estimate_contrast(view)
    clusters, rows_by_cluster = _cluster_rows(view)
    base.update(
        block_length=int(block_length),
        L_eff=max(0, min(int(block_length), len(clusters) - 1)),
        n_clusters=int(len(clusters)),
        independent_arms=independent_arms,
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

    if independent_arms:
        # EXP-101: Independent arm/comparator resampling (vectorized chunks).
        arm_cluster_names, arm_rows_by_cluster, comparator_cluster_names, comparator_rows_by_cluster = _split_arm_comparator_clusters(view)
        values = np.asarray(view.values, dtype=float)
        labels = view.labels

        # Precompute arm and comparator totals per cluster
        arm_sum, arm_n = _cluster_arm_totals(arm_cluster_names, arm_rows_by_cluster, values, labels, view.arm)
        comparator_sum, comparator_n = _cluster_arm_totals(comparator_cluster_names, comparator_rows_by_cluster, values, labels, view.comparator)

        n_arm_clusters = len(arm_cluster_names)
        n_comparator_clusters = len(comparator_cluster_names)

        if n_arm_clusters < 1 or n_comparator_clusters < 1:
            base.update(
                reason="EMPTY_ARM_OR_COMPARATOR_CLUSTERS",
                interval=None,
                seeds=[],
                finite_draws=0,
                nonfinite_draws=0,
            )
            return base

        arm_sum_a = np.asarray(arm_sum, dtype=float)
        arm_n_a = np.asarray(arm_n, dtype=np.int64)
        comparator_sum_a = np.asarray(comparator_sum, dtype=float)
        comparator_n_a = np.asarray(comparator_n, dtype=np.int64)
        for seed in seeds:
            rng = np.random.default_rng(seed)
            draws = np.empty(int(n_boot), dtype=float)
            offset = 0
            for arm_sel, comp_sel in _independent_selection_chunks(
                n_arm_clusters, n_comparator_clusters, block_length, int(n_boot), rng
            ):
                c = arm_sel.shape[0]
                an = arm_n_a[arm_sel].sum(axis=1)
                cn = comparator_n_a[comp_sel].sum(axis=1)
                est = np.full(c, float("nan"))
                with np.errstate(divide="ignore", invalid="ignore"):
                    valid = (an > 0) & (cn > 0)
                    est[valid] = (
                        arm_sum_a[arm_sel][valid].sum(axis=1) / an[valid]
                        - comparator_sum_a[comp_sel][valid].sum(axis=1) / cn[valid]
                    )
                draws[offset : offset + c] = est
                offset += c
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
    else:
        # EXP-102/103: Joint resampling (vectorized chunks; the chunked integer
        # stream is identical to the registered per-draw form, so every draw
        # and statistic is bit-identical to the scalar implementation).
        arm_sum, arm_n, comparator_sum, comparator_n = _cluster_contrast_totals(view, rows_by_cluster)
        arm_sum_a = np.asarray(arm_sum, dtype=float)
        arm_n_a = np.asarray(arm_n, dtype=np.int64)
        comparator_sum_a = np.asarray(comparator_sum, dtype=float)
        comparator_n_a = np.asarray(comparator_n, dtype=np.int64)
        for seed in seeds:
            rng = np.random.default_rng(seed)
            draws = np.empty(int(n_boot), dtype=float)
            offset = 0
            for sel in _selection_chunks(len(clusters), block_length, int(n_boot), rng):
                c = sel.shape[0]
                an = arm_n_a[sel].sum(axis=1)
                cn = comparator_n_a[sel].sum(axis=1)
                est = np.full(c, float("nan"))
                with np.errstate(divide="ignore", invalid="ignore"):
                    valid = (an > 0) & (cn > 0)
                    est[valid] = (
                        arm_sum_a[sel][valid].sum(axis=1) / an[valid]
                        - comparator_sum_a[sel][valid].sum(axis=1) / cn[valid]
                    )
                draws[offset : offset + c] = est
                offset += c
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
    independent_arms: bool = False,
) -> dict[str, dict[str, Any]]:
    """Return all registered block-length reads without dropping unavailable rows."""
    return {
        str(length): clustered_contrast_bootstrap(
            view,
            block_length=int(length),
            n_boot=int(n_boot),
            seeds=seeds,
            independent_arms=independent_arms,
        )
        for length in lengths
    }

