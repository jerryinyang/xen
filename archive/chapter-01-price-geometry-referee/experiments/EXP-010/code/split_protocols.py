"""Experiment-local split-protocol fold generators and a faithful multi-fold
referee evaluator for EXP-010.

This module changes ONLY the train/test partition. Every referee primitive (cost
model, naive control, block bootstrap, materiality, Wilson legs) is imported and
reused unchanged from the frozen ``xen.referee_calibration``.

Two design properties (both required by the EXP-010 scope / analysis plan and the
2026-06-03 adversarial-review amendment):

1. **Within-fold disjoint train/test, no cross-fold pooled overlap (F02 fix).**
   The earlier implementation de-duplicated the *union* of every fold's train
   indices and every fold's test indices into one ``(insample, oos)`` pair, which
   overlapped (rows out-of-sample in one fold re-entered the in-sample union via
   another fold). :func:`evaluate_partition_referees` now evaluates the frozen
   gate **per fold** — block length on that fold's own (disjoint) train, bootstrap
   on that fold's own test — and combines fold outputs by pooling the
   out-of-sample returns (each row once) and taking a **test-size-weighted, per-resample
   average** of the per-fold bootstrap-mean distributions (a stratified bootstrap of
   the pooled OOS mean; see :func:`_weighted_combine`). No row ever informs the block
   length or train-stability mean of a fold in which it is scored out-of-sample. For the
   single contiguous fold this reduces **exactly** to the frozen
   ``evaluate_referees`` (the reference-reproduction anchor).

2. **Timestamp-mapped fold boundaries (F05 fix).** Fold boundary *indices* are
   computed by the orchestrator from shared 1-minute ``CloseTime`` timestamps
   mapped into each domain (never per-timeframe row fractions, design section 7);
   the generators here consume those pre-mapped boundary indices.

No shared ``python/src/xen`` module is modified.
"""
from __future__ import annotations

import json
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

# Predeclared protocol parameters (scope "Protocols under test"). Frozen, untuned.
PROTOCOLS: tuple[str, ...] = ("single", "walk_forward", "purged_cv")
WALK_FORWARD_FOLDS = 5
WALK_FORWARD_WARMUP_FRACTION = 0.5
PURGED_CV_FOLDS = 5
PURGE_BARS = 1

# Per-fold bootstrap-seed stride. Fold 0 keeps the frozen base offsets so the
# single-fold path is seed-identical to ``evaluate_referees``; later folds are
# offset by multiples of this stride to decorrelate their resamples.
_FOLD_SEED_STRIDE = 1000

Fold = tuple[np.ndarray, np.ndarray]  # (train_idx, test_idx)


# --------------------------------------------------------------------------- #
# Fold index generators (within the first-70% analysis set only)
# --------------------------------------------------------------------------- #
def single_split_folds(n: int, split_index: int) -> list[Fold]:
    """One contiguous fold at the mandated chronological boundary (= EXP-003)."""
    cut = int(split_index)
    if n >= 2:
        cut = max(1, min(cut, n - 1))
    return [(np.arange(0, cut), np.arange(cut, n))]


def walk_forward_folds(n: int, edges: list[int]) -> list[Fold]:
    """Anchored (expanding) walk-forward folds from pre-mapped boundary indices.

    ``edges`` is the monotone list ``[warmup, e1, ..., n]`` of domain row indices
    obtained by mapping shared 1-minute ``CloseTime`` boundaries into this domain.
    Fold ``i`` trains on all rows strictly before its contiguous test block, so
    every training set is strictly causal; out-of-sample = the union of the test
    blocks = ``[warmup, n)``. Degenerate (empty) blocks are skipped.
    """
    folds: list[Fold] = []
    for i in range(len(edges) - 1):
        test_start, test_end = int(edges[i]), int(edges[i + 1])
        if test_end <= test_start or test_start <= 0:
            continue
        folds.append((np.arange(0, test_start), np.arange(test_start, test_end)))
    return folds


