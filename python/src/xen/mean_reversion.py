"""RSI-2 mean-reversion entry generator for CF-MR-001 (Phase 020).

The new entry-side lever for the mean-reversion family: a **fade** generator (buy
oversold, sell overbought) — the opposite of every prior continuation/pullback
family. All indicators are Wilder-smoothed on **real** domain ``Close`` and are
strictly causal (bar ``i`` uses only closes ``<= i``), so the entry signal at a
bar close is known at that close and the favourable excursion is measured from
``i + 1`` onward (no look-ahead).

Frozen constants (D1, never tuned in batch 1):

- Entry ``RSI(2)`` Wilder; **long iff ``RSI2 < 10``**, **short iff ``RSI2 > 90``**.
- ``CORE+TREND``  — long ``& Close > EMA20``, short ``& Close < EMA20``.
- ``CORE+FILTER`` — long ``& RSI5 > 50``, short ``& RSI5 < 50``.

Favourable direction is ``+1`` for long (upward excursion) and ``-1`` for short
(downward excursion); the consumer passes this direction to
``xen.capgeo_geometry.lifetime_path_geometry`` to read the entry-signed MFE.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# --------------------------------------------------------------------------- #
# Frozen constants (D1; never tuned)
# --------------------------------------------------------------------------- #
RSI_FAST_PERIOD: int = 2           # entry oscillator period
RSI_FILTER_PERIOD: int = 5         # /RSI-FILTER variant oscillator period
EMA_PERIOD: int = 20               # /TREND variant trend filter period
RSI_LONG_MAX: float = 10.0         # long iff RSI2 < 10 (oversold)
RSI_SHORT_MIN: float = 90.0        # short iff RSI2 > 90 (overbought)
RSI_FILTER_MID: float = 50.0       # /RSI-FILTER 50-cross

# Causal MR-tempo cap (D0-amendment-001; replaces the trend-length MA-segment cap).
RSI_MID: float = 50.0              # reversion "complete" = oscillator back to the neutral midline
MR_K_MULT: float = 1.0            # cap = K_MULT x median reversion-episode duration (one reversion)
MR_EPISODE_WINDOW: int = 20      # trailing completed-episode window for the median tempo
MR_MIN_EPISODES: int = 5         # < this many completed episodes before entry -> warmup (excluded)
MR_CAP_FLOOR: int = 3            # minimum cap (bars); a reversion needs a few bars to register
MR_CAP_MAX: int = 40             # loose guard; rarely binds (reversion-to-neutral is fast)

CORE = "CORE"
CORE_TREND = "CORE+TREND"
CORE_FILTER = "CORE+FILTER"
VARIANT_SUB_SCREENS = (CORE, CORE_TREND, CORE_FILTER)

LONG: int = 1
SHORT: int = -1


# --------------------------------------------------------------------------- #
# Output container
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MREntrySet:
    """One sub-screen's RSI-MR entry population for one (instrument, domain) cell.

    Attributes
    ----------
    sub_screen, instrument, domain : str
        Identity of the entry population.
    n_bars : int
        Domain-bar count of the fenced TRAIN slice.
    entry_idx : np.ndarray
        Int64 domain-bar indices of the entries (ascending), one per entry event.
    direction : np.ndarray
        Int64 entry-signed favourable direction per entry (``+1`` long / ``-1`` short),
        aligned to ``entry_idx``.
    """

    sub_screen: str
    instrument: str
    domain: str
    n_bars: int
    entry_idx: np.ndarray
    direction: np.ndarray


# --------------------------------------------------------------------------- #
# Pure computation — Wilder indicators (causal; bar i uses only closes <= i)
# --------------------------------------------------------------------------- #
def wilder_rsi(close: np.ndarray, period: int) -> np.ndarray:
    """Wilder's RSI over ``close`` with the given period (causal; NaN during warmup).

    Seeds the average gain/loss with the simple mean of the first ``period`` deltas,
    then applies Wilder smoothing ``avg = (avg*(p-1) + x) / p``. ``RSI = 0`` when the
    average gain is 0 and ``100`` when the average loss is 0 (never ``0/0``).

    Parameters
    ----------
    close : np.ndarray
        Real domain-bar close prices (float64), length ``n``.
    period : int
        Wilder smoothing period (``>= 1``).

    Returns
    -------
    np.ndarray
        RSI in ``[0, 100]``; the first ``period`` entries are ``NaN`` (warmup).
    """
    x = np.asarray(close, dtype=np.float64)
    n = x.shape[0]
    rsi = np.full(n, np.nan, dtype=np.float64)
    if n <= period:
        return rsi
    delta = np.diff(x)
    gain = np.where(delta > 0.0, delta, 0.0)
    loss = np.where(delta < 0.0, -delta, 0.0)
    avg_gain = float(np.mean(gain[:period]))
    avg_loss = float(np.mean(loss[:period]))
    rsi[period] = _rsi_value(avg_gain, avg_loss)
    for i in range(period + 1, n):
        avg_gain = (avg_gain * (period - 1) + gain[i - 1]) / period
        avg_loss = (avg_loss * (period - 1) + loss[i - 1]) / period
        rsi[i] = _rsi_value(avg_gain, avg_loss)
    return rsi


def _rsi_value(avg_gain: float, avg_loss: float) -> float:
    """RSI from Wilder average gain/loss with safe zero-baseline handling."""
    if avg_loss == 0.0:
        return 100.0 if avg_gain > 0.0 else 50.0
    if avg_gain == 0.0:
        return 0.0
    return 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)


def wilder_avg_gain_loss(close: np.ndarray, period: int) -> tuple[np.ndarray, np.ndarray]:
    """Causal Wilder average gain/loss arrays underlying :func:`wilder_rsi` (EXP-090 D2.1).

    Exposes the smoothed average gain ``AG`` and average loss ``AL`` series that
    :func:`wilder_rsi` consumes internally, so the EXIT-RCT reversion-completion target can be
    derived in closed form (``P* = Close + (AL - AG)`` long, for period ``n = 2``). Byte-identical
    seeding/recursion to :func:`wilder_rsi` (simple mean of the first ``period`` deltas, then
    ``avg = (avg*(p-1) + x)/p``); the first ``period`` entries are ``NaN`` (warmup). Strictly
    causal — bar ``i`` uses only closes ``<= i``.

    Parameters
    ----------
    close : np.ndarray
        Real domain-bar close prices (float64), length ``n``.
    period : int
        Wilder smoothing period (``>= 1``).

    Returns
    -------
    (avg_gain, avg_loss) : (np.ndarray, np.ndarray)
        Wilder average gain / average loss aligned to ``close``; first ``period`` entries ``NaN``.
    """
    x = np.asarray(close, dtype=np.float64)
    n = x.shape[0]
    ag = np.full(n, np.nan, dtype=np.float64)
    al = np.full(n, np.nan, dtype=np.float64)
    if n <= period:
        return ag, al
    delta = np.diff(x)
    gain = np.where(delta > 0.0, delta, 0.0)
    loss = np.where(delta < 0.0, -delta, 0.0)
    avg_gain = float(np.mean(gain[:period]))
    avg_loss = float(np.mean(loss[:period]))
    ag[period] = avg_gain
    al[period] = avg_loss
    for i in range(period + 1, n):
        avg_gain = (avg_gain * (period - 1) + gain[i - 1]) / period
        avg_loss = (avg_loss * (period - 1) + loss[i - 1]) / period
        ag[i] = avg_gain
        al[i] = avg_loss
    return ag, al


def reversion_completion_target(
    close: np.ndarray, period: int = RSI_FAST_PERIOD,
) -> np.ndarray:
    """EXIT-RCT trailing reversion-completion target price per bar (EXP-090 D2.1).

    The next-bar close that returns ``RSI(period)`` to the neutral midline 50 satisfies the
    closed form ``P*_t = Close_t + (period - 1)·(AL_t - AG_t)``. The offset ``(AL - AG)`` is
    **signed**: when oversold (``AL > AG``) it is positive so ``P* > Close`` (a long's favourable
    target above); when overbought (``AL < AG``) it is negative so ``P* < Close`` (a short's
    favourable target below) — one formula for both directions, matching the D2.1 long
    ``Close + (AL - AG)`` and short ``Close - (AG - AL)`` specs. The target is a causal transform
    of the Wilder state through bar ``t`` (no look-ahead); ``NaN`` during the RSI warmup. The
    consumer (the intrabar fill engine) uses the entry direction to decide the touch side
    (long fills when ``high >= P*``; short when ``low <= P*``).

    Parameters
    ----------
    close : np.ndarray
        Real domain-bar close prices (float64), length ``n``.
    period : int, default ``RSI_FAST_PERIOD`` (2)
        Wilder RSI period (the entry oscillator; frozen at 2).

    Returns
    -------
    np.ndarray
        Per-bar trailing target price (float64); ``NaN`` during warmup. The RSI implied by
        reaching ``P*_t`` equals 50 by construction (EXP-090 readiness invariant).
    """
    ag, al = wilder_avg_gain_loss(close, period)
    return np.asarray(close, dtype=np.float64) + float(period - 1) * (al - ag)


def wilder_ema(close: np.ndarray, period: int) -> np.ndarray:
    """Exponential moving average of ``close`` (causal; NaN during warmup).

    Seeds with the simple mean of the first ``period`` closes, then applies
    ``ema = alpha*close + (1-alpha)*ema_prev`` with ``alpha = 2/(period+1)``.

    Parameters
    ----------
    close : np.ndarray
        Real domain-bar close prices (float64), length ``n``.
    period : int
        EMA period (``>= 1``).

    Returns
    -------
    np.ndarray
        EMA aligned to ``close``; the first ``period - 1`` entries are ``NaN``.
    """
    x = np.asarray(close, dtype=np.float64)
    n = x.shape[0]
    ema = np.full(n, np.nan, dtype=np.float64)
    if n < period:
        return ema
    alpha = 2.0 / (period + 1.0)
    ema[period - 1] = float(np.mean(x[:period]))
    for i in range(period, n):
        ema[i] = alpha * x[i] + (1.0 - alpha) * ema[i - 1]
    return ema


# --------------------------------------------------------------------------- #
# Pure computation — RSI-MR entry populations (CORE + variant toggles)
# --------------------------------------------------------------------------- #
def _core_masks(rsi2: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Boolean long / short CORE masks from the entry oscillator (NaN-safe)."""
    defined = np.isfinite(rsi2)
    long_mask = defined & (rsi2 < RSI_LONG_MAX)
    short_mask = defined & (rsi2 > RSI_SHORT_MIN)
    return long_mask, short_mask


