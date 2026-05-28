# Audit Report: Experiment EXP-032

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

The EXP-032 implementation and outputs are suitable for interpretation. The code follows the approved 1-hour USTEC magnitude-gate scope, excludes the global holdout before aggregation, uses real 1-minute prices for all outcome metrics, and makes the Branch A gate mechanically from the predeclared EXP-031 reference threshold.

## Code Review

| File | Check | Verdict | Notes |
| --- | --- | --- | --- |
| `python/experiments/EXP-032/code/run_experiment.py` | Scope compliance | PASS | Implements only USTEC, synthetic 1-hour aggregation, sweep -> displacement -> Candidate A labeling, real-price 60-minute outcomes, EXP-031/EXP-023 reference comparison, and scoped plots/tables. |
| `python/experiments/EXP-032/code/run_experiment.py` | Holdout exclusion | PASS | `load_data()` calls `load_analysis_timebars()` before 1-hour aggregation; that helper sorts by `CloseTime`, slices the first 70 percent, and only then collects the analysis frame. |
| `python/experiments/EXP-032/code/run_experiment.py` | Loader ordering | PASS | 1-hour aggregation receives only the holdout-excluded 1-minute frame. No code path aggregates or plots the full USTEC file. |
| `python/experiments/EXP-032/code/run_experiment.py` | Temporal alignment | PASS | Detection uses 1-hour `CloseTime`; outcomes use `np.searchsorted(..., side="right")` on real 1-minute `CloseTime`, excluding movement inside the confirming 1-hour candle. |
| `python/experiments/EXP-032/code/run_experiment.py` | Look-ahead prevention | PASS | ATR and body-median features are shifted by one completed 1-hour bar; displacement and breaker searches only move forward from event timestamps as scoped. |
| `python/experiments/EXP-032/code/run_experiment.py` | Real-price discipline | PASS | The synthetic 1-hour series is detection-only. Return_R, MAE_R, MFE_R, hit rates, and log returns are computed from real 1-minute OHLC. |
| `python/experiments/EXP-032/code/run_experiment.py` | Edge cases / NaN handling | PASS | Empty frames, missing references, no displacement events, zero/invalid risk, and no forward bars are handled explicitly. |
| `python/experiments/EXP-032/code/run_experiment.py` | Code standards | PASS | Imports/path/constants/helpers/plotting/orchestration are separated; output directories are created only in `run_experiment()`; logging and final stdout are concise. |
| `python/experiments/EXP-032/code/run_experiment.py` | Complexity budget | PASS | Statistical test families: 2 / 3. Plots: 4 / 4. New reusable modules: 0 / 0. |

## Numerical Validation

### Spot Checks

Per-event CSV recomputation matched the summary tables:

- Train: 417 sweeps, 189 displacement entries, 144 breaker-labeled entries, 143 risk-feasible breaker entries.
- Test: 147 sweeps, 74 displacement entries, 62 breaker-labeled entries, 62 risk-feasible breaker entries.
- Train mean Return_R_60m: baseline `0.103482`, breaker `0.319529`, diff `0.216047`.
- Test mean Return_R_60m: baseline `0.161946`, breaker `0.278440`, diff `0.116494`.
- Test EXP-031 half-magnitude gate: `0.5 * 1.8357017074 = 0.9178508537`; EXP-032 test diff `0.1164937910`, so the hard magnitude gate fails.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
| --- | --- | --- | --- |
| Risk-feasible Return_R_60m | Real-valued, finite for evaluable rows | Train feasible range `[-2.0001, 6.2074]`; Test feasible range `[-1.4021, 5.0812]` | YES |
| Risk-feasible MAE_R_60m | `>= 0` | Train/Test feasible values non-negative; summary means `0.31` to `0.48` | YES |
| Risk-feasible MFE_R_60m | `>= 0` | Train/Test feasible values non-negative; summary means `0.56` to `0.61` | YES |
| Event counts | Non-negative integers | All count fields non-negative; train/test floors pass | YES |
| Plot files | Non-empty PNG | Four generated PNGs have valid PNG signatures and non-zero file sizes | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
| --- | --- | --- | --- |
| Train Return_R_60m diff | `+0.2160`, CI `[+0.1437, +0.2977]` | YES | Direction is positive but smaller than EXP-031 train effect. |
| Test Return_R_60m diff | `+0.1165`, CI `[+0.0391, +0.2203]` | YES | Positive CI, but far below the predeclared `+0.9179R` threshold. |
| Test feasible breaker count | `62` | YES | Above the `>= 50` floor but much smaller than the 15-minute reference count. |
| Displacement retention vs EXP-031 | `0.5680` | YES | Above the 30 percent resolution-cost limit. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
| --- | --- | --- | --- |
| Chronological split | Analysis excludes final 30 percent before aggregation | YES | 1-hour aggregation consumes only the `load_analysis_timebars()` frame. |
| Label-stratified bootstrap | Event-level resampling estimates uncertainty without normality assumptions | PARTIAL | Appropriate for the predeclared descriptive gate; temporal dependence still limits inference strength. |
| Reference comparison | EXP-031/EXP-023 comparisons are metric-level references, not event-level matches | YES | `reference_comparison.csv` joins by segment and metric only. |
| Real-price outcome evaluation | Synthetic 1-hour bars are detection-only | YES | Outcomes are computed from real 1-minute OHLC after entry timestamp. |

## Results Plausibility

The outputs are plausible and internally consistent. The 1-hour chain keeps adequate counts and positive point estimates, but the effect size shrinks sharply versus the 15-minute reference. MAE_R improves by about `-0.16R` in both segments, while MFE_R does not improve reliably. This pattern supports the mechanical `AGAINST` verdict: the 1-hour gate finds some favorable filtering, but not enough magnitude to justify Branch A continuation under the approved criterion.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 2 / 3 test families, 4 / 4 plots, 0 / 0 new reusable modules
- Holdout exclusion verified: YES
- Real-price outcome discipline verified: YES
- Timestamp alignment verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **One finite-outcome count caveat**
   - One train breaker-labeled row is risk-feasible but has no forward 1-minute path, so finite Return_R means and bootstrap intervals exclude it. The reported train `N=188` / `BreakerN=143` in `bootstrap_primary.csv` are risk-feasible counts; the finite-return counts are `187` / `142`. The hard gate is unchanged because both train and test remain above the `>= 50` floor, and the result is already `AGAINST` on magnitude.

2. **Duplicate level-family events are retained by design**
   - Some rows share the same entry timestamp when different liquidity level families trigger on the same 1-hour candle. This matches the scoped first-touch policy per NY date and level family; the implementation does not silently deduplicate denominator events.

## Re-Audit Requirements

None. The experiment can proceed to interpretation.
