# Results: Experiment EXP-002-TF

## Summary

The EXP-002 volatility-regime boundary-cost hypothesis was **refuted** when retested on 15-minute and 1-hour source bars. Both Line Break and Renko exceeded the 0.05 hybrid-rate bound on all 4 instruments at both timeframes (hybrid rates: 8.9-22.3%). Median transition lag was at or below the 2-bar bound for most combinations but exceeded it for BTCUSD 1h LineBreak (5.0 bars). The time-bar baseline has zero hybrid rate and zero lag by construction, so event charts can only match or exceed these bounds — and they consistently exceed them.

## Detailed Findings

### Hybrid Rates Exceed 0.05 Bound Universally

- **Observation**: All event chart combinations have hybrid rates well above the 0.05 threshold.
- **Evidence**: LineBreak hybrid rates: 8.9-12.7% across all instruments/timeframes. Renko hybrid rates: 13.9-22.3%. Bootstrap 95% CI for 15m LineBreak absolute hybrid excess: [0.091, 0.100]. For 1h Renko: [0.170, 0.212]. All CIs are far above 0.05.
- **Interpretation**: Event charts inherently straddle regime boundaries because their bars are not aligned to time-bar regime transitions. A LineBreak or Renko bar that spans a regime change will have a "hybrid" character — part of its price action occurred under one regime and part under another. This is a structural property of event charts, not a parameter-specific issue.

### Median Transition Lag Is Generally Within Bounds

- **Observation**: Median lag is ≤2 source bars for most combinations, with one exception.
- **Evidence**: 15m timeframe: LineBreak median lag = 2.0 bars (all instruments), Renko median lag = 1.0-2.0 bars. 1h timeframe: LineBreak median lag = 0.0-5.0 bars (BTCUSD 1h LB = 5.0), Renko median lag = 1.0 bars.
- **Interpretation**: Event charts confirm regime transitions within 1-2 source bars on median, which is reasonable. The BTCUSD 1h LineBreak outlier (5.0 bars) reflects crypto's higher volatility causing longer periods without a confirming LineBreak direction change.

### Missed Transitions Are Low but Non-Zero

- **Observation**: Most regime transitions are matched by event charts, but 0-3 transitions are missed per combination.
- **Evidence**: EURUSD 15m LineBreak: 3 missed out of 904 transitions (0.3%). BTCUSD 1h Renko: 0 missed out of 326. USTEC 1h LineBreak: 3 missed out of 269.
- **Interpretation**: Event charts capture the vast majority of regime transitions. Missed transitions are rare and likely correspond to brief regime changes that revert before an event bar confirms.

### Time-Bar Baseline Is Zero by Construction

- **Observation**: Time bars define the regime timeline, so their hybrid rate and lag are both 0.0.
- **Evidence**: All Time and HeikenAshi rows show HybridRate = 0.0, MedianLagBars = 0.0.
- **Interpretation**: This is the correct baseline. Event charts are being compared against the timeline they are measured against, so they can only match (if perfectly aligned) or exceed (if misaligned) the baseline.

### Heiken Ashi Matches Time-Bar Baseline

- **Observation**: HA has identical hybrid rate and lag as time bars.
- **Evidence**: HA rows mirror Time rows exactly: HybridRate = 0.0, MedianLagBars = 0.0.
- **Interpretation**: HA is a 1:1 transformation of time bars with the same timestamps, so it inherits the regime timeline perfectly.

## Hypothesis Verdict

**REFUTED**

The hypothesis required Line Break or Renko to have hybrid rate ≤0.05 AND median lag ≤2 source bars on at least 3 of 4 instruments. While median lag was within bounds for most combinations, hybrid rates exceeded 0.05 universally (8.9-22.3%). SupportCount = 0/4 for all chart type and timeframe combinations. WithinBounds = False for every event chart combination.

The EXP-002 conclusion replicates in its refuted direction: event charts incur measurable boundary cost relative to same-timeframe time-bar regime timelines. This cost is structural — event charts emit bars at irregular intervals that do not align with time-based regime boundaries.

## Limitations

- Bootstrap operates on n=4 instrument-level values. CIs are descriptive only.
- The hybrid rate metric counts any interval spanning multiple regimes as "hybrid," regardless of how much of the interval falls in each regime. A bar that crosses a boundary by one minute is treated the same as one that spans the entire interval.
- Regime labels are derived from rolling 20-bar volatility on the aggregated timeframe, which may lag actual regime changes.
- Max lag values are extremely large for some combinations (e.g., USTEC 15m LineBreak: 3,376 bars), reflecting rare events where the chart type took very long to confirm a transition. Median is robust to these outliers.

## Alternative Explanations

- The hybrid rate could be reduced by using event-chart-specific regime definitions (e.g., regimes based on event-bar volatility rather than time-bar volatility). However, this would change the experiment's question from "how well do event charts represent time-bar regimes" to "what regimes do event charts naturally produce."
- The boundary cost is an inherent trade-off: event charts reduce bar count (information density benefit) but lose temporal alignment with time-based regimes (boundary cost). Both effects are real and should be weighed together.

## Recommended Next Steps

1. Complete the timeframe-replication series before drawing cross-experiment conclusions.
2. A follow-up experiment could quantify whether the boundary cost is offset by the information-density benefits found in other experiments (e.g., fewer bars to process, lower ghost rates).
3. Consider testing whether event-chart-specific regime definitions reduce boundary cost while preserving regime discrimination.
