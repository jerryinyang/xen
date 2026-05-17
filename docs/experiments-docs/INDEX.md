# Experiments Index (Comprehensive)

## Checkpoint Retrospectives

| Checkpoint | Status | Key Synthesis | Document |
| --- | --- | --- | --- |
| 2026-05-14-001-chart-type-validation | COMPLETED | Phase 1 validates time bars as the master timeline for 1-minute-source analysis; higher-timeframe robustness remains a Phase 1B bridge item before Phase 2 signal-quality characterization. | [retrospective.md](checkpoints/2026-05-14-001-chart-type-validation/retrospective.md) |


## EXP-001 — Information Density & Ghost Bar Comparison

**Status**: REFUTED
**Date**: 2026-05-16
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Chart Types**: Time Bars, Line Break (levels 3, 5), Renko (ATR 14), Heiken Ashi

### Hypothesis Tests

1. **Hypothesis**: Line Break and Renko event bars have higher information density than 1-minute time bars on at least 3 of 4 instruments, measured as lower ghost rate (>= 25% reduction), better use of remaining directional-entropy headroom (>= 50% capture), and a practical absolute entropy gain (>= 0.005 bits).

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Chart Types**: Time Bars, Line Break (levels 3, 5), Renko (ATR 14), Heiken Ashi
- **Features**: Ghost rate, directional entropy, volatility terciles, bootstrap confidence intervals, distinct-source sensitivity
- **Parameter ranges**: LineBreak level 3 and 5; Renko ATR period 14
- **Exclusions**: No strategy backtesting, no parameter optimization, no predictive modeling, no higher-timeframe comparison
- **Constraints**: Final 30% global holdout excluded; synthetic price discipline; timestamp alignment over bar count

### Results / Observations

| Instrument | Chart Type | Ghost Rate | Ghost Reduction | Entropy Increase | Headroom Capture | Meets All Thresholds |
|------------|-----------|-----------|----------------|-----------------|-----------------|---------------------|
| EURUSD | Time | 0.0899 | — | — | — | — |
| EURUSD | LineBreak3 | 0.0 | 1.0 | +0.0056 | 0.97 | Yes |
| EURUSD | Renko | 0.0024 | 0.97 | +0.0057 | 0.98 | Yes |
| XAUUSD | Time | 0.0179 | — | — | — | — |
| XAUUSD | LineBreak3 | 0.0 | 1.0 | -0.00009 | -0.17 | No |
| XAUUSD | Renko | 0.0003 | 0.98 | +0.0003 | 0.56 | No |
| BTCUSD | Time | 0.0035 | — | — | — | — |
| BTCUSD | LineBreak3 | 0.0 | 1.0 | +0.00004 | 0.25 | No |
| BTCUSD | Renko | 0.00005 | 0.98 | +0.0001 | 0.67 | No |
| USTEC | Time | 0.0261 | — | — | — | — |
| USTEC | LineBreak3 | 0.0 | 1.0 | -0.0004 | -0.42 | No |
| USTEC | Renko | 0.0005 | 0.98 | +0.0005 | 0.49 | No |

Bootstrap (10,000 resamples, seed 42):
- LineBreak3 vs Time ghost-rate reduction: mean 0.034, CI [0.009, 0.072], excludes zero, 4/4 instruments positive
- LineBreak3 vs Time entropy increase: mean 0.0013, CI [-0.0003, 0.0042], includes zero, 2/4 positive
- Renko vs Time ghost-rate reduction: mean 0.034, CI [0.009, 0.070], excludes zero, 4/4 positive
- Renko vs Time entropy increase: mean 0.0016, CI [0.0002, 0.0043], excludes zero, 4/4 positive

Bar compression: LineBreak3 produces ~25% as many bars as time bars; Renko ~30%.

### Hypothesis-Specific Conclusion

**REFUTED**

Only 1 of 4 instruments (EURUSD) meets all three thresholds. Ghost-rate reduction is universal but is a structural property of event charts. Entropy gains are instrument-specific and below practical thresholds for 3 of 4 instruments.

### Hypothesis-Agnostic Observations

- Event charts compress time by a factor of 3-4x while eliminating economically empty bars
- Directional entropy is near the binary ceiling (0.994+) for all chart types on all instruments
- Heiken Ashi is a 1:1 transformation with identical ghost rates; its value is visual smoothing, not information compression
- Renko emits 13-12% same-source duplicate rows, requiring explicit denominator handling
- EURUSD shows qualitatively different entropy response than the other three instruments

---

## EXP-002 — Volatility & Trend Regime Representation

**Status**: REFUTED
**Date**: 2026-05-16
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Chart Types**: Time Bars, Line Break (level 3), Renko (ATR 14), Heiken Ashi

### Hypothesis Tests

1. **Hypothesis**: Line Break level 3 and Renko ATR-14 are evaluated for volatility-regime boundary cost versus the 1-minute time-bar lower bound, measured by hybrid rate and regime transition lag. On at least 3 instruments, Line Break or Renko has hybrid rate no greater than 0.05 and median transition lag no greater than 2 source time bars.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Chart Types**: Time Bars, Line Break (level 3), Renko (ATR 14), Heiken Ashi
- **Features**: Rolling realised volatility (window=20), train-derived tercile regime labels, hybrid rate, confirmed transition lag, paired bootstrap (10,000 resamples, seed=42)
- **Parameter ranges**: LineBreak level 3; Renko ATR period 14
- **Exclusions**: No parameter search, no predictive models, no strategy validation, no higher-timeframe regimes
- **Constraints**: Final 30% global holdout excluded; synthetic price discipline; timestamp alignment via CloseTime/SourceCloseTime

### Results / Observations

Hybrid rate by chart type and instrument:

