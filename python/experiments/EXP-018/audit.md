# Audit Report: Experiment EXP-018

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

EXP-018 results are suitable for interpretation. The implementation uses the approved first-70% analysis slice, preserves timestamp alignment through `CloseTime`, applies the Phase 003b revised incremental gate with no L2 output, and the generated FPR/TPR/domain-MDE summaries recompute from draw-level results with zero mismatches.

## Code Review

| File | Check | Verdict | Notes |
| --- | --- | --- | --- |
| `python/experiments/EXP-018/code/run_experiment.py` | Dependency gate | PASS | Requires EXP-013 PASS, EXP-017 PASS, and EXP-003 MDE map at lines 159-187. |
| `python/src/xen/referee_calibration.py` | Holdout exclusion | PASS | `load_analysis_data()` sorts by `CloseTime`, slices the first 70 percent, then collects at lines 120-143. |
| `python/experiments/EXP-018/code/run_experiment.py` | Analysis data construction | PASS | `build_cells()` uses `load_analysis_data()`, domain resampling, next-step returns, and shared timestamp split at lines 561-591. |
| `python/src/xen/referee_calibration.py` | Temporal alignment | PASS | `next_log_returns_from_bars()` sorts by `CloseTime` and computes next-step returns at lines 463-472; `domain_split_index()` uses the shared 1-minute train timestamp at lines 475-485. |
| `python/experiments/EXP-018/code/run_experiment.py` | Dependence grid | PASS | Enumerates the frozen rho/overlap/lag/reference-strength grid and inherited edge grid at lines 594-660. |
| `python/experiments/EXP-018/code/run_experiment.py` | Progress/performance | PASS | Draw execution is bounded and tracked with `tqdm`; multiprocessing uses task chunks at lines 663-686. |
| `python/experiments/EXP-018/code/run_experiment.py` | Summary correctness | PASS | FPR, TPR, leg diagnostics, cell MDE, binding corner, and domain MDE are summarized at lines 737-1075. |
| `python/experiments/EXP-018/code/run_experiment.py` | Domain rollup | PASS | `overall_status = COMPLETE` requires all domain statuses to start with SUPPORTED at lines 1234-1252. |
| `python/src/xen/incremental_referee.py` | Revised gate | PASS | Revised gate removes L2 and gates on L1/L3/L4'/strict-L5 at lines 535-574; revised-only callers skip unused standalone bootstrap via `compute_standalone=False` at lines 605-637. |

## Numerical Validation

### Spot Checks

- `draw_verdicts.csv`: 1,890,000 rows.
- `construction_diagnostics.csv`: 810,000 rows; 630,000 accepted, 180,000 construction-invalid with reason `target_rho_infeasible_for_overlap`.
- `fpr_summary.csv`: 162 rows; 126 PASS, 36 CONSTRUCTION_INVALID.
- `tpr_summary.csv`: 1,458 rows.
- `cell_mde_summary.csv`: 162 rows; 126 PASS, 36 CONSTRUCTION_INVALID.
- Recomputed `fpr_summary.csv` success counts and denominators from `draw_verdicts.csv` at `alpha = 0.05`: 0 mismatches.
- Recomputed `tpr_summary.csv` success counts and denominators from `draw_verdicts.csv` at `alpha = 0.05`: 0 mismatches.
- Recomputed domain MDE as max finite PASS-cell MDE: 5m `12.0`, 1h `16.0`, 4h `32.0`, matching `domain_mde_summary.csv`.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
| --- | --- | --- | --- |
| Accepted-cell FPR | <= 0.05 | 0.0 to 0.004 | YES |
| Accepted-cell FPR Wilson half-width | <= 0.03 | max 0.006684203250090802 | YES |
| Finite domain MDE | finite bps value where supported | 5m 12.0, 1h 16.0, 4h 32.0 | YES |
| Failing cells | 0 for support | 0 in all domains | YES |
| L2 columns in draw output | absent | none | YES |

### Binding Corner

The synchronous/high-overlap/null_R corner is explicitly reported for every domain and rho level:

| Domain | Rho | FPR | Cell MDE | Status |
| --- | --- | --- | --- | --- |
| 5m | independent | 0.0 | 1.0 | PASS |
| 5m | moderate | 0.0 | 1.0 | PASS |
| 5m | high | 0.0 | 1.0 | PASS |
| 1h | independent | 0.0 | 8.0 | PASS |
| 1h | moderate | 0.0 | 8.0 | PASS |
| 1h | high | 0.0 | 8.0 | PASS |
| 4h | independent | 0.002 | 16.0 | PASS |
| 4h | moderate | 0.002 | 24.0 | PASS |
| 4h | high | 0.0 | 24.0 | PASS |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
| --- | --- | --- | --- |
| Redundancy-null FPR | Null draws carry no planted marginal edge | YES | FPR is summarized only for `draw_kind = redundancy_null`; accepted cells all PASS. |
| Positive TPR/MDE | Positive draws use inherited edge grid and known planted marginal edge | YES | `run_metadata.json` records edge grid `[0.5, 1.0, 2.0, 4.0, 8.0, 12.0, 16.0, 24.0, 32.0]`; TPR rows cover accepted grid cells. |
| Worst-case domain MDE | Headline MDE is max finite cell MDE, not pooled average | YES | Domain recomputation matches `domain_mde_summary.csv`. |
| Construction invalidity | Invalid cells are disclosed before interpretation | YES | 36 invalid cells are listed in `underpowered_or_invalid_cells.csv`, all `CONSTRUCTION_INVALID`. |
| Holdout discipline | Final 30 percent global holdout excluded | YES | Shared loader slices before domain construction. |

## Results Plausibility

The revised gate resolves the EXP-015 failure mode: every accepted cell controls FPR and attains a finite MDE, including the moderate/high-rho synchronous high-overlap null_R stress corner. The cost of removing L2 is a higher worst-case incremental MDE map than the strict standalone map: 12/16/32 bps for 5m/1h/4h. The 36 invalid high-rho/low-overlap cells are construction-feasibility exclusions, not hidden failures.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 4 measurements / 4 budgeted, 5 plots / 5 budgeted, 0 new modules / 1 budgeted
- Holdout exclusion verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Generic supported-status label covers construction-invalid cells**
   - File: `python/experiments/EXP-018/results/domain_mde_summary.csv`
   - Description: The domain status string is `SUPPORTED_WITH_UNDERPOWERED_CELLS`, while `underpowered_or_invalid_cells.csv` shows the disclosed non-PASS cells are all `CONSTRUCTION_INVALID`, not precision-underpowered.
   - Impact: No numerical impact; interpretation should use the detailed invalid-cell table to avoid wording ambiguity.

## Re-Audit Requirements

None. The EXP-018 artifacts are suitable for interpretation and downstream EXP-019 dependency use.
