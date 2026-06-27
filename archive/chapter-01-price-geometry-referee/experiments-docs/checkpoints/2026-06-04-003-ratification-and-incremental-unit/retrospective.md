# Phase 003 — Ratification & Incremental-Information Unit (Framework Conclusion) — Retrospective

**Phase number:** 003
**Design finalised:** 2026-06-04
**Retrospective written:** 2026-06-05
**Status:** COMPLETED — all five planned experiments (EXP-012…016) executed and governance-reviewed; adversarial review issued amendment [A1](amendments/2026-06-04-A1-incremental-unit-corrections.md) and Track B (EXP-013→014→015) was re-validated 2026-06-04/05. **Phase outcome: PARTIAL_SUCCESS** (§9) — Track A concluded, Track B did not reach a validated *and* calibrated incremental unit, so the framework is **not** FULL_FRAMEWORK_CONCLUDED and Phase 004 is blocked by default pending an operator decision (§11).

**Design reference:** [design.md](design.md)
**Amendment:** [A1 — Incremental-Unit Methodology Corrections](amendments/2026-06-04-A1-incremental-unit-corrections.md)
**Predecessor retrospective:** [Phase 002](../2026-06-03-002-referee-refinement-and-stringency/retrospective.md)
**Experiments:** EXP-012 (Track A spine), EXP-013 (Track B P0), EXP-014 (Track B logic), EXP-015 (Track B keystone), EXP-016 (conclusion anchor) — see `python/experiments/<ID>/report.md`.

---

## 1. Phase objective recap

Phase 002 left the strict referee fully characterized and trustworthy but with two items open *by design*: (i) the EXP-011 loose operating point (τ 0.75/0.25/0.5 on 5m/1h/4h) was only **recommended** — chosen by reading the same synthetic draws used to characterize it; and (ii) the **incremental-information / portfolio-fitness unit** existed only as a design-only seed (P2-§11).

Phase 003's job was to **conclude the testing-framework programme** by completing the qualification suite the operator will use for signal exploration. Three concrete deliverables ([design §1](design.md)):

1. **Ratify the loose referee (Track A).** Re-measure the EXP-011 loose point on **fresh synthetic draws** (new seeds, disjoint from Phase 001/002) and either adopt it per the predeclared conditional adoption rule or record a clean strict-fallback — the meta-Goodhart-clean freeze (the point is fixed going in; fresh draws *confirm*, they do not re-select).
2. **Build and validate the incremental unit (Track B).** Promote the P2-§11 seed to an executed, validated referee that judges a candidate by the **incremental net edge it adds beyond an existing reference signal R** (the economic reading: *portfolio fitness*), mirroring the Phase 001 substrate→logic→calibration chain (EXP-013→014→015).
3. **Demonstrate the assembled suite (EXP-016).** Run the complete "two referees + fitness check" suite end-to-end on both the reject path (real dogfood) and a synthetic positive path, as the framework-conclusion integration anchor.

The binding constraint (D-posture): this **is** the decision/adoption phase. Adoption is in scope, but governed by the predeclaration-freeze and fresh-draw discipline. The frozen Phase 001 strict gate stack remains the reference object throughout. Only the **FULL_FRAMEWORK_CONCLUDED** outcome (§9 — which requires a *validated* fitness unit, not merely an attempted one) unlocks Phase 004.

---

## 2. Outcomes vs objectives

| EXP | Role | Track | Verdict | One-line outcome |
| --- | --- | --- | --- | --- |
| 012 | **Loose-referee ratification (Track A spine)** | A | **SUPPORTED** | Fresh draws reproduce Phase 002 exactly; all three domains `ADOPT_LOOSE`. The loose point is now *adopted*, not merely recommended. |
| 013 | Incremental substrate (Track B P0) | B | **SUPPORTED** | Recovers planted marginal edge (108/108); no phantom edge from shared R–C structure. Substrate gate PASS. |
| 014 | Incremental referee logic | B | **SUPPORTED** | 7/7 golden-fixture verdicts, 35/35 leg states, L3 generalized to reference-control, no short-circuit. Logic correct. |
| 015 | **Portfolio-fitness calibration (Track B keystone)** | B | **REFUTED** | FPR controlled, but every domain has qualifying dependence cells with **no finite MDE**. The incremental unit is not validated for freeze. |
| 016 | Assembled-suite composition anchor | A+B | **BLOCKED** | Correctly stopped before measurement: EXP-015 is REFUTED (not COMPLETE) and the dogfood reference book is undefined. |

