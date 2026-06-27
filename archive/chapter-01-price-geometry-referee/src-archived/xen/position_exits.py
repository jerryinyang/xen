"""Position-management exit machinery for ``CF-HA-HARAMI-001`` (Phase 014-B, EXP-059).

The single new analysis module for the position-management surface read. It supplies
the two genuinely new computations the ``/EXIT-PARTIAL`` and ``/EXIT-TRAIL-STRUCT``
branches need, while the conditioned signal, the benchmark favourable level
(``fav = C + rd*0.5*M_sofar``), the benchmark 1:1 adverse level, the benchmark
adaptive time cap, the P15 path model, ATR normalisation, the median moving-block
bootstrap, and the paired/independent contrasts are reused from
:mod:`xen.expectancy` / :mod:`xen.favourable_targets` / :mod:`xen.third_barrier`:

1. **Causal monotone structure trailing-stop builder** (:func:`build_active_stops`)
   — from the **secondary** (``ATR_MULT_TRAIL = 0.5``) ZigZag's confirmed moves,
   the per-event active-stop **step function** over the forward window. For a long
   fade (``rd = +1``) the stop ratchets up to the most-recent confirmed secondary
   pivot **low** on each newly-confirmed secondary **pivot high** (up-move); mirror
   for a short fade. The stop is monotone (never loosens) and changes level only at
   a secondary confirmation bar (``ConfirmIdx <= i``) strictly after entry. The
   initial stop is the benchmark 1:1 level (``adv``) or ``NaN`` (no stop) until the
   first post-entry confirmation, per arm.
2. **Multi-leg P15 partial-exit / trailing resolver** (:func:`resolve_legs`) — a
   bounded, explicit, **sequential** forward scan over real OHLC that assigns each
   of up to 3 weighted legs its P15 exit given its favourable trigger (a price
   level, the first profitable close, or a precomputed reversal-event bar), a
   **shared** adverse exit (the fixed benchmark 1:1 stop *or* the trailing
   structure stop), and the benchmark time cap. When the shared adverse binds, all
   still-open legs close at that level/bar. **This loop is the object under test —
   never vectorize it.**
3. **Reversal-event locator** (:func:`reversal_event_targets`) — the per-event exit
   bar for a reversal-event leg: the earlier of the next primary-ZigZag move
   confirmed with ``Direction == rd`` after entry (reuses the
   :func:`xen.third_barrier.third_event_caps` forward-locator) and the next
   ``/STRONG``-conditioned HA harami whose own reversal direction is ``-rd``.
4. **Weighted realised return** (:func:`weighted_returns`) — the position-weighted
   per-event gross ATR-normalised return plus the exit-reason weight composition.

Real prices only in every metric. Heiken Ashi prices enter solely through the
upstream harami detector (locating the opposing-harami reversal bar); the leg then
exits at that real bar's close. No Heiken Ashi value ever enters a metric here.
"""
from __future__ import annotations

import numpy as np

from xen.third_barrier import third_event_caps

# --------------------------------------------------------------------------- #
# Frozen EXP-059 predeclared position-management constants (no tuning)
# --------------------------------------------------------------------------- #
ATR_MULT_TRAIL = 0.5            # P18: secondary trailing-ZigZag ATR multiple

# Leg favourable-trigger kinds (per-arm constant; never per-event).
LEG_LEVEL = 0                  # exit when a favourable price level is touched (P15)
LEG_FIRST_PROFIT = 1           # exit at the first bar whose real close is in profit
LEG_REVERSAL = 2               # exit at a precomputed reversal-event bar's close
LEG_NONE = 3                   # no favourable trigger (TRAIL-PURE: stop/cap only)

# Shared adverse mode.
ADV_FIXED = 0                  # benchmark 1:1 stop, constant level
ADV_TRAIL = 1                  # structure trailing stop (monotone step function)

