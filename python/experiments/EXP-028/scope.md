# Experiment: EXP-028 - ICT Candidate Robustness and Falsification

## Hypothesis

A candidate ICT variant is robust only if it survives predeclared year/regime/instrument segmentation, execution-delay perturbation, and spread/slippage stress.

## Question

Does the candidate survive robustness and falsification checks?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`; no Line Break, Renko, or Heiken Ashi inputs.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used.
- **Global holdout**: The final 30% of each chronologically ordered instrument dataset is excluded from all analysis.
- **Look-ahead bias prevention**: Features and events use only bars with `CloseTime` at or before the event timestamp.
- **Real-price outcome discipline**: All outcomes use real time-bar OHLC prices aligned by timestamp.
- **Exclusions**: No unapproved full-model variant, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data unless explicitly identified as unavailable or proxied.
- **Parameters**: Segment the EXP-027 candidate by year, instrument, train/test segment, ATR_14 volatility tercile computed inside the analysis set, execution delays of 0/1/2 bars, and EXP-012 cost scenarios; no parameter refitting or threshold tuning.

## Success / Failure Criteria

- **Evidence FOR**: candidate remains non-negative after costs in test overall, positive in at least two-thirds of instrument/year or volatility segments with >= 30 trades, and does not lose all edge under 1-bar delay or base cost stress.
- **Evidence AGAINST**: edge vanishes under plausible costs, execution delay, or segmentation.
- **Inconclusive**: candidate was not eligible from EXP-027 or data coverage is insufficient.

## Prerequisites and Sequencing

Requires EXP-027 approval. Robustness checks are falsification only; any new parameter choice or regime-specific variant requires a later experiment scope.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 5
- Max new code modules: 2

## Data Requirements

Use sorted 1-minute bars by `CloseTime` for each available instrument. Convert timestamps to New York time where scoped. Apply the nested chronological split before any feature, event, or outcome analysis, and never materialize the final 30 percent holdout.

## Suggested Direction

Use robustness to falsify, not optimize, the candidate.