**Adversarial review (amendment [A1](amendments/2026-06-04-A1-incremental-unit-corrections.md)) corrected Track B methodology (F01/F03/F04) and re-validated EXP-013→014→015. Direction unchanged on every experiment**: Track A SUPPORTED, Track B substrate/logic PASS, Track B calibration REFUTED.

---

## 3. Track A — the loose referee is ratified and adopted (headline for the half that succeeded)

**The EXP-011 loose operating point survives fresh-seed ratification on every domain. Phase 003 adopts τ 0.75/0.25/0.5 on 5m/1h/4h as the second screen alongside the frozen strict gate.**

EXP-012 fixed the τ point *before* generating any fresh draws (the Goodhart guardrail), then confirmed its operating characteristics on seeds disjoint from Phase 001/002 (`payload_overlap_count = 0`; 6 benign 32-bit integer collisions versus ≈7.1 expected by chance). The predeclared three-condition adoption rule (FPR, MDE-within-one-grid-step, sub-material rate within ±0.10 and below the 0.50 ceiling) passed cleanly on all three domains:

| Domain | Fresh gate FPR (α₀) | Fresh loose MDE | Phase 002 MDE | Sub-material rate (fresh / P002) | Decision |
| --- | --- | --- | --- | --- | --- |
| 5m | 0/4000 | 0.5 bps | 0.5 bps | 0.399 / 0.398 | `ADOPT_LOOSE` |
| 1h | 0/4000 | 2.0 bps | 2.0 bps | 0.027 / 0.026 | `ADOPT_LOOSE` |
| 4h | 0/4000 | 8.0 bps | 8.0 bps | 0.000 / 0.000 | `ADOPT_LOOSE` |

The MDEs reproduce Phase 002 to the edge grid; the sub-material rates reproduce within the ±0.10 tolerance. The 4h split-sensitivity gate (D-ratify-4h) also cleared: the single chronological split and the anchored walk-forward K=5 protocol both returned a 4h loose MDE of 8.0 bps with FPR 0.0 (`protocols_agree = true`), so the corrected-EXP-010 4h split flag did not block adoption.

**Reading.** Track A is the clean half of the phase. The meta-Goodhart freeze that Phase 002 deferred is now executed: the loose referee was confirmed on randomness *not* used to pick it, without ever touching the holdout. Two honest caveats carry forward: 5m still passes with a material ~0.40 sub-material rate (nearly half its operating-MDE passes are net-positive but economically negligible), and ratification establishes robustness to **synthetic-draw selection** only — not to fresh market regimes, which remain sealed behind the global holdout.

---

## 4. Track B — substrate and logic validated, calibration refuted

Track B mirrored the Phase 001 substrate→logic→calibration chain on the new incremental claim. The first two links held; the keystone did not.

**EXP-013 — incremental substrate (H-incr-substrate SUPPORTED).** The EXP-001 analogue for incremental edges passed both halves of its binding test: it recovered the planted marginal edge in 108/108 cells (max absolute recovery error 0.396 bps, below the `max(0.5 bps, 15% of m)` tolerance), and it read **no phantom edge** for the redundancy null where R and C share structure but C adds nothing marginal. Under the A1/F01 across-draw verdict, the most positive across-draw mean across all 12 redundancy cells is −0.041 bps — not a single cell carries even a positive point estimate. The redundancy null resolved to **8 PASS / 3 UNDER_POWERED (BTCUSD/1h, BTCUSD/4h, USTEC/4h) / 1 NULL_COST_DOMINATED (XAUUSD/4h) / 0 PHANTOM**, with the binding control powered in 9/12 cells. The substrate gate is PASS: the incremental machinery does not manufacture portfolio fitness from correlation.

**EXP-014 — incremental referee logic (H-incr-correct SUPPORTED).** The incremental referee reproduced 7/7 predeclared golden-fixture verdicts and 35/35 L1–L5 leg states with all legs exposed and no short-circuit. The `l3_reference_control_fail` fixture rejects a candidate with a standalone-looking edge that adds nothing beyond R, isolating the incremental-beyond-R requirement — the core portfolio-fitness generalization of L3. After the A1/F04 block-length fix, `effective_n` is episode-aware (276.9 on `all_pass`) and all verdicts/leg states reproduced unchanged. The logic wiring is correct.