def mean_reversion_entries(
    close: np.ndarray, *, instrument: str, domain: str, n_bars: int,
) -> dict[str, MREntrySet]:
    """The three variant-axis RSI-MR entry populations for one cell.

    Builds ``CORE`` (bare RSI-2 fade), ``CORE+TREND`` (EMA20 trend agreement), and
    ``CORE+FILTER`` (RSI5 50-cross agreement). Each variant is a direction-preserving
    subset of CORE.

    Parameters
    ----------
    close : np.ndarray
        Real domain-bar close prices (float64), length ``n_bars``.
    instrument, domain : str
        Cell identity.
    n_bars : int
        Domain-bar count of the fenced TRAIN slice.

    Returns
    -------
    dict[str, MREntrySet]
        Keyed by sub-screen name (``CORE``, ``CORE+TREND``, ``CORE+FILTER``).
    """
    rsi2 = wilder_rsi(close, RSI_FAST_PERIOD)
    rsi5 = wilder_rsi(close, RSI_FILTER_PERIOD)
    ema20 = wilder_ema(close, EMA_PERIOD)
    long_mask, short_mask = _core_masks(rsi2)

    trend_long = long_mask & np.isfinite(ema20) & (close > ema20)
    trend_short = short_mask & np.isfinite(ema20) & (close < ema20)
    filt_long = long_mask & np.isfinite(rsi5) & (rsi5 > RSI_FILTER_MID)
    filt_short = short_mask & np.isfinite(rsi5) & (rsi5 < RSI_FILTER_MID)

    specs = {
        CORE: (long_mask, short_mask),
        CORE_TREND: (trend_long, trend_short),
        CORE_FILTER: (filt_long, filt_short),
    }
    out: dict[str, MREntrySet] = {}
    for name, (lmask, smask) in specs.items():
        out[name] = _entry_set_from_masks(lmask, smask, instrument, domain, n_bars, name)
    return out


