"""Live conditioned-signal expectancy kernels for ``CF-HA-HARAMI-001`` (Phase 014-B).

Reusable across the 014-B slate (EXP-053–EXP-060). This module supplies the
*causal* machinery that turns an entry timestamp (a harami, or any chosen bar)
on a confirmed move segmentation into a realised, ATR-normalised gross return
under the benchmark 3-barrier geometry with **path-ordered intrabar fills (P15)**:

1. **Live in-progress state** (`live_in_progress_state`) — at each entry bar
   ``t_i``, the last *confirmed* move with ``ConfirmTime <= t_i`` defines the
   in-progress (still-unconfirmed) move: ``StartPrice_inprogress = EndPrice_k``,
   in-progress trend ``= -Direction_k``, reversal trade direction
   ``rd = Direction_k``, and the current-price magnitude-so-far
   ``M_sofar = |C - StartPrice_inprogress|`` (``C`` = the entry bar's real close).
2. **Live ``/STRONG-STAT``** (`live_strong_stat`) — retain iff ``M_sofar`` clears
   the trailing-window magnitude percentile (binding p75; disclosed median+MAD).
   The single current-price test implements both family exclusions (before
   significance / after a retracement) because ``M_sofar`` retraces.
3. **Adaptive time cap** (`adaptive_time_caps_by_epoch`) — P4 cap from the
   durations of moves confirmed *strictly before* ``t_i`` (reuses the
   ``xen.capture_barriers.time_caps`` duration semantics, re-anchored to the
   entry timestamp).
4. **P15 path-ordered first-touch resolver** (`resolve_path_ordered`) — an
   explicit bounded sequential scan on **real OHLC** whose causal/streaming
   semantics are the object under test (never vectorized). Same-bar double-touch
   resolves along the fixed intrabar path (bullish ``O->L->H->C``; bearish
   ``O->H->L->C``).
5. **Realised gross return** (`realised_returns`) — ``rd*(exit - C)/ATR_entry``.
6. **Median moving-block bootstrap** (`bootstrap_median_distribution`,
   `median_ci`, `contrast_ci`) — mirrors the
   ``xen.capture_barriers.block_bootstrap_ci`` block construction exactly; only
   the statistic changes (``np.median`` of the resampled real-valued returns).

Real prices only in every metric. Heiken Ashi prices enter solely through the
upstream harami/impulse detectors, never here.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from xen.capture_barriers import (
    CLASS_ADV,
    CLASS_DATA_CENSORED,
    CLASS_FAV,
    CLASS_TIMECAP,
)

# --------------------------------------------------------------------------- #
# Frozen Phase 014-B / D0 constants (no tuning)
# --------------------------------------------------------------------------- #
STAT_WINDOW = 20            # P7: trailing confirmed-move window
STAT_MIN_WINDOW = 5         # P7: warmup floor (fewer prior moves -> NO_DECISION)
STAT_Q = 0.75               # P7: binding magnitude percentile
TIMECAP_K = 1.5             # P4: time-cap multiple
TIMECAP_WINDOW = 20         # P4: trailing confirmed-move window
TIMECAP_FLOOR = 6           # P4: minimum cap (bars)
TIMECAP_MIN_MOVES = 5       # P4: warmup -> fewer than this -> excluded
FAVOURABLE_FRACTION = 0.50  # P2: favourable distance = 0.5 * M_sofar
N_BOOT = 10_000             # P14: bootstrap resamples
BOOT_BATCH = 2_000          # bounded bootstrap memory batch


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class InProgressState:
    """Per-entry live in-progress-move state (causal; all fields length n)."""

    valid: np.ndarray        # bool: a confirmed move exists with ConfirmTime <= t_i
    k: np.ndarray            # int: index of that last confirmed move (-1 if none)
    rd: np.ndarray           # int: reversal trade direction = Direction_k
    start_price: np.ndarray  # float: EndPrice_k (in-progress move start pivot)
    start_epoch: np.ndarray  # int: EndTime_k epoch (in-progress move start time)
    m_sofar: np.ndarray      # float: |C - start_price| (current-price magnitude)


# --------------------------------------------------------------------------- #
# Pure computation — live in-progress state (causal as-of on ConfirmTime)
# --------------------------------------------------------------------------- #
def live_in_progress_state(
    entry_epoch: np.ndarray,
    entry_close: np.ndarray,
    move_confirm_epoch: np.ndarray,
    move_end_price: np.ndarray,
    move_end_epoch: np.ndarray,
    move_direction: np.ndarray,
) -> InProgressState:
    """Resolve the live in-progress move at each entry timestamp.

    For entry ``t_i`` the binding move ``k`` is the last confirmed move with
    ``ConfirmTime <= t_i`` (inclusive forward as-of search). The in-progress move
    then starts at that move's terminal pivot ``EndPrice_k`` / ``EndTime_k``, its
    (unconfirmed) trend is ``-Direction_k``, and the reversal trade direction is
    ``rd = Direction_k``. ``M_sofar = |C - EndPrice_k|`` uses only the known
    pivot and the entry bar's own real close ``C`` (no future bar, no running
    extreme).

    Parameters
    ----------
    entry_epoch : np.ndarray
        Entry-bar ``CloseTime`` epochs (int seconds), ascending.
    entry_close : np.ndarray
        Entry-bar real close prices ``C`` (float64), aligned to ``entry_epoch``.
    move_confirm_epoch, move_end_price, move_end_epoch, move_direction : np.ndarray
        Confirmed-move fields in confirmation order (``ConfirmTime`` ascending).

    Returns
    -------
    InProgressState
        Per-entry arrays; ``valid`` is ``False`` (and other fields are sentinel
        0) wherever no confirmed move precedes the entry.
    """
    n = int(entry_epoch.shape[0])
    k = np.searchsorted(move_confirm_epoch, entry_epoch, side="right") - 1
    valid = k >= 0
    if valid.any():                                   # causality guard (as-of)
        assert np.all(move_confirm_epoch[k[valid]] <= entry_epoch[valid]), \
            "live_in_progress_state: as-of selected a move confirmed after the entry"
    rd = np.zeros(n, dtype=np.int64)
    start_price = np.zeros(n, dtype=np.float64)
    start_epoch = np.zeros(n, dtype=np.int64)
    m_sofar = np.zeros(n, dtype=np.float64)
    kv = k[valid]
    rd[valid] = move_direction[kv].astype(np.int64)
    start_price[valid] = move_end_price[kv].astype(np.float64)
    start_epoch[valid] = move_end_epoch[kv].astype(np.int64)
    m_sofar[valid] = np.abs(entry_close[valid] - start_price[valid])
    return InProgressState(valid=valid, k=k, rd=rd, start_price=start_price,
                           start_epoch=start_epoch, m_sofar=m_sofar)


# --------------------------------------------------------------------------- #
# Pure computation — live /STRONG-STAT magnitude-percentile filter
# --------------------------------------------------------------------------- #
def live_strong_stat(
    k_inclusive: np.ndarray,
    m_sofar: np.ndarray,
    move_magnitudes: np.ndarray,
    window: int = STAT_WINDOW,
    min_window: int = STAT_MIN_WINDOW,
    q: float = STAT_Q,
) -> dict[str, np.ndarray]:
    """Live ``/STRONG-STAT`` retention per entry (binding p75; disclosed MAD).

    For entry with binding move index ``k`` (inclusive, from
    :func:`live_in_progress_state`), the trailing window is the magnitudes of the
    last ``min(window, k+1)`` confirmed moves with ``ConfirmTime <= t_i``. Fewer
    than ``min_window`` -> ``NO_DECISION`` (``defined = False``). Retention is
    inclusive: ``M_sofar >= threshold``. The p75 form is binding; ``median + MAD``
    is a disclosed sensitivity. Quantiles are linear (numpy type-7), matching
    ``xen.strong_move``.

    Returns
    -------
    dict[str, np.ndarray]
        ``defined``, ``retained_p75``, ``retained_mad`` (bool, length n);
        retained flags are ``False`` wherever ``defined`` is ``False``.
    """
    n = int(k_inclusive.shape[0])
    defined = np.zeros(n, dtype=bool)
    retained_p75 = np.zeros(n, dtype=bool)
    retained_mad = np.zeros(n, dtype=bool)
    for e in range(n):
        kk = int(k_inclusive[e])
        if kk < 0:
            continue
        lo = max(0, kk - window + 1)
        w = move_magnitudes[lo:kk + 1]            # last <=window moves, inclusive
        if w.shape[0] < min_window:
            continue
        defined[e] = True
        thr = float(np.quantile(w, q, method="linear"))
        med = float(np.median(w))
        mad = float(np.median(np.abs(w - med)))   # raw MAD (no 1.4826)
        retained_p75[e] = m_sofar[e] >= thr
        retained_mad[e] = m_sofar[e] >= (med + mad)
    return {"defined": defined, "retained_p75": retained_p75,
            "retained_mad": retained_mad}


# --------------------------------------------------------------------------- #
# Pure computation — adaptive P4 time cap anchored to the entry timestamp
# --------------------------------------------------------------------------- #
def adaptive_time_caps_by_epoch(
    entry_epoch: np.ndarray,
    move_confirm_epoch: np.ndarray,
    confirm_idx: np.ndarray,
    window: int = TIMECAP_WINDOW,
    k_mult: float = TIMECAP_K,
    floor: int = TIMECAP_FLOOR,
    min_moves: int = TIMECAP_MIN_MOVES,
) -> tuple[np.ndarray, np.ndarray]:
    """P4 adaptive cap per entry from durations of moves confirmed before ``t_i``.

    ``duration_bars`` of move ``j`` is ``confirm_idx[j] - confirm_idx[j-1]``
    (reusing the ``xen.capture_barriers.time_caps`` semantics). For an entry at
    ``t_i`` the trailing window is the durations of the (up to ``window``) moves
    whose ``ConfirmTime`` is *strictly* before ``t_i``. Fewer than ``min_moves``
    durations -> warmup (no cap, ``n_event = 0``), never silently capped.

    Returns
    -------
    (n_event, warmup) : (np.ndarray[int64], np.ndarray[bool])
        ``n_event`` is 0 wherever ``warmup`` is True.
    """
    durations = np.diff(confirm_idx)                  # durations[i] = move i+1
    n_moves = int(confirm_idx.shape[0])
    cap_by_j = np.zeros(n_moves, dtype=np.int64)
    warm_by_j = np.ones(n_moves, dtype=bool)
    for j in range(1, n_moves):                       # j = j_last (last move < t_i)
        lo = max(0, j - window)
        w = durations[lo:j]                           # durations of moves 1..j
        if w.shape[0] < min_moves:
            continue
        cap_by_j[j] = max(floor, int(round(k_mult * float(np.median(w)))))
        warm_by_j[j] = False
    j_last = np.searchsorted(move_confirm_epoch, entry_epoch, side="left") - 1
    n_event = np.zeros(int(entry_epoch.shape[0]), dtype=np.int64)
    warmup = np.ones(int(entry_epoch.shape[0]), dtype=bool)
    has = j_last >= 1
    n_event[has] = cap_by_j[j_last[has]]
    warmup[has] = warm_by_j[j_last[has]]
    return n_event, warmup


# --------------------------------------------------------------------------- #
# Pure computation — benchmark single-geometry barriers from M_sofar
# --------------------------------------------------------------------------- #
def benchmark_barriers(
    entry_close: np.ndarray, rd: np.ndarray, m_sofar: np.ndarray,
) -> dict[str, np.ndarray]:
    """Single benchmark favourable/adverse targets (G1 == G2 collapse).

    ``fav_dist = 0.5 * M_sofar``; ``fav = C + rd*fav_dist``;
    ``adv = C - rd*fav_dist`` (1:1). Real prices only.
    """
    fav_dist = FAVOURABLE_FRACTION * m_sofar
    return {"fav_dist": fav_dist,
            "fav": entry_close + rd * fav_dist,
            "adv": entry_close - rd * fav_dist}


# --------------------------------------------------------------------------- #
# Pure computation — P15 path-ordered first-touch resolver (causal loop)
# --------------------------------------------------------------------------- #
def resolve_path_ordered(
    open_: np.ndarray, high: np.ndarray, low: np.ndarray, close: np.ndarray,
    entry_idx: np.ndarray, fav_target: np.ndarray, adv_target: np.ndarray,
    rd: np.ndarray, n_event: np.ndarray, defined: np.ndarray, n_bars: int,
    exit_off: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """First-touch class + exit price per event under the P15 path model.

    Scans ``[entry_idx+1, min(entry_idx+N, n_bars-1)]`` on real OHLC. A same-bar
    double-touch resolves along the intrabar path: a bullish bar
    (``Close >= Open``) visits ``Low`` before ``High``; a bearish bar visits
    ``High`` before ``Low``. ``FAV``/``ADV`` exit at the target level (gaps fill
    at the level); ``TIMECAP`` exits at the cap bar's real close;
    ``DATA_CENSORED`` (window truncated by the data edge before the cap and
    before any touch) carries no exit price.

    This loop is intentionally explicit and bounded — its causal/streaming
    semantics are the object under test. Do not vectorize.

    When the optional ``exit_off`` array (int64, length ``n``) is supplied it is
    filled in place with the per-event resolving bar offset ``exit_idx -
    entry_idx`` (``-1`` off-population) — the measured holding-duration input. It
    is additive: classes/prices and every downstream metric are unchanged whether
    or not it is supplied, so the frozen EXP-049/053–059 results hold.
    """
    n = int(entry_idx.shape[0])
    classes = np.full(n, CLASS_DATA_CENSORED, dtype=np.int64)
    exit_price = np.full(n, np.nan, dtype=np.float64)
    for e in range(n):
        if not defined[e]:
            continue
        start = int(entry_idx[e]) + 1
        cap_end = int(entry_idx[e]) + int(n_event[e])
        end = min(cap_end, n_bars - 1)
        cls, px, hit_idx = _scan_path(open_, high, low, close, start, end,
                                      float(fav_target[e]), float(adv_target[e]), int(rd[e]))
        if cls in (CLASS_FAV, CLASS_ADV):
            classes[e], exit_price[e] = cls, px
            off = hit_idx - int(entry_idx[e])
        elif end < cap_end:                            # truncated by the data edge
            classes[e] = CLASS_DATA_CENSORED
            off = end - int(entry_idx[e])
        else:                                          # full cap, no touch
            classes[e], exit_price[e] = CLASS_TIMECAP, float(close[end])
            off = end - int(entry_idx[e])
        if exit_off is not None:
            exit_off[e] = off
    return classes, exit_price


def _scan_path(
    open_: np.ndarray, high: np.ndarray, low: np.ndarray, close: np.ndarray,
    start: int, end: int, fav_t: float, adv_t: float, rd: int,
) -> tuple[int, float, int]:
    """Bounded sequential P15 first-touch scan of one event window (causal).

    Returns ``(class, exit_price, hit_idx)``; ``hit_idx`` is the bar index of the
    FAV/ADV touch, or ``end`` when the scan exhausts the window with no touch (the
    TIMECAP/edge bar). The third element is additive — existing callers unpack the
    first two via :func:`resolve_path_ordered`.
    """
    for i in range(start, end + 1):
        if rd == 1:                                    # fav on the High side
            fav_hit, adv_hit = high[i] >= fav_t, low[i] <= adv_t
        else:                                          # fav on the Low side
            fav_hit, adv_hit = low[i] <= fav_t, high[i] >= adv_t
        if fav_hit and adv_hit:
            bullish = close[i] >= open_[i]             # bullish visits Low first
            low_side_first = bullish
            if rd == 1:
                # rd=+1: adv is Low side, fav is High side.
                return (CLASS_ADV, adv_t, i) if low_side_first else (CLASS_FAV, fav_t, i)
            # rd=-1: fav is Low side, adv is High side.
            return (CLASS_FAV, fav_t, i) if low_side_first else (CLASS_ADV, adv_t, i)
        if fav_hit:
            return CLASS_FAV, fav_t, i
        if adv_hit:
            return CLASS_ADV, adv_t, i
    return CLASS_TIMECAP, float("nan"), end


# --------------------------------------------------------------------------- #
# Pure computation — realised gross ATR-normalised return
# --------------------------------------------------------------------------- #
def realised_returns(
    classes: np.ndarray, exit_price: np.ndarray, entry_close: np.ndarray,
    rd: np.ndarray, atr_entry: np.ndarray,
) -> np.ndarray:
    """Realised gross return in ATR units: ``rd*(exit - C)/ATR_entry``.

    Defined for resolved/capped events (finite ``exit_price`` and a finite,
    positive ``atr_entry``); ``NaN`` elsewhere. The caller selects the
    qualifying population via :func:`qualifying_mask`.
    """
    with np.errstate(invalid="ignore", divide="ignore"):
        r = rd * (exit_price - entry_close) / atr_entry
    bad = ~np.isfinite(exit_price) | ~np.isfinite(atr_entry) | (atr_entry <= 0.0)
    r = np.where(bad, np.nan, r)
    return r


def qualifying_mask(
    classes: np.ndarray, exit_price: np.ndarray, atr_entry: np.ndarray,
) -> np.ndarray:
    """Boolean mask of the P14 denominator: built-barrier FAV/ADV/TIMECAP."""
    resolved = np.isin(classes, (CLASS_FAV, CLASS_ADV, CLASS_TIMECAP))
    return resolved & np.isfinite(exit_price) & np.isfinite(atr_entry) & (atr_entry > 0.0)


# --------------------------------------------------------------------------- #
# Pure computation — median moving-block bootstrap (block ctor == capture_barriers)
# --------------------------------------------------------------------------- #
def bootstrap_median_distribution(
    values: np.ndarray, rng: np.random.Generator,
    n_boot: int = N_BOOT, batch: int = BOOT_BATCH,
) -> tuple[np.ndarray, int]:
    """Moving-block bootstrap distribution of the **median** of ``values``.

    Events are taken in entry-time order. Block length ``b = max(1,
    round(m**(1/3)))``; ``ceil(m/b)`` contiguous blocks per resample (truncated
    to length ``m``) — identical block construction to
    ``xen.capture_barriers.block_bootstrap_ci``; only the statistic differs
    (``np.median`` of resampled real-valued returns). A median of ``m >= 1``
    values is always defined, so no degenerate-resample discard is needed.

    Returns ``(medians, block_len)``; ``medians`` has length ``n_boot`` (empty
    when ``values`` is empty).
    """
    m = int(values.shape[0])
    if m == 0:
        return np.empty(0, dtype=np.float64), 1
    b = max(1, int(round(m ** (1.0 / 3.0))))
    n_blocks = int(np.ceil(m / b))
    max_start = max(0, m - b)
    offsets = np.arange(b, dtype=np.int64)
    out = np.empty(n_boot, dtype=np.float64)
    done = 0
    while done < n_boot:
        k = min(batch, n_boot - done)
        starts = rng.integers(0, max_start + 1, size=(k, n_blocks))
        idx = (starts[:, :, None] + offsets[None, None, :]
               ).reshape(k, n_blocks * b)[:, :m]
        out[done:done + k] = np.median(values[idx], axis=1)
        done += k
    return out, b


def median_ci(dist: np.ndarray) -> tuple[float, float, float]:
    """One-sided 95% lower bound (5th pct) + two-sided (2.5/97.5) bounds."""
    if dist.shape[0] == 0:
        return float("nan"), float("nan"), float("nan")
    return (float(np.percentile(dist, 5.0)),
            float(np.percentile(dist, 2.5)),
            float(np.percentile(dist, 97.5)))


def contrast_ci(
    signal_dist: np.ndarray, baseline_dist: np.ndarray,
) -> tuple[float, float, float]:
    """Bootstrap CI of the median difference under independence.

    Distributions are combined elementwise (independent RNG streams — signal vs
    baseline; resample-index pairing is a Monte Carlo convenience, not statistical
    pairing of dependent samples). Returns the one-sided lower bound (5th pct) and
    two-sided bounds of ``signal* - baseline*``; ``NaN`` when either distribution
    is empty.
    """
    if signal_dist.shape[0] == 0 or baseline_dist.shape[0] == 0:
        return float("nan"), float("nan"), float("nan")
    delta = signal_dist - baseline_dist
    return (float(np.percentile(delta, 5.0)),
            float(np.percentile(delta, 2.5)),
            float(np.percentile(delta, 97.5)))
