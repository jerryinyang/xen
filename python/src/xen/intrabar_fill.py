"""Timestamp-aligned domain→1-minute intrabar fill engine for CF-MR-001 (Phase 021, D2.5).

The reason 1-minute resolution is required: it resolves **which barrier was hit first within a
domain bar** — the EXP-054 fill-model question — with real data instead of a worst-case tie-break.
Every Phase-021 exit arm shares one adverse side (a static ``2.0×ATR`` stop + the MR-tempo cap,
D2.3) and one fill engine (this module); only the favourable mechanism varies:

* an **intrabar favourable limit** (trailing for EXIT-RCT / EXIT-ERT, static for the ATR
  triple-barrier) — filled on the first 1-minute bar whose high (long) / low (short) touches the
  per-domain-bar level; or
* a **domain-close favourable condition** (RSI-revert-on-close when ``RSI₂`` crosses 50; the
  fixed-bar horizon) — exits at that domain bar's close.

Resolution is strictly **causal** (only 1-minute bars at/after entry), **timestamp-aligned**
(each domain bar maps to its constituent 1-minute bars by ``CloseTime`` — never by bar index),
and **holdout-fenced** (no 1-minute bar past ``train_edge_epoch`` is consulted). When both the
favourable target and the adverse stop lie inside one 1-minute bar's ``[Low, High]`` the
**conservative adverse-first tie-break** resolves it. The fill price is the touched **level**
(a real, marketable price), never the 1-minute close and never a synthetic price.

This engine is **readiness/return-shape infrastructure**: it returns resolved exit paths. It does
**not** apply cost, compute strategy expectancy, or select an exit (those are EXP-091+).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

# Exit-kind codes (compact, deterministic).
KIND_UNRESOLVED: int = -1
KIND_FAV: int = 0          # favourable target / condition filled
KIND_ADV: int = 1          # adverse stop hit
KIND_CAP: int = 2          # max-hold cap reached -> exit-on-close

LONG: int = 1
SHORT: int = -1


@dataclass(frozen=True)
class ExitResolution:
    """Per-event resolved exit path (arrays aligned to the input event order, length ``m``).

    Attributes
    ----------
    kind : np.ndarray[int64]
        One of ``KIND_FAV`` / ``KIND_ADV`` / ``KIND_CAP`` per event; ``KIND_UNRESOLVED`` only if
        the post-entry window is empty (clipped at the TRAIN edge before any bar).
    fill_price : np.ndarray[float64]
        Real touched fill level (target/stop level for FAV/ADV; domain close for CAP and for a
        domain-close favourable condition). ``NaN`` when unresolved.
    exit_domain_idx : np.ndarray[int64]
        Domain-bar index at which the event exited (``-1`` when unresolved).
    ttp_bars : np.ndarray[int64]
        Domain bars from entry to exit (``exit_domain_idx - entry_idx``; ``-1`` unresolved).
    tie_break : np.ndarray[bool]
        ``True`` when the terminal 1-minute bar contained **both** barriers and the conservative
        adverse-first rule resolved it (the event is then ``KIND_ADV``).
    resolved : np.ndarray[bool]
        ``kind != KIND_UNRESOLVED``.
    n_fence_clipped : int
        Count of events whose post-entry window was empty after the TRAIN-edge clip.
    """

    kind: np.ndarray
    fill_price: np.ndarray
    exit_domain_idx: np.ndarray
    ttp_bars: np.ndarray
    tie_break: np.ndarray
    resolved: np.ndarray
    n_fence_clipped: int


# --------------------------------------------------------------------------- #
# Pure computation — timestamp mapping (domain bar -> its constituent 1m bars)
# --------------------------------------------------------------------------- #
def minute_bounds_for_domain(
    domain_close_epoch: np.ndarray, minute_close_epoch: np.ndarray, period_s: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Per-domain-bar [start, end) index range into the 1-minute series, **by timestamp**.

    Domain bar ``k`` owns exactly the 1-minute bars whose ``CloseTime`` lies in its own resample
    window ``(domain_close_epoch[k] - period_s, domain_close_epoch[k]]`` (right-closed, matching the
    ``aggregate_ohlc`` ``(epoch-1)//period`` bucket with the right label ``(bucket+1)*period``).
    Both ends are located by ``searchsorted`` on the sorted 1-minute close epochs — never by bar
    index or bar count.

    The window start is anchored to ``close - period_s`` (the bar's own boundary), **not** to the
    previous *kept* domain bar's close: ``domain_close_epoch`` is non-contiguous (``build_domain_bars``
    drops coverage/fence windows, and markets have session gaps), so anchoring to ``[k-1]`` would
    absorb 1-minute bars from dropped/gap windows whose prices lie outside this bar's ``[Low, High]``
    — corrupting intrabar fills (CF-MR-001 Phase-021 fill-engine fix).

    Parameters
    ----------
    domain_close_epoch : np.ndarray
        Domain-bar close epochs (seconds, int64), strictly increasing, length ``n_domain``.
    minute_close_epoch : np.ndarray
        1-minute close epochs (seconds, int64), strictly increasing.
    period_s : int
        Domain period in seconds (e.g. ``15*60``); defines each bar's resample window width.

    Returns
    -------
    (starts, ends) : (np.ndarray[int64], np.ndarray[int64])
        Half-open ``[start, end)`` 1-minute index ranges per domain bar (length ``n_domain``).
    """
    dce = np.asarray(domain_close_epoch, dtype=np.int64)
    mce = np.asarray(minute_close_epoch, dtype=np.int64)
    ends = np.searchsorted(mce, dce, side="right").astype(np.int64)
    starts = np.searchsorted(mce, dce - np.int64(period_s), side="right").astype(np.int64)
    return starts, ends


