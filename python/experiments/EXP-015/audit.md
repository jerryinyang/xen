# Audit Report: Experiment EXP-015

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

EXP-015 can be interpreted. The implementation matches the approved sweep-only scope, excludes the global holdout through `load_analysis_timebars()`, uses real 1-minute OHLC prices for all forward outcomes, and writes the planned primary and secondary outputs. I did not rerun the full experiment code inside the pipeline; validation used code inspection and lightweight checks over generated result files.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-015/code/run_experiment.py` | Correctness | PASS | Sweep/breach events are mutually exclusive first touches per `NYDate` and `LevelType`; high and low definitions match scope. |
| `python/experiments/EXP-015/code/run_experiment.py` | Edge cases | PASS | Empty event sets, zero/negative risk, same-bar ambiguous target/stop hits, and missing horizon bars are handled explicitly. |
| `python/experiments/EXP-015/code/run_experiment.py` | Type safety | PASS | Public functions have type hints and docstrings. |
| `python/experiments/EXP-015/code/run_experiment.py` | NaN handling | PASS | ATR nulls are bounded through the precision-step floor; ambiguous hits are set to NaN for hit-probability comparisons. |
| `python/experiments/EXP-015/code/run_experiment.py` | Holdout exclusion | PASS | Data enters through `load_analysis_timebars()` before feature/event construction. |
| `python/src/ict_timebar.py` | Loader ordering | PASS | Polars scan selects scoped columns, sorts by `CloseTime`, slices the first 70%, then collects the analysis set. |
| `python/experiments/EXP-015/code/run_experiment.py` | Memory/performance | PASS | Result tables are bounded event-level outputs; plotting reuses in-memory analysis results. |
| `python/experiments/EXP-015/code/run_experiment.py` | Logging/output | PASS | Helper functions do not print; orchestration prints a concise completion summary. |
| `python/experiments/EXP-015/code/run_experiment.py` | Organization/import side effects | PASS | Output directory creation is inside `run_experiment()`, not import-time code. |
| `python/experiments/EXP-015/code/run_experiment.py` | Plot data reuse | PASS | Plots are generated from computed `events` and `effects`, not by reloading data. |
| `python/experiments/EXP-015/code/run_experiment.py` | Docstrings | PASS | Public and core helper functions have useful docstrings. |

## Numerical Validation

### Spot Checks

The generated `sweep_events.csv` has 4,837 event rows: 3,456 train and 1,381 test. Event types total 1,721 `Sweep` and 3,116 `Breach`.

Primary means recomputed from `sweep_events.csv` after excluding `Ambiguous60=True` and missing `Hit1R_60m` match `primary_effects.csv` counts and means:

| Instrument | Segment | Sweep N | Sweep Mean | Breach N | Breach Mean | Point Diff |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| EURUSD | Train | 236 | 0.504 | 341 | 0.566 | -0.062 |
| EURUSD | Test | 84 | 0.607 | 142 | 0.472 | +0.135 |
| XAUUSD | Train | 249 | 0.470 | 361 | 0.482 | -0.012 |
| XAUUSD | Test | 116 | 0.491 | 131 | 0.519 | -0.028 |
| BTCUSD | Train | 354 | 0.480 | 336 | 0.521 | -0.041 |
| BTCUSD | Test | 86 | 0.453 | 142 | 0.570 | -0.117 |
| USTEC | Train | 333 | 0.477 | 330 | 0.467 | +0.011 |
| USTEC | Test | 144 | 0.444 | 144 | 0.396 | +0.049 |

The `Diff` column in `primary_effects.csv` is the mean of bootstrap replicate differences, so it differs slightly from the direct point difference. That is consistent with `bootstrap_primary_diff()`.

### Range Checks

| Metric | Expected Range | Actual Range / Count | Pass? |
|--------|---------------|----------------------|-------|
| `EventType` | `Sweep`, `Breach` | Both present; no other labels observed | YES |
| `Risk1R` | `> 0` | 0 rows with `Risk1R <= 0` | YES |
| `Ambiguous60` handling | Ambiguous rows excluded from primary hit rates | 1,308 ambiguous rows equal 1,308 missing `Hit1R_60m` values | YES |
| Test sweep event count gate | >=100 total, or >=50 balanced high/low | All 4 instruments pass by total or balanced split | YES |
| Plots | 4 scoped PNGs | All 4 files present and non-empty | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|---------------------|-------|
| Supporting instruments | 1/4 | YES | Scope required at least 3 instruments; only EURUSD test passes. |
| EURUSD Test primary CI | `[0.001, 0.267]` | YES | Positive but borderline lower bound; train segment is negative. |
| XAUUSD Test primary CI | `[-0.151, 0.095]` | YES | Crosses zero and point estimate is negative. |
| BTCUSD Test primary CI | `[-0.250, 0.018]` | YES | Crosses zero and point estimate is materially negative. |
| USTEC Test primary CI | `[-0.063, 0.160]` | YES | Crosses zero despite positive point estimate. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|------------|--------|----------|
| Sweep detection | PDH/PDL and ONH/ONL are already reproducible | YES | EXP-014 approved the inherited level definitions. |
| ATR buffer | ATR uses only prior information | YES | `ATR14Prior` is shifted by one bar in `add_bar_diagnostics()`. |
| ONH/ONL eligibility | Overnight levels are not usable before 09:30 NY | YES | `_build_level_events()` requires `NYMinuteOfDay >= 570` for ONH/ONL. |
| Forward outcome measurement | No event-bar or future-before-event leakage | YES | `searchsorted(..., side="right")` starts outcomes after event `CloseTime`. |
| Bootstrap comparison | Event resampling is sufficient for the scoped descriptive test | PARTIAL | Event dependence is not modeled, but the plan selected simple non-parametric intervals for a component study. |

## Results Plausibility

Primary outcomes are plausible and internally consistent. Event counts are adequate across all instruments, but only EURUSD test has a positive confidence interval excluding zero. Secondary outputs do not contradict the primary conclusion: test-segment sweep MFE is far lower than breach MFE on all four instruments, while sweep MAE is also lower; the scoped primary hit-probability criterion is therefore a narrow failed-breakout test, not a broad excursion dominance result.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 2-3 tests / 3 planned, 4 plots / 5 planned, 1 modified shared module / 2 allowed
- Holdout exclusion verified: YES
- Real-price outcome discipline verified: YES
- Timestamp alignment verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Bootstrap `Diff` is not the direct point estimate**
   - Description: `primary_effects.csv` reports `Diff` as the mean of bootstrap replicate differences, not `SweepMean - BreachMean`. The difference is small and does not affect the verdict.

2. **Secondary excursion magnitudes are large**
   - Description: Some MFE/MAE R-multiple means are high because initial risk can be small relative to 60-minute movement. Plots cap display values at 8R, but raw secondary tables preserve full values.

## Re-Audit Requirements

None.
