# Phase 2 Design: Signal-Quality Characterisation
**Phase:** 002 — Signal-Quality Characterisation  
**Date:** 2026-05-16  
**Status:** Active  
**Predecessor:** 2026-05-14-001-chart-type-validation  

**Decision status:** Phase 1 validated the architecture. Time bars are the master timeline. Renko ATR-14 is the primary event-chart layer. Line Break level 3 is a high-confidence confirmation filter. Heiken Ashi is a smoothed signal view, never a return-evaluation price. Phase 2 does not ask which chart type is better; it asks what each validated view contributes to a shared signal-quality objective on the real-price timeline.

---

## Phase Objectives

Phase 1 established what each chart type does to price data. Phase 2 establishes whether what each chart type does is useful for producing cleaner, more reliable real-price signals.

The central question is: **when each chart type is used in the role Phase 1 validated for it, does the resulting signal show measurably better real-price outcomes than signals derived from the time-bar timeline alone?**

This phase is still characterisation. It extends the no-P&L boundary: signal quality is measured by real-price excursion, precision, recall, adverse excursion, and run continuation at signal timestamps — not by strategy P&L, optimised parameters, or live execution. No parameter optimisation and no predictive models are introduced in Phase 2.

Phase 2 has two sequential blocks:

**Block A — Timeframe Replication (prerequisite):** Run EXP-001 through EXP-006 on 15-minute and 1-hour source bars. All six Phase 1 experiments ran on 1-minute bars only. The research setup mandates timeframe as a major experiment dimension. Block A closes that gap before Phase 2 signal-quality hypotheses are tested, so that the conclusions those hypotheses are built on are known to be general rather than 1-minute-specific.

**Block B — Signal-Quality Experiments:** Five experiments that test what each chart type's validated strength contributes to real-price signal quality, using a shared measurement framework developed in EXP-007.

---

## Prerequisites

### Data

No new cAlgo or generator work is required before Phase 2. The existing instruments, time-bar datasets, and Python generators are sufficient.

**Block A** requires rerunning the generators on 15-minute and 1-hour aggregated time bars. The generators are already timeframe-agnostic. The aggregation step — grouping 1-minute bars into 15-minute and 1-hour OHLCV bars — must be added to the pipeline if not already present. This is a data-preparation step, not an architectural change.

**Block B** requires one new shared infrastructure component: the real-price signal-quality measurement framework (described below). This must be implemented before any Block B experiment begins, because all five experiments reference it.

### Real-Price Signal-Quality Measurement Framework

All Block B experiments evaluate signal quality using the same set of real-price metrics computed at signal emission timestamps. This framework must be implemented once as a shared utility before EXP-007 begins. It is not an experiment; it is infrastructure.

**Inputs:**
- A list of signal timestamps and directions (one per signal event), derived from any chart type or chart-type combination.
- The time-bar dataset for the relevant instrument (real OHLCV prices).

**Outputs per signal:**
- **Forward excursion (FE):** The maximum favourable real-price move in the N minutes following signal emission, measured in ATR units. N = {30, 60, 120, 240} minutes.
- **Adverse excursion (AE):** The maximum adverse real-price move in the same windows before FE is reached.
- **FE/AE ratio:** Forward excursion divided by adverse excursion.
- **Run continuation:** Whether the signal direction is confirmed by a time-bar close in the same direction within a defined tolerance window.
- **Signal precision:** Fraction of signals where FE exceeds a threshold (1.0× ATR) within the forward window.
- **Signal recall:** Fraction of qualifying real-price moves (FE ≥ 1.0× ATR from any bar in the window) that have a corresponding signal within a tolerance window.

**Constraints:**
- All prices resolved from 1-minute time bars at the signal CloseTime/SourceCloseTime, not from any chart-type construction price.
- ATR computed from time bars, train-segment calibrated, matching the EXP-002 and EXP-004 conventions.
- Metrics computed separately per instrument and per volatility regime (train-set tercile labels, same methodology as Phase 1).
- Framework must be deterministic and produce identical outputs on the same input.
- Framework must carry explicit missing-signal indicators: if a chart type did not emit in a window, that absence is coded as a measurable state, not excluded from the denominator.

