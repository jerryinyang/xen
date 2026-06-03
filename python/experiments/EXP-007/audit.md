# Audit Report: Experiment EXP-007

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

EXP-007 is trustworthy for interpretation. The implementation measures the predeclared lenient L5 rule on the frozen EXP-003 draw substrate, confirms verdict-level equivalence with EXP-006 `tau=0` and the L5-removed gate, and reports the required economically sub-material pass accounting.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-007/code/run_experiment.py` | Correctness | PASS | Dependency and predeclaration gates run before measurement (`lines 126-189`); lenient verdict is `legs_pass & (ci_lower_bps > 0.0)` and drop-L5 is `legs_pass` (`lines 204-220`). |
| `python/experiments/EXP-007/code/run_experiment.py` | Edge cases | PASS | Missing dependencies, missing predeclaration token, zero lenient-pass cells, no finite MDE, FPR precision, and FPR control are handled explicitly (`lines 137-161`, `178-189`, `335-354`, `521-533`, `630-649`). |
| `python/experiments/EXP-007/code/run_experiment.py` | Type safety | PASS | Public helpers have type hints and docstrings. |
| `python/experiments/EXP-007/code/run_experiment.py` | NaN handling | PASS | Zero lenient passes produce `NaN` submaterial rate, not zero (`lines 521-533`); `_mde_equal()` handles NaN/None comparisons (`lines 478-484`). |
| `python/experiments/EXP-007/code/run_experiment.py` | Holdout exclusion | PASS | Only EXP-003 and EXP-006 result CSVs are read (`lines 47-56`, `211-221`, `389-392`, `447`, `544`, `577-579`); no source market data or holdout path exists. |
| `python/experiments/EXP-007/code/run_experiment.py` | Loader ordering | PASS | Not applicable to source data; all inputs are holdout-safe result artifacts from EXP-003/EXP-006. |
| `python/experiments/EXP-007/code/run_experiment.py` | Memory/performance | PASS | Uses Polars scans and group-bys; plots convert only bounded summary frames to pandas (`lines 657-739`). |
| `python/experiments/EXP-007/code/run_experiment.py` | Safe optimization | PASS | Boolean vectorization preserves draw membership, denominators, effect/CI fields, and L1-L4 states. |
| `python/experiments/EXP-007/code/run_experiment.py` | Progress tracking | PASS | No long Python loop over raw draws; loops operate on grouped summaries. |
| `python/experiments/EXP-007/code/run_experiment.py` | Logging/output | PASS | Four concise INFO lines in `main()` (`lines 838-841`). |
| `python/experiments/EXP-007/code/run_experiment.py` | Organization/import side effects | PASS | Output directories are created only inside `main()` through `ensure_output_dirs()` (`lines 112-115`, `746-751`). |
| `python/experiments/EXP-007/code/run_experiment.py` | Plot data reuse | PASS | Plots use summary rows, not the 216,000-row draw table (`lines 655-739`). |
| `python/experiments/EXP-007/code/run_experiment.py` | Docstrings | PASS | Public helpers have useful docstrings. |

## Numerical Validation

### Spot Checks

Independent CSV aggregation of `lenient_draw_verdicts.csv` found:

- Total lenient draw rows: `216,000`, matching `gate_draw_rows`.
- `5m`, alpha `0.05`, null rows: `0 / 4000` lenient passes, FPR `0.0`.
- `5m`, alpha `0.05`, positive `0.5` bps rows: `2000 / 2000` lenient passes, TPR `1.0`.
- `1h`, alpha `0.05`, positive `2.0` bps rows: `1848 / 2000` lenient passes, TPR `0.924`.
- `4h`, alpha `0.05`, positive `8.0` bps rows: `1804 / 2000` lenient passes, TPR `0.902`.
- Internal lenient vs drop-L5 mismatches: `0`.

`structural_equivalence_check.csv` has 9 domain/alpha rows with `0` lenient-vs-drop-L5 mismatches, `0` lenient-vs-EXP-006-tau0 mismatches, `0` unmatched EXP-006 tau0 rows, and all MDE equality flags true.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| FPR denominators | 4000 per domain/alpha/variant | min `4000`, max `4000` | YES |
| TPR denominators | 2000 per domain/alpha/edge/variant | min `2000`, max `2000` | YES |
| FPR Wilson half-width | <= 0.03 | max `0.000480` | YES |
| TPR half-width at alpha0 lenient MDE | <= 0.05 | 5m `0.000959`, 1h `0.011631`, 4h `0.013041` | YES |
| MDE statuses | PASS or declared inconclusive | `PASS` in all 18 strict/lenient rows | YES |
| Structural mismatches | 0 | 0 | YES |
| Submaterial rate | [0, 1] or NaN for zero passes | all finite rates in [0, 1] for observed passes | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| alpha0 lenient FPR | `0/4000` for 5m, 1h, 4h | YES | Lenient L5 does not admit null passes because other gate legs remain binding. |
| alpha0 lenient MDE | 5m `0.5`, 1h `2.0`, 4h `8.0` bps | YES | Matches EXP-006 tau=0 endpoint exactly. |
| alpha0 strict MDE | 5m `1.0`, 1h `4.0`, 4h `12.0` bps | YES | Recomputed strict rows match EXP-003 strict reference. |
| alpha0 submaterial at lenient MDE | 5m `0.4965`, 1h `0.054654`, 4h `0.0` | YES | Required D-lenientL5 economic-quality accounting is present and below the 0.50 cutoff at the MDE. |
| Headline verdict | `EVIDENCE_AGAINST_NO_STRUCTURAL_GAIN` in all domains | YES | Lenient equals the EXP-006 zero-buffer frontier, so it cannot improve beyond that frontier. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Dependency reuse | EXP-001, EXP-003, and EXP-006 are valid dependencies | YES | Metadata records EXP-001 `PASS`, EXP-003 `COMPLETE`, EXP-006 `COMPLETE` with `strict_reference_pass: true`. |
| Lenient reconstruction | `L5_lenient = ci_lower_bps > 0.0` and L1-L4 unchanged | YES | Code `lines 204-220`; frozen harness L3/L5 definitions in `python/src/xen/referee_calibration.py:1037-1038`. |
| Structural equivalence | Lenient == drop-L5 == EXP-006 tau=0 | YES | Verdict-level mismatch and unmatched counts are all zero across 9 domain/alpha cells. |
| Submaterial accounting | Rate denominator is lenient positive passes per domain/alpha/edge | YES | `submaterial_pass_rates.csv` includes 90 full-grid rows; zero-pass cells would be retained as NaN by code. |

## Results Plausibility

Outputs match the corrected pre-results scope: lenient L5 lowers strict MDE while keeping FPR at zero, but it does so exactly by landing on the EXP-006 zero-buffer threshold endpoint. Generated plots exist and are valid PNGs:

- `plots/mde_comparison.png`
- `plots/fpr_comparison.png`
- `plots/tpr_strict_vs_lenient.png`
- `plots/submaterial_heatmap.png`

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 4 / 4 tests, 4 / 4 plots, 0 / 0 new modules
- Holdout exclusion verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Pre-execution dependency banner is historical**
   - Description: `governance/pre-execution-review.md` records that EXP-007's manual execution gate was blocked until EXP-006 completed. Runtime metadata now confirms EXP-006 completed and `strict_reference_pass` was true before EXP-007 measurement, so this historical banner does not affect interpretation.

2. **Refuted hypothesis is an expected measurement outcome**
   - Description: The headline `EVIDENCE_AGAINST_NO_STRUCTURAL_GAIN` is not a run failure. The scope predeclared that exact structural falsification would be the expected result if lenient L5 equaled EXP-006 `tau=0`.

## Re-Audit Requirements

None.
