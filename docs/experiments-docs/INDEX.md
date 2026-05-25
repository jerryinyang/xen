# Experiments Index (Comprehensive)

## Checkpoint Retrospectives

| Checkpoint | Status | Key Synthesis | Document |
| --- | --- | --- | --- |
| 2026-05-14-001-chart-type-validation | COMPLETED | Phase 1 validates time bars as the master timeline for 1-minute-source analysis; higher-timeframe robustness remains a Phase 1B bridge item before Phase 2 signal-quality characterization. | [retrospective.md](checkpoints/2026-05-14-001-chart-type-validation/retrospective.md) |
| 2026-05-16-001-signal-quality-classification | COMPLETED | Phase 2 validates the FE/AE measurement framework but refutes the event-chart signal-quality path; broad event-chart strategy exploration is not justified without a new narrower thesis. | [retrospective.md](checkpoints/2026-05-16-001-signal-quality-classification/retrospective.md) |
| 2026-05-23-003-ict-one-setup-timebar-validation | ACTIVE | Starts a separate time-bar-native ICT thesis; prior event-chart hypotheses and infrastructure do not carry forward except for the canonical time-bar timeline and research governance. | [design.md](checkpoints/2026-05-23-003-ict-one-setup-timebar-validation/design.md) |


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

---

## EXP-008 - Renko as a Precision Gate Over Time-Bar Signals

**Status**: REFUTED
**Date**: 2026-05-17
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: Time Bars, Renko ATR-14

### Hypothesis Tests

1. **Hypothesis**: At the 15-minute source timeframe, time-bar direction signals confirmed by a same-or-prior Renko ATR-14 emission within a fixed tolerance window show a better AE-relative-to-FE trade-off than the full set of time-bar direction signals, after accounting for Renko's coverage cost.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: Time Bars as candidate signals, Renko ATR-14 as confirmation gate
- **Features**: Time-bar direction signals, Renko `SourceCloseTime` confirmation, FE60, AE60, log FE/AE, coverage, coverage-adjusted outcomes, raw Renko comparator
- **Parameter ranges**: 1-minute exploratory and 15-minute confirmatory source timeframes; confirmation windows 5, 15, and 30 minutes; 15-minute window is primary
- **Exclusions**: No strategy P&L, no parameter optimization, no tick-level data, no Line Break or Heiken Ashi analysis, no best-timeframe selection
- **Constraints**: Final 30% global holdout excluded before aggregation/generation; Renko confirmation must be same-or-prior; all outcomes use real 1-minute prices

### Results / Observations

- Primary 15-minute Renko confirmation coverage: BTCUSD `0.246`, EURUSD `0.282`, USTEC `0.287`, XAUUSD `0.272`.
- Confirmed-minus-all-time log FE/AE mean differences: BTCUSD `-0.032` with CI including zero; EURUSD `-0.073` with CI excluding zero negatively; USTEC `+0.042` with CI excluding zero positively; XAUUSD `-0.015` with CI including zero.
- Confirmed-minus-all-time AE60 is lower on all four instruments: BTCUSD `-0.598`, EURUSD `-0.157`, USTEC `-0.296`, XAUUSD `-0.262`; all CIs exclude zero.
- Confirmed-minus-all-time FE60 is lower on BTCUSD (`-0.249`), EURUSD (`-0.308`), and XAUUSD (`-0.216`) with CIs excluding zero; USTEC is inconclusive (`-0.136`, CI includes zero).
- Confirmed-minus-raw-Renko log FE/AE CIs include zero on all four instruments.

### Hypothesis-Specific Conclusion

**REFUTED**

The primary criterion required log FE/AE improvement on at least 3 of 4 instruments. Only USTEC shows a positive significant log-ratio improvement, while EURUSD worsens significantly. Renko confirmation reduces AE, but it also compresses FE and discards about 71-75% of time-bar signals.

### Hypothesis-Agnostic Observations

- Renko confirmation behaves more like a magnitude-compression gate than a signal-quality gate.
- The AE reduction is real and consistent, but it is not enough to justify the coverage cost under the approved FE/AE criteria.
- Future Renko-gating work would need to explicitly scope an AE-control objective with an allowed FE sacrifice.

---

## EXP-009 - Heiken Ashi Direction as a Signal Generator, Evaluated on Real Prices

**Status**: REFUTED
**Date**: 2026-05-17
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: Time Bars, Heiken Ashi

### Hypothesis Tests

