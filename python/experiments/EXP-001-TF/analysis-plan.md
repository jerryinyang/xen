# Analysis Plan: Experiment EXP-001-TF

## Objective

Determine whether the EXP-001 information-density and ghost-bar conclusions replicate when Line Break, Renko, and Heiken Ashi are generated from 15-minute and 1-hour source bars instead of 1-minute bars.

## Methodology

### Step 1: Build Holdout-Safe Higher-Timeframe Samples

- **Method**: Lazily load each instrument's 1-minute bars, sort by `CloseTime`, slice the first 70% chronological analysis set, aggregate only that analysis set into complete 15-minute and 1-hour OHLCV bars, then generate chart types per timeframe.
- **Why this method**: Block A requires higher-timeframe replication while preserving the global holdout boundary.
- **Simpler alternative considered**: Aggregate the full 1-minute file then slice. That is not acceptable because it processes the global holdout.
- **Assumptions**: 1-minute bars are chronologically ordered after sorting; incomplete aggregation buckets at the analysis boundary can be dropped and reported.
- **Expected output**: A validation table with source rows, analysis rows, aggregated rows, dropped boundary rows, generated rows, and date ranges per instrument, timeframe, and chart type.

### Step 2: Compute Information-Density Metrics

- **Method**: Descriptive statistics for bar count, bars per day, ghost rate, directional entropy, directional-entropy headroom capture, absolute entropy gain, median absolute real-price movement per bar, coefficient of variation by volatility tercile, and distinct-source sensitivity metrics for event charts.
- **Why this method**: The experiment is a direct characterisation replication and does not require a model.
- **Simpler alternative considered**: Bar count alone. It does not distinguish useful compression from empty or low-information bars.
- **Assumptions**: Volatility terciles are derived only from same-timeframe time-bar analysis data and applied by timestamp; observations are temporally dependent.
- **Expected output**: Per-instrument, per-timeframe summary tables and distinct-source sensitivity tables.

### Step 3: Compare Event-Based Types With Same-Timeframe Time Bars

- **Method**: Paired instrument-level effect sizes for ghost-rate reduction, entropy-headroom capture, and absolute entropy gain, plus sign-count summaries and descriptive bootstrap confidence intervals. Verdict entropy comparisons use distinct-source event rows.
- **Why this method**: Four instruments are too few for strong parametric inference; paired effect sizes and bootstrap intervals are transparent and distribution-light.
- **Simpler alternative considered**: A t-test on instrument-level differences. It adds an unjustified normality assumption for very small n.
- **Assumptions**: Instruments are the primary comparison units; bootstrap intervals are descriptive uncertainty estimates.
- **Expected output**: Effect-size table with threshold flags, bootstrap 95% intervals, per-timeframe support/refutation flags, and a reproducibility manifest.

## Visualisations

1. Grouped bar chart of ghost rate by instrument, timeframe, and chart type.
2. Box plot of absolute real-price movement per bar by timeframe and chart type.
3. Heatmap of directional entropy by instrument, timeframe, and chart type.
4. Bar-density timeline by chart type for one representative instrument at each timeframe.

## Interpretation Guide

- If Line Break or Renko meets the EXP-001 practical thresholds on at least 3 instruments at both 15-minute and 1-hour timeframes, classify the finding as replicated.
- If the thresholds are met on fewer than 2 instruments at both timeframes, classify the finding as not replicated.
- If one timeframe replicates and the other does not, classify the finding as timeframe-conditional or attenuated.

## Complexity Check

- Statistical tests: 2 / 2
- Visualisations: 4 / 4
- New modules: 1 / 1

## Chart-Type Comparison Considerations

### Cross-Chart Alignment

- Align time bars and Heiken Ashi by `CloseTime`; align Line Break and Renko by `SourceCloseTime`.
- Never compare chart types by bar index.
- Report bar density per elapsed day for each timeframe.

### Synthetic Price Discipline

- Do not compute strategy returns or P&L.
- Heiken Ashi movement metrics use `RealClose`, not `HAClose`.
- Renko and Line Break movement metrics use `SourceCloseTime`-aligned same-timeframe time-bar closes.
- Exclude repeated `SourceCloseTime` rows from event ghost-rate denominators and report sensitivity metrics.

### Bar Density Differences

- Report sample sizes beside every metric.
- Separate raw chart-row summaries from distinct-source verdict metrics.

### Regime Stratification

- Use realised-volatility terciles from same-timeframe time bars.
- Apply regime labels to generated events by timestamp only.
