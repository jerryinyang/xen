# Results: Experiment EXP-024

## Summary

EXP-024 supports the second-candle-open execution-timing hypothesis under the scoped non-inferiority rule. After the rerun applied the inherited-risk feasibility guard from EXP-021, all four instruments still met the `>= 50` feasible-event floor for both confirmation-close and second-candle-open entries in train and test, and none showed statistically negative second-candle-open return, worse MAE, or worse slippage versus confirmation-close. The support is conservative: it validates the timing rule as not worse on the predeclared metrics, not as a universal source of stronger expectancy.

## Detailed Findings

### The Rerun Removes The Timing-Denominator Trust Issue

- **Observation**: The regenerated timing tables filter inherited-stop rows below the carried feasible-risk floor and no longer contain collapsed-R artifacts.
- **Evidence**: `entry_timing_outcomes.csv` marks `61/5526` rows as `RiskFeasible=False`, and every infeasible row has null R-based outcomes and null `Slippage_R`. `missing_forward_bars.csv` reports `0` missing-forward-bar cases across all rows.
- **Interpretation**: The timing comparison is now mechanically trustworthy and not confounded by denominator failures or missing-bar bias.

### Second-Candle-Open Clears The Predeclared Gate On All Four Instruments

- **Observation**: Every instrument has enough feasible data, and every instrument passes the scoped non-inferiority decision rule in both train and test.
- **Evidence**: `results.json` records `instruments_passing = 4`. Feasible confirmation-close and second-candle-open counts are EURUSD `208/212` train and `75/76` test, XAUUSD `240/241` train and `109/111` test, BTCUSD `342/341` train and `81/81` test, and USTEC `305/301` train and `130/131` test.
- **Interpretation**: The second-candle-open rule is not losing the setup through underpowered samples or structurally worse bootstrap comparisons.

### Support Is Mostly About Preservation, Not Clear Improvement

- **Observation**: Point estimates are mixed, and hit-rate gains are absent even where the verdict passes.
- **Evidence**: EURUSD Train second-candle-open mean return improves from `-0.329R` to `+0.178R`, and USTEC Test improves from `-0.524R` to `+0.718R`. But BTCUSD Test worsens in point estimate from `-0.055R` to `-2.670R`, and the second-candle-open hit-rate differences in `bootstrap_comparison.csv` all have intervals crossing zero. The pass condition still holds because return, MAE, and slippage intervals do not show statistically worse outcomes.
- **Interpretation**: The evidence supports second-candle-open as an acceptable execution rule under the scoped non-inferiority contract, not as a broad expectancy enhancer.

## Hypothesis Verdict

**SUPPORTED**

The experiment asked whether the ICT second-candle-open execution rule improves or degrades entry quality versus simpler post-confirmation entries. Under the predeclared support rule, it is supported: `4/4` instruments clear the non-inferiority gate with adequate feasible counts in both train and test.

## Limitations

- The support verdict is tied to a non-inferiority-style criterion against confirmation-close, not a requirement for universal positive return deltas.
- The experiment inherits its confirmation set from the refuted EXP-021 IFVG path; it isolates timing only and does not rehabilitate that confirmation concept.
- Outcomes are measured on 1-minute OHLC prices only; no transaction-cost model is included.

## Alternative Explanations

- The second-candle-open rule may mainly change path shape or execution practicality rather than raw expectancy.
- Some apparent point-estimate gains may be instrument-specific and unstable, which is why the support claim is intentionally limited to the scoped non-inferiority gate.

## Recommended Next Steps

1. Carry second-candle-open forward as an allowed execution-timing variant, but not as proof of extra edge by itself.
2. When this rule is reused later, keep the feasible-risk guard and interpret it in the context of the underlying confirmation component rather than in isolation.
