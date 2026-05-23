# Experiment: EXP-026 - Incremental ICT Component Ablation

## Hypothesis

Validated ICT components contribute measurable net value when combined incrementally, after accounting for sample-size loss.

## Question

Which validated components contribute net value when combined incrementally?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`; no Line Break, Renko, or Heiken Ashi inputs.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used.
- **Global holdout**: The final 30% of each chronologically ordered instrument dataset is excluded from all analysis.
- **Look-ahead bias prevention**: Features and events use only bars with `CloseTime` at or before the event timestamp.
- **Real-price outcome discipline**: All outcomes use real time-bar OHLC prices aligned by timestamp.
- **Exclusions**: No full ICT model, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data unless explicitly identified as unavailable or proxied.
- **Parameters**: Add one previously validated component at a time in a fixed order: sweep, macro, premium/discount, displacement, IFVG, breaker, execution rule, risk model. A component is eligible only if its prior experiment documented deterministic implementation, train/test sample counts above its floor, and non-negative or clearly diagnostic contribution. Components that failed may be included only as labelled negative controls, not as candidate model rules.

## Success / Failure Criteria

- **Evidence FOR**: at least one component adds net expectancy or risk-adjusted improvement beyond sample-size effects and survives train/test comparison.
- **Evidence AGAINST**: improvements disappear as components are combined or sample size collapses.
- **Inconclusive**: too few components have prior evidence to form a chain.

## Prerequisites and Sequencing

Requires completed EXP-015 through EXP-025 for every component included. This produces the component contribution table and must finish before EXP-027 can be executed.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 5
- Max new code modules: 2

## Data Requirements

Use sorted 1-minute bars by `CloseTime` for each available instrument. Convert timestamps to New York time where scoped. Apply the nested chronological split before any feature, event, or outcome analysis, and never materialize the final 30 percent holdout.

## Suggested Direction

Produce a component contribution table before any full-model test.
