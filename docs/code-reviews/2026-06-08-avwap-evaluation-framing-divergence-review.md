# AVWAP Evaluation-Framing Divergence: Critical Review

**Date:** 2026-06-08
**Type:** Governance / methodology review (research-pipeline Stage 4/8 class).
**Scope:** The CF-AVWAP-001 baseline chain EXP-020 → EXP-025, with focus on the
evaluation vehicle introduced at EXP-023 and inherited by EXP-024/025.
**Companion:** `docs/code-reviews/2026-06-08-avwap-original-vs-experiment-gaps.md`
(original-concept vs. shipped-implementation gaps). This review extends gap #4
(S/R never tested directly) and gap #5 (risk-adjusted/equity-curve metric never
built) into a single root cause: **the evaluation vehicle, not the strategy.**
**Consequence:** Phase 005 halted; correction checkpoint 006 opened
(`docs/experiments-docs/checkpoints/2026-06-08-006-avwap-evaluation-correction/design.md`).

---

## 1. One-line finding

A ~2–3 % prevalence (≈6 % active-bar) **event signal** was screened and diagnosed
through a **per-bar continuous-position referee** (the frozen qualification suite)
whose operating characteristics were calibrated and validated only for
**high-activity (≥80 % active)** position series. The negative results of EXP-023,
the fork-(b) leg of EXP-024, and EXP-025 are dominated by this mismatch, not by an
absence of signal. The strategy *position rule* was largely faithful; the
**yardstick** was not.

## 2. The lineage and the divergence point

| Stage | Estimand | Faithful to original concept? |
| --- | --- | --- |
| Original `anchored-vwap.md` (HYP-002) | **Per-event**: bounce expectancy, win rate, equity-curve risk-adjusted return vs. buy-hold, prevalence | — (this is the spec) |
| EXP-021 (bounce reaction vs. matched control) | Per-event excess reaction | ✅ = "bounce expectancy" |
| EXP-022 (lifetime completion vs. control) | Per-event completion-rate difference | ✅ = "successful bounce rate" |
| **EXP-023 (baseline candidate screen)** | **Per-bar continuous position** vs. a per-bar MDE floor | ❌ — new vehicle |

EXP-020/021/022 measured **per-event** quantities and map cleanly onto the
original metric book. EXP-023 changed the unit of analysis to a **per-bar mean
over the entire chronological series** (flat bars contributing zero) and compared
it to a **per-bar MDE floor** drawn from the frozen suite. That is the divergence.

Important precision: EXP-023's *position rule* (flat → enter on confirmed bounce →
hold to EXP-022 completion → flat → wait) is itself ~faithful to HYP-002. The only
minor deviation is suppressing pyramids while in a position. **The infidelity is
in the evaluation/metric, not the trade logic.**

## 3. Why the evaluation vehicle is the wrong yardstick

### 3.1 Out-of-calibration application of the frozen suite

The frozen suite's FPR/TPR/MDE map was calibrated in EXP-003 and validated in
EXP-005. EXP-005's "realistic candidate" had **`p_active = 0.80`** — an
80 %-of-bars-active position series. EXP-023 applied the same floors to a signal
active **~6 % of bars** (EXP-024: 6.17 % / 5.73 % / 5.67 % active; prevalence
2.68 % / 2.26 % / 2.21 %). The detection guarantee does not transfer across a
>13× activity gap; the floor's meaning for a sparse signal was never established.

### 3.2 The mechanical dilution

A per-bar mean is roughly the per-event edge attenuated by the active fraction. At
~6 % active, that is on the order of a **~16× per-bar haircut** relative to the
per-event magnitude. EXP-021's +3.8 / +9.1 / +37.6 bps *per-event* reaction
landing at EXP-023's −0.56 to +0.14 bps *gross per-bar* model means is exactly
what that attenuation predicts. The Phase 004 provenance read this as "the edge
dissipates before cost"; a large part of that "dissipation" is **denominator
dilution**, not edge decay.

### 3.3 The original's own metric was abandoned

`anchored-vwap.md` specifies the headline metric as bounce expectancy plus the
**risk-adjusted return of the model's return *series* vs. raw price returns** — an
equity-curve comparison, i.e. a per-event / per-trade-aggregated object. Per gap
#5 this was never built; it was replaced wholesale by the per-bar MDE suite.

## 4. Per-experiment dispositions (supersede + retain — no erasure)

The computations are not buggy; the **interpretations** are. Records are retained
in the file-drawer ledger; only the conclusions are corrected.

### EXP-023 — SUPERSEDED (framing-corrected)
- Results are *correct as a per-bar continuous-position screen* — the per-bar
  effects genuinely sit below the per-bar floors.
- They do **not** constitute a tradability test of the original selective event
  vehicle. "REFUTED — did not qualify as a cost-bearing tradable strategy" cannot
  bear that weight.
