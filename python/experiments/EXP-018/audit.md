# Audit Report: Experiment EXP-018

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

EXP-018 can be interpreted. The implementation matches the scoped displacement definition, loads holdout-excluded bars through `load_analysis_timebars()`, evaluates all outcomes on real 1-minute OHLC prices, and writes the planned primary and secondary result tables. Validation used code inspection plus lightweight recomputation from the generated result files; I did not rerun the full experiment code inside the pipeline.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-018/code/run_experiment.py` | Correctness | PASS | Displacement requires the first post-sweep candle within 10 bars whose body is at least `1.5x` the prior 100-bar median body and whose close sits in the directional quartile, matching scope and plan. |
| `python/experiments/EXP-018/code/run_experiment.py` | Edge cases | PASS | Missing files/columns, no forward bars, no qualifying displacement, no next open, and zero-risk entries are handled explicitly. |
| `python/experiments/EXP-018/code/run_experiment.py` | Type safety | PASS | Public functions have type hints and docstrings. |
| `python/experiments/EXP-018/code/run_experiment.py` | NaN handling | PASS | Ambiguous hit rows are excluded from hit-rate summaries; zero-risk entries return NaN outcomes rather than silent infinities. |
| `python/experiments/EXP-018/code/run_experiment.py` | Holdout exclusion | PASS | Instrument bars are loaded through `python/src/ict_timebar.py::load_analysis_timebars()`, which sorts by `CloseTime`, slices the first 70%, and only then collects. |
| `python/src/ict_timebar.py` | Loader ordering | PASS | The shared loader preserves chronological slicing before collection, satisfying the holdout rule. |
| `python/experiments/EXP-018/code/run_experiment.py` | Memory/performance | PASS | One instrument at a time is loaded into pandas with only the helper columns the experiment needs; plots reuse computed results. |
| `python/experiments/EXP-018/code/run_experiment.py` | Logging/output | PASS | Helper functions do not print; orchestration writes a short completion summary only. |
| `python/experiments/EXP-018/code/run_experiment.py` | Organization/import side effects | PASS | Directory creation occurs in `run_experiment()`, not on import. |
| `python/experiments/EXP-018/code/run_experiment.py` | Plot data reuse | PASS | Plotting uses existing `events`, `misses`, `retention`, `effects`, and `filter_effects` tables rather than reloading bars. |
| `python/experiments/EXP-018/code/run_experiment.py` | Docstrings | PASS | Public and core helper functions are documented. |

## Numerical Validation

### Spot Checks

Manual recomputation from `python/experiments/EXP-015/results/sweep_events.csv` plus `python/experiments/EXP-018/results/displacement_detection.csv` matches the EURUSD test primary row in `filter_effects.csv`:

- Total EURUSD test sweeps: `89`
- Displacement-confirmed EURUSD test sweeps: `77`
- Baseline non-ambiguous `Hit1R_60m` mean: `0.6071428571`
- Confirmed-sweep non-ambiguous `Hit1R_60m` mean: `0.6301369863`
- Hit-rate difference: `+0.0229941292`
- Baseline `MAE_R_60m` median: `4.5425287356`
- Confirmed-sweep `MAE_R_60m` median: `4.1377387425`
- MAE improvement (`all - confirmed`): `+0.4047899931`

Those values match `python/experiments/EXP-018/results/filter_effects.csv`.

Train/test segment handling is also internally consistent for the scoped 10-bar confirmation window: no train-labeled EXP-018 entry rows have `DisplacementTime` after the actual train/test cutoff on any instrument.

### Range Checks

| Metric | Expected Range | Actual Range / Count | Pass? |
|--------|---------------|----------------------|-------|
| Confirmed delay | 1-10 bars by scope | 1 to 10 on confirmed rows | YES |
| `Risk1R` | `> 0` for evaluable outcomes | 1 zero-risk raw row; all zero-risk outcomes are NaN and excluded from summaries | YES |
| `RetentionPct` | `[0, 1]` | `0.825` to `0.871` in test rows | YES |
| Test retention floors | >=50 confirmed or >=50% retained | 4/4 instruments pass | YES |
| Plots | 5 scoped PNGs | All 5 files present and non-empty | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|---------------------|-------|
| Instruments passing | `0/4` | YES | No test instrument clears the interval-based support threshold. |
| Instruments refuting | `0/4` | YES | Wide intervals mean the result stays inconclusive rather than cleanly negative. |
| EURUSD Test paired delay hit effect | `-0.159`, CI `[-0.304, -0.014]` | YES | Waiting for displacement can worsen entry quality even when confirmed-sweep filtering looks mildly positive. |
| USTEC Test filter hit effect | `+0.001`, CI `[-0.036, 0.039]` | YES | Essentially null effect with adequate counts is consistent with the verdict. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|------------|--------|----------|
| Displacement detection | Body/close-location features use prior-known data only | YES | `BodyMedian100Prior` and `ATR14Prior` are shifted one bar in the shared diagnostics. |
| Outcome measurement | No event-bar leakage | YES | `compute_real_price_outcome()` starts from `CloseTime > EntryTime`. |
| Real-price discipline | Outcomes use time-bar OHLC, not synthetic prices | YES | All outcomes come from `High`, `Low`, and `Close` on the canonical 1-minute bars. |
| Nested bootstrap | Confirmed sweeps are a subset of the full sweep universe | YES | `compute_filter_effects()` uses a nested-subset bootstrap on the full EXP-015 sweep population. |

## Results Plausibility

The result pattern is coherent. The displacement filter retains most events on every test instrument and often improves point estimates, but the confidence intervals remain wide and the paired delay-cost diagnostic is negative on two instruments. That supports the reported INCONCLUSIVE verdict.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 2 primary tests plus 1 secondary diagnostic / 3 allowed, 5 plots / 5 allowed, 0 new shared modules / 2 allowed
- Holdout exclusion verified: YES
- Real-price outcome discipline verified: YES
- Timestamp alignment verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **One raw `NextOpen` entry has zero risk and is excluded from outcome summaries**
   - File: `python/experiments/EXP-018/results/entry_proxy_events.csv`
   - Description: EURUSD Test contains one `NextOpen` row with `Entry == Stop == 1.03726`, so `Risk1R == 0.0`.
   - Impact: `compute_real_price_outcome()` returns NaN outcomes for that row, so it stays in the raw event table but does not contribute to `ReturnN`, `HitN`, or effect calculations.
   - Reproduction: Filter `entry_proxy_events.csv` for `Risk1R <= 0`.

## Re-Audit Requirements

None.