def purged_cv_folds(n: int, edges: list[int], embargo: int) -> list[Fold]:
    """Purged K-fold CV with a forward embargo from pre-mapped boundary indices.

    ``edges`` is the monotone list ``[0, e1, ..., n]`` of domain row indices
    obtained by mapping shared 1-minute ``CloseTime`` boundaries into this domain.
    Each contiguous test block removes from training: the test rows themselves, a
    1-bar purge on each side (label overlap for ``t -> t+1``), and ``embargo`` rows
    immediately after the block (serial-correlation guard, López de Prado).
    Out-of-sample = the union of the held-out blocks = ``[0, n)``. Within every
    fold the returned ``train_idx`` and ``test_idx`` are disjoint by construction.
    """
    folds: list[Fold] = []
    for i in range(len(edges) - 1):
        test_start, test_end = int(edges[i]), int(edges[i + 1])
        if test_end <= test_start:
            continue
        mask = np.ones(n, dtype=bool)
        lo = max(0, test_start - PURGE_BARS)
        hi = min(n, test_end + PURGE_BARS + max(0, embargo))
        mask[lo:hi] = False  # purge-before + test + purge-after + embargo
        train = np.nonzero(mask)[0]
        folds.append((train, np.arange(test_start, test_end)))
    return folds


def build_protocol_folds(
    n: int,
    *,
    split_index: int,
    walk_forward_edges: list[int],
    purged_cv_edges: list[int],
    embargo: int,
) -> dict[str, list[Fold]]:
    """Build the fold lists for all three protocols for one (instrument, domain).

    ``split_index``, ``walk_forward_edges`` and ``purged_cv_edges`` are all
    timestamp-mapped domain row indices supplied by the orchestrator.
    """
    return {
        "single": single_split_folds(n, split_index),
        "walk_forward": walk_forward_folds(n, walk_forward_edges),
        "purged_cv": purged_cv_folds(n, purged_cv_edges, embargo=embargo),
    }


# --------------------------------------------------------------------------- #
# Faithful multi-fold referee evaluation (frozen legs, only the partition moves)
# --------------------------------------------------------------------------- #
def _pooled_oos(folds: list[Fold]) -> np.ndarray:
    """Out-of-sample index union (each row scored once). Metadata/reporting only."""
    if not folds:
        return np.empty(0, dtype=int)
    return np.unique(np.concatenate([fold[1] for fold in folds]))


def _episode_counts_folds(positions: np.ndarray, folds: list[Fold]) -> tuple[int, int, int, int]:
    """Up/down episode counts summed per fold (no seam artifacts across folds)."""
    train_up = train_down = test_up = test_down = 0
    for train_idx, test_idx in folds:
        train_up += count_state_episodes(positions[train_idx], 1.0)
        train_down += count_state_episodes(positions[train_idx], -1.0)
        test_up += count_state_episodes(positions[test_idx], 1.0)
        test_down += count_state_episodes(positions[test_idx], -1.0)
    return train_up, train_down, test_up, test_down


def _mean_or(values: np.ndarray, default: float) -> float:
    """Mean of finite ``values``; ``default`` for an empty array."""
    finite = finite_values(values)
    return float(np.mean(finite)) if len(finite) else default


def _weighted_combine(means_parts: list[np.ndarray], counts: list[int]) -> np.ndarray:
    """Stratified pooled-OOS bootstrap: per-resample, size-weighted fold means.

    Each fold contributes one block-bootstrap mean distribution computed on its own
    disjoint out-of-sample test rows with its own block length. Averaging those
    distributions *per resample* with population weights ``n_fold / sum(n_fold)``
    yields bootstrap replicates of the **pooled** OOS mean, so the combined CI scales
    with the pooled OOS size (``~1/sqrt(N_oos)``) rather than the smaller per-fold size.

    This replaces the earlier (2026-06-03 amendment) rule that *concatenated* the
    per-fold mean distributions: concatenation estimates the variability of a single
    fold-sized mean, which inflated multi-fold CIs and produced a spurious walk-forward
    MDE increase even though the pooled estimate and ``effective_n`` used all OOS rows
    (2026-06-04 adversarial review F01). For a single contiguous fold this returns that
    fold's means unchanged, so the wrapper stays bit-identical to the frozen
    ``evaluate_referees`` (the reference-reproduction anchor).
    """
    pairs = [(m, c) for m, c in zip(means_parts, counts) if c > 0 and len(m) > 0]
    if not pairs:
        return np.empty(0, dtype=float)
    length = min(len(m) for m, _ in pairs)
    matrix = np.vstack([m[:length] for m, _ in pairs])
    weights = np.array([c for _, c in pairs], dtype=float)
    weights = weights / weights.sum()
    return (weights[:, None] * matrix).sum(axis=0)