# --------------------------------------------------------------------------- #
# Pure computation — the causal intrabar resolution (genuinely sequential per event)
# --------------------------------------------------------------------------- #
def resolve_exit_paths(
    minute_high: np.ndarray,
    minute_low: np.ndarray,
    minute_open: np.ndarray,
    minute_close_epoch: np.ndarray,
    domain_close_epoch: np.ndarray,
    domain_close_price: np.ndarray,
    entry_idx: np.ndarray,
    direction: np.ndarray,
    adv_level: np.ndarray,
    cap: np.ndarray,
    fav_level: np.ndarray,
    fav_close_fire: np.ndarray,
    train_edge_epoch: int,
    period_s: int,
) -> ExitResolution:
    """Resolve each event's exit via the causal 1-minute intrabar walk (adverse-first tie-break).

    For event ``j`` the walk runs domain bars ``entry_idx[j] + 1 .. entry_idx[j] + cap[j]``
    (clipped at the last domain bar = the TRAIN edge). Within each domain bar its constituent
    1-minute bars (mapped by timestamp via :func:`minute_bounds_for_domain`) are walked forward;
    a 1-minute bar resolves the event when:

    * **adverse** — ``low <= adv_level`` (long) / ``high >= adv_level`` (short); **or**
    * **favourable intrabar** — ``high >= fav_level[j, off]`` (long) / ``low <= fav_level[j, off]``
      (short), when ``fav_level`` is finite for that offset.

    If both lie in the same 1-minute bar the **conservative adverse-first** rule resolves it as
    adverse (``tie_break = True``). If no intrabar touch occurs in a domain bar, a **domain-close
    favourable condition** (``fav_close_fire[j, off]``) exits at that bar's close. At the cap with
    no exit, the event exits on the cap bar's close (``KIND_CAP``).

    This is a genuinely **sequential, causal** algorithm (an event's resolution depends on the
    ordered walk of its post-entry bars), so it is an explicit bounded loop — bounded by ``cap``
    (``<= MR_CAP_MAX``) and the per-domain-bar 1-minute count. No future bar past the exit, and no
    1-minute bar past ``train_edge_epoch``, is consulted.

    Parameters
    ----------
    minute_high, minute_low : np.ndarray
        Real 1-minute high/low (float64), aligned to ``minute_close_epoch``.
    minute_open : np.ndarray
        Real 1-minute open (float64), aligned to ``minute_close_epoch``. Used as the fill price when
        a stop/limit **gaps** beyond the bar (level outside ``[Low, High]``): the order fills at the
        bar's first traded price, which lies in ``[Low, High]`` (the gap-through fill convention).
    minute_close_epoch : np.ndarray
        1-minute close epochs (seconds, int64), strictly increasing.
    domain_close_epoch, domain_close_price : np.ndarray
        Domain-bar close epochs (int64) and close prices (float64), length ``n_domain``.
    entry_idx, direction, adv_level, cap : np.ndarray
        Per-event domain-bar entry index (int64), direction (+1/-1), adverse stop level (float64),
        and max-hold cap in domain bars (int64), length ``m``.
    fav_level : np.ndarray
        Per-event per-offset favourable intrabar limit price, shape ``(m, max_off)``; ``NaN`` where
        the arm has no intrabar favourable target at that offset (offset ``k`` = domain bar
        ``entry_idx + k``, ``k`` in ``1..max_off``; index ``k-1`` along axis 1).
    fav_close_fire : np.ndarray
        Per-event per-offset boolean domain-close favourable exit, shape ``(m, max_off)``.
    train_edge_epoch : int
        Last TRAIN 1-minute close epoch; no 1-minute bar past it is consulted (holdout fence).
    period_s : int
        Domain period in seconds; defines each domain bar's 1-minute resample window (see
        :func:`minute_bounds_for_domain`).

    Returns
    -------
    ExitResolution
        Per-event resolved exit path; see the dataclass.
    """
    m = int(entry_idx.shape[0])
    n_domain = int(domain_close_price.shape[0])
    starts, ends = minute_bounds_for_domain(domain_close_epoch, minute_close_epoch, period_s)
    edge = int(train_edge_epoch)

    kind = np.full(m, KIND_UNRESOLVED, dtype=np.int64)
    fill_price = np.full(m, np.nan, dtype=np.float64)
    exit_didx = np.full(m, -1, dtype=np.int64)
    tie_break = np.zeros(m, dtype=bool)
    n_fence_clipped = 0

    for j in range(m):
        ei = int(entry_idx[j])
        d = int(direction[j])
        adv = float(adv_level[j])
        last_off = min(int(cap[j]), n_domain - 1 - ei)   # clip at TRAIN edge (last domain bar)
        if last_off < 1:
            n_fence_clipped += 1
            continue
        resolved = False
        for off in range(1, last_off + 1):
            di = ei + off
            lo_i, hi_i = int(starts[di]), int(ends[di])
            fav = float(fav_level[j, off - 1])
            has_fav = math.isfinite(fav)        # scalar finite test; identical truth to np.isfinite
            for mi in range(lo_i, hi_i):
                if int(minute_close_epoch[mi]) > edge:        # holdout fence (defensive)
                    break
                mh, ml, mo = float(minute_high[mi]), float(minute_low[mi]), float(minute_open[mi])
                if d == LONG:
                    adv_hit = ml <= adv
                    fav_hit = has_fav and mh >= fav
                    # gap fill: a stop/limit gapped beyond this bar fills at the bar OPEN (a real,
                    # marketable price in [Low, High]); the level only when the bar traded through
                    # it. Honors the D2.5 "real touched price" rule at 1m gap granularity.
                    adv_fill = adv if mh >= adv else mo       # gap down through the long stop -> open
                    fav_fill = fav if ml <= fav else mo       # gap up through the long limit -> open
                else:
                    adv_hit = mh >= adv
                    fav_hit = has_fav and ml <= fav
                    adv_fill = adv if ml <= adv else mo        # gap up through the short stop -> open
                    fav_fill = fav if mh >= fav else mo        # gap down through the short limit -> open
                if adv_hit and fav_hit:                       # conservative: adverse first
                    kind[j], fill_price[j], exit_didx[j] = KIND_ADV, adv_fill, di
                    tie_break[j] = True
                    resolved = True
                    break
                if adv_hit:
                    kind[j], fill_price[j], exit_didx[j] = KIND_ADV, adv_fill, di
                    resolved = True
                    break
                if fav_hit:
                    kind[j], fill_price[j], exit_didx[j] = KIND_FAV, fav_fill, di
                    resolved = True
                    break
            if resolved:
                break
            if bool(fav_close_fire[j, off - 1]):              # domain-close favourable exit
                kind[j], fill_price[j], exit_didx[j] = KIND_FAV, float(domain_close_price[di]), di
                resolved = True
                break
            if off == last_off:                               # cap reached -> exit-on-close
                kind[j], fill_price[j], exit_didx[j] = KIND_CAP, float(domain_close_price[di]), di
                resolved = True
        # (resolved is always True here unless last_off<1, handled above)

    ttp = np.where(exit_didx >= 0, exit_didx - np.asarray(entry_idx, dtype=np.int64), -1)
    resolved_mask = kind != KIND_UNRESOLVED
    return ExitResolution(
        kind=kind, fill_price=fill_price, exit_domain_idx=exit_didx, ttp_bars=ttp.astype(np.int64),
        tie_break=tie_break, resolved=resolved_mask, n_fence_clipped=n_fence_clipped)


def net_return_atr(
    fill_price: np.ndarray, entry_close: np.ndarray, direction: np.ndarray, atr_entry: np.ndarray,
) -> np.ndarray:
    """Direction-signed realized per-event return in ATR units (real prices; gross — no cost).

    ``r = direction · (fill_price - entry_close) / atr_entry``. ``NaN`` where the fill or ATR is
    undefined or the ATR is non-positive (never ``0/0``). This is the gross return-shape input to
    the EXP-090 estimator calibration; **cost and strategy expectancy are out of scope here**
    (EXP-091+).
    """
    fp = np.asarray(fill_price, dtype=np.float64)
    ec = np.asarray(entry_close, dtype=np.float64)
    d = np.asarray(direction, dtype=np.float64)
    a = np.asarray(atr_entry, dtype=np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        r = d * (fp - ec) / a
    bad = ~np.isfinite(fp) | ~np.isfinite(a) | (a <= 0.0)
    return np.where(bad, np.nan, r)
