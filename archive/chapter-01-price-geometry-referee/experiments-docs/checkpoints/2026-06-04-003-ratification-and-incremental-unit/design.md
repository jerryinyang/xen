# Phase 003 — Ratification & Incremental-Information Unit (Framework Conclusion)

**Phase number:** 003
**Design finalised:** 2026-06-04
**Status:** ACTIVE (design complete; execution begins at EXP-012)

**Provenance:**
- Predecessor: Phase 002 `2026-06-03-002-referee-refinement-and-stringency` — [design.md](../2026-06-03-002-referee-refinement-and-stringency/design.md), [retrospective.md](../2026-06-03-002-referee-refinement-and-stringency/retrospective.md).
- Phase 002 delivered a *characterized, trustworthy* referee: the strict gate stack is an **honest detection floor** (not blind; EXP-005), its single stringency lever is fully traced and one-dimensional (EXP-006/007), the per-instrument map is conservative-leaning (EXP-008), untuned simple strategies are robust net losers (EXP-009), inference is split-robust on 5m/1h with 4h moving toward greater sensitivity (EXP-010), and a predeclared-loss **recommended** loose operating point exists per domain (EXP-011: τ 0.75/0.25/0.5 on 5m/1h/4h).
- Phase 002 deliberately **adopted nothing** (D-posture). It left two items by design: (i) the loose operating point was *recommended*, not *ratified* — it was chosen on the same draws used to characterize it; (ii) the **incremental-information unit** was a design-only seed (P2-§11).

This phase references Phase 001 decisions as *P1-§n / P1-D-x* and Phase 002 decisions as *P2-§n / P2-D-x*.

---

## 1. Phase objective

**Conclude the testing-framework programme** by completing the qualification suite the operator will use for signal exploration. Three concrete deliverables:

1. **Ratify the loose referee (Track A).** Re-measure the EXP-011-recommended loose operating point on **fresh synthetic draws** (new random seeds, fully disjoint from the Phase 001/002 draws) and either **adopt** it per the EXP-011 conditional adoption rule, or record a clean decision not to adopt where it fails on the fresh seeds. This is the meta-Goodhart-clean freeze: the operating point is *fixed going in* (predeclared from EXP-011) and the fresh draws *confirm* it — they do not re-select it.
2. **Build and validate the incremental-information / portfolio-fitness unit (Track B).** Promote the P2-§11 seed from design-only to an executed, validated referee that judges a candidate by the **incremental net edge it adds beyond an existing reference signal** — the economic reading being *portfolio fitness* (does this candidate earn its place alongside what is already validated?). Track B mirrors the Phase 001 substrate→logic→calibration chain on the new incremental claim.
3. **Demonstrate the assembled suite (framework conclusion).** Run the complete **"two referees + fitness check"** suite end-to-end on the real untuned dogfood set as an integration anchor, confirming it composes and behaves sensibly before the programme is declared concluded.

**Target instrument (end-state).** For any candidate signal, the operator can: (a) screen it with **both referees** (strict + ratified-loose) for standalone net edge at two stringency levels; and (b) evaluate its **portfolio fitness** — the incremental edge beyond the already-validated book — with the incremental unit. Phase 003 *builds and freezes* this suite. **Phase 004 (the first signal-exploration phase) *uses* it.**

**Posture.** This is the **decision/adoption + framework-completion** phase that P2-D-posture deferred here. Adoption is in scope (that is the point), but it is governed by the predeclaration-freeze and fresh-draw discipline (§2, §10). On the **FULL_FRAMEWORK_CONCLUDED** outcome (§9) the framework is frozen and no further referee characterization is planned; lesser outcomes (§9) carry the unfinished element forward to a follow-up and do **not** unlock Phase 004.

---

## 2. Predeclared decisions (frozen before any measurement is read)

Frozen for the phase. Changing any requires a new predeclared design amendment (meta-Goodhart guardrail).

