# Phase 014-B Addendum — EXP-060B: MA(20,50) Substrate Dominance — Genuine Lead or Skew Artifact? (EXP-060 Gap-Fill)

**Type:** Research sub-phase addendum (extends `014-B-design.md` §5/§8; parallels the EXP-059B addendum §10).
**Date:** 2026-06-17.
**Status:** PLANNED — scoped (`python/experiments/EXP-060B/scope.md`); registered
`CF-HA-HARAMI-001/HYP-013b` (`multiplicity-registry.md`, Phase 014-B batch).
**Slot/ledger:** 0 candidate slots, 0 TEST reads, TRAIN-only, gross, holdouts sealed. **No new countable item.**
**Feeds:** the single 014-B **G2** (no intermediate gate). EXP-060B runs **before** G2 adjudicates.

---

## 1. Why this addendum exists (what EXP-060 did *not* test)

EXP-060 measured the best-per-layer combined event system (V2A partial take-profit × `/ADV-NONE` × benchmark
adaptive cap, conditioned `/STRONG-STAT` HA harami) and returned **`CHARACTERISED_NOT_VIABLE_ELIGIBLE`**: the
champion (A3) won **0/99 cells** against the two-baseline conjunction, despite being individually viable
(median CI_low>0) in 69/99. The recorded interpretation was *"MA-baseline dominance is a substrate property —
ZigZag single-point entry cannot match multi-leg MA(20,50) trend hold."*

A post-hoc investigation of EXP-060's generated results (operator + analyst, 2026-06-17) surfaced **two
confounds that the experiment's emitted outputs cannot resolve**, and on which the closure interpretation
depends:

### Confound 1 — the median is a left-skew mirage (mean ≈ 0)

The 014-B binding endpoint is the **median** per-event expectancy (P14), chosen for robustness to fat tails.
But EXP-060's champion combines a **win-capping** favourable scheme (V2A scales out at `{1/3,2/3,1}×fav_dist`)
with a **loss-uncapping** adverse scheme (`/ADV-NONE` carries no stop; adverse excursions are realized in full
at the time-cap close). Re-reading the per-cell `mean` column showed the champion's **gross mean is ≈0 or
negative on five of six domains** (5m −0.001, 15m −0.012, 30m −0.020, 1h −0.075, 2h −0.059; only 4h +0.090)
while the median is +0.14…+0.44. The median-based "69 viable cells" verdict therefore masks a strategy whose
*average* gross trade makes nothing — and the same capped-up/uncapped-down geometry was applied to the MA(20,50)
baseline, whose **mean was never emitted**. If MA's mean is also ≈0, MA's median "dominance" is the same
artifact at larger move scale, not a real edge.

### Confound 2 — the harami entry was never tested against random on the MA substrate

EXP-060 proved the harami **entry is redundant on the ZigZag substrate**: the champion (~0.37 ATR median on
5m) does not beat a matched-random entry through the identical exit pipeline (beats random in only 3/99 cells).
The MA(20,50) baseline, however, **was never run against a matched-random control on the MA substrate.** MA(20,50)
changes four things at once vs ZigZag — trade **direction** `rd`, the **qualifying** subset, the favourable
**target levels** (`0.5·M_sofar` with MA-defined `M_sofar`), and the **adaptive cap** (MA-defined durations) —
so its higher median is most plausibly a **trend-following-direction + no-stop drift-capture** effect that any
in-MA-regime entry would share. Without the MA-substrate matched-random control, "MA is a better substrate for
the harami" is unsupported; the strong prior (from the ZigZag redundancy result) is that the harami adds nothing
on MA either.

A separate, broader question — *does the harami add value on the MA substrate when measured properly?* — is
**out of EXP-060B scope** and would be a new scoped experiment only if EXP-060B returns SUBSTRATE_LEAD_FOUND.

## 2. Objective

Determine whether the MA(20,50) median advantage over the ZigZag champion is **(a)** a genuine,
signal-attributable, tradable edge, or **(b)** the same median-positive / mean-≈0, TIMECAP-dominated,
entry-redundant artifact as the ZigZag champion — so the G2 desk adjudicates closure on the *correct*
interpretation rather than on EXP-060's provisional "substrate property" reading.

## 3. What EXP-060B adds over EXP-060 (minimal; mostly re-instrumentation)

EXP-060's `_resolve_baselines` **already computes** the MA(20,50) arm (`ma_seg_arm`) for every arm and the
matched-random entry selection. EXP-060B makes three minimal changes:

