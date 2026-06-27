# Audit Report: Experiment EXP-010

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 3

EXP-010 was re-audited against the corrected multi-fold estimator and the saved re-run artifacts. The implementation now combines fold bootstrap means as a test-size-weighted pooled-OOS bootstrap, the single-split arm still reproduces EXP-003, FPR remains controlled for every protocol/domain, and the corrected H-split verdict is supported on 5m/1h and falsified only on 4h.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Dependency gate | PASS | Requires EXP-001 PASS and EXP-003 COMPLETE before measurement; EXP-003 MDE/FPR artifacts must exist (lines 137-155). |
| `code/run_experiment.py` | Holdout exclusion | PASS | Uses the frozen `load_analysis_data` first-70% analysis slice; fold boundaries are built over in-analysis return rows only (lines 775-790). |
| `code/run_experiment.py` | Draw generation | PASS | Regenerates scoped null/positive draws with deterministic namespaced seeds and reuses the same draw arrays across all protocols (lines 161-227). |
| `code/run_experiment.py` | Bounded output | PASS | Streams `protocol_draw_verdicts.csv` and keeps bounded FPR/TPR pass-count accumulators; the full verdict table is not retained in memory (lines 270-308). |
| `code/run_experiment.py` | Timestamp fold mapping | PASS | Fold edges map shared 1-minute `CloseTime` fractions into each domain, not per-timeframe row fractions (lines 722-790). |
| `code/run_experiment.py` | Material criterion | PASS | H-split materiality is evaluated from reportable MDE shifts or precise FPR shifts using the frozen OR criterion (lines 520-610). |
| `code/run_experiment.py` | Metadata and plots | PASS | Metadata records `multi_fold_aggregation = per_fold_disjoint_pooled_oos`; plots use bounded summary tables only (lines 856-889). |
| `code/split_protocols.py` | Split semantics | PASS | Single, walk-forward, and purged-CV folds are bounded to domain row indices; walk-forward training is strictly prior and purged-CV removes purge/embargo rows around test blocks (lines 70-138). |
| `code/split_protocols.py` | Multi-fold combination | PASS | `_weighted_combine()` size-weights per-fold bootstrap means per resample, so CIs scale with pooled OOS size rather than fold size; single-fold output is unchanged (lines 168-192). |
| `code/split_protocols.py` | Referee faithfulness | PASS | `evaluate_partition_referees()` evaluates fold-local train/test partitions, pools OOS effects once per row, preserves frozen L1-L5/minimal semantics, and reports one verdict per draw (lines 256-403). |
| `code/split_protocols.py` | Real-price discipline | PASS | Returns are generated from real return arrays through `strategy_return_bps`; no chart-type or synthetic-price path is present. |
| `code/run_experiment.py` | Import side effects / logging | PASS | Output directories are created only in `main()`; long loops use `tqdm` and output is concise (lines 823-894). |

## Numerical Validation

### Spot Checks

Output dimensions match the approved re-run design:

- `protocol_draw_verdicts.csv`: 594,000 rows = 4 instruments x 3 domains x (2 null generators x 250 + 9 positive edges x 250) draws x 3 protocols x 2 referees x 3 alphas.
- `protocol_fpr_summary.csv`: 54 rows.
- `protocol_mde_summary.csv`: 27 rows.
- `protocol_comparison.csv`: 6 rows.
- `reference_reproduction_check.csv`: 9 rows.

Independent result-table reconciliation found:

- Reference reproduction: 9/9 domain/alpha rows have `fpr_consistent = true` and `mde_consistent = true`.
- Alpha0 gate FPR: 0/2000 for every domain/protocol, Wilson half-width 0.000959.
- Alpha0 gate MDE:

| Domain | Single | Walk-Forward | Purged CV | Material Shift? |
|--------|--------|--------------|-----------|-----------------|
| 5m | 1.0 | 1.0 | 1.0 | NO |
| 1h | 4.0 | 4.0 | 4.0 | NO |
| 4h | 12.0 | 8.0 | 8.0 | YES, both alternatives lower |

`protocol_comparison.csv` reports only the 4h alternative-protocol rows as material: walk-forward and purged CV both have `delta_mde_bps = -4.0` versus margin 2.4, with FPR still 0.0.

### Multi-Fold CI Scaling Check

The former defect was a fold-combination issue, so the audit checked the corrected path directly. For EURUSD/4h, positive edge 12.0 bps, alpha0, gate stack:

| Protocol | Draws | Mean CI Width | Mean Effective N |
|----------|-------|---------------|------------------|
| single | 250 | 2.59 | 1056 |
| walk_forward | 250 | 1.75 | 1760 |
| purged_cv | 250 | 1.26 | 3515 |

CI width now decreases as pooled OOS effective N increases, which is the expected behavior for the corrected stratified pooled-OOS bootstrap.

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|------------|--------|----------|
| Split-only perturbation | Draw arrays and referee semantics stay fixed across protocols | YES | Each draw task generates returns/positions once and evaluates every protocol with the same referee seed. |
| Fold train/test separation | Multi-fold protocols avoid fold-local train/test contamination | YES | `evaluate_partition_referees()` estimates block length on fold train and bootstraps fold test only. |
| Pooled-OOS inference | Multi-fold CI reflects the pooled OOS mean | YES | `_weighted_combine()` combines per-fold bootstrap means per resample with test-size weights; CI scaling check passes. |
| Timestamp alignment | Fold boundaries use shared 1-minute `CloseTime` mapping | YES | `_mapped_fold_edges()` maps canonical base timestamps into each domain. |
| D-prec reportability | FPR/TPR precision gates are met before material calls | YES | All alpha0 gate MDE rows have status PASS; FPR half-width 0.000959. |

## Results Plausibility

The corrected results are coherent. Single-split reproduces EXP-003; FPR is unchanged and controlled across every protocol; 5m and 1h MDEs are split-robust; 4h alternative protocols detect a smaller 8 bps edge because they score more OOS rows than the single split. That direction is consistent with an OOS-window/sample-size effect at the data-poorest domain, not referee instability.

## Scope Compliance

- Analysis plan followed: YES, including the corrected pooled-OOS multi-fold combination.
- Deviations: none found in the corrected artifacts.
- Complexity budget: 4 statistical checks / 4, 4 plots / 4, 1 local module / 1.
- Holdout exclusion verified: YES.
- Referee/cost/materiality changes: none found.

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Reduced draw budget is intentional**
   - EXP-010 uses 250 draws per generator/edge rather than EXP-003's 500 for tri-protocol tractability. Precision still meets D-prec for reportable cells.

2. **Protocol is confounded with OOS window and sample size**
   - The three protocols inherently score different OOS windows (`single` about last 30%, walk-forward about 50%, purged CV nearly all rows). The 4h shift is therefore reported as protocol-plus-OOS-window sensitivity.

3. **Single-split reproduction is not a complete multi-fold guardrail**
   - The single arm has one fold, so future multi-fold wrappers must also verify pooled-OOS CI scaling. EXP-010 now records and passes that check.

## Re-Audit Requirements

None.
