# Experiment: EXP-012 - ICT Data Readiness and Feasibility

## Hypothesis

The available 1-minute time-bar datasets are sufficient for deterministic NY-time ICT macro-window research if timezone conversion, session coverage, missing-bar rates, and cost assumptions can be documented without using unavailable data.

## Question

Is the current time-bar dataset sufficient for ICT macro-window research?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`; no Line Break, Renko, or Heiken Ashi inputs.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used.
- **Global holdout**: The final 30% of each chronologically ordered instrument dataset is excluded from all analysis.
- **Look-ahead bias prevention**: Features and events use only bars with `CloseTime` at or before the event timestamp.
- **Real-price outcome discipline**: All outcomes use real time-bar OHLC prices aligned by timestamp.
- **Exclusions**: No full ICT model, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data unless explicitly identified as unavailable or proxied.
- **Parameters**: Treat stored timestamps as the cTrader/server timestamps recorded in the file and document the conversion assumption before converting to `America/New_York`; macro windows AM1 07:50-08:10, AM2 08:50-09:10, AM3 09:50-10:10, AM4 10:50-11:10, AM5 11:50-12:10, PM1 13:20-13:40, PM2 14:50-15:10, PM3 15:15-15:45, PM4 15:50-16:10; observed active-session coverage by instrument; missing-bar checks; instrument coverage; spread/slippage availability audit.

## Success / Failure Criteria

- **Evidence FOR**: all four instruments can be converted to NY time with documented assumptions, have >= 80% observed bar coverage in each macro-window family in train and test, missing-bar rates are quantified, and unavailable spread/slippage fields have explicit proxy scenarios.
- **Evidence AGAINST**: NY-time conversion or macro-window assignment is unreliable for most instruments, or > 20% of expected bars are missing in macro windows for most instruments.
- **Inconclusive**: one or more instruments are usable but coverage gaps prevent a phase-wide conclusion.

## Prerequisites and Sequencing

This is the data-readiness gate for Phase 003 and has no prior experiment dependency. EXP-013 and all later macro-window or cost-sensitive experiments must use the timestamp, coverage, and cost-proxy decisions recorded here without changing them after seeing outcomes.

## Complexity Budget

- Max statistical tests: 0-1
- Max visualisations: 4
- Max new code modules: 1

## Data Requirements

Use sorted 1-minute bars by `CloseTime` for each available instrument. Convert timestamps to New York time where scoped. Apply the nested chronological split before any feature, event, or outcome analysis, and never materialize the final 30 percent holdout.

## Suggested Direction

Build a data-readiness table, macro-window coverage summary, missing-bar diagnostics, and explicit cost-data availability statement.
