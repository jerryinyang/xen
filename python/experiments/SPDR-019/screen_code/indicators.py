"""Causal indicators — ATR20 (delta normaliser only) + Parkinson-EWMA ŝ (SPDR-014 identical)."""
from __future__ import annotations

import numpy as np

from config import ATR_PERIOD, EWMA_LAMBDA, SIGMA_WARMUP_BARS, ZVOL_EPS


def parkinson(high: np.ndarray, low: np.ndarray) -> np.ndarray:
    """Dimensionless Parkinson range vol per bar: sqrt(ln(H/L)^2 / (4 ln 2))."""
    with np.errstate(divide="ignore", invalid="ignore"):
        ln_hl = np.log(high / low)
    out = np.sqrt(ln_hl ** 2 / (4.0 * np.log(2.0)))
    bad = ~np.isfinite(ln_hl) | (high <= 0) | (low <= 0) | (high < low)
    return np.where(bad, np.nan, out)


def ewma_park(park: np.ndarray, lam: float = EWMA_LAMBDA) -> np.ndarray:
    """Causal EWMA of Parkinson: EWMA_t = λ·EWMA_{t-1} + (1-λ)·park_t."""
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
    """Open-to-open absolute move in bps over bar j at index j."""
    n = open_.size
    out = np.full(n, np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        out[:-1] = 1e4 * np.abs(open_[1:] / open_[:-1] - 1.0)
    return out


def freeze_zvol_scale(
    ewma: np.ndarray,
    abs_oo: np.ndarray,
    design_mask: np.ndarray,
    warmup_bars: int = SIGMA_WARMUP_BARS,
) -> float:
    """s_symbol = median(abs_oo / max(EWMA_park, ε)) on first warmup DESIGN origins."""
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


def wilder_atr(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = ATR_PERIOD
) -> np.ndarray:
    """Wilder ATR(period). Evaluated at bar i using bars ≤ i (causal at bar close)."""
    n = close.size
    atr = np.full(n, np.nan)
    if n < 2:
        return atr
    prev_close = np.empty(n)
    prev_close[0] = np.nan
    prev_close[1:] = close[:-1]
    tr = np.maximum(
        high - low,
        np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)),
    )
    tr[0] = high[0] - low[0]
    if n <= period:
        return atr
    seed = float(np.mean(tr[1: period + 1]))
    atr[period] = seed
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def expanding_decile_edges(x: np.ndarray, *, min_hist: int) -> tuple[np.ndarray, np.ndarray]:
    """Per-bar decile (1..10) of x_i vs history strictly before i; NaN if hist < min_hist.

    Decile d means x is in the d-th decile of the expanding history (d=10 = top).
    """
    n = x.size
    decile = np.full(n, np.nan)
    rank = np.full(n, np.nan)
    hist: list[float] = []
    for i in range(n):
        if len(hist) >= min_hist and np.isfinite(x[i]):
            arr = np.asarray(hist, dtype=float)
            # empirical rank in (0,1]: fraction of hist strictly < x, plus half ties
            less = float(np.mean(arr < x[i]))
            ties = float(np.mean(arr == x[i]))
            r = less + 0.5 * ties
            rank[i] = r
            # decile 1..10; r in [0,1] → ceil(r*10) with r=0 → 1, r=1 → 10
            d = int(np.ceil(max(r, 1e-15) * 10.0))
            decile[i] = float(min(10, max(1, d)))
        if np.isfinite(x[i]):
            hist.append(float(x[i]))
    return decile, rank


def train_median_finite(x: np.ndarray, mask: np.ndarray | None = None) -> float:
    v = x if mask is None else x[mask]
    v = v[np.isfinite(v)]
    if v.size == 0:
        return float("nan")
    return float(np.median(v))
