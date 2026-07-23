"""Direction arms: D-SMA signal cells and the D-ZZ signed-policy signal (design §3.2 / §3.3).

Signals are per-bar sides ``s[t] in {-1,0,+1}`` decided on completed bar ``t``; the capture engine
actions them at ``open[t+1]``. Nothing here reads a bar > t.
"""
from __future__ import annotations

import numpy as np

from config import SMA_ANGLE_THRESHOLD_ATR, SMA_ANGLE_MODES, SMA_PERIODS
from indicators import Swing, sma, sma_angle_ok


def sma_signal(close: np.ndarray, atr_lag: np.ndarray, period: int, angle_mode: str
               ) -> np.ndarray:
    """D-SMA signal (§3.2): +1 if C_t>SMA_t, -1 if <, 0 if equal. Angle ON gates to flat when
    ``|SMA_t-SMA_{t-3}|/ATR[t-1] < 0.15``. ``atr_lag[t]`` must be ``atr[t-1]``."""
    m = sma(close, period)
    sig = np.zeros(close.size)
    sig[close > m] = 1.0
    sig[close < m] = -1.0
    sig[~np.isfinite(m)] = 0.0
    if angle_mode == "on":
        ok = sma_angle_ok(m, atr_lag, SMA_ANGLE_THRESHOLD_ATR)
        sig = np.where(ok, sig, 0.0)
    return sig


def sma_cells(close: np.ndarray, atr_lag: np.ndarray) -> dict[tuple[int, str], np.ndarray]:
    """All 12-per-clock … actually 6-per-clock D-SMA signal cells (3 periods x 2 angle modes)."""
    out: dict[tuple[int, str], np.ndarray] = {}
    for p in SMA_PERIODS:
        for mode in SMA_ANGLE_MODES:
            out[(p, mode)] = sma_signal(close, atr_lag, p, mode)
    return out


def zz_signal(n_bars: int, swings: list[Swing]) -> np.ndarray:
    """D-ZZ signed policy (§3.3): after a swing k confirms at bar c, expected next structural
    direction = ``-direction_k``; hold it until the next confirmation. Signal is 0 before the
    first confirmation. Causal: swing k's features are known at its confirmation bar c, and the
    engine enters at ``open[c+1]``."""
    sig = np.zeros(n_bars)
    for sw in swings:
        c = sw.confirm_idx
        if c < n_bars:
            sig[c:] = -sw.direction        # later swings overwrite the tail
    return sig
