"""Arm 2b — ordinal next-swing magnitude (design §3).

Targets: T-GT-CUR, T-GT-MED K=5/10. Models: AR1-threshold, Ridge-cont, Logit-ridge.
Features of swing k known at confirmation; predict swing k+1 only after k confirmed.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np

from config import (
    ATR_PERIOD,
    BOOT_BLOCKS,
    BOOT_RESAMPLES,
    BOOT_SEEDS,
    DERANGE_SEEDS,
    INITIAL_FIT_FRACTION,
    LOGIT_RIDGE_ALPHA,
    MIN_DATES,
    MIN_SWINGS,
    RIDGE_ALPHA,
    ZZ_FEATURES,
    ZZ_MEDIAN_K,
    ZZ_MIN_TRAIN,
    ZZ_REVERSAL_ATR,
)
from controls import label_derange_collapse
from transitions import brier, _clip_p
from xen.evaluation import block_bootstrap_ci


def _swing_ci_sweep(vals: np.ndarray) -> dict:
    """Block-bootstrap CI over the per-swing series (design §5 blocks 1/3/7; QA Issue 2 fix).

    Swings are non-overlapping episodes (H=1 swing), so any block≥1 satisfies block≥H; the
    1/3/7-swing sweep discloses block sensitivity. Returns the conservative envelope
    (`ci` = [min ci_lo, max ci_hi] across the sweep) + the full sweep.
    """
    vals = vals[np.isfinite(vals)]
    if vals.size < 30:
        return {"ci": [float("nan"), float("nan")], "sweep": [], "n": int(vals.size)}
    sweep = []
    for bd in BOOT_BLOCKS:
        r = block_bootstrap_ci(
            vals, np.mean, block=int(bd), n_boot=BOOT_RESAMPLES,
            seed=int(BOOT_SEEDS[0]), n_seeds=len(BOOT_SEEDS),
        )
        sweep.append({"block": int(bd), "ci_lo": r["ci"][0], "ci_hi": r["ci"][1]})
    return {
        "ci": [min(s["ci_lo"] for s in sweep), max(s["ci_hi"] for s in sweep)],
        "sweep": sweep, "n": int(vals.size),
    }


# ------------------------------------------------------------- ATR / ZZ ----


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
    confirm_slot_end: int = 0
    confirm_date: int = 0


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
    seed = float(np.mean(tr[1 : period + 1]))
    atr[period] = seed
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def _swing_features(start_idx, end_idx, confirm_idx, close, atr) -> Swing:
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
    dev = np.abs(close[start_idx : end_idx + 1] - bridge)
    atr_seg = atr[start_idx : end_idx + 1]
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


def _feature_matrix(swings: list[Swing]) -> np.ndarray:
    return np.array([[getattr(s, f) for f in ZZ_FEATURES] for s in swings], float)


def _ridge_fit_predict(X_tr, y_tr, x_te, alpha=RIDGE_ALPHA) -> float:
    mu = X_tr.mean(axis=0)
    sd = X_tr.std(axis=0)
    sd[sd == 0] = 1.0
    Xs = (X_tr - mu) / sd
    ym = y_tr.mean()
    yc = y_tr - ym
    p = Xs.shape[1]
    w = np.linalg.solve(Xs.T @ Xs + alpha * np.eye(p), Xs.T @ yc)
    xs = (x_te - mu) / sd
    return float(xs @ w + ym)


def _ar1_fit_predict(t_tr, y_tr, t_te) -> float:
    m = np.isfinite(t_tr) & np.isfinite(y_tr)
    if m.sum() < 3:
        return float(np.nanmean(y_tr))
    a, b = t_tr[m], y_tr[m]
    va = a.var()
    if va == 0:
        return float(b.mean())
    slope = ((a - a.mean()) * (b - b.mean())).mean() / va
    inter = b.mean() - slope * a.mean()
    return float(slope * t_te + inter)


def _logit_ridge_fit_predict(X_tr, y_tr, x_te, alpha=LOGIT_RIDGE_ALPHA) -> float:
    """Binary logistic ridge → P(y=1)."""
    m = np.isfinite(X_tr).all(axis=1) & np.isfinite(y_tr)
    if m.sum() < 20 or y_tr[m].sum() < 3 or (1 - y_tr[m]).sum() < 3:
        return float(np.nanmean(y_tr))
    Xv = X_tr[m]
    yv = y_tr[m].astype(float)
    mu = Xv.mean(axis=0)
    sd = Xv.std(axis=0)
    sd[sd == 0] = 1.0
    Xs = (Xv - mu) / sd
    ones = np.ones((Xs.shape[0], 1))
    Z = np.hstack([ones, Xs])
    w = np.zeros(Z.shape[1])
    for _ in range(30):
        eta = Z @ w
        p = 1.0 / (1.0 + np.exp(-np.clip(eta, -30, 30)))
        W = np.maximum(p * (1.0 - p), 1e-6)
        z = eta + (yv - p) / W
        Zw = Z * W[:, None]
        A = Z.T @ Zw
        A[1:, 1:] += alpha * np.eye(A.shape[0] - 1)
        b = Z.T @ (W * z)
        try:
            w_new = np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            return float(np.nanmean(y_tr))
        if np.max(np.abs(w_new - w)) < 1e-6:
            w = w_new
            break
        w = w_new
    xs = (x_te - mu) / sd
    eta = float(w[0] + xs @ w[1:])
    return float(1.0 / (1.0 + np.exp(-np.clip(eta, -30, 30))))


def _spearman(x, y) -> float:
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3:
        return float("nan")
    from scipy.stats import rankdata
    rx, ry = rankdata(x[m]), rankdata(y[m])
    sx, sy = rx.std(), ry.std()
    if sx == 0 or sy == 0:
        return float("nan")
    return float(((rx - rx.mean()) * (ry - ry.mean())).mean() / (sx * sy))


def _median_last_k(mags: np.ndarray, k: int, idx: int) -> float:
    lo = max(0, idx - k + 1)
    seg = mags[lo : idx + 1]
    seg = seg[np.isfinite(seg)]
    if seg.size == 0:
        return float("nan")
    return float(np.median(seg))


def build_ordinal_panel(swings: list[Swing]) -> dict:
    """Build targets and walk-forward predictions for all models × targets."""
    ns = len(swings)
    if ns < ZZ_MIN_TRAIN + 3:
        return {"n_swings": ns, "powered": False, "rows": [], "metrics": []}

    mags = np.array([s.magnitude_bps for s in swings], float)
    X = _feature_matrix(swings)
    dates = np.array([s.confirm_date for s in swings], np.int64)

    # targets for predicting swing k+1 from features at k
    # y_gt_cur[k] = 1{mag[k+1] > mag[k]}
    y_cur = np.full(ns, np.nan)
    y_med5 = np.full(ns, np.nan)
    y_med10 = np.full(ns, np.nan)
    for k in range(ns - 1):
        y_cur[k] = 1.0 if mags[k + 1] > mags[k] else 0.0
        med5 = _median_last_k(mags, 5, k)
        med10 = _median_last_k(mags, 10, k)
        if np.isfinite(med5):
            y_med5[k] = 1.0 if mags[k + 1] > med5 else 0.0
        if np.isfinite(med10):
            y_med10[k] = 1.0 if mags[k + 1] > med10 else 0.0

    targets = {
        "T-GT-CUR": (y_cur, None),
        "T-GT-MED5": (y_med5, 5),
        "T-GT-MED10": (y_med10, 10),
    }

    rows = []
    metrics = []
    derange = []

    for tname, (y, med_k) in targets.items():
        # continuous ridge / ar1 heads + ordinal
        for model in ("ar1_threshold", "ridge_cont", "logit_ridge"):
            preds_p = []  # probability or soft score in [0,1]
            preds_cont = []
            actual_y = []
            actual_mag = []
            used_k = []
            for k in range(ZZ_MIN_TRAIN, ns - 1):
                if not np.isfinite(y[k]):
                    continue
                X_tr = X[:k]
                # continuous target for ridge/ar1 is mag[k+1] for training pairs
                y_cont_tr = mags[1 : k + 1]
                y_bin_tr = y[:k]
                row_ok = np.isfinite(X_tr).all(axis=1) & np.isfinite(y_cont_tr)
                if row_ok.sum() < ZZ_MIN_TRAIN // 2 or not np.isfinite(X[k]).all():
                    continue

                thr = mags[k] if tname == "T-GT-CUR" else _median_last_k(mags, med_k, k)
                if not np.isfinite(thr):
                    continue

                if model == "ar1_threshold":
                    cont = _ar1_fit_predict(mags[:k][row_ok], y_cont_tr[row_ok], mags[k])
                    # soft: sigmoid of (pred - thr) / scale
                    scale = max(1.0, float(np.nanstd(mags[: k + 1])))
                    p = float(1.0 / (1.0 + np.exp(-(cont - thr) / scale)))
                elif model == "ridge_cont":
                    cont = _ridge_fit_predict(X_tr[row_ok], y_cont_tr[row_ok], X[k])
                    scale = max(1.0, float(np.nanstd(mags[: k + 1])))
                    p = float(1.0 / (1.0 + np.exp(-(cont - thr) / scale)))
                else:  # logit_ridge direct
                    cont = float("nan")
                    yb = y_bin_tr[row_ok]
                    if not np.isfinite(yb).all():
                        continue
                    p = _logit_ridge_fit_predict(X_tr[row_ok], yb, X[k])

                preds_p.append(p)
                preds_cont.append(cont)
                actual_y.append(y[k])
                actual_mag.append(mags[k + 1])
                used_k.append(k)

                rows.append({
                    "swing_k": k,
                    "swing_k1": k + 1,
                    "target": tname,
                    "model": model,
                    "y": float(y[k]),
                    "p": p,
                    "pred_cont": cont if np.isfinite(cont) else None,
                    "mag_k": float(mags[k]),
                    "mag_k1": float(mags[k + 1]),
                    "threshold": float(thr),
                    "confirm_date": int(dates[k]),
                    "confirm_idx": int(swings[k].confirm_idx),
                    "confirm_slot_end": int(swings[k].confirm_slot_end),
                })

            pp = np.array(preds_p, float)
            yy = np.array(actual_y, float)
            cont_arr = np.array(preds_cont, float)
            mag_arr = np.array(actual_mag, float)
            n = int(pp.size)
            base = float(np.mean(yy)) if n else float("nan")
            hit = float(np.mean((pp >= 0.5) == (yy >= 0.5))) if n else float("nan")
            # hard hit: for continuous models, use cont > thr already encoded in p>=0.5
            br = brier(yy, pp) if n else float("nan")
            br_base = float(np.mean((base - yy) ** 2)) if n and np.isfinite(base) else float("nan")
            d_brier = br - br_base if np.isfinite(br) and np.isfinite(br_base) else float("nan")
            ic = _spearman(cont_arr, mag_arr) if model != "logit_ridge" else _spearman(pp, mag_arr)
            n_dates = int(np.unique(dates[np.array(used_k, int)]).size) if used_k else 0

            # calibration slope (5 bins)
            cal_slope = _calibration_slope(pp, yy)

            # design §3.4 SUPPORTED needs the point effect AND a clearing CI (QA Issue 2 fix):
            #   hit leg   — per-swing hit indicator, CI_low (conservative min over sweep) > base
            #   brier leg — per-swing Δ Brier vs base, CI_hi (conservative max over sweep) < 0
            # CI only runs on powered cells (UNPOWERED labels UNPOWERED regardless of CI).
            powered = n >= MIN_SWINGS and n_dates >= MIN_DATES
            if powered:
                hit_i = ((pp >= 0.5) == (yy >= 0.5)).astype(float)
                dbrier_i = (pp - yy) ** 2 - (base - yy) ** 2 if np.isfinite(base) else np.array([])
                hit_ci = _swing_ci_sweep(hit_i)
                dbrier_ci = _swing_ci_sweep(dbrier_i)
            else:
                hit_ci = {"ci": [float("nan")] * 2, "sweep": []}
                dbrier_ci = {"ci": [float("nan")] * 2, "sweep": []}
            hit_ci_lo = hit_ci["ci"][0]     # conservative low bound on hit rate
            dbrier_ci_hi = dbrier_ci["ci"][1]  # conservative high bound on Δ Brier

            hit_supported = (
                np.isfinite(hit) and hit >= base + 0.05
                and np.isfinite(hit_ci_lo) and hit_ci_lo > base
            )
            brier_supported = (
                np.isfinite(d_brier) and d_brier < 0
                and np.isfinite(dbrier_ci_hi) and dbrier_ci_hi < 0
            )

            if not powered:
                band = "UNPOWERED"
            elif hit_supported or brier_supported:
                band = "SUPPORTED"
            elif np.isfinite(hit) and hit < base - 0.05:
                band = "CONTRADICTED"
            else:
                band = "WASH"

            metrics.append({
                "target": tname,
                "model": model,
                "n_oos": n,
                "n_dates": n_dates,
                "hit_rate": hit,
                "base_rate": base,
                "delta_hit_vs_base": hit - base if np.isfinite(hit) and np.isfinite(base) else float("nan"),
                "hit_ci_lo": hit_ci_lo,
                "brier": br,
                "brier_base": br_base,
                "delta_brier_vs_base": d_brier,
                "delta_brier_ci_hi": dbrier_ci_hi,
                "hit_ci_sweep_json": json.dumps(hit_ci["sweep"]),
                "delta_brier_ci_sweep_json": json.dumps(dbrier_ci["sweep"]),
                "rank_ic_cont": ic,
                "calibration_slope": cal_slope,
                "band_label": band,
            })

            # LABEL-SHUFFLE derangement collapse on this powered cell (design §4, both arms).
            if powered:
                col = label_derange_collapse(yy, pp, DERANGE_SEEDS)
                col.update({"arm": "2b", "target": tname, "model": model})
                derange.append(col)

    return {"n_swings": ns, "powered": True, "rows": rows, "metrics": metrics,
            "derange": derange, "mags": mags.tolist()}


def _calibration_slope(p: np.ndarray, y: np.ndarray) -> float:
    m = np.isfinite(p) & np.isfinite(y)
    if m.sum() < 20:
        return float("nan")
    pp, yy = p[m], y[m]
    # 5 quantile bins
    try:
        qs = np.quantile(pp, [0, 0.2, 0.4, 0.6, 0.8, 1.0])
    except Exception:
        return float("nan")
    xs, ys = [], []
    for i in range(5):
        lo, hi = qs[i], qs[i + 1]
        if i < 4:
            mask = (pp >= lo) & (pp < hi)
        else:
            mask = (pp >= lo) & (pp <= hi)
        if mask.sum() < 3:
            continue
        xs.append(float(np.mean(pp[mask])))
        ys.append(float(np.mean(yy[mask])))
    if len(xs) < 3:
        return float("nan")
    xa, ya = np.array(xs), np.array(ys)
    va = xa.var()
    if va == 0:
        return float("nan")
    return float(((xa - xa.mean()) * (ya - ya.mean())).mean() / va)


def feature_shift_control(swings: list[Swing]) -> dict:
    """CONTROL FEATURE-SHIFT (2b): lag features by +1 swing → skill should drop."""
    ns = len(swings)
    if ns < ZZ_MIN_TRAIN + 5:
        return {"status": "UNPOWERED", "n_swings": ns}
    mags = np.array([s.magnitude_bps for s in swings], float)
    X = _feature_matrix(swings)
    # causal: X[k] → mag[k+1]
    # shifted: X[k-1] → mag[k+1] (extra lag, past)
    # illegal: X[k+1] → mag[k+1] (future — must inflate if leak)
    live_ic, lag_ic, fut_ic = [], [], []
    for k in range(ZZ_MIN_TRAIN, ns - 2):
        X_tr = X[:k]
        y_tr = mags[1 : k + 1]
        ok = np.isfinite(X_tr).all(axis=1) & np.isfinite(y_tr)
        if ok.sum() < 10:
            continue
        live = _ridge_fit_predict(X_tr[ok], y_tr[ok], X[k])
        lag = _ridge_fit_predict(X_tr[ok], y_tr[ok], X[k - 1]) if k >= 1 else float("nan")
        fut = _ridge_fit_predict(X_tr[ok], y_tr[ok], X[k + 1])
        act = mags[k + 1]
        if np.isfinite(live) and np.isfinite(act):
            live_ic.append((live, act))
        if np.isfinite(lag) and np.isfinite(act):
            lag_ic.append((lag, act))
        if np.isfinite(fut) and np.isfinite(act):
            fut_ic.append((fut, act))

    def _ic(pairs):
        if len(pairs) < 10:
            return float("nan")
        a = np.array([p[0] for p in pairs])
        b = np.array([p[1] for p in pairs])
        return _spearman(a, b)

    return {
        "status": "OK",
        "n_live": len(live_ic),
        "ic_causal_lag0": _ic(live_ic),
        "ic_extra_lag_plus1": _ic(lag_ic),
        "ic_illegal_future": _ic(fut_ic),
        "note": "illegal future should inflate IC if leak; extra lag should drop skill",
    }


def run_zz_ordinal(symbol: str, clock_bars, slot_end: np.ndarray) -> dict:
    """Full 2b for one symbol on H1 complete bars."""
    import polars as pl

    cb = clock_bars.filter(pl.col("complete")).sort("slot_start")
    if cb.height < 100:
        return {"symbol": symbol, "n_swings": 0, "powered": False, "metrics": [], "rows": []}

    h = cb["high"].to_numpy()
    lo = cb["low"].to_numpy()
    c = cb["close"].to_numpy()
    se = cb["slot_end"].to_numpy()
    atr = wilder_atr(h, lo, c)
    start = ATR_PERIOD + 1
    swings = atr_zigzag(c, atr, start)
    for s in swings:
        s.confirm_slot_end = int(se[s.confirm_idx])
        s.confirm_date = int(se[s.confirm_idx] // 1_000_000_000 // 86400)

    panel = build_ordinal_panel(swings)
    panel["symbol"] = symbol
    panel["n_swings"] = len(swings)
    # attach symbol to metrics/rows
    for m in panel.get("metrics", []):
        m["symbol"] = symbol
        m["clock"] = "H1"
    for r in panel.get("rows", []):
        r["symbol"] = symbol
        r["clock"] = "H1"
    for d in panel.get("derange", []):
        d["symbol"] = symbol
        d["clock"] = "H1"
    panel["feature_shift"] = feature_shift_control(swings)
    panel["swings_meta"] = [
        {
            "k": i,
            "confirm_idx": s.confirm_idx,
            "confirm_slot_end": s.confirm_slot_end,
            "magnitude_bps": s.magnitude_bps,
            "direction": s.direction,
            "end_idx": s.end_idx,
            "confirm_ge_end": s.confirm_idx >= s.end_idx,
        }
        for i, s in enumerate(swings[:5])  # sample for golden / integrity
    ]
    return panel
