"""Causal indicators: Wilder ATR(14), SMA, and ATR-ZigZag with line features.

All operate on COMPLETED clock bars of a single clock (design §3.1: never mix clocks). ATR is
used lagged — the caller takes ``atr[t-1]`` at a decision on bar ``t``. The ZigZag is a
deterministic streaming state machine (no look-ahead): a swing END pivot at index ``ext_idx`` is
only emitted at the later CONFIRMATION bar ``i`` (>= ext_idx), so every swing feature is known at
bar ``i`` and any policy entering on ``open[i+1]`` is causal.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from config import ATR_PERIOD, SMA_ANGLE_LOOKBACK, ZZ_REVERSAL_ATR


# ------------------------------------------------------------- ATR / SMA ----


def wilder_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = ATR_PERIOD
               ) -> np.ndarray:
    """Wilder ATR(``period``) on completed bars. ``atr[i]`` uses true ranges of bars <= i.

    ``atr[i]`` is NaN until ``period`` true ranges exist (bar 0 has no prior close). The seed is
    the simple mean of the first ``period`` true ranges; thereafter Wilder recursive smoothing
    ``atr[i] = (atr[i-1]*(period-1) + tr[i]) / period``.
    """
    n = close.size
    atr = np.full(n, np.nan)
    if n < 2:
        return atr
    prev_close = np.empty(n)
    prev_close[0] = np.nan
    prev_close[1:] = close[:-1]
    tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))
    tr[0] = high[0] - low[0]                       # no prior close for bar 0
    if n <= period:
        return atr
    seed = float(np.mean(tr[1 : period + 1]))       # bars 1..period (first with prev close)
    atr[period] = seed
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def sma(close: np.ndarray, period: int) -> np.ndarray:
    """Simple moving average of ``close`` over ``period`` completed bars. ``sma[i]`` uses
    ``close[i-period+1 .. i]``; NaN before ``period-1``."""
    n = close.size
    out = np.full(n, np.nan)
    if n < period:
        return out
    csum = np.cumsum(close)
    out[period - 1] = csum[period - 1] / period
    out[period:] = (csum[period:] - csum[: n - period]) / period
    return out


def sma_angle_ok(sma_arr: np.ndarray, atr_lag: np.ndarray, threshold: float,
                 lookback: int = SMA_ANGLE_LOOKBACK) -> np.ndarray:
    """Angle filter (design §3.2): ``|SMA_t - SMA_{t-lookback}| / ATR(14)[t-1] >= threshold``.

    ``atr_lag`` must already be the lagged ATR array (``atr[t-1]`` at index t). Returns a boolean
    array; False (and NaN-driven False) => flat.
    """
    n = sma_arr.size
    ok = np.zeros(n, dtype=bool)
    if n <= lookback:
        return ok
    slope = np.full(n, np.nan)
    slope[lookback:] = np.abs(sma_arr[lookback:] - sma_arr[: n - lookback])
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = slope / atr_lag
    ok = np.isfinite(ratio) & (ratio >= threshold)
    return ok


# ------------------------------------------------------------- ZigZag ----


@dataclass
class Swing:
    """One confirmed ATR-ZigZag swing (leg)."""

    start_idx: int          # index of the swing's start pivot
    end_idx: int            # index of the swing's end pivot (extreme)
    confirm_idx: int        # bar at which the reversal confirmed the swing (>= end_idx)
    start_price: float
    end_price: float
    direction: int          # +1 up-leg, -1 down-leg
    magnitude_bps: float    # |end-start|/start * 1e4
    bars_in_swing: int      # end_idx - start_idx
    angle_bps_per_bar: float
    path_noise_atr: float   # mean |close - linear bridge| over the swing, in ATR units


def _swing_features(start_idx: int, end_idx: int, confirm_idx: int,
                    close: np.ndarray, atr: np.ndarray) -> Swing:
    start_price = float(close[start_idx])
    end_price = float(close[end_idx])
    direction = 1 if end_price >= start_price else -1
    magnitude_bps = abs(end_price - start_price) / start_price * 1e4
    bars = max(1, end_idx - start_idx)
    angle = magnitude_bps / bars
    # path_noise: mean abs deviation of closes from the start->end linear bridge, in ATR units.
    # ATR scale = mean Wilder ATR(14) over the swing bars (path-local, causal <= confirm_idx).
    seg = np.arange(start_idx, end_idx + 1)
    if end_idx > start_idx:
        bridge = start_price + (end_price - start_price) * (seg - start_idx) / (end_idx - start_idx)
    else:
        bridge = np.array([start_price])
    dev = np.abs(close[start_idx : end_idx + 1] - bridge)
    atr_seg = atr[start_idx : end_idx + 1]
    atr_scale = np.nanmean(atr_seg) if np.isfinite(atr_seg).any() else np.nan
    path_noise = float(np.mean(dev) / atr_scale) if (atr_scale and np.isfinite(atr_scale)
                                                     and atr_scale > 0) else float("nan")
    return Swing(start_idx, end_idx, confirm_idx, start_price, end_price, direction,
                 magnitude_bps, bars, angle, path_noise)


def atr_zigzag(close: np.ndarray, atr: np.ndarray, start: int,
               reversal_atr: float = ZZ_REVERSAL_ATR) -> list[Swing]:
    """Deterministic ATR-ZigZag on completed bars (design §3.3).

    A swing END pivot is confirmed only when the close reverses from the running extreme by
    ``>= reversal_atr * ATR(14)[confirm bar]``. The confirmation bar carries the swing; the
    feature vector is known there. Streaming/causal: bar ``i`` uses only closes/ATR <= ``i``.

    Parameters
    ----------
    close, atr : np.ndarray
        Completed-bar closes and Wilder ATR(14) (``atr[i]`` uses bars <= i).
    start : int
        First bar with a valid (finite) ATR — the warm-up boundary.
    reversal_atr : float
        Threshold multiple (2.0 x ATR).

    Returns
    -------
    list[Swing]
        Confirmed swings in time order.
    """
    n = close.size
    swings: list[Swing] = []
    if n - start < 3:
        return swings
    direction = 1
    ext_idx = start
    ext_price = float(close[start])
    last_pivot_idx = start
    for i in range(start + 1, n):
        thr = reversal_atr * atr[i]
        if not np.isfinite(thr) or thr <= 0:
            continue
        if direction == 1:
            if close[i] >= ext_price:
                ext_price = float(close[i])
                ext_idx = i
            elif ext_price - close[i] >= thr:
                if ext_idx > last_pivot_idx:
                    swings.append(_swing_features(last_pivot_idx, ext_idx, i, close, atr))
                    last_pivot_idx = ext_idx
                direction = -1
                ext_price = float(close[i])
                ext_idx = i
        else:
            if close[i] <= ext_price:
                ext_price = float(close[i])
                ext_idx = i
            elif close[i] - ext_price >= thr:
                if ext_idx > last_pivot_idx:
                    swings.append(_swing_features(last_pivot_idx, ext_idx, i, close, atr))
                    last_pivot_idx = ext_idx
                direction = 1
                ext_price = float(close[i])
                ext_idx = i
    return swings