**EXP-015 — portfolio-fitness calibration (H-incr-floor REFUTED, the Track B keystone).** FPR stayed controlled in every accepted cell (max 0.0 on 5m, 0.01 on 1h/4h; no cell exceeds α₀), but the unit **failed the finite-MDE requirement in every domain**: 5m has 1 failing cell, 1h and 4h have 2 each, all in synchronous high-overlap `null_R` contexts. Under the predeclared worst-case rule (a qualifying cell with no finite MDE refutes the domain), all three domains are REFUTED. The A1/F03 diagnostics located the cause precisely: in every failing cell the verdict pass rate equals the **L2 standalone-significance** leg's pass rate (5m/high 0.75, 1h/mod 0.784, 1h/high 0.716, 4h/mod 0.63, 4h/high 0.382) with L1/L4/L5 saturated at 1.0 and L3 ≥ 0.97; `tpr_by_instrument.csv` shows the shortfall is driven by **BTCUSD**, whose standalone TPR is 0.0–0.136 even at the 32 bps edge ceiling while the other three instruments reach or approach 1.0, holding the pooled per-cell TPR below the 0.80 power floor.

**Reading.** The refutation is **sensitivity-driven, not false-positive-driven**, and it is localized to one leg and one instrument — not a substrate or logic defect (EXP-013/014 still stand). The incremental unit, as calibrated at this operating point, cannot reliably detect a marginal edge when the candidate must clear a standalone-significance bar that BTCUSD's high-cost, low-power return series defeats at the synchronous-high-overlap corner of the dependence grid. The portfolio-fitness unit is **not validated** and **cannot be frozen** for Phase 004.

---

## 5. The adversarial review and amendment A1 — what the governance layer caught

The Track B story is inseparable from the adversarial review that produced amendment [A1](amendments/2026-06-04-A1-incremental-unit-corrections.md) (findings F01–F07). A1 is a **correctness/methodology correction, not a re-selection** of any predeclared object — the primary estimator (D-incr-form), operating point, substrate construction, and leg *mapping* are all unchanged in intent. It corrected the inference layer and diagnostics, and because that touched frozen Track B code (`xen/incremental_referee.py` + two experiment scripts), D-reuse forced the EXP-013→014→015 re-validation chain *before any Track B result was re-read*. The corrections:

- **F04 — block length on the contiguous series.** The block length was estimated on the gap-extracted denominator series, which discarded cross-episode time gaps and collapsed `block_length = 1` in every cell — quietly turning the L2/L3 CI-lower significance machinery into an i.i.d. bootstrap, in tension with governance §2 for a unit meant to be frozen and applied to autocorrelated real candidates. The fix estimates the block on the contiguous full-length marginal series; it is adaptive (≈13 for episode-coherent 5m, 1 for genuinely per-row signals) and **directionally conservative** (wider CIs make passing harder), so it cannot convert a refutation into a false validation. EXP-014 re-ran with verdicts/leg states unchanged.
- **F01 — across-draw redundancy verdict.** The EXP-013 redundancy null (the binding Track B control) was being judged on a *single canonical draw's* CI, which in cost-dominated/low-N cells was far too wide to detect a materiality-sized phantom — those cells "passed" only because the test had no power, and four of five even showed positive single-draw point estimates from one-draw noise. The fix judges the verdict on the across-draw distribution with an explicit `UNDER_POWERED` class that is **reported, never counted as a clean pass**, plus a requirement that the binding control be powered in at least one cell. Result: 3 honestly-flagged under-powered cells where the original silently passed.
- **F03 — per-leg and per-instrument diagnostics.** EXP-015 discarded leg states and pooled instruments, making the REFUTED verdict undiagnosable (TPR plateaued at exactly 0.75, ambiguous between a pooled ceiling and a single-instrument cap). Retaining `leg_pass_rates.csv` and `tpr_by_instrument.csv` resolved it to the L2/BTCUSD cause above.
- **F02 — first-principles leg semantics.** A1 documents *why* the incremental legs are deliberately **less conservative** than the strict gate, and flags the residual risk: **L4** (no material sign reversal, vs strict "both segments positive") and **L5** (point estimate > materiality, vs strict CI-lower > materiality) are weaker than their strict counterparts. EXP-014 confirms the legs are *internally consistent*; it does **not** establish that the reduced-conservatism L4/L5 are sound for live use. **The legs must not be treated as validated for freeze until an operator accepts the L4/L5 reductions (or overrides them to strict CI-based forms and re-validates).** This is moot while EXP-015 stands REFUTED, but it is a precondition for any future fix-and-freeze attempt.

