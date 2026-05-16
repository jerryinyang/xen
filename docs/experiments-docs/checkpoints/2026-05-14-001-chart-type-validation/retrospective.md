# Independent Retrospective: Phase 1 Chart-Type Validation
**Checkpoint:** 2026-05-14-001-chart-type-validation  
**Experiments:** EXP-001 through EXP-006  
**Design date:** 2026-05-14  
**Retrospective date:** 2026-05-16  
**Status:** Phase Completed — All Experiments Adjudicated  
**Assessor:** Independent Audit Agent  

---

## 1. Preamble and Scope

This document is an independent assessment of the Phase 1 experimental checkpoint. It synthesizes all six experiments (EXP-001 through EXP-006), cross-references findings against the Phase 1 design commitments in `design.md`, and draws conclusions about model implications, architecture integrity, and recommended next steps. It is produced independently of the audit agent's retrospective and should be read as a parallel, not derivative, evaluation.

All experiments complied with the global 30% holdout boundary, used timestamp-aligned (not bar-index-aligned) cross-chart comparisons, and remained within Phase 1's characterization-only perimeter. No strategy P&L, parameter optimization, or predictive model validation was performed in any experiment.

---

## 2. Experiment Status Summary

| Experiment | Question | Verdict | Governance |
|------------|----------|---------|------------|
| EXP-001 | Information density and ghost bar comparison | REFUTED | APPROVED |
| EXP-002 | Volatility and trend regime representation | REFUTED | APPROVED |
| EXP-003 | Noise filtering and statistical robustness | SUPPORTED (with qualification) | APPROVED |
| EXP-004 | Market structure capture speed and fidelity | REFUTED | APPROVED |
| EXP-005 | Cross-chart-type alignment and regime correspondence | REFUTED | APPROVED |
| EXP-006 | Heiken Ashi synthetic price distortion quantification | REFUTED | APPROVED |

Five of six hypotheses were refuted. This is not a research failure. The hypotheses were specific and falsifiable; their refutations are coherent, mutually reinforcing, and yield a precise empirical picture of what each chart type does and does not provide.

---

## 3. Comparative Evaluation

### 3.1 Time Bars — The Ground Truth Layer

Time bars did not enter Phase 1 as a hypothesis subject; they served as the measurement substrate. This role is validated, not merely assumed, by the experimental evidence.

EXP-002 establishes that time bars, by construction, have zero hybrid rate and zero regime-transition lag. EXP-004 shows a median reversal detection latency of 2.0 minutes and ~100% recall. EXP-006 requires real time-bar prices as the evaluation anchor for HA distortion diagnostics. EXP-005 finds that both Line Break and Renko show stronger alignment with time bars than with each other on matched-denominator paired sets. In every experiment where time bars were tested alongside event charts, they emerged as the complete-coverage, exact-timing reference.

The real weakness is noise throughput. EXP-001 documents ghost rates up to 8.99% on EURUSD. EXP-004 reports a reversal signal split rate of 83–85% and precision of only 26–28%. A system that naively consumes raw time-bar direction changes as signals will experience severe redundancy and low signal-to-noise. This is not an argument against time bars as the base layer; it is an argument for pairing them with event-chart denoising filters.

**Assessment:** Time bars are irreplaceable as the canonical timeline. Their limitations are real but well-characterized.

### 3.2 Line Break Level 3 — The Precision Filter

Line Break is the most aggressive noise suppressor tested. It reduces bar count to approximately 25% of the time-bar baseline and eliminates ghost bars entirely. Reversal signal precision reaches ~99.9% with a near-zero split rate. These properties make it the cleanest possible signal emitter when a signal is emitted.

However, the cost structure is steep:

- EXP-002: Hybrid rates of 0.064–0.086 on all instruments, exceeding the 0.05 bound. Missed regime transitions range from 25% to 34%. Tail lags are severe: P95 of 12–14 bars; max lags of 158–660 source bars on individual instruments.
- EXP-004: Median reversal latency is 110–111 minutes — approximately 55× the time-bar baseline. Recall is only 34–40%.
- EXP-003: Sequence complexity drift is higher than time bars (LZ76 mean difference +0.0153, CI [0.0131, 0.0175]). Return-variance drift is mixed: CI includes zero for Line Break, indicating limited robustness on this metric.
- EXP-005: On the paired bootstrap subset, Line Break agrees marginally more with time bars than with Renko — refuting the expectation of independent event-chart confirmation.

