# Analysis Plan: Experiment EXP-002

## Objective

Assess the boundary cost Line Break and Renko incur when mapped onto volatility and trend regimes derived from 1-minute time bars. The time-bar baseline is a lower bound because regimes are defined on those bars.

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

- **Method**: Descriptive transition metrics plus paired bootstrap confidence intervals for chart-type excess cost versus the time-bar lower bound.
- **Why this method**: Hybrid rate and lag directly match the hypothesis and avoid distributional assumptions.
- **Simpler alternative considered**: Kruskal-Wallis test across chart types. It tests broad distribution differences but does not directly quantify boundary cost versus the baseline.
- **Assumptions**: Transition events are temporally clustered and not independent; bootstrap intervals are computed at transition-block or instrument level where possible.
- **Expected output**: Per-instrument effect-size table for absolute hybrid-rate and median-lag excess versus the time-bar lower bound.

## Visualisations

1. Regime timeline with chart-type events overlaid for one representative instrument - verifies alignment.
2. Grouped bar chart of hybrid rate by chart type and instrument - compares boundary cleanliness.
3. Box plot of transition lag by chart type - compares speed of regime reflection.
4. Heatmap of absolute or relative improvement versus time bars by instrument and metric - shows consistency without dividing by a zero baseline.

## Interpretation Guide

- If Line Break or Renko stays within the predefined absolute boundary-cost limits on at least 3 instruments, the chart type preserves usable regime representation.
- If both event-based types exceed either boundary-cost limit on at least 3 instruments, the original cleaner-than-time-bars hypothesis is refuted.
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
- Do not compute percentage improvement when the time-bar baseline is zero; use absolute differences and label them as such.

### Regime Stratification

- Regime labels are the primary object of this experiment and must be derived from time bars before chart-type comparison.
