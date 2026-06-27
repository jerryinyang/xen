# Phase 018 D0 — Predeclarations (CF-CAPGEO-001: Data-Derived Exit / Capture Geometry)

**Status:** **RATIFIED — G0 PASS 2026-06-21 (operator-ratified).** All G0 gate items closed: both
opening preconditions met (G-017 `DISCOVERY_ONLY`; INFR-003 COMPLETE ∧ VAL-005 PASS), D2/D8 operator
decisions ratified, and the **D9 bite-check GREEN** with the D4/D9 separability constants FROZEN
(`K_tail=3.0, τ_tail=0.06, δ=0.40, m=m_cell`, operating floor `n≥120`; `B_pos` blind spot dispositioned
as economically benign). **Phase 018 is OPEN; the pipeline opens at EXP-080** (HYP-001 readiness — 0
slots, 0 TEST reads). The frozen derivation rule (D3), separability gate (D4), WF protocol (D5), and
gate thresholds are locked; no post-result cell/variant selection. *(Prior status: DRAFT — candidate
values populated; D9 bite-check GREEN awaiting ratification.)* Both opening preconditions are met (G-017
`DISCOVERY_ONLY` 2026-06-21; INFR-003 COMPLETE ∧ VAL-005 PASS 2026-06-21). **Both operator decisions are RATIFIED 2026-06-21** (D2: no per-variant
rationing — TRAIN gates select, all valid candidates batched into one read per stratum; D8 EURUSD =
fully eligible, clean slate). The last remaining G0 gate item — the **D9 bite-check** of the D4
separability thresholds (`τ_tail`, `δ`, S1 margin `m`) and the D3 derivation-quantile estimability — is
**GREEN (all four checks `OK`, 2026-06-21)**: thresholds calibrated (neither vacuous nor impossible) and
FROZEN at `K_tail=3.0, τ_tail=0.06, δ=0.40, m=m_cell`, operating floor `n≥120` (see §D4/§D9). No
result-producing screening code (EXP-080→) and no TEST contact are authorized until this D0 is **ratified
G0 by the operator**; the bite-check precondition is now satisfied.

**Checkpoint:** `2026-06-20-018-capgeo-exit-geometry`
**Governing design:** `design.md` (this directory).
**Family:** `CF-CAPGEO-001` (REGISTERED, SCREENING-UNBLOCKED 2026-06-21).
**Binding qualifier:** the **frozen referee suite** (G-017 `DISCOVERY_ONLY`); `ASS` is a **non-binding
discovery overlay** — expectancy/median/tail reported alongside every read, no decision rests on it.
**Discipline (binding throughout Phase 018):** all return/expectancy/capture metrics on **real prices**
(`RealOpen/High/Low/Close`); HA/Renko brick prices never for P&L; timestamp alignment never bar-index;
per-stratum adjudication default (no pooling without demonstrated homogeneity — LESSON-001); the
final-30% global holdout is never loaded and never a WF fold.

---

## D1 — Substrates, universe, data (frozen)

- **Entry substrates (frozen, never tuned):** `SUB-AVWAP` (CF-AVWAP-001 final), `SUB-HARAMI-PARTIAL-V2A`
  and `SUB-HARAMI-V2A-ADVNONE` (CF-HA-HARAMI-001 finals), `SUB-RANDOM` (matched-control, seed fixed at
  D2). Entries carry the event only; their prior exits are benchmark arms (D2), not the family's frozen
  exit.
- **Universe:** **16 instruments** — the VAL-003 universe **minus DE30** (dropped at INFR-003 §3.1;
  broker m1 stale). *(Amends the Phase 018 multiplicity batch's "all 17" — see D2; removes one
  instrument, consumes no new slot.)*
- **Domains:** 15m, 1h, 4h.
- **Data:** the VAL-005-admitted 5-year dataset (2021-06-02 → 2026-06-21; first-70% analysis slice only;
  new final-30% holdout sealed, 0 rows read). **Domain construction:** holdout-fenced `build_domain_bars`
  (`min_coverage=0.90` + drop any window whose label crosses the analysis-slice boundary — VAL-005 G1).