This framework is the shared evaluation substrate for all Block B experiments. Any Block B experiment that needs a metric not listed above must define it as an extension of the framework, not as a separate ad hoc computation.

---

## Block A: Timeframe Replication

### Rationale

The Phase 1 research setup states: *"Treat timeframe as a major experiment dimension. Test the same hypothesis across timeframes where appropriate (1min, 15min, 30min, 1h, 4h, 1d, etc.)."* The Phase 1 design lists *"Timeframe as a hyperparameter (experiments may be repeated on different timeframes)"* in the in-scope boundary. Individual experiment scopes deferred higher-timeframe comparison as an exclusion — not an abandonment.

Every Phase 1 experiment ran on 1-minute source bars. All six conclusions are therefore conditional on the 1-minute timeframe. The effects documented — ghost rates, hybrid rates, reversal latency, noise robustness, cross-chart agreement, HA distortion — may shift at higher timeframes for structural reasons:

- Ghost rates at higher timeframes are lower, reducing the relative ghost-elimination headroom for event charts.
- ATR-based Renko brick sizes are larger at higher timeframes relative to regime-transition magnitudes, changing the hybrid-rate and missed-transition profiles.
- Event-chart reversal latency of 101–111 minutes measured against a 2-minute time-bar baseline may compress substantially at 1-hour bars, where the time-bar baseline is already 60 minutes.
- Noise-robustness advantages of event charts may narrow at higher timeframes where time bars already aggregate intrabar noise.

Block A determines whether Phase 1 findings are general properties of event-chart aggregation or 1-minute microstructure observations. That determination materially shapes how confidently Block B hypotheses can be stated.

### Block A Scope

- **Timeframes:** 15-minute and 1-hour (generated by aggregating 1-minute source bars).
- **Instruments:** EURUSD, XAUUSD, BTCUSD, USTEC.
- **Chart types:** Same as Phase 1 for each experiment (Time Bars, Line Break level 3, Renko ATR-14, Heiken Ashi).
- **Hypotheses:** Identical to Phase 1 for each experiment. No new hypotheses are introduced.
- **Metrics:** Identical to Phase 1 for each experiment.
- **Analysis segment:** First 70% of each instrument's dataset by time; final 30% global holdout maintained.
- **Exclusions:** No new parameters, no strategy testing, no P&L, no predictive models.

Each Block A experiment is designated with a `-TF` suffix to distinguish it from the Phase 1 originals:

| Block A ID | Phase 1 Original | Timeframes |
|---|---|---|
| EXP-001-TF | EXP-001: Information Density & Ghost Bar Comparison | 15min, 1h |
| EXP-002-TF | EXP-002: Volatility & Trend Regime Representation | 15min, 1h |
| EXP-003-TF | EXP-003: Noise Filtering & Statistical Robustness | 15min, 1h |
| EXP-004-TF | EXP-004: Market Structure Capture Speed & Fidelity | 15min, 1h |
| EXP-005-TF | EXP-005: Cross-Chart-Type Alignment & Regime Correspondence | 15min, 1h |
| EXP-006-TF | EXP-006: Heiken Ashi Synthetic Price Distortion Quantification | 15min, 1h |

### Block A Success Criteria

Block A produces one of two outcomes for each Phase 1 finding:

- **Replicated:** The effect holds at both higher timeframes, within the same directional conclusion (supported/refuted), with consistent instrument behaviour. Phase 1 conclusions are treated as general.
- **Not replicated / attenuated:** The effect changes direction, loses instrument consistency, or falls within noise at one or both higher timeframes. Phase 1 conclusions are marked as 1-minute-conditional, and Block B hypotheses that depend on those conclusions must explicitly state the timeframe conditioning.

