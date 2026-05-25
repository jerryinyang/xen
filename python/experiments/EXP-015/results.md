# Results: Experiment EXP-015

## Summary

EXP-015 refutes the hypothesis that failed PDH/PDL and ONH/ONL sweeps show broad measurable opposite-direction behavior versus non-failed breaches under the predeclared 60-minute 1R-before-stop criterion. All four instruments have adequate test-segment sweep counts, but only EURUSD passes the primary test. XAUUSD and BTCUSD are negative in test, and USTEC is positive but inconclusive because its bootstrap interval crosses zero.

## Detailed Findings

### Primary 60-Minute 1R Outcome Does Not Generalize

- **Observation**: Only 1 of 4 instruments supports the primary criterion in the test segment.
- **Evidence**: `primary_effects.csv` reports EURUSD Test sweep hit rate `0.607` versus breach `0.472`, bootstrap diff `+0.134`, CI `[0.001, 0.267]`. XAUUSD Test diff is `-0.029`, CI `[-0.151, 0.095]`; BTCUSD Test diff is `-0.117`, CI `[-0.250, 0.018]`; USTEC Test diff is `+0.048`, CI `[-0.063, 0.160]`.
- **Interpretation**: The predeclared support rule required at least 3 instruments with adequate counts and positive CIs excluding zero. EXP-015 reaches only 1 instrument, so the failed-breakout behavior is not robust across the available instrument set.

### Event Counts Are Adequate, So The Negative Result Is Interpretable

- **Observation**: All instruments pass the event-count gate in both train and test segments.
- **Evidence**: Test sweep counts are EURUSD `89`, XAUUSD `131`, BTCUSD `93`, and USTEC `160`. EURUSD and BTCUSD are below 100 but pass the balanced high/low rule: EURUSD `44/45`, BTCUSD `51/42`.
- **Interpretation**: The result is not inconclusive due to sample size. The failed support criterion reflects effect inconsistency, not insufficient event coverage.

### Train/Test Direction Is Not Stable

- **Observation**: EURUSD passes only in test while its train effect is negative; USTEC is mildly positive in both segments but never significant; XAUUSD and BTCUSD are negative in test.
- **Evidence**: EURUSD Train diff is `-0.061`, CI `[-0.145, 0.021]`, while EURUSD Test is positive. BTCUSD is negative in both train and test. XAUUSD is near-zero to negative in both segments.
- **Interpretation**: The one supporting EURUSD test result should be treated as instrument-specific, not a general ICT sweep effect.

### Secondary Excursion Metrics Do Not Rescue The Hypothesis

- **Observation**: Test-segment sweeps often have lower MFE and lower MAE than breaches. Hit2R differences are mixed.
- **Evidence**: Weighted test-segment 60-minute MFE_R means for sweeps versus breaches are EURUSD `6.788` vs `29.085`, XAUUSD `7.543` vs `30.957`, BTCUSD `8.505` vs `34.251`, and USTEC `6.763` vs `29.680`. Hit2R means are better for EURUSD sweeps (`0.448` vs `0.359`), worse for XAUUSD (`0.299` vs `0.338`) and BTCUSD (`0.256` vs `0.398`), and nearly tied for USTEC (`0.288` vs `0.282`).
- **Interpretation**: Sweeps can reduce both favorable and adverse path movement relative to breaches, but that does not satisfy the predefined 1R-before-stop support rule.

## Hypothesis Verdict

**REFUTED**

Failed PDH/PDL and ONH/ONL sweeps do not show robust opposite-direction behavior across the available instruments. The primary support threshold required at least 3 instruments; the experiment finds only 1.

## Limitations

- The experiment uses 1-minute OHLC data only; no tick, spread, bid/ask, slippage, or commission data is available.
- The price precision step is an observed close-to-close proxy, not an exchange tick-size field.
- Bootstrap intervals resample events and do not fully model temporal clustering.
- The result applies to sweep-only events. It does not test macro-window context, premium/discount location, displacement, IFVG, breaker confirmation, or full strategy execution.

## Alternative Explanations

- The sweep definition may identify a real phenomenon only on specific instruments or regimes, as suggested by EURUSD's isolated test result.
- Breaches may have larger overall excursion because they include stronger continuation moves, while sweeps may represent lower-volatility rejection behavior rather than a directional edge.
- Missing transaction-cost data means the results characterize gross path behavior, not net tradable performance.

## Recommended Next Steps

1. Run EXP-016 as scoped: test whether sweep outcomes differ inside versus outside macro windows.
2. Treat EXP-015 as a weak standalone H2 component; do not promote sweep-only signals into a full strategy without additional component evidence.