def _gate_rows(
    *,
    core: dict[str, Any],
    alpha_values: tuple[float, ...],
    base_label: dict[str, Any],
) -> list[dict[str, Any]]:
    """Assemble gate-stack verdict rows per alpha from a precomputed core."""
    rows: list[dict[str, Any]] = []
    for alpha in alpha_values:
        ci_neutral = ci_from_means(
            core["neutral_mean"], core["neutral_means"], core["n_neu"], alpha=alpha
        )
        ci_naive = ci_from_means(
            core["naive_mean"], core["naive_means"], core["n_nai"], alpha=alpha
        )
        l3 = bool(ci_neutral.lower > 0.0 and ci_naive.lower > 0.0)
        l5 = bool(ci_neutral.lower > core["materiality_bps"])
        passed = bool(core["l1"] and core["l2"] and l3 and core["l4"] and l5)
        rows.append(
            {
                **base_label,
                "referee": "gate_stack",
                "alpha": alpha,
                "passed": passed,
                "effect_bps": ci_neutral.mean,
                "ci_lower_bps": ci_neutral.lower,
                "ci_upper_bps": ci_neutral.upper,
                "effective_n": core["effective_n"],
                "block_length": core["block_length"],
            }
        )
    return rows


def _minimal_rows(
    *,
    core: dict[str, Any],
    alpha_values: tuple[float, ...],
    base_label: dict[str, Any],
) -> list[dict[str, Any]]:
    """Assemble minimal-baseline verdict rows per alpha from a precomputed core."""
    rows: list[dict[str, Any]] = []
    for alpha in alpha_values:
        ci = ci_from_means(core["sample_mean"], core["means"], core["n"], alpha=alpha)
        passed = bool(np.isfinite(ci.lower) and ci.lower > 0.0)
        rows.append(
            {
                **base_label,
                "referee": "minimal_baseline",
                "alpha": alpha,
                "passed": passed,
                "effect_bps": ci.mean,
                "ci_lower_bps": ci.lower,
                "ci_upper_bps": ci.upper,
                "effective_n": core["effective_n"],
                "block_length": core["block_length"],
            }
        )
    return rows