# Per-leg exit-class codes (a superset of the FAV/ADV/TIMECAP/CENSORED scheme).
PX_DATA_CENSORED = -1
PX_TIMECAP = 0
PX_ADV = 1                     # shared fixed 1:1 adverse stop
PX_FAV = 2                     # favourable price-level leg
PX_FIRST_PROFIT = 3            # first-profitable-close leg
PX_REVERSAL = 4                # reversal-event leg
PX_TRAIL = 5                   # structure trailing-stop fill
PX_CLASS_LABELS: dict[int, str] = {
    PX_DATA_CENSORED: "DATA_CENSORED", PX_TIMECAP: "TIMECAP", PX_ADV: "ADV",
    PX_FAV: "FAV", PX_FIRST_PROFIT: "FIRST_PROFIT", PX_REVERSAL: "REVERSAL",
    PX_TRAIL: "TRAIL",
}


# --------------------------------------------------------------------------- #
# Pure computation — reversal-event locator (V1/V2C leg-3)
# --------------------------------------------------------------------------- #
def reversal_event_targets(
    entry_idx: np.ndarray,
    entry_epoch: np.ndarray,
    rd: np.ndarray,
    move_confirm_epoch: np.ndarray,
    move_confirm_idx: np.ndarray,
    move_direction: np.ndarray,
    bench_n_event: np.ndarray,
    bench_warmup: np.ndarray,
    cond_entry_idx: np.ndarray,
    cond_rd: np.ndarray,
) -> np.ndarray:
    """Per-event reversal-event exit-bar index (the take-profit completion signal).

    The reversal-event bar is the **earlier** of:

    - (i) the next **primary-ZigZag** move confirmed with ``Direction == rd`` and
      ``ConfirmTime > t_i`` — the fade-succeeded structural completion, located via
      :func:`xen.third_barrier.third_event_caps` (identical to EXP-058
      ``/THIRD-EVENT``); and
    - (ii) the next ``/STRONG``-conditioned HA harami (same conditioned stream)
      whose own reversal direction is ``-rd`` and whose entry bar is strictly after
      ``entry_idx`` — a harami fading the ``rd`` reversal move.

    A ``Direction == -rd`` ZigZag confirmation is the *adverse* event (the strong
    move resumed) and is **not** a take-profit trigger — it is handled by the 1:1 /
    trailing stop, never here.

    Returns ``reversal_idx`` (int64, length ``n``); ``-1`` where no reversal event
    is located (the leg then resolves at the benchmark time cap). The forward scan
    of the time-cap window in :func:`resolve_legs` bounds the leg regardless.
    """
    n = int(entry_idx.shape[0])
    out = np.full(n, -1, dtype=np.int64)
    if n == 0:
        return out
    zz = third_event_caps(entry_idx, entry_epoch, move_confirm_epoch,
                          move_confirm_idx, move_direction, rd,
                          bench_n_event, bench_warmup)
    zz_idx = np.where(zz["event_bound"], entry_idx + zz["n_event"], -1)
    # Opposing conditioned harami: next conditioned event (strictly later bar) with
    # rd == -rd_e. cond_entry_idx is ascending (entry-time order).
    for e in range(n):
        ha_idx = _next_opposing_harami(int(entry_idx[e]), int(rd[e]),
                                       cond_entry_idx, cond_rd)
        candidates = [c for c in (int(zz_idx[e]), ha_idx) if c > int(entry_idx[e])]
        if candidates:
            out[e] = min(candidates)
    return out


def _next_opposing_harami(
    entry_i: int, rd_e: int, cond_entry_idx: np.ndarray, cond_rd: np.ndarray,
) -> int:
    """Next conditioned-harami bar strictly after ``entry_i`` with ``rd == -rd_e``."""
    lo = int(np.searchsorted(cond_entry_idx, entry_i, side="right"))
    for j in range(lo, int(cond_entry_idx.shape[0])):
        if int(cond_rd[j]) == -rd_e:
            return int(cond_entry_idx[j])
    return -1


