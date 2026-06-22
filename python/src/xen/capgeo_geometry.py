"""Adaptive-cap realized path geometry + shape diagnostics for CF-CAPGEO-001 (EXP-081).

Pure, real-price return-structure characterization of a frozen-entry event's realized
post-entry path over a per-event **adaptive time cap** on **real** domain OHLC:

1. :func:`lifetime_path_geometry` — per event ``(entry index i, direction d, cap c bars)``
   over the window ``W = [i+1, min(i+c, last)]`` (``last`` = the final available domain-bar
   index; windows clip there so they never read holdout/TEST rows):

   - ``fav_t = (H_t - C_i)`` if ``d = +1`` else ``(C_i - L_t)``  (favourable excursion)
   - ``adv_t = (C_i - L_t)`` if ``d = +1`` else ``(H_t - C_i)``  (adverse excursion magnitude)
   - ``MFE`` (ATR) ``= max(0, max_t fav_t) / ATR_i``;  ``MAE`` (ATR) ``= max(0, max_t adv_t) / ATR_i``
     (floored at 0 — the programme MFE/MAE convention, EXP-055 ``availability.py``; both ``>= 0`` so
     ``MAE_q90`` is a valid adverse stop distance for EXP-082)
   - ``TTP`` (bars) ``= argmax_t fav_t`` measured from entry (first/earliest on ties)
   - ``outcome`` (ATR) ``= d * (C_last(W) - C_i) / ATR_i``  (signed cap-bar realized return)

2. :func:`antimode_mae` — the antimode/dip location ``m_anti`` of the MAE distribution
   (dominant-vs-catastrophic-minority boundary) via the Hartigan dip test plus an adaptive-KDE
   antimode between the two highest modes; ``NaN`` when unimodal (dip not significant) or the
   two modes are unresolved.

3. :func:`tail_stats` — the minority-mass / left-tail read ``ASS`` structurally lacks:
   ``tailmass`` (fraction of realized outcomes below the catastrophe boundary
   ``median - K_tail * MAD``) and ``q05``.

No exit / barrier / target is applied here (those are EXP-082/083). Every metric is on real
prices; Heiken Ashi prices never enter. The per-event loop is explicit and causal (bounded by
the adaptive cap); only the intra-window max/argmax is vectorized.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

from xen.ass import adaptive_kde_pdf, default_k_bw, knn_bandwidths, make_grid

# Frozen catastrophe-boundary constant (Phase 018 D0 §D9 bite-check; never tuned).
K_TAIL: float = 3.0
# Hartigan dip-test significance for the m_anti bimodality leg (frozen, matches xen.ass).
DIP_ALPHA: float = 0.05


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PathGeometry:
    """Per-usable-event realized path geometry (ATR units; aligned to input event order).

    ``mfe``/``mae``/``outcome`` are ``NaN`` and ``ttp`` is ``-1`` for events excluded by the
    ATR-undefined or clipped-empty guards; ``usable`` is the boolean mask of retained events.
    """

    mfe: np.ndarray
    mae: np.ndarray
    ttp: np.ndarray
    outcome: np.ndarray
    usable: np.ndarray
    n_atr_undefined: int
    n_clipped_empty: int


@dataclass(frozen=True)
class TailStats:
    """Left-tail / minority-mass read on a realized-outcome sample."""

    tailmass: float
    q05: float
    boundary: float
    mad_zero: bool
    n: int


# --------------------------------------------------------------------------- #
# Pure computation — adaptive-cap path geometry (explicit causal event loop)
# --------------------------------------------------------------------------- #
def lifetime_path_geometry(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    atr_entry: np.ndarray,
    entry_idx: np.ndarray,
    direction: np.ndarray,
    cap: np.ndarray,
    n_bars: int,
) -> PathGeometry:
    """Realized MFE/MAE/TTP/outcome over each event's adaptive cap on real OHLC.

    Parameters
    ----------
    high, low, close : np.ndarray
        Real domain-bar OHLC arrays (float64), length ``n_bars``.
    atr_entry : np.ndarray
        Per-event Wilder ATR at the entry bar (ATR units denominator), length ``m``.
    entry_idx : np.ndarray
        Per-event entry bar index into the OHLC arrays (int), length ``m``.
    direction : np.ndarray
        Per-event position direction ``+1``/``-1`` (int), length ``m``.
    cap : np.ndarray
        Per-event adaptive time cap in bars (int, > 0; warmup events excluded upstream),
        length ``m``.
    n_bars : int
        Number of available domain bars; windows clip at ``n_bars - 1`` (the TRAIN edge).

    Returns
    -------
    PathGeometry
        Per-event geometry in ATR units plus the usable mask and exclusion counts. An event
        with non-finite/non-positive ATR (``n_atr_undefined``) or an empty post-clip window
        (``n_clipped_empty``) is excluded.
    """
    m = int(entry_idx.shape[0])
    mfe = np.full(m, np.nan, dtype=np.float64)
    mae = np.full(m, np.nan, dtype=np.float64)
    ttp = np.full(m, -1, dtype=np.int64)
    outcome = np.full(m, np.nan, dtype=np.float64)
    last = n_bars - 1
    atr_ok = np.isfinite(atr_entry) & (atr_entry > 0.0)
    n_atr_undefined = int(np.count_nonzero(~atr_ok))
    n_clipped_empty = 0
    for j in range(m):
        if not atr_ok[j]:
            continue
        i = int(entry_idx[j])
        lo = i + 1
        hi = min(i + int(cap[j]), last)
        if lo > hi:
            n_clipped_empty += 1
            continue
        d = int(direction[j])
        c0 = float(close[i])
        a = float(atr_entry[j])
        h = high[lo:hi + 1]
        ll = low[lo:hi + 1]
        if d == 1:
            fav = h - c0
            adv = c0 - ll
        else:
            fav = c0 - ll
            adv = h - c0
        kfav = int(np.argmax(fav))                 # first/earliest favourable peak on ties
        mfe[j] = max(0.0, float(fav[kfav])) / a    # MFE/MAE floored at 0 (EXP-055 convention)
        mae[j] = max(0.0, float(adv.max())) / a
        ttp[j] = kfav + 1                          # bars from entry (lo == i + 1)
        outcome[j] = d * (float(close[hi]) - c0) / a
    usable = np.isfinite(mfe)
    return PathGeometry(mfe=mfe, mae=mae, ttp=ttp, outcome=outcome, usable=usable,
                        n_atr_undefined=n_atr_undefined, n_clipped_empty=n_clipped_empty)


# --------------------------------------------------------------------------- #
# Pure computation — shape diagnostics (m_anti antimode; tail mass)
# --------------------------------------------------------------------------- #
def _antimode_between_top_modes(grid: np.ndarray, pdf: np.ndarray) -> float:
    """Min-density grid point strictly between the two highest KDE modes (else ``NaN``)."""
    if pdf.shape[0] < 3:
        return float("nan")
    is_max = (pdf[1:-1] > pdf[:-2]) & (pdf[1:-1] >= pdf[2:])
    peaks = np.where(is_max)[0] + 1
    if peaks.shape[0] < 2:
        return float("nan")
    top2 = peaks[np.argsort(pdf[peaks])[-2:]]
    a, b = int(min(top2)), int(max(top2))
    if b - a < 1:
        return float("nan")
    seg = pdf[a:b + 1]
    return float(grid[a + int(np.argmin(seg))])


def antimode_mae(mae: np.ndarray, *, dip_alpha: float = DIP_ALPHA) -> tuple[float, float, float]:
    """Hartigan dip statistic/p-value and the MAE antimode location ``m_anti``.

    Returns ``(dip_stat, dip_p, m_anti)``. ``m_anti`` is ``NaN`` when the sample is too small
    (``< 4``), unimodal (``dip_p >= dip_alpha``), or the two modes cannot be resolved on the
    adaptive KDE. ``m_anti`` is power-limited at small ``n`` by construction (Phase 018 D0
    §D9); the EXP-082 adverse leg uses the ``MAE_q90`` fallback wherever it is ``NaN``.
    """
    import diptest                                  # project dependency (also used by xen.ass)

    x = np.asarray(mae, dtype=np.float64)
    n = x.shape[0]
    if n < 4:
        return (float("nan"), float("nan"), float("nan"))
    dip_stat, dip_p = diptest.diptest(x)
    if not (float(dip_p) < dip_alpha):
        return (float(dip_stat), float(dip_p), float("nan"))
    k_bw = default_k_bw(n)
    grid = make_grid(x, knn_bandwidths(x, k_bw))
    pdf = adaptive_kde_pdf(x, grid, k_bw)
    return (float(dip_stat), float(dip_p), _antimode_between_top_modes(grid, pdf))


def tail_stats(outcome: np.ndarray, *, k_tail: float = K_TAIL) -> TailStats:
    """Left-tail-mass and q05 of a realized-outcome sample (catastrophe boundary read).

    The catastrophe boundary is ``median - k_tail * MAD`` (``MAD`` = median absolute deviation,
    ``scale=1.0``; matches :func:`xen.ass.shape_diagnostic`). ``tailmass`` is the fraction of
    outcomes strictly below the boundary; with a zero-tail it is ``0.0`` (never ``0/0``). A
    degenerate ``MAD == 0`` sample sets ``mad_zero`` (the boundary collapses to the median) so
    the caller can record it rather than pass silently.
    """
    x = np.asarray(outcome, dtype=np.float64)
    n = int(x.shape[0])
    if n == 0:
        return TailStats(tailmass=0.0, q05=float("nan"), boundary=float("nan"),
                         mad_zero=False, n=0)
    median = float(np.median(x))
    mad = float(stats.median_abs_deviation(x, scale=1.0))
    boundary = median - k_tail * mad
    tailmass = float(np.count_nonzero(x < boundary)) / n
    q05 = float(np.quantile(x, 0.05, method="linear"))
    return TailStats(tailmass=tailmass, q05=q05, boundary=boundary,
                     mad_zero=bool(mad == 0.0), n=n)
