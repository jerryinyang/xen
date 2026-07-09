"""Multiplicity-adjusted permuted-axis admission gate (Phase 019 D2b; EXP-086/087/088).

The binding family-selection gate, calibrated GREEN by the Phase 019 bite-check
(`…/2026-06-22-019-family-selection-availability-screen/bite-check/bite_check.py`). It decides, per
information **axis**, whether a conditioned availability read beats a matched random control by more
than a multiplicity-adjusted permuted-axis null would at the realized cell count — never a tradability
claim. The machinery (faithful production generalization of the bite-check):

1. **Per-cell beats-random test** — for a read metric ``θ`` with cell estimate
   ``Δ̂ = θ(conditioned) − θ(matched-random)`` and a **once-per-cell** standard error ``s_cell``
   (moving-block bootstrap on the conditioned series + iid bootstrap on the random control), the cell
   "beats random" iff its one-sided lower bound ``Δ̂ − Z·s_cell > 0`` (``Z = 1.645``). ``s_cell`` is
   held fixed across permutations exactly as the bite-check holds ``se`` fixed.
2. **Axis statistic** — ``S = #cells-beat-random`` over the powered cells.
3. **Permuted-axis null** — shuffle which timestamps are "signal": per permutation, per cell, draw a
   fresh ``n_cond``-sized pseudo-signal subsample from that cell's precomputed random-timing pool
   (preserving per-cell counts + the regime/direction match), recompute ``Δ̂`` and the beats flag with
   the **same fixed** ``s_cell``; ``S_perm = Σ_cells beats``. No per-permutation path scan, no nested
   bootstrap.
4. **Within-axis multiplicity (max-statistic)** — Screen M runs 4 sub-screens
   ``{2 primitives} × {typical-range, tail}``; the axis statistic is ``S_M = max_sub S`` and the joint
   null is ``S_perm_max = max_sub S_perm`` (same permutation index across sub-screens), controlling the
   "screen-many-keep-the-best" risk. ``S* = Q(1−FWER)(S_perm_max)``; ``ADMITTED`` iff ``S_M > S*`` AND
   the axis permutation p ``≤ FWER``.
5. **Cross-axis Holm** — applied over the {M, X, (F)} axis permutation p-values **at G-019**, not here.

Deterministic given the seed stream. Real-price discipline is the caller's responsibility (this module
operates on already-computed per-event metric arrays).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from xen.ass import default_block_length

# --------------------------------------------------------------------------- #
# Frozen gate constants (GREEN bite-check; never tuned)
# --------------------------------------------------------------------------- #
Z_ONE_SIDED: float = 1.645         # one-sided 95% normal quantile (per-cell CI_low>0 test)
FWER: float = 0.05                 # axis-level family-wise error rate
FWER_BAND: tuple[float, ...] = (0.025, 0.05, 0.10)   # pre-registered sensitivity sweep
N_PERM: int = 5000                 # production permutations
N_PERM_STABILITY: int = 1000       # MC-stability cross-check scale
B_SE: int = 2000                   # bootstrap resamples for the once-per-cell SE
PERM_BATCH: int = 500              # permutation batch (memory bound)
EVENT_FLOOR_DEFAULT: int = 30      # usable-event floor; below -> underpowered (excluded from S)

STAT_MEDIAN = "median"             # typical-range read statistic
STAT_TAILMASS = "tailmass"         # lower-catastrophe tail read statistic (median − K_TAIL·MAD)
K_TAIL: float = 3.0                # catastrophe boundary median − K_TAIL·MAD (matches capgeo_geometry)

# Additive upper-favourable-tail read for availability screens whose outcome is a *favourable*
# excursion (higher is better), e.g. CF-MR-003/EXP-008 reversion excursion toward the anchor. This
# is the design §5 endpoint (S) ``#{θ >= TAU_UPPER}/n``. Additive only — existing STAT_MEDIAN /
# STAT_TAILMASS callers are byte-unchanged; no frozen gate constant (Z/FWER/N_PERM/…) is touched.
STAT_TAILMASS_UPPER = "tailmass_upper"
TAU_UPPER: float = 1.0             # upper-tail threshold in the metric's units (ATR for EXP-008)

# Additive mean read for a binary/rate endpoint (e.g. CF-MR-003/EXP-009 anchor-hit rate = mean of a
# 0/1 hit indicator). Additive only — existing stat_kinds byte-unchanged; no frozen gate constant touched.
STAT_MEAN = "mean"


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CellReadInput:
    """Per (cell, sub-screen) gate inputs — already on real prices, ATR units."""

    cell_id: str                   # e.g. "EURUSD-1h"
    cond_values: np.ndarray        # conditioned per-event metric (range_sym or signed_outcome)
    ctrl_values: np.ndarray        # matched-random per-event metric (count == n_cond)
    pool_values: np.ndarray        # large random-timing pool per-event metric
    n_cond: int
    underpowered: bool             # n_cond usable < EVENT_FLOOR -> excluded from S


@dataclass(frozen=True)
class CellReadResult:
    """Per-cell realized read result."""

    cell_id: str
    theta_cond: float
    theta_ctrl: float
    delta_hat: float
    s_cell: float
    ci_low: float
    beats_random: bool
    n_cond: int
    underpowered: bool


@dataclass(frozen=True)
class SubScreenResult:
    """One sub-screen (primitive × read): realized S, permuted null, transparency stats."""

    primitive: str
    read: str
    stat_kind: str
    s_realized: int
    s_star: int                    # Q(1−FWER) of this sub-screen's own permuted null
    perm_p: float
    n_powered_cells: int
    cells: list[CellReadResult]
    s_perm: np.ndarray             # per-permutation S (length N_PERM), for the joint max


@dataclass(frozen=True)
class AxisResult:
    """Axis-level (max-statistic) admission result. Provisional — G-019 applies cross-axis Holm."""

    axis: str
    s_m: int
    s_star: int                    # Q(1−FWER) of the joint S_perm_max
    perm_p: float                  # axis permutation p of the max statistic
    rank_z: float                  # (S_M − mean(S_perm_max)) / sd(S_perm_max)
    driving_sub: str               # "<primitive>/<read>" attaining S_M (tie -> first by SUB order)
    fwer_band: dict                # {fwer: {"s_star": int, "admitted": bool}}
    mc_stability: dict             # {"s_star_1000": int, "perm_p_1000": float, ...}
    disposition: str               # provisional ADMITTED / EXONERATED / INCONCLUSIVE (NON-BINDING)
    s_perm_max: np.ndarray


# --------------------------------------------------------------------------- #
# Pure computation — vectorized read statistics over a 2-D resample matrix
# --------------------------------------------------------------------------- #
def _stat_1d(values: np.ndarray, stat_kind: str) -> float:
    """Realized read statistic on a 1-D sample (median or tailmass)."""
    x = np.asarray(values, dtype=np.float64)
    if x.shape[0] == 0:
        return float("nan")
    if stat_kind == STAT_MEDIAN:
        return float(np.median(x))
    if stat_kind == STAT_MEAN:
        return float(np.mean(x))
    if stat_kind == STAT_TAILMASS_UPPER:
        return float(np.count_nonzero(x >= TAU_UPPER)) / x.shape[0]
    med = float(np.median(x))
    mad = float(np.median(np.abs(x - med)))           # scale=1.0 (matches capgeo_geometry.tail_stats)
    boundary = med - K_TAIL * mad
    return float(np.count_nonzero(x < boundary)) / x.shape[0]


def _stat_2d(mat: np.ndarray, stat_kind: str) -> np.ndarray:
    """Vectorized read statistic per row of a ``(rows, n)`` resample matrix."""
    if stat_kind == STAT_MEDIAN:
        return np.median(mat, axis=1)
    if stat_kind == STAT_MEAN:
        return mat.mean(axis=1)
    if stat_kind == STAT_TAILMASS_UPPER:
        return (mat >= TAU_UPPER).mean(axis=1)
    med = np.median(mat, axis=1)
    mad = np.median(np.abs(mat - med[:, None]), axis=1)
    boundary = med - K_TAIL * mad
    return (mat < boundary[:, None]).mean(axis=1)


# --------------------------------------------------------------------------- #
# Pure computation — once-per-cell SE of Δ̂ (block bootstrap cond + iid bootstrap ctrl)
# --------------------------------------------------------------------------- #
def _moving_block_resamples(x: np.ndarray, n_boot: int, rng: np.random.Generator) -> np.ndarray:
    """``(n_boot, n)`` moving-block bootstrap resample matrix (preserves serial dependence)."""
    n = x.shape[0]
    b = int(min(max(1, default_block_length(n)), n))
    n_starts = n - b + 1
    n_blocks = int(np.ceil(n / b))
    starts = rng.integers(0, n_starts, size=(n_boot, n_blocks))        # block start positions
    offs = np.arange(b)
    idx = (starts[:, :, None] + offs[None, None, :]).reshape(n_boot, n_blocks * b)[:, :n]
    return x[idx]


def cell_se(cond: np.ndarray, ctrl: np.ndarray, stat_kind: str,
            rng: np.random.Generator, n_boot: int = B_SE) -> float:
    """Once-per-cell SE of ``Δ̂ = θ(cond) − θ(ctrl)`` (block-bootstrap cond, iid-bootstrap ctrl).

    The conditioned series is moving-block resampled (compression events cluster in time → preserve
    autocorrelation, conservative under positive dependence); the random control is iid-resampled (its
    timing is random → no autocorrelation). Generalizes the bite-check's independence-assuming
    ``σ/√n``.
    """
    cond = np.asarray(cond, dtype=np.float64)
    ctrl = np.asarray(ctrl, dtype=np.float64)
    if cond.shape[0] < 2 or ctrl.shape[0] < 2:
        return float("nan")
    cond_rs = _moving_block_resamples(cond, n_boot, rng)
    ctrl_idx = rng.integers(0, ctrl.shape[0], size=(n_boot, ctrl.shape[0]))
    ctrl_rs = ctrl[ctrl_idx]
    delta = _stat_2d(cond_rs, stat_kind) - _stat_2d(ctrl_rs, stat_kind)
    return float(np.std(delta, ddof=1))


# --------------------------------------------------------------------------- #
# Pure computation — realized per-cell beats-random + permuted null per sub-screen
# --------------------------------------------------------------------------- #
def _perm_beats(pool: np.ndarray, theta_ctrl: float, s_cell: float, n_cond: int,
                stat_kind: str, n_perm: int, rng: np.random.Generator,
                batch: int = PERM_BATCH) -> np.ndarray:
    """Per-permutation beats-random booleans for one cell (subsample pool → Δ̂_perm − Z·s_cell > 0).

    The pseudo-signal is an ``n_cond``-sized **with-replacement** subsample of the cell's random-timing
    pool (a large representative random-timing sample), drawn fully vectorized per batch.
    With-replacement is a deliberate performance choice — it makes the permutation stream fully
    vectorized/deterministic; the ~10% within-draw repeats it induces are statistically immaterial for
    a null calibration, and the self-calibrating gate (bite §C) absorbs any residual per-cell test
    variation. ``s_cell`` is the fixed once-per-cell SE (exactly as the bite-check holds ``se`` fixed
    and varies the permuted mean).
    """
    out = np.zeros(n_perm, dtype=bool)
    if pool.shape[0] < 1 or n_cond < 1 or not np.isfinite(s_cell):
        return out
    done = 0
    while done < n_perm:
        k = int(min(batch, n_perm - done))
        idx = rng.integers(0, pool.shape[0], size=(k, n_cond))     # vectorized with-replacement draw
        theta_pseudo = _stat_2d(pool[idx], stat_kind)
        out[done:done + k] = (theta_pseudo - theta_ctrl - Z_ONE_SIDED * s_cell) > 0.0
        done += k
    return out


def run_sub_screen(primitive: str, read: str, stat_kind: str, cells: list[CellReadInput],
                   rng: np.random.Generator, n_perm: int = N_PERM) -> SubScreenResult:
    """Realized per-cell beats-random + the permuted-axis S null for one sub-screen.

    Underpowered cells are excluded from the S count (recorded). Returns the realized S, this
    sub-screen's own ``S*``/perm-p (transparency), and the per-permutation ``S_perm`` for the joint
    max.
    """
    results: list[CellReadResult] = []
    s_perm = np.zeros(n_perm, dtype=np.int64)
    n_powered = 0
    for c in cells:
        theta_cond = _stat_1d(c.cond_values, stat_kind)
        theta_ctrl = _stat_1d(c.ctrl_values, stat_kind)
        delta_hat = theta_cond - theta_ctrl
        s_cell = cell_se(c.cond_values, c.ctrl_values, stat_kind, rng)
        ci_low = delta_hat - Z_ONE_SIDED * s_cell if np.isfinite(s_cell) else float("nan")
        beats = bool(np.isfinite(ci_low) and ci_low > 0.0 and not c.underpowered)
        results.append(CellReadResult(
            cell_id=c.cell_id, theta_cond=theta_cond, theta_ctrl=theta_ctrl,
            delta_hat=delta_hat, s_cell=s_cell, ci_low=ci_low, beats_random=beats,
            n_cond=c.n_cond, underpowered=c.underpowered))
        if c.underpowered:
            continue
        n_powered += 1
        s_perm += _perm_beats(c.pool_values, theta_ctrl, s_cell, c.n_cond,
                              stat_kind, n_perm, rng).astype(np.int64)
    s_realized = int(sum(r.beats_random for r in results))
    s_star = int(np.quantile(s_perm, 1.0 - FWER)) if n_perm else 0
    perm_p = (1.0 + float(np.count_nonzero(s_perm >= s_realized))) / (1.0 + n_perm)
    return SubScreenResult(primitive=primitive, read=read, stat_kind=stat_kind,
                           s_realized=s_realized, s_star=s_star, perm_p=perm_p,
                           n_powered_cells=n_powered, cells=results, s_perm=s_perm)


def holm_adjust(pvals: list[float]) -> list[float]:
    """Holm step-down adjusted p-values (monotone-enforced). Applied across axes at G-019."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * pvals[idx])
        adj[idx] = min(running, 1.0)
    return adj


