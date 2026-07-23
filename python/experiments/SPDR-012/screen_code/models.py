"""Causal forecasting models: walk-forward OLS / ridge / unconditional baseline.

Design §6.2 OOS protocol — expanding window, initial fit on the first 40% of the symbol x
clock's scored DESIGN origins (interpretation IN-1), walk-forward re-fit each calendar month.
Every fit uses origins strictly before the first predicted row; the model frozen at the DESIGN
end is the only model ever applied to CONFIRM (design §7.3).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from config import RIDGE_ALPHA


@dataclass(frozen=True)
class LinearModel:
    """Standardised linear model: ``y_hat = intercept + ((X - mu)/sd) @ beta``."""

    mu: np.ndarray
    sd: np.ndarray
    beta: np.ndarray
    intercept: float
    alpha: float
    n_fit: int
    fit_end_ts: int

    def predict(self, X: np.ndarray) -> np.ndarray:
        Z = (X - self.mu) / self.sd
        return self.intercept + Z @ self.beta


def fit_linear(X: np.ndarray, y: np.ndarray, alpha: float, fit_end_ts: int = 0) -> LinearModel | None:
    """Fit OLS (``alpha=0``) or ridge on standardised features; intercept unpenalised."""
    m = np.isfinite(y) & np.all(np.isfinite(X), axis=1)
    Xf, yf = X[m], y[m]
    if Xf.shape[0] < max(20, 3 * Xf.shape[1]):
        return None
    mu = Xf.mean(axis=0)
    sd = Xf.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    Z = (Xf - mu) / sd
    yc = yf - yf.mean()
    A = Z.T @ Z + alpha * np.eye(Z.shape[1])
    try:
        beta = np.linalg.solve(A, Z.T @ yc)
    except np.linalg.LinAlgError:
        return None
    return LinearModel(mu, sd, beta, float(yf.mean()), alpha, int(Xf.shape[0]), int(fit_end_ts))


def month_key(slot_end_ns: np.ndarray) -> np.ndarray:
    """Calendar-month key (YYYY*12 + MM) from ns timestamps — refit schedule axis."""
    days = slot_end_ns // (86_400 * 1_000_000_000)
    # exact civil-from-days (Howard Hinnant algorithm)
    z = days + 719468
    era = np.where(z >= 0, z, z - 146096) // 146097
    doe = z - era * 146097
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    y = yoe + era * 400
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    mp = (5 * doy + 2) // 153
    m = np.where(mp < 10, mp + 3, mp - 9)
    y = np.where(m <= 2, y + 1, y)
    return (y * 12 + m).astype(np.int64)


def walk_forward_predict(
    X: np.ndarray,
    y: np.ndarray,
    slot_end_ns: np.ndarray,
    start_idx: int,
    *,
    alpha: float = RIDGE_ALPHA,
) -> tuple[np.ndarray, np.ndarray, LinearModel | None, list[dict]]:
    """Expanding-window monthly-refit OOS forecasts.

    Parameters
    ----------
    X, y : np.ndarray
        Feature matrix and target over the band's origins (time-ordered).
    slot_end_ns : np.ndarray
        Origin timestamps (ns), used for the calendar-month refit schedule.
    start_idx : int
        First OOS row (= end of the initial fit window).
    alpha : float
        Ridge penalty; ``0.0`` gives OLS.

    Returns
    -------
    pred : np.ndarray
        OOS model forecasts (NaN inside the initial fit window).
    baseline : np.ndarray
        Unconditional-mean forecast from the same expanding fit window (design §5).
    final_model : LinearModel | None
        Model fitted on ALL rows of this band — the frozen model applied to CONFIRM.
    fits : list[dict]
        Refit log (index, n_fit, fit_end_ts).
    """
    n = y.size
    pred = np.full(n, np.nan)
    baseline = np.full(n, np.nan)
    fits: list[dict] = []
    if n == 0 or start_idx >= n:
        return pred, baseline, None, fits

    mk = month_key(slot_end_ns)
    refit_points = [start_idx]
    for i in range(start_idx + 1, n):
        if mk[i] != mk[i - 1]:
            refit_points.append(i)
    refit_points.append(n)

    for a, b in zip(refit_points[:-1], refit_points[1:]):
        if a >= n:
            break
        model = fit_linear(X[:a], y[:a], alpha, fit_end_ts=int(slot_end_ns[a - 1]))
        ys = y[:a][np.isfinite(y[:a])]
        base = float(ys.mean()) if ys.size else np.nan
        baseline[a:b] = base
        if model is not None:
            pred[a:b] = model.predict(X[a:b])
            fits.append({"idx": int(a), "n_fit": model.n_fit, "fit_end_ts": model.fit_end_ts})
    final_model = fit_linear(X, y, alpha, fit_end_ts=int(slot_end_ns[-1]))
    return pred, baseline, final_model, fits
