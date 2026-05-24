# Experiment: EXP-013 - NY Macro Window Characterization

## Hypothesis

Predefined NY macro windows have statistically different range, absolute return, sweep frequency, displacement frequency, or forward-return shape than adjacent and randomized control windows on the available instruments.

## Question

Are predefined NY macro windows statistically different from adjacent and randomized control windows?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`; no Line Break, Renko, or Heiken Ashi inputs.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used.
- **Global holdout**: The final 30% of each chronologically ordered instrument dataset is excluded from all analysis.
- **Look-ahead bias prevention**: Features and events use only bars with `CloseTime` at or before the event timestamp.
- **Real-price outcome discipline**: All outcomes use real time-bar OHLC prices aligned by timestamp.
- **Exclusions**: No full ICT model, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data unless explicitly identified as unavailable or proxied.
- **Parameters**: Fixed NY macro windows from EXP-012; adjacent equal-duration controls immediately before and after each macro window where available; 100 deterministic same-day randomized equal-duration control windows per instrument/segment using a fixed seed and excluding macro overlaps; primary H1 metric = window true range normalized by ATR_14; secondary metrics = absolute close-to-close return, sweep frequency, displacement frequency, and forward returns at 10/20/60 minutes.
- **Secondary metric denominators**: One macro or control window observation is the denominator for sweep frequency, displacement frequency, and forward-return availability. Sweep frequency is descriptive only and uses EXP-014 liquidity definitions: a high sweep is `High > PDH/ONH` and `Close < PDH/ONH`; a low sweep is `Low < PDL/ONL` and `Close > PDL/ONL`. PDH/PDL are eligible all day; ONH/ONL are eligible only for windows starting at or after 09:30 NY to avoid look-ahead. Displacement frequency is descriptive only and counts a window if any contained 1-minute bar has true range at or above the prior rolling 100-bar 80th percentile and closes in the top 25 percent or bottom 25 percent of its own range. Forward returns use the close before the window as baseline and the first available close at or after 10/20/60 minutes after the window end.

## Success / Failure Criteria

- **Evidence FOR**: the primary metric differs from both adjacent and randomized controls on at least 3 of 4 instruments, with bootstrap confidence intervals excluding zero and median practical effect size >= 0.10 ATR.
- **Evidence AGAINST**: the primary metric is mixed, near zero, or fails against either control on at least 3 instruments; secondary-only differences are not sufficient for support.
- **Inconclusive**: sample size or coverage is below the EXP-012 readiness thresholds.

## Prerequisites and Sequencing

Requires EXP-012 data-readiness approval for NY-time conversion, usable macro-window coverage, and cost-data status. This experiment characterizes H1 only and must not optimize or drop macro windows based on results.

## Complexity Budget

- Max statistical tests: 2
- Max visualisations: 4
- Max new code modules: 1

## Data Requirements

Use sorted 1-minute bars by `CloseTime` for each available instrument. Convert timestamps to New York time where scoped. Apply the nested chronological split before any feature, event, or outcome analysis, and never materialize the final 30 percent holdout.

## Suggested Direction

Compare fixed macro windows against adjacent and randomized controls using non-parametric intervals, not optimized windows.
