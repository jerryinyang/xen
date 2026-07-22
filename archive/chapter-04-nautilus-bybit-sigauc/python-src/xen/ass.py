"""Adaptive Signal Scoring (``ASS``) qualifier — the CF-CAPGEO-001 estimator core.

Implements the frozen ``ASS`` pipeline (Phase 017 D0 §D3 / ``ass.md``):

1. **Adaptive kNN-bandwidth KDE** — a sample-point (Abramson-style) variable-bandwidth
   Gaussian KDE whose per-point bandwidth is the distance from each datum to its
   ``k_bw = max(5, round(sqrt(n)))``-th nearest neighbour (widens in sparse regions,
   narrows in dense). This is the single bandwidth method (no balloon estimator).
2. **Empirical-Bayes shrinkage** — each signal type's estimate is blended toward the
   pooled (all-types) estimate with ``weight = n / (n + k)``, ``k`` defaulting to the
   median sample size across types. ``shrink=False`` exposes the un-pooled estimator.
3. **Bootstrap CI** — within-type iid resample (synthetic data), ``N_BOOT = 10_000``,
   5th/95th percentile. (The real-data moving-block variant is EXP-077, not here.)

Scoring outputs, none collapsed (D3): expectancy in **both** the KDE-integrated form
(``int x * pdf_tilde(x) dx``) and the algebraically-equivalent direct weighted-mean form
(``ass.md`` step 4 endorses the latter as simpler), median, ``P(return > X)``, and the
diagnostic shrinkage weight.

Design note on the three estimands. The expectancy/median/``P(>X)`` point estimates all
use the **direct shrinkage-weighted empirical** form, which is exact and mutually
consistent: un-pooled they reduce to ``mean(x)``, ``median(x)``, ``mean(x > X)``
respectively (the bite-check reference quantities). The adaptive KDE additionally yields
the KDE-integrated expectancy used as the EXP-076 R3 integrity anchor (its gap to the
direct mean bounds the smoothing/boundary distortion) and the density object reused by the
EXP-078 shape diagnostics. Returns are ATR-unit synthetic values here; in Phase 018 the
same machinery scores real-price ATR-normalised event returns.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import diptest
import numpy as np
from scipy import stats

# --------------------------------------------------------------------------- #
# Frozen configuration (Phase 017 D0 §D3 — no tuning without a D0-amendment)
# --------------------------------------------------------------------------- #
N_BOOT: int = 10_000                       # bootstrap resamples (programme convention)
CI_ALPHA: float = 0.10                     # 90% CI -> 5th / 95th percentile
DEFAULT_THRESHOLDS: tuple[float, ...] = (0.0, 0.05, 1.0, 2.0)  # X in {0, breakeven, 1R, 2R}
KNN_MIN: int = 5                           # bandwidth floor: k_bw = max(5, round(sqrt(n)))
GRID_SIZE: int = 2048                      # KDE evaluation grid resolution
GRID_PAD_MULT: float = 5.0                 # grid extends +/- this many max-bandwidths
BW_FLOOR_FRAC: float = 1e-6                # bandwidth floor as a fraction of the data span
BOOT_BATCH: int = 2_000                    # bounded bootstrap memory batch
_INV_SQRT_2PI: float = 1.0 / np.sqrt(2.0 * np.pi)


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class AssScore:
    """A single ``ASS`` scoring of one signal type's return sample.

    All return-scale fields are in the input units (ATR units in Phase 017). The two
    expectancy fields are algebraically equivalent (``ass.md`` step 4); a non-trivial gap
    indicates KDE smoothing/boundary distortion (the EXP-076 R3 diagnostic).
    """

    n: int
    k_bw: int
    shrink: bool
    weight: float                          # n / (n + k); 1.0 when shrink is False
    expectancy_direct: float               # weighted-mean form (primary; bite-check anchor)
    expectancy_kde: float                  # int x * pdf_tilde(x) dx (nan if not computed)
    median: float                          # shrinkage-weighted empirical median
    p_gt: dict[float, float] = field(default_factory=dict)  # X -> P(return > X)


@dataclass(frozen=True)
class AssCI:
    """Bootstrap 90% CIs (5th/95th percentile) for the expectancy and median."""

    expectancy_lo: float
    expectancy_hi: float
    median_lo: float
    median_hi: float


@dataclass(frozen=True)
class ShapeDiag:
    """Tail/bimodality diagnostic (Phase 017 D2.5) for one return sample.

    Computed on the **raw sample only** — independent of the shrinkage ``k``, the pooled
    prior, and the KDE (the gate inputs are the dip statistic, mean, median, and MAD of the
    raw data). The binding flag is ``flag = dip_flag OR gap_flag``:

    - ``dip_flag``  : Hartigan dip-test p-value ``dip_p < dip_alpha`` (bimodality leg).
    - ``gap_flag``  : robust mean-median gap ``|g| > tau_gap`` with ``g = (mean - median)/MAD``
      (left-tail asymmetry leg). ``False`` when ``MAD == 0`` (degenerate sample — the gap is
      undefined and the decision defers to the dip leg; ``mad_zero`` records the occurrence so
      the caller can count and assert it, never silently passing).

    The dip p-value is the analytic/interpolated Hartigan uniform-null value (``diptest``),
    so it is **deterministic given ``x``** (no RNG / seed).
    """

    n: int
    dip_stat: float
    dip_p: float
    mean: float
    median: float
    mad: float
    gap: float                 # g = (mean - median) / MAD; 0.0 when MAD == 0
    dip_flag: bool             # dip_p < dip_alpha
    gap_flag: bool             # |gap| > tau_gap (False when MAD == 0)
    flag: bool                 # dip_flag OR gap_flag (the binding bimodal/asymmetric flag)
    mad_zero: bool             # MAD == 0 (degenerate; gap deferred to the dip leg)


# --------------------------------------------------------------------------- #
# Pure computation — adaptive kNN-bandwidth Gaussian KDE (sample-point estimator)
# --------------------------------------------------------------------------- #
def knn_bandwidths(x: np.ndarray, k_bw: int) -> np.ndarray:
    """Per-point bandwidths = distance to the ``k_bw``-th nearest neighbour (1-D).

    For each datum the bandwidth is the distance to its ``k_bw``-th nearest neighbour
    among the other samples. Computed exactly on sorted data by minimising the width of
    every length-``k_bw`` contiguous window that contains the point (the k nearest
    neighbours of a 1-D point are always contiguous in sorted order). Bandwidths are
    floored at ``BW_FLOOR_FRAC`` of the data span so coincident points cannot yield a
    zero-width kernel.

    Parameters
    ----------
    x : np.ndarray
        1-D return sample (need not be sorted), ``len(x) >= 2``.
    k_bw : int
        Neighbour rank for the bandwidth (clamped to ``len(x) - 1``).

    Returns
    -------
    np.ndarray
        Bandwidth per input point, aligned to the *original* (unsorted) order.
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    if n < 2:
        raise ValueError(f"knn_bandwidths needs >= 2 points, got {n}")
    k = int(min(max(1, k_bw), n - 1))
    order = np.argsort(x, kind="stable")
    xs = x[order]
    # For sorted index i, the k-NN distance is the smallest max-edge over the k+1 windows
    # [i-k, i], ..., [i, i+k]; window [i-k+t, i+t] contributes max(xs[i]-left, right-xs[i]).
    best = np.full(n, np.inf, dtype=np.float64)
    for t in range(k + 1):
        left = np.arange(n) - k + t
        right = np.arange(n) + t
        valid = (left >= 0) & (right < n)
        if not valid.any():
            continue
        idx = np.where(valid)[0]
        width = np.maximum(xs[idx] - xs[left[idx]], xs[right[idx]] - xs[idx])
        best[idx] = np.minimum(best[idx], width)
    span = float(xs[-1] - xs[0])
    floor = BW_FLOOR_FRAC * span if span > 0 else BW_FLOOR_FRAC
    best = np.where(np.isfinite(best) & (best > floor), best, floor)
    out = np.empty(n, dtype=np.float64)
    out[order] = best
    return out


