"""Registered exit-rule library for the AVWAP bounce-entry substrate (EXP-039+).

Bar-close semantics throughout: every exit condition is evaluated at completed
domain-bar closes using only data at or before that close, and the fill price
is the triggering bar's real ``Close``. Heiken Ashi values may appear only in
trigger conditions (E1/E2); they never price a fill.

Event-independent rules (E1, E2, E3) are precomputed as sorted "fire index"
arrays per cell (vectorised but causally equivalent to a sequential scan: each
condition at bar ``j`` reads only bars ``<= j``); the per-event exit is then
the first fire strictly after the entry bar, found with ``searchsorted``.
Target-based rules (E4, E5) depend on per-event frozen levels and scan a
bounded slice, mirroring the EXP-022 completion-scan semantics
(``direction * (close - favorable_target) >= 0`` / ``direction *
(close - adverse_target) <= 0``; first hit wins, ties counted as favorable
exits at the same bar by the same convention).

All scan bounds are caller-supplied (``scan_end`` inclusive) so TRAIN-only
experiments can refuse to read past their boundary. Functions return ``-1``
when the rule does not resolve by ``scan_end``.
"""
from __future__ import annotations

import numpy as np

UNRESOLVED: int = -1


# --------------------------------------------------------------------------- #
# Heiken Ashi trigger values (canonical recurrence; trigger-only, never prices)
# --------------------------------------------------------------------------- #
def ha_trigger_values(
    open_: np.ndarray, high: np.ndarray, low: np.ndarray, close: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(ha_open, ha_close)`` per bar via the canonical HA recurrence.

    Matches ``xen.heiken_ashi_generator``: ``HAClose = (O+H+L+C)/4``;
    ``HAOpen_0 = (O_0+C_0)/2``; ``HAOpen_i = (HAOpen_{i-1}+HAClose_{i-1})/2``.
    Sequential by definition (genuinely stateful recurrence, kept explicit).

    Parameters
    ----------
    open_, high, low, close : np.ndarray
        Real domain-bar OHLC arrays (equal length).

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        ``(ha_open, ha_close)`` float arrays, same length as the inputs.
    """
    n = close.size
    ha_close = (open_ + high + low + close) / 4.0
    ha_open = np.empty(n, dtype=float)
    if n == 0:
        return ha_open, ha_close
    ha_open[0] = (open_[0] + close[0]) / 2.0
    for i in range(1, n):
        ha_open[i] = (ha_open[i - 1] + ha_close[i - 1]) / 2.0
    return ha_open, ha_close


# --------------------------------------------------------------------------- #
# Event-independent fire-index precomputation (E1, E2, E3)
# --------------------------------------------------------------------------- #
def harami_fire_indices(ha_open: np.ndarray, ha_close: np.ndarray) -> np.ndarray:
    """E1 — HA Harami size exhaustion fire bars (direction-independent).

    Fires at bar ``j`` (``j >= 1``) iff the prior HA body range strictly
    contains the latest: ``max(body_{j-1}) > max(body_j)`` and
    ``min(body_{j-1}) < min(body_j)`` with ``body = (HAOpen, HAClose)``.

    Returns
    -------
    np.ndarray
        Sorted int64 indices of fire bars.
    """
    body_hi = np.maximum(ha_open, ha_close)
    body_lo = np.minimum(ha_open, ha_close)
    fire = (body_hi[:-1] > body_hi[1:]) & (body_lo[:-1] < body_lo[1:])
    return (np.flatnonzero(fire) + 1).astype(np.int64)


def ha_trailing_fire_indices(
    close: np.ndarray, ha_open: np.ndarray, ha_close: np.ndarray, direction: int,
) -> np.ndarray:
    """E2 — HA trailing-reference fire bars for one direction.

    Long (+1): fires at ``j`` iff ``close[j] < min(HAOpen, HAClose)[j-1]``.
    Short (-1): fires at ``j`` iff ``close[j] > max(HAOpen, HAClose)[j-1]``.
    Bar-close market-style trigger (the stop-style variant is out of scope).
    """
    if direction not in (1, -1):
        raise ValueError(f"direction must be +1/-1, got {direction}")
    if direction == 1:
        ref = np.minimum(ha_open, ha_close)[:-1]
        fire = close[1:] < ref
    else:
        ref = np.maximum(ha_open, ha_close)[:-1]
        fire = close[1:] > ref
    return (np.flatnonzero(fire) + 1).astype(np.int64)


def last_x_fire_indices(
    close: np.ndarray, high: np.ndarray, low: np.ndarray, direction: int, x: int,
) -> np.ndarray:
    """E3 — Last-X high/low trailing fire bars for one direction.

    Long (+1): fires at ``j`` iff ``close[j] < min(low[j-x .. j-1])``.
    Short (-1): fires at ``j`` iff ``close[j] > max(high[j-x .. j-1])``.
    Undefined (never fires) for ``j < x``. The rolling prior-``x`` extreme is
    computed with a sliding window over completed bars only.
    """
    if direction not in (1, -1):
        raise ValueError(f"direction must be +1/-1, got {direction}")
    if x < 1:
        raise ValueError(f"x must be >= 1, got {x}")
    n = close.size
    if n <= x:
        return np.empty(0, dtype=np.int64)
    if direction == 1:
        windows = np.lib.stride_tricks.sliding_window_view(low, x)  # [k, x]
        prior_ext = windows.min(axis=1)          # min(low[k .. k+x-1])
        fire = close[x:] < prior_ext[: n - x]    # j = k + x
    else:
        windows = np.lib.stride_tricks.sliding_window_view(high, x)
        prior_ext = windows.max(axis=1)
        fire = close[x:] > prior_ext[: n - x]
    return (np.flatnonzero(fire) + x).astype(np.int64)


def first_fire_after(fire_idx: np.ndarray, entry_idx: int, scan_end: int) -> int:
    """First fire index strictly after ``entry_idx`` and ``<= scan_end``.

    Returns ``UNRESOLVED`` when no fire lands inside the bounded scan window.
    """
    pos = int(np.searchsorted(fire_idx, entry_idx + 1, side="left"))
    if pos >= fire_idx.size:
        return UNRESOLVED
    j = int(fire_idx[pos])
    return j if j <= scan_end else UNRESOLVED


# --------------------------------------------------------------------------- #
# Per-event target-based rules (E4, E5)
# --------------------------------------------------------------------------- #
def target_exit_idx(
    close: np.ndarray,
    entry_idx: int,
    direction: int,
    favorable_target: float,
    adverse_target: float,
    scan_end: int,
    h_cap: int | None = None,
) -> int:
    """First close-based hit of either frozen target after entry (E4/E5 core).

    EXP-022 semantics: favorable hit iff ``direction * (close - favorable)
    >= 0``; adverse hit iff ``direction * (close - adverse) <= 0``; the first
    hit (either kind) is the exit bar. With ``h_cap`` (E5), an un-hit scan
    exits unconditionally at ``entry_idx + h_cap`` when that bar is inside the
    scan window; otherwise the event is unresolved.

    Returns the exit bar index, or ``UNRESOLVED``.
    """
    if direction not in (1, -1):
        raise ValueError(f"direction must be +1/-1, got {direction}")
    last = scan_end if h_cap is None else min(scan_end, entry_idx + h_cap)
    if last <= entry_idx:
        return UNRESOLVED
    seg = close[entry_idx + 1 : last + 1]
    hits = (direction * (seg - favorable_target) >= 0.0) | (
        direction * (seg - adverse_target) <= 0.0
    )
    pos = np.flatnonzero(hits)
    if pos.size:
        return entry_idx + 1 + int(pos[0])
    if h_cap is not None and entry_idx + h_cap <= scan_end:
        return entry_idx + h_cap
    return UNRESOLVED


def fixed_horizon_exit_idx(entry_idx: int, horizon: int, scan_end: int) -> int:
    """FH reference exit: ``entry_idx + horizon`` if inside the scan window."""
    j = entry_idx + horizon
    return j if j <= scan_end else UNRESOLVED
