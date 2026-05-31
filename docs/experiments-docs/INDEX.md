# Experiments Index (Comprehensive)

## Current Checkpoint Status

| Checkpoint | Status | Focus | Documents |
| --- | --- | --- | --- |
| 2026-05-31-006-thesis-qualification-referee-calibration | ACTIVE | Phase 006 refreshes Xen in place onto a new object of study: the **referee** that qualifies theses, not any market thesis. Founding thesis H1/H0 — can a qualification system's operating characteristics (FPR, a power *surface*, per-leg pass rates) be measured with enough fidelity that "reject" carries trustworthy meaning? Baseline referee under test = the existing §5.6 closure stack (transcribed/frozen from EXP-036), calibrated in two parts: EXP-037 null calibration (trustworthy FPR + per-leg leak/over-reject) and EXP-038 power bracketing (power surface + synthetic-family sensitivity = the H0/H1 verdict). Yields the §5.6 ruling + founding-thesis ruling. Holdout untouched; successor-stack design deferred; no gate loosened pre-calibration. Synthesises `docs/planning/` (problem-statement + charter + state-and-open-decisions). Immediate next artifact: Deliverable #2 (predeclared reference-stack spec). | [design.md](checkpoints/2026-05-31-006-thesis-qualification-referee-calibration/design.md) |
| 2026-05-28-005-htf-state-descriptor-differentiation | COMPLETED | Phase 005 closes the higher-timeframe state-descriptor thesis before holdout. Prior-Range Location passes readiness but fails the matched-control return gate; Market Bias is deterministic but a canonical strict readiness no-go; contingents are not activated because no directional source survived. No EXP-038 robustness path or candidate manifest exists. | [design.md](checkpoints/2026-05-28-005-htf-state-descriptor-differentiation/design.md) · [mid-phase-reflection.md](checkpoints/2026-05-28-005-htf-state-descriptor-differentiation/mid-phase-reflection.md) · [retrospective.md](checkpoints/2026-05-28-005-htf-state-descriptor-differentiation/retrospective.md) |

## Checkpoint Retrospectives

| Checkpoint | Status | Key Synthesis | Document |
| --- | --- | --- | --- |
| 2026-05-14-001-chart-type-validation | COMPLETED | Phase 1 validates time bars as the master timeline for 1-minute-source analysis; higher-timeframe robustness remains a Phase 1B bridge item before Phase 2 signal-quality characterization. | [retrospective.md](checkpoints/2026-05-14-001-chart-type-validation/retrospective.md) |
| 2026-05-16-001-signal-quality-classification | COMPLETED | Phase 2 validates the FE/AE measurement framework but refutes the event-chart signal-quality path; broad event-chart strategy exploration is not justified without a new narrower thesis. | [retrospective.md](checkpoints/2026-05-16-001-signal-quality-classification/retrospective.md) |
| 2026-05-23-003-ict-one-setup-timebar-validation | COMPLETED | Phase 003 translates the ICT setup into deterministic time-bar components, but no optional component earns full-model promotion; the broad ICT chain is blocked before holdout or robustness validation. | [retrospective.md](checkpoints/2026-05-23-003-ict-one-setup-timebar-validation/retrospective.md) |
| 2026-05-26-004-ustec-breaker-ifvg-selectivity | COMPLETED | Phase 004 closes both narrow ICT continuations: the USTEC Candidate A breaker is microstructure-sensitive (Return_R decays 1m +4.18R → 15m +1.84R → 1h +0.12R), and IFVG non-selectivity is intrinsic to the lifecycle-windowed three-candle definition (0/5 rule families pass readiness on ≥2 instruments). EURUSD sweep deferral invalidated at 15m. No candidate manifest; holdout intact. Closes the ICT-as-alpha thesis; Phase 005 should start from a new thesis. | [retrospective.md](checkpoints/2026-05-26-004-ustec-breaker-ifvg-selectivity/retrospective.md) |
| 2026-05-28-005-htf-state-descriptor-differentiation | COMPLETED | Phase 005 closes the higher-timeframe state-descriptor thesis: Prior-Range Location was count-eligible but failed replicated neutral-plus-control return differentiation, Market Bias failed canonical strict episode readiness, contingents were not activated, and no robustness path or candidate manifest exists. Holdout intact. | [retrospective.md](checkpoints/2026-05-28-005-htf-state-descriptor-differentiation/retrospective.md) |


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

## EXP-016 - Macro Window Interaction With Sweep Outcomes

**Status**: INCONCLUSIVE
**Date**: 2026-05-25
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: 1-minute Time Bars, NY Macro Windows, Liquidity Sweeps

### Hypothesis Tests

1. **Hypothesis**: Sweep outcomes inside predefined macro windows are materially different from sweep outcomes outside macro windows after accounting for event count and instrument coverage.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: EXP-012 macro-window labels; EXP-015 first-touch PDH/PDL and ONH/ONL sweep events; real-price 60-minute outcomes
- **Features**: `InMacro`, `MacroWindow`, `EventType`, `Side`, `Risk1R`, `Hit1R_60m`, `MAE_R_60m`, matched outside-window controls by instrument/segment/side/NY date
- **Parameter ranges**: Macro windows AM1-AM5 and PM1-PM4; buffer `max(price_precision_step, 0.05 * ATR14Prior)`; 60-minute 1R-before-stop probability and median MAE
- **Exclusions**: No full ICT model, no premium/discount filter, no displacement, no IFVG, no breaker, no event-chart features, no tick or bid/ask data
- **Constraints**: Final 30% global holdout excluded; all outcomes use real 1-minute OHLC prices; support requires at least 50 inside-window sweeps and 50 matched outside-window comparator events per train/test segment

### Results / Observations

Test-segment matched comparison coverage:

| Instrument | Inside Sweeps | All Outside Sweeps | Matched Outside Sweeps | Matched Fraction |
| --- | ---: | ---: | ---: | ---: |
| EURUSD | 24 | 65 | 2 | 3.1% |
| XAUUSD | 27 | 104 | 4 | 3.8% |
| BTCUSD | 21 | 72 | 1 | 1.4% |
| USTEC | 34 | 126 | 12 | 9.5% |

- Instruments meeting train/test inside and matched-outside floors: `0/4`.
- All primary threshold-pass flags are false after applying the event/comparator floors.
- USTEC Test raw HitDiff is `+0.237`, CI `[-0.081, 0.525]`, but the row is non-evaluable because event floors fail.
- BTCUSD Test has no non-ambiguous matched outside hit observations.

### Hypothesis-Specific Conclusion

**INCONCLUSIVE**

The matched macro-context comparison cannot evaluate the hypothesis because no instrument meets the required train/test inside and matched-outside event floors. EXP-016 therefore provides no support or refutation for macro-window filtering of sweep outcomes.

### Hypothesis-Agnostic Observations

- Combining narrow fixed macro windows with same-day, same-side matched outside controls is too sparse under the current sweep definition.
- Macro-window context should not be promoted as a required filter from EXP-016.
- Later ICT component experiments should continue as separate component tests; a future macro-context rerun would need a new predeclared control design.

---

## EXP-017 - Premium Discount Filter Impact on Sweep Quality

**Status**: INCONCLUSIVE
**Date**: 2026-05-25
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: 1-minute Time Bars, Prior-Day Midpoint, Liquidity Sweeps

### Hypothesis Tests