# --------------------------------------------------------------------------- #
# Pure computation — causal monotone structure trailing-stop builder
# --------------------------------------------------------------------------- #
def build_active_stops(
    entry_idx: np.ndarray,
    rd: np.ndarray,
    adv_level: np.ndarray,
    trail_init_none: bool,
    sec_confirm_idx: np.ndarray,
    sec_direction: np.ndarray,
    sec_end_price: np.ndarray,
    n_event: np.ndarray,
    last_train_idx: int,
) -> np.ndarray:
    """Per-event active trailing-stop step function over the forward window.

    Returns ``stops`` (float64, shape ``(n, width)`` with ``width = max(n_event)+1``):
    ``stops[e, off]`` is the active stop level at bar ``entry_idx[e] + off`` (for
    ``off`` in ``1..n_event[e]``), ``NaN`` where no stop is active. The stop is
    seeded at ``adv_level[e]`` (benchmark 1:1) unless ``trail_init_none`` (then
    ``NaN`` — no adverse exit until the first post-entry confirmation). On each
    secondary move confirmed strictly after entry whose ``Direction`` matches the
    trailing trigger (up-move for a long fade, down-move for a short fade), the stop
    ratchets to the **previous** secondary move's pivot ``EndPrice`` — monotone:
    ``max`` for a long, ``min`` for a short. The stop never loosens and only changes
    at a confirmation bar (``ConfirmIdx <= i``); pivots are located retroactively so
    the candidate price is from a fully-confirmed past move (causal).
    """
    n = int(entry_idx.shape[0])
    width = int(n_event.max()) + 1 if n and n_event.size else 1
    stops = np.full((n, width), np.nan, dtype=np.float64)
    n_sec = int(sec_confirm_idx.shape[0])
    for e in range(n):
        ei, rd_e = int(entry_idx[e]), int(rd[e])
        end = min(ei + int(n_event[e]), last_train_idx)
        stop = np.nan if trail_init_none else float(adv_level[e])
        ptr = int(np.searchsorted(sec_confirm_idx, ei, side="right"))  # first > entry
        for off in range(1, end - ei + 1):
            i = ei + off
            while ptr < n_sec and int(sec_confirm_idx[ptr]) <= i:
                if ptr >= 1 and int(sec_direction[ptr]) == rd_e:
                    cand = float(sec_end_price[ptr - 1])   # previous opposite pivot
                    if not np.isfinite(stop):
                        stop = cand
                    else:
                        stop = max(stop, cand) if rd_e == 1 else min(stop, cand)
                ptr += 1
            stops[e, off] = stop
    return stops


def trail_is_monotone(stops_row: np.ndarray, rd_e: int) -> bool:
    """True iff a per-event active-stop row never loosens (ignoring inactive NaN)."""
    active = stops_row[np.isfinite(stops_row)]
    if active.shape[0] <= 1:
        return True
    diffs = np.diff(active)
    return bool(np.all(diffs >= -1e-12)) if rd_e == 1 else bool(np.all(diffs <= 1e-12))


# --------------------------------------------------------------------------- #
# Pure computation — leg favourable price levels
# --------------------------------------------------------------------------- #
def leg_levels_from_fracs(
    entry_close: np.ndarray, rd: np.ndarray, fav_dist: np.ndarray,
    leg_fracs: tuple[float | None, ...],
) -> np.ndarray:
    """Per-event favourable price level per leg: ``C + rd*frac*fav_dist`` (``NaN`` if no frac).

    A ``frac`` of ``None`` marks a non-level leg (first-profit / reversal / none).
    """
    n = int(entry_close.shape[0])
    levels = np.full((n, len(leg_fracs)), np.nan, dtype=np.float64)
    for lg, frac in enumerate(leg_fracs):
        if frac is not None:
            levels[:, lg] = entry_close + rd * float(frac) * fav_dist
    return levels


