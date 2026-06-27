# Phase 015 Retrospective — MA(20,50)-Substrate Conditioned Harami, Full-Surface Characterisation

**Phase:** 2026-06-17-015-ma-substrate-conditioned-harami-full-surface
**Status:** **CLOSED 2026-06-18 at G-015 — PROCEED_TO_SCREEN (native object); first candidate slot consumed.**
**Family:** `CF-HA-HARAMI-001` (REGISTERED, OPEN → first candidate active).
**Gate record:** [`G-015-gate-review.md`](G-015-gate-review.md).
**Design / D0:** [`design.md`](design.md), [`D0-predeclarations.md`](D0-predeclarations.md),
[`D0-amendment-001-dual-parallel-substrate.md`](D0-amendment-001-dual-parallel-substrate.md),
[`D0-amendment-002-drop-exp067.md`](D0-amendment-002-drop-exp067.md).

---

## 1. Objective vs outcome

**Objective (design §3).** Re-derive the full 014-B capture/exit surface on the MA(20,50) substrate
for the `/STRONG-STAT`-conditioned HA harami — hybrid and MA-native conditioning as parallel
first-class objects, reported individually — so a single terminal G-015 could decide, on the
*complete* MA surface, whether the family yields a robust mean-positive candidate (PROCEED), is a
structurally un-tradable median-only artifact (close), or has a tail-driven recoverable mean
(follow-up).

**Outcome.** **PROCEED_TO_SCREEN on the MA-native object.** The MA-substrate edge EXP-060B found at
a single geometry (V2A × `/ADV-NONE`) generalises into a robust, signal-attributable, **mean-positive**
candidate across the full surface — but only for the **native** conditioning object (`/STRONG-STAT`
recomputed on MA segments). The **hybrid** object (ZigZag-`/STRONG-STAT` conditioning × MA geometry)
is EVIDENCE_AGAINST across the entire individual surface. The objective was met: the gate had a
complete surface on both objects and a mechanical, predeclared decision.

## 2. The slate and what each read returned

| Read | EXP | Native | Hybrid |
| --- | --- | --- | --- |
| L1 benchmark efficacy | EXP-061 | EVIDENCE_FOR (8 cells/6 instr, all non-4h; reconciles EXP-060B @1e-9) | EVIDENCE_AGAINST (1 cell) |
| L2 lifetime availability | EXP-062 | AVAILABILITY_GOOD (91/99), but 4/99 signal-attributable | (same; generic MA-segment property) |
| L3 adverse + mean | EXP-063 | EVIDENCE_FOR (nuanced): V-BENCH 8 cells, mean_viable 10 cells, recovery_positive=0 | — |
| S1 favourable-target | EXP-064 | EVIDENCE_AGAINST (0/7) | EVIDENCE_AGAINST (0/7) |
| S2 third-barrier | EXP-065 | EVIDENCE_AGAINST (0/4) | INCONCLUSIVE (power-limited) |
| S3 position-mgmt exits | EXP-066 | EVIDENCE_FOR (PARTIAL-V2A 21 cells; mean-positive 11) | EVIDENCE_AGAINST (0 arms) |
| S4 native combined champion | EXP-068 | **PROCEED_TO_SCREEN-candidate** (both champion arms compose the conjunction) | (hybrid disclosed; P12 check only) |
| S4 hybrid combined champion | ~~EXP-067~~ | — | **DROPPED (Amendment 002)** — no positive lever to combine |

All reads: gross, TRAIN-only, 0 candidate slots, 0 TEST reads, holdouts sealed, integrity all-pass
(99/99 reconciliation @1e-9, determinism / causality / invariants clean across the slate).

## 3. The decisive findings

1. **The MA edge is real, signal-attributable, and now mean-positive — on the native object.**
   EXP-068's two champion arms (`N-PARTIAL-V2A`, `N-V2A×ADV-NONE`) each compose the full G-015
   conjunction (median CI_low>0 ∧ raw-mean CI_low>0 ∧ beats-`RM-native`) at P11+P6. This is the
   first Phase 015 native read where the **mean co-primary** composes — the obstacle the Phase 014
   G2 flagged (mean ≈ 0) is overcome in a bounded subset.
2. **The negative mean is not structural.** `N-PARTIAL-V2A` is P4=PARTIAL_RECOVERY (1 structural / 0
   tail-driven). The Phase 015 mean-recoverability thesis is supported (narrowly): the MA mean ≈ 0 is
   a removable-tail / geometry phenomenon, not a broadly negative distribution. The closure-on-mean
   rule (P4) is therefore **not** satisfied — the family is not closed.
3. **The edge is matched-substrate-specific.** It generalises only when `/STRONG-STAT` is computed on
   the same MA segment that defines the outcome geometry. The hybrid object, which conditions on the
   ZigZag move, is EVIDENCE_AGAINST across the surface. The Amendment 001 correction — elevating
   native to a parallel first-class object — was load-bearing: had the programme kept the original
   hybrid-primary framing, the genuine signal object would have been mislabelled and under-measured.
