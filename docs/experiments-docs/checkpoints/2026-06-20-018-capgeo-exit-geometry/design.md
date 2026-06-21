# Phase 018 — CF-CAPGEO-001: Data-Derived Exit / Capture Geometry (DRAFT SKELETON)

**Status:** **DRAFT — GATED, NOT OPENED.** Pre-drafted 2026-06-20; **revised 2026-06-21 for the G-017
`DISCOVERY_ONLY` outcome.** **Does not open** until **INFR-003 COMPLETE ∧ VAL-005 PASS** (the G-017
gate is already resolved — see below). The directory date will be re-stamped to the actual open date if
it differs; all numeric/slate items below are skeleton placeholders pending the Phase 018 D0.
**Family:** `CF-CAPGEO-001` (REGISTERED, SCREENING-GATED — `candidate-families/cf-capgeo-001.md`).
**Opened by (when it opens):** INFR-003 completion + VAL-005 PASS (G-017 resolved 2026-06-21).
**Discipline (binding):** all returns/expectancy on **real prices**; HA/Renko brick prices never used
for P&L; timestamp alignment never bar-index; the final-30% holdout never loaded or made a WF fold.

> **G-017 outcome (binding for this design) — `DISCOVERY_ONLY` (2026-06-21,
> [`../2026-06-20-017-capgeo-qualifier-validation/G-017-gate-review.md`](../2026-06-20-017-capgeo-qualifier-validation/G-017-gate-review.md)).**
> `ASS` was validated as an *estimator/protocol* (recovery, coverage at n≥30, finite MDE, honest
> accounting, determinism) but **failed two binding legs** in EXP-078 — its shape diagnostic is
> structurally blind to the subtle median-positive minority-catastrophe shape (the exact
> CF-HA-HARAMI-001 failure shape), and its shrunk edge-call FPR is `k`-fragile. Per the predeclared D5
> rule the `ASS_VALIDATED` conjunction cannot hold, so **`ASS` is NOT the binding qualifier here.** The
> **frozen referee suite (EXP-003 strict stack + EXP-012 ratified-loose + EXP-018 revised
> incremental/fitness + EXP-027/070-analog event-level calibration) is the binding gate**; `ASS` is a
> **non-binding discovery/disclosure overlay** (expectancy + median + tail per cell, return-structure
> characterization, `WF-EXPANDING` as the evaluation scaffold). This is **not** `PROTOCOL_DEFECT` —
> determinism held byte-identically and the counted-read accounting honored the 2-read cap (8/8). See
> §5 and §8 for how this reshapes the verdict and the separability gate.

---

## 1. Why Phase 018 exists

Both prior families closed because *the lever that removes the binding obstacle also removes the edge*
(retrospective §4.1) — CF-AVWAP-001 on capture geometry, CF-HA-HARAMI-001 on entry bimodality. Phase
018 is the first **exit/capture-geometry-first** screen: entries are frozen to four known substrates
and the **only open axis is the exit**, asked in reverse — derive the exit from each system's own
realized return structure, then benchmark the conventional exits — judged on overall **expectancy**
(anti-overfit), under the **frozen referee suite as the binding gate** with **`ASS` as a discovery
overlay**, and behind a **pre-TEST separability gate** that would have pre-empted both prior deaths.

## 2. Substrates (frozen) and surface

| Substrate | Entry (frozen) | Role |
| --- | --- | --- |
| `SUB-AVWAP` | CF-AVWAP-001 final candidate (EXP-028/029 cTrader-confirmed) | real prior entry |
| `SUB-HARAMI-PARTIAL-V2A` | CF-HA-HARAMI-001 `N-PARTIAL-V2A` entry population | real prior entry |
| `SUB-HARAMI-V2A-ADVNONE` | CF-HA-HARAMI-001 `N-V2A×ADV-NONE` entry population | real prior entry |
| `SUB-RANDOM` | fixed-seed random entry, matched per domain | attribution null |

- **Domains:** 15m, 1h, 4h. **Instruments:** all 17. **Data:** the 5-year post-INFR-003 dataset.
- **Substrates never pooled** without a demonstrated-homogeneity claim (retrospective §2.5);
  per-stratum adjudication is the default, pooled is disclosure-only (LESSON-001).

## 3. Slate (skeleton — EXP-IDs confirmed at open; next free after Phase 017 = EXP-080)