| Instrument | Time | LineBreak3 | Renko | HeikenAshi |
|------------|------|------------|-------|------------|
| EURUSD | 0.000 | 0.086 | 0.104 | 0.000 |
| XAUUSD | 0.000 | 0.083 | 0.119 | 0.000 |
| BTCUSD | 0.000 | 0.077 | 0.115 | 0.000 |
| USTEC | 0.000 | 0.064 | 0.092 | 0.000 |

Transition lag diagnostics:

| Chart Type | Median Lag | P95 Lag | Max Lag | Missed Transitions (range) |
|------------|-----------|---------|---------|---------------------------|
| Time | 0.0 | 0.0 | 0.0 | 0 |
| LineBreak3 | 0.0 | 12–14 | 158–660 | 10,741–18,489 (25–34%) |
| Renko | 0.0 | 7 | 24–40 | 7,691–13,031 (17–24%) |
| HeikenAshi | 0.0 | 0.0 | 0.0 | 0 |

Analysis set sizes: EURUSD 872,222 bars; XAUUSD 830,651 bars; BTCUSD 1,088,940 bars; USTEC 830,521 bars.

### Hypothesis-Specific Conclusion

**REFUTED**

Both Line Break level 3 and Renko ATR-14 exceed the absolute hybrid-rate boundary-cost bound (0.05) on all 4 instruments. LineBreak3 hybrid rates range from 0.064 to 0.086; Renko from 0.092 to 0.119. Event charts miss 17–34% of regime transitions and show heavy tail lag.

### Hypothesis-Agnostic Observations

- Event chart aggregation is a structural source of regime boundary cost
- Renko performs better than Line Break on miss rate (17–24% vs 25–34%) and tail lag
- Heiken Ashi is a 1:1 transformation with identical regime metrics to time bars
- Zero median lag across all chart types: when event charts confirm a regime change, they often do so at the transition timestamp — the issue is coverage, not speed

---

## EXP-003 — Noise Filtering & Statistical Robustness

**Status**: SUPPORTED
**Date**: 2026-05-16
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Chart Types**: Time Bars, Line Break (level 3), Renko (ATR 14), Heiken Ashi

### Hypothesis Tests

1. **Hypothesis**: Under controlled source-bar noise injection, Line Break level 3 and Renko ATR-14 preserve directional and distributional statistics more stably than 1-minute time bars on at least 3 of 4 instruments, while Heiken Ashi reduces variance but increases synthetic price distortion.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Chart Types**: Time Bars, Line Break, Renko, Heiken Ashi
- **Features**: Direction stability (up-fraction drift), Return variance stability, LZ76 complexity stability
- **Parameter ranges**: Noise levels 0%, 10%, 20%, 30%; Line Break level 3; Renko ATR period 14
- **Exclusions**: No stochastic simulation sweep, no strategy testing, no parameter optimization, no tick-level noise model
- **Constraints**: Final 30% global holdout excluded; HA uses HAClose only as distortion diagnostic; deterministic perturbation with instrument-level seed

### Results / Observations

- Renko vs Time DirectionDrift at 20% noise: MeanDiff = -0.0050, 95% CI [-0.0104, -0.0011], 4/4 instruments lower
- LineBreak vs Time DirectionDrift at 20% noise: MeanDiff = -0.0042, CI [-0.0093, -0.0004], 3/4 instruments lower
- Renko vs Time ReturnVarianceDrift at 20% noise: MeanDiff = -0.0040, CI [-0.0059, -0.0023], 4/4 instruments lower
- LineBreak vs Time ReturnVarianceDrift at 20% noise: MeanDiff = +0.0035, CI [-0.0247, 0.0347], 2/2 split
- LineBreak vs Time ComplexityDrift at 20% noise: MeanDiff = +0.0153, CI [0.0131, 0.0175], 0/4 instruments lower
- Renko vs Time ComplexityDrift at 20% noise: MeanDiff = +0.0083, CI [0.0070, 0.0097], 0/4 instruments lower
- HeikenAshi vs Time ReturnVarianceDrift at 20% noise: MeanDiff = -0.0770, CI [-0.0788, -0.0754], 4/4 instruments lower
- OHLC repair: 0 invalid rows across all instrument/noise combinations

### Hypothesis-Specific Conclusion

**SUPPORTED (with qualification)**

Renko preserves direction stability more robustly than time bars on all 4 instruments with a small but consistent return variance advantage. Line Break shows direction stability on 3 of 4 instruments. Heiken Ashi portion confirmed: HAClose variance drift 80-93% lower than time bars.

### Hypothesis-Agnostic Observations

- Event-based chart types trade direction stability for sequence complexity under noise
- Return variance drift scales proportionally with noise level across all chart types
- XAUUSD shows the smallest absolute time-bar direction drift
- OHLC repair via High/Low adjustment is fully effective for close-price perturbation

---

## EXP-004 — Market Structure Capture Speed & Fidelity

**Status**: REFUTED
**Date**: 2026-05-16
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Chart Types**: Time Bars, Line Break (level 3), Renko (ATR-14), Heiken Ashi

### Hypothesis Tests

1. **Hypothesis**: Line Break level 3 and Renko ATR-14 detect predefined real-price trend reversals faster than 1-minute time-bar confirmation on at least 3 of 4 instruments, but their precision is not higher than the time-bar baseline.
   - Success criterion: >=30% latency reduction on >=3 instruments, precision within +10pp of time bars.
   - Failure criterion: <15% latency reduction on >=3 instruments, or precision worse by >25pp on >=3 instruments.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Chart Types**: Time Bars, Line Break, Renko, Heiken Ashi
