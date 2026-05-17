# Phase 2 Design: Signal-Quality Characterisation
**Phase:** 002 — Signal-Quality Characterisation  
**Date:** 2026-05-16  
**Status:** Active  
**Predecessor:** 2026-05-14-001-chart-type-validation  

**Decision status:** Phase 1 validated the architecture. Time bars are the master timeline. Renko ATR-14 is the primary event-chart layer. Line Break level 3 is a high-confidence confirmation filter. Heiken Ashi is a smoothed signal view, never a return-evaluation price. Phase 2 does not ask which chart type is better; it asks what each validated view contributes to a shared signal-quality objective on the real-price timeline.

**Block A status (complete):** EXP-001-TF through EXP-006-TF completed 2026-05-17. Most Phase 1 findings replicate directionally at higher timeframes. Three findings are 1-minute-conditional: Renko's noise-robustness advantage (EXP-003), the direction of the event-chart latency disadvantage (EXP-004 — which inverts to a latency *advantage* at higher timeframes), and the information-density entropy gain (EXP-001 — which inverts to an entropy *reduction* at higher timeframes). Block B hypotheses and rationales have been updated accordingly. See Block A Verdict for the full generalisation determination.

---

## Phase Objectives

Phase 1 established what each chart type does to price data. Phase 2 establishes whether what each chart type does is useful for producing cleaner, more reliable real-price signals.

The central question is: **when each chart type is used in the role Phase 1 validated for it, does the resulting signal show measurably better real-price outcomes than signals derived from the time-bar timeline alone?**

This phase is still characterisation. It extends the no-P&L boundary: signal quality is measured by real-price excursion, precision, recall, adverse excursion, and run continuation at signal timestamps — not by strategy P&L, optimised parameters, or live execution. No parameter optimisation and no predictive models are introduced in Phase 2.

Phase 2 has two sequential blocks:

**Block A — Timeframe Replication (complete):** EXP-001-TF through EXP-006-TF, completed 2026-05-17. Verdicts recorded below.

**Block B — Signal-Quality Experiments:** Five experiments that test what each chart type's validated strength contributes to real-price signal quality, using a shared measurement framework established in EXP-007.

### EXP-007 as the Functional Gate for Block B

EXP-007 is not a hard gate — a refuted verdict does not automatically terminate Block B. But it is a **functional gate**: EXP-008 through EXP-011 all use the measurement framework EXP-007 validates. If that framework cannot differentiate chart types on any multi-state metric, the downstream experiments have no measurement language to work with and should not run.

The minimum condition to proceed with EXP-008 through EXP-011 is pre-specified and must not be adjusted after EXP-007 results are seen:

**Proceed criterion (any one of the following must hold):**
- For at least one primary metric (FE distribution or AE distribution at the 60-minute window), the difference between the best-performing event chart type and the time-bar baseline is in a consistent direction on at least 3 of 4 instruments, with a bootstrap CI (10,000 resamples, seed 42) excluding zero.
- For signal-level precision, at least one event chart type shows a difference from time bars of ≥ 5 percentage points on at least 3 of 4 instruments, with a bootstrap CI excluding zero.
- For run-continuation rate, at least one event chart type shows a difference from time bars of ≥ 3 percentage points on at least 3 of 4 instruments, with a bootstrap CI excluding zero.

These thresholds are fixed. If none is met at either timeframe (1-minute or 15-minute), Block B stops and the failure-path redirect applies. A partial result — some metrics meet a criterion, others do not — is sufficient to proceed; non-meeting metrics are dropped from downstream experiments.

**If EXP-007 fails entirely** — no multi-state metric differentiates chart types on either timeframe — the logical path forward is not to abandon the programme but to redirect it. The finding would mean that event-chart precision does not translate into better real-price outcomes, and the research question shifts to: *what time-bar-native features produce better signal quality?* Three directions follow directly:

