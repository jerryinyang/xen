# G-017 Gate Review — CF-CAPGEO-001 Qualifier & Protocol Validation (Terminal)

**Date:** 2026-06-21
**Gate:** G-017 (Phase 017 terminal gate — validation of the `ASS` qualifier and the `WF-EXPANDING`
walk-forward protocol, **not** candidate screening)
**Adjudication:** desk review against the **predeclared mechanical verdict rule** (`D0-predeclarations.md` §D5);
drafted for operator ratification
**Outcome:** **`DISCOVERY_ONLY`** — `ASS` is **binding-ineligible** for CF-CAPGEO-001; the **frozen
referee suite remains the binding gate** for Phase 018.
**Holdout:** never touched at any point in Phase 017. **0 candidate slots, 0 counted TEST reads**
(synthetic substrates + current first-49% TRAIN-only dogfood). `test-read-ledger.md` unchanged.

---

## 1. Decision

The `ASS` (Adaptive Signal Scoring) qualifier and the `WF-EXPANDING` expanding-window walk-forward
protocol are adjudicated **`DISCOVERY_ONLY`**:

- **`ASS` is NOT binding-eligible** for any CF-CAPGEO-001 verdict. It may be used in Phase 018 as a
  **non-binding discovery / disclosure instrument** (it produces trustworthy expectancy, median, and
  CIs in its validated regime — see §4), but it **cannot adjudicate** a candidate.
- **The frozen referee suite remains the binding gate** for Phase 018 — the EXP-003 strict gate stack,
  the EXP-012 ratified-loose referee, the EXP-018 revised incremental/fitness unit, and the
  EXP-027/070-analog event-level calibration, exactly as carried through every prior family.
- This is **`DISCOVERY_ONLY`, not `PROTOCOL_DEFECT`.** Determinism held byte-identical everywhere and
  the `WF-EXPANDING` counted-read accounting honored the 2-read cap in all 8 tested scenarios (§3, §6).
  There is **no defect to fix and re-run**; the demotion is a substantive limitation of the qualifier's
  shape-sight, established cleanly.

The verdict is the **predeclared mechanical consequence** of the D5 conjunction failing on EXP-078; it
is not operator discretion beyond the table (§2).

## 2. Relationship to the predeclared D5 verdict rule (mechanical)

`D0-predeclarations.md` §D5 defines `ASS_VALIDATED` as a **conjunction** of eight legs across
EXP-076/077/078. `DISCOVERY_ONLY` is the predeclared consequence if **any** leg fails or is
power-limited while **no fundamental defect** is present:

```
ASS_VALIDATED  iff  recovery (076) ∧ shrinkage-monotone (076)
                AND  FPR≤0.05 (077) ∧ MDE finite (077) ∧ P(>X) reliable (077) ∧ cap-honoring accounting (077)
                AND  shape discriminates (078) ∧ k-sensitivity routing-invariant (078)
DISCOVERY_ONLY iff  any of the above fails / is power-limited, but no fundamental defect
PROTOCOL_DEFECT iff WF-EXPANDING accounting cannot honor the 2-read cap OR determinism fails
```

**EXP-078 fails two of its two binding legs** (shape discrimination FAIL on both sub-legs; `k`-sensitivity
ROUTING_FLIP). The conjunction therefore **cannot hold**. Per the pre-registered routing (EXP-078 scope
§Success/Failure; design.md §7), the mechanical verdict is **`DISCOVERY_ONLY`**. Determinism held and the
accounting cap was honored, so the `PROTOCOL_DEFECT` branch is not triggered. The gate is decided by the
frozen rule; the explanation below was not predeclared (freeze the rule, not the story — retrospective §2.1).

## 3. Per-leg adjudication of the `ASS_VALIDATED` conjunction

Each leg is read **per stratum** (LESSON-001); no collapsed cross-cell boolean is binding. All numbers
below were independently re-derived by the Stage-5 audits (EXP-076 CONDITIONAL PASS 1C-resolved/2W/3I;
EXP-077 PASS 0C/1W/3I; EXP-078 PASS-trust 0C/2W/4I); all three post-experiment governance verdicts are
APPROVE.