1. **Hypothesis**: A previous-day midpoint premium/discount filter improves sweep quality enough to justify the sample-size cost.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: EXP-014 prior-day midpoint derived from `PDH`/`PDL`; EXP-015 first-touch sweep events; real-price 60-minute outcomes
- **Features**: `Midpoint`, `PassMidpointFilter`, `Hit1R_60m`, `MAE_R_60m`, retention by side and segment
- **Parameter ranges**: High-side sweeps require `Close > midpoint`; low-side sweeps require `Close < midpoint`; unchanged EXP-015 stop/risk/horizon definitions
- **Exclusions**: No VWAP or distance-from-open filters, no macro filter, no displacement, no IFVG, no breaker, no event-chart features
- **Constraints**: Final 30% global holdout excluded through approved prerequisite artifacts; outcomes use real 1-minute prices inherited from EXP-015

### Results / Observations

Test-segment primary effects (`filtered - all sweeps`):

| Instrument | Retention | Hit Diff | 95% CI | Median MAE Improvement | 95% CI |
| --- | ---: | ---: | --- | ---: | --- |
| EURUSD | 84/89 = 94.4% | -0.007 | [-0.029, 0.015] | -0.086R | [-0.785, 0.640] |
| XAUUSD | 121/131 = 92.4% | -0.001 | [-0.026, 0.024] | 0.000R | [-0.885, 0.378] |
| BTCUSD | 89/93 = 95.7% | -0.014 | [-0.041, 0.008] | +0.052R | [-0.073, 0.354] |
| USTEC | 138/160 = 86.2% | -0.036 | [-0.072, -0.004] | +0.185R | [-0.672, 0.591] |

- Instruments passing support thresholds: `0/4`.
- Instruments meeting retention floors: `4/4`.

### Hypothesis-Specific Conclusion

**INCONCLUSIVE**

The midpoint filter does not achieve the predeclared support rule on any instrument, but the result is better described as inconclusive than cleanly negative because retention is high and several MAE intervals remain wide rather than decisively harmful.

### Hypothesis-Agnostic Observations

- The midpoint rule is a low-cost filter in this dataset, not a high-value one.
- USTEC is the clearest negative case because test hit rate worsens while retention remains high.
- Any future location-filter work should test one tighter rule at a time rather than expanding the filter family inside this scope.

---

## EXP-018 - Displacement Confirmation Added to Sweeps

**Status**: INCONCLUSIVE
**Date**: 2026-05-25
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: 1-minute Time Bars, Liquidity Sweeps, Displacement Confirmation

### Hypothesis Tests

1. **Hypothesis**: Adding a deterministic displacement candle after a sweep improves sweep-only outcomes enough to offset delayed confirmation and fewer signals.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: EXP-015 sweep events; 1-minute candle-body displacement confirmation; real-price 60-minute outcomes
- **Features**: `BodyMedian100Prior`, close-location quartile, `DelayBars`, `Hit1R_60m`, `Return_R_60m`, `MAE_R_60m`
- **Parameter ranges**: First confirming candle within 10 bars; body size `>= 1.5x` prior 100-bar median absolute body; entry proxies `SweepClose`, `DisplacementClose`, `NextOpen`
- **Exclusions**: No swing-break logic, no IFVG/breaker logic, no full ICT model, no event-chart features
- **Constraints**: Final 30% global holdout excluded; all outcomes use real 1-minute OHLC prices

### Results / Observations

Test-segment confirmed-versus-all-sweep effects:

| Instrument | Confirmed Retention | Hit Diff | 95% CI | Median MAE Improvement | 95% CI |
| --- | ---: | ---: | --- | ---: | --- |
| EURUSD | 77/89 = 86.5% | +0.023 | [-0.018, 0.068] | +0.405R | [-0.365, 1.361] |
| XAUUSD | 112/131 = 85.5% | +0.024 | [-0.013, 0.063] | +0.345R | [-0.000, 1.128] |
| BTCUSD | 81/93 = 87.1% | +0.027 | [-0.012, 0.068] | +0.052R | [-0.326, 0.466] |
| USTEC | 132/160 = 82.5% | +0.001 | [-0.036, 0.039] | +0.404R | [-0.164, 1.180] |

- Instruments passing support thresholds: `0/4`.
- Instruments refuting on both metrics: `0/4`.
- Paired delay-cost diagnostic is negative on EURUSD and XAUUSD test when comparing `DisplacementClose` to `SweepClose`.

### Hypothesis-Specific Conclusion

**INCONCLUSIVE**

The displacement-confirmed subset sometimes looks slightly cleaner than the full sweep population, but no test interval clears the predeclared support bar and the paired delay-cost diagnostic is often negative. The evidence does not justify promoting displacement confirmation as a validated improvement.

### Hypothesis-Agnostic Observations

- Displacement confirmation preserves most sweeps, so the failure is not a sample-collapse problem.
- Waiting for confirmation can consume much of any quality gain the filter appears to create.
- H3 should be interpreted jointly with EXP-019 rather than assuming displacement is the default confirmation path.

---

## EXP-019 - Micro Swing Break Confirmation After Sweep

**Status**: INCONCLUSIVE
**Date**: 2026-05-25
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: 1-minute Time Bars, Liquidity Sweeps, Causal Swing Breaks

### Hypothesis Tests

1. **Hypothesis**: A micro swing break after a sweep improves signal quality beyond the simpler displacement definition.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: EXP-015 sweep events; two-left/two-right causal swing pivots; comparison to EXP-018 displacement baseline
- **Features**: `SwingPrice`, `SwingUsableTime`, `BreakTime`, `DelayBars`, `Return_R_60m`, `MAE_R_60m`, matched paired effects
- **Parameter ranges**: High-side sweeps require a later close below the latest usable swing low; low-side sweeps require a later close above the latest usable swing high
- **Exclusions**: No candle/body displacement combination, no IFVG/breaker logic, no event-chart features, no full ICT model
- **Constraints**: Final 30% global holdout excluded; all outcomes use real 1-minute OHLC prices; support requires `>= 50` matched test events and no excessive median delay

### Results / Observations

Test-segment paired effects versus EXP-018 displacement:

| Instrument | Matched N | Return Diff | 95% CI | Median MAE Improvement | 95% CI |
| --- | ---: | ---: | --- | ---: | --- |
| EURUSD | 77 | +0.252R | [-7.542, 7.186] | +0.114R | [-0.097, 0.276] |
| XAUUSD | 112 | +0.630R | [-16.675, 16.508] | +0.404R | [0.022, 0.642] |
| BTCUSD | 81 | +1.477R | [-4.050, 9.390] | +0.157R | [0.000, 0.471] |
| USTEC | 132 | +18.153R | [-4.762, 58.643] | +0.597R | [0.186, 1.076] |

- Instruments passing support thresholds: `0/4`.
- Instruments refuting on both metrics: `0/4`.
- Instruments flagged for excessive median delay: `0/4`.
- Audit note: one confirmed BTCUSD cross-segment case is grouped under the sweep segment, but the measured effect on the verdict is immaterial.

### Hypothesis-Specific Conclusion

**INCONCLUSIVE**

The causal swing-break variant is reproducible and keeps adequate counts, but it does not show a validated improvement over EXP-018 displacement on the predeclared interval-based criteria. The evidence is positive in places, especially on MAE, but not strong enough to support the hypothesis.

### Hypothesis-Agnostic Observations

- Causal swing confirmation is operationally feasible on this dataset; sparsity and excessive delay are not the blocking issues.
- The main problem is uncertainty: the paired intervals are too wide to justify promotion of the variant.
- H3 remains unresolved after both completed confirmation variants.

---

## EXP-020 - FVG IFVG Detection Reproducibility

**Status**: INCONCLUSIVE
**Date**: 2026-05-25
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: 1-minute Time Bars, FVG Zones, IFVG Lifecycle

### Hypothesis Tests

