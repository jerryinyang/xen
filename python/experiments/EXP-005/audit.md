# Audit Report: Experiment EXP-005

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

EXP-005 can be interpreted. The implementation matches the approved scope, uses the frozen Phase 001 referee harness unchanged, excludes the final 30% global holdout through the shared lazy loading helper, and writes internally consistent result tables. Independent table checks recomputed the FPR and TPR summaries from `realistic_candidate_draws.csv` with zero mismatches.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Scope compliance | PASS | Implements dependency/predeclaration gates, holdout-safe domain construction, candidate sanity, paired null/positive verdicts, detection classification, and the five scoped plots only. |
| `code/run_experiment.py` | Holdout exclusion | PASS | Uses `load_analysis_data()` from the frozen harness before domain generation (`run_experiment.py:764-766`); the harness sorts by `CloseTime`, slices the first 70%, then collects (`python/src/xen/referee_calibration.py:120-158`). |
| `code/run_experiment.py` | Dependency and freeze gates | PASS | Requires EXP-001 PASS, EXP-003 COMPLETE plus finite MDE artifact, and the Stage 4 predeclaration token before measurement (`run_experiment.py:132-205`). |
| `code/run_experiment.py` | Real-price outcomes | PASS | Uses `next_log_returns_from_bars()` on real domain `Close` prices (`python/src/xen/referee_calibration.py:463-472`) plus the scoped planted drift; no chart-type synthetic prices are in scope. |
| `code/run_experiment.py` | Temporal alignment | PASS | Domain train/test split inherits the 1-minute `CloseTime` boundary via `domain_split_index()` (`python/src/xen/referee_calibration.py:475-484`). No bar-index cross-view alignment is used. |
| `code/run_experiment.py` | Referee reuse | PASS | Imports and reuses `xen.referee_calibration`; `git status` shows no change to `python/src/xen/referee_calibration.py`. |
| `code/run_experiment.py` | Determinism | PASS | Draws use stable `seed_for(...)`; unordered multiprocessing output is sorted canonically before writing (`run_experiment.py:796-810`). |
| `code/run_experiment.py` | Memory/performance | PASS | Long draw loops use `tqdm`; persisted outputs are verdict-level, not per-bar; plots consume summary or bounded filtered draw data (`run_experiment.py:334-369`, `400-429`, `606-736`). |
| `code/run_experiment.py` | Import side effects | PASS | Output directories are created only in `main()` via `ensure_output_dirs()` (`run_experiment.py:118-121`, `813-818`). |
| `code/candidate.py` | Candidate construction | PASS | Implements fixed `p_active=0.80`, `q_match=0.75` noisy positions and closed-form latent drift calibration (`candidate.py:19-100`). |
| `code/candidate.py` | Diagnostics | PASS | Reports eligible/active/matched counts, train/test active counts, episodes, and realized gross/net bps without persisting per-bar arrays (`candidate.py:106-158`). |

## Numerical Validation

### Table Consistency

Independent CSV checks, without running the experiment script, verified:

- `realistic_candidate_draws.csv`: 216,000 verdict rows, matching 4 instruments x 3 domains x (1,000 null + 2,000 positive tasks) x 2 referees x 3 alpha values.
- `fpr_summary.csv` and `tpr_summary.csv`: recomputed from the verdict-level rows with 0 mismatches in successes, denominators, or rates.
- `candidate_sanity.csv`: 60 rows, matching 4 instruments x 3 domains x (1 null aggregate + 4 positive edge levels).
- `detection_summary.csv`: 12 rows, matching 3 pooled domains x 4 edge multipliers.
- `per_instrument_detection.csv`: 48 rows, matching 4 instruments x 3 domains x 4 edge multipliers.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|----------------|--------------|-------|
| Candidate active rate | 0.80 +/- 0.02 | 0.798518 to 0.800561 | YES |
| Candidate active match rate | 0.75 +/- 0.02 | 0.749482 to 0.750623 | YES |
| Positive calibration absolute error | small vs target bps | 0.000005 to 0.129769 bps | YES |
| Gate-stack pooled FPR at alpha0 | <= 0.05, half-width <= 0.03 | 0.0, half-width 0.000480 in all domains | YES |
| Gate-stack pooled TPR at 1.0x MDE | >= 0.80, half-width <= 0.05 | 5m 1.0000, 1h 0.9850, 4h 0.9465 | YES |
| Effective N | positive and plausible | 902 to 65,144 | YES |
| Block length | positive integer | 1 in all verdict rows | YES |

