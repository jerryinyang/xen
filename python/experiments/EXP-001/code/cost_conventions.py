"""EXP-001 (E1) cost-convention helpers — the per-turnover amortized arm vs the frozen per-held-bar arm.

The frozen referee charges a full round-trip on **every active bar**
(`xen.referee_calibration.strategy_return_bps`). For a persistent (low-turnover) signal that over-charges:
a direction held across an episode of length L pays ~L round-trips it never incurs (F3/F9). This module
adds the **amortized** arm — one round-trip per holding **episode** (charged at entry) — which is the
standalone analog of Component B's per-episode amortization. E1 compares the two; if reused beyond E1 it
is promoted to `xen.referee_adaptive`.
"""
from __future__ import annotations

import numpy as np


def entry_mask(positions: np.ndarray) -> np.ndarray:
    """Bars that **open a new directional commitment** (one round-trip per holding episode).

    An entry is a non-zero position that differs from the previous bar's position (the first bar counts
    as an entry if non-zero). A direct sign flip (long->short) is one entry (one round-trip to reverse);
    an exit to flat is not charged at the zero bar (its round-trip was charged at the matching entry).

    Parameters
    ----------
    positions : np.ndarray
        Per-bar positions in ``{-1, 0, +1}``.

    Returns
    -------
    np.ndarray
        Boolean mask, ``True`` on entry bars.
    """
    pos = np.asarray(positions, dtype=float)
    if len(pos) == 0:
        return np.zeros(0, dtype=bool)
    prev = np.concatenate(([0.0], pos[:-1]))
    return (pos != 0.0) & (pos != prev)


def strategy_return_bps_turnover(
    returns: np.ndarray, positions: np.ndarray, *, cost_bps: float
) -> np.ndarray:
    """Per-bar net strategy return in bps, charging ``cost_bps`` **once per entry** (amortized arm).

    Identical to `xen.referee_calibration.strategy_return_bps` except the round-trip cost is deducted on
    **entry** bars only (one round-trip per holding episode) rather than on every active bar. Total cost
    over an episode of length L is ``cost_bps`` (vs ``L * cost_bps`` for the frozen per-held-bar arm), so
    by construction this arm's total cost is <= the frozen arm's, with equality iff every active bar is an
    entry (L == 1, the per-bar-flip negative control).

    Parameters
    ----------
    returns : np.ndarray
        Real next-step returns (fractional).
    positions : np.ndarray
        Per-bar positions in ``{-1, 0, +1}``.
    cost_bps : float
        Round-trip cost (bps), charged once per entry.

    Returns
    -------
    np.ndarray
        Net per-bar strategy return in bps.
    """
    n = min(len(returns), len(positions))
    ret = np.asarray(returns[:n], dtype=float)
    pos = np.asarray(positions[:n], dtype=float)
    gross = pos * ret * 10_000.0
    return gross - (cost_bps * entry_mask(pos).astype(float))