1. **Hypothesis**: Three-candle FVGs and close-through IFVG inversions can be detected reproducibly with stable sample sizes on available time bars.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: Three-candle FVG detection, 120-bar lifecycle tracking, IFVG close-through inversion
- **Features**: `FVGSize`, `ATR14Prior`, `LifecycleState`, `IsIFVG`, reproducibility digests, count/readiness flags
- **Parameter ranges**: Bearish `High[i] < Low[i-2]`; bullish `Low[i] > High[i-2]`; minimum size `max(price_precision_step, 0.02 * ATR14Prior)`; lifecycle `120` bars
- **Exclusions**: No profitability claims, no sweep/entry linkage, no event-chart features, no parameter tuning inside this scope
- **Constraints**: Final 30% global holdout excluded; IFVG readiness requires both count floors and a non-tautological inversion rate

### Results / Observations

- Reproducibility checks pass on `4/4` instruments: fresh reload and shuffled-resort digests all match first-pass digests.
- Every instrument and segment exceeds the count floors by large margins.
- IFVG rates are uniformly high:
  - EURUSD Train/Test: `0.851` / `0.853`
  - XAUUSD Train/Test: `0.852` / `0.852`
  - BTCUSD Train/Test: `0.851` / `0.852`
  - USTEC Train/Test: `0.843` / `0.842`
- All `ReadyForIFVGStudy` flags are `False` because every row is tautological under the predeclared `IFVGRate >= 0.50` gate.

### Hypothesis-Specific Conclusion

**INCONCLUSIVE**

The experiment supports the narrow mechanical claim that FVG/IFVG detection is deterministic and abundant, but it does not clear the downstream readiness gate for IFVG-entry studies. Under the current rule set, inversion happens too often to serve as a selective confirmation event.

### Hypothesis-Agnostic Observations

- The detector itself is usable; the selectivity problem is conceptual rather than mechanical.
- EXP-021 should not proceed unchanged because its prerequisite confirmation event is not discriminating enough.
- Any IFVG follow-up must tighten one explicit parameter or lifecycle rule in a fresh scope.


## EXP-021 - IFVG Confirmation Entry Quality

**Status**: REFUTED
**Date**: 2026-05-26
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: 1-minute Time Bars, Sweep and Displacement Event Chains, IFVG Confirmation Timing

### Hypothesis Tests

1. **Hypothesis**: IFVG confirmation improves entry quality enough to offset later entry timing and fewer signals.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: EXP-015 sweep events, EXP-018 displacement prerequisite, EXP-020 IFVG confirmation, fixed entry timestamps
- **Features**: sweep-close, displacement-close, IFVG-close, second-candle-open outcomes; feasible-risk counts; bootstrap expectancy, drawdown-adjusted return, MAE, and hit-rate diagnostics
- **Parameter ranges**: 60-minute outcome horizon; IFVG side follows sweep side; feasible delayed-entry risk requires `Risk1R >= EXP-015 Buffer`; event floor `>= 50` feasible IFVG events per train/test segment
- **Exclusions**: No retest unless predeclared, no alternative IFVG rule, no post-hoc confirmation redesign inside this scope
- **Constraints**: Final 30% global holdout excluded; real-price outcome discipline; infeasible delayed-entry rows remain in chain counts but not in R-based summaries

### Results / Observations

- The rerun resolves the denominator-collapse issue cleanly:
  - `53 / 6030` delayed-entry rows are flagged `RiskFeasible=False`
  - all infeasible rows have null R-based outcomes
  - feasible `Return_R_60m` values range from `-288.0000` to `276.8245`
- IFVG confirmation retains almost the full displacement set:
  - counts are identical on `7/8` displacement-to-IFVG rows
  - BTCUSD Train is the only drop, from `345` to `344`
- Every instrument still clears the feasible-event floor in both train and test:
  - EURUSD `208 / 75`
  - XAUUSD `240 / 109`
  - BTCUSD `342 / 81`
  - USTEC `305 / 130`
- The stored verdict is `AGAINST`, with `0/4` instruments passing the predeclared support rule.

### Hypothesis-Specific Conclusion

**REFUTED**

After the feasible-risk guard is applied, IFVG confirmation still fails to improve test-segment return or drawdown-adjusted quality against both simpler baselines on any instrument. The broad H4 claim is therefore refuted under the frozen IFVG rule set.

### Hypothesis-Agnostic Observations

- The rerun changed trust, not direction: the negative result persists after the normalization fix.
- The near-perfect displacement-to-IFVG retention reinforces EXP-020's concern that the current IFVG rule is not very selective.
- Any future IFVG work should start by redefining the prerequisite confirmation event, not by reinterpreting this result.

---

---

## EXP-022 - Objective Breaker Candidate Reproducibility

**Status**: SUPPORTED
**Date**: 2026-05-26
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: 1-minute Time Bars, Displacement-Confirmed Sweeps, Breaker Candidate Definitions

### Hypothesis Tests

1. **Hypothesis**: At least one objective breaker candidate can be defined reproducibly with enough occurrences to justify outcome testing.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: Candidate A last-opposite-candle order-block proxy; Candidate B causal swing-break breaker
- **Features**: post-displacement breaker boundary, confirmation timestamp, invalidation reason, ambiguity count, retention rate, reproducibility digests
- **Parameter ranges**: Candidate A lookback `30` bars; Candidate B swing window `2` bars left/right; confirmation delay cap `120` bars; readiness floor `>= 50` events per instrument-segment
- **Exclusions**: No profitability or trade-quality comparison, no post-hoc candidate selection by outcomes, no event-chart features
- **Constraints**: Final 30% global holdout excluded; candidate selection based on deterministic rerun equality, occurrence floors, and ambiguity only

### Results / Observations

- Both candidates are reproducible on `4/4` instruments; fresh-reload and second-pass digests match for every instrument.
- Candidate A clears the train/test floor in every instrument-segment:
  - EURUSD `140 / 54`
  - XAUUSD `172 / 79`
  - BTCUSD `239 / 66`
  - USTEC `205 / 86`
- Candidate B clears all train floors but misses the test floor on EURUSD and BTCUSD:
  - EURUSD `99 / 40`
  - XAUUSD `119 / 55`
  - BTCUSD `181 / 49`
  - USTEC `151 / 58`
- Ambiguity is `0` for every candidate, instrument, and segment row.
- `selection.json` records `CandidateA` as the only eligible candidate.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The scoped readiness criterion is satisfied because Candidate A is deterministic and clears the `>= 50` event floor in both train and test on all four instruments. Candidate B remains reproducible but does not qualify broadly enough for the downstream outcome test.

### Hypothesis-Agnostic Observations

- The blocker for Candidate B is sample availability, not ambiguity or nondeterminism.
- EXP-023 later used Candidate A exactly as scoped, but the completed outcome test still failed broad cross-instrument support.

---


## EXP-023 - Breaker Confirmation Trade Quality

**Status**: REFUTED
**Date**: 2026-05-26
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: 1-minute Time Bars, Displacement Baseline, Candidate A Breaker Confirmation

### Hypothesis Tests

1. **Hypothesis**: One objective breaker confirmation improves trade quality beyond a predeclared pre-breaker baseline.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: EXP-018 displacement baseline, EXP-022 Candidate A breaker confirmation
- **Features**: baseline-to-breaker waterfall, feasible-risk counts, R-based expectancy, drawdown-adjusted return, MAE, hit rate, bootstrap contribution tables
- **Parameter ranges**: 60-minute outcome horizon; Candidate A only; feasible delayed-entry risk requires `Risk1R >= EXP-015 Buffer`; event floor `>= 50` feasible breaker events per train/test segment
- **Exclusions**: No alternative breaker definitions, no post-hoc baseline switching, no event-chart features
- **Constraints**: Final 30% global holdout excluded; real-price outcome discipline; infeasible rows remain in retention diagnostics but not in R-based summaries

### Results / Observations

