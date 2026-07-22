"""ATR-based ZigZag trend/move substrate on real bars (streaming, causal).

A trend-direction and move-boundary substrate with no chart-type or HA
dependency, used by the ``CF-HA-HARAMI-001`` family (Phase 014). It is the
fixed first-branch trend substrate frozen at the Phase 014 D0 (P1):

- ATR estimator: **Wilder**, ``atr_period = 14``.
- ``ATR_MULT = 1.0``.
- Warmup: no pivot/threshold until ATR is defined (>= ``atr_period`` completed
  bars); pre-warmup bars carry no trend state.
- Seeding (first ATR-defined bar): bullish bar (``Close > Open``) -> trend
  Bullish, pivot ``High``; otherwise -> trend Bearish, pivot ``Low``.
- Tracking: maintain the running extreme (``High`` in a bullish trend, ``Low``
  in a bearish trend) and the threshold ``pivot -/+ ATR_MULT * ATR``. A
  trend-change confirmation fires at the first completed bar whose ``Close``
  closes beyond the threshold adversely to the current trend. Confirmed moves
  alternate direction.

**Causality (binding).** ATR at bar *N* uses only bars <= *N*. The running
extreme is updated only on non-confirming completed bars; the confirmation bar
never improves the extreme it confirms, so every ``ConfirmTime`` is strictly
later than the ``EndTime`` (pivot time) of the move it closes. The retroactively
located pivot labels the boundaries of an *already completed* move only; it is
never used as a point-in-time signal. The generator is deterministic and
streaming-compatible: identical input plus identical parameters yields identical
output.

Computed on real (non-HA) bars. ``ATR_MULT`` sensitivity is the registered
``CF-HA-HARAMI-001/ATRMULT`` branch, not an in-place change here.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl


ZIGZAG_COLUMNS = [
    "StartTime",
    "EndTime",
    "ConfirmTime",
    "Direction",
    "StartPrice",
    "EndPrice",
    "ConfirmClose",
    "ATRAtConfirm",
    "ThresholdAtConfirm",
]


def wilder_atr(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    atr_period: int,
) -> np.ndarray:
    """Compute the causal Wilder ATR series.

    ``ATR`` is undefined (``NaN``) before index ``atr_period - 1``; it is seeded
    as the simple mean of the first ``atr_period`` true ranges and thereafter
    updated by Wilder smoothing ``ATR_t = (ATR_{t-1} * (n - 1) + TR_t) / n``.
    ``TR_t`` uses only the current bar and the prior close, so ``ATR_t`` depends
    only on bars ``<= t`` (no look-ahead).

    Parameters
    ----------
    high, low, close : np.ndarray
        Real-bar OHLC component arrays (float64), chronologically ordered.
    atr_period : int
        Wilder ATR period (>= 1).

    Returns
    -------
    np.ndarray
        ATR series, ``NaN`` for indices ``< atr_period - 1``.
    """
    n = high.shape[0]
    atr = np.full(n, np.nan, dtype=np.float64)
    if n == 0 or atr_period < 1:
        return atr
    tr = np.empty(n, dtype=np.float64)
    tr[0] = high[0] - low[0]
    if n > 1:
        prev_close = close[:-1]
        tr[1:] = np.maximum.reduce([
            high[1:] - low[1:],
            np.abs(high[1:] - prev_close),
            np.abs(low[1:] - prev_close),
        ])
    if n < atr_period:
        return atr
    seed = float(np.mean(tr[:atr_period]))
    atr[atr_period - 1] = seed
    prev = seed
    for i in range(atr_period, n):
        prev = (prev * (atr_period - 1) + tr[i]) / atr_period
        atr[i] = prev
    return atr


def generate_zigzag(
    bars: pl.DataFrame,
    atr_period: int = 14,
    atr_mult: float = 1.0,
) -> pl.DataFrame:
    """Generate confirmed ZigZag moves from completed real bars.

    ``bars`` must contain ``CloseTime``, ``Open``, ``High``, ``Low``, ``Close``
    and be sorted by ``CloseTime`` (non-decreasing); the generator is sequential
    and does not reorder input. Unsorted input raises ``ValueError``.

    Parameters
    ----------
    bars : pl.DataFrame
        Real-bar OHLC frame (one domain, chronologically ordered).
    atr_period : int, default 14
        Wilder ATR period.
    atr_mult : float, default 1.0
        Threshold multiple of ATR for trend-change confirmation.

    Returns
    -------
    pl.DataFrame
        Confirmed moves with columns ``ZIGZAG_COLUMNS``. ``Direction`` is
        ``+1`` for an up-move (price rose to the ``EndPrice`` high) and ``-1``
        for a down-move. ``ConfirmTime`` is the bar that confirmed the move;
        ``EndTime`` is the (strictly earlier) pivot bar. Empty when no move is
        confirmed.
    """
    _validate_bars(bars)
    if atr_period < 1:
        raise ValueError("atr_period must be >= 1")
    if atr_mult <= 0:
        raise ValueError("atr_mult must be > 0")

    n = bars.height
    if n < atr_period:
        return _empty_frame()

    open_ = bars.get_column("Open").to_numpy().astype(np.float64)
    high = bars.get_column("High").to_numpy().astype(np.float64)
    low = bars.get_column("Low").to_numpy().astype(np.float64)
    close = bars.get_column("Close").to_numpy().astype(np.float64)
    close_time = bars.get_column("CloseTime").to_list()

    atr = wilder_atr(high, low, close, atr_period)
    seed = atr_period - 1  # first ATR-defined index

    moves = _walk_moves(
        open_, high, low, close, close_time, atr, seed, atr_mult
    )
    return _frame(moves)


# --------------------------------------------------------------------------- #
# Sequential core (causal; do not vectorize the confirmation logic)
# --------------------------------------------------------------------------- #
def _walk_moves(
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    close_time: list[Any],
    atr: np.ndarray,
    seed: int,
    atr_mult: float,
) -> list[dict[str, Any]]:
    """Run the explicit sequential ZigZag state machine. One pass, O(n)."""
    moves: list[dict[str, Any]] = []
    trend = 1 if close[seed] > open_[seed] else -1
    pivot_price = high[seed] if trend == 1 else low[seed]
    pivot_time = close_time[seed]
    start_price = pivot_price
    start_time = pivot_time

    for i in range(seed + 1, high.shape[0]):
        a = atr[i]
        if trend == 1:
            threshold = pivot_price - atr_mult * a
            if close[i] < threshold:
                moves.append(_move(1, start_price, start_time, pivot_price,
                                   pivot_time, close_time[i], close[i], a, threshold))
                trend = -1
                start_price, start_time = pivot_price, pivot_time
                pivot_price, pivot_time = low[i], close_time[i]
            elif high[i] > pivot_price:
                pivot_price, pivot_time = high[i], close_time[i]
        else:
            threshold = pivot_price + atr_mult * a
            if close[i] > threshold:
                moves.append(_move(-1, start_price, start_time, pivot_price,
                                   pivot_time, close_time[i], close[i], a, threshold))
                trend = 1
                start_price, start_time = pivot_price, pivot_time
                pivot_price, pivot_time = high[i], close_time[i]
            elif low[i] < pivot_price:
                pivot_price, pivot_time = low[i], close_time[i]
    return moves


def _move(
    direction: int,
    start_price: float,
    start_time: Any,
    end_price: float,
    end_time: Any,
    confirm_time: Any,
    confirm_close: float,
    atr_at_confirm: float,
    threshold_at_confirm: float,
) -> dict[str, Any]:
    """Build one confirmed-move record."""
    return {
        "StartTime": start_time,
        "EndTime": end_time,
        "ConfirmTime": confirm_time,
        "Direction": direction,
        "StartPrice": float(start_price),
        "EndPrice": float(end_price),
        "ConfirmClose": float(confirm_close),
        "ATRAtConfirm": float(atr_at_confirm),
        "ThresholdAtConfirm": float(threshold_at_confirm),
    }


# --------------------------------------------------------------------------- #
# Validation / framing
# --------------------------------------------------------------------------- #
def _validate_bars(bars: pl.DataFrame) -> None:
    required = {"CloseTime", "Open", "High", "Low", "Close"}
    missing = required.difference(bars.columns)
    if missing:
        raise ValueError(f"Missing required bar columns: {sorted(missing)}")
    if bars.height and not bars.get_column("CloseTime").is_sorted():
        raise ValueError(
            "bars must be sorted by CloseTime (non-decreasing) before generation; "
            "the generator is sequential and does not reorder input."
        )


def _empty_frame() -> pl.DataFrame:
    schema = {
        "StartTime": pl.Datetime,
        "EndTime": pl.Datetime,
        "ConfirmTime": pl.Datetime,
        "Direction": pl.Int32,
        "StartPrice": pl.Float64,
        "EndPrice": pl.Float64,
        "ConfirmClose": pl.Float64,
        "ATRAtConfirm": pl.Float64,
        "ThresholdAtConfirm": pl.Float64,
    }
    return pl.DataFrame({name: [] for name in ZIGZAG_COLUMNS}, schema=schema)


def _frame(moves: list[dict[str, Any]]) -> pl.DataFrame:
    if not moves:
        return _empty_frame()
    return pl.DataFrame(moves).select(ZIGZAG_COLUMNS).with_columns(
        pl.col("Direction").cast(pl.Int32)
    )