1. **Hypothesis**: At the 15-minute source timeframe, Heiken Ashi direction changes evaluated on real prices select a subset of the time-bar signal population with a better AE-relative-to-FE trade-off than raw time-bar direction changes.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: 15-minute Time Bars and Heiken Ashi
- **Features**: Time-bar direction changes, HA direction changes, FE60, AE60, log FE/AE, coverage-adjusted FE60/AE60, direction-change alignment
- **Parameter ranges**: 15-minute source timeframe only; HA has no configurable parameter
- **Exclusions**: No strategy P&L, no HA construction-price returns, no Renko or Line Break data, no parameter variation, no 1-minute analysis
- **Constraints**: Final 30% global holdout excluded before aggregation; HA prices define signal direction only; all outcomes use real 1-minute time-bar prices

### Results / Observations

- HA/time-bar direction-change count ratios: EURUSD `0.493`, XAUUSD `0.484`, BTCUSD `0.492`, USTEC `0.477`.
- HA direction changes aligned to same-direction time-bar direction changes within 15 minutes at shares of `0.866-0.895`.
- HA-minus-time log FE/AE mean differences: BTCUSD `-0.040`, EURUSD `-0.017`, USTEC `+0.013`, XAUUSD `+0.012`; all CIs include zero.
- HA-minus-time FE60 has one significant positive result: XAUUSD `+0.034`, CI `[+0.019, +0.397]`.
- HA-minus-time AE60 has no instrument with a CI excluding zero.
- Coverage by regime ranges from `0.436` to `0.534`.

### Hypothesis-Specific Conclusion

**REFUTED**

The primary criterion required log FE/AE improvement on at least 3 of 4 instruments with CIs excluding zero. HA achieved 0 of 4. HA smoothing reduces signal frequency but does not select a consistently better AE-relative-to-FE subset.

### Hypothesis-Agnostic Observations

- HA is a stronger 15-minute direction-change filter than expected from the design rationale, cutting direction-change counts by about half.
- HA remains better framed as a smoothing descriptor or future time-bar-native feature, not as a standalone signal generator.
- FE60 and AE60 should continue to be reported separately because isolated FE movement did not translate into a log-ratio finding.

---

## EXP-010 - Line Break as a Confirmation Layer Over Renko Signals

**Status**: REFUTED
**Date**: 2026-05-17
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: Renko ATR-14, Line Break level 3

### Hypothesis Tests

1. **Hypothesis**: At the 15-minute source timeframe, Renko signals confirmed by a same-or-prior Line Break level 3 emission show a better AE-relative-to-FE trade-off than the full Renko signal set, after accounting for the additional coverage reduction imposed by Line Break.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: Renko ATR-14 primary signals, Line Break level 3 confirmation layer
- **Features**: Renko `SourceCloseTime` signals, same-or-prior Line Break confirmation, FE60, AE60, log FE/AE, coverage, coverage-adjusted outcomes
- **Parameter ranges**: 1-minute exploratory and 15-minute confirmatory source timeframes; confirmation windows 5, 15, and 30 minutes; 15-minute window is primary
- **Exclusions**: No strategy P&L, no time-bar or HA primary signals, no parameter optimization, no best-timeframe selection
- **Constraints**: Final 30% global holdout excluded; outcomes use real 1-minute prices at Renko signal timestamps; Renko and Line Break construction prices are not used for returns or excursions

### Results / Observations

- Primary 15-minute Line Break confirmation coverage: BTCUSD `0.535`, EURUSD `0.626`, USTEC `0.605`, XAUUSD `0.618`.
- Confirmed-minus-all-Renko log FE/AE mean differences: BTCUSD `+0.057` with CI `[+0.010, +0.183]`; EURUSD `-0.059`, USTEC `+0.013`, XAUUSD `-0.020`, all with CIs including zero.
- Confirmed-minus-all-Renko FE60 is significantly lower on EURUSD (`-0.204`), USTEC (`-0.189`), and XAUUSD (`-0.153`).
- Confirmed-minus-all-Renko AE60 is significantly lower on USTEC (`-0.183`) and XAUUSD (`-0.128`).
- Confirmed-minus-non-confirmed AE60 is lower on all four instruments (`-0.299` to `-0.473`), but log FE/AE is mixed.

### Hypothesis-Specific Conclusion

**REFUTED**

The primary criterion required log FE/AE improvement versus all Renko on at least 3 of 4 instruments. Only BTCUSD meets that criterion. Line Break confirmation selects lower-AE Renko subsets, but FE also declines and the ratio advantage does not generalize.

### Hypothesis-Agnostic Observations

- Line Break confirmation acts as a coverage selector, not a reliable quality gate.
- Confirmed signals are lower adverse-excursion episodes, but not consistently better AE-relative-to-FE episodes.
- Same-timestamp Renko emissions are material and remain counted as emitted signal rows under the approved denominator policy.