- The rerun resolves the prior denominator issue:
  - `24 / 2549` rows are flagged `RiskFeasible=False`
  - all infeasible rows have null R-based outcomes
  - feasible `Return_R_60m` values range from `-148.8444` to `106.9811`
- Candidate A remains operationally broad enough for testing:
  - EURUSD `140 / 54`
  - XAUUSD `172 / 79`
  - BTCUSD `239 / 66`
  - USTEC `205 / 86`
- Duplicate join keys remain `0` on every baseline-to-breaker row.
- The stored verdict is `AGAINST`, with `1/4` instruments passing the predeclared support rule; USTEC is the lone clean pass.

### Hypothesis-Specific Conclusion

**REFUTED**

Breaker confirmation under the fixed Candidate A definition does not deliver the broad cross-instrument quality improvement required by the scope. Event floors are met everywhere, but only USTEC passes the return / drawdown / MAE gate.

### Hypothesis-Agnostic Observations

- EXP-022's readiness result still matters: Candidate A is real, deterministic, and count-eligible.
- The main consistent effect is better trade path control on some instruments, not broad expectancy improvement.
- Any future breaker work should be explicitly narrower rather than assuming the current cross-instrument claim survived.

---

## EXP-024 - Second Candle Open Execution Timing

**Status**: SUPPORTED
**Date**: 2026-05-26
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: 1-minute Time Bars, IFVG Confirmation Events, Post-Confirmation Entry Timing Variants

### Hypothesis Tests

1. **Hypothesis**: The ICT second-candle-open execution rule has equal or better trade quality than simpler post-confirmation entries.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: confirmation-close, immediate-next-open, second-candle-open, first deterministic retest
- **Features**: feasible-risk counts, R-based expectancy, MAE, hit rate, slippage proxy, bootstrap timing comparisons, missing-forward-bars diagnostics
- **Parameter ranges**: 60-minute outcome horizon; feasible timing risk requires inherited `Risk1R >= MinRisk1R` from EXP-021; support floor `>= 50` feasible confirmation-close and second-candle-open rows per train/test segment
- **Exclusions**: No new confirmation filter, no alternative risk anchor, no cost model
- **Constraints**: Final 30% global holdout excluded; real-price outcome discipline; infeasible rows remain in timing diagnostics but not in R-based or slippage summaries

### Results / Observations

- The rerun resolves the timing denominator issue:
  - `61 / 5526` rows are flagged `RiskFeasible=False`
  - all infeasible rows have null R-based outcomes and null `Slippage_R`
  - `missing_forward_bars.csv` reports `0` missing-forward-bar cases everywhere
- Every instrument clears the feasible-count gate for both confirmation-close and second-candle-open in train and test:
  - EURUSD `208 / 212` train, `75 / 76` test
  - XAUUSD `240 / 241` train, `109 / 111` test
  - BTCUSD `342 / 341` train, `81 / 81` test
  - USTEC `305 / 301` train, `130 / 131` test
- The stored verdict is `FOR`, with `4/4` instruments passing the predeclared non-inferiority rule versus confirmation-close.

### Hypothesis-Specific Conclusion

**SUPPORTED**

Second-candle-open satisfies the scoped timing criterion: across all four instruments, it does not show statistically worse return, MAE, or slippage than confirmation-close once the feasible-risk guard is enforced.

### Hypothesis-Agnostic Observations

- This is a narrow positive result: the support comes from preservation, not from a universal point-estimate improvement.
- Hit-rate differences remain small and statistically unresolved.
- The result isolates timing only and does not rehabilitate the refuted EXP-021 IFVG confirmation layer.

---

## EXP-025 - Fixed 1 to 2 Risk Reward Justification

**Status**: INCONCLUSIVE
**Date**: 2026-05-26
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: 1-minute Time Bars, EXP-024 Second-Candle-Open Entries, Alternative Exit Variants

### Hypothesis Tests

1. **Hypothesis**: A fixed `2R` target is justified only if it outperforms simpler target and exit alternatives for the approved entry definition.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: EXP-024 second-candle-open entries, inherited stop anchors, `1R`, `1.5R`, `2R`, `3R`, `TimeStop60`, and `NearestLiquidity` exits
- **Features**: exit outcome table, realized-R summaries, hit rates, bootstrap `2R` versus alternative comparisons
- **Parameter ranges**: 60-minute outcome horizon; event floors `>= 100` train and `>= 50` test per instrument; real-price OHLC path only
- **Exclusions**: no new entry filters, no stop retuning, no event-chart features, no cost model
- **Constraints**: Final 30% global holdout excluded; real-price outcome discipline; comparator coverage required before interpretation

### Results / Observations

- All four instruments are fully comparable in the test segment:
  - EURUSD `N_2R=70`
  - XAUUSD `N_2R=100`
  - BTCUSD `N_2R=77`
  - USTEC `N_2R=125`
- The stored verdict records `0/4` passing instruments and `0/4` dominated instruments.
- Representative bootstrap rows:
  - EURUSD `2R vs 1R`: diff `-0.356`, CI `[-0.950, 0.229]`
  - XAUUSD `2R vs TimeStop60`: diff `-0.707`, CI `[-2.318, 0.981]`
- Test mean returns show weaker point estimates for `2R` than `TimeStop60` on all four instruments:
  - EURUSD `-0.815R` vs `-0.297R`
  - XAUUSD `-0.810R` vs `-0.092R`
  - BTCUSD `-0.474R` vs `-0.257R`
  - USTEC `-0.918R` vs `-0.233R`

### Hypothesis-Specific Conclusion

**INCONCLUSIVE**

The broad H6 claim is not supported, but it is not formally refuted by the experiment's own domination rule either. `2R` shows no superiority evidence on any instrument despite full comparator coverage, so it is not positively justified for this entry source.

### Hypothesis-Agnostic Observations

- The result is evidence-based rather than sample-limited: all four instruments clear the comparison floor.
- `RiskModel_2R` should not be promoted into downstream candidate selection under the current chain.

---

## EXP-026 - Incremental ICT Component Ablation

**Status**: INCONCLUSIVE
**Date**: 2026-05-26
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: Prior ICT Experiment Outputs, Fixed-Order Component Chain, Bootstrap Contribution Gate

### Hypothesis Tests

1. **Hypothesis**: Validated ICT components contribute measurable net value when combined incrementally, after accounting for sample-size loss.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: sweep baseline, macro filter, premium/discount filter, displacement, IFVG, breaker, second-candle-open execution rule, `2R` risk model
- **Features**: component eligibility matrix, fixed-order chain-step counts, proxy expectancy, mean return, marginal bootstrap intervals, frozen manifest selection
- **Parameter ranges**: fixed chain order from Step 1 Sweep through Step 8 `Disp+SCO+2R`; candidate promotion requires positive Test `MeanDiff` and `CI_Lo > 0`
- **Exclusions**: no new component variants, no reordered chain, no event-chart features
- **Constraints**: Final 30% global holdout excluded through inherited upstream artifacts; downstream promotion allowed only for manifest-eligible components

### Results / Observations

- The chain is populated rather than empty:
  - Sweep Test counts: EURUSD `84`, XAUUSD `116`, BTCUSD `86`, USTEC `144`
  - Displacement Test counts: EURUSD `72`, XAUUSD `105`, BTCUSD `71`, USTEC `115`
- `bootstrap_marginal.csv` contains `0` Test rows with both `MeanDiff > 0` and `CI_Lo > 0`.
- Step 7 (`Disp+SCO`) Test rows are negative in point estimate on all four instruments:
  - EURUSD `-0.419`, CI `[-1.387, 0.539]`
  - XAUUSD `-0.121`, CI `[-1.578, 1.294]`
  - BTCUSD `-0.984`, CI `[-2.564, 0.488]`
  - USTEC `-0.101`, CI `[-1.515, 1.238]`