def make_grid(x: np.ndarray, bandwidths: np.ndarray, size: int = GRID_SIZE) -> np.ndarray:
    """Uniform KDE evaluation grid padded by ``GRID_PAD_MULT`` max-bandwidths."""
    pad = GRID_PAD_MULT * float(np.max(bandwidths))
    lo = float(np.min(x)) - pad
    hi = float(np.max(x)) + pad
    return np.linspace(lo, hi, size)


def adaptive_kde_pdf(
    x: np.ndarray,
    grid: np.ndarray,
    k_bw: int,
    sample_weights: np.ndarray | None = None,
) -> np.ndarray:
    """Evaluate the sample-point adaptive Gaussian KDE on ``grid``.

    ``pdf(g) = sum_i w_i * phi((g - x_i) / h_i) / h_i`` with ``w_i`` normalised to sum to
    one and ``h_i`` the kNN bandwidth of ``x_i``. Passing a pooled-sample concatenation via
    ``sample_weights`` yields the shrunk mixture density directly.

    Parameters
    ----------
    x : np.ndarray
        1-D sample the kernels are centred on.
    grid : np.ndarray
        Evaluation points.
    k_bw : int
        Neighbour rank for the per-point bandwidth.
    sample_weights : np.ndarray, optional
        Per-point mixture weights (default uniform ``1 / len(x)``).

    Returns
    -------
    np.ndarray
        Density values on ``grid`` (same length as ``grid``).
    """
    x = np.asarray(x, dtype=np.float64)
    h = knn_bandwidths(x, k_bw)
    if sample_weights is None:
        w = np.full(x.shape[0], 1.0 / x.shape[0], dtype=np.float64)
    else:
        w = np.asarray(sample_weights, dtype=np.float64)
        w = w / w.sum()
    z = (grid[:, None] - x[None, :]) / h[None, :]        # (grid, n)
    kern = _INV_SQRT_2PI * np.exp(-0.5 * z * z) / h[None, :]
    return kern @ w


