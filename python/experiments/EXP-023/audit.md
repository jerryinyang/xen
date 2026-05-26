# Audit Report: Experiment EXP-023

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

EXP-023 can now be interpreted. The rerun applies the inherited-risk feasibility guard to both baseline and breaker-confirmed entries, removes the prior unstable denominator rows from all R-based outputs, and keeps the Candidate A selection frozen from EXP-022. I did not rerun the full experiment code inside the pipeline; validation used code inspection and lightweight checks over the regenerated result tables.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-023/code/run_experiment.py` | Correctness | PASS | Baseline and breaker entries now carry `MinRisk1R` from the original sweep buffer and exclude inherited-stop rows below that floor from R-based summaries. |
| `python/experiments/EXP-023/code/run_experiment.py` | Edge cases | PASS | Risk-infeasible delayed entries remain in the waterfall but do not enter outcome means or bootstrap verdict logic. |
| `python/experiments/EXP-023/code/run_experiment.py` | Type safety | PASS | Public helpers remain typed. |
| `python/experiments/EXP-023/code/run_experiment.py` | NaN handling | PASS | Empty bootstrap inputs still return explicit NaNs. |
| `python/experiments/EXP-023/code/run_experiment.py` | Holdout exclusion | PASS | Bars load through `load_analysis_timebars()`. |
| `python/src/ict_timebar.py` | Loader ordering | PASS | Shared loader sorts by `CloseTime`, slices the first 70%, then collects. |
| `python/src/ict_timebar.py` | Zero-baseline safety | PASS | `compute_real_price_outcome()` now honors the carried `MinRisk1R` guard. |
| `python/experiments/EXP-023/code/run_experiment.py` | Memory/performance | PASS | Outcome computation and plots reuse materialized tables. |
| `python/experiments/EXP-023/code/run_experiment.py` | Logging/output | PASS | Orchestration output is concise and traceable. |
| `python/experiments/EXP-023/code/run_experiment.py` | Organization/import side effects | PASS | Output directories are created in orchestration only. |
| `python/experiments/EXP-023/code/run_experiment.py` | Plot data reuse | PASS | Plots are built from the already-computed comparison tables. |
| `python/experiments/EXP-023/code/run_experiment.py` | Docstrings | PASS | Public helpers are documented. |

## Numerical Validation

### Spot Checks

The regenerated outputs no longer contain denominator-driven artifacts:

- `outcome_events.csv` contains `2,549` rows, of which `24` are `RiskFeasible=False`.
- All `24` infeasible rows have null R-based outcomes; no infeasible row carries a non-null `Return_R_60m`, `DrawdownAdjusted_R_60m`, or `MAE_R_60m`.
- Feasible `Return_R_60m` values now range from `-148.8444` to `106.9811`, with no thousand-R or larger collapse artifacts.
- `outcome_comparison.csv` reports explicit `FeasibleRiskN`, `RiskFilteredN`, and `ReturnR_N` for both `DisplacementClose` and `BreakerClose`, and every breaker train/test row still clears the scoped `>= 50` feasible-event floor.

These checks match the revised contract and support interpretation of the stored verdict.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| `RiskFeasible` | boolean | Only `True` / `False` observed | YES |
| `Risk1R` on feasible rows | `>= MinRisk1R > 0` | All feasible rows satisfy the carried floor; infeasible rows are filtered | YES |
| `Return_R_60m` | finite on feasible rows only | `-148.8444` to `106.9811`; null on all infeasible rows | YES |
| `MAE_R_60m` | finite, non-negative on feasible rows only | `0.0` to `179.0447`; null on all infeasible rows | YES |
| Breaker feasible event floor | `>= 50` per instrument-segment | `54` to `238` | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|---------------------|-------|
| Instruments passing scoped support rule | `1/4` | YES | Only USTEC clears the predeclared breaker-improves rule. |
| Instruments meeting breaker feasible floor | `4/4` | YES | Sample size is not the reason for the negative verdict. |
| Duplicate join keys | `0` on all waterfall rows | YES | Baseline and breaker chains remain one-to-one aligned. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Baseline vs breaker R comparison | Delayed-entry denominator is explicitly guarded | YES | Infeasible baseline and breaker rows are excluded via the carried `MinRisk1R` floor. |
| Candidate selection handoff from EXP-022 | Breaker definition stays frozen before outcomes | YES | `results.json` records Candidate A as the selected breaker and the code compares only that definition. |
| Support criterion | Event floors are satisfied before interpretation | YES | Every breaker train/test row reports `EventFloorMet=True` with feasible counts `>= 50`. |

## Results Plausibility

The rerun is numerically plausible and internally consistent. The negative experiment outcome is substantive: breaker confirmation improves one instrument cleanly, but it does not produce the broad `>= 3/4` trade-quality support required by the scope.

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

1. **Candidate A is reproducible and count-eligible, but the quality gain is narrow**
   - File: `python/experiments/EXP-023/results/results.json`
   - Description: The rerun records `instruments_passing = 1`, with only USTEC clearing the full breaker-improves rule despite all instruments meeting the event floor.
   - Impact: This is a substantive experiment result, not a trust issue. It means EXP-022's readiness gate succeeded mechanically, but the broad H5 quality claim still fails.

## Re-Audit Requirements

None.