Block A does not require all Phase 1 findings to replicate. Partial or non-replication is informative and does not block Block B. It adjusts the confidence language used in Block B hypotheses.

---

## Block B: Signal-Quality Experiments

### Design Principles

Block B experiments are not chart-vs-chart comparisons. Phase 1 answered the competitive question: each chart type has a specific, validated role. Block B tests what each role contributes to a shared signal objective.

The validated role of each chart type, derived from Phase 1:

| Chart type | Validated strength | Validated limitation |
|---|---|---|
| Time bars | Complete temporal coverage; exact real-price anchoring; full recall; 2-minute reversal detection | High noise throughput; 83–85% signal split rate; 26–28% reversal precision |
| Renko ATR-14 | Direction and return-variance stability under noise (4/4 instruments, CI excludes zero); ~99.9% reversal precision; 72–75% recall; manageable lag tails | 17–24% missed regime transitions; ~50× reversal latency vs. time bars; higher hybrid rate than Line Break |
| Line Break level 3 | Maximum reversal precision (~99.9%); near-zero split rate; strongest bar compression (~25% of time-bar count) | 34–40% recall; 25–34% missed regime transitions; 110–111 minute median latency |
| Heiken Ashi | Strongest variance smoothing under noise (~80–93% lower HAClose variance drift); 30–35% lower direction-change frequency; high recall with minimal latency | No bar compression; ~25–26% return compression invalidates direct P&L use; lowest cross-chart agreement (~65%) |

Each Block B experiment uses one or more of these validated strengths and tests whether applying them in combination with the time-bar timeline produces measurably better real-price signal quality than the time-bar baseline alone. Experiments are designed around the contribution each chart type makes, not the chart type as a competitive unit.

All Block B experiments use the shared signal-quality measurement framework defined in Prerequisites.

---

### EXP-007: Multi-State Signal-Quality Baseline

**Hypothesis:** Real-price signal quality cannot be adequately characterised by binary direction alone. A multi-state signal-quality framework — measuring forward excursion, adverse excursion, run continuation, and signal precision and recall in ATR units on the real-price timeline — produces meaningfully differentiated quality distributions across the four chart types and across volatility regimes, providing a baseline measurement vocabulary for all subsequent Phase 2 experiments.

**Question:** What does the signal-quality distribution look like for each chart type when measured on real prices at signal emission timestamps, and is binary direction entropy an adequate summary of that distribution?

**Rationale:** Phase 1 EXP-001 found that binary directional entropy is at or above 0.994 bits for all chart types on all instruments — near the binary ceiling. This means binary direction cannot discriminate between chart types in a learning or evaluation setting. EXP-004 documented that time bars produce 83–85% split-rate redundancy and 26–28% precision, while Renko and Line Break reach ~99.9% precision at much lower recall. But EXP-004 used a fixed 1.5× and 2.0× ATR reversal reference, not a general forward-excursion measurement. EXP-007 establishes the general baseline.

This experiment does not test a strategy or optimise parameters. It characterises the shape of signal quality for each chart type using the framework defined above, producing the measurement substrate that all other Block B experiments depend on.

**Key metrics:**
- Forward excursion (FE) distribution at 30, 60, 120, 240 minutes per chart type and regime.
- Adverse excursion (AE) distribution in the same windows.
- FE/AE ratio distribution per chart type.
- Run-continuation rate per chart type.
- Signal-quality precision (FE ≥ 1.0× ATR) per chart type and regime.
- Signal-quality recall (qualifying real-price moves captured) per chart type.
- Comparison of binary direction entropy versus FE-based distribution: does the FE distribution show between-chart-type differences that binary direction cannot?

