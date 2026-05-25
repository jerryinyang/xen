# Audit Report: Experiment EXP-019

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

EXP-019 can be interpreted, with two narrow caveats documented below. The implementation is otherwise aligned with the scoped swing-break variant, uses holdout-excluded time bars, computes outcomes on real 1-minute OHLC prices, and produces internally consistent effect tables. Validation used code inspection plus lightweight checks over the generated outputs; I did not rerun the full experiment code inside the pipeline.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-019/code/run_experiment.py` | Correctness | PASS | The two-left/two-right swing definition is causal because each pivot becomes usable only at its right-side confirmation bar, and break detection uses only prior usable swings. |
| `python/experiments/EXP-019/code/run_experiment.py` | Edge cases | PASS | Missing files, no forward bars, missing usable swings, and zero-risk entries are handled explicitly. |
| `python/experiments/EXP-019/code/run_experiment.py` | Type safety | PASS | Public functions have type hints and docstrings. |
| `python/experiments/EXP-019/code/run_experiment.py` | NaN handling | PASS | Paired bootstrap helpers drop NaN pairs before computing return and MAE effects. |
| `python/experiments/EXP-019/code/run_experiment.py` | Holdout exclusion | PASS | Instrument bars are loaded through `python/src/ict_timebar.py::load_analysis_timebars()` before any swing detection or break search. |
| `python/src/ict_timebar.py` | Loader ordering | PASS | The shared loader sorts by `CloseTime`, slices the first 70%, then collects. |
| `python/experiments/EXP-019/code/run_experiment.py` | Memory/performance | PASS | One instrument at a time is converted to pandas with only the columns needed for swing detection and outcome measurement. |
| `python/experiments/EXP-019/code/run_experiment.py` | Logging/output | PASS | Helper functions do not print; orchestration writes a concise completion summary only. |
| `python/experiments/EXP-019/code/run_experiment.py` | Organization/import side effects | PASS | Output directory creation stays inside `run_experiment()`. |
| `python/experiments/EXP-019/code/run_experiment.py` | Plot data reuse | PASS | Plots use the already-computed `swings`, `counts`, `comparison`, and `effects` tables. |
| `python/experiments/EXP-019/code/run_experiment.py` | Docstrings | PASS | Public and core helper functions are documented. |

## Numerical Validation

### Spot Checks

Manual recomputation from `python/experiments/EXP-019/results/baseline_comparison.csv` matches the XAUUSD test primary row in `primary_effects.csv`:

- Matched XAUUSD test pairs: `112`
- Mean return difference (`swing break - EXP-018 displacement`): `+0.6302343536`
- Median MAE improvement (`baseline - swing break`): `+0.4044965551`

Those values match `python/experiments/EXP-019/results/primary_effects.csv`.

The cross-segment caveat is real but narrow. `python/experiments/EXP-019/results/swing_break_detection.csv` contains exactly one confirmed BTCUSD case with `Segment=Train`, `BreakSegment=Test`, `SweepTime=2024-10-31 13:50:00`, and `BreakTime=2024-10-31 14:38:00`. Relabeling that one pair from Train to Test changes the direct BTCUSD mean/median point estimates only trivially:

- BTCUSD Train direct return diff: `0.7874 -> 0.7822`
- BTCUSD Train direct median MAE improvement: `0.2468 -> 0.2398`
- BTCUSD Test direct return diff: `1.4771 -> 1.4905`
- BTCUSD Test direct median MAE improvement: `0.1573 -> 0.1584`

The experiment verdict remains INCONCLUSIVE either way.

### Range Checks

| Metric | Expected Range | Actual Range / Count | Pass? |
|--------|---------------|----------------------|-------|
| `MatchedN` | `>= 0` | 77 to 345 across segments | YES |
| Confirmation delay | `>= 1` bar | 1 to 213 bars on confirmed rows | YES |
| Excessive-delay gate | median delay > 60 bars triggers failure | 0/4 instruments flagged | YES |
| `Risk1R` | `> 0` for evaluable outcomes | 1 zero-risk raw row; all zero-risk outcomes are NaN and excluded from paired effects | YES |
| Plots | 4 scoped PNGs | All 4 files present and non-empty | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|---------------------|-------|
| Instruments passing | `0/4` | YES | No test instrument clears the interval-based support threshold. |
| Instruments refuting | `0/4` | YES | Wide intervals leave the result inconclusive rather than negative. |
| USTEC Test MAE effect | `+0.597`, CI `[0.186, 1.076]` | YES | Strong MAE point estimate that still misses the scoped `CI95-low >= 0.25R` pass rule. |
| EURUSD Test return effect | `+0.252`, CI `[-7.542, 7.186]` | YES | Extremely wide interval is consistent with the verdict logic. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|------------|--------|----------|
| Causal swing confirmation | No future pivot knowledge is used at the break timestamp | YES | Swings are usable only at `idx + 2`, and break detection filters on `UsableTime < candidate CloseTime`. |
| Outcome measurement | No entry-bar leakage | YES | `compute_real_price_outcome()` starts from `CloseTime > EntryTime`. |
| Real-price discipline | Outcomes use canonical OHLC prices | YES | Forward outcomes are computed from the time-bar `High`, `Low`, and `Close` columns. |
| Paired comparison | Effects are measured on matched sweep keys | YES | `build_baseline_comparison()` pairs each swing-break event to the EXP-018 displacement baseline on the shared sweep identity. |

## Results Plausibility

The output pattern is coherent. Swing-break confirmation is reproducible and sample sizes remain above the floor, but the paired intervals are too wide to support or refute improvement beyond EXP-018. The reported INCONCLUSIVE verdict is consistent with that evidence.

## Scope Compliance

- Analysis plan followed: YES, except for one non-material segment-labeling caveat noted below
- Deviations: one confirmed cross-segment event is grouped under the sweep segment instead of the break segment
- Complexity budget: 2 paired bootstrap tests / 3 allowed, 4 plots / 5 allowed, 0 new shared modules / 2 allowed
- Holdout exclusion verified: YES
- Real-price outcome discipline verified: YES
- Timestamp alignment verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **One confirmed cross-segment event is labeled by the sweep segment**
   - File: `python/experiments/EXP-019/code/run_experiment.py`, lines 271-287 and 389-414
   - Description: `build_swing_break_events()` writes `Segment` from the sweep row, and `build_baseline_comparison()` keeps `Segment` in the merge key. One BTCUSD confirmed break occurs in Test after a Train sweep, so that pair remains allocated to Train in `swing_break_events.csv`, `baseline_comparison.csv`, and `primary_effects.csv`.
   - Impact: Segment-level BTCUSD counts are off by one pair. The direct BTCUSD Train/Test point estimates shift only trivially, and the overall INCONCLUSIVE verdict does not change.
   - Reproduction: Filter `python/experiments/EXP-019/results/swing_break_detection.csv` for `Confirmed == True` and `CrossSegment == True`.

2. **One raw swing-break event has zero risk and is excluded from paired effects**
   - File: `python/experiments/EXP-019/results/swing_break_events.csv`
   - Description: EURUSD Train contains one row with `Entry == Stop == 1.07815`, so `Risk1R == 0.0`.
   - Impact: `compute_real_price_outcome()` returns NaN outcomes for that row, so it remains in the raw event table but does not contribute to `MatchedN` or the paired bootstrap metrics.
   - Reproduction: Filter `swing_break_events.csv` for `Risk1R <= 0`.

## Re-Audit Requirements

None.
