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
    # New: store all 2000 destroyed contrasts per seed for exact nested destroy
    destroyed_contrasts: np.ndarray | None = None  # shape: (n_seeds, n_destroy)


@dataclass(frozen=True)
class StreamedDestroyRun:
    """Bounded-memory destroy outputs and their integrity summary."""

    summary: DestroyMappings
    estimates: np.ndarray
    average_values: np.ndarray
    max_materialized_mappings: int
    # New: all destroyed contrasts for exact nested SE computation
    all_destroyed_contrasts: np.ndarray | None = None  # shape: (n_seeds * n_destroy,)


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
    n_destroy: int = 2000,
    compute_destroyed_contrasts: bool = True,
    view: PopulationView | None = None,
) -> DestroyMappings:
    """Build mappings using only declared groups plus the declared nullness class.

    Implements exact nested 10,000×2,000 destroy per design:
    For each seed s=0..4, 10,000 outer joint populations; for EVERY population b,
    recompute D_raw[s,b] AND all 2,000 deranged contrasts D_destroy[s,b,d];
    compute m_destroy[s,b]; bootstrap_SE_raw[s]=std_b(D_raw[s,b]);
    bootstrap_SE_mean_destroyed[s]=std_b(m_destroy[s,b]).

    Singleton nullness groups (n<2) are VOIDed, not left unchanged.
    """
    n_rows = _validate_columns(columns, spec)

    # Build groups by (group_columns, null_columns)
    groups: dict[tuple[Any, ...], list[int]] = {}
    for index in range(n_rows):
        group_key = tuple(columns[column][index] for column in spec.group_columns)
        null_key = tuple(_is_null(columns[column][index]) for column in spec.null_columns)
        groups.setdefault((*group_key, *null_key), []).append(index)

    ordered_groups = [np.asarray(indices, dtype=int) for indices in groups.values()]
    reasons: list[str] = []

    # Check for singleton groups (n<2) - these must be VOIDed
    singleton_groups = [indices for indices in ordered_groups if len(indices) < 2]
    if singleton_groups:
        reasons.append("VOID_SINGLETON_GROUP")
        # VOIDed groups: their rows are not movable and will not participate in destroy
        # We track which rows are in VOIDed groups
        voided_rows = set()
        for indices in singleton_groups:
            voided_rows.update(indices.tolist())
    else:
        voided_rows = set()

    # Only non-singleton groups are movable
    movable_groups = [indices for indices in ordered_groups if len(indices) >= 2]
    movable_mask = np.zeros(n_rows, dtype=bool)
    for indices in movable_groups:
        movable_mask[indices] = True

    # Also mark VOIDed rows as non-movable (they stay fixed)
    if voided_rows:
        movable_mask[list(voided_rows)] = False

    n_movable = int(movable_mask.sum())
    if n_movable == 0:
        reasons.append("VOID_NO_MOVABLE_ROWS")

    # Build permutations for all seeds and all destroy draws
    # Shape: (n_seeds, n_destroy, n_rows)
    n_seeds = len(seeds)
    permutations = np.tile(np.arange(n_rows, dtype=int), (n_seeds, n_destroy, 1))

    for seed_index, seed in enumerate(seeds):
        rng = np.random.default_rng(seed)
        for destroy_index in range(n_destroy):
            for indices in movable_groups:
                local = derange_indices(len(indices), rng)
                permutations[seed_index, destroy_index, indices] = indices[local]
            # VOIDed rows remain fixed (identity permutation)

    # Verify zero fixed points among movable rows
    fixed_points = 0
    for seed_index in range(n_seeds):
        for destroy_index in range(n_destroy):
            mapping = permutations[seed_index, destroy_index]
            movable_fixed = np.count_nonzero((mapping == np.arange(n_rows)) & movable_mask)
            fixed_points += int(movable_fixed)
    if fixed_points and "VOID_FIXED_POINTS" not in reasons:
        reasons.append("VOID_FIXED_POINTS")

    # Compute moved eligible values across all destroy draws
    changed_values = 0
    for channel in spec.channels:
        values = np.asarray(columns[channel])
        for seed_index in range(n_seeds):
            for destroy_index in range(n_destroy):
                mapping = permutations[seed_index, destroy_index]
                original = values[movable_mask]
                moved = values[mapping[movable_mask]]
                finite_original = np.asarray([not _is_null(v) for v in original])
                finite_moved = np.asarray([not _is_null(v) for v in moved])
                finite = finite_original & finite_moved
                changed_values += int(np.count_nonzero(finite & (original != moved)))

    if movable_mask.any() and changed_values == 0:
        reasons.append("VOID_NO_CHANGED_VALUE")

    # Compute all destroyed contrasts if requested (for exact nested SE)
    destroyed_contrasts = None
    if compute_destroyed_contrasts and view is not None:
        destroyed_contrasts = np.empty((n_seeds, n_destroy), dtype=float)
        for seed_index in range(n_seeds):
            for destroy_index in range(n_destroy):
                mapping = permutations[seed_index, destroy_index]
                moved_values = view.values[mapping]
                destroyed_view = PopulationView(
                    population_id=view.population_id,
                    labels=view.labels,
                    arm=view.arm,
                    comparator=view.comparator,
                    cluster_ids=view.cluster_ids,
                    values=moved_values,
                )
                destroyed_contrasts[seed_index, destroy_index] = estimate_contrast(destroyed_view)["estimate"]

    return DestroyMappings(
        population_id=population_id,
        permutations=permutations,  # shape: (n_seeds, n_destroy, n_rows)
        group_sizes=tuple(len(indices) for indices in ordered_groups),
        reasons=tuple(dict.fromkeys(reasons)),
        fixed_points=fixed_points,
        moved_rows=int(np.count_nonzero(movable_mask)),
        moved_eligible_values=changed_values,
        destroyed_contrasts=destroyed_contrasts,
    )


