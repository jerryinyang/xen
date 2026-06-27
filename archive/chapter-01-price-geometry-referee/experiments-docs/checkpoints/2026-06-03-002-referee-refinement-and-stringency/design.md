# Phase 002 — Referee Refinement & Stringency Characterization

**Phase number:** 002
**Design finalised:** 2026-06-03
**Status:** ACTIVE (design complete; execution begins at EXP-005)

**Provenance:**
- Predecessor: Phase 001 `2026-06-01-001-thesis-qualification-calibration` — [design.md](../2026-06-01-001-thesis-qualification-calibration/design.md), [retrospective.md](../2026-06-01-001-thesis-qualification-calibration/retrospective.md).
- Phase 001 delivered a *calibrated* referee: per-domain FPR/TPR/economic-MDE map (EXP-003), gated by a validated substrate (EXP-001) and correct referee logic (EXP-002), anchored against real dogfood (EXP-004).
- Phase 001 left **one open item**: H-keystone is *bounded, not closed*. The EXP-004 anchor was a null anchor (untuned Donchian/MA carry ~0 edge), so the gate's rejections are confirmed true negatives, but no realistic candidate carrying a *real* edge near the MDE was ever tested. Whether the gate is structurally blind to weak-but-real edges is undecided.

This phase references Phase 001 decisions as *P1-§n / P1-D-x*.

---

## 1. Phase objective

Take the calibrated referee from Phase 001 and make it **usable and trustworthy**: (1) **close the open keystone** by testing whether the gate detects a *realistic* candidate carrying a *real* edge near its MDE; (2) **characterize the stringency lever** identified in Phase 001 — the L5 materiality leg — by sweeping its threshold and testing a structurally lenient variant; (3) **sharpen the map** by de-pooling MDE per instrument and broadening the real-strategy effect-size distribution; (4) **stress-test the inference** by comparing split protocols; and (5) **synthesize** all of this through a predeclared loss function into a **recommended** operating point per domain.

**This is still a characterization phase, not an optimization phase.** Per the binding programme principle *no premature optimisation*, Phase 002 measures options and *recommends*; it does **not** adopt or freeze any new referee. The actual adoption decision — ratifying a recommended operating point / lenient referee — is deferred to a dedicated **Phase 003 decision phase**, run against *fresh* synthetic draws (meta-Goodhart guardrail, §10). The freeze, where Goodhart bites, happens where it can be done cleanly — not in the same phase that characterizes the options.

The organizing decision for the phase: **the Phase 001 frozen referee remains the reference object. Every new variant is a predeclared alternative measured against it, once.**

---

## 2. Predeclared decisions (frozen before any measurement is read)

Frozen for the phase. Changing any requires a new predeclared design (meta-Goodhart guardrail, §10).

