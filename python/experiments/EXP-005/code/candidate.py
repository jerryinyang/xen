"""Experiment-local realistic-candidate construction for EXP-005.

The frozen ``xen.referee_calibration`` harness is reused unchanged; this module
adds only the EXP-005-specific imperfect-candidate generator, the closed-form
edge calibration, and per-draw construction diagnostics. Nothing here is shared
back into ``python/src/xen`` (checkpoint design D-reuse), so editing it never
triggers substrate/harness re-validation.
"""
from __future__ import annotations

import numpy as np

from xen.referee_calibration import count_state_episodes, strategy_return_bps


# --------------------------------------------------------------------------- #
# Closed-form edge calibration
# --------------------------------------------------------------------------- #
def calibrate_delta_bps(
    target_edge_bps: float,
    cost_bps: float,
    *,
    p_active: float,
    q_match: float,
) -> float:
    """Closed-form latent-state drift (bps) for a target net candidate edge.

    Solves ``E[net all-eligible-row edge] = target`` for the drift planted on
    the latent state ``S``. With ``E[C * S] = p_active * (2 * q_match - 1)`` and
    the harness charging ``cost_bps`` to every active bar (active fraction
    ``p_active``), the expected net all-row edge is
    ``delta_bps * p_active * (2 * q_match - 1) - cost_bps * p_active``; setting
    it equal to ``target_edge_bps`` yields this value. The candidate carries the
    edge imperfectly while its expected net edge equals the target, matching how
    EXP-003 calibrated the oracle MDE.

    Parameters
    ----------
    target_edge_bps : float
        Desired expected net (cost-applied) edge over all eligible rows, in bps.
    cost_bps : float
        Per-active-bar round-trip cost (bps) charged by the harness.
    p_active : float
        Probability the candidate takes a non-zero position on an eligible bar.
    q_match : float
        Probability an active candidate matches the latent state.

    Returns
    -------
    float
        Drift magnitude ``delta_bps`` to plant on the latent state. Inject it in
        fractional units (``delta_bps / 10_000``).
    """
    signal = p_active * (2.0 * q_match - 1.0)
    if signal <= 0.0:
        raise ValueError("p_active * (2 * q_match - 1) must be positive")
    return (target_edge_bps + p_active * cost_bps) / signal


# --------------------------------------------------------------------------- #
# Imperfect-candidate generation
# --------------------------------------------------------------------------- #
def generate_realistic_candidate(
    states: np.ndarray,
    *,
    p_active: float,
    q_match: float,
    seed: int,
) -> np.ndarray:
    """Imperfect candidate positions in ``{-1, 0, +1}`` from a latent state.

    Each eligible bar is independently active with probability ``p_active``;
    when active it equals the latent state with probability ``q_match`` and the
    opposite with probability ``1 - q_match``; inactive bars are ``0``. The two
    Bernoulli draws use a single seeded generator consumed in a fixed order, so
    the output is deterministic and strictly causal (per-bar, no look-ahead):
    bar ``t`` depends only on ``states[t]`` and the seed.

    Parameters
    ----------
    states : np.ndarray
        Latent state per eligible bar, in ``{-1.0, +1.0}``.
    p_active : float
        Probability of an active (non-zero) position.
    q_match : float
        Probability an active position matches the latent state.
    seed : int
        Deterministic seed for the candidate noise.

    Returns
    -------
    np.ndarray
        Candidate positions in ``{-1.0, 0.0, +1.0}``, same length as ``states``.
    """
    states = np.asarray(states, dtype=float)
    rng = np.random.default_rng(seed)
    active = rng.random(len(states)) < p_active
    matched = rng.random(len(states)) < q_match
    directed = np.where(matched, states, -states)
    return np.where(active, directed, 0.0)


# --------------------------------------------------------------------------- #
# Per-draw construction diagnostics
# --------------------------------------------------------------------------- #
def candidate_diagnostics(
    states: np.ndarray,
    candidate: np.ndarray,
    scoped_returns: np.ndarray,
    *,
    split_index: int,
    cost_bps: float,
) -> dict[str, float]:
    """Compact per-draw construction diagnostics for the candidate sanity check.

    Returns counts/rates only (no per-bar arrays) so the caller can aggregate
    cheaply across draws. ``realized_net_bps`` is the all-eligible-row mean of
    the harness net strategy return and drives the closed-form edge-calibration
    check; ``realized_gross_bps`` is the cost-free counterpart.

    Parameters
    ----------
    states : np.ndarray
        Latent state per bar.
    candidate : np.ndarray
        Candidate positions per bar.
    scoped_returns : np.ndarray
        Returns the candidate is scored against (drift-planted for positives).
    split_index : int
        Shared-timestamp train/test boundary index.
    cost_bps : float
        Per-active-bar cost used for the realized net edge.

    Returns
    -------
    dict[str, float]
        Eligible/active/matched counts (overall, train, test), up/down episode
        counts, and realized gross/net all-row mean edge (bps).
    """
    candidate = np.asarray(candidate, dtype=float)
    states = np.asarray(states, dtype=float)
    active_mask = candidate != 0.0
    cut = max(0, min(int(split_index), len(candidate)))
    net = strategy_return_bps(scoped_returns, candidate, cost_bps=cost_bps)
    gross = strategy_return_bps(scoped_returns, candidate, cost_bps=0.0)
    return {
        "eligible_rows": float(len(candidate)),
        "active_bars": float(np.sum(active_mask)),
        "matched_active": float(np.sum(active_mask & (candidate == states))),
        "eligible_train": float(cut),
        "active_train": float(np.sum(active_mask[:cut])),
        "eligible_test": float(len(candidate) - cut),
        "active_test": float(np.sum(active_mask[cut:])),
        "up_episodes": float(count_state_episodes(candidate, 1.0)),
        "down_episodes": float(count_state_episodes(candidate, -1.0)),
        "realized_gross_bps": float(np.mean(gross)) if len(gross) else float("nan"),
        "realized_net_bps": float(np.mean(net)) if len(net) else float("nan"),
    }
