"""Expanding-window walk-forward protocol (``WF-EXPANDING``) — CF-CAPGEO-001 component.

Implements the frozen Phase 017 D0 §D4 protocol and its D4.1 counted-read accounting rule
(``wf-model.md``). Three concerns, kept pure and reusable (no experiment-specific I/O):

1. **Fold schedule** (:func:`make_folds`) — an expanding window over a chronologically
   ordered event series: initial train = first ``initial_frac`` of the series, then
   ``n_folds`` test folds of ``step_frac`` each, every tested fold rolled into the next
   train. Including a completed test fold in the next train is **not leakage** (those
   observations are historical at the next train time). The final-30% global holdout is
   **never** a fold (the caller passes only the in-analysis series).

2. **Aggregation to one stratum verdict** (:func:`aggregate_walk_forward`) — pool the test-fold
   returns and emit exactly **one** ``(expectancy, median, P(>X), 90% CI)`` per stratum via a
   **fold-clustered bootstrap** (cluster = fold): resample whole folds with replacement and,
   within each chosen fold, resample iid (synthetic) or by moving block (real data, preserving
   serial dependence). This is the binding stratum unit; the individual folds are in-protocol
   disclosures, not separate inferences.

3. **Counted-read accounting** (:func:`counted_reads`) — the binding governance rule: one frozen,
   pre-declared WF run on a stratum is **exactly one** counted TEST read against that stratum's
   2-lifetime cap; the folds are disclosures. The rule reverts each fold to a separate counted
   read if any D4.1 condition fails, rejects an at-cap stratum, and never admits a holdout fold.

All returns are real-price ATR-normalised values in deployment (Phase 018); the synthetic
Phase 017 legs pass ATR-unit synthetic returns. The module never loads data or touches a holdout.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from xen import ass

# --------------------------------------------------------------------------- #
# Frozen protocol configuration (Phase 017 D0 §D4 — no tuning without a D0-amendment)
# --------------------------------------------------------------------------- #
INITIAL_FRAC: float = 0.50          # initial train = first 50% of the analysis series
STEP_FRAC: float = 0.10             # each expanding test fold = 10%
N_FOLDS: int = 5                    # 5 expanding folds -> tests (0.50, 1.00]
MIN_FOLD: int = 30                  # programme power floor per (stratum, fold); below = disclosed
CAP_COUNTED_READS: int = 2          # TEST-read ledger: 2 lifetime counted reads per stratum


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Fold:
    """One expanding-window fold over an ordered series of length ``n``.

    Index ranges are half-open ``[start, stop)`` into the chronological series. ``train`` always
    starts at 0 (expanding); ``test`` is the next contiguous slice. ``below_floor`` flags a
    test fold under :data:`MIN_FOLD` — disclosed, never silently dropped.
    """

    index: int
    train_start: int
    train_stop: int
    test_start: int
    test_stop: int

    @property
    def test_size(self) -> int:
        return self.test_stop - self.test_start

    @property
    def train_size(self) -> int:
        return self.train_stop - self.train_start

    def below_floor(self, min_fold: int = MIN_FOLD) -> bool:
        return self.test_size < min_fold


@dataclass(frozen=True)
class WFAggregate:
    """The single fold-clustered stratum verdict produced by one WF run.

    All return-scale fields are in the input units (ATR units in Phase 017). ``ci_low_1s`` is the
    one-sided 95% lower bound on the expectancy (= the 5th-percentile bootstrap bound), the
    quantity the FPR margin rule and the MDE detection rule read.
    """

    n_pooled: int
    n_folds_used: int
    fold_sizes: tuple[int, ...]
    subfloor_folds: tuple[int, ...]
    expectancy: float
    expectancy_lo: float                 # 5th pct == one-sided 95% lower bound (ci_low_1s)
    expectancy_hi: float
    median: float
    median_lo: float
    median_hi: float
    p_gt: dict[float, float] = field(default_factory=dict)

    @property
    def ci_low_1s(self) -> float:
        return self.expectancy_lo


@dataclass(frozen=True)
class RunSpec:
    """A declared ``WF-EXPANDING`` run against one stratum, for counted-read accounting (D4.1)."""

    stratum: str
    frozen_before_oos: bool          # D4.1(1): whole schedule hash-pinned before any OOS row read
    between_fold_selection: bool     # D4.1(2): human selection between folds (True = violated)
    predeclared_aggregation: bool    # D4.1(3): one predeclared aggregation + verdict rule
    holdout_used_as_fold: bool       # D4.1(4): holdout appears as a fold (True = violated)
    n_folds: int = N_FOLDS
    is_rolling_comparison: bool = False   # 1y/2y/3y comparison on already-read folds -> +0


@dataclass(frozen=True)
class ReadOutcome:
    """The counted-read decision for one :class:`RunSpec` given the stratum's prior tally."""

    stratum: str
    accepted: bool
    counted_increment: int
    per_fold_reverted: bool
    weakened_evidence: bool
    prior_counted: int
    new_counted: int
    reason: str


