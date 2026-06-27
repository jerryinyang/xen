"""Per-event cost/financing overlay + exit-bar recovery for CF-CAPGEO-001 (Phase 018 / EXP-085).

This module supports the **TRAIN-only gross->net cost read-gate** (EXP-085, HYP-004 cost layer,
D0-amendment-002). It adds **no** entry, exit, barrier, or denominator logic: it (a) recovers the per-event
**exit bar index** that the frozen ``xen.capgeo_screen`` resolvers compute internally but discard, by
running a **line-faithful mirror** of each resolver's causal first-touch scan, and (b) converts a
predeclared conservative round-trip + holding-time financing model into the screen's **ATR units** so a net
per-event return can be formed on the *identical* resolved-event set.

Why the mirror is needed. The frozen resolvers (``resolve_static_barrier``, ``resolve_fixed_horizon``,
``resolve_partial_two_leg``) return only ``ret``/``cls``/``resolved`` (``Resolution``); the exit bar ``k`` is
local. The **financing** leg charges per realized holding day, so the exit bar (and, for the two-leg partial,
the *final* leg-2 bar) is required. The frozen modules must not be edited (their source hashes are asserted),
so the exit index is recovered here. The mirror scans are **byte-faithful transcriptions** of the frozen
resolver bodies (same ``entry+1..min(cap,last)`` window, same **adverse-first P15 tie-break**); fidelity is
enforced at the call site by a reconciliation guard that the mirror's recomputed ``ret`` matches the frozen
``Resolution.ret`` within 1e-9 AND the recomputed ``cls`` and resolved mask match exactly. Because a FAV/ADV
touch yields the same realized value at any touching bar, ret-reconciliation alone cannot pin the bar — the
guard is *necessary but not sufficient*; bar-index fidelity rests on the transcription being line-faithful
(auditable by diffing against ``capgeo_screen.py``). The guard HALTs on any mismatch.

Discipline: real prices only; ATR(14) normalization (the EXP-081 frame); causal (cost applied to the
already-resolved path, no look-ahead); no I/O, no RNG, no globals. Financing is always a **subtracted cost**,
never credited, direction-agnostic. One round-trip per event (a partial's scale-out leg is not separately
charged — the frozen "one round-trip per event" rule).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from xen.capgeo_screen import (
    CLASS_ADV,
    CLASS_CENSORED,
    CLASS_FAV,
    CLASS_TIMECAP,
)

# --------------------------------------------------------------------------- #
# Predeclared cost model (frozen structure; constants pending operator ratification at Stage 4).
# CONSERVATIVE round-trip = 2 x BASE (EXP-030 precedent); financing = adverse-side bps/day (EXP-034).
# RT_i is round-trip bps of price (spread + commission + spread-scaled slippage, folded in); F_i is
# financing bps of price per calendar day, charged on realized holding duration.
# --------------------------------------------------------------------------- #
RECON_TOL: float = 1e-9          # mirror-vs-frozen realized-return reconciliation tolerance
MINUTES_PER_DAY: float = 1_440.0

#: Per-instrument (RT_i bps round-trip, F_i bps/day adverse financing) — CONSERVATIVE binding.
COST_CONSTANTS: dict[str, tuple[float, float]] = {
    "AUDUSD": (4.0, 0.8),
    "NZDUSD": (4.5, 0.8),
    "USDCAD": (4.0, 0.7),
    "USTEC": (5.0, 1.2),
}

#: Holding-duration definition (binding; operator-ratified at EXP-085 Stage 4, 2026-06-22).
HOLDING_DAYS_DEFINITION: str = (
    "bar-count proxy = (exit_idx - entry_idx) * domain_minutes / 1440 (trading-bar span only); "
    "partial two-leg uses the leg-2 (final) exit bar. Operator-ratified Stage 4 over the wall-clock "
    "alternative."
)


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ExitPath:
    """Recovered per-event exit geometry for one candidate Resolution (entry-ordered, all kept events).

    ``exit_idx`` is the bar the position fully closes on (leg-2 for the partial); -1 for unresolved /
    censored / excluded events. ``leg1_idx`` is the partial's scale-out bar (-1 otherwise / unresolved).
    ``ret_mirror``/``cls_mirror`` are the mirror's independently recomputed realized return / class, used
    only to reconcile against the frozen resolver (never returned to any statistic).
    """

    exit_idx: np.ndarray         # int64; -1 where unresolved
    leg1_idx: np.ndarray         # int64; -1 where not applicable / unresolved
    ret_mirror: np.ndarray       # float64; NaN where unresolved (reconciliation only)
    cls_mirror: np.ndarray       # int64 (reconciliation only)


# --------------------------------------------------------------------------- #
# Pure computation — line-faithful exit-bar mirrors of the frozen resolvers
# (transcribe capgeo_screen.resolve_* EXACTLY: same window, adverse-first tie-break, mark-to-close).
# --------------------------------------------------------------------------- #
def static_barrier_exit(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, atr_entry: np.ndarray,
    entry_idx: np.ndarray, direction: np.ndarray,
    t_fav: np.ndarray, s_adv: np.ndarray, h_cap: np.ndarray, n_bars: int,
) -> ExitPath:
    """Exit-bar mirror of ``capgeo_screen.resolve_static_barrier`` (first-touch triple barrier)."""
    m = int(entry_idx.shape[0])
    exit_idx = np.full(m, -1, dtype=np.int64)
    ret = np.full(m, np.nan, dtype=np.float64)
    cls = np.full(m, CLASS_CENSORED, dtype=np.int64)
    last = n_bars - 1
    for j in range(m):
        a = float(atr_entry[j])
        if not np.isfinite(a) or a <= 0.0:
            continue
        tf = float(t_fav[j])
        if not np.isfinite(tf) or tf <= 0.0:
            continue
        i = int(entry_idx[j])
        d = int(direction[j])
        c0 = float(close[i])
        has_stop = bool(np.isfinite(s_adv[j]))
        fav_lvl = c0 + d * tf * a
        adv_lvl = c0 - d * float(s_adv[j]) * a if has_stop else np.nan
        lo, cap_end = i + 1, i + int(h_cap[j])
        hi = min(cap_end, last)
        if lo > hi:
            continue
        hit, k_hit = None, -1
        for k in range(lo, hi + 1):
            if d == 1:
                fav, adv = high[k] >= fav_lvl, has_stop and low[k] <= adv_lvl
            else:
                fav, adv = low[k] <= fav_lvl, has_stop and high[k] >= adv_lvl
            if adv:
                hit, k_hit = CLASS_ADV, k
                break
            if fav:
                hit, k_hit = CLASS_FAV, k
                break
        if hit == CLASS_ADV:
            cls[j], ret[j], exit_idx[j] = CLASS_ADV, -float(s_adv[j]), k_hit
        elif hit == CLASS_FAV:
            cls[j], ret[j], exit_idx[j] = CLASS_FAV, float(t_fav[j]), k_hit
        elif hi < cap_end:
            cls[j] = CLASS_CENSORED
        else:
            cls[j], ret[j], exit_idx[j] = CLASS_TIMECAP, d * (float(close[hi]) - c0) / a, hi
    return ExitPath(exit_idx=exit_idx, leg1_idx=np.full(m, -1, dtype=np.int64),
                    ret_mirror=ret, cls_mirror=cls)


def fixed_horizon_exit(
    close: np.ndarray, atr_entry: np.ndarray, entry_idx: np.ndarray, direction: np.ndarray,
    h_cap: np.ndarray, n_bars: int,
) -> ExitPath:
    """Exit-bar mirror of ``capgeo_screen.resolve_fixed_horizon`` (mark-to-close at the horizon)."""
    m = int(entry_idx.shape[0])
    exit_idx = np.full(m, -1, dtype=np.int64)
    ret = np.full(m, np.nan, dtype=np.float64)
    cls = np.full(m, CLASS_CENSORED, dtype=np.int64)
    last = n_bars - 1
    for j in range(m):
        a = float(atr_entry[j])
        if not np.isfinite(a) or a <= 0.0:
            continue
        i = int(entry_idx[j])
        cap_end = i + int(h_cap[j])
        if i + 1 > last:
            continue
        hi = min(cap_end, last)
        if hi == cap_end:
            cls[j] = CLASS_TIMECAP
            ret[j] = int(direction[j]) * (float(close[hi]) - float(close[i])) / a
            exit_idx[j] = hi
        else:
            cls[j] = CLASS_CENSORED
    return ExitPath(exit_idx=exit_idx, leg1_idx=np.full(m, -1, dtype=np.int64),
                    ret_mirror=ret, cls_mirror=cls)


def partial_two_leg_exit(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, atr_entry: np.ndarray,
    entry_idx: np.ndarray, direction: np.ndarray,
    t_fav: np.ndarray, s_adv: np.ndarray, h_cap: np.ndarray, n_bars: int,
    leg_frac: float = 0.5,
) -> ExitPath:
    """Exit-bar mirror of ``capgeo_screen.resolve_partial_two_leg``; ``exit_idx`` = leg-2 (final) bar."""
    m = int(entry_idx.shape[0])
    exit_idx = np.full(m, -1, dtype=np.int64)
    leg1_idx = np.full(m, -1, dtype=np.int64)
    ret = np.full(m, np.nan, dtype=np.float64)
    cls = np.full(m, CLASS_CENSORED, dtype=np.int64)
    last = n_bars - 1
    for j in range(m):
        a = float(atr_entry[j])
        if not np.isfinite(a) or a <= 0.0:
            continue
        tf = float(t_fav[j])
        if not np.isfinite(tf) or tf <= 0.0:
            continue
        i = int(entry_idx[j])
        d = int(direction[j])
        c0 = float(close[i])
        has_stop = bool(np.isfinite(s_adv[j]))
        fav_lvl = c0 + d * tf * a
        adv_lvl = c0 - d * float(s_adv[j]) * a if has_stop else np.nan
        lo, cap_end = i + 1, i + int(h_cap[j])
        hi = min(cap_end, last)
        if lo > hi:
            continue
        leg1, taken1, k1 = np.nan, False, -1
        leg2, done2, k2 = np.nan, False, -1
        for k in range(lo, hi + 1):
            if d == 1:
                fav, adv = high[k] >= fav_lvl, has_stop and low[k] <= adv_lvl
            else:
                fav, adv = low[k] <= fav_lvl, has_stop and high[k] >= adv_lvl
            if adv:
                if not taken1:
                    leg1, taken1, k1 = -float(s_adv[j]), True, k
                leg2, done2, k2 = -float(s_adv[j]), True, k
                break
            if fav and not taken1:
                leg1, taken1, k1 = float(t_fav[j]), True, k
        if not done2:
            if hi < cap_end and not taken1:
                cls[j] = CLASS_CENSORED
                continue
            tail_ret = d * (float(close[hi]) - c0) / a
            leg2, k2 = tail_ret, hi
            if not taken1:
                leg1, k1 = tail_ret, hi
        cls[j] = CLASS_FAV if taken1 else CLASS_TIMECAP
        ret[j] = leg_frac * float(leg1) + (1.0 - leg_frac) * float(leg2)
        exit_idx[j], leg1_idx[j] = k2, k1
    return ExitPath(exit_idx=exit_idx, leg1_idx=leg1_idx, ret_mirror=ret, cls_mirror=cls)


# --------------------------------------------------------------------------- #
# Pure computation — reconciliation guard + per-event cost / net
# --------------------------------------------------------------------------- #
def reconcile_exit_path(path: ExitPath, frozen_ret: np.ndarray, frozen_cls: np.ndarray,
                        tol: float = RECON_TOL) -> bool:
    """True iff the mirror reproduces the frozen resolver's ret (within ``tol``) and cls / mask exactly.

    Parameters
    ----------
    path : ExitPath
        Mirror output for one candidate.
    frozen_ret, frozen_cls : np.ndarray
        The frozen ``Resolution.ret`` / ``Resolution.cls`` for the same candidate (same event order).
    tol : float
        Absolute tolerance on the realized-return reconciliation.

    Returns
    -------
    bool
        True on a full match (the caller HALTs on False).
    """
    fin_m, fin_f = np.isfinite(path.ret_mirror), np.isfinite(frozen_ret)
    if not np.array_equal(fin_m, fin_f):
        return False
    if not np.array_equal(path.cls_mirror, frozen_cls):
        return False
    if fin_f.any() and float(np.max(np.abs(path.ret_mirror[fin_f] - frozen_ret[fin_f]))) > tol:
        return False
    # Every resolved event must carry a real exit bar.
    return bool(np.all(path.exit_idx[fin_f] >= 0))


def holding_days(entry_idx: np.ndarray, exit_idx: np.ndarray, domain_minutes: int) -> np.ndarray:
    """Bar-count-proxy days held per event = bars-held * domain_minutes / 1440 (entry->final exit).

    Operator-ratified definition (EXP-085 Stage 4, 2026-06-22): the trading-bar span, not wall-clock
    calendar time. ``bars_held = exit_idx - entry_idx`` (>= 1 on resolved events, since exit >= entry+1).

    Parameters
    ----------
    entry_idx, exit_idx : np.ndarray
        Per-event entry / final-exit bar indices (exit_idx >= 0 on resolved events).
    domain_minutes : int
        Minutes per domain bar (15, 60, or 240).

    Returns
    -------
    np.ndarray
        Holding duration in days (> 0 on resolved events; NaN where exit_idx < 0).
    """
    out = np.full(entry_idx.shape[0], np.nan, dtype=np.float64)
    ok = exit_idx >= 0
    out[ok] = (exit_idx[ok] - entry_idx[ok]).astype(np.float64) * float(domain_minutes) \
        / MINUTES_PER_DAY
    return out


@dataclass(frozen=True)
class EventCosts:
    """Per-event ATR-unit cost decomposition and net return on the resolved-event set."""

    cost_txn: np.ndarray
    cost_fin: np.ndarray
    cost_total: np.ndarray
    net: np.ndarray
    holding_days: np.ndarray


def event_costs(gross_atr: np.ndarray, p_entry: np.ndarray, atr_entry: np.ndarray,
                holding_days_e: np.ndarray, rt_bps: float, fin_bps_day: float) -> EventCosts:
    """Per-event transaction + financing cost (ATR units) and net = gross - cost, on resolved events.

    All inputs are aligned, resolved-event arrays. ``cost_txn = (RT/1e4) * P_entry / ATR_entry``;
    ``cost_fin = (F/1e4) * holding_days * P_entry / ATR_entry``. Financing is always a subtracted cost.

    Parameters
    ----------
    gross_atr : np.ndarray
        Frozen realized ATR returns (resolved events only).
    p_entry, atr_entry : np.ndarray
        Entry close price and entry ATR(14) (price units), per resolved event (atr_entry > 0).
    holding_days_e : np.ndarray
        Realized holding duration in days (>= 0).
    rt_bps, fin_bps_day : float
        Round-trip bps and financing bps/day for the instrument.

    Returns
    -------
    EventCosts
        Per-event cost decomposition and net return.
    """
    if np.any(~np.isfinite(atr_entry)) or np.any(atr_entry <= 0.0):
        raise ValueError("event_costs: non-finite or non-positive ATR on a resolved event")
    if np.any(~np.isfinite(holding_days_e)) or np.any(holding_days_e < 0.0):
        raise ValueError("event_costs: non-finite or negative holding duration on a resolved event")
    px_per_atr = p_entry / atr_entry
    cost_txn = (rt_bps / 1e4) * px_per_atr
    cost_fin = (fin_bps_day / 1e4) * holding_days_e * px_per_atr
    cost_total = cost_txn + cost_fin
    return EventCosts(cost_txn=cost_txn, cost_fin=cost_fin, cost_total=cost_total,
                      net=gross_atr - cost_total, holding_days=holding_days_e)