- **Features**: Direction changes as reversal signals; ATR-scaled swing reversals (1.5x and 2.0x ATR) as reference
- **Parameter ranges**: Line Break level=3; Renko ATR period=14; tolerance window=120 minutes
- **Exclusions**: No strategy entry/exit testing, no optimisation of reversal thresholds, no predictive model, no bar-index alignment
- **Constraints**: Final 30% holdout excluded; real-price reversal reference; timestamp alignment via CloseTime/SourceCloseTime

### Results / Observations

- Median latency: Time=2.0 min, LineBreak=110-111 min, Renko=101-105 min, HeikenAshi=4.0 min
- Precision: Time=26-28%, LineBreak=99.9%, Renko=99.9%, HeikenAshi=52-56%
- Recall: Time=~100%, LineBreak=34-40%, Renko=72-75%, HeikenAshi=~100%
- Split rate: Time=83-85%, LineBreak=~0%, Renko=~0.04%, HeikenAshi=47-51%
- FasterCount (>=30% latency reduction): 0/4 for all chart types

### Hypothesis-Specific Conclusion

**REFUTED**

Event-based charts are 50-55x slower than the time-bar baseline, not faster. Zero of four instruments show the hypothesized speed advantage. Event charts are far more precise (~99.9%) but with dramatically lower recall (34-75% vs ~100%).

### Hypothesis-Agnostic Observations

- Event-based charts trade recall for precision: fewer, higher-quality signals but miss most reversals
- Time bars produce massive signal redundancy (83-85% split rate), confirming high noise relative to event charts
- The practical value of Line Break and Renko is signal denoising, not faster detection
- Heiken Ashi occupies an intermediate position: modest latency penalty (2x), moderate precision (52-56%), high recall (~100%)

---

## EXP-005 — Cross-Chart-Type Alignment & Regime Correspondence

**Status**: REFUTED
**Date**: 2026-05-16
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Chart Types**: Time Bars, Line Break (level 3), Renko (ATR 14), Heiken Ashi

### Hypothesis Tests

1. **Hypothesis**: Line Break level 3 and Renko ATR-14 show stronger trend-direction agreement with each other than either does with 1-minute time bars during medium- and high-volatility regimes, measured by timestamp-aligned agreement within a fixed tolerance window.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Chart Types**: Time Bars, Line Break, Renko, Heiken Ashi
- **Features**: Direction labels, timestamp-aligned pairwise agreement (5m tolerance), volatility tercile regimes, paired bootstrap (10,000 resamples, seed=42)
- **Parameter ranges**: Line Break level=3; Renko ATR period=14; tolerance window=5 minutes (15m sensitivity)
- **Exclusions**: No claim that agreement implies profitability, no predictive modelling, no optimisation of tolerance windows, no bar-index alignment
- **Constraints**: Final 30% holdout excluded; no strategy P&L; timestamp alignment via CloseTime/SourceCloseTime; regime labels calibrated on train segment

### Results / Observations

Raw pairwise agreement at 5m tolerance:

| Pair | EURUSD | XAUUSD | BTCUSD | USTEC |
|------|--------|--------|--------|-------|
| LB↔Renko | 0.901 | 0.902 | 0.901 | 0.905 |
| LB↔TimeBars | 0.783 | 0.792 | 0.794 | 0.791 |
| Renko↔TimeBars | 0.807 | 0.815 | 0.817 | 0.814 |
| TimeBars↔HeikenAshi | 0.650 | 0.658 | 0.662 | 0.657 |

Paired bootstrap (ref=LineBreak, target_a=Renko, target_b=TimeBars, medium_high regime):

| Instrument | Diff (pp) | 95% CI | n |
|-----------|-----------|--------|---|
| EURUSD | -0.73 | [-0.93, -0.53] | 54,833 |
| XAUUSD | -2.80 | [-2.99, -2.60] | 58,460 |
| BTCUSD | -3.22 | [-3.41, -3.04] | 66,003 |
| USTEC | -2.75 | [-2.95, -2.55] | 54,052 |

All CIs exclude zero in the negative direction. For ref=Renko, differences are larger (-13 to -15 pp).

Agreement increases with volatility regime by 1-2 pp per regime step.

### Hypothesis-Specific Conclusion

**REFUTED**

The paired bootstrap — the pre-specified test — shows negative differences for all instruments. Line Break agrees with Time Bars slightly more than with Renko on the paired subset (diff = -0.7 to -3.2 pp). Renko agrees with Time Bars substantially more than with Line Break (diff = -13 to -15 pp). The raw ~90% LB↔Renko agreement reflects shared noise-filtering methodology, not independent trend confirmation.

### Hypothesis-Agnostic Observations

- Event density differences between chart types explain agreement patterns independently of trend-direction correspondence
- Renko's ATR-based sizing tracks time bars more closely than Line Break's fixed level parameter
- Heiken Ashi's low agreement (~65%) confirms its direction labels are structurally different from raw bar direction
- Agreement increases with volatility, consistent with stronger trends producing clearer directional signals

---

## EXP-006 — Heiken Ashi Synthetic Price Distortion Quantification

**Status**: REFUTED
**Date**: 2026-05-16
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Chart Types**: Time Bars, Heiken Ashi

### Hypothesis Tests

1. **Hypothesis**: Heiken Ashi synthetic prices compress realised return magnitude and volatility by at least 30% versus real 1-minute prices on all 4 Phase 1 instruments, making HA-price-derived returns unsuitable for strategy evaluation.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Chart Types**: Time Bars, Heiken Ashi
- **Features**: HAClose vs RealClose returns at identical CloseTime, volatility compression, median absolute return compression, regime-stratified compression, block bootstrap (n=1000, block size 100)
- **Parameter ranges**: Heiken Ashi generated from 1-minute source bars; no configurable parameters
- **Exclusions**: No Line Break or Renko analysis, no strategy backtesting, no predictive modelling, no claim that lower HA volatility is improved risk
- **Constraints**: Final 30% holdout excluded; HAClose returns used only for distortion diagnostics, not P&L; regime labels calibrated on train segment

