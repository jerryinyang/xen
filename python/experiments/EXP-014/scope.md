# Experiment: EXP-014 - PDH PDL ONH ONL Liquidity Level Reproducibility

## Hypothesis

Previous-day and overnight high/low liquidity levels can be computed reproducibly from available time bars without exchange-calendar or preferred-data assumptions that are absent from the repository.

## Question

Can previous-day and overnight high/low liquidity levels be computed reproducibly on the available instruments?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`; no Line Break, Renko, or Heiken Ashi inputs.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used.
- **Global holdout**: The final 30% of each chronologically ordered instrument dataset is excluded from all analysis.
- **Look-ahead bias prevention**: Features and events use only bars with `CloseTime` at or before the event timestamp.
- **Real-price outcome discipline**: All outcomes use real time-bar OHLC prices aligned by timestamp.
- **Exclusions**: No full ICT model, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data unless explicitly identified as unavailable or proxied.
- **Parameters**: PDH/PDL from the prior observed weekday NY date using all observed bars for that date in the analysis set; ONH/ONL from 17:00 NY on the prior calendar date through 09:30 NY on the event date where bars exist, using CloseTimeNY boundary membership; for instruments without clean session boundaries, record the observed-session caveat and compute levels from available bars only; no swing/equal-high levels.

## Success / Failure Criteria

- **Evidence FOR**: deterministic levels are produced for >= 80% of eligible NY dates on all EXP-012 usable instruments, with missing-level reasons classified and train/test counts above 50 dates per segment where coverage permits.
- **Evidence AGAINST**: level definitions are calendar-dependent in a way current data cannot support, or level availability is too sparse.
- **Inconclusive**: definitions work for continuous instruments but not session-bound instruments.

## Prerequisites and Sequencing

Requires EXP-012 data-readiness approval. EXP-015, EXP-016, EXP-017, EXP-018, and later sweep-dependent experiments must use these level definitions and missing-level rules unchanged.

## Complexity Budget

- Max statistical tests: 0-1
- Max visualisations: 4
- Max new code modules: 1

## Data Requirements

Use sorted 1-minute bars by `CloseTime` for each available instrument. Convert timestamps to New York time where scoped. Apply the nested chronological split before any feature, event, or outcome analysis, and never materialize the final 30 percent holdout.

## Suggested Direction

Validate level construction before testing sweep outcomes.