def kde_expectancy(grid: np.ndarray, pdf: np.ndarray) -> float:
    """``int x * pdf(x) dx`` via the trapezoid rule, normalised by ``int pdf``."""
    mass = float(np.trapezoid(pdf, grid))
    num = float(np.trapezoid(grid * pdf, grid))
    return num / mass if mass > 0 else float("nan")


# --------------------------------------------------------------------------- #
# Pure computation — direct shrinkage-weighted empirical estimands
# --------------------------------------------------------------------------- #
def direct_expectancy(x: np.ndarray, pool: np.ndarray | None, weight: float) -> float:
    """``weight * mean(x) + (1 - weight) * mean(pool)`` (un-pooled: ``mean(x)``)."""
    mx = float(np.mean(x))
    if weight >= 1.0 or pool is None:
        return mx
    return weight * mx + (1.0 - weight) * float(np.mean(pool))


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    """Linear-interpolated weighted quantile ``q`` of ``values``."""
    order = np.argsort(values, kind="stable")
    v = values[order]
    w = weights[order]
    cum = np.cumsum(w) - 0.5 * w
    cum /= w.sum()
    return float(np.interp(q, cum, v))


def weighted_median(x: np.ndarray, pool: np.ndarray | None, weight: float) -> float:
    """Shrinkage-weighted empirical median (un-pooled: ``median(x)``)."""
    if weight >= 1.0 or pool is None:
        return float(np.median(x))
    values = np.concatenate([x, pool])
    weights = np.concatenate([
        np.full(x.shape[0], weight / x.shape[0]),
        np.full(pool.shape[0], (1.0 - weight) / pool.shape[0]),
    ])
    return weighted_quantile(values, weights, 0.5)


def prob_gt(
    x: np.ndarray, thresholds: tuple[float, ...], pool: np.ndarray | None, weight: float,
) -> dict[float, float]:
    """Shrinkage-weighted ``P(return > X)`` per threshold (``ass.md`` §A.2)."""
    out: dict[float, float] = {}
    for thr in thresholds:
        px = float(np.mean(x > thr))
        if weight >= 1.0 or pool is None:
            out[thr] = px
        else:
            out[thr] = weight * px + (1.0 - weight) * float(np.mean(pool > thr))
    return out