- **Regime-conditional time-bar signals.** The measurement framework built for EXP-007 remains valid; the chart-type dimension is removed. If volatility regime alone differentiates real-price forward excursion, regime-conditional time-bar signals become the focus.
- **Time-bar-native signal filtering.** The 75–85% split-rate redundancy problem does not go away. Filters constructed from run length, volatility-normalised move size, consecutive direction count, or proximity to recent swing extremes — all computable from time bars alone — become the next experimental candidates.
- **HA smoothing as a time-bar feature.** HA's 27–35% direction-change compression is structural and timeframe-invariant. If event charts add no signal value, HA direction can still be tested as a feature alongside raw time-bar direction — not as a separate signal source, but as a smoothing component of a time-bar-native filter. EXP-009's question becomes a feature-engineering question rather than a chart-type contribution question.

In either outcome — partial support or complete failure — the measurement infrastructure, instruments, holdout structure, and architectural discipline established through Phase 1 and Block A carry forward intact.

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
- **Forward excursion (FE):** The maximum favourable real-price move in the N minutes following signal emission, measured in ATR units. N = {30, 60, 120, 240} minutes. Primary metric.
- **Adverse excursion (AE):** The maximum adverse real-price move within the same window, measured in ATR units, computed independently of whether FE is reached first. Primary metric. AE = 0 is a valid and meaningful outcome (price never moved adversely before reaching the target); it must be preserved as-is in distributions and not imputed or replaced.
- **Log FE/AE ratio:** Secondary metric only. Computed as log(FE + ε) − log(AE + ε) where ε = 0.01 ATR, to prevent explosion at AE = 0 and to produce a symmetric, interpretable scale. Raw FE/AE is never used. Where AE = 0 occurs for more than 20% of signals in any stratum, the log-ratio must be flagged and FE and AE reported separately as the primary evidence for that stratum.
- **Run continuation:** Boolean per signal. Whether the 1-minute time-bar close moves in the signal direction by at least 0.1× ATR within a 30-minute window following signal emission. Computed from real time-bar prices only.
- **Signal-level precision:** Fraction of signals where FE at the 60-minute window ≥ 1.0× ATR. Denominator is the count of signals emitted. This metric is bounded [0, 1] by construction — one signal either meets the threshold or does not. It cannot exceed 1.0.
- **Event-level recall:** Fraction of qualifying real-price moves (any 60-minute window starting from a time-bar bar where the subsequent maximum favourable move ≥ 1.0× ATR) that have a corresponding signal within a 30-minute tolerance window. Denominator is the count of qualifying real-price moves, not signals. Reported separately from precision.
- **Signal multiplicity diagnostic:** Count of qualifying real-price moves matched per signal, reported as a distribution. This is a diagnostic, not a primary metric. It replaces the EXP-004 precision-exceeds-1.0 artefact with a well-defined, bounded quantity.

**Metric hierarchy:** FE and AE distributions are primary. Signal-level precision and event-level recall are primary. Log FE/AE ratio is secondary. Run continuation is secondary. Signal multiplicity is diagnostic only. Any experiment that cannot compute a primary metric for a given stratum must report the stratum as missing, not substitute a secondary metric.

**Constraints:**
- All prices resolved from 1-minute time bars at the signal CloseTime/SourceCloseTime, not from any chart-type construction price.
- ATR computed from time bars, train-segment calibrated, matching the EXP-002 and EXP-004 conventions.
- Metrics computed separately per instrument and per volatility regime (train-set tercile labels, same methodology as Phase 1).
- Framework must be deterministic: identical inputs must produce identical outputs across runs. This must be verified by a test that runs the framework twice on the same input and compares outputs exactly.
- Framework must carry explicit missing-signal indicators: if a chart type did not emit in a window, that absence is coded as a measurable state with its own denominator contribution, not excluded.
- No look-ahead in signal construction: signal generation, ATR calibration, regime labels, and confirmation eligibility must not use any price, ATR value, or regime label that could not have been known at the signal emission timestamp. Forward windows are allowed only for post-signal outcome measurement (FE, AE, precision, recall, and run continuation). This must be verified by a test that checks feature, regime, and confirmation lookups are at or before the signal timestamp, while outcome windows start after the signal timestamp.
- All metric denominators must be declared before execution and must not change based on results. Signal-level precision denominator = signals emitted. Event-level recall denominator = qualifying real-price moves in the analysis segment. Neither may be post-hoc filtered.

