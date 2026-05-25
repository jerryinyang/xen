# Audit Report: Experiment EXP-016

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

EXP-016 can be interpreted as an INCONCLUSIVE component study. The implementation uses the approved EXP-012 macro windows and EXP-015 sweep definition, excludes the global holdout through `load_analysis_timebars()`, uses real 1-minute OHLC prices for all forward outcomes, and now prevents underpowered inside/outside comparisons from being marked as criterion passes. I did not rerun the full data-loading experiment workflow inside the pipeline; validation used code inspection plus a refresh of the output/statistics layer from the already-generated `sweep_events.csv`.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-016/code/run_experiment.py` | Correctness | PASS | Sweep detection matches the inherited EXP-015 first-touch definitions and labels macro membership from the event bar's own `MacroWindow`. |
| `python/experiments/EXP-016/code/run_experiment.py` | Edge cases | PASS | Empty events, zero/negative risk, missing horizon bars, same-bar ambiguous target/stop hits, and insufficient bootstrap samples are handled explicitly. |
| `python/experiments/EXP-016/code/run_experiment.py` | Type safety | PASS | Public/core functions have type hints and docstrings. |
| `python/experiments/EXP-016/code/run_experiment.py` | NaN handling | PASS | Missing hit/CI values remain unavailable in CSV and are converted to strict JSON `null` values in `results.json`. |
| `python/experiments/EXP-016/code/run_experiment.py` | Holdout exclusion | PASS | Data enters through `load_analysis_timebars()` before features, events, outcomes, and macro labels are computed. |
| `python/src/ict_timebar.py` | Loader ordering | PASS | Polars scans select scoped columns, sort by `CloseTime`, slice the first 70%, then collect. |
| `python/experiments/EXP-016/code/run_experiment.py` | Look-ahead prevention | PASS | Outcome windows start with `searchsorted(..., side="right")`, excluding the event bar itself. Macro membership is contemporaneous at event `CloseTime`. |
| `python/experiments/EXP-016/code/run_experiment.py` | Real-price discipline | PASS | Outcomes use real time-bar `High`, `Low`, and `Close` arrays; no synthetic chart prices or event-chart generators are used. |
| `python/experiments/EXP-016/code/run_experiment.py` | Memory/performance | PASS | Plotting reuses computed event/effect tables; plot inputs are grouped or clipped before plotting. |
| `python/experiments/EXP-016/code/run_experiment.py` | Logging/output | PASS | Helper functions do not print; orchestration output is concise. |
| `python/experiments/EXP-016/code/run_experiment.py` | Organization/import side effects | PASS | Output directories are created only inside `run_experiment()`. |

## Numerical Validation

### Spot Checks

Generated `sweep_events.csv` contains 4,837 events: 1,248 train sweeps, 473 test sweeps, 2,208 train breaches, and 908 test breaches. Risk units are valid: zero rows have `Risk1R <= 0`.

Inside-macro and outside-macro sweep counts match the refreshed `primary_effects.csv`:

| Instrument | Segment | Inside Sweeps | Outside Sweeps | Matched Outside | Evaluable |
| --- | ---: | ---: | ---: | ---: | --- |
| EURUSD | Train | 49 | 202 | 8 | False |
| EURUSD | Test | 24 | 65 | 2 | False |
| XAUUSD | Train | 65 | 206 | 11 | False |
| XAUUSD | Test | 27 | 104 | 4 | False |
| BTCUSD | Train | 78 | 293 | 16 | False |
| BTCUSD | Test | 21 | 72 | 1 | False |
| USTEC | Train | 60 | 295 | 10 | False |
| USTEC | Test | 34 | 126 | 12 | False |

The refreshed result tables correctly mark every instrument/segment as non-evaluable for threshold-pass purposes because no row satisfies both the inside event floor and matched-outside comparator floor.

### Range Checks

| Metric | Expected Range | Actual Range / Count | Pass? |
|--------|---------------|----------------------|-------|
| `EventType` | `Sweep`, `Breach` | Both present; no other labels observed | YES |
| `Risk1R` | `> 0` | 0 rows with `Risk1R <= 0` | YES |
| `Ambiguous60` handling | Ambiguous hits excluded from hit-rate arrays | 1,308 ambiguous rows | YES |
| `results.json` | Strict JSON | `python -m json.tool` parses successfully | YES |
| Plots | 4 scoped PNGs | All 4 files present | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|---------------------|-------|
| Final verdict | `INCONCLUSIVE` | YES | 0/4 instruments meet both train/test inside and matched-outside floors. |
| Test inside counts | 21-34 | YES | Below the `>=50` floor for all instruments. |
| Test matched-outside counts | 1-12 | YES | Too sparse for stable matched bootstrap inference. |
| Test hit CIs | Wide or unavailable | YES | Reflects small matched comparator samples. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|------------|--------|----------|
| Macro labeling | Macro membership is knowable at event close | YES | `MacroWindow` comes from the event row's NY time features. |
| Matched outside baseline | Same-day instrument/side matching reduces date/session confounding | PARTIAL | Matching is implemented, but it removes most outside events and leaves too few comparators. |
| Bootstrap intervals | Event-level resampling is sufficient for a component comparison | PARTIAL | Non-parametric intervals are appropriate, but sample sizes are below the floor for interpretation. |
| Outcome measurement | Forward outcomes use only post-event bars | YES | `searchsorted(..., side="right")` starts after event `CloseTime`. |

## Results Plausibility

The inconclusive result is plausible: macro windows cover narrow time slices, so inside-window sweeps are sparse. Same-day matched outside sweeps are even sparser because most outside sweeps occur on dates without same-side inside macro sweeps.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none after repair; the matched-outside comparator floor is now explicit in scope, plan, code, and result metadata.
- Complexity budget: 2 statistical tests / 2 budgeted; 4 plots / 4 budgeted; 0 new reusable modules / 1 budgeted.
- Holdout exclusion verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Matched outside baseline is too sparse**
   - Description: Matched outside counts are 1-12 in the test segment and 8-16 in train.
   - Impact: This is the reason the experiment is inconclusive, not a code failure.

2. **Result refresh was output-layer only**
   - Description: After code repair, result tables were refreshed from existing `sweep_events.csv` rather than re-running the full data-loading workflow.
   - Impact: This is acceptable for the repaired criterion/serialization outputs because event detection and outcomes were not changed.

## Re-Audit Requirements

No required re-audit unless sweep detection, macro labeling, or outcome computation logic changes.
