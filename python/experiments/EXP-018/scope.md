# Experiment: EXP-018 - Displacement Confirmation Added to Sweeps

## Hypothesis

Adding a deterministic displacement candle after a sweep improves sweep-only outcomes enough to offset delayed confirmation and fewer signals.

## Question

Does adding deterministic displacement improve sweep-only outcomes?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`; no Line Break, Renko, or Heiken Ashi inputs.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used.
- **Global holdout**: The final 30% of each chronologically ordered instrument dataset is excluded from all analysis.
- **Look-ahead bias prevention**: Features and events use only bars with `CloseTime` at or before the event timestamp.
- **Real-price outcome discipline**: All outcomes use real time-bar OHLC prices aligned by timestamp.
- **Exclusions**: No full ICT model, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data unless explicitly identified as unavailable or proxied.
- **Parameters**: Displacement after an EXP-015 failed sweep: directional candle body, body size >= 1.5 * rolling median absolute body over the prior 100 completed bars, and close location in the directional quartile of that candle range; displacement must occur within 10 bars after the sweep; compare sweep-close entry proxy to displacement-close and next-open entry proxies using unchanged stop/risk definitions.

## Success / Failure Criteria

- **Evidence FOR**: sweep plus displacement improves 60-minute expectancy by >= 0.05R or 1R-before-stop probability by >= 5 percentage points on at least 3 instruments while retaining >= 50 confirmed events per train/test segment.
- **Evidence AGAINST**: confirmation delays entries without improving quality, or reduces samples below threshold.
- **Inconclusive**: improvement appears on train but not test.

## Prerequisites and Sequencing

Requires EXP-015 sweep-only event definitions. This experiment uses only the candle/body displacement variant; swing-break confirmation is reserved for EXP-019.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 5
- Max new code modules: 2

## Data Requirements

Use sorted 1-minute bars by `CloseTime` for each available instrument. Convert timestamps to New York time where scoped. Apply the nested chronological split before any feature, event, or outcome analysis, and never materialize the final 30 percent holdout.

## Suggested Direction

Use one candle/body displacement definition only; do not combine with swing break yet.
