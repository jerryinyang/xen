# Experiment: EXP-021 - IFVG Confirmation Entry Quality

## Hypothesis

IFVG confirmation improves entry quality enough to offset later entry timing and fewer signals compared with simpler post-sweep entries.

## Question

Does IFVG confirmation improve entry quality enough to offset later entry and fewer signals?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`; no Line Break, Renko, or Heiken Ashi inputs.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used.
- **Global holdout**: The final 30% of each chronologically ordered instrument dataset is excluded from all analysis.
- **Look-ahead bias prevention**: Features and events use only bars with `CloseTime` at or before the event timestamp.
- **Real-price outcome discipline**: All outcomes use real time-bar OHLC prices aligned by timestamp.
- **Exclusions**: No full ICT model, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data unless explicitly identified as unavailable or proxied.
- **Parameters**: Use EXP-015 sweeps, the approved EXP-018 or EXP-019 displacement prerequisite selected before execution, and EXP-020 IFVG rules; compare four fixed entry timestamps only: sweep rejection close, displacement confirmation close, IFVG close, and second-candle-open after IFVG close; retest entry is included only if EXP-020 defines a deterministic first-touch retest before this experiment starts. All four entry proxies keep the original EXP-015 stop. If the inherited stop distance for any proxy falls below the original EXP-015 `Buffer`, that row is counted in chain diagnostics but excluded from R-based outcome and bootstrap summaries as infeasible under the inherited-stop convention.

## Success / Failure Criteria

- **Evidence FOR**: IFVG-confirmed entries improve expectancy or drawdown-adjusted return versus simpler entries on at least 3 instruments with >= 50 risk-feasible IFVG-confirmed events per train/test segment.
- **Evidence AGAINST**: later entries degrade R distribution or sample size dominates.
- **Inconclusive**: too few IFVG confirmations after prerequisites.

## Prerequisites and Sequencing

Requires EXP-015, EXP-018 or EXP-019, and EXP-020. The chosen displacement prerequisite and any retest rule must be written into the implementation config before outcomes are inspected. EXP-020's readiness finding remains acknowledged: this experiment is a diagnostic consequence check of the frozen current IFVG rule set, not a promotion of that rule as already selective enough for downstream use.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 5
- Max new code modules: 2

## Data Requirements

Use sorted 1-minute bars by `CloseTime` for each available instrument. Convert timestamps to New York time where scoped. Apply the nested chronological split before any feature, event, or outcome analysis, and never materialize the final 30 percent holdout. Carry the original EXP-015 sweep `Buffer` forward as the minimum feasible inherited risk denominator for all delayed-entry R-multiple calculations.

## Suggested Direction

Compare a small fixed set of entry timestamps without optimizing confirmation delay.
