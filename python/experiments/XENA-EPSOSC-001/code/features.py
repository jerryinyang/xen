"""EPSOSC feature defs — verbatim from SPDR-005 ``spdr005_screen.py`` (no retune).

Pins (SPDR-005 §5.3 / design §1):
  ATR_PERIOD = 14, ATR_SLOW = 56 (14×4)
  VOLARM_RATIO = 1.25 (fixed — no retune)
  RET_CLEAR_FRAC = 0.25  (re-cross below 0.25·k·ATR or anchor cross)
  rolling-median anchor over W bars (confirmed closes ≤ t)
  stretch_units = (close[t−1] − anchor[t−1]) / ATR(14)[t−1]
  VOLARM arm: ATR(14)[t−1] / ATR(56)[t−1] ≥ 1.25
  fade direction: stretch up → short (−1); stretch down → long (+1)

File origin: ``python/experiments/SPDR-005/screen_code/spdr005_screen.py``
  ``causal_rolling_median``, ``stretch_events``, ``simulate_episodes`` clear logic.
ATR uses ``xen.zigzag.wilder_atr`` (same as SPDR-005) for batch; streaming path uses
equivalent incremental Wilder seed + RMA.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import numpy as np

from xen.zigzag import wilder_atr

ATR_PERIOD = 14
ATR_SLOW = 14 * 4  # 56
VOLARM_RATIO = 1.25
RET_CLEAR_FRAC = 0.25
W_LEVELS = (96, 192)
K_LEVELS = (2.5, 3.0)


def causal_rolling_median(x: np.ndarray, window: int) -> np.ndarray:
    """Median of last ``window`` values ending at each index; NaN until full window.

    Verbatim SPDR-005 (pandas rolling median, min_periods=window).
    """
    import pandas as pd

    n = len(x)
    if n == 0 or window < 1:
        return np.full(n, np.nan)
    s = pd.Series(x)
    return s.rolling(window=window, min_periods=window).median().to_numpy(dtype=np.float64)


def wilder_atr_pair(
    high: np.ndarray, low: np.ndarray, close: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """ATR(14) and ATR(56) series (confirmed at bar close)."""
    return wilder_atr(high, low, close, ATR_PERIOD), wilder_atr(high, low, close, ATR_SLOW)


class _WilderAtrStream:
    """Incremental Wilder ATR matching ``xen.zigzag.wilder_atr`` seed + update."""

    def __init__(self, period: int) -> None:
        self.period = int(period)
        self._trs: list[float] = []
        self._prev_close: float | None = None
        self.value: float = float("nan")
        self.n = 0

    def update(self, high: float, low: float, close: float) -> float:
        if self._prev_close is None:
            tr = float(high) - float(low)
        else:
            pc = self._prev_close
            tr = max(
                float(high) - float(low),
                abs(float(high) - pc),
                abs(float(low) - pc),
            )
        self._prev_close = float(close)
        self.n += 1
        if self.n < self.period:
            self._trs.append(tr)
            self.value = float("nan")
            return self.value
        if self.n == self.period:
            self._trs.append(tr)
            self.value = float(sum(self._trs) / self.period)
            self._trs.clear()
            return self.value
        # Wilder: ATR_t = (ATR_{t-1} * (n-1) + TR_t) / n
        self.value = (self.value * (self.period - 1) + tr) / self.period
        return self.value


@dataclass
class StreamingLtfState:
    """Causal online ATR + rolling-median anchor + stretch/VOLARM event state.

    Call :meth:`update` once per completed LTF bar (confirmed ≤ t). Features exposed
    for the *next* bar open decision are the just-updated values (i.e. [t−1] relative
    to the next open).
    """

    w: int
    volarm: bool = True
    _anchor_buf: deque[float] = field(default_factory=deque)
    _atr14: _WilderAtrStream = field(default_factory=lambda: _WilderAtrStream(ATR_PERIOD))
    _atr56: _WilderAtrStream = field(default_factory=lambda: _WilderAtrStream(ATR_SLOW))
    # last confirmed features (for decision at next open)
    atr: float = float("nan")
    atr_slow: float = float("nan")
    anchor: float = float("nan")
    close: float = float("nan")
    close_ns: int = 0
    n_bars: int = 0

    def __post_init__(self) -> None:
        if self.w not in W_LEVELS:
            raise ValueError(f"W must be one of {W_LEVELS}, got {self.w}")
        self._anchor_buf = deque(maxlen=self.w)
        self._atr14 = _WilderAtrStream(ATR_PERIOD)
        self._atr56 = _WilderAtrStream(ATR_SLOW)

    def update(self, high: float, low: float, close: float, close_ns: int) -> None:
        """Ingest one confirmed LTF bar; refresh ATR / anchor / last close."""
        self.n_bars += 1
        self.close = float(close)
        self.close_ns = int(close_ns)
        self._anchor_buf.append(float(close))

        if len(self._anchor_buf) >= self.w:
            self.anchor = float(np.median(np.asarray(self._anchor_buf, dtype=np.float64)))
        else:
            self.anchor = float("nan")

        self.atr = float(self._atr14.update(high, low, close))
        self.atr_slow = float(self._atr56.update(high, low, close))

    @property
    def vol_ratio(self) -> float:
        a, s = self.atr, self.atr_slow
        if not (a == a and s == s and s > 0):
            return float("nan")
        return float(a / s)

    @property
    def armed(self) -> bool:
        if not self.volarm:
            return True
        vr = self.vol_ratio
        return bool(vr == vr and vr >= VOLARM_RATIO)

    def stretch_units(self) -> float:
        """(close − anchor) / ATR on last confirmed bar; NaN if not ready."""
        a, c, atr = self.anchor, self.close, self.atr
        if not (a == a and c == c and atr == atr and atr > 0):
            return float("nan")
        return float((c - a) / atr)

    def event_side(self, k: float) -> int:
        """Fade direction for entry at *next* open: +1 long / −1 short / 0 none.

        stretch ≥ +k → short fade; stretch ≤ −k → long fade. VOLARM requires arm.
        """
        su = self.stretch_units()
        if not (su == su) or not self.armed:
            return 0
        if su >= k:
            return -1
        if su <= -k:
            return 1
        return 0

    def clear_hit(self, side: int, k: float) -> bool:
        """RET_ANCHOR clear on last confirmed bar (for exit at next open).

        Cleared when |close−anchor|/ATR < 0.25·k OR price has crossed the anchor
        in the fade direction (long: close ≥ anchor; short: close ≤ anchor).
        """
        a, c, atr = self.anchor, self.close, self.atr
        if not (a == a and c == c and atr == atr and atr > 0):
            return False
        thr = RET_CLEAR_FRAC * float(k)
        dist = abs(c - a) / atr
        crossed = (side == 1 and c >= a) or (side == -1 and c <= a)
        return bool(dist < thr or crossed)


def batch_event_mask(
    close_prev: np.ndarray,
    atr_prev: np.ndarray,
    atr_slow_prev: np.ndarray,
    anchor_prev: np.ndarray,
    member: np.ndarray,
    k: float,
    *,
    volarm: bool,
) -> tuple[np.ndarray, np.ndarray]:
    """Vectorised stretch/VOLARM events (SPDR-005 ``stretch_events`` core).

    Inputs are already lagged to [t−1] for entry at bar t. Returns
    (event_mask, direction) length n.
    """
    n = len(close_prev)
    valid = (
        member.astype(bool)
        & np.isfinite(anchor_prev)
        & np.isfinite(close_prev)
        & np.isfinite(atr_prev)
        & (atr_prev > 0)
    )
    stretch_units = (close_prev - anchor_prev) / atr_prev
    up = valid & (stretch_units >= k)
    dn = valid & (stretch_units <= -k)
    if volarm:
        with np.errstate(divide="ignore", invalid="ignore"):
            vrat = atr_prev / atr_slow_prev
        arm = (
            np.isfinite(vrat)
            & (vrat >= VOLARM_RATIO)
            & np.isfinite(atr_slow_prev)
            & (atr_slow_prev > 0)
        )
        up &= arm
        dn &= arm
    direction = np.zeros(n, dtype=np.int8)
    direction[up] = -1
    direction[dn] = 1
    return direction != 0, direction
