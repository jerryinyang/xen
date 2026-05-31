# Phase 006 Mid-Phase Reflection (Post-EXP-037 Directive)

**Phase:** 006 — Thesis-Qualification Referee Calibration
**Date:** 2026-05-31
**Gate:** 9 (Reflection-before-power) — issued after the Stage A null-calibration experiment (EXP-037), before any Stage B power scope.
**Inputs:** EXP-037 (Null Calibration of Frozen Reference Stack — REFUTED, measurement-validity branch; post-experiment governance APPROVE). Companions: [`design.md`](design.md), [`reference-stack-spec.md`](reference-stack-spec.md).

**Closure note:** This directive was superseded by the Phase 006 [retrospective](retrospective.md). EXP-040 was not instantiated; Stage B remains unopened; the checkpoint is closed after EXP-037.

This document is the predeclared reflection directive required by Gate 9. Its job is **not** the one the design anticipated — it cannot fix the Stage B mechanism grouping or target the leaking gate legs, **because EXP-037 produced no trusted null/per-leg profile to target.** EXP-037 hit its predeclared *"Evidence AGAINST measurement validity"* branch: the harness is validated and faithful to EXP-036, but the predeclared κ=0 null fails its own realism diagnostics on 100% of realizations, so the trusted second-order-holdout denominator is 0 and no FPR exists.

The disciplined consequence is that the reflection issues a **dated predeclared amendment to the null construction** (the explicit `reference-stack-spec.md` §6 change-control mechanism), authorizes **one** corrected Stage-A re-run (`EXP-040`), and keeps **Stage B fully gated** until that re-run yields a trusted profile. No power scope is created here.

**Predeclaration discipline (stated up front).** Every change below is predeclared *before* any `EXP-040` code is written, with a structural, non-outcome-driven rationale. No FPR, leak rate, or verdict value was used to choose the amendment. The frozen evidentiary stack (Part 1 of the spec: admissibility + E1–E7 + the verdict ladder) is **not** touched by any clause in this document. What is amended is the **null that tests the stack** and its **realism diagnostics** — harness degrees of freedom that constraint 7 explicitly pre-registers as correctable once via §6, not the gate stack under test (constraint 13 / Gate 6).

---

## 1. What EXP-037 Established (and what it did not)

EXP-037 is recorded as **REFUTED — null-calibration invalidity**. Three facts from it drive every decision below; none of them is a property of the stack or a return value, so using them here is not test-selection.

1. **The harness measures the right object.** With `seed_index = 0` the observed-stack verdict reproduces EXP-036 field-for-field (`outcome = AGAINST`; `four_bar_neutral_and_control = {1h:[XAUUSD], 4h:[]}`; control adjudicable on all four instruments at both timeframes). The transcription is faithful, so the precondition for the whole phase holds: any FPR a *valid* null would yield belongs to the EXP-036 stack. **This is preserved as-is; `EXP-040` reuses the same harness.**

2. **The descriptor null fails realism structurally.** `DescriptorPass = 0/450`. Independent episode-block resampling (`_descriptor_indices` / `_descriptor_blocks`) draws whole episodes i.i.d. and concatenates; because the observed bucket stream is a sequence of *maximal runs* it has **zero** adjacent same-bucket episodes, but i.i.d. draws create them, and `_episode_ids` then **merges** adjacent same-bucket blocks into one episode. The result collapses the episode count by 35–56% (`descriptor_max_count_rel_diff ∈ [0.39, 0.56]`, median 0.44, tolerance 0.05) and inflates lengths (audit SC-2: a 978-episode stream → 632, median length 3→4). The diagnostic is correct; **the construction does not preserve the structure it was meant to preserve.**

3. **The return-autocorrelation gate is near-unpassable independently.** `ReturnAutocorrPass = 0/450`. `_autocorr_compare` requires **zero** sign mismatches across 64 (instrument × timeframe × segment × horizon × lag∈{1,5}) cells; raw-return lag-1/lag-5 autocorrelations are within sampling noise of zero, so their *signs* flip readily under any resample (median 12 mismatches, match rate ≈0.81, min 4). A literal "all 64 signs unchanged" gate tests noise and fails even on a perfectly reasonable return null.

What EXP-037 did **not** establish: any trustworthy operating characteristic of the stack. The untrusted raw rates (full-stack `FOR = 0/450`; cell-level control leak 4.7–6.0% vs neutral 1.0–2.0%) are **bias-suspect and explicitly not an FPR** — the merged null has fewer, longer episodes → wider bootstrap CIs → a downward-biased pass rate, and the control-leg elevation is plausibly the control's own preserved `c·r` structure rather than descriptor→return leakage. These are hypotheses for `EXP-040` to resolve, **not** inputs to a Stage B targeting decision.