### Headline Detection Rows

| Domain | MDE bps | FPR | TPR at 1.0x MDE | TPR half-width | Status |
|--------|---------|-----|-----------------|----------------|--------|
| 5m | 1.0 | 0.0000 | 1.0000 | 0.000959 | DETECTED_FLOOR |
| 1h | 4.0 | 0.0000 | 0.9850 | 0.005403 | DETECTED_FLOOR |
| 4h | 12.0 | 0.0000 | 0.9465 | 0.009890 | DETECTED_FLOOR |

All 12 per-instrument headline rows also classify as `DETECTED_FLOOR` with `under_powered=false`.

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|------------|--------|----------|
| Chronological holdout split | First 70% only, ordered by `CloseTime` | YES | Shared helper sorts, slices, then collects; `analysis_metadata.csv` records analysis ends in 2025 while source filenames run to 2026. |
| Wilson FPR/TPR intervals | Binomial draw-level pass/reject counts | YES | FPR denominators are 4,000 pooled null verdicts; TPR denominators are 2,000 pooled positive verdicts per edge. |
| Block bootstrap CIs | Train-estimated block length used on test segment | YES | Harness estimates block length from train strategy returns before test bootstrap (`python/src/xen/referee_calibration.py:812-819`, `968-982`). |
| Realistic candidate sanity | Candidate is neither inactive nor oracle-perfect | YES | Overall active rate 0.799997 and match rate 0.750005; per-cell rates stay within the predeclared tolerance. |
| Frozen-harness comparability | Phase 001 referee logic unchanged | YES | No shared harness file changes detected; EXP-005 adds only experiment-local `candidate.py`. |

## Results Plausibility

The pattern is coherent with EXP-003 and the EXP-005 construction. Gate-stack null FPR remains 0 across domains and alpha values; minimal-baseline FPR stays near the nominal alpha grid. Positive detection rises monotonically with edge multiplier at alpha0 for the gate stack, and the 1.0x MDE point clears the predeclared TPR target in every pooled domain.

The candidate calibration is also plausible: null realized net bps are approximately `-cost * active_rate`, while positive realized net bps concentrate near the target edge. The largest positive calibration error in the aggregated sanity table is 0.1298 bps, immaterial relative to the 4h MDE scale and not large enough to affect any headline status.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none found
- Complexity budget: 4 / 4 statistical tests, 5 / 5 plots, 1 / 1 experiment-local helper module
- Holdout exclusion verified: YES
- Chart-type and synthetic-price exclusions respected: YES
- Shared module changes requiring P0 revalidation: none found

## Issues

### Critical

None.

### Warning

None.

### Info

1. **`status` in `detection_summary.csv` is cell-level**
   - Description: The same domain-level status is repeated on each multiplier row. This is consistent with `build_detection()` (`run_experiment.py:461-533`), where status is determined from the 1.0x MDE headline row and `detection_multiplier` records the first multiplier that clears the target.
   - Impact: Readers should not interpret a `0.5x` row with `status=DETECTED_FLOOR` as saying the 0.5x row itself met the TPR target; use `tpr_meets_target` for row-level pass/fail.

2. **Block length collapsed to 1**
   - Description: All verdict rows report `block_length=1`, so the stationary bootstrap reduced to i.i.d. resampling for these test return series.
   - Impact: This does not invalidate the result because the block length is train-estimated by the frozen harness, but interpretation should note that the observed candidate returns showed negligible autocorrelation under this estimator.

## Re-Audit Requirements

None. Re-audit only if EXP-005 code, result CSVs, plots, or the frozen `xen.referee_calibration` harness are changed.
