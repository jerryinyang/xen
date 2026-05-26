# Audit Report: Experiment EXP-021

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

EXP-021 can now be interpreted. The rerun applies the scoped inherited-risk feasibility guard consistently, excludes infeasible delayed-entry rows from all R-based summaries and bootstraps, and removes the prior denominator-collapse artifacts from the stored outputs. I did not rerun the full experiment code inside the pipeline; validation used code inspection and lightweight checks over the regenerated result tables.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-021/code/run_experiment.py` | Correctness | PASS | Delayed entries now carry `MinRisk1R` from the EXP-015 sweep buffer and mark inherited-stop rows below that floor as risk-infeasible. |
| `python/experiments/EXP-021/code/run_experiment.py` | Edge cases | PASS | IFVG and second-candle rows that collapse onto the inherited stop remain in retention diagnostics but are excluded from R-space outcomes. |
| `python/experiments/EXP-021/code/run_experiment.py` | Type safety | PASS | Public helpers remain typed. |
| `python/experiments/EXP-021/code/run_experiment.py` | NaN handling | PASS | Empty bootstrap inputs still return explicit NaNs. |
| `python/experiments/EXP-021/code/run_experiment.py` | Holdout exclusion | PASS | Bars load through `load_analysis_timebars()`. |
| `python/src/ict_timebar.py` | Loader ordering | PASS | Shared loader sorts by `CloseTime`, slices the first 70%, then collects. |
| `python/src/ict_timebar.py` | Zero-baseline safety | PASS | `compute_real_price_outcome()` now rejects inherited-risk rows below the carried `MinRisk1R` floor. |
| `python/experiments/EXP-021/code/run_experiment.py` | Memory/performance | PASS | Outcome computation and plots reuse materialized tables. |
| `python/experiments/EXP-021/code/run_experiment.py` | Logging/output | PASS | Orchestration output is concise and traceable. |
| `python/experiments/EXP-021/code/run_experiment.py` | Organization/import side effects | PASS | Output directories are created in orchestration only. |
| `python/experiments/EXP-021/code/run_experiment.py` | Plot data reuse | PASS | Plots are built from already-computed summaries. |
| `python/experiments/EXP-021/code/run_experiment.py` | Docstrings | PASS | Public helpers are documented. |

## Numerical Validation

### Spot Checks

The regenerated outputs no longer show denominator explosions:

- `entry_outcomes.csv` contains `6,030` rows, of which `53` are `RiskFeasible=False`.
- All `53` infeasible rows have null R-based outcomes; no infeasible row carries a non-null `Return_R_60m`, `MFE_R_60m`, or `MAE_R_60m`.
- `Return_R_60m` is finite on all `5,977` feasible rows and now ranges from `-288.0000` to `276.8245`, rather than the prior billion-R artifacts.
- `expectancy_summary.csv` reports explicit `FeasibleRiskN`, `RiskFilteredN`, and `ReturnR_N` fields for every entry proxy, and all IFVG rows still clear the scoped `>= 50` feasible-event floor in both train and test.

These checks match the revised contract: the experiment still counts delayed entries for chain retention, but it no longer lets risk-collapsed rows drive the verdict.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| `RiskFeasible` | boolean | Only `True` / `False` observed | YES |
| `Risk1R` on feasible rows | `>= MinRisk1R > 0` | All feasible rows satisfy the carried floor; infeasible rows are filtered | YES |
| `Return_R_60m` | finite on feasible rows only | `-288.0000` to `276.8245`; null on all infeasible rows | YES |
| `MAE_R_60m` | finite, non-negative on feasible rows only | `0.0` to `438.0000`; null on all infeasible rows | YES |
| IFVG feasible event floor | `>= 50` per instrument-segment | `75` to `342` | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|---------------------|-------|
| Instruments passing scoped support rule | `0/4` | YES | The rerun fails on the hypothesis itself, not on sample size or broken normalization. |
| Instruments meeting IFVG feasible floor | `4/4` | YES | Every instrument has both train and test IFVG rows above the predeclared minimum. |
| IFVG retention after displacement | `~100%` on `7/8` rows; `344/345` on BTCUSD Train | YES | This matches the prior concern that the frozen IFVG rule is not very selective. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| R-multiple outcome comparison | Delayed-entry denominator is explicitly guarded | YES | Infeasible delayed-entry rows are identified via `MinRisk1R` and excluded from R-based tables. |
| Fixed-stop delayed-entry comparison | Chain retention can still be audited after filtering infeasible rows | YES | `waterfall.csv` keeps the full chain counts while `expectancy_summary.csv` reports feasible counts separately. |
| IFVG contribution test | Interpretation requires feasible event floors before bootstraps | YES | Every IFVG train/test row reports `EventFloorMet=True` with feasible counts `>= 50`. |

## Results Plausibility

The rerun is numerically plausible and internally consistent. The negative experiment outcome is substantive: IFVG confirmation keeps almost the full displacement sample yet fails to show test-segment return or drawdown-adjusted improvement against both simpler baselines on any instrument.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 2 bootstrap comparison families / 3 allowed, 4 plots / 5 allowed, 1 shared module reuse / 2 allowed
- Holdout exclusion verified: YES
- Real-price discipline verified: YES
- Timestamp alignment verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **The rerun resolves the trust issue but not the underlying IFVG selectivity concern**
   - File: `python/experiments/EXP-021/results/waterfall.csv`
   - Description: IFVG confirmation retains essentially all displacement-confirmed events, with only one drop from displacement to IFVG across all eight instrument-segment rows.
   - Impact: This is a substantive experiment result, not an implementation defect. It strengthens the conclusion that the frozen IFVG rule adds little selective value even after the denominator fix.

## Re-Audit Requirements

None.
