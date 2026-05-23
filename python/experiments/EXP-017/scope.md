# Experiment: EXP-017 - Premium Discount Filter Impact on Sweep Quality

## Hypothesis

A previous-day midpoint premium/discount filter improves sweep quality enough to justify the sample-size cost.

## Question

Does previous-day midpoint premium/discount filtering improve sweep quality or only reduce sample size?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`; no Line Break, Renko, or Heiken Ashi inputs.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used.
- **Global holdout**: The final 30% of each chronologically ordered instrument dataset is excluded from all analysis.
- **Look-ahead bias prevention**: Features and events use only bars with `CloseTime` at or before the event timestamp.
- **Real-price outcome discipline**: All outcomes use real time-bar OHLC prices aligned by timestamp.
- **Exclusions**: No full ICT model, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data unless explicitly identified as unavailable or proxied.
- **Parameters**: Premium/discount midpoint = prior-day `(PDH + PDL) / 2` from EXP-014; bearish high sweeps require sweep close above the midpoint; bullish low sweeps require sweep close below the midpoint; compare to unfiltered EXP-015 sweeps using identical stop, horizon, and risk definitions.

## Success / Failure Criteria

- **Evidence FOR**: filtered sweeps improve EXP-015's primary 60-minute 1R-before-stop probability by >= 5 percentage points or reduce median MAE by >= 0.25R on at least 3 instruments while retaining >= 50% of EXP-015 failed-sweep events or >= 50 events per train/test segment.
- **Evidence AGAINST**: filter does not improve outcomes or removes too many events.
- **Inconclusive**: mixed effects with wide intervals.

## Prerequisites and Sequencing

Requires EXP-014 level definitions and EXP-015 sweep outcomes. Do not add VWAP, distance-from-open, overnight midpoint, or other location filters in this experiment.

## Complexity Budget

- Max statistical tests: 2
- Max visualisations: 4
- Max new code modules: 1

## Data Requirements

Use sorted 1-minute bars by `CloseTime` for each available instrument. Convert timestamps to New York time where scoped. Apply the nested chronological split before any feature, event, or outcome analysis, and never materialize the final 30 percent holdout.

## Suggested Direction

Test the simplest location filter before adding VWAP, open-price, or distance variants.
