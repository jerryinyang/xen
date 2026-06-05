"""Experiment-local loose-referee derivation and 4h split-sensitivity evaluator
for EXP-012.

This module changes nothing in the frozen ``xen.referee_calibration`` harness. It
adds exactly two EXP-012-specific things on top of the frozen primitives:

1. **Loose-referee verdict derivation (single chronological split).** The loose
   referee is the EXP-006 / EXP-011 tau operating point: identical to the frozen
   5-check gate stack except the L5 materiality leg uses ``ci_lower_bps > tau_bps``
   with ``tau_bps = tau_multiplier * materiality_bps`` instead of the strict
   ``ci_lower_bps > materiality_bps`` (tau=1.0). L1-L4 are taken unchanged from the
   frozen :func:`xen.referee_calibration.gate_stack_core`. :func:`gate_verdict_rows`
   derives both the loose and the strict (tau=1.0 reference) verdict from one core,
   so the single-split arm is bit-identical to the frozen gate at tau=1.0.

2. **Anchored walk-forward, pooled-OOS loose evaluation (4h split gate only).**
   :func:`evaluate_partition_gate` reproduces the corrected EXP-010 estimator
   (test-size-weighted, per-resample average of per-fold bootstrap-mean
   distributions = stratified bootstrap of the pooled-OOS mean; adversarial-review
   F01) and applies the same loose / strict L5 thresholds. For a single contiguous
   fold it reduces exactly to the frozen gate, which the orchestrator asserts as a
   reference-reproduction check. The walk-forward fold boundaries are timestamp-
   mapped from the shared 1-minute ``CloseTime`` base into the 4h domain (never
   per-timeframe row fractions), exactly as EXP-010 does.

No file under ``python/src/xen`` is modified.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from xen.referee_calibration import (
    DOMAIN_SPECS,
    block_bootstrap_means,
    ci_from_means,
    cost_bps_for,
    count_state_episodes,
    estimate_block_length,
    finite_values,
    materiality_bps_for,
    naive_momentum_positions,
    strategy_return_bps,
)

# Anchored walk-forward parameters for the 4h split-sensitivity gate. Frozen,
# untuned, and identical to the EXP-010 corrected protocol (K=5, 50% warmup).
WALK_FORWARD_FOLDS = 5
WALK_FORWARD_WARMUP_FRACTION = 0.5
# Per-fold bootstrap-seed stride. Fold 0 keeps the frozen base offsets so the
# single-fold path is seed-identical to the frozen harness; later folds are offset
# to decorrelate their resamples (identical to EXP-010 ``_FOLD_SEED_STRIDE``).
_FOLD_SEED_STRIDE = 1000

Fold = tuple[np.ndarray, np.ndarray]  # (train_idx, test_idx)


# --------------------------------------------------------------------------- #
# Loose / strict verdict derivation from a frozen gate-stack core
# --------------------------------------------------------------------------- #
def _gate_passed(
    ci_lower: float, ci_naive_lower: float, *, l1: bool, l2: bool, l4: bool, l5_threshold_bps: float
) -> tuple[bool, bool]:
    """Conjoin the 5 gate legs for a given L5 threshold.

    Parameters
    ----------
    ci_lower : float
        Neutral block-bootstrap CI lower bound (bps) for this alpha.
    ci_naive_lower : float
        Vs-naive block-bootstrap CI lower bound (bps) for this alpha.
    l1, l2, l4 : bool
        Alpha-independent readiness / integrity / stability legs from the core.
    l5_threshold_bps : float
        The L5 materiality threshold (``tau_bps`` for loose, ``materiality_bps``
        for strict).

    Returns
    -------
    tuple[bool, bool]
        ``(passed, l5)`` where ``l5 = ci_lower > l5_threshold_bps`` and ``passed``
        is the conjunction of all five legs.
    """
    l3 = bool(ci_lower > 0.0 and ci_naive_lower > 0.0)
    l5 = bool(ci_lower > l5_threshold_bps)
    passed = bool(l1 and l2 and l3 and l4 and l5)
    return passed, l5


def gate_verdict_rows(
    core: dict[str, Any],
    *,
    alpha_values: tuple[float, ...],
    tau_bps: float,
    base_label: dict[str, Any],
) -> list[dict[str, Any]]:
    """Derive loose and strict (tau=1.0) gate verdicts from one frozen core.

    The core is :func:`xen.referee_calibration.gate_stack_core` output. Both
    referees share L1-L4 and the neutral/vs-naive bootstrap-mean distributions;
    only the L5 threshold differs (``tau_bps`` for loose, ``materiality_bps`` for
    strict). The strict rows reproduce the frozen gate exactly.

    Parameters
    ----------
    core : dict[str, Any]
        Alpha-independent gate state for one draw.
    alpha_values : tuple[float, ...]
        Operating points for the percentile CIs.
    tau_bps : float
        Loose L5 threshold for this domain (``tau_multiplier * materiality_bps``).
    base_label : dict[str, Any]
        Draw labels copied onto every emitted row.

    Returns
    -------
    list[dict[str, Any]]
        ``2 * len(alpha_values)`` rows (loose + strict per alpha).
    """
    materiality_bps = core["materiality_bps"]
    rows: list[dict[str, Any]] = []
    for alpha in alpha_values:
        ci_neutral = ci_from_means(
            core["neutral_mean"], core["neutral_means"], core["n_neutral"], alpha=alpha
        )
        ci_naive = ci_from_means(
            core["naive_mean"], core["naive_means"], core["n_naive"], alpha=alpha
        )
        for referee, threshold in (("loose", tau_bps), ("strict", materiality_bps)):
            passed, _l5 = _gate_passed(
                ci_neutral.lower,
                ci_naive.lower,
                l1=core["l1"],
                l2=core["l2"],
                l4=core["l4"],
                l5_threshold_bps=threshold,
            )
            rows.append(
                {
                    **base_label,
                    "referee": referee,
                    "alpha": alpha,
                    "passed": passed,
                    "effect_bps": ci_neutral.mean,
                    "ci_lower_bps": ci_neutral.lower,
                    "tau_bps": threshold,
                    "effective_n": core["effective_n"],
                    "block_length": core["block_length"],
                }
            )
    return rows


# --------------------------------------------------------------------------- #
# Anchored walk-forward folds (timestamp-mapped, within the first-70% set only)
# --------------------------------------------------------------------------- #
def mapped_fold_edges(
    base_times: np.ndarray, aligned_times: np.ndarray, fractions: np.ndarray, n: int
) -> list[int]:
    """Map shared 1-minute ``CloseTime`` boundary fractions into domain indices.

    A boundary at fraction ``f`` is the timestamp of 1-minute base row
    ``floor(f * n_base)``; that timestamp is mapped into this domain by counting
    domain return rows at or before it (identical to
    :func:`xen.referee_calibration.domain_split_index` and EXP-010's
    ``_mapped_fold_edges``). Fold boundaries are therefore shared across domains as
    ``CloseTime`` timestamps, never per-timeframe row fractions.
    """
    n_base = len(base_times)
    edges: list[int] = []
    for fraction in fractions:
        if fraction <= 0.0:
            edges.append(0)
            continue
        if fraction >= 1.0:
            edges.append(n)
            continue
        base_pos = min(int(fraction * n_base), n_base - 1)
        boundary_ts = base_times[base_pos]
        index = int(np.count_nonzero(aligned_times <= boundary_ts))
        edges.append(max(0, min(index, n)))
    return edges


def single_split_folds(n: int, split_index: int) -> list[Fold]:
    """One contiguous fold at the mandated chronological boundary (= frozen gate)."""
    cut = int(split_index)
    if n >= 2:
        cut = max(1, min(cut, n - 1))
    return [(np.arange(0, cut), np.arange(cut, n))]


def walk_forward_folds(edges: list[int]) -> list[Fold]:
    """Anchored (expanding) walk-forward folds from pre-mapped boundary indices.

    Fold ``i`` trains on all rows strictly before its contiguous test block, so
    every training set is strictly causal; out-of-sample = the union of the test
    blocks. Degenerate (empty) blocks are skipped. Mirrors EXP-010.
    """
    folds: list[Fold] = []
    for i in range(len(edges) - 1):
        test_start, test_end = int(edges[i]), int(edges[i + 1])
        if test_end <= test_start or test_start <= 0:
            continue
        folds.append((np.arange(0, test_start), np.arange(test_start, test_end)))
    return folds


# --------------------------------------------------------------------------- #
# Pooled-OOS (stratified) combination of per-fold bootstrap-mean distributions
# --------------------------------------------------------------------------- #
def _weighted_combine(means_parts: list[np.ndarray], counts: list[int]) -> np.ndarray:
    """Stratified pooled-OOS bootstrap: per-resample, size-weighted fold means.

    Each fold contributes one block-bootstrap mean distribution on its own disjoint
    out-of-sample test rows. Averaging those distributions per resample with
    population weights ``n_fold / sum(n_fold)`` yields bootstrap replicates of the
    pooled-OOS mean, so the combined CI scales with the pooled OOS size, not the
    per-fold size. This is the corrected EXP-010 estimator (adversarial-review
    F01); for a single contiguous fold it returns that fold's means unchanged.
    """
    pairs = [(m, c) for m, c in zip(means_parts, counts) if c > 0 and len(m) > 0]
    if not pairs:
        return np.empty(0, dtype=float)
    length = min(len(m) for m, _ in pairs)
    matrix = np.vstack([m[:length] for m, _ in pairs])
    weights = np.array([c for _, c in pairs], dtype=float)
    weights = weights / weights.sum()
    return (weights[:, None] * matrix).sum(axis=0)


def _mean_or(values: np.ndarray, default: float) -> float:
    """Mean of finite ``values``; ``default`` for an empty array."""
    finite = finite_values(values)
    return float(np.mean(finite)) if len(finite) else default


def _partition_core(
    returns: np.ndarray,
    positions: np.ndarray,
    *,
    instrument: str,
    domain: str,
    folds: list[Fold],
    n_bootstrap: int,
    seed: int,
) -> dict[str, Any]:
    """Per-fold frozen-leg gate core combined over the pooled out-of-sample rows.

    Block length is estimated on each fold's own (disjoint) training returns and
    the neutral / vs-naive bootstraps run on each fold's own out-of-sample test
    returns, so no row contaminates the block length or stability mean of a fold in
    which it is scored out-of-sample. Fold outputs are combined with the corrected
    stratified pooled-OOS estimator. Reuses only frozen ``xen`` primitives.
    """
    spec = DOMAIN_SPECS[domain]
    cost_bps = cost_bps_for(instrument, domain)
    materiality_bps = materiality_bps_for(domain)
    net = strategy_return_bps(returns, positions, cost_bps=cost_bps)
    naive = strategy_return_bps(returns, naive_momentum_positions(returns), cost_bps=cost_bps)
    pos = np.asarray(positions, dtype=float)

    neutral_parts: list[np.ndarray] = []
    naive_parts: list[np.ndarray] = []
    neu_counts: list[int] = []
    nai_counts: list[int] = []
    net_oos_parts: list[np.ndarray] = []
    diff_oos_parts: list[np.ndarray] = []
    gate_blocks: list[int] = []
    train_up = train_down = test_up = test_down = 0
    net_train_sum = 0.0
    net_train_count = 0
    for fold_index, (train_idx, test_idx) in enumerate(folds):
        net_tr, net_te = net[train_idx], net[test_idx]
        diff_te = net_te - naive[test_idx]
        offset = _FOLD_SEED_STRIDE * fold_index
        gate_block = estimate_block_length(net_tr)
        gate_blocks.append(gate_block)
        neutral_means, _, _ = block_bootstrap_means(
            net_te, n_resamples=n_bootstrap, block_length=gate_block, seed=seed + 1 + offset
        )
        naive_means, _, _ = block_bootstrap_means(
            diff_te, n_resamples=n_bootstrap, block_length=gate_block, seed=seed + 2 + offset
        )
        neutral_parts.append(neutral_means)
        naive_parts.append(naive_means)
        neu_counts.append(len(finite_values(net_te)))
        nai_counts.append(len(finite_values(diff_te)))
        net_oos_parts.append(net_te)
        diff_oos_parts.append(diff_te)
        train_up += count_state_episodes(pos[train_idx], 1.0)
        train_down += count_state_episodes(pos[train_idx], -1.0)
        test_up += count_state_episodes(pos[test_idx], 1.0)
        test_down += count_state_episodes(pos[test_idx], -1.0)
        net_tr_finite = finite_values(net_tr)
        net_train_sum += float(np.sum(net_tr_finite))
        net_train_count += len(net_tr_finite)

    def _concat(parts: list[np.ndarray]) -> np.ndarray:
        return np.concatenate(parts) if parts else np.empty(0, dtype=float)

    net_oos = finite_values(_concat(net_oos_parts))
    diff_oos = finite_values(_concat(diff_oos_parts))
    gate_block = max(gate_blocks) if gate_blocks else 1
    effective_n = len(net_oos) / max(gate_block, 1)
    net_train_mean = net_train_sum / net_train_count if net_train_count else float("-inf")
    return {
        "neutral_means": _weighted_combine(neutral_parts, neu_counts),
        "neutral_mean": _mean_or(net_oos, float("nan")),
        "n_neutral": len(net_oos),
        "naive_means": _weighted_combine(naive_parts, nai_counts),
        "naive_mean": _mean_or(diff_oos, float("nan")),
        "n_naive": len(diff_oos),
        "block_length": gate_block,
        "effective_n": effective_n,
        "materiality_bps": materiality_bps,
        "l1": bool(
            effective_n >= spec.min_effective_n
            and min(train_up, train_down, test_up, test_down) >= spec.min_state_count
        ),
        "l2": True,
        "l4": bool(net_train_mean > 0.0 and _mean_or(net_oos, float("-inf")) > 0.0),
    }


def evaluate_partition_gate(
    returns: np.ndarray,
    positions: np.ndarray,
    *,
    instrument: str,
    domain: str,
    folds: list[Fold],
    alpha_values: tuple[float, ...],
    tau_bps: float,
    n_bootstrap: int,
    seed: int,
    base_label: dict[str, Any],
) -> list[dict[str, Any]]:
    """Loose + strict gate verdicts under a split protocol (single or walk-forward).

    Computes the pooled-OOS gate core for ``folds`` and derives both the loose
    (``tau_bps``) and strict (``materiality_bps``) verdicts per alpha. For a single
    contiguous fold this reduces exactly to the frozen gate, so the single-split arm
    reproduces the main-measurement values (an orchestrator reference check).
    """
    core = _partition_core(
        returns,
        positions,
        instrument=instrument,
        domain=domain,
        folds=folds,
        n_bootstrap=n_bootstrap,
        seed=seed,
    )
    return gate_verdict_rows(
        core, alpha_values=alpha_values, tau_bps=tau_bps, base_label=base_label
    )
