"""Strategy-agnostic ATR volatility-regime partition + regime-matched control (CF-MR-001, Phase 020).

The co-primary new lever for the mean-reversion family: a **market-intrinsic**
volatility regime — an ``ATR(14)`` causal trailing rolling-percentile cut — made a
*cell-differentiating* factor of the signal (cell = ``asset+domain+regime``).

**D0-amendment-001 (2026-06-23):** the original leg-2 ``beats-CORE`` conjunction and
the regime-membership-shuffle null are **retired** (they were structurally blind to an
ATR-normalization confound; see EXP-089 audit C-1). Under the amendment each
``/VOLREGIME`` sub-screen is a single-test **leg-1** read whose matched-random control
is drawn from **same-regime bars** (so the entry-ATR denominator cancels within the
comparison), routed through ``xen.availability_gate.run_sub_screen`` unchanged. This
module therefore supplies only (1) the causal regime labeller and (2) the
regime-matched random-draw helper; the per-cell test, the null, and the joint-max
combiner are all reused from ``xen.availability_gate``.

Real-price discipline is the caller's responsibility (this module operates on
already-computed real-OHLC ATR arrays / domain-bar index sets).
"""

from __future__ import annotations

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from xen.zigzag import wilder_atr

# --------------------------------------------------------------------------- #
# Frozen constants (D1; never tuned)
# --------------------------------------------------------------------------- #
ATR_PERIOD: int = 14               # Wilder ATR period for the regime read
REGIME_WINDOW: int = 50            # trailing rolling percentile window (bars)
REGIME_CUTS: tuple[float, float] = (0.33, 0.66)   # LOW < p33 ; HIGH > p66 ; else MED

REGIME_UNDEFINED: int = -1
REGIME_LOW: int = 0
REGIME_MED: int = 1
REGIME_HIGH: int = 2
REGIME_INDICES: tuple[int, int, int] = (REGIME_LOW, REGIME_MED, REGIME_HIGH)
REGIME_SUB_SCREENS: tuple[str, str, str] = ("CORE-VOL-LOW", "CORE-VOL-MED", "CORE-VOL-HIGH")


# --------------------------------------------------------------------------- #
# Pure computation — causal ATR rolling-percentile regime labels
# --------------------------------------------------------------------------- #
def regime_labels(high: np.ndarray, low: np.ndarray, close: np.ndarray, *,
                  window: int = REGIME_WINDOW, cuts: tuple[float, float] = REGIME_CUTS,
                  atr_period: int = ATR_PERIOD) -> np.ndarray:
    """Causal trailing rolling-percentile ATR regime label per bar.

    For bar ``i`` with a full trailing window of defined ATR, the label is the cut of
    the percentile of the current ``ATR(i)`` within the ``window`` most-recent ATR
    values (ending at ``i``, all known at bar close ``i`` — no future bar enters a
    label). Bars without a full finite trailing window are ``REGIME_UNDEFINED``.

    Parameters
    ----------
    high, low, close : np.ndarray
        Real domain-bar OHLC arrays (float64), length ``n``.
    window : int
        Trailing percentile window in bars.
    cuts : (float, float)
        ``(p_low, p_high)`` percentile cuts; ``< p_low`` -> LOW, ``> p_high`` -> HIGH.
    atr_period : int
        Wilder ATR period.

    Returns
    -------
    np.ndarray
        Int64 regime label per bar (``-1`` undefined / ``0`` LOW / ``1`` MED / ``2`` HIGH).
    """
    atr = wilder_atr(np.asarray(high, np.float64), np.asarray(low, np.float64),
                     np.asarray(close, np.float64), atr_period)
    n = atr.shape[0]
    labels = np.full(n, REGIME_UNDEFINED, dtype=np.int64)
    if n < window:
        return labels
    sw = sliding_window_view(atr, window)                 # row k spans atr[k : k+window], ends at i
    ends = np.arange(window - 1, n)
    cur = atr[ends]
    finite = np.all(np.isfinite(sw), axis=1) & np.isfinite(cur)
    less = np.where(np.isfinite(sw), sw < cur[:, None], False)
    pct = less.sum(axis=1) / float(window)
    lo_cut, hi_cut = cuts
    bucket = np.full(pct.shape[0], REGIME_MED, dtype=np.int64)
    bucket[pct < lo_cut] = REGIME_LOW
    bucket[pct > hi_cut] = REGIME_HIGH
    sel = ends[finite]
    labels[sel] = bucket[finite]
    return labels


# --------------------------------------------------------------------------- #
# Pure computation — regime-matched random draw (leg-1 control + permutation pool)
# --------------------------------------------------------------------------- #
def regime_candidate_idx(regime_label: np.ndarray, regime: int) -> np.ndarray:
    """Ascending domain-bar indices whose regime label equals ``regime``."""
    return np.flatnonzero(np.asarray(regime_label) == regime).astype(np.int64)


def regime_matched_entries(regime_label: np.ndarray, regime: int, n_target: int,
                           rng: np.random.Generator) -> np.ndarray:
    """``min(n_target, n_candidates)`` distinct same-regime bar indices (ascending).

    The regime-restricted analog of ``xen.capgeo_substrates.random_entries``: random
    timing **within the regime** (entries land only on real closes carrying ``regime``
    → look-ahead-safe and regime-matched by construction), sampled without replacement
    and sorted. Fully determined by ``rng``. Used for both the count-matched control
    and the larger permutation pool (the caller passes the desired ``n_target``).

    Parameters
    ----------
    regime_label : np.ndarray
        Per-bar regime label (``regime_labels`` output).
    regime : int
        Target regime (LOW/MED/HIGH).
    n_target : int
        Desired draw size; clipped to the number of same-regime candidate bars.
    rng : np.random.Generator
        Seeded generator.

    Returns
    -------
    np.ndarray
        Int64 ascending bar indices, length ``min(n_target, n_candidates)``.
    """
    cand = regime_candidate_idx(regime_label, regime)
    k = int(min(max(0, int(n_target)), cand.shape[0]))
    if k == 0:
        return np.empty(0, dtype=np.int64)
    return np.sort(rng.choice(cand, size=k, replace=False)).astype(np.int64)
