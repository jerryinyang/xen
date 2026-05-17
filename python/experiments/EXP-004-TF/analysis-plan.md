# Analysis Plan: Experiment EXP-004-TF

## Objective

Quantify the detection latency and precision of chart-type trend reversal signals against real-price reversal references built from 15-minute and 1-hour time bars, then classify whether the EXP-004 speed-fidelity conclusion replicates.

## Methodology

### Step 1: Build Higher-Timeframe Real-Price Reversal References

- **Method**: Lazily load each instrument's 1-minute bars, sort by `CloseTime`, slice the first 70% chronological analysis set, aggregate only that analysis set into complete 15-minute and 1-hour bars, then run the EXP-004 ATR-scaled swing reversal detector on each timeframe.
- **Why this method**: It creates same-timeframe real-price references while respecting when reversals would have become knowable.
- **Simpler alternative considered**: Use the original 1-minute reversal reference. That would not test higher-timeframe market-structure capture.
- **Assumptions**: The reference is an operational label, not ground truth market structure; sensitivity to the alternate ATR threshold is reported.
- **Expected output**: Reference reversal tables per instrument and timeframe with confirmation timestamp and direction.

### Step 2: Extract Chart-Type Reversal Signals

- **Method**: Generate chart types from each aggregated timeframe and extract direction-change events timestamped by `CloseTime` for time bars and Heiken Ashi and `SourceCloseTime` for Line Break and Renko.
- **Why this method**: Direction changes are the simplest comparable reversal signal across chart types and preserve EXP-004's metric definition.
- **Simpler alternative considered**: Pattern-specific structure labels. That would broaden the experiment beyond the replication scope.
- **Assumptions**: Chart types have different event densities, so false and duplicate signals must be normalised per real-time window.
- **Expected output**: Signal tables by instrument, timeframe, chart type, timestamp, and direction.

### Step 3: Match Signals to Real Reversals

- **Method**: Event matching within the fixed 120-minute tolerance window, reporting median latency in clock minutes and source bars, total signal precision, recall, and split rate. Use exact instrument-count summaries for the 3-of-4 decision rule.
- **Why this method**: These metrics map directly to speed and fidelity without strategy-return assumptions.
- **Simpler alternative considered**: Correlation between signal direction and future price movement. That would move toward predictive validation and is out of scope.
- **Assumptions**: Matched events are temporally dependent; interpretation focuses on instrument-level summaries and effect sizes. Precision counts duplicate same-direction signals in the denominator.
- **Expected output**: Speed-precision table, latency intervals, support/refutation flags, and reversal-label stability diagnostics under the alternate threshold.

## Visualisations

1. Event timeline for one representative reversal cluster by timeframe.
2. Box plot of detection latency by chart type and timeframe.
3. Precision-recall scatter by chart type, instrument, and timeframe.
4. Bar chart of split rate by chart type and timeframe.
5. Heatmap of latency improvement versus precision change by instrument and timeframe.

## Interpretation Guide

- If Line Break or Renko reduces median latency by at least 30% on at least 3 instruments at both timeframes and precision does not exceed time bars by more than 10 percentage points, classify the speed-trade-off hypothesis as replicated.
- If event-based chart types do not materially reduce latency at both higher timeframes, classify the EXP-004 finding as replicated in its refuted direction.
- If latency improves at one timeframe but not the other, report the finding as timeframe-conditional and do not generalize it to subsequent signal-quality work without qualification.

## Complexity Check

- Statistical tests: 3 / 3
- Visualisations: 5 / 5
- New modules: 1 / 1

## Chart-Type Comparison Considerations

### Cross-Chart Alignment

- Match events by timestamp tolerance windows, never by bar sequence.
- Report unmatched real reversals and unmatched chart-type signals.
- Time bars and Heiken Ashi use `CloseTime`; Line Break and Renko use `SourceCloseTime`.

### Synthetic Price Discipline

- Reversal reference and validation use real same-timeframe time-bar prices.
- Heiken Ashi may produce direction-change signals, but HA synthetic prices are not used as real reversal evidence.
- This plan does not compute strategy returns or P&L.

### Bar Density Differences

- Normalise false signal and split rates per elapsed time and per reference reversal count.
- Precision uses total emitted signals.

### Regime Stratification

- Report optional low/medium/high volatility breakdown only if each regime has enough reversals for stable summaries.
