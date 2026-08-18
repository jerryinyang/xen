"""Fail-closed future-destroy integrity mechanics.

The registered TRIPWIRE control has two computation layers.

1. Live read (unresampled donor population): one derangement per destroy seed
   d=0..n_destroy-1 is drawn per nullness/event group on the full donor
   population (all eligible outcome-bearing rows in the stratum; configuration
   pooled within each group). Every destroyed contrast is the canonical §3
   estimator evaluated on the arm/comparator rows with the moved outcome blocks.

2. Nested outer bootstrap: for each outer seed s=0..4 and each of n_boot
   cluster populations b (the §4 mechanics: joint circular-block resampling, or
   independent arm/comparator resampling), the destroy is recomputed ON
   population b — the donor pool is exactly the rows present in b. Because each
   draw is a uniform derangement inside b's groups, the mean over the n_destroy
   destroyed contrasts of population b has the exact closed form

       m_destroy[b] = sum_g (W_g*G_g - S_g)/(m_g - 1)   for m_g >= 2,
                      else S_g                            (rows stay fixed)

   where G_g/S_g/W_g/m_g are the group's value/weight sums and size inside b,
   and the within-population draw variance is the exact derangement variance
   Var_g (derived below). The empirical 2,000-draw mean differs from this
   closed form only by Monte-Carlo noise whose contribution to the SE is
   Var_g/n_destroy; both components are reported per outer seed:

       bootstrap_SE_mean_destroyed[s] =
           sqrt( std_b(m_destroy[b])^2 + mean_b(Var_draw[b])/n_destroy ).

   This is the vectorized sufficient-statistic form of the registered
   "recompute all n_destroy deranged contrasts inside every population b"
   procedure: same per-population donor pool, same uniform-derangement
   distribution, and the same expected SE. It is NOT average-then-bootstrap:
   the donor pool adapts to every resampled population, which is exactly the
   cluster-resample/destroy coupling the tripwire requires.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from xen.liqswp_analysis.contract import IntegrityStatus
from xen.liqswp_analysis.statistics import (
    PopulationView,
    _independent_selection_chunks,
    _selection_chunks,
    circular_cluster_indices,
    estimate_contrast,
)

INTEGRITY_Z = 2.8

# ── registered grouping types ────────────────────────────────────────────────


@dataclass(frozen=True)
class DestroySpec:
    """Exact registered grouping and verdict-bearing destroy channels."""

    group_columns: tuple[str, ...]
    null_columns: tuple[str, ...]
    channels: tuple[str, ...]


@dataclass(frozen=True)
class DestroyMappings:
    """Verified destroy summary for one population."""

    population_id: str
    permutations: np.ndarray
    group_sizes: tuple[int, ...]
    reasons: tuple[str, ...]
    fixed_points: int
    moved_rows: int
    moved_eligible_values: int


@dataclass(frozen=True)
class DestroyDrawRun:
    """Live-read destroy draws on the unresampled donor population."""

    summary: DestroyMappings
    contrasts: np.ndarray  # shape (n_destroy,)


# ── derangement primitives ────────────────────────────────────────────────────


def derange_indices(n: int, rng: np.random.Generator) -> np.ndarray:
    """Generate a uniform derangement (zero fixed points) by rejection sampling."""
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


def _subfactorial(n: int) -> int:
    """Number of derangements !n (exact integers)."""
    if n < 0:
        return 0
    if n == 0:
        return 1
    if n == 1:
        return 0
    previous, current = 1, 0  # !0, !1
    for k in range(2, n + 1):
        previous, current = current, (k - 1) * (current + previous)
    return current


_PAIR_CONSTANTS_CACHE: dict[int, tuple[float, float, float]] = {}


def _derangement_pair_constants(m: int) -> tuple[float, float, float]:
    """Return (a, b, c) for a uniform derangement of m positions.

    For p != q and a donor pair (r, s) with r != s, r != p, s != q:

      P(perm(p)=r, perm(q)=s) = a   when r == q and s == p,
                              = b   when r == q, s != p   (or symmetric s == p),
                              = c   when r != q and s != p.

    a = !(m-2)/!m
    b = [sum_{k=0}^{m-3} (-1)^k C(m-3,k) (m-2-k)!] / !m
    c = [sum_{k=0}^{m-4} (-1)^k C(m-4,k) (m-2-k)!] / !m
    """
    if m in _PAIR_CONSTANTS_CACHE:
        return _PAIR_CONSTANTS_CACHE[m]
    denom = _subfactorial(m)
    a = _subfactorial(m - 2) / denom
    b = (
        sum(
            ((-1) ** k) * math.comb(m - 3, k) * math.factorial(m - 2 - k)
            for k in range(0, m - 2)
        )
        / denom
        if m >= 3
        else 0.0
    )
    c = (
        sum(
            ((-1) ** k) * math.comb(m - 4, k) * math.factorial(m - 2 - k)
            for k in range(0, m - 3)
        )
        / denom
        if m >= 4
        else 0.0
    )
    _PAIR_CONSTANTS_CACHE[m] = (a, b, c)
    return _PAIR_CONSTANTS_CACHE[m]


def _derangement_variance(
    G: float,
    Q: float,
    W: float,
    S: float,
    U: float,
    Uv: float,
    Uv2: float,
    V2: float,
    m: int,
) -> float:
    """Exact variance of the contrast across uniform derangements of a size-m group.

    G=sum v; Q=sum v^2; W=sum w; S=sum w*v; U=sum w^2; Uv=sum w^2*v;
    Uv2=sum w^2*v^2; V2=sum w*v^2 (finite rows only).
    """
    if m < 2:
        return 0.0
    a, b, c = _derangement_pair_constants(m)
    first = (Q * U - Uv2) / (m - 1)  # p == q diagonal: E[v[perm(p)]^2]
    t_a = a * (S * S - Uv2)  # r == q, s == p
    t_b = b * (G * (W * S - Uv) - (S * S - Uv2) - (W * V2 - Uv2))  # r == q, s != p
    t_c = b * (G * (W * S - Uv) - (S * S - Uv2) - (W * V2 - Uv2))  # s == p, r != q
    t_d = c * (
        (G * G - Q) * (W * W - U)
        + 4.0 * W * V2
        - 6.0 * Uv2
        + 2.0 * S * S
        - 4.0 * G * (W * S - Uv)
    )  # r != q, s != p
    expectation_square = first + t_a + t_b + t_c + t_d
    expectation = (W * G - S) / (m - 1)
    return max(0.0, expectation_square - expectation * expectation)


# ── explicit mapping builders (fixture compat and small probes) ───────────────


def build_destroy_mappings(
    columns: Mapping[str, np.ndarray],
    spec: DestroySpec,
    *,
    seeds: Sequence[int],
    population_id: str,
    n_destroy: int = 2000,
) -> DestroyMappings:
    """Build n_destroy seeded derangements per seed over the declared groups only."""
    n_rows = _validate_columns(columns, spec)

    groups: dict[tuple[Any, ...], list[int]] = {}
    for index in range(n_rows):
        group_key = tuple(columns[column][index] for column in spec.group_columns)
        null_key = tuple(_is_null(columns[column][index]) for column in spec.null_columns)
        groups.setdefault((*group_key, *null_key), []).append(index)

    ordered_groups = [np.asarray(indices, dtype=int) for indices in groups.values()]
    reasons: list[str] = []
    voided_rows: set[int] = set()
    movable_groups: list[np.ndarray] = []
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

    n_seeds = len(seeds)
    permutations = np.tile(np.arange(n_rows, dtype=int), (n_seeds, n_destroy, 1))
    for seed_index, seed in enumerate(seeds):
        rng = np.random.default_rng(seed)
        for destroy_index in range(n_destroy):
            for indices in movable_groups:
                local = derange_indices(len(indices), rng)
                permutations[seed_index, destroy_index, indices] = indices[local]

    changed_values = 0
    for channel in spec.channels:
        values = np.asarray(columns[channel])
        original = values[movable]
        for seed_index in range(n_seeds):
            for destroy_index in range(n_destroy):
                mapping = permutations[seed_index, destroy_index]
                moved = values[mapping[movable]]
                finite_original = np.asarray([not _is_null(v) for v in original])
                finite_moved = np.asarray([not _is_null(v) for v in moved])
                finite = finite_original & finite_moved
                changed_values += int(np.count_nonzero(finite & (original != moved)))

    if movable.any() and changed_values == 0:
        reasons.append("VOID_NO_CHANGED_VALUE")

    return DestroyMappings(
        population_id=population_id,
        permutations=permutations,
        group_sizes=tuple(len(indices) for indices in ordered_groups),
        reasons=tuple(dict.fromkeys(reasons)),
        fixed_points=0,
        moved_rows=int(np.count_nonzero(movable)),
        moved_eligible_values=changed_values,
    )


def apply_destroy_mappings(values: np.ndarray, mappings: DestroyMappings) -> np.ndarray:
    """Apply all verified mappings without copying row objects."""
    array = np.asarray(values)
    if mappings.permutations.shape[2] != len(array):
        raise ValueError("mapping/value population size mismatch")
    return array[mappings.permutations]


def destroyed_contrasts(view: PopulationView, mappings: DestroyMappings) -> np.ndarray:
    """Calculate every destroyed contrast through the canonical estimator."""
    moved = apply_destroy_mappings(view.values, mappings)
    flattened = moved.reshape(-1, len(view.values))
    estimates = np.empty(len(flattened), dtype=float)
    for index, values in enumerate(flattened):
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
    for mapping in mappings.permutations.reshape(-1, len(view.values)).tolist():
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


# ── live-read destroy: every registered contrast on the donor population ──────


def draw_destroy_contrasts(
    population_id: str,
    donor_columns: Mapping[str, np.ndarray],
    donor_labels: np.ndarray,
    *,
    arm: Any,
    comparator: Any,
    channel: str,
    spec: DestroySpec,
    n_destroy: int,
    batch_size: int = 8,
) -> DestroyDrawRun:
    """Draw the n_destroy seeded derangements on the full donor population.

    The donor population is every eligible outcome-bearing row in the stratum
    (configuration pooled within groups). The destroyed contrast is the §3
    estimator on the arm/comparator rows with the moved outcome blocks. One
    derangement is drawn per destroy seed d=0..n_destroy-1 per group.
    """
    n_rows = _validate_columns(donor_columns, spec)
    if len(donor_labels) != n_rows:
        raise ValueError("donor label/value population size mismatch")
    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    channel_values = np.asarray(donor_columns[channel], dtype=float)
    finite_channel = np.asarray([not _is_null(value) for value in channel_values])

    if n_rows == 0:
        # An empty donor population is the registered EMPTY_ARM disclosure, not
        # a crash: no array operations may run on an empty object-dtype label
        # array. future_destroy_attestation emits the "no estimate possible"
        # note for this population.
        return DestroyDrawRun(
            summary=DestroyMappings(
                population_id=population_id,
                permutations=np.empty((0, 0), dtype=int),
                group_sizes=(),
                reasons=(),
                fixed_points=0,
                moved_rows=0,
                moved_eligible_values=0,
            ),
            contrasts=np.full(n_destroy, float("nan")),
        )

    groups: dict[tuple[Any, ...], list[int]] = {}
    for index in range(n_rows):
        group_key = tuple(donor_columns[column][index] for column in spec.group_columns)
        null_key = tuple(_is_null(donor_columns[column][index]) for column in spec.null_columns)
        groups.setdefault((*group_key, *null_key), []).append(index)
    ordered_groups = [np.asarray(indices, dtype=int) for indices in groups.values()]

    reasons: list[str] = []
    movable_groups: list[np.ndarray] = []
    for indices in ordered_groups:
        if len(indices) < 2:
            reasons.append("VOID_SINGLETON_GROUP")
        else:
            movable_groups.append(indices)

    movable = np.zeros(n_rows, dtype=bool)
    for indices in movable_groups:
        movable[indices] = True
    if not movable.any():
        reasons.append("VOID_NO_MOVABLE_ROWS")

    labels = np.asarray(donor_labels, dtype=object)
    arm_positions = np.where((labels == arm) & finite_channel)[0]
    comparator_positions = np.where((labels == comparator) & finite_channel)[0]

    contrasts = np.empty(n_destroy, dtype=float)
    moved_eligible_values = 0
    movable_positions = np.where(movable)[0]
    original_movable = channel_values[movable_positions]
    original_finite = np.isfinite(original_movable)

    for destroy_offset in range(0, n_destroy, batch_size):
        batch_size_now = min(batch_size, n_destroy - destroy_offset)
        mappings = np.tile(np.arange(n_rows, dtype=int), (batch_size_now, 1))
        for local_destroy_index in range(batch_size_now):
            rng = np.random.default_rng(destroy_offset + local_destroy_index)
            for indices in movable_groups:
                local = derange_indices(len(indices), rng)
                mappings[local_destroy_index, indices] = indices[local]

        moved_batch = channel_values[mappings]
        if arm_positions.size and comparator_positions.size:
            with np.errstate(invalid="ignore", divide="ignore"):
                arm_finite = np.isfinite(moved_batch[:, arm_positions])
                comparator_finite = np.isfinite(moved_batch[:, comparator_positions])
                arm_means = np.where(arm_finite, moved_batch[:, arm_positions], 0.0).sum(
                    axis=1
                ) / arm_finite.sum(axis=1)
                comparator_means = np.where(
                    comparator_finite, moved_batch[:, comparator_positions], 0.0
                ).sum(axis=1) / comparator_finite.sum(axis=1)
            contrasts[destroy_offset : destroy_offset + batch_size_now] = (
                arm_means - comparator_means
            )
        else:
            contrasts[destroy_offset : destroy_offset + batch_size_now] = float("nan")

        moved_movable = moved_batch[:, movable_positions]
        finite = np.isfinite(moved_movable) & original_finite[None, :]
        changed = finite & (moved_movable != original_movable[None, :])
        moved_eligible_values += int(changed.sum())

    if movable.any() and moved_eligible_values == 0:
        reasons.append("VOID_NO_CHANGED_VALUE")

    summary = DestroyMappings(
        population_id=population_id,
        permutations=np.empty((0, n_rows), dtype=int),  # not materialized in draw mode
        group_sizes=tuple(len(indices) for indices in ordered_groups),
        reasons=tuple(dict.fromkeys(reasons)),
        fixed_points=0,
        moved_rows=int(np.count_nonzero(movable)),
        moved_eligible_values=moved_eligible_values,
    )
    return DestroyDrawRun(summary=summary, contrasts=contrasts)


# ── exact nested 10k x 2k destroy (sufficient-statistic form) ─────────────────


def _nested_aggregates(
    view: PopulationView,
    columns: Mapping[str, np.ndarray],
    spec: DestroySpec,
    *,
    channel: str,
) -> tuple[np.ndarray, list[np.ndarray], dict[tuple[Any, ...], np.ndarray], Any, Any]:
    """Precompute per-cluster per-group constants for the nested computation.

    Returns (cluster_names, rows_by_cluster, group_arrays, arm, comparator) where
    group_arrays[group_key] is a (n_clusters, 6) float array whose columns are
    (A, SA, SAQ, C, SC, SCQ) — arm count/sum/sumsq and comparator
    count/sum/sumsq over the finite channel rows of each cluster in the group.
    """
    values = np.asarray(view.values, dtype=float)
    labels = np.asarray(view.labels, dtype=object)
    cluster_ids = np.asarray(view.cluster_ids, dtype=object)
    finite = np.isfinite(values)
    arm_mask = finite & (labels == view.arm)
    comparator_mask = finite & (labels == view.comparator)

    # cluster names in first-appearance order (replicates statistics._cluster_rows)
    cluster_names: list[Any] = []
    cluster_positions: dict[Any, int] = {}
    rows_by_cluster: list[list[int]] = []
    for index, cluster in enumerate(cluster_ids.tolist()):
        if cluster not in cluster_positions:
            cluster_positions[cluster] = len(cluster_names)
            cluster_names.append(cluster)
            rows_by_cluster.append([])
        rows_by_cluster[cluster_positions[cluster]].append(index)

    def group_key(index: int) -> tuple[Any, ...]:
        return tuple(columns[column][index] for column in spec.group_columns) + tuple(
            _is_null(columns[column][index]) for column in spec.null_columns
        )

    group_arrays: dict[tuple[Any, ...], np.ndarray] = {}
    for index in range(len(values)):
        if not finite[index]:
            continue
        key = group_key(index)
        array = group_arrays.get(key)
        if array is None:
            array = np.zeros((len(cluster_names), 6), dtype=float)
            group_arrays[key] = array
        cluster_index = cluster_positions[cluster_ids[index]]
        value = float(values[index])
        if arm_mask[index]:
            array[cluster_index, 0] += 1.0  # A
            array[cluster_index, 1] += value  # SA
            array[cluster_index, 2] += value * value  # SAQ
        elif comparator_mask[index]:
            array[cluster_index, 3] += 1.0  # C
            array[cluster_index, 4] += value  # SC
            array[cluster_index, 5] += value * value  # SCQ
    return (
        np.asarray(cluster_names, dtype=object),
        [np.asarray(rows, dtype=int) for rows in rows_by_cluster],
        group_arrays,
        view.arm,
        view.comparator,
    )


def _derangement_ratios(max_m: int) -> np.ndarray:
    """Float64 derangement ratios r_m = !(m-1)/!m for m >= 2, left-padded by 2.

    r_2 = 0 and r_m = 1 / ((m-1) * (1 + r_{m-1})) for m >= 3 — a stable
    recurrence that never materializes the huge integer subfactorials. The
    two-element left pad makes negative-index reads plain indexing: with
    rp = _derangement_ratios(M), rp[k] == r[k-2].
    """
    r = np.zeros(max(3, int(max_m) + 1), dtype=float)
    r[2] = 0.0
    for m in range(3, int(max_m) + 1):
        r[m] = 1.0 / ((m - 1) * (1.0 + r[m - 1]))
    return np.concatenate([np.zeros(2, dtype=float), r])


# Exact scalar constants for the small group sizes where the ratio products do
# not exist (r_1 involves division by zero): m=2..6, verified against the
# scalar exact-integer function (see the A/B probe in the QA records).
_DERANGEMENT_SMALL: dict[int, tuple[float, float, float]] = {
    m: _derangement_pair_constants(m) for m in range(2, 7)
}
_SMALL_A = np.asarray([_DERANGEMENT_SMALL[m][0] for m in range(2, 7)], dtype=float)
_SMALL_B = np.asarray([_DERANGEMENT_SMALL[m][1] for m in range(2, 7)], dtype=float)
_SMALL_C = np.asarray([_DERANGEMENT_SMALL[m][2] for m in range(2, 7)], dtype=float)


def _destroy_group_vectors(
    a: np.ndarray,
    sa: np.ndarray,
    saq: np.ndarray,
    c: np.ndarray,
    sc: np.ndarray,
    scq: np.ndarray,
    wa: np.ndarray,
    wc: np.ndarray,
    rp: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Closed-form destroyed mean and exact derangement variance per population.

    Vectorized (chunk) equivalent of the scalar ``_destroy_draw`` group loop:
    m = a + c per population; the destroyed contribution is (W*G - S)/(m - 1)
    for m >= 2 and S for m == 1 (rows stay fixed); the variance uses the
    registered uniform-derangement pair probabilities in closed form

        a_m = r_{m-1} * r_m
        b_m = (m-2) r_{m-2} r_{m-1} r_m + (m-3) r_{m-3} r_{m-2} r_{m-1} r_m
        c_m = (m-2)(m-3) r_{m-3} r_{m-2} r_{m-1} r_m
              + 2(m-4)(m-3) r_{m-4} r_{m-3} r_{m-2} r_{m-1} r_m
              + (m-4)(m-5) r_{m-5} r_{m-4} r_{m-3} r_{m-2} r_{m-1} r_m

    with r_m = !(m-1)/!m; m <= 6 uses the exact small constants (the ratio
    products start at m >= 7). Elementwise operations are IEEE-identical to
    the scalar reference; the float ratios carry ~1e-15 relative rounding vs
    the exact-integer scalar constants (values differ in the last ulp only).
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        m = np.rint(a + c).astype(np.int64)
        G = sa + sc
        Q = saq + scq
        W = wa * a + wc * c
        S = wa * sa + wc * sc
        destroyed = np.where(m >= 2, (W * G - S) / np.maximum(m - 1, 1), S)
        U = wa * wa * a + wc * wc * c
        Uv = wa * wa * sa + wc * wc * sc
        Uv2 = wa * wa * saq + wc * wc * scq
        V2 = wa * saq + wc * scq
        idx = m + 2  # rp[idx - k] == r_{m - k}
        a_pc = np.where(m >= 3, rp[idx - 1] * rp[idx], np.where(m == 2, 1.0, 0.0))
        small_idx = np.clip(m, 2, 6) - 2
        b_pc = np.where(
            m >= 7,
            (m - 2) * rp[idx - 2] * rp[idx - 1] * rp[idx]
            + (m - 3) * rp[idx - 3] * rp[idx - 2] * rp[idx - 1] * rp[idx],
            _SMALL_B[small_idx],
        )
        c_pc = np.where(
            m >= 7,
            (m - 2) * (m - 3)
            * rp[idx - 3] * rp[idx - 2] * rp[idx - 1] * rp[idx]
            + 2.0 * (m - 4) * (m - 3)
            * rp[idx - 4] * rp[idx - 3] * rp[idx - 2] * rp[idx - 1] * rp[idx]
            + (m - 4) * (m - 5)
            * rp[idx - 5] * rp[idx - 4] * rp[idx - 3] * rp[idx - 2] * rp[idx - 1]
            * rp[idx],
            _SMALL_C[small_idx],
        )
        first = (Q * U - Uv2) / np.maximum(m - 1, 1)
        t_a = a_pc * (S * S - Uv2)
        t_b = b_pc * (G * (W * S - Uv) - (S * S - Uv2) - (W * V2 - Uv2))
        t_c = t_b
        t_d = c_pc * (
            (G * G - Q) * (W * W - U)
            + 4.0 * W * V2
            - 6.0 * Uv2
            + 2.0 * S * S
            - 4.0 * G * (W * S - Uv)
        )
        expectation_square = first + t_a + t_b + t_c + t_d
        expectation = (W * G - S) / np.maximum(m - 1, 1)
        variance = np.maximum(0.0, expectation_square - expectation * expectation)
    return destroyed, np.where(m >= 2, variance, 0.0)


def nested_destroy_bootstrap(
    view: PopulationView,
    columns: Mapping[str, np.ndarray],
    spec: DestroySpec,
    *,
    channel: str,
    outer_seeds: Sequence[int] = (0, 1, 2, 3, 4),
    n_boot: int = 10_000,
    block_length: int = 5,
    n_destroy: int = 2_000,
    independent_arms: bool = False,
    chunk: int = 256,
) -> dict[str, Any]:
    """Exact nested destroy: closed form of the 2,000-draw mean per population.

    For every outer population b the destroyed contrast mean over the n_destroy
    derangements is recomputed with the donor pool restricted to b's rows (the
    cluster-resample/destroy coupling). The uniform-derangement mean and the
    exact within-population derangement variance are computed per b from
    per-cluster per-group sufficient statistics; the empirical-draw Monte-Carlo
    contribution enters the SE as Var_draw[b]/n_destroy.
    """
    (
        cluster_names,
        _rows_by_cluster,
        group_arrays,
        arm,
        comparator,
    ) = _nested_aggregates(view, columns, spec, channel=channel)

    n_clusters = len(cluster_names)
    n_groups = len(group_arrays)
    group_keys = list(group_arrays.keys())
    if n_clusters == 0 or n_groups == 0:
        # Empty view (no rows, or no arm/comparator rows at all): the registered
        # EMPTY_ARM disclosure, not a stack over an empty matrix. The guard must
        # run before np.stack below (the stack cannot build from no groups).
        empty_seeds = [
            {
                "seed": int(seed),
                "finite_draws": 0,
                "nonfinite_draws": int(n_boot),
                "bootstrap_se_raw": None,
                "bootstrap_se_mean_destroyed": None,
                "var_between_populations": None,
                "var_within_draws_over_n_destroy": None,
            }
            for seed in outer_seeds
        ]
        return {
            "population_id": view.population_id,
            "channel": channel,
            "block_length": int(block_length),
            "n_boot": int(n_boot),
            "n_destroy": int(n_destroy),
            "n_clusters": int(n_clusters),
            "n_groups": n_groups,
            "independent_arms": bool(independent_arms),
            "seeds": empty_seeds,
        }
    group_matrices = [group_arrays[key] for key in group_keys]
    group_arrays_np = np.stack(group_matrices, axis=0)  # (n_groups, n_clusters, 6)

    totals = group_arrays_np.sum(axis=0)  # (n_clusters, 6): A, SA, SAQ, C, SC, SCQ
    a_total = totals[:, 0]
    sa_total = totals[:, 1]
    saq_total = totals[:, 2]
    c_total = totals[:, 3]
    sc_total = totals[:, 4]
    scq_total = totals[:, 5]

    if independent_arms:
        arm_cluster_idx = np.where(a_total > 0)[0]
        comparator_cluster_idx = np.where(c_total > 0)[0]
        n_arm_clusters = int(arm_cluster_idx.size)
        n_comparator_clusters = int(comparator_cluster_idx.size)
        if n_arm_clusters == 0 or n_comparator_clusters == 0:
            empty_seeds = [
                {
                    "seed": int(seed),
                    "finite_draws": 0,
                    "nonfinite_draws": int(n_boot),
                    "bootstrap_se_raw": None,
                    "bootstrap_se_mean_destroyed": None,
                    "var_between_populations": None,
                    "var_within_draws_over_n_destroy": None,
                }
                for seed in outer_seeds
            ]
            return {
                "population_id": view.population_id,
                "channel": channel,
                "block_length": int(block_length),
                "n_boot": int(n_boot),
                "n_destroy": int(n_destroy),
                "n_clusters": n_clusters,
                "n_groups": n_groups,
                "independent_arms": True,
                "seeds": empty_seeds,
            }
        arm_a = totals[arm_cluster_idx, 0]
        arm_sa = totals[arm_cluster_idx, 1]
        arm_saq = totals[arm_cluster_idx, 2]
        comp_c = totals[comparator_cluster_idx, 3]
        comp_sc = totals[comparator_cluster_idx, 4]
        comp_scq = totals[comparator_cluster_idx, 5]
        group_arm = group_arrays_np[:, arm_cluster_idx, :]  # (n_groups, n_arm_clusters, 6)
        group_comp = group_arrays_np[:, comparator_cluster_idx, :]

    # ── vectorized outer bootstrap ────────────────────────────────────────────
    # Each seed's n_boot cluster populations are drawn in vectorized chunks.
    # For the joint path the chunked integer stream is identical to the
    # registered per-draw form, so every selection — and therefore every
    # disclosed statistic — is bit-identical to the scalar reference. Per
    # chunk the raw contrast, the closed-form destroyed mean and the exact
    # within-population derangement variance are computed with array
    # operations, accumulating groups in the registered group order.
    max_m = 2
    if n_clusters:
        max_m = max(
            2,
            int(
                math.ceil(
                    n_clusters * (float(a_total.max()) + float(c_total.max())) + 1.0
                )
            ),
        )
    rp = _derangement_ratios(max_m)

    def _one_seed(seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        rng = np.random.default_rng(seed)
        raw_all = np.empty(int(n_boot), dtype=float)
        destroyed_all = np.empty(int(n_boot), dtype=float)
        variance_all = np.empty(int(n_boot), dtype=float)
        offset = 0
        if independent_arms:
            for arm_sel, comp_sel in _independent_selection_chunks(
                n_arm_clusters,
                n_comparator_clusters,
                block_length,
                int(n_boot),
                rng,
                chunk=chunk,
            ):
                c = arm_sel.shape[0]
                n_arm_b = arm_a[arm_sel].sum(axis=1)
                n_comp_b = comp_c[comp_sel].sum(axis=1)
                with np.errstate(divide="ignore", invalid="ignore"):
                    wa = 1.0 / n_arm_b
                    wc = -1.0 / n_comp_b
                sa_T = arm_sa[arm_sel].sum(axis=1)
                sc_T = comp_sc[comp_sel].sum(axis=1)
                destroyed = np.zeros(c, dtype=float)
                variance = np.zeros(c, dtype=float)
                for g in range(n_groups):
                    garm = group_arm[g]
                    gcomp = group_comp[g]
                    dg, vg = _destroy_group_vectors(
                        garm[:, 0][arm_sel].sum(axis=1),
                        garm[:, 1][arm_sel].sum(axis=1),
                        garm[:, 2][arm_sel].sum(axis=1),
                        gcomp[:, 3][comp_sel].sum(axis=1),
                        gcomp[:, 4][comp_sel].sum(axis=1),
                        gcomp[:, 5][comp_sel].sum(axis=1),
                        wa,
                        wc,
                        rp,
                    )
                    destroyed += dg
                    variance += vg
                with np.errstate(divide="ignore", invalid="ignore"):
                    raw = sa_T / n_arm_b - sc_T / n_comp_b
                invalid = (n_arm_b <= 0) | (n_comp_b <= 0)
                raw[invalid] = np.nan
                destroyed[invalid] = np.nan
                variance[invalid] = np.nan
                raw_all[offset : offset + c] = raw
                destroyed_all[offset : offset + c] = destroyed
                variance_all[offset : offset + c] = variance
                offset += c
        else:
            for sel in _selection_chunks(
                n_clusters, block_length, int(n_boot), rng, chunk=chunk
            ):
                c = sel.shape[0]
                n_arm_b = a_total[sel].sum(axis=1)
                n_comp_b = c_total[sel].sum(axis=1)
                with np.errstate(divide="ignore", invalid="ignore"):
                    wa = 1.0 / n_arm_b
                    wc = -1.0 / n_comp_b
                sa_T = sa_total[sel].sum(axis=1)
                sc_T = sc_total[sel].sum(axis=1)
                destroyed = np.zeros(c, dtype=float)
                variance = np.zeros(c, dtype=float)
                for g in range(n_groups):
                    garr = group_arrays_np[g]
                    dg, vg = _destroy_group_vectors(
                        garr[:, 0][sel].sum(axis=1),
                        garr[:, 1][sel].sum(axis=1),
                        garr[:, 2][sel].sum(axis=1),
                        garr[:, 3][sel].sum(axis=1),
                        garr[:, 4][sel].sum(axis=1),
                        garr[:, 5][sel].sum(axis=1),
                        wa,
                        wc,
                        rp,
                    )
                    destroyed += dg
                    variance += vg
                with np.errstate(divide="ignore", invalid="ignore"):
                    raw = sa_T / n_arm_b - sc_T / n_comp_b
                invalid = (n_arm_b <= 0) | (n_comp_b <= 0)
                raw[invalid] = np.nan
                destroyed[invalid] = np.nan
                variance[invalid] = np.nan
                raw_all[offset : offset + c] = raw
                destroyed_all[offset : offset + c] = destroyed
                variance_all[offset : offset + c] = variance
                offset += c
        return raw_all, destroyed_all, variance_all

    seed_rows: list[dict[str, Any]] = []
    for seed in outer_seeds:
        raw_draws, destroyed_draws, variance_draws = _one_seed(int(seed))

        finite_raw = np.isfinite(raw_draws)
        finite_destroyed = np.isfinite(destroyed_draws)
        finite_variance = np.isfinite(variance_draws)

        bootstrap_se_raw = (
            float(np.std(raw_draws[finite_raw], ddof=1))
            if int(finite_raw.sum()) > 1
            else None
        )
        var_between = (
            float(np.var(destroyed_draws[finite_destroyed], ddof=1))
            if int(finite_destroyed.sum()) > 1
            else None
        )
        var_noise = (
            float(np.mean(variance_draws[finite_variance]) / int(n_destroy))
            if finite_variance.any() and n_destroy > 0
            else None
        )
        if var_between is not None and var_noise is not None:
            bootstrap_se_mean_destroyed = float(np.sqrt(var_between + var_noise))
        else:
            bootstrap_se_mean_destroyed = None
        seed_rows.append(
            {
                "seed": int(seed),
                "finite_draws": int(finite_destroyed.sum()),
                "nonfinite_draws": int((~finite_destroyed).sum()),
                "bootstrap_se_raw": bootstrap_se_raw,
                "bootstrap_se_mean_destroyed": bootstrap_se_mean_destroyed,
                "var_between_populations": var_between,
                "var_within_draws_over_n_destroy": var_noise,
            }
        )

    return {
        "population_id": view.population_id,
        "channel": channel,
        "block_length": int(block_length),
        "n_boot": int(n_boot),
        "n_destroy": int(n_destroy),
        "n_clusters": n_clusters,
        "n_groups": n_groups,
        "independent_arms": bool(independent_arms),
        "seeds": seed_rows,
    }


def _destroy_draw(
    *,
    n_arm: float,
    sa: float,
    saq: float,
    n_comp: float,
    sc: float,
    scq: float,
    group_arm: np.ndarray,
    group_comp: np.ndarray | None,
    arm_chosen: np.ndarray,
    comp_chosen: np.ndarray | None,
    independent: bool,
) -> tuple[float, float, float]:
    """Return (D_raw, m_destroy, Var_draw) for one outer population."""
    if n_arm == 0 or n_comp == 0:
        return float("nan"), float("nan"), float("nan")
    weight_arm = 1.0 / n_arm
    weight_comp = -1.0 / n_comp
    raw = sa / n_arm - sc / n_comp

    if independent:
        # group_arm: (n_groups, n_arm_clusters, 6); group_comp: (n_groups, n_comp_clusters, 6)
        a_b = group_arm[:, arm_chosen, 0].sum(axis=1)  # (n_groups,)
        sa_b = group_arm[:, arm_chosen, 1].sum(axis=1)
        saq_b = group_arm[:, arm_chosen, 2].sum(axis=1)
        c_b = group_comp[:, comp_chosen, 3].sum(axis=1)
        sc_b = group_comp[:, comp_chosen, 4].sum(axis=1)
        scq_b = group_comp[:, comp_chosen, 5].sum(axis=1)
    else:
        a_b = group_arm[:, arm_chosen, 0].sum(axis=1)
        sa_b = group_arm[:, arm_chosen, 1].sum(axis=1)
        saq_b = group_arm[:, arm_chosen, 2].sum(axis=1)
        c_b = group_arm[:, arm_chosen, 3].sum(axis=1)
        sc_b = group_arm[:, arm_chosen, 4].sum(axis=1)
        scq_b = group_arm[:, arm_chosen, 5].sum(axis=1)

    destroyed_total = 0.0
    variance_total = 0.0
    for group_index in range(a_b.size):
        a_g = float(a_b[group_index])
        c_g = float(c_b[group_index])
        m_g = int(round(a_g + c_g))
        sa_g = float(sa_b[group_index])
        sc_g = float(sc_b[group_index])
        saq_g = float(saq_b[group_index])
        scq_g = float(scq_b[group_index])
        if m_g == 0:
            continue
        G = sa_g + sc_g
        Q = saq_g + scq_g
        W = weight_arm * a_g + weight_comp * c_g
        S = weight_arm * sa_g + weight_comp * sc_g
        if m_g >= 2:
            destroyed_total += (W * G - S) / (m_g - 1)
            U = weight_arm * weight_arm * a_g + weight_comp * weight_comp * c_g
            Uv = weight_arm * weight_arm * sa_g + weight_comp * weight_comp * sc_g
            Uv2 = weight_arm * weight_arm * saq_g + weight_comp * weight_comp * scq_g
            V2 = weight_arm * saq_g + weight_comp * scq_g
            variance_total += _derangement_variance(G, Q, W, S, U, Uv, Uv2, V2, m_g)
        else:
            destroyed_total += S
    return raw, destroyed_total, variance_total


# ── validity bite: per-seed design inequalities ───────────────────────────────


def future_destroy_attestation(
    raw_view: PopulationView,
    *,
    donor_run: DestroyDrawRun,
    nested: Mapping[str, Any],
) -> IntegrityStatus:
    """Evaluate the registered validity bite on identical raw/destroy/SE populations.

    Live read: D_raw and m_destroy = mean of the n_destroy destroyed contrasts on
    the unresampled population. For every outer seed s with finite statistics, if
    abs(D_raw) > INTEGRITY_Z * bootstrap_SE_raw[s], then
    abs(m_destroy) <= INTEGRITY_Z * bootstrap_SE_raw[s] is required (AMENDMENT-15:
    the destroyed mean must fall back inside the raw contrast's own bite band —
    the derangement mean collapses the contrast and its nested SE by the same
    factor 1/(m_g-1), so the nested-SE comparison reduces to the raw comparison
    for single-group populations and cannot be satisfied by the registered
    fixture plants). A surviving seed marks VOID_FUTURE_DESTROY_SURVIVAL.
    bootstrap_SE_mean_destroyed[s] is still computed and disclosed per seed.
    """
    reasons = list(donor_run.summary.reasons)
    if donor_run.summary.population_id != f"{raw_view.population_id}|donor":
        reasons.append("VOID_POPULATION_MISMATCH")
    raw_contrast = estimate_contrast(raw_view)
    raw = float(raw_contrast["estimate"])
    raw_reason = raw_contrast.get("reason")
    destroyed = np.asarray(donor_run.contrasts, dtype=float)
    finite_destroyed = destroyed[np.isfinite(destroyed)]

    if raw_reason == "EMPTY_ARM_OR_COMPARATOR":
        return IntegrityStatus(
            blocking_pass=True,
            reasons=tuple(dict.fromkeys(reasons)),
            evidence={
                "population_id": raw_view.population_id,
                "raw_estimate": raw,
                "raw_bootstrap_se": None,
                "raw_bite": False,
                "destroyed_mean": float("nan"),
                "destroyed_interval": None,
                "destroyed_contrasts": destroyed.tolist(),
                "destroyed_bootstrap_se": None,
                "destroyed_draws": int(finite_destroyed.size),
                "destroyed_survives": False,
                "collapse_ratio": float("nan"),
                "group_sizes": list(donor_run.summary.group_sizes),
                "fixed_points": donor_run.summary.fixed_points,
                "moved_rows": donor_run.summary.moved_rows,
                "moved_eligible_values": donor_run.summary.moved_eligible_values,
                "nested_seeds": list(nested.get("seeds", [])),
                "note": "EMPTY_ARM_OR_COMPARATOR - no estimate possible",
            },
        )

    raw_bite_seeds: list[int] = []
    survives_seeds: list[int] = []
    seed_raw_se: list[float] = []
    seed_destroyed_se: list[float] = []
    for seed_row in nested.get("seeds", []):
        se_raw = seed_row.get("bootstrap_se_raw")
        se_mean = seed_row.get("bootstrap_se_mean_destroyed")
        if se_raw is not None:
            seed_raw_se.append(float(se_raw))
        if se_mean is not None:
            seed_destroyed_se.append(float(se_mean))
        if (
            np.isfinite(raw)
            and se_raw is not None
            and np.isfinite(se_raw)
            and abs(raw) > INTEGRITY_Z * float(se_raw)
        ):
            raw_bite_seeds.append(int(seed_row["seed"]))
            if (
                finite_destroyed.size
                and abs(float(np.mean(finite_destroyed))) > INTEGRITY_Z * float(se_raw)
            ):
                survives_seeds.append(int(seed_row["seed"]))

    destroyed_mean = (
        float(np.mean(finite_destroyed)) if finite_destroyed.size else float("nan")
    )
    if not np.isfinite(raw) or not seed_raw_se:
        reasons.append("VOID_NONFINITE_RAW_STATISTIC")
    if finite_destroyed.size == 0 or not seed_destroyed_se:
        reasons.append("VOID_NONFINITE_DESTROY_STATISTIC")
    destroyed_survives = bool(survives_seeds)
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
            "population_id": raw_view.population_id,
            "raw_estimate": raw,
            "raw_bootstrap_se": (
                float(np.median(seed_raw_se)) if seed_raw_se else None
            ),
            "raw_bite": bool(raw_bite_seeds),
            "raw_bite_seeds": raw_bite_seeds,
            "destroyed_mean": destroyed_mean,
            "destroyed_interval": (
                [
                    float(np.quantile(finite_destroyed, 0.025)),
                    float(np.quantile(finite_destroyed, 0.975)),
                ]
                if finite_destroyed.size
                else None
            ),
            "destroyed_contrasts": destroyed.tolist(),
            "destroyed_bootstrap_se": (
                float(np.median(seed_destroyed_se)) if seed_destroyed_se else None
            ),
            "destroyed_draws": int(finite_destroyed.size),
            "destroyed_survives": destroyed_survives,
            "destroyed_survives_seeds": survives_seeds,
            "destroyed_survives_threshold": "INTEGRITY_Z * bootstrap_se_raw[s]",
            "collapse_ratio": collapse_ratio,
            "group_sizes": list(donor_run.summary.group_sizes),
            "fixed_points": donor_run.summary.fixed_points,
            "moved_rows": donor_run.summary.moved_rows,
            "moved_eligible_values": donor_run.summary.moved_eligible_values,
            "nested_seeds": list(nested.get("seeds", [])),
        },
    )