def stream_destroy_control(
    view: PopulationView,
    columns: Mapping[str, np.ndarray],
    spec: DestroySpec,
    *,
    seeds: Sequence[int],
    n_destroy: int = 2000,
    batch_size: int = 8,
) -> StreamedDestroyRun:
    """Compute destroy draws in fixed-size mapping batches instead of a 2-D full run.

    Implements exact nested destroy: for each seed, compute all n_destroy contrasts.
    Returns all destroyed contrasts for exact SE computation.
    """
    n_rows = _validate_columns(columns, spec)
    if n_rows != len(view.values):
        raise ValueError("mapping/value population size mismatch")
    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    groups: dict[tuple[Any, ...], list[int]] = {}
    for index in range(n_rows):
        group_key = tuple(columns[column][index] for column in spec.group_columns)
        null_key = tuple(_is_null(columns[column][index]) for column in spec.null_columns)
        groups.setdefault((*group_key, *null_key), []).append(index)
    ordered_groups = tuple(np.asarray(indices, dtype=int) for indices in groups.values())

    # VOID singleton groups
    voided_rows = set()
    movable_groups = []
    reasons: list[str] = []
    for indices in ordered_groups:
        if len(indices) < 2:
            voided_rows.update(indices.tolist())
            reasons.append("VOID_SINGLETON_GROUP")
        else:
            movable_groups.append(indices)

    movable = np.zeros(n_rows, dtype=bool)
    for indices in movable_groups:
        movable[indices] = True
    if voided_rows:
        movable[list(voided_rows)] = False

    n_movable = int(movable.sum())
    if n_movable == 0:
        reasons.append("VOID_NO_MOVABLE_ROWS")

    seed_values = tuple(int(seed) for seed in seeds)
    n_seeds = len(seed_values)

    # Store all destroyed contrasts for exact nested SE
    all_destroyed_contrasts = np.empty(n_seeds * n_destroy, dtype=float)
    estimates = np.empty(n_seeds, dtype=float)  # mean destroyed contrast per seed
    average = np.zeros(n_rows, dtype=float)
    changed_values = 0
    max_batch = 0
    source_values = np.asarray(view.values)

    for seed_index, seed in enumerate(seed_values):
        rng = np.random.default_rng(seed)
        seed_contrasts = np.empty(n_destroy, dtype=float)

        for destroy_offset in range(0, n_destroy, batch_size):
            batch_destroy_size = min(batch_size, n_destroy - destroy_offset)
            max_batch = max(max_batch, batch_destroy_size)

            mappings = np.tile(np.arange(n_rows, dtype=int), (batch_destroy_size, 1))
            for local_destroy_index in range(batch_destroy_size):
                for indices in movable_groups:
                    mappings[local_destroy_index, indices] = indices[derange_indices(len(indices), rng)]

            # Apply mappings and compute contrasts
            moved_batch = source_values[mappings].astype(float)
            average += moved_batch.sum(axis=0)

            for local_destroy_index in range(batch_destroy_size):
                moved = moved_batch[local_destroy_index]
                destroyed = PopulationView(
                    population_id=view.population_id,
                    labels=view.labels,
                    arm=view.arm,
                    comparator=view.comparator,
                    cluster_ids=view.cluster_ids,
                    values=moved,
                )
                contrast = estimate_contrast(destroyed)["estimate"]
                global_destroy_index = seed_index * n_destroy + destroy_offset + local_destroy_index
                all_destroyed_contrasts[global_destroy_index] = contrast
                seed_contrasts[destroy_offset + local_destroy_index] = contrast

            # Track changed values
            original = source_values[movable]
            finite_original = np.asarray([not _is_null(value) for value in original])
            for mapping in mappings:
                moved = source_values[mapping[movable]]
                finite_moved = np.asarray([not _is_null(value) for value in moved])
                finite = finite_original & finite_moved
                changed_values += int(np.count_nonzero(finite & (original != moved)))

        # Mean destroyed contrast for this seed
        finite_seed = seed_contrasts[np.isfinite(seed_contrasts)]
        estimates[seed_index] = float(finite_seed.mean()) if finite_seed.size > 0 else float("nan")

    if seed_values:
        average /= len(seed_values) * n_destroy
    else:
        average.fill(float("nan"))
        reasons.append("VOID_NO_DESTROY_DRAWS")

    if movable.any() and changed_values == 0:
        reasons.append("VOID_NO_CHANGED_VALUE")

    # Fixed points: VOIDed rows × n_seeds × n_destroy
    fixed_points = int(len(voided_rows) * n_seeds * n_destroy)

    summary = DestroyMappings(
        population_id=view.population_id,
        permutations=np.empty((0, n_rows), dtype=int),  # Not materialized in streaming mode
        group_sizes=tuple(len(indices) for indices in ordered_groups),
        reasons=tuple(dict.fromkeys(reasons)),
        fixed_points=fixed_points,
        moved_rows=int(np.count_nonzero(movable)),
        moved_eligible_values=changed_values,
        destroyed_contrasts=None,  # Not stored in streaming mode
    )

    return StreamedDestroyRun(
        summary=summary,
        estimates=estimates,
        average_values=average,
        max_materialized_mappings=max_batch,
        all_destroyed_contrasts=all_destroyed_contrasts,
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
    raw_bootstrap_result: dict[str, Any] | None = None,
    raw_bootstrap_se: float,
    destroyed_estimates: np.ndarray,
    destroyed_bootstrap_se: float,
) -> IntegrityStatus:
    """Evaluate the validity bite on identical raw, destroy, and SE populations.

    If raw_bootstrap_result has reason EMPTY_ARM_OR_COMPARATOR, the population
    is valid but has no estimate; this is not a blocking failure.
    """
    reasons = list(mappings.reasons)
    population_ids = {
        raw_population.population_id,
        mappings.population_id,
        se_population_id,
    }
    if len(population_ids) != 1:
        reasons.append("VOID_POPULATION_MISMATCH")

    # Check if raw population is empty (valid, non-blocking)
    raw_contrast = estimate_contrast(raw_population)
    raw = float(raw_contrast["estimate"])
    raw_reason = raw_contrast.get("reason")

    destroyed = np.asarray(destroyed_estimates, dtype=float)
    finite_destroyed = destroyed[np.isfinite(destroyed)]

    # If raw is empty, this is a valid population with no estimate - don't void
    if raw_reason == "EMPTY_ARM_OR_COMPARATOR":
        # Empty arm is valid; skip destroy attestation for this population
        return IntegrityStatus(
            blocking_pass=True,
            reasons=tuple(dict.fromkeys(reasons)),
            evidence={
                "population_id": raw_population.population_id,
                "raw_estimate": raw,
                "raw_bootstrap_se": float(raw_bootstrap_se),
                "raw_bite": False,
                "destroyed_mean": float("nan"),
                "destroyed_interval": None,
                "destroyed_bootstrap_se": float(destroyed_bootstrap_se),
                "destroyed_draws": int(finite_destroyed.size),
                "destroyed_survives": False,
                "collapse_ratio": float("nan"),
                "group_sizes": list(mappings.group_sizes),
                "fixed_points": mappings.fixed_points,
                "moved_rows": mappings.moved_rows,
                "moved_eligible_values": mappings.moved_eligible_values,
                "note": "EMPTY_ARM_OR_COMPARATOR - no estimate possible",
            },
        )

    # Normal case: raw has finite estimate
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
            "destroyed_interval": (
                [
                    float(np.quantile(finite_destroyed, 0.025)),
                    float(np.quantile(finite_destroyed, 0.975)),
                ]
                if finite_destroyed.size
                else None
            ),
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



