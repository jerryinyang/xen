# Analysis Plan: Experiment EXP-002

## Objective

Assess whether Line Break and Renko provide cleaner volatility and trend regime representation than 1-minute time bars, using predefined regime labels derived from time-bar realised volatility.

## Methodology

### Step 1: Define Regime Labels From Time Bars

- **Method**: Rolling realised-volatility estimates on 1-minute time bars, labelled into low, medium, and high regimes using train-segment tercile thresholds.
- **Why this method**: It keeps the regime definition independent of the chart type being evaluated and avoids using future or holdout data.
- **Simpler alternative considered**: Full-analysis-set terciles. That is simpler but leaks later analysis-set distribution information into earlier timestamps.
- **Assumptions**: Regime labels are descriptive and locally estimated; financial volatility is non-stationary, so fixed terciles are treated as empirical bins, not stable market states.
- **Expected output**: Timestamped regime table per instrument with transition timestamps and regime duration summaries.

### Step 2: Align Chart-Type Events to Regime Timeline

- **Method**: Timestamp join from each chart-type event to the current time-bar regime using `CloseTime` or `SourceCloseTime`.
- **Why this method**: It follows the design requirement that chart types are compared by time, not bar index.
- **Simpler alternative considered**: Assign regimes by generated bar sequence number. That violates chart-type alignment rules and is excluded.
- **Assumptions**: Every generated event maps to a source timestamp within the analysis set; missing mappings are reported and excluded from metric denominators.
- **Expected output**: Aligned event table with chart type, instrument, source timestamp, direction, and regime.

### Step 3: Measure Hybrid Rate and Transition Lag

- **Method**: Descriptive transition metrics plus paired bootstrap confidence intervals for chart-type improvement over time bars.
- **Why this method**: Hybrid rate and lag directly match the hypothesis and avoid distributional assumptions.
- **Simpler alternative considered**: Kruskal-Wallis test across chart types. It tests broad distribution differences but does not directly quantify improvement versus baseline.
- **Assumptions**: Transition events are temporally clustered and not independent; bootstrap intervals are computed at transition-block or instrument level where possible.
- **Expected output**: Per-instrument effect-size table for hybrid rate reduction and median lag reduction.

## Visualisations

1. Regime timeline with chart-type events overlaid for one representative instrument - verifies alignment.
2. Grouped bar chart of hybrid rate by chart type and instrument - compares boundary cleanliness.
3. Box plot of transition lag by chart type - compares speed of regime reflection.
4. Heatmap of improvement versus time bars by instrument and metric - shows consistency.

## Interpretation Guide

- If Line Break or Renko has at least 20% lower hybrid rate and transition lag than time bars on at least 3 instruments with intervals excluding zero, the hypothesis is supported.
- If time bars equal or beat both event-based types on at least 3 instruments, the hypothesis is refuted.
- If hybrid rate improves while transition lag worsens, the result is inconclusive and should be reported as a trade-off rather than a win.

## Complexity Check

- Statistical tests: 3 / 3
- Visualisations: 4 / 4
- New modules: 1 / 1

## Chart-Type Comparison Considerations

### Cross-Chart Alignment

- Use only timestamp joins from generated events to time-bar regimes.
- Report unmatched event counts and exclude unmatched rows from metric denominators.

### Synthetic Price Discipline

- Do not compute strategy P&L.
- Heiken Ashi direction may use HA candle direction, but any realised volatility or price movement uses real time-bar prices.

### Bar Density Differences

- Report event counts around each transition to avoid mistaking sparse events for clean regimes.

### Regime Stratification

- Regime labels are the primary object of this experiment and must be derived from time bars before chart-type comparison.