A key structural insight from EXP-004 is that Line Break's high precision is mechanically enforced by the level-3 confirmation rule, not by superior trend detection. It takes longer precisely because it waits for three prior confirmed lines before emitting a signal. That patience makes it precise but slow and sparse.

**Assessment:** Line Break level 3 is a high-confidence confirmation filter, not a broad detector. It is appropriate for applications that tolerate low signal frequency and high signal-quality requirements. It should not be used as the primary source of volatility-regime or reversal coverage.

### 3.3 Renko ATR-14 — The Preferred Event-Chart Baseline

Renko is the most balanced event chart tested. Its validation profile across six experiments is more consistent than Line Break's and offers materially better recall coverage.

Validated advantages over time bars:
- Ghost rate of 0.00005–0.0024: effectively zero.
- EXP-003: Direction drift lower on all 4 instruments at 20% noise (MeanDiff −0.0050, CI [−0.0104, −0.0011]); return variance drift lower on all 4 instruments (MeanDiff −0.0040, CI [−0.0059, −0.0023]). These are the only metrics with instrument-consistent, CI-excluding-zero advantages.
- EXP-004: ~99.9% reversal precision; recall of 72–75%, substantially better than Line Break's 34–40%.
- EXP-002: Missed transitions 17–24%, better than Line Break's 25–34%. Tail lag P95 of 7 bars and max lag 24–40 — far tighter than Line Break's 158–660.
- EXP-001: Entropy increase is positive on all 4 instruments (bootstrapped mean +0.0016, CI [0.0002, 0.0043]).

Validated costs:
- EXP-002: Hybrid rates of 0.092–0.119, the worst among chart types tested.
- EXP-004: Median latency 101–105 minutes, still ~50× slower than time bars.
- EXP-003: Sequence complexity drift higher than time bars (LZ76 mean difference +0.0083, CI [0.0070, 0.0097]).
- EXP-001: 12–13% same-source duplicate rows require explicit denominator handling in all downstream analysis.

A nuanced EXP-005 finding deserves independent attention: Renko agrees with time bars substantially more than with Line Break on the paired bootstrap subset (difference −13 to −15 pp when Renko is the reference). This is counterintuitive if one assumed event charts form a coherent independent cluster. The ATR-based sizing of Renko naturally tracks realized price amplitude — the same signal embedded in time-bar price ranges. This explains both the higher recall and the closer time-bar alignment. Renko is not independent of the time-bar signal; it is a smoothed expression of it.

**Assessment:** Renko ATR-14 is the strongest candidate for Phase 2 event-chart feature development. Its robustness advantages are the only cross-instrument, CI-excluding-zero advantages in Phase 1. However, it should be architected as an event-layer attached to the time-bar timeline, not as an autonomous price representation.

### 3.4 Heiken Ashi — The Smoothing Transform

Heiken Ashi is categorically different from Line Break and Renko. It is a 1:1 per-bar transformation — it does not aggregate, compress, or create event-based timing. Every time bar produces exactly one HA bar. This means all regime-timing metrics in EXP-002 are identical to time bars by construction, not by virtue of any detection capability.

The experimental profile is internally consistent:

- EXP-001: No ghost-rate improvement, no bar compression, no entropy gain. HA is irrelevant to information density.
- EXP-002: Identical regime timing to time bars — an artifact of 1:1 mapping, not a genuine advantage.
- EXP-003: Strongest variance drift reduction (MeanDiff −0.0770, CI [−0.0788, −0.0754]). This is real but expected: HA averaging compresses the signal range, which mechanically reduces variance sensitivity.
- EXP-004: High recall (~100%), but precision of only 52–56% and split rate of 47–51%. HA smoothing does not clean up signal redundancy.
- EXP-005: Lowest pairwise agreement with time bars (~65%). HA direction labels are structurally different from raw bar direction because they encode multi-bar averaging.
- EXP-006: Volatility compression consistently ~25–26% across all four instruments. Direction change frequency 30–35% lower than real prices. The 30% compression threshold was refuted (actual: 25–26%), but the practical conclusion — HA prices are invalid for strategy-return evaluation — is unchanged and supported with very tight bootstrap CIs.

One finding in EXP-006 is worth flagging specifically: HA mean range is *higher* than the real mean range. This is not compression in the conventional sense. HAOpen and HAClose averaging expands the apparent body while HAHigh and HALow remain bounded by real extremes, meaning the HA candle body appears wider relative to its wick. This bidirectional distortion — downward compression of return magnitude, upward expansion of candle range — adds complexity to any HA-based volatility model.

