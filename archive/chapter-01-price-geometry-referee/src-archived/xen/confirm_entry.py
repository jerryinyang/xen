"""HA-harami signal-interpretation primitives: direct entry vs signal+confirmation.

`CF-HA-HARAMI-001/CONFIRM` (Phase 014-A, EXP-052). Pure, causal, deterministic
helpers shared by EXP-052 and reusable in 014-B. Two entry interpretations of the
same HA harami signal are evaluated, **gross, on real prices**:

- **DIRECT**: enter at the harami signal bar (real close).
- **CONFIRM** (stop-order): place a stop at the signal bar's real extreme in the
  predicted reversal direction; it fills only if a later real bar trades through it
  before the next ZigZag trend-change confirmation (capped at the P4 adaptive
  horizon). The first-touch fill is a genuinely sequential scan (kept explicit).

Reversal direction (causal): `rd = Direction(most recent move confirmed at
ConfirmTime <= HA0Time)` — after an up-move confirms the ZigZag tracks a down-trend,
so the in-progress move is down and the harami at its exhaustion predicts a down
reversal; symmetrically after a down-move (`scope.md` §"Reversal-direction
assignment"). The per-signal P4 cap reuses the frozen `capture_barriers` constants.

All thresholds/levels here are **real prices**; HA candles are used only upstream
for harami detection. No metric in this module uses HA prices.
"""
from __future__ import annotations

import numpy as np

from xen.capture_barriers import (
    THIRD_BARRIER_FLOOR,
    THIRD_BARRIER_K,
    THIRD_BARRIER_MIN_MOVES,
    THIRD_BARRIER_WINDOW,
)

__all__ = [
    "exact_bar_indices",
    "assign_reversal_context",
    "signal_time_caps",
    "forward_excursion",
    "evaluate_events",
]


# --------------------------------------------------------------------------- #
# Index mapping
# --------------------------------------------------------------------------- #
def exact_bar_indices(bar_epoch: np.ndarray, target_epoch: np.ndarray) -> np.ndarray:
    """Map each target timestamp (epoch seconds) to its exact domain-bar index.

    ``bar_epoch`` must be sorted ascending. Raises ``ValueError`` if any target is
    absent from the bar grid (a substrate/aggregation inconsistency).

    Parameters
    ----------
    bar_epoch : np.ndarray
        Sorted int64 epoch-seconds of the domain bars' ``CloseTime``.
    target_epoch : np.ndarray
        Int64 epoch-seconds to locate (e.g. harami ``HA0Time``).

    Returns
    -------
    np.ndarray
        Int64 indices into ``bar_epoch`` (one per target).
    """
    idx = np.searchsorted(bar_epoch, target_epoch, side="left")
    n = bar_epoch.shape[0]
    if np.any(idx >= n) or np.any(bar_epoch[np.minimum(idx, n - 1)] != target_epoch):
        raise ValueError("target timestamp not found on the domain-bar grid")
    return idx.astype(np.int64)


