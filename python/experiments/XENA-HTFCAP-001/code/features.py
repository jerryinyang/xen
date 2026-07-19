"""HTFCAP feature defs — verbatim from SPDR-006 ``spdr006_screen.py`` (no retune).

Pins (SPDR-006):
  ADX_PERIOD = ATR_PERIOD = 14
  VOL_MEDIAN_W = 100 HTF bars
  Wilder DI/ADX + causal rolling-median ATR vol_ratio
  map_htf_to_ltf: last HTF CloseTime STRICTLY < LTF OpenTime

File:line origin: ``python/experiments/SPDR-006/screen_code/spdr006_screen.py``
  ``_wilder_rma``, ``wilder_adx_di``, ``map_htf_to_ltf``, ``causal_rolling_median``.
ATR uses ``xen.zigzag.wilder_atr`` (same as SPDR-006).
"""
from __future__ import annotations

import numpy as np

from xen.zigzag import wilder_atr

ADX_PERIOD = 14
ATR_PERIOD = 14
VOL_MEDIAN_W = 100  # HTF bars for rolling-median ATR — frozen


def wilder_rma(x: np.ndarray, period: int) -> np.ndarray:
    """Causal Wilder RMA (SPDR-006 ``_wilder_rma``)."""
    n = len(x)
    out = np.full(n, np.nan)
    if n < period:
        return out
    seed = float(np.mean(x[:period]))
    out[period - 1] = seed
    prev = seed
    for i in range(period, n):
        prev = (prev * (period - 1) + x[i]) / period
        out[i] = prev
    return out


def wilder_adx_di(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = ADX_PERIOD
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Causal Wilder ADX, +DI, −DI. NaN during warmup. Verbatim SPDR-006."""
    n = len(high)
    plus_di = np.full(n, np.nan)
    minus_di = np.full(n, np.nan)
    adx = np.full(n, np.nan)
    if n < period + 1:
        return adx, plus_di, minus_di
    up = high[1:] - high[:-1]
    dn = low[:-1] - low[1:]
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    prev_close = close[:-1]
    tr = np.maximum.reduce(
        [high[1:] - low[1:], np.abs(high[1:] - prev_close), np.abs(low[1:] - prev_close)]
    )
    atr = wilder_rma(tr, period)
    pdm = wilder_rma(plus_dm, period)
    mdm = wilder_rma(minus_dm, period)
    with np.errstate(divide="ignore", invalid="ignore"):
        pdi = 100.0 * pdm / atr
        mdi = 100.0 * mdm / atr
        dx = 100.0 * np.abs(pdi - mdi) / (pdi + mdi)
    adx_core = wilder_rma(np.nan_to_num(dx, nan=0.0), period)
    plus_di[1:] = pdi
    minus_di[1:] = mdi
    adx[1:] = adx_core
    adx[: 2 * period] = np.nan
    return adx, plus_di, minus_di


def map_htf_to_ltf(ltf_open_ns: np.ndarray, htf_close_ns: np.ndarray) -> np.ndarray:
    """Index of last HTF bar with CloseTime STRICTLY < LTF OpenTime; −1 if none."""
    return np.searchsorted(htf_close_ns, ltf_open_ns, side="left") - 1


def causal_rolling_median(x: np.ndarray, window: int) -> np.ndarray:
    """Causal rolling median ending at each index; NaN until full window of finite values."""
    n = len(x)
    out = np.full(n, np.nan)
    if n == 0 or window < 1:
        return out
    for i in range(window - 1, n):
        chunk = x[i - window + 1 : i + 1]
        if np.all(np.isfinite(chunk)):
            out[i] = float(np.median(chunk))
    return out


def htf_features(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    *,
    adx_period: int = ADX_PERIOD,
    atr_period: int = ATR_PERIOD,
    vol_median_w: int = VOL_MEDIAN_W,
) -> dict[str, np.ndarray]:
    """HTF feature pack on confirmed bars: dir, adx, atr, vol_ratio.

    DI sign: +DI > −DI ⇒ +1, else −1; 0 when DI undefined.
    vol_ratio = ATR(period) / causal_rolling_median(ATR, W) on the same closed bar.
    """
    adx, pdi, mdi = wilder_adx_di(high, low, close, adx_period)
    htf_dir = np.where(pdi > mdi, 1, -1).astype(np.int8)
    htf_dir[~np.isfinite(pdi) | ~np.isfinite(mdi)] = 0
    atr = wilder_atr(high, low, close, atr_period)
    med_atr = causal_rolling_median(atr, vol_median_w)
    with np.errstate(divide="ignore", invalid="ignore"):
        vol_ratio = atr / med_atr
    vol_ratio[~np.isfinite(vol_ratio) | (med_atr <= 0)] = np.nan
    return {
        "adx": adx,
        "plus_di": pdi,
        "minus_di": mdi,
        "htf_dir": htf_dir,
        "atr": atr,
        "vol_ratio": vol_ratio,
    }


class StreamingHtfState:
    """Streaming confirmed-bar HTF state (4h) for in-engine gate evaluation.

    Append only completed HTF OHLC; exposes last confirmed features for LTF gate.
    Warmup matches batch Wilder (NaN until periods fill).
    """

    def __init__(
        self,
        *,
        adx_period: int = ADX_PERIOD,
        atr_period: int = ATR_PERIOD,
        vol_median_w: int = VOL_MEDIAN_W,
    ) -> None:
        self.adx_period = adx_period
        self.atr_period = atr_period
        self.vol_median_w = vol_median_w
        self.highs: list[float] = []
        self.lows: list[float] = []
        self.closes: list[float] = []
        self.close_ns: list[int] = []
        # last confirmed feature snapshot
        self.dir: int = 0
        self.adx: float = float("nan")
        self.atr: float = float("nan")
        self.vol_ratio: float = float("nan")
        self.ready: bool = False

    def update(self, high: float, low: float, close: float, close_ns: int) -> None:
        """Ingest one completed HTF bar and refresh feature snapshot."""
        self.highs.append(float(high))
        self.lows.append(float(low))
        self.closes.append(float(close))
        self.close_ns.append(int(close_ns))
        h = np.asarray(self.highs, dtype=np.float64)
        l = np.asarray(self.lows, dtype=np.float64)
        c = np.asarray(self.closes, dtype=np.float64)
        pack = htf_features(
            h, l, c,
            adx_period=self.adx_period,
            atr_period=self.atr_period,
            vol_median_w=self.vol_median_w,
        )
        i = len(h) - 1
        self.dir = int(pack["htf_dir"][i])
        self.adx = float(pack["adx"][i])
        self.atr = float(pack["atr"][i])
        self.vol_ratio = float(pack["vol_ratio"][i])
        self.ready = (
            self.dir != 0
            and np.isfinite(self.adx)
            and np.isfinite(self.atr)
            and self.atr > 0
            and np.isfinite(self.vol_ratio)
        )

    def gate(
        self,
        *,
        vol_thr: float,
        adx_min: float | None,
    ) -> tuple[bool, int, float]:
        """Return (gate_on, side, atr) from last confirmed HTF bar.

        DI×VOL_HI: vol_ratio ≥ thr and DI sign defined.
        DI_ADX×VOL_HI: adds ADX ≥ adx_min.
        """
        if not self.ready:
            return False, 0, float("nan")
        if not (self.vol_ratio >= vol_thr):
            return False, 0, float("nan")
        if adx_min is not None:
            if not (np.isfinite(self.adx) and self.adx >= adx_min):
                return False, 0, float("nan")
        return True, self.dir, self.atr
