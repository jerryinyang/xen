# Audit Report: Experiment EXP-017

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 0

EXP-017 can be interpreted. The implementation matches the approved midpoint-filter scope, reuses approved EXP-014 and EXP-015 prerequisite artifacts rather than reopening raw data, and produces the planned retention and effect tables. I did not rerun the full experiment code inside the pipeline; validation used code inspection plus lightweight recomputation from the generated prerequisite/result files.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-017/code/run_experiment.py` | Correctness | PASS | Midpoint labeling uses EXP-014 `PDH`/`PDL` on the same `NYDate`, then applies the scoped `Close > midpoint` / `Close < midpoint` rules by sweep side. |
| `python/experiments/EXP-017/code/run_experiment.py` | Edge cases | PASS | Missing prerequisite files/columns raise immediately; missing midpoint rows become `FilterEligible=False`; bootstrap outputs degrade to NaN when a group is too small. |
| `python/experiments/EXP-017/code/run_experiment.py` | Type safety | PASS | Public functions have type hints and useful docstrings. |
| `python/experiments/EXP-017/code/run_experiment.py` | NaN handling | PASS | `HasPDLevels`, midpoint values, ambiguous hit rows, and absent bootstrap intervals are handled explicitly. |
| `python/experiments/EXP-017/code/run_experiment.py` | Holdout exclusion | PASS | EXP-017 consumes approved EXP-014/EXP-015 result files only; it does not reopen raw time bars or touch the holdout. |
| `python/experiments/EXP-017/code/run_experiment.py` | Loader ordering | PASS | No raw-data loader is implemented here; prerequisite outputs already came from approved holdout-excluded upstream experiments. |
| `python/experiments/EXP-017/code/run_experiment.py` | Memory/performance | PASS | The workflow operates on bounded CSV outputs and writes compact summary tables. |
| `python/experiments/EXP-017/code/run_experiment.py` | Logging/output | PASS | Helper functions do not print; orchestration emits a concise completion summary only. |
| `python/experiments/EXP-017/code/run_experiment.py` | Organization/import side effects | PASS | Output directories are created in `run_experiment()`, not at import time. |
| `python/experiments/EXP-017/code/run_experiment.py` | Plot data reuse | PASS | Plots are built from the already-computed `events`, `retention`, and `effects` tables. |
| `python/experiments/EXP-017/code/run_experiment.py` | Docstrings | PASS | Public and core helper functions are documented. |

## Numerical Validation

### Spot Checks

Manual recomputation from `python/experiments/EXP-015/results/sweep_events.csv` plus `python/experiments/EXP-014/results/liquidity_levels.csv` matches the generated EXP-017 EURUSD test row:

- Total EURUSD test sweeps: `89`
- Filtered EURUSD test sweeps: `84`
- Unfiltered non-ambiguous `Hit1R_60m` mean: `0.6071428571` (`84` rows)
- Filtered non-ambiguous `Hit1R_60m` mean: `0.6000000000` (`80` rows)
- Hit-rate difference: `-0.0071428571`
- Unfiltered `MAE_R_60m` median: `4.5425287356`
- Filtered `MAE_R_60m` median: `4.6284072250`
- MAE improvement (`all - filtered`): `-0.0858784893`

Those values match `python/experiments/EXP-017/results/primary_effects.csv`. The side-level test retention rows also sum to the same filtered total (`42 + 42 = 84` for EURUSD test).

### Range Checks

| Metric | Expected Range | Actual Range / Count | Pass? |
|--------|---------------|----------------------|-------|
| `FilteredSweepN` | `>= 0` and `<= TotalSweepN` | 84-333 and always `<= TotalSweepN` | YES |
| `RetentionPct` | `[0, 1]` | `0.779` to `0.980` in test rows | YES |
| `MidpointMissingSweeps` | `>= 0` | 0 on all test rows; 1 on BTCUSD Train only | YES |
| `Hit1R_60m` means | `[0, 1]` | `0.408` to `0.630` in test rows | YES |
| Plots | 3 scoped PNGs | All 3 files present and non-empty | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|---------------------|-------|
| Instruments passing | `0/4` | YES | Scope required at least 3 instruments; none clears the thresholds. |
| Retention floors met | `4/4` | YES | The negative verdict is not a sample-size failure. |
| USTEC Test hit effect | `-0.036`, CI `[-0.072, -0.004]` | YES | The filter hurts hit rate on one instrument despite high retention. |
| BTCUSD Test MAE effect | `+0.052`, CI `[-0.073, 0.354]` | YES | Small positive point estimate with wide interval is consistent with an inconclusive single-instrument signal. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|------------|--------|----------|
| Midpoint labeling | EXP-014 PDH/PDL definitions are reproducible | YES | EXP-014 is completed and governance-approved. |
| Outcome reuse | EXP-015 outcome columns are the fixed baseline | YES | EXP-017 never alters stop, horizon, or real-price outcome definitions. |
| Nested bootstrap | Filtered sweeps are a subset of the baseline sweep set | YES | `bootstrap_nested_difference()` resamples the full baseline and recomputes the filtered statistic inside the same resample. |
| Holdout discipline | No post-hoc raw-data access is introduced | YES | Only approved prerequisite result files are read. |

## Results Plausibility

The output pattern is coherent: the midpoint filter retains a large majority of events on every test instrument yet does not deliver the scoped 5pp hit-rate or 0.25R median-MAE improvement threshold anywhere. That is exactly the type of outcome the experiment was designed to detect.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 2 tests / 2 budgeted, 3 plots / 4 budgeted, 0 new shared modules / 1 allowed
- Holdout exclusion verified: YES
- Real-price outcome discipline verified: YES, inherited from approved EXP-015 outcomes
- Timestamp alignment verified: YES, inherited from approved EXP-015 event timestamps

## Issues

### Critical

None.

### Warning

None.

### Info

None.

## Re-Audit Requirements

None.