**Instruments:** EURUSD, XAUUSD, BTCUSD, USTEC  
**Chart types:** Time Bars (baseline), Line Break level 3, Renko ATR-14, Heiken Ashi  
**Scope:**
- Uses the shared real-price signal-quality measurement framework.
- Regime labels computed on time bars, train-set calibrated, same methodology as Phase 1.
- Signal timestamps are chart-type native CloseTime/SourceCloseTime; no bar-index alignment.
- Missing signals (chart types that did not emit in a given window) are coded as an explicit state, not excluded.
- Analysis segment: first 70% by time; final 30% global holdout maintained.
- **Exclusions:** No strategy P&L, no parameter optimisation, no predictive models, no cross-chart combination logic (that is the domain of EXP-010 and EXP-011).

---

### EXP-008: Renko as a Precision Gate Over Time-Bar Signals

**Hypothesis:** Time-bar direction signals that are confirmed by a Renko emission within a defined tolerance window show materially higher real-price forward excursion and lower adverse excursion than the full set of time-bar direction signals, without reducing signal quality relative to raw Renko signals alone.

**Question:** Does using Renko as a precision filter over the time-bar signal pool improve the signal-quality distribution of the filtered subset — on real prices — compared to both the unfiltered time-bar pool and the Renko signal set used alone?

**Rationale:** Phase 1 established two complementary validated properties: time bars have complete coverage and full recall, but 83–85% split-rate noise and 26–28% precision. Renko has ~99.9% precision and 72–75% recall, but ~50× latency cost when used as the sole signal source. These properties are not competing; they are potentially complementary at different layers. Time bars generate candidates. Renko confirms or rejects.

This experiment tests that architecture directly. It does not ask whether Renko beats time bars. It asks whether Renko's validated denoising strength, applied as a gate over time-bar candidates, produces a filtered signal set that is better than either view alone.

**Key metrics (using shared framework):**
- Signal-quality distribution (FE, AE, FE/AE, run continuation, precision, recall) for: (a) all time-bar direction signals, (b) Renko-confirmed time-bar signals, (c) Renko signals alone.
- Coverage: what fraction of time-bar signals are confirmed by Renko within the tolerance window?
- Regime-stratified results: does the precision gain differ between low, medium, and high volatility?
- Tolerance window sensitivity: tested at 5-minute, 15-minute, and 30-minute confirmation windows.

**Instruments:** EURUSD, XAUUSD, BTCUSD, USTEC  
**Chart types:** Time Bars (candidate pool), Renko ATR-14 (precision gate)  
**Scope:**
- Signal timestamps resolved from time bars; Renko confirmation tested against Renko native CloseTime.
- No Renko construction prices used in any return or excursion calculation.
- The missing-signal state (Renko did not emit in the window) is a first-class outcome: not excluded from analysis.
- Regime labels and ATR from time-bar train segment, matching Phase 1 conventions.
- Analysis segment: first 70% by time; final 30% global holdout maintained.
- **Exclusions:** No strategy P&L, no parameter optimisation, no tick-level data, no Line Break or HA data in this experiment.

---

### EXP-009: Heiken Ashi Direction as a Signal Generator, Evaluated on Real Prices

**Hypothesis:** Direction signals generated from Heiken Ashi state changes — evaluated on real prices at signal timestamps — show higher forward excursion and lower adverse excursion than time-bar direction signals of equivalent direction, because HA smoothing reduces false direction-change signals that arise from microstructure noise.

**Question:** When HA direction changes are treated as signal events and evaluated using real prices on the time-bar timeline, do they produce better real-price signal-quality distributions than time-bar direction changes alone?

**Rationale:** Phase 1 established two things about HA that are relevant here. EXP-003 found that HAClose variance drift is 80–93% lower than time-bar variance drift under noise — the strongest variance-smoothing result in Phase 1. EXP-004 found that HA direction-change frequency is 30–35% lower than real prices. Together, these suggest that HA emits fewer, smoother directional transitions. EXP-006 confirmed that HA prices must not be used for P&L evaluation. What Phase 1 did not test is whether those fewer, smoother transitions — when evaluated on real prices — represent higher-quality signal candidates.

This experiment is the legitimate use case for HA: signal generation (from HA direction), evaluated on the real-price timeline (from time-bar prices at signal timestamps). It is not HA vs. time bars. It is HA-as-smoother tested on the signal-quality dimension that Phase 1 established is the right measurement domain.

