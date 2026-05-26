# Audit Report: Experiment EXP-024

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

EXP-024 can now be interpreted. The rerun inherits the feasible-risk floor from the EXP-021 confirmation set, excludes infeasible timing rows from all R-based and slippage summaries, and removes the prior denominator-collapse artifacts from the stored outputs. I did not rerun the full experiment code inside the pipeline; validation used code inspection and lightweight checks over the regenerated result tables.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-024/code/run_experiment.py` | Correctness | PASS | Timing variants now carry the inherited `MinRisk1R` floor from EXP-021 and exclude rows below that floor from R-based outcomes and slippage summaries. |
| `python/experiments/EXP-024/code/run_experiment.py` | Edge cases | PASS | Risk-infeasible timing rows remain in diagnostics, and the experiment fails early if the revised EXP-021 output is missing the required floor field. |
| `python/experiments/EXP-024/code/run_experiment.py` | Type safety | PASS | Public helpers remain typed. |
| `python/experiments/EXP-024/code/run_experiment.py` | NaN handling | PASS | Missing-forward-bar and infeasible-risk cases are encoded explicitly. |
| `python/experiments/EXP-024/code/run_experiment.py` | Holdout exclusion | PASS | Bars load through `load_analysis_timebars()`. |
| `python/src/ict_timebar.py` | Loader ordering | PASS | Shared loader sorts by `CloseTime`, slices the first 70%, then collects. |
| `python/src/ict_timebar.py` | Zero-baseline safety | PASS | `compute_real_price_outcome()` honors the carried `MinRisk1R` guard. |
| `python/experiments/EXP-024/code/run_experiment.py` | Memory/performance | PASS | Outcome computation and plots reuse materialized timing tables. |
| `python/experiments/EXP-024/code/run_experiment.py` | Logging/output | PASS | Orchestration output is concise and traceable. |
| `python/experiments/EXP-024/code/run_experiment.py` | Organization/import side effects | PASS | Output directories are created in orchestration only. |
| `python/experiments/EXP-024/code/run_experiment.py` | Plot data reuse | PASS | Plots are built from already-computed timing tables. |
| `python/experiments/EXP-024/code/run_experiment.py` | Docstrings | PASS | Public helpers are documented. |

## Numerical Validation

### Spot Checks

The regenerated outputs no longer show unstable denominator behavior:

- `entry_timing_outcomes.csv` contains `5,526` rows, of which `61` are `RiskFeasible=False`.
- All `61` infeasible rows have null R-based outcomes and null `Slippage_R`; no infeasible row contributes to the bootstrap inputs.
- Feasible `Return_R_60m` values now range from `-288.0000` to `276.8245`, and feasible `Slippage_R` ranges from `-20.0000` to `15.0000`, with no billion-R artifacts.
- `missing_forward_bars.csv` reports `0` missing-forward-bar cases for every instrument, segment, and entry proxy.
- `outcome_summary.csv` reports explicit `FeasibleRiskN`, `RiskFilteredN`, and `ReturnR_N` fields, and every confirmation-close and second-candle-open row still clears the scoped `>= 50` feasible-event floor.

These checks support interpretation of the stored verdict.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| `RiskFeasible` | boolean | Only `True` / `False` observed | YES |
| `Risk1R` on feasible rows | `>= MinRisk1R > 0` | All feasible rows satisfy the carried floor; infeasible rows are filtered | YES |
| `Return_R_60m` | finite on feasible rows only | `-288.0000` to `276.8245`; null on all infeasible rows | YES |
| `Slippage_R` | finite on feasible rows only | `-20.0000` to `15.0000`; null on all infeasible rows | YES |
| Missing forward bars | integer, non-negative | `0` for every row | YES |
| Confirmation/second-open feasible floor | `>= 50` per instrument-segment | All `8/8` confirmation-close and `8/8` second-open rows pass | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|---------------------|-------|
| Instruments passing scoped support rule | `4/4` | YES | All four instruments satisfy the predeclared non-inferiority gate. |
| Instruments meeting feasible floor | `4/4` | YES | Sample size is adequate across train and test. |
| Missing forward bars | `0` | YES | Later entry timing does not create a data-availability artifact in this run. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Timing comparison in R-space | Inherited-stop denominator is explicitly guarded | YES | Infeasible timing rows are excluded via the carried `MinRisk1R` floor. |
| Confirmation source inheritance | EXP-021 provides the minimum feasible risk needed for timing isolation | YES | `EXP021_REQUIRED` enforces `MinRisk1R`, and the rerun consumes the revised EXP-021 output successfully. |
| Support criterion | Confirmation-close and second-candle-open both satisfy feasible floors before interpretation | YES | Every instrument has `>= 50` feasible rows for both proxies in train and test. |

## Results Plausibility

The rerun is numerically plausible and internally consistent. The support result is also correctly narrow: second-candle-open clears the scoped non-inferiority gate, but the underlying point estimates are mixed and do not show a universal improvement claim.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 2 bootstrap comparison families / 2 allowed, 4 plots / 4 allowed, 1 shared module reuse / 1 allowed
- Holdout exclusion verified: YES
- Real-price discipline verified: YES
- Timestamp alignment verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Support comes from non-inferiority, not from universal point-estimate improvement**
   - File: `python/experiments/EXP-024/results/results.json`
   - Description: The verdict passes because no instrument shows statistically negative second-candle-open return, worse MAE, or worse slippage versus confirmation-close under the scoped bootstrap gate. Point estimates remain mixed, especially in BTCUSD and USTEC.
   - Impact: This is a substantive experiment result, not a trust issue. It means the rule is defensible as an execution-timing choice, but not as a proven source of broad extra edge.

## Re-Audit Requirements

None.
