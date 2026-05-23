# Experiment: EXP-023 - Breaker Confirmation Trade Quality

## Hypothesis

Adding one approved breaker confirmation improves trade quality beyond sweep plus displacement or IFVG baselines, not merely win rate.

## Question

Does breaker confirmation improve trade quality beyond sweep plus displacement or IFVG?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`; no Line Break, Renko, or Heiken Ashi inputs.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used.
- **Global holdout**: The final 30% of each chronologically ordered instrument dataset is excluded from all analysis.
- **Look-ahead bias prevention**: Features and events use only bars with `CloseTime` at or before the event timestamp.
- **Real-price outcome discipline**: All outcomes use real time-bar OHLC prices aligned by timestamp.
- **Exclusions**: No full ICT model, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data unless explicitly identified as unavailable or proxied.
- **Parameters**: Use the single breaker candidate selected by EXP-022. The pre-breaker baseline must be predeclared before execution as either the approved displacement baseline from EXP-018/EXP-019 or the approved IFVG baseline from EXP-021; no post-hoc "best baseline" selection. Report expectancy, drawdown proxy, trade count, and average R.

## Success / Failure Criteria

- **Evidence FOR**: breaker confirmation improves expectancy or drawdown-adjusted return on at least 3 instruments while retaining >= 50 breaker-confirmed events per train/test segment.
- **Evidence AGAINST**: win rate improves only by reducing samples, expectancy does not improve, or drawdown worsens.
- **Inconclusive**: candidate is valid but event count is too low.

## Prerequisites and Sequencing

Requires EXP-022 plus the baseline experiment named in the implementation config before execution. This experiment tests one breaker definition at a time and cannot combine IFVG and breaker unless that confluence is explicitly chosen as the predeclared baseline.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 5
- Max new code modules: 2

## Data Requirements

Use sorted 1-minute bars by `CloseTime` for each available instrument. Convert timestamps to New York time where scoped. Apply the nested chronological split before any feature, event, or outcome analysis, and never materialize the final 30 percent holdout.

## Suggested Direction

Test one breaker definition at a time; no combined full-model optimization.
