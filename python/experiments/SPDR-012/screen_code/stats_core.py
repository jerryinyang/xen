"""Inference primitives: rank IC, date-block bootstrap, MDE, interpretation bands.

Design §6.2 (per-symbol first; date-block bootstrap on unique UTC dates, blocks 1/3/7,
seeds 101/211/307/401/503, 10k resamples) and §6.3 (bands are LABELS, never gates).

The bootstrap is exact-and-vectorised via per-date sufficient statistics: a statistic that
is a smooth function of additive per-date sums (Pearson correlation of pre-computed global
ranks, group means, paired means) can be recomputed for a resampled set of dates by summing
the sufficient-statistic rows of the sampled dates. Blocks are circular over the ordered
unique-date axis (dependence-matched uncertainty, SPDR lane rule).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from scipy.stats import rankdata

from config import (
    BAND_GAP_CONTRADICTED_BPS,
    BAND_GAP_SUPPORTED_BPS,
    BAND_GAP_WASH_BPS,
    BAND_IC_CONTRADICTED,
    BAND_IC_SUPPORTED,
    BAND_IC_WASH_ABS,
    BOOT_BLOCKS,
    BOOT_CI_ALPHA,
    BOOT_RESAMPLES,
    BOOT_SEEDS,
    MDE_GAP_CEILING_BPS,
    MDE_IC_CEILING,
    MDE_IC_CONST,
    MIN_EFFECTIVE_DATES,
)

_CHUNK = 1000  # resamples per gather chunk (memory bound)


# ------------------------------------------------------------ statistics ----


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation on finite pairs (NaN-safe). Returns NaN if n < 3."""
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3:
        return float("nan")
    rx = rankdata(x[m])
    ry = rankdata(y[m])
    sx, sy = rx.std(), ry.std()
    if sx == 0 or sy == 0:
        return float("nan")
    return float(((rx - rx.mean()) * (ry - ry.mean())).mean() / (sx * sy))


def pearson(x: np.ndarray, y: np.ndarray) -> float:
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3:
        return float("nan")
    a, b = x[m], y[m]
    sa, sb = a.std(), b.std()
    if sa == 0 or sb == 0:
        return float("nan")
    return float(((a - a.mean()) * (b - b.mean())).mean() / (sa * sb))


def autocorr(x: np.ndarray, lag: int) -> float:
    if x.size <= lag + 2:
        return float("nan")
    return pearson(x[:-lag], x[lag:])


def ar1_half_life(x: np.ndarray) -> tuple[float, float]:
    """AR(1) slope and half-life of ``x`` (NaN half-life when slope not in (0,1))."""
    m = np.isfinite(x[:-1]) & np.isfinite(x[1:])
    if m.sum() < 10:
        return float("nan"), float("nan")
    a, b = x[:-1][m], x[1:][m]
    va = a.var()
    if va == 0:
        return float("nan"), float("nan")
    slope = float(((a - a.mean()) * (b - b.mean())).mean() / va)
    hl = float(np.log(0.5) / np.log(slope)) if 0.0 < slope < 1.0 else float("nan")
    return slope, hl


def r2_oos(y: np.ndarray, pred: np.ndarray, baseline: np.ndarray) -> float:
    """Out-of-sample R^2 of ``pred`` against a ``baseline`` forecast (Campbell-Thompson)."""
    m = np.isfinite(y) & np.isfinite(pred) & np.isfinite(baseline)
    if m.sum() < 3:
        return float("nan")
    sse = float(((y[m] - pred[m]) ** 2).sum())
    sst = float(((y[m] - baseline[m]) ** 2).sum())
    return float("nan") if sst == 0 else 1.0 - sse / sst


# ---------------------------------------------- sufficient-stat bootstrap ----


