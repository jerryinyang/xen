# Audit Report: Experiment EXP-008

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

EXP-008 is a result-level reprocessing of EXP-003 draw verdicts. The implementation stays within scope, does not read market-data Parquet files, preserves EXP-003 draw denominators, and reproduces the per-instrument FPR/TPR counts from the source draw artifact with zero mismatches.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Scope compliance | PASS | Regroups EXP-003 gate-stack draw verdicts only; no new draws, market-data measurement, chart-type data, or referee changes. |
| `code/run_experiment.py` | Dependency gate | PASS | Requires EXP-001 PASS, EXP-003 COMPLETE, and EXP-003 draw/MDE artifacts before processing (`require_dependencies`, lines 81-106). |
| `code/run_experiment.py` | Holdout exclusion | PASS | No raw Parquet load path exists; EXP-003 artifacts are reused as the validated first-70%-only substrate (`load_gate_draws`, lines 112-129). |
| `code/run_experiment.py` | Denominators | PASS | Aggregates raw draw rows by instrument/domain/alpha without deduplication; per-cell null `n=1000`, positive `n=500`. |
| `code/run_experiment.py` | Numerical method | PASS | Wilson intervals and grid MDE rule match the EXP-003 definition; D-prec gates are applied before MDE reportability (lines 260-277). |
| `code/run_experiment.py` | Material comparison | PASS | Uses the frozen margin `max(0.5, 20% of pooled MDE)` and reports material, grid-resolution, and reportable flags (lines 318-379). |
| `code/run_experiment.py` | Memory/performance | PASS | Uses `pl.scan_csv(...).select(DRAW_COLS)` before collection; plotting converts only small summary frames to pandas. |
| `code/run_experiment.py` | Progress/logging | PASS | Work is a bounded grouped aggregation; no long-running row loop or noisy helper output. |
| `code/run_experiment.py` | Import side effects | PASS | Output directories are created only inside `main()` via `ensure_output_dirs` (lines 67-70, 494-501). |

## Numerical Validation

### Spot Checks

Independent reconciliation from `python/experiments/EXP-003/results/draw_verdicts.csv`:

- Gate-stack draw rows used: 216,000.
- FPR summary count mismatches vs EXP-003 source regrouping: 0.
- TPR summary count mismatches vs EXP-003 source regrouping: 0.

Alpha 0.05 FPR checks:

| Metric | Expected | Actual | Pass? |
|--------|----------|--------|-------|
| Per-instrument null denominator | 1,000 | min 1,000 / max 1,000 | YES |
| Gate FPR | `<= 0.05` | 0.0 in all 12 cells | YES |
| FPR Wilson half-width | `<= 0.03` | 0.001913 in all 12 cells | YES |
| TPR denominator per edge | 500 | min 500 / max 500 | YES |
| Max TPR Wilson half-width | `<= 0.05` at reportable MDE | 0.043182 across alpha0 TPR rows | YES |

Material alpha0 cells:

| Domain | Instrument | Per-Instrument MDE | Pooled MDE | Delta | Margin | Material? |
|--------|------------|--------------------|------------|-------|--------|-----------|
| 1h | EURUSD | 2.0 | 4.0 | -2.0 | 0.8 | YES |
| 4h | EURUSD | 8.0 | 12.0 | -4.0 | 2.4 | YES |
| 4h | XAUUSD | 8.0 | 12.0 | -4.0 | 2.4 | YES |

All other alpha0 cells are reportable and within the frozen material margin.

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|------------|--------|----------|
| Result-level regrouping | EXP-003 draw artifacts are the validated substrate | YES | Dependency gate enforces EXP-003 COMPLETE; no new market-data path is used. |
| Wilson pass rates | Draw verdict rows are counted exactly once per cell | YES | Independent FPR/TPR regrouping produced zero mismatches. |
| Grid MDE | MDE is discrete over the EXP-003 edge grid | YES | `per_instrument_mde_summary.csv` reports PASS for all 36 instrument/domain/alpha cells. |

## Results Plausibility

The outputs are internally consistent with EXP-003 and the Phase 002 H-pool scope. All 12 alpha0 cells are reportable. Three cells differ materially from the pooled domain MDE, all in the lower-MDE direction; 5m is unchanged for all instruments.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none found
- Complexity budget: 3 statistical checks / 3, 4 plots / 4, 0 new modules / 0
- Holdout exclusion verified: YES
- Referee/sample changes: none found

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Grid resolution is first-class context**
   - The non-material unchanged cells are mostly `within_grid_resolution=true`; interpretation should avoid claiming finer precision than the EXP-003 grid supports.

2. **Directional heterogeneity is descriptive**
   - The material differences are lower per-instrument MDEs, not evidence for adopting per-instrument operating points. That decision remains reserved for EXP-011 / Phase 003.

## Re-Audit Requirements

None for the original run.

## Re-Audit Addendum (2026-06-04, adversarial-review corrections F07/F08)

Two code-correctness fixes were applied and the experiment re-run:

- `within_grid_resolution` now uses the **full local grid spacing** (`grid_full_step`)
  instead of the half-step MDE uncertainty, matching analysis-plan Step 5. This does not
  change any flag value (the only non-zero deltas are one-grid-step material cells, for
  which `|delta|` equals the spacing under both the old and new band, so `within_grid`
  stays `false`).
- A `tpr_monotone` column was added to `per_instrument_mde_summary.csv`; all 36 cells
  report `true`.

The frozen predeclared material margin is **unchanged**. Re-run reproduces the original
numeric result exactly: H-pool SUPPORTED, 12/12 reportable at alpha0, 3 material cells
(EURUSD/1h, EURUSD/4h, XAUUSD/4h). Verdict remains **PASS**. The review additionally
notes (interpretation, not a defect) that the frozen margin is below one grid step, so
"material" here means "differs by >= one grid point" — recorded in results.md/report.md
Limitations.
