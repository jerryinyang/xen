# Results: Experiment EXP-001

## Summary

EXP-001 tested whether Line Break and Renko event bars have higher information density than 1-minute time bars, measured by ghost rate reduction, entropy-headroom capture, and absolute entropy gain. The hypothesis is **REFUTED**. While ghost-rate reduction is strong and universal across all instruments and event chart types, the entropy-based criteria are met on only one instrument (EURUSD). The success criteria required at least 3 instruments to meet all three thresholds; only EURUSD qualifies for both LineBreak3 and Renko.

## Detailed Findings

### Finding 1: Ghost-rate reduction is strong and universal

- **Observation**: All event chart types have dramatically lower ghost rates than time bars on every instrument. LineBreak3 and LineBreak5 achieve 0.0 ghost rate across all four instruments. Renko achieves near-zero rates (0.00005 to 0.0024). Time bars range from 0.0035 (BTCUSD) to 0.0899 (EURUSD).
- **Evidence**: `summary_metrics.csv` GhostRate column; `ghost_rate_by_instrument_charttype.png`; bootstrap mean ghost-rate reduction 0.034 (95% CI [0.009, 0.072]) for LineBreak3 vs Time, all four instruments positive.
- **Interpretation**: Event-based charts eliminate economically empty bars by construction. Line Break only emits confirmed price movements; Renko only emits bricks when price crosses a threshold. This is a structural property of the chart types, not an instrument-specific effect.

### Finding 2: Directional entropy is near-maximum for all chart types

- **Observation**: All chart types have directional entropy between 0.994 and 0.9999 bits (binary maximum = 1.0). The up/down direction distribution is nearly balanced regardless of chart type.
- **Evidence**: `summary_metrics.csv` DirectionalEntropy column; `entropy_heatmap.png`. Time bars: 0.994-0.9998; LineBreak3: 0.9986-0.9999; Renko: 0.9998-0.99998.
- **Interpretation**: Directional entropy is already near the binary ceiling for 1-minute time bars, leaving very little headroom for improvement. This makes the entropy-headroom and absolute entropy-gain thresholds extremely difficult to satisfy in practice.

### Finding 3: Entropy gains are instrument-specific, not universal

- **Observation**: Only EURUSD shows meaningful entropy increases for event charts. LineBreak3 on EURUSD: +0.0056 bits; Renko on EURUSD: +0.0057 bits. For all other instruments, entropy changes are negative (LineBreak3 on XAUUSD/BTCUSD/USTEC) or below the 0.005 threshold (Renko on XAUUSD/BTCUSD/USTEC: +0.0001 to +0.0005).
- **Evidence**: `threshold_evaluation.csv`; `distinct_source_sensitivity.csv`. Bootstrap CI for LineBreak3 entropy increase [-0.0003, 0.0042] includes zero; for Renko [0.0002, 0.0043] excludes zero but mean 0.0016 < 0.005 practical threshold.
- **Interpretation**: The entropy advantage of event charts is not a general property. EURUSD may have unique characteristics (tight tick size, high liquidity, specific volatility regime in the analysis period) that make its time bars relatively more directional-biased, leaving more headroom for event charts to exploit.

### Finding 4: Heiken Ashi is a smoothed mirror of time bars

- **Observation**: Heiken Ashi produces exactly the same number of bars (872,242 for EURUSD), same ghost rate, and same movement metrics as time bars. Its directional entropy is slightly higher (0.9999 vs 0.9942 for EURUSD) because the HA averaging smooths price fluctuations, creating more consistent directional signals.
- **Evidence**: `summary_metrics.csv` HeikenAshi rows match Time rows on AnalysisBars, BarsPerDay, GhostRate, MedianAbsMovement, and CV values.
- **Interpretation**: Heiken Ashi is a 1:1 transformation of time bars. It does not compress or expand the bar count. Its value lies in visual smoothing, not information density. This was expected per the scope ("not expected to reduce bar count").

### Finding 5: Bar compression is substantial but not equivalent to information concentration

- **Observation**: LineBreak3 produces ~25% as many bars as time bars (248 vs 1016 bars/day for EURUSD). Renko produces ~30%. This compression is real, but most of the "saved" bars are ghosts that time bars spend on empty movement. The remaining non-ghost time bars already carry near-maximum directional entropy.
- **Evidence**: `summary_metrics.csv` BarsPerDay column; `bar_density_timeline_eurusd.png`.
- **Interpretation**: Event charts compress time, not information. They skip over periods of low activity and emit bars only when price moves meaningfully. This is valuable for chart readability and potentially for signal timing, but it does not increase the information content per bar beyond what the non-ghost time bars already provide.

## Hypothesis Verdict

**REFUTED**

The hypothesis required Line Break level 3 or Renko ATR-14 to meet all three thresholds (ghost rate >= 25% lower, >= 50% entropy headroom capture, >= 0.005 bits absolute entropy gain) on at least 3 instruments. Results:

| Chart Type | Instruments Meeting All Three Thresholds |
|------------|----------------------------------------|
| LineBreak3 | 1 (EURUSD only) |
| Renko | 1 (EURUSD only) |

The bootstrap descriptive summaries support this: LineBreak3 entropy CI includes zero; Renko entropy CI excludes zero but the mean effect (0.0016 bits) is below the practical threshold (0.005 bits). Ghost-rate reduction is consistently positive but is a structural property of event charts, not an information-density advantage per se.

The "evidence against" criterion (fewer than 2 instruments meet thresholds for every primary event type) is met: zero instruments meet thresholds for both LineBreak3 and Renko simultaneously.

## Limitations

- **Four instruments, one analysis period**: The instrument sample is too small for strong generalisation. Results may differ in other market regimes or with different instrument selections.
- **Entropy near ceiling**: Directional entropy is already 0.994+ for time bars, leaving minimal headroom. A different information-density metric (e.g., mutual information with future returns, or multi-state entropy beyond binary direction) might reveal different patterns.
- **Bootstrap is descriptive, not inferential**: With four instrument-level units, bootstrap resampling provides uncertainty estimates but not strong statistical proof.
- **1-minute source bars only**: Higher-timeframe time bars may have different ghost rates and entropy profiles, potentially changing the comparison. This is out of scope for EXP-001 but relevant for Phase 2.
- **Ghost-rate definition**: The min_tick proxy is instrument-specific and based on observed minimum non-zero close differences. A different ghost definition could shift absolute rates, though the relative ordering (event < time) is robust.

## Alternative Explanations

- The EURUSD-specific entropy gain may reflect the particular market regime during the analysis period (2023-2025) rather than a structural property of the chart types. EURUSD experienced distinct volatility regimes during this period that may have made its 1-minute bars more directionally biased.
- The near-zero ghost rates for Line Break are a definitional consequence: Line Break bars only form when price confirms a movement. This guarantees low ghost rates but does not imply higher information content per bar.

## Recommended Next Steps

1. **EXP-002 (Volatility & Trend Regime Representation)**: Already planned. Test whether event charts better represent volatility regimes and trend structure, using metrics beyond directional entropy.
2. **Multi-state entropy**: Replace binary direction entropy with a 3+ state classification (e.g., strong up, weak up, neutral, weak down, strong down) to create more headroom for differentiation.
3. **Higher-timeframe baseline**: Compare event charts against 5-minute or 15-minute time bars, which may have lower ghost rates and different entropy profiles than 1-minute bars.
4. **Instrument-specific analysis**: Investigate why EURUSD shows entropy gains while other instruments do not. This may inform instrument specialization for Phase 2.
