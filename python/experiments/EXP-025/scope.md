# Experiment: EXP-025 - Fixed 1 to 2 Risk Reward Justification

## Hypothesis

A fixed 2R target is justified only if it outperforms simpler target/stop alternatives in expectancy or robustness for an approved entry definition.

## Question

Is the fixed 1:2 risk/reward target justified versus alternatives?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`; no Line Break, Renko, or Heiken Ashi inputs.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used.
- **Global holdout**: The final 30% of each chronologically ordered instrument dataset is excluded from all analysis.
- **Look-ahead bias prevention**: Features and events use only bars with `CloseTime` at or before the event timestamp.
- **Real-price outcome discipline**: All outcomes use real time-bar OHLC prices aligned by timestamp.
- **Exclusions**: No full ICT model, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data unless explicitly identified as unavailable or proxied.
- **Parameters**: Compare 1R, 1.5R, 2R, 3R, a 60-minute time stop, and nearest opposing-liquidity target after an entry definition has >= 100 train and >= 50 test events on at least 3 instruments; stops fixed by approved sweep/IFVG/breaker logic; nearest opposing liquidity is prior-day or overnight high/low from EXP-014 in the trade direction, chosen at entry time only.

## Success / Failure Criteria

- **Evidence FOR**: 2R produces better expectancy or robustness than alternatives on at least 3 instruments with acceptable drawdown.
- **Evidence AGAINST**: 2R is dominated by simpler targets or has unstable outcomes.
- **Inconclusive**: no entry definition has enough sample size.

## Prerequisites and Sequencing

Requires an approved entry definition from EXP-021, EXP-023, or EXP-024. This is an exit/risk experiment only; it must not introduce new entry filters or retune stops based on target outcomes.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 5
- Max new code modules: 2

## Data Requirements

Use sorted 1-minute bars by `CloseTime` for each available instrument. Convert timestamps to New York time where scoped. Apply the nested chronological split before any feature, event, or outcome analysis, and never materialize the final 30 percent holdout.

## Suggested Direction

Treat exits as a separate experiment, not as part of component discovery.
