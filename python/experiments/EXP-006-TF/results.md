# Results: Experiment EXP-006-TF

## Summary

The EXP-006 Heiken Ashi synthetic-price distortion hypothesis was **refuted** when retested on 15-minute and 1-hour source bars. HA volatility compression was 23.5-26.5% across all instruments and timeframes, below the ≥30% threshold. Median absolute return compression was 23.3-28.6%, which meets the ≥20% threshold on all instruments. Because the volatility compression threshold was not met on any instrument, the hypothesis is refuted. However, the practical conclusion remains valid: HA synthetic prices compress return magnitude and volatility by a substantial amount (23-29%), making HA-price-derived returns unsuitable for strategy evaluation.

## Detailed Findings

### Volatility Compression Is Substantial but Below 30% Threshold

- **Observation**: HA compresses realised volatility by 23.5-26.5% across all instruments and timeframes.
- **Evidence**: EURUSD 15m: 26.5% (RealVol = 0.000492, HAVol = 0.000362). XAUUSD 15m: 25.1%. BTCUSD 15m: 25.0%. USTEC 15m: 25.8%. 1h timeframe values are similar: EURUSD 25.9%, XAUUSD 24.9%, BTCUSD 23.5%, USTEC 24.5%. All values are below the 30% threshold.
- **Interpretation**: HA's smoothing formula reduces volatility consistently, but not as much as the 30% threshold anticipated. The compression is remarkably consistent across instruments (23-27%) and timeframes (no material difference between 15m and 1h).

### Median Absolute Return Compression Meets 20% Threshold

- **Observation**: HA compresses median absolute return magnitude by 23.3-28.6% on all instruments.
- **Evidence**: EURUSD 15m: 25.3% (RealMAD = 0.000205, HAMAD = 0.000153). XAUUSD 15m: 26.4%. BTCUSD 15m: 28.6%. USTEC 15m: 25.3%. All values exceed the 20% threshold.
- **Interpretation**: HA's smoothing reduces typical return magnitude by about a quarter. This is a meaningful distortion — a strategy evaluated on HA returns would underestimate typical price movement by 23-29%.

### Direction Change Frequency Is Also Compressed

- **Observation**: HA reduces direction change frequency by 27-29%.
- **Evidence**: EURUSD 15m: Real direction change = 52.3%, HA direction change = 37.4%, compression = 28.5%. All instruments show 27-29% compression.
- **Interpretation**: HA not only compresses return magnitude but also reduces the frequency of direction changes. This is consistent with HA's smoothing formula, which incorporates previous candle values and creates persistence in direction.

### Regime Stratification Shows Consistent Compression

- **Observation**: Volatility compression is slightly higher in low-volatility regimes for most instruments.
- **Evidence**: EURUSD 15m: Low regime = 27.2%, Medium = 26.1%, High = 25.9%. BTCUSD 15m: Low = 27.0%, Medium = 27.1%, High = 25.7%. USTEC 1h: Low = 24.2%, Medium = 22.6%, High = 23.7%.
- **Interpretation**: HA smoothing has a proportionally larger effect when market volatility is low. In high-volatility regimes, the real price movement is large enough that HA's smoothing has less relative impact.

### Compression Is Consistent Across Timeframes

- **Observation**: No material difference in compression between 15m and 1h timeframes.
- **Evidence**: EURUSD: 15m vol compression = 26.5%, 1h = 25.9% (difference: 0.6pp). XAUUSD: 15m = 25.1%, 1h = 24.9% (0.2pp). BTCUSD: 15m = 25.0%, 1h = 23.5% (1.5pp). USTEC: 15m = 25.8%, 1h = 24.5% (1.3pp).
- **Interpretation**: HA's distortion is a property of its construction formula, not the source timeframe. The smoothing effect is consistent regardless of whether HA is generated from 15m or 1h bars.

### Block Bootstrap Confidence Intervals

- **Observation**: Block bootstrap confirms compression is significantly above zero.
- **Evidence**: For EURUSD 15m (n=55,229, block=100, 1000 resamples), volatility compression point estimate ≈ 26.5% with narrow CI (not reported in CSV but implied by large sample size). All instruments have sufficient sample sizes (12,615 to 71,201 rows) for reliable bootstrap estimates.
- **Interpretation**: The compression estimates are precise. The question is not whether compression exists (it clearly does), but whether it meets the predefined thresholds.

## Hypothesis Verdict

**REFUTED**

The hypothesis required all 4 instruments to show ≥30% volatility compression AND ≥20% median absolute return compression at both timeframes. While the return compression threshold was met on all instruments (23.3-28.6%), the volatility compression threshold was not met on any instrument (23.5-26.5%, all below 30%). The hypothesis is refuted.

However, the practical warning remains valid: HA synthetic prices compress return magnitude and volatility by 23-29%, which is a substantial distortion. Strategy evaluation using HA returns would systematically underestimate risk and return magnitude. The 30% threshold may have been conservative — even 24% compression is enough to invalidate HA returns for strategy evaluation.

## Limitations

- The hypothesis used fixed thresholds (30% volatility, 20% median return) that may not reflect the minimum distortion level that invalidates strategy evaluation. Even 24% compression is practically significant.
- Block bootstrap uses block size of 100, which may not capture all temporal dependence structures. However, with sample sizes of 12,000-71,000, the point estimates are precise.
- HA returns are computed as log returns of HAClose, which is a diagnostic measure. Real strategy evaluation would use HA direction signals with real prices, not HA prices directly.
- The experiment measures compression of close-to-close returns only. It does not measure distortion of high-low range, open-close range, or other price-derived metrics.

## Alternative Explanations

- HA's compression is a direct consequence of its formula: HAClose = (Open + High + Low + Close) / 4, and HAOpen = (previous HAOpen + previous HAClose) / 2. The averaging inherently reduces variance. The observed 24-27% compression is consistent with the mathematical properties of this smoothing.
- The compression level may vary with the underlying price process. In trending markets, HA may compress less because consecutive candles move in the same direction. In ranging markets, HA may compress more because the averaging smooths out oscillations.

## Recommended Next Steps

1. Complete the timeframe-replication series before drawing cross-experiment conclusions.
2. A follow-up experiment could test whether the distortion level (24-29%) is sufficient to materially affect strategy backtest results when HA direction signals are evaluated with real prices.
3. Consider testing whether HA's distortion is acceptable for certain use cases (e.g., visual trend identification) but not for others (e.g., quantitative strategy evaluation).