- `model_manifest.json` records `selected_components = ["Sweep", "Displacement"]` and `candidate_eligible = false`.

### Hypothesis-Specific Conclusion

**INCONCLUSIVE**

The ablation chain can be measured, but no optional component adds enough robust cross-instrument evidence to justify promotion into a full-model candidate. The phase therefore stops at the baseline pair rather than producing a model-ready chain.

### Hypothesis-Agnostic Observations

- The current phase has a measurable baseline (`Sweep + Displacement`) but no promoted optional layer.
- The blocker is contribution quality, not missing infrastructure or zero event counts.

---

## EXP-027 - Predeclared Full ICT Model Analysis-Set Test

**Status**: INCONCLUSIVE
**Date**: 2026-05-26
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: EXP-026 Frozen Model Manifest Gate

### Hypothesis Tests

1. **Hypothesis**: The best predeclared full-model variant survives analysis-set testing only if the upstream ablation produces an eligible candidate first.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: EXP-026 model manifest, gated full-model test contract
- **Features**: manifest eligibility check, model-verdict payload, early-exit result contract
- **Parameter ranges**: no downstream trade-performance evaluation unless `candidate_eligible = true`
- **Exclusions**: no post-hoc candidate promotion, no fallback full-model run, no event-chart features
- **Constraints**: full-model stage must stop when the upstream ablation gate fails

### Results / Observations

- The embedded EXP-026 manifest records:
  - `selected_components = ["Sweep", "Displacement"]`
  - `candidate_eligible = false`
  - `source_verdict = "INCONCLUSIVE"`
- `results.json` records:
  - `criteria = {"ManifestEligible": false}`
  - `reason = "EXP-026 manifest did not identify an eligible full-model candidate."`
  - `per_instrument = []`
- Current valid outputs are the short gate contract only:
  - `results.json`
  - `model_verdict.json`
  - `numerical_summary.txt`

### Hypothesis-Specific Conclusion

**INCONCLUSIVE**

The full-model test never legitimately starts because no eligible candidate exists to test. This is a blocked stage outcome, not a model-performance failure.

### Hypothesis-Agnostic Observations

- The phase respected the ablation gate instead of manufacturing a downstream full-model run from an ineligible manifest.

---

## EXP-028 - ICT Candidate Robustness and Falsification

**Status**: INCONCLUSIVE
**Date**: 2026-05-26
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Feature Categories**: EXP-027 Candidate Gate, Robustness/Falsification Contract

### Hypothesis Tests

1. **Hypothesis**: A candidate ICT variant is robust only if it first survives the EXP-027 eligibility gate and then remains defensible under the predeclared segment, delay, and cost stresses.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Feature Categories**: EXP-027 candidate gate, robustness contract for segment, delay, and cost stress
- **Features**: upstream verdict check, early-exit robustness payload
- **Parameter ranges**: no robustness calculations unless EXP-027 supplies an eligible candidate
- **Exclusions**: no candidate rescue path, no segment-specific model redesign, no event-chart features
- **Constraints**: robustness is a falsification stage only after eligibility

### Results / Observations

- `results.json` records:
  - `verdict = "INCONCLUSIVE"`
  - `reason = "EXP-027 candidate is not eligible for robustness checks (verdict=INCONCLUSIVE)."`
  - `output_contract = "early_inconclusive_no_robustness_outputs"`
- The only valid outputs are:
  - `results.json`
  - `numerical_summary.txt`
- No segment, delay-stress, cost-stress, robustness-summary, or plot artifacts are present.

### Hypothesis-Specific Conclusion

**INCONCLUSIVE**

The robustness question is unreachable because EXP-027 never produced a candidate eligible for falsification. This is an unopened stage, not a failed robustness test.

### Hypothesis-Agnostic Observations

- The pipeline kept the robustness artifact contract honest about what did and did not run.

---

## EXP-029 — 15-Minute FVG IFVG Selectivity Check

**Status**: REFUTED
**Date**: 2026-05-27
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Phase**: 004A Pre-Phase

### Hypothesis Tests

1. **Hypothesis**: Applying the EXP-020 three-candle FVG and 120-bar close-through IFVG rules unchanged to synthetic 15-minute bars produces an IFVG inversion rate materially below the Phase 003 1-minute baseline of 84–85% on at least two of four instruments.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Data**: 1-minute analysis-set bars (holdout excluded before aggregation) resampled to synthetic 15-minute OHLC via `python/src/bar_aggregator.py`
- **Features**: IFVG inversion rate (120-bar primary, 8-bar sensitivity), FVG/IFVG counts, SHA-256 reproducibility digests, block bootstrap (n=2,000, block=50)
- **Lifecycle windows**: 120 15-minute bars (direct EXP-020 transfer); 8 15-minute bars (≈120-minute elapsed, lifecycle sensitivity)
- **Exclusions**: no return outcomes, no rule redesign, no parameter tuning, no chart-type features

### Results / Observations

Primary 120-bar IFVG inversion rate by instrument (combined train/test):

| Instrument | IFVGRate | Bootstrap 95% CI | Near 1m Baseline? |
|------------|----------|-----------------|-------------------|
| EURUSD | 0.854 | [0.846, 0.865] | YES |
| XAUUSD | 0.836 | [0.825, 0.846] | YES |
| BTCUSD | 0.832 | [0.823, 0.842] | YES |
| USTEC | 0.848 | [0.837, 0.859] | YES |

8-bar lifecycle sensitivity rates: 0.454–0.479 across all instruments (≈38pp below 120-bar rates).

FVG counts: 3,391–9,283 per segment. All count floors met. Detection fully reproducible on all 4 instruments.

### Hypothesis-Specific Conclusion

**REFUTED**

The 120-bar IFVG inversion rate at 15-minute resolution replicates the Phase 003 1-minute baseline within 2pp on all four instruments. The FOR criterion (rate < 50% on ≥ 2 instruments) is not met; the AGAINST criterion (rate near baseline on ≥ 3 instruments) is met.

### Hypothesis-Agnostic Observations

- The ~38pp gap between 120-bar (83–86%) and 8-bar (45–48%) rates is consistent across all four instruments, confirming that lifecycle window duration — not FVG rule permissiveness — drives the high inversion rate.
- Timeframe change alone does not solve IFVG selectivity; Branch B must pursue a rule-level redesign (shorter lifecycle or stricter qualification).
- `python/src/bar_aggregator.py` is a new shared module providing deterministic clock-aligned OHLC resampling, reused by EXP-030 and EXP-031.

---

## EXP-030 — 15-Minute Sweep Reversal Behavior

**Status**: INCONCLUSIVE
**Date**: 2026-05-27
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Phase**: 004A Pre-Phase

### Hypothesis Tests

1. **Hypothesis**: First-touch PDH/PDL/ONH/ONL failed-breakout sweeps detected on synthetic 15-minute bars show measurably different or stronger opposite-direction behavior versus non-failed breaches than the EXP-015 1-minute baseline, on at least one of four instruments.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Data**: Synthetic 15-minute OHLC for sweep/breach detection; real 1-minute prices for all outcomes
- **Features**: Sweep/breach first-touch events per NYDate, 1R-before-stop probability at 30/60/120 minutes (primary: 60m), MAE_R, MFE_R, Return_R
- **Levels**: PDH/PDL/ONH/ONL inherited from EXP-014 (resolution-independent)
- **Buffer**: `max(price_precision_step, 0.05 × ATR_14_15m)`
- **Exclusions**: no ICT model, no filters, no parameter tuning against outcomes

### Results / Observations

Primary sweep-minus-breach Hit1R_60m (test segment):