# --------------------------------------------------------------------------- #
# Pure computation — fold schedule
# --------------------------------------------------------------------------- #
def make_folds(
    n: int,
    *,
    initial_frac: float = INITIAL_FRAC,
    step_frac: float = STEP_FRAC,
    n_folds: int = N_FOLDS,
) -> list[Fold]:
    """Build the expanding-window fold schedule over an ordered series of length ``n``.

    Boundaries are computed as ``round(frac * n)`` so the test folds tile ``(initial_frac, 1.0]``
    with no gaps or overlaps and the last fold ends exactly at ``n``. A completed test fold is
    included in the next fold's train (expanding) — historical at the next train time, not leakage.

    Parameters
    ----------
    n : int
        Length of the chronological series (the in-analysis stratum; the holdout is never passed).
    initial_frac, step_frac, n_folds : float, float, int
        Frozen D4 schedule (0.50 initial, 0.10 step, 5 folds by default).

    Returns
    -------
    list[Fold]
        The ``n_folds`` folds in chronological order.
    """
    if n < 2:
        raise ValueError(f"make_folds needs n >= 2, got {n}")
    folds: list[Fold] = []
    for i in range(n_folds):
        test_lo = int(round((initial_frac + i * step_frac) * n))
        test_hi = n if i == n_folds - 1 else int(round((initial_frac + (i + 1) * step_frac) * n))
        test_lo = min(test_lo, n)
        test_hi = min(test_hi, n)
        folds.append(Fold(index=i, train_start=0, train_stop=test_lo,
                          test_start=test_lo, test_stop=test_hi))
    return folds


# --------------------------------------------------------------------------- #
# Pure computation — fold-clustered aggregation to one stratum verdict
# --------------------------------------------------------------------------- #
def _resample_fold(block: np.ndarray, rng: np.random.Generator, kind: str) -> np.ndarray:
    """Resample one fold's returns: ``iid`` simple resample or ``block`` moving-block."""
    m = block.shape[0]
    if m == 0:
        return block
    if kind == "iid":
        return block[rng.integers(0, m, size=m)]
    if kind == "block":
        b = ass.default_block_length(m)
        b = int(min(max(1, b), m))
        n_starts = m - b + 1
        n_blk = int(np.ceil(m / b))
        starts = rng.integers(0, n_starts, size=n_blk)
        idx = (starts[:, None] + np.arange(b)[None, :]).reshape(-1)[:m]
        return block[idx]
    raise ValueError(f"kind must be 'iid' or 'block', got {kind!r}")


