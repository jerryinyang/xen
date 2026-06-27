# Phase 003b — Incremental-Unit Redesign & Recalibration (Track B follow-up) — Retrospective

**Phase number:** 003b (revision of Phase 003 Track B — **not** a new programme phase)
**Design finalised:** 2026-06-05
**Retrospective written:** 2026-06-05
**Status:** COMPLETED — all three planned experiments (EXP-017, EXP-018, EXP-019) executed and governance-reviewed (pre- and post-execution **APPROVE** on each); pre-execution adversarial review issued amendment [B1](amendments/2026-06-05-B1-pre-execution-review-corrections.md) before any results existed. **Phase outcome: REVISED_UNIT_VALIDATED** (§9) — the incremental / portfolio-fitness unit is validated, calibrated, and frozen. This **retroactively completes the Phase 003 framework conclusion** and **unlocks Phase 004**, subject to its mandatory programme-level multiplicity-registry precondition (P3-§11).

**Design reference:** [design.md](design.md)
**Amendment:** [B1 — Pre-Execution Review Corrections](amendments/2026-06-05-B1-pre-execution-review-corrections.md)
**Parent phase:** Phase 003 [design.md](../2026-06-04-003-ratification-and-incremental-unit/design.md) · [retrospective.md](../2026-06-04-003-ratification-and-incremental-unit/retrospective.md) · amendment [A1](../2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md)
**Experiments:** EXP-017 (revised logic gate), EXP-018 (revised keystone), EXP-019 (assembled-suite composition anchor) — see `python/experiments/<ID>/report.md`.

---

## 1. Phase objective recap

Phase 003 closed **PARTIAL_SUCCESS**. Track A ratified and **adopted** the EXP-012 loose referee, but Track B's keystone calibration **REFUTED** (EXP-015): the incremental / portfolio-fitness unit attained **no finite MDE in any domain** at the synchronous / high-overlap / `null_R` dependence corner. Adversarial review (A1/F03) attributed the refutation precisely — the **L2 standalone-significance leg**, with **BTCUSD** unable to clear standalone significance even at the 32 bps edge ceiling, holding pooled TPR below the 0.80 floor. The substrate (EXP-013) and logic-wiring machinery (EXP-014) were sound. The operator chose **Path B** (P3-§11): fix and freeze the unit *before* Phase 004 rather than rescoping Phase 004 to standalone-only.

Phase 003b's job was to **repair the one element that blocked the framework conclusion** and reach the freezable state. Three deliverables ([design §1](design.md)):