| Instrument | EXP-030 Test Diff | 95% CI | EXP-015 1m Test | Direction Change |
|------------|------------------|--------|----------------|-----------------|
| EURUSD | −0.145 | [−0.255, −0.036] | +0.134 [+0.001, +0.267] | **REVERSED** |
| XAUUSD | +0.011 | [−0.101, +0.122] | −0.029 [−0.151, +0.095] | No (near zero) |
| BTCUSD | −0.154 | [−0.266, −0.047] | −0.117 [−0.250, +0.018] | No (consistent) |
| USTEC | +0.046 | [−0.057, +0.149] | +0.048 [−0.063, +0.160] | No (stable null) |

All 8 instrument-segment floors (≥100 sweep events) met. Verdict is INCONCLUSIVE by criteria; no new positive instrument; EURUSD does not replicate.

### Hypothesis-Specific Conclusion

**INCONCLUSIVE**

No instrument shows a new positive sweep advantage at 15-minute resolution, and the EXP-015 EURUSD partial positive reverses direction. BTCUSD and EURUSD sweeps consistently underperform breaches with CIs excluding zero negatively. XAUUSD and USTEC remain null at both resolutions.

### Hypothesis-Agnostic Observations

- The EURUSD reversal is a resolution-timing artefact: the 15-minute confirmation bar incorporates the post-sweep reversal price action within its body, compressing the outcome window.
- BTCUSD shows the most consistent signal (both segments negative, CIs excluding zero), suggesting sweeps are structurally weaker than breaches at 15-minute resolution.
- USTEC and XAUUSD results are stable across timeframes — neither shows sweep behavior at any tested resolution.
- The EURUSD deferred positive from Phase 003 is functionally closed at 15-minute resolution; any future sweep work must address resolution-timing explicitly.

---

## EXP-031 — 15-Minute USTEC Breaker Chain

**Status**: INCONCLUSIVE
**Date**: 2026-05-27
**Instruments**: USTEC only
**Phase**: 004A Pre-Phase

### Hypothesis Tests

1. **Hypothesis**: The EXP-022 Candidate A breaker confirmation applied to USTEC sweep-plus-displacement events detected on synthetic 15-minute bars improves trade-quality expectancy versus the displacement-only baseline at a magnitude comparable to or stronger than the EXP-023 1-minute USTEC point estimate.

### Scope

- **Instruments**: USTEC only
- **Data**: Synthetic 15-minute OHLC for detection chain; real 1-minute prices for outcomes
- **Chain**: EXP-015 sweep → EXP-018 displacement (1.5× body median, close-location) → EXP-022 Candidate A (last opposite candle OB, first close-through within 120 bars)
- **Entry**: Displacement-close at 15-minute resolution (canonical EXP-023 timing)
- **Outcomes**: Return_R, MAE_R, MFE_R, Hit1R at 60 minutes on real 1-minute prices
- **Exclusions**: no second-candle-open, no segmentation, no cost stress, no Candidate B

### Results / Observations

Event waterfall: Sweep 399/145 → Displacement 339/124 → Breaker 224/79 → Feasible 219/78 (train/test).
Retention vs EXP-023 1m: ratio 1.059 (15m finds slightly more events). Both floors met.

Primary bootstrap (breaker minus baseline Return_R_60m):

| Segment | Baseline | Breaker | Diff | 95% CI | EXP-023 Ref | ≥ 50% of EXP-023 |
|---------|---------|---------|------|--------|------------|-----------------|
| Train | −0.003R | +0.514R | +0.517R | [+0.235, +0.837] | +0.334R | YES |
| Test | +0.583R | +2.418R | +1.836R | [+0.560, +3.636] | +4.176R | NO (44%) |

MAE reduction: Train −0.679R [−1.093, −0.296]; Test −1.331R [−2.629, −0.165]. Both CIs exclude zero.

### Hypothesis-Specific Conclusion

**INCONCLUSIVE** (TEST_POSITIVE_BUT_BELOW_EXP023_50PCT_REFERENCE_BAND)

Both train and test CIs exclude zero positively. Direction is consistent with EXP-023. The test magnitude (1.84R) is at 44% of EXP-023's test point (4.18R), narrowly below the predeclared 50% comparability threshold. The FOR criterion is not met; the AGAINST criterion is not triggered (no sign reversal). Verdict is INCONCLUSIVE.

### Hypothesis-Agnostic Observations

- The USTEC Candidate A breaker positive is directionally preserved at 15-minute resolution. The Phase 003 local positive is not a 1-minute resolution artifact.
- The 15-minute train CI [0.235, 0.837] is sharper and more definitively positive than EXP-023's 1-minute train CI [−1.085, 1.795].
- MAE reduction is the most structurally coherent finding: the breaker selects events with approximately half the drawdown of the displacement baseline (both segments, CIs excluding zero).
- EXP-023's test point (4.18R) was itself an imprecise estimate (wide CI [0.07, 8.88]); the 44% vs 50% distinction may not be practically meaningful.
- Phase 004B Branch A (USTEC breaker) was supported to proceed after EXP-031, but this directive is superseded by EXP-032 and the amended reflection: Branch A is now closed with no candidate manifest.

---

## EXP-032 — 1-Hour USTEC Candidate A Breaker Magnitude Gate

**Status**: REFUTED
**Date**: 2026-05-27
**Instruments**: USTEC only
**Phase**: 004B Branch A conditional 1-hour extension

### Hypothesis Tests

1. **Hypothesis**: The USTEC Candidate A breaker chain, applied to synthetic 1-hour bars with elapsed-time-scaled definitions, preserves the EXP-031 15-minute positive direction and reaches the predeclared minimum magnitude before Branch A is allowed to proceed to temporal segmentation.

### Scope

- **Instruments**: USTEC only
- **Data**: Synthetic 1-hour OHLC for sweep, displacement, and Candidate A breaker detection; real 1-minute prices for outcomes
- **Chain**: EXP-015 sweep -> EXP-018 displacement -> EXP-022 Candidate A breaker, with elapsed-time-scaled constants
- **Constants**: 60-minute aggregation; 25-bar body median; 3-bar max displacement confirmation; 8-bar Candidate A lookback; 30-bar breaker lifecycle
- **Outcomes**: Return_R_60m, MAE_R_60m, MFE_R_60m, Hit1R_60m, Hit2R_60m, 60-minute log return
- **Exclusions**: no segmentation, controls, cost stress, stop perturbation, Branch B IFVG logic, Candidate B, or instruments other than USTEC
- **Constraints**: final 30 percent global holdout excluded before aggregation; outcomes use real 1-minute OHLC strictly after the confirming 1-hour displacement candle close

### Results / Observations

Event waterfall:

| Segment | Sweeps | Displacement | Breaker-Labeled | Feasible Breaker | Floor >= 50 |
| --- | ---: | ---: | ---: | ---: | --- |
| Train | 417 | 189 | 144 | 143 | PASS |
| Test | 147 | 74 | 62 | 62 | PASS |

Primary bootstrap (breaker minus displacement baseline Return_R_60m):

| Segment | Baseline | Breaker | Diff | 95% CI | EXP-031 50% Gate | Meets Gate |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| Train | +0.103R | +0.320R | +0.216R | [+0.144, +0.298] | +0.258R | NO |
| Test | +0.162R | +0.278R | +0.116R | [+0.039, +0.220] | +0.918R | NO |

Retention vs EXP-031: displacement `263 / 463 = 0.568`; feasible breaker `205 / 297 = 0.690`. The 30 percent retention failure rule is not triggered.

Secondary MAE_R_60m:

| Segment | Baseline MAE | Breaker MAE | Diff | 95% CI |
| --- | ---: | ---: | ---: | --- |
| Train | 0.481R | 0.324R | -0.157R | [-0.226, -0.096] |
| Test | 0.470R | 0.311R | -0.159R | [-0.327, -0.029] |

