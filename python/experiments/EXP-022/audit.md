# Audit Report: Experiment EXP-022

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

EXP-022 can be interpreted. The implementation matches the scoped objective-candidate comparison, enforces holdout exclusion through the shared loader, keeps the selection rule outcome-free, and produces internally consistent counts plus reproducibility digests. I did not rerun the full experiment code inside the pipeline; validation used code inspection and lightweight checks over the generated output files.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-022/code/run_experiment.py` | Correctness | PASS | Candidate A and Candidate B are both detected with explicit post-displacement confirmation rules and predeclared selection criteria. |
| `python/experiments/EXP-022/code/run_experiment.py` | Edge cases | PASS | Miss tables capture no-opposite-candle, invalidation, and no-breaker cases explicitly. |
| `python/experiments/EXP-022/code/run_experiment.py` | Type safety | PASS | Public helpers are typed and documented. |
| `python/experiments/EXP-022/code/run_experiment.py` | NaN handling | PASS | Empty candidate tables and zero-denominator ambiguity rates are handled explicitly. |
| `python/experiments/EXP-022/code/run_experiment.py` | Holdout exclusion | PASS | All raw bars enter through `load_analysis_timebars()`. |
| `python/src/ict_timebar.py` | Loader ordering | PASS | Shared loader sorts by `CloseTime`, slices the first 70%, then collects. |
| `python/experiments/EXP-022/code/run_experiment.py` | Memory/performance | PASS | Detection works on holdout-excluded per-instrument tables and hashes result tables rather than replaying large raw data. |
| `python/experiments/EXP-022/code/run_experiment.py` | Logging/output | PASS | Orchestration output is concise and traceable. |
| `python/experiments/EXP-022/code/run_experiment.py` | Organization/import side effects | PASS | Output directories are created in orchestration only. |
| `python/experiments/EXP-022/code/run_experiment.py` | Plot data reuse | PASS | Plots are built from the already-computed count and miss tables. |
| `python/experiments/EXP-022/code/run_experiment.py` | Docstrings | PASS | Public and core helper functions are documented. |

## Numerical Validation

### Spot Checks

The selection outputs are internally consistent:

- `selection.json` marks `CandidateA` as the only eligible candidate.
- `candidate_counts.csv` shows `CandidateA` meets the `>= 50` floor in all `8/8` instrument-segment cells.
- `candidate_counts.csv` shows `CandidateB` misses the floor in EURUSD Test (`40`) and BTCUSD Test (`49`), so it reaches only `2/4` instruments in test.
- `reproducibility.csv` reports matching SHA-256 digests across both reruns for both candidates on all four instruments.

These checks match the narrative in `numerical_summary.txt`.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| `AmbiguityRate` | `[0, 1]` | `0.0` for every row | YES |
| `RetentionPct` | `[0, 1]` | `0.4394` to `0.8148` | YES |
| `EventFloorMet` | boolean | Only `True` / `False` observed | YES |
| Candidate digests | exact match booleans | `True` for both reruns on all instruments | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|---------------------|-------|
| Candidate A train/test floor coverage | `4/4` and `4/4` | YES | Satisfies the scoped support criterion. |
| Candidate B train/test floor coverage | `4/4` and `2/4` | YES | Fails the scoped readiness threshold without needing profitability data. |
| Mean ambiguity rate | `0.0` | YES | Consistent with deterministic boundary rules in both candidate definitions. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Candidate selection by counts and reproducibility | No profitability data is needed | YES | Only counts, ambiguity rates, and digests appear in `selection.json` and result tables. |
| Post-displacement confirmation timing | Candidate boundaries are confirmed using only bars available after displacement | YES | Candidate A breaker search starts after `disp_ns`; reproducibility tables are stable across reruns. |
| Deterministic rerun check | Same input and config produce identical candidate tables | YES | All digest equality flags are `True` in `reproducibility.csv`. |

## Results Plausibility

The outputs are plausible and consistent with the scoped question. Candidate A is broader and retains enough events everywhere, while Candidate B remains deterministic but loses too many test events on EURUSD and BTCUSD.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 0 statistical tests / 0-1 allowed, 3 plots / 4 allowed, 1 new module / 1 allowed
- Holdout exclusion verified: YES
- Real-price discipline verified: YES, no profitability metrics are computed
- Timestamp alignment verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Candidate B remains deterministic but not broadly ready**
   - File: `python/experiments/EXP-022/results/candidate_counts.csv`
   - Description: Candidate B passes reproducibility on all instruments but misses the scoped test floor on EURUSD (`40`) and BTCUSD (`49`).
   - Impact: This is a substantive experiment result, not a trust issue. It narrows the eligible breaker definition for EXP-023 to Candidate A.

## Re-Audit Requirements

None.
