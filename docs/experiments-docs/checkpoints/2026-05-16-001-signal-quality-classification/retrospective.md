# Retrospective: Phase 2 Signal-Quality Characterisation
**Checkpoint:** 2026-05-16-001-signal-quality-classification  
**Experiments:** EXP-001-TF through EXP-006-TF, EXP-007 through EXP-011  
**Design date:** 2026-05-16  
**Retrospective date:** 2026-05-23  
**Status:** Phase Completed - Event-Chart Signal Path Exhausted Under Current Evidence  

---

## 1. Scope

This retrospective evaluates Phase 2 against its design objective: determine whether the validated chart-type properties from Phase 1 produce cleaner, more reliable real-price signals when measured on the canonical time-bar timeline.

The phase had two blocks:

- **Block A:** Replicate Phase 1 findings at 15-minute and 1-hour source timeframes.
- **Block B:** Test signal-quality contribution hypotheses using a shared real-price FE/AE measurement framework.

All experiments preserved the global final 30 percent holdout exclusion, resolved all return and excursion outcomes from real time-bar prices, avoided strategy P&L, and avoided parameter optimization. EXP-007 through EXP-011 all completed with approved pre- and post-experiment governance.

---

## 2. Experiment Status Summary

| Experiment | Question | Verdict | Governance |
| --- | --- | --- | --- |
| EXP-001-TF | Higher-timeframe replication of information density findings | REFUTED | APPROVED |
| EXP-002-TF | Higher-timeframe replication of volatility/regime findings | REFUTED | APPROVED |
| EXP-003-TF | Higher-timeframe replication of noise robustness findings | REFUTED | APPROVED |
| EXP-004-TF | Higher-timeframe replication of structure capture findings | REFUTED | APPROVED |
| EXP-005-TF | Higher-timeframe replication of cross-chart correspondence findings | REFUTED | APPROVED |
| EXP-006-TF | Higher-timeframe replication of HA distortion findings | REFUTED | APPROVED |
| EXP-007 | Multi-state signal-quality baseline | SUPPORTED | APPROVED |
| EXP-008 | Renko as a precision gate over time-bar signals | REFUTED | APPROVED |
| EXP-009 | Heiken Ashi direction as a real-price signal generator | REFUTED | APPROVED |
| EXP-010 | Line Break as a confirmation layer over Renko signals | REFUTED | APPROVED |
| EXP-011 | Event-native Renko volatility regime detection | REFUTED | APPROVED |

Phase 2 did not fail operationally. It completed its planned evidence-gathering work. The substantive result is that the proposed event-chart signal-quality path did not produce enough reproducible, instrument-consistent evidence to justify Phase 3 strategy-theory exploration on that basis.

---

## 3. What Phase 2 Established

### 3.1 Block A Separated General Properties From 1-Minute-Conditional Findings

The timeframe replication block materially changed the interpretation of Phase 1.

Findings that generalized:

- Event charts structurally reduce or eliminate ghost bars.
- Event-chart regime boundary cost is real and worsens at higher source timeframes.
- Time-bar signal redundancy persists across timeframes.
- Renko and Line Break preserve high reversal precision at higher timeframes.
- Heiken Ashi distortion remains stable across timeframes.

Findings that did not generalize:

- Renko's noise-robustness advantage is strongest at 1 minute and weakens or disappears at higher timeframes.
- Directional entropy gains invert at higher timeframes; event charts reduce entropy rather than improving it.
- The 1-minute event-chart latency disadvantage changes meaningfully at 15 minutes, where Renko can appear faster and more precise than time bars.

This prevented Phase 2 from overgeneralizing Phase 1. The revised Block B correctly focused on 15-minute FE60/AE60 signal quality instead of carrying forward unsupported 1-minute-only claims.

### 3.2 EXP-007 Validated the Measurement Framework, Not the Trading Thesis

EXP-007 was the one supported Block B experiment. Its support is important but narrow.

It established that binary direction is too weak a summary and that real-price multi-state signal-quality metrics can differentiate chart types. The validated downstream metrics were **FE60 and AE60 at 15 minutes**. Precision, run continuation, and all 1-minute criteria did not meet the proceed thresholds.

The central effect was not improvement. It was **magnitude compression**:

- 15-minute Renko FE60: `4.644` vs Time `4.964`.
- 15-minute Renko AE60: `4.462` vs Time `4.943`.

Renko reduced adverse excursion, but it also reduced favourable excursion. EXP-007 therefore gave Block B a measurement language, not a green light for event-chart signal construction.

### 3.3 Coverage Cost Became the Dominant Constraint

Across Block B, event charts repeatedly selected smaller subsets:

- EXP-007: event-chart missing source-bar shares were roughly `72-76%`.
- EXP-008: Renko confirmed only `24.6-28.7%` of 15-minute time-bar signals.
- EXP-009: HA direction-change count was about `47.7-49.3%` of time-bar direction changes.
- EXP-010: Line Break confirmed only `53.5-62.6%` of 15-minute Renko signals.

Coverage loss is not just a sample-size nuisance. It is the main economic shape of the evidence. Every event-chart filter that reduced AE also removed a large share of opportunities and usually reduced FE. Under the approved criteria, that is not a quality improvement.

### 3.4 The Event-Chart Gating Hypotheses Were Exhausted

EXP-008, EXP-009, and EXP-010 tested the natural event-chart signal contributions implied by Phase 1 and Block A:

- Renko confirming time-bar signals.
- HA smoothing selecting higher-quality direction changes.
- Line Break confirming Renko signals.

All three were refuted.