@dataclass
class BootResult:
    """Bootstrap CI grid over (block length x seed) with the worst-case envelope."""

    point: float
    ci_low: float                      # min over the grid — a conservative ENVELOPE, not a 95% CI
    ci_high: float                     # max over the grid — ditto
    se: float                          # MAX bootstrap SD over the grid (matches envelope, F-11)
    n_dates: int
    n_obs: int
    grid: list[dict] = field(default_factory=list)
    se_median: float = float("nan")    # median SD over the grid (disclosure)

    def to_dict(self) -> dict:
        return {
            "point": self.point, "ci_low": self.ci_low, "ci_high": self.ci_high,
            "se_max": self.se, "se_median": self.se_median,
            "n_dates": self.n_dates, "n_obs": self.n_obs,
            "envelope_note": (
                "ci_low/ci_high are the min/max over the 3 block lengths x 5 seeds; this is a "
                "conservative envelope of 95% CIs, not itself a 95% interval (design §6.3)"
            ),
            "block_sensitivity": self.grid,
        }


def _date_index(dates: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    uniq, inv = np.unique(dates, return_inverse=True)
    return uniq, inv


def _accumulate(suff: np.ndarray, inv: np.ndarray, nd: int) -> np.ndarray:
    """Per-date sums of the observation-level sufficient statistics."""
    out = np.zeros((nd, suff.shape[1]))
    for j in range(suff.shape[1]):
        out[:, j] = np.bincount(inv, weights=suff[:, j], minlength=nd)
    return out


def block_bootstrap(
    suff: np.ndarray,
    dates: np.ndarray,
    reducer: Callable[[np.ndarray], np.ndarray],
    *,
    blocks: tuple[int, ...] = BOOT_BLOCKS,
    seeds: tuple[int, ...] = BOOT_SEEDS,
    n_resample: int = BOOT_RESAMPLES,
    alpha: float = BOOT_CI_ALPHA,
) -> BootResult:
    """Circular date-block bootstrap of a sufficient-statistic functional.

    Parameters
    ----------
    suff : np.ndarray
        ``(n_obs, m)`` observation-level sufficient statistics.
    dates : np.ndarray
        ``(n_obs,)`` integer UTC day index per observation.
    reducer : callable
        Maps summed statistics ``(B, m)`` to a statistic vector ``(B,)``.
    blocks, seeds, n_resample, alpha :
        Design §6.2 inference pins.
    """
    nan = float("nan")
    if suff.size == 0:
        return BootResult(nan, nan, nan, nan, 0, 0)
    uniq, inv = _date_index(dates)
    nd = uniq.size
    per_date = _accumulate(suff, inv, nd)
    point = float(reducer(per_date.sum(axis=0)[None, :])[0])
    if nd < 3:
        return BootResult(point, nan, nan, nan, nd, int(suff.shape[0]))

    grid: list[dict] = []
    lows, highs, sds = [], [], []
    for L in blocks:
        L_eff = min(L, nd)
        k = int(np.ceil(nd / L_eff))
        offs = np.arange(L_eff)
        for seed in seeds:
            rng = np.random.default_rng(seed)
            stats = np.empty(n_resample)
            done = 0
            while done < n_resample:
                b = min(_CHUNK, n_resample - done)
                starts = rng.integers(0, nd, size=(b, k))
                idx = (starts[:, :, None] + offs[None, None, :]) % nd
                idx = idx.reshape(b, k * L_eff)[:, :nd]
                sums = per_date[idx].sum(axis=1)
                stats[done : done + b] = reducer(sums)
                done += b
            finite = stats[np.isfinite(stats)]
            if finite.size < 10:
                continue
            lo = float(np.quantile(finite, alpha / 2))
            hi = float(np.quantile(finite, 1 - alpha / 2))
            sd = float(finite.std())
            grid.append({"block": L, "seed": seed, "ci_low": lo, "ci_high": hi, "sd": sd})
            lows.append(lo)
            highs.append(hi)
            sds.append(sd)
    if not grid:
        return BootResult(point, nan, nan, nan, nd, int(suff.shape[0]))
    return BootResult(
        point=point,
        ci_low=float(min(lows)),
        ci_high=float(max(highs)),
        se=float(max(sds)),
        n_dates=nd,
        n_obs=int(suff.shape[0]),
        grid=grid,
        se_median=float(np.median(sds)),
    )


# ------------------------------------------------------------- reducers ----


def _corr_reducer(s: np.ndarray) -> np.ndarray:
    n, sx, sy, sxy, sxx, syy = (s[:, i] for i in range(6))
    with np.errstate(invalid="ignore", divide="ignore"):
        cov = sxy / n - (sx / n) * (sy / n)
        vx = sxx / n - (sx / n) ** 2
        vy = syy / n - (sy / n) ** 2
        return cov / np.sqrt(vx * vy)


def _diff_reducer(s: np.ndarray) -> np.ndarray:
    n1, s1, n0, s0 = (s[:, i] for i in range(4))
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where((n1 > 0) & (n0 > 0), s1 / np.maximum(n1, 1) - s0 / np.maximum(n0, 1), np.nan)


def _mean_reducer(s: np.ndarray) -> np.ndarray:
    n, tot = s[:, 0], s[:, 1]
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(n > 0, tot / np.maximum(n, 1), np.nan)


def boot_rank_corr(x: np.ndarray, y: np.ndarray, dates: np.ndarray, **kw) -> BootResult:
    """Date-block CI for the Spearman IC (ranks taken once on the full cell sample)."""
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3:
        return BootResult(float("nan"), float("nan"), float("nan"), float("nan"), 0, 0)
    rx = rankdata(x[m])
    ry = rankdata(y[m])
    suff = np.column_stack([np.ones_like(rx), rx, ry, rx * ry, rx * rx, ry * ry])
    return block_bootstrap(suff, dates[m], _corr_reducer, **kw)


def boot_group_mean_diff(
    value: np.ndarray, group_hi: np.ndarray, dates: np.ndarray, **kw
) -> BootResult:
    """Date-block CI for ``mean(value | group_hi) - mean(value | ~group_hi)``."""
    m = np.isfinite(value) & np.isfinite(group_hi)
    v, g = value[m], group_hi[m].astype(float)
    if v.size < 3:
        return BootResult(float("nan"), float("nan"), float("nan"), float("nan"), 0, 0)
    suff = np.column_stack([g, g * v, 1.0 - g, (1.0 - g) * v])
    return block_bootstrap(suff, dates[m], _diff_reducer, **kw)


def boot_mean(value: np.ndarray, dates: np.ndarray, **kw) -> BootResult:
    """Date-block CI for a (paired-difference) mean."""
    m = np.isfinite(value)
    v = value[m]
    if v.size < 3:
        return BootResult(float("nan"), float("nan"), float("nan"), float("nan"), 0, 0)
    suff = np.column_stack([np.ones_like(v), v])
    return block_bootstrap(suff, dates[m], _mean_reducer, **kw)


# ---------------------------------------------------- MDE + band labels ----


def mde_ic(n_dates: int) -> float:
    """Design §6.5: MDE(Spearman IC) ~ 1.5/sqrt(n_eff), n_eff ~ unique dates."""
    return float("inf") if n_dates <= 0 else MDE_IC_CONST / np.sqrt(n_dates)


def mde_from_se(se: float) -> float:
    """MDE at 80% power / 5% two-sided = (1.96 + 0.84) * SE."""
    return float("nan") if not np.isfinite(se) else 2.8 * se


def band_ic(ic: float, ci_low: float, ci_high: float, n_dates: int) -> str:
    """Design §6.3 V-LEVEL band label. Labels never gate."""
    if n_dates < MIN_EFFECTIVE_DATES or mde_ic(n_dates) > MDE_IC_CEILING:
        return "UNPOWERED"
    if not np.isfinite(ic):
        return "UNPOWERED"
    if ic >= BAND_IC_SUPPORTED and np.isfinite(ci_low) and ci_low > 0:
        return "SUPPORTED"
    if ic <= BAND_IC_CONTRADICTED and np.isfinite(ci_high) and ci_high < 0:
        return "CONTRADICTED"
    if abs(ic) < BAND_IC_WASH_ABS:
        return "WASH"
    if abs(ic) < BAND_IC_SUPPORTED and np.isfinite(ci_low) and np.isfinite(ci_high) and (
        ci_low <= 0 <= ci_high
    ):
        return "WASH"
    return "INDETERMINATE"


def band_ic_detected(ic: float, ci_low: float, ci_high: float, n_dates: int) -> str:
    """DISCLOSURE companion to :func:`band_ic` (never replaces it).

    The design's UNPOWERED clause fires on the PROSPECTIVE MDE (>0.10), which the realised
    DESIGN sample cannot clear because the catalog's trailing 4-year history cap leaves
    ~100 unique dates. This variant keeps every other threshold and calls a cell UNPOWERED
    only when the observed effect is genuinely below its own detection floor. Both labels are
    emitted side by side; the design label is the one that counts.
    """
    if n_dates < MIN_EFFECTIVE_DATES or not np.isfinite(ic):
        return "UNPOWERED"
    if abs(ic) <= mde_ic(n_dates) and not (
        np.isfinite(ci_low) and np.isfinite(ci_high) and (ci_low > 0 or ci_high < 0)
    ):
        return "UNPOWERED"
    if ic >= BAND_IC_SUPPORTED and np.isfinite(ci_low) and ci_low > 0:
        return "SUPPORTED"
    if ic <= BAND_IC_CONTRADICTED and np.isfinite(ci_high) and ci_high < 0:
        return "CONTRADICTED"
    if abs(ic) < BAND_IC_WASH_ABS:
        return "WASH"
    if abs(ic) < BAND_IC_SUPPORTED and np.isfinite(ci_low) and np.isfinite(ci_high) and (
        ci_low <= 0 <= ci_high
    ):
        return "WASH"
    return "INDETERMINATE"


def band_gap(gap: float, ci_low: float, ci_high: float, n_dates: int, se: float) -> str:
    """Design §6.3 V-REGIME magnitude-gap band label (bps). Labels never gate."""
    mde = mde_from_se(se)
    if n_dates < MIN_EFFECTIVE_DATES or (np.isfinite(mde) and mde > MDE_GAP_CEILING_BPS):
        return "UNPOWERED"
    if not np.isfinite(gap):
        return "UNPOWERED"
    if gap >= BAND_GAP_SUPPORTED_BPS and np.isfinite(ci_low) and ci_low > 0:
        return "SUPPORTED"
    if gap <= BAND_GAP_CONTRADICTED_BPS and np.isfinite(ci_high) and ci_high < 0:
        return "CONTRADICTED"
    if abs(gap) < BAND_GAP_WASH_BPS:
        return "WASH"
    return "INDETERMINATE"


def band_gap_detected(gap: float, ci_low: float, ci_high: float, n_dates: int, se: float) -> str:
    """DISCLOSURE companion to :func:`band_gap` (never replaces it) — see band_ic_detected."""
    mde = mde_from_se(se)
    if n_dates < MIN_EFFECTIVE_DATES or not np.isfinite(gap):
        return "UNPOWERED"
    if np.isfinite(mde) and abs(gap) <= mde and not (
        np.isfinite(ci_low) and np.isfinite(ci_high) and (ci_low > 0 or ci_high < 0)
    ):
        return "UNPOWERED"
    if gap >= BAND_GAP_SUPPORTED_BPS and np.isfinite(ci_low) and ci_low > 0:
        return "SUPPORTED"
    if gap <= BAND_GAP_CONTRADICTED_BPS and np.isfinite(ci_high) and ci_high < 0:
        return "CONTRADICTED"
    if abs(gap) < BAND_GAP_WASH_BPS:
        return "WASH"
    return "INDETERMINATE"
