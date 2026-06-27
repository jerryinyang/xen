# Results: Experiment EXP-009

## Summary

EXP-009 is measurement-complete. Across the broadened fixed, untuned six-strategy set, every gate-stack net-effect cell is below its EXP-003 pooled domain gate MDE. The result strengthens the EXP-004 lower anchor: simple untuned real-price strategies remain well below the calibrated gate detection floor. Crucially, "below_MDE" here is not "small positive edge under the floor" — domain median net effects are roughly -1 bps and most cells are net-negative after cost, so the set is a *lower* anchor (net losers), not a near-detection null.

## Detailed Findings

### All gate-stack cells are below MDE

- **Observation**: 72/72 gate-stack alpha0 cells classify as `below_MDE`; no cell is `near_MDE` or `at_or_above_MDE`.
- **Evidence**: `effect_vs_mde.csv` and `effect_distribution_summary.csv` report 24/24 below-MDE cells in each domain.
- **Interpretation**: The broadened simple-strategy set does not reveal a real untuned candidate near the gate MDE. This is consistent with EXP-004's two-strategy dogfood anchor.

### Net effects are mostly negative after cost

- **Observation**: Domain median gate-stack net effects are approximately -1 bps across 5m, 1h, and 4h.
- **Evidence**:
  - 5m median -1.018395 bps, IQR [-3.007847, -0.406185], range [-9.987340, -0.069953].
  - 1h median -0.998325 bps, IQR [-2.878832, -0.383782], range [-10.949345, -0.080834].
  - 4h median -0.952547 bps, IQR [-2.318087, -0.098853], range [-13.029254, +0.045022].
- **Interpretation**: Cost-applied simple standalone signals are not merely below the MDE; most are negative net of cost.

### The strongest point estimate is still far below MDE

- **Observation**: The largest positive gate-stack point estimate is EURUSD/4h Donchian(20), +0.045022 bps.
- **Evidence**: Its bootstrap CI is [-0.390681, +0.514643] bps, while the 4h gate MDE is 12.0 bps.
- **Interpretation**: Even the best point estimate is not close to the gate detection floor and does not merit action inside this experiment.

### Precision is sufficient for the distribution read

- **Observation**: Gate-stack effective N ranges from 902 to 65,144; block length is 1 in all 72 gate cells.
- **Evidence**: `strategy_effects.csv` reports finite CIs for every strategy/instrument/domain cell, and every CI upper bound is below the relevant MDE.
- **Interpretation**: The below-MDE conclusion is not caused by missing output or unreportable cells.

## Hypothesis Verdict

**MEASUREMENT COMPLETE**

EXP-009 is exploratory and has no pass/fail strategy hypothesis. Its scoped measurement deliverable was produced: all fixed untuned strategy effects were measured, classified relative to the MDE map, and summarized by domain and family. The substantive finding is that the broadened simple-strategy distribution sits below every domain MDE.

## Limitations

- The strategy set is intentionally fixed and untuned; the result does not refute optimized or incremental-information strategies.
- The experiment compares against pooled domain MDEs, not EXP-008 per-instrument MDEs, by scope.
- Negative net effects partly reflect the scoped flat cost model and active-bar exposure.

## Alternative Explanations

- A tuned strategy or a different candidate family might approach the MDE, but testing that would require a new predeclared experiment.
- Some gross effects may be less negative than net effects; the gate-stack result is cost-applied by design.

## Recommended Next Steps

1. Use EXP-009 as optional context in EXP-011: the real simple-strategy distribution remains a lower/null anchor.
2. Defer any tuned or incremental-information candidate search to a new scoped phase after the referee operating point is settled.
