# Audit Report: Experiment EXP-008

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 3

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-008/code/run_experiment.py` | Correctness | PASS | Thin runner delegates to `run_signal_quality_experiment("EXP-008")`. |
| `python/src/signal_quality.py` | Scope compliance | PASS | `run_exp008()` builds all time-bar signals, Renko-confirmed time-bar signals, non-confirmed time-bar signals, raw Renko signals, and fixed 5/15/30-minute windows. |
| `python/src/signal_quality.py` | Holdout exclusion | PASS | `load_instrument_data()` sorts by `CloseTime`, slices the first 70% analysis rows, and only then aggregates/generates Renko. |
| `python/src/signal_quality.py` | Look-ahead prevention | PASS | `confirmation_mask()` only accepts same-direction Renko events in `[candidate_time - tolerance, candidate_time]`. |
| `python/src/signal_quality.py` | Synthetic price discipline | PASS | Renko construction prices are not used for outcomes; FE/AE use real 1-minute time-bar OHLC prices. |
| `python/src/signal_quality.py` | Timestamp alignment | PASS | Renko confirmation uses `SourceCloseTime` converted to `SignalTime`; no bar-index alignment is used. |
| `python/src/signal_quality.py` | NaN and edge cases | PASS | Empty sets, missing ATR, unresolved future windows, and zero/invalid ATR are represented explicitly. |
| `python/src/signal_quality.py` | Memory/performance | PASS | Time-bar metrics are evaluated once and relabelled for confirmed/non-confirmed subsets; plots sample bounded rows before rendering. |

## Numerical Validation

### Spot Checks

- Direction domain in `results/signal_metrics.parquet`: min `-1`, max `1`.
- Real-price resolution: `14,489,081 / 14,489,081` rows resolved.
- Precision flag is bounded: min `0`, max `1`.
- FE60 and AE60 are non-negative where present.
- Primary 15-minute confirmation coverage is `24.6-28.7%`.
- Raw Renko duplicate timestamp shares are reported, with 15-minute values up to `13.5%`.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|----------------|--------------|-------|
| Direction | {-1, 1} | [-1, 1] | YES |
| FE60 | >= 0 | [0.0, 640.5] | YES |
| AE60 | >= 0 | [0.0, 1281.0] | YES |
| PrecisionHit_60m | {0, 1} | [0, 1] | YES |
| Primary 15m coverage | [0, 1] | [0.246, 0.287] | YES |

### Statistical Sanity

At the primary 15-minute confirmation window, confirmed-minus-all-time AE60 is significantly negative on all four instruments (`-0.156` to `-0.598`). FE60 is also significantly negative on three instruments and inconclusive on USTEC. Log FE/AE improves significantly only on USTEC (`+0.042`, CI `[+0.020, +0.196]`) and worsens on EURUSD (`-0.073`, CI `[-0.184, -0.002]`).

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

1. **Early ATR gaps are explicit**
   - Description: `ATRAtSignal` has 116 null rows across the full output, consistent with warm-up periods.
   - Impact: Bootstrap sample sizes use finite metric rows; this does not affect trust.

2. **Coverage-adjusted table includes null-regime warm-up rows**
   - Description: BTCUSD and USTEC include null-regime reference rows with no selected confirmed signals.
   - Impact: Main regime conclusions should use Low/Medium/High rows; null rows reflect early unavailable regime labels.

3. **Raw Renko duplicate timestamps are material**
   - Description: Same-timestamp raw Renko emissions are preserved and reported, with 15-minute duplicate shares up to `13.5%`.
   - Impact: This matches the approved denominator policy; avoid treating Renko rows as unique timestamps.

## Re-Audit Requirements

None.