**The cross-instrument return-correlation diagnostic partially held** (`CrossCorrPass` 0.21→0.36 with L), confirming the *return* block bootstrap behaves sensibly. The two failures are localized to the descriptor resampler and the autocorr-sign gate — which is exactly what the amendment targets.

---

## 2. Decision

> **A single corrected Stage-A re-run (`EXP-040`) under a predeclared, amended null is required before any Stage B power scope. Stage B (`EXP-038`/`EXP-039`) remains gated and dormant. The §5.6 ruling and the H0/H1 founding-thesis ruling both remain open, pending a trusted FPR that does not yet exist.**

This is the design's *Expected Phase Outcome #3* path held in suspense: null calibration is the trustworthy half and must be made to *work* before the fragile half (power) is touched. The amendment fixes the **method and its realism targets**; it does not relax any bar on the stack.

**Regress bound (predeclared, load-bearing).** `EXP-040` is the **one** anticipated null correction permitted by constraint 7's stopping rule. If the corrected null *also* fails its (unchanged) realism diagnostics, the phase does **not** attempt a third null. It reports that a dependence-preserving null for this descriptor/stack pair is **infeasible within the predeclared family** — itself a reportable finding bearing on H0 (a calibrator that cannot be calibrated), per honesty clause C4. This caps the infinite regress the charter warns against: we correct a demonstrable method defect once, we do not iterate a generator until a number looks right.

---

## 3. Dated Predeclared Amendment to the Null Construction

Issued under `reference-stack-spec.md` §6 ("a dated amendment in this file stating a non-outcome-driven rationale"). The full amendment text is recorded in the spec's new **Amendment Log (AM-1, 2026-05-31)**; this section is the directive and rationale. Each clause names what changes, what stays, and why the rationale is structural rather than outcome-driven.

### A1 — Descriptor resampler: first-order Markov episode-label model with empirical per-bucket durations

**Changes** spec §3 method item 1 only (the descriptor stream). **Replaces** "resampled in circular blocks whose boundaries are snapped to complete state episodes."

Per instrument × timeframe × segment:

1. Extract the ordered episode-label sequence `b₁…b_{n_ep}` (`b ∈ {bottom, middle, top}`, maximal runs ⇒ `b_{j+1} ≠ b_j` by construction) and the per-label pool of observed episode durations.
2. Estimate the first-order transition matrix `P[b→b′]` over episode labels (zero diagonal by construction — same-bucket adjacency is structurally forbidden).
3. Generate a synthetic label sequence of the **same length `n_ep`**, starting from the observed `b₁`, drawing each next label from `P` on a descriptor RNG stream **independent of the return RNG stream**.
4. Assign each synthetic episode a duration drawn with replacement from the observed duration pool **for that label**; expand `(label, duration)` to per-row buckets; truncate or pad the final episode so total rows equal the observed segment length.
5. Map bucket → `D` deterministically (top→+1, bottom→−1, middle→0), as the frozen stack does. The synthetic stream carries explicit episode boundaries; because no same-bucket adjacency is generated, the stack's `_episode_ids` snapping is a verified no-op on it.

**Realism targets — UNCHANGED, not loosened.** The descriptor diagnostic stays at episode count within ±5% (now exact by construction) and median & p90 episode length within ±10% (now matched by per-label duration resampling). We are raising the construction to clear the *existing* bar, not lowering the bar.

**What it preserves / breaks.** Preserved: episode count, per-bucket length distribution, no-same-bucket-adjacency, and marginal bucket frequencies (via the stationary distribution of `P`). Broken: the descriptor→return conditioning, because the descriptor RNG is independent of the return RNG — exactly the relationship the null must destroy.

**Rationale (non-outcome-driven).** EXP-037 Finding 2 / audit SC-2 demonstrate analytically and by live reproduction that i.i.d. episode-block draws *must* manufacture same-bucket adjacency that `_episode_ids` then merges, deterministically collapsing the count for a ~3-state stream. This is a property of the resampler, provable without running the stack or inspecting any FPR. A run-respecting generator is the minimal correct construction, not a dial toward a desired result.

### A2 — Return-autocorrelation realism gate: noise-floored sign agreement

**Changes** spec §3 diagnostics only (the return-autocorr gate). **Replaces** "return lag-1/lag-5 autocorrelation signs unchanged" (read as zero mismatches across all 64 cells).

For each (instrument × timeframe × segment × horizon × lag) cell, compute the observed autocorrelation `ρ_obs` and the white-noise band `ρ_floor = 1.96 / √N_seg` (`N_seg` = return observations in that segment). Evaluate sign agreement **only on cells with `|ρ_obs| > ρ_floor`** (above-noise, genuine autocorrelation structure) and require **zero sign mismatches among those above-floor cells**. Cells with `|ρ_obs| ≤ ρ_floor` are excluded — a sampling-zero autocorrelation has no sign to preserve. A segment with no above-floor cells is reported as "no testable autocorr structure" and does not block trust (the cross-correlation and volatility-clustering ledger entries still apply).