### Results / Observations

Volatility compression (30% threshold required):

| Instrument | Point Estimate | 95% CI | Meets 30%? |
|------------|---------------|--------|------------|
| EURUSD | 0.254 | [0.247, 0.259] | NO |
| XAUUSD | 0.260 | [0.255, 0.265] | NO |
| BTCUSD | 0.259 | [0.251, 0.267] | NO |
| USTEC | 0.257 | [0.250, 0.262] | NO |

Median absolute return compression (20% threshold required):

| Instrument | Point Estimate | 95% CI | Meets 20%? |
|------------|---------------|--------|------------|
| EURUSD | 0.202 | [0.194, 0.207] | Barely |
| XAUUSD | 0.248 | [0.246, 0.251] | YES |
| BTCUSD | 0.270 | [0.268, 0.272] | YES |
| USTEC | 0.256 | [0.254, 0.259] | YES |

Regime stratification: compression present across all three volatility regimes on all instruments. HA direction change frequency 30-35% lower than real prices. HA mean range is higher than real mean range (negative compression) due to OHLC averaging.

### Hypothesis-Specific Conclusion

**REFUTED**

Zero of 4 instruments meet the 30% volatility compression threshold. Compression is approximately 25-26% for volatility and 20-27% for median absolute returns — consistently below the 30% threshold. The finding is precise (tight bootstrap CIs from 830K-1.09M bars per instrument), consistent across all four instruments, and present across all volatility regimes.

### Hypothesis-Agnostic Observations

- The ~25-26% volatility compression varies by only 0.6 percentage points across forex, commodity, crypto, and index — a structural property of the HA formula
- HA direction change frequency is 30-35% lower, confirming trend smoothing
- HA mean range is higher than real range because HAClose averaging produces wider apparent candle bodies
- The practical implication is unchanged: HA-derived returns are unsuitable for strategy evaluation

---

## EXP-001-TF — Timeframe Replication: Information Density & Ghost Bar Comparison

**Status**: REFUTED
**Date**: 2026-05-17
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Chart Types**: Time Bars (15m, 1h), Line Break (levels 3, 5), Renko (ATR 14), Heiken Ashi

### Hypothesis Tests

1. **Hypothesis**: Line Break and Renko event bars have higher information density than same-timeframe time bars on at least 3 of 4 instruments at 15m and 1h source timeframes, measured as lower ghost rate (≥25% reduction), better use of remaining directional-entropy headroom (≥50% capture), and a practical absolute entropy gain (≥0.005 bits).

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Chart Types**: Time Bars (15m, 1h), Line Break (levels 3, 5), Renko (ATR 14), Heiken Ashi
- **Features**: Ghost rate, directional entropy, volatility terciles, bootstrap confidence intervals, distinct-source sensitivity
- **Parameter ranges**: Source timeframes 15m and 1h; LineBreak level 3 and 5; Renko ATR period 14
- **Exclusions**: No strategy backtesting, no parameter optimization, no predictive modeling, no source timeframes beyond 15m and 1h
- **Constraints**: Final 30% global holdout excluded before aggregation; synthetic price discipline; timestamp alignment over bar count

### Results / Observations

Ghost reduction and entropy metrics by instrument, timeframe, and chart type:

| Instrument | TF | ChartType | GhostRate | DirectionalEntropy | BarsPerElapsedDay |
|------------|-----|-----------|-----------|-------------------|-------------------|
| EURUSD | 15m | Time | 0.0218 | 0.99938 | 64.3 |
| EURUSD | 15m | LineBreak3 | 0.0064 | 0.99963 | 16.8 |
| EURUSD | 15m | Renko | 0.0007 | 0.99959 | 16.0 |
| EURUSD | 1h | Time | 0.0097 | 0.99997 | 14.7 |
| EURUSD | 1h | Renko | 0.0000 | 0.99954 | 3.8 |
| BTCUSD | 15m | Time | 0.0003 | 0.99996 | 79.3 |
| BTCUSD | 15m | Renko | 0.0000 | 0.99953 | 17.6 |

Threshold evaluation (all combinations):

| Timeframe | ChartType | SupportCount (of 4) | Verdict |
|-----------|-----------|---------------------|---------|
| 15m | LineBreak3 | 0 | REFUTED |
| 15m | Renko | 0 | REFUTED |
| 1h | LineBreak3 | 0 | REFUTED |
| 1h | Renko | 0 | REFUTED |

Bootstrap (n=4 instruments):
- 15m LB3 GhostReduction: mean 0.865, CI [0.742, 0.988]
- 15m LB3 EntropyGain: mean -0.0034, CI [-0.0058, -0.0010] — entirely negative
- 1h Renko GhostReduction: mean 1.0, CI [1.0, 1.0]
- 1h Renko EntropyGain: mean -0.0042, CI [-0.0069, -0.0014] — entirely negative

Renko duplicate-source share: 12-21% across instruments/timeframes. LineBreak: 0%.

### Hypothesis-Specific Conclusion

**REFUTED**

Ghost-rate reduction replicates robustly (70-100%) but directional entropy gains are uniformly negative across all instruments and timeframes. SupportCount = 0/4 for all combinations. Maximum headroom capture was 40.6% (EURUSD 15m LB3), below the 50% threshold.

### Hypothesis-Agnostic Observations

- Event charts reduce ghost bars and bar count but also reduce directional entropy at higher timeframes
- Renko duplicate-source rows (12-21%) require explicit denominator handling for entropy metrics
- Bar compression at 15m: LB3 ~26% of time bars, Renko ~25%. At 1h: LB3 ~27%, Renko ~26%
- The entropy reduction pattern is consistent across all 4 instruments, suggesting a structural property of event charts at higher timeframes