def _entry_set_from_masks(long_mask: np.ndarray, short_mask: np.ndarray,
                          instrument: str, domain: str, n_bars: int, name: str) -> MREntrySet:
    """Assemble an ascending-index, direction-tagged MREntrySet from long/short masks."""
    long_idx = np.flatnonzero(long_mask)
    short_idx = np.flatnonzero(short_mask)
    idx = np.concatenate([long_idx, short_idx]).astype(np.int64)
    direction = np.concatenate([
        np.full(long_idx.shape[0], LONG, dtype=np.int64),
        np.full(short_idx.shape[0], SHORT, dtype=np.int64),
    ])
    order = np.argsort(idx, kind="stable")
    return MREntrySet(sub_screen=name, instrument=instrument, domain=domain, n_bars=n_bars,
                      entry_idx=idx[order], direction=direction[order])


# --------------------------------------------------------------------------- #
# Pure computation — causal MR-tempo cap (RSI-2 reversion-episode tempo)
# --------------------------------------------------------------------------- #
def reversion_episodes(rsi2: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Causal RSI-2 reversion episodes → (ascending close index, duration in bars).

    A long episode opens at the first bar with ``RSI₂ < RSI_LONG_MAX`` and closes at
    the first later bar with ``RSI₂ ≥ RSI_MID``; a short episode opens at
    ``RSI₂ > RSI_SHORT_MIN`` and closes at the first later bar with ``RSI₂ ≤ RSI_MID``.
    Duration = ``close_idx − open_idx`` (bars to revert to the neutral midline). A
    single state machine handles both sides; only **completed** episodes are returned
    (an open episode at the series end contributes nothing). Strictly causal — bar
    ``i`` uses only ``rsi2[≤ i]``. Warmup ``NaN`` RSI bars are skipped.

    Parameters
    ----------
    rsi2 : np.ndarray
        Causal Wilder ``RSI(2)`` series (float64), length ``n``.

    Returns
    -------
    (close_idx, durations) : (np.ndarray[int64], np.ndarray[int64])
        Ascending episode close indices and their bar durations.
    """
    x = np.asarray(rsi2, dtype=np.float64)
    n = x.shape[0]
    close_idx: list[int] = []
    durations: list[int] = []
    state = 0          # 0 flat / +1 in-long / -1 in-short
    open_i = -1
    for i in range(n):
        v = x[i]
        if not np.isfinite(v):
            continue
        if state == 0:
            if v < RSI_LONG_MAX:
                state, open_i = 1, i
            elif v > RSI_SHORT_MIN:
                state, open_i = -1, i
        elif state == 1:
            if v >= RSI_MID:
                close_idx.append(i)
                durations.append(i - open_i)
                state = 0
        else:
            if v <= RSI_MID:
                close_idx.append(i)
                durations.append(i - open_i)
                state = 0
    return (np.asarray(close_idx, dtype=np.int64), np.asarray(durations, dtype=np.int64))


def mr_tempo_caps(entry_idx: np.ndarray, close_idx: np.ndarray,
                  durations: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-entry causal MR-tempo cap (bars) + warmup mask from reversion-episode tempo.

    For entry ``i`` the cap is ``clip(round(MR_K_MULT · median(durations of the last
    MR_EPISODE_WINDOW episodes whose close index is strictly < i)), MR_CAP_FLOOR,
    MR_CAP_MAX)``. Fewer than ``MR_MIN_EPISODES`` completed episodes before ``i`` →
    **warmup** (cap 0, excluded by the caller). The cap-by-count table is precomputed
    once and mapped by ``searchsorted`` (no per-entry median loop), so the rule is
    applied identically to signal, control, and pool entries.

    Parameters
    ----------
    entry_idx : np.ndarray
        Int domain-bar indices of the entries.
    close_idx, durations : np.ndarray
        Ascending episode close indices and durations from :func:`reversion_episodes`.

    Returns
    -------
    (cap, warmup) : (np.ndarray[int64], np.ndarray[bool])
        Per-entry cap in bars (0 where warmup) and the warmup mask.
    """
    m = int(entry_idx.shape[0])
    cap = np.zeros(m, dtype=np.int64)
    warmup = np.ones(m, dtype=bool)
    n_ep = int(close_idx.shape[0])
    if m == 0 or n_ep == 0:
        return cap, warmup
    cap_by_count = np.zeros(n_ep + 1, dtype=np.int64)
    warm_by_count = np.ones(n_ep + 1, dtype=bool)
    for c in range(MR_MIN_EPISODES, n_ep + 1):
        w = durations[max(0, c - MR_EPISODE_WINDOW):c]
        val = int(round(MR_K_MULT * float(np.median(w))))
        cap_by_count[c] = int(min(max(val, MR_CAP_FLOOR), MR_CAP_MAX))
        warm_by_count[c] = False
    jc = np.searchsorted(close_idx, np.asarray(entry_idx, dtype=np.int64), side="left")
    return cap_by_count[jc], warm_by_count[jc]
