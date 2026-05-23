# Experiment: EXP-022 - Objective Breaker Candidate Reproducibility

## Hypothesis

At least one objective breaker candidate can be defined reproducibly with enough occurrences to justify outcome testing.

## Question

Which objective breaker candidate is reproducible enough for testing?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`; no Line Break, Renko, or Heiken Ashi inputs.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used.
- **Global holdout**: The final 30% of each chronologically ordered instrument dataset is excluded from all analysis.
- **Look-ahead bias prevention**: Features and events use only bars with `CloseTime` at or before the event timestamp.
- **Real-price outcome discipline**: All outcomes use real time-bar OHLC prices aligned by timestamp.
- **Exclusions**: No full ICT model, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data unless explicitly identified as unavailable or proxied.
- **Parameters**: Compare candidate definitions only: Candidate B swing-structure break from the planning spec and Candidate A last-opposite-candle/order-block proxy from the planning spec; each candidate is evaluated after an EXP-015 failed sweep and an approved displacement event; boundaries, confirmation timestamp, invalidation, and duplicate handling must be recorded; no profitability comparison beyond counts and reproducibility.

## Success / Failure Criteria

- **Evidence FOR**: one candidate has deterministic boundaries, clear invalidation rules, and >= 50 train/test occurrences on at least 3 usable instruments.
- **Evidence AGAINST**: candidates are ambiguous, overly discretionary, or sparse.
- **Inconclusive**: one candidate works only for a subset of instruments.

## Prerequisites and Sequencing

Requires EXP-015 and an approved displacement definition from EXP-018 or EXP-019. EXP-023 may test only one breaker candidate selected here before outcome results are inspected.

## Complexity Budget

- Max statistical tests: 0-1
- Max visualisations: 4
- Max new code modules: 1

## Data Requirements

Use sorted 1-minute bars by `CloseTime` for each available instrument. Convert timestamps to New York time where scoped. Apply the nested chronological split before any feature, event, or outcome analysis, and never materialize the final 30 percent holdout.

## Suggested Direction

Select at most one breaker definition for a later outcome experiment.