### Hypothesis-Specific Conclusion

**REFUTED**

Counts and positive direction survive, but the binding magnitude gate fails. The test Return_R_60m diff is +0.116R versus the required +0.918R, only about 6 percent of EXP-031's 15-minute test effect. Per scope, Branch A stops before EXP-033 unless a new reflection explicitly reframes the branch with weaker claims.

### Hypothesis-Agnostic Observations

- The 1-hour Candidate A breaker still filters adverse excursion: MAE_R improves by about -0.16R in both segments with CIs excluding zero.
- The failure is magnitude-based, not count-based; retention remains above the predeclared 30 percent floor.
- The 15-minute USTEC positive does not strengthen at 1-hour resolution. The higher-timeframe structural path is weaker than required for candidate validation.
- The amended reflection closes Branch A after rejecting weaker reframe options; no automatic temporal segmentation or follow-on Branch A experiment is scoped.

---

## EXP-033 — 15-Minute IFVG Rule Family Readiness Survey

**Status**: REFUTED
**Date**: 2026-05-27
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Phase**: 004B Branch B IFVG selectivity redesign

### Hypothesis Tests

1. **Hypothesis**: At least one of five predeclared IFVG/FVG rule-family modifications applied independently to the EXP-020/EXP-029 15-minute FVG/IFVG detector is deterministic, count-eligible, materially less tautological than the 84-85% baseline, meaningfully selective, and delay-bounded on at least two of four instruments in both train and test segments.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Data**: 1-minute analysis-set bars with the final 30% global holdout excluded before synthetic 15-minute OHLC aggregation
- **Rule families**: R1 stricter FVG size (`0.10 * ATR14`), R2 shorter lifecycle (24 bars), R3 displacement-qualified FVG creation, R4 mitigation-before-inversion, R5 zone-location near a swept PDH/PDL/ONH/ONL level
- **Readiness checks**: reproducibility digest, FVG/IFVG count floor, inversion-rate band `[0.55, 0.75]`, selectivity ratio `<= 0.80`, median delay `<= 24` bars, finite non-zero denominators
- **Exclusions**: no return, MAE, MFE, hit-rate, cost, P&L, parameter tuning, rule combinations, segmentation, or non-15-minute timeframe analysis

### Results / Observations

Baseline 15-minute FVG/IFVG counts replicated EXP-029:

| Instrument | Train FVG | Train IFVG Rate | Test FVG | Test IFVG Rate |
| --- | ---: | ---: | ---: | ---: |
| EURUSD | 8,583 | 0.853 | 3,683 | 0.857 |
| XAUUSD | 7,702 | 0.842 | 3,391 | 0.821 |
| BTCUSD | 9,283 | 0.826 | 4,129 | 0.845 |
| USTEC | 8,266 | 0.848 | 3,483 | 0.846 |

Rule-family outcomes:

| Rule | Main Result | Binding Failure |
| --- | --- | --- |
| R1 stricter size | Retained 79-83% of baseline FVGs; inversion rates 0.81-0.85 | inversion band and mostly selectivity |
| R2 shorter lifecycle | Inversion rates 0.64-0.68 in all cells | FVG-count selectivity ratio = 1.0 |
| R3 displacement-qualified | Retained 16-22% of FVGs; BTCUSD Train passed all six checks | inversion band in Test and most other cells |
| R4 mitigation-before-inversion | Inversion rates 0.81-0.85; FVG count unchanged | inversion band and selectivity |
| R5 zone-location | Retained 11-17% of FVGs | inversion band |

All 40 reproducibility digests matched. `verdict.json` records `rules_in_contention = []`, `selected_rule = null`, and `qualifying_instruments_per_rule = {R1: [], R2: [], R3: [], R4: [], R5: []}`.

### Hypothesis-Specific Conclusion

**REFUTED**

No rule family passed all six readiness checks on at least two instruments in both train and test segments. The predeclared aggregate verdict is "Branch B closes at EXP-033 with selectivity-gated no-go"; no follow-on entry-quality scope is authorized from this rule menu.

### Hypothesis-Agnostic Observations

- The high 120-bar IFVG inversion rate appears structural to the lifecycle-windowed three-candle FVG definition; rules that narrow FVG count generally preserve near-baseline inversion rates.
- Shorter lifecycle is the only tested modification that reliably moves inversion rate into the readiness band, but it does not reduce FVG count under the EXP-033 selectivity denominator.
- Displacement-qualified FVG creation is the closest single-rule candidate: it creates meaningful FVG selectivity, but its inversion rate remains just above the predeclared upper band in almost every segment.
- With EXP-032 closing Branch A and EXP-033 closing Branch B, Phase 004 has no eligible candidate manifest before holdout.

---

## EXP-034 — Prior-Range Location Readiness and Shared Aggregation-Coverage Rule

**Status**: SUPPORTED
**Date**: 2026-05-29
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Data Views / Feature Categories**: 1-minute time bars aggregated to strict and tolerant `1h`/`4h` real OHLC; Prior-Range Location buckets

### Hypothesis Tests

1. **Hypothesis**: On `1h` and `4h` real-price bars aggregated from holdout-excluded 1-minute data, the Prior-Range Location descriptor over the prior 20 completed same-timeframe bars, bucketed at bottom `<=0.20`, middle `(0.20,0.80)`, and top `>=0.80`, produces deterministic states whose top, middle, and bottom buckets each meet row and independent-episode floors on at least two distinct instruments in both train and test segments, and the shared strict-vs-tolerant aggregation rule is decidable by coverage and feature-stability checks.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Data Views / Feature Categories**: holdout-excluded 1-minute time bars; deterministic `1h` and `4h` real OHLC aggregation; Prior-Range Location readiness
- **Features**: `range_location = (Close - prior_low) / (prior_high - prior_low)`, prior 20-bar high/low shifted one bar, outside-range flag, bottom/middle/top buckets, independent bucket episodes
- **Parameter ranges**: fixed lookback `20`; fixed buckets `0.20/0.80`; strict aggregation and tolerant `min_coverage=0.90`; no parameter sweep
- **Exclusions**: no return, FE/AE, hit-rate, P&L, matched-control test, `1d`, other descriptors, chart-type generators, or coverage-tolerance sweep
- **Constraints**: final 30 percent global holdout excluded before aggregation; timestamp alignment by `CloseTime`; denominator validity checked; strict-vs-tolerant stability joined by timestamp

### Results / Observations

- `results/verdict.json` records `passes_readiness=true`.
- Strict aggregation is canonical for both `1h` and `4h`.
- Passing instruments under strict aggregation: `EURUSD`, `XAUUSD`, `BTCUSD`, and `USTEC` for both `1h` and `4h`.
- All 32 readiness rows pass determinism, row floor, episode floor, and denominator-valid checks.
- Strict bucket row counts range from `118` to `7324`; strict independent-episode counts range from `35` to `1244`.
- Strict dropped-window rates: `1h` ranges `4.44%` to `13.13%`; `4h` ranges `14.10%` to `24.00%`.
- Tolerant matched-bucket stability passes at `1h` for all instruments, but fails at `EURUSD 4h` (`92.67%`) and `BTCUSD 4h` (`90.72%`).

### Hypothesis-Specific Conclusion

**SUPPORTED**

The Prior-Range Location count-eligibility hypothesis is supported. The descriptor passes the predeclared row, episode, determinism, and denominator gates on all four instruments at both scoped timeframes under strict aggregation, exceeding the required `>=2` distinct-instrument threshold.

### Hypothesis-Agnostic Observations

- Strict aggregation is sufficient for this descriptor; tolerant windows are not needed to rescue counts.
- Tolerant aggregation can materially perturb `4h` bucket assignment for some instruments, so the coverage convenience is not neutral for Prior-Range Location.
- The result authorizes readiness consideration only. It does not establish executable return differentiation or edge.