---

## EXP-011 - Event-Native Volatility Regime Detection

**Status**: REFUTED
**Date**: 2026-05-17
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: Renko ATR-14, Time Bars

### Hypothesis Tests

1. **Hypothesis**: Volatility-regime labels derived from Renko event density, source-bar count per brick, and brick-to-ATR ratio identify Renko regime states with lower boundary cost and fewer missed transitions than time-bar-derived regime labels applied to Renko events.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: Renko ATR-14 event-native features, time-bar volatility regime reference
- **Features**: 60-minute Renko event density, 60-minute median source count per brick, brick-to-ATR ratio, train-frozen terciles, hybrid rate, missed-transition rate, agreement, FE60/AE60 strata
- **Parameter ranges**: 1-minute and 15-minute source timeframes; Renko ATR period 14; terciles only
- **Exclusions**: No strategy P&L, no parameter optimization, no clustering, no quartiles/custom bins, no feature weights, no composite scoring, no post-hoc best-feature selection
- **Constraints**: Final 30% global holdout excluded; tercile boundaries computed on train segment only; all signal-quality outcomes use real 1-minute prices

### Results / Observations

- 15-minute hybrid rates:
  - Event density: `0.564-0.659`
  - Median source count: `0.739-0.750`
  - Brick-to-ATR: `0.750-0.788`
- 15-minute missed-transition rates:
  - Event density: `0.383-0.759`
  - Median source count: `0.448-0.491`
  - Brick-to-ATR: `0.324-0.407`
- 15-minute agreement with time-bar regimes:
  - Event density: up to `0.436`
  - Median source count: `0.250-0.261`
  - Brick-to-ATR: `0.211-0.250`
- Train-frozen boundaries were produced for all feature/instrument/timeframe combinations. Some discrete features have tied terciles, including 1-minute `BrickToATR` with Q1=Q2=`1.0`.

### Hypothesis-Specific Conclusion

**REFUTED**

No pre-fixed Renko-native feature provides a consistent lower-boundary-cost regime label. Brick-to-ATR has the lowest missed-transition rates, but its hybrid disagreement is high. Event density has lower hybrid rates than the other features in some cases, but missed-transition rates are inconsistent and can exceed 0.70.

### Hypothesis-Agnostic Observations

- Renko-native features describe event-generation mechanics more than canonical volatility regimes.
- Time-bar-derived volatility regimes should remain the default regime frame for Renko signal analysis.
- Renko-native features may still be useful as descriptive covariates, but not as volatility-regime replacements under the tested criteria.

---

## EXP-012 - ICT Data Readiness and Feasibility

**Status**: SUPPORTED
**Date**: 2026-05-23
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: 1-minute Time Bars, NY Macro Windows, Data Readiness

### Hypothesis Tests

1. **Hypothesis**: The available 1-minute time-bar datasets are sufficient for deterministic NY-time ICT macro-window research if timezone conversion, session coverage, missing-bar rates, and cost assumptions can be documented without using unavailable data.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: 1-minute time-bar inventory, NY-time macro-window coverage, missing-bar diagnostics, active-session summaries, cost-field availability
- **Features**: `CloseTime` ordering, train/test segment counts inside the analysis set, fixed macro windows AM1-AM5 and PM1-PM4, family-level coverage ratios, missing-bar rates within observed daily spans, schema-based cost-field availability
- **Parameter ranges**: UTC-to-`America/New_York` conversion assumption; macro windows AM1 `07:50-08:10`, AM2 `08:50-09:10`, AM3 `09:50-10:10`, AM4 `10:50-11:10`, AM5 `11:50-12:10`, PM1 `13:20-13:40`, PM2 `14:50-15:10`, PM3 `15:15-15:45`, PM4 `15:50-16:10`
- **Exclusions**: No event-chart inputs, no ICT signal generation, no parameter tuning, no tick or bid/ask data, no cost haircut applied to outcomes
- **Constraints**: Final 30% global holdout excluded from approved analysis; all timing aligned on `CloseTime`; cost assumptions recorded only as proxy scenarios

### Results / Observations