- **Substrates never pooled** without a demonstrated-homogeneity claim; per-stratum adjudication default.

## D2 — Slate, EXP-IDs, candidate items & TEST-read accounting

**Slate (EXP-IDs confirmed; next free after Phase 017 = EXP-080):**

| EXP | HYP | Role | Slots / TEST |
| --- | --- | --- | --- |
| EXP-080 | HYP-001 | Substrate/exit **readiness** (G0-equivalent): all 4 substrates deterministic, look-ahead-safe, adequate per-cell coverage on 5-year × {15m,1h,4h}; `SUB-RANDOM` seed fixed; holdout fence verified. **Also emits the D7 `[15,8000]` bracket re-confirmation** (realized per-cell event counts). | 0 / 0 |
| EXP-081 | HYP-002 | **Characterize** (TRAIN-only, gross): per-substrate return-structure features (D3 inputs) + the **minority-mass / left-tail-mass descriptive read** (the detector `ASS` lacks). | 0 / 0 |
| EXP-082 | HYP-003 | **Derive** exits via the frozen D3 mechanical rule (D1/D2/D3 derived candidates). | 0 / 0 |
| EXP-083 | HYP-004 | **Test all TRAIN-valid candidates** (derived + benchmark survivors of G-018a + separability) under the frozen referee suite (binding) with the D4 G-018 conjunction, in one frozen pre-declared WF run. | **1 counted read per stratum** (all valid candidates batched; Holm across the {candidate × stratum} grid; 2-lifetime cap) |

(Conditional cost-aware / portfolio follow-ups register at their own D0 only on a confirmed EXP-083
result — Phase 016 EXP-072/073 precedent.)

**Registered exit/sizing branches (already in the multiplicity registry, Phase 018 batch):**
`/EXIT-DERIVED`, `/EXIT-RR`, `/EXIT-TRAIL`, `/EXIT-VP`, `/EXIT-PARTIAL`, `/SIZE-VOLADJ` (`/MTF`,
`/VOLREGIME` deferred).

**Derived candidates registered at this D0 (countable items under `/EXIT-DERIVED`):** `D1-MEDIAN-CAPTURE`,
`D2-TAIL-ROBUST`, `D3-CAPTURE-EFFICIENT` (defined in D3). Benchmark arms under the registered branches:
`/EXIT-RR` (fixed favourable/adverse RR), `/EXIT-TRAIL` (market-structure/price trailing), `/EXIT-VP`
(volume-profile POC/value-area; `TickVolume` proxy disclosed), `/EXIT-PARTIAL` (splits, incl. named
reference arms PARTIAL-V2A, V2A-ADVNONE, AVWAP-FH), `/SIZE-VOLADJ` (vs raw-return baseline).

> **D2 — RATIFIED 2026-06-21: no per-variant rationing; TRAIN validity is the only filter.** There is
> **no "slot budget" choosing which ideas get tested.** The design is:
> 1. **Everything is screened on TRAIN first** — all exit ideas (the 3 derived candidates D1/D2/D3 **and**
>    every registered conventional benchmark) run the cheap gross screen (G-018a) and the separability
>    gate (D4) on training data only. No TEST contact.
> 2. **Surviving both TRAIN gates ⇒ "valid candidate."** That screening *is* the selection; nothing is
>    pre-excluded by fiat.
> 3. **All valid candidates are evaluated together in ONE frozen, pre-declared WF confirmation experiment
>    (EXP-083); each stratum is touched exactly once = ONE counted TEST read** (D4.1). Multiplicity across
>    candidates is handled by a **pre-declared correction — Holm across the full {valid-candidate ×
>    stratum} grid** — not by picking favorites.
>
> **Legitimacy condition (D4.1, binding):** the valid-candidate set **and** the Holm correction rule are
> **frozen and hash-pinned before any TEST row is read.** No human selects among candidates after seeing
> TEST — that is what makes "many candidates, one read" one honest look rather than many. The
> **2-lifetime-read cap per stratum still governs**: EXP-083 spends the 1st read; at most one follow-up
> confirmation could spend the 2nd.