# --------------------------------------------------------------------------- #
# Pure computation — multi-leg P15 resolver (bounded sequential; do not vectorize)
# --------------------------------------------------------------------------- #
def resolve_legs(
    open_: np.ndarray, high: np.ndarray, low: np.ndarray, close: np.ndarray,
    entry_idx: np.ndarray, entry_close: np.ndarray, rd: np.ndarray,
    leg_kinds: tuple[int, ...], leg_levels: np.ndarray, reversal_idx: np.ndarray,
    adv_level: np.ndarray, n_event: np.ndarray, population: np.ndarray,
    adv_mode: int, active_stops: np.ndarray | None, last_train_idx: int,
    exit_off: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Resolve every leg's P15 exit for every event under one arm's exit machinery.

    Scans ``[entry_idx+1, min(entry_idx+n_event, last_train_idx)]`` on real OHLC.
    Same-bar resolution follows the P15 path (bullish bar ``O->L->H->C``; bearish
    ``O->H->L->C``). When the **shared adverse** (fixed ``adv_level`` if
    ``adv_mode == ADV_FIXED`` else the trailing ``active_stops`` level) is reached
    on the adverse-side extreme **before** the favourable side along the path, every
    still-open leg closes at that level/bar (invariant: the shared stop binds all
    legs together). Otherwise touched favourable-level legs close at their levels;
    the first-profit and reversal-event legs close at the bar's real close. A
    still-open leg at the full cap exits ``TIMECAP``; a window truncated by the
    TRAIN edge before resolution leaves the leg ``DATA_CENSORED``.

    Returns ``(leg_exit_px, leg_exit_class)``, both shape ``(n, n_legs)``. When the
    optional ``exit_off`` array (int64, length ``n``) is supplied it is filled in
    place with the per-event resolving bar offset (``-1`` off-population) — the
    measured holding-duration input. The return value and every metric are
    unchanged whether or not it is supplied, so EXP-059's frozen results hold.
    """
    n, nl = int(entry_idx.shape[0]), len(leg_kinds)
    px = np.full((n, nl), np.nan, dtype=np.float64)
    cls = np.full((n, nl), PX_DATA_CENSORED, dtype=np.int64)
    adv_cls = PX_TRAIL if adv_mode == ADV_TRAIL else PX_ADV
    for e in range(n):
        if not population[e]:
            continue
        stops_e = active_stops[e] if active_stops is not None else None
        off = _scan_event(open_, high, low, close, int(entry_idx[e]), float(entry_close[e]),
                          int(rd[e]), leg_kinds, leg_levels[e], int(reversal_idx[e]),
                          float(adv_level[e]), stops_e, int(n_event[e]), last_train_idx,
                          adv_cls, px[e], cls[e])
        if exit_off is not None:
            exit_off[e] = off
    return px, cls


def _scan_event(
    open_: np.ndarray, high: np.ndarray, low: np.ndarray, close: np.ndarray,
    ei: int, C: float, rd_e: int, leg_kinds: tuple[int, ...], levels_e: np.ndarray,
    reversal_e: int, adv_fixed: float, stops_e: np.ndarray | None, n_ev: int,
    last_train_idx: int, adv_cls: int, px_e: np.ndarray, cls_e: np.ndarray,
) -> int:
    """Bounded sequential P15 scan of one event (writes ``px_e``/``cls_e`` in place).

    Explicit and stateful by contract — the causal/streaming semantics are the
    object under test (mirrors :func:`xen.expectancy.resolve_path_ordered`). Bound
    by ``n_ev`` (~6 bars in 96/99 cells); per-event cost is ``O(n_ev * n_legs)``.

    Returns the **resolving bar offset** ``exit_idx - ei`` (the bar at which the
    position fully closes / the shared stop binds / the cap or TRAIN edge is
    reached) — the measured holding-duration input. The return is additive: the
    legacy ``resolve_legs`` caller ignores it, so EXP-059's frozen results are
    unchanged.
    """
    nl = len(leg_kinds)
    open_mask = np.ones(nl, dtype=bool)
    cap_end = ei + n_ev
    end = min(cap_end, last_train_idx)
    for i in range(ei + 1, end + 1):
        s = adv_fixed if stops_e is None else float(stops_e[i - ei])
        stop_active = np.isfinite(s)
        bullish = close[i] >= open_[i]
        adverse_first = bullish if rd_e == 1 else (not bullish)
        adv_hit = stop_active and (low[i] <= s if rd_e == 1 else high[i] >= s)
        if adverse_first and adv_hit:                  # shared stop binds first
            _close_open(open_mask, px_e, cls_e, s, adv_cls)
            return i - ei
        for lg in range(nl):                           # favourable-side level legs
            if open_mask[lg] and leg_kinds[lg] == LEG_LEVEL and np.isfinite(levels_e[lg]):
                if (high[i] >= levels_e[lg]) if rd_e == 1 else (low[i] <= levels_e[lg]):
                    px_e[lg], cls_e[lg], open_mask[lg] = levels_e[lg], PX_FAV, False
        if (not adverse_first) and adv_hit:            # adverse extreme after fav
            _close_open(open_mask, px_e, cls_e, s, adv_cls)
            return i - ei
        for lg in range(nl):                           # close-based legs
            if not open_mask[lg]:
                continue
            if leg_kinds[lg] == LEG_FIRST_PROFIT and rd_e * (close[i] - C) > 0.0:
                px_e[lg], cls_e[lg], open_mask[lg] = close[i], PX_FIRST_PROFIT, False
            elif leg_kinds[lg] == LEG_REVERSAL and reversal_e >= 0 and i == reversal_e:
                px_e[lg], cls_e[lg], open_mask[lg] = close[i], PX_REVERSAL, False
        if not open_mask.any():
            return i - ei
    if end < cap_end:                                  # truncated by the TRAIN edge
        for lg in range(nl):
            if open_mask[lg]:
                px_e[lg], cls_e[lg] = np.nan, PX_DATA_CENSORED
        return end - ei
    for lg in range(nl):                               # full cap -> TIMECAP
        if open_mask[lg]:
            px_e[lg], cls_e[lg] = float(close[end]), PX_TIMECAP
    return end - ei


def _close_open(
    open_mask: np.ndarray, px_e: np.ndarray, cls_e: np.ndarray, level: float, cls: int,
) -> None:
    """Close every still-open leg at the shared stop level/class (invariant vi)."""
    for lg in range(int(open_mask.shape[0])):
        if open_mask[lg]:
            px_e[lg], cls_e[lg], open_mask[lg] = level, cls, False


# --------------------------------------------------------------------------- #
# Pure computation — UNCAPPED lazy trailing resolver (EXP-059B; do not vectorize)
# --------------------------------------------------------------------------- #
# EXP-059B `/EXIT-TRAIL-UNCAPPED`: the structure trailing stop as a standalone
# adverse-exit model — **no benchmark time-cap backstop and no initial stop**. The
# forward window runs to the TRAIN data edge; the only censoring is DATA_CENSORED.
# Added ALONGSIDE the capped machinery (resolve_legs/build_active_stops/_scan_event
# are unchanged — EXP-059's frozen results and the capped-sibling/BENCH reproduction
# depend on them). The trailing stop is computed LAZILY inside the scan (an advancing
# secondary-confirmation pointer), so no dense (n, width) stop array is materialised —
# uncapped, that array would be O(n_events * train_len).
def resolve_legs_uncapped(
    open_: np.ndarray, high: np.ndarray, low: np.ndarray, close: np.ndarray,
    entry_idx: np.ndarray, entry_close: np.ndarray, rd: np.ndarray,
    leg_kinds: tuple[int, ...], leg_levels: np.ndarray, reversal_idx: np.ndarray,
    sec_confirm_idx: np.ndarray, sec_direction: np.ndarray, sec_end_price: np.ndarray,
    population: np.ndarray, last_train_idx: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Resolve every leg's P15 exit under the uncapped structure-trailing model.

    Scans ``[entry_idx+1, last_train_idx]`` on real OHLC with **no** ``bench_n``
    window bound, terminating early when the trailing stop fills or all legs close.
    The shared adverse is the monotone structure trailing stop on the secondary
    ZigZag, computed lazily (identical ratchet to :func:`build_active_stops`): the
    stop is ``NaN`` (no adverse exit) until the first secondary move confirmed
    strictly after entry whose ``Direction == rd``, then ratchets to the previous
    opposite secondary pivot ``EndPrice`` (``max`` for a long, ``min`` for a short)
    and never loosens. When the stop binds on the adverse-side extreme along the P15
    path, every still-open leg closes at that level/bar (``PX_TRAIL``); favourable
    ``LEG_LEVEL`` legs close at their levels (``PX_FAV``). **No ``PX_TIMECAP`` is ever
    emitted** — any leg still open at ``last_train_idx`` is ``PX_DATA_CENSORED``.

    Returns ``(leg_exit_px, leg_exit_class, exit_offset)``; the first two are shape
    ``(n, n_legs)``; ``exit_offset`` (int64, length ``n``) is the position's resolving
    bar offset ``exit_idx − entry_idx`` (the last bar at which any leg closed, or
    ``last_train_idx − entry_idx`` when censored), ``-1`` for non-population events —
    the disclosed holding-duration input.
    """
    n, nl = int(entry_idx.shape[0]), len(leg_kinds)
    px = np.full((n, nl), np.nan, dtype=np.float64)
    cls = np.full((n, nl), PX_DATA_CENSORED, dtype=np.int64)
    exit_off = np.full(n, -1, dtype=np.int64)
    for e in range(n):
        if not population[e]:
            continue
        exit_off[e] = _scan_event_uncapped(
            open_, high, low, close, int(entry_idx[e]), float(entry_close[e]),
            int(rd[e]), leg_kinds, leg_levels[e], int(reversal_idx[e]),
            sec_confirm_idx, sec_direction, sec_end_price, last_train_idx, px[e], cls[e])
    return px, cls, exit_off


def _scan_event_uncapped(
    open_: np.ndarray, high: np.ndarray, low: np.ndarray, close: np.ndarray,
    ei: int, C: float, rd_e: int, leg_kinds: tuple[int, ...], levels_e: np.ndarray,
    reversal_e: int, sec_confirm_idx: np.ndarray, sec_direction: np.ndarray,
    sec_end_price: np.ndarray, last_train_idx: int, px_e: np.ndarray, cls_e: np.ndarray,
) -> int:
    """Bounded sequential P15 scan of one event under the uncapped trailing model.

    Explicit and stateful by contract — the causal/streaming semantics are the
    object under test (mirrors :func:`_scan_event` but without the time cap and with
    the trailing stop computed lazily). Per-event cost is ``O(last_train_idx − ei)``
    in the worst case (the position can hold to the TRAIN edge), not ``O(n_ev)``.
    Writes ``px_e``/``cls_e`` in place; returns the resolving bar offset.
    """
    nl = len(leg_kinds)
    open_mask = np.ones(nl, dtype=bool)
    n_sec = int(sec_confirm_idx.shape[0])
    stop = np.nan                                  # no initial stop (NaN until 1st confirm)
    ptr = int(np.searchsorted(sec_confirm_idx, ei, side="right"))  # first confirm > entry
    for i in range(ei + 1, last_train_idx + 1):
        while ptr < n_sec and int(sec_confirm_idx[ptr]) <= i:      # lazy ratchet (causal)
            if ptr >= 1 and int(sec_direction[ptr]) == rd_e:
                cand = float(sec_end_price[ptr - 1])   # previous opposite pivot
                if not np.isfinite(stop):
                    stop = cand
                else:
                    stop = max(stop, cand) if rd_e == 1 else min(stop, cand)
            ptr += 1
        stop_active = np.isfinite(stop)
        bullish = close[i] >= open_[i]
        adverse_first = bullish if rd_e == 1 else (not bullish)
        adv_hit = stop_active and (low[i] <= stop if rd_e == 1 else high[i] >= stop)
        if adverse_first and adv_hit:                  # trailing stop binds first
            _close_open(open_mask, px_e, cls_e, stop, PX_TRAIL)
            return i - ei
        for lg in range(nl):                           # favourable-side level legs
            if open_mask[lg] and leg_kinds[lg] == LEG_LEVEL and np.isfinite(levels_e[lg]):
                if (high[i] >= levels_e[lg]) if rd_e == 1 else (low[i] <= levels_e[lg]):
                    px_e[lg], cls_e[lg], open_mask[lg] = levels_e[lg], PX_FAV, False
        if (not adverse_first) and adv_hit:            # adverse extreme after fav
            _close_open(open_mask, px_e, cls_e, stop, PX_TRAIL)
            return i - ei
        for lg in range(nl):                           # close-based legs (inert for PURE/V2A)
            if not open_mask[lg]:
                continue
            if leg_kinds[lg] == LEG_FIRST_PROFIT and rd_e * (close[i] - C) > 0.0:
                px_e[lg], cls_e[lg], open_mask[lg] = close[i], PX_FIRST_PROFIT, False
            elif leg_kinds[lg] == LEG_REVERSAL and reversal_e >= 0 and i == reversal_e:
                px_e[lg], cls_e[lg], open_mask[lg] = close[i], PX_REVERSAL, False
        if not open_mask.any():
            return i - ei
    for lg in range(nl):                               # reached the TRAIN edge still open
        if open_mask[lg]:
            px_e[lg], cls_e[lg] = np.nan, PX_DATA_CENSORED
    return last_train_idx - ei


# --------------------------------------------------------------------------- #
# Pure computation — position-weighted realised return + exit-reason composition
# --------------------------------------------------------------------------- #
def weighted_returns(
    leg_exit_px: np.ndarray, leg_exit_class: np.ndarray, weights: np.ndarray,
    entry_close: np.ndarray, rd: np.ndarray, atr_entry: np.ndarray,
    population: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Position-weighted per-event gross ATR-normalised return + qualifying mask.

    ``R_event = sum_l w_l * rd*(exit_px_l - C)/ATR_entry`` over the legs. An event
    **qualifies** iff it is in ``population``, ``ATR_entry`` is finite and positive,
    and **every** leg reached a finite exit (no leg ``DATA_CENSORED``). Non-qualifying
    events carry ``NaN`` (excluded by the caller's mask). ``weights`` sums to 1.

    Returns ``(r_event, qualifying)`` (float64 / bool, length ``n``).
    """
    legged = rd[:, None] * (leg_exit_px - entry_close[:, None])
    with np.errstate(invalid="ignore", divide="ignore"):
        contrib = (legged * weights[None, :]).sum(axis=1) / atr_entry
    all_resolved = np.all(leg_exit_class != PX_DATA_CENSORED, axis=1) \
        & np.all(np.isfinite(leg_exit_px), axis=1)
    qualifying = (population & all_resolved & np.isfinite(atr_entry) & (atr_entry > 0.0))
    r_event = np.where(qualifying, contrib, np.nan)
    return r_event, qualifying


def exit_reason_weights(
    leg_exit_class: np.ndarray, weights: np.ndarray, qualifying: np.ndarray,
) -> dict[str, float]:
    """Fraction of position weight exiting via each class, pooled over qualifying events.

    Denominator is the total weight of qualifying events (``sum(qualifying) * 1.0``,
    since per-event leg weights sum to 1). Returns a label->fraction dict over the
    seven exit classes; empty (all 0) when no event qualifies.
    """
    out = {label: 0.0 for label in PX_CLASS_LABELS.values()}
    m = int(qualifying.sum())
    if m == 0:
        return out
    cls_q = leg_exit_class[qualifying]
    for code, label in PX_CLASS_LABELS.items():
        out[label] = float((weights[None, :] * (cls_q == code)).sum()) / m
    return out