1. **Emit MA mean + MA exit-reason composition** — EXP-060 computed the MA arm but emitted only its *median*.
2. **Add the one new computation — RM3 (matched-random on the MA substrate):** the existing matched-random
   in-regime entry selection run through the existing MA `ma_seg_arm` V2A×ADV-NONE×cap pipeline.
3. **Bootstrap the mean alongside the median** for every arm, and compute the `M3 − RM3` (and disclosed
   `Z3 − RZ3`) paired contrasts.

No new geometry, no new substrate beyond the already-registered MA(20,50) baseline, no horizon (floor=48) arm,
no parameter tuning. Expected **0 new `xen/` modules** (≤1 thin orchestration wrapper).

## 4. Diagnostic readouts

- **D1 — skew (median−mean gap):** median and **mean** (each bootstrap-CI'd) for the 8 signal arms across both
  substrates {Z3,Z2,Z1,Z0,M3,M2,M1,M0}. Headline: does **M3** show median ≫ mean like Z3? Attribution:
  ADV-NONE arms (Z3/Z1/M3/M1) vs 1:1 arms (Z2/Z0/M2/M0) — a large gap under ADV-NONE only ⇒ **uncapped
  downside is the entry-agnostic skew source.**
- **D2 — MA signal redundancy (binding discriminator):** `M3 − RM3` paired-median contrast (+ disclosed mean
  contrast). Mirrors EXP-060's own champion-vs-random test, now on the MA substrate.
- **D3 — exit-reason composition:** weight via each V2A leg / 1:1 stop / time cap, Z3 vs M3 (and nulls). Is MA
  also TIMECAP-dominated (~64% on Z3) or does it convert to FAV?

## 5. Binding endpoint & metric posture (P14-consistent)

The 014-B binding endpoint is **unchanged: median** per-event expectancy (P14), CI_low>0, ≥30 events,
P11-composed (≥5 cells/≥3 instruments). The **mean** is the P14-sanctioned **disclosed secondary**, here the
central characterisation lens (the median≫mean skew is the object under study). EXP-060B introduces **no new
binding gate that contradicts P14**: the artifact-vs-lead fork uses median-P11 viability + the own-substrate
matched-random control (exactly EXP-060's champion logic), with the mean reported as the tradability caveat.

## 6. G2 outcome routing (predeclared)

| EXP-060B verdict | Meaning | G2 consequence |
| --- | --- | --- |
| **ARTIFACT_CONFIRMED** | **Either** M3 has median≫mean with mean failing P11 (skew), **or** M3 does not beat RM3 in P11 (redundancy). | EXP-060's `CHARACTERISED_NOT_VIABLE` routing **strengthened** — MA dominance is a left-skew/entry-redundant artifact, not a missed signal. Closure well-supported (adjudicated at G2). |
| **SUBSTRATE_LEAD_FOUND** | M3 clears P11 median viability **AND** beats RM3 (CI_low>0) **AND** M3 mean clears P11. | G2 must **not** close CF-HA-HARAMI-001 without a **new scoped MA-substrate experiment**; candidate registration would occur there at PROCEED — never in EXP-060B. |
| **INCONCLUSIVE** | M3 or RM3 power-limited (<P11 quorum at ≥30 events); no correctness failure. | Record; new scope for follow-up. |
| **SUBSTRATE/METHOD_DEFECT** | Z3 fails to reproduce EXP-060 A3, or M3 fails to reproduce EXP-060 `maseg_median`, or determinism/causality/invariant failure. | Fix before reporting; no G2 input until clean. |

## 7. Mandatory-reading compliance (014-B, binding)

`014-A-conditioning-gap-and-validation-lessons.md` read in full before scoping. (a) conditioning — binding
`/STRONG-STAT` population byte-identical to EXP-053/060; matched-random controls are deliberate nulls.
(b) harami-anchor — every signal arm enters at the harami confirmation-bar real close; the substrate swap
changes only the move definition (rd/`M_sofar`/cap), not the anchor; the random controls intentionally break
the anchor (that is what makes them nulls). (c) position-in-move — descriptive-only, no live filter.
(d) expectancy — median binding (P14); mean is the disclosed secondary and characterisation focus.

## 8. Guardrails

Final-30% global holdout excluded; no new stratum opened (population byte-identical to EXP-053/060); gross only;
detection on HA candles, **all metrics on real prices** (MA(20,50) on real close, identical to EXP-060's
`ma_segment_moves`); MA crossovers and caps use only pre-entry confirmed information; matched-random entries
constructed causally; no tuning, no post-result variant selection; `tqdm`, lazy Polars, per-cell bounded memory
over the 99-cell grid; deterministic (fixed seed; second full pass). Single 014-B G2 after the full slate —
EXP-060B emits a characterisation readout only.
