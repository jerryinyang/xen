# Results: Experiment EXP-025

## Summary

EXP-025 is **INCONCLUSIVE** under its predeclared H6 rule, but the substantive message is still clear: the fixed `2R` target was not positively justified for the approved EXP-024 second-candle-open entry set. All four instruments met the scoped test-floor and comparator-coverage requirements, yet none produced bootstrap superiority evidence for `2R` versus the alternative exits, and no instrument showed a formal domination pattern strong enough to trigger an explicit refutation verdict.

## Detailed Findings

### Comparator Coverage Was Adequate On All Four Instruments

- **Observation**: The experiment had enough data to answer the scoped question.
- **Evidence**: `results.json` records `instruments_floor_met = 4` and `instruments_fully_comparable = 4`. Test `2R` counts were EURUSD `70`, XAUUSD `100`, BTCUSD `77`, and USTEC `125`.
- **Interpretation**: This result is not being driven by an underpowered sample or missing comparator rows.

### 2R Showed No Superiority Evidence Anywhere

- **Observation**: No instrument passed the scoped "2R superiority" rule.
- **Evidence**: `results.json` records `instruments_passing = 0`. Representative bootstrap rows from `bootstrap_comparison.csv` are EURUSD `2R vs 1R: diff=-0.356, CI [-0.950, 0.229]` and XAUUSD `2R vs TimeStop60: diff=-0.707, CI [-2.318, 0.981]`.
- **Interpretation**: The bootstrap intervals never support the claim that `2R` beats a scoped alternative on any instrument.

### Simpler Exits Usually Have Better Test Point Estimates

- **Observation**: Even without a formal domination verdict, `2R` is usually weaker in point estimate than simpler exits.
- **Evidence**: In `exit_summary.csv`, EURUSD Test `2R` is `-0.815R` versus `TimeStop60 -0.297R`; XAUUSD Test `2R` is `-0.810R` versus `TimeStop60 -0.092R`; USTEC Test `2R` is `-0.918R` versus `TimeStop60 -0.233R`. BTCUSD Test `2R` is `-0.474R`, worse than `3R -0.303R` and `TimeStop60 -0.257R`.
- **Interpretation**: The broad H6 claim is not supported in practical terms even though the predeclared verdict remains INCONCLUSIVE rather than REFUTED.

## Hypothesis Verdict

**INCONCLUSIVE**

The experiment asked whether a fixed `1:2` risk/reward target is justified versus simpler alternatives. Under the predeclared interpretation guide, it is inconclusive because `2R` is neither positively superior on any instrument nor formally dominated on enough instruments to trigger the "against" rule. The practical takeaway is narrower and negative: this entry source does not provide evidence that `2R` is worth carrying forward as a preferred default.

## Limitations

- The result is tied to the approved EXP-024 second-candle-open entry set and does not generalize to other entry definitions.
- Outcomes are measured on a fixed 60-minute horizon and do not test longer holding logic.
- No transaction-cost model is applied in this experiment.

## Alternative Explanations

- A different entry family could interact differently with fixed-R targets, but that would require a new scoped experiment.
- Some higher targets may need a longer horizon to express, which is outside this experiment's frozen design.

## Recommended Next Steps

1. Treat `RiskModel_2R` as ineligible for downstream candidate selection under the current Phase 003 chain.
2. Revisit exit-logic questions only in a new scope tied to a materially stronger entry candidate, not as an extension of this experiment.
