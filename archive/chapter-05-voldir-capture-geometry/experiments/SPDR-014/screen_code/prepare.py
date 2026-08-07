"""Per-symbol series preparation (features, widths, strata)."""
from __future__ import annotations

from datetime import datetime

import numpy as np
import polars as pl

from catalog_io import aggregate_clock, load_minute_bars
from config import (
    BANDS,
    CLOCKS,
    CONFIRM_END,
    DESIGN_END,
    DESIGN_START,
    NS,
    ZVOL_WARMUP_BARS,
)
from engine import SeriesPack
from indicators import (
    abs_oo_bps,
    atr_zigzag,
    ewma_park,
    expanding_percentile,
    expanding_std,
    freeze_zvol_scale,
    parkinson,
    rolling_median_split,
    wilder_atr,
    zz_mag_forecast_series,
)


def _band_index_bounds(slot_start: np.ndarray, start: datetime, end: datetime) -> tuple[int, int]:
    lo_ns = int(start.timestamp() * NS)
    hi_ns = int(end.timestamp() * NS)
    lo = int(np.searchsorted(slot_start, lo_ns, side="left"))
    hi = int(np.searchsorted(slot_start, hi_ns, side="left"))
    return lo, hi


def prepare_symbol(symbol: str, clock: str, manifest, s_symbol: float | None = None
                   ) -> SeriesPack | None:
    minutes = load_minute_bars(symbol, DESIGN_START, CONFIRM_END, band="TRAIN", manifest=manifest)
    if minutes.height == 0:
        return None
    bars = aggregate_clock(minutes, clock).filter(pl.col("complete"))
    if bars.height < CLOCKS[clock]["warmup_bars"] + 30:
        return None

    slot_start = bars["slot_start"].to_numpy().astype(np.int64)
    slot_end = bars["slot_end"].to_numpy().astype(np.int64)
    open_ = bars["open"].to_numpy().astype(float)
    high = bars["high"].to_numpy().astype(float)
    low = bars["low"].to_numpy().astype(float)
    close = bars["close"].to_numpy().astype(float)

    park = parkinson(high, low)
    ewma = ewma_park(park)
    abs_oo = abs_oo_bps(open_)
    atr = wilder_atr(high, low, close)
    atr_lag = np.concatenate([[np.nan], atr[:-1]])

    design_lo_raw, design_hi = _band_index_bounds(slot_start, *BANDS["DESIGN"])
    _, confirm_hi = _band_index_bounds(slot_start, *BANDS["CONFIRM"])

    # warm-up: first ZVOL_WARMUP_BARS complete bars in DESIGN with finite ewma
    design_mask = np.zeros(open_.size, dtype=bool)
    design_mask[design_lo_raw:design_hi] = True
    # start design origins after warmup within DESIGN
    warm_idx = np.where(design_mask & np.isfinite(ewma))[0]
    if warm_idx.size < ZVOL_WARMUP_BARS:
        # catalog often starts mid-DESIGN (2022-07); use available
        design_lo = int(warm_idx[0]) + 1 if warm_idx.size else design_lo_raw
    else:
        design_lo = int(warm_idx[ZVOL_WARMUP_BARS - 1]) + 1

    if s_symbol is None or not np.isfinite(s_symbol):
        s_symbol = freeze_zvol_scale(ewma, abs_oo, design_mask, ZVOL_WARMUP_BARS)
    sigma_zvol = np.where(np.isfinite(ewma), s_symbol * ewma, np.nan)

    atr_start = int(np.argmax(np.isfinite(atr))) if np.isfinite(atr).any() else 0
    swings = atr_zigzag(close, atr, atr_start)
    sigma_zmag = zz_mag_forecast_series(close.size, swings)

    uncond = expanding_std(abs_oo, min_n=20)
    vol_pct = expanding_percentile(ewma)
    mag_pct = expanding_percentile(np.where(np.isfinite(sigma_zmag), sigma_zmag, np.nan))
    slow = rolling_median_split(ewma, window=20)

    r = np.full(close.size, np.nan)
    r[1:] = np.log(close[1:] / close[:-1])
    abs_r = np.abs(r)
    # expanding top-decile shock flag on |r|
    shock = np.zeros(close.size, dtype=float)
    hist: list[float] = []
    for i in range(close.size):
        if not np.isfinite(abs_r[i]):
            shock[i] = 0.0
            continue
        hist.append(float(abs_r[i]))
        thr = float(np.quantile(hist, 0.9)) if len(hist) >= 20 else float("inf")
        shock[i] = 1.0 if abs_r[i] >= thr else 0.0

    return SeriesPack(
        symbol=symbol, clock=clock,
        slot_start=slot_start, slot_end=slot_end,
        open=open_, high=high, low=low, close=close,
        atr=atr, atr_lag=atr_lag,
        park=park, ewma_park=ewma,
        sigma_zvol=sigma_zvol, sigma_zmag=sigma_zmag,
        abs_oo=abs_oo, uncond_sigma=uncond,
        vol_pct=vol_pct, mag_pct=mag_pct,
        slow_regime=slow, shock_flag=shock, r=r,
        s_symbol=float(s_symbol) if np.isfinite(s_symbol) else float("nan"),
        design_lo=design_lo, design_hi=design_hi, confirm_hi=confirm_hi,
    )