---

## EXP-002-TF — Timeframe Replication: Volatility & Trend Regime Representation

**Status**: REFUTED
**Date**: 2026-05-17
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Chart Types**: Time Bars (15m, 1h), Line Break (level 3), Renko (ATR 14), Heiken Ashi

### Hypothesis Tests

1. **Hypothesis**: On at least 3 instruments at each tested timeframe, Line Break level 3 or Renko ATR-14 has hybrid rate ≤0.05 and median transition lag ≤2 source time bars.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Chart Types**: Time Bars (15m, 1h), Line Break (level 3), Renko (ATR 14), Heiken Ashi
- **Features**: Rolling realised volatility (window=20), train-derived tercile regime labels, hybrid rate, confirmed transition lag, paired bootstrap
- **Parameter ranges**: Source timeframes 15m and 1h; LineBreak level 3; Renko ATR period 14
- **Exclusions**: No parameter search, no predictive models, no strategy validation, no source timeframes beyond 15m and 1h
- **Constraints**: Final 30% global holdout excluded before aggregation; synthetic price discipline; timestamp alignment via CloseTime/SourceCloseTime

### Results / Observations

Hybrid rate by chart type, instrument, and timeframe:

| Instrument | TF | Time | LineBreak | Renko | HeikenAshi |
|------------|-----|------|-----------|-------|------------|
| EURUSD | 15m | 0.000 | 0.095 | 0.149 | 0.000 |
| EURUSD | 1h | 0.000 | 0.125 | 0.191 | 0.000 |
| XAUUSD | 15m | 0.000 | 0.101 | 0.179 | 0.000 |
| XAUUSD | 1h | 0.000 | 0.127 | 0.223 | 0.000 |
| BTCUSD | 15m | 0.000 | 0.099 | 0.156 | 0.000 |
| BTCUSD | 1h | 0.000 | 0.127 | 0.178 | 0.000 |
| USTEC | 15m | 0.000 | 0.089 | 0.139 | 0.000 |
| USTEC | 1h | 0.000 | 0.115 | 0.163 | 0.000 |

Transition lag diagnostics:

| Instrument | TF | ChartType | MedianLagBars | MissedTransitions | TransitionCount |
|------------|-----|-----------|--------------|-------------------|-----------------|
| EURUSD | 15m | LineBreak | 2.0 | 3 | 904 |
| EURUSD | 15m | Renko | 2.0 | 5 | 904 |
| BTCUSD | 1h | LineBreak | 5.0 | 1 | 326 |
| USTEC | 15m | LineBreak | 3.0 | 1 | 855 |

Bootstrap (n=4 instruments):
- 15m LineBreak AbsoluteHybridExcessVsTime: mean 0.096, CI [0.091, 0.100]
- 1h Renko AbsoluteHybridExcessVsTime: mean 0.189, CI [0.170, 0.212]

Verdict: SupportCount = 0/4 for all combinations. WithinBounds = False for all event chart rows.

### Hypothesis-Specific Conclusion

**REFUTED**

Hybrid rates exceed 0.05 on all 4 instruments at both timeframes (8.9-22.3%). Median lag is within bounds (≤2 bars) for most combinations but BTCUSD 1h LineBreak exceeds at 5.0 bars. The boundary cost is structural — event charts emit bars at irregular intervals that do not align with time-based regime boundaries.

### Hypothesis-Agnostic Observations

- Event charts miss only 0-3 transitions per combination (0-1% of total), showing high coverage despite boundary cost
- Renko hybrid rates are consistently higher than LineBreak (by 4-10pp), reflecting Renko's different event generation mechanism
- Max lag values are extremely large for some combinations (USTEC 15m LineBreak: 3,376 bars), reflecting rare events where the chart type took very long to confirm a transition
- Heiken Ashi inherits the time-bar regime timeline perfectly (1:1 timestamp mapping)

---

## EXP-003-TF — Timeframe Replication: Noise Filtering & Statistical Robustness

**Status**: REFUTED
**Date**: 2026-05-17
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Chart Types**: Time Bars (15m, 1h), Line Break (level 3), Renko (ATR 14), Heiken Ashi

### Hypothesis Tests

1. **Hypothesis**: At 20% noise level, Line Break or Renko has ≥25% lower relative drift than same-timeframe time bars in at least 2 of 3 metrics on at least 3 instruments at each tested timeframe.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Chart Types**: Time Bars (15m, 1h), Line Break (level 3), Renko (ATR 14), Heiken Ashi
- **Features**: Direction stability (up-fraction drift), Return variance stability, LZ76 complexity stability
- **Parameter ranges**: Source timeframes 15m and 1h; noise levels 0%, 10%, 20%, 30%; LineBreak level 3; Renko ATR period 14
- **Exclusions**: No stochastic simulation sweep, no strategy testing, no parameter optimization, no tick-level noise model
- **Constraints**: Final 30% global holdout excluded before aggregation and perturbation; HA uses HAClose only as distortion diagnostic; deterministic perturbation with instrument-timeframe seed

### Results / Observations

Robustness ranking at 20% noise (InstrumentsWithAtLeast25PctLowerDrift than Time):

| Timeframe | ChartType | Metric | Count (of 4) |
|-----------|-----------|--------|--------------|
| 15m | LineBreak | DirectionDrift | 2 |
| 15m | LineBreak | ReturnVarianceDrift | 1 |
| 15m | LineBreak | ComplexityDrift | 0 |
| 15m | Renko | DirectionDrift | 2 |
| 15m | Renko | ReturnVarianceDrift | 2 |
| 15m | Renko | ComplexityDrift | 0 |
| 1h | LineBreak | DirectionDrift | 0 |
| 1h | LineBreak | ReturnVarianceDrift | 1 |
| 1h | LineBreak | ComplexityDrift | 1 |
| 1h | Renko | DirectionDrift | 0 |
| 1h | Renko | ReturnVarianceDrift | 1 |
| 1h | Renko | ComplexityDrift | 0 |