| # | Decision | Resolution |
| --- | --- | --- |
| D-posture | Phase identity | **Adopt & conclude.** Phase 003 ratifies the loose operating point and builds+freezes the incremental unit. The frozen Phase 001 strict gate stack remains the reference object throughout and is carried into the concluded suite unchanged. |
| D-reuse | Substrate & harness | **Reuse the EXP-001-validated substrate and the EXP-003 calibration harness (`python/src/xen/referee_calibration.py`) unchanged** for Track A. Track B requires **new** incremental machinery (`python/src/xen/incremental_referee.py` or equivalent); any new module is validated (EXP-013/014) before it calibrates anything (EXP-015). Any change to the loader, `aggregate_ohlc`, generators, or the frozen harness triggers re-validation (P0) before dependent experiments. |
| D-frozen-ref | Reference referees | The Phase 001 **minimal baseline** and **5-check strict gate stack** are carried forward **frozen and unchanged**. The **loose referee** is the EXP-006/EXP-011 τ-operating-point variant, fixed at the EXP-011 recommendation; it is the object ratified in Track A, not a free parameter. |
| D-invariants | Carried-forward invariants | Domains **5m/1h/4h**; instruments **EURUSD/XAUUSD/BTCUSD/USTEC**; per-domain costs & materiality (P1-D-cost); coverage `min_coverage` (5m strict, 1h/4h 0.90); precision target (95% Wilson half-width ≤0.03 FPR / ≤0.05 TPR); block bootstrap (P1-D-block); α grid {0.10, 0.05, 0.01}, primary α₀=0.05. Retained **unchanged** so Phase 003 results compose with the Phase 001/002 map. |
| D-ratify-point | Operating point under ratification (EXP-012) | The point ratified is **exactly the EXP-011 recommendation** — τ **0.75 / 0.25 / 0.5** on 5m/1h/4h — fixed before fresh draws are generated. Fresh draws **confirm** its operating characteristics; they do **not** re-select τ. **Adoption rule (predeclared, all three conditions, per domain):** adopt the loose point iff (1) fresh-draw gate FPR ≤ α₀ at D-prec precision; (2) the fresh-draw MDE equals the Phase 002 MDE within one edge-grid step; **and (3) the fresh-draw economically sub-material pass rate at the operating MDE reproduces the Phase 002 value within ±0.10 absolute *and* does not exceed the 0.50 ceiling** (the EXP-007 sub-material cutoff; binding mainly on 5m, whose Phase 002 sub-material rate is 0.398). If any condition fails, that domain **falls back to the strict point** (no adoption there). Adoption is **reported per domain with an explicit materiality verdict** (FPR, MDE, and sub-material rate all stated). 4h additionally requires passing the split-sensitivity gate (D-ratify-4h). |
| D-ratify-4h | 4h split-sensitivity gate (EXP-012) | Because corrected EXP-010 flagged 4h as split-sensitive (toward *lower* MDE under more-OOS protocols), 4h ratification additionally requires the fresh-draw measurement to agree across the **single chronological split** and an **anchored walk-forward K=5** protocol (reusing the corrected EXP-010 test-size-weighted, stratified pooled-OOS estimator). **Predeclared agreement rule (fixed now, not revisable at EXP-012 scope time):** the two protocols *agree* iff their fresh-draw 4h gate MDEs lie within **one edge-grid step** of each other **and both** hold FPR ≤ α₀ at D-prec. 4h adopts the loose point iff it passes all three D-ratify-point conditions under the single split **and** the two protocols agree by this rule; **otherwise 4h falls back to strict (no adoption)**. The outcome is **binary** (adopt or strict-fallback) and fully determined by these predeclared criteria — there is **no** intermediate 'adopt-with-caveat' verdict. |
| D-fresh | Fresh-draw definition | **"Fresh" means new random seeds for the known-null and known-positive generators, disjoint from every Phase 001/002 seed — NOT new real data.** All draws are generated on the **same first-70% analysis slice** of real prices. The final 30% global holdout is **never** loaded. Fresh-draw seeds are recorded in `run_metadata.json`. This is the Goodhart guardrail (the adoption is confirmed on randomness not used to pick the point), implemented without ever touching the holdout. |
| D-incr-form | Incremental-edge formalization (EXP-013/014) | The unit judges the **incremental net edge of candidate C beyond reference signal R**, read economically as *portfolio fitness*. **Primary estimator — model-free marginal net P&L (predeclared, fixed now, not deferred to scope):** incremental edge = (mean net-of-cost real-price return of the combined book **with** C) − (combined book **without** C), per eligible bar. **Combination rule:** a fixed predeclared position blend — additive then clipped to the per-domain position bound — so C alters the book's position only where C is active. **Cost attribution:** cost is charged on the *incremental turnover* C induces in the combined book (position change relative to R-alone), never on C's standalone turnover. **Denominator:** bars where the combined position differs from R-alone; zero-baseline handled with finite guards. This estimator imposes **no linear / i.i.d. / stationarity model** of the R–C relationship (governance §2/§4), so dependence cannot manufacture a phantom linear-residual edge; it *is* portfolio fitness by construction. The legged machinery (CI-lower-bound > materiality, block bootstrap on the **joint** (R,C) series) is applied to this marginal-P&L series. **Linear residualization is permitted only as a secondary diagnostic**, never the qualifying estimator, and only if it first passes the EXP-013 redundancy and nonlinear-dependence nulls. The EXP-013 scope states the simpler alternative considered and why this primary was chosen. ⚠ Confirm before EXP-013. |
| D-incr-substrate | Incremental known-truth substrate (EXP-013) | The EXP-001 analogue for incremental edges. Must construct (i) a **positive** case — R and C where C carries a *known* marginal edge beyond R, recoverable within the EXP-001 tolerance family `max(0.5 bps, 15% of m)`; and critically (ii) a **redundancy null** — R and C that **share structure** but where C adds *no* marginal edge, which the substrate must read as incremental edge ≈ 0 (no phantom edge from shared structure). The redundancy null is the binding control: it is the incremental analogue of "two structurally different nulls agreeing at ≈0." ⚠ Confirm before EXP-013. |
| D-incr-legs | Leg mapping for the conditional claim (EXP-014) | How the 5 gate legs map onto the marginal/conditional claim. Default: **L3 "naive control" generalizes to "reference control"** (the incremental edge replaces the raw edge); L1/L2 readiness and L4 cross-market apply to the incremental position; L5 materiality is the incremental-edge materiality buffer. Frozen and verified on golden fixtures before EXP-015. ⚠ Confirm before EXP-014. |
| D-dependence | Reference/candidate dependence handling | The incremental calibration (EXP-015) must measure operating characteristics **across a predeclared dependence grid** between R and C, since shared structure is the false-positive mode the track exists to control. **Dependence grid (fixed now):** (i) R–C position agreement / shared-latent-state strength ∈ {independent, moderate ρ≈0.4, high ρ≈0.8}; (ii) active-overlap fraction (bars both active) ∈ {low, medium, high}; (iii) lead/lag alignment ∈ {synchronous, C lags R by 1 bar, C leads R by 1 bar}; (iv) reference edge strength ∈ {null R, R at its domain MDE}. The redundancy-null FPR (no marginal edge despite dependence) must hold ≤ α₀ at D-prec in **every** grid cell that meets D-prec, not a single easy case; under-powered cells are reported as such. Block bootstrap and any embargo are applied to the joint (R,C) series. The dependence stress is **core** calibration, not optional. |
| D-adopt | What "adoption" freezes | At phase end the **concluded qualification suite** = {frozen strict gate stack, ratified loose referee (per-domain, possibly strict-fallback), validated incremental/fitness unit}. This bundle is frozen and recorded as the Phase 004 reference. No element is tuned against real candidate signals — that is Phase 004's separate, frozen-suite-using work. **Scope of control:** the suite controls **per-candidate** qualification error (FPR/MDE for a single candidate); **programme-level multiplicity across many screened candidates is explicitly outside the suite** and is gated separately by the mandatory Phase 004 multiplicity/registry precondition (§11). |

