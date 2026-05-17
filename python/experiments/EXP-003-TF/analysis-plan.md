# Analysis Plan: Experiment EXP-003-TF

## Objective

Measure whether the EXP-003 noise-robustness findings replicate when deterministic perturbations are applied to 15-minute and 1-hour aggregated source bars.

## Methodology

### Step 1: Build and Perturb Holdout-Safe Higher-Timeframe Bars

- **Method**: Lazily load each instrument's 1-minute bars, sort by `CloseTime`, slice the first 70% chronological analysis set, aggregate only that analysis set into complete 15-minute and 1-hour bars, then apply fixed 0%, 10%, 20%, and 30% perturbation levels with OHLC repair.
- **Why this method**: It tests robustness at the Block A source timeframes without allowing perturbation or aggregation to touch the global holdout.
- **Simpler alternative considered**: Perturb 1-minute bars before aggregation. That changes the noise model and would not replicate EXP-003 on higher-timeframe source bars.
- **Assumptions**: Perturbations are artificial stressors, not realistic microstructure noise; results describe robustness to this perturbation family only.
- **Expected output**: Validated perturbed higher-timeframe datasets and row-level perturbation and repair audit counts.

### Step 2: Regenerate Chart Types and Compute Stability Metrics

- **Method**: Sequentially regenerate chart types from each perturbed source dataset, then compute direction stability, return variance stability, and Lempel-Ziv 76 complexity drift versus each timeframe's unperturbed baseline. For Heiken Ashi, return variance stability uses HAClose returns as a non-tradable distortion diagnostic.
- **Why this method**: It measures each chart transformation's response to source noise rather than only the source bars' response.
- **Simpler alternative considered**: Compare only close-to-close return variance. That misses direction and sequence-complexity robustness.
- **Assumptions**: Metrics are descriptive and temporally dependent; no row-level i.i.d. inference is assumed.
- **Expected output**: Stability metric table by instrument, timeframe, chart type, noise level, and metric.

### Step 3: Rank Robustness Versus Same-Timeframe Time Bars

- **Method**: Instrument-level paired relative-drift comparisons and permutation/sign summaries for Line Break and Renko versus same-timeframe time bars at the 20% noise level.
- **Why this method**: The EXP-003 hypothesis is about relative stability at a named stress level; paired comparisons control instrument differences.
- **Simpler alternative considered**: Kruskal-Wallis over all rows. Row-level tests would overstate evidence because observations are serially dependent.
- **Assumptions**: Instrument-level paired differences are the appropriate unit for support/refutation; permutation summaries are descriptive with small n.
- **Expected output**: Robustness ranking table and support/refutation flags by timeframe.

## Visualisations

1. Line plot of relative metric drift by noise level, timeframe, and chart type.
2. Heatmap of 20% noise robustness rank by instrument, timeframe, and metric.
3. Box plot of direction stability by chart type at 20% noise, faceted by timeframe.
4. Bar chart of invalid or repaired OHLC rows by instrument, timeframe, and noise level.
5. Scatter plot of return variance drift versus complexity drift by timeframe.

## Interpretation Guide

- If Line Break or Renko has at least 25% lower relative drift than same-timeframe time bars in at least two metrics on at least 3 instruments at both timeframes, classify the EXP-003 robustness finding as replicated.
- If same-timeframe time bars are as stable or more stable in at least two metrics on at least 3 instruments at both timeframes, classify the finding as not replicated.
- If Heiken Ashi shows lower HAClose variance drift but larger HAClose-to-RealClose distortion, report the expected smoothing/distortion trade-off, not strategy evidence.

## Complexity Check

- Statistical tests: 3 / 3
- Visualisations: 5 / 5
- New modules: 1 / 1

## Chart-Type Comparison Considerations

### Cross-Chart Alignment

- Compare each perturbed chart type to its own unperturbed same-timeframe baseline by timestamp where possible.
- Never force equal row counts by bar index across chart types.
- Time bars use `CloseTime`; Line Break and Renko use `SourceCloseTime` for event-time context.

### Synthetic Price Discipline

- Heiken Ashi return variance stability uses HAClose returns only as a distortion diagnostic.
- Renko stability uses generated direction and real timestamp context, not brick-price P&L.

### Bar Density Differences

- Report generated row counts at every noise level and timeframe.

### Regime Stratification

- Regime stratification is optional and limited to a sensitivity table if the main robustness rankings are ambiguous.