| EXP | HYP | Question | Slot / TEST |
| --- | --- | --- | --- |
| EXP-080 | HYP-001 readiness | Are all four substrates deterministic, look-ahead-safe, with adequate per-cell coverage on the 5-year data × {15m,1h,4h}? `SUB-RANDOM` seed fixed; holdout fence verified. **Bracket check (§6):** realized per-cell event counts recorded for the §6 `[15,8000]` `ASS`-discovery bracket re-confirmation. | 0 / 0 |
| EXP-081 | HYP-002 characterize | (TRAIN-only, gross) Per-substrate realized return-structure features — capture-time geometry, time-to-peak, exhaustion, **bimodality/tail shape** — that expose what exit fits. `ASS` reports expectancy+median+tail per cell **as discovery disclosure**; the binding suite is not invoked here. | 0 / 0 |
| EXP-082 | HYP-003 derive | Derive exit candidates from EXP-081 behaviour via **predeclared mechanical derivation rules** (freeze the rule, not the story — §2.1). Lock the rule on TRAIN. | 0 / 0 |
| EXP-083 | HYP-004 test+benchmark | Test derived exits **and** conventionally benchmark the known exits (RR, trailing, volume-profile, partial splits, prior-family PARTIAL-V2A/V2A-ADVNONE/AVWAP-FH), judged under the **frozen referee suite (binding)** with **`ASS` expectancy+median+tail reported alongside (disclosure)**, **per substrate**, behind the separability gate. | per-variant slots / counted WF reads |

(Conditional cost-aware and portfolio follow-ups, analogous to the Phase 016 EXP-072/073, register at
their own D0 only on a confirmed EXP-083 result.)

## 4. Gates (skeleton)

- **G-018a (cheap TRAIN screen):** a derived/benchmark exit must clear a TRAIN-only gross
  expectancy+median+tail screen vs `SUB-RANDOM` and the per-cell matched-random null before any net
  machinery or TEST contact — the inverted-inference "fail cheaply first" structure (§2.1) that made
  negative phases free.
- **Separability gate (binding, pre-TEST — §4.1; reinforced for the `ASS` shape blind spot):**
  demonstrate the binding net-expectancy leg and the favourable signal are not driven by one
  unfilterable mechanism (the obstacle moves without moving the edge). **Because EXP-078 proved `ASS`'s
  tail diagnostic cannot see the subtle minority-catastrophe shape, this gate — not `ASS` — is the
  binding shape-guard** (see §8). A candidate that fails is a capture-bound / median-only artifact and
  is **not** carried to a counted TEST read.
- **G-018 (terminal):** the walk-forward verdict conjunction on the surviving candidates, adjudicated by
  the **frozen referee suite** (see §5).

## 5. Evaluation protocol & verdict (skeleton)

- **`WF-EXPANDING`** within the first-70% analysis set per the Phase 017 D4 schedule (validated, with the
  EXP-077 guards in §7); the **one-frozen-WF-run = one counted TEST read** accounting (D4.1, validated
  8/8) governs the ledger; holdout never a fold.
- **Binding qualifier: the frozen referee suite** (G-017 `DISCOVERY_ONLY`). **`ASS` is a non-binding
  discovery overlay** — its expectancy/median/tail are reported alongside every read for interpretation
  and disclosure, but **no pass/reject/admit decision rests on `ASS`.**