**⚠ Operator-confirmation items.** D-incr-form (incremental-edge estimator), D-incr-substrate (known-truth construction incl. the redundancy null), and D-incr-legs (leg mapping) are set here as defensible defaults. To preserve the predeclaration freeze, **operator confirmation or override of all three must be recorded before EXP-013 executes** — i.e., before any Track B measurement exists. Any change after EXP-013 begins requires a **new dated design amendment authored before the dependent experiment's results are read**, referencing only predeclared reasoning. D-ratify-point is likewise frozen before EXP-012's fresh draws are generated.

---

## 3. Definitions (additions to Phase 001 §3 / Phase 002 §3)

| Term | Definition |
| --- | --- |
| **Ratification** | **Fresh-seed synthetic confirmation** — on draws whose seeds are disjoint from those used to *select* the operating point — that a *fixed* point delivers the operating characteristics (FPR, MDE, **sub-material rate**) promised by the in-sample characterization. It establishes robustness to **synthetic-draw selection** (the Goodhart risk being addressed), **not** independence across market regimes or fresh real samples — the only real-sample out-of-sample reserve is the global holdout, which stays sealed. Ratification can only confirm or reject; it never re-selects the point. |
| **Adopted operating point** | A per-domain (referee, τ) choice that Phase 003 **freezes for live use** after ratification — distinct from Phase 002's *recommendation* (which committed to nothing). |
| **Incremental-information unit** | A qualification unit that judges a candidate C by the net edge it adds **beyond** a reference signal R, rather than C's standalone edge. Generalizes the L3 naive-control leg from a fixed naive baseline to an arbitrary validated reference. |
| **Portfolio fitness** | The economic reading of a positive incremental verdict: C earns its place alongside R because it adds material net edge the existing book does not already capture. |
| **Redundancy null** | A known-truth case where R and C share structure but C adds no marginal edge. The incremental unit must read it as ≈0 incremental edge; failing this would mean the unit manufactures phantom edge from correlation. The binding Track B control. |
| **Concluded qualification suite** | The frozen end-state instrument: strict referee + ratified-loose referee + validated incremental/fitness unit. The deliverable that ends the framework programme. |

