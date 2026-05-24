# Audit Report: Experiment EXP-013

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

EXP-013 is interpretable after the rerun. The primary ATR-normalized range comparison is implemented on holdout-excluded 1-minute time bars, uses fixed macro windows, compares against adjacent and deterministic session-bounded random controls, and reports bootstrap intervals by instrument and segment.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-013/code/run_experiment.py` | Scope compliance | PASS | Implements fixed EXP-012 macro windows, adjacent controls, deterministic random controls, primary ATR-normalized range, and scoped secondary metrics. |
| `python/src/ict_timebar.py` | Holdout exclusion | PASS | `load_analysis_timebars()` uses lazy scan, sorts by `CloseTime`, slices first 70%, then collects. |
| `python/experiments/EXP-013/code/run_experiment.py` | Look-ahead prevention | PASS | ATR normalization uses the bar before window start; ONH/ONL are excluded before 09:30. |
| `python/experiments/EXP-013/code/run_experiment.py` | Timestamp alignment | PASS | Window membership uses NY minute derived from `CloseTimeNY`; no chart-type or bar-index cross-view alignment is used. |
| `python/experiments/EXP-013/code/run_experiment.py` | Randomness | PASS | Random controls use deterministic per-instrument/date/window hash seeds. |
| `python/experiments/EXP-013/code/run_experiment.py` | Plot memory | PASS | Plots use window observations and effect summaries, not raw full time-bar frames. |

## Numerical Validation

### Spot Checks

- Macro observation date counts are present by train/test segment: BTCUSD `478/163`, EURUSD `430/185`, USTEC `428/185`, XAUUSD `428/183`.
- `primary_effects.csv` contains both scoped control families, `AdjacentMean` and `RandomControl`, for every instrument and train/test segment.
- All 16 primary comparison rows have `SupportsPrimaryCriterion=False`, matching the support summary of `0/4` supporting instruments.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|----------------|--------------|-------|
| `CoverageRatio` | 0 to near 1 for fixed windows | Primary macro means approximately 0.986 to 1.000 by instrument/segment | YES |
| `TrueRangeNormATR14` | Non-negative when ATR is finite | Positive medians in all primary groups | YES |
| `SweepOccurred` | 0 or 1 | Macro sweep means are 0.0 for all instrument/segment rows | YES |
| `DisplacementOccurred` | 0 or 1 | Macro means are finite and between 0 and 1 | YES |
| `ForwardReturn10m/20m/60m` | Real-valued | Values are small return ratios with mixed signs | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|---------------------|-------|
| Primary pass count | `0/16` comparison rows | YES | No row has both a strictly positive CI and median difference `>= 0.10 ATR`. |
| BTCUSD test vs AdjacentMean | mean `-0.3547`, CI `[-0.5434, -0.1621]` | YES | Macro windows are lower range than this control, so they cannot support H1. |
| EURUSD test vs AdjacentMean | mean `+0.1791`, CI `[-0.0727, 0.4136]` | YES | Positive median but interval includes zero, so it fails the predefined criterion. |

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none affecting the primary test
- Complexity budget: 2 tests / 2, 3 plots / 4, 1 shared module / 1
- Holdout exclusion verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Secondary sweep frequency is descriptive only**
   - Macro sweep means are zero under the scoped window-level sweep definition. This is useful context but does not drive the H1 verdict.

## Re-Audit Requirements

None.
