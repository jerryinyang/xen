# Experiment: EXP-019 - Micro Swing Break Confirmation After Sweep

## Hypothesis

A micro swing break after a sweep improves signal quality beyond the simpler displacement definition.

## Question

Does requiring a micro swing break after sweep improve signal quality beyond simpler displacement?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`; no Line Break, Renko, or Heiken Ashi inputs.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used.
- **Global holdout**: The final 30% of each chronologically ordered instrument dataset is excluded from all analysis.
- **Look-ahead bias prevention**: Features and events use only bars with `CloseTime` at or before the event timestamp.
- **Real-price outcome discipline**: All outcomes use real time-bar OHLC prices aligned by timestamp.
- **Exclusions**: No full ICT model, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data unless explicitly identified as unavailable or proxied.
- **Parameters**: Micro swing break after an EXP-015 failed sweep: a swing low/high is confirmed only after the two bars to its right have closed, so the swing's usable timestamp is the confirmation bar, not the pivot bar; bearish confirmation closes below the most recent usable confirmed swing low, bullish confirmation closes above the most recent usable confirmed swing high; compare to EXP-018 candle/body displacement without combining both filters.

## Success / Failure Criteria

- **Evidence FOR**: micro swing break improves primary outcome versus EXP-018 displacement by >= 0.25R or materially lowers MAE on at least 3 instruments.
- **Evidence AGAINST**: no improvement, excessive delay, or sparse events.
- **Inconclusive**: definition is reproducible but effects conflict across instruments.

## Prerequisites and Sequencing

Requires EXP-015 and should be interpreted alongside EXP-018 as an H3 variant. This experiment must not use future pivot knowledge at the event timestamp and must not combine swing-break and candle/body displacement.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 5
- Max new code modules: 2

## Data Requirements

Use sorted 1-minute bars by `CloseTime` for each available instrument. Convert timestamps to New York time where scoped. Apply the nested chronological split before any feature, event, or outcome analysis, and never materialize the final 30 percent holdout.

## Suggested Direction

Isolate swing-break confirmation from candle-size displacement.