---

## 4. Falsifiable claims

- **H-ratify (EXP-012, Track A spine):** *On each domain, the EXP-011-recommended loose operating point reproduces its Phase 002 operating characteristics on fresh draws — gate FPR ≤ α₀ at D-prec precision and MDE within one edge-grid step of the Phase 002 value.* **Falsified on a domain** if fresh-draw FPR exceeds α₀ or the MDE inflates beyond one grid step → that domain does **not** adopt the loose point and falls back to strict (a clean, recorded decision, not a phase failure). 4h additionally gated by D-ratify-4h.
- **H-incr-substrate (EXP-013, gates Track B):** *The incremental substrate recovers a planted marginal edge within `max(0.5 bps, 15% of m)` AND reads incremental edge ≈ 0 for the redundancy null (shared-structure R,C with no marginal edge).* **Falsified** if it cannot recover the planted marginal edge, or if the redundancy null shows a spurious positive incremental edge → the incremental unit is unsound and Track B halts (recorded; Track A still completes).
- **H-incr-correct (EXP-014):** *The incremental referee reproduces predeclared hand-computed verdicts on deterministic golden fixtures, exposing all legs without short-circuit, with L3 correctly generalized to reference-control.* Correctness gate for EXP-015.
- **H-incr-floor (EXP-015, Track B keystone):** *The incremental referee has a finite portfolio-fitness MDE at FPR ≤ α₀ on each domain — the smallest incremental net edge it reliably detects — and that FPR is controlled under reference/candidate dependence (D-dependence).* **Falsified on a domain** if no finite MDE is attainable at D-prec, or if dependence drives FPR above α₀ (the unit false-positives on redundant candidates).
- **Exploratory (no pass/fail, measurement only):**
  - **EXP-016** — run the assembled suite (strict + ratified-loose + incremental) end to end on **both paths**: (a) the real EXP-009 dogfood set against a reference book — the **negative path**, expected standalone REJECT and no incremental edge (net losers); and (b) a **synthetic positive suite-level fixture** — a planted-edge candidate calibrated to **PASS both referees** and register a **positive incremental edge** against a reference book it is *not* redundant with — the **positive path**. Characterize that the suite composes and wires both the reject and pass paths. The framework-conclusion integration anchor.

