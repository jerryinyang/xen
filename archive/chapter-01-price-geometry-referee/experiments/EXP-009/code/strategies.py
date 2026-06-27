"""Experiment-local untuned strategy position generators for EXP-009.

Each function returns directional positions in ``{-1.0, 0.0, +1.0}`` aligned to
``t -> t+1`` real Close-to-Close returns (length ``len(close) - 1``), matching the
convention of the frozen ``xen.referee_calibration`` Donchian/MA generators. The
position at bar ``t`` uses only information available at or before ``t`` (no
look-ahead); warmup bars with insufficient history are flat (0). Parameters are
fixed, untuned defaults predeclared in ``scope.md``; nothing here is tuned.

Donchian(20) breakout and MA(20/50) crossover are NOT defined here — they are
reused unchanged from ``xen.referee_calibration``.
"""
from __future__ import annotations

import numpy as np

# Predeclared fixed parameters (scope "Strategy set"). Never tuned.
RSI_PERIOD = 14
RSI_LOW = 30.0
RSI_HIGH = 70.0
BOLLINGER_WINDOW = 20
BOLLINGER_NUM_STD = 2.0
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
ROC_PERIOD = 20

# Direction family per strategy, for distribution reporting.
STRATEGY_FAMILY: dict[str, str] = {
    "donchian_20": "trend",
    "ma_20_50": "trend",
    "rsi_14": "mean_reversion",
    "bollinger_20_2": "trend",
    "macd_12_26_9": "trend",
    "roc_20": "momentum",
}


def _ewm(values: np.ndarray, span: int) -> np.ndarray:
    """Recursive EMA seeded by the first value (causal, sequential).

    Parameters
    ----------
    values : np.ndarray
        Input series.
    span : int
        EMA span; smoothing factor ``alpha = 2 / (span + 1)``.

    Returns
    -------
    np.ndarray
        EMA series of the same length, seeded with ``values[0]``.
    """
    values = np.asarray(values, dtype=float)
    out = np.empty(len(values), dtype=float)
    if len(values) == 0:
        return out
    alpha = 2.0 / (span + 1.0)
    out[0] = values[0]
    # Genuinely sequential recursion; bounded by series length.
    for i in range(1, len(values)):
        out[i] = alpha * values[i] + (1.0 - alpha) * out[i - 1]
    return out


def _rolling_std_pop(values: np.ndarray, window: int) -> np.ndarray:
    """Trailing population std (ddof=0); leading ``window - 1`` entries are NaN.

    Vectorized via cumulative sums of ``x`` and ``x**2`` over the trailing window
    ending at each index — causally equivalent to an explicit trailing loop.
    """
    values = np.asarray(values, dtype=float)
    result = np.full(values.shape, np.nan, dtype=float)
    if len(values) < window:
        return result
    cs = np.cumsum(np.insert(values, 0, 0.0))
    cs2 = np.cumsum(np.insert(values * values, 0, 0.0))
    win_sum = cs[window:] - cs[:-window]
    win_sum2 = cs2[window:] - cs2[:-window]
    mean = win_sum / window
    var = np.maximum(win_sum2 / window - mean * mean, 0.0)
    result[window - 1 :] = np.sqrt(var)
    return result


def _rolling_mean(values: np.ndarray, window: int) -> np.ndarray:
    """Trailing simple moving average; leading ``window - 1`` entries are NaN."""
    values = np.asarray(values, dtype=float)
    result = np.full(values.shape, np.nan, dtype=float)
    if len(values) < window:
        return result
    cs = np.cumsum(np.insert(values, 0, 0.0))
    result[window - 1 :] = (cs[window:] - cs[:-window]) / window
    return result


def _align(positions: np.ndarray) -> np.ndarray:
    """Drop the last position so positions align to ``t -> t+1`` returns."""
    clean = np.nan_to_num(np.asarray(positions, dtype=float), nan=0.0)
    return clean[:-1] if len(clean) > 0 else clean


