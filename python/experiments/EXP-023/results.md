# Results: Experiment EXP-023

## Summary

EXP-023 does not support the breaker-confirmation trade-quality hypothesis under the fixed Candidate A definition from EXP-022. After the rerun applied the inherited-risk feasibility guard, all four instruments still met the `>= 50` feasible breaker-event floor in both train and test, but only USTEC satisfied the predeclared bootstrap rule for a broad improvement over the displacement baseline. The result is a clean substantive failure rather than a denominator-trust failure.

## Detailed Findings

### The Rerun Removes The Normalization Trust Issue

- **Observation**: The regenerated outputs filter inherited-stop rows that fall below the original sweep buffer and no longer contain unstable R artifacts.
- **Evidence**: `outcome_events.csv` marks `24/2549` rows as `RiskFeasible=False`, and every infeasible row has null R-based outcomes. Feasible `Return_R_60m` values range from `-148.8444` to `106.9811`.
- **Interpretation**: The downstream comparison is now auditable. The negative verdict is no longer a math artifact.

### Candidate A Retains Enough Events Everywhere

- **Observation**: The selected breaker definition remains operationally broad enough for testing.
- **Evidence**: `chain_waterfall.csv` reports breaker counts of EURUSD `140/54`, XAUUSD `172/79`, BTCUSD `239/66`, and USTEC `205/86` for train/test, with `EventFloorMet=True` throughout. Duplicate join keys remain `0` on every row.
- **Interpretation**: EXP-022's readiness gate holds up in the rerun. Sparse sample size is not the reason the experiment fails.

### Only USTEC Shows The Required Broad Improvement

- **Observation**: Breaker confirmation improves quality clearly on one instrument, but not on three or more.
- **Evidence**: `results.json` records `instruments_passing = 1`. USTEC Test breaker return is `+1.756R` versus displacement `-2.414R`, with bootstrap return and drawdown-adjusted intervals excluding zero on the positive side while train return is not worse and MAE is not worse. EURUSD and XAUUSD show better test point estimates and better MAE, but their test return and drawdown-adjusted intervals still cross zero. BTCUSD is largely flat versus baseline.
- **Interpretation**: The breaker layer may help selectively in USTEC, but it does not justify a broad H5 promotion across the current instrument set.

## Hypothesis Verdict

**REFUTED**

The experiment asked whether one objective breaker confirmation improves trade quality beyond the predeclared baseline. Under the scoped rule, the answer is no: every instrument has enough feasible data, but only `1/4` passes the required return/drawdown conditions.

## Limitations

- The experiment tests only Candidate A, as required by EXP-022; other breaker definitions were intentionally excluded.
- Outcomes are measured on 1-minute OHLC prices only; no execution-cost model is included.
- The inherited-risk feasibility guard preserves the fixed-stop convention but does not change the original sweep-based risk framing.

## Alternative Explanations

- The breaker layer may provide value only on specific instruments such as USTEC rather than as a broad cross-instrument rule.
- The retained breaker subset may improve path quality mainly through MAE compression without producing reliable enough expectancy gains to pass the scope.

## Recommended Next Steps

1. Treat the broad H5 breaker-confirmation claim as refuted for the current cross-instrument scope.
2. If breaker work continues, reopen it as a narrower follow-up that explicitly targets where Candidate A looked strongest rather than assuming broad portability.