---

## 5. Object-level scope

- **Candidate form:** standalone, price-based **directional** signals (position in {−1,0,+1}) for the referees, as in Phase 001/002. The incremental unit adds a **reference signal R**: in calibration (EXP-013/015) R is synthetic/known-truth; in use (Phase 004) R becomes the already-validated book.
- **Instruments / domains:** unchanged (D-invariants); timeframe remains first-class and never pooled across domains.
- **Outcome metric:** direction-adjusted next-step real-price return, evaluated on **real bar prices only** — never HA/Renko construction prices. The incremental edge is computed from real-price return contributions.
- **Excluded candidate sources:** **chart-type signals (Line Break / Renko / Heiken Ashi) remain out of scope as candidates** — signal exploration (including chart-type and other operator-defined families) begins in Phase 004 once the suite is frozen.

---

## 6. Referees / units under test

| Object | Status in Phase 003 | Used by |
| --- | --- | --- |
| Minimal baseline (P1) | Frozen reference | calibration controls |
| 5-check strict gate stack (P1) | Frozen reference — carried into concluded suite unchanged | all EXPs |
| **Loose referee (EXP-011 τ point)** | **Ratified on fresh draws → adopted or strict-fallback per domain** | EXP-012, EXP-016 |
| **Incremental / portfolio-fitness unit** | **New, built, validated, calibrated, frozen** | EXP-013/014/015/016 |

Track A reuses the EXP-003 harness unchanged (D-reuse). Track B builds new machinery, validated before it calibrates anything. No element is tuned against real candidate signals (D-adopt).

---

## 7. Holdout & discipline constraints

- All runs use **only the first 70% analysis set**; the final 30% global holdout is **never loaded or inspected** — including the fresh-draw ratification (D-fresh: "fresh" = new seeds, not new data).
- Within the analysis set, the mandated 70/30 chronological train/test split applies, except where EXP-012's 4h split-sensitivity gate (D-ratify-4h) reuses the corrected EXP-010 walk-forward protocol *within the analysis set*.
- Shared split boundary across domains as `CloseTime` timestamps from the canonical base — never per-timeframe row fractions.
- **Validation precondition P0:** Track A reuses the EXP-001-validated substrate/harness at the same {5,60,240}-minute parameterizations. Track B introduces new incremental machinery — its EXP-013 substrate validation **is** its P0 gate. If any loader/`aggregate_ohlc`/generator/frozen-harness code changes, temporal-integrity + substrate validation must be re-run before dependent experiments.
- Real-price outcome discipline, timestamp alignment over bar count, deterministic generation (fixed/recorded seeds), single-question-per-experiment — all hold.

---

## 8. Planned experiments

Next ID is **EXP-012**. Each answers one question. IDs continue from Phase 002 and are never reused.

