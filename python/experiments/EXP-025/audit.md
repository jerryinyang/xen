# Audit Report: Experiment EXP-025

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

EXP-025 is interpretable. The code stays inside the scoped analysis set, uses real time-bar OHLC outcomes, and the stored `exit_summary.csv` is exactly reproducible from `exit_outcomes.csv`. I did not rerun the full experiment code inside the pipeline; validation used code inspection plus lightweight checks over the stored result tables.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-025/code/run_experiment.py` | Correctness | PASS | The script freezes the EXP-024 second-candle-open entry source, simulates the six scoped exits, and evaluates the predeclared H6 rule without adding new entry logic. |
| `python/experiments/EXP-025/code/run_experiment.py` | Edge cases | PASS | Empty arrays, missing liquidity targets, and non-finite values are handled explicitly. |
| `python/experiments/EXP-025/code/run_experiment.py` | Type safety | PASS | Public helpers are annotated and documented. |
| `python/experiments/EXP-025/code/run_experiment.py` | NaN handling | PASS | Liquidity-target misses and invalid outcome values remain explicit rather than silently propagated. |
| `python/experiments/EXP-025/code/run_experiment.py` | Holdout exclusion | PASS | Bar data loads through `load_analysis_timebars()` only. |
| `python/src/ict_timebar.py` | Loader ordering | PASS | Shared loader sorts by `CloseTime`, slices the first 70%, then collects. |
| `python/experiments/EXP-025/code/run_experiment.py` | Real-price outcome discipline | PASS | Exit simulation walks forward on real time-bar `High` / `Low` / `Close` arrays; no synthetic-price inputs are used. |
| `python/experiments/EXP-025/code/run_experiment.py` | Memory/performance | PASS | Instrument bars are loaded once per instrument, and plots reuse already-computed tables. |
| `python/experiments/EXP-025/code/run_experiment.py` | Logging/output | PASS | Manual-run output is concise and traceable. |
| `python/experiments/EXP-025/code/run_experiment.py` | Organization/import side effects | PASS | Output directories are created in orchestration only. |
| `python/experiments/EXP-025/code/run_experiment.py` | Plot data reuse | PASS | Plotting consumes stored outcome tables and summaries instead of rerunning the bar walk. |
| `python/experiments/EXP-025/code/run_experiment.py` | Docstrings | PASS | Public helpers are documented. |

## Numerical Validation

### Spot Checks

Independent regrouping of `results/exit_outcomes.csv` reproduced every row of `results/exit_summary.csv` exactly:

- max `|N - N_calc| = 0`
- max `|N_valid - N_valid_calc| = 0`
- max `|MeanReturn_R - MeanReturn_R_calc| = 2.22e-16`
- max `|HitRate - HitRate_calc| = 5.55e-17`

Manual example from the stored table:

- EURUSD Test `2R`: `70` valid rows
- realized-R sum: `-57.02195410960108`
- mean realized-R: `-0.8145993444228726`
- positive rows: `22 / 70`
- hit rate: `0.3142857142857143`

That matches the EURUSD Test `2R` row in `results/exit_summary.csv`.

Bootstrap spot checks on representative pairs reproduce the stored direction and interval placement under the same bootstrap-of-means method (`_bootstrap_mean_diff()`), confirming that the stored comparison table is mechanically consistent with the implementation.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| `Risk1R` | `> 0` | `0.00004` to `1771.35464` | YES |
| Realized R across all variants | finite real values | `-68.5441` to `52.3871` | YES |
| Event timestamps | valid datetimes | `2023-01-02 22:19:00` to `2025-06-17 10:57:00` | YES |
| Fully comparable instruments | `>= 0` | `4` | YES |
| Passing instruments (2R superiority evidence) | `0..4` | `0` | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|---------------------|-------|
| Instruments meeting test floor and comparator coverage | `4/4` | YES | This is a real no-go on evidence, not a floor failure. |
| Instruments with 2R superiority evidence | `0/4` | YES | No bootstrap comparison clears `CI_Lo > 0`. |
| Instruments with formal 2R domination | `0/4` | YES | No comparator drives `CI_Hi < 0`; the predeclared verdict therefore remains INCONCLUSIVE rather than REFUTED. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Exit comparison | Entry and stop rules are frozen before exit evaluation | YES | Entry source is fixed to EXP-024 second-candle-open rows and stops are inherited, not retuned here. |
| Bootstrap comparison | Non-parametric resampling is appropriate for the scoped exit comparison | YES | The code uses bootstrap-of-means rather than parametric return assumptions. |
| Outcome evaluation | Real-price OHLC path is sufficient for the scoped 60-minute horizon test | YES | The bar walk uses time-bar highs, lows, and closes only. |

## Results Plausibility

The stored result is plausible and internally consistent. All four instruments were eligible for comparison, yet `2R` failed to show positive superiority evidence anywhere. Simpler exits, especially `TimeStop60`, often have better point estimates, which fits the experiment's inconclusive no-justification verdict.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: within scope; one bootstrap comparison family plus descriptive summaries, `5 / 5` plots, no extra shared modules beyond scoped utility reuse
- Holdout exclusion verified: YES
- Real-price discipline verified: YES
- Timestamp alignment verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **The H6 result is a true no-justification outcome, not a sample-floor miss**
   - File: `python/experiments/EXP-025/results/results.json`
   - Description: All four instruments are fully comparable, but none shows `2R` superiority evidence against any scoped comparator.
   - Impact: The experiment closes the broad "fixed 1:2 is justified" claim for this entry source without needing to invoke a low-sample explanation.

## Re-Audit Requirements

None.
