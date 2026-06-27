# Audit Report: Experiment EXP-006

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

EXP-006 is trustworthy for interpretation. The implementation is scoped result-level post-processing of EXP-003 verdict rows, no market data or holdout path is present, and the strict `tau=1.0` reconstruction reproduces EXP-003 exactly.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-006/code/run_experiment.py` | Correctness | PASS | `load_gate_draws()` filters EXP-003 to `gate_stack` rows and decodes only L1-L4 plus `materiality_bps` (`lines 136-156`); `sweep_thresholds()` changes only L5 via `ci_lower_bps > tau_bps` while preserving L1-L4 (`lines 159-185`). |
| `python/experiments/EXP-006/code/run_experiment.py` | Edge cases | PASS | Empty gate rows, missing FPR, FPR precision, uncontrolled FPR, and no MDE crossing are explicit statuses (`lines 154-155`, `306-325`). |
| `python/experiments/EXP-006/code/run_experiment.py` | Type safety | PASS | Public helpers have type hints and docstrings. |
| `python/experiments/EXP-006/code/run_experiment.py` | NaN handling | PASS | Missing/non-finite MDE is handled with `math.nan` and status fields rather than coerced to zero (`lines 306-325`). |
| `python/experiments/EXP-006/code/run_experiment.py` | Holdout exclusion | PASS | Only EXP-003 result CSVs are scanned (`lines 37-42`, `146-152`); no `data/timebars` or source market-data read exists. |
| `python/experiments/EXP-006/code/run_experiment.py` | Loader ordering | PASS | Not applicable to source data; EXP-003 already applied the chronological first-70% slice. |
| `python/experiments/EXP-006/code/run_experiment.py` | Memory/performance | PASS | The large operation is one Polars cross-join over 216,000 rows x 7 multipliers; summaries aggregate before scalar Wilson loops (`lines 172-185`, `235-258`). |
| `python/experiments/EXP-006/code/run_experiment.py` | Safe optimization | PASS | Vectorization preserves draw membership, alpha, edge, denominator, and effect/CI fields. |
| `python/experiments/EXP-006/code/run_experiment.py` | Progress tracking | PASS | No long Python loop over raw draws; loops operate only on small grouped summary frames. |
| `python/experiments/EXP-006/code/run_experiment.py` | Logging/output | PASS | Three concise INFO lines in `main()` (`lines 547-549`). |
| `python/experiments/EXP-006/code/run_experiment.py` | Organization/import side effects | PASS | Output directories are created only inside `main()` through `ensure_output_dirs()` (`lines 91-94`, `492-496`). |
| `python/experiments/EXP-006/code/run_experiment.py` | Plot data reuse | PASS | Plots consume bounded FPR/TPR/MDE summary rows, not the 1.512M-row draw file (`lines 409-486`). |
| `python/experiments/EXP-006/code/run_experiment.py` | Docstrings | PASS | Public helpers have useful docstrings. |

## Numerical Validation

### Spot Checks

Independent CSV aggregation of `threshold_draw_verdicts.csv` found:

- Total threshold rows: `1,512,000`, matching `216,000 gate_draw_rows x 7 multipliers`.
- `5m`, alpha `0.05`, strict `tau=1.0`, null rows: `0 / 4000` passes, FPR `0.0`.
- `5m`, alpha `0.05`, strict `tau=1.0`, positive `1.0` bps rows: `2000 / 2000` passes, TPR `1.0`.
- `1h`, alpha `0.05`, `tau=0.0`, positive `2.0` bps rows: `1848 / 2000` passes, TPR `0.924`.
- `4h`, alpha `0.05`, `tau=0.0`, positive `8.0` bps rows: `1804 / 2000` passes, TPR `0.902`.

The strict-reference file has 9 domain/alpha rows, `draw_mismatch_count` sums to `0`, and all `mde_match` / `draws_match` values are true.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| FPR denominators | 4000 per domain/alpha/tau | min `4000`, max `4000` | YES |
| TPR denominators | 2000 per domain/alpha/tau/edge | min `2000`, max `2000` | YES |
| FPR Wilson half-width | <= 0.03 | max `0.000480` | YES |
| TPR Wilson half-width | <= 0.05 at MDE | max across table `0.021892` | YES |
| MDE statuses | PASS or declared inconclusive | `PASS` in all 63 rows | YES |
| Strict-reference mismatches | 0 | 0 | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| alpha0 FPR | `0/4000` for every domain and threshold | YES | Lowering L5 did not admit null passes because L3/L4 remain binding on null rows. |
| alpha0 strict MDE | 5m `1.0`, 1h `4.0`, 4h `12.0` bps | YES | Matches EXP-003 strict gate reference exactly. |
| alpha0 tau=0 MDE | 5m `0.5`, 1h `2.0`, 4h `8.0` bps | YES | Sensitivity improves at the zero-buffer endpoint without FPR loss in these draws. |
| alpha0 tau=2 MDE | 5m `2.0`, 1h `8.0`, 4h `16.0` bps | YES | Higher L5 threshold reduces sensitivity as expected. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| EXP-003 result-level reuse | EXP-003 was valid and complete | YES | EXP-001 metadata `overall_status: PASS`; EXP-003 metadata `overall_status: COMPLETE`, `mde_status_counts: {PASS: 18}`. |
| Threshold reconstruction | `ci_lower_bps > multiplier * materiality_bps` changes only L5 | YES | Code keeps L1-L4 fixed (`lines 172-184`) and strict reference has zero mismatches. |
| Wilson rate summaries | Bernoulli pass-count denominators are stable | YES | FPR n `4000`; TPR n `2000`; no denominator drift by threshold. |
| MDE frontier | Grid-defined MDE, no interpolation | YES | `mde_grid_uncertainty_bps` reports prior-grid gap; all statuses PASS. |

## Results Plausibility

Outputs are internally consistent and match the active checkpoint's expectation that L5 is the stringency lever. Reducing tau lowers economic MDE in all domains at alpha0 while FPR remains zero; increasing tau raises MDE. Generated plots exist and are valid PNGs:

- `plots/fpr_vs_threshold.png`
- `plots/mde_vs_threshold.png`
- `plots/tpr_curves_by_threshold.png`
- `plots/mde_fpr_frontier.png`

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 3 / 3 tests, 4 / 4 plots, 0 / 0 new modules
- Holdout exclusion verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Large draw artifact**
   - Description: `threshold_draw_verdicts.csv` is 114 MB and intentionally contains the auditable 1.512M-row threshold reconstruction. It is written once from a Polars frame and not accumulated in Python.

2. **Zero-edge positive rows carried from EXP-003**
   - Description: Summary artifacts include the EXP-003 positive `0.0` bps edge rows because the source draw file includes them. MDE does not cross at zero, and the scoped frontier findings are unaffected.

## Re-Audit Requirements

None.
