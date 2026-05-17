# Analysis Plan: Experiment EXP-002-TF

## Objective

Assess whether the EXP-002 volatility-regime boundary-cost conclusion replicates when Line Break and Renko are generated from 15-minute and 1-hour source bars.

## Methodology

### Step 1: Build Holdout-Safe Higher-Timeframe Regime Tables

- **Method**: Lazily load each instrument's 1-minute bars, sort by `CloseTime`, slice the first 70% chronological analysis set, aggregate only that analysis set into complete 15-minute and 1-hour bars, and compute rolling realised volatility on each aggregated timeframe.
- **Why this method**: It creates the higher-timeframe regime reference without touching the global holdout.
- **Simpler alternative considered**: Reuse 1-minute regime labels. That would not test same-timeframe regime representation.
- **Assumptions**: Aggregated source bars are ordered by `CloseTime`; early rows without a rolling window have undefined regimes and are reported.
- **Expected output**: Timestamped regime tables by instrument and timeframe with transition timestamps, duration summaries, and undefined-window counts.

### Step 2: Align Chart-Type Events to the Same-Timeframe Regime Timeline

- **Method**: Generate Line Break, Renko, and Heiken Ashi from the aggregated analysis bars, then timestamp-join each chart-type event to the current same-timeframe regime using `CloseTime` or `SourceCloseTime`.
- **Why this method**: It follows the project rule that chart types are compared by timestamp, not sequence number.
- **Simpler alternative considered**: Assign regimes by generated bar sequence number. That violates chart-type alignment rules.
- **Assumptions**: Every generated event maps to a source timestamp within the analysis set; missing mappings are reported and excluded from denominators.
- **Expected output**: Aligned event tables with row counts, matched rows, null-regime rows, transition counts, and denominators.

### Step 3: Measure Hybrid Rate and Transition Lag

- **Method**: Descriptive transition metrics plus paired bootstrap confidence intervals for event-chart excess cost versus the same-timeframe time-bar lower bound. Transition lag is measured in both source bars and clock time.
- **Why this method**: Hybrid rate and lag directly match the EXP-002 hypothesis without distributional assumptions.
- **Simpler alternative considered**: Kruskal-Wallis tests across chart types. They do not directly quantify boundary cost versus the lower bound.
- **Assumptions**: Transition events are temporally clustered; bootstrap intervals are descriptive and should be computed at transition-block or instrument level where possible.
- **Expected output**: Per-instrument and per-timeframe effect-size tables for hybrid rate, median lag, p95 lag, max lag, missed transitions, verdict flags, and a reproducibility manifest.

## Visualisations

1. Regime timeline with chart-type events overlaid for one representative instrument and timeframe.
2. Grouped bar chart of hybrid rate by chart type, instrument, and timeframe.
3. Box plot of confirmed transition lag by chart type and timeframe.
4. Heatmap of absolute excess boundary cost by instrument, timeframe, and metric.

## Interpretation Guide

- If Line Break or Renko stays within the EXP-002 absolute boundary-cost limits on at least 3 instruments at both timeframes, classify the finding as replicated.
- If both event-based types exceed either boundary-cost limit on at least 3 instruments at both timeframes, classify the finding as not replicated for higher timeframes.
- If hybrid rate and lag point in different directions, or one timeframe differs materially from the other, report a timeframe-conditioned trade-off.

## Complexity Check

- Statistical tests: 3 / 3
- Visualisations: 4 / 4
- New modules: 1 / 1

## Chart-Type Comparison Considerations

### Cross-Chart Alignment

- Use timestamp joins from generated events to same-timeframe regimes.
- Report unmatched and null-regime event counts.
- Do not compute percentage improvement when the same-timeframe time-bar baseline is zero; use absolute excess cost.

### Synthetic Price Discipline

- Do not compute strategy P&L.
- Heiken Ashi direction may use HA candle direction, but realised volatility and price movement use real source prices.

### Bar Density Differences

- Report transition count, matched-transition count, missed-transition count, p95 lag, and max lag.

### Regime Stratification

- Regime labels are the primary object of this experiment and must be derived from same-timeframe time bars before chart-type comparison.