| # | Leg (source) | Per-stratum standing | Contributes to gate |
| --- | --- | --- | --- |
| 1 | **Recovery bias** (EXP-076) | **PASS** — 0/99 fails for expectancy and median; worst `median\|err\|/SE` 0.722 (expectancy, `Sminus0` n=500) and 0.702 (median, `U2` n=250), both under the 0.85 band and above the unbiased floor 0.6745. Holds across unimodal/skew/bimodal incl. negative-median skews. | **HOLDS** |
| 2 | **Shrinkage monotone** (EXP-076) | **PASS** — weight `n/(n+k)` monotone (reproduces closed form to ~1e-16); sparse-pull 0.889@n=15 / 0.80@n=30 (≥0.25); rich-pull <0.05 except the **predeclared** n=2000 marginal (120/2120 = 0.0566, surfaced not silently passed). | **HOLDS** (one disclosed marginal) |
| 3 | **FPR ≤ 0.05** (EXP-077) | **HOLDS per stratum, with one bounded guard.** U0 point-crossings (n=120/1000/2000 at 0.051–0.052) are MC noise around a margin calibrated *to* 0.05 (binomial P=0.36–0.43; all binding cells Wilson-hi ≤ 0.075). `B_zero` mild inflation 0.059 at n=30/60 decaying to ~0 by n≥120 → triggers the predeclared **defer-to-median at effective-n ≤ 60** guard. The `verdict.json` FPR=FAIL flag is faithful to the point gate but is **not** a whole-qualifier error-control failure. | **HOLDS** (Guard i) |
| 4 | **MDE finite** (EXP-077) | **PASS** — `MDE(n)` finite/non-degenerate at every n≥30 (0.644@n=30 → 0.050@n=8000; max TPR 0.986–1.0). Degeneracy, not magnitude, is the gate. | **HOLDS** |
| 5 | **`P(return>X)` reliable** (EXP-077) | **HOLDS at X=0/0.05/1.0** (slope 0.923–0.950, max-gap ≤0.029). **X=2.0 fails the slope sub-gate only** (0.652) while max-gap 0.017 (best of four) and corr 0.934 — a gate-shape artifact of predicted mass compressed near zero (deciles 10→6), not 2R miscalibration → **Guard (ii): bind on max-gap when predicted-P span is small.** | **HOLDS** (Guard ii) |
| 6 | **Cap-honoring accounting** (EXP-077) | **PASS** — 8/8 accounting scenarios (one conforming frozen WF run = +1 read; non-conforming reverts to per-fold; at-cap rejected; holdout-fold rejected; rolling 1y/2y/3y +0; 3rd read blocked). Dogfood 12/12 cells, read fraction 0.490 < 0.491, fence held, 0 counted reads. | **HOLDS** (no `PROTOCOL_DEFECT`) |
| 7 | **Shape discrimination** (EXP-078) | **FAIL — BINDING.** Both legs blind to the **subtle median-positive minority-catastrophe shape** (`B_zero` true \|g\|=0.25, `B_pos` 0.067 — below `τ_gap`=0.30; dip_p≈0.99 — not dip-bimodal). Detection on `B_zero`/`B_pos` **decays monotonically to 0 as n grows** (the sub-threshold signature). Gross bimodals detected (`B_strong` PASS; `B_neg` 0.76@n=30→1.0). U false-flag fails the **n=30 floor only** (0.135–0.152; ≤0.046 n≥60). **This is the CF-HA-HARAMI-001 / EXP-074 failure shape the diagnostic was commissioned to catch.** | **FAILS** |
| 8 | **`k`-sensitivity routing-invariant** (EXP-078) | **ROUTING_FLIP — BINDING.** K1 (shrinkage behaviour) invariant across the grid; **K2 (shrunk-expectancy null edge-call FPR) flips CONTROLLED→INFLATED at k=240 — the 2× multiplier, a core grid point, not an extreme anchor** (FPR 0.39–1.0). Mechanism: margin frozen at k=120, increasing k shrinks the null estimate toward the positive SP pooled prior (+0.518), crossing the fixed margin between k=120 (+0.414) and k=240 (+0.460). | **FAILS** |

**Six legs hold (three cleanly, three with disclosed/bounded behaviour); legs 7 and 8 fail.** The
conjunction fails ⇒ `ASS_VALIDATED` cannot be declared ⇒ **`DISCOVERY_ONLY`**.

## 4. What `DISCOVERY_ONLY` means — `ASS` is a trustworthy estimator that cannot yet adjudicate

