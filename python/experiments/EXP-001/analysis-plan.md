# Analysis Plan: Experiment EXP-001

## Objective

Determine whether Line Break and Renko provide more information-dense bars than 1-minute time bars over the Phase 1 analysis set, while characterising where Heiken Ashi sits as a smoothed one-bar-per-source-bar transformation.

## Methodology

### Step 1: Build Comparable Chart-Type Samples

- **Method**: Deterministic chart generation on the pre-holdout analysis set, followed by timestamp alignment to real 1-minute closes.
- **Why this method**: It directly matches the project architecture and prevents generated chart events from seeing holdout data.
- **Simpler alternative considered**: Use raw generated bar counts only. That is insufficient because ghost rate and movement metrics require comparable real-price coordinates.
- **Assumptions**: The source time bars are chronologically ordered by `CloseTime`; generated event bars expose `SourceCloseTime`; Heiken Ashi carries `RealClose`. These assumptions are required by the dataset reference and fit the Phase 1 design.
- **Expected output**: A validation table with source rows, analysis rows, generated rows, and date ranges per instrument and chart type.

### Step 2: Compute Information-Density Metrics

- **Method**: Descriptive statistics for bar count, bars per day, ghost rate, directional entropy, median absolute real-price movement per bar, and coefficient of variation by volatility tercile.
- **Why this method**: The experiment is a characterisation task; simple descriptive metrics answer the question without model assumptions.
- **Simpler alternative considered**: Bar count alone. It does not distinguish useful compression from empty or low-information bars.
- **Assumptions**: Volatility terciles are derived only from the time-bar analysis set and then applied by timestamp; observations are temporally dependent, so the plan reports effect sizes and uncertainty rather than assuming independent rows.
- **Expected output**: Per-instrument and pooled summary tables.

### Step 3: Compare Event-Based Types With Time Bars

- **Method**: Paired instrument-level bootstrap confidence intervals for ghost-rate reduction and entropy increase, plus a sign-count summary across instruments.
- **Why this method**: Four instruments are too few for strong parametric inference; paired bootstrap intervals and sign counts are transparent and distribution-light.
- **Simpler alternative considered**: A t-test on instrument-level differences. It adds an unjustified normality assumption for very small n.
- **Assumptions**: Instruments are treated as the primary comparison units; bootstrap results are descriptive uncertainty estimates, not proof of independent market behavior.
- **Expected output**: Effect-size table with bootstrap 95% intervals and support/refutation flags.

## Visualisations

1. Grouped bar chart of ghost rate by instrument and chart type - shows empty-bar reduction.
2. Box plot of absolute real-price movement per bar by chart type - shows information concentration.
3. Heatmap of directional entropy by instrument and chart type - shows cross-instrument consistency.
4. Bar-density timeline by chart type for one representative instrument - shows temporal compression without aligning by bar index.

## Interpretation Guide

- If Line Break or Renko reduces ghost rate by at least 25% and increases entropy by at least 10% on at least 3 instruments with intervals excluding zero, the hypothesis is supported.
- If improvements occur in only 1 instrument or confidence intervals include zero across all event-based types, the hypothesis is refuted.
- If results differ by instrument class or effects are consistent but below threshold, the result is inconclusive and should guide narrower Phase 2 scopes.

## Complexity Check

- Statistical tests: 2 / 2
- Visualisations: 4 / 4
- New modules: 1 / 1

## Chart-Type Comparison Considerations

### Cross-Chart Alignment

- Align time bars and Heiken Ashi by `CloseTime`; align Line Break and Renko by `SourceCloseTime`.
- Never compare the nth bar of one chart type to the nth bar of another.
- Report bar density per elapsed day because chart types produce different row counts.

### Synthetic Price Discipline

- Do not compute strategy returns or P&L.
- Heiken Ashi movement metrics use `RealClose`, not `HAClose`.
- Renko and Line Break movement metrics use `SourceCloseTime`-aligned time-bar closes, not construction closes for return-like quantities.

### Bar Density Differences

- Report both per-bar and per-day metrics so compression is not mistaken for superior information.
- Keep sample-size counts visible beside every metric.

### Regime Stratification

- Use realised-volatility terciles from the 1-minute time-bar analysis set.
- Apply regime labels to generated events by timestamp only.
