# Phase 003b — Incremental-Unit Redesign & Recalibration (Track B follow-up)

**Phase number:** 003b (revision of Phase 003 Track B — **not** a new programme phase; Phase 004 remains reserved for signal exploration)
**Design finalised:** 2026-06-05
**Status:** ACTIVE (design complete; **D-revised-legs + D-l4l5-freeze confirmed by operator 2026-06-05** → EXP-017 ready to execute; **D-dogfood-book confirmed by operator 2026-06-05 as `donchian_20`** before EXP-019)

**Amendments:** [2026-06-05-B1](amendments/2026-06-05-B1-pre-execution-review-corrections.md) — pre-execution adversarial-review corrections (binding-leg semantics reconciliation, explicit binding-corner reporting, EXP-018/019 verdict-rollup + clean-block robustness, fixture-nature wording, standalone-bootstrap efficiency). **No predeclared decision, gate leg, threshold, edge grid, or dependence grid is changed**, so the meta-Goodhart freeze (D-no-retune) is preserved.

**Provenance:**
- Parent phase: Phase 003 `2026-06-04-003-ratification-and-incremental-unit` — [design.md](../2026-06-04-003-ratification-and-incremental-unit/design.md), [retrospective.md](../2026-06-04-003-ratification-and-incremental-unit/retrospective.md), amendment [A1](../2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md).
- Phase 003 closed **PARTIAL_SUCCESS**: Track A ratified and **adopted** the loose referee (EXP-012); Track B validated the incremental substrate (EXP-013) and logic (EXP-014) but the keystone calibration **REFUTED** (EXP-015 — no finite portfolio-fitness MDE in any domain), so the framework is not FULL_FRAMEWORK_CONCLUDED.
- **Operator decision (Phase 003 retrospective §11, 2026-06-05): Path B** — open this follow-up to fix and freeze the incremental unit *before* Phase 004, rather than rescoping Phase 004 to standalone-only.

This phase references Phase 001 decisions as *P1-§n / P1-D-x*, Phase 002 as *P2-§n / P2-D-x*, Phase 003 as *P3-§n / P3-D-x*, and amendment A1 findings as *A1/Fnn*. It **inherits every Phase 003 invariant unchanged** except where §2 explicitly revises the incremental unit.

---

## 1. Phase objective

**Repair the one element that blocked the framework conclusion** — the incremental / portfolio-fitness unit — and reach the validated, calibrated, freezable state that unlocks Phase 004. Phase 003 isolated the failure precisely (A1/F03): the keystone REFUTED because the **L2 standalone-significance leg** is binding in the failing cells and **BTCUSD** cannot clear standalone significance even at the 32 bps edge ceiling, holding pooled TPR below the 0.80 floor. The substrate (EXP-013) and logic-wiring machinery (EXP-014) are sound and reusable. Three concrete deliverables:

