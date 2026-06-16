"""Adverse-target geometry for ``CF-HA-HARAMI-001`` (Phase 014-B, EXP-057).

The single new analysis module for the adverse-target surface read. It supplies
the *adverse-leg* primitives EXP-057 varies one-at-a-time against the frozen
benchmark 1:1 adverse target (``adv = C - rd*0.5*M_sofar``), while the
favourable target (50% of ``M_sofar``), the third barrier (adaptive time cap),
and the P15 intrabar fills are held at benchmark and reused from
:mod:`xen.expectancy`:

1. **Faded-move running extreme** (`faded_move_extreme`) — the causal running
   extreme of the in-progress (faded) move as-of entry, scanned over the real-bar
   span ``[start_idx+1 .. entry_idx]`` inclusive (``min Low`` for a long fade
   ``rd=+1``, ``max High`` for a short fade ``rd=-1``). ``start_idx`` is the bar
   of the in-progress move's start pivot (``EndTime_k`` of a move confirmed
   ``<= t_i``), so every scanned bar has ``CloseTime <= t_i`` and the quantity is
   known at entry. This is the *causal* reading of "previous-move extreme" for a
   reversal fade — distinct from the EXP-050 descriptive position-in-move metric,
   and never an unconfirmed end pivot.
2. **/ADV-EXTREME adverse levels** (`adverse_extreme_raw`,
   `adverse_extreme_rr1`) — a buffered faded-extreme stop (raw; R:R free) and the
   same stop widened to at least the benchmark 1:1 distance (rr1; isolates
   extreme-anchoring from stop-width). The buffer is ``0.25 * ATR_entry``; the raw
   form carries a disclosed degeneracy floor ``adv_dist >= 0.10 * ATR_entry``.
3. **/ADV-NONE sentinel** (`adverse_none_sentinel`) — an unreachable adverse
   level (``-inf`` for a long fade, ``+inf`` for a short fade) so the shared P15
   resolver returns only ``FAV`` or ``TIMECAP``.
4. **Generalized adverse barriers** (`barriers_with_adverse`) — pair the
   benchmark favourable level ``fav = C + rd*fav_dist`` with a supplied adverse
   level and compute the base validity flag.

Real prices only in every metric. Heiken Ashi prices never enter this module.
"""
from __future__ import annotations

import numpy as np

# --------------------------------------------------------------------------- #
# Frozen EXP-057 predeclared adverse-target constants (no tuning)
# --------------------------------------------------------------------------- #
ADV_BUFFER_FRAC = 0.25      # /ADV-EXTREME buffer beyond the faded extreme (* ATR_entry)
ADV_FLOOR_FRAC = 0.10       # raw degeneracy floor: adv_dist >= 0.10 * ATR_entry


