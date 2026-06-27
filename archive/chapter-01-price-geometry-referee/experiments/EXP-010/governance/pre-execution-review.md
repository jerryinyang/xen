# Governance Review: Experiment EXP-010 — Pre-Execution

**Date**: 2026-06-03
**Review Type**: Pre-Execution (consolidated, Stage 4)
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `code/split_protocols.py`

## Executive Summary

Split-protocol robustness test holding the referee frozen and changing only the
train/test partition (single vs anchored walk-forward vs purged/embargoed CV),
pooled by domain. The faithful multi-fold wrapper reuses the frozen harness
primitives unchanged; the single-fold path reduces leg-for-leg to the frozen
gate, and a reference-reproduction consistency check against EXP-003 guards
fidelity. Material criterion frozen pre-results. All checks pass. **APPROVE.**

## Constraint Checks

### Simplicity Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| all | PASS | One experiment-local module for fold indices + a faithful referee wrapper that imports every estimator primitive from the frozen harness; no shared `python/src/xen` change (no P0 re-validation triggered). |

### Academic-Finance Pitfall Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| all | PASS | Wilson FPR/TPR + grid MDE + stationary block bootstrap (frozen); purged/embargoed CV explicitly guards serial-correlation leakage rather than assuming iid; no normality/stationarity assumptions. |

### Scope Compliance Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Single question (H-split); protocols, K, purge, embargo, draw counts, and the material criterion `max(0.5, 0.20·MDE_single)` / disjoint-FPR predeclared and frozen pre-results. |
| code | PASS | Budget honoured: 4 stat operations / 4 plots / 1 module. Pooled-by-domain (de-pooling is EXP-008, excluded). No adoption (deferred to EXP-011/Phase 003). |

### Principles Check

| Artifact | Data-Driven | Non-Parametric | Phantom Price Discipline | Holdout Excluded |
|----------|------------|---------------|--------------------------|-----------------|
| all | PASS | PASS | PASS (real domain `Close` + predeclared planted drift, same substrate as EXP-003; no chart prices) | PASS (first-70% slice; all fold indices bounded to `[0, n)` of the analysis domain; no protocol can extend past the cutoff) |

### Look-Ahead / Causality Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| split_protocols.py | PASS | Walk-forward trains only on indices strictly before its test block; purged CV applies a 1-bar purge each side + forward embargo; the scored quantity (pooled-OOS bootstrap) uses out-of-sample rows only. L1 episodes summed per fold (no seam artifacts). |
| faithfulness | PASS | Only the index partition feeding block length and the test bootstrap changes; legs, cost, materiality, naive control, and seeds mirror `evaluate_referees`. Single-fold path is leg-for-leg identical to the frozen gate; reference-reproduction check is the numeric guard. |

### Safe-Optimization Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| code | PASS | `multiprocessing` mirrors the seed-deterministic EXP-003/EXP-005 pattern (worker count never changes a verdict); per-draw arrays reused across protocols; verdict rows sorted into canonical order before write. No change to sample membership, denominators, or temporal ordering. |

### Quality Check (type-specific)

| Artifact | Verdict | Notes |
|----------|---------|-------|
| code | PASS | Sectioned per conventions; output dirs in `ensure_output_dirs()`; `tqdm` over the draw pool; denominators = draw counts (no dedup of draws); deterministic seeds via `seed_for`. ruff F/E9/E501 clean; both files compile. |
| zero-baseline | PASS | Material margin floored at 0.5 bps; `MDE_single` asserted finite via the reference path before comparison. |
| reference check | PASS | Single-split arm compared to EXP-003 by Wilson-interval overlap (FPR) and grid-uncertainty match (MDE); failure routes `overall_status = FAILED_REPRODUCTION`, blocking interpretation of protocol deltas. |

## Findings

### Critical
None.

### Warnings
None.

### Info
1. **Multi-fold in-sample overlap (documented approximation).** For walk-forward
   and purged CV the dedup-union "in-sample" used for block-length estimation and
   the L4 stability leg overlaps the pooled OOS rows. This affects only those
   reference statistics; the headline FPR/MDE come from the strictly-OOS
   bootstrap, so there is no look-ahead in the scored quantity. Acceptable for a
   robustness measurement; the Stage-5 audit should confirm the single-fold path
   reproduces the frozen gate.
2. **Pooled-OOS bootstrap across fold seams.** Because EXP-003 observed
   `block_length = 1` throughout (near-iid), the stationary bootstrap reduces to
   iid resampling and fold seams introduce no bias; if any protocol's in-sample
   block length exceeds 1, results should note the cross-seam approximation
   (already stated in the plan).
3. **Reduced draws (250/cell vs EXP-003's 500).** Held identical across the three
   arms for fair comparison; pooled cells still meet D-prec. The reference check
   is consistency, not bit-identity, by design.
4. 4h (and folded 4h) cells may be under-powered; reported with honest CIs, not
   forced to a verdict (design §9).

## Verdict

```
VERDICT: APPROVE
```

---

## Stage-4 Re-Review Addendum — 2026-06-03 (post adversarial review)

**Trigger.** Adversarial review
`docs/code-reviews/2026-06-03-194448-exp-008-010-adversarial-review.md` raised four EXP-010
findings (F01, F02, F05, F06), validated in
`docs/code-reviews/2026-06-03-exp-008-010-review-validation.md`. All are valid; all are now fixed
pre-execution. This addendum supersedes the original APPROVE.

| Finding | Resolution |
|---------|------------|
| F01 (FPR materiality suppressed when MDE not PASS) | `compare_protocols` now evaluates FPR materiality independent of MDE reportability, gated on FPR precision; domain verdict FALSIFIED on any material protocol. The uncontrolled-FPR inversion is closed. |
| F02 (multi-fold pooled train/OOS overlap) | **Upgraded from Info #1 to a fix.** `evaluate_partition_referees` now evaluates the frozen referee per fold (disjoint train/test) and combines (pooled OOS effect, concatenated per-fold bootstrap-mean CI, per-fold L1/L4). Reduces bit-for-bit to the frozen gate at K=1 (verified, 0 diff), so the reference-reproduction anchor is intact. Recorded as a dated `scope.md`/`analysis-plan.md` amendment (§2 ⚠). |
| F05 (per-timeframe row-fraction folds) | Fold boundaries are now shared 1-minute `CloseTime` boundaries mapped per domain (timestamp discipline, design §7). |
| F06 (unbounded verdict accumulation) | Verdicts streamed to disk with bounded FPR/TPR pass-count accumulators; full list never materialized. |

**Re-checks.** `py_compile` and `ruff` clean on `run_experiment.py` and `split_protocols.py`;
pure-function checks confirm within-fold disjointness for all three protocols, bit-identical K=1
equivalence to the frozen `evaluate_referees`, shared-timestamp fold mapping, the F01 FPR-uncontrolled
case flagging FALSIFIED, and streamed-CSV/accumulator consistency. Scope, budget (4 stat ops / 4
plots / 1 module), holdout discipline, and frozen-referee faithfulness are unchanged.

```
RE-REVIEW VERDICT: APPROVE (findings F01/F02/F05/F06 resolved)
```