**Rationale (non-outcome-driven).** Preserving the sign of a statistically-zero autocorrelation is not a realism property — it is preserving noise. `z = 1.96` is the standard 95% white-noise confidence band, fixed before any run and independent of any FPR outcome. This makes the gate *correct* (it tests genuine short-range dependence, which a block bootstrap should and does preserve), not *easier on the stack* — the gate constrains the null's realism, never the stack's verdict.

### A3 — Required construct-validity sub-check on the control leg (new EXP-040 diagnostic)

Once at least one block length `L` yields a valid null, `EXP-040` must decompose `Delta_control = mean_ext((d − c)·r)` under that null into its `mean_ext(d·r)` and `mean_ext(c·r)` components per cell, to test whether the EXP-037 untrusted control-leg elevation is the control sign's **own preserved `c·r` structure** (an artefact of decoupling only `d`) or genuine descriptor→return leakage. This is a **reported diagnostic** feeding the post-`EXP-040` Stage B targeting directive, **not** a trust gate and **not** a change to E3. It resolves the one open hypothesis (EXP-037 Finding 5) before any per-leg leak is read as descriptor-conditioning leakage in Stage B.

### A4 — Compute-budget reconciliation (spec §2.4)

One Stage-A re-run is now part of the phase. EXP-037 profiled at **≈2.2 CPU-s/FSE** (`profile_summary.csv`), ~38× under the 84 CPU-s/FSE cap, so 450 FSE of Part A is ≈16 CPU-minutes; a second Part-A pass is trivially affordable in wall-clock terms. For accounting honesty (constraint 6 requires the cost be *flagged*, not silently absorbed), the Part A allowance is amended from one pass (450 FSE) to **≤ 2 passes (≤ 900 FSE)** — EXP-037 spent + the `EXP-040` re-run — raising the phase total cap from ≤1,290 to **≤ 1,740 FSE** (still ≪ the 30 CPU-hour wall-clock target: full phase ≈ 1.1 CPU-hours at the measured rate). `EXP-040` inherits the unchanged profile-first-10-FSE and downscale-to-100-realizations/block rule; no mechanism, magnitude, regime, block length, or the second-order holdout is dropped for speed.

### What is explicitly NOT changed

- **Part 1 in its entirety** — the admissibility layer, E1–E7 (floors 100/50 rows, 30/15 episodes; `Delta_neutral` vs measured `mu_mid`; naive-momentum `Delta_control`; B=10,000 episode bootstrap, seed 42; E5 sign-preservation; E6 k=2 distinct instruments; E7 4-bar secondary), and the verdict ladder. The frozen stack is byte-for-byte the EXP-036 stack. (Gate 6 / constraint 13.)
- The **κ=0 FPR definition**, adjudicability rules, and the FPR-envelope-across-valid-L headline.
- The **descriptor diagnostic tolerances** (±5% count, ±10% median/p90) and the **cross-correlation gate** (Frobenius ≤ 0.20).
- The **block-length grid** `L ∈ {20, 60, 240}`, the **150-realization** count, and the **odd-seed second-order-holdout** trust partition (§2.3).
- **§4 synthetic-effect family** (mechanisms 1–5, parameter grid, `S ≤ 2.0` H0/H1 cutoff), **§2.2 stopping rule**, **§2.1 proxy-cost/materiality regimes**. All confirmed unchanged and still in force (§5 below).

---

## 4. Stage B Status (deferred, not authorized)

Gate 9 requires the EXP-037 null/per-leg profile before Stage B scope; that profile does not exist. Therefore:

- **No Stage B scope is created by this reflection.** The directive that the design assigns to this gate — *which mechanisms earn a power experiment, how they group into IDs, which leaking legs to target, which instrument×timeframe cells and proxy-cost regimes carry forward* — is **deferred to a post-`EXP-040` reflection addendum (§7 of this file)**, issued only if `EXP-040` yields a trusted FPR + per-leg profile.
- **`EXP-038` (directional-drift power) and `EXP-039` (structural-blindness mechanisms) remain RESERVED and dormant.** No ID is reused; neither is instantiated. The reserved Stage B IDs are unchanged from `reference-stack-spec.md` §5.
- **Carried forward unchanged, pending that addendum:** the four instruments × {1h, 4h} cell set and the low/central/stress proxy-cost regimes. The synthetic-effect family (§4) and the harness stopping rule (§2.2) are re-confirmed intact — the amendment touches only the null (§3) and its diagnostics, never the planted-effect machinery.

