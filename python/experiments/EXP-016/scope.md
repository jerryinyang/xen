# Experiment: EXP-016 - Macro Window Interaction With Sweep Outcomes

## Hypothesis

Sweep outcomes inside predefined macro windows are materially different from sweep outcomes outside macro windows after accounting for event count and instrument coverage.

## Question

Are sweep outcomes materially different inside macro windows versus outside macro windows?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`; no Line Break, Renko, or Heiken Ashi inputs.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used.
- **Global holdout**: The final 30% of each chronologically ordered instrument dataset is excluded from all analysis.
- **Look-ahead bias prevention**: Features and events use only bars with `CloseTime` at or before the event timestamp.
- **Real-price outcome discipline**: All outcomes use real time-bar OHLC prices aligned by timestamp.
- **Exclusions**: No full ICT model, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data unless explicitly identified as unavailable or proxied.
- **Parameters**: Use EXP-015 sweep definition and EXP-012 macro windows; compare inside-window sweeps to outside-window sweeps matched by instrument, sweep side, and NY date where possible; no additional confirmation filters; primary outcome is the same 60-minute 1R-before-stop probability from EXP-015.

## Success / Failure Criteria

- **Evidence FOR**: inside-macro sweeps improve the primary sweep outcome by >= 5 percentage points or reduce median MAE by >= 0.25R on at least 3 instruments while retaining >= 50 inside-window sweep events and >= 50 matched outside-window comparator events per train/test segment.
- **Evidence AGAINST**: macro filtering gives no improvement or only reduces sample size.
- **Inconclusive**: macro-window sweep counts or matched outside-window comparator counts are below the event-count floor.

## Prerequisites and Sequencing

Requires EXP-012 macro readiness and EXP-015 sweep outcome definitions. Results may affect whether macro is included in later ablations, but they must not remove the need to characterize later ICT components.

## Complexity Budget

- Max statistical tests: 2
- Max visualisations: 4
- Max new code modules: 1

## Data Requirements

Use sorted 1-minute bars by `CloseTime` for each available instrument. Convert timestamps to New York time where scoped. Apply the nested chronological split before any feature, event, or outcome analysis, and never materialize the final 30 percent holdout.

## Suggested Direction

Measure interaction between H1 and H2 before treating macro windows as a required setup condition.
