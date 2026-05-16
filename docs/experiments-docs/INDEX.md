# Experiments Index (Comprehensive)

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
