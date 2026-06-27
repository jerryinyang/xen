"""Single-series compression primitives for Phase 019 Screen M (EXP-086, CF-VOLEXP-001).

Two **non-directional compression states**, frozen at Phase 019 D0-amendment-001
(`docs/experiments-docs/checkpoints/2026-06-22-019-family-selection-availability-screen/`), behind
the shared :class:`xen.capgeo_substrates.EntrySet` interface so Screen M reuses the EXP-080/081
readiness/geometry scaffolding unchanged:

- ``COND-HARAMI`` — the **raw** direction-agnostic HA harami inside-bar
  (:func:`xen.ha_harami.detect_ha_harami`); HA candles are used for **detection only** (no MA(20,50)
  segmentation, no ``/STRONG-STAT`` conditioning — that is the directional dead-cell substrate, not
  used here). Each harami is mapped to the real domain-bar that *confirms* it (``HA0Time``).
- ``COND-NR7`` — real-OHLC **NR7**: bar ``i`` fires iff its true range is the (weak) minimum of the
  trailing 7 true ranges, ``TR_i <= min(TR[i-6 .. i])`` — the canonical low-volatility compression
  precursor to range expansion. Causal (uses only bars ``<= i``); deterministic.

Both detectors are deterministic and look-ahead-safe. Every return/range metric downstream is on real
prices; these detectors only locate entry bars. The matched-random control and the permuted-axis null
that screen these primitives live in :mod:`xen.availability_gate`.
"""
from __future__ import annotations

import numpy as np
import polars as pl

from xen.capgeo_substrates import EntrySet, _harami_entry_indices, _real_ohlc

# --------------------------------------------------------------------------- #
# Frozen primitive identifiers + parameters (D0-amendment-001; never tuned)
# --------------------------------------------------------------------------- #
COND_HARAMI = "COND-HARAMI"
COND_NR7 = "COND-NR7"
PRIMITIVES = (COND_HARAMI, COND_NR7)

NR_LOOKBACK: int = 7               # NR7 trailing window (bars), frozen


# --------------------------------------------------------------------------- #
# Pure computation — NR7 true-range compression mask
# --------------------------------------------------------------------------- #
def true_range(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    """Gap-inclusive true range per bar (causal): ``max(H,C_prev) - min(L,C_prev)``.

    The first bar has no prior close, so ``TR_0 = H_0 - L_0``. Uses only bars at or before each
    index (no look-ahead).

    Parameters
    ----------
    high, low, close : np.ndarray
        Real domain-bar OHLC arrays (float64), equal length.

    Returns
    -------
    np.ndarray
        Per-bar true range (float64), same length.
    """
    n = high.shape[0]
    tr = np.empty(n, dtype=np.float64)
    if n == 0:
        return tr
    tr[0] = high[0] - low[0]
    if n > 1:
        prev_c = close[:-1]
        tr[1:] = np.maximum(high[1:], prev_c) - np.minimum(low[1:], prev_c)
    return tr


def nr7_mask(high: np.ndarray, low: np.ndarray, close: np.ndarray,
             lookback: int = NR_LOOKBACK) -> np.ndarray:
    """Boolean NR-``lookback`` fire mask: ``TR_i`` is the (weak) minimum of ``TR[i-lookback+1 .. i]``.

    Bars with fewer than ``lookback`` trailing bars (``i < lookback - 1``) never fire (warmup). Causal:
    the window ends at ``i`` and uses only bars ``<= i``.

    Parameters
    ----------
    high, low, close : np.ndarray
        Real domain-bar OHLC (float64), equal length.
    lookback : int
        Trailing window length (default 7, frozen).

    Returns
    -------
    np.ndarray
        Boolean fire mask (length ``n``); ``True`` where bar ``i`` is the trailing-window TR minimum.
    """
    n = high.shape[0]
    fire = np.zeros(n, dtype=bool)
    if n < lookback:
        return fire
    tr = true_range(high, low, close)
    # Trailing-window minimum ending at each index via a sliding view (causal, bounded).
    windows = np.lib.stride_tricks.sliding_window_view(tr, lookback)   # shape (n-lookback+1, lookback)
    win_min = windows.min(axis=1)                                       # min of TR[i-lookback+1 .. i]
    fire[lookback - 1:] = tr[lookback - 1:] <= win_min
    return fire


# --------------------------------------------------------------------------- #
# Entry generators (uniform EntrySet interface; EXP-080/081-compatible)
# --------------------------------------------------------------------------- #
def harami_raw_entries(bars: pl.DataFrame, *, instrument: str, domain: str) -> EntrySet:
    """``COND-HARAMI`` entries: raw direction-agnostic HA harami inside-bars on the domain grid.

    Detects HA haramis (:func:`xen.ha_harami.detect_ha_harami`) and maps each to its confirming real
    domain-bar index (exact ``HA0Time`` match). No MA/``STRONG`` conditioning.

    Parameters
    ----------
    bars : pl.DataFrame
        Real domain bars (one instrument×domain cell, ``CloseTime``-sorted).
    instrument, domain : str
        Cell identity (recorded on the ``EntrySet``).

    Returns
    -------
    EntrySet
        ``substrate='COND-HARAMI'`` with ascending ``entry_idx``/``entry_epoch``.
    """
    ohlc = _real_ohlc(bars)
    n_bars = int(bars.height)
    fence = int(ohlc["epoch"][-1]) if n_bars else 0
    if n_bars == 0:
        return EntrySet(COND_HARAMI, instrument, domain, 0,
                        np.empty(0, np.int64), np.empty(0, np.int64), fence, {})
    entry_idx = _harami_entry_indices(bars, ohlc["epoch"])
    return EntrySet(COND_HARAMI, instrument, domain, n_bars,
                    entry_idx.astype(np.int64), ohlc["epoch"][entry_idx].astype(np.int64),
                    fence, {})


def nr7_entries(bars: pl.DataFrame, *, instrument: str, domain: str,
                lookback: int = NR_LOOKBACK) -> EntrySet:
    """``COND-NR7`` entries: real-OHLC NR-``lookback`` compression bars (trailing TR minimum).

    Parameters
    ----------
    bars : pl.DataFrame
        Real domain bars (one instrument×domain cell, ``CloseTime``-sorted).
    instrument, domain : str
        Cell identity.
    lookback : int
        NR window (default 7, frozen).

    Returns
    -------
    EntrySet
        ``substrate='COND-NR7'`` with ascending ``entry_idx``/``entry_epoch``.
    """
    ohlc = _real_ohlc(bars)
    n_bars = int(bars.height)
    fence = int(ohlc["epoch"][-1]) if n_bars else 0
    if n_bars == 0:
        return EntrySet(COND_NR7, instrument, domain, 0,
                        np.empty(0, np.int64), np.empty(0, np.int64), fence, {})
    fire = nr7_mask(ohlc["high"], ohlc["low"], ohlc["close"], lookback=lookback)
    entry_idx = np.flatnonzero(fire).astype(np.int64)
    return EntrySet(COND_NR7, instrument, domain, n_bars, entry_idx,
                    ohlc["epoch"][entry_idx].astype(np.int64), fence, {})