def aggregate_walk_forward(
    returns: np.ndarray,
    rng: np.random.Generator,
    *,
    kind: str = "iid",
    thresholds: tuple[float, ...] = ass.DEFAULT_THRESHOLDS,
    n_boot: int = ass.N_BOOT,
    alpha: float = ass.CI_ALPHA,
    initial_frac: float = INITIAL_FRAC,
    step_frac: float = STEP_FRAC,
    n_folds: int = N_FOLDS,
    min_fold: int = MIN_FOLD,
) -> WFAggregate:
    """Run ``WF-EXPANDING`` on one ordered return series and aggregate to one stratum verdict.

    Pools the test-fold returns (the out-of-train slices); the point estimates are the direct
    (un-pooled) expectancy / median / ``P(>X)`` over the pooled test returns. The 90% CI depends on
    ``kind``:

    - ``kind="iid"`` (synthetic data, iid by construction): a flat within-pool percentile bootstrap
      (:func:`xen.ass.bootstrap_cis`). For an exchangeable population the fold-clustered and flat
      resamples are statistically equivalent, so the fast batched form is used; the WF **structure**
      (expanding train, pooled out-of-train test, one stratum verdict) is preserved.
    - ``kind="block"`` (real data, serially dependent): a true **fold-clustered moving-block**
      bootstrap — resample whole folds with replacement and, within each chosen fold, resample by
      moving block — preserving the fold structure and within-fold serial dependence.

    Sub-floor folds (test size < ``min_fold``) are still used **but disclosed** in
    ``subfloor_folds`` — never silently dropped.

    Parameters
    ----------
    returns : np.ndarray
        Chronologically ordered return series for one stratum (in-analysis only).
    rng : np.random.Generator
        Seeded generator (determinism).
    kind : str
        ``"iid"`` (synthetic within-fold resample) or ``"block"`` (real-data moving-block).
    thresholds : tuple[float, ...]
        ``X`` values for ``P(return > X)``.
    n_boot, alpha, initial_frac, step_frac, n_folds, min_fold :
        Frozen bootstrap and schedule parameters.

    Returns
    -------
    WFAggregate
        The single fold-clustered stratum verdict.
    """
    returns = np.asarray(returns, dtype=np.float64)
    n = returns.shape[0]
    folds = make_folds(n, initial_frac=initial_frac, step_frac=step_frac, n_folds=n_folds)
    fold_arrays = [returns[f.test_start:f.test_stop] for f in folds]
    fold_arrays = [a for a in fold_arrays if a.shape[0] > 0]
    fold_sizes = tuple(int(a.shape[0]) for a in fold_arrays)
    subfloor = tuple(f.index for f in folds if 0 < f.test_size < min_fold)
    pooled = np.concatenate(fold_arrays) if fold_arrays else np.asarray([], dtype=np.float64)
    if pooled.shape[0] < 2:
        raise ValueError(f"WF aggregate needs >= 2 pooled test points, got {pooled.shape[0]}")

    expectancy = float(np.mean(pooled))
    median = float(np.median(pooled))
    p_gt = {thr: float(np.mean(pooled > thr)) for thr in thresholds}
    k = len(fold_arrays)

    if kind == "iid":
        # Exchangeable population: fold-clustered == flat resample. Use the fast batched form.
        ci = ass.bootstrap_cis(pooled, rng, n_boot=n_boot, alpha=alpha)
        exp_lo, exp_hi = ci.expectancy_lo, ci.expectancy_hi
        med_lo, med_hi = ci.median_lo, ci.median_hi
    elif kind == "block":
        exp_boot = np.empty(n_boot, dtype=np.float64)
        med_boot = np.empty(n_boot, dtype=np.float64)
        for j in range(n_boot):
            chosen = rng.integers(0, k, size=k)                   # cluster (fold) resample
            parts = [_resample_fold(fold_arrays[c], rng, "block") for c in chosen]
            rs = np.concatenate(parts)
            exp_boot[j] = rs.mean()
            med_boot[j] = np.median(rs)
        lo_pct = 100.0 * alpha / 2.0
        hi_pct = 100.0 * (1.0 - alpha / 2.0)
        exp_lo = float(np.percentile(exp_boot, lo_pct))
        exp_hi = float(np.percentile(exp_boot, hi_pct))
        med_lo = float(np.percentile(med_boot, lo_pct))
        med_hi = float(np.percentile(med_boot, hi_pct))
    else:
        raise ValueError(f"kind must be 'iid' or 'block', got {kind!r}")

    return WFAggregate(
        n_pooled=int(pooled.shape[0]), n_folds_used=k, fold_sizes=fold_sizes,
        subfloor_folds=subfloor, expectancy=expectancy,
        expectancy_lo=exp_lo, expectancy_hi=exp_hi, median=median,
        median_lo=med_lo, median_hi=med_hi, p_gt=p_gt,
    )