The demotion is **specific and bounded**. `ASS` failed on **shape-sight and `k`-robustness**, not on
estimation:

- **`ASS` is a trustworthy estimator in its validated regime.** It recovers expectancy and median
  without material bias across every tested shape (leg 1), produces calibrated CIs at n≥30 (leg, EXP-076
  Stratum 2), shrinks as designed (leg 2), has finite detection power (leg 4), and is well-calibrated on
  `P(>X)` for X ∈ {0, 0.05, 1R} (leg 5) — all on i.i.d. synthetic strata carried by `WF-EXPANDING`. Its
  protocol arithmetic, determinism, and counted-read accounting are validated (leg 6); see §6.1 for the
  external-validity bound.
- **What it cannot do is *guard* the verdict against the exact shape that killed CF-HA-HARAMI-001.** A
  qualifier leaning on the `ASS` shape leg alone would still pass a `B_zero`-like population (90% at +0.15,
  10% catastrophic at −1.5, true mean ≈ 0) as non-pathological. That is precisely the structural blindness
  the frozen referee suite — with its independent gate legs — does not share, which is why the suite stays
  binding.

**Permitted Phase-018 use of `ASS` (non-binding):** expectancy/median/tail **disclosure** alongside the
binding suite verdict; descriptive characterization of realized return structure (HYP-002); the
expanding-window protocol as an evaluation scaffold. **Prohibited:** any pass/reject decision, candidate
admission, or holdout-release adjudication resting on `ASS`.

## 5. Carry-forward limitations & guards to register (binding into Phase 018)

These are recorded here as the gate's ratified dispositions; they are registered, not acted on now.

1. **Guard (i) — defer-to-median at effective-n ≤ 60** on bimodal/asymmetric mean-null strata under
   `WF-EXPANDING` (extends the EXP-076 "no expectancy edge-calls at effective-n < 30" disposition; the
   5-fold split lowers effective per-fold count, so `B_zero` under-coverage persists to n=60). (EXP-077.)
2. **Guard (ii) — `P(>X)` slope sub-gate inapplicable at compressed predicted-probability span** (e.g.
   ptp < ~0.1); bind on max-gap there. The D2.4 gate was **not** retro-edited. (EXP-077.)
3. **Shape-sight is only PARTIALLY closed.** `ASS` catches gross bimodality and strong left-skew but is
   structurally blind to the subtle median-positive minority-catastrophe shape. Any Phase-018 reliance on
   shape-sight must treat this blind spot as on-the-record; the binding shape guard remains the frozen
   referee suite, not `ASS`. (EXP-078.)
4. **Clean-unimodal false-flag operating point needs n ≥ 60** at the frozen `τ_gap`=0.30. (EXP-078.)
5. **The shrunk edge-call FPR is `k`-fragile** — the default `k`=120 sits near the boundary where
   shrinkage-toward-prior begins to dominate; doubling `k` inflates the null FPR. Any future binding use
   of the shrunk-expectancy edge-call must treat `k` as load-bearing. (EXP-078.)
6. **Coverage `k`-leg disclosure is partial** — EXP-078 swept 2 of 3 pre-registered `k`-dependent legs
   (CI-coverage leg not swept). It cannot rescue the verdict (a missing leg can only add flips) but the
   `k`-sweep disclosure is incomplete and noted. (EXP-078 audit Warning 2.)
7. **Recovery/coverage governance dispositions (EXP-076):** coverage binding at n≥30 with n=15 expectancy
   recorded as a disclosed sparse-stress diagnostic (intrinsic percentile-mean-bootstrap floor, not a
   defect; median coverage holds at n=15); the n=2000 rich-pull marginal is the predeclared analytic
   boundary. These should be carried in the dated `D0-amendment` noted by EXP-076.

## 6. Why not `PROTOCOL_DEFECT`

The `PROTOCOL_DEFECT` branch fires only if `WF-EXPANDING` accounting cannot honor the 2-read cap **or**
determinism fails. Neither occurred:

- **Accounting:** 8/8 scenarios pass; the 2-lifetime-read cap is demonstrably honored, folds are
  in-protocol disclosures (not separate reads) under the D4.1 freeze-before-OOS conditions, and the
  holdout is never a fold. The rule was **validated as a function**, not exercised against the live ledger
  (Phase 017 spends 0 counted reads).
