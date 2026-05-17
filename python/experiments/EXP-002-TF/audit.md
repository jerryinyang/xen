# Audit Report: Experiment EXP-002-TF

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 1
- **Info Notes**: 2

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/src/timeframe_replication.py` (run_exp002_tf) | Correctness | PASS | Hybrid rate, transition lag, and verdict logic implemented correctly. |
| `python/src/timeframe_replication.py` (event_hybrid_rate) | Edge cases | PASS | Returns (0.0, valid, 0) for Time/HA; handles empty tables. |
| `python/src/timeframe_replication.py` (transition_lags) | Type safety | PASS | Returns tuple of DataFrame and dict; uses `np.nan` for missing values. |
| `python/src/timeframe_replication.py` (run_exp002_tf) | NaN handling | PASS | `float("nan")` for empty lag summaries; `np.nan` in lag DataFrame. |
| `python/src/timeframe_replication.py` (load_source_analysis) | Holdout exclusion | PASS | Lazy scan sorts by `CloseTime`, slices first 70% before `.collect()`. |
| `python/src/timeframe_replication.py` (load_timeframes) | Memory/performance | PASS | Lazy loading; plotting uses aggregates. |
| `python/src/timeframe_replication.py` (run_exp002_tf) | Logging/output | PASS | 7 CSVs + 1 JSON + 4 plots produced. |
| `python/src/timeframe_replication.py` (run_exp002_tf) | Docstrings | PASS | Public functions in shared module have docstrings. |

## Numerical Validation

### Spot Checks

**EURUSD 15m LineBreak hybrid rate:**
- HybridCount: 405, HybridDenominator: 4262
- Hybrid rate = 405 / 4262 = 0.09503 ✓ matches summary_metrics.csv

**EURUSD 15m LineBreak WithinBounds:**
- Hybrid rate 0.095 > 0.05 threshold → False ✓
- MedianLagBars = 2.0, which is <= 2.0 (passes lag bound)
- But hybrid rate fails, so WithinBounds = False ✓

**BTCUSD 1h LineBreak median lag:**
- MedianLagBars = 5.0, exceeds 2-bar bound ✓
- WithinBounds = False ✓

**Bootstrap AbsoluteHybridExcessVsTime (15m LineBreak):**
- Mean = 0.0962, CI = [0.0908, 0.1002], n=4
- All 4 instruments have hybrid rates in [0.089, 0.101], mean ≈ 0.096 ✓

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| HybridRate | [0, 1] | 0.0 to 0.2234 | YES |
| MedianLagBars | ≥ 0 | 0.0 to 5.0 | YES |
| P95LagBars | ≥ 0 | 0.0 to 304.05 | YES |
| MaxLagBars | ≥ 0 | 0.0 to 3376.0 | YES (extreme but valid) |
| TransitionCount | ≥ 0 | 265 to 21361 | YES |
| MissedTransitions | ≥ 0 | 0 to 3 | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| Bootstrap CI (15m Renko hybrid excess) | [0.141, 0.171] | YES | All 4 instruments exceed 0.05 bound |
| All verdicts | REFUTED (0/4 support) | YES | All hybrid rates exceed 0.05 bound |
| Time-bar baseline | HybridRate=0.0, MedianLag=0.0 | YES | By construction, time bars define the regime timeline |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Hybrid rate definition | Event intervals straddling multiple regimes count as "hybrid" | YES | `event_hybrid_rate` checks regime uniqueness between consecutive event timestamps |
| Transition lag | First event in new regime after transition timestamp | YES | `transition_lags` finds first event with matching regime after transition |
| Regime calibration | Train-derived terciles applied to evaluation segment only | YES | `add_timebar_regimes` calibrates on first 70%, applies only after train end |
| Temporal ordering | CloseTime-sorted before analysis | YES | Verified in loader |

## Results Plausibility

Results are plausible. Event charts (LineBreak, Renko) inherently straddle regime boundaries because they are not aligned to time-bar regime transitions. Hybrid rates of 9-22% are expected given event charts emit bars at irregular intervals. Median lag of 1-5 source bars is also expected — event charts must wait for a direction change that confirms the new regime. The REFUTED verdict is well-supported.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: None
- Complexity budget: 3 statistical tests (hybrid rate, lag, bootstrap) / 3 budgeted; 4 visualisations / 4 budgeted; 0 new modules / 1 budgeted
- Holdout exclusion verified: YES

## Issues

### Warning

1. **Max lag values extremely large for some instruments**
   - File: `python/experiments/EXP-002-TF/results/summary_metrics.csv`
   - Description: USTEC 15m LineBreak MaxLagBars = 3376.0 (~35 days at 15m). EURUSD 15m LineBreak MaxLagBars = 235.0. These represent rare events where the chart type took very long to confirm a regime transition.
   - Impact: Median lag is robust to outliers, but p95 lag may be affected. The analysis plan reports p95 and max for transparency, which is appropriate.
   - Fix: No fix needed; these are reported as diagnostics, not primary metrics.

### Info

1. **Heiken Ashi has zero hybrid rate and zero lag**
   - Description: HA has the same timestamps as time bars (1:1 mapping), so it inherits the time-bar regime timeline exactly. Hybrid rate = 0.0 and lag = 0.0 by construction.
   - Impact: HA is not part of the primary hypothesis (LineBreak vs Renko), but results are correctly reported.

2. **Bootstrap operates on n=4 instrument-level hybrid rates**
   - Description: Same limitation as EXP-001-TF. Small sample size produces wide CIs.
   - Impact: Descriptive only; not inferential.

## Re-Audit Requirements

None. Verdict is PASS.