def evaluate_partition_referees(
    returns: np.ndarray,
    positions: np.ndarray,
    *,
    instrument: str,
    domain: str,
    folds: list[Fold],
    alpha_values: tuple[float, ...],
    n_bootstrap: int,
    seed: int,
    base_label: dict[str, Any],
) -> list[dict[str, Any]]:
    """Both frozen referees evaluated **per fold** and combined to one verdict/draw.

    For each fold the block length is estimated on that fold's own (disjoint)
    in-sample training returns and the neutral / vs-naive / minimal bootstraps run
    on that fold's own out-of-sample test returns — so no row ever contaminates the
    block length or stability mean of a fold in which it is scored out-of-sample
    (F02 fix). The fold outputs are then combined:

    - the **effect** and ``effective_n`` use the pooled out-of-sample returns
      (each row once),
    - the **CI** is taken over a test-size-weighted, per-resample average of the
      per-fold bootstrap-mean distributions (stratified bootstrap of the pooled OOS
      mean, so the CI width tracks the pooled OOS size, not the per-fold size),
    - **L1** episode counts are summed per fold (no seam artifacts),
    - **L4** uses the size-weighted in-sample mean over all fold trains and the
      pooled out-of-sample mean,
    - the reported ``block_length`` is the max over folds (conservative).

    For a single contiguous fold this reduces exactly to the frozen
    ``evaluate_referees`` (block on train, bootstrap on test, same legs and seeds).

    Parameters
    ----------
    returns, positions : np.ndarray
        Scenario returns and candidate positions for one draw.
    folds : list[Fold]
        ``(train_idx, test_idx)`` partitions for one protocol; train/test are
        disjoint within every fold.
    base_label : dict[str, Any]
        Draw/protocol labels copied onto every emitted row.

    Returns
    -------
    list[dict[str, Any]]
        Verdict rows (one per referee x alpha), schema-compatible with the
        ``verdict_rate_rows`` denominator helper.
    """
    spec = DOMAIN_SPECS[domain]
    cost_bps = cost_bps_for(instrument, domain)
    materiality_bps = materiality_bps_for(domain)

    net = strategy_return_bps(returns, positions, cost_bps=cost_bps)
    naive = strategy_return_bps(returns, naive_momentum_positions(returns), cost_bps=cost_bps)
    gross = strategy_return_bps(returns, positions, cost_bps=0.0)
    gate_seed = seed + 100_000

    neutral_parts: list[np.ndarray] = []
    naive_parts: list[np.ndarray] = []
    min_parts: list[np.ndarray] = []
    neu_counts: list[int] = []
    nai_counts: list[int] = []
    min_counts: list[int] = []
    net_oos_parts: list[np.ndarray] = []
    diff_oos_parts: list[np.ndarray] = []
    gross_oos_parts: list[np.ndarray] = []
    gate_blocks: list[int] = []
    min_blocks: list[int] = []
    net_train_sum = 0.0
    net_train_count = 0
    for fold_index, (train_idx, test_idx) in enumerate(folds):
        net_tr, net_te = net[train_idx], net[test_idx]
        gross_tr, gross_te = gross[train_idx], gross[test_idx]
        diff_te = net_te - naive[test_idx]
        offset = _FOLD_SEED_STRIDE * fold_index

        gate_block = estimate_block_length(net_tr)
        min_block = estimate_block_length(gross_tr)
        gate_blocks.append(gate_block)
        min_blocks.append(min_block)

        neutral_means, _, _ = block_bootstrap_means(
            net_te, n_resamples=n_bootstrap, block_length=gate_block, seed=gate_seed + 1 + offset
        )
        naive_means, _, _ = block_bootstrap_means(
            diff_te, n_resamples=n_bootstrap, block_length=gate_block, seed=gate_seed + 2 + offset
        )
        min_means, _, _ = block_bootstrap_means(
            gross_te, n_resamples=n_bootstrap, block_length=min_block, seed=seed + 1 + offset
        )
        neutral_parts.append(neutral_means)
        naive_parts.append(naive_means)
        min_parts.append(min_means)
        # Per-fold finite OOS counts are the population weights for the stratified
        # pooled-OOS combination (F01 fix); they match the rows each bootstrap saw.
        neu_counts.append(len(finite_values(net_te)))
        nai_counts.append(len(finite_values(diff_te)))
        min_counts.append(len(finite_values(gross_te)))
        net_oos_parts.append(net_te)
        diff_oos_parts.append(diff_te)
        gross_oos_parts.append(gross_te)

        net_tr_finite = finite_values(net_tr)
        net_train_sum += float(np.sum(net_tr_finite))
        net_train_count += len(net_tr_finite)

    def _concat(parts: list[np.ndarray]) -> np.ndarray:
        return np.concatenate(parts) if parts else np.empty(0, dtype=float)

    net_oos = finite_values(_concat(net_oos_parts))
    diff_oos = finite_values(_concat(diff_oos_parts))
    gross_oos = finite_values(_concat(gross_oos_parts))
    gate_block = max(gate_blocks) if gate_blocks else 1
    min_block = max(min_blocks) if min_blocks else 1
    gate_eff_n = len(net_oos) / max(gate_block, 1)
    train_up, train_down, test_up, test_down = _episode_counts_folds(positions, folds)
    net_train_mean = net_train_sum / net_train_count if net_train_count else float("-inf")
    net_oos_mean = _mean_or(net_oos, float("-inf"))

    gate_core = {
        "neutral_means": _weighted_combine(neutral_parts, neu_counts),
        "neutral_mean": _mean_or(net_oos, float("nan")),
        "n_neu": len(net_oos),
        "naive_means": _weighted_combine(naive_parts, nai_counts),
        "naive_mean": _mean_or(diff_oos, float("nan")),
        "n_nai": len(diff_oos),
        "block_length": gate_block,
        "effective_n": gate_eff_n,
        "materiality_bps": materiality_bps,
        "l1": bool(
            gate_eff_n >= spec.min_effective_n
            and min(train_up, train_down, test_up, test_down) >= spec.min_state_count
        ),
        "l2": True,
        "l4": bool(net_train_mean > 0.0 and net_oos_mean > 0.0),
    }
    minimal_core = {
        "means": _weighted_combine(min_parts, min_counts),
        "sample_mean": _mean_or(gross_oos, float("nan")),
        "n": len(gross_oos),
        "block_length": min_block,
        "effective_n": len(gross_oos) / max(min_block, 1),
    }

    rows = _minimal_rows(core=minimal_core, alpha_values=alpha_values, base_label=base_label)
    rows.extend(_gate_rows(core=gate_core, alpha_values=alpha_values, base_label=base_label))
    return rows


def fold_summary(folds_by_protocol: dict[str, list[Fold]]) -> str:
    """Compact JSON description of each protocol's fold sizes (for metadata)."""
    summary: dict[str, Any] = {}
    for protocol, folds in folds_by_protocol.items():
        oos_idx = _pooled_oos(folds)
        summary[protocol] = {
            "n_folds": len(folds),
            "pooled_oos": int(len(oos_idx)),
            "fold_test_sizes": [int(len(test_idx)) for _train_idx, test_idx in folds],
        }
    return json.dumps(summary, sort_keys=True)
