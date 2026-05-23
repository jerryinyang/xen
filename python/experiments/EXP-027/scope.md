# Experiment: EXP-027 - Predeclared Full ICT Model Analysis-Set Test

## Hypothesis

The best predeclared full-model variant survives analysis-set testing after costs and robustness checks only if prior component experiments justify every included rule.

## Question

Does the best predeclared full-model variant survive analysis-set testing after costs and robustness checks?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`; no Line Break, Renko, or Heiken Ashi inputs.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used.
- **Global holdout**: The final 30% of each chronologically ordered instrument dataset is excluded from all analysis.
- **Look-ahead bias prevention**: Features and events use only bars with `CloseTime` at or before the event timestamp.
- **Real-price outcome discipline**: All outcomes use real time-bar OHLC prices aligned by timestamp.
- **Exclusions**: No unapproved full ICT model variant, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data unless explicitly identified as unavailable or proxied.
- **Parameters**: One predeclared variant selected from EXP-026 with all rules frozen before execution; no optimization; include explicit spread/slippage scenarios from EXP-012; evaluate only analysis-set train/test.

## Success / Failure Criteria

- **Evidence FOR**: the model has positive median expectancy after costs, >= 100 train and >= 50 test trades overall with at least 3 contributing instruments, stable train/test direction, and no single instrument contributing > 60% of net R.
- **Evidence AGAINST**: expectancy is non-positive after costs, unstable, or dominated by simpler component baselines.
- **Inconclusive**: prerequisite components do not identify an eligible model.

## Prerequisites and Sequencing

Requires EXP-026 approval and a frozen model-variant manifest listing included components, parameters, entry, stop, target, and cost scenario. This is the first allowed full-model analysis-set test and still excludes the global holdout.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 5
- Max new code modules: 2

## Data Requirements

Use sorted 1-minute bars by `CloseTime` for each available instrument. Convert timestamps to New York time where scoped. Apply the nested chronological split before any feature, event, or outcome analysis, and never materialize the final 30 percent holdout.

## Suggested Direction

Run only after component ablation identifies eligible variants.