| # | Decision | Resolution |
| --- | --- | --- |
| D-posture | Phase identity | **Characterize & recommend.** No new referee is adopted/frozen in Phase 002. EXP-011 produces a *recommended* operating point per domain plus a predeclared conditional adoption rule; ratification is Phase 003 with fresh draws. |
| D-reuse | Substrate & harness | **Reuse the EXP-001-validated substrate and the EXP-003 calibration harness (`python/src/xen/referee_calibration.py`) unchanged**, for comparability with Phase 001. Any change to the loader, `aggregate_ohlc`, generators, or harness triggers re-validation (P0, §9) before dependent experiments. |
| D-frozen-ref | Reference referees | The Phase 001 **minimal baseline** and **5-check gate stack** are carried forward **frozen and unchanged** as the reference. New variants (lenient L5) are *separate* predeclared referees. |
| D-invariants | Carried-forward invariants | Domains **5m/1h/4h** (P1-D-dom); instruments **EURUSD/XAUUSD/BTCUSD/USTEC**; per-domain costs & materiality (P1-D-cost); coverage `min_coverage` (P1-D-cov: 5m strict, 1h/4h 0.90); precision target (P1-D-prec: 95% Wilson half-width ≤0.03 FPR / ≤0.05 TPR); block bootstrap (P1-D-block); α grid {0.10, 0.05, 0.01}, primary α₀=0.05 (P1-D-op). All retained **unchanged** so Phase 002 results compose with the Phase 001 map. |
| D-lenientL5 | Lenient-L5 definition (EXP-007) | The lenient variant is a **mechanism** change, not merely a smaller number: L5 passes if the **lower bound of the net-of-cost effect CI exceeds 0** (statistical net-positivity after costs), replacing the strict leg's requirement that the point estimate exceed *cost + per-domain materiality buffer*. This is structurally distinct from EXP-006's threshold-magnitude sweep. **Materiality caveat:** because this mechanism drops the materiality buffer, it can admit reliably-positive-but-economically-negligible effects, which is in tension with the referee's purpose (allocating scarce validation resources). EXP-007 must therefore (a) state the *economic* interpretation of a lenient pass explicitly, and (b) report the **economically sub-material pass rate** — the fraction of lenient-L5 passes whose net-of-cost point estimate falls below *cost + per-domain materiality buffer* — read against the EXP-006 threshold frontier (which already spans the strict-mechanism materiality-buffer→0 limit). A lower MDE bought mostly by sub-material passes is reported as such, **not** counted as a genuine sensitivity gain. ⚠ Confirm at the EXP-007 gate. |
| D-nearMDE | Near-MDE planting grid (EXP-005) | Plant a real, oracle-validated edge at a predeclared grid of **{0.5, 1.0, 1.5, 2.0} × the EXP-003 gate MDE** per domain (5m 1.0 / 1h 4.0 / 4h 12.0 bps), carried by a **realistic (imperfect) candidate** signal, not the perfect oracle. The EXP-005 scope must **predeclare, before execution**, the full realistic-candidate construction so the keystone-closure verdict is interpretable: (i) the candidate-generation mechanism (how the imperfect position series is derived from the planted-edge state); (ii) the noise / signal-to-noise model and its parameters; (iii) the active-bar denominator used for TPR/FPR; (iv) the cost treatment; and (v) an explicit argument for why this candidate is a valid proxy for a *weak-but-real* edge — neither so oracle-adjacent that detection is trivial (which would make EXP-005 a tautology), nor so noisy that non-detection is vacuous. ⚠ Confirm this construction before EXP-005 executes (see ⚠ block below). |
| D-loss | Loss-function form (EXP-011) | The loss/utility over (FPR, economic MDE, cost) is **predeclared in full in the EXP-011 scope before any operating-point is read**. Default family: an explicit cost-weighted combination penalising false positives and missed material edges, evaluated per domain. The operating-point read is mechanical once the loss is fixed. |
| D-freshdraw | Variant-measurement draws | New referee variants (lenient L5) are measured on the **same paired draws** as the frozen reference for within-draw comparison — permissible because each variant is **fully predeclared before measurement** (not selected against these draws). The Goodhart-sensitive *adoption* step uses **fresh draws in Phase 003**, never these. |

**⚠ Operator-confirmation items.** The near-MDE construction (D-nearMDE), the lenient-L5 definition (D-lenientL5), and the loss-function form (D-loss) are set here as defensible defaults. To preserve the predeclaration freeze (the §2 heading: *frozen before any measurement is read*), **operator confirmation or override of all three must be recorded before EXP-005 executes — i.e., before any Phase 002 measurement exists.** Any change after EXP-005 begins requires a **new dated design amendment authored before the dependent experiment's results are read**, and that amendment may reference only predeclared reasoning, never earlier Phase 002 results (EXP-005/EXP-006 outcomes in particular). This closes the outcome-aware path in which D-lenientL5 (read at the EXP-007 gate) or D-loss (read at the EXP-011 gate) could otherwise be tuned against already-visible EXP-005/EXP-006 results. Once an item's experiment runs, it is frozen for the phase.

### ⚠ Erratum 2026-06-03 — D-lenientL5 "distinct mechanism" framing corrected (frozen-harness clarification)