# --------------------------------------------------------------------------- #
# Causal reversal-direction context
# --------------------------------------------------------------------------- #
def assign_reversal_context(
    harami_epoch: np.ndarray,
    confirm_epoch: np.ndarray,
    move_dir: np.ndarray,
    move_start_price: np.ndarray,
    move_end_price: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Most-recent confirmed-move context for each harami (causal).

    For harami time ``t``, ``j = searchsorted(confirm_epoch, t, side="right") - 1``
    is the index of the most recent move with ``ConfirmTime <= t``. The predicted
    reversal direction is ``rd = Direction[j]`` and the LOOKBACK=1 reference
    magnitude is ``|EndPrice[j] - StartPrice[j]|``. Haramis before the first
    confirmation have no trend context.

    Returns
    -------
    (j_idx, rd, ref_mag, has_context)
        ``j_idx`` clipped to 0 where ``has_context`` is False (do not read those
        ``rd``/``ref_mag`` entries — they are placeholders).
    """
    j = np.searchsorted(confirm_epoch, harami_epoch, side="right") - 1
    has_context = j >= 0
    jj = np.where(has_context, j, 0)
    rd = np.where(has_context, move_dir[jj], 0).astype(np.int64)
    ref_mag = np.where(
        has_context, np.abs(move_end_price[jj] - move_start_price[jj]), np.nan
    )
    return j.astype(np.int64), rd, ref_mag, has_context


def signal_time_caps(
    j_idx: np.ndarray, confirm_idx: np.ndarray, has_context: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Per-signal P4 adaptive time cap and the warmup (insufficient-context) mask.

    For a harami whose most-recent confirmed move is index ``j``, the trailing
    window is the durations of the up-to-``THIRD_BARRIER_WINDOW`` moves confirmed
    up to and including move ``j`` (``durations[i] = ConfirmIdx[i+1]-ConfirmIdx[i]``
    is the realized length of move ``i+1``, so moves ``1..j`` are ``durations[:j]``).
    ``< THIRD_BARRIER_MIN_MOVES`` available -> warmup (no defined cap). Otherwise
    ``N = max(THIRD_BARRIER_FLOOR, round(THIRD_BARRIER_K * median(window)))``. Frozen
    at the signal bar; identical for both arms (a property of the harami, not the
    entry bar). Explicit bounded loop (one pass over haramis; inner window <= 20).

    Returns
    -------
    (n_event, p4_defined)
        ``n_event`` is 0 where ``p4_defined`` is False (no defined cap).
    """
    durations = np.diff(confirm_idx)            # durations[i] = length of move i+1
    n = j_idx.shape[0]
    n_event = np.zeros(n, dtype=np.int64)
    p4_defined = np.zeros(n, dtype=bool)
    for k in range(n):
        if not has_context[k]:
            continue
        j = int(j_idx[k])
        lo = max(0, j - THIRD_BARRIER_WINDOW)
        window = durations[lo:j]                 # durations of moves up to move j
        if window.shape[0] < THIRD_BARRIER_MIN_MOVES:
            continue
        cap = max(THIRD_BARRIER_FLOOR,
                  int(round(THIRD_BARRIER_K * float(np.median(window)))))
        n_event[k], p4_defined[k] = cap, True
    return n_event, p4_defined


# --------------------------------------------------------------------------- #
# Direction-signed forward excursion (real prices)
# --------------------------------------------------------------------------- #
def forward_excursion(
    entry_idx: int, entry_price: float, rd: int, n_event: int,
    high: np.ndarray, low: np.ndarray, n_bars: int,
) -> tuple[float, float, bool]:
    """MFE/MAE over ``[entry_idx+1, entry_idx+n_event]`` (real prices, fenced).

    Favourable = the reversal direction. ``rd=+1``: fav uses ``High - entry``, adv
    uses ``entry - Low``; ``rd=-1``: mirrored. ``MFE/MAE = max(0, max excursion)``.
    A window extending past ``n_bars-1`` is censored.

    Returns
    -------
    (mfe, mae, censored)
        ``(nan, nan, True)`` when censored.
    """
    cap_end = entry_idx + n_event
    if cap_end > n_bars - 1:
        return float("nan"), float("nan"), True
    h = high[entry_idx + 1:cap_end + 1]
    l = low[entry_idx + 1:cap_end + 1]
    if h.shape[0] == 0:
        return float("nan"), float("nan"), True
    if rd == 1:
        fav, adv = h - entry_price, entry_price - l
    else:
        fav, adv = entry_price - l, h - entry_price
    return max(0.0, float(fav.max())), max(0.0, float(adv.max())), False


# --------------------------------------------------------------------------- #
# Combined per-event evaluation (the genuinely-sequential CONFIRM fill scan)
# --------------------------------------------------------------------------- #
def evaluate_events(
    s: np.ndarray, rd: np.ndarray, n_event: np.ndarray,
    stop_level: np.ndarray, next_confirm_bar: np.ndarray,
    high: np.ndarray, low: np.ndarray, close: np.ndarray, n_bars: int,
) -> dict[str, np.ndarray]:
    """Evaluate DIRECT and CONFIRM outcomes for an aligned set of qualifying haramis.

    All input arrays have length ``E`` (qualifying haramis: defined ``rd``, defined
    ``n_event``, DIRECT window non-censored). DIRECT entry = ``close[s]``; CONFIRM
    stop = ``stop_level`` (the signal bar's real extreme). The CONFIRM validity
    window is ``(s, min(next_confirm_bar-1, s+n_event)]`` and the first-touch fill is
    an **explicit bounded sequential scan** (first crossing wins — genuinely
    sequential, not vectorised). CONFIRM outcomes are measured from the trigger bar
    and may be independently censored.

    Returns a dict of per-event arrays: ``direct_entry_price, direct_mfe, direct_mae,
    direct_censored, fill, trigger_idx, confirm_entry_price, confirm_mfe,
    confirm_mae, confirm_censored``.
    """
    e = int(s.shape[0])
    d_price = close[s].astype(np.float64)
    d_mfe = np.full(e, np.nan)
    d_mae = np.full(e, np.nan)
    d_cens = np.zeros(e, dtype=bool)
    fill = np.zeros(e, dtype=bool)
    trigger = np.full(e, -1, dtype=np.int64)
    c_mfe = np.full(e, np.nan)
    c_mae = np.full(e, np.nan)
    c_cens = np.zeros(e, dtype=bool)
    for k in range(e):
        si, r, ne = int(s[k]), int(rd[k]), int(n_event[k])
        d_mfe[k], d_mae[k], d_cens[k] = forward_excursion(
            si, float(d_price[k]), r, ne, high, low, n_bars)
        window_end = min(int(next_confirm_bar[k]) - 1, si + ne)
        stop = float(stop_level[k])
        tr = -1
        for i in range(si + 1, window_end + 1):           # explicit causal first-touch
            if (r == 1 and high[i] >= stop) or (r == -1 and low[i] <= stop):
                tr = i
                break
        if tr >= 0:
            fill[k] = True
            trigger[k] = tr
            c_mfe[k], c_mae[k], c_cens[k] = forward_excursion(
                tr, stop, r, ne, high, low, n_bars)
    return {
        "direct_entry_price": d_price, "direct_mfe": d_mfe, "direct_mae": d_mae,
        "direct_censored": d_cens, "fill": fill, "trigger_idx": trigger,
        "confirm_entry_price": stop_level.astype(np.float64),
        "confirm_mfe": c_mfe, "confirm_mae": c_mae, "confirm_censored": c_cens,
    }
