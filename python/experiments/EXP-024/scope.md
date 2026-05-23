# Experiment: EXP-024 - Second Candle Open Execution Timing

## Hypothesis

The second-candle-open execution rule improves or preserves entry quality versus simpler post-confirmation entries.

## Question

Does the second-candle-open execution rule improve or degrade entry quality versus simpler post-confirmation entries?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`; no Line Break, Renko, or Heiken Ashi inputs.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used.
- **Global holdout**: The final 30% of each chronologically ordered instrument dataset is excluded from all analysis.
- **Look-ahead bias prevention**: Features and events use only bars with `CloseTime` at or before the event timestamp.
- **Real-price outcome discipline**: All outcomes use real time-bar OHLC prices aligned by timestamp.
- **Exclusions**: No full ICT model, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data unless explicitly identified as unavailable or proxied.
- **Parameters**: Compare confirmation-close proxy, immediate next-open, second-candle-open, and first deterministic retest entry after the same approved IFVG or breaker confirmation event; first retest means the first later bar whose high/low touches the confirmation zone before invalidation, using only bars after confirmation; no new filters.

## Success / Failure Criteria

- **Evidence FOR**: second-candle-open has equal or better expectancy/MAE than simpler entries on at least 3 instruments without worse slippage proxy.
- **Evidence AGAINST**: second-candle-open materially degrades entry price, R distribution, or hit rate.
- **Inconclusive**: differences are small with intervals crossing zero.

## Prerequisites and Sequencing

Requires an approved confirmation event definition from EXP-021 or EXP-023. This isolates execution timing and must not change confirmation filters, stops, targets, or event eligibility.

## Complexity Budget

- Max statistical tests: 2
- Max visualisations: 4
- Max new code modules: 1

## Data Requirements

Use sorted 1-minute bars by `CloseTime` for each available instrument. Convert timestamps to New York time where scoped. Apply the nested chronological split before any feature, event, or outcome analysis, and never materialize the final 30 percent holdout.

## Suggested Direction

Isolate execution timing from confirmation quality.
