# Phase 017 Retrospective — CF-CAPGEO-001 Qualifier & Protocol Validation

**Phase:** 2026-06-20-017-capgeo-qualifier-validation
**Status:** **CLOSED at G-017 (2026-06-21) — `DISCOVERY_ONLY`.**
**Outcome:** the `ASS` qualifier and `WF-EXPANDING` protocol are validated as *estimation/protocol*
machinery but **not binding-eligible**; the **frozen referee suite remains the binding gate** for
Phase 018. `ASS` is admitted as a non-binding discovery overlay.
**Discipline held:** synthetic substrates + current first-49% TRAIN-only dogfood; **0 candidate slots,
0 counted TEST reads, holdout never touched.** `test-read-ledger.md` unchanged.
**Companion:** [`G-017-gate-review.md`](G-017-gate-review.md) (terminal adjudication, per-leg).

---

## 1. Objective vs outcome

Phase 017 was the CF-CAPGEO-001 analogue of the 001–003b referee-hardening era: **validate the
yardstick before the signal.** It asked one question — are `ASS` and `WF-EXPANDING` trustworthy enough
to *bind* a CF-CAPGEO-001 verdict, or must `ASS` be demoted to discovery-only with the frozen suite
staying binding?

**Answer: demoted to discovery-only.** The validate-first posture paid off exactly as intended — it
caught a load-bearing weakness in the qualifier **before** a single market read was spent on it. `ASS`
is a sound *estimator* (recovers expectancy/median without material bias; calibrated CIs at n≥30;
finite detection power; honest protocol accounting), but it **cannot guard the verdict against the very
shape that killed CF-HA-HARAMI-001** — the subtle median-positive minority-catastrophe bimodal. That is
the one thing a binding qualifier for this family had to do, and it is the one thing `ASS` cannot yet do.

The phase changed no verdict about any market signal. It decided only the qualifier's standing.

## 2. Experiment slate (as run)

| EXP | Role | Result | One-line |
| --- | --- | --- | --- |
| **EXP-076** (`ASS`/VAL-001) | G-017a recovery screen | **RECOVERY_VALIDATED_G017a** | Recovers ground truth — recovery PASS all 198 cells; coverage in-band ∀ n≥30; shrinkage as designed. n=15 expectancy sub-band is the intrinsic percentile-mean-bootstrap floor (disclosed diagnostic), n=2000 rich-pull marginal predeclared. Audit C1 (collapsed verdict) → per-stratum, no recompute. |
| **EXP-077** (`ASS`/VAL-002) | Error-control + protocol under `WF-EXPANDING` | **VALIDATED_WITH_GUARDS** | MDE finite ∀ n≥30; accounting 8/8 cap-honored; dogfood 12/12 fence-held; determinism/anchor exact. FPR/reliability leg-flags faithful but not whole-qualifier failures → two bounded per-stratum guards. No PROTOCOL_DEFECT. |
| **EXP-078** (`ASS`/VAL-003) | Shape discrimination + `k`-sensitivity | **DISCOVERY_ONLY (binding double-FAIL)** | Shape diagnostic structurally blind to the subtle `B_zero`/`B_pos` shape (decays to 0 with n); U false-flag fails the n=30 floor only; K2 shrunk edge-call FPR `k`-fragile (flips at the 2× grid point). Determinism held → not a defect. |

The slate ran in pipeline order (EXP-076 G-017a screen gated EXP-077; EXP-078 last). All three carry
post-experiment governance **APPROVE**.

## 3. The decision (why `DISCOVERY_ONLY`, mechanically)

`D0-predeclarations.md` §D5 makes `ASS_VALIDATED` a conjunction of eight legs. **Six hold** (recovery,
shrinkage-monotone, FPR-with-guard, MDE, reliability-with-guard, accounting); **two fail** (EXP-078
shape discrimination; EXP-078 `k`-routing-invariance). A conjunction with two failing binding legs
cannot be declared, so the predeclared routing is `DISCOVERY_ONLY`. It is **not** `PROTOCOL_DEFECT`:
determinism was byte-identical everywhere and the `WF-EXPANDING` counted-read accounting honored the
2-read cap in all 8 scenarios — there is nothing to fix and re-run. The gate is a mechanical table
lookup on the frozen rule; the explanation was not predeclared.

## 4. Lessons learned

1. **Validate-first earned its tax again.** Three synthetic experiments and 0 TEST reads surfaced a
   qualifier blind spot that, undiscovered, would have let a Phase-018 candidate of exactly the
   CF-HA-HARAMI-001 failure shape pass as non-pathological. The cost of finding this now is trivial;
   the cost of finding it after spending counted reads would not have been.