**The governance layer did its job — twice now.** As in Phase 002 (EXP-010's CI-scaling artifact, F01), adversarial review caught wrong-power / undiagnosable results before they reached the phase conclusion. None of the corrections changed the phase's direction, which is itself the reassurance: the REFUTED keystone is robust to the methodology fixes, not an artifact of them.

---

## 6. EXP-016 — the assembled suite correctly refused to assemble

EXP-016 was the framework-conclusion integration anchor: wire the strict + ratified-loose + incremental suite end-to-end on both the reject path (real EXP-009 dogfood) and a synthetic positive path. It returned **BLOCKED** with two recorded blockers: EXP-015's `overall_status = REFUTED` (the precondition required COMPLETE), and a missing `inputs/dogfood_reference_book.csv`. No suite manifest, expected-output matrix, positive fixture, or composition summary was produced.

This is the **correct** outcome, not a failure of the experiment. The script did not invent an undefined dogfood reference book and did not proceed past a refuted incremental unit — it confirmed governance discipline by stopping. The §8-sequencing fallback (migrate the positive-path composition check into EXP-015 if EXP-016 is dropped) is also unavailable here, because EXP-015 itself is REFUTED — there is no calibrated incremental unit through which to carry a planted-edge candidate. The suite's pass path therefore remains **unexercised** under the incremental unit, which is exactly what PARTIAL_SUCCESS implies.

---

## 7. State of the testing framework — is it "concluded"?

The operator's standing question (signal exploration begins only after the framework is concluded). Phase 003's honest answer:

**The two-referee screen is concluded and usable today. The fitness check is not.** Concretely, the operator can take any candidate signal right now and screen it with both the **frozen strict gate** (validated and adopted since Phase 002) and the **ratified-loose referee** (adopted this phase, EXP-012) for standalone net edge at two stringency levels. That half of the target instrument is complete and frozen.

**What does not exist is a validated portfolio-fitness unit.** Its substrate is sound (EXP-013) and its logic is correct (EXP-014), but its calibration is refuted (EXP-015) and — even if recalibrated — its reduced-conservatism L4/L5 legs are not yet operator-accepted for freeze (A1/F02). The "two referees + fitness check" suite that Phase 003 set out to freeze ships as **two referees only**.

Against design §9, that is precisely **PARTIAL_SUCCESS**: Track A completes with a recorded adoption decision, but Track B does not reach a validated, calibrated incremental unit. The framework is **not** FULL_FRAMEWORK_CONCLUDED, so Phase 004 does **not** auto-unlock. It may begin only if the operator records an explicit decision to rescope Phase 004 to **standalone-only** qualification (using the two ratified referees), with the incremental/fitness unit carried to a follow-up checkpoint as an open item (§10/§11).

---

## 8. Lessons learned

1. **The meta-Goodhart freeze worked exactly as designed.** Fixing τ before the fresh draws and confirming (not re-selecting) on disjoint seeds is the cleanest part of the phase. EXP-012's fresh MDEs reproduced Phase 002 to the grid and the 4h split gate agreed — adoption is now defensible against synthetic-draw selection bias. This ratification pattern (fix the point in design, confirm on fresh seeds, report per-domain with an explicit materiality verdict) is reusable for any future operating-point freeze.
2. **A substrate and correct logic do not imply a usable operating point.** EXP-013/014 passed cleanly, yet the calibrated unit failed (EXP-015). The substrate→logic→calibration chain is not a formality: each link tests a genuinely different claim, and the keystone (finite MDE under dependence stress) is where an inference unit actually earns the right to be frozen. The chain caught the weakness at the correct link.
3. **The binding control must be judged on its sampling distribution, not one draw.** F01's single-draw redundancy verdict gave low-power cells a free pass. Judging the redundancy null on the across-draw distribution — with an explicit `UNDER_POWERED` class that is reported rather than counted as a pass — is now the standard for any known-truth null control. "Passed because the test had no power" is a failure mode that must be designed out.
4. **Gap-extracted series destroy the time axis the bootstrap needs.** F04: estimating block length on the denominator-masked series collapsed it to 1 everywhere and silently made the significance legs i.i.d. For any conditional/marginal estimator, the inference block length must be estimated on the **contiguous** series so within-episode autocorrelation is preserved. This is the incremental analogue of Phase 001/002's `block_length = 1` finding — except here the 1 was an *artifact*, and the corrected block recovers the episode as the independent unit.
5. **Diagnostics are not optional for a REFUTED keystone.** F03: discarding leg states and pooling instruments made the refutation undiagnosable. Retaining per-leg and per-instrument tables converted "the unit fails somewhere" into "the L2 standalone-significance leg fails, driven by BTCUSD" — a precise, actionable target for the follow-up. A refutation without attribution wastes the measurement.
6. **Reduced conservatism must be justified on first principles and operator-accepted, not inferred from fixture reachability.** F02: the incremental L4/L5 are weaker than the strict legs by design, and EXP-014's internal-consistency pass does **not** validate them for live use. Any leg that departs from the frozen reference's conservatism carries a standing freeze precondition: explicit operator acceptance or a strict-form override + re-validation.
7. **A correctly-blocked experiment is a successful governance result.** EXP-016 refusing to assemble an un-assembleable suite (refuted dependency + undefined input) is the system working, not a gap. The absence of a fabricated dogfood reference book is the discipline that keeps the eventual framework conclusion trustworthy.
8. **Adversarial review changed the rigor, not the direction.** Every A1 correction made passing *harder* (wider CIs, power gates, honest under-powered flags) and the phase verdicts held: Track A SUPPORTED, substrate/logic PASS, calibration REFUTED. A correction layer that cannot flip a conclusion is the strongest evidence the conclusion is real.

---

## 9. Phase verdict vs §9 criteria

**PARTIAL_SUCCESS — Track A concluded; Track B did not reach a validated, calibrated incremental unit.**

Mapping to design [§9](design.md):

- **FULL_FRAMEWORK_CONCLUDED — NOT reached.** It requires EXP-013 validates the substrate (✓), EXP-014 confirms logic correctness (✓), **EXP-015 produces a portfolio-fitness MDE map at controlled FPR across the D-dependence grid (✗ — REFUTED)**, and EXP-012 delivers a per-domain ratification/adoption decision (✓). The single unmet condition (EXP-015) is decisive: D-adopt is not satisfiable because the validated-incremental element of the concluded suite does not exist.
- **PARTIAL_SUCCESS — reached (this outcome).** Track A completes (EXP-012 adoption recorded), Track B does not reach a validated+calibrated incremental unit (EXP-015 attains no finite portfolio-fitness MDE at D-prec across the dependence grid). The suite ships as two referees only; the incremental/fitness unit is carried to a follow-up checkpoint as an open item.
- **BLOCKED / DEFERRED — not triggered.** No P0 re-validation failed (the A1-driven re-validation *passed*), EXP-014 did not show the logic uncorrectable, and the phase was not halted for cause. EXP-016's BLOCKED status is a within-phase precondition stop, not a phase-level BLOCKED outcome.

The two non-SUPPORTED headline verdicts are **clean predeclared findings, not phase failures**: EXP-015 REFUTED is a falsifiable claim resolving against the unit at this operating point (with the cause attributed), and EXP-016 BLOCKED is the correct governance stop. Phase 003 answered every question it posed; the framework simply is not finishable on this attempt because the fitness unit's calibration genuinely fails.

---

## 10. Proposed next research direction

Under §9 PARTIAL_SUCCESS, Phase 004 is **blocked by default**. Two operator-gated paths forward, mutually exclusive at the phase boundary:

**Path A — Rescope Phase 004 to standalone-only qualification (ship the two referees).**
Record an explicit decision to begin Phase 004 with the frozen strict gate + ratified-loose referee as the qualification instrument, deferring the incremental/fitness unit to a later checkpoint. This unblocks real signal exploration immediately using the half of the suite that is concluded. The cost: candidates are screened for *standalone* net edge only; portfolio fitness (does C add edge beyond the existing book?) is not assessed, so the validated book cannot yet be grown with a leakage-controlled incremental test. The mandatory Phase 004 multiplicity / file-drawer registry precondition (design §11) still applies before any candidate screening begins.

**Path B — Open an incremental-unit follow-up checkpoint before Phase 004.**
Carry the incremental/fitness unit to a new checkpoint that fixes the EXP-015 failure before any signal exploration. The F03 diagnostics make the target concrete: the failure is the **L2 standalone-significance leg driven by BTCUSD** at the synchronous-high-overlap corner. Candidate follow-up scopes (each a new predeclared experiment, not an in-place edit):
- Re-examine whether L2 (standalone C significance) belongs in a *portfolio-fitness* unit at all — the A1/F02 rationale already notes L3 (beats R) is the binding incremental test, so an L2-relaxed or L2-removed variant may be the correct unit, validated fresh.
- Resolve the A1/F02 freeze precondition: operator acceptance of the reduced-conservatism L4/L5, or a strict-CI-form override with re-validation.
- Re-run the EXP-013→014→015 chain on the revised unit; only a finite MDE map at controlled FPR across the dependence grid reaches the validated state FULL requires.

**Standing programme-level deferrals (unchanged):** programme-level multiplicity / file-drawer registry (a hard Phase 004 precondition); non-stationary / drifting planted edges; tunable context-dependent loss beyond the EXP-011 form; multi-signal / k-of-N reference books beyond a single R. Chart-type candidate signals (Line Break / Renko / Heiken Ashi) remain a Phase 004 candidate family once the chosen path unblocks exploration.

---

## 11. Operator decision (2026-06-05) — incremental-unit follow-up before Phase 004

**Decision recorded: Path B (§10) — open a new incremental-unit follow-up checkpoint and fix the unit before any signal exploration.** The operator declines the standalone-only Phase 004 rescope (Path A). Phase 004 remains blocked until the follow-up delivers a validated *and* calibrated incremental/portfolio-fitness unit (or the operator later records a different decision).

**What this commits to:**

1. **The two-referee screen ships as-is.** The frozen Phase 001 strict gate stack and the **ratified-loose referee adopted this phase** (EXP-012, τ 0.75/0.25/0.5 on 5m/1h/4h) are the confirmed standalone qualification instrument and need no further work. They are carried into the follow-up unchanged.
2. **A new predeclared follow-up checkpoint is opened** to fix the EXP-015 keystone failure before it is frozen — preserving the meta-Goodhart discipline (the revised unit is predeclared, then measured once on its purpose-built substrate). EXP-013 (substrate) and EXP-014 (logic) stand validated and are reusable; the follow-up re-opens the unit at the calibration layer with the A1/F03 attribution as its starting diagnosis. Concretely, the follow-up must:
   - **Address the L2 standalone-significance leg / BTCUSD sensitivity** — the F03-attributed cause of the no-finite-MDE refutation. Per A1/F02, L3 (beats reference R) is the binding incremental test, so an **L2-relaxed or L2-removed variant** is a candidate redesign, to be predeclared and validated fresh rather than tuned against EXP-015's numbers.
   - **Resolve the A1/F02 freeze precondition** — record operator acceptance of the reduced-conservatism L4/L5 legs, or override them to the strict CI-based forms; either way re-validate.
   - **Re-run the substrate→logic→calibration chain** on the revised unit (EXP-013→014→015 analogues). Only a finite portfolio-fitness MDE map at controlled FPR across the D-dependence grid reaches the validated state the framework conclusion requires.
3. **Phase 004 unlock is deferred to the follow-up's FULL-equivalent outcome.** When the follow-up delivers a validated+calibrated incremental unit, the concluded "two referees + fitness check" suite is frozen and Phase 004 (first real signal-exploration phase) may begin. The mandatory Phase 004 multiplicity / file-drawer registry plan (design §11) remains a hard precondition before any candidate screening, regardless.

**Process note (meta-Goodhart preserved):** the incremental-unit redesign is predeclared in the follow-up checkpoint's `design.md` *before* its re-calibration is read; the ratified-loose and strict referees are already frozen and are not reopened by this decision. No element is tuned against real candidate signals — that remains Phase 004's separate, frozen-suite-using work.

**Next action:** author the follow-up checkpoint `design.md` (a new `docs/experiments-docs/checkpoints/<date>-004-...` phase that predeclares the revised incremental unit and its substrate→logic→calibration chain). This is a fresh design task and is not part of this retrospective.
