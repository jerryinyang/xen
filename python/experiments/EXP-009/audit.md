# Audit Report: Experiment EXP-009

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-009/code/run_experiment.py` | Correctness | PASS | Thin runner delegates to `run_signal_quality_experiment("EXP-009")`. |
| `python/src/signal_quality.py` | Scope compliance | PASS | `run_exp009()` builds only 15-minute time-bar direction-change and HA direction-change signal sets. |
| `python/src/signal_quality.py` | Holdout exclusion | PASS | `load_instrument_data()` sorts by `CloseTime`, computes the first 70% analysis slice, and aggregates 15-minute bars only from that slice. |
| `python/src/signal_quality.py` | Synthetic price discipline | PASS | HA synthetic values are used only by `generate_heiken_ashi()` to define `Direction`; FE/AE outcomes use real 1-minute OHLC arrays in `evaluate_signals()`. |
| `python/src/signal_quality.py` | Timestamp alignment | PASS | HA and time-bar signals align by `CloseTime`; no bar-index comparison is used. |
| `python/src/signal_quality.py` | NaN and edge cases | PASS | Empty signals, missing future windows, non-finite ATR, and zero/invalid ATR are handled with explicit NaN outputs. |
| `python/src/signal_quality.py` | Memory/performance | PASS | Input loading is column-selected and sliced before aggregation; plotting samples at `PLOT_SAMPLE_N` before seaborn conversion. |
| `python/src/signal_quality.py` | Logging/output | PASS | Manual-run output is concise; generated tables carry reproducibility details in `run_manifest.json`. |

## Numerical Validation

### Spot Checks

- Direction domain in `results/signal_metrics.parquet`: min `-1`, max `1`.
- Real-price resolution: `179,376 / 179,376` rows resolved.
- Precision flag is bounded: min `0`, max `1`.
- FE60 and AE60 are non-negative; AE60 preserves zero outcomes.
- Denominator diagnostics show no duplicate signal timestamps for HA or time-bar direction-change signals.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|----------------|--------------|-------|
| Direction | {-1, 1} | [-1, 1] | YES |
| FE60 | >= 0 | [0.0, 1281.0] | YES |
| AE60 | >= 0 | [0.0, 1281.0] | YES |
| PrecisionHit_60m | {0, 1} | [0, 1] | YES |
| Duplicate timestamp share | 0 for HA/time-bar 15m changes | 0.0 | YES |

### Statistical Sanity

The primary bootstrap comparison is HA minus time-bar direction changes. No log FE/AE CI excludes zero on any instrument. Only XAUUSD FE60 excludes zero positively (`+0.034`, CI `[+0.019, +0.397]`), which is not enough to support the hypothesis and is not corroborated by log FE/AE.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 3 comparison families / 3, 4 plots / 4, 0 shared modules / 0
- Holdout exclusion verified: YES
- Synthetic-price discipline verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Observed HA coverage differs from the design rationale**
   - Description: HA direction changes are about 47.7-49.3% of time-bar direction-change counts, a larger reduction than the 27-35% rationale cited from prior direction-change compression results.
   - Impact: This is an empirical result, not a code defect; interpretation should emphasize the actual measured coverage cost.

2. **Extreme excursion values exist**
   - Description: FE60/AE60 maxima reach 1281 ATR units in the saved metrics.
   - Impact: The values are non-negative and finite, but conclusions should rely on bootstrap differences and medians/means with caveats rather than a single extreme observation.

## Re-Audit Requirements

None.
