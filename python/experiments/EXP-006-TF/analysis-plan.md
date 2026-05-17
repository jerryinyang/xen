# Analysis Plan: Experiment EXP-006-TF

## Objective

Quantify how much Heiken Ashi synthetic prices distort real return magnitude and volatility on 15-minute and 1-hour source bars, then classify whether the EXP-006 synthetic-price warning replicates.

## Methodology

### Step 1: Generate Higher-Timeframe Heiken Ashi and Paired Real-Price Series

- **Method**: Lazily load each instrument's 1-minute bars, sort by `CloseTime`, slice the first 70% chronological analysis set, aggregate only that analysis set into complete 15-minute and 1-hour bars, then sequentially generate Heiken Ashi while retaining paired `HAClose` and `RealClose` at each `CloseTime`.
- **Why this method**: HA distortion is meaningful only when synthetic and real prices are compared at identical timestamps and the global holdout is excluded before aggregation.
- **Simpler alternative considered**: Compare aggregate HA range to aggregate real range. That misses close-to-close return distortion and regime dependence.
- **Assumptions**: HA generation is deterministic and uses only completed aggregated bars; paired timestamps are exact because HA has one row per source bar.
- **Expected output**: Paired HA/real tables per instrument and timeframe with close-to-close synthetic and real returns.

### Step 2: Compute Distortion Metrics

- **Method**: Descriptive compression ratios for median absolute return, realised volatility, high-low range, and direction-change frequency; stratify by same-timeframe volatility tercile using thresholds calibrated on the train segment and applied only to the later evaluation segment.
- **Why this method**: Ratios directly quantify the synthetic-price distortion named in the hypothesis.
- **Simpler alternative considered**: A single volatility compression factor. It is necessary but insufficient because HA can distort direction changes and return magnitudes differently.
- **Assumptions**: HA returns are diagnostic synthetic-price changes, not tradable returns; real returns use `RealClose`.
- **Expected output**: Distortion tables by instrument, timeframe, and volatility regime.

### Step 3: Estimate Uncertainty of Compression

- **Method**: Block bootstrap confidence intervals for volatility and median absolute return compression ratios, with both metrics evaluated from the same resampled blocks for efficiency and consistency.
- **Why this method**: Block bootstrap respects temporal clustering better than independent row resampling and avoids normality assumptions.
- **Simpler alternative considered**: Parametric confidence interval for variance ratios. It assumes distributional properties that are weak for market returns.
- **Assumptions**: Blocks provide approximate uncertainty; results are descriptive, not a claim of stationary compression.
- **Expected output**: Compression-ratio intervals and support/refutation flags by timeframe.

## Visualisations

1. Paired real versus HA close timeline for one representative window by timeframe.
2. Bar chart of volatility compression by instrument and timeframe.
3. Box plot of absolute real and HA returns by instrument and timeframe.
4. Heatmap of compression ratios by instrument, timeframe, and volatility regime.

## Interpretation Guide

- If all 4 instruments show at least 30% volatility compression and at least 20% median absolute return compression at both timeframes, classify the EXP-006 distortion warning as replicated.
- If fewer than 3 instruments meet thresholds at both timeframes or intervals overlap zero for most instruments, classify the finding as not replicated.
- If aggregate compression is strong but concentrated in one timeframe or regime, classify the result as timeframe-conditional or regime-dependent distortion.

## Complexity Check

- Statistical tests: 2 / 2
- Visualisations: 4 / 4
- New modules: 1 / 1

## Chart-Type Comparison Considerations

### Cross-Chart Alignment

- HA rows align exactly to aggregated source bars by `CloseTime`; no bar-index alignment across different chart types is needed.
- This experiment does not include Line Break or Renko.

### Synthetic Price Discipline

- HA returns are explicitly labelled synthetic diagnostic returns.
- Conclusions must state whether HA-price-derived returns remain unsuitable for strategy evaluation at higher source timeframes.

### Bar Density Differences

- HA and same-timeframe time bars have the same row count by design; still report row counts after holdout exclusion and aggregation.

### Regime Stratification

- Regime labels are derived from real same-timeframe volatility and applied to paired HA rows by `CloseTime`, but only after the calibration segment so regime-dependent summaries do not use future-informed thresholds.