4. **The signal is genuine but narrow.** Present even at single-leg BENCH (6 non-4h FX cells); the
   defensible geometry-independent core is ~5 non-4h FX cells (GBPUSD/NZDUSD/GBPJPY ± EURUSD). The
   mean breadth is thin (11–14/99 vs median-viable 45–89); `N-V2A×ADV-NONE` is TAIL_DRIVEN and
   4h-concentrated. These are screening-scope caveats, not gate blockers.

## 4. Process lessons

- **Predeclared mechanical gates resist post-result goalpost-moving.** The thin mean breadth made
  MEAN_RECOVERABLE tempting, but the raw-mean co-primary *composes* at CI_low>0 (P11+P6), so the
  PROCEED bar was mechanically met. Down-routing a composing conjunction on discretionary discomfort
  would have been the reselection the programme guards against. The correct home for the caveats is
  the *screening scope's definition* (lead with bounded-downside `N-PARTIAL-V2A`, target the non-4h
  FX core), not the gate verdict.
- **A post-hoc diagnostic can underwrite a verdict's direction without widening its basis.** EXP-068's
  non-predeclared winsorized mean is positive in 46–73 cells vs 10–14 for the raw mean — strong
  corroboration that the negative mean is tail-driven, not structural (it licenses keeping the family
  OPEN and routing PROCEED over CHARACTERISED_NOT_VIABLE). But it was held strictly to its diagnostic
  role: the binding PROCEED test stayed the **predeclared raw mean** (11/14 cells). Swapping in the
  tail-robust estimator to broaden the PROCEED basis would have been post-result metric redefinition
  (P8). Whether a tail-robust mean should be a *predeclared* endpoint is a question for the screening
  scope's D0, not a retroactive gate edit. (Resolved in [`G-015-gate-review.md`](G-015-gate-review.md)
  §"On the post-hoc winsorized-mean diagnostic".)
- **The dual-object split (Amendment 001) was the phase's key methodological correction.** It traces
  to the EXP-060B/061 `M`-arm mislabelling; catching it before the surface re-run prevented a second
  instance of the 014-A "narrow read stands in for the family hypothesis" error.
- **Dropping a confirmatory read on an already-negative object (Amendment 002) is not early closure.**
  EXP-067 gated nothing — the native PROCEED path is independent — and every read on the *native*
  object carrying the live signal was run. The honest caveat (hybrid combined-champion efficacy is
  strictly unmeasured) is recorded; it is reinstatable if a future gate judges the inference
  insufficient.
- **The fixed per-cell bootstrap seed (P3 [REC])** removed the family-index BENCH viability ±1–2-cell
  drift that the 014-B G2 had to caveat — absolute viability counts are now stable across scripts.

## 5. Routing — next phase (candidate screening)

The MA-native candidate `CF-HA-HARAMI-001/CAND-001` (both champion arms, first slot consumed) advances
to candidate screening under the established pipeline (own design, own D0/G0):

1. **Event-level method calibration (EXP-027-analog), TRAIN-only** — FPR control, finite MDE,
   determinism on the MA-native conditioned population before any TEST contact.
2. **One-shot TEST confirmation of the non-4h FX core** under the bounded-downside `N-PARTIAL-V2A`
   lead definition (`N-V2A×ADV-NONE` disclosed). Materialize the 5m/15m/30m FX-core strata in
   `test-read-ledger.md` first; honor the 2-lifetime-counted-reads cap; **EURUSD is ineligible**
   (TEST-capped instrument-wide, holdout-contaminated EXP-032).
3. **Cost-aware / tail-filter follow-up (conditional)** — re-read the mean co-primary on the FX core
   under costs; targeted capped-downside / tail-filter for the `N-V2A×ADV-NONE` TAIL_DRIVEN cells
   (the MEAN_RECOVERABLE lever), opened only if the bounded-downside confirmation survives.

The screening scope makes the first TEST/holdout contact in the family's history; nothing is read
until it predeclares it.

## 6. Ledger / accounting at phase close

| Item | State |
| --- | --- |
| Candidate slots | **1 (first) consumed at G-015** — the MA-native branch. All Phase 015 *experiments* were 0-slot. |
| TEST reads | **0 spent.** `test-read-ledger.md` unchanged; holdouts sealed; no new-universe row read under the HA-harami event definition. |
| Registered branches measured | `/MA-SUBSTRATE` (+ `hybrid`/`native` modes), `/VPTARGET`, `/MAGTARGET`, `/THIRD-TIME`, `/THIRD-EVENT`, `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, `/ADV-EXTREME-rr1`, `/ADV-NONE` (disclosed). Dispositions recorded; negative/inconclusive items retained in the file drawer. |
| Dropped items | EXP-067 (HYP-020), EXP-069 (HYP-022) — retained in the ledger, never deleted or reused. |
| Family | `CF-HA-HARAMI-001` REGISTERED / OPEN — **first candidate active.** |
