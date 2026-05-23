# Experiment: EXP-015 - Prior High Low Sweep Reversal Behavior

## Hypothesis

Failed breakouts beyond PDH/PDL or ONH/ONL show measurable opposite-direction behavior compared with non-failed breaches, using real time-bar prices and predeclared risk units.

## Question

Do prior-day and overnight high/low sweeps show measurable failed-breakout behavior?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`; no Line Break, Renko, or Heiken Ashi inputs.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used.
- **Global holdout**: The final 30% of each chronologically ordered instrument dataset is excluded from all analysis.
- **Look-ahead bias prevention**: Features and events use only bars with `CloseTime` at or before the event timestamp.
- **Real-price outcome discipline**: All outcomes use real time-bar OHLC prices aligned by timestamp.
- **Exclusions**: No full ICT model, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data unless explicitly identified as unavailable or proxied.
- **Parameters**: Sweep definitions: bearish high sweep `High > level + buffer` and `Close < level`; bullish low sweep `Low < level - buffer` and `Close > level`; buffer `max(price_precision_step, 0.05 * ATR_14)` where `price_precision_step` is the smallest positive observed price increment in the analysis set for that instrument; horizons 30, 60, 120 minutes; stop/invalidation is the sweep extreme plus/minus the same buffer; initial risk is absolute distance from sweep close to stop.

## Success / Failure Criteria

- **Evidence FOR**: failed sweeps improve the primary outcome, 1R-before-stop probability at 60 minutes, versus non-failed breaches on at least 3 instruments with >= 100 failed-sweep events per train/test segment or >= 50 when events are balanced across high and low sweeps.
- **Evidence AGAINST**: failed sweeps do not outperform breaches, or adverse excursion dominates.
- **Inconclusive**: event counts fall below >= 100 failed-sweep events per train/test segment, or >= 50 when events are balanced across high and low sweeps, or the confidence interval on the primary difference crosses zero on most instruments.

## Prerequisites and Sequencing

Requires EXP-014 level reproducibility approval. This is a sweep-only event study before macro, premium/discount, displacement, IFVG, or breaker filters are allowed.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 5
- Max new code modules: 2

## Data Requirements

Use sorted 1-minute bars by `CloseTime` for each available instrument. Convert timestamps to New York time where scoped. Apply the nested chronological split before any feature, event, or outcome analysis, and never materialize the final 30 percent holdout.

## Suggested Direction

Run a sweep-only event study before adding macro, displacement, IFVG, or breaker filters.
