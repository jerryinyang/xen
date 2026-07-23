"""D-ZZ next-move forecast heads (design §3.3, mandatory characterisation on BOTH clocks).

For each confirmed swing k, predict the NEXT swing's magnitude (bps) and path_noise (vol proxy)
from swing k's feature vector, with two model forms:

* **AR(1)** — OLS of target_{k+1} on target_k (the autoregressive baseline).
* **ridge** — ridge (alpha=1.0) on the full feature vector [magnitude, direction, angle,
  path_noise, bars_in_swing].

Causal expanding walk-forward: fit on swings < k, predict swing k's target. Report OOS rank-IC and
MAE per clock. This does NOT replace expectancy as the direction headline (§3.3) but is required.
"""
from __future__ import annotations

import numpy as np

from indicators import Swing

RIDGE_ALPHA = 1.0
MIN_TRAIN = 20            # swings required before the first walk-forward prediction
_FEATURES = ("magnitude_bps", "direction", "angle_bps_per_bar", "path_noise_atr", "bars_in_swing")


def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3:
        return float("nan")
    from scipy.stats import rankdata
    rx, ry = rankdata(x[m]), rankdata(y[m])
    sx, sy = rx.std(), ry.std()
    if sx == 0 or sy == 0:
        return float("nan")
    return float(((rx - rx.mean()) * (ry - ry.mean())).mean() / (sx * sy))


def _feature_matrix(swings: list[Swing]) -> np.ndarray:
    return np.array([[getattr(s, f) for f in _FEATURES] for s in swings], float)


def _targets(swings: list[Swing]) -> dict[str, np.ndarray]:
    mag = np.array([s.magnitude_bps for s in swings], float)
    noise = np.array([s.path_noise_atr for s in swings], float)
    return {"magnitude_bps": mag, "path_noise_atr": noise}


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


def _ar1_fit_predict(t_tr: np.ndarray, y_tr: np.ndarray, t_te: float) -> float:
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


def walk_forward(swings: list[Swing]) -> dict:
    """OOS predictions for both targets x both models. Predict swing k (>=MIN_TRAIN) from swings
    <k; swing k's own features/target feed swing k+1's prediction. Returns per-target IC/MAE."""
    ns = len(swings)
    if ns < MIN_TRAIN + 2:
        return {"n_swings": ns, "powered": False}
    X = _feature_matrix(swings)
    tg = _targets(swings)
    out: dict = {"n_swings": ns, "powered": True}
    # feature row k predicts target of swing k+1
    for tname, y in tg.items():
        ar_pred, rg_pred, actual = [], [], []
        for k in range(MIN_TRAIN, ns - 1):
            X_tr = X[:k]
            y_tr = y[1: k + 1]              # target_{i+1} for i in 0..k-1
            row_ok = np.isfinite(X_tr).all(axis=1) & np.isfinite(y_tr)
            if row_ok.sum() < MIN_TRAIN // 2 or not np.isfinite(X[k]).all():
                continue
            act = y[k + 1]
            if not np.isfinite(act):
                continue
            rg_pred.append(_ridge_fit_predict(X_tr[row_ok], y_tr[row_ok], X[k]))
            t_tr = y[:k]
            ar_pred.append(_ar1_fit_predict(t_tr[row_ok], y_tr[row_ok], y[k]))
            actual.append(act)
        actual = np.array(actual, float)
        for mname, pred in (("ar1", np.array(ar_pred, float)), ("ridge", np.array(rg_pred, float))):
            n = int(np.isfinite(pred).sum())
            ic = _spearman(pred, actual) if n >= 3 else float("nan")
            mae = float(np.nanmean(np.abs(pred - actual))) if n else float("nan")
            out[f"{tname}__{mname}"] = {"n_oos": n, "ic": ic, "mae": mae}
    return out
