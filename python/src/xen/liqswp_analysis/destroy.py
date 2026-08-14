"""Fail-closed, array-based future-destroy integrity mechanics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from xen.liqswp_analysis.contract import IntegrityStatus
from xen.liqswp_analysis.statistics import PopulationView, estimate_contrast

INTEGRITY_Z = 2.8


@dataclass(frozen=True)
class DestroySpec:
    """Exact registered grouping and verdict-bearing destroy channels."""

    group_columns: tuple[str, ...]
    null_columns: tuple[str, ...]
    channels: tuple[str, ...]


@dataclass(frozen=True)
class DestroyMappings:
    """Verified global row mappings for all requested destroy seeds."""

    population_id: str
    permutations: np.ndarray
    group_sizes: tuple[int, ...]
    reasons: tuple[str, ...]
    fixed_points: int
    moved_rows: int
    moved_eligible_values: int


def derange_indices(n: int, rng: np.random.Generator) -> np.ndarray:
    """Generate a uniform-enough zero-fixed-point permutation for integrity controls."""
    if n < 2:
        raise ValueError("a derangement requires at least two rows")
    original = np.arange(n)
    while True:
        candidate = rng.permutation(n)
        if not np.any(candidate == original):
            return candidate


def _is_null(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(not np.isfinite(value))
    except TypeError:
        return False


def _validate_columns(columns: Mapping[str, np.ndarray], spec: DestroySpec) -> int:
    required = (*spec.group_columns, *spec.null_columns, *spec.channels)
    missing = [column for column in required if column not in columns]
    if missing:
        raise KeyError(f"missing destroy columns: {missing}")
    lengths = {len(columns[column]) for column in required}
    if len(lengths) != 1:
        raise ValueError("destroy columns must have equal length")
    return lengths.pop()


def build_destroy_mappings(
    columns: Mapping[str, np.ndarray],
    spec: DestroySpec,
    *,
    seeds: Sequence[int],
    population_id: str,
) -> DestroyMappings:
    """Build mappings using only declared groups plus the declared nullness class."""
    n_rows = _validate_columns(columns, spec)
    groups: dict[tuple[Any, ...], list[int]] = {}
    for index in range(n_rows):
        group_key = tuple(columns[column][index] for column in spec.group_columns)
        null_key = tuple(_is_null(columns[column][index]) for column in spec.null_columns)
        groups.setdefault((*group_key, *null_key), []).append(index)

    ordered_groups = [np.asarray(indices, dtype=int) for indices in groups.values()]
    reasons: list[str] = []
    if any(len(indices) < 2 for indices in ordered_groups):
        reasons.append("VOID_SINGLETON_GROUP")
    permutations = np.tile(np.arange(n_rows, dtype=int), (len(seeds), 1))
    for seed_index, seed in enumerate(seeds):
        rng = np.random.default_rng(seed)
        for indices in ordered_groups:
            if len(indices) < 2:
                continue
            local = derange_indices(len(indices), rng)
            permutations[seed_index, indices] = indices[local]

    fixed_points = int(np.count_nonzero(permutations == np.arange(n_rows)))
    if fixed_points and "VOID_SINGLETON_GROUP" not in reasons:
        reasons.append("VOID_FIXED_POINTS")
    movable_mask = np.zeros(n_rows, dtype=bool)
    for indices in ordered_groups:
        if len(indices) >= 2:
            movable_mask[indices] = True
    changed_values = 0
    for channel in spec.channels:
        values = np.asarray(columns[channel])
        for mapping in permutations:
            original = values[movable_mask]
            moved = values[mapping[movable_mask]]
            finite = np.asarray([not _is_null(value) for value in original]) & np.asarray(
                [not _is_null(value) for value in moved]
            )
            changed_values += int(np.count_nonzero(finite & (original != moved)))
    if movable_mask.any() and changed_values == 0:
        reasons.append("VOID_NO_CHANGED_VALUE")
    return DestroyMappings(
        population_id=population_id,
        permutations=permutations,
        group_sizes=tuple(len(indices) for indices in ordered_groups),
        reasons=tuple(dict.fromkeys(reasons)),
        fixed_points=fixed_points,
        moved_rows=int(np.count_nonzero(movable_mask)),
        moved_eligible_values=changed_values,
    )


def apply_destroy_mappings(values: np.ndarray, mappings: DestroyMappings) -> np.ndarray:
    """Apply all verified mappings without copying row objects."""
    array = np.asarray(values)
    if mappings.permutations.shape[1] != len(array):
        raise ValueError("mapping/value population size mismatch")
    return array[mappings.permutations]


def destroyed_contrasts(view: PopulationView, mappings: DestroyMappings) -> np.ndarray:
    """Calculate every destroyed contrast through the canonical estimator."""
    moved = apply_destroy_mappings(view.values, mappings)
    estimates = np.empty(len(moved), dtype=float)
    for index, values in enumerate(moved):
        destroyed = PopulationView(
            population_id=view.population_id,
            labels=view.labels,
            arm=view.arm,
            comparator=view.comparator,
            cluster_ids=view.cluster_ids,
            values=values,
        )
        estimates[index] = estimate_contrast(destroyed)["estimate"]
    return estimates


def reference_destroyed_contrasts(view: PopulationView, mappings: DestroyMappings) -> np.ndarray:
    """Small-fixture reference implementation used to prove optimized parity."""
    estimates: list[float] = []
    for mapping in mappings.permutations.tolist():
        values = np.asarray([view.values[index] for index in mapping], dtype=float)
        arm_values = [
            value for value, label in zip(values, view.labels, strict=True) if label == view.arm
        ]
        comparator_values = [
            value
            for value, label in zip(values, view.labels, strict=True)
            if label == view.comparator
        ]
        estimates.append(float(np.mean(arm_values) - np.mean(comparator_values)))
    return np.asarray(estimates)


def future_destroy_attestation(
    raw_population: PopulationView,
    mappings: DestroyMappings,
    *,
    se_population_id: str,
    raw_bootstrap_se: float,
    destroyed_estimates: np.ndarray,
    destroyed_bootstrap_se: float,
) -> IntegrityStatus:
    """Evaluate the validity bite on identical raw, destroy, and SE populations."""
    reasons = list(mappings.reasons)
    population_ids = {
        raw_population.population_id,
        mappings.population_id,
        se_population_id,
    }
    if len(population_ids) != 1:
        reasons.append("VOID_POPULATION_MISMATCH")
    raw = float(estimate_contrast(raw_population)["estimate"])
    destroyed = np.asarray(destroyed_estimates, dtype=float)
    finite_destroyed = destroyed[np.isfinite(destroyed)]
    if not np.isfinite(raw) or not np.isfinite(raw_bootstrap_se) or raw_bootstrap_se < 0:
        reasons.append("VOID_NONFINITE_RAW_STATISTIC")
    if (
        finite_destroyed.size == 0
        or not np.isfinite(destroyed_bootstrap_se)
        or destroyed_bootstrap_se < 0
    ):
        reasons.append("VOID_NONFINITE_DESTROY_STATISTIC")
        destroyed_mean = float("nan")
    else:
        destroyed_mean = float(finite_destroyed.mean())
    raw_bite = bool(
        np.isfinite(raw)
        and np.isfinite(raw_bootstrap_se)
        and abs(raw) > INTEGRITY_Z * raw_bootstrap_se
    )
    destroyed_survives = bool(
        raw_bite
        and np.isfinite(destroyed_mean)
        and np.isfinite(destroyed_bootstrap_se)
        and abs(destroyed_mean) > INTEGRITY_Z * destroyed_bootstrap_se
    )
    if destroyed_survives:
        reasons.append("VOID_FUTURE_DESTROY_SURVIVAL")
    collapse_ratio = (
        destroyed_mean / raw
        if np.isfinite(destroyed_mean) and np.isfinite(raw) and raw != 0
        else float("nan")
    )
    unique_reasons = tuple(dict.fromkeys(reasons))
    return IntegrityStatus(
        blocking_pass=not unique_reasons,
        reasons=unique_reasons,
        evidence={
            "population_id": raw_population.population_id,
            "raw_estimate": raw,
            "raw_bootstrap_se": float(raw_bootstrap_se),
            "raw_bite": raw_bite,
            "destroyed_mean": destroyed_mean,
            "destroyed_bootstrap_se": float(destroyed_bootstrap_se),
            "destroyed_draws": int(finite_destroyed.size),
            "destroyed_survives": destroyed_survives,
            "collapse_ratio": collapse_ratio,
            "group_sizes": list(mappings.group_sizes),
            "fixed_points": mappings.fixed_points,
            "moved_rows": mappings.moved_rows,
            "moved_eligible_values": mappings.moved_eligible_values,
        },
    )