1. **Redesign the incremental gate to test portfolio fitness, not standalone edge (the fix).** Remove the L2 standalone-significance requirement that A1/F03 identified as the binding cause, leaving L3 (incremental-beyond-R) as the operative portfolio-fitness leg — the unit's actual purpose. (Binding-leg nuance, B1/F01: under the D-l4l5-freeze strict-L5 form, `L5 (ci_lower > materiality)` implies `L3 (ci_lower > 0)` on the same marginal series, so **L5 is the operationally binding significance-at-materiality test and L3 is its directional precondition** — the conjunction is effectively L1∧L4′∧L5. This matches the nesting recorded in D-l4l5-freeze; EXP-018's `leg_pass_rates.csv` and `binding_corner_summary.csv` report the actual binding leg so a second refutation is attributable.) Resolve the A1/F02 freeze precondition on the reduced-conservatism L4/L5 legs (accept with recorded rationale, or override to strict CI-based forms). The revised gate is **predeclared once** here and measured once (meta-Goodhart freeze preserved — it is **not** tuned against EXP-015's numbers).
2. **Re-validate logic, then recalibrate (the chain).** Re-run the logic→calibration links on the revised unit: golden-fixture correctness for the redesigned legs (EXP-017), then the portfolio-fitness MDE map at controlled FPR across the **unchanged** P3-D-dependence grid (EXP-018). The EXP-013 substrate + D-incr-form estimator are reused unchanged as the P0 gate.
3. **Compose and freeze (conditional).** If EXP-018 validates, run the assembled-suite composition anchor that EXP-016 could not (EXP-019) — both reject and pass paths — with the previously-missing dogfood reference book now predeclared. On success the concluded "two referees + fitness check" suite is frozen and **Phase 004 unlocks**.

**What is *not* reopened.** The frozen Phase 001 strict gate stack and the **ratified-loose referee adopted in EXP-012** are the confirmed standalone screen; they are carried forward unchanged and are not re-measured here. The D-incr-form marginal-net-P&L estimator is unchanged. Only the incremental gate's **leg composition** changes.

**Posture.** This is a **targeted repair + freeze** follow-up. Success freezes the incremental unit and unlocks Phase 004; a second refutation does not (it carries the unit to a further follow-up or forces the standalone-only rescope the operator declined in P3-§11).

---

## 2. Predeclared decisions (frozen before any measurement is read)

Frozen for the phase. Changing any after its dependent experiment begins requires a new dated design amendment authored before that experiment's results are read (meta-Goodhart guardrail), as in Phase 003.

| # | Decision | Resolution |
| --- | --- | --- |
| D-revision | Phase identity | **Revision of Phase 003 Track B, not a new phase.** Experiment IDs continue EXP-017+ (never reused). Phase 004 stays reserved for the first real signal-exploration phase (P3-§11). Success here = the FULL-equivalent for the incremental unit, which completes the P3 framework conclusion retroactively and unlocks Phase 004. |
| D-reuse-up | Reused frozen objects | The Phase 001 **minimal baseline** + **5-check strict gate stack** and the **EXP-012 ratified-loose referee** are carried forward **frozen and unchanged**. The **EXP-013 incremental substrate** and the **D-incr-form marginal-net-P&L estimator** (model-free; additive-clipped combination; cost on incremental turnover; A1/F04 contiguous block length) are reused **unchanged** and serve as the Track B **P0 gate**. Only `incremental_referee.py`'s **leg-composition** is revised. |
| D-revised-legs ✔ | Revised incremental gate | **CONFIRMED by operator 2026-06-05 (⚠→✔): remove L2.** The gate becomes **L1 ∧ L3 ∧ L4′ ∧ L5** on the incremental claim. **L1** readiness on the incremental position (unchanged from P3-D-incr-legs). **L3** incremental-beyond-R `ci_lower_bps > 0` on the marginal series — the **binding** portfolio-fitness test. **L4′** no material sign reversal of the *incremental* edge across train/OOS (A1/F02 reduced form). **L5** incremental materiality (form set by D-l4l5-freeze). **L2 (standalone C significance) is removed** because A1/F03 attributes the EXP-015 refutation to it and A1/F02 already records that L3 is the binding incremental test — a portfolio-fitness unit should not reject a genuine diversifier (or a high-cost-instrument candidate like BTCUSD) merely because C is not independently significant *standalone*. **Alternative considered:** *re-point* L2 to a property of the incremental position rather than removing it — rejected because that makes L2 and L3 test the same series (redundant), whereas removal yields a strictly portfolio-fitness gate. The EXP-017 scope must state this comparison. |
| D-l4l5-freeze ✔ | F02 freeze precondition | The A1/F02 reduced-conservatism residual risk **must be resolved before EXP-017** (it was moot only while the unit was REFUTED). **CONFIRMED by operator 2026-06-05 (⚠→✔):** **accept L4′** (no material sign reversal — first-principles justified: a redundant candidate's ≈0 cost-drag must not be forced to fail a "both segments positive" test), and **set L5 to the strict `ci_lower_bps > materiality` form** (resolving A1/F02's specific concern that a point-estimate L5 with CI-lower below materiality is too weak for freeze). Under this default **L3 ⊆ L5** on the marginal series (L5-strict implies L3), so L3 functions as the directional/readiness precondition and L5 is the binding significance-at-materiality test — an intentional, documented nesting analogous to the Phase 001 L3/L5 relationship (P2-EXP-007). The operator may instead keep the point-estimate L5 (weaker) or override L4′ to strict "both positive"; whichever is chosen is frozen here and verified on fixtures in EXP-017. |
| D-no-retune | Meta-Goodhart freeze | The revised gate (D-revised-legs + D-l4l5-freeze) is predeclared **before** EXP-017/018 run and measured **once**. It is **not** iterated against EXP-018's own MDE/FPR output, and **not** tuned to make BTCUSD pass. If EXP-018 refutes again, that is a recorded finding, not a trigger to re-edit the legs within this phase. |
| D-invariants | Carried-forward invariants | **Unchanged from P3-D-invariants:** domains 5m/1h/4h; instruments EURUSD/XAUUSD/BTCUSD/USTEC; per-domain costs & materiality (P1-D-cost); coverage (5m strict, 1h/4h 0.90); precision target (95% Wilson half-width ≤0.03 FPR / ≤0.05 TPR); block bootstrap with A1/F04 contiguous block length; α grid {0.10, 0.05, 0.01}, primary α₀=0.05. Retained so results compose with the Phase 001/002/003 map. |
| D-dependence | Dependence grid | **Reused unchanged from P3-D-dependence.** EXP-018 measures across the same grid: shared-latent-state ρ ∈ {independent, moderate≈0.4, high≈0.8}; active-overlap ∈ {low, medium, high}; lead/lag ∈ {synchronous, C lags R 1 bar, C leads R 1 bar}; reference strength ∈ {null R, R at domain MDE}. Redundancy-null FPR must hold ≤ α₀ at D-prec in every powered grid cell; the synchronous-high-overlap-null_R corner (where EXP-015 failed) is the binding stress and must be reported explicitly. (Corner axis, B1/F03: A1/F03 attributes the EXP-015 refutation to the moderate/high shared-latent-state ρ cells specifically, so EXP-018 reports this corner across all three ρ levels in a dedicated `binding_corner_summary.csv` and flags the moderate/high-ρ cells as the EXP-015 stress.) Block bootstrap / embargo on the joint (R,C) series. |
| D-dogfood-book ✔ | Dogfood reference book (EXP-019) | The EXP-016 blocker was a missing `dogfood_reference_book.csv`. **CONFIRMED by operator 2026-06-05:** R = EXP-009 Donchian(20) breakout (`donchian_20`) as the standing "book"; the candidates C are the remaining EXP-009 families (`ma_20_50`, `rsi_14`, `bollinger_20_2`, `macd_12_26_9`, `roc_20`) on the same instruments/domains. Expected negative-path outcome: no material incremental edge (all net losers, REJECT), since EXP-009 established the whole family sits below every MDE. The book and candidate slate are fixed here, not chosen after seeing incremental results. |
| D-adopt-revised | What success freezes | On EXP-018 validation (+ EXP-019 composition), the **concluded suite = {frozen strict gate stack, ratified-loose referee (EXP-012), validated revised incremental/fitness unit}** is frozen and recorded as the Phase 004 reference. Per-candidate qualification error only; programme-level multiplicity remains the mandatory Phase 004 precondition (P3-§11). |

**Operator-confirmation items.** **D-revised-legs** (remove L2; gate = L1∧L3∧L4′∧L5) and **D-l4l5-freeze** (accept L4′ + strict `ci_lower>materiality` L5) were **confirmed by the operator on 2026-06-05** and are now **frozen for the phase — EXP-017 may execute.** **D-dogfood-book** (EXP-019 reference book) was **confirmed by the operator on 2026-06-05** as `donchian_20` and is now frozen before EXP-019. Any change to a frozen decision after its dependent experiment begins requires a new dated amendment authored before that experiment's results are read.

---

## 3. Definitions (additions to Phase 001/002/003 §3)

| Term | Definition |
| --- | --- |
| **Revised incremental unit** | The Phase 003 incremental gate with the L2 standalone-significance leg removed and the L4′/L5 freeze precondition resolved (D-revised-legs, D-l4l5-freeze). Same D-incr-form estimator and same EXP-013 substrate; only the leg composition differs. |
| **Incremental-beyond-R test (L3)** | `ci_lower_bps > 0` on the marginal-net-P&L series of adding C to a book holding R — the direct portfolio-fitness question. Removing L2 makes the incremental claim the gate's purpose; under the strict-L5 freeze L3 is the **directional precondition** that nests within the binding **L5** materiality test `ci_lower_bps > materiality` (B1/F01). |
| **FULL-equivalent outcome** | The §9 success state for this follow-up: revised-unit logic correct (EXP-017) + finite portfolio-fitness MDE at controlled FPR across the dependence grid (EXP-018). Reaching it satisfies the Phase 003 D-adopt requirement and unlocks Phase 004. |

---

## 4. Falsifiable claims

- **H-revised-correct (EXP-017, logic gate):** *The revised incremental referee (L1∧L3∧L4′∧L5, L2 removed) reproduces predeclared, hand-reasoned verdicts on seeded-deterministic fixtures (B1/F04), exposing all retained legs without short-circuit, with L2 absent, L3 exposed as the incremental-beyond-R directional precondition, and L5 (strict materiality) the operationally binding leg (B1/F01).* Correctness gate for EXP-018. The EXP-014 fixture construction is reused/adapted and extended (B1/F05): fixtures that previously isolated L2 must now confirm L2 is gone (verified by a run-time legacy-L2 check), and the `l3_reference_control_fail` fixture must still reject.
- **H-revised-floor (EXP-018, keystone — re-posed on the revised unit):** *The revised incremental referee has a finite portfolio-fitness MDE at FPR ≤ α₀ on each domain across the P3-D-dependence grid, and FPR stays controlled at the synchronous-high-overlap-null_R corner where EXP-015 failed.* **Falsified on a domain** if no finite MDE is attainable at D-prec across the grid, or if dependence drives redundancy-null FPR above α₀. A second refutation here means the unit is not freezable on this redesign.
- **Exploratory (no pass/fail, conditional on EXP-018 validating):**
  - **EXP-019** — run the assembled suite (frozen strict + ratified-loose + revised incremental) end-to-end on both paths: (a) the EXP-009 dogfood set against the D-dogfood-book reference R — the **negative path** (expected standalone REJECT and no incremental edge); and (b) a **synthetic positive suite-level fixture** — a planted-edge candidate that passes both referees and registers a positive incremental edge against a book it is not redundant with — the **positive path**. The framework-conclusion integration anchor that EXP-016 was blocked from running.

---

## 5. Object-level scope

Unchanged from Phase 003 §5: standalone price-based **directional** signals (position in {−1,0,+1}) for the referees; the incremental unit adds a reference signal R (synthetic/known-truth in EXP-017/018; the EXP-009-derived book in EXP-019). Outcome metric is direction-adjusted next-step **real-price** return — never HA/Renko construction prices. **Chart-type and other operator-defined candidate families remain out of scope** — they begin in Phase 004 once the suite is frozen.

---

## 6. Units under test

| Object | Status in 003b | Used by |
| --- | --- | --- |
| Minimal baseline (P1) | Frozen reference | calibration controls |
| 5-check strict gate stack (P1) | Frozen reference — carried into concluded suite unchanged | EXP-019 |
| Ratified-loose referee (EXP-012 τ point) | Frozen — adopted in Phase 003, not reopened | EXP-019 |
| EXP-013 incremental substrate + D-incr-form estimator | Reused unchanged — Track B P0 gate | EXP-017/018 |
| **Revised incremental / portfolio-fitness unit** | **Redesigned (L2 removed), re-validated, recalibrated, frozen** | EXP-017/018/019 |

---

## 7. Holdout & discipline constraints

- All runs use **only the first 70% analysis set**; the final 30% global holdout is **never loaded or inspected**.
- Within the analysis set, the mandated 70/30 chronological train/test split applies; the joint (R,C) series carries the block bootstrap (A1/F04 contiguous block length) and any embargo.
- **P0 gate:** the EXP-013 substrate + D-incr-form estimator are the reused P0. The L2-removal patch modifies only `incremental_referee.py`'s **leg-composition** function; if it touches any shared estimator/CI code path (`marginal_net_series`, `incremental_edge_ci`, `_contiguous_block_length`), **EXP-013 must be re-run** before EXP-017/018 (D-reuse). If it modifies only leg composition, EXP-013 stands and is cited as the P0 dependency token.
- Real-price outcome discipline, timestamp alignment over bar count, deterministic generation (fixed/recorded seeds), single-question-per-experiment — all hold.

---

## 8. Planned experiments

Next ID is **EXP-017**. Each answers one question. IDs continue from Phase 003 (last was EXP-016) and are never reused.

| ID | One-line question | Track | Depends on | Budget (tests / plots / modules) |
| --- | --- | --- | --- | --- |
| **EXP-017** (logic gate) | Does the revised incremental referee (L2 removed; L3 binding; L4′/L5 frozen) reproduce predeclared golden-fixture verdicts with all retained legs exposed? | B | EXP-013, EXP-014 | single-hypothesis, ~1–2 / 2–3 / 0–1 |
| **EXP-018** (keystone) | Does the revised unit attain a finite portfolio-fitness MDE at FPR ≤ α₀ per domain across the P3-D-dependence grid (incl. the synchronous-high-overlap-null_R corner)? | B | EXP-013, EXP-017, EXP-003 | comparative, ~2–4 / 3–5 / 0–1 |
| **EXP-019** (conclusion, conditional) | Does the assembled suite (strict + ratified-loose + revised incremental) compose and wire **both reject and pass paths** end to end — EXP-009 dogfood (negative) **and** a synthetic positive fixture? | A+B | EXP-012, EXP-018, EXP-009 | comparative, ~2–4 / 3–5 / 0–1 |

**Sequencing.** Strictly chained: EXP-017 gates EXP-018 gates EXP-019 (logic→calibration→composition). **EXP-019 is the only droppable item**; if dropped, its positive-path composition check migrates into EXP-018 (a planted-edge candidate carried through the recalibrated unit), so the suite's pass path is never left untested — the same fallback Phase 003 §8 specified for EXP-016, now executable because the unit is no longer REFUTED.

**Predeclaration freeze.** D-revised-legs, D-l4l5-freeze, and D-dogfood-book are predeclared **before** their dependent measurement and measured **once**. No object is iterated against its own measurement within the phase (D-no-retune).

---

## 9. Phase-level outcomes & criteria

This follow-up resolves to one graded outcome, determining whether the Phase 003 framework conclusion is completed and Phase 004 unlocks.

- **REVISED_UNIT_VALIDATED (the target — completes the Phase 003 conclusion, unlocks Phase 004):** EXP-017 confirms the revised-referee correctness, **EXP-018 produces a finite portfolio-fitness MDE map at controlled FPR across the D-dependence grid** (the claim EXP-015 refuted, now holding on the redesigned unit), and EXP-019 (or its EXP-018-migrated positive-path check) exercises both reject and pass paths. (Operationalization, B1/F02: EXP-018 reports `overall_status = COMPLETE` only when **every** in-scope domain concludes SUPPORTED with a finite worst-case MDE; a domain left INCONCLUSIVE — no finite MDE anywhere, binding cells did not conclude — yields overall INCONCLUSIVE and requires an operator ruling before EXP-019, which BLOCKs cleanly rather than crashing on a non-finite domain MDE.) The concluded suite {strict, ratified-loose, validated-revised-incremental} is frozen; D-adopt (P3) is satisfied; **Phase 004 may begin** under its mandatory multiplicity-registry precondition (P3-§11).
- **REFUTED_AGAIN (unit still not freezable; Phase 004 stays blocked):** EXP-018 again attains no finite MDE at D-prec across the grid (e.g. the L2 removal exposes a different binding leg, or L3/L5 cannot clear power at the dependence corner). Recorded as a clean second falsification. The unit carries to a further follow-up **or** the operator now records the standalone-only Phase 004 rescope declined in P3-§11. The two-referee screen still ships.
- **BLOCKED / DEFERRED:** the P0 re-validation (EXP-013, if triggered) fails, EXP-017 shows the revised logic cannot be made correct, or the phase is halted for cause. No suite is frozen.

- **Inconclusive (per domain/cell):** effective sample too small for D-prec — most likely on 4h and at the joint (R,C) dependence corners. Reported as under-powered, not forced to a verdict; an under-powered cell does not by itself block REVISED_UNIT_VALIDATED when the binding cells conclude.

---

## 10. Explicit non-goals (deferred)

- **Running real candidate model families** (chart-type and other operator-defined signals) — **Phase 004**, using the frozen suite.
- **Tuning the revised unit against EXP-015/018 output or against BTCUSD** (D-no-retune) — forbidden; the redesign is predeclared and measured once.
- **Re-opening the strict gate or the ratified-loose referee** — both are frozen; this phase touches only the incremental unit's legs.
- **Multi-signal / k-of-N reference books; non-stationary planted edges; programme-level multiplicity registry** — carried forward (P1-§12 / P2-§10 / P3-§10); the multiplicity registry remains the hard Phase 004 precondition.

---

## 11. Relationship to Phase 004

Phase 004 is unchanged in identity (P3-§11): the first **real signal-exploration** phase, in which the operator defines candidate model families (tuned/ensemble standalone strategies; chart-type-derived signals via the VAL-001 layer; incremental candidates) and screens them through the frozen suite. 003b does **not** begin signal exploration; it only finishes the instrument. On REVISED_UNIT_VALIDATED the framework programme is concluded and Phase 004 opens (subject to its multiplicity-registry precondition); on REFUTED_AGAIN Phase 004 stays blocked pending the operator's standalone-only rescope or a further unit follow-up.

---

## 12. Summary

Phase 003 left the framework one element short of concluded: the incremental / portfolio-fitness unit had a sound substrate (EXP-013) and correct logic wiring (EXP-014) but a refuted calibration (EXP-015), attributed by adversarial review (A1/F03) to the L2 standalone-significance leg defeating BTCUSD at the dependence corner. The operator chose (P3-§11, Path B) to fix the unit before signal exploration. Phase 003b **removes L2** so the gate tests portfolio fitness (L3-binding) rather than standalone edge, **resolves the A1/F02 L4/L5 freeze precondition**, and re-runs the logic→calibration chain (EXP-017→018, EXP-013 substrate reused as P0) across the unchanged dependence grid — once, predeclared, un-retuned. On the **REVISED_UNIT_VALIDATED** outcome the concluded "two referees + fitness check" suite is frozen, the Phase 003 framework conclusion is completed, and Phase 004 — the first real signal-exploration phase — finally opens. The strict and ratified-loose referees are already frozen and are carried through untouched.