- All `16` macro-family coverage rows in `python/experiments/EXP-012/results/macro_family_coverage_summary.csv` exceed the scoped `0.80` threshold.
- Lowest family coverage: `USTEC Test PM = 0.9459`; highest family coverage: `BTCUSD Test PM = 0.9995`.
- Missing-bar rates within observed daily spans range from `0.0052` (`EURUSD Test`) to `0.0414` (`XAUUSD Train`).
- `python/experiments/EXP-012/results/cost_data_availability.csv` reports `False` for `Bid`, `Ask`, `Spread`, `Commission`, and `Slippage`; proxy scenarios were written to `python/experiments/EXP-012/results/cost_proxy_scenarios.json`.
- The rerun audit confirms `load_analysis_timebars()` computes row count lazily and collects only the holdout-excluded sorted analysis slice.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The experiment meets the scoped support condition. All four instruments can be converted to New York time under the documented UTC assumption, each clears the `>= 80%` macro-family coverage threshold in both train and test, missing-bar behavior is quantified, and cost assumptions are recorded through explicit proxy scenarios.

### Hypothesis-Agnostic Observations

- PM coverage is consistently weaker than AM coverage for `USTEC` and `XAUUSD`, even though all family ratios remain above the scoped threshold.
- The current repository time-bar schema is sufficient for macro-window presence studies but not for observed transaction-cost modeling; later ICT experiments need proxy costs or new data.

---

## EXP-014 - PDH PDL ONH ONL Liquidity Level Reproducibility

**Status**: SUPPORTED
**Date**: 2026-05-24
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: 1-minute Time Bars, Liquidity Levels

### Hypothesis Tests

1. **Hypothesis**: Previous-day and overnight high/low liquidity levels can be computed reproducibly from available time bars without exchange-calendar or preferred-data assumptions that are absent from the repository.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: PDH/PDL from prior observed weekday NY date; ONH/ONL from 17:00 prior calendar date through 09:30 event date
- **Features**: `PDH`, `PDL`, `ONH`, `ONL`, prior date, overnight bar count, missing-level reason, train/test readiness
- **Parameter ranges**: Availability threshold `0.80`; minimum all-level dates per train/test segment `50`
- **Exclusions**: No sweep outcome test, no full ICT model, no swing/equal-high levels, no event-chart features, no parameter tuning
- **Constraints**: Final 30% global holdout excluded; NY-time conversion uses EXP-012 convention; missing levels are classified rather than imputed

### Results / Observations

| Instrument | Train All-Level Availability | Test All-Level Availability | Instrument Pass |
| --- | ---: | ---: | --- |
| BTCUSD | 475/478 = 0.994 | 163/163 = 1.000 | True |
| EURUSD | 427/430 = 0.993 | 183/185 = 0.989 | True |
| USTEC | 425/428 = 0.993 | 184/185 = 0.995 | True |
| XAUUSD | 425/428 = 0.993 | 182/183 = 0.995 | True |

- Deterministic rerun equality: `True`.
- Missing reasons are classified as `NO_PRIOR_WEEKDAY`, `NO_OVERNIGHT_BARS`, or the combined first-row case.

### Hypothesis-Specific Conclusion

**SUPPORTED**

All four instruments meet the predefined reproducibility, availability, and train/test count thresholds. EXP-015 can inherit these liquidity-level definitions.

### Hypothesis-Agnostic Observations

- The prior observed weekday convention materially changes Monday PDH/PDL values versus a calendar-day convention for instruments with weekend data.
- Missing-level loss is small and explicit, making downstream sweep denominators auditable.

---

## EXP-015 - Prior High Low Sweep Reversal Behavior

**Status**: REFUTED
**Date**: 2026-05-25
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: 1-minute Time Bars, Liquidity Sweeps, PDH/PDL, ONH/ONL

### Hypothesis Tests

1. **Hypothesis**: Failed breakouts beyond PDH/PDL or ONH/ONL show measurable opposite-direction behavior compared with non-failed breaches, using real time-bar prices and predeclared risk units.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: Prior-day high/low, overnight high/low, first-touch sweep/breach events, forward real-price excursions
- **Features**: `PDH`, `PDL`, `ONH`, `ONL`, `EventType`, `Side`, `Risk1R`, `MFE_R`, `MAE_R`, `Hit1R`, `Hit2R`, time-to-target, time-to-stop
- **Parameter ranges**: Buffer `max(price_precision_step, 0.05 * ATR14Prior)`; horizons `30`, `60`, and `120` minutes; ONH/ONL eligible only at or after 09:30 NY
- **Exclusions**: No full ICT model, no macro-window filter, no premium/discount filter, no displacement, no IFVG, no breaker, no event-chart features, no tick or bid/ask data
- **Constraints**: Final 30% global holdout excluded; outcomes use real 1-minute OHLC prices; features use only information available at or before event `CloseTime`

### Results / Observations

Primary outcome: sweep minus breach 60-minute 1R-before-stop probability.

