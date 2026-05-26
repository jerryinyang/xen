# Results: Experiment EXP-021

## Summary

EXP-021 does not support the IFVG-confirmation entry-quality hypothesis. After the rerun applied the inherited-risk feasibility guard, all four instruments still met the `>= 50` feasible-event floor in both train and test, but none showed test-segment IFVG improvement against both the sweep-close and displacement-close baselines on the predeclared bootstrap criteria. The result is now a clean substantive failure rather than a numerical trust failure.

## Detailed Findings

### The Denominator Fix Changed Trust, Not The Verdict

- **Observation**: The rerun removes the prior near-zero-risk distortion without changing the hypothesis outcome.
- **Evidence**: `entry_outcomes.csv` now marks `53/6030` delayed-entry rows as `RiskFeasible=False`, and every infeasible row has null R-based outcomes. No billion-R artifacts remain; feasible `Return_R_60m` values range from `-288.0000` to `276.8245`.
- **Interpretation**: The experiment can now be interpreted as scoped. The negative verdict is not an artifact of broken denominator handling.

### IFVG Keeps Almost The Entire Displacement Sample

- **Observation**: The frozen IFVG rule barely reduces the displacement-confirmed chain.
- **Evidence**: `waterfall.csv` reports identical displacement and IFVG counts on `7/8` instrument-segment rows, with only BTCUSD Train dropping from `345` to `344`. All IFVG train/test feasible counts remain above the floor: EURUSD `208/75`, XAUUSD `240/109`, BTCUSD `342/81`, USTEC `305/130`.
- **Interpretation**: IFVG confirmation is not functioning as a strong filter under this rule set. The experiment is mostly testing entry delay rather than meaningful event selection.

### No Instrument Clears The Predeclared Support Rule

- **Observation**: IFVG entries fail to show test-segment improvement against both simpler baselines on any instrument.
- **Evidence**: `results.json` records `instruments_passing = 0` and `instruments_floor_met = 4`. On EURUSD Test, mean IFVG return is `-0.823R` versus sweep-close `+0.791R`; on XAUUSD Test it is `-0.551R` versus sweep-close `+0.623R`; on BTCUSD Test it is `-0.055R` versus displacement-close `+0.534R`; on USTEC Test it is `-0.524R` versus second-candle-open `-0.157R` and displacement-close `-2.414R`. The bootstrap tables show no instrument with test return or drawdown-adjusted improvement against both baselines.
- **Interpretation**: Waiting for IFVG confirmation does not produce a broad trade-quality gain under the scoped rule set. Where drawdown or MAE improves, the return evidence still fails the support gate.

## Hypothesis Verdict

**REFUTED**

The experiment asked whether IFVG confirmation improves entry quality enough to offset later entry timing and fewer signals. With feasible-risk filtering applied, the answer is no: the event floors are met, but `0/4` instruments satisfy the predeclared support rule.

## Limitations

- The experiment inherits the frozen IFVG rule from EXP-020 as a diagnostic consequence check, even though EXP-020 already suggested the rule was not very selective.
- Outcomes are measured on 1-minute OHLC prices only; no transaction-cost model is included.
- The inherited-risk feasibility guard excludes only rows below the original EXP-015 sweep buffer. Small but still-feasible original buffers remain part of the scoped risk convention.

## Alternative Explanations

- The IFVG rule may be too permissive to create a genuinely better subset, so the experiment is paying the delay cost without earning enough selectivity.
- Any real benefit may require a stricter zone or lifecycle definition, but that would be a new prerequisite experiment rather than a reinterpretation of this one.

## Recommended Next Steps

1. Treat the current IFVG confirmation path as refuted for broad H4 entry-quality use under the frozen EXP-020 rule set.
2. Reopen IFVG work only through a new prerequisite scope that tightens selectivity with one explicit predeclared change.