1. **Redesign the incremental gate to test portfolio fitness, not standalone edge (the fix).** Remove the L2 standalone-significance requirement A1/F03 identified as the binding cause, leaving the gate as **L1 ∧ L3 ∧ L4′ ∧ L5** on the incremental claim, and resolve the A1/F02 freeze precondition on the reduced-conservatism L4/L5 legs. Predeclared **once** and measured **once** (meta-Goodhart freeze — never tuned against EXP-015's numbers or to make BTCUSD pass).
2. **Re-validate logic, then recalibrate (the chain).** Golden-fixture correctness for the redesigned legs (EXP-017), then the portfolio-fitness MDE map at controlled FPR across the **unchanged** P3-D-dependence grid (EXP-018). EXP-013 substrate + D-incr-form estimator reused unchanged as the P0 gate.
3. **Compose and freeze (conditional).** Run the assembled-suite composition anchor that EXP-016 was blocked from (EXP-019) — both reject and pass paths — with the previously-missing dogfood reference book now predeclared (`donchian_20`).

The binding constraint (D-no-retune): the revised gate was frozen in design before any measurement, and success here is the **FULL-equivalent outcome** that completes the Phase 003 conclusion and unlocks Phase 004.

---

## 2. Outcomes vs objectives

| EXP | Role | Track | Verdict | One-line outcome |
| --- | --- | --- | --- | --- |
| 017 | **Revised incremental logic gate** | B | **SUPPORTED** | 7/7 fixture verdicts, 28/28 retained-leg states, L2 absent from every revised-gate output; the former standalone-L2 failure fixture now passes as intended. |
| 018 | **Revised portfolio-fitness calibration (keystone — re-posed)** | B | **SUPPORTED** | 126/126 construction-accepted cells PASS; finite worst-case MDEs 12/16/32 bps on 5m/1h/4h; FPR 0.0–0.004; the EXP-015 stress corner passes in every domain. The claim EXP-015 refuted now holds. |
| 019 | **Assembled-suite composition anchor** | A+B | **SUPPORTED** | Dogfood rejects across all domains (0 strict / loose / incremental passes); synthetic positive passes all three components in every domain. The frozen suite composes end to end. |

**Every planned experiment reached its scoped verdict, all in the SUPPORTED direction.** The chain held at all three links: logic → calibration → composition. This is the **clean inverse of Phase 003 Track B**, where logic passed but calibration refuted and composition was correctly blocked.

---

## 3. The fix that worked — removing the L2 standalone-significance leg (headline)

**Removing exactly the leg A1/F03 diagnosed as the binding cause flipped the keystone from REFUTED (EXP-015) to SUPPORTED (EXP-018), with no other predeclared change.** This is the strongest possible confirmation that the Phase 003 adversarial attribution was correct: the L2 standalone-significance requirement, not the substrate, the logic wiring, or the estimator, was what defeated BTCUSD at the dependence corner.

The redesign was a single, predeclared leg-composition change (D-revised-legs):

- **Before (Phase 003):** the incremental gate was `L1 ∧ L2 ∧ L3 ∧ L4 ∧ L5`, where **L2** required the candidate C to be independently significant *standalone*.
- **After (Phase 003b):** the gate is **`L1 ∧ L3 ∧ L4′ ∧ L5`** on the incremental claim. L2 is removed because a *portfolio-fitness* unit should not reject a genuine diversifier (or a high-cost, low-power instrument like BTCUSD) merely because C is not independently significant. The operator considered *re-pointing* L2 to a property of the incremental position instead of removing it, and rejected it because that makes L2 and L3 test the same series — removal yields a strictly portfolio-fitness gate (D-revised-legs, recorded in EXP-017 scope).

The A1/F02 freeze precondition was resolved at the same time (D-l4l5-freeze): **accept L4′** (no material sign reversal — first-principles justified so a redundant candidate's ≈0 cost-drag is not forced to fail a "both segments positive" test) and **set L5 to the strict `ci_lower_bps > materiality` form**. Under this default, on the marginal series **L3 (`ci_lower > 0`) ⊆ L5 (`ci_lower > materiality`)**, so L5 is the operationally binding significance-at-materiality test and L3 is its directional precondition — an intentional, documented nesting analogous to the Phase 001 L3/L5 relationship (B1/F01 reconciled the design language to name this correctly).

**The trade is explicit and recorded, not hidden.** Removing L2 buys the correct portfolio-fitness semantics but at a coarser detection floor: the revised worst-case MDEs (12/16/32 bps) are materially higher than the strict standalone map (1/4/12) and the ratified-loose map (0.5/2/8). The incremental screen is the coarsest of the three — it detects a *marginal* edge beyond an existing book only at or above these dependence-grid worst-case levels (§7). This is the cost of asking the right question; it is disclosed in the suite manifest, not absorbed silently.

---

## 4. The validation chain — logic, calibration, composition

### EXP-017 — revised logic gate (H-revised-correct SUPPORTED)

The revised referee reproduced **7/7** seeded-deterministic fixture verdicts (`mismatch_details.csv` empty) and **28/28** retained-leg states (L1, L3, L4′, L5 for every fixture, all `exposed = true`, no short-circuit). The L2-absence check passed **7/7**: no emitted gate leg begins with `L2`, and the revised output carries only `L1_readiness`, `L3_reference_control`, `L4_no_material_sign_reversal`, `L5_strict_materiality`. The decisive fixture is `l2_absent_former_standalone_fail`: it has `legacy_l2_pass_diagnostic = false` (its standalone leg, `legacy_l2_ci_lower_bps ≈ −3.39`, *would* have failed the old gate) yet the revised verdict is **PASS** — confirming EXP-017 does not merely drop an unused column but verifies that a case previously blocked by standalone L2 is now accepted when the incremental evidence clears the retained legs. The `l3_reference_control_fail` fixture is retained and still rejects, preserving the incremental-beyond-R requirement. Per B1/F04–F05, these are **seeded-deterministic fixtures with hand-reasoned expected leg states verified against a fixed-seed 1000-resample block bootstrap** (reproducible, not closed-form), built by reusing/adapting/extending the EXP-014 fixture construction.

### EXP-018 — revised portfolio-fitness calibration (H-revised-floor SUPPORTED, the re-posed keystone)

The claim EXP-015 refuted — *a finite portfolio-fitness MDE at FPR ≤ α₀ on each domain across the dependence grid* — now **holds**:

| Domain | Worst-case domain MDE (bps) | Finite-MDE cells | Failing cells | Construction-invalid cells | Domain status |
| --- | ---: | ---: | ---: | ---: | --- |
| 5m | 12.0 | 42 | 0 | 12 | SUPPORTED_WITH_UNDERPOWERED_CELLS |
| 1h | 16.0 | 42 | 0 | 12 | SUPPORTED_WITH_UNDERPOWERED_CELLS |
| 4h | 32.0 | 42 | 0 | 12 | SUPPORTED_WITH_UNDERPOWERED_CELLS |

- **126/126 construction-accepted cells PASS** (`cell_mde_summary.csv`); no FPR failure and no no-finite-MDE failure anywhere.
- **Redundancy-null FPR is controlled** in every accepted cell: range 0.0–0.004, well below α₀ = 0.05, max Wilson half-width 0.0067 (below the 0.03 D-prec target). Shared R–C structure does not manufacture false incremental passes.
- **The EXP-015 failure corner now passes.** `binding_corner_summary.csv` reports PASS FPR and PASS cell MDE for the synchronous / high-overlap / `null_R` corner across **all three ρ levels** in **all three domains** (9/9 rows). The A1/F03 moderate/high-ρ stress cells — the specific shared-latent-state cells the EXP-015 refutation was attributed to — have finite MDEs of **1.0 bps (5m), 8.0 bps (1h), 24.0 bps (4h)**.
- **36 cells are disclosed as `CONSTRUCTION_INVALID`** (12 per domain), all with reason `target_rho_infeasible_for_overlap` — infeasible combinations of high ρ with low overlap, *not* failed inference cells. They are excluded from the support claim rather than forced into a verdict (180,000 invalid construction rows vs 630,000 accepted).

Under B1/F02's tightened rollup, `overall_status = COMPLETE` requires **every** in-scope domain to conclude SUPPORTED with a finite worst-case MDE — all three did.

### EXP-019 — assembled-suite composition anchor (integration claim SUPPORTED)

The exploratory anchor that EXP-016 was blocked from running. Both paths wire end to end (`suite_composition_summary.csv`):

- **Negative path (real dogfood).** Using the confirmed `donchian_20` reference book R and the remaining five EXP-009 candidate families C, the suite rejects in every domain: **0 strict passes, 0 loose/fallback passes, 0 incremental passes** on 5m/1h/4h, each marked `REJECT_PATH_EXERCISED`. Consistent with EXP-009's lower-anchor result (the whole simple-strategy family sits below every MDE).
- **Positive path (synthetic fixture).** A nonredundant planted-edge candidate passes **every** component — **1 strict, 1 loose/fallback, 1 incremental pass** in each domain, each marked `PASS_PATH_EXERCISED`. The positive fixture is nonredundant (active-overlap fraction 0.0, signed R–C ρ ≈ 0; `positive_fixture_manifest.csv`), so the pass is not a redundant-reference artifact.
- **Frozen upstream decisions flow through.** `suite_manifest.csv` carries strict MDEs 1/4/12 bps, EXP-012 ratified-loose effective MDEs 0.5/2/8 bps (`ADOPT_LOOSE`, τ 0.375/0.375/1.5 bps), and EXP-018 revised-incremental MDEs 12/16/32 bps for 5m/1h/4h.

One artifact-hygiene note: a stale `results/blocker_report.csv` from an earlier blocked state remains in EXP-019's results directory; `run_metadata.json` (`overall_status = COMPLETE`) and `dependency_manifest.csv` (book FOUND) supersede it. It is hygiene debt, not a measurement blocker.

---

## 5. The B1 pre-execution review — what the governance layer caught (before any result existed)

As in Phase 003 (A1) and Phase 002 (EXP-010's CI-scaling artifact), the adversarial layer ran **before** the conclusion was reachable. Amendment [B1](amendments/2026-06-05-B1-pre-execution-review-corrections.md) was authored while every `results/` directory was still empty, so the predeclaration freeze was preserved by documenting the changes before any dependent result was read. Critically, **B1 changed no predeclared object** — not the revised gate, not a threshold, not the edge grid, not the dependence grid, not the D-incr-form estimator — so the meta-Goodhart freeze (D-no-retune) held and D-reuse did not trigger an EXP-013 re-run. Its corrections were documentation reconciliation plus experiment-code robustness/efficiency:

- **F01 — binding-leg semantics reconciled.** The design used "binding" for two legs. Under the strict-L5 freeze, `L5 = (ci_lower > materiality)` *implies* `L3 = (ci_lower > 0)` on the same marginal series, so **L5 is the operationally binding leg and L3 its directional precondition** — propagated into EXP-017's claim and the §3 definition. EXP-018's `leg_pass_rates.csv` and `binding_corner_summary.csv` report the actual binding leg per cell, so a second refutation (had it occurred) would have been attributable.
- **F02 — validation rollup tightened; EXP-019 blocks instead of crashing.** EXP-018 `COMPLETE` now requires **every** domain SUPPORTED (was: *any* SUPPORTED and none REFUTED); EXP-019 verifies a finite per-domain MDE and writes clean `BLOCKED` metadata if any is missing rather than raising an uncaught error. **Strictly more conservative** — it cannot manufacture a pass.
- **F03 — binding corner reported explicitly across all three ρ levels**, clarifying that A1/F03 attributes the EXP-015 refutation to the moderate/high shared-latent-state ρ cells (added reporting only; budget unchanged).
- **F06 — dogfood candidate slate excludes the reference family** (EXP-019 reads `reference_family` from the operator-provided manifest and drops it from C), aligning with D-dogfood-book.
- **F07 — standalone (L2) bootstrap made opt-out** for revised-only callers (`compute_standalone=False`), removing ~1.46M wasted bootstraps across EXP-018. Because each bootstrap draws from its own explicitly-seeded RNG, the marginal/L3/L5/L1/L4 outputs are **byte-for-byte identical** with or without the flag — a pure efficiency change, so D-reuse is not triggered.

**The governance layer made the bar stricter and the unit still cleared it.** A validation that survives a tightened, more-conservative rollup is stronger evidence than one that passes the original. As with A1, none of B1's corrections could flip a conclusion — and none did.

---

## 6. State of the testing framework — now concluded

Phase 003's honest answer was *"the two-referee screen is concluded; the fitness check is not."* Phase 003b closes the gap.

**The concluded qualification suite is now complete and frozen:**

```
{ frozen Phase 001 strict gate stack,
  EXP-012 ratified-loose referee (τ 0.75/0.25/0.5 of materiality on 5m/1h/4h),
  EXP-018 validated revised incremental / portfolio-fitness unit (L1 ∧ L3 ∧ L4′ ∧ L5) }
```

The operator can now screen any candidate signal at three levels: **standalone net edge** at two stringency points (strict 1/4/12 bps, ratified-loose 0.5/2/8 bps on 5m/1h/4h), and **portfolio fitness** — does the candidate add a material net edge beyond an existing book? — at the revised-incremental floor (12/16/32 bps). EXP-019 demonstrates the three compose end to end on both the reject and pass paths.

Against design §9 this is **REVISED_UNIT_VALIDATED**: EXP-017 confirmed correctness, EXP-018 produced the finite portfolio-fitness MDE map at controlled FPR across the dependence grid (the claim EXP-015 refuted), and EXP-019 exercised both paths. This satisfies the Phase 003 D-adopt requirement that PARTIAL_SUCCESS left open, **retroactively completing the Phase 003 framework conclusion**. The framework programme is concluded; **Phase 004 — the first real signal-exploration phase — unlocks**, subject to its mandatory programme-level multiplicity-registry precondition (P3-§11), which remains a hard gate before any candidate screening begins.

---

## 7. Honest caveats carried forward

1. **The incremental screen is the coarsest of the three.** Worst-case revised MDEs (12/16/32 bps) are materially above the strict (1/4/12) and loose (0.5/2/8) maps. The unit detects *marginal* edges only at or above these dependence-grid worst-case floors; this reflects both the stricter strict-L5 `ci_lower > materiality` form and dependence-grid stress, not solely intrinsic weakness (EXP-018 §"Worst-Case Domain MDEs", "Alternative Explanations"). A candidate that adds a sub-12-bps marginal edge will not be detected as a portfolio improvement by this unit — a known sensitivity ceiling, not a defect.
2. **Validation covers construction-accepted cells only.** The 36 high-ρ/low-overlap cells are infeasible by construction and disclosed, not measured. A differently parameterized ρ/overlap grid would have different infeasible regions and would require a new scope.
3. **Synthetic known-truth draws, not real candidates or fresh regimes.** EXP-018 calibrates on seeded dependence draws; EXP-019's pass path is a synthetic fixture and its reject path reuses the EXP-009 simple-strategy lower anchor. Robustness is established to **synthetic-draw selection and dependence stress** — not to real candidate families (Phase 004 work) and not to fresh market regimes (sealed behind the global 30% holdout).
4. **The L4′/L5 freeze precondition is resolved by operator decision, not by independent proof of live soundness.** D-l4l5-freeze records operator acceptance of the reduced-conservatism L4′ plus the strict-L5 override; EXP-017 verifies the chosen forms on fixtures. This satisfies the A1/F02 precondition for freeze, but the reduced-conservatism L4′ is accepted on first-principles rationale, not demonstrated optimal in live use.
5. **Artifact-hygiene debt.** EXP-019's stale `results/blocker_report.csv` should be cleared or annotated to avoid confusing future readers; current metadata supersedes it.

---

## 8. Lessons learned

1. **A precise refutation attribution turns a redesign into a one-line repair.** A1/F03 located the EXP-015 failure to a single leg (L2) and a single instrument (BTCUSD). That made the Phase 003b fix a *predeclared removal of exactly that leg* — not a speculative redesign. Removing it flipped REFUTED→SUPPORTED with no other change, which is itself the cleanest confirmation the attribution was right. A refutation without attribution would have forced a far broader, less defensible search.
2. **The meta-Goodhart freeze holds under a fix-and-freeze attempt.** The hardest test of the predeclaration discipline is *repairing a known failure* — the temptation to tune toward the number that previously failed is maximal. The revised gate was predeclared once (D-revised-legs, D-l4l5-freeze), measured once, and never iterated against EXP-018's own output or to make BTCUSD pass. Even the pre-execution adversarial pass (B1) changed no predeclared object. A repair that survives the freeze is trustworthy; one tuned against the failing number would not be.
3. **Correct semantics can cost sensitivity — record the trade, don't hide it.** Removing L2 makes the unit a true portfolio-fitness gate (does C beat the book R?) rather than a standalone-significance gate, but at a coarser MDE. The trade is disclosed in the suite manifest and in EXP-018's limitations, so the operator screens Phase 004 candidates knowing the incremental floor is the highest of the three. A silent sensitivity loss would be the real failure.
4. **A stricter validation bar that still passes is the strongest signal.** B1/F02 tightened EXP-018's `COMPLETE` to require *every* domain SUPPORTED (not *any*) and made EXP-019 block cleanly instead of crash. The unit cleared the higher bar. Designing the bar to be conservative *before* reading results, then passing it, is more convincing than passing a lenient bar.
5. **A well-isolated unit lets you repair one layer without re-validating the stack.** Only `incremental_referee.py`'s leg-composition changed, so only the logic gate (EXP-017) and calibration (EXP-018) re-ran; EXP-013 (substrate) and the D-incr-form estimator stood unchanged and were cited as the P0 token. The substrate→logic→calibration decomposition paid off a second time — the failure and the fix were both localized to the calibration-relevant leg set.
6. **Name the binding leg up front so a second refutation stays diagnosable.** B1/F01 reconciled that under strict-L5, L5 is binding and L3 its precondition (L3 ⊆ L5), and EXP-018 emits `leg_pass_rates.csv` + `binding_corner_summary.csv` per cell. No second refutation occurred, but the diagnostic infrastructure is now standard — the Phase 003 lesson ("diagnostics are not optional for a keystone") is institutionalized rather than re-learned.
7. **Composition is a distinct test from component correctness.** Each component passing in isolation does not prove the suite composes. EXP-019 exercised the pass path Phase 003 could never reach (EXP-016 BLOCKED) and confirmed both reject and pass paths wire end to end with frozen upstream decisions flowing through. The integration anchor earned its place in the conclusion.

---

## 9. Phase verdict vs §9 criteria

**REVISED_UNIT_VALIDATED — the target outcome. The Phase 003 framework conclusion is completed and Phase 004 unlocks.**

Mapping to design [§9](design.md):

- **REVISED_UNIT_VALIDATED — reached (this outcome).** EXP-017 confirms the revised-referee correctness (✓: 7/7 verdicts, 28/28 retained legs, L2 absent), **EXP-018 produces a finite portfolio-fitness MDE map at controlled FPR across the D-dependence grid** (✓: 126/126 accepted cells PASS, worst-case 12/16/32 bps, FPR 0.0–0.004, EXP-015 corner resolved), and EXP-019 exercises both reject and pass paths (✓). Per B1/F02, EXP-018 reported `COMPLETE` only because **every** domain concluded SUPPORTED with a finite worst-case MDE. The concluded suite {strict, ratified-loose, validated-revised-incremental} is frozen; D-adopt (P3) is satisfied; Phase 004 may begin under its multiplicity-registry precondition.
- **REFUTED_AGAIN — not triggered.** No domain failed to produce a finite MDE; the L2 removal did not expose a different binding leg that fails power (the strict-L5 binding leg cleared the dependence corner in every domain).
- **BLOCKED / DEFERRED — not triggered.** The P0 re-validation was not needed (B1's only `incremental_referee.py` change is an additive, default-preserving opt-out — no estimator/CI path altered), EXP-017 showed the revised logic is correct, and the phase was not halted for cause.

The under-powered cells within domains do not block validation: each domain concludes `SUPPORTED_WITH_UNDERPOWERED_CELLS` because its binding cells produced a finite worst-case MDE (§9 rule). Phase 003b answered every question it posed, and every answer was in the SUPPORTED direction.

---

## 10. Proposed next research direction

**Phase 004 — the first real signal-exploration phase — is now unlocked, behind one hard precondition.**

**Mandatory precondition (P3-§11, unchanged):** the **programme-level multiplicity / file-drawer registry** must be documented before any candidate screening begins. The frozen three-component suite controls *per-candidate* qualification error only; screening many candidates without a registry reintroduces the multiple-comparisons problem the suite cannot see. This is a hard gate, not a recommendation.

**Phase 004 scope (operator-defined, screened through the frozen suite):**
- **Candidate model families** — tuned/ensemble standalone strategies; **chart-type-derived signals** (Line Break / Renko / Heiken Ashi) via the VAL-001 layer, with real-price outcome discipline (never HA/Renko construction prices); incremental candidates assessed against an existing book via the now-validated portfolio-fitness unit.
- Each candidate family is a new predeclared scope; the suite is **frozen** and must not be tuned against candidate outcomes (the Phase 004 analogue of D-no-retune).

**Standing programme-level deferrals (carried forward, P1-§12 / P2-§10 / P3-§10):** multi-signal / k-of-N reference books beyond a single R; non-stationary / drifting planted edges; tunable context-dependent loss beyond the EXP-011 form. The global 30% holdout remains sealed — robustness to fresh market regimes is still untested by construction and is a separate, later question.

**Next action:** author the Phase 004 checkpoint `design.md`, leading with the programme-level multiplicity-registry plan as its first deliverable, then the operator's first candidate-family scope. That is a fresh design task and is not part of this retrospective.

---

*Phase 003b closes the framework-construction programme. Phases 001–003b built, characterized, ratified, and froze a three-component qualification suite — strict gate, ratified-loose referee, and validated portfolio-fitness unit — without ever touching the global holdout. The instrument is finished; signal exploration begins in Phase 004.*