| Instrument | Segment | Sweep N | Breach N | Sweep Mean | Breach Mean | Bootstrap Diff | 95% CI | Supports Primary |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| EURUSD | Train | 236 | 341 | 0.504 | 0.566 | -0.061 | [-0.145, 0.021] | False |
| EURUSD | Test | 84 | 142 | 0.607 | 0.472 | +0.134 | [0.001, 0.267] | True |
| XAUUSD | Train | 249 | 361 | 0.470 | 0.482 | -0.012 | [-0.092, 0.068] | False |
| XAUUSD | Test | 116 | 131 | 0.491 | 0.519 | -0.029 | [-0.151, 0.095] | False |
| BTCUSD | Train | 354 | 336 | 0.480 | 0.521 | -0.041 | [-0.114, 0.034] | False |
| BTCUSD | Test | 86 | 142 | 0.453 | 0.570 | -0.117 | [-0.250, 0.018] | False |
| USTEC | Train | 333 | 330 | 0.477 | 0.467 | +0.010 | [-0.067, 0.086] | False |
| USTEC | Test | 144 | 144 | 0.444 | 0.396 | +0.048 | [-0.063, 0.160] | False |

- Supporting instruments: `1/4`.
- Test sweep counts pass the event-count gate for all instruments: EURUSD `89`, XAUUSD `131`, BTCUSD `93`, USTEC `160`.
- Test-segment weighted 60-minute MFE_R means are lower for sweeps than breaches on all instruments: EURUSD `6.788` vs `29.085`, XAUUSD `7.543` vs `30.957`, BTCUSD `8.505` vs `34.251`, USTEC `6.763` vs `29.680`.

### Hypothesis-Specific Conclusion

**REFUTED**

The predefined support rule required at least 3 instruments with adequate event counts and positive confidence intervals excluding zero. EXP-015 finds support on only EURUSD Test, while XAUUSD and BTCUSD are negative in test and USTEC crosses zero.

### Hypothesis-Agnostic Observations

- Sweep-only behavior is a weak standalone ICT component in the available data.
- Adequate event counts mean the failure is not a sample-size gate failure.
- Sweeps often have lower favorable and adverse excursion than breaches, suggesting a lower-movement rejection profile rather than broad directional edge.

---

## EXP-013 - NY Macro Window Characterization

**Status**: REFUTED
**Date**: 2026-05-24
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: 1-minute Time Bars, NY Macro Windows, Adjacent Controls, Random Controls

### Hypothesis Tests

1. **Hypothesis**: Predefined NY macro windows have statistically different range, absolute return, sweep frequency, displacement frequency, or forward-return shape than adjacent and randomized control windows on the available instruments.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: Fixed EXP-012 macro windows, adjacent equal-duration controls, deterministic same-day session-bounded random controls
- **Features**: ATR-normalized true range, absolute close return, sweep frequency, displacement frequency, 10/20/60-minute forward returns
- **Parameter ranges**: 100 deterministic random controls per instrument/date/window; primary effect threshold `0.10 ATR`; bootstrap reps `10,000`
- **Exclusions**: No optimized macro windows, no full ICT model, no event-chart features, no cost-sensitive P&L
- **Constraints**: Final 30% global holdout excluded; ATR uses values known before the window start; ONH/ONL excluded before 09:30 for sweep diagnostics

### Results / Observations

| Instrument | Segment | AdjacentMean Mean Diff | RandomControl Mean Diff | Primary Pass |
| --- | --- | ---: | ---: | --- |
| BTCUSD | Test | -0.3547 | -0.3804 | False |
| BTCUSD | Train | -0.3738 | -0.2965 | False |
| EURUSD | Test | 0.1791 | -0.0742 | False |
| EURUSD | Train | 0.0769 | -0.2910 | False |
| USTEC | Test | -0.2300 | -0.3944 | False |
| USTEC | Train | -0.5281 | -0.7439 | False |
| XAUUSD | Test | -0.0026 | -0.1532 | False |
| XAUUSD | Train | -0.1757 | -0.5790 | False |

- Supporting instruments: `0/4`.
- Macro observation date counts are adequate in train and test for all instruments.
- Macro-window sweep frequency is `0.0` for all instruments under the scoped window-level reclaim definition.

### Hypothesis-Specific Conclusion

**REFUTED**

The primary criterion required the macro-window ATR-normalized range to beat both adjacent and randomized controls on at least 3 of 4 instruments with CIs excluding zero and median effect at least `0.10 ATR`. No instrument meets that rule.

### Hypothesis-Agnostic Observations

- Fixed macro windows should not be treated as a standalone range-expansion filter under the tested control design.
- Direct sweep behavior was tested separately in EXP-015 because this H1 refutation did not test failed-breakout outcomes.