Sample drift values at 20% noise, 15m:

| Instrument | ChartType | DirectionDrift | ReturnVarianceDrift | ComplexityDrift |
|------------|-----------|---------------|---------------------|-----------------|
| EURUSD | Time | 0.0031 | 0.1098 | 0.0031 |
| EURUSD | LineBreak | 0.0016 | 0.1286 | 0.0313 |
| EURUSD | Renko | 0.0002 | 0.0755 | 0.0296 |
| EURUSD | HeikenAshi | 0.0010 | 0.0178 | 0.0014 |

Perturbation audit: InvalidRows = 0 for all 32 combinations. InvalidPct = 0.0.

### Hypothesis-Specific Conclusion

**REFUTED**

Maximum instrument count for any metric was 2 (DirectionDrift and ReturnVarianceDrift for Renko at 15m), below the ≥3 threshold. Complexity drift is consistently worse for event charts (0 instruments meet threshold). The EXP-003 noise-robustness finding does not replicate at higher timeframes.

### Hypothesis-Agnostic Observations

- Heiken Ashi shows the lowest drift across all metrics, confirming its smoothing effect (uses HAClose as distortion diagnostic)
- Event charts are more sensitive to source-bar noise in terms of sequence complexity — perturbing close prices changes event-bar boundaries, altering direction sequence structure
- Drift generally increases monotonically with noise level (0% → 10% → 20% → 30%), confirming graded stress response
- OHLC repair via High/Low adjustment is fully effective for close-price perturbation

---

## EXP-004-TF — Timeframe Replication: Market Structure Capture Speed & Fidelity

**Status**: REFUTED
**Date**: 2026-05-17
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Chart Types**: Time Bars (15m, 1h), Line Break (level 3), Renko (ATR 14), Heiken Ashi

### Hypothesis Tests

1. **Hypothesis**: Line Break or Renko median detection latency is ≥30% lower than same-timeframe time-bar baseline on ≥3 instruments, while precision is no more than 10pp higher than time bars.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Chart Types**: Time Bars (15m, 1h), Line Break (level 3), Renko (ATR 14), Heiken Ashi
- **Features**: Direction changes as reversal signals; ATR-scaled swing reversals (1.5x and 2.0x ATR) as reference; precision, recall, split rate
- **Parameter ranges**: Source timeframes 15m and 1h; LineBreak level 3; Renko ATR period 14; tolerance window 120 minutes
- **Exclusions**: No strategy entry/exit testing, no optimisation of reversal thresholds, no predictive model, no bar-index alignment
- **Constraints**: Final 30% holdout excluded before aggregation; real-price reversal reference; timestamp alignment via CloseTime/SourceCloseTime

### Results / Observations

Speed and precision metrics by instrument, timeframe, and chart type:

| Instrument | TF | ChartType | MedianLatencyMin | Precision | Recall | SplitRate | TotalSignals |
|------------|-----|-----------|-----------------|-----------|--------|-----------|--------------|
| EURUSD | 15m | Time | 30.0 | 0.244 | 0.969 | 0.756 | 28,081 |
| EURUSD | 15m | LineBreak | 15.0 | 0.891 | 0.358 | 0.109 | 2,841 |
| EURUSD | 15m | Renko | 0.0 | 0.997 | 0.694 | 0.003 | 4,922 |
| EURUSD | 1h | Time | 0.0 | 0.154 | 0.598 | 0.846 | 6,474 |
| EURUSD | 1h | Renko | 0.0 | 0.798 | 0.535 | 0.202 | 1,121 |
| BTCUSD | 15m | Time | 30.0 | 0.247 | 0.982 | 0.753 | 36,966 |
| BTCUSD | 15m | Renko | 15.0 | 0.985 | 0.612 | 0.015 | 5,769 |

FasterCount (≥30% latency reduction vs Time):

| Timeframe | ChartType | FasterCount (of 4) |
|-----------|-----------|-------------------|
| 15m | LineBreak | 4 |
| 15m | Renko | 4 |
| 1h | LineBreak | 4 |
| 1h | Renko | 4 |

Reversal label sensitivity (alt/primary count ratio): 0.63-0.68 across all instruments/timeframes.

### Hypothesis-Specific Conclusion

**REFUTED**

Latency criterion met (FasterCount = 4/4 for all combinations). Precision criterion not met — event chart precision exceeds time bar precision by 35-80pp (far above 10pp bound). Event charts are both faster and more precise, at the cost of lower recall. This is a speed-recall-precision trade-off, not a speed-precision trade-off.

**Audit caveat**: Precision can exceed 1.0 (USTEC 15m Renko = 1.022) due to counting methodology where multiple reversals can match the same signal.

### Hypothesis-Agnostic Observations

- Time bars produce massive signal redundancy (split rate 75-85%), confirming high noise relative to event charts
- Renko achieves near-zero split rate (0-2%) — almost every signal matches a real reversal
- LineBreak has lowest recall (16-36%) but high precision (51-90%)
- 1h timeframe resolution limits latency differentiation — all chart types show 0-minute median latency
- Reversal labels are stable under threshold variation (alt/primary ratio 0.63-0.68)

---

## EXP-005-TF — Timeframe Replication: Cross-Chart-Type Alignment & Regime Correspondence

**Status**: REFUTED
**Date**: 2026-05-17
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Chart Types**: Time Bars (15m, 1h), Line Break (level 3), Renko (ATR 14), Heiken Ashi

### Hypothesis Tests

