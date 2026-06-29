"""Referee-renew synthetic-positive shape substrate (promoted from EXP-002 ``code/edge_shapes.py``).

Shared calibration substrate for the D-referee branch (E2/E3a/E4). Behaviorally identical to the
EXP-002 local copy (its frozen record). Original header follows.

EXP-002 (E2) non-constant edge-shape menu + sparse/state position substrates.

Extends the frozen constant-drift `plant_positive_edge` (F6) to the L-12-named blind shapes. Every
shape injects a direction-aligned drift whose **mean over the shape's declared denominator equals the
DENSE per-bar delta** `(net_edge_bps + cost_bps)/1e4` — i.e. matched economic magnitude, varied shape
(L-08/L-11). The grid level `e` (`EDGE_GRID_BPS`) is therefore in the same per-held-net-edge units as
EXP-001's DENSE anchor; the gate nets cost per its own convention downstream. Matched-magnitude is
asserted at construction.

Causal provenance: these helpers consume an exogenous synthetic position series and a real return
series; they read no bar's own OHLC to choose a position (the planted edge is a known oracle stimulus,
not a tradable signal). No `[di]`-vs-`[di-1]` intrabar limit is involved.

Shape constants are module-level, performance-independent (Q5) — never read from any outcome.
"""
from __future__ import annotations

import numpy as np

from xen.incremental_referee import _blockwise_state
from xen.referee_calibration import plant_positive_edge

# --------------------------------------------------------------------------- #
# Frozen shape constants (Q5: pre-registered, performance-independent)
# --------------------------------------------------------------------------- #
F_TAIL: float = 0.10      # fraction of active bars carrying the tail-concentrated drift
A_SPARSE: float = 0.06    # sparse/event activity rate (~AVWAP event rate, L-04; disclosed borrow)
FRAC_A: float = 0.50      # fraction of episodes in the edge-bearing latent state


def _delta(net_edge_bps: float, cost_bps: float) -> float:
    """DENSE per-active-bar drift (fraction) — the matched-magnitude unit shared by all shapes."""
    return (net_edge_bps + cost_bps) / 10_000.0


# --------------------------------------------------------------------------- #
# Position substrates (pure, seeded)
# --------------------------------------------------------------------------- #
def persistent_positions(n: int, episode_length: int, seed: int) -> np.ndarray:
    """Blockwise-persistent {-1,+1} positions of episode length L (frozen primitive)."""
    return _blockwise_state(n, episode_length, np.random.default_rng(seed))


def sparse_positions(n: int, episode_length: int, seed: int, *, activity: float = A_SPARSE) -> np.ndarray:
    """Low-activity blockwise positions: ~``activity`` of bars active, the rest flat (event signal).

    Each episode is kept (sign ±1) with probability ``activity`` and zeroed otherwise, so the active
    fraction ≈ ``activity`` (a persistent series is otherwise fully active). Tests the sparse-denominator
    dilution failure mode (L-04).
    """
    rng = np.random.default_rng(seed)
    n_episodes = (n + episode_length - 1) // episode_length
    keep = rng.random(n_episodes) < activity
    signs = rng.choice(np.array([-1.0, 1.0]), size=n_episodes) * keep
    return np.repeat(signs, episode_length)[:n]


def state_positions(
    n: int, episode_length: int, seed: int, *, frac_a: float = FRAC_A
) -> tuple[np.ndarray, np.ndarray]:
    """Fully-active persistent positions + a blockwise latent-state mask (``frac_a`` of episodes = A).

    Returns ``(positions, state_a_mask)``. The edge is planted only on state-A active bars
    (:func:`state_dependent_planted`), so the harness can report the pooled dilution
    (edge-bearing fraction of all active bars).
    """
    rng = np.random.default_rng(seed)
    positions = _blockwise_state(n, episode_length, rng)
    n_episodes = (n + episode_length - 1) // episode_length
    state_a_ep = rng.random(n_episodes) < frac_a
    state_a_mask = np.repeat(state_a_ep, episode_length)[:n]
    return positions, state_a_mask


# --------------------------------------------------------------------------- #
# Planters (extend plant_positive_edge; matched mean over the declared denominator)
# --------------------------------------------------------------------------- #
def dense_planted(returns: np.ndarray, positions: np.ndarray, *, net_edge_bps: float,
                  cost_bps: float) -> np.ndarray:
    """DENSE anchor — constant drift on every active bar (the frozen `plant_positive_edge`)."""
    return plant_positive_edge(returns, positions, net_edge_bps=net_edge_bps, cost_bps=cost_bps)


def tail_only_planted(returns: np.ndarray, positions: np.ndarray, *, net_edge_bps: float,
                      cost_bps: float, seed: int, f_tail: float = F_TAIL) -> np.ndarray:
    """TAIL-ONLY — same mean drift as DENSE but concentrated in a random ``f_tail`` of active bars.

    On ``f_tail`` of active bars the drift is ``delta/f_tail`` (sign-aligned); 0 on the other active
    bars → mean over active bars = ``delta``. Tests whether the conjunctive gate's stability /
    materiality legs collapse under tail concentration (L-12 §1 / L-11).
    """
    pos = np.asarray(positions, dtype=float)
    delta = _delta(net_edge_bps, cost_bps)
    active = np.flatnonzero(pos != 0.0)
    drift = np.zeros(len(pos), dtype=float)
    if len(active) > 0 and delta != 0.0:
        rng = np.random.default_rng(seed)
        k = max(1, int(round(f_tail * len(active))))
        tail = rng.choice(active, size=k, replace=False)
        drift[tail] = pos[tail] * (delta * len(active) / k)   # mean over active == delta
    return np.asarray(returns, dtype=float) + drift


def state_dependent_planted(returns: np.ndarray, positions: np.ndarray, state_a_mask: np.ndarray, *,
                            net_edge_bps: float, cost_bps: float) -> np.ndarray:
    """STATE-DEPENDENT — constant drift on state-A active bars only (per-state magnitude = delta).

    Mean over state-A active bars = ``delta`` (matched); mean over ALL active bars = ``delta * frac_A``
    (pooled dilution, reported). Tests whether the pooled gate detects an edge confined to a sub-state
    (L-03).
    """
    pos = np.asarray(positions, dtype=float)
    delta = _delta(net_edge_bps, cost_bps)
    edge_bars = (pos != 0.0) & np.asarray(state_a_mask, dtype=bool)
    drift = pos * delta * edge_bars.astype(float)
    return np.asarray(returns, dtype=float) + drift


# --------------------------------------------------------------------------- #
# Matched-magnitude check (used by the harness smoke + as a runtime assert)
# --------------------------------------------------------------------------- #
def mean_drift_over_denominator(planted: np.ndarray, returns: np.ndarray, positions: np.ndarray,
                                *, denominator_mask: np.ndarray) -> float:
    """Sign-aligned mean injected drift over a denominator mask (should equal ``delta``)."""
    pos = np.asarray(positions, dtype=float)
    drift = np.asarray(planted, dtype=float) - np.asarray(returns, dtype=float)
    mask = np.asarray(denominator_mask, dtype=bool)
    if not mask.any():
        return float("nan")
    return float(np.mean((drift * pos)[mask]))