**Status:** dated amendment, §2 ⚠-compliant. **Derived solely from Phase 001 artifacts** — the frozen `xen.referee_calibration.gate_stack_row` and the EXP-003 draws — references **no Phase 002 measurement** (no EXP-005/EXP-006/EXP-007 outcome), and was **authored before any EXP-006 or EXP-007 result existed**. **It changes no predeclared object:** the lenient-L5 definition stays `L5_lenient = ci_lower_bps > 0`, and H-lenient (§4) stays exactly as written and falsifiable.

**What is corrected.** The D-lenientL5 row above frames the lenient variant as a *mechanism* change ("not merely a smaller number… structurally distinct from EXP-006's threshold-magnitude sweep") and describes the strict leg as a *point-estimate exceeds cost + materiality buffer* requirement. **Both descriptions are inconsistent with the frozen code, which governs.** In the frozen harness, strict L5 is `ci_lower_bps > materiality_bps` (a CI-lower-bound test, not a point-estimate test) and L3 already requires `ci_lower_bps > 0`. Two exact consequences follow on the shared draws (verified across all 216,000 frozen gate-stack rows, 0 exceptions):

1. **Lenient L5 ≡ EXP-006 `τ=0` endpoint.** EXP-006 sweeps `L5_τ = ci_lower_bps > τ`, `τ = mult × materiality_bps`; at `mult=0` this is exactly `ci_lower_bps > 0`. The lenient leg therefore lies *on* the EXP-006 threshold frontier (its zero-buffer endpoint) and **cannot strictly improve beyond it**.
2. **Lenient gate ≡ gate with L5 removed.** Because L3 already enforces `ci_lower_bps > 0`, `L1∧L2∧L3∧L4∧(ci_lower>0) = L1∧L2∧L3∧L4`. Maximal L5 leniency equals dropping L5, with L3 the binding net-positivity gate.

