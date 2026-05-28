# Retrospective: Phase 004 USTEC Breaker Validation and IFVG Selectivity Redesign

**Checkpoint:** 2026-05-26-004-ustec-breaker-ifvg-selectivity
**Experiments:** EXP-029 through EXP-033
**Design date:** 2026-05-26
**Mid-checkpoint reflection:** 2026-05-27 (amended 2026-05-27 after EXP-032)
**Retrospective date:** 2026-05-28
**Status:** Phase Completed — Both Branches Closed With No Candidate Manifest; ICT-as-Alpha Thesis Closed
**Predecessor:** [2026-05-23-003-ict-one-setup-timebar-validation](../2026-05-23-003-ict-one-setup-timebar-validation/retrospective.md)

---

## 1. Scope

This retrospective evaluates Phase 004 against its design objective:

> Is there a narrowly defensible candidate in USTEC breaker behavior or stricter IFVG selectivity that is worth a future holdout-preserving model validation checkpoint?

Phase 004 was a deliberately narrow, falsification-first continuation of Phase 003. It inherited only completed, audited, time-bar-native findings (EXP-020, EXP-021, EXP-022, EXP-023, EXP-024, EXP-026) and pursued the two — and only two — Phase 003 results that retained any local promise: the USTEC Candidate A breaker positive (Branch A) and a stricter-IFVG selectivity redesign (Branch B). It also introduced a mandatory pre-phase (Phase 004A) to test a structural scope gap identified at Phase 003 close: all Phase 003 ICT components were measured at 1-minute resolution, whereas ICT concepts have their natural domain on 15-minute and higher timeframes.

Every Phase 004 experiment preserved the final 30 percent global holdout (applied to the 1-minute series before aggregation), used real 1-minute OHLC prices for all outcomes, added no event-chart features, and received APPROVE at both pre-execution and post-experiment governance.

The phase answer to its objective is **negative on both branches**. This is design.md Expected Outcome #4 — "Neither survives: Phase 004 closes both branches before holdout and records a clean no-go" — and it is the design's explicitly preferred form of result: a defensible decision rather than a forced positive.

---

## 2. Experiment Status Summary