- **Determinism:** every experiment's second full pass is byte-identical (EXP-076/077/078 hash-matches;
  cross-experiment anchors reconcile diff 0.0). The double-FAIL in EXP-078 is **implementation-faithful**,
  independently reproduced to MC noise by the auditor (mixture means to 1e-4, U0 false-flag exactly, the
  sub-0.30 true \|g\|, the K2 shrink-toward-prior mechanism).

So the demotion is a real limitation of the qualifier, not a fixable protocol bug.

### 6.1 External-validity bound — synthetic is the easy case (the FAIL is a lower bound)

The binding legs validated `ASS` against **known synthetic ground truth**, which is the *correct and
only* method for recovery/coverage/MDE/FPR — no ground truth exists on real returns. The gate is **not**
weakened over "it wasn't tested on real data." But two genuine external-validity limits bound what
`DISCOVERY_ONLY` (and any future re-validation) can claim:

1. **i.i.d.-synthetic ≠ serially-dependent real.** All binding legs are i.i.d. by construction. The
   dependence-aware **moving-block bootstrap — the one bridge to real data — was exercised only in
   EXP-077's non-binding dogfood, with no ground-truth coverage check.** It is the least-validated
   component in the phase.
2. **Reliability (D2.4) was binding-on-synthetic / non-binding-on-real,** despite being the one leg that
   needs no ground truth and *could* run bindingly on real first-70% TRAIN folds.

**Framing:** synthetic is the **easy** case, so EXP-078's shape FAIL is a **lower bound** — real,
serially-dependent, fat-tailed data cannot *rescue* a diagnostic already structurally blind on clean
synthetic shapes. This makes `DISCOVERY_ONLY` **robust**, not marginal. Accordingly, the EXP-077 phrase
"validated under `WF-EXPANDING`" is read precisely as **"validated on i.i.d. synthetic strata *carried by*
`WF-EXPANDING`"** — the protocol arithmetic and estimator error-control are what the synthetic legs
certify; real strata remain the live test (Phase 018).

## 7. Bracket re-confirmation at Phase 018 D0 (carried, design §7.1)

Phase 017 validated `ASS` against synthetic ground truth across `n ∈ [15, 8000]`. Although the verdict is
`DISCOVERY_ONLY`, the bracket condition still governs any **discovery** use of `ASS` in Phase 018: once
INFR-003 produces the real 5-year per-cell event-count distribution, confirm at the Phase 018 D0 that
every (substrate × instrument × domain) cell's `n` falls inside `[15, 8000]`; any out-of-bracket cell is
excluded from `ASS` discovery with disclosure or triggers a scoped EXP-079 synthetic-span extension — not
a Phase 017 re-run.

## 8. Integrity confirmation

- **Holdout sealed** throughout Phase 017; the final-30% global holdout was never loaded. Synthetic
  substrates + current first-49% TRAIN-only dogfood only.
- **TEST discipline:** 0 counted TEST reads; the next-21% TEST stratum and final-30% holdout were never
  sliced. `test-read-ledger.md` unchanged (INFR-003 will re-materialize it on the 5-year strata before
  Phase 018).
- **Determinism / anchors:** byte-identical second passes everywhere; cross-experiment anchors EXP-076 ↔
  EXP-077 ↔ EXP-078 reconcile to diff 0.0.
- **No goalpost-moving:** the frozen D2.5 shape diagnostic, the D2.4 slope gate, and the D2.2 FPR margin
  were **not** retro-edited; the FAILs stand as written against the frozen rules. Per-stratum doctrine
  (LESSON-001) enforced — `collapsed_convenience_flag=false` is NON-BINDING in every `verdict.json`.
- **Audits / governance:** EXP-076 CONDITIONAL PASS (C1 resolved) / EXP-077 PASS / EXP-078 PASS-trust; all
  three post-experiment governance verdicts APPROVE.

## 9. Consequences

1. **G-017 → `DISCOVERY_ONLY`.** `ASS` binding-ineligible; the frozen referee suite remains the binding
   gate for CF-CAPGEO-001. Recorded in `docs/signal-registry/candidate-families/cf-capgeo-001.md`,
   `docs/signal-registry/multiplicity-registry.md` (Phase 017 batch outcome), the family detail index
   `docs/experiments-docs/families/cf-capgeo-001/INDEX.md`, and the master index
   `docs/experiments-docs/INDEX.md`. No counted TEST read or disclosure entered (none spent).