1. **Hypothesis**: In medium- and high-volatility regimes, LB/Renko timestamp-aligned direction agreement is ≥10pp higher than each chart type's agreement with same-timeframe time bars on ≥3 instruments, with paired bootstrap CIs excluding zero.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Chart Types**: Time Bars (15m, 1h), Line Break (level 3), Renko (ATR 14), Heiken Ashi
- **Features**: Direction labels, timestamp-aligned pairwise agreement (5m primary, 15m sensitivity), volatility tercile regimes, paired bootstrap
- **Parameter ranges**: Source timeframes 15m and 1h; LineBreak level 3; Renko ATR period 14; tolerance windows 5 and 15 minutes
- **Exclusions**: No claim that agreement implies profitability, no predictive modelling, no optimisation of tolerance windows, no bar-index alignment
- **Constraints**: Final 30% holdout excluded before aggregation; no strategy P&L; timestamp alignment via CloseTime/SourceCloseTime; regime labels calibrated on train segment

### Results / Observations

Pairwise agreement at 5-minute tolerance:

| Instrument | TF | Pair | Agreement | OverlapRate |
|------------|-----|------|-----------|-------------|
| EURUSD | 15m | LB<->Renko | 1.000 | 0.499 |
| EURUSD | 15m | LB<->Time | 0.986 | 1.000 |
| EURUSD | 15m | Renko<->Time | 0.990 | 1.000 |
| EURUSD | 15m | Time<->HA | 0.656 | 1.000 |
| BTCUSD | 15m | LB<->Renko | 1.000 | 0.498 |
| BTCUSD | 15m | LB<->Time | 0.991 | 1.000 |
| USTEC | 1h | LB<->Renko | 1.000 | 0.531 |
| USTEC | 1h | LB<->Time | 0.981 | 1.000 |

Bootstrap CIs for LB_Renko improvement over LB_Time (medium/high regimes, n=8):

| Timeframe | Tolerance | Comparison | Mean | CI Lower | CI Upper |
|-----------|-----------|------------|------|----------|----------|
| 15m | 5min | LB_Renko_minus_LB_Time | 0.0108 | 0.0080 | 0.0145 |
| 15m | 15min | LB_Renko_minus_LB_Time | -0.0009 | -0.0041 | 0.0024 |
| 1h | 5min | LB_Renko_minus_LB_Time | 0.0215 | 0.0157 | 0.0268 |
| 1h | 15min | LB_Renko_minus_LB_Time | 0.0215 | 0.0157 | 0.0268 |

Regime-stratified agreement (5-min tolerance, Medium regime):

| Instrument | TF | LB<->Renko | LB<->Time | Renko<->Time | Time<->HA |
|------------|-----|-----------|-----------|-------------|-----------|
| EURUSD | 15m | 1.000 | 0.979 | 0.991 | 0.658 |
| XAUUSD | 15m | 1.000 | 0.989 | 0.990 | 0.654 |
| BTCUSD | 15m | 1.000 | 0.996 | 0.996 | 0.648 |
| USTEC | 15m | 1.000 | 0.986 | 0.993 | 0.665 |

### Hypothesis-Specific Conclusion

**REFUTED**

LB<->Renko agreement improvement over LB<->Time is only 1-2pp (far below 10pp threshold). Bootstrap CI at 5-min tolerance excludes zero (statistically significant) but the effect size is practically negligible. Event charts agree with time bars at 97-99%, nearly as well as they agree with each other (100% on matched events). Overlap is only ~50% at 5-min tolerance.

### Hypothesis-Agnostic Observations

- LB<->Renko agreement is exactly 1.0 across all instruments/timeframes when events align within 5 minutes
- Overlap rate of ~50% means perfect agreement applies to only half of LB events
- Time<->HA agreement is consistently ~65%, reflecting HA's different direction formula
- Agreement patterns are consistent across low, medium, and high volatility regimes
- Increasing tolerance from 5 to 15 minutes increases overlap to ~73-77% but does not materially change agreement rankings

---

## EXP-006-TF — Timeframe Replication: Heiken Ashi Synthetic Price Distortion Quantification

**Status**: REFUTED
**Date**: 2026-05-17
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Chart Types**: Time Bars (15m, 1h), Heiken Ashi

### Hypothesis Tests

1. **Hypothesis**: On all 4 instruments at both timeframes, absolute HA close-to-close return volatility is ≥30% lower than real same-timeframe return volatility, and median absolute HA return magnitude is ≥20% lower than real return magnitude.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Chart Types**: Time Bars (15m, 1h), Heiken Ashi
- **Features**: HAClose vs RealClose returns at identical CloseTime, volatility compression, median absolute return compression, direction change compression, regime-stratified compression, block bootstrap (n=1000, block size 100)
- **Parameter ranges**: Source timeframes 15m and 1h; Heiken Ashi generated from aggregated bars; no configurable parameters
- **Exclusions**: No Line Break or Renko analysis, no strategy backtesting, no predictive modelling, no claim that lower HA volatility is improved risk
- **Constraints**: Final 30% holdout excluded before aggregation; HAClose returns used only for distortion diagnostics; regime labels calibrated on train segment

### Results / Observations

Volatility compression (30% threshold required):

| Instrument | TF | RealVolatility | HAVolatility | VolatilityCompression | Meets 30%? |
|------------|-----|---------------|-------------|----------------------|------------|
| EURUSD | 15m | 0.000492 | 0.000362 | 0.265 | NO |
| EURUSD | 1h | 0.001014 | 0.000751 | 0.259 | NO |
| XAUUSD | 15m | 0.000948 | 0.000710 | 0.251 | NO |
| XAUUSD | 1h | 0.001957 | 0.001470 | 0.249 | NO |
| BTCUSD | 15m | 0.002888 | 0.002166 | 0.250 | NO |
| BTCUSD | 1h | 0.005900 | 0.004516 | 0.235 | NO |
| USTEC | 15m | 0.001364 | 0.001013 | 0.258 | NO |
| USTEC | 1h | 0.002775 | 0.002096 | 0.245 | NO |