# --------------------------------------------------------------------------- #
# Pure computation — axis-level max-statistic admission (within-axis multiplicity control)
# --------------------------------------------------------------------------- #
def combine_axis(axis: str, subs: list[SubScreenResult], null_band: tuple[int, int],
                 n_perm: int = N_PERM, subs_stability: list[SubScreenResult] | None = None
                 ) -> AxisResult:
    """Combine sub-screens into the axis max statistic with the joint permuted null.

    ``S_M = max_sub S``; the joint null is the per-permutation max across sub-screens. ``ADMITTED``
    (provisional) iff ``S_M > S*`` and the axis permutation p ``≤ FWER``; ``EXONERATED`` iff every
    sub-screen's S lies within the descriptive D2a ``null_band``; ``INCONCLUSIVE`` iff the joint null
    cannot separate (``S* >=`` max attainable powered S). Cross-axis Holm is applied at G-019.
    """
    s_perm_stack = np.vstack([s.s_perm for s in subs])                 # (n_sub, n_perm)
    s_perm_max = s_perm_stack.max(axis=0)
    s_realized = np.array([s.s_realized for s in subs], dtype=np.int64)
    s_m = int(s_realized.max())
    drive_i = int(np.argmax(s_realized))                              # first on ties (SUB order)
    s_star = int(np.quantile(s_perm_max, 1.0 - FWER)) if n_perm else 0
    perm_p = (1.0 + float(np.count_nonzero(s_perm_max >= s_m))) / (1.0 + n_perm)
    mean_p, sd_p = float(s_perm_max.mean()), float(s_perm_max.std(ddof=1))
    rank_z = (s_m - mean_p) / sd_p if sd_p > 0 else float("nan")

    band = {}
    for fw in FWER_BAND:
        ss = int(np.quantile(s_perm_max, 1.0 - fw))
        band[fw] = {"s_star": ss, "admitted": bool(s_m > ss)}

    max_powered = max(s.n_powered_cells for s in subs)
    lo, hi = null_band
    all_in_band = all(lo <= s.s_realized <= hi for s in subs)
    admitted = bool(s_m > s_star and perm_p <= FWER)
    inconclusive = bool(s_star >= max_powered) and not admitted
    if admitted:
        disposition = "ADMITTED (NON-BINDING — pending G-019 cross-axis Holm)"
    elif inconclusive:
        disposition = "INCONCLUSIVE (permuted null cannot separate at realized cell count)"
    elif all_in_band:
        disposition = "EXONERATED (NON-BINDING — every sub-screen S in the D2a null band)"
    else:
        disposition = "NOT_ADMITTED (NON-BINDING — S_M <= S* but outside null band on >=1 read)"

    mc = {}
    if subs_stability is not None:
        s_perm_max_1k = np.vstack([s.s_perm for s in subs_stability]).max(axis=0)
        n1k = s_perm_max_1k.shape[0]
        mc = {
            "n_perm_stability": n1k,
            "s_star_stability": int(np.quantile(s_perm_max_1k, 1.0 - FWER)),
            "perm_p_stability": (1.0 + float(np.count_nonzero(s_perm_max_1k >= s_m))) / (1.0 + n1k),
        }

    return AxisResult(axis=axis, s_m=s_m, s_star=s_star, perm_p=perm_p, rank_z=rank_z,
                      driving_sub=f"{subs[drive_i].primitive}/{subs[drive_i].read}",
                      fwer_band=band, mc_stability=mc, disposition=disposition,
                      s_perm_max=s_perm_max)