2. **Phase 017 CLOSES at G-017.** Retrospective to be written (`retrospective.md`, this checkpoint),
   carrying the guards in §5 and the two-instrument validation lessons.
3. **CF-CAPGEO-001 stays REGISTERED — SCREENING-GATED.** Precondition (1) (G-017 `ASS_VALIDATED`)
   resolves to `DISCOVERY_ONLY`: Phase 018 proceeds with the **frozen referee suite binding** and `ASS`
   as a discovery instrument only. Precondition (2) — **INFR-003 (5-year data + holdout re-seal, VAL-005)**
   — remains OPEN and must complete before Phase 018 opens.
4. **No Phase 018 entry until INFR-003 + VAL-005 PASS.** Phase 018 opens with its own D0/G0, including the
   §7 bracket re-confirmation and the §5 guard register.
5. **Programme routing (next phase)** is an operator decision outside this gate. This gate makes no claim
   on the Phase 018 screening design beyond fixing the binding-gate posture (frozen suite) and the
   discovery role of `ASS`.

## 10. Conditions on any future re-validation of `ASS` to binding status

If a future scope (a candidate **EXP-079**, for the operator/retrospective to decide — **not initiated
here**) seeks to lift `ASS` from discovery to binding, it must satisfy, at minimum:

- **C1 — validate moving-block CI coverage against a *dependent* synthetic DGP with known truth** (e.g.
  GARCH / regime-switch), not just i.i.d. — closing the §6.1(1) gap (the least-validated component).
- **C2 — make the D2.4 `P(>X)` reliability check binding on real first-70% TRAIN folds** — closing the
  §6.1(2) gap (the one leg that needs no ground truth and can run bindingly on real data).
- **C3 — carry the per-stratum guards** (§5): defer expectancy edge-calls to the median at effective-n
  ≤ 60; bind reliability on max-gap when the predicted-probability range is compressed; and treat **`k` as
  load-bearing** (the routing flips at the 2× grid point — do not assume robustness).
- **C4 — honor the bracket condition** (§7): any `ASS` use is valid only for realized per-cell
  `n ∈ [15, 8000]`, re-confirmed at the Phase 018 D0 once INFR-003 lands.

And, necessarily, a **shape leg that sees the subtle median-positive minority-catastrophe shape** the
current diagnostic is blind to (§3 leg 7; the §11 follow-ups are candidate paths).

## 11. Retained follow-up candidate scopes (noted, not initiated)

These were surfaced by the slate and are recorded for a future scope, not opened here (the frozen `τ_gap`
and `k` are not re-tuned in-gate):

- Map the `|g|` detectability crossover for the gap leg on a finer bimodal grid around `τ_gap`=0.30
  (quantify exactly which subtle bimodal shapes `ASS` can/cannot see). (EXP-078 §next-steps 1.)
- Add a **minority-mass / left-tail-mass shape detector** complementary to dip + mean–median gap, targeting
  the small-minority-catastrophe shape the current legs miss — a candidate path to *fully* closing the
  EXP-074 gap (new scope; do not retro-edit the frozen D2.5 diagnostic). (EXP-078 §next-steps 2.)
- Re-anchor or `n`-condition the false-flag operating point, or formally restrict the diagnostic's binding
  domain to n≥60. (EXP-078 §next-steps 3.)
- Optional protocol refinement: replace the FPR point-≤-0.05 sub-gate with a Wilson-hi/MC-CI-aware decision
  so calibrated-to-0.05 estimators are not failed by chance crossings (pre-register before any TEST
  contact). (EXP-077 §next-steps 2.)

All file-drawer items (the `ASS`/VAL-001/002/003 outcomes, the synthetic DGP registrations, the guards)
are **retained in the registry, never deleted or reused**, per programme discipline.

---

*Companion documents: [`design.md`](design.md) §7 (gate criteria) · [`D0-predeclarations.md`](D0-predeclarations.md)
§D5 (mechanical rule) · [`LESSON-001-per-stratum-verdict.md`](LESSON-001-per-stratum-verdict.md) ·
EXP-076/077/078 `results.md` + `audit.md` · family spec
[`../../../signal-registry/candidate-families/cf-capgeo-001.md`](../../../signal-registry/candidate-families/cf-capgeo-001.md).*
