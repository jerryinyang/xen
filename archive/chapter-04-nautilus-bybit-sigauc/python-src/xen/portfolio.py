"""Causal portfolio construction for the CF-MR-001 deployment study (EXP-095, Phase 022).

Parameter-light, **causal** equal-risk-contribution (ERC) portfolio construction over a set of
per-cell net per-event return streams, with:

  * a trailing rolling **Ledoit-Wolf**-shrunk covariance (parameter-free shrinkage to the diagonal),
  * **ERC / risk-parity** weights (no free weight parameter; determined by the covariance),
  * a single **global volatility anchor** (target annualized vol; Sharpe-invariant),
  * a **concurrent-risk cap** (correlation-adjusted exposure ceiling),
  * an optional online **circuit-breaker** overlay (de-allocate a cell whose trailing realized mean
    net return deteriorates below zero; re-allocate on recovery).

All estimators at grid step ``t`` (or rebalance ``r``) consume **only** per-cell returns realized in
steps strictly before ``t`` — there is no look-ahead. Cross-domain alignment is by **timestamp** (the
common wall-clock grid), never by bar index. The module is pure computation: no I/O, no plotting, and
no import-time side effects. Determinism is a property of the inputs and the (optional) seeded RNG.

Estimands and conventions (EXP-095 analysis-plan / D0 §D2–D6):
  * The per-cell stream is the resolved EXIT-RCT **net per-event return in ATR units**, timestamped at
    the event's exit ``CloseTime`` (reused verbatim from the EXP-090/093 substrate by the caller).
  * The portfolio return series lives on a regular wall-clock grid (the finest deployable domain's
    close = 1 hour); a trade's realized net return is booked into the grid step containing its exit
    (closed-market steps carry 0 — flat — identically for every portfolio and baseline, so the
    comparison is fair). 4h positions are realized at exit (no fabricated intermediate mark-to-market
    trajectory is available; documented in the analysis plan, conservative for drawdown timing).
  * Annualized Sharpe uses ``periods_per_year`` supplied by the caller (seconds/year / step_seconds).
  * A trailing window with ``< MIN_ACTIVE_TRADES`` resolved trades for a cell yields **0 weight** for
    that cell that rebalance (causal warmup / INDETERMINATE handling — never forced to a number).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

# --------------------------------------------------------------------------- #
# Constants (construction invariants — NOT tunable hyperparameters; those are
# passed in by the caller from the frozen D0 ratified-parameter table)
# --------------------------------------------------------------------------- #
ERC_MAX_ITER: int = 10_000          # ERC fixed-point iteration cap (deterministic convergence)
ERC_TOL: float = 1e-10              # ERC convergence tolerance on the risk-contribution spread
MIN_ACTIVE_TRADES: int = 2          # < this many trailing trades for a cell -> 0 weight (INDETERMINATE)
EPS: float = 1e-12                  # numerical floor (guards divide-by-zero)


# --------------------------------------------------------------------------- #
# Dataclasses / types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CellStream:
    """One deployable cell's resolved net per-event return stream (ATR units).

    All arrays are aligned, length = number of resolved trades, in entry-time order.

    Attributes
    ----------
    name : str
        Cell label, e.g. ``"EURUSD-4h"``.
    entry_epoch, exit_epoch : np.ndarray[int64]
        Per-trade entry / exit domain-bar ``CloseTime`` epoch seconds.
    net : np.ndarray[float64]
        Per-trade net return in ATR units (gross minus the frozen cost).
    """

    name: str
    entry_epoch: np.ndarray
    exit_epoch: np.ndarray
    net: np.ndarray
    mark_epoch: np.ndarray = None        # (D0-amendment-001 A1) intra-position 1h MTM mark epochs
    mark_return: np.ndarray = None       # (D0-amendment-001 A1) per-1h unrealized-P&L increment at each mark


@dataclass(frozen=True)
class PortfolioResult:
    """Output of one causal portfolio construction (A or B) on a grid return matrix."""

    returns: np.ndarray          # (T,) portfolio net return per grid step (vol-anchored)
    weights: np.ndarray          # (T, k) applied weight per cell per step (held between rebalances)
    breaker_active: np.ndarray   # (T, k) bool: cell allocated (True) / circuit-broken (False)
    rebalance_idx: np.ndarray    # (R,) grid indices at which weights were recomputed
    n_indeterminate: int         # rebalances at which >=1 cell was warmup/INDETERMINATE (0 weight)


# --------------------------------------------------------------------------- #
# Pure computation — covariance estimation (Ledoit-Wolf shrinkage to the diagonal)
# --------------------------------------------------------------------------- #
def ledoit_wolf_shrinkage(returns: np.ndarray) -> tuple[np.ndarray, float]:
    """Ledoit-Wolf (2004) shrinkage of the sample covariance toward its diagonal.

    Parameter-free analytical shrinkage intensity (no tuned ridge). Shrinks the sample covariance
    ``S`` toward the diagonal target ``diag(S)`` by ``Sigma = (1-d)*S + d*diag(S)``, with ``d`` the
    Ledoit-Wolf optimal intensity clipped to ``[0, 1]``. Suited to the small-sample / high-correlation
    8x8 regime (the JPY cluster) where the raw sample covariance is unstable.

    Parameters
    ----------
    returns : np.ndarray
        ``(T, k)`` return matrix (rows = grid steps, columns = cells). ``T >= 2`` required.

    Returns
    -------
    tuple[np.ndarray, float]
        The ``(k, k)`` shrunk covariance and the realized shrinkage intensity ``d``.
    """
    x = np.asarray(returns, dtype=np.float64)
    t, k = x.shape
    if t < 2:
        raise ValueError(f"ledoit_wolf_shrinkage needs >= 2 rows, got {t}")
    mean = x.mean(axis=0)
    xc = x - mean
    sample = (xc.T @ xc) / t                                   # MLE sample covariance (T normalization)
    target = np.diag(np.diag(sample))                          # diagonal shrinkage target
    # pi_hat: sum of asymptotic variances of the sample covariance entries
    xc2 = xc ** 2
    pi_mat = (xc2.T @ xc2) / t - sample ** 2
    pi_hat = float(pi_mat.sum())
    # rho_hat for a diagonal target is the sum of the diagonal pi terms only
    rho_hat = float(np.trace(pi_mat))
    # gamma_hat: squared Frobenius distance between sample and target
    gamma_hat = float(((sample - target) ** 2).sum())
    if gamma_hat <= EPS:
        return sample, 0.0
    kappa = (pi_hat - rho_hat) / gamma_hat
    delta = float(min(1.0, max(0.0, kappa / t)))
    sigma = (1.0 - delta) * sample + delta * target
    return sigma, delta


# --------------------------------------------------------------------------- #
# Pure computation — ERC (equal risk contribution) weights
# --------------------------------------------------------------------------- #
def erc_weights(cov: np.ndarray, max_iter: int = ERC_MAX_ITER,
                tol: float = ERC_TOL) -> np.ndarray:
    """Long-only equal-risk-contribution (risk-parity) weights for a covariance matrix.

    Solved by the standard deterministic cyclical-coordinate fixed-point iteration (Spinu / Griveau-
    Billion), which converges for any positive-definite ``cov`` from a strictly positive start and has
    **no free parameter** (the weights are determined by ``cov``). Weights are non-negative and sum to 1.

    Parameters
    ----------
    cov : np.ndarray
        ``(k, k)`` covariance matrix (symmetric positive semi-definite).
    max_iter, tol : int, float
        Iteration cap and convergence tolerance on the normalized risk-contribution spread.

    Returns
    -------
    np.ndarray
        ``(k,)`` ERC weights (>= 0, sum to 1).
    """
    sigma = np.asarray(cov, dtype=np.float64)
    k = sigma.shape[0]
    if k == 0:
        return np.zeros(0, dtype=np.float64)
    if k == 1:
        return np.ones(1, dtype=np.float64)
    vol = np.sqrt(np.maximum(np.diag(sigma), EPS))
    w = (1.0 / vol)
    w = w / w.sum()                                           # inverse-vol warm start (deterministic)
    for _ in range(max_iter):
        mrc = sigma @ w                                       # marginal risk contributions (unscaled)
        rc = w * mrc                                          # risk contributions
        port_var = float(w @ mrc)
        if port_var <= EPS:
            break
        target = port_var / k
        # multiplicative update toward equal risk contribution; renormalize
        w_new = w * np.sqrt(target / np.maximum(rc, EPS))
        w_new = np.maximum(w_new, 0.0)
        s = w_new.sum()
        if s <= EPS:
            break
        w_new = w_new / s
        if np.max(np.abs(w_new - w)) < tol:
            w = w_new
            break
        w = w_new
    return w


# --------------------------------------------------------------------------- #
# Pure computation — grid construction + per-cell grid return matrix
# --------------------------------------------------------------------------- #
def regular_grid(start_epoch: int, end_epoch: int, step_seconds: int) -> np.ndarray:
    """Inclusive regular wall-clock grid of step-start epochs ``[start, end]`` at ``step_seconds``."""
    if end_epoch < start_epoch:
        raise ValueError("regular_grid: end_epoch < start_epoch")
    n = int((end_epoch - start_epoch) // step_seconds) + 1
    return start_epoch + np.arange(n, dtype=np.int64) * int(step_seconds)


def grid_return_matrix(streams: Sequence[CellStream], grid_start: int, step_seconds: int,
                       n_steps: int) -> np.ndarray:
    """Book each cell's per-trade net return into the grid step containing its **exit** epoch.

    A step accumulates the sum of net returns of all of a cell's trades that exit within it (rare for
    a single cell at 1h granularity, but defined). Steps with no exit carry 0 (flat). Returns the
    ``(n_steps, k)`` per-cell grid return matrix.
    """
    k = len(streams)
    mat = np.zeros((n_steps, k), dtype=np.float64)
    for ci, s in enumerate(streams):
        if s.exit_epoch.shape[0] == 0:
            continue
        step = ((s.exit_epoch - grid_start) // step_seconds).astype(np.int64)
        in_range = (step >= 0) & (step < n_steps)
        if not np.any(in_range):
            continue
        np.add.at(mat[:, ci], step[in_range], s.net[in_range])
    return mat


def grid_mark_matrix(streams: Sequence[CellStream], grid_start: int, step_seconds: int,
                     n_steps: int) -> np.ndarray:
    """Book each cell's **intra-position mark-to-market increments** onto the grid (D0 §D2.1 / amendment-001 A1).

    Unlike :func:`grid_return_matrix` (which lumps each trade's whole net at its exit step), this books the
    per-1h **unrealized-P&L increment** of every open position at each intervening 1h close — so the grid
    return series carries each position's adverse excursion, making Sharpe / MaxDD economically comparable
    across 1h and 4h cells. Requires ``mark_epoch`` / ``mark_return`` populated by the caller (the increments
    telescope so that, per position, their sum equals the realized net; the caller asserts that conservation).
    Returns the ``(n_steps, k)`` per-cell grid increment matrix.
    """
    k = len(streams)
    mat = np.zeros((n_steps, k), dtype=np.float64)
    for ci, s in enumerate(streams):
        if s.mark_epoch is None or s.mark_epoch.shape[0] == 0:
            continue
        step = ((s.mark_epoch - grid_start) // step_seconds).astype(np.int64)
        in_range = (step >= 0) & (step < n_steps)
        if not np.any(in_range):
            continue
        np.add.at(mat[:, ci], step[in_range], s.mark_return[in_range])
    return mat


# --------------------------------------------------------------------------- #
# Pure computation — metrics (annualized Sharpe, drawdown, Calmar)
# --------------------------------------------------------------------------- #
def annualized_sharpe(returns: np.ndarray, periods_per_year: float) -> float:
    """Annualized Sharpe of a per-step return series (NaN if std == 0; never inf)."""
    r = np.asarray(returns, dtype=np.float64)
    if r.shape[0] < 2:
        return float("nan")
    sd = float(r.std(ddof=1))
    if sd <= EPS:
        return float("nan")
    return float(r.mean() / sd * np.sqrt(periods_per_year))


def max_drawdown(step_returns: np.ndarray) -> float:
    """Maximum drawdown of the cumulative (additive) equity curve, as a positive magnitude."""
    r = np.asarray(step_returns, dtype=np.float64)
    if r.shape[0] == 0:
        return float("nan")
    equity = np.cumsum(r)
    running_max = np.maximum.accumulate(equity)
    dd = running_max - equity
    return float(np.max(dd)) if dd.shape[0] else float("nan")


def calmar(step_returns: np.ndarray, periods_per_year: float) -> float:
    """Annualized return divided by max drawdown (NaN if MaxDD == 0; never inf)."""
    r = np.asarray(step_returns, dtype=np.float64)
    if r.shape[0] == 0:
        return float("nan")
    ann_return = float(r.mean() * periods_per_year)
    mdd = max_drawdown(r)
    if not np.isfinite(mdd) or mdd <= EPS:
        return float("nan")
    return ann_return / mdd


# --------------------------------------------------------------------------- #
# Pure computation — causal weight overlays (vol anchor + concurrent-risk cap)
# --------------------------------------------------------------------------- #
def vol_anchor_scalar(weights: np.ndarray, cov: np.ndarray, target_ann_vol: float,
                      periods_per_year: float) -> float:
    """Single global scalar so the (trailing-cov) annualized portfolio vol hits the target.

    Sharpe is invariant to this scalar; it sets drawdown/leverage realism only.
    """
    w = np.asarray(weights, dtype=np.float64)
    sigma = np.asarray(cov, dtype=np.float64)
    step_var = float(w @ sigma @ w)
    if step_var <= EPS:
        return 0.0
    ann_vol = np.sqrt(step_var * periods_per_year)
    return float(target_ann_vol / max(ann_vol, EPS))


def concurrent_risk_scale(weights: np.ndarray, cov: np.ndarray, budget_ann_vol: float,
                          cap_mult: float, periods_per_year: float) -> float:
    """Pro-rata down-scale factor if correlation-adjusted annualized risk exceeds ``cap_mult*budget``.

    Returns a factor in ``(0, 1]``; 1.0 when within the cap. Correlation-adjusted because the risk is
    ``sqrt(w' Sigma w)`` (a simultaneous JPY-cluster firing counts ~ one bet).
    """
    w = np.asarray(weights, dtype=np.float64)
    sigma = np.asarray(cov, dtype=np.float64)
    step_var = float(w @ sigma @ w)
    if step_var <= EPS:
        return 1.0
    ann_risk = np.sqrt(step_var * periods_per_year)
    ceiling = cap_mult * budget_ann_vol
    if ann_risk <= ceiling + EPS:
        return 1.0
    return float(ceiling / ann_risk)


# --------------------------------------------------------------------------- #
# Pure computation — grid-derived causal trailing quantities (unify real & null)
# --------------------------------------------------------------------------- #
# A "trade" for trailing-count / circuit-breaker purposes is a non-zero grid entry (a realized net
# return booked at its exit step). At the 1h grid granularity same-step trade collisions are
# negligible, so a column's non-zero entries are that cell's trade stream — this lets the real and the
# block-permuted null share one construction path (both are just grid matrices).
def _trailing_trade_counts(r_mat: np.ndarray, r_row: int) -> np.ndarray:
    """Per-cell count of non-zero grid entries strictly before grid row ``r_row``."""
    if r_row <= 0:
        return np.zeros(r_mat.shape[1], dtype=np.int64)
    return (r_mat[:r_row] != 0.0).sum(axis=0).astype(np.int64)


def breaker_multipliers(r_mat: np.ndarray, r_row: int, window: int) -> np.ndarray:
    """Per-cell {0,1} multiplier: 0 while the trailing-``window`` non-zero-entry mean (< row) < 0.

    Strictly causal: only grid rows before ``r_row`` enter; a cell with no prior trade is not-yet-
    decayed (1).
    """
    k = r_mat.shape[1]
    mult = np.ones(k, dtype=np.float64)
    if r_row <= 0:
        return mult
    for ci in range(k):
        col = r_mat[:r_row, ci]
        nz = col[col != 0.0]
        if nz.shape[0] == 0:
            continue
        if float(nz[-window:].mean()) < 0.0:
            mult[ci] = 0.0
    return mult


def _rebalance_weight(r_mat: np.ndarray, t: int, *, lookback_steps: int, target_ann_vol: float,
                      cap_mult: float, periods_per_year: float, use_breaker: bool,
                      breaker_window: int, trade_mat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Compute the (causal) applied weight vector at rebalance grid row ``t``; return (w, active).

    ``r_mat`` is the P&L (MTM-increment) matrix used for the covariance / portfolio variance; ``trade_mat``
    is the per-resolved-trade matrix (one net per trade at its exit step) used for the active-cell warmup
    gate and the circuit-breaker's trailing-trade mean (D0-amendment-001 A1 — MTM gives multiple grid marks
    per trade, so trade counting must use the trade stream, not the P&L marks).
    """
    k = r_mat.shape[1]
    counts = _trailing_trade_counts(trade_mat, t)
    active = counts >= MIN_ACTIVE_TRADES
    w = np.zeros(k, dtype=np.float64)
    if not np.any(active):
        return w, active
    lo = max(0, t - lookback_steps)
    hist = r_mat[lo:t][:, active]
    if hist.shape[0] < 2:
        return w, active
    cov, _ = ledoit_wolf_shrinkage(hist)
    w_active = erc_weights(cov)
    if use_breaker:
        mult = breaker_multipliers(trade_mat[:, active], t, breaker_window)
        w_active = w_active * mult
        s = w_active.sum()
        w_active = w_active / s if s > EPS else w_active
    if w_active.sum() > EPS:
        # Vol-anchor FIRST: scale the unit-sum weights to the target annualized vol (causal, trailing cov).
        scalar = vol_anchor_scalar(w_active, cov, target_ann_vol, periods_per_year)
        w_active = w_active * scalar
        # Concurrent-risk cap is a guardrail on the *applied* (vol-anchored) risk-aware exposure (D0 D2.3):
        # scale down pro-rata only if that exposure still exceeds cap_mult x budget. Measuring it on the
        # un-anchored unit-sum weights and multiplying with the anchor double-counts leverage and yields
        # ~1/vol^2 ("vol-squared") targeting instead of the intended 1/vol vol-targeting (audit C1).
        cap = concurrent_risk_scale(w_active, cov, target_ann_vol, cap_mult, periods_per_year)
        w_active = w_active * cap
    w[active] = w_active
    return w, active


def _forward_fill_weights(reb_idx: np.ndarray, reb_weights: np.ndarray, n_steps: int) -> np.ndarray:
    """Hold each rebalance weight vector until the next rebalance (vectorized forward-fill)."""
    k = reb_weights.shape[1]
    weights = np.zeros((n_steps, k), dtype=np.float64)
    for i, r in enumerate(reb_idx):
        end = int(reb_idx[i + 1]) if i + 1 < reb_idx.shape[0] else n_steps
        weights[int(r):end] = reb_weights[i]
    return weights


def build_portfolio(grid_return_mat: np.ndarray, grid_start: int, step_seconds: int, *,
                    rebalance_steps: int, lookback_steps: int, target_ann_vol: float,
                    cap_mult: float, periods_per_year: float, use_breaker: bool,
                    breaker_window: int, trade_mat: np.ndarray | None = None) -> PortfolioResult:
    """Construct one causal portfolio (A: ``use_breaker=False`` / B: ``True``) on the grid matrix.

    At each weekly rebalance ``r`` (grid row, every ``rebalance_steps`` steps):
      1. active cells = those with ``>= MIN_ACTIVE_TRADES`` trailing **trades** (from ``trade_mat``), else 0;
      2. Ledoit-Wolf covariance from the trailing ``lookback_steps`` rows of the **P&L** matrix strictly
         before ``r`` (active cells only);
      3. ERC weights on the active covariance;
      4. (B only) circuit-breaker {0,1} multiplier (trailing-trade mean from ``trade_mat``), renormalized;
      5. global vol-anchor scalar (target annualized vol) then concurrent-risk cap down-scale.
    Weights are held until the next rebalance (vectorized forward-fill). The portfolio per-step return
    is ``sum_i w_i * R_pnl[t,i]``. ``trade_mat`` (one net per resolved trade at its exit step) drives the
    warmup gate + breaker; it defaults to ``grid_return_mat`` (back-compat / the null path, where the P&L
    grid *is* the per-trade grid). Every quantity at ``r`` uses only rows ``[max(0, r-lookback), r)`` —
    strictly causal.
    """
    r_mat = np.asarray(grid_return_mat, dtype=np.float64)
    t_mat = r_mat if trade_mat is None else np.asarray(trade_mat, dtype=np.float64)
    n_steps, k = r_mat.shape
    reb_idx = np.arange(0, n_steps, max(1, rebalance_steps), dtype=np.int64)
    reb_weights = np.zeros((reb_idx.shape[0], k), dtype=np.float64)
    n_indeterminate = 0
    for i, t in enumerate(reb_idx):
        w, active = _rebalance_weight(
            r_mat, int(t), lookback_steps=lookback_steps, target_ann_vol=target_ann_vol,
            cap_mult=cap_mult, periods_per_year=periods_per_year, use_breaker=use_breaker,
            breaker_window=breaker_window, trade_mat=t_mat)
        reb_weights[i] = w
        if int(active.sum()) < k:
            n_indeterminate += 1
    weights = _forward_fill_weights(reb_idx, reb_weights, n_steps)
    port = (weights * r_mat).sum(axis=1)
    breaker_active = weights > 0.0
    return PortfolioResult(returns=port, weights=weights, breaker_active=breaker_active,
                           rebalance_idx=reb_idx, n_indeterminate=n_indeterminate)


def naive_inverse_vol(grid_return_mat: np.ndarray, grid_start: int, step_seconds: int, *,
                      rebalance_steps: int, lookback_steps: int, target_ann_vol: float,
                      periods_per_year: float, trade_mat: np.ndarray | None = None) -> np.ndarray:
    """Disclosed contrast: causal naive inverse-vol weights (no ERC, no breaker, no cap).

    Each rebalance weights active cells by ``1/trailing_vol`` (renormalized) then applies the same
    global vol anchor. Over-allocates to correlated clusters (the JPY cross cells) — the baseline ERC
    is meant to beat. P&L / vol from ``grid_return_mat`` (MTM); the warmup gate uses ``trade_mat`` (defaults
    to ``grid_return_mat``).
    """
    r_mat = np.asarray(grid_return_mat, dtype=np.float64)
    t_mat = r_mat if trade_mat is None else np.asarray(trade_mat, dtype=np.float64)
    n_steps, k = r_mat.shape
    reb_idx = np.arange(0, n_steps, max(1, rebalance_steps), dtype=np.int64)
    reb_weights = np.zeros((reb_idx.shape[0], k), dtype=np.float64)
    for i, t in enumerate(reb_idx):
        counts = _trailing_trade_counts(t_mat, int(t))
        active = counts >= MIN_ACTIVE_TRADES
        if not np.any(active):
            continue
        lo = max(0, int(t) - lookback_steps)
        hist = r_mat[lo:int(t)][:, active]
        if hist.shape[0] < 2:
            continue
        vol = hist.std(axis=0, ddof=1)
        inv = np.where(vol > EPS, 1.0 / np.maximum(vol, EPS), 0.0)
        s = inv.sum()
        w_active = inv / s if s > EPS else inv
        cov = np.atleast_2d(np.cov(hist, rowvar=False))
        scalar = vol_anchor_scalar(w_active, cov, target_ann_vol, periods_per_year)
        wv = np.zeros(k, dtype=np.float64)
        wv[active] = w_active * scalar
        reb_weights[i] = wv
    weights = _forward_fill_weights(reb_idx, reb_weights, n_steps)
    return (weights * r_mat).sum(axis=1)


def aggregate_to_cadence(step_returns: np.ndarray, cadence_steps: int) -> np.ndarray:
    """Sum a per-step return series into non-overlapping cadence buckets (e.g. hourly -> weekly).

    The binding Sharpe statistic and its moving-block bootstrap run on this cadence-aggregated series
    (block length then expressed in cadence units), which keeps the bootstrap tractable and sets the
    natural block scale at the rebalance cadence (D0 §D4). A trailing partial bucket is kept (it is a
    real, shorter period).
    """
    r = np.asarray(step_returns, dtype=np.float64)
    n = r.shape[0]
    c = max(1, int(cadence_steps))
    n_buckets = int(np.ceil(n / c))
    out = np.zeros(n_buckets, dtype=np.float64)
    for i in range(n_buckets):
        out[i] = r[i * c:(i + 1) * c].sum()
    return out


# --------------------------------------------------------------------------- #
# Pure computation — moving-block bootstrap Sharpe one-sided lower bound
# --------------------------------------------------------------------------- #
def moving_block_sharpe_lower_bound(step_returns: np.ndarray, rng: np.random.Generator,
                                    periods_per_year: float, *, n_boot: int, alpha: float,
                                    block: int, batch: int = 2_000) -> float:
    """One-sided lower bound on annualized Sharpe via a moving-block bootstrap (serial dependence kept).

    Resamples overlapping length-``block`` blocks of the per-step return series (mirroring
    ``xen.ass.moving_block_bootstrap_cis``), recomputes annualized Sharpe per resample, and returns the
    ``alpha/2`` percentile (the one-sided ~95% lower bound when ``alpha=0.10``). Memory-bounded by
    ``batch``; randomness fully determined by ``rng``.
    """
    x = np.asarray(step_returns, dtype=np.float64)
    n = x.shape[0]
    if n < 2:
        return float("nan")
    b = int(min(max(1, block), n))
    n_starts = n - b + 1
    n_blocks = int(np.ceil(n / b))
    sharpe_boot = np.empty(n_boot, dtype=np.float64)
    sqrt_ppy = np.sqrt(periods_per_year)
    done = 0
    while done < n_boot:
        bs = min(batch, n_boot - done)
        starts = rng.integers(0, n_starts, size=(bs, n_blocks))
        idx = starts[:, :, None] + np.arange(b)[None, None, :]
        idx = idx.reshape(bs, n_blocks * b)[:, :n]
        g = x[idx]
        mean = g.mean(axis=1)
        sd = g.std(axis=1, ddof=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            sharpe = np.where(sd > EPS, mean / sd * sqrt_ppy, np.nan)
        sharpe_boot[done:done + bs] = sharpe
        done += bs
    finite = sharpe_boot[np.isfinite(sharpe_boot)]
    if finite.shape[0] == 0:
        return float("nan")
    return float(np.percentile(finite, 100.0 * alpha / 2.0))


def moving_block_boot_components(step_returns: np.ndarray, rng: np.random.Generator, *, n_boot: int,
                                 block: int, batch: int = 2_000) -> tuple[np.ndarray, np.ndarray]:
    """Per-resample (mean, std) of a moving-block bootstrap — the reusable components of the Sharpe LB.

    Returns ``(mean_r, sd_r)`` over ``n_boot`` resamples (same resampling as
    :func:`moving_block_sharpe_lower_bound`). Caching these lets a planted-edge sweep evaluate
    ``LB(series + c)`` analytically: adding a constant ``c`` shifts every resample mean by ``c`` and leaves
    the std unchanged, so ``Sharpe_resample(c) = (mean_r + c)/sd_r * sqrt(ppy)`` — no re-bootstrapping per
    plant (D0-amendment-001 A4 MDE sweep).
    """
    x = np.asarray(step_returns, dtype=np.float64)
    n = x.shape[0]
    if n < 2:
        return np.empty(0), np.empty(0)
    b = int(min(max(1, block), n))
    n_starts = n - b + 1
    n_blocks = int(np.ceil(n / b))
    mean_r = np.empty(n_boot, dtype=np.float64)
    sd_r = np.empty(n_boot, dtype=np.float64)
    done = 0
    while done < n_boot:
        bs = min(batch, n_boot - done)
        starts = rng.integers(0, n_starts, size=(bs, n_blocks))
        idx = starts[:, :, None] + np.arange(b)[None, None, :]
        idx = idx.reshape(bs, n_blocks * b)[:, :n]
        g = x[idx]
        mean_r[done:done + bs] = g.mean(axis=1)
        sd_r[done:done + bs] = g.std(axis=1, ddof=1)
        done += bs
    return mean_r, sd_r


def sharpe_lower_bound_shift(mean_r: np.ndarray, sd_r: np.ndarray, shift: float,
                            periods_per_year: float, alpha: float) -> float:
    """Analytic Sharpe one-sided lower bound for the series shifted by an additive constant ``shift``.

    Uses cached bootstrap components from :func:`moving_block_boot_components`. Equivalent to
    ``moving_block_sharpe_lower_bound(series + shift, ...)`` but free of re-bootstrapping.
    """
    if mean_r.shape[0] == 0:
        return float("nan")
    sqrt_ppy = np.sqrt(periods_per_year)
    with np.errstate(divide="ignore", invalid="ignore"):
        sharpe = np.where(sd_r > EPS, (mean_r + shift) / sd_r * sqrt_ppy, np.nan)
    finite = sharpe[np.isfinite(sharpe)]
    if finite.shape[0] == 0:
        return float("nan")
    return float(np.percentile(finite, 100.0 * alpha / 2.0))


def moving_block_calmar_lower_bound(step_returns: np.ndarray, rng: np.random.Generator,
                                    periods_per_year: float, *, n_boot: int, alpha: float,
                                    block: int, batch: int = 2_000) -> float:
    """One-sided lower bound on Calmar (ann. return / MaxDD) via the same moving-block bootstrap.

    Resamples blocks, rebuilds each resample's additive equity path, computes Calmar per resample, and
    returns the ``alpha/2`` percentile. NaN when no resample has a positive drawdown. Drawdown-aware
    co-binding endpoint for the mean-reversion family (D0-amendment-001 A3).
    """
    x = np.asarray(step_returns, dtype=np.float64)
    n = x.shape[0]
    if n < 2:
        return float("nan")
    b = int(min(max(1, block), n))
    n_starts = n - b + 1
    n_blocks = int(np.ceil(n / b))
    calmar_boot = np.empty(n_boot, dtype=np.float64)
    done = 0
    while done < n_boot:
        bs = min(batch, n_boot - done)
        starts = rng.integers(0, n_starts, size=(bs, n_blocks))
        idx = starts[:, :, None] + np.arange(b)[None, None, :]
        idx = idx.reshape(bs, n_blocks * b)[:, :n]
        g = x[idx]                                                # (bs, n) resampled return paths
        ann_ret = g.mean(axis=1) * periods_per_year
        equity = np.cumsum(g, axis=1)
        running_max = np.maximum.accumulate(equity, axis=1)
        mdd = (running_max - equity).max(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            calmar_boot[done:done + bs] = np.where(mdd > EPS, ann_ret / mdd, np.nan)
        done += bs
    finite = calmar_boot[np.isfinite(calmar_boot)]
    if finite.shape[0] == 0:
        return float("nan")
    return float(np.percentile(finite, 100.0 * alpha / 2.0))


def cvar(returns: np.ndarray, q: float = 0.05) -> float:
    """Conditional value-at-risk (expected shortfall) at lower-tail level ``q`` — a positive magnitude.

    Mean of the worst ``q``-fraction of returns, sign-flipped so a larger number = a worse tail. NaN on an
    empty series. Computed on the cadence-aggregated (weekly) series by the caller (D0-amendment-001 A3).
    """
    r = np.asarray(returns, dtype=np.float64)
    r = r[np.isfinite(r)]
    if r.shape[0] == 0:
        return float("nan")
    k = max(1, int(np.ceil(q * r.shape[0])))
    worst = np.sort(r)[:k]
    return float(-worst.mean())


def ulcer_index(step_returns: np.ndarray) -> float:
    """Ulcer index on the additive equity path: ``sqrt(mean(drawdown^2))`` (same units as ``max_drawdown``).

    A depth-and-duration-weighted drawdown metric (penalises sustained underwater stretches more than a
    single MaxDD spike). NaN on an empty series (D0-amendment-001 A3).
    """
    r = np.asarray(step_returns, dtype=np.float64)
    if r.shape[0] == 0:
        return float("nan")
    equity = np.cumsum(r)
    dd = np.maximum.accumulate(equity) - equity
    return float(np.sqrt(np.mean(dd ** 2)))


# --------------------------------------------------------------------------- #
# Pure computation — null construction (block-permute rows; zero-expectancy)
# --------------------------------------------------------------------------- #
def block_permute_zero_mean(grid_return_mat: np.ndarray, rng: np.random.Generator, *, block: int,
                            n_out: int) -> np.ndarray:
    """No-edge null: block-permute the **common time index** of the grid matrix, then zero each cell's
    **trade** expectancy while preserving its sparse flat-step structure.

    Resamples contiguous length-``block`` blocks of grid **rows** (the same row index across all cells,
    so the contemporaneous cross-cell covariance and within-cell autocorrelation up to ~``block`` lags
    are preserved), concatenates to ``n_out`` rows, then re-centers **only the non-zero (trade) entries**
    of each column to zero mean — the structural flat-step zeros are left at **exactly 0.0**.

    The trade-only re-centering is the matched no-edge condition for this construction: a "trade" is a
    non-zero grid entry (module note above), so zeroing the mean of the non-zero entries removes each
    cell's edge **without** densifying the matrix. Re-centering across all rows would turn every flat
    zero into ``-mean`` (a spurious non-zero), which would (i) defeat the ``_trailing_trade_counts``
    active/warmup gate and (ii) feed ``breaker_multipliers`` a dense noise series — so the null A/B
    portfolios would no longer mirror the real A/B construction path the calibration must reflect.
    Preserving the zero mask keeps the real and null on one construction path (real-vs-null parallelism).

    This is the ``null_b_block_permute_returns`` form (EXP-001/027/044) — **NOT** a price-path rotation,
    and the null is **not** built around any signal-derived target.
    """
    r_mat = np.asarray(grid_return_mat, dtype=np.float64)
    n, k = r_mat.shape
    if n < 1:
        return np.zeros((n_out, k), dtype=np.float64)
    b = int(min(max(1, block), n))
    n_starts = n - b + 1
    n_blocks = int(np.ceil(n_out / b))
    starts = rng.integers(0, n_starts, size=n_blocks)
    idx = (starts[:, None] + np.arange(b)[None, :]).reshape(-1)[:n_out]
    out = r_mat[idx].copy()
    nz = out != 0.0                                           # trade entries (the per-cell trade stream)
    counts = nz.sum(axis=0)                                   # (k,) trades per cell in the resample
    sums = out.sum(axis=0)                                    # (k,) zeros contribute 0 to the sum
    trade_means = np.divide(sums, counts, out=np.zeros(k, dtype=np.float64), where=counts > 0)
    out -= trade_means[None, :] * nz                          # zero trade expectancy; flat steps stay 0
    return out


def wilson_upper(p: float, n: int, z: float = 1.959963984540054) -> float:
    """Wilson score interval upper bound for a proportion ``p`` over ``n`` trials."""
    if n <= 0:
        return float("nan")
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    half = (z * np.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))) / denom
    return float(centre + half)
