# Results: Experiment EXP-026

## Summary

EXP-026 is **INCONCLUSIVE** and functions as a phase gate: the incremental ablation chain could be assembled, but no optional ICT component produced the robust positive marginal contribution required for full-model promotion. The stored manifest therefore keeps only the mandatory baseline pair `["Sweep", "Displacement"]` and marks the candidate as ineligible for EXP-027.

## Detailed Findings

### The Chain Was Real Enough To Evaluate

- **Observation**: The experiment was not blocked by zero counts or missing upstream tables.
- **Evidence**: `chain_steps.csv` records Test event counts of EURUSD `84`, XAUUSD `116`, BTCUSD `86`, and USTEC `144` at Sweep, and still `72`, `105`, `71`, and `115` at Displacement.
- **Interpretation**: The no-go result comes from contribution quality, not from an inability to form the ablation chain.

### No Optional Component Cleared The Positive Lower-CI Rule

- **Observation**: IFVG, Breaker, SecondCandleOpen, and RiskModel_2R all fail candidate promotion.
- **Evidence**: `bootstrap_marginal.csv` contains `0` Test rows with both `MeanDiff > 0` and `CI_Lo > 0`. For Step 7 (`SecondCandleOpen`), all four Test rows are negative in point estimate and have lower bounds below zero: EURUSD `-0.419`, XAUUSD `-0.121`, BTCUSD `-0.984`, USTEC `-0.101`.
- **Interpretation**: No optional layer shows the robust, cross-instrument marginal benefit the manifest rule requires.

### The Stored Manifest Correctly Blocks Full-Model Promotion

- **Observation**: The final manifest selects only the mandatory baseline components.
- **Evidence**: `model_manifest.json` records `selected_components = ["Sweep", "Displacement"]`, `candidate_eligible = false`, and excludes `RiskModel_2R` because EXP-025 is not a positive support result.
- **Interpretation**: The experiment does exactly what the phase gate asked for: it prevents a weak or ambiguous chain from being rebranded as a full-model candidate.

## Hypothesis Verdict

**INCONCLUSIVE**

The experiment asked which validated ICT components contribute net value when combined incrementally. Under the frozen rule, the answer is incomplete: Sweep and Displacement remain the measurable baseline, but no optional component survives the positive lower-CI gate strongly enough to justify a promoted model candidate.

## Limitations

- Early chain steps use proxy expectancy rather than R-based returns because those stages are structural filters rather than full trade rules.
- The result inherits the strengths and weaknesses of EXP-015 through EXP-025.
- Fixed-order ablation cannot prove that a different, newly invented component order would work; that would require a new scope.

## Alternative Explanations

- Some optional components may be instrument-specific or context-specific rather than broadly useful.
- A stronger upstream entry definition could change the contribution of later components, but that is outside this experiment.

## Recommended Next Steps

1. Treat EXP-027 as blocked unless a new experiment produces an eligible optional component under a fresh scope.
2. If component work continues, target a narrower thesis rather than reviving the full chain unchanged.
