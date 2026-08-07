"""Per-symbol series + layered features + walk-forward ŷ (design §2–§3)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import polars as pl

from catalog_io import aggregate_clock, load_minute_bars
from config import (
    ABLATIONS,
    BANDS,
    CLOCKS,
    CONFIRM_END,
    DESIGN_START,
    FEATURE_LAYERS,
    H_STAR,
    H_VALUES,
    MIN_TRAIN_ROWS,
    MODELS,
    NS,
    PRIMARY_MODEL,
    ZVOL_EPS,
    ZVOL_WARMUP_BARS,
)
from indicators import (
    abs_oo_bps,
    atr_zigzag,
    ewma_park,
    expanding_percentile,
    expanding_std,
    freeze_zvol_scale,
    parkinson,
    rolling_median_split,
    signed_oo_bps,
    sma,
    sma_angle_on,
    wilder_atr,
    zz_mag_forecast_series,
    zz_next_leg_sign_series,
)
from models import feature_matrix, walk_forward_predict_causal


@dataclass
class SeriesPack:
    """Precomputed per-symbol H1 series + model forecasts."""
    symbol: str
    clock: str
    slot_start: np.ndarray
    slot_end: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    atr: np.ndarray
    atr_lag: np.ndarray
    park: np.ndarray
    ewma_park: np.ndarray
    sigma_zvol: np.ndarray
    sigma_zmag: np.ndarray
    abs_oo: np.ndarray
    uncond_sigma: np.ndarray
    vol_pct: np.ndarray
    mag_pct: np.ndarray
    slow_regime: np.ndarray
    shock_flag: np.ndarray
    r: np.ndarray
    s_symbol: float
    design_lo: int
    design_hi: int
    confirm_hi: int
    # layered features
    features: dict[str, np.ndarray] = field(default_factory=dict)
    # yhat[model][ablation][H] -> array
    yhat: dict = field(default_factory=dict)
    # targets y[H]
    y_target: dict = field(default_factory=dict)
    y_ready: dict = field(default_factory=dict)


def _band_index_bounds(slot_start: np.ndarray, start: datetime, end: datetime) -> tuple[int, int]:
    lo_ns = int(start.timestamp() * NS)
    hi_ns = int(end.timestamp() * NS)
    lo = int(np.searchsorted(slot_start, lo_ns, side="left"))
    hi = int(np.searchsorted(slot_start, hi_ns, side="left"))
    return lo, hi


def _build_features(
    open_: np.ndarray,
    close: np.ndarray,
    ewma: np.ndarray,
    sigma_zvol: np.ndarray,
    sigma_zmag: np.ndarray,
    slow: np.ndarray,
    shock: np.ndarray,
    atr_lag: np.ndarray,
    swings,
    h_star: int = H_STAR,
) -> dict[str, np.ndarray]:
    n = open_.size
    lvl_pct = expanding_percentile(ewma)

    # DERIVED error dynamics over last completed H* window ending at t
    # real_move_bps: |open[t]/open[t-H*] - 1| * 1e4  (completed path ending at decision t)
    real_move = np.full(n, np.nan)
    signed_path = np.full(n, np.nan)
    for t in range(h_star, n):
        o0 = open_[t - h_star]
        o1 = open_[t]
        if o0 > 0 and np.isfinite(o0) and np.isfinite(o1):
            signed_path[t] = 1e4 * (o1 / o0 - 1.0)
            real_move[t] = abs(signed_path[t])

    pred_move = sigma_zvol.copy()
    err_abs = pred_move - real_move
    err_signed = signed_path  # path vs flat centre (0)
    d_err = np.full(n, np.nan)
    d_vol = np.full(n, np.nan)
    d_err[1:] = err_abs[1:] - err_abs[:-1]
    d_vol[1:] = ewma[1:] - ewma[:-1]
    err_z = err_abs / np.maximum(ewma, ZVOL_EPS)

    sma25 = sma(close)
    sma_sign = np.where(
        np.isfinite(sma25) & np.isfinite(close) & (close != sma25),
        np.sign(close - sma25),
        np.nan,
    )
    angle_on = sma_angle_on(sma25, atr_lag)
    zz_next = zz_next_leg_sign_series(n, swings)

    return {
        "ewma_park": ewma.astype(float),
        "lvl_pct": lvl_pct,
        "zz_mag_hat": sigma_zmag.astype(float),
        "slow_reg": slow.astype(float),
        "shock": shock.astype(float),
        "pred_move_bps": pred_move.astype(float),
        "real_move_bps": real_move,
        "err_abs": err_abs,
        "err_signed": err_signed,
        "d_err": d_err,
        "d_vol": d_vol,
        "err_z": err_z,
        "sma25_sign": sma_sign.astype(float),
        "sma25_angle_on": angle_on.astype(float),
        "zz_next_leg_sign": zz_next.astype(float),
    }


def _targets(open_: np.ndarray, H: int) -> tuple[np.ndarray, np.ndarray]:
    """Target: H-bar open-to-open return from anchor open[t+1] → open[t+1+H].

    y[t] known only after bar t+1+H's open is observed → ready_at = t+1+H.
    """
    n = open_.size
    y = np.full(n, np.nan)
    ready = np.full(n, np.nan)
    for t in range(n - 1 - H):
        o0 = open_[t + 1]
        o1 = open_[t + 1 + H]
        if o0 > 0 and np.isfinite(o0) and np.isfinite(o1):
            y[t] = 1e4 * (o1 / o0 - 1.0)
            ready[t] = float(t + 1 + H)
    return y, ready


def prepare_symbol(symbol: str, clock: str, manifest,
                   *, fit_models: bool = True,
                   ablations: tuple[str, ...] | None = None,
                   models: tuple[str, ...] | None = None,
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

    design_mask = np.zeros(open_.size, dtype=bool)
    design_mask[design_lo_raw:design_hi] = True
    warm_idx = np.where(design_mask & np.isfinite(ewma))[0]
    if warm_idx.size < ZVOL_WARMUP_BARS:
        design_lo = int(warm_idx[0]) + 1 if warm_idx.size else design_lo_raw
    else:
        design_lo = int(warm_idx[ZVOL_WARMUP_BARS - 1]) + 1

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
    r[1:] = np.log(np.maximum(close[1:], 1e-12) / np.maximum(close[:-1], 1e-12))
    abs_r = np.abs(r)
    shock = np.zeros(close.size, dtype=float)
    hist: list[float] = []
    for i in range(close.size):
        if not np.isfinite(abs_r[i]):
            continue
        hist.append(float(abs_r[i]))
        thr = float(np.quantile(hist, 0.9)) if len(hist) >= 20 else float("inf")
        shock[i] = 1.0 if abs_r[i] >= thr else 0.0

    feats = _build_features(
        open_, close, ewma, sigma_zvol, sigma_zmag, slow, shock, atr_lag, swings,
    )

    pack = SeriesPack(
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
        features=feats,
    )

    # targets per H
    for H in H_VALUES:
        y, ready = _targets(open_, H)
        pack.y_target[H] = y
        pack.y_ready[H] = ready

    if not fit_models:
        return pack

    ablations = ablations or ABLATIONS
    models = models or MODELS
    # eligible: design_lo..confirm_hi with finite features for A2 (richest)
    n = open_.size
    eligible = np.zeros(n, dtype=bool)
    eligible[design_lo:confirm_hi] = True

    pack.yhat = {m: {a: {} for a in ablations} for m in models}
    # Fit plan (runtime):
    #   M-RIDGE: A2 × all H; A0/A1 × H=12 only (ablation cell)
    #   M-GBM:   A2 × H=12 only (sensitivity)
    for H in H_VALUES:
        y = pack.y_target[H]
        ready = pack.y_ready[H]
        for abl in ablations:
            X = feature_matrix(feats, abl)
            row_ok = np.isfinite(X).all(axis=1)
            elig = eligible & row_ok
            for model in models:
                need = False
                if model == "M-RIDGE" and abl == "A2":
                    need = True
                elif model == "M-RIDGE" and abl in ("A0", "A1") and H == 12:
                    need = True
                elif model == "M-GBM" and abl == "A2" and H == 12:
                    need = True
                if not need:
                    pack.yhat[model][abl][H] = np.full(n, np.nan)
                    continue
                yh = walk_forward_predict_causal(
                    X, y, ready, elig, slot_start, model=model, min_train=MIN_TRAIN_ROWS,
                )
                pack.yhat[model][abl][H] = yh

    return pack


def feature_rows(pack: SeriesPack, band: str = "DESIGN") -> list[dict]:
    """Emit feature table rows for results/features.parquet."""
    lo = pack.design_lo if band == "DESIGN" else pack.design_hi
    hi = pack.design_hi if band == "DESIGN" else pack.confirm_hi
    rows = []
    cols = FEATURE_LAYERS["A2"]
    for t in range(lo, hi):
        row = {
            "symbol": pack.symbol, "clock": pack.clock, "band": band,
            "t_idx": t, "decision_ts": int(pack.slot_end[t]),
        }
        for c in cols:
            row[c] = float(pack.features[c][t]) if np.isfinite(pack.features[c][t]) else None
        rows.append(row)
    return rows


def model_oos_rows(pack: SeriesPack) -> list[dict]:
    rows = []
    for model, by_abl in pack.yhat.items():
        for abl, by_h in by_abl.items():
            for H, yh in by_h.items():
                y = pack.y_target[H]
                for t in range(pack.design_lo, pack.confirm_hi):
                    if not np.isfinite(yh[t]):
                        continue
                    band = "DESIGN" if t < pack.design_hi else "CONFIRM"
                    err = (yh[t] - y[t]) if np.isfinite(y[t]) else float("nan")
                    rows.append({
                        "symbol": pack.symbol, "band": band, "model": model,
                        "ablation": abl, "H": H, "t_idx": t,
                        "decision_ts": int(pack.slot_end[t]),
                        "yhat_bps": float(yh[t]),
                        "y_bps": float(y[t]) if np.isfinite(y[t]) else None,
                        "err_bps": float(err) if np.isfinite(err) else None,
                        "abs_err_bps": float(abs(err)) if np.isfinite(err) else None,
                    })
    return rows