| Experiment | Sub-phase / Branch | Verdict | Key phase finding |
| --- | --- | --- | --- |
| EXP-029 | 004A pre-phase | REFUTED | 120-bar IFVG inversion is 83–86% at 15-minute on all 4 instruments, within 2pp of the Phase 003 1-minute 84–85% baseline. An 8-bar (~2h) lifecycle drops it to 45–48% uniformly. Lifecycle window **duration**, not source-bar resolution, drives the high inversion. |
| EXP-030 | 004A pre-phase | INCONCLUSIVE | No positive sweep-minus-breach Hit1R_60m on any instrument at 15-minute. The lone EXP-015 EURUSD positive (+0.134) **reverses** to −0.145, CI [−0.255, −0.036] excluding zero. BTCUSD consistently negative; XAUUSD and USTEC null at both 1m and 15m. |
| EXP-031 | 004A pre-phase | INCONCLUSIVE | USTEC breaker direction preserved at 15-minute: test Return_R +1.836R, CI [+0.560, +3.636]; train CI [+0.235, +0.837] (sharper than EXP-023's 1m train CI). MAE reduction −0.679R train / −1.331R test (CIs exclude zero). But test magnitude is 44% of the EXP-023 1m reference, below the predeclared 50% comparability threshold. |
| EXP-032 | 004B Branch A | REFUTED | 1-hour USTEC breaker: counts pass (143 train / 62 test feasible events), direction stays positive, but test Return_R diff is +0.116R against a binding +0.918R gate (~6%). Branch A **closed**; no candidate manifest. Residual: a small consistent MAE reduction (~0.16R). |
| EXP-033 | 004B Branch B | REFUTED | 0 of 5 predeclared IFVG/FVG rule families pass all six readiness checks on ≥2 instruments at 15-minute. Exactly 1 of 40 cells passes (BTCUSD R3 Train); its Test pair narrowly fails. Branch B **closed** with a selectivity-gated no-go. |

Status counts: 3 REFUTED (EXP-029, EXP-032, EXP-033), 2 INCONCLUSIVE (EXP-030, EXP-031). The two INCONCLUSIVE results are pre-phase diagnostics, not failed candidate tests; they functioned exactly as designed — they fed the mid-checkpoint reflection directive. The phase completed its planned roadmap and produced a clean no-go.

The phase introduced one new reusable module: `python/src/bar_aggregator.py`, a deterministic clock-aligned 1-minute → N-minute resampler with holdout exclusion applied before aggregation. It is the shared infrastructure for all 15-minute and 1-hour analysis.

---

## 3. Branch-Level Results

### 3.1 Phase 004A: The Timeframe Question Is Settled — Resolution Was Not the Problem

The pre-phase was the highest-leverage decision in the checkpoint. Its purpose was to determine whether Phase 003's negative and weak results were artifacts of measuring ICT structure at the "wrong" (1-minute) resolution.

The combined answer is **no**:

- **IFVG non-selectivity is not a resolution artifact (EXP-029).** Moving to 15-minute left the 120-bar inversion rate essentially unchanged (83–86% vs 84–85%). The high inversion rate tracks the *lifecycle window duration*, not the bar resolution. This reframed Branch B from "try the existing rule at 15-minute" to "the lifecycle-windowed three-candle definition is intrinsically tautological; only a structurally different rule could fix it."
- **Sweep reversal does not strengthen at 15-minute (EXP-030).** It weakened. The only Phase 003 sweep positive (EURUSD) inverted sign with a CI excluding zero. This functionally invalidated the one deferred fallback the design had left open.
- **The USTEC breaker survived 1m → 15m directionally but lost magnitude (EXP-031).** Direction and sign held with a first-time-clean train CI and confirmed MAE reduction, but magnitude fell to 44% of the 1m reference. This was promising enough to keep testing but not a clean pass, so the reflection converted the planned segmentation into a binding 1-hour magnitude-comparability gate (EXP-032) *before* segmentation.

### 3.2 Branch A (USTEC Candidate A Breaker): CLOSED at EXP-032

The decisive finding is the cross-resolution magnitude trajectory for the same instrument and the same rule family, holding the chain constant and scaling lookback/lifecycle by elapsed time:

| Source | Resolution | Test Return_R diff | Gate | Verdict |
| --- | --- | --- | --- | --- |
| EXP-023 | 1-minute | +4.176R (wide CI) | cross-instrument H5 refuted elsewhere | local positive only |
| EXP-031 | 15-minute | +1.836R, CI [+0.560, +3.636] | 50% of 1m (+2.088R) | FAIL (44%) — INCONCLUSIVE |
| EXP-032 | 1-hour | +0.116R, CI [+0.039, +0.220] | 50% of 15m (+0.918R) | FAIL (~6%) — REFUTED |

The effect decays by roughly an order of magnitude at each timeframe coarsening while direction is preserved, with adequate counts and retention (0.568) throughout — so the collapse is not a count or sampling artifact. A genuine *structural* breaker advantage should not lose this much magnitude under deterministic elapsed-time-scaled aggregation. The pattern is the signature of a **microstructure-sensitive effect that concentrates at high resolution** — exactly the behavior the design treated as suspect.

The reflection (§10.3) considered and rejected three reframes before closing:

- **Drawdown-only filter:** the surviving MAE reduction (~0.16R) is real and consistent across resolutions, but far too small to carry a candidate manifest on its own and would still depend on an entry path sourced elsewhere. Sustaining 3–4 follow-on experiments for a +0.16R MAE finding contradicts the design's falsification-over-expansion preference.
- **1-minute microstructure proxy:** explicitly forbidden by the reflection, and the trajectory weakens rather than strengthens the 1-minute structural claim.
- **Chain re-engineering on 1-hour data:** this would be parameter tuning against analysis-set returns, prohibited by design.md and the programme's no-premature-optimisation principle.

Branch A closed without a candidate. The MAE reduction is recorded as a hypothesis-agnostic observation only.

### 3.3 Branch B (IFVG/FVG Selectivity Redesign): CLOSED at EXP-033

EXP-033 ran the full predeclared rule-family menu — R1 stricter size, R2 shorter lifecycle, R3 displacement-qualified FVG creation, R4 mitigation-before-inversion, R5 zone-location — as a readiness-only survey (no returns or excursions entered selection). The six readiness checks were reproducibility, count floor, inversion band [0.55, 0.75], selectivity (rule-eligible FVG count ≤ 80% of baseline), median delay ≤ 24 bars, and a valid risk denominator. A rule needed to pass all six on **both** segments of **≥2 instruments**.

Result: `selected_rule = null`, `qualifying_instrument_count = 0` for all five rules. Exactly 1 of 40 cells (BTCUSD R3 Train, inversion 0.737) passed all six checks; its Test pair failed the inversion band by 0.017 (0.767 vs 0.750). The structural reading per rule:

- **R2 (shorter lifecycle, 24 bars)** pulled inversion into the band (0.64–0.68) on every cell — directly confirming EXP-029 — but cannot pass selectivity *by construction*, because it modifies the inversion criterion, not FVG creation (selectivity ratio = 1.0).
- **R3 (displacement-qualified creation)** was the only rule that meaningfully restructured the event set (retains 16–22%, inversion 0.74–0.78), but it sits structurally at the upper band edge and qualified only one segment of one instrument.
- **R1, R4, R5** narrowed the event count to varying degrees but left the inversion rate essentially at baseline (0.80–0.85). Proximity to swept levels, stricter size, and explicit mitigation do not change the close-through propensity of a 15-minute FVG.

The mechanical verdict per design.md §"Readiness Pattern" (a rule passing on only one instrument records a selectivity-gated no-go) is REFUTED. Branch B closed; EXP-034/035 were not created.

---

## 4. Thesis-Level Result: ICT-as-Alpha Is Closed

This is the formal closure the phase exists to record.

The ICT investigation spanned two full phases and roughly 22 experiments:

- **Phase 003 (EXP-012 → EXP-028)** translated the discretionary "macro + sweep + displacement + IFVG/breaker + second-candle-open + 2R" setup into deterministic, auditable, time-bar-native components and tested the chain. The broad cross-instrument model was **blocked before full-model promotion**: no optional component had a positive lower-CI marginal contribution (EXP-026), so EXP-027/028 never opened. It left exactly two local positives and one deferred fallback.
- **Phase 004 (EXP-029 → EXP-033)** took those survivors to their natural higher-timeframe domain and closed all three:
  - USTEC breaker (the strongest local positive) — closed; microstructure-sensitive, not structural.
  - IFVG selectivity redesign — closed; the high inversion rate is intrinsic to the lifecycle-windowed three-candle definition, not a rule-design accident fixable within the predeclared menu.
  - EURUSD sweep deferral (the fallback) — closed; it reversed sign at 15-minute.

The cleanest accurate statement:

> Across Phases 003–004, every objective ICT component is reproducible and deterministic, but none — alone, combined, or at any tested resolution (1m, 15m, 1h) — produced a robust post-signal edge eligible for a holdout-preserving validation. The ICT-as-alpha thesis is closed. No ICT result carries forward as a positive candidate.

Computation was never the obstacle and is the durable asset: the repository can construct macro windows, PDH/PDL/ONH/ONL levels, sweeps, displacement, FVG/IFVG zones, breaker candidates, second-candle-open entries, fixed-R exits, and deterministic multi-timeframe resampling. Computation is simply not evidence of edge, and the evidence of edge did not materialise.

### Honest caveat — the one residual unexplored corner

The closure is "ICT-as-alpha, as explored," not "every conceivable ICT variant disproven." Two corners were deliberately *scoped out* rather than refuted:

1. **Daily and 4-hour structural timeframes.** The design targeted 15-minute as the lowest ICT-valid structural timeframe with adequate event counts, with a single 1-hour extension permitted for the surviving breaker branch. Daily/4h — arguably ICT's canonical HTF-bias domain — were explicit non-goals. *However*, the EXP-023 → EXP-031 → EXP-032 trajectory argues against expecting a rescue there: the breaker effect concentrated at high resolution and decayed an order of magnitude per coarsening, the opposite of what an HTF-structural thesis predicts.
2. **IFVG selectivity defined at the IFVG-event level.** EXP-033's selectivity check is defined on FVG count, which structurally excludes R2-style lifecycle rules that reduce inversions without changing FVG creation. A future scope could credit those rules — but that is a fresh hypothesis, not a re-interpretation of EXP-033.

These are recorded as reopenable only with **new design evidence**; neither carries forward automatically with a new checkpoint.

---

## 5. Lessons and Model Implications

### 5.1 Higher timeframe is not a free rescue for a weak low-resolution effect

The pre-phase's central lesson: when an effect appears only at high resolution, coarsening the timeframe under elapsed-time-scaled aggregation is a clean discriminator between structure and microstructure. An order-of-magnitude magnitude decay with preserved direction and adequate counts should be read as microstructure-sensitivity, not as a structural edge awaiting the right timeframe. This is a reusable diagnostic for any future Xen work.

### 5.2 Selectivity is a property of the rule's definition, not its parameters

EXP-029 and EXP-033 together show the IFVG inversion rate is governed by lifecycle window duration and the three-candle definition itself. Narrowing *which* FVGs qualify (size, location, mitigation) does not change *whether* they invert. A detector that retains everything or inverts almost always is a state descriptor, not a confirmation signal — and no parameter choice within the family changes that.

### 5.3 The falsification-first, gated structure worked

The phase's gating did its job: the pre-phase reflection prevented a wasted Branch B run at the existing rule; the binding magnitude gate killed Branch A in one experiment instead of four; the readiness-before-outcome gate stopped Branch B before any return test. Two branches were resolved in five experiments with no holdout spend and no moved goalposts.

### 5.4 The global holdout remains untouched

No Phase 004 candidate reached analysis-set eligibility, so there is no candidate to validate and no reason to spend the final 30 percent global holdout. It remains a full global reserve for a future thesis that first earns analysis-set validation.

---

## 6. Phase Gate Assessment

| design.md gate | Assessment |
| --- | --- |
| Pre-phase gate | Met. EXP-029–031 completed and audited; mid-checkpoint reflection issued and amended. |
| Mid-checkpoint reflection gate | Met. Directive issued, then amended after EXP-032 to close Branch A and renumber Branch B. |
| Local-positive falsification gate | Met, negative. The USTEC local positive did not survive the binding 1-hour magnitude gate (EXP-032). |
| Selectivity-before-outcome gate | Met, negative. No IFVG rule passed readiness on ≥2 instruments (EXP-033); outcome testing correctly never opened. |
| Execution-friction gate | Not reached. No branch produced a candidate to stress-test. |
| Convergence gate | Deactivated. Convergence requires two eligible candidates; neither branch produced one. |
| Holdout gate | Intact. No Phase 004 experiment inspected or used the final 30 percent holdout. |

---

## 7. Recommended Next Steps

1. **Treat ICT-as-alpha as closed.** Do not reopen the broad ICT chain, the USTEC breaker, the IFVG confirmation rule, or the EURUSD sweep as positive candidates. Any return requires new design evidence, not a fresh checkpoint alone.
2. **Phase 005 should start from a genuinely new thesis.** The project has now closed both major theses it has pursued — the event-chart thesis (Phases 1–2) and the ICT thesis (Phases 3–4). The next checkpoint should not be an ICT continuation; it should introduce a new, falsifiable, single-hypothesis direction with its own design.md.
3. **If ICT is ever revisited, only as a narrow, freshly-scoped redesign.** The two reopenable corners are (a) Daily/4h HTF structural behavior — pursue only if a new rationale overrides the unfavorable resolution trajectory; and (b) IFVG selectivity defined on the IFVG-event denominator (crediting R2-style lifecycle rules), per EXP-033's note. Each requires its own predeclared design and readiness gates.
4. **Keep the infrastructure.** `python/src/bar_aggregator.py`, the time-bar-native ICT detectors, holdout discipline, and the gated pipeline are validated research infrastructure and should be retained regardless of thesis.
5. **Preserve the global holdout.** Unchanged from Phase 003: it stays reserved for a future candidate that first earns analysis-set validation.

---

## 8. Final Phase Conclusion

Phase 004 achieved its purpose. It took the only two Phase 003 results with any local promise to their natural higher-timeframe domain, applied binding magnitude- and selectivity-comparability gates, and closed both branches with a disciplined, holdout-preserving no-go. The USTEC Candidate A breaker is a microstructure-sensitive effect that does not survive elapsed-time-scaled aggregation; the IFVG inversion rate is intrinsic to the lifecycle-windowed three-candle definition and is not selectivity-fixable within the predeclared rule family; the EURUSD sweep deferral is invalidated at 15-minute.

Combined with Phase 003's blocked broad chain, this closes the ICT-as-alpha thesis for the Xen programme. The valid output is not a strategy candidate but a clear, evidence-backed boundary: the objective ICT translation is fully computable and fully auditable, and — across 1-minute, 15-minute, and 1-hour resolutions — it does not produce a defensible post-signal edge. The next phase should begin from a new thesis.
