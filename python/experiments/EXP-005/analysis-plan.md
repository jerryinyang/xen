# Analysis Plan: Experiment EXP-005

## Objective

Measure whether chart types agree on trend direction and event timing after timestamp alignment, and whether agreement is stronger in specific volatility regimes.

## Methodology

### Step 1: Build Direction and Regime Tables

- **Method**: Extract direction labels from time bars, Line Break, Renko, and Heiken Ashi; assign volatility regime labels from time-bar realised volatility.
- **Why this method**: Direction and regime are the minimal common concepts across all Phase 1 chart types.
- **Simpler alternative considered**: Use only up/down bar counts. That ignores whether directions occur at the same real times.
- **Assumptions**: Direction is chart-type-specific but comparable as a sign label; regime labels are descriptive and derived independently from time bars.
- **Expected output**: Per-chart-type event table with instrument, timestamp, direction, and regime.

### Step 2: Pairwise Timestamp Alignment

- **Method**: Nearest-neighbour timestamp matching within a fixed tolerance window, reporting overlap rate and unmatched rates for every chart-type pair.
- **Why this method**: It directly implements design compliance for cross-chart-type comparison by timestamp.
- **Simpler alternative considered**: Resampling all chart types to 1-minute timestamps. That may be useful later but can blur sparse event timing in this experiment.
- **Assumptions**: A tolerance window is necessary because event-based charts do not emit bars every minute; sensitivity to one wider tolerance can be reported without changing the main criterion.
- **Expected output**: Pairwise aligned event tables and overlap-rate summaries.

### Step 3: Estimate Direction Agreement by Regime

- **Method**: Pairwise agreement rates by instrument and regime, paired bootstrap intervals for Line Break/Renko agreement improvement versus each chart type's agreement with time bars.
- **Why this method**: Agreement rates are direct and interpretable; paired intervals avoid row-level independence assumptions.
- **Simpler alternative considered**: Cohen's kappa. Kappa can be informative, but with sparse event overlap and imbalanced directions it may obscure the raw agreement rate; it can be reported as a secondary sensitivity only if budget allows.
- **Assumptions**: Agreement does not imply predictive value or profitability; it only measures correspondence.
- **Expected output**: Agreement matrix, regime-stratified effect table, and support/refutation flags.

## Visualisations

1. Pairwise agreement heatmap by chart type and instrument - shows broad correspondence.
2. Regime-stratified agreement bar chart - answers the regime question.
3. Overlap-rate heatmap - separates low agreement from sparse matching.
4. Timeline raster of direction labels for one representative window - visually checks alignment.
5. Sensitivity plot for main agreement ranking under base and wider tolerance windows - checks robustness.

## Interpretation Guide

- If Line Break/Renko agreement exceeds each event type's agreement with time bars by at least 10 percentage points in medium/high regimes on at least 3 instruments, the hypothesis is supported.
- If Line Break/Renko agreement is not higher than time-bar agreement or falls below 50%, the hypothesis is refuted.
- If overlap rates are low, report agreement as inconclusive even if matched-event agreement is high.

## Complexity Check

- Statistical tests: 3 / 3
- Visualisations: 5 / 5
- New modules: 1 / 1

## Chart-Type Comparison Considerations

### Cross-Chart Alignment

- All pairwise comparisons use timestamp matching and report tolerance windows.
- No comparison uses bar index or equal row counts.
- The final 30% global holdout remains excluded before direction extraction, regime labelling, alignment, and plotting.
- Time bars and Heiken Ashi use `CloseTime`; Line Break and Renko use `SourceCloseTime`.

### Synthetic Price Discipline

- Agreement uses direction labels only.
- Heiken Ashi synthetic prices and Renko construction prices are not used for returns or P&L.
- This plan does not compute strategy returns, signal returns, or tradable P&L.

### Bar Density Differences

- Report overlap rate and event counts beside every agreement rate.

### Regime Stratification

- Main criterion focuses on medium- and high-volatility regimes, but all three regimes are reported for context.
