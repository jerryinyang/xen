# Audit Report: Experiment EXP-034

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Scope compliance | PASS | Implements the readiness-only Prior-Range Location survey: 1h/4h, lookback 20, fixed 0.20/0.80 buckets, strict and 0.90 tolerant aggregation, no returns or P&L. |
| `code/run_experiment.py` | Holdout exclusion | PASS | Loads data through `load_analysis_timebars`, which sorts by `CloseTime` and collects only the first 70 percent before aggregation. |
| `code/run_experiment.py` | Look-ahead prevention | PASS | `PriorHigh`/`PriorLow` use rolling 20-bar high/low shifted by one bar; feature at bar `i` uses only completed prior same-timeframe bars and the bar-`i` close. |
| `code/run_experiment.py` | Timestamp alignment | PASS | Strict-vs-tolerant comparison joins by `CloseTime`; no cross-view bar-index alignment. |
| `code/run_experiment.py` | Real-price discipline | PASS | No outcome metric is computed; only aggregated real OHLC is used to build the descriptor. |
| `code/run_experiment.py` | Edge cases / NaN handling | PASS | Initial insufficient-lookback and non-positive denominators are excluded from buckets; finite eligible locations are checked. |
| `code/run_experiment.py` | Memory/performance | PASS | Plot inputs are aggregated feature/readiness tables; no full holdout or unbounded plotting conversion. |
| `python/src/bar_aggregator.py` | Backward compatibility | PASS | `min_coverage=None` preserves strict exactly-`N` behavior; tolerant mode is opt-in and validates `0 < min_coverage <= 1`. |
| `python/src/bar_aggregator.py` | Ordering | PASS | Sorts source bars by `CloseTime` before clock-bucket aggregation and returns sorted output. |

## Numerical Validation

### Spot Checks

- Coverage arithmetic matches output. For `EURUSD 1h`, `1 - 12628 / 14537 = 0.1313200798`, matching `StrictDroppedRate` in `results/coverage_stability.csv`.
- Readiness row example: `EURUSD 1h strict Train` has bottom/middle/top rows `1907/4745/2167`, all above the train row floor of 100, and episodes `431/894/482`, all above the train episode floor of 30.
- Binding low-count example still passes: `BTCUSD 4h strict Test` has bottom/middle/top rows `155/638/302` and episodes `49/111/63`, all above the test floors of 50 rows and 15 episodes.
- All 32 readiness rows have `Check1Determinism=True`, `Check2RowFloor=True`, `Check3EpisodeFloor=True`, `Check4DenominatorValid=True`, and `PassesAllChecks=True`.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|----------------|--------------|-------|
| Strict bucket rows | `>= 50` in test, `>= 100` in train for pass cells | min row count 118, max 7324 | YES |
| Strict bucket episodes | `>= 15` in test, `>= 30` in train for pass cells | min episode count 35, max 1244 | YES |
| Outside-range rate | `[0, 1]` | 0.0802 to 0.1451 strict | YES |
| Degenerate share | `[0, 1]` | 0.0 to 0.01035 strict | YES |
| Determinism digest checks | all true for trusted output | all true | YES |

### Statistical Sanity

No inferential statistics were scoped or run. The exact counts and deterministic hashes are sufficient for the readiness question.

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|------------|--------|----------|
| Chronological split | Financial data must not be randomized for train/test | YES | Aggregated rows are split chronologically after holdout-excluded aggregation. |
| Prior-range location | Feature should use prior range only | YES | Rolling max/min is shifted by one bar. |
| Episode counts | Adjacent bars are serially dependent | YES | Episode floors, not row floors alone, are the binding denominator. |
| Coverage stability | Tolerant aggregation can perturb the prior-20 range | YES | Matched strict/tolerant bucket stability is reported by `CloseTime`. |

## Results Plausibility

The output is internally coherent. Strict aggregation passes all readiness checks on all four instruments at both `1h` and `4h`, so the predeclared canonical rule selects strict aggregation for both timeframes. Tolerant aggregation lowers dropped-window rates, but it is not needed for readiness; its lower stability on `EURUSD 4h` and `BTCUSD 4h` therefore does not affect the canonical verdict.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 0 statistical tests / 0 budgeted, 4 plots / 4 budgeted, 0 new analytical modules / 0 budgeted
- Holdout exclusion verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Tolerant dropped-window denominator can be slightly negative**
   - File: `results/coverage_stability.csv`, line 4
   - Description: `XAUUSD 1h` has `TolerantDroppedRate=-0.00072` because the predeclared denominator is `floor(source_1m_rows / period_minutes)`, while tolerant clock-aligned retention can keep more partial windows than that row-count denominator.
   - Impact: No verdict impact. Strict aggregation already passes on all instruments and is canonical for both timeframes; tolerant dropped rate is diagnostic only.

## Re-Audit Requirements

None.
