# Analysis Plan: Experiment EXP-006

## Objective

Quantify how much Heiken Ashi synthetic prices distort real return magnitude and volatility compared with the underlying 1-minute time-bar prices.

## Methodology

### Step 1: Generate Heiken Ashi and Paired Real-Price Series

- **Method**: Sequential Heiken Ashi generation from analysis-set time bars, retaining paired `HAClose` and `RealClose` at each `CloseTime`.
- **Why this method**: HA distortion is only meaningful when synthetic and real prices are compared at identical timestamps.
- **Simpler alternative considered**: Compare aggregate HA range to aggregate real range. That misses close-to-close return distortion and regime dependence.
- **Assumptions**: HA generation is deterministic and uses only completed bars; paired timestamps are exact because HA has one row per source bar.
- **Expected output**: Paired HA/real table per instrument with close-to-close synthetic and real returns.

### Step 2: Compute Distortion Metrics

- **Method**: Descriptive compression ratios for median absolute return, realised volatility, high-low range, and direction-change frequency; stratify by volatility tercile using thresholds calibrated on the train segment and applied only to the later evaluation segment.
- **Why this method**: Ratios directly quantify the synthetic-price distortion named in the hypothesis.
- **Simpler alternative considered**: Single volatility compression factor. It is necessary but insufficient because HA can also distort direction changes and return magnitudes differently.
- **Assumptions**: HA returns are diagnostic synthetic-price changes, not tradable returns; real returns use `RealClose`.
- **Expected output**: Distortion table by instrument and volatility regime.

### Step 3: Estimate Uncertainty of Compression

- **Method**: Block bootstrap confidence intervals for volatility and median absolute return compression ratios, with both metrics evaluated from the same resampled blocks for efficiency and consistency.
- **Why this method**: Block bootstrap respects temporal clustering better than independent row resampling and avoids normality assumptions.
- **Simpler alternative considered**: Parametric confidence interval for variance ratios. It assumes distributional properties that are weak for market returns.
- **Assumptions**: Blocks provide an approximate uncertainty measure; results are descriptive, not a claim of stationary compression.
- **Expected output**: Compression-ratio intervals and support/refutation flags.

## Visualisations

1. Paired real versus HA close timeline for one representative window - shows smoothing visually.
2. Bar chart of volatility compression by instrument - tests the main threshold.
3. Box plot of absolute real and HA returns by instrument - compares magnitude distributions.
4. Heatmap of compression ratios by instrument and volatility regime - shows regime dependence.

## Interpretation Guide

- If all 4 instruments show at least 30% volatility compression and at least 20% median absolute return compression, the hypothesis is supported.
- If fewer than 3 instruments meet thresholds or intervals overlap zero for most instruments, the hypothesis is refuted.
- If aggregate compression is strong but concentrated in one regime, the result is partially supported and should be documented as regime-dependent distortion.

## Complexity Check

- Statistical tests: 2 / 2
- Visualisations: 4 / 4
- New modules: 1 / 1

## Chart-Type Comparison Considerations

### Cross-Chart Alignment

- HA rows align exactly to source bars by `CloseTime`; no bar-index alignment across different chart types is needed.
- The experiment does not include Line Break or Renko.

### Synthetic Price Discipline

- HA returns are explicitly labelled synthetic diagnostic returns.
- Conclusions must state that HA-price-derived returns are unsuitable for strategy evaluation if compression thresholds are met.

### Bar Density Differences

- HA and time bars have the same row count by design; still report row counts after holdout exclusion.

### Regime Stratification

- Regime labels are derived from real time-bar volatility and applied to paired HA rows by `CloseTime`, but only after the calibration segment so regime-dependent summaries do not use future-informed thresholds.