## D3 — EXP-082 mechanical exit-derivation rule (frozen — "freeze the rule, not the story")

**Inputs — EXP-081 TRAIN-only per-cell statistics** (realized post-entry path of each frozen-entry
event; real prices; per-event ATR-normalized):

| Symbol | Statistic | Method |
| --- | --- | --- |
| `MFE_med`, `MFE_q40` | median / q40 lifetime MFE (ATR) | quantile |
| `TTP_med`, `TTP_q75` | median / q75 bars-to-peak-MFE | quantile (capture-time geometry) |
| `MAE_q90` | q90 lifetime MAE (ATR) | quantile |
| `m_anti` | antimode/dip location of the MAE distribution (dominant-vs-catastrophic-minority boundary); `NaN` if unimodal | Hartigan dip + 2-component robust split |
| `tailmass`, `q05` | left-tail-mass (fraction below the catastrophe threshold) and q05 outcome | the **minority-mass detector `ASS` lacks** |

**Rule — triple-barrier exit, barriers ARE measured quantiles (no grid search):**

| Candidate (countable item) | `T_fav` | `S_adv` | `H_cap` | Tests |
| --- | --- | --- | --- | --- |
| `D1-MEDIAN-CAPTURE` | `MFE_med` | `m_anti` else `MAE_q90` | `TTP_q75` | central favourable capture |
| `D2-TAIL-ROBUST` | `MFE_med` | `m_anti` (tightened to the dip; unimodal → `MAE_q90`) | `TTP_q75` | does cutting the minority tail help net expectancy? |
| `D3-CAPTURE-EFFICIENT` | `MFE_q40` | `m_anti` else `MAE_q90` | `TTP_med` | does an earlier/higher-hit target capture more? |

- **Adverse leg is left-tail-parameterized, not a symmetric mirror** — every candidate's own stop must
  engage the catastrophic-minority boundary (`m_anti`). This is the structural guard against the
  CF-HA-HARAMI-001 "harvest the median, leave the catastrophe" trap.
- **EXP-042 guard (binding):** `(T_fav, S_adv, H_cap)` are **exit** barriers on the *held position* of
  frozen-entry events. **None filters, selects, or alters the entry event population**; every candidate
  is evaluated on the identical frozen-substrate event set (no denominator change).
- **Causality / WF re-fit:** within a WF fold the three barriers are computed from that fold's **TRAIN
  portion only**, then applied causally to the test fold — the pre-declared mechanical re-fit satisfying
  D5/D4.1(2) (no human selection between folds; whole WF run = one counted read).
- **No human selection** between the EXP-081 feature read and the EXP-082 exit: the mapping above is the
  entire rule. The narrative EXP-081 produces is not predeclared; the rule is.

## D4 — Separability gate (binding pre-TEST shape-guard) + G-018 verdict conjunction (frozen)

**Separability gate — two legs, both must pass, on TRAIN, before any counted TEST read:**

- **(S1) Attribution separability** — *the obstacle moves without moving the edge.* Decompose each
  candidate's net expectancy additively (EXP-031 precedent, additive to machine precision) into `X_fav`
  (favourable-target + time-cap contribution; adverse leg at a neutral reference) and `X_tail`
  (stop-truncation contribution). **PASS iff `X_fav` independently beats the per-cell matched-random
  control** (moving-block bootstrap, `CI_low > m` on the matched-control difference). Edge that is
  entirely `X_tail` with `X_fav ≈` matched-random is a capture-bound/tail-truncation artifact → FAIL.