| ID | One-line question | Track | Depends on | Budget (tests / plots / modules) |
| --- | --- | --- | --- | --- |
| **EXP-012** (Track A spine) | Does the EXP-011-recommended loose operating point reproduce its Phase 002 FPR/MDE on **fresh** draws, and is it adopted per domain (4h split-gated)? | A | EXP-003, EXP-010, EXP-011 | comparative, ~2–4 / 3–4 / 0–1 |
| **EXP-013** (Track B gate) | Does the incremental substrate recover a planted marginal edge **and** read ≈0 for the redundancy null? **(Track B P0)** | B | EXP-001 | comparative, ~2–3 / 3–4 / 1 |
| **EXP-014** | Does the incremental referee reproduce predeclared golden-fixture verdicts with all legs exposed (L3→reference-control)? | B | EXP-002, EXP-013 | single-hypothesis, ~1–2 / 2–3 / 0–1 |
| **EXP-015** (Track B keystone) | What is the incremental referee's portfolio-fitness MDE at FPR ≤ α₀ per domain, under reference/candidate dependence? | B | EXP-013, EXP-014 | comparative, ~2–4 / 3–5 / 0–1 |
| **EXP-016** (conclusion) | Does the assembled suite (strict + ratified-loose + incremental) compose and wire **both the reject and pass paths** end to end — real dogfood (negative) **and** a synthetic positive fixture? | A+B | EXP-012, EXP-015, EXP-009 | comparative, ~2–4 / 3–5 / 0–1 |
| **Phase 004 seed** | (Design-only) specify the first real signal-exploration protocol using the frozen suite; operator defines candidate model families. | — | — | spec only |

**Sequencing.** Track A (EXP-012) and Track B (EXP-013→014→015) are methodologically independent and may run in parallel. Track B is strictly chained: EXP-013 gates EXP-014 gates EXP-015 (the substrate→logic→calibration chain, mirroring EXP-001→002→003). **EXP-016 runs last**, requiring both the ratified loose referee (EXP-012) and the calibrated incremental unit (EXP-015). If the phase proves too heavy, **EXP-016 is the only droppable item** — but if it is dropped, its **positive-path composition check migrates into EXP-015** (a planted-edge candidate carried through the calibrated incremental unit), so the suite's pass path is never left untested. The EXP-012 ratification and the EXP-013→015 Track B chain are all core.

**Predeclaration freeze (meta-Goodhart guardrail).** The operating point (D-ratify-point), the incremental estimator (D-incr-form), the incremental substrate (D-incr-substrate), and the leg mapping (D-incr-legs) are all predeclared **before** their measurement and measured **once**. Ratification uses fresh draws (D-fresh). No object is iterated against its own measurement within the phase.

---

## 9. Phase-level outcomes & criteria

Phase 003 resolves to exactly **one graded outcome**, which determines whether Phase 004 signal exploration may begin. The distinction matters because the framework is "concluded" only when the full qualification suite — including a *validated* fitness unit — actually exists.

- **FULL_FRAMEWORK_CONCLUDED (the target — the only outcome that unlocks Phase 004):** EXP-013 **validates** the incremental substrate (positive recovery + redundancy-null ≈0), EXP-014 confirms incremental-referee correctness, EXP-015 produces the portfolio-fitness MDE map at controlled FPR across the **D-dependence grid**, **and** EXP-012 delivers a per-domain ratification + adoption decision (adopt or strict-fallback) for the loose referee. D-adopt is then satisfiable and the concluded suite {strict, ratified-loose, validated-incremental} is frozen. *A per-domain strict-fallback on the loose referee is compatible with FULL* — the loose referee is an optional second screen, not a suite prerequisite; FULL requires a **decision** on it, not its adoption. EXP-016 (or its EXP-015-migrated positive-path check) must have exercised both the reject and pass paths.
- **PARTIAL_SUCCESS (framework NOT concluded; Phase 004 blocked by default):** Track A completes (EXP-012 decision recorded) but Track B does **not** reach a validated, calibrated incremental unit — e.g. EXP-013 cleanly falsifies the substrate (H-incr-substrate refuted) or EXP-015 attains no finite portfolio-fitness MDE at D-prec across the dependence grid. The suite ships as **two referees only (no fitness check)**. **Phase 004 may not begin** under PARTIAL unless the operator records an explicit decision to rescope Phase 004 to **standalone-only** qualification; the incremental/fitness unit is carried to a follow-up checkpoint as an open item.
- **BLOCKED / DEFERRED:** a gating precondition fails — substrate/harness re-validation (P0) fails, EXP-014 shows the incremental-referee logic cannot be made correct, or the phase is halted for cause. No suite is frozen; Phase 004 does not begin.

