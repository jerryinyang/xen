# Audit Report: Experiment EXP-012

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-012/code/run_experiment.py` | Scope compliance | PASS | The implementation stays within the approved readiness scope: inventory, NY-window coverage, missing-bar diagnostics, active-session summaries, and cost-field availability. |
| `python/experiments/EXP-012/code/run_experiment.py` | Holdout exclusion | PASS | `load_analysis_timebars()` now computes row count lazily, then collects only `scan.sort("CloseTime").slice(0, analysis_rows)`. The loader returns exactly the analysis-set row count and does not materialize the holdout. |
| `python/experiments/EXP-012/code/run_experiment.py` | Loader ordering | PASS | Rows are ordered by `CloseTime` before the first-70-percent cutoff. |
| `python/experiments/EXP-012/code/run_experiment.py` | Timezone/window logic | PASS | The UTC-to-NY assumption and close-time boundary rule are explicit in both code and saved outputs. |
| `python/experiments/EXP-012/code/run_experiment.py` | Memory/performance | PASS | Large inputs stay in a lazy scan until the holdout-excluded slice is collected; plots are built from aggregated summaries. |
| `python/experiments/EXP-012/code/run_experiment.py` | Logging/output | PASS | Manual-run output is concise and traceable. |
| `python/experiments/EXP-012/code/run_experiment.py` | Organization/import side effects | PASS | Imports, constants, helpers, orchestration, and `main()` are separated; output directories are created in orchestration only. |
| `python/experiments/EXP-012/code/run_experiment.py` | Plot data reuse | PASS | Plots are generated from summary tables instead of a second heavy source-data pass. |
| `python/experiments/EXP-012/code/run_experiment.py` | Docstrings/type hints | PASS | Public helpers are typed and documented proportionately to the scope. |

## Numerical Validation

### Spot Checks

- Summing `python/experiments/EXP-012/results/macro_window_coverage_summary.csv` by `Instrument`, `Segment`, and `Family` exactly reproduces every row in `python/experiments/EXP-012/results/macro_family_coverage_summary.csv` (`16/16` matches).
- A direct loader check using the fixed `load_analysis_timebars("EURUSD")` returns `total_rows=1,246,061`, `analysis_rows=872,242`, `train_rows=610,569`, and `loaded_rows=872,242`, confirming that only analysis rows are materialized.
- A bounded raw-data check on the holdout-excluded EURUSD analysis rows reproduces the saved AM1 coverage inputs: weekday trading-day counts `Train=430`, `Test=185`, and observed AM1 bars `Train=8,559`, `Test=3,660`. These imply the saved expected denominators `8,600` and `3,700` in `macro_window_coverage_summary.csv`.
- A schema check on `data/timebars/timebars_eurusd_20230102_000000_20260514_203330.parquet` returns only the documented eight OHLCV columns: `Symbol`, `OpenTime`, `CloseTime`, `Open`, `High`, `Low`, `Close`, `TickVolume`. This matches `python/experiments/EXP-012/results/cost_data_availability.csv`, which correctly reports the absence of `Bid`, `Ask`, `Spread`, `Commission`, and `Slippage`.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|----------------|--------------|-------|
| CoverageRatio | [0, 1] | [0.9459, 1.0000] | YES |
| DuplicateCloseTimeRows | 0 or small non-negative int | [0, 0] | YES |
| OHLCIntegrityFailures | 0 or small non-negative int | [0, 0] | YES |
| MissingRateWithinObservedSpan | [0, 1] | [0.0052, 0.0414] | YES |
| Cost-field availability flags | {True, False} | all `False` | YES |

### Statistical Sanity

The saved coverage values are plausible for a descriptive readiness gate. All macro-family coverage ratios exceed the scoped `0.80` threshold, with the weakest family still materially above it (`USTEC Test PM = 0.9459`). PM coverage is consistently weaker than AM coverage for `USTEC` and `XAUUSD`, which matches the session-shape pattern implied by the hourly-presence summaries.

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| NY-time conversion | Naive `CloseTime` values can be treated as UTC before conversion to `America/New_York` | PARTIAL | The assumption is explicit in `scope.md`, `analysis-plan.md`, code, and `results/numerical_summary.txt`, but the repository does not contain external broker timezone metadata to prove it independently. |
| Macro-window denominator | Weekend dates should be excluded from macro-window expected-bar denominators | YES | `build_daily_window_coverage()` filters to Monday-Friday before building the date-window grid, and the saved coverage summaries match that rule. |
| Cost readiness | Missing transaction-cost fields may be represented as labelled proxy scenarios | YES | The scope approved proxy scenarios only as later scenario inputs; no cost haircut is applied to current readiness outputs. |

## Results Plausibility

The output package is internally coherent. Coverage tables reconcile exactly, schema-derived cost-field absence matches the dataset reference, and the reported missing-bar rates are within a plausible range for mixed FX, commodity, crypto, and index CFD feeds.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 0 tests / 0-1, 2 plots / 4, 1 module / 1
- Holdout exclusion verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Saved summaries are internally consistent**
   - Description: Family-level coverage totals reconcile exactly with the per-window tables, and bounded source-bar checks reproduce the saved EURUSD AM1 denominator and observed-bar counts.

2. **Timezone boundary choice is explicit and reproducible**
   - Description: The run consistently uses `CloseTimeNY` minute membership, with the 1-minute boundary offset relative to open-time logic documented in both machine-readable and human-readable outputs.

## Re-Audit Requirements

None.
