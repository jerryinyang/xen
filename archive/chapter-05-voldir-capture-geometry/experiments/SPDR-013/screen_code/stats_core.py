"""Inference: circular date-block bootstrap on episode entry dates + §7.2 expectancy bands.

Bootstrap machinery is the SPDR-012 sufficient-statistic engine (block >= H dependence match; the
CI is the min/max ENVELOPE over 3 block lengths x 5 seeds, never a single 95% interval — L-20).
Here the estimand is a plain mean (expectancy_partial in bps) resampled over unique UTC entry dates.
Bands are LABELS, never gates (§7.2).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from config import (
    BAND_CONTRADICTED_BPS,
    BAND_SUPPORTED_BPS,
    BAND_WASH_ABS_BPS,
    BOOT_BLOCKS,
    BOOT_CI_ALPHA,
    BOOT_RESAMPLES,
    BOOT_SEEDS,
    THIRDS_SIGN_MIN,
    UNPOWERED_MDE_CEILING_BPS,
    UNPOWERED_MIN_DATES,
    UNPOWERED_MIN_EPISODES,
)

_CHUNK = 1000


@dataclass
class BootResult:
    point: float
    ci_low: float           # min over grid — conservative envelope, not a 95% CI
    ci_high: float          # max over grid
    se: float               # MAX bootstrap SD over grid (drives MDE)
    n_dates: int
    n_obs: int
    grid: list[dict] = field(default_factory=list)
    se_median: float = float("nan")

    def to_dict(self) -> dict:
        return {
            "point": self.point, "ci_low": self.ci_low, "ci_high": self.ci_high,
            "se_max": self.se, "se_median": self.se_median,
            "n_dates": self.n_dates, "n_obs": self.n_obs,
            "envelope_note": "ci_low/ci_high = min/max over 3 blocks x 5 seeds (envelope, §7.1)",
            "block_sensitivity": self.grid,
        }


def _date_index(dates: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    uniq, inv = np.unique(dates, return_inverse=True)
    return uniq, inv


def _accumulate(suff: np.ndarray, inv: np.ndarray, nd: int) -> np.ndarray:
    out = np.zeros((nd, suff.shape[1]))
    for j in range(suff.shape[1]):
        out[:, j] = np.bincount(inv, weights=suff[:, j], minlength=nd)
    return out


def _mean_reducer(s: np.ndarray) -> np.ndarray:
    n, tot = s[:, 0], s[:, 1]
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(n > 0, tot / np.maximum(n, 1), np.nan)


def block_bootstrap(
    suff: np.ndarray, dates: np.ndarray, reducer: Callable[[np.ndarray], np.ndarray], *,
    blocks: tuple[int, ...] = BOOT_BLOCKS, seeds: tuple[int, ...] = BOOT_SEEDS,
    n_resample: int = BOOT_RESAMPLES, alpha: float = BOOT_CI_ALPHA,
) -> BootResult:
    """Circular date-block bootstrap of a sufficient-statistic functional (envelope over grid)."""
    nan = float("nan")
    if suff.size == 0:
        return BootResult(nan, nan, nan, nan, 0, 0)
    uniq, inv = _date_index(dates)
    nd = uniq.size
    per_date = _accumulate(suff, inv, nd)
    point = float(reducer(per_date.sum(axis=0)[None, :])[0])
    if nd < 3:
        return BootResult(point, nan, nan, nan, nd, int(suff.shape[0]))
    grid, lows, highs, sds = [], [], [], []
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
                stats[done: done + b] = reducer(sums)
                done += b
            finite = stats[np.isfinite(stats)]
            if finite.size < 10:
                continue
            lo = float(np.quantile(finite, alpha / 2))
            hi = float(np.quantile(finite, 1 - alpha / 2))
            sd = float(finite.std())
            grid.append({"block": L, "seed": seed, "ci_low": lo, "ci_high": hi, "sd": sd})
            lows.append(lo); highs.append(hi); sds.append(sd)
    if not grid:
        return BootResult(point, nan, nan, nan, nd, int(suff.shape[0]))
    return BootResult(point, float(min(lows)), float(max(highs)), float(max(sds)),
                      nd, int(suff.shape[0]), grid, float(np.median(sds)))


def boot_mean(value: np.ndarray, dates: np.ndarray, **kw) -> BootResult:
    """Date-block CI for a mean (expectancy_partial in bps)."""
    m = np.isfinite(value)
    v = value[m]
    if v.size < 3:
        return BootResult(float("nan"), float("nan"), float("nan"), float("nan"), 0, 0)
    suff = np.column_stack([np.ones_like(v), v])
    return block_bootstrap(suff, dates[m], _mean_reducer, **kw)


def mde_from_se(se: float) -> float:
    """MDE at 80% power / 5% two-sided = 2.8 * SE."""
    return float("nan") if not np.isfinite(se) else 2.8 * se


def band_expectancy(mean: float, ci_low: float, ci_high: float, n_episodes: int,
                    n_dates: int, se: float, thirds_sign: int = 3) -> str:
    """Design §7.2 expectancy_partial band label (bps). Labels NEVER gate.

    §7.1 eligibility: SUPPORTED additionally requires the expectancy sign to hold in
    ``>= THIRDS_SIGN_MIN`` of the 3 DESIGN thirds; a would-be SUPPORTED cell that fails that
    stability test is demoted to INDETERMINATE (not silently kept SUPPORTED).
    """
    mde = mde_from_se(se)
    if (n_episodes < UNPOWERED_MIN_EPISODES or n_dates < UNPOWERED_MIN_DATES
            or (np.isfinite(mde) and mde > UNPOWERED_MDE_CEILING_BPS) or not np.isfinite(mean)):
        return "UNPOWERED"
    if mean >= BAND_SUPPORTED_BPS and np.isfinite(ci_low) and ci_low > 0:
        return "SUPPORTED" if thirds_sign >= THIRDS_SIGN_MIN else "INDETERMINATE"
    if mean <= BAND_CONTRADICTED_BPS and np.isfinite(ci_high) and ci_high < 0:
        return "CONTRADICTED"
    if abs(mean) < BAND_WASH_ABS_BPS:
        return "WASH"
    return "INDETERMINATE"
