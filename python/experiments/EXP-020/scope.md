# Experiment: EXP-020 - FVG IFVG Detection Reproducibility

## Hypothesis

Three-candle FVGs and close-through IFVG inversions can be detected reproducibly with stable sample sizes on available time bars.

## Question

Can FVG and IFVG zones be detected reproducibly with stable sample sizes?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`; no Line Break, Renko, or Heiken Ashi inputs.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used.
- **Global holdout**: The final 30% of each chronologically ordered instrument dataset is excluded from all analysis.
- **Look-ahead bias prevention**: Features and events use only bars with `CloseTime` at or before the event timestamp.
- **Real-price outcome discipline**: All outcomes use real time-bar OHLC prices aligned by timestamp.
- **Exclusions**: No full ICT model, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data unless explicitly identified as unavailable or proxied.
- **Parameters**: Bearish FVG `High[i] < Low[i-2]`; bullish FVG `Low[i] > High[i-2]`; FVG size must be >= `max(price_precision_step, 0.02 * ATR_14)` using the EXP-015 price precision convention; IFVG requires a later close through the opposite side after formation; lifecycle states are formed, partially filled, fully filled, inverted, and expired after 120 bars; no profitability claims.

## Success / Failure Criteria

- **Evidence FOR**: FVG and IFVG counts, lifecycle states, and invalidation reasons are reproducible with >= 100 FVGs and >= 50 IFVGs per usable instrument/segment where coverage permits.
- **Evidence AGAINST**: definitions are too sparse, ambiguous, or unstable.
- **Inconclusive**: FVGs are common but IFVG inversions are too sparse for later entry studies.

## Prerequisites and Sequencing

Requires EXP-012 data readiness only. EXP-021 must use the FVG size, lifecycle, and IFVG close-through rules from this experiment unchanged.

## Complexity Budget

- Max statistical tests: 0-1
- Max visualisations: 4
- Max new code modules: 1

## Data Requirements

Use sorted 1-minute bars by `CloseTime` for each available instrument. Convert timestamps to New York time where scoped. Apply the nested chronological split before any feature, event, or outcome analysis, and never materialize the final 30 percent holdout.

## Suggested Direction

Validate zone detection mechanics before attaching IFVGs to sweep entries.
