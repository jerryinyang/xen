# Results: Experiment EXP-003-TF

## Summary

The EXP-003 noise-robustness hypothesis was **refuted** when retested on 15-minute and 1-hour source bars. Under 20% noise perturbation, neither Line Break nor Renko achieved ≥25% lower relative drift than same-timeframe time bars in at least two of three metrics on at least 3 instruments. The maximum instrument count for any metric was 2 (DirectionDrift for both LB and Renko at 15m). Heiken Ashi showed the lowest drift across all metrics, confirming its smoothing effect, but this uses HAClose returns as a non-tradable distortion diagnostic per synthetic price discipline rules.

## Detailed Findings

### Direction Drift: Event Charts Marginally Better at 15m

- **Observation**: At 20% noise on 15m bars, Line Break and Renko show lower direction drift than time bars on 2 of 4 instruments.
- **Evidence**: EURUSD 15m: LB drift = 0.0016 vs Time = 0.0031 (48% lower). USTEC 15m: LB drift = 0.0014 vs Time = 0.0035 (59% lower). XAUUSD 15m: LB drift = 0.0015 vs Time = 0.0009 (LB worse). BTCUSD 15m: LB drift = 0.0032 vs Time = 0.0007 (LB worse). InstrumentsWithAtLeast25PctLowerDrift = 2 for LB DirectionDrift at 15m.
- **Interpretation**: At 15m, event charts show direction robustness on 2 instruments but not 3. The hypothesis requires ≥3 instruments, so this does not meet the threshold.

### Return Variance Drift: Mixed Results

- **Observation**: Return variance drift at 20% noise shows no consistent advantage for event charts.
- **Evidence**: 15m LineBreak: only 1 instrument (EURUSD: 0.129 vs 0.110 — actually worse; XAUUSD: 0.121 vs 0.102 — worse). 15m Renko: 2 instruments (EURUSD: 0.075 vs 0.110 — 32% lower; XAUUSD: 0.070 vs 0.102 — 31% lower). 1h timeframe: only 1 instrument for both LB and Renko.
- **Interpretation**: Renko shows some return variance robustness at 15m (2 instruments), but not enough to meet the ≥3 instrument threshold.

### Complexity Drift: Event Charts Consistently Worse

- **Observation**: LZ76 complexity drift is higher for event charts than time bars on all instruments.
- **Evidence**: InstrumentsWithAtLeast25PctLowerDrift = 0 for all chart type and timeframe combinations. LB complexity drift at 15m ranges from 0.031 to 0.045 vs Time at 0.001 to 0.003 — 10-30x higher.
- **Interpretation**: Event charts are more sensitive to source-bar noise in terms of sequence complexity. This is expected: perturbing source bars changes the timing and occurrence of event-bar boundaries, which alters the direction sequence structure more than it affects time-bar direction sequences.

### Heiken Ashi: Lowest Drift Across All Metrics

- **Observation**: HA consistently shows the lowest drift across all three metrics.
- **Evidence**: At 20% noise, 15m HA DirectionDrift: 0.0007-0.0010 (vs Time: 0.0007-0.0035). ReturnVarianceDrift: 0.015-0.025 (vs Time: 0.075-0.137). ComplexityDrift: 0.001-0.005 (vs Time: 0.001-0.003).
- **Interpretation**: HA's smoothing formula absorbs noise effectively. However, HA return variance uses HAClose (synthetic prices) as a distortion diagnostic, not as a tradable return metric. The low drift reflects HA's construction, not necessarily robustness to real-price noise.

### Perturbation Quality: No Invalid Bars

- **Observation**: OHLC repair is fully effective — zero invalid bars across all combinations.
- **Evidence**: InvalidRows = 0 for all 32 instrument-timeframe-noise combinations. InvalidPct = 0.0.
- **Interpretation**: The perturbation and repair process produces valid OHLC bars in all cases, well below the 5% invalidity threshold for inconclusive results.

### Noise Level Progression

- **Observation**: Drift generally increases monotonically with noise level (0% → 10% → 20% → 30%).
- **Evidence**: EURUSD 15m Time DirectionDrift: 0.0 → 0.0014 → 0.0031 → 0.0030. Renko ReturnVarianceDrift: 0.0 → 0.032 → 0.075 → 0.133.
- **Interpretation**: The perturbation produces a graded stress response, confirming the noise model is working as intended.

## Hypothesis Verdict

**REFUTED**

The hypothesis required Line Break or Renko to have ≥25% lower relative drift than time bars in at least 2 of 3 metrics on at least 3 instruments at the 20% noise level. The maximum count achieved was 2 instruments (DirectionDrift for LB and Renko at 15m), which is below the ≥3 threshold. No chart type achieved the threshold for ComplexityDrift on any instrument. The EXP-003 noise-robustness finding does not replicate at higher timeframes.

## Limitations

- LZ76 complexity is log-normalized but may still be confounded by row count differences between chart types. ComplexityDrift comparisons are most reliable within the same chart type (perturbed vs baseline).
- The perturbation model adds noise to close prices of aggregated time bars, which is an artificial stressor. Real market noise may have different characteristics.
- HA return variance uses HAClose (synthetic prices), which is appropriate as a distortion diagnostic but not comparable to real-price variance metrics.
- Deterministic perturbation seeds are instrument-timeframe specific, which is correct for reproducibility but means results are specific to these perturbation instances.

## Alternative Explanations

- Event charts may be more sensitive to noise because their bar boundaries are determined by price movement thresholds. Perturbing close prices changes which bars form and when, amplifying the effect on direction sequences.
- The 20% noise level may be too high for higher-timeframe bars, which already aggregate away much of the 1-minute noise. The relative impact of perturbation may differ across timeframes.
- HA's superior robustness is expected given its smoothing formula — each HA candle incorporates the previous candle's values, creating a low-pass filter effect.

## Recommended Next Steps

1. Complete the timeframe-replication series before drawing cross-experiment conclusions.
2. A follow-up experiment could test noise robustness using realistic noise models (e.g., bid-ask spread simulation, volume-weighted perturbation) rather than deterministic close-price perturbation.
3. Consider testing whether event charts are more robust to noise at the 1-minute timeframe (original EXP-003) but less robust at higher timeframes, which would suggest a timeframe-dependent robustness profile.