- **Optional/context:** EXP-016 (assembled-suite integration anchor) strengthens FULL but is droppable to a follow-up — *provided* its positive-path fixture is instead exercised within EXP-015's positive composition check (§8 sequencing). Its absence does not by itself downgrade FULL.
- **Inconclusive (per domain/cell):** effective sample too small for D-prec — **expected most likely on 4h**, including the incremental 4h calibration where the joint (R,C) effective N may be smaller than the standalone case. Reported as under-powered, not forced to a verdict; an under-powered 4h cell does not by itself block FULL when 5m/1h conclude.

---

## 10. Explicit non-goals (deferred)

- **Running real candidate model families** (chart-type and other operator-defined signals) — **Phase 004**, using the frozen suite. Phase 003 builds the instrument; it does not hunt for edges with it.
- **Tuning any referee or the incremental unit against real candidate signals** — forbidden; the suite is frozen before Phase 004 use.
- **Multi-signal ensembles / k-of-N reference books beyond a single reference R for the incremental calibration** — the calibration uses a single known-truth reference; portfolio-of-many fitness is a Phase 004+ extension.
- **Non-stationary / drifting planted edges; tunable context-dependent loss beyond the EXP-011 form; programme-level multiplicity / file-drawer registry.** (Carried from P1-§12 / P2-§10.)

---

## 11. Phase 004 seed (design-only): first signal-exploration phase

Recorded now so Phase 004 starts from a specified seed. **Not executed in Phase 003.**

- **Idea:** with the qualification suite frozen, begin **real signal exploration** — the operator defines candidate model families (e.g. tuned/ensemble standalone strategies; chart-type-derived signals via the VAL-001 data layer; incremental-information candidates), runs each through the two referees for standalone qualification, and evaluates portfolio fitness against the growing validated book via the incremental unit.
- **Why next:** on Phase 003's **FULL_FRAMEWORK_CONCLUDED** outcome (§9) the framework is frozen and Phase 004 is the first phase whose object is a *market edge*, not the referee. EXP-009 establishes that the first real near-MDE candidate is unlikely to come from naive standalone signals, so Phase 004 should prioritize tuned/ensemble/incremental candidate sources.
- **Mandatory precondition (predeclared now):** before *any* Phase 004 candidate run, a **multiplicity / file-drawer registry plan** must be recorded — every screened candidate family, instrument, domain, and variant logged, with a predeclared programme-level false-discovery control (e.g. a registered candidate count and an error-rate budget across screens). The concluded suite controls **per-candidate** error only (D-adopt); programme-level false discoveries are this plan's responsibility. **Phase 004 may not begin candidate screening until this plan exists.**
- **Open design questions for Phase 004:** the candidate-family slate and predeclaration discipline for live exploration; how the validated book R is seeded and grown without leakage; the exact form of the multiplicity control above; promotion criteria from "passes the suite" to "traded."

---

## 12. Summary

Phase 002 left the strict referee validated and usable but the loose operating point only *recommended*, and the incremental-information unit only *seeded*. Phase 003 closes both: it **ratifies** the loose point on fresh seeds (adopting it per domain or falling back to strict, 4h split-gated), **builds and validates** the incremental / portfolio-fitness unit through a substrate→logic→calibration chain (EXP-013→014→015) with a redundancy null as the binding control, and **assembles and freezes** the concluded **"two referees + fitness check"** suite (EXP-016 integration anchor). On the **FULL_FRAMEWORK_CONCLUDED** outcome (§9) the framework programme is concluded and Phase 004 — the first real signal-exploration phase — may begin, using the frozen suite (and its mandatory multiplicity registry, §11) to judge candidate models; lesser outcomes carry the unfinished element to a follow-up. We will have a finalized, **fresh-seed-confirmed** qualification instrument — *before* we point it at any real market edge.
