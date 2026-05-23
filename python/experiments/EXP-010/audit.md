# Audit Report: Experiment EXP-010

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-010/code/run_experiment.py` | Correctness | PASS | Thin runner delegates to `run_signal_quality_experiment("EXP-010")`. |
| `python/src/signal_quality.py` | Scope compliance | PASS | `run_exp010()` builds Renko primary signals, Line Break confirmation labels, 5/15/30-minute windows, and 1-minute exploratory plus 15-minute confirmatory outputs. |
| `python/src/signal_quality.py` | Holdout exclusion | PASS | Data are sorted by `CloseTime`, sliced to the first 70%, then aggregated/generated. |
| `python/src/signal_quality.py` | Look-ahead prevention | PASS | Confirmation uses same-direction Line Break `SignalTime` values in `[RenkoTime - tolerance, RenkoTime]`; no future confirmation is allowed. |
| `python/src/signal_quality.py` | Synthetic price discipline | PASS | Outcomes are evaluated from real 1-minute OHLC prices at Renko `SourceCloseTime`; Renko and Line Break construction prices are not used for FE/AE. |
| `python/src/signal_quality.py` | Timestamp alignment | PASS | Renko and Line Break signals use `SourceCloseTime`; no bar-index alignment is used. |
| `python/src/signal_quality.py` | NaN and edge cases | PASS | Empty confirmation sets, missing future windows, non-finite ATR, and zero/invalid ATR are explicitly handled. |
| `python/src/signal_quality.py` | Memory/performance | PASS | Plotting samples before pandas/seaborn rendering; output tables carry denominator diagnostics. |

## Numerical Validation

### Spot Checks

- Direction domain in `results/signal_metrics.parquet`: min `-1`, max `1`.
- Real-price resolution: `3,692,050 / 3,692,050` rows resolved.
- Precision flag is bounded: min `0`, max `1`.
- FE60 and AE60 are non-negative and finite where resolved.
- Same-timestamp Renko rows are preserved and reported; maximum duplicate timestamp share in the 15-minute confirmed sets is about `18.1%`.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|----------------|--------------|-------|
| Direction | {-1, 1} | [-1, 1] | YES |
| FE60 | >= 0 | [0.0, finite] | YES |
| AE60 | >= 0 | [0.0, 298.667] | YES |
| PrecisionHit_60m | {0, 1} | [0, 1] | YES |
| Primary 15m coverage | [0, 1] | [0.535, 0.626] | YES |

### Statistical Sanity

At the primary 15-minute confirmation window, confirmed-minus-all-Renko log FE/AE improves with a CI excluding zero only for BTCUSD (`+0.057`, CI `[+0.010, +0.183]`). EURUSD, USTEC, and XAUUSD do not meet the pre-specified criterion. Confirmed signals reduce AE60 versus non-confirmed signals on all instruments, but FE60 also falls on 3 of 4 instruments.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 4 comparison families / 4, 5 plots / 5, 0 shared modules / 0
- Holdout exclusion verified: YES
- Synthetic-price discipline verified: YES
- 1-minute arm treated as exploratory: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Same-timestamp Renko duplicates are material**
   - Description: Duplicate timestamp shares reach about `18%` in 15-minute confirmed Renko subsets.
   - Impact: The denominator policy is explicit and matches the pre-execution review, but interpretation should avoid treating rows as unique timestamps.

2. **Line Break confirmation is mainly a coverage selector**
   - Description: Primary 15-minute Line Break confirmation coverage is `53.5-62.6%`.
   - Impact: This is expected from the scope; results should emphasize coverage cost before subset quality.

## Re-Audit Requirements

None.
