# Analysis Plan: Experiment EXP-003

## Objective

Measure whether chart-type statistics are stable under predefined synthetic noise injection, without treating the noise experiment as a trading simulation or optimisation problem.

## Methodology

### Step 1: Generate Deterministic Perturbed Source Bars

- **Method**: Apply fixed 0%, 10%, 20%, and 30% perturbation levels to analysis-set 1-minute bars only, with OHLC repair and validation.
- **Why this method**: Deterministic perturbation gives repeatable stress tests and avoids adding simulation variance to a Phase 1 characterisation experiment.
- **Simpler alternative considered**: Single 20% perturbation only. It would answer the success criterion but would not reveal whether robustness degrades monotonically.
- **Assumptions**: Perturbations are artificial stressors, not a realistic microstructure noise model; results describe robustness to this perturbation family only.
- **Expected output**: Validated perturbed time-bar datasets and row-level perturbation audit counts.

### Step 2: Regenerate Chart Types and Compute Stability Metrics

- **Method**: Sequentially regenerate all chart types from each perturbed source dataset, then compute direction stability, variance ratio stability, and Lempel-Ziv complexity drift versus unperturbed baseline.
- **Why this method**: It measures the chart transformation's response to source noise rather than only the source bars' response.
- **Simpler alternative considered**: Compare only close-to-close return variance. That misses direction and sequence-complexity robustness, both named in the phase design.
- **Assumptions**: Metrics are descriptive and temporally dependent; no i.i.d. row-level inference is assumed.
- **Expected output**: Stability metric table by instrument, chart type, noise level, and metric.

### Step 3: Rank Robustness Versus Time Bars

- **Method**: Instrument-level paired relative-drift comparison and permutation/sign summaries for event-based chart types versus time bars at the 20% noise level.
- **Why this method**: The hypothesis is about relative stability at a named stress level; paired comparisons keep instrument differences controlled.
- **Simpler alternative considered**: Kruskal-Wallis over all rows. Row-level tests would overstate evidence because observations are serially dependent.
- **Assumptions**: Instrument-level paired differences are the appropriate unit for support/refutation; permutation summaries are descriptive with small n.
- **Expected output**: Robustness ranking table and support/refutation flags.

## Visualisations

1. Line plot of relative metric drift by noise level and chart type - shows degradation curves.
2. Heatmap of 20% noise robustness rank by instrument and metric - shows consistency.
3. Box plot of direction stability by chart type at 20% noise - compares core hypothesis metric.
4. Bar chart of invalid or repaired OHLC rows by instrument and noise level - validates perturbation quality.
5. Scatter plot of variance drift versus complexity drift - shows robustness trade-offs.

## Interpretation Guide

- If Line Break or Renko has at least 25% lower relative drift than time bars in at least two metrics on at least 3 instruments, the hypothesis is supported.
- If time bars are as stable or more stable in at least two metrics on at least 3 instruments, the hypothesis is refuted.
- If Heiken Ashi reduces variance but synthetic-to-real distortion grows materially, report that as the expected smoothing/distortion trade-off, not as strategy evidence.

## Complexity Check

- Statistical tests: 3 / 3
- Visualisations: 5 / 5
- New modules: 1 / 1

## Chart-Type Comparison Considerations

### Cross-Chart Alignment

- Compare each perturbed chart type to its own unperturbed baseline by timestamp where possible.
- Never force equal row counts by bar index across chart types.
- The final 30% global holdout remains excluded before perturbation, generation, metric computation, and plotting.
- Time bars use `CloseTime`; Line Break and Renko use `SourceCloseTime` for event-time context.

### Synthetic Price Discipline

- Heiken Ashi distortion diagnostics may use `HAClose` versus `RealClose`, but no tradable return conclusion may be drawn from HA prices.
- Renko stability uses generated direction and real timestamp context, not brick-price P&L.

### Bar Density Differences

- Report generated row counts at every noise level because perturbations may change event-bar frequency.

### Regime Stratification

- Regime stratification is optional and limited to a sensitivity table if the main robustness rankings are ambiguous.