**Key metrics (using shared framework):**
- Signal-quality distribution (FE, AE, FE/AE, run continuation, precision, recall) for: (a) time-bar direction changes, (b) HA direction changes evaluated on real prices.
- Signal-count ratio: how many fewer signals does HA emit? Does the quality improvement (if any) justify the coverage reduction?
- Regime-stratified results: is the HA smoothing advantage larger in low-volatility regimes (where microstructure noise is proportionally more disruptive)?
- Direction-change alignment: what fraction of HA direction changes occur within a tolerance window of a time-bar direction change?

**Instruments:** EURUSD, XAUUSD, BTCUSD, USTEC  
**Chart types:** Time Bars (baseline and real-price anchor), Heiken Ashi (signal generator)  
**Scope:**
- HA direction changes identified from HAClose series. Signal timestamps are HA CloseTime (identical to time-bar CloseTime since HA is a 1:1 transformation).
- All excursion and return metrics resolved from time-bar real prices at signal timestamps.
- HA construction prices (HAOpen, HAHigh, HALow, HAClose) are not used in any excursion or return calculation.
- Regime labels and ATR from time-bar train segment, matching Phase 1 conventions.
- Analysis segment: first 70% by time; final 30% global holdout maintained.
- **Exclusions:** No strategy P&L, no HA construction prices in any return metric, no Renko or Line Break data in this experiment, no parameter variation.

---

### EXP-010: Line Break as a Confirmation Layer Over Renko Signals

**Hypothesis:** Renko signals that are also confirmed by a Line Break emission within a defined tolerance window show materially higher real-price forward excursion and lower adverse excursion than the full set of Renko signals, and this quality improvement is large enough to justify the coverage reduction imposed by Line Break's lower recall.

**Question:** Does Line Break confirmation of Renko signals add measurable real-price signal quality beyond what Renko alone produces, and if so, at what coverage cost?

**Rationale:** Phase 1 established that Renko has ~99.9% precision with 72–75% recall, and Line Break has ~99.9% precision with only 34–40% recall. From a chart-type competition perspective, Renko dominates. But that framing misses the architectural question: given that Line Break confirms only a fraction of Renko signals (because it requires more consecutive confirmed lines before emitting), is that subset — where both chart types agree — a higher-quality subset? If so, Line Break is not competing with Renko; it is stratifying Renko's signal set by confidence.

This experiment tests that layering hypothesis directly. It uses Renko as the primary signal layer and Line Break as the confidence stratifier, both evaluated on the shared real-price framework.

**Key metrics (using shared framework):**
- Signal-quality distribution (FE, AE, FE/AE, run continuation, precision, recall) for: (a) all Renko signals, (b) Renko signals confirmed by Line Break within the tolerance window, (c) Renko signals not confirmed by Line Break.
- Coverage cost: what fraction of Renko signals are confirmed by Line Break?
- Quality trade-off: is the FE/AE improvement in the confirmed subset large enough, relative to the coverage loss, to justify the stratification in practice?
- Regime-stratified results: does Line Break confirmation add more quality in low-volatility regimes (where both chart types may be sparser) or high-volatility regimes (where trend strength makes confirmation easier)?
- Tolerance window sensitivity: tested at 5-minute, 15-minute, and 30-minute confirmation windows.

**Instruments:** EURUSD, XAUUSD, BTCUSD, USTEC  
**Chart types:** Renko ATR-14 (primary signal layer), Line Break level 3 (confirmation layer)  
**Scope:**
- Primary signal timestamps from Renko SourceCloseTime; Line Break confirmation tested against Line Break SourceCloseTime within the tolerance window.
- All excursion and return metrics resolved from time-bar real prices at Renko signal timestamps.
- Neither Renko nor Line Break construction prices used in any excursion or return calculation.
- Missing Line Break confirmation (Line Break did not emit in the window) is the non-confirmed case: it must be analysed explicitly, not excluded.
- Regime labels and ATR from time-bar train segment, matching Phase 1 conventions.
- Analysis segment: first 70% by time; final 30% global holdout maintained.
- **Exclusions:** No strategy P&L, no time-bar or HA data in this experiment's primary analysis (time bars are used only as the real-price return anchor), no parameter optimisation.

