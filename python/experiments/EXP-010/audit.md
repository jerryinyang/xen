# Audit Report: Experiment EXP-010

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 3

EXP-010 regenerates EXP-003-style draws on the first-70% analysis slice and evaluates the frozen referees under three within-analysis-set split protocols. The implementation incorporates the pre-results amendment: multi-fold protocols evaluate the referee per fold with disjoint fold train/test sets, then combine fold outputs into one verdict per draw. The reference single-split arm reproduces EXP-003 statistically across all domain/alpha cells.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Dependency gate | PASS | Requires EXP-001 PASS, EXP-003 COMPLETE, and EXP-003 MDE/FPR artifacts before measurement (lines 137-155). |
| `code/run_experiment.py` | Holdout exclusion | PASS | Uses the frozen `load_analysis_data` first-70% analysis slice; protocol fold indices are built over in-analysis return rows only. |
| `code/run_experiment.py` | Draw generation | PASS | Regenerates scoped null/positive draws with deterministic `seed_for` namespacing and reuses the same draw arrays across protocols (lines 161-227). |
| `code/run_experiment.py` | Bounded output | PASS | Streams `protocol_draw_verdicts.csv` and keeps bounded FPR/TPR pass-count accumulators; the full verdict list is not held in memory (lines 270-308). |
| `code/run_experiment.py` | Progress/logging | PASS | Uses `tqdm` for load/domain and draw loops; output is concise. |
| `code/run_experiment.py` | Material criterion | PASS | FPR materiality is evaluated independently of MDE reportability, matching the amendment and frozen OR criterion (lines 560-619). |
| `code/run_experiment.py` | Timestamp fold mapping | PASS | Fold edges map shared 1-minute `CloseTime` boundary fractions into each domain, not per-timeframe row fractions (lines 725-750, 762-815). |
| `code/split_protocols.py` | Split semantics | PASS | Single, walk-forward, and purged-CV folds are bounded to domain row indices; walk-forward training is strictly prior; purged-CV masks purge + embargo around test blocks (lines 70-137). |
| `code/split_protocols.py` | Multi-fold referee faithfulness | PASS | Per-fold block-length estimation and bootstraps use each fold's own disjoint train/test partition; combined rows keep frozen leg semantics (lines 228-366). |
| `code/split_protocols.py` | Real-price discipline | PASS | Uses `strategy_return_bps` on generated real-return arrays; no chart-type synthetic prices are referenced. |
| `code/run_experiment.py` | Import side effects | PASS | Directories are created only inside `main()` via `ensure_output_dirs` (lines 123-126, 824-831). |

## Numerical Validation

### Spot Checks

Expected streamed verdict rows:

`4 instruments x 3 domains x (2 null generators x 250 + 9 positive edges x 250) draws x 3 protocols x 2 referees x 3 alphas = 594,000`

Actual `protocol_draw_verdicts.csv` data rows: 594,000.

Independent reconciliation from streamed verdicts:

- FPR summary mismatches vs streamed verdict counts: 0.
- FPR summary rows: 54.
- Positive TPR count cells in streamed verdicts: 486.

Reference reproduction:

| Check | Result |
|-------|--------|
| FPR interval consistency vs EXP-003 | PASS for all 9 domain/alpha rows |
| MDE consistency vs EXP-003 | PASS for all 9 domain/alpha rows |
| Overall reference reproduction | PASS |

Alpha0 gate FPR:

| Domain | Protocols | FPR | Wilson Half-Width | Null n |
|--------|-----------|-----|-------------------|--------|
| 5m | single, walk_forward, purged_cv | 0.0 | 0.000959 | 2,000 each |
| 1h | single, walk_forward, purged_cv | 0.0 | 0.000959 | 2,000 each |
| 4h | single, walk_forward, purged_cv | 0.0 | 0.000959 | 2,000 each |

Alpha0 gate MDE:

| Domain | Single | Walk-Forward | Purged CV | Material Shift? |
|--------|--------|--------------|-----------|-----------------|
| 5m | 1.0 | 1.0 | 1.0 | NO |
| 1h | 4.0 | 8.0 | 4.0 | YES, walk-forward |
| 4h | 12.0 | 24.0 | 12.0 | YES, walk-forward |

All alpha0 MDE rows have status PASS. FPR is controlled for every protocol/domain, so the material shifts are driven by MDE, not false-positive inflation.

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|------------|--------|----------|
| Split-only perturbation | Draw arrays and referee semantics stay fixed across protocols | YES | Draws are generated once per task and evaluated across all protocols with the same referee seed. |
| Fold train/test separation | Multi-fold protocols avoid pooled train/test overlap | YES | `evaluate_partition_referees` evaluates fold-local train/test partitions and combines outputs after fold evaluation. |
| Timestamp alignment | Fold boundaries use shared 1-minute `CloseTime` mapping | YES | `_mapped_fold_edges` maps canonical 1-minute boundaries into each domain. |
| Bounded inference precision | D-prec is met before material calls | YES | FPR half-width 0.000959; TPR half-width at MDE max 0.024249 among alpha0 rows. |

## Results Plausibility

The single-split reproduction passing makes the protocol deltas interpretable. Purged CV matches the single split across all domains. Walk-forward leaves FPR unchanged but raises MDE from 4 to 8 bps on 1h and from 12 to 24 bps on 4h, both exceeding the frozen material margins. That is a substantive split-protocol finding, not an implementation failure.

## Scope Compliance

- Analysis plan followed: YES, including the pre-results amendment
- Deviations: none found
- Complexity budget: 4 statistical checks / 4, 4 plots / 4, 1 local module / 1
- Holdout exclusion verified: YES
- Referee/cost/materiality changes: none found

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Reduced draw budget is intentional**
   - EXP-010 uses 250 draws per generator/edge rather than EXP-003's 500 for tri-protocol tractability. Precision still meets D-prec for reportable cells.

2. **Walk-forward material shifts are results, not defects**
   - The 1h and 4h H-split falsifications come from MDE increases while FPR remains zero.

3. **Multi-fold CI combination is experiment-local**
   - The per-fold bootstrap-combination wrapper is an amended, scoped EXP-010 implementation choice. The single-split reference check is the guardrail that makes its deltas interpretable.

## Re-Audit Requirements

None.
