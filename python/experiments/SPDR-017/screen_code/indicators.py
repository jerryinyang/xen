"""Causal indicators for SPDR-017: Parkinson, EWMA, ATR-ZigZag, SMA, ridge mag."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from config import (
    ATR_PERIOD,
    EWMA_LAMBDA,
    RIDGE_ALPHA,
    SMA_ANGLE_ATR_MULT,
    SMA_ANGLE_LOOKBACK,
    SMA_PERIOD,
    ZMAG_FLOOR_BPS,
    ZZ_MIN_TRAIN_SWINGS,
    ZZ_REVERSAL_ATR,
    ZVOL_EPS,
)


def parkinson(high: np.ndarray, low: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        ln_hl = np.log(high / low)
    out = np.sqrt(ln_hl ** 2 / (4.0 * np.log(2.0)))
    bad = ~np.isfinite(ln_hl) | (high <= 0) | (low <= 0) | (high < low)
    return np.where(bad, np.nan, out)


def ewma_park(park: np.ndarray, lam: float = EWMA_LAMBDA) -> np.ndarray:
    n = park.size
    out = np.full(n, np.nan)
    prev = np.nan
    for i in range(n):
        p = park[i]
        if not np.isfinite(p):
            out[i] = prev
            continue
        prev = p if not np.isfinite(prev) else lam * prev + (1.0 - lam) * p
        out[i] = prev
    return out


def abs_oo_bps(open_: np.ndarray) -> np.ndarray:
    n = open_.size
    out = np.full(n, np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        out[:-1] = 1e4 * np.abs(open_[1:] / open_[:-1] - 1.0)
    return out


def signed_oo_bps(open_: np.ndarray) -> np.ndarray:
    """Open-to-open signed move in bps over bar j: 1e4*(O_{j+1}/O_j - 1) at index j."""
    n = open_.size
    out = np.full(n, np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        out[:-1] = 1e4 * (open_[1:] / open_[:-1] - 1.0)
    return out


def freeze_zvol_scale(
    ewma: np.ndarray,
    abs_oo: np.ndarray,
    design_mask: np.ndarray,
    warmup_bars: int,
) -> float:
    idx = np.where(design_mask & np.isfinite(ewma) & np.isfinite(abs_oo) & (ewma > 0))[0]
    if idx.size == 0:
        return float("nan")
    take = idx[:warmup_bars]
    if take.size < max(10, warmup_bars // 3):
        return float("nan")
    ratio = abs_oo[take] / np.maximum(ewma[take], ZVOL_EPS)
    ratio = ratio[np.isfinite(ratio) & (ratio > 0)]
    if ratio.size < 5:
        return float("nan")
    return float(np.median(ratio))


def wilder_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray,
               period: int = ATR_PERIOD) -> np.ndarray:
    n = close.size
    atr = np.full(n, np.nan)
    if n < 2:
        return atr
    prev_close = np.empty(n)
    prev_close[0] = np.nan
    prev_close[1:] = close[:-1]
    tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))
    tr[0] = high[0] - low[0]
    if n <= period:
        return atr
    seed = float(np.mean(tr[1: period + 1]))
    atr[period] = seed
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def sma(close: np.ndarray, period: int = SMA_PERIOD) -> np.ndarray:
    n = close.size
    out = np.full(n, np.nan)
    if n < period:
        return out
    csum = np.cumsum(close)
    out[period - 1] = csum[period - 1] / period
    out[period:] = (csum[period:] - csum[: n - period]) / period
    return out


def sma_angle_on(sma_arr: np.ndarray, atr_lag: np.ndarray,
                 lookback: int = SMA_ANGLE_LOOKBACK,
                 thr: float = SMA_ANGLE_ATR_MULT) -> np.ndarray:
    n = sma_arr.size
    ok = np.zeros(n, dtype=float)
    if n <= lookback:
        return ok
    slope = np.full(n, np.nan)
    slope[lookback:] = np.abs(sma_arr[lookback:] - sma_arr[: n - lookback])
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = slope / atr_lag
    ok = np.where(np.isfinite(ratio) & (ratio >= thr), 1.0, 0.0)
    return ok


@dataclass
class Swing:
    start_idx: int
    end_idx: int
    confirm_idx: int
    start_price: float
    end_price: float
    direction: int
    magnitude_bps: float
    bars_in_swing: int
    angle_bps_per_bar: float
    path_noise_atr: float


def _swing_features(start_idx: int, end_idx: int, confirm_idx: int,
                    close: np.ndarray, atr: np.ndarray) -> Swing:
    start_price = float(close[start_idx])
    end_price = float(close[end_idx])
    direction = 1 if end_price >= start_price else -1
    magnitude_bps = abs(end_price - start_price) / start_price * 1e4
    bars = max(1, end_idx - start_idx)
    angle = magnitude_bps / bars
    seg = np.arange(start_idx, end_idx + 1)
    if end_idx > start_idx:
        bridge = start_price + (end_price - start_price) * (seg - start_idx) / (end_idx - start_idx)
    else:
        bridge = np.array([start_price])
    dev = np.abs(close[start_idx: end_idx + 1] - bridge)
    atr_seg = atr[start_idx: end_idx + 1]
    atr_scale = np.nanmean(atr_seg) if np.isfinite(atr_seg).any() else np.nan
    path_noise = (
        float(np.mean(dev) / atr_scale)
        if (atr_scale and np.isfinite(atr_scale) and atr_scale > 0)
        else float("nan")
    )
    return Swing(start_idx, end_idx, confirm_idx, start_price, end_price, direction,
                 magnitude_bps, bars, angle, path_noise)


def atr_zigzag(close: np.ndarray, atr: np.ndarray, start: int,
               reversal_atr: float = ZZ_REVERSAL_ATR) -> list[Swing]:
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


_FEATURES = ("magnitude_bps", "direction", "angle_bps_per_bar", "path_noise_atr", "bars_in_swing")


def _ridge_fit_predict(X_tr: np.ndarray, y_tr: np.ndarray, x_te: np.ndarray) -> float:
    mu = X_tr.mean(axis=0)
    sd = X_tr.std(axis=0)
    sd[sd == 0] = 1.0
    Xs = (X_tr - mu) / sd
    ym = y_tr.mean()
    yc = y_tr - ym
    p = Xs.shape[1]
    w = np.linalg.solve(Xs.T @ Xs + RIDGE_ALPHA * np.eye(p), Xs.T @ yc)
    xs = (x_te - mu) / sd
    return float(xs @ w + ym)


def zz_mag_forecast_series(n_bars: int, swings: list[Swing]) -> np.ndarray:
    pred = np.full(n_bars, np.nan)
    ns = len(swings)
    if ns < ZZ_MIN_TRAIN_SWINGS + 1:
        return pred
    X = np.array([[getattr(s, f) for f in _FEATURES] for s in swings], float)
    y = np.array([s.magnitude_bps for s in swings], float)
    for k in range(ZZ_MIN_TRAIN_SWINGS, ns):
        X_fit = X[:k]
        y_fit = y[1: k + 1]
        ok = np.isfinite(X_fit).all(axis=1) & np.isfinite(y_fit)
        if ok.sum() < ZZ_MIN_TRAIN_SWINGS // 2 or not np.isfinite(X[k]).all():
            continue
        pval = _ridge_fit_predict(X_fit[ok], y_fit[ok], X[k])
        if not np.isfinite(pval):
            continue
        start = swings[k].confirm_idx
        end = swings[k + 1].confirm_idx if k + 1 < ns else n_bars
        pred[start:end] = max(pval, ZMAG_FLOOR_BPS)
    return pred


def zz_next_leg_sign_series(n_bars: int, swings: list[Swing]) -> np.ndarray:
    """Constructive next-leg sign (SPDR-013): after confirm of swing k, signal = -direction_k."""
    sig = np.full(n_bars, np.nan)
    for k, sw in enumerate(swings):
        start = sw.confirm_idx
        end = swings[k + 1].confirm_idx if k + 1 < len(swings) else n_bars
        sig[start:end] = -float(sw.direction)
    return sig


def expanding_percentile(x: np.ndarray) -> np.ndarray:
    """Causal expanding percentile via sorted insertion (O(n log n))."""
    n = x.size
    out = np.full(n, np.nan)
    import bisect
    hist: list[float] = []
    for i in range(n):
        if not np.isfinite(x[i]):
            continue
        v = float(x[i])
        bisect.insort(hist, v)
        # rank of current among history (rightmost for ties ≈ proportion ≤ v)
        # after insert, position of last v
        pos = bisect.bisect_right(hist, v)
        out[i] = pos / len(hist)
    return out


def expanding_std(x: np.ndarray, min_n: int = 20) -> np.ndarray:
    n = x.size
    out = np.full(n, np.nan)
    s = 0.0
    s2 = 0.0
    cnt = 0
    for i in range(n):
        if np.isfinite(x[i]):
            s += x[i]
            s2 += x[i] * x[i]
            cnt += 1
        if cnt >= min_n:
            mu = s / cnt
            var = max(0.0, s2 / cnt - mu * mu)
            out[i] = np.sqrt(var)
    return out


def rolling_median_split(x: np.ndarray, window: int = 20) -> np.ndarray:
    n = x.size
    out = np.full(n, np.nan)
    for i in range(window - 1, n):
        w = x[i - window + 1: i + 1]
        w = w[np.isfinite(w)]
        if w.size < window // 2:
            continue
        med = np.median(w)
        out[i] = 1.0 if x[i] > med else 0.0
    return out
