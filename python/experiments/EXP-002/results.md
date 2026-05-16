# Results: Experiment EXP-002

## Summary

EXP-002 evaluated whether Line Break level 3 and Renko ATR-14 preserve volatility-regime representation relative to the 1-minute time-bar lower bound, measured by hybrid rate (fraction of bars spanning regime boundaries) and median confirmed transition lag. The hypothesis is **REFUTED**: both event chart types exceed the absolute boundary-cost thresholds on all 4 instruments. Line Break hybrid rates range from 6.4% to 8.6% (bound: 5.0%), and Renko hybrid rates range from 9.2% to 11.9%. Median transition lag is 0.0 for all chart types, but event charts show substantial tail lag (P95 up to 14 bars, max up to 660 bars) and miss 24–34% of regime transitions entirely. Paired bootstrap confirms event charts are consistently worse than time bars on hybrid rate (all CIs exclude zero, 0/4 instruments positive).

## Detailed Findings

### Finding 1: Event charts incur substantial hybrid rate cost versus time bars

- **Observation**: Both Line Break and Renko have non-zero hybrid rates on all instruments, meaning a significant fraction of their bars span multiple volatility regimes. Time bars have zero hybrid rate by construction.
- **Evidence**:
  - LineBreak3 hybrid rates: EURUSD 0.086, XAUUSD 0.083, BTCUSD 0.077, USTEC 0.064 (all > 0.05 bound).
  - Renko hybrid rates: EURUSD 0.104, XAUUSD 0.119, BTCUSD 0.115, USTEC 0.092 (all > 0.05 bound).
  - Bootstrap HybridRateReduction: LB3 mean = -0.078, CI [-0.085, -0.069]; Renko mean = -0.108, CI [-0.117, -0.098]. Both CIs exclude zero; 0/4 instruments show improvement.
  - See `plots/hybrid_rate_by_instrument_charttype.png`, `results/bootstrap_results.csv`.
- **Interpretation**: Event chart aggregation necessarily spans regime boundaries. Line Break's 3-level reversal requirement and Renko's ATR-scaled brick size both produce bars that cover multiple time-bar intervals, some of which cross tercile-defined regime boundaries. This is a structural property of event aggregation, not a parameter tuning issue. Renko incurs higher hybrid rate than Line Break on all instruments, consistent with Renko producing slightly more bars (less aggregation) but with less regime-aware boundaries.

### Finding 2: Median transition lag is zero, but tail lag and missed transitions are substantial

- **Observation**: The median confirmed transition lag is 0.0 for all chart types, meaning most regime transitions are confirmed by a chart event at the transition timestamp itself. However, the tail of the lag distribution is heavy, and a significant fraction of transitions are never confirmed.
- **Evidence**:
  - Median lag: 0.0 for all chart types on all instruments.
  - P95 lag: LineBreak3 = 12–14 bars; Renko = 7 bars (consistent across instruments).
  - Max lag: LineBreak3 = 158–660 bars; Renko = 24–40 bars.
  - Missed transitions: LineBreak3 misses 10,741–18,489 (25–34% of transitions); Renko misses 7,691–13,031 (17–24%).
  - See `results/summary_metrics.csv`, `plots/lag_boxplot_by_charttype.png`.
- **Interpretation**: The zero median lag is encouraging — when event charts do confirm a regime change, they often do so immediately. But the heavy tail (especially for Line Break, with max lag up to 660 bars ≈ 11 hours on 1-minute data) and the substantial miss rate mean event charts cannot be relied upon for timely regime detection. Renko performs better than Line Break on both miss rate and tail lag, likely because Renko's ATR-scaled bricks react more continuously to price movement than Line Break's discrete 3-level reversal logic.

### Finding 3: Heiken Ashi mirrors time bars exactly

- **Observation**: Heiken Ashi has zero hybrid rate and zero transition lag on all instruments, identical to time bars.
- **Evidence**: All HA metrics match Time metrics exactly (872,222 bars for EURUSD, 41,673 transitions, 0 missed).
- **Interpretation**: This is expected — Heiken Ashi is a 1:1 transformation of time bars, so every HA candle maps to exactly one time bar with the same timestamp and regime label. HA provides no regime representation advantage or cost relative to time bars. Its value lies in visual smoothing, not regime fidelity.

### Finding 4: No instrument meets the success criteria for either event chart type

- **Observation**: The success criteria required hybrid rate ≤ 0.05 AND median lag ≤ 2.0 on at least 3 instruments. Neither Line Break nor Renko meets the hybrid rate bound on any instrument.
- **Evidence**:
  - LineBreak3: exceeds hybrid rate bound on 4/4 instruments; median lag ≤ 2.0 on 4/4 (but this is moot given hybrid rate failure).
  - Renko: exceeds hybrid rate bound on 4/4 instruments; median lag ≤ 2.0 on 4/4.
  - Verdict: REFUTED (see `results/hypothesis_verdict.csv`).
- **Interpretation**: The boundary cost of event chart aggregation is too large to preserve useful regime representation under the defined thresholds. This does not mean event charts are useless for regime analysis — it means their regime labels should not be assumed to align cleanly with time-bar-defined regimes.

## Hypothesis Verdict

**REFUTED**

Line Break level 3 and Renko ATR-14 both exceed the absolute hybrid-rate boundary-cost bound (0.05) on all 4 instruments. The median transition lag criterion (≤ 2.0 bars) is met by both, but this is driven by the zero-median phenomenon and does not compensate for the hybrid rate failure. Paired bootstrap confirms the hybrid rate disadvantage is consistent and statistically distinguishable from zero across instruments.

## Limitations

1. **Regime definition dependency**: Regimes are defined on time bars (rolling volatility terciles). Event charts are evaluated against this external definition, not their own internal regime structure. A different regime definition based on event chart properties might yield different results, but that would be a different experiment.
2. **Bootstrap at N=4**: The bootstrap resamples only 4 instrument-level differences. CIs are descriptive summaries, not population inference. The small N limits the granularity of the bootstrap distribution.
3. **Single parameter setting**: Only Line Break level 3 and Renko ATR-14 were tested. Different parameters might produce different boundary costs, but parameter search is outside Phase 1 characterisation scope.
4. **Tercile-based regimes**: Volatility terciles are empirical bins, not stable market states. The boundaries are somewhat arbitrary and may not correspond to economically meaningful regime shifts.

## Alternative Explanations

1. **Event charts aggregate by price movement, not volatility**: Line Break and Renko are designed to filter noise by requiring minimum price movement. Volatility regime boundaries (based on return dispersion) are a different dimension than price direction changes. The hybrid rate cost may reflect a fundamental mismatch between price-aggregation and volatility-classification, not a deficiency of event charts per se.
2. **The time-bar baseline is trivially optimal**: Since regimes are defined on time bars, time bars have zero boundary cost by construction. Any chart type that aggregates multiple time bars will necessarily incur some boundary cost. The question is whether the cost is "small enough" — and the predefined thresholds (5% hybrid rate, 2-bar median lag) appear too strict for event charts to meet.

## Recommended Next Steps

1. **EXP-007 (proposed)**: Evaluate whether event charts' own internal structure (e.g., Line Break reversal frequency, Renko brick size changes) can serve as a regime detection method independent of time-bar-defined regimes. This tests whether event charts are better at defining their own regimes than matching time-bar regimes.
2. **Cross-experiment synthesis**: Combine EXP-002 (regime representation), EXP-003 (noise filtering), and EXP-004 (structure capture speed) findings to assess whether event charts' value lies in signal denoising and precision rather than regime fidelity.