2. **A guard must fit the shape of the observation — and `ASS`'s shape leg only partially does.** The
   EXP-074 lesson (a tail-shape-blind guard vetoed the one feature explaining a mean's collapse)
   motivated building EXP-078 as the predeclared escape hatch *before* the guard fires. EXP-078 found
   the escape hatch itself is half-built: the dip + mean–median-gap legs catch *gross* bimodality but
   are structurally blind to the *subtle* minority-catastrophe shape (true `|g|` < `τ_gap`=0.30 AND no
   dip antimode). Fully closing the EXP-074 gap needs a **minority-mass / left-tail-mass detector** the
   current diagnostic lacks (candidate follow-up, not initiated).

3. **Synthetic is the easy case — so the FAIL is a lower bound, and that makes the verdict robust.**
   The binding legs are i.i.d.-synthetic by construction (the only place ground truth exists). The one
   bridge to real, serially-dependent data — the moving-block bootstrap — was exercised only in
   EXP-077's *non-binding* dogfood with no ground-truth coverage check, making it the least-validated
   component. Real data cannot *rescue* a diagnostic already blind on clean synthetic shapes, so
   `DISCOVERY_ONLY` is robust, not marginal. **Wording discipline:** prefer "validated on i.i.d.
   synthetic strata *carried by* `WF-EXPANDING`" over "validated under `WF-EXPANDING`," which slightly
   oversells the real-data reach.

4. **Per-stratum verdict representation is now enforced (LESSON-001).** EXP-076 audit C1 caught a
   collapsed `overall_pass_literal` boolean masking 194/198 passing cells. The fix was representational
   (regenerate per-stratum, no recompute) and is now a binding Stage-4/Stage-8 governance check plus a
   standing lesson file. Every later experiment (077/078) emitted per-stratum verdicts with the
   collapsed convenience flag explicitly captioned NON-BINDING — the doctrine working as intended.
   EXP-078's "pooled B-detection FAIL" was precisely a per-stratum 2-way split (gross vs subtle
   bimodal) the doctrine kept visible.

5. **Freeze the design alongside D0.** The governing `design.md` was amended mid-phase (2026-06-20) to
   add LESSON-001 and the §8 per-stratum-verdict guardrail, retrofitted from EXP-076's C1 audit.
   Legitimate reactive hardening, but next time the verdict-representation guardrail should be in the
   design at G0, not added after the first experiment exposes the gap.

6. **`k` is load-bearing, not a free knob.** The shrinkage constant's default (`k`=120 = median SP `n`)
   sits near the boundary where shrinkage-toward-prior starts to dominate the null estimate; the
   edge-call FPR flips at the 2× grid point. Any future binding use of the shrunk-expectancy edge-call
   must treat `k` as a calibrated, disclosed choice — never assume robustness.

## 5. Carry-forward (binding into Phase 018)

`ASS` enters Phase 018 as a **non-binding discovery overlay**; the **frozen referee suite
(EXP-003/012/018 + EXP-027/070-analog) is the binding gate.** The following are registered (not acted
on now):

- **Guard (i):** defer expectancy edge-calls to the median at **effective-n ≤ 60** on bimodal/asymmetric
  mean-null strata under `WF-EXPANDING`. (EXP-077.)
- **Guard (ii):** `P(>X)` slope sub-gate inapplicable at compressed predicted-probability span — bind
  on max-gap. (EXP-077; D2.4 not retro-edited.)
- **Shape blind spot:** `ASS` shape-sight only partially closes the EXP-074 gap — on the record before
  any Phase-018 candidate is read; the binding shape guard remains the frozen suite. (EXP-078.)
- **Operating-point floors:** clean-unimodal false-flag controlled only at **n ≥ 60**; `k`-fragile
  shrunk edge-call FPR; CI-coverage `k`-leg disclosure partial (2/3). (EXP-078.)
- **Recovery dispositions:** coverage binding at n≥30 (n=15 expectancy a disclosed sparse-stress
  diagnostic); n=2000 rich-pull marginal predeclared. (EXP-076; dated `D0-amendment`.)
- **Bracket condition (§7.1):** any `ASS` use valid only for realized per-cell `n ∈ [15, 8000]`,
  re-confirmed at the Phase-018 D0 once INFR-003 lands.

**Conditions to re-validate `ASS` to binding (a candidate EXP-079, operator's call — not initiated):**
C1 moving-block CI coverage on a *dependent* known-truth DGP (GARCH/regime-switch); C2 make the D2.4
reliability check binding on real first-70% TRAIN folds; C3 carry the guards + treat `k` as load-bearing;
C4 honor the bracket. And, necessarily, a shape leg that sees the subtle minority-catastrophe shape.

## 6. Integrity ledger

- **Holdout sealed** throughout; final-30% never loaded. **0 counted TEST reads** (synthetic + current
  first-49% TRAIN dogfood only); next-21% TEST stratum never sliced. `test-read-ledger.md` unchanged.
- **0 candidate slots** consumed (methodology validation, not screening).
- **Determinism:** every second pass byte-identical; cross-experiment anchors EXP-076 ↔ 077 ↔ 078
  reconcile to diff 0.0.
- **No goalpost-moving:** frozen D2.5 shape diagnostic, D2.4 slope gate, and D2.2 FPR margin not
  retro-edited; FAILs stand against the frozen rules.
- **Audits:** EXP-076 CONDITIONAL PASS (C1 resolved, 2W/3I); EXP-077 PASS (0C/1W/3I); EXP-078 PASS-trust
  (0C/2W/4I). All post-experiment governance verdicts APPROVE.

## 7. Proposed next direction (operator decision, outside this gate)

1. **INFR-003 remains the live Phase-018 precondition** — the 5-year 1-minute data upgrade + VAL-005 +
   holdout re-seal. It runs/ran in parallel to Phase 017; Phase 018 does **not** open until it completes
   and VAL-005 passes.
2. **Phase 018 opens with the frozen referee suite binding and `ASS` as a discovery overlay** — its D0
   carries the §5 guards, the bracket re-confirmation, and the separability gate. The precondition
   wording in the family spec and Phase-018 skeleton is updated from "once `ASS_VALIDATED`" to this
   posture.
3. **Optional, operator's call:** an EXP-079 re-validation of `ASS` toward binding status under
   conditions C1–C4 (above), and/or a shape-leg upgrade targeting the minority-catastrophe shape. Noted,
   not initiated; `τ_gap` and `k` remain frozen.

All Phase-017 file-drawer items (the three `ASS`/VAL outcomes, the synthetic DGP registrations, the
guards, LESSON-001) are **retained in the registry, never deleted or reused.**