def rsi_positions(close: np.ndarray, *, period: int = RSI_PERIOD) -> np.ndarray:
    """Wilder RSI(period) mean-reversion positions aligned to next returns.

    +1 when ``RSI_t < RSI_LOW`` (oversold -> long), -1 when ``RSI_t > RSI_HIGH``
    (overbought -> short), else flat. RSI at bar ``t`` uses closes up to ``t``.
    """
    close = np.asarray(close, dtype=float)
    n = len(close)
    rsi = np.full(n, np.nan, dtype=float)
    if n >= period + 1:
        delta = np.diff(close)  # delta[i] is the change into bar i+1
        gain = np.where(delta > 0.0, delta, 0.0)
        loss = np.where(delta < 0.0, -delta, 0.0)
        avg_gain = float(np.mean(gain[:period]))
        avg_loss = float(np.mean(loss[:period]))
        # First defined RSI corresponds to bar index `period`.
        for i in range(period, n):
            if i > period:
                avg_gain = (avg_gain * (period - 1) + gain[i - 1]) / period
                avg_loss = (avg_loss * (period - 1) + loss[i - 1]) / period
            if avg_loss == 0.0:
                rsi[i] = 100.0 if avg_gain > 0.0 else 50.0
            else:
                rsi[i] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    positions = np.where(rsi < RSI_LOW, 1.0, np.where(rsi > RSI_HIGH, -1.0, 0.0))
    return _align(positions)


def bollinger_positions(
    close: np.ndarray, *, window: int = BOLLINGER_WINDOW, num_std: float = BOLLINGER_NUM_STD
) -> np.ndarray:
    """Bollinger(window, num_std) breakout positions aligned to next returns.

    Bands = trailing SMA +/- ``num_std`` * trailing population std of close, all
    from closes up to ``t``. +1 when ``close_t`` > upper band, -1 when below the
    lower band, else flat (trend/breakout convention).
    """
    close = np.asarray(close, dtype=float)
    sma = _rolling_mean(close, window)
    std = _rolling_std_pop(close, window)
    upper = sma + num_std * std
    lower = sma - num_std * std
    positions = np.where(close > upper, 1.0, np.where(close < lower, -1.0, 0.0))
    positions = np.where(np.isnan(upper), 0.0, positions)
    return _align(positions)


def macd_positions(
    close: np.ndarray,
    *,
    fast: int = MACD_FAST,
    slow: int = MACD_SLOW,
    signal: int = MACD_SIGNAL,
) -> np.ndarray:
    """MACD(fast, slow, signal) crossover positions aligned to next returns.

    ``MACD = EMA_fast(close) - EMA_slow(close)``, ``signal = EMA_signal(MACD)``,
    all causal EMAs seeded by the first value. +1 when ``MACD_t > signal_t``, -1
    when below, else flat (trend convention).
    """
    close = np.asarray(close, dtype=float)
    if len(close) == 0:
        return close[:-1] if len(close) > 0 else close
    macd = _ewm(close, fast) - _ewm(close, slow)
    signal_line = _ewm(macd, signal)
    positions = np.where(macd > signal_line, 1.0, np.where(macd < signal_line, -1.0, 0.0))
    return _align(positions)


def roc_positions(close: np.ndarray, *, period: int = ROC_PERIOD) -> np.ndarray:
    """ROC(period) momentum positions aligned to next returns.

    ``ROC_t = close_t / close_{t-period} - 1``; +1 when ``ROC_t > 0``, -1 when
    ``< 0``, else flat. Uses only past closes (momentum convention).
    """
    close = np.asarray(close, dtype=float)
    n = len(close)
    roc = np.full(n, np.nan, dtype=float)
    if n > period:
        prior = close[:-period]
        roc[period:] = np.where(prior != 0.0, close[period:] / prior - 1.0, np.nan)
    positions = np.where(roc > 0.0, 1.0, np.where(roc < 0.0, -1.0, 0.0))
    positions = np.where(np.isnan(roc), 0.0, positions)
    return _align(positions)