---

### EXP-011: Event-Native Volatility Regime Detection

**Hypothesis:** Volatility-regime labels derived from event-chart internal features — specifically Renko event density, source-bar count per brick, and running brick-to-ATR ratio — identify volatility regime transitions with lower boundary cost (hybrid rate) and fewer missed transitions than time-bar-derived regime labels applied to Renko events.

**Question:** Can Renko's own internal structure define volatility regimes that align better with Renko event boundaries than the time-bar-derived tercile labels used in Phase 1?

**Rationale:** EXP-002 found that applying time-bar-derived regime labels to event-chart data creates structural boundary costs: Renko hybrid rates of 0.092–0.119 and 17–24% missed transitions. That boundary cost is a direct consequence of forcing a time-bar-defined boundary onto an event-chart-native timeline — the transition may occur in the middle of a brick. EXP-002's experiment scope explicitly excluded event-native regime definitions. This experiment fills that gap.

The question is not whether event-native regimes are better than time-bar regimes in general — time-bar regimes must remain the canonical reference for return evaluation. The question is whether event-native regime features can define Renko-specific regime states that reduce hybrid rate and missed-transition counts when analysing Renko signal quality in EXP-008 and EXP-010. If so, Phase 3 can use event-native regime stratification alongside time-bar regimes for signal analysis.

**Key metrics:**
- Event-native regime features: Renko event density (bricks per N time-bar window), source-bar count per brick (shorter = faster market), brick-to-ATR ratio (brick size relative to recent ATR).
- Candidate regime definitions derived from clustering or tercile segmentation of the above features.
- Hybrid rate of event-native regimes vs. time-bar-derived tercile regimes applied to Renko events.
- Missed-transition rate vs. time-bar-derived transitions (same reference as EXP-002).
- Agreement between event-native regime labels and time-bar regime labels: do they identify the same episodes, or structurally different market states?
- Signal-quality distribution (FE, AE, FE/AE from shared framework) stratified by event-native regime: does event-native stratification produce more differentiated signal-quality distributions than time-bar regime stratification?

**Instruments:** EURUSD, XAUUSD, BTCUSD, USTEC  
**Chart types:** Renko ATR-14 (primary), Time Bars (reference and real-price anchor)  
**Scope:**
- Event-native features computed from Renko dataset only; no HA or Line Break features in this experiment.
- Time-bar regime labels from train-set calibrated terciles (same as Phase 1) used as the reference for comparison.
- Regime feature engineering uses only the analysis segment (70%); no look-ahead from the holdout.
- All signal-quality excursion metrics resolved from time-bar real prices.
- **Exclusions:** No strategy P&L, no parameter optimisation of the regime feature definitions, no claim that event-native regimes replace time-bar regimes for return evaluation purposes.

---

## Phase Scope Boundaries

**In scope:**
- Block A: Timeframe replication of EXP-001 through EXP-006 on 15-minute and 1-hour source bars.
- Block B: Signal-quality characterisation using the shared real-price measurement framework.
- Multi-state signal-quality metrics: forward excursion, adverse excursion, FE/AE ratio, run continuation, precision, recall — all in ATR units on real prices.
- Cross-chart combination as a contribution test (not a competition): Renko gating time bars, Line Break stratifying Renko, HA smoothing evaluated on real prices.
- Event-native volatility regime features derived from Renko internal structure.
- Regime-stratified signal-quality analysis using time-bar-derived tercile labels (consistent with Phase 1).
- Tolerance window sensitivity analysis where specified (EXP-008, EXP-010).
- The shared signal-quality measurement framework as infrastructure.