**Assessment:** Heiken Ashi's value is narrowly defined: smoothed directional state representation for signal generation, never for return evaluation. Its synthetic-price discipline must be structurally enforced at the code level.

---

## 4. Performance Insights

### 4.1 The Ghost Rate Hypothesis Was Half Right

EXP-001 confirms that event charts eliminate ghost bars structurally. LineBreak3 achieves zero ghost rate universally; Renko reaches near-zero. This is a real and useful property. But the hypothesis conflated ghost elimination with information gain. The directional entropy analysis separates these:

- Directional entropy is at or above 0.994 bits for every chart type on every instrument — near the binary ceiling.
- Only EURUSD meets all three information-density thresholds (ghost rate reduction ≥25%, headroom capture ≥50%, absolute entropy gain ≥0.005 bits).

This ceiling effect is a design signal. Binary direction is not a discriminative feature space for this dataset. Phase 2 cannot make progress using binary direction entropy as its primary information metric.

### 4.2 Regime Boundary Cost Is Structural, Not Incidental

EXP-002 shows that event chart aggregation is not regime-neutral. When a volatility regime transition occurs mid-event-bar, that bar spans two regimes — a hybrid bar. This is not a calibration problem; it is a consequence of the aggregation mechanic. Larger event-bar sizes relative to volatility changes produce higher hybrid rates.