- Superseded by the EXP-028 faithful redo under a fit-for-purpose evaluation.
- **Severity: HIGH.** Governance should have flagged the activity-envelope
  mismatch at the EXP-023 Stage 4 pre-execution review.

### EXP-024 — RETAINED, fork leg discounted
- The fork-(b) leg compares a **cumulative multi-bar per-event hold return**
  against a **per-bar floor** (e.g. 5m `g*`=+0.370 bps cumulative over a 16-bar
  hold ≈ 0.02 bps/bar vs. a 0.5 bps/bar floor). That comparison is a category
  mismatch and makes fork (b) close to foreordained — **low-information as a fork
  verdict.**
- Two findings are **genuinely valid and decision-relevant and are retained**:
  1. **The edge is relative, not absolute.** EXP-021's +3.8 bps was excess over
     controls; the *raw* directional hold return is ~0. Events fall *less than*
     controls but do not actually rise.
  2. **Trend-change exits cut losers, not winners** (−2.79 / −8.76 / −17.59 bps;
     54–66 % negative), directly falsifying the "holding too long gives back
     winners" exit-repair story.
- **Severity: MODERATE.** Fork apparatus mis-yardsticked; side findings stand.

### EXP-025 — INCONCLUSIVE retained, annotated non-informative for HYP-001
- The metric **conflates the trigger definition with the line-rejection signal**:
  a bounce trigger by definition crosses AVWAP intrabar, so events mechanically
  carry higher adverse penetration than non-crossing controls. The metric was
  structurally biased to a negative result before any data was seen (the report's
  own limitations section concedes this).
- It also redefined the original's **forward** "reaction" concept as a
  **contemporaneous intrabar** wick score at `h=0` — a deviation, and the one
  quantity guaranteed to be confounded.
- **HYP-001 (does price respect the AVWAP line as S/R) therefore remains
  untested.** EXP-025 carries **zero weight** in the Stage A synthesis; reading it
  as evidence the line is *not* S/R would be wrong.
- **Severity: MODERATE-to-HIGH** — a scarce diagnostic slot spent on a metric that
  could not answer the question; the foundational thesis is still open.

## 5. The honest counter-argument (steelman of the existing approach)

The frozen suite exists to prevent **metric-shopping / garden-of-forking-paths**;
the entire Phase 001–003 investment was to make qualification adversarially
honest. Letting every signal define its own bespoke metric and floor reopens that
risk. A per-event expectancy metric is *more natural* here but is currently
**uncalibrated** (no FPR/TPR/MDE map, no validated null). The resolution is **not**
"abandon the suite." It is: the suite has **no calibrated operating mode for
sparse event signals**, and until one exists, its negative verdict on a ~6 %-active
signal cannot be read as "no tradable edge."

## 6. What is actually at risk

The danger is interpretive. The **correct** reading of the halted Stage A is:

> The AVWAP event edge (EXP-021/022 supported) does not express as tradable
> per-bar edge under a continuous-position frozen-suite framing the suite was
> never calibrated for; whether a *selective* event vehicle with proper
> event-level evaluation works is **untested**; HYP-001 is **untested**.

The **overreach to avoid**:

> Stage A came back weak → AVWAP is probably dead → move on.

That would discard a signal with supported event-level evidence on the basis of a
mis-framed screen plus a confounded diagnostic. Phase 005's own
`OVERLAY_WRONG_VEHICLE` outcome anticipated this ("redirect to a non-always-on
operationalization"); this review elevates that branch to the phase's primary
correction.

## 7. Corrective direction (implemented in checkpoint 006)

1. **Fix the evaluation vehicle first.** Define and calibrate an **event-level
   evaluation method** — per-event expectancy + equity-curve-vs-buy-hold, with the
   matched-control / regime-cluster-bootstrap / Holm machinery already validated in
   EXP-021/022 as the predeclared decision rule, plus a null/control to keep
   anti-overfitting discipline. (EXP-027.)
2. **Re-screen the faithful selective strategy under that method.** The EXP-023
   position rule was ~faithful; re-evaluate it on the fit-for-purpose yardstick.
   (EXP-028.)
3. **Holdout stays sealed; no tuning; predeclared once, measured once.**
4. HYP-001 (direct line-S/R) remains open and is *not* in checkpoint 006 scope
   (operator decision: the strategy redo is the sole in-scope strategy); it is
   recorded as an open foundational question.

## 8. Status changes triggered by this review

- Phase 005 (`2026-06-08-005-avwap-exit-and-branch-exploration`) **HALTED**;
  retrospective written.
- EXP-023 → SUPERSEDED; EXP-024 → RETAINED (fork leg discounted);
  EXP-025 → INCONCLUSIVE (annotated non-informative for HYP-001). EXP-IDs and
  ledger rows retained.
- EXP-026 `/EXIT` reservation **SHELVED** (never scoped; number retired, not
  reused).
- Correction checkpoint 006 opened with EXP-027 (evaluation method) → EXP-028
  (faithful redo).