**Out of scope (for Phase 2):**
- Strategy P&L of any kind.
- Parameter optimisation (best level for Line Break, best ATR period for Renko, best tolerance window).
- Predictive models or machine learning.
- Live trading integration.
- Additional instruments beyond EURUSD, XAUUSD, BTCUSD, USTEC.
- Timeframes beyond 15-minute and 1-hour for Block B experiments (Block A covers this; Block B runs on 1-minute unless a Block A finding specifically motivates a different timeframe).
- Any analysis that computes returns from HA or Renko construction prices.
- Any analysis that uses out-of-sample data from the final 30% global holdout.
- Tick-level data or sub-minute source bars.
- Strategy theories or trading rules derived from Phase 2 signal-quality observations. These are Phase 3 territory.

**Global holdout:** The final 30% of the dataset (by time) is excluded from all analysis. Inherited from Phase 1. This boundary is unconditional in Phase 2.

---

## Success Criteria for Phase 2

Phase 2 is successful if it produces:

1. **Timeframe generalisation verdict (Block A):** A clear determination for each Phase 1 finding: replicated across timeframes (general property) or not replicated (1-minute-conditional). This must be documented before Block B conclusions are treated as final.

2. **Shared measurement framework:** The real-price signal-quality measurement framework implemented, validated for determinism and no look-ahead, and used consistently across all Block B experiments.

3. **Multi-state signal-quality baseline (EXP-007):** A characterised signal-quality distribution for each chart type on real prices, demonstrating whether the FE/AE framework differentiates chart types in ways that binary direction entropy cannot.

4. **Renko-as-gate result (EXP-008):** A quantified precision-coverage trade-off for Renko-confirmed time-bar signals, with regime-stratified results.

5. **HA signal evaluation result (EXP-009):** A quantified comparison of HA direction signals evaluated on real prices versus time-bar direction signals, with signal-count ratio and regime-stratified results.

6. **Line Break confirmation result (EXP-010):** A quantified quality-coverage trade-off for Line Break-confirmed Renko signals, with regime-stratified results and tolerance-window sensitivity.

7. **Event-native regime result (EXP-011):** A determination of whether event-native Renko regime features reduce hybrid rate and missed-transition count relative to time-bar-derived labels, and whether they produce more differentiated signal-quality distributions.

8. **Phase 3 direction:** Enough evidence to determine whether any chart-type combination produces a reproducible, instrument-consistent real-price signal advantage large enough to justify Phase 3 strategy-theory exploration.

---

## Estimated Timeline

| Week | Task | Deliverable |
|------|------|-------------|
| **1** | 15-minute and 1-hour bar aggregation pipeline; Block A data preparation | Aggregated time-bar datasets for EURUSD, XAUUSD, BTCUSD, USTEC at 15min and 1h |
| **2–3** | EXP-001-TF through EXP-003-TF (Information Density, Regime Representation, Noise Robustness at higher timeframes) | Three timeframe-replicated experiments |
| **4–5** | EXP-004-TF through EXP-006-TF (Structure Capture, Cross-Type Alignment, HA Distortion at higher timeframes) | Three timeframe-replicated experiments; Block A timeframe generalisation verdict |
| **6** | Shared signal-quality measurement framework implementation + validation | Framework utility, unit tests, determinism confirmation |
| **7** | EXP-007 (Multi-State Signal-Quality Baseline) | Baseline signal-quality distributions per chart type |
| **8** | EXP-008 (Renko as Precision Gate) | Renko-gating precision-coverage analysis |
| **9** | EXP-009 (HA Signal Evaluated on Real Prices) | HA signal-quality comparison |
| **10** | EXP-010 (Line Break Confirmation Layer) | Line Break stratification quality-coverage analysis |
| **11** | EXP-011 (Event-Native Regime Detection) | Event-native regime feature analysis |
| **12** | Phase 2 retrospective + Phase 3 design | Retrospective document, Phase 3 checkpoint |