EXP-008 found that Renko confirmation lowered AE but also lowered FE, with primary log FE/AE improvement on only USTEC. EXP-009 found that HA reduced signal count by about half but did not reliably improve log FE/AE. EXP-010 found that Line Break confirmation improved the primary log FE/AE criterion only on BTCUSD and otherwise behaved like another magnitude-compression layer.

These were not arbitrary hypotheses. They were the direct, disciplined tests of the event-chart roles Phase 1 appeared to leave open. Their refutation closes the broad event-chart-as-signal-filter path under the current evidence.

### 3.5 Event-Native Regime Replacement Is Not Supported

EXP-011 tested whether Renko-native internal features could repair the regime-boundary problem documented in Phase 1 and Block A.

The result was negative:

- 15-minute event-density hybrid rates: `0.564-0.659`.
- 15-minute median-source-count hybrid rates: `0.739-0.750`.
- 15-minute brick-to-ATR hybrid rates: `0.750-0.788`.
- Agreement with time-bar regimes remained low, with event density at most `0.436` and brick-to-ATR about `0.211-0.250`.

Brick-to-ATR reduced missed transitions relative to the other Renko-native features, but its hybrid disagreement remained too high. The correct conclusion is to keep time-bar regimes as the canonical volatility frame and treat Renko-native features, if used at all, as descriptive diagnostics rather than regime labels.

---

## 4. Interpretation

### 4.1 The Programme Avoided Overfitting By Stopping at Refutation

Phase 2 had many plausible degrees of freedom it deliberately did not use: Renko ATR period changes, Line Break level changes, tolerance-window optimization, alternate HA definitions, alternate regime bins, composite scores, model-based feature selection, and strategy P&L thresholds.

The evidence does not justify opening those degrees of freedom for the same broad thesis. Doing so now would be a search for a favorable configuration after multiple principled formulations failed. That would increase overfitting risk faster than it would increase research confidence.

### 4.2 Event Charts Still Have Descriptive Value

The phase does not show that event charts are useless. It shows that their tested signal-filter roles are not strong enough to support strategy-theory development.

Supported descriptive uses remain:

- Renko and Line Break describe compressed, high-precision event states.
- HA describes smoothed directional state, but not tradable price.
- Event-chart silence and coverage gaps are informative diagnostics.
- Renko-native features can describe Renko mechanics, even though they failed as volatility regime labels.

These uses are observational and diagnostic. They should not be promoted into a strategy-development foundation without a new, narrower evidence path.

### 4.3 Time Bars Remain the Research Anchor

Phase 2 reinforces the Phase 1 architecture decision:

- Time bars are still the canonical timeline.
- Volatility regimes should remain time-bar-derived.
- Real-price outcomes must continue to be measured from time-bar OHLC.
- Event-chart rows are overlays joined by timestamp, not replacement bars.

The strongest path forward is therefore not another event-chart combination. It is a return to time-bar-native signal quality, possibly with event-chart diagnostics as secondary covariates only if a future scope gives them a specific reason to exist.

---

## 5. Phase 2 Success Criteria Assessment

| Criterion | Assessment |
| --- | --- |
| Timeframe generalisation verdict | Met. Block A identified which Phase 1 findings generalized and which were 1-minute-conditional. |
| Shared measurement framework | Met. EXP-007 implemented and validated deterministic, no-lookahead FE/AE measurement on real prices. |
| Multi-state signal-quality baseline | Met. EXP-007 supported the framework and narrowed downstream metrics to 15-minute FE60/AE60. |
| Renko-as-gate result | Met, refuted. EXP-008 found no general AE-relative-to-FE improvement after coverage cost. |
| HA signal evaluation result | Met, refuted. EXP-009 found signal-count reduction without reliable AE/FE improvement. |
| Line Break confirmation result | Met, refuted. EXP-010 found coverage selection and AE reduction without stable ratio gain. |
| Event-native regime result | Met, refuted. EXP-011 found no acceptable Renko-native volatility regime replacement. |
| Phase 3 direction | Met. Broad event-chart strategy-theory exploration is not justified by the evidence. |

Phase 2 is therefore successful as a research phase because it answered the decision question. The answer is negative for the event-chart signal path.

---

## 6. Recommended Next Direction

Do **not** proceed into Phase 3 as an event-chart strategy-development phase.

Recommended next checkpoint options:

1. **Close the event-chart thesis.** Record that Line Break, Renko, and HA have been characterized and do not provide enough instrument-consistent signal-quality advantage to justify strategy development under the current dataset and constraints.

2. **Start a new time-bar-native phase.** Use the validated FE/AE measurement framework, but remove chart-type combination as the central thesis. Candidate directions include volatility-conditioned time-bar signals, run-length filters, adverse-excursion control, and swing-structure features computed directly on real prices.

3. **Keep event-chart diagnostics secondary.** If used later, event-chart features should enter only as pre-specified diagnostics with explicit hypotheses, not as a broad search over chart-type combinations.

4. **Do not spend the global holdout yet.** The final 30 percent holdout has not been needed for the refuted event-chart path. Preserve it for a future candidate that survives analysis-set characterization and has a genuine validation claim.

---

## 7. Final Phase Conclusion

Phase 2 reached the natural end of the event-chart signal-quality programme.

The project now has a coherent empirical record:

- Event charts compress and denoise price representation.
- Their signal emissions have high precision-like descriptive properties.
- Those properties do not translate into a robust, coverage-adjusted real-price FE/AE advantage across instruments.
- Attempts to repair the path through HA smoothing, Line Break confirmation, Renko gating, and Renko-native regimes were refuted.

The disciplined conclusion is to stop developing the current event-chart thesis and redirect future research toward time-bar-native signal-quality mechanisms, using the Phase 2 framework as reusable measurement infrastructure.