# --------------------------------------------------------------------------- #
# Pure computation — counted-read accounting (D4.1, binding governance rule)
# --------------------------------------------------------------------------- #
def counted_reads(
    spec: RunSpec,
    prior_counted: int,
    *,
    cap: int = CAP_COUNTED_READS,
) -> ReadOutcome:
    """Apply the D4.1 counted-read accounting rule for one declared WF run.

    The rule (D0 §D4.1):

    - A **conforming** frozen WF run (D4.1 conditions 1-4 all hold) = **+1** counted read; the
      folds are in-protocol disclosures. A second conforming run on a 1/``cap`` stratum is admitted
      as **weakened-evidence**; an at-``cap`` stratum is **rejected** (no further stratum-specific
      claim).
    - A **non-conforming** run (any of: not frozen-before-OOS, between-fold human selection, or no
      predeclared aggregation) **reverts each fold to a separate counted read** (``+n_folds``); if
      that would exceed the cap the run is **rejected**.
    - A run that uses the **holdout as a fold** is **rejected** outright (the holdout is never a fold).
    - A **rolling 1y/2y/3y comparison** on already-read folds adds **+0** (disclosure).

    Parameters
    ----------
    spec : RunSpec
        The declared run and its D4.1 condition flags.
    prior_counted : int
        The stratum's lifetime counted reads before this run.
    cap : int
        Lifetime counted-read cap (default 2).

    Returns
    -------
    ReadOutcome
        The accounting decision: accepted, the counted increment, and disclosure flags.
    """
    def _out(accepted: bool, inc: int, reverted: bool, weakened: bool, reason: str) -> ReadOutcome:
        new = prior_counted + (inc if accepted else 0)
        return ReadOutcome(spec.stratum, accepted, inc if accepted else 0, reverted,
                           weakened, prior_counted, new, reason)

    if spec.holdout_used_as_fold:
        return _out(False, 0, False, False, "REJECTED: holdout used as a fold (D4.1 cond 4)")
    if spec.is_rolling_comparison:
        return _out(True, 0, False, False, "DISCLOSURE: rolling 1y/2y/3y on already-read folds (+0)")
    if prior_counted >= cap:
        return _out(False, 0, False, False,
                    f"REJECTED: stratum at cap ({prior_counted}/{cap}); no stratum-specific claim")

    conforming = (spec.frozen_before_oos and (not spec.between_fold_selection)
                  and spec.predeclared_aggregation)
    if conforming:
        weakened = (prior_counted + 1) >= cap and prior_counted >= 1
        return _out(True, 1, False, weakened,
                    "COUNTED: conforming frozen WF run = +1 (folds are disclosures)"
                    + ("; weakened-evidence (second read)" if weakened else ""))

    inc = spec.n_folds
    if prior_counted + inc > cap:
        return _out(False, inc, True, False,
                    f"REJECTED: non-conforming run reverts to +{inc} folds, exceeds cap "
                    f"({prior_counted}+{inc}>{cap})")
    return _out(True, inc, True, False,
                f"COUNTED: non-conforming run reverts each fold to a separate read (+{inc})")