# --------------------------------------------------------------------------- #
# Pure computation — shape / tail-bimodality diagnostic (Phase 017 D2.5; EXP-078)
# --------------------------------------------------------------------------- #
DIP_ALPHA: float = 0.05                    # Hartigan dip-test significance (bimodality leg)
TAU_GAP: float = 0.30                      # |mean-median|/MAD threshold (asymmetry leg; D2.5)


def shape_diagnostic(
    x: np.ndarray, *, tau_gap: float = TAU_GAP, dip_alpha: float = DIP_ALPHA,
) -> ShapeDiag:
    """Frozen D2.5 tail/bimodality diagnostic on a raw return sample.

    ``flag = (dip_p < dip_alpha) OR (|g| > tau_gap)`` with ``g = (mean - median) / MAD``
    (``MAD = median_abs_deviation(x, scale=1.0)``). Computed on the **raw sample only** — it
    does not read the shrinkage ``k``, the pooled prior, or the KDE, so it is invariant to the
    ``ASS`` shrinkage knob by construction (the EXP-078 ``k``-sensitivity sweep therefore acts
    only on the ``k``-dependent point/edge machinery, never on this flag).

    Parameters
    ----------
    x : np.ndarray
        1-D return sample, ``len(x) >= 4`` (the dip test needs at least four points).
    tau_gap : float
        Robust mean-median gap threshold (frozen D2.5 operating point ``0.30``).
    dip_alpha : float
        Hartigan dip-test p-value cutoff (frozen ``0.05``).

    Returns
    -------
    ShapeDiag
        The per-leg and combined flags plus the raw diagnostic quantities. ``mad_zero`` is
        ``True`` for a degenerate (``MAD == 0``) sample, where the gap leg is undefined and the
        decision defers to the dip leg; callers should count and assert ``mad_zero`` rather than
        let a degenerate sample pass silently.
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    if n < 4:
        raise ValueError(f"shape_diagnostic needs >= 4 points, got {n}")
    dip_stat, dip_p = diptest.diptest(x)             # analytic Hartigan p-value (deterministic)
    mean = float(np.mean(x))
    median = float(np.median(x))
    mad = float(stats.median_abs_deviation(x, scale=1.0))
    if mad == 0.0:
        gap, gap_flag, mad_zero = 0.0, False, True   # undefined -> defer to dip leg, record it
    else:
        gap = (mean - median) / mad
        gap_flag = bool(abs(gap) > tau_gap)
        mad_zero = False
    dip_flag = bool(dip_p < dip_alpha)
    return ShapeDiag(
        n=n, dip_stat=float(dip_stat), dip_p=float(dip_p), mean=mean, median=median, mad=mad,
        gap=float(gap), dip_flag=dip_flag, gap_flag=gap_flag,
        flag=bool(dip_flag or gap_flag), mad_zero=mad_zero,
    )


# --------------------------------------------------------------------------- #
# Orchestrated scoring
# --------------------------------------------------------------------------- #
def default_k_bw(n: int) -> int:
    """Frozen adaptive bandwidth rank ``k_bw = max(5, round(sqrt(n)))``."""
    return max(KNN_MIN, int(round(np.sqrt(n))))


def shrinkage_weight(n: int, k: float) -> float:
    """Empirical-Bayes blend weight ``n / (n + k)``."""
    return float(n) / (float(n) + float(k))


def score(
    x: np.ndarray,
    *,
    shrink: bool = False,
    pool: np.ndarray | None = None,
    k_shrink: float | None = None,
    thresholds: tuple[float, ...] = DEFAULT_THRESHOLDS,
    compute_kde_expectancy: bool = False,
) -> AssScore:
    """Score one return sample with the ``ASS`` pipeline.

    Parameters
    ----------
    x : np.ndarray
        1-D return sample for this signal type.
    shrink : bool
        Enable empirical-Bayes shrinkage toward ``pool`` (requires ``pool`` and
        ``k_shrink``). ``False`` is the un-pooled estimator core used by the EXP-076
        recovery legs (R1).
    pool : np.ndarray, optional
        Pooled (all-types) return sample — the shrinkage prior.
    k_shrink : float, optional
        Shrinkage constant ``k`` (default = median sample size across types).
    thresholds : tuple[float, ...]
        ``X`` values for ``P(return > X)``.
    compute_kde_expectancy : bool
        If ``True``, also build the adaptive KDE and integrate ``int x * pdf_tilde(x) dx``
        (the R3 anchor diagnostic). Off by default — the recovery/coverage loops use only
        the exact direct forms.

    Returns
    -------
    AssScore
        Point estimates and the diagnostic shrinkage weight.
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    if n < 2:
        raise ValueError(f"score needs >= 2 points, got {n}")
    k_bw = default_k_bw(n)
    if shrink:
        if pool is None or k_shrink is None:
            raise ValueError("shrink=True requires both pool and k_shrink")
        weight = shrinkage_weight(n, k_shrink)
    else:
        weight = 1.0

    exp_direct = direct_expectancy(x, pool, weight)
    med = weighted_median(x, pool, weight)
    pg = prob_gt(x, thresholds, pool, weight)

    exp_kde = float("nan")
    if compute_kde_expectancy:
        if shrink and pool is not None:
            xc = np.concatenate([x, pool])
            sw = np.concatenate([
                np.full(n, weight / n),
                np.full(pool.shape[0], (1.0 - weight) / pool.shape[0]),
            ])
            grid = make_grid(xc, knn_bandwidths(xc, default_k_bw(xc.shape[0])))
            pdf = adaptive_kde_pdf(xc, grid, default_k_bw(xc.shape[0]), sample_weights=sw)
        else:
            grid = make_grid(x, knn_bandwidths(x, k_bw))
            pdf = adaptive_kde_pdf(x, grid, k_bw)
        exp_kde = kde_expectancy(grid, pdf)

    return AssScore(
        n=n, k_bw=k_bw, shrink=shrink, weight=weight,
        expectancy_direct=exp_direct, expectancy_kde=exp_kde, median=med, p_gt=pg,
    )


