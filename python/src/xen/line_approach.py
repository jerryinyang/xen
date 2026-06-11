"""Approach-episode detection for line support/resistance science (EXP-040+).

Implements the HYP-001 confound-free framing (Phase 007 design §8): the event
is an *approach* to a price level (close enters an epsilon-neighborhood from
outside), the outcome is whether the episode resolves by exiting the
neighborhood on the side it entered from (a *bounce*) or the opposite side
(a *pass-through*). No bounce-trigger machinery appears anywhere here.

The detector is a single explicit sequential state machine (genuinely
stateful; kept as a loop by design) and is shared verbatim between the AVWAP
arm (moving level) and the control arm (frozen horizontal levels), so any
definitional artifact cancels in the arm contrast. All inputs are completed
domain-bar closes; nothing reads past the supplied window.
"""
from __future__ import annotations

from typing import Any

import numpy as np

BOUNCE = "bounce"
PASS_THROUGH = "pass"
UNRESOLVED = "unresolved"


def detect_episodes(
    close: np.ndarray,
    level: np.ndarray,
    eps: np.ndarray,
    start_idx: int,
    end_idx: int,
    max_len: int,
    hysteresis_mult: float = 2.0,
) -> list[dict[str, Any]]:
    """Detect approach episodes to a level series over ``[start_idx, end_idx]``.

    An episode opens at the first bar whose close is within ``eps`` of the
    level, provided the path was beyond ``hysteresis_mult * eps`` since the
    last episode (the duplicate-source rule). The entry side is the side of
    the most recent bar outside the eps-neighborhood. The episode resolves at
    the first bar whose close exits the neighborhood: ``bounce`` iff it exits
    on the entry side, ``pass`` otherwise. Episodes still inside the
    neighborhood after ``max_len`` bars, or at the window end, are
    ``unresolved`` (disclosed by callers, excluded from rates).

    Parameters
    ----------
    close : np.ndarray
        Real domain-bar closes (full-cell array; absolute indexing).
    level, eps : np.ndarray
        Level value and epsilon per bar (absolute indexing; NaN = undefined,
        bars with NaN level/eps are skipped and close any armed state).
    start_idx, end_idx : int
        Inclusive detection window (callers bound this to the regime window
        and, where applicable, the level lifetime).
    max_len : int
        Episode cap in bars from the open bar.
    hysteresis_mult : float
        Hysteresis radius as a multiple of eps.

    Returns
    -------
    list[dict[str, Any]]
        One dict per episode: ``open_idx``, ``entry_side`` (+1 approached
        from above, -1 from below), ``outcome``, ``resolve_idx`` (-1 when
        unresolved), ``bars_in``.
    """
    if not (0 <= start_idx <= end_idx < close.size):
        raise ValueError("invalid detection window bounds")
    episodes: list[dict[str, Any]] = []
    armed = False
    last_outside_side = 0
    in_episode = False
    open_idx = -1
    entry_side = 0
    for k in range(start_idx, end_idx + 1):
        lv, ep = level[k], eps[k]
        if not (np.isfinite(lv) and np.isfinite(ep)) or ep <= 0.0:
            if in_episode:
                episodes.append({"open_idx": open_idx, "entry_side": entry_side,
                                 "outcome": UNRESOLVED, "resolve_idx": -1,
                                 "bars_in": k - open_idx})
                in_episode = False
            armed = False
            continue
        dist = close[k] - lv
        ad = abs(dist)
        if in_episode:
            if ad > ep:
                outcome = BOUNCE if np.sign(dist) == entry_side else PASS_THROUGH
                episodes.append({"open_idx": open_idx, "entry_side": entry_side,
                                 "outcome": outcome, "resolve_idx": k,
                                 "bars_in": k - open_idx})
                in_episode = False
                armed = ad > hysteresis_mult * ep
                last_outside_side = int(np.sign(dist))
            elif k - open_idx >= max_len:
                episodes.append({"open_idx": open_idx, "entry_side": entry_side,
                                 "outcome": UNRESOLVED, "resolve_idx": -1,
                                 "bars_in": k - open_idx})
                in_episode = False
                armed = False
            continue
        if ad > ep:
            last_outside_side = int(np.sign(dist))
            if ad > hysteresis_mult * ep:
                armed = True
        elif armed and last_outside_side != 0:
            in_episode = True
            open_idx = k
            entry_side = last_outside_side
            armed = False
    if in_episode:
        episodes.append({"open_idx": open_idx, "entry_side": entry_side,
                         "outcome": UNRESOLVED, "resolve_idx": -1,
                         "bars_in": end_idx - open_idx})
    return episodes


def spawn_control_levels(
    avwap: np.ndarray,
    band_width: np.ndarray,
    start_idx: int,
    end_idx: int,
    spacing: int,
    lifetime: int,
    delta_lo: float,
    delta_hi: float,
    rng: np.random.Generator,
) -> list[dict[str, Any]]:
    """Frozen horizontal control levels on a regular grid inside one window.

    At every ``spacing``-th bar ``k0`` in ``[start_idx, end_idx]`` with a
    finite positive band width, freeze one horizontal level
    ``avwap[k0] + delta * band_width[k0]`` with ``|delta|`` drawn uniformly
    from ``[delta_lo, delta_hi]`` and a random sign. The level lives for
    ``lifetime`` bars (clipped to the window). The snapshot uses only data at
    ``k0`` — controls are look-ahead-safe by construction.

    Returns
    -------
    list[dict[str, Any]]
        One dict per level: ``spawn_idx``, ``level_value``, ``delta``,
        ``alive_start`` (= spawn_idx), ``alive_end``.
    """
    if spacing < 1 or lifetime < 1:
        raise ValueError("spacing and lifetime must be >= 1")
    levels: list[dict[str, Any]] = []
    for k0 in range(start_idx, end_idx + 1, spacing):
        bw = band_width[k0]
        if not np.isfinite(bw) or bw <= 0.0 or not np.isfinite(avwap[k0]):
            continue
        delta = float(rng.uniform(delta_lo, delta_hi)) * float(rng.choice((-1.0, 1.0)))
        levels.append({
            "spawn_idx": k0,
            "level_value": float(avwap[k0] + delta * bw),
            "delta": delta,
            "alive_start": k0,
            "alive_end": min(k0 + lifetime, end_idx),
        })
    return levels