This has a concrete implication for Renko. Its higher hybrid rates compared to Line Break (0.092–0.119 vs. 0.064–0.086) reflect the ATR-based brick size: larger bricks relative to regime transition magnitude produce more hybrid events. This is the same property that gives Renko better recall (bricks are reached more frequently than Line Break's multi-line reversals), but it creates more regime-straddling events.

The practical architecture response is clear: regime labels must be computed on time bars and joined to event charts by timestamp, not recomputed on event-chart native coordinates.

### 4.3 The Speed Hypothesis Inverted: Event Charts Are Precise, Not Fast

The most consequential refutation across Phase 1 is EXP-004. The original hypothesis stated that Line Break and Renko detect trend reversals *faster* than time bars. The measured result is the opposite: Line Break and Renko are 50–55× *slower* at median latency. This is not a borderline refutation; it is a direction reversal.

The correct framing that emerges from EXP-004 is precision vs. recall, not speed vs. noise. Event charts do not speed up reversal detection; they defer emission until the event is confirmed by their native aggregation rules. That deferral is what produces precision (~99.9%) at the cost of recall (34–75%) and latency (100+ minutes).

This finding should reshape how Phase 2 models are designed. A model expecting fast event-chart signals will be frequently surprised by silence — the chart type simply has not emitted yet. Architecture must treat event-chart silence as informative, not as missing data.

### 4.4 Noise Robustness Is the Genuine, Data-Grounded Event-Chart Advantage

EXP-003 is the only supported Phase 1 hypothesis, and its Renko results are the most consistently positive findings in the checkpoint:

- Direction drift: lower on all 4 instruments, CI excludes zero.
- Return variance drift: lower on all 4 instruments, CI excludes zero.
- These are the only results with consistent direction and CI-excluding-zero support across all instruments.

Line Break's direction drift advantage holds on 3 of 4 instruments, but its return-variance result is mixed. HA's variance drift reduction is real but reflects synthetic price averaging, not genuine robustness of the underlying signal.

The cost of this robustness is sequence complexity. Both event charts show higher LZ76 complexity drift than time bars under noise, meaning that noise does not just perturb event-chart values — it changes event boundaries, direction sequences, and event counts. A model that treats event-chart sequences as deterministic encodings of market structure will be fragile to noise-induced boundary shifts.

### 4.5 Cross-Chart Agreement Is Dominated by Denominator Effects

EXP-005's raw agreement numbers (LB↔Renko ~90%) create a misleading impression of independent confirmation. The paired bootstrap corrects this. When the comparison is made on matched reference events — the correct denominator — Line Break agrees *marginally more* with time bars than with Renko (difference −0.7 to −3.2 pp), and Renko agrees *substantially more* with time bars than with Line Break (difference −13 to −15 pp).

The agreement gradient by volatility regime (1–2 pp per step, low to high) is real but small. Stronger trends produce clearer directional signals that all chart types can agree on. This is structurally expected and does not validate event charts as independent confirmation mechanisms.

### 4.6 HA Distortion Is Consistent, Bounded, and Instrument-Invariant

EXP-006's ~25–26% volatility compression finding is unusually consistent across four instruments spanning forex, commodity, crypto, and equity index. The point estimates span a range of only 0.6 percentage points (EURUSD 25.4% to XAUUSD 26.0%). This is a structural property of the HA formula, not an instrument-specific effect.

The practical conclusion — HA prices must not be used for strategy returns — does not depend on whether compression reaches 30%. The 25–26% measured compression is large enough to materially distort realized P&L and volatility estimates. The 30% threshold in the hypothesis was calibrated on the expectation of a more severe distortion; its refutation does not soften the architectural constraint.

---

## 5. Model Implications

### 5.1 Timeline-First Architecture Is Validated

The Phase 1 design decision to store 1-minute time bars as the canonical data unit is not merely a practical choice — it is empirically necessary. Every experiment that required ground-truth evaluation (regime timing in EXP-002, real reversal references in EXP-004, real-price returns in EXP-006) used time bars as the anchor. No event-chart-native timeline could have served as a substitute without introducing the regime boundary cost documented in EXP-002 or the latency bias documented in EXP-004.

The model architecture should maintain this structure formally:
- Time bars are the index. Splits, holdouts, and regime labels are defined on this index.
- Event-chart data is an irregular overlay, joined by timestamp, not by bar count.
- Return labels are resolved from time-bar prices at signal timestamps.

### 5.2 Event Missingness Must Be a First-Class Feature

The most underappreciated finding across Phase 1 is that event-chart silence is informative. Line Break emitting no signal between regime transitions (25–34% of transitions missed) and no reversal signal (60–66% of real reversals missed) is not a data gap — it is the chart type's behavior under its aggregation rules. Similarly, Renko's 17–24% missed transitions and 25–28% missed reversals are structural properties.

Phase 2 feature engineering should treat event-chart silence as a first-class state. Features to develop include:

- Time since last event (per chart type).
- Source bar count since last event.
- Event count in rolling time windows.
- Boolean: did each chart type emit within a tolerance window of the label timestamp?
- Duplicate-source event count for Renko.

A model that treats missing events as nulls to be filled or dropped will lose information systematically.

### 5.3 Sequence Complexity Degrades Under Noise, Requiring Robust Event Representations

EXP-003 shows that under controlled noise injection, event-chart sequence complexity (LZ76) increases more than time-bar complexity. This means that noise changes the *structure* of event sequences — not just their values. If a model encodes event-chart history as a sequence of direction states, those sequences are not stable under perturbation.

This suggests that future model features should focus on event properties rather than event-sequence position:

- Event magnitude (price move per event).
- Event duration (source bars consumed).
- Event direction confidence (how close to the reversal threshold at emission).
- Event-density features over time windows.

Positional event sequence models (e.g., treating event N as a fixed positional input) will be fragile to boundary-shift noise.

### 5.4 Binary Direction Is an Inadequate Target Space

Phase 1's consistent entropy-ceiling finding (directional entropy ≥0.994 bits for all chart types on all instruments) is a strong signal that binary direction labels will not discriminate between chart types in a learning setting. Every chart type saturates the binary entropy metric. Models trained to predict binary direction from chart-type features will likely default to noise-fitting.

Phase 2 should evaluate richer target definitions:
- Multi-state movement classes (e.g., sustained trend, reversal, consolidation).
- Run-length features: how many consecutive same-direction events occur after a signal.
- Event quality: forward real-price excursion in a window after a signal emission.
- Adverse excursion: maximum adverse real-price move before a follow-through is reached.
- Regime-conditioned signal precision and recall as label quality metrics.

### 5.5 Synthetic Price Segregation Must Be Structurally Enforced

Phase 1 confirms that both HA and Renko construction prices are invalid for return evaluation, but for different reasons. HA compresses realized volatility by ~25–26%. Renko brick prices are threshold-aligned synthetic levels that do not track real price continuously.

Relying on analysis discipline to separate synthetic from real prices is fragile at scale. The recommended architectural enforcement:

- A real-price return utility that accepts a list of signal timestamps and resolves all returns against the time-bar price series. This function should not accept HA or Renko price fields.
- Signal-generation APIs may reference HA or Renko construction fields.
- Any use of construction prices in a return-related computation should require an explicit diagnostic flag — and that flag should not exist in any production code path.

### 5.6 Cross-Chart Agreement Features Require Denominator Discipline

EXP-005's lesson is directly applicable to feature engineering. Raw LB↔Renko agreement (~90%) is not a valid model-confidence feature because it confounds event-density differences with trend-direction agreement. A model that uses raw cross-chart direction matching as a confidence signal will systematically overestimate agreement during dense-event periods and underestimate it during sparse periods.

Cross-chart agreement features must be constructed with explicit:
- Reference population (which chart type defines the event-set denominator).
- Tolerance window (how close in time counts as matching).
- Missing-event handling (whether non-emission is coded as disagreement or excluded).

These must be the same across training and inference to avoid silent leakage.

---

## 6. Instrument-Level Differentiation

### 6.1 EURUSD

EURUSD is the clearest differentiated instrument in Phase 1. It is the only instrument where LineBreak3 and Renko meet all three EXP-001 information-density thresholds. It also has the highest time-bar ghost rate (8.99%), which creates genuine headroom for event-chart entropy improvement. EURUSD's entropy response to event-chart sparsification is qualitatively different from the other three instruments, suggesting that the forex microstructure at this tick density produces more economically empty bars than commodity, crypto, or index instruments.

This makes EURUSD the instrument where event-chart ghost elimination is most practically valuable, not just structurally guaranteed.

### 6.2 XAUUSD

XAUUSD shows the weakest event-chart information-density response: LineBreak3 entropy change is negative (−0.00009 bits) and headroom capture is −0.17, meaning Line Break actually *reduces* directional entropy relative to time bars. EXP-003 also notes that XAUUSD has the smallest absolute time-bar direction drift under noise — leaving less room for event charts to demonstrate a comparative robustness advantage. EXP-002 shows Renko achieving its highest hybrid rate on XAUUSD (0.119). XAUUSD may require different event-chart parameters or a different characterization approach in Phase 2.

### 6.3 BTCUSD

BTCUSD has the largest analysis set (1,088,940 bars) and a very low time-bar ghost rate (0.35%). Event charts eliminate the small ghost fraction, but there is little entropy headroom to exploit. The large dataset makes BTCUSD the most statistically reliable instrument for Phase 2 experiments that need high event counts. EXP-004 shows that BTCUSD follows the cross-instrument pattern precisely, suggesting it is not an outlier for reversal detection studies.

### 6.4 USTEC

USTEC shows the lowest event-chart hybrid rates in EXP-002 (LineBreak3: 0.064, Renko: 0.092) — still above the 0.05 threshold but comparatively better than other instruments. This suggests that USTEC's volatility regime transitions produce fewer mid-event-bar transitions, possibly due to its equity index characteristics (e.g., lower overnight gap frequency in the analysis window, or smoother intraday volatility patterns). USTEC also shows the lowest time-bar reversal precision in EXP-004 (~25.6%), reinforcing the utility of event-chart precision filtering for this instrument.

---

## 7. Practical Conclusions

### 7.1 What the Data Support

**Use time bars as the mandatory base layer.** No alternative timeline is available that provides complete temporal coverage, exact regime timing, and real-price return evaluation simultaneously.

**Use Renko ATR-14 as the default Phase 2 event-chart feature layer.** Its noise-robustness results are the only consistent, CI-excluding-zero, all-instrument advantages in Phase 1. Its higher recall (72–75%) relative to Line Break (34–40%) means it covers a broader set of market events. Its manageable duplicate-source rate (12–13%) and bounded tail lag (P95: 7 bars, max: 24–40) make it operationally tractable.

**Use Line Break level 3 selectively, as a precision confirmation feature.** Its near-zero split rate and ~99.9% reversal precision are genuinely useful for applications that require high-confidence signals. Its latency (110–111 minutes median) and low recall (34–40%) mean it should supplement Renko, not replace it.

**Use Heiken Ashi for smoothed state features only.** Its variance compression and direction-smoothing properties may be useful signal inputs. HA-derived return computation is architecturally prohibited.

### 7.2 What the Data Refute

Do not use event charts as primary reversal detectors expecting speed advantages. EXP-004 shows a 50–55× latency penalty relative to time bars.

Do not assume event-chart hybrid rates are an acceptable approximation of time-bar regime boundaries. EXP-002 shows 17–34% missed regime transitions — a structural, not incidental, coverage gap.

Do not treat high raw LB↔Renko agreement as evidence of independent trend confirmation. EXP-005's paired bootstrap shows the relationship is dominated by shared noise-filtering methodology and Renko's natural ATR-time-bar alignment.

Do not assume HA distortion must exceed 30% to matter for strategy evaluation. The measured ~25–26% compression is large enough to materially invalidate HA-based return estimates.

Do not rely on binary directional entropy as a discriminative metric for Phase 2 experiments. All chart types saturate the binary ceiling on all instruments.

---

## 8. Recommended Next Steps

### 8.1 Immediate Architecture Actions (Pre-Phase 2)

The following infrastructure changes are warranted before Phase 2 experiments begin:

**Real-price return utility.** A shared function that accepts signal timestamps and resolves all returns from time-bar prices exclusively. HA and Renko construction price fields must not be acceptable inputs to this function.

**Event-state feature library.** Reusable utilities for time-since-last-event, source-bar-count-since-last-event, rolling event density, per-chart-type emission boolean within a tolerance window, and Renko duplicate-source event count. These should be produced by the same deterministic generators, not recomputed ad hoc.

**Denominator-explicit agreement utilities.** Cross-chart comparison functions must require the caller to declare: reference chart type (defines the event denominator), comparison chart type, tolerance window (in minutes), and missing-event handling (disagree vs. exclude). Undeclared denominators should fail.

**Renko duplicate-source event handling.** EXP-001 documents 12–13% same-source duplicate rows. These should be preserved in the dataset with an explicit `is_duplicate_source` flag, not silently deduplicated. Downstream analysis may choose to aggregate or exclude them, but the raw event structure should be preserved.

### 8.2 Prerequisite: Complete the Phase 1 Timeframe Dimension Before Phase 2

The research setup document specifies that timeframe should be treated as a major experiment dimension, with hypotheses tested across `1min`, `15min`, `30min`, `1h`, `4h`, and `1d` where appropriate. The design document lists "Timeframe as a hyperparameter (experiments may be repeated on different timeframes)" explicitly within Phase 1's in-scope boundary. Individual experiment scopes deferred higher-timeframe comparison rather than excluding it from the programme.

Every Phase 1 experiment ran on 1-minute source bars only. This means all six refutations and the one supported hypothesis are conditional on a single timeframe. The conclusions about ghost rates, hybrid rates, reversal latency, noise robustness, and HA distortion may look materially different at 15-minute or 1-hour aggregation, where time bars are already natively smoother and ATR-based event sizes are proportionally larger.

Before committing to a Phase 2 design, EXP-001 through EXP-006 should be repeated on at least 15-minute and 1-hour source bars. The generators are already timeframe-agnostic and the experimental frameworks are defined; implementation cost is low. The outcomes fall into two cases:

- **Effects replicate across timeframes:** Phase 1 findings are general properties of event-chart aggregation, not 1-minute microstructure artifacts. Phase 2 can build on them with confidence.
- **Effects do not replicate:** Phase 1 conclusions are timeframe-conditional. Phase 2 must treat timeframe as an active variable in every experiment rather than a fixed assumption inherited from characterization.

Either outcome materially shapes the Phase 2 design. Running Phase 2 without this information risks building signal-quality experiments on findings that are specific to 1-minute behaviour.

### 8.3 Phase 2 Experiment Design Principles

Phase 1's central lesson for Phase 2 design is that each chart type has a validated, specific role — and those roles do not overlap. Phase 2 experiments should not be structured as "chart A vs chart B" comparisons asking which is better overall. They should be structured around what each chart type is now known to *contribute*, with the shared objective being real-price signal quality on the time-bar timeline.

The validated contribution map from Phase 1:

| Chart type | Validated strength | Validated limitation |
|---|---|---|
| Time bars | Complete temporal coverage; exact regime timing; real-price anchoring; full recall | High noise throughput; low reversal precision (26–28%); 83–85% signal split rate |
| Renko ATR-14 | Direction and variance stability under noise (all 4 instruments, CI excludes zero); high reversal precision (~99.9%); 72–75% recall; manageable tail lag | Structural regime boundary cost; 50× reversal latency; complexity instability under noise |
| Line Break level 3 | Maximum reversal precision (~99.9%); near-zero split rate; strongest compression (25% of time-bar count) | Lowest recall (34–40%); 55× reversal latency; 25–34% missed regime transitions; mixed variance robustness |
| Heiken Ashi | Strongest variance smoothing under noise; high recall with low latency penalty; 30–35% direction-change reduction | No bar compression; ~25–26% return compression invalidates P&L evaluation; lowest cross-chart agreement |

Phase 2 experiments should ask: given that each chart type does what Phase 1 says it does, how does combining their validated strengths produce better real-price signal characterization than any single view alone?

### 8.4 Phase 2 Experiment Priorities

The experiments below follow from Phase 1 findings. They are framed around signal objectives, not chart-type competition.

**Priority 1: Time-bar noise reduction using Renko as a precision gate.**  
Rationale: Time bars have the best coverage and real-price anchoring but suffer 83–85% signal split rate and 26–28% reversal precision (EXP-004). Renko has ~99.9% precision but 50× latency cost when used alone. The question is not "which is better?" but "can Renko's confirmed events be used to gate or score time-bar signal candidates, improving time-bar precision without sacrificing coverage?" This uses time-bar full recall as the candidate pool and Renko's validated denoising as the filter — a multi-view architecture grounded in Phase 1 findings.

**Priority 2: HA smoothing as a signal generator evaluated on real prices.**  
Rationale: EXP-003 confirms HA reduces variance drift more strongly than any event chart (MeanDiff −0.0770). EXP-006 confirms HA direction-change frequency is 30–35% lower than real prices. What Phase 1 did not test is whether HA's smoothed direction — evaluated at signal emission timestamps against *real* time-bar prices — produces better forward real-price outcomes than raw time-bar direction changes. This uses HA in its validated role (smoothing, not return evaluation) and time bars in their validated role (real-price anchoring). It is not HA vs. time bars; it is HA-generated signals evaluated on the time-bar timeline.

**Priority 3: Multi-state signal quality characterization.**  
Rationale: EXP-001's binary direction entropy ceiling (≥0.994 bits for all chart types on all instruments) shows that binary direction cannot discriminate between chart-type signal quality. Phase 2 needs a richer signal-quality measurement framework. Candidate target states: run-continuation duration after a signal, forward real-price excursion in a defined window, adverse excursion before follow-through, and volatility-normalized movement class. These should be defined once as a shared measurement framework and applied consistently across all subsequent Phase 2 experiments — not designed separately per experiment.

**Priority 4: Line Break as a confirmation layer over Renko signals.**  
Rationale: Phase 1 establishes that Line Break's 99.9% precision and Renko's 72–75% recall are not competing properties — they are complementary ones operating at different latency and coverage levels. The experiment question is: of the Renko signals that are also confirmed within a tolerance window by a Line Break emission, do real-price outcomes differ materially from the full Renko signal set? This is not "Line Break vs. Renko" — it is a test of whether Line Break confirmation adds measurable signal quality over Renko alone, using each chart type's validated strength.

**Priority 5: Event-native volatility regime detection.**  
Rationale: EXP-002 shows that applying time-bar-derived regime labels to event charts creates 17–34% missed transitions and 0.064–0.119 hybrid rates. The unresolved question is whether event-chart-internal features — Renko event density, source-bar count per brick, running ATR-to-brick-size ratio — can identify volatility-regime states that better match event-chart natural boundaries. This should be evaluated against time-bar regime labels as a reference. It is not a replacement; it is a test of whether event-native regime detection reduces boundary cost in event-chart signal analysis.

### 8.5 Deferred to Phase 3 or Later

The following are not warranted in Phase 2:

- Strategy P&L evaluation of any chart-type-derived signal. This boundary should hold until at least one signal-quality experiment (Priority 1 or 2 above) produces a reproducible real-price signal advantage.
- Live trading integration or cAlgo chart-type transmission. Phase 1 confirms that the Python generator approach is adequate; live integration introduces operational risk without research benefit at this stage.
- Additional instruments beyond EURUSD, XAUUSD, BTCUSD, USTEC. The four-instrument set is adequate for Phase 2 characterization. New instruments should only be added after Phase 2 hypotheses identify instrument-specific signal effects worth confirming.
- Parameter sweeps over Line Break level or Renko ATR period. Phase 1 parameters (Level 3, ATR 14) were fixed for characterization. Parameter sensitivity is a valid Phase 2 question, but it should follow the signal-quality framework being established in Priorities 1–5 above, not precede it. Parameter optimization without a defined signal-quality objective risks producing parameters tuned to characterization metrics rather than real-price signal outcomes.

---

## 9. Caveats and Limitations

Phase 1 uses one historical collection window per instrument. The documented effects — ghost rates, hybrid rates, precision, recall, compression ratios — are measured on the available 70% analysis segment. They may not generalize identically to different market regimes, particularly if the analysis window contains an unusual concentration of trending or ranging behavior.

Most bootstrap intervals in Phase 1 are derived from instrument-level means. For effects that are consistent across all four instruments and where point estimates are well away from the threshold (e.g., Renko direction drift, HA volatility compression), the evidence is robust. For effects that are instrument-specific (e.g., EURUSD entropy improvement, XAUUSD hybrid rate outlier), the sample of four instruments is not sufficient to draw general conclusions.

EXP-002's missed-transition rates (17–34%) depend on the definition of "regime transition": a tercile change in rolling realized volatility (window=20 bars, train-set calibrated). Alternative regime definitions would produce different missed-transition rates. The finding that event charts structurally miss some transitions is robust; the specific magnitude is definition-dependent.

EXP-006's regime threshold calibration used the full analysis segment rather than a strictly nested train segment. This is an accepted documentation-level caveat. Aggregate HA compression and the refuted verdict are not affected.

### 9.1 The Timeframe Dimension Was Not Executed

This is a significant unaddressed gap. The Phase 1 design explicitly includes "Timeframe as a hyperparameter (experiments may be repeated on different timeframes)" in its in-scope list. The research setup document is more emphatic: "Treat timeframe as a major experiment dimension. Test the same hypothesis across timeframes where appropriate (`1min`, `15min`, `30min`, `1h`, `4h`, `1d`, etc.)."

Every experiment in this checkpoint ran on 1-minute source bars only. Individual experiment scopes for EXP-001 and EXP-002 explicitly list "no higher-timeframe comparison" as an exclusion — meaning higher timeframes were deferred within Phase 1, not abandoned from the programme.

This matters materially for how confidently Phase 1 conclusions can be stated. All six refutations and the one supported hypothesis are conditional on the 1-minute timeframe. Several findings may not hold at higher timeframes:

- **Ghost rate and information density (EXP-001):** The 8.99% EURUSD ghost rate at 1-minute reflects microstructure activity at that resolution. At 15-minute or 1-hour aggregation, ghost rates for time bars will be lower, potentially reducing the relative ghost-elimination advantage of event charts.
- **Regime boundary cost (EXP-002):** Hybrid rates are a function of the ratio between event-bar size and regime-transition granularity. At higher timeframes, ATR-based Renko bricks are larger, and regime transitions occur across fewer source bars — changing the boundary-cost profile substantially.
- **Reversal latency (EXP-004):** The 101–111 minute median event-chart latency measured against 2-minute time-bar latency is specific to 1-minute source bars. At 1-hour time bars, the time-bar latency is already 60 minutes per bar, compressing the latency gap between event charts and time bars considerably.
- **Noise robustness (EXP-003):** The controlled noise injection used 1-minute close perturbation. At higher timeframes, the underlying bars already aggregate intrabar noise. The relative advantage of event charts in filtering injected noise may differ — higher-timeframe bars are natively smoother, reducing the headroom for event-chart robustness improvements.

**Recommended action:** Before closing Phase 1 and moving to Phase 2, the six experiments should be repeated on at least two higher timeframes — 15-minute and 1-hour are the natural candidates given the research setup's listed examples. These repetitions share the same hypotheses, scope boundaries, and generators; the implementation cost is low because the generators are already timeframe-agnostic. The outcome determines whether Phase 1 conclusions are 1-minute-specific observations or general properties of event-chart aggregation. If the effects replicate at higher timeframes, the Phase 2 architecture can be designed with greater confidence in the chart-type characterizations. If they do not, Phase 2 will need to treat timeframe as an active variable in every experiment rather than a fixed assumption.

---

## 10. Final Assessment

Phase 1 validates the Xen architecture and refutes five of six original hypotheses with precision and consistency. The refutations form a coherent picture of what each chart type does and does not provide. That picture is valuable precisely because it is specific: it rules out several incorrect assumptions about event-chart superiority and identifies, with quantitative evidence, the narrow roles in which each chart type is genuinely useful.

There is one material gap: the timeframe dimension. The design and research setup documents both commit to treating timeframe as a major experiment variable. None of the six experiments executed this. All findings are conditional on 1-minute source bars. The gap does not invalidate Phase 1's conclusions, but it constrains how confidently they can be generalized. The timeframe repetitions should be completed before Phase 2 experiment design is finalized.

Subject to that caveat, the Phase 1 characterization supports the following architecture:

**Time bars as the master timeline — the only valid anchoring point for returns, regime labels, and holdout boundaries.**  
**Renko ATR-14 as the primary event-chart signal layer — validated denoising with manageable coverage cost.**  
**Line Break level 3 as a high-confidence confirmation filter — not a primary detector.**  
**Heiken Ashi as a smoothed signal-generation view — evaluated exclusively on real prices.**

Phase 2 should not extend the "which chart type is better?" question. That question has been answered: none is universally better; each has a specific validated role. The productive Phase 2 question is whether combining each chart type's validated strengths — time-bar coverage, Renko precision, Line Break confirmation, HA smoothing — into a multi-view signal framework produces measurably better real-price signal outcomes than any single view alone. The experimental infrastructure and generator stack are ready for that question. The Phase 1 characterizations provide the empirical basis for designing experiments that test complementary contributions rather than competitive rankings.

---