# --------------------------------------------------------------------------- #
# Pure computation — within-type iid bootstrap CIs (synthetic data)
# --------------------------------------------------------------------------- #
def bootstrap_cis(
    x: np.ndarray,
    rng: np.random.Generator,
    *,
    n_boot: int = N_BOOT,
    alpha: float = CI_ALPHA,
    batch: int = BOOT_BATCH,
    pool_mean: float | None = None,
    weight: float = 1.0,
) -> AssCI:
    """Within-type iid percentile-bootstrap CIs for the expectancy and median.

    Resamples ``x`` with replacement (size-``n``) ``n_boot`` times and recomputes the
    direct expectancy and empirical median on each resample, taking the 5th/95th
    percentiles. Expectancy and median are read from the **same** gathered resample to
    avoid a second pass. Memory is bounded by ``batch``; randomness is fully determined by
    ``rng``.

    For the un-pooled recovery legs (R1) pass ``weight = 1.0``. When ``weight < 1.0`` the
    fixed ``pool_mean`` shifts each resample expectancy as
    ``weight * resample_mean + (1 - weight) * pool_mean`` (the median resample stays the
    within-type empirical median; the shrunk median CI is not used by EXP-076).

    Returns
    -------
    AssCI
        90% CI bounds for the expectancy and median.
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    exp_boot = np.empty(n_boot, dtype=np.float64)
    med_boot = np.empty(n_boot, dtype=np.float64)
    done = 0
    while done < n_boot:
        b = min(batch, n_boot - done)
        idx = rng.integers(0, n, size=(b, n))
        g = x[idx]                                        # (b, n)
        means = g.mean(axis=1)
        if weight < 1.0 and pool_mean is not None:
            means = weight * means + (1.0 - weight) * pool_mean
        exp_boot[done:done + b] = means
        med_boot[done:done + b] = np.median(g, axis=1)
        done += b
    lo_pct = 100.0 * alpha / 2.0
    hi_pct = 100.0 * (1.0 - alpha / 2.0)
    return AssCI(
        expectancy_lo=float(np.percentile(exp_boot, lo_pct)),
        expectancy_hi=float(np.percentile(exp_boot, hi_pct)),
        median_lo=float(np.percentile(med_boot, lo_pct)),
        median_hi=float(np.percentile(med_boot, hi_pct)),
    )


def default_block_length(n: int) -> int:
    """Moving-block length ``b = round(n ** (1/3))`` (programme convention), floored at 1."""
    return max(1, int(round(float(n) ** (1.0 / 3.0))))


def moving_block_bootstrap_cis(
    x: np.ndarray,
    rng: np.random.Generator,
    *,
    n_boot: int = N_BOOT,
    alpha: float = CI_ALPHA,
    block: int | None = None,
    batch: int = BOOT_BATCH,
    pool_mean: float | None = None,
    weight: float = 1.0,
) -> AssCI:
    """Moving-block percentile-bootstrap CIs that preserve serial dependence.

    The real-data variant reserved by this module's docstring (EXP-077). Instead of the
    iid within-type resample, it resamples overlapping length-``b`` blocks (``b`` defaulting
    to ``round(n**(1/3))``, the programme convention) and concatenates ``ceil(n / b)`` of them
    to a length-``n`` series, so within-series autocorrelation up to ~``b`` lags is retained.
    Expectancy and median are read from the **same** gathered resample. Memory is bounded by
    ``batch``; randomness is fully determined by ``rng``. When ``weight < 1.0`` the fixed
    ``pool_mean`` shifts each resample expectancy (shrinkage), mirroring :func:`bootstrap_cis`.

    Parameters
    ----------
    x : np.ndarray
        1-D ordered return sample (chronological — block resampling assumes serial order).
    rng : np.random.Generator
        Seeded generator (determinism).
    n_boot, alpha, batch :
        Resample count, CI level (90% -> 5th/95th pct), and memory batch size.
    block : int, optional
        Block length ``b`` (default ``round(n**(1/3))``, floored at 1).
    pool_mean, weight :
        Optional shrinkage shift (un-pooled when ``weight >= 1.0``).

    Returns
    -------
    AssCI
        90% CI bounds for the expectancy and median.
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    if n < 2:
        raise ValueError(f"moving_block_bootstrap_cis needs >= 2 points, got {n}")
    b = int(block) if block is not None else default_block_length(n)
    b = int(min(max(1, b), n))
    n_starts = n - b + 1                       # number of valid block start positions
    n_blocks = int(np.ceil(n / b))             # blocks per resample (trimmed to n)
    exp_boot = np.empty(n_boot, dtype=np.float64)
    med_boot = np.empty(n_boot, dtype=np.float64)
    done = 0
    while done < n_boot:
        bs = min(batch, n_boot - done)
        starts = rng.integers(0, n_starts, size=(bs, n_blocks))        # (bs, n_blocks)
        # offsets within each block -> (bs, n_blocks, b); flatten and trim to n
        idx = starts[:, :, None] + np.arange(b)[None, None, :]
        idx = idx.reshape(bs, n_blocks * b)[:, :n]                     # (bs, n)
        g = x[idx]
        means = g.mean(axis=1)
        if weight < 1.0 and pool_mean is not None:
            means = weight * means + (1.0 - weight) * pool_mean
        exp_boot[done:done + bs] = means
        med_boot[done:done + bs] = np.median(g, axis=1)
        done += bs
    lo_pct = 100.0 * alpha / 2.0
    hi_pct = 100.0 * (1.0 - alpha / 2.0)
    return AssCI(
        expectancy_lo=float(np.percentile(exp_boot, lo_pct)),
        expectancy_hi=float(np.percentile(exp_boot, hi_pct)),
        median_lo=float(np.percentile(med_boot, lo_pct)),
        median_hi=float(np.percentile(med_boot, hi_pct)),
    )
