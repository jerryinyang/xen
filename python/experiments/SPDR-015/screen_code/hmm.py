"""2-state Gaussian HMM on rv20 (R-HMM-RV) — causal expanding fit + forward filter.

O3 §2.1: genuine level HMM on rv20, not on r. HIGH = larger-mean state on the level series.
Causality: fit window ends strictly before origin; state at t uses obs ≤ t only.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

_MIN_SIGMA = 1e-12
_LOG2PI = float(np.log(2.0 * np.pi))


@dataclass(frozen=True)
class HMMParams:
    pi: np.ndarray
    A: np.ndarray
    mu: np.ndarray
    sigma: np.ndarray
    n_fit: int
    n_iter: int
    loglik: float

    @property
    def high(self) -> int:
        """HIGH = larger mean on rv20 (level), not larger sigma on returns."""
        return int(np.argmax(self.mu))

    def to_dict(self) -> dict:
        return {
            "pi": self.pi.tolist(), "A": self.A.tolist(),
            "mu": self.mu.tolist(), "sigma": self.sigma.tolist(),
            "high_state": self.high, "n_fit": self.n_fit,
            "n_iter": self.n_iter, "loglik": self.loglik,
        }


def _emission(x: np.ndarray, mu: np.ndarray, sigma: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    s = np.maximum(sigma, _MIN_SIGMA)
    z = (x[:, None] - mu[None, :]) / s[None, :]
    logp = -0.5 * (z * z) - np.log(s)[None, :] - 0.5 * _LOG2PI
    rowmax = logp.max(axis=1)
    return np.exp(logp - rowmax[:, None]), rowmax


def _forward(B: np.ndarray, pi: np.ndarray, A: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = B.shape[0]
    alpha = np.zeros((n, 2))
    scale = np.zeros(n)
    a = pi * B[0]
    scale[0] = a.sum()
    alpha[0] = a / scale[0] if scale[0] > 0 else np.array([0.5, 0.5])
    for t in range(1, n):
        a = (alpha[t - 1] @ A) * B[t]
        s = a.sum()
        scale[t] = s
        alpha[t] = a / s if s > 0 else np.array([0.5, 0.5])
    return alpha, scale


def _backward(B: np.ndarray, A: np.ndarray, scale: np.ndarray) -> np.ndarray:
    n = B.shape[0]
    beta = np.zeros((n, 2))
    beta[-1] = 1.0
    for t in range(n - 2, -1, -1):
        b = A @ (B[t + 1] * beta[t + 1])
        s = scale[t + 1]
        beta[t] = b / s if s > 0 else b
    return beta


def fit_gaussian_hmm(x: np.ndarray, *, n_iter: int = 100, tol: float = 1e-7) -> HMMParams | None:
    """Baum-Welch fit of a 2-state Gaussian HMM to level series ``x`` (NaNs dropped)."""
    v = x[np.isfinite(x)]
    if v.size < 60:
        return None
    med = np.median(v)
    lo, hi = v[v <= med], v[v > med]
    if lo.size < 5 or hi.size < 5:
        return None
    mu = np.array([lo.mean(), hi.mean()])
    sigma = np.array([max(lo.std(), _MIN_SIGMA), max(hi.std(), _MIN_SIGMA)])
    A = np.array([[0.9, 0.1], [0.1, 0.9]])
    pi = np.array([0.5, 0.5])

    prev_ll = -np.inf
    it = 0
    for it in range(1, n_iter + 1):
        B, rowmax = _emission(v, mu, sigma)
        alpha, scale = _forward(B, pi, A)
        if not np.all(scale > 0):
            return None
        beta = _backward(B, A, scale)
        gamma = alpha * beta
        gsum = gamma.sum(axis=1, keepdims=True)
        gamma = np.divide(gamma, gsum, out=np.full_like(gamma, 0.5), where=gsum > 0)

        xi = np.einsum("ti,ij,tj,tj->tij", alpha[:-1], A, B[1:], beta[1:])
        xs = xi.sum(axis=(1, 2), keepdims=True)
        xi = np.divide(xi, xs, out=np.zeros_like(xi), where=xs > 0)

        pi = gamma[0] / gamma[0].sum()
        num = xi.sum(axis=0)
        den = num.sum(axis=1, keepdims=True)
        A = np.divide(num, den, out=np.full_like(num, 0.5), where=den > 0)
        w = gamma.sum(axis=0)
        mu = (gamma * v[:, None]).sum(axis=0) / np.maximum(w, 1e-12)
        var = (gamma * (v[:, None] - mu[None, :]) ** 2).sum(axis=0) / np.maximum(w, 1e-12)
        sigma = np.maximum(np.sqrt(np.maximum(var, 0.0)), _MIN_SIGMA)

        ll = float(np.log(np.maximum(scale, 1e-300)).sum() + rowmax.sum())
        if np.isfinite(prev_ll) and abs(ll - prev_ll) < tol * max(1.0, abs(prev_ll)):
            prev_ll = ll
            break
        prev_ll = ll
    return HMMParams(pi, A, mu, sigma, int(v.size), it, float(prev_ll))


def filter_high_prob(x: np.ndarray, params: HMMParams) -> np.ndarray:
    """Causal filtered P(HIGH) at each t (NaN where x is NaN)."""
    out = np.full(x.size, np.nan)
    m = np.isfinite(x)
    if not m.any():
        return out
    B, _ = _emission(x[m], params.mu, params.sigma)
    alpha, _ = _forward(B, params.pi, params.A)
    out[m] = alpha[:, params.high]
    return out


def walk_forward_states(
    x: np.ndarray,
    slot_end_ns: np.ndarray,
    start_idx: int,
    month_keys: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    """Monthly-refit expanding-window HMM; returns hard state, high_prob, fit log.

    HARD causality: for segment [a, b), fit uses x[:a] only (fit end index a-1 < a).
    """
    n = x.size
    state = np.full(n, -1, dtype=np.int64)
    prob = np.full(n, np.nan)
    fits: list[dict] = []
    if n == 0 or start_idx >= n:
        return state, prob, fits

    points = [start_idx]
    for i in range(start_idx + 1, n):
        if month_keys[i] != month_keys[i - 1]:
            points.append(i)
    points.append(n)

    for a, b in zip(points[:-1], points[1:]):
        if a < 1:
            continue
        p = fit_gaussian_hmm(x[:a])
        if p is None:
            continue
        pr = filter_high_prob(x[:b], p)
        # HARD: fit_end = slot_end of last fit obs = index a-1
        fit_end_ts = int(slot_end_ns[a - 1]) if a > 0 else -1
        fits.append({
            "idx": int(a),
            "n_fit": p.n_fit,
            "fit_end_ts": fit_end_ts,
            "first_origin_ts": int(slot_end_ns[a]) if a < n else -1,
            "fit_end_lt_origin": bool(fit_end_ts < int(slot_end_ns[a])) if a < n else False,
        })
        for i in range(a, b):
            if np.isfinite(pr[i]):
                prob[i] = pr[i]
                state[i] = 1 if pr[i] >= 0.5 else 0
    return state, prob, fits