This framework is the shared evaluation substrate for all Block B experiments. Any Block B experiment that needs a metric not listed above must define it as an extension of the framework, not as a separate ad hoc computation.

---

## Block A: Timeframe Replication — Completed 2026-05-17

EXP-001-TF through EXP-006-TF were completed on 15-minute and 1-hour source bars across all four instruments. The experiments used identical hypotheses, metrics, and scope boundaries as their Phase 1 originals. Results are recorded in the experiments index. The findings below are the generalisation verdict that governs Block B design.

### Block A Verdict

| Phase 1 Finding | Generalises? | Verdict Detail |
|---|---|---|
| Ghost rate elimination (EXP-001) | **Yes — general** | Ghost reduction replicates robustly (70–100%) at both timeframes, all instruments. Structural property of event-chart aggregation. |
| Directional entropy gain (EXP-001) | **No — 1-minute-conditional** | Entropy gains at 1-minute **invert to entropy reductions** at 15-minute and 1-hour. CIs are entirely negative for all combinations. Event charts reduce directional entropy at higher timeframes rather than increasing it. |
| Regime boundary cost / hybrid rate (EXP-002) | **Yes — general and worsening** | Hybrid rates replicate and increase at higher timeframes (up to 0.223 for XAUUSD 1h Renko vs. 0.119 at 1-minute). Structural property; worsens as ATR-based brick size grows relative to regime transition magnitude. |
| Missed regime transitions (EXP-002) | **Yes — general, but attenuated in absolute count** | Missed transitions replicate directionally. In absolute counts they are far smaller at higher timeframes (0–5 per combination vs. 7,000–18,000 at 1-minute) because fewer total transitions occur. The structural coverage gap is real but small in absolute event terms at these timeframes. |
| Tail lag extremes (EXP-002) | **Yes — general, with new outlier** | Tail lag extremes replicate. USTEC 15m LineBreak max lag of 3,376 bars is a new extreme not seen at 1-minute, confirming that rare but severe lag events are a structural feature of LineBreak aggregation. |
| Noise robustness — Renko direction and variance (EXP-003) | **No — 1-minute-conditional** | At 1-minute: 4/4 instruments, CIs excluding zero. At 15-minute: 2/4 instruments. At 1-hour: 0/4 instruments for direction drift, 1/4 for variance drift. The advantage dissolves as the source timeframe increases. Higher-timeframe bars already aggregate intrabar noise, leaving less headroom for event-chart robustness to provide additional benefit. |
| Noise robustness — complexity instability (EXP-003) | **Yes — general** | Complexity drift worsens for event charts under noise at all timeframes. Structural consequence of event-boundary shifts under perturbation. |
| Reversal detection latency disadvantage (EXP-004) | **No — 1-minute-conditional; inverts meaningfully at 15-minute only** | At 1-minute, event charts are 50–55× slower. At 15-minute, FasterCount = 4/4 — a genuine inversion: time bars 30-minute median, Renko 0–15 minutes. At 1-hour, FasterCount = 4/4 but the result is uninformative: all chart types including time bars resolve at 0-minute median latency due to the 60-minute bar floor. The 1-hour latency result is a resolution artefact, not a finding. |
| Reversal detection precision advantage (EXP-004) | **Yes — general** | ~99.7–99.9% Renko precision replicates at 15-minute. Precision is consistently far higher than time bars across all timeframes. The precision advantage is a general property. |
| Time-bar signal redundancy (EXP-004) | **Yes — general** | Time-bar split rates of 75–85% replicate at higher timeframes. Signal noise is a persistent property of raw time-bar direction changes regardless of timeframe. |
| Cross-chart agreement patterns (EXP-005) | **Yes — general** | Hypothesis refuted at all timeframes. LB↔Renko agreement improvement over LB↔Time is 1–2pp (below 10pp threshold) at higher timeframes. HA↔Time agreement ~65% is consistent across all timeframes — structural property of the HA formula. New finding: at 15-minute and 1-hour, LB↔Renko agreement on matched events is exactly 1.0, meaning when both chart types emit within a 5-minute window they never disagree directionally. |
| HA distortion magnitude (EXP-006) | **Yes — general** | Volatility compression 23.5–26.5% across all instruments and timeframes. Direction change compression 27–29% (slightly narrower than 1-minute's 30–35%). The architectural constraint is timeframe-invariant. |

### Block A Implications for Block B

Three Block A findings require changes to Block B experiment rationales and the validated contribution table:

**1. Renko's primary validated strength in Block B is precision, not noise-robustness.** The noise-robustness advantage (EXP-003) is 1-minute-conditional. Renko's precision advantage (~99.9% at 1-minute; ~99.7% at 15-minute) is general across timeframes and is the correct justification for EXP-008's gating architecture.

**2. EXP-007 must test signal-quality at both 1-minute and 15-minute.** The speed/precision trade-off inverts meaningfully at 15-minute, where Renko is faster *and* more precise than time bars simultaneously. The 1-hour timeframe adds no latency signal because the 60-minute bar floor makes all chart types resolve at 0-minute median latency — that result is a resolution artefact and is not informative for signal-quality characterisation. EXP-007 therefore runs at 1-minute and 15-minute only.

**3. EXP-010's Line Break confirmation rationale needs refinement for higher timeframes.** At 15-minute and 1-hour, LB↔Renko agreement on matched events is exactly 1.0 — when Line Break confirms a Renko signal, it will never contradict it directionally. Line Break's confirmation value at higher timeframes is therefore entirely about *coverage selection* (which subset of Renko events does Line Break also confirm?) rather than directional filtering. EXP-010 should test this distinction explicitly.

---

## Block B: Signal-Quality Experiments

### Design Principles

Block B experiments are not chart-vs-chart comparisons. Phase 1 answered the competitive question: each chart type has a specific, validated role. Block A confirmed which of those roles are general across timeframes and which are 1-minute-conditional. Block B tests what each validated role contributes to a shared signal objective.

The validated role of each chart type, updated with Block A generalisation verdicts:

| Chart type | Validated strength | Scope | Validated limitation |
|---|---|---|---|
| Time bars | Complete temporal coverage; exact real-price anchoring; full recall | General across timeframes | High noise throughput; 75–85% signal split rate; 25–28% reversal precision |
| Renko ATR-14 | ~99.7–99.9% reversal precision; near-zero split rate | Precision: general. Noise-robustness: **1-minute only** | Structural regime boundary cost (hybrid rate worsens at higher timeframes); latency relationship inverts — slower than time bars at 1-minute, faster at 15-minute+ |
| Line Break level 3 | Maximum reversal precision (~99.9%); near-zero split rate; strongest bar compression (~25% of time-bar count); perfect directional agreement with Renko on matched events at 15-minute and 1-hour | Precision and compression: general | Low recall (34–40% at 1-minute, lower at higher timeframes); structural regime boundary cost |
| Heiken Ashi | Strongest variance smoothing; 27–35% lower direction-change frequency; high recall with minimal latency | General across timeframes | No bar compression; 23–29% return compression invalidates P&L use; lowest cross-chart agreement (~65%) across all timeframes |

Each Block B experiment uses one or more of these validated strengths and tests whether applying them in combination with the time-bar timeline produces measurably better real-price signal quality than the time-bar baseline alone. Experiments are designed around the contribution each chart type makes, not the chart type as a competitive unit.

All Block B experiments use the shared signal-quality measurement framework defined in Prerequisites.

---

### EXP-007: Multi-State Signal-Quality Baseline

**Hypothesis:** Real-price signal quality cannot be adequately characterised by binary direction alone. A multi-state signal-quality framework — measuring forward excursion, adverse excursion, run continuation, and signal precision and recall in ATR units on the real-price timeline — produces meaningfully differentiated quality distributions across the four chart types and across volatility regimes, providing a baseline measurement vocabulary for all subsequent Phase 2 experiments.

**Question:** What does the signal-quality distribution look like for each chart type when measured on real prices at signal emission timestamps, and is binary direction entropy an adequate summary of that distribution?

**Rationale:** Phase 1 EXP-001 found that binary directional entropy is at or above 0.994 bits for all chart types on all instruments at 1-minute — near the binary ceiling. Block A EXP-001-TF reveals that this is not merely a ceiling effect: at 15-minute and 1-hour, event charts actively *reduce* directional entropy below the time-bar level (CIs entirely negative for all combinations). Binary direction is therefore structurally inadequate as a discriminator at any timeframe — at 1-minute because all chart types saturate the ceiling, at higher timeframes because event charts reduce entropy below the time-bar baseline. A richer signal-quality measurement space is required.

The timeframe dimension also matters for the signal profile directly. Block A EXP-004-TF shows that Renko's speed/precision relationship inverts between 1-minute (slower, more precise) and 15-minute (faster *and* more precise). EXP-007 must characterise signal quality at both timeframes because the contribution structure differs qualitatively.

This experiment does not test a strategy or optimise parameters. It characterises the shape of signal quality for each chart type using the framework defined in Prerequisites, producing the measurement substrate that all other Block B experiments depend on.

**Key metrics:**
- Forward excursion (FE) distribution at 30, 60, 120, 240 minutes per chart type, timeframe, and regime.
- Adverse excursion (AE) distribution in the same windows.
- Log FE/AE ratio distribution per chart type and timeframe.
- Run-continuation rate per chart type and timeframe.
- Signal-quality precision (FE ≥ 1.0× ATR) per chart type, timeframe, and regime.
- Signal-quality recall (qualifying real-price moves captured) per chart type and timeframe.
- Signal-count ratio: how many signals does each chart type emit relative to time bars at each timeframe?
- Comparison of binary direction entropy versus FE-based distribution: does the FE distribution show between-chart-type differences that binary direction cannot, at both timeframes?

**Instruments:** EURUSD, XAUUSD, BTCUSD, USTEC  
**Chart types:** Time Bars (baseline), Line Break level 3, Renko ATR-14, Heiken Ashi  
**Timeframes:** 1-minute and 15-minute (both required; signal profiles are qualitatively different)  
**Scope:**
- Uses the shared real-price signal-quality measurement framework. All excursion metrics resolved from 1-minute time-bar real prices regardless of source timeframe.
- Regime labels computed on time bars, train-set calibrated, same methodology as Phase 1.
- Signal timestamps are chart-type native CloseTime/SourceCloseTime; no bar-index alignment.
- Missing signals (chart types that did not emit in a given window) are coded as an explicit state, not excluded.
- Analysis segment: first 70% by time; final 30% global holdout maintained.
- **Exclusions:** No strategy P&L, no parameter optimisation, no predictive models, no cross-chart combination logic (that is the domain of EXP-008 through EXP-011).

---

### EXP-008: Renko as a Precision Gate Over Time-Bar Signals

**Hypothesis:** Time-bar direction signals that are confirmed by a Renko emission within a defined tolerance window show materially higher real-price forward excursion and lower adverse excursion than the full set of time-bar direction signals, without reducing signal quality relative to raw Renko signals alone.

**Question:** Does using Renko as a precision filter over the time-bar signal pool improve the signal-quality distribution of the filtered subset — on real prices — compared to both the unfiltered time-bar pool and the Renko signal set used alone?

**Rationale:** Phase 1 and Block A establish two complementary properties that are general across timeframes: time bars have complete coverage and full recall but 75–85% split-rate noise and 25–28% precision; Renko has ~99.7–99.9% precision across timeframes. These properties are not competing; they are potentially complementary at different layers. Time bars generate candidates. Renko confirms or rejects.

Importantly, the nature of Renko's contribution differs by timeframe. At 1-minute, Renko is slower than time bars but more precise — a precision trade-off for latency. At 15-minute (EXP-004-TF), Renko is *faster and more precise* simultaneously. EXP-008 tests both cases: the 1-minute latency-cost trade-off and the 15-minute simultaneous speed-and-precision opportunity.

Note: Renko's noise-robustness advantage (EXP-003) is 1-minute-conditional and is not a justification for this experiment's architecture. The gating value of Renko rests on its precision advantage, which is general.

This experiment does not ask whether Renko beats time bars. It asks whether Renko's validated precision, applied as a gate over time-bar candidates, produces a filtered signal set that is better on real-price outcomes than either view alone.

**Key metrics (using shared framework):**
- Signal-quality distribution (FE, AE, log FE/AE, run continuation, precision, recall) for: (a) all time-bar direction signals, (b) Renko-confirmed time-bar signals, (c) Renko signals alone.
- Coverage: what fraction of time-bar signals are confirmed by Renko within the tolerance window?
- Regime-stratified results: does the precision gain differ between low, medium, and high volatility?
- Tolerance window sensitivity: tested at 5-minute, 15-minute, and 30-minute confirmation windows.

**Instruments:** EURUSD, XAUUSD, BTCUSD, USTEC  
**Chart types:** Time Bars (candidate pool), Renko ATR-14 (precision gate)  
**Timeframes:** 1-minute and 15-minute  
**Scope:**
- At 1-minute: the gating trade-off is precision for latency — Renko is slower but more precise. The experiment quantifies whether the precision gain justifies the latency and coverage cost.
- At 15-minute: Renko is faster *and* more precise than time bars simultaneously (Block A EXP-004-TF). The experiment tests whether this stronger property translates into a measurable real-price signal-quality improvement over time bars alone.
- Both timeframes run in the same experiment. Results are reported separately per timeframe and compared. No single "best timeframe" is selected; both are characterised.
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

**Rationale:** Phase 1 established two HA properties relevant here. EXP-003 found that HAClose variance drift is 80–93% lower than time-bar variance drift under noise — the strongest variance-smoothing result in Phase 1 and confirmed as general by Block A. EXP-006 and EXP-006-TF confirmed that HA direction-change frequency is 27–35% lower than real prices across all timeframes (slightly narrower at higher timeframes: 27–29% vs. 30–35% at 1-minute), and the return-compression constraint is timeframe-invariant at 23–29%. Together, these suggest that HA emits fewer, smoother directional transitions at all timeframes tested.

What neither Phase 1 nor Block A tested is whether those fewer, smoother transitions — when evaluated on real prices — represent higher-quality signal candidates. This experiment is the legitimate use case for HA: signal generation (from HA direction), evaluated on the real-price timeline (from time-bar prices at signal timestamps). It is not HA vs. time bars. It is HA-as-smoother tested on the signal-quality dimension that Phase 1 and Block B establish as the right measurement domain.

**Key metrics (using shared framework):**
- Signal-quality distribution (FE, AE, log FE/AE, run continuation, precision, recall) for: (a) time-bar direction changes, (b) HA direction changes evaluated on real prices.
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

**Rationale:** Phase 1 established that Renko has ~99.9% precision with 72–75% recall, and Line Break has ~99.9% precision with only 34–40% recall. From a chart-type competition perspective, Renko dominates. But that framing misses the architectural question: given that Line Break confirms only a subset of Renko signals (because it requires more consecutive confirmed lines before emitting), is that subset a higher-quality subset?

Block A adds a specific finding that sharpens this question. At 15-minute and 1-hour, LB↔Renko agreement on matched events is exactly 1.0: when both chart types emit within the same 5-minute window, they *never* disagree directionally. This means Line Break's confirmation mechanism at higher timeframes is purely about *coverage selection* — which subset of Renko events does Line Break also reach — not about directional filtering. At 1-minute the picture is less clear (matched agreement is high but not 1.0), so the directional filtering question remains open at that timeframe.

EXP-010 therefore tests two distinct things:
- At 1-minute: does Line Break confirmation add directional quality (i.e., are confirmed signals better not just by coverage but also by direction reliability)?
- At 15-minute: does Line Break coverage selection alone — choosing the subset of Renko events that Line Break also confirms — identify a higher-quality subset, even when directional agreement is guaranteed?

This experiment uses Renko as the primary signal layer and Line Break as the confidence stratifier, not as a competitor.

**Key metrics (using shared framework):**
- Signal-quality distribution (FE, AE, log FE/AE, run continuation, precision, recall) for: (a) all Renko signals, (b) Renko signals confirmed by Line Break within the tolerance window, (c) Renko signals not confirmed by Line Break — measured at both 1-minute and 15-minute.
- Coverage cost: what fraction of Renko signals are confirmed by Line Break at each timeframe?
- Directionality of the quality gain: at 1-minute, does confirmation add directional quality? At 15-minute, where directional agreement on matched events is guaranteed (1.0), does Line Break confirmation select structurally different market episodes than Renko alone?
- Regime-stratified results at each timeframe: does Line Break confirmation add more quality in low, medium, or high volatility?
- Tolerance window sensitivity: tested at 5-minute, 15-minute, and 30-minute confirmation windows.

**Instruments:** EURUSD, XAUUSD, BTCUSD, USTEC  
**Chart types:** Renko ATR-14 (primary signal layer), Line Break level 3 (confirmation layer)  
**Timeframes:** 1-minute and 15-minute  
**Scope:**
- Primary signal timestamps from Renko SourceCloseTime; Line Break confirmation tested against Line Break SourceCloseTime within the tolerance window.
- All excursion and return metrics resolved from 1-minute time-bar real prices at Renko signal timestamps, regardless of source timeframe.
- Neither Renko nor Line Break construction prices used in any excursion or return calculation.
- Missing Line Break confirmation (Line Break did not emit in the window) is the non-confirmed case: it must be analysed explicitly, not excluded.
- Regime labels and ATR from time-bar train segment, matching Phase 1 conventions.
- Analysis segment: first 70% by time; final 30% global holdout maintained.
- **Exclusions:** No strategy P&L, no time-bar or HA data in this experiment's primary analysis (time bars are used only as the real-price return anchor), no parameter optimisation.

---

### EXP-011: Event-Native Volatility Regime Detection

**Hypothesis:** Volatility-regime labels derived from event-chart internal features — specifically Renko event density, source-bar count per brick, and running brick-to-ATR ratio — identify volatility regime transitions with lower boundary cost (hybrid rate) and fewer missed transitions than time-bar-derived regime labels applied to Renko events.

**Question:** Can Renko's own internal structure define volatility regimes that align better with Renko event boundaries than the time-bar-derived tercile labels used in Phase 1?

**Rationale:** EXP-002 found that applying time-bar-derived regime labels to event-chart data creates structural boundary costs: Renko hybrid rates of 0.092–0.119 and 17–24% missed transitions at 1-minute. Block A EXP-002-TF shows that this problem is not timeframe-neutral — Renko hybrid rates worsen at higher timeframes (up to 0.223 for XAUUSD 1-hour), reflecting that larger ATR-based brick sizes at higher timeframes span more regime transition boundaries. The structural case for event-native regime detection therefore strengthens across the timeframe range tested.

The question is not whether event-native regimes are better than time-bar regimes in general — time-bar regimes must remain the canonical reference for return evaluation. The question is whether event-native regime features can define Renko-specific regime states that reduce hybrid rate and missed-transition counts, and whether those event-native states produce more differentiated signal-quality distributions when used to stratify EXP-008 and EXP-010 results. If so, Phase 3 can use event-native regime stratification alongside time-bar regimes for signal analysis.

**Key metrics:**
- Three pre-fixed event-native regime features, computed from the Renko train segment only, with no variation after definition:
  1. **Renko event density:** brick count per 60-minute rolling window, tercile-labelled on the train segment.
  2. **Source-bar count per brick:** median source bars consumed per brick in a 60-minute rolling window, tercile-labelled on the train segment.
  3. **Brick-to-ATR ratio:** each brick's price move divided by the train-segment ATR, tercile-labelled on the train segment.
- Regime segmentation is fixed at terciles for all three features. No clustering, no k selection, no alternative segmentation explored. Tercile boundaries computed on the train segment and applied forward without adjustment.
- Hybrid rate of each event-native regime vs. time-bar-derived tercile regime boundaries (same reference as EXP-002).
- Missed-transition rate vs. time-bar-derived transitions (same reference as EXP-002).
- Agreement between each event-native regime label and the time-bar tercile regime label at matching timestamps.
- Signal-quality distribution (FE, AE from shared framework, using only primary metrics) stratified by each event-native regime: does any of the three event-native features produce more differentiated FE distributions across strata than the time-bar tercile regime does? Comparison is descriptive — distributional separation, not optimisation.
- The three features are analysed independently. No composite scoring, no feature selection based on which produces the best signal-quality separation.

**Instruments:** EURUSD, XAUUSD, BTCUSD, USTEC  
**Chart types:** Renko ATR-14 (primary), Time Bars (reference and real-price anchor)  
**Scope:**
- Feature set is fixed: the three features listed above. No additional features may be added after seeing results.
- Segmentation is fixed at terciles for all three features. No alternative segmentation (quartiles, clustering, custom bins) is explored.
- All tercile boundaries computed on the nested train segment (the first 70% of the analysis segment by time, after excluding the final 30% global holdout) and frozen before any signal-quality metrics are computed. Boundaries are not adjusted after seeing signal-quality distributions.
- Event-native features computed from Renko dataset only; no HA or Line Break features in this experiment.
- Time-bar regime labels from train-set calibrated terciles (same as Phase 1) used as the reference for comparison.
- All signal-quality excursion metrics resolved from time-bar real prices.
- **Exclusions:** No strategy P&L, no parameter optimisation of any kind including feature weights or segmentation choices, no composite scoring across features, no selecting the best-performing feature after seeing signal-quality results.

---

## Phase Scope Boundaries

**In scope:**
- Block A: Timeframe replication of EXP-001 through EXP-006 on 15-minute and 1-hour source bars.
- Block B: Signal-quality characterisation using the shared real-price measurement framework.
- Multi-state signal-quality metrics: forward excursion and adverse excursion in ATR units on real prices, plus log FE/AE ratio, run continuation, precision, and recall.
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

3. **Multi-state signal-quality baseline (EXP-007):** A characterised signal-quality distribution for each chart type on real prices, demonstrating whether the FE/AE measurement framework differentiates chart types in ways that binary direction entropy cannot.

4. **Renko-as-gate result (EXP-008):** A quantified precision-coverage trade-off for Renko-confirmed time-bar signals, with regime-stratified results.

5. **HA signal evaluation result (EXP-009):** A quantified comparison of HA direction signals evaluated on real prices versus time-bar direction signals, with signal-count ratio and regime-stratified results.

6. **Line Break confirmation result (EXP-010):** A quantified quality-coverage trade-off for Line Break-confirmed Renko signals, with regime-stratified results and tolerance-window sensitivity.

7. **Event-native regime result (EXP-011):** A determination of whether event-native Renko regime features reduce hybrid rate and missed-transition count relative to time-bar-derived labels, and whether they produce more differentiated signal-quality distributions.

8. **Phase 3 direction:** Enough evidence to determine whether any chart-type combination produces a reproducible, instrument-consistent real-price signal advantage large enough to justify Phase 3 strategy-theory exploration.

---

## Estimated Timeline

| Week | Task | Deliverable |
|------|------|-------------|
| ~~**1**~~ | ~~15-minute and 1-hour bar aggregation pipeline; Block A data preparation~~ | **Complete** |
| ~~**2–3**~~ | ~~EXP-001-TF through EXP-003-TF~~ | **Complete** |
| ~~**4–5**~~ | ~~EXP-004-TF through EXP-006-TF; Block A timeframe generalisation verdict~~ | **Complete — 2026-05-17** |
| **1** | Shared signal-quality measurement framework implementation + validation | Framework utility; unit tests for determinism, no-lookahead, fixed denominators, AE=0 handling, log FE/AE ratio, signal-level precision bounded [0,1], multiplicity diagnostic |
| **2** | EXP-007 (Multi-State Signal-Quality Baseline) at 1-minute and 15-minute | Baseline signal-quality distributions per chart type, both timeframes |
| **3** | EXP-008 (Renko as Precision Gate, 1-minute and 15-minute) | Renko-gating precision-coverage analysis across both timeframes |
| **4** | EXP-009 (HA Signal Evaluated on Real Prices) | HA signal-quality comparison |
| **5** | EXP-010 (Line Break Confirmation Layer, 1-minute and 15-minute) | Line Break stratification analysis; coverage-selection vs. directional-filtering distinction |
| **6** | EXP-011 (Event-Native Regime Detection) | Event-native regime feature analysis, hybrid-rate reduction assessment |
| **7** | Phase 2 retrospective + Phase 3 design | Retrospective document, Phase 3 checkpoint |