---

## EXP-035 — Market Bias (CEREBR) Deterministic Port and State-Episode Readiness

**Status**: SUPPORTED (conditional)
**Date**: 2026-05-29
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Data Views / Feature Categories**: 1-minute time bars aggregated to strict and tolerant `1h`/`4h` real OHLC; Market Bias sign-only and four-way states

### Hypothesis Tests

1. **Hypothesis**: On holdout-excluded `1h`/`4h` real-price bars, the chart-timeframe Market Bias port (`EMA(OHLC,100) → Heiken-Ashi with the source `xhaopen[1]` recursion → EMA(haopen/haclose,100) → osc_bias = 100·(c2−o2)`, `osc_smooth = EMA(osc_bias,7)`) is deterministic under shuffle-then-resort with a convergent two-seeding warmup, and its sign-only states meet row and independent-episode floors on at least two distinct instruments in both train and test segments under an admissible aggregation.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Data Views / Feature Categories**: holdout-excluded 1-minute time bars; deterministic `1h`/`4h` real OHLC aggregation (strict and tolerant `0.90`); Market Bias state-episode readiness
- **Features**: sign-only state (`bull` if `osc_bias > 0` else `bear`, zero-tie carried) as primary; four-way strong/weak bull/bear as secondary diagnostic; independent state episodes; transitions; persistence; `|osc_bias|` quartiles; dominant-state share
- **Parameter ranges**: fixed `HA_LEN=100`, `HA_LEN2=100`, `OSC_LEN=7`; warmup floor `300`; predeclared two-seeding (Pine-SMA vs cold) convergence rule for `W`; no parameter sweep
- **Exclusions**: no return, FE/AE, hit-rate, P&L, matched-control test, `1d`, neutral-band return construct, multi-timeframe Pine mode, or parameter tuning
- **Constraints**: final 30% global holdout excluded before aggregation; causal EMAs; chart-timeframe collapse (no Pine repaint path); segment assignment by `CloseTime`; deterministic-only fidelity claim (no exported TradingView reference series present)

### Results / Observations

- Critical no-collapse bug (`np.isnan(value) is False` inversion) found in post-execution audit, patched to `np.isfinite(dominant_share) and dominant_share <= 0.95`, experiment rerun; re-audit PASS on regenerated outputs.
- `results/verdict.json` records `passes_readiness=true` on cell `1h/tolerant` = `[BTCUSD, USTEC]`; `1h/strict=[BTCUSD]` (single instrument); `4h/strict=[]`; `4h/tolerant=[]`.
- All 32 rows pass determinism (`Check1`) and warmup convergence (`Check2`); `W` ranges `300–405`.
- The independent-episode floor (`Check4`) is the binding constraint, failing 25 of 32 rows.
- Every `4h` cell fails the episode floor (train sign-episodes `4–9`); `EURUSD`/`XAUUSD` fall just short at `1h` (`24–28` train episodes vs the `30` floor).
- No state collapse: `DominantShare` ranges `0.501–0.774`.

### Hypothesis-Specific Conclusion

**SUPPORTED (conditional)**

The port is deterministic and warmup-convergent on all instruments and timeframes, and sign-only states are count-eligible on `BTCUSD` and `USTEC` at `1h` under tolerant aggregation, meeting the predeclared `>= 2`-distinct-instrument rule at `>= 1` timeframe under an admissible aggregation. The support is narrow and aggregation-dependent.

### Hypothesis-Agnostic Observations

- Readiness is aggregation-dependent: under the strict rule EXP-034 selected as canonical, Market Bias has a single passing instrument (inconclusive). The mid-phase reflection inherits a phase-level aggregation-canonicity decision.
- Readiness is instrument-concentrated: only the higher-turnover `BTCUSD`/`USTEC` reach the episode floor; the double-`EMA(100)` smoothing produces long, rarely-flipping states that starve FX/gold and all `4h` cells of transitions.
- Fidelity is unverified: deterministic re-implementation only; no Pine reference series exists, so any later negative Market Bias return result must carry the unverified-fidelity caveat.
- The result authorizes readiness consideration only; it establishes the descriptor can be return-tested on a specific cell, not that it carries edge.

---

## EXP-036 — Prior-Range Location Executable State-Aligned Return Test

**Status**: REFUTED
**Date**: 2026-05-29
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Data Views / Feature Categories**: 1-minute time bars aggregated to strict `1h`/`4h` real OHLC; Prior-Range Location return test

### Hypothesis Tests

1. **Hypothesis**: On holdout-excluded `1h` and `4h` strict-aggregated real-price bars, the Prior-Range Location descriptor's executable direction-adjusted next-bar log return, with top bucket (`>=0.80`) traded long and bottom bucket (`<=0.20`) traded short, exceeds both its own measured middle-bucket neutral baseline and a matched same-timeframe prior-bar-momentum-sign control, with episode-level bootstrap CIs and train/test sign preservation on at least two distinct instruments. The single predeclared 4-bar hold can identify horizon-dependent state differentiation only if it passes both contrasts on at least two distinct instruments.

### Scope

- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
- **Data Views / Feature Categories**: holdout-excluded 1-minute time bars; strict `1h` and `4h` real OHLC aggregation; Prior-Range Location buckets
- **Features**: `range_location = (Close - prior_low) / (prior_high - prior_low)`, prior 20 completed same-timeframe bars shifted one bar, clipped bottom/middle/top buckets, top -> long, bottom -> short, middle as measured neutral baseline
- **Parameter ranges**: fixed lookback `20`; fixed buckets `0.20/0.80`; strict aggregation only; next-bar primary and fixed 4-bar secondary; no parameter sweep
- **Exclusions**: no tolerant aggregation, no `1d`, no reversal framing, no cost/slippage/spread model, no stops/targets/sizing, no other descriptor, no robustness perturbation, no holdout access
- **Constraints**: final 30 percent global holdout excluded before aggregation; all outcomes use real `Open`/`Close`; forward returns enter at next bar open; inference uses independent state episodes

### Results / Observations

- All 32 `(instrument, timeframe, segment, horizon)` rows are adjudicable for both neutral and control contrasts.
- Minimum post-filter train state count is `326` rows / `89` episodes; minimum test state count is `118` rows / `35` episodes.
- Next-bar `next_bar_neutral_and_control` is empty for both `1h` and `4h`.
- No next-bar test-segment `Delta_neutral` CI has lower bound above zero.
- The only next-bar matched-control positive test cell is `XAUUSD 1h`: `Delta_control = +0.000153`, CI `[+0.000052, +0.000252]`.
- The only 4-bar cell passing both contrasts is `XAUUSD 1h`: `Delta_neutral = +0.000482`, CI `[+0.000088, +0.000855]`; `Delta_control = +0.000317`, CI `[+0.000040, +0.000571]`.
- `4h` gap-spanning entry shares range from `20.6%` to `25.2%`; this is a scoped executability caveat, not a primary verdict input.

### Hypothesis-Specific Conclusion

**REFUTED**

Prior-Range Location fails the predeclared matched-control replication gate. The next-bar primary has zero instruments passing both `Delta_neutral` and `Delta_control`, and the 4-bar secondary has only one passing instrument, below the `>=2` distinct-instrument threshold.

### Hypothesis-Agnostic Observations

- The failure is not count-driven; every scoped contrast remains adjudicable after return filtering.
- The localized `XAUUSD 1h` 4-bar positive is insufficient for the phase gate but indicates the descriptor is not uniformly inert.
- With Market Bias already a readiness-gated no-go under canonical strict aggregation, Phase 005 has no surviving directional state-descriptor candidate from its authorized path.