# --------------------------------------------------------------------------- #
# Pure computation — faded-move causal running extreme
# --------------------------------------------------------------------------- #
def faded_move_extreme(
    low: np.ndarray, high: np.ndarray, start_idx: np.ndarray,
    entry_idx: np.ndarray, rd: np.ndarray, available: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Causal running extreme of the in-progress (faded) move as-of each entry.

    For each available event the span is ``[start_idx+1 .. entry_idx]`` inclusive
    on real bars; if ``start_idx == entry_idx`` (no intervening bar) the span is
    the entry bar alone. The extreme is ``min(Low)`` for a long fade (``rd=+1``)
    and ``max(High)`` for a short fade (``rd=-1``). Bounded sequential scan per
    event — its causal semantics are the object under test; every scanned bar has
    index ``<= entry_idx`` (``CloseTime <= t_i``), so no future bar is read.

    Parameters
    ----------
    low, high : np.ndarray
        Real domain-bar ``Low`` / ``High`` (float64), full cell grid.
    start_idx : np.ndarray
        Bar index of each event's in-progress move start pivot (``-1`` if none).
    entry_idx : np.ndarray
        Bar index of each event's entry (harami) bar.
    rd : np.ndarray
        Reversal trade direction per event (``+1`` long fade / ``-1`` short fade).
    available : np.ndarray
        Bool gate (a confirmed move precedes the entry, so ``start_idx`` resolves).

    Returns
    -------
    (faded_extreme, avail) : (np.ndarray[float64], np.ndarray[bool])
        ``faded_extreme`` is ``NaN`` wherever ``avail`` is ``False``.
    """
    n = int(entry_idx.shape[0])
    extreme = np.full(n, np.nan, dtype=np.float64)
    avail = np.zeros(n, dtype=bool)
    for e in range(n):
        if not available[e]:
            continue
        si, ei = int(start_idx[e]), int(entry_idx[e])
        if si < 0 or ei < 0 or si > ei:
            continue
        lo = si + 1 if si < ei else ei            # entry bar == start bar -> entry bar alone
        if rd[e] == 1:                            # long fade: adverse side is below C
            extreme[e] = float(np.min(low[lo:ei + 1]))
        else:                                     # short fade: adverse side is above C
            extreme[e] = float(np.max(high[lo:ei + 1]))
        avail[e] = True
    return extreme, avail


# --------------------------------------------------------------------------- #
# Pure computation — generalized adverse barriers + per-variant builders
# --------------------------------------------------------------------------- #
def _zero_reasons(n: int) -> dict[str, np.ndarray]:
    """Mutually-exclusive disclosed exclusion-reason masks (all ``False``)."""
    return {"reason_validity": np.zeros(n, dtype=bool),
            "reason_warmup": np.zeros(n, dtype=bool),
            "reason_degenerate": np.zeros(n, dtype=bool)}


def barriers_with_adverse(
    entry_close: np.ndarray, rd: np.ndarray, fav_dist: np.ndarray,
    adv: np.ndarray, adv_dist: np.ndarray, has_stop: bool,
) -> dict[str, np.ndarray]:
    """Pair the benchmark favourable level with a supplied adverse level.

    ``fav = C + rd*fav_dist`` (the benchmark favourable, held fixed across all
    variants); base validity requires ``fav_dist > 0`` and, for a stopped variant,
    a finite adverse level with ``adv_dist > 0``. The raw degeneracy floor and the
    extreme-availability gate are applied by the calling builder. Real prices only.
    """
    fav = entry_close + rd * fav_dist
    fav_ok = fav_dist > 0.0
    if has_stop:
        ok = fav_ok & np.isfinite(adv) & np.isfinite(adv_dist) & (adv_dist > 0.0)
    else:
        ok = fav_ok
    return {"fav": fav, "adv": adv, "fav_dist": fav_dist, "adv_dist": adv_dist, "ok": ok}


def adverse_extreme_raw(
    entry_close: np.ndarray, rd: np.ndarray, fav_dist: np.ndarray,
    faded_extreme: np.ndarray, atr_entry: np.ndarray, ext_avail: np.ndarray,
) -> dict[str, np.ndarray]:
    """``/ADV-EXTREME`` raw stop: buffered faded extreme, R:R free.

    ``adv = faded_extreme - rd*0.25*ATR_entry``; ``adv_dist = rd*(C - adv)``. By
    construction ``adv_dist >= 0.25*ATR_entry`` (the faded extreme is on the
    adverse side), so the disclosed floor ``adv_dist >= 0.10*ATR_entry`` is a
    defensive invariant (expected count ~0), never a silent clamp. Excluded with
    record when the in-progress span is unavailable / ATR is non-finite (warmup)
    or the floor is breached (degenerate). Real prices only.
    """
    n = int(entry_close.shape[0])
    with np.errstate(invalid="ignore"):
        adv = faded_extreme - rd * ADV_BUFFER_FRAC * atr_entry
        adv_dist = rd * (entry_close - adv)
    base = barriers_with_adverse(entry_close, rd, fav_dist, adv, adv_dist, has_stop=True)
    fav_ok = fav_dist > 0.0
    atr_ok = np.isfinite(atr_entry) & (atr_entry > 0.0)
    ext_ok = ext_avail & np.isfinite(faded_extreme)
    floor = ADV_FLOOR_FRAC * np.where(atr_ok, atr_entry, np.nan)
    with np.errstate(invalid="ignore"):
        not_degen = adv_dist >= floor
    ok = base["ok"] & ext_ok & atr_ok & not_degen
    res = _zero_reasons(n)
    res["reason_validity"] = ~fav_ok
    res["reason_warmup"] = fav_ok & (~ext_ok | ~atr_ok)
    res["reason_degenerate"] = fav_ok & ext_ok & atr_ok & ~not_degen
    return {**base, "ok": ok, **res}


def adverse_extreme_rr1(
    entry_close: np.ndarray, rd: np.ndarray, fav_dist: np.ndarray,
    faded_extreme: np.ndarray, atr_entry: np.ndarray, ext_avail: np.ndarray,
) -> dict[str, np.ndarray]:
    """``/ADV-EXTREME`` >=1:1 stop: extreme-anchored, widened to the 1:1 distance.

    ``adv_dist = max(adv_dist_raw, fav_dist)``; ``adv = C - rd*adv_dist``. Keeps
    R:R >= 1:1 like the benchmark, so any expectancy difference vs benchmark is
    attributable to extreme-anchoring, not to a tighter stop. No degeneracy
    exclusion can fire (``adv_dist >= fav_dist > 0``); still requires an available
    faded extreme + finite ATR (else warmup-excluded). Real prices only.
    """
    n = int(entry_close.shape[0])
    raw = adverse_extreme_raw(entry_close, rd, fav_dist, faded_extreme, atr_entry, ext_avail)
    with np.errstate(invalid="ignore"):
        adv_dist = np.maximum(raw["adv_dist"], fav_dist)
        adv = entry_close - rd * adv_dist
    base = barriers_with_adverse(entry_close, rd, fav_dist, adv, adv_dist, has_stop=True)
    fav_ok = fav_dist > 0.0
    atr_ok = np.isfinite(atr_entry) & (atr_entry > 0.0)
    ext_ok = ext_avail & np.isfinite(faded_extreme)
    ok = base["ok"] & ext_ok & atr_ok
    res = _zero_reasons(n)
    res["reason_validity"] = ~fav_ok
    res["reason_warmup"] = fav_ok & (~ext_ok | ~atr_ok)
    return {**base, "ok": ok, **res}


def adverse_none_sentinel(
    entry_close: np.ndarray, rd: np.ndarray, fav_dist: np.ndarray,
) -> dict[str, np.ndarray]:
    """``/ADV-NONE``: unreachable adverse level (no stop).

    Passes ``adv = -inf`` for a long fade (``rd=+1``) and ``adv = +inf`` for a
    short fade (``rd=-1``) into the shared P15 resolver, so ``adv_hit`` never
    fires and only ``FAV`` / ``TIMECAP`` (or ``DATA_CENSORED`` at the data edge)
    can resolve. No stop, hence no degeneracy/extreme exclusion — only the
    favourable-validity gate ``fav_dist > 0`` applies. Real prices only.
    """
    n = int(entry_close.shape[0])
    adv = np.where(rd == 1, -np.inf, np.inf).astype(np.float64)
    adv_dist = np.full(n, np.inf, dtype=np.float64)
    base = barriers_with_adverse(entry_close, rd, fav_dist, adv, adv_dist, has_stop=False)
    res = _zero_reasons(n)
    res["reason_validity"] = ~(fav_dist > 0.0)
    return {**base, **res}