---

## 5. Confirmation of Carried-Forward Commitments

- **Frozen stack (Part 1):** intact, untouched, canonical = EXP-036.
- **Synthetic-effect family (§4):** intact — five observable OHLC mechanisms, magnitude grid `{0.5,1,2,4}×(central κ+η)`, regime/decay/correlation axes, `S ≤ 2.0` cutoff. Re-confirmed, no change.
- **Stopping rule (§2.2):** intact — the family is run once; family-sensitivity *is* the H0/H1 finding; no generator iteration. The A1/A2 null correction is the single §6-permitted method amendment, not a relaxation of this rule.
- **Second-order holdout (§2.3):** intact — trust attaches only to odd-seed realizations; development battery labelled in-sample.
- **Economic-materiality / proxy costs (§2.1):** intact — applied as a separate survival axis in Stage B, never folded into the κ=0 stack verdict.
- **Holdout:** the final 30% global market holdout remains untouched; no clause here approaches it.

---

## 6. Gate Compliance (Phase 006 Gates 1–9)

1. **Spec-before-experiment** — satisfied: the amendment is a dated predeclared change recorded in `reference-stack-spec.md` §6 *before* any `EXP-040` scope; no `EXP-040` code exists.
2. **Species-tagging** — preserved: the null remains the trustworthy half; nothing is reclassified, no power number is reported.
3. **Admissibility-fixed** — PASS: the admissibility layer is untouched; the amendment is to null construction + realism diagnostics only.
4. **No-scalar-MDE** — N/A here (no power reported); the §4 surface/cutoff is unchanged.
5. **Second-order-holdout** — PASS: the odd-seed trusted partition is unchanged; `EXP-040` trust still attaches only to second-order-holdout realizations.
6. **Do-not-loosen** — PASS: **no evidentiary threshold or gate leg is changed.** The frozen stack is identical to EXP-036. The A2 gate change makes the *null's realism check* correct; it does not make the *stack* easier to pass — the autocorr gate constrains the null, never the verdict. Relaxation of any stack gate remains deferred to post-ruling successor design.
7. **Holdout** — PASS: the global market holdout is untouched.
8. **§5.6-measures-the-referee** — PASS: no closed thesis is re-run, re-scored, or rescued; §5.6 remains explicitly *unanswered by trusted calibration*, pending `EXP-040`.
9. **Reflection-before-power** — discharged by this directive: Stage B stays gated; only the Stage-A re-run is authorized; the power directive is deferred to the §7 addendum.

**Predeclaration check.** Both A1 and A2 rest on structural arguments (provable from the resampler/gate definitions, reproduced by EXP-037 audit SC-2) that are independent of whether the stack passes or fails. No outcome value motivated the change; the change is not "the stack kept failing" but "the null demonstrably failed to represent the real series' own structure." Honesty clause C4 stands: if the corrected null also fails realism, that is reported as a finding, not retried.

---

## 7. Assigned IDs

| ID | Status | Scope |
| --- | --- | --- |
| **EXP-040** | **Authorized** | Amended-null re-run of Stage A: the frozen EXP-036 stack calibrated under the A1 Markov episode-label descriptor null + A2 noise-floored autocorr gate, with the A3 control-leg construct-validity sub-check. Four instruments × {1h,4h}, block grid `L ∈ {20,60,240}`, 150 realizations, odd-seed second-order-holdout trust, κ=0 FPR + per-leg leak/over-reject profile. Reuses `python/src/referee_calibration.py` with the §3 amendments. |
| EXP-038 | **Reserved (dormant)** | Stage B directional-drift power. Not created; gated behind a trusted `EXP-040` profile and the §7 post-run directive. |
| EXP-039 | **Reserved (dormant)** | Stage B structural-blindness mechanisms (2–5). Not created; gated as above. |

`EXP-037` is closed (REFUTED, measurement-validity branch, post-experiment APPROVE). IDs are never reused; `EXP-038`/`EXP-039` stay attached to their reserved Stage B meaning.

---

## 8. Immediate Next Step

Record the **AM-1 dated amendment** in `reference-stack-spec.md` §6 (done with this reflection), then scope **`EXP-040`** through the research pipeline at Stage 1 against the amended spec — same harness, A1/A2 null amendments, A3 diagnostic, all frozen-stack and Stage-B commitments intact. The phase remains on its disciplined path: either `EXP-040` delivers a trusted FPR + per-leg profile (then the §7 addendum opens Stage B and the §5.6 ruling becomes answerable), or the corrected null also fails realism (then the phase reports dependence-preserving-null infeasibility for this descriptor/stack as an H0-adjacent finding, holdout intact). No Stage B scope, no gate-threshold change, and no holdout access occurs before that re-run.