So the lenient leg is the `τ→0` magnitude limit of the *same* CI-lower-bound mechanism — not a structurally distinct one. **H-lenient's structural-gain branch is consequently expected to resolve FALSIFIED** (a legitimate predeclared finding). EXP-007's attainable, non-redundant deliverable is therefore (a) the lenient operating characteristics at Phase-002 precision, (b) the **economically sub-material pass-rate** accounting at the lenient MDE (not produced by EXP-006, required by D-lenientL5's materiality caveat), and (c) numerical **verdict-level** confirmation of the two equivalences above.

**Downstream obligation.** Synthesis experiments — **EXP-011 in particular** — must cite this erratum and describe the lenient variant as the **EXP-006 zero-buffer threshold endpoint plus sub-material accounting**, *not* as a mechanism-level sensitivity gain. Full reasoning: EXP-007 `scope.md` → "Predeclared Structural Relationship", and `docs/code-reviews/2026-06-03-exp-006-007-review-validation.md` (validates adversarial-review finding F04).

---

## 3. Definitions (additions to Phase 001 §3)

| Term | Definition |
| --- | --- |
| **Realistic candidate** | An *imperfect* signal (noisy position series, like the dogfood strategies) — as opposed to the EXP-003 **oracle** (perfect state-follower). The distinction matters: the Phase 001 MDE was calibrated on the oracle; a realistic candidate carrying the same planted edge may present a weaker effective signal to the referee. |
| **Honest detection floor** | A property of the MDE map: that a *realistic* candidate carrying an edge ≥ the mapped MDE is detected with TPR ≥ 0.80 at FPR ≤ α₀. EXP-005 tests whether the oracle-calibrated MDE is an honest detection floor in this sense. |
| **Stringency lever** | The L5 materiality leg, identified in Phase 001 as the binding, α-invariant determinant of the gate's MDE. "Pulling the lever" = changing L5's threshold magnitude (EXP-006) or mechanism (EXP-007). |
| **Recommended operating point** | A per-domain (referee variant, threshold) choice that EXP-011 names as loss-minimising — explicitly a *recommendation*, not a frozen commitment (D-posture). |
| **Conditional adoption rule** | A predeclared if-then recorded by EXP-011, e.g. *"if EXP-005 shows the strict gate misses real near-MDE edges AND a lenient variant recovers that detection at FPR ≤ α₀, recommend adopting it in Phase 003."* The rule is recorded in Phase 002; the decision is executed in Phase 003. |

---

## 4. Falsifiable claims

- **H-blindness (EXP-005, keystone closure):** *On each domain, a realistic candidate carrying a real edge ≥ the domain's gate MDE is detected by the gate stack with TPR ≥ 0.80 at FPR ≤ α₀ — i.e., the oracle-calibrated MDE map is an honest detection floor for realistic candidates.* **Falsified on a domain** if a realistic candidate carrying an edge ≥ MDE is systematically rejected (the map overstates real detection / the gate is structurally blind there). Either outcome is a finding and resolves the Phase 001 open item. **Pooling caveat (carried from P1-§lesson-4):** the gate MDE is a four-instrument pooled aggregate over heterogeneous per-instrument cost (1–10 bps) and dispersion, so a pooled-domain pass can mask per-instrument blindness. EXP-005 therefore reports detection **both pooled-domain and per-instrument wherever the effective sample meets D-prec**; per-instrument cells failing D-prec (most likely 4h) are reported as under-powered, not forced to a verdict. The pooled-domain verdict remains the headline (it matches how EXP-003 calibrated the MDE), with the per-instrument breakdown as the masking check.
- **H-lenient (EXP-007):** *The predeclared structurally-lenient L5 (D-lenientL5) lowers the gate's economic MDE relative to the strict gate while holding FPR ≤ α₀, beyond what merely lowering the threshold magnitude (the EXP-006 frontier) achieves.* **Falsified** if the lenient variant fails to lower MDE, or lowers it only as much as a threshold reduction would, or pushes FPR above α₀.
- **H-pool (EXP-008):** *Per-instrument MDEs differ materially from the Phase 001 four-instrument pooled domain MDEs.* "Materially" is predeclared here as **|per-instrument MDE − pooled domain MDE| ≥ max(0.5 bps, 20% of the pooled domain MDE)** (the same tolerance family as the EXP-001 recovery band). The EXP-008 scope must restate and freeze this margin **before any per-instrument MDE artifact is loaded**, and may change it only via a dated amendment recorded pre-results (§2 ⚠ block discipline). A descriptive comparison; either direction is informative.
- **H-split (EXP-010):** *Alternative split protocols (walk-forward, purged/embargoed CV) do not materially change the referee's operating characteristics versus the mandated single chronological split.* The null is robustness; **falsified (and interesting)** if a protocol materially shifts FPR/MDE.
- **Exploratory (no pass/fail, measurement only):**
  - **EXP-006** — trace MDE(threshold) and FPR(threshold): the L5 lever curve.
  - **EXP-009** — characterize the net-effect-size *distribution* of a broadened untuned strategy set relative to each domain's MDE.
  - **EXP-011** — given the predeclared loss, identify the loss-minimising operating point per domain per variant and record the recommendation + conditional adoption rule.

---

## 5. Object-level scope

- **Candidate form:** standalone, price-based **directional** signals (position in {−1,0,+1}), same as Phase 001 §5. The *incremental-information unit is NOT introduced this phase* — it is the Phase 003 seed (§12).
- **Instruments / domains:** unchanged (D-invariants). Timeframe remains a first-class, never-pooled dimension — **except** EXP-008, whose entire purpose is to de-pool by instrument.
- **Outcome metric:** direction-adjusted next-step real-price return, evaluated on **real bar prices only** — never HA/Renko construction prices.
- **Excluded candidate sources:** **chart-type signals (Line Break / Renko / Heiken Ashi) remain out of scope** — by explicit operator decision, signal exploration begins only after the testing framework is concluded (§12).

---

## 6. Referees / variants under test

| Referee | Status in Phase 002 | Used by |
| --- | --- | --- |
| Minimal baseline (P1) | Frozen reference | all calibration EXPs |
| 5-check gate stack (P1) | Frozen reference | all EXPs |
| **Gate stack — L5 threshold τ swept** | **Parameterised, swept (not a freeze)** | EXP-006 |
| **Gate stack — lenient L5 (D-lenientL5)** | **New, predeclared, measured once** | EXP-007 |

All variants reuse the EXP-003 harness machinery (paired draws, block bootstrap, Wilson CIs, empirical MDE) unchanged (D-reuse). No referee is adopted/frozen (D-posture).

---

## 7. Holdout & discipline constraints

- All runs use **only the first 70% analysis set**; the final 30% global holdout is never loaded or inspected.
- Within the analysis set, the mandated 70/30 chronological train/test split applies — **except** EXP-010, which compares this against alternative *within-analysis-set* protocols (walk-forward, purged/embargoed CV). No protocol may touch the global holdout.
- Shared split boundary across domains as `CloseTime` timestamps from the canonical base (P1-§9) — never per-timeframe row fractions.
- **Validation precondition P0 (gates the phase):** Phase 002 reuses the EXP-001-validated substrate/harness at the *same* {5,60,240}-minute parameterizations already validated. If any loader/`aggregate_ohlc`/generator/harness code changes before or during the phase, the temporal-integrity + substrate validation must be re-run (VAL-001 control-per-check standard / EXP-001 P0) before dependent experiments resume.
- Real-price outcome discipline, timestamp alignment over bar count, deterministic generation (fixed seeds, recorded), single-question-per-experiment — all hold.

---

## 8. Planned experiments

Next ID is **EXP-005**. Each answers one question. Numbering continues from Phase 001 (EXP-001…004); IDs are never reused.

| ID | One-line question | Depends on | Budget (tests / plots / modules) |
| --- | --- | --- | --- |
| **EXP-005** (spine) | Does the gate stack detect a *realistic* candidate carrying a *real* edge near each domain's MDE, consistent with the oracle-calibrated map? **(keystone closure)** | EXP-001, EXP-003 | comparative, ~2–4 / 3–5 / 0–1 |
| **EXP-006** | How do the gate's economic MDE and FPR vary as the L5 materiality threshold is swept per domain (the lever curve)? | EXP-001, EXP-003 | comparative, ~2–3 / 3–4 / 0–1 |
| **EXP-007** | Does the predeclared structurally-lenient L5 lower the gate's economic MDE at FPR ≤ α₀, beyond a mere threshold reduction (EXP-006 frontier)? | EXP-001, EXP-003, EXP-006 | comparative, ~2–4 / 3–4 / 0–1 |
| **EXP-008** | Do per-instrument MDEs differ materially from the Phase 001 four-instrument pooled domain MDEs? | EXP-001, EXP-003 | comparative, ~2–3 / 3–5 / 0–1 |
| **EXP-009** | Where do the net effect sizes of a broadened set of untuned simple strategies sit relative to each domain's MDE? | EXP-003, EXP-004 | comparative, ~2–4 / 3–5 / 0–1 |
| **EXP-010** | Do alternative split protocols (walk-forward, purged/embargoed CV) materially change the referee's operating characteristics vs the single chronological split? | EXP-001, EXP-003 | comparative, ~2–4 / 3–5 / 1 |
| **EXP-011** | Given a predeclared loss function, what operating point does each variant imply per domain, and which does the phase *recommend* (with the conditional adoption rule)? | EXP-005…008 (009/010 context) | synthesis, ~1–2 / 3–4 / 0–1 |
| **Phase 003 seed** | (Design-only) specify the incremental-information / ensemble candidate unit for the next phase. | — | spec only |

**Sequencing.** EXP-005 runs **first** as the spine — its blindness verdict conditions how the L5-leniency work is *interpreted* (whether leniency is even motivated). EXP-006 (threshold sweep) precedes EXP-007 (the lenient variant is read against the sweep frontier). EXP-008/009/010 are methodologically independent and may run in any order after the substrate/harness reuse is confirmed. **EXP-011 runs last** as the synthesis. If the phase proves too heavy, drop **only EXP-009 and EXP-010** (the optional/context items in §9) to a follow-up checkpoint before touching the EXP-005→006→007→011 spine or the EXP-008 per-instrument map (both core in §9).

**Predeclaration freeze (meta-Goodhart guardrail).** All new referee variants (lenient L5) and the loss function are predeclared **before** their measurement and measured **once**. No variant is iterated against synthetic results within the phase. The frozen Phase 001 referees are not modified. Adoption of any recommendation uses **fresh draws in Phase 003**.

---

## 9. Phase-level success / failure / inconclusive criteria

- **Success (core — required for phase success):** (a) EXP-005 returns an interpretable per-domain blindness verdict with usable precision — reported both pooled-domain and per-instrument where sample permits (the strict gate is shown an honest detection floor, or shown blind, on each domain); (b) the L5 stringency lever is characterized (EXP-006 curve + EXP-007 lenient-variant operating characteristics, including its economically sub-material pass rate per D-lenientL5); (c) the per-instrument MDE map (EXP-008) is produced; (d) EXP-011 yields a predeclared-loss-minimising **recommended** operating point per domain plus the recorded conditional adoption rule. **Success is stating these characteristics and landing a recommendation — not adopting anything.**
- **Success (optional/context — strengthens the phase but does not gate it):** the broadened untuned effect-size distribution (EXP-009) and the split-protocol robustness comparison (EXP-010). Per §8, if the phase proves too heavy these two may be deferred to a follow-up checkpoint **without failing the phase**; the deferral is recorded and each deferred question is carried forward as an explicit open item. (This resolves the prior conflict between the §8 drop rule and the success criteria: only EXP-009/EXP-010 are droppable; EXP-005–008 and EXP-011 are not.)
- **Failure:** substrate/harness re-validation fails (P0, §7) → halt; or the keystone-closure machinery (EXP-005) cannot be made to work on any domain.
- **Inconclusive (per domain/cell):** effective sample too small for the D-prec precision target — **expected most likely on 4h and on per-instrument 4h cells** (EXP-008). Treated as a first-class measured result ("under-powered there"), reported with honest CIs, not forced to a verdict.

---

## 10. Explicit non-goals (deferred)

- **Adopting/freezing any new referee or operating point** — deferred to the **Phase 003 decision phase**, with fresh synthetic draws (D-posture, meta-Goodhart guardrail).
- **Incremental-information / ensemble candidate unit** — **Phase 003 seed**; specified design-only in §11, not run in Phase 002.
- **Chart-type candidate signals** (Line Break / Renko / Heiken Ashi as candidates) — deferred by operator decision until the testing framework is concluded.
- Non-stationary / drifting planted edges; full cross-market k-of-N replication (beyond L4); tunable context-dependent loss beyond the single predeclared EXP-011 form; programme-level multiplicity / file-drawer registry. (Carried from P1-§12.)

---

## 11. Phase 003 seed (design-only): incremental-information unit

Recorded now so Phase 003 starts from a specified seed, not a blank page. **Not executed in Phase 002.**

- **Idea:** redefine the unit of qualification from a *standalone* directional signal to an **incremental-information unit** — judge a candidate by the edge it adds *beyond* an existing reference signal (the leg L3 "naive control" generalised into the unit itself).
- **Why next:** it changes *what* the referee judges, so it belongs after the referee's sensitivity and operating point are settled (Phase 002), and it pairs naturally with the Phase 003 *adoption/decision* work.
- **Open design questions for Phase 003:** how to construct a known-truth substrate for incremental edges (analogue of EXP-001); how the gate stack's legs map onto a conditional/marginal claim; cross-unit dependence (PS-T7) when the reference signal and candidate share structure.

---

## 12. Summary

Phase 001 built and calibrated the referee and produced its blind-spot map, but left open whether that map is an honest detection floor for *real* edges, and identified L5 materiality as the single stringency lever. Phase 002 closes the open item (EXP-005 near-MDE realistic-candidate anchor) and characterizes the lever and the map's robustness (EXP-006 threshold sweep + EXP-007 lenient variant, EXP-008 per-instrument, EXP-009 broadened dogfood, EXP-010 split protocols), then synthesizes a **recommended** operating point under a predeclared loss (EXP-011). It deliberately stops at *recommend*: adoption and the new incremental-information unit are the Phase 003 decision/expansion phase, run on fresh draws. We will know whether the referee is honestly sensitive, how its one stringency lever behaves, and what operating point we would recommend — *before* we commit to any of it.
