# Audit Report: Experiment EXP-014

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

EXP-014 is interpretable after the rerun. PDH/PDL now use the prior observed weekday NY date, ONH/ONL use the approved 17:00-09:30 NY overnight window, the final 30 percent global holdout remains excluded, and all four instruments pass the predefined availability and segment-count thresholds.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/src/ict_timebar.py` | Scope compliance | PASS | `compute_liquidity_levels()` now computes PDH/PDL from weekday-only daily highs/lows and labels missing prior rows as `NO_PRIOR_WEEKDAY`. |
| `python/src/ict_timebar.py` | Holdout exclusion | PASS | `load_analysis_timebars()` uses lazy scan, sorts by `CloseTime`, slices first 70%, then collects. |
| `python/experiments/EXP-014/code/run_experiment.py` | Result labeling | PASS | Output notes match the approved prior observed weekday convention. |
| `python/experiments/EXP-014/code/run_experiment.py` | Determinism | PASS | Reversed instrument-order rerun equality is `True`. |
| `python/experiments/EXP-014/code/run_experiment.py` | Plot memory | PASS | Plots use aggregate availability and missing-reason tables. |
| `python/experiments/EXP-014/code/run_experiment.py` | Organization/import side effects | PASS | Output directories are created only in orchestration. |

## Numerical Validation

### Spot Checks

Monday rows now use the previous Friday as `PriorNYDate`:

- `EURUSD` `2023-01-09` -> `2023-01-06`
- `BTCUSD` `2023-01-09` -> `2023-01-06`
- `XAUUSD` `2023-01-09` -> `2023-01-06`
- `USTEC` `2023-01-09` -> `2023-01-06`

The first available Monday rows correctly lack a prior weekday where the dataset has no earlier weekday row.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|----------------|--------------|-------|
| `AllLevelAvailability` | 0 to 1 | 0.989 to 1.000 in train/test rows | YES |
| `AllLevelDates` | At least 50 per segment | Minimum train/test row is 163 | YES |
| Level prices | Positive real values where non-null | All inspected non-null PDH/PDL/ONH/ONL rows are positive | YES |
| `DeterministicRerunEqual` | `True` | `True` | YES |

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 0 tests / 0-1, 2 plots / 4, 1 shared module / 1
- Holdout exclusion verified: YES
- Real-price discipline: YES; no synthetic chart inputs or strategy P&L are used

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Availability margin is high after the weekday correction**
   - The correction reduced a few train PD rows but all segment thresholds remain comfortably above the scoped `>= 80%` availability and `>= 50` all-level-date criteria.

## Re-Audit Requirements

None.