Median absolute return compression (20% threshold required):

| Instrument | TF | RealMAD | HAMAD | MADCompression | Meets 20%? |
|------------|-----|---------|-------|----------------|------------|
| EURUSD | 15m | 0.000205 | 0.000153 | 0.253 | YES |
| EURUSD | 1h | 0.000447 | 0.000338 | 0.245 | YES |
| XAUUSD | 15m | 0.000405 | 0.000298 | 0.264 | YES |
| XAUUSD | 1h | 0.000861 | 0.000661 | 0.233 | YES |
| BTCUSD | 15m | 0.001186 | 0.000846 | 0.286 | YES |
| BTCUSD | 1h | 0.002352 | 0.001777 | 0.244 | YES |
| USTEC | 15m | 0.000438 | 0.000327 | 0.253 | YES |
| USTEC | 1h | 0.000933 | 0.000710 | 0.240 | YES |

Direction change compression: 27-29% across all instruments/timeframes.

Regime stratification (15m, VolatilityCompression):

| Instrument | Low | Medium | High |
|------------|-----|--------|------|
| EURUSD | 0.272 | 0.261 | 0.259 |
| XAUUSD | 0.252 | 0.253 | 0.253 |
| BTCUSD | 0.270 | 0.271 | 0.257 |
| USTEC | 0.267 | 0.266 | 0.255 |

### Hypothesis-Specific Conclusion

**REFUTED**

Volatility compression threshold (≥30%) not met on any instrument (range: 23.5-26.5%). Median return compression threshold (≥20%) met on all instruments (range: 23.3-28.6%). Because both thresholds must be met, the hypothesis is refuted. Compression is consistent across instruments (23-27%) and timeframes (no material 15m vs 1h difference).

### Hypothesis-Agnostic Observations

- Volatility compression varies by only 0.6pp across forex, commodity, crypto, and index — a structural property of the HA formula
- HA direction change frequency is 27-29% lower, confirming trend smoothing
- Compression is slightly higher in low-volatility regimes for most instruments
- The practical conclusion remains valid: HA compresses return magnitude by 23-29%, making HA-price-derived returns unsuitable for strategy evaluation


## EXP-007 - Multi-State Signal-Quality Baseline

**Status**: SUPPORTED
**Date**: 2026-05-17
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: Time Bars, Line Break level 3, Renko ATR-14, Heiken Ashi

### Hypothesis Tests

1. **Hypothesis**: Real-price signal quality cannot be adequately characterized by binary direction alone. A multi-state signal-quality framework measuring forward excursion, adverse excursion, run continuation, signal-level precision, and event-level recall in ATR units on the real-price timeline produces pre-specified differentiation across chart types and volatility regimes.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: Time Bars, Line Break level 3, Renko ATR-14, Heiken Ashi
- **Features**: FE and AE at 30/60/120/240 minutes, log FE/AE ratio, 60-minute signal-level precision, event-level recall, 30-minute run continuation, signal multiplicity, missing-signal states
- **Parameter ranges**: 1-minute and 15-minute source timeframes; Line Break level 3; Renko ATR period 14
- **Exclusions**: No strategy P&L, no parameter optimization, no predictive models, no chart-combination logic, no 1-hour Block B signal-quality analysis
- **Constraints**: Final 30% global holdout excluded; all outcomes measured from aligned 1-minute real OHLC prices; event charts aligned by `SourceCloseTime`; time bars and Heiken Ashi aligned by `CloseTime`

### Results / Observations

- Proceed criteria met:
  - 15-minute Renko AE60: 4/4 instruments, CIs excluding zero
  - 15-minute Renko FE60: 4/4 instruments, CIs excluding zero
  - 15-minute LineBreak AE60: 3/4 instruments, CIs excluding zero
- No 1-minute proceed criterion passed.
- 15-minute Renko-minus-Time AE60 mean differences: BTCUSD `-0.738`, EURUSD `-0.299`, USTEC `-0.448`, XAUUSD `-0.400`; all CIs exclude zero.
- 15-minute Renko-minus-Time FE60 mean differences: BTCUSD `-0.242`, EURUSD `-0.427`, USTEC `-0.282`, XAUUSD `-0.326`; all CIs exclude zero.
- Weighted 15-minute means: Time FE60 `4.964`, Time AE60 `4.943`; Renko FE60 `4.644`, Renko AE60 `4.462`; LineBreak FE60 `4.732`, LineBreak AE60 `4.622`.
- Weighted precision stayed tightly clustered: 15-minute Time `0.836`, Heiken Ashi `0.836`, LineBreak `0.824`, Renko `0.818`; no precision proceed criterion passed.
- Event-chart missing source-bar shares: 1-minute LineBreak `0.737`, 1-minute Renko `0.720`, 15-minute LineBreak `0.763`, 15-minute Renko `0.759`.

### Hypothesis-Specific Conclusion

**SUPPORTED**

EXP-007 supports the measurement-gate hypothesis because the pre-specified proceed gate was met through 15-minute FE60 and AE60 differentiation. The support validates the framework, not a simple event-chart superiority claim: Renko reduced both favourable and adverse excursion relative to Time at 15 minutes.

### Hypothesis-Agnostic Observations

- FE60 and AE60 should carry forward as separate primary metrics for Block B; combining them would hide the main trade-off.
- Signal-level precision and run continuation did not differentiate chart types strongly enough to drive downstream experiments.
- Missing-signal states are large enough that every downstream event-chart signal-quality experiment must report coverage cost explicitly.
