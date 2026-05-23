# Results: Experiment EXP-011

## Summary

EXP-011 refutes the hypothesis that the three pre-fixed Renko-native features define lower-boundary-cost volatility regimes. Event density, median source-count, and brick-to-ATR labels all show high disagreement with time-bar regimes. Brick-to-ATR has the lowest missed-transition rates, but its hybrid rates remain high, so it does not satisfy the combined boundary-cost rationale.

## Detailed Findings

### Event-Native Labels Do Not Reduce Hybrid Disagreement

- **Observation**: 15-minute hybrid rates are high across all features.
- **Evidence**: At 15 minutes, event-density hybrid rates range `0.564-0.659`, median-source-count rates `0.739-0.750`, and brick-to-ATR rates `0.750-0.788`.
- **Interpretation**: Event-native regimes do not align cleanly with the canonical time-bar volatility regime reference.

### Missed-Transition Behavior Is Feature-Specific but Not Sufficient

- **Observation**: Brick-to-ATR has the lowest missed-transition rates, while event density and source-count miss many transitions.
- **Evidence**: At 15 minutes, brick-to-ATR missed-transition rates are `0.324-0.407`; event-density rates are `0.383-0.759`; median-source-count rates are `0.448-0.491`.
- **Interpretation**: Brick-to-ATR catches more reference transitions, but its high hybrid disagreement means it is not a supported regime stratifier.

### Agreement With Time-Bar Regimes Is Low

- **Observation**: 15-minute agreement with time-bar regimes is below 0.44 for all features and instruments.
- **Evidence**: Event density agreement reaches at most `0.436`; median source-count is about `0.250-0.261`; brick-to-ATR is about `0.211-0.250`.
- **Interpretation**: The Renko-native states are not simple replacements for time-bar volatility regimes.

### Signal-Quality Stratification Is Descriptive Only

- **Observation**: Some 15-minute feature strata separate FE60/AE60 descriptively.
- **Evidence**: Brick-to-ATR low/high strata differ in FE60 and AE60 across instruments, but the direction is not uniform and boundary-cost criteria fail.
- **Interpretation**: Signal-quality separation is not enough to support Phase 3 use when the primary boundary-cost criterion is not met.

## Feature Verdicts

- **EventDensity60m**: REFUTED. Lower hybrid than the other features in some 15-minute cases, but missed-transition rates are inconsistent and can exceed `0.70`.
- **MedianSourceCount60m**: REFUTED. Hybrid rates are high and missed-transition rates remain about `0.45-0.49` at 15 minutes.
- **BrickToATR**: REFUTED. Missed-transition rates are lowest, but hybrid rates are the highest or near-highest across instruments.

## Hypothesis Verdict

**REFUTED**

No pre-fixed feature provides a consistent, auditable reduction in boundary cost suitable for Phase 3 regime stratification. Time-bar regimes should remain the canonical volatility reference for Renko signal analysis.

## Limitations

- The experiment tests fixed terciles only; no quartiles, clustering, or feature combinations were allowed.
- Tied discrete feature values collapse some strata.
- 1-minute signal-quality stratification is exploratory context; 15-minute is the relevant downstream context.

## Alternative Explanations

- Renko-native features may be measuring event-generation mechanics rather than market volatility regimes.
- Brick-to-ATR may be useful as a diagnostic for brick construction pressure, but not as a volatility regime label.

## Recommended Next Steps

1. Keep time-bar-derived volatility regimes as the canonical reference in Phase 3.
2. Use Renko-native features only as descriptive diagnostics unless a new experiment scopes a different target than regime-boundary reduction.