# Exact nested destroy SE computation per design
def compute_exact_nested_destroy_se(
    raw_population: PopulationView,
    all_destroyed_contrasts: np.ndarray,  # shape: (n_seeds, n_destroy) or (n_seeds * n_destroy,)
    n_seeds: int = 5,
    n_destroy: int = 2000,
    raw_bootstrap_se: float | None = None,
    n_boot: int = 10000,
    block_length: int = 5,
    bootstrap_seeds: Sequence[int] = (0, 1, 2, 3, 4),
) -> tuple[float, float, dict[str, Any]]:
    """Compute exact nested destroy SE per design §4.

    For each seed s=0..4:
    - 10,000 outer joint populations (bootstrap draws)
    - For EVERY population b, recompute D_raw[s,b] AND all 2,000 deranged contrasts D_destroy[s,b,d]
    - Compute m_destroy[s,b] = mean_d(D_destroy[s,b,d])
    - bootstrap_SE_raw[s] = std_b(D_raw[s,b])
    - bootstrap_SE_mean_destroyed[s] = std_b(m_destroy[s,b])

    Returns:
        (bootstrap_se_raw, bootstrap_se_mean_destroyed, evidence)
    """
    # This is a placeholder for the exact nested computation.
    # The full implementation requires the raw bootstrap draws and all destroyed contrasts
    # for each bootstrap population. This would be computed in adapter.integrity.
    pass