- **(S2) Tail non-residual (the detector `ASS` lacks, made binding)** — after the candidate's exit is
  applied, re-measure the candidate's **own** realized distribution. **PASS iff** post-exit
  `tailmass ≤ τ_tail` **AND** post-exit `q05 ≥ q05_control − δ` (the candidate's tail is no worse than
  its matched-random control's). A positive-net candidate that still carries a catastrophic minority mode
  FAILS — exactly the EXP-078 blind spot, made binding here. **`tailmass` = fraction of mass below the
  catastrophe boundary `median − K_tail·MAD`** (the separated minority mode, not the bulk's shoulder).
  **Frozen at the D9 bite-check (GREEN 2026-06-21): `K_tail = 3.0`, `τ_tail = 0.06`, `δ = 0.40` ATR**;
  the two legs are complementary (tailmass catches `B_zero`'s separated mode, relative-q05 catches deep
  `B_neg` catastrophes). **Operating floor `n ≥ 120`** (S2 reliable only at n ≥ 120; cells below the
  floor — some 4h cells — get S2 **deferred + disclosed**, adjudication carried by the frozen referee
  suite + median/tail disclosure). Residual `B_pos` blind spot disclosed (see D9).

**G-018 terminal verdict — candidate CONFIRMS iff ALL:**
1. **Frozen referee suite PASS** on the aggregate WF verdict (materiality / standalone significance /
   portfolio fitness / event-level calibration — EXP-003/012/018 + EXP-027/070-analog), per stratum;
2. **Beats `SUB-RANDOM` / per-cell matched-random** (`CI_low > 0`, moving-block bootstrap);
3. **Separability gate (S1 ∧ S2) PASS** on TRAIN.

`ASS` expectancy/median/tail are **disclosures** reported alongside every read; no binding leg rests on
`ASS`. Endpoint: overall **expectancy** (risk-aware; `SIZE-VOLADJ` tested vs raw-return baseline), read
jointly with median + the S2 tail diagnostic so the CF-HA-HARAMI-001 mean/median split cannot recur
undetected. Methods are non-parametric / bootstrap / matched-control throughout.

## D5 — `WF-EXPANDING` protocol (re-anchored from Phase 017 — validated, unchanged)

Per Phase 017 D4 (validated 8/8 under EXP-077): initial train = first 0.50 of the analysis set; 5
expanding folds of 0.10, each rolled into the next train; min fold size ≥ 30 events (below-floor folds
disclosed, not dropped); fold-clustered moving-block bootstrap → exactly one verdict per stratum.
**D4.1 counted-read rule (binding):** one frozen pre-declared WF run = one counted TEST read; folds are
in-protocol disclosures; freeze-before-OOS + hash-pin + no between-fold human selection + holdout never a
fold. ≤ 2 WF runs lifetime per stratum. (No re-anchoring needed — EXP-077 did not change the schedule.)

## D6 — Carry-forward guards (§7; registered verbatim, binding)

- **Guard (i):** when `ASS` discovery readouts are used, defer expectancy reads to the **median at
  effective-n ≤ 60** on bimodal/asymmetric mean-null strata under `WF-EXPANDING`.
- **Guard (ii):** treat the `P(>X)` calibration **slope** sub-gate as inapplicable at compressed
  predicted-probability span (ptp < ~0.1) — bind on **max-gap** there.
- **`ASS` shape blind spot:** `ASS`'s tail diagnostic is **never** the tail/shape guard; the binding
  shape-guard is the D4 separability gate (S2) + the frozen suite.
- **Operating-point floors:** clean-unimodal false-flag controlled only at **n ≥ 60**; the shrunk
  edge-call FPR is **`k`-fragile** — treat `k` as load-bearing, disclose `ASS` reads across the `k`-grid,
  never assume robustness.

## D7 — `ASS`-discovery sample-size bracket re-confirmation (EXP-080 output)

EXP-080 records each (substrate × instrument × domain) cell's realized 5-year event count and confirms
it falls **inside the Phase-017-validated synthetic span `[15, 8000]`** (and that moving-block FPR holds
on a 5-year null slice). Inside the bracket → `ASS` discovery readouts are trustworthy in their validated
regime. Any out-of-bracket cell → `ASS` discovery **excluded for that cell with disclosure**, or a scoped
addendum (own EXP-ID) extends the synthetic span — **not** a Phase 017 re-run. Binding adjudication is the
frozen suite regardless.

## D8 — EURUSD TEST eligibility on the 5-year dataset

> **D8 — RATIFIED 2026-06-21: EURUSD ELIGIBLE, clean slate (no carried disclosure).** EURUSD was
> TEST-capped instrument-wide on the **old** dataset (holdout-contaminated via EXP-032, EURUSD-4h). On the
> disjoint 5-year dataset the contamination does **not transfer** (INFR-003 §4.3): the new strata are
> disjoint rows with a 0-read re-materialized ledger. **EURUSD-{15m,1h,4h} new-dataset strata are fully
> eligible** for stratum-specific counted TEST reads, on the same footing as every other instrument —
> **no carried disclosure.** EXP-032 is old enough, and the programme's methodology has evolved
> sufficiently, that it carries no weight on the new dataset.

## D9 — G0 bite-check plan (thresholds to calibrate before ratification)

Mirrors Phase 017 D2: each candidate threshold is confirmed **neither vacuous nor impossible** on
synthetic + TRAIN fixtures, then frozen; re-anchor failures in a dated `D0-amendment-*`.

- **`τ_tail`, `δ` (D4 S2):** set so a **known-separable** fixture (unimodal-positive) PASSES and a
  **known-harami** fixture (Phase-017 `B_zero`/`B_neg` minority-catastrophe shapes) FAILS S2. ROC on the
  separable-vs-harami fixtures, operating point at false-flag ≤ 0.05 / detection ≥ 0.80 (the D2.5 analog,
  using minority-**mass** not the mean–median gap).
- **S1 margin `m` (D4 S1):** the synthetic-null-calibrated margin driving the `X_fav` matched-control
  edge-call FPR ≤ 0.05 (Wilson-hi ≤ 0.075) — the `m_cell` standard (EXP-027/070).
- **Derivation-quantile sanity (D3):** confirm `MFE_med`/`MFE_q40`/`TTP_q75`/`MAE_q90`/`m_anti` are
  estimable (non-degenerate) at the ≥ 30-event floor on a TRAIN fixture; cells below floor → disclosed,
  derived candidate not formed for that cell.

> **D9 — BITE CHECK GREEN 2026-06-21 (all four checks `OK`; recommended for G0 freeze).** Tooling +
> spec: [`bite-check/bite_check.py`](bite-check/bite_check.py) ·
> [`bite-check/bite-check.md`](bite-check/bite-check.md) ·
> [`bite-check/bite_check_report.json`](bite-check/bite_check_report.json) (deterministic,
> `SEED=20260621`, byte-identical on re-run; `bite_check.py` sha256
> `35d6351820072bc132068333d89ecd90fa6bbfc89f8f6be7b554ecb4bd0eddcc`).
>
> **Frozen values (calibrated, not magic numbers — §5.3):**
> - **S2:** `K_tail = 3.0` (catastrophe boundary `median − 3·MAD`), **`τ_tail = 0.06`**, **`δ = 0.40`
>   ATR**. @n=250: separable false-flag **0.006** (Wilson-hi 0.009); binding detection **`B_neg`=1.000,
>   `B_zero`=0.913**; disclosed `B_strong`=1.000, `B_pos`=0.056. The two legs are complementary
>   (tailmass→`B_zero`, relative-q05→`B_neg`); S2 detects if either trips.
> - **S2 operating floor:** **`n ≥ 120`** (binds on Wilson-hi(false-flag) ≤ 0.075 at n=120: ff 0.040,
>   Wilson-hi 0.048, det `B_neg`=0.997/`B_zero`=0.805). **Infeasible at n=60** (ff 0.147, Wilson-hi
>   0.160) → **S2 deferred + disclosed for sub-floor cells** (some 4h cells); adjudication carried by
>   the frozen referee suite (binding regardless) + median/tail disclosure.
> - **S1:** bind `X_fav CI_low > m_cell` with **`m_cell = Q95(null CI_low)`** (per-cell); calibrated
>   FPR **0.050** (Wilson-hi 0.058), `m_cell` finite/non-degenerate. Recomputed per realized structure
>   in EXP-083 at `N_BOOT = 10_000`.
> - **D3:** quantiles `MFE_med/MFE_q40/TTP_q75/MAE_q90` estimable at the n≥30 floor (non-estimable
>   **0.000**); the adverse leg `m_anti else MAE_q90` is always well-defined (undefined **0.000**).
>
> **Disclosed limitations (binding into EXP-082/083):**
> 1. **`B_pos` blind spot persists but is economically benign — DISPOSITION: accept, do not tune.**
>    Detection 0.056 at n=250 (mirrors EXP-078). The `bpos_harm_visibility_map` disclosure (in the
>    report JSON) sweeps the minority (mass × depth) plane and proves the blind region and the harm
>    region are **anti-correlated**: every blind cell with a real tail has true mean > 0 (benign);
>    every materially-negative-mean shape (the median+/expectancy-dead trap) is DETECTED (det
>    0.90–1.00); the single "blind+harmful" cell (`w=0.05, depth=−3.0`) has mean −0.008 (break-even,
>    rejected by the frozen suite's expectancy leg) and is still caught 55% of the time. Lowering
>    `K_tail` cannot recover `B_pos` (intrinsic separability is tiny). **Closed by three backstops
>    already in the design:** the frozen referee suite (binding on expectancy), the S1 attribution leg
>    (orthogonal to tail shape), and the EXP-081 per-cell descriptive minority-mass read. Optional
>    EXP-079 shape-leg upgrade is the escape hatch — only if a real suite-passing `B_pos` candidate
>    with a concerning tail appears.
> 2. **`m_anti` is power-limited** (dip-resolution finite-rate ~0.02/0.45/0.95 at n=30/250/500) → the
>    D3 adverse leg predominantly uses the **MAE_q90 fallback** at realistic cell sizes; `m_anti`
>    engages only in large-n cells. Does **not** weaken S2 (which uses minority-mass, not the dip).
>
> **Re-anchor recorded:** the D3 sub-requirement "`m_anti` finite on bimodal at n=30" was **impossible**
> (dip underpowered at small n — EXP-078) and is handled by the `m_anti else MAE_q90` fallback;
> re-anchored to the binding requirement (quantiles estimable at n≥30 + rule always well-defined), which
> passes. No `D0-amendment-*` needed (re-anchor is to a sub-requirement of the bite plan, not a frozen
> design constant). **This is the last open G0 gate item per the status header — bite-check GREEN clears
> it pending operator G0 ratification.**

## D10 — Determinism & real-price discipline

- All RNG seeds fixed and recorded; a second full pass of every experiment is byte-identical.
- All return/expectancy/capture/P&L on **real prices**; no HA/Renko brick-price returns anywhere.
- No tuning against any TEST or holdout data; the derivation rule and gate thresholds frozen at G0.

## Slot & TEST accounting (at D0)

- **0 candidate slots and 0 counted TEST reads** consumed by this D0. Counted reads are spent only at
  EXP-083, on the new 5-year strata, **after** the TRAIN gates (G-018a + separability) select the valid
  candidates, via the D4.1 rule: **all valid candidates batched into one frozen WF run per stratum = one
  counted read** (Holm across the {valid-candidate × stratum} grid; candidate set + correction hash-pinned
  before any TEST row; 2-lifetime cap).
- Ledger: re-materialized on the new 16×{15m,1h,4h} strata (all 0 counted reads); EURUSD fully eligible
  (D8, clean slate).
- Holdout sealed throughout; never a WF fold.

---

*Companion: Phase 018 design [`design.md`](design.md); G-017 review
[`../2026-06-20-017-capgeo-qualifier-validation/G-017-gate-review.md`]; Phase 017 D0
[`../2026-06-20-017-capgeo-qualifier-validation/D0-predeclarations.md`]; family spec
[`../../../signal-registry/candidate-families/cf-capgeo-001.md`]; VAL-005 report
[`../../../../python/experiments/VAL-005/report.md`].*
