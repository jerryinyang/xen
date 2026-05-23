# Audit Report: Experiment EXP-011

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 3

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-011/code/run_experiment.py` | Correctness | PASS | Thin runner delegates to `run_signal_quality_experiment("EXP-011")`. |
| `python/src/signal_quality.py` | Scope compliance | PASS | `run_exp011()` computes only the three approved Renko-native features and no composite score or post-hoc feature selection. |
| `python/src/signal_quality.py` | Holdout exclusion | PASS | Time bars are sorted by `CloseTime`, sliced to the first 70%, then used for aggregation and Renko generation. |
| `python/src/signal_quality.py` | Train-only boundaries | PASS | `label_event_native_regime()` computes tercile boundaries from rows with `SignalTime <= train_end_time`, then applies them unchanged. |
| `python/src/signal_quality.py` | Look-ahead prevention | PASS | Rolling event-density and source-count features use same-or-prior timestamps; `BrickToATR` uses ATR available at the aligned event timestamp. |
| `python/src/signal_quality.py` | Synthetic price discipline | PASS | Renko construction prices are used only for the approved `BrickToATR` diagnostic feature; FE/AE outcomes use real 1-minute prices. |
| `python/src/signal_quality.py` | Timestamp alignment | PASS | Renko events align to time-bar regimes and outcomes through `SourceCloseTime`; no bar-index alignment is used. |
| `python/src/signal_quality.py` | NaN and edge cases | PASS | Missing ATR/regime values are represented explicitly and excluded from boundary comparisons where needed. |

## Numerical Validation

### Spot Checks

- Direction domain in `results/signal_metrics.parquet`: min `-1`, max `1`.
- Real-price resolution: `4,158,321 / 4,158,321` rows resolved.
- Precision flag is bounded: min `0`, max `1`.
- Feature boundaries are present for all 3 features x 4 instruments x 2 timeframes.
- Same-timestamp Renko rows are preserved and reported; maximum duplicate timestamp share is about `35.2%`.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|----------------|--------------|-------|
| Direction | {-1, 1} | [-1, 1] | YES |
| FE60 | >= 0 | [0.0, finite] | YES |
| AE60 | >= 0 | [0.0, 298.667] | YES |
| HybridRate | [0, 1] | [0.564, 0.788] at 15m | YES |
| MissedTransitionRate | [0, 1] | [0.324, 0.759] at 15m | YES |

### Statistical Sanity

Event-native labels show high disagreement with time-bar regimes. At 15 minutes, agreement ranges from `0.211` to `0.436`; hybrid rates range from `0.564` to `0.788`. `BrickToATR` has the lowest missed-transition rates in many cases (`0.324-0.407` at 15 minutes), but with high hybrid rates (`0.750-0.788`).

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 3 feature-specific comparison families / 3, 5 plots / 5, 0 shared modules / 0
- Holdout exclusion verified: YES
- Train-only feature boundary calibration verified: YES
- Synthetic-price discipline verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Discrete feature boundaries can collapse strata**
   - Description: Some train terciles are tied, such as 1-minute `BrickToATR` with Q1=Q2=`1.0` and EURUSD 15-minute event density with Q1=Q2=`2.0`.
   - Impact: This is expected for discrete Renko-native features, but interpretation should note sparse or missing medium strata where they occur.

2. **Same-timestamp Renko duplicates are material**
   - Description: Duplicate timestamp shares reach about `35%`.
   - Impact: The denominator policy is explicit and approved; results should not be interpreted as unique timestamp counts.

3. **Boundary metrics are descriptive rates, not optimized scores**
   - Description: The experiment reports feature-specific hybrid, missed-transition, and agreement rates independently.
   - Impact: This matches scope; no best feature should be selected from signal-quality stratification alone.

## Re-Audit Requirements

None.
