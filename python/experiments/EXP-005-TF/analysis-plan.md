# Analysis Plan: Experiment EXP-005-TF

## Objective

Measure whether the EXP-005 cross-chart agreement conclusion replicates when chart types are generated from 15-minute and 1-hour source bars.

## Methodology

### Step 1: Build Higher-Timeframe Direction and Regime Tables

- **Method**: Lazily load each instrument's 1-minute bars, sort by `CloseTime`, slice the first 70% chronological analysis set, aggregate only that analysis set into complete 15-minute and 1-hour bars, extract direction labels from time bars, Line Break, Renko, and Heiken Ashi, collapse repeated event-chart rows at the same source timestamp, and assign same-timeframe volatility regime labels calibrated on the train segment.
- **Why this method**: Direction and regime are the minimal common concepts across all chart types and must be defined at the tested timeframe.
- **Simpler alternative considered**: Use only up/down bar counts. That ignores whether directions occur at the same real times.
- **Assumptions**: Direction is chart-type-specific but comparable as a sign label; regime labels are descriptive and derived independently from same-timeframe time bars.
- **Expected output**: Per-chart-type event tables with instrument, timeframe, timestamp, direction, and regime.

### Step 2: Pairwise Timestamp Alignment

- **Method**: Nearest-neighbour timestamp matching within the EXP-005 primary 5-minute tolerance window for sparse event-chart pairs, with a 15-minute sensitivity and exact timestamp alignment for time-bar versus Heiken Ashi comparisons where `CloseTime` is shared.
- **Why this method**: It directly implements timestamp-based cross-chart comparison without sequence alignment.
- **Simpler alternative considered**: Resampling all chart types to every source bar. That can blur sparse event timing and changes the EXP-005 matching rule.
- **Assumptions**: A tolerance window is necessary because event-based charts do not emit bars every source bar; sparse overlap is itself an important result.
- **Expected output**: Pairwise aligned event tables and overlap-rate summaries by instrument and timeframe.

### Step 3: Estimate Direction Agreement by Regime

- **Method**: Pairwise agreement rates by instrument, timeframe, and regime, plus paired bootstrap intervals for Line Break/Renko agreement improvement versus each chart type's agreement with same-timeframe time bars on the medium/high-regime subset.
- **Why this method**: Agreement rates are direct and interpretable; paired intervals avoid row-level independence assumptions.
- **Simpler alternative considered**: Cohen's kappa. It can obscure raw agreement under sparse overlap and imbalanced directions.
- **Assumptions**: Agreement does not imply predictive value or profitability; it only measures correspondence.
- **Expected output**: Agreement matrices, regime-stratified effect tables, overlap-rate diagnostics, and support/refutation flags by timeframe.

## Visualisations

1. Pairwise agreement heatmap by chart type, instrument, and timeframe.
2. Regime-stratified agreement bar chart by timeframe.
3. Overlap-rate heatmap by pair and timeframe.
4. Timeline raster of direction labels for one representative window at each timeframe.
5. Sensitivity plot for the main agreement ranking under 5-minute and 15-minute tolerance windows.

## Interpretation Guide

- If Line Break/Renko agreement exceeds each event type's agreement with same-timeframe time bars by at least 10 percentage points in medium/high regimes on at least 3 instruments at both timeframes, classify the finding as replicated.
- If Line Break/Renko agreement is not higher than same-timeframe time-bar agreement or falls below 50% at both timeframes, classify the finding as not replicated.
- If overlap rates are low, report the result as inconclusive even if matched-event agreement is high.

## Complexity Check

- Statistical tests: 3 / 3
- Visualisations: 5 / 5
- New modules: 1 / 1

## Chart-Type Comparison Considerations

### Cross-Chart Alignment

- All pairwise comparisons use timestamp matching and report tolerance windows.
- No comparison uses bar index or equal row counts.
- Time bars and Heiken Ashi use `CloseTime`; Line Break and Renko use `SourceCloseTime`.

### Synthetic Price Discipline

- Agreement uses direction labels only.
- Heiken Ashi synthetic prices and Renko construction prices are not used for returns or P&L.
- This plan does not compute strategy returns, signal returns, or tradable P&L.

### Bar Density Differences

- Report overlap rate and event counts beside every agreement rate.

### Regime Stratification

- Main criterion focuses on medium- and high-volatility regimes, but all three regimes are reported for context.