- **Verdict conjunction (to fix at D0; binding legs are the frozen suite's):** a candidate "confirms"
  iff it **passes the frozen referee suite** on the aggregate WF verdict ∧ **beats `SUB-RANDOM`/matched-
  random** ∧ **passes the separability gate**. `ASS` co-primary readouts (expectancy CI_low, median
  CI_low, tail diagnostic) are **disclosures that inform interpretation and the separability argument**,
  not binding legs. Thresholds calibrated/data-derived, not magic numbers (§5.3).
- **Endpoint:** overall **expectancy** (risk-aware; `SIZE-VOLADJ` tested vs raw-return baseline), read
  jointly with median + tail so the CF-HA-HARAMI-001 mean/median split cannot recur undetected.

## 6. D0 items to decide when Phase 018 opens

- Confirm EXP-IDs and per-variant slot budget; register each derived/benchmark exit variant.
- Fix the mechanical exit-derivation rule(s) for EXP-082 (freeze before EXP-081 results inform them
  beyond the predeclared mechanical mapping).
- Fix the separability-gate operational test (now the binding shape-guard — §8) and the G-018 verdict
  conjunction thresholds (calibrated), with the frozen suite as the binding legs.
- Re-evaluate the **EURUSD** TEST eligibility on the disjoint 5-year dataset (old-dataset
  contamination does not mechanically transfer — INFR-003 §4.3).
- **`ASS`-discovery sample-size bracket re-confirmation (Phase 017 §7.1):** confirm every (substrate ×
  instrument × domain) cell's realized 5-year event count falls **inside the validated synthetic span
  `[15, 8000]`** (and that the moving-block FPR holds on a 5-year null slice). Inside the bracket → `ASS`
  discovery readouts are trustworthy in their validated regime. Any out-of-bracket cell → `ASS` discovery
  excluded for that cell with disclosure, or a scoped addendum (own EXP-ID) extends the synthetic span —
  **not** a Phase 017 re-run. (Binding adjudication is the frozen suite regardless.)
- Confirm the `WF-EXPANDING` parameters as validated in Phase 017 (re-anchor if EXP-077 changed them).
- cTrader parity plan: no parity exists yet for the harami entry; parity is a post-screen gate.

## 7. Phase-017 carry-forward (binding into this phase's D0)

From the G-017 review (§5) and the Phase 017 retrospective — register at D0, do not re-derive:

- **Guard (i):** when `ASS` discovery readouts are used, **defer expectancy reads to the median at
  effective-n ≤ 60** on bimodal/asymmetric mean-null strata under `WF-EXPANDING` (the 5-fold split
  lowers effective per-fold count; mean-null under-coverage persists to n=60).
- **Guard (ii):** treat the `P(>X)` calibration **slope** sub-gate as **inapplicable at compressed
  predicted-probability span** (e.g. ptp < ~0.1) — bind on max-gap there.
- **`ASS` shape blind spot:** `ASS`'s tail diagnostic catches gross bimodality / strong left-skew but is
  **structurally blind to the subtle median-positive minority-catastrophe shape**. It must **not** be
  relied on as a tail/shape guard; the binding shape-guard is the separability gate + the frozen suite
  (§8).
- **Operating-point floors:** clean-unimodal false-flag controlled only at **n ≥ 60**; the shrunk
  edge-call FPR is **`k`-fragile** (treat `k` as load-bearing, never assume robustness).
- **Re-validation path (optional, operator's call — not initiated):** a future **EXP-079** could lift
  `ASS` to binding under conditions C1–C4 (dependent-DGP moving-block coverage; D2.4 reliability binding
  on real TRAIN folds; carry the guards + load-bearing `k`; honor the bracket) **plus** a shape leg that
  sees the minority-catastrophe shape. Until then `ASS` stays discovery-only here.

## 8. Why the separability gate — not `ASS` — is the binding shape-guard (G-017 consequence)

The deepest Phase-017 finding is that the one diagnostic built to catch the CF-HA-HARAMI-001 failure
shape (a dominant median-positive mode hiding a small catastrophic minority mode) **cannot see it** at
the frozen operating point. A verdict leaning on `ASS`'s tail leg would therefore re-admit exactly the
shape that killed the prior family. Phase 018 closes this by construction:

1. **The frozen referee suite is binding** — its independent gate legs (materiality, standalone
   significance, portfolio fitness, event-level calibration) do not share `ASS`'s blind spot.
2. **The separability gate is the explicit shape-guard** — it requires showing the net-expectancy edge
   and the favourable signal are not one unfilterable mechanism, which is precisely the "is the mean
   propped up by a structure that will collapse?" question `ASS`'s tail leg failed to answer.
3. **`ASS` median + tail readouts are disclosure inputs to that argument**, surfacing bimodality where
   they *can* see it (gross cases) and never being trusted where they cannot (subtle cases). EXP-081's
   return-structure characterization should add a **minority-mass / left-tail-mass read** (the detector
   `ASS` lacks) as a descriptive companion, so the subtle shape is visible to the human/separability
   argument even though it is invisible to `ASS`'s frozen legs.

## 9. Guardrails (carried)

- 0 TEST reads until the separability gate passes; counted reads via the D4.1 rule only.
- No entry tuning (entries frozen); only exit/capture geometry + sizing explored.
- No substrate pooling without demonstrated homogeneity; per-stratum default (LESSON-001).
- Real-price returns only; holdout never loaded or made a fold; determinism (fixed seeds).
- No post-result cell/variant selection; the surface and rules are fixed at D0.
- `ASS` is discovery-only; no binding decision rests on it (G-017).

---

*Companion: family spec
[`../../../signal-registry/candidate-families/cf-capgeo-001.md`](../../../signal-registry/candidate-families/cf-capgeo-001.md);
Phase 017 (qualifier/protocol) [`../2026-06-20-017-capgeo-qualifier-validation/design.md`](../2026-06-20-017-capgeo-qualifier-validation/design.md)
+ [`G-017-gate-review.md`](../2026-06-20-017-capgeo-qualifier-validation/G-017-gate-review.md)
+ [`retrospective.md`](../2026-06-20-017-capgeo-qualifier-validation/retrospective.md);
INFR-003 (data) [`../2026-06-20-INFR-003-five-year-data-upgrade/design.md`](../2026-06-20-INFR-003-five-year-data-upgrade/design.md);
multiplicity Phase 018 batch
[`../../../signal-registry/multiplicity-registry.md`](../../../signal-registry/multiplicity-registry.md).*
