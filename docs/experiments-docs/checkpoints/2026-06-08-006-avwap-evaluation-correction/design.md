# Phase 006 — AVWAP Evaluation Correction

**Checkpoint type:** Research phase design (correction phase).
**Date finalized:** 2026-06-08.
**Status:** ACTIVE — design opened; no Phase 006 result exists.
**Candidate family:** `CF-AVWAP-001` — Anchored VWAP on regime pivots (continued
from Phases 004/005).
**Supersedes:** `2026-06-08-005-avwap-exit-and-branch-exploration` (HALTED).
**Root-cause review:**
`docs/code-reviews/2026-06-08-avwap-evaluation-framing-divergence-review.md`.

## 1. Provenance

Phases 004–005 built supported per-event evidence for the AVWAP baseline
(EXP-020 substrate, EXP-021 bounce reaction, EXP-022 lifetime completion) and then
screened/diagnosed it through the **frozen qualification suite** — a **per-bar
continuous-position referee** whose FPR/TPR/MDE map was calibrated for
**≥80 %-active** position series (EXP-005, `p_active=0.80`).

The signal is **~6 % active** (EXP-024: 6.17 / 5.73 / 5.67 % active; prevalence
2.68 / 2.26 / 2.21 %). Applying a per-bar floor to it is an out-of-envelope
extrapolation. As a result:

- **EXP-023** (per-bar screen) returned a negative dominated by ~16× denominator
  dilution, not absence of signal → **SUPERSEDED (framing-corrected)**.
- **EXP-024** fork-(b) leg compared a cumulative per-event hold return against a
  per-bar floor (category mismatch) → **RETAINED, fork leg discounted**; its
  relative-not-absolute-edge and trend-change-cuts-losers findings stand.
- **EXP-025** metric conflated the trigger definition with line-rejection →
  **INCONCLUSIVE retained, non-informative for HYP-001**.

The strategy *position rule* in EXP-023 was ~faithful to the original HYP-002
sequence. **The defect is the evaluation yardstick, not the trade logic.** This
phase fixes the yardstick, then re-screens the faithful strategy under it.

## 2. Objective

Restore a fit-for-purpose evaluation of the AVWAP selective event strategy:

1. Define and **calibrate** an event-level evaluation method that matches the
   signal's activity regime and the original metric book, with controlled error
   and a validated null — without reopening metric-shopping risk.
2. Re-screen the **faithful selective AVWAP strategy** under that method.

This phase does **not** sweep parameters, tune any rule against analysis-set
performance, build exit overlays, or explore detector/anchor branches. Predeclared
once, measured once. Holdout sealed.

## 3. Scope discipline — what is and is not in scope

**In scope (the only strategy):** the EXP-023 baseline selective AVWAP strategy
(MA(20,50) regime detector, typical price, `TickVolume**0.75`, MAD band ×1.0,
EXP-020 bounce definition, EXP-022 completion rule), re-evaluated faithfully.

**Out of scope (carried, not worked):**
- `/EXIT` (HYP-005, EXP-026) — **shelved**; EXP-ID retired, not reused.
- Stage C detectors/anchor (`/LB` `/MB` `/ATR` `/ANCHOR`) — **deferred**;
  reconsidered only after the faithful redo is read.
- `/ALPHA` `/BAND` `/XTF` `/MA-DOMAIN` — remain deferred/registered.
- **HYP-001** (direct AVWAP line S/R) — remains an **open foundational question**;
  recorded but not addressed here (operator decision: the strategy redo is the
  sole in-scope strategy). EXP-025 did not answer it.

## 4. Phase structure (EXP-027 → EXP-028, gated)

```
EXP-027  Event-level evaluation method: definition + null/control calibration
         -> does the method have controlled error and sensible null behavior
            for a sparse (~6% active) event strategy?
EXP-028  Faithful selective AVWAP strategy re-screen under EXP-027
         -> evaluated on per-event expectancy + equity-curve vs buy-hold,
            with the EXP-027 predeclared decision rule. Gated on EXP-027.
```

### EXP-027 — Event-level evaluation method (definition + calibration)

Infrastructure/methodology experiment, in the lineage of EXP-001/002 (substrate +
golden-fixture) and EXP-018 (fitness unit). Consumes **no** candidate-screening
multiplicity slot.

- **Falsifiable question:** does a predeclared event-level evaluation method —
  per-event expectancy and an equity-curve-vs-buy-hold comparison, with
  regime-cluster bootstrap CIs and matched-control / Holm inference reused from
  EXP-021/022 — exhibit **controlled error** (acceptable false-positive behavior on
  known-null sparse signals) and **recovery** (detects a planted sparse-event edge)
  across the 5m/1h/4h domains?
- **Required design elements (fixed before measurement):** the primary per-event
  estimand and its denominator; the equity-curve construction and its buy-hold
  baseline; the null/control generator(s) for a sparse event process; the decision
  rule (Evidence FOR / AGAINST / INCONCLUSIVE) and any multiple-comparison
  adjustment; the activity-regime range over which the method is declared valid.
- **Anti-overfitting guard:** the method must be specified and calibrated on
  synthetic / null + planted-edge substrates (not on the real AVWAP candidate
  outcome). It is frozen before EXP-028 reads any real candidate result.

### EXP-028 — Faithful selective AVWAP strategy re-screen

- **Falsifiable question:** under the frozen EXP-027 method, does the faithful
  selective AVWAP strategy show event-level edge (per-event expectancy and/or
  equity-curve advantage over buy-hold) on at least one domain, on the first-70 %
  analysis set?
- **Faithfulness requirement:** position rule reproduces the original HYP-002
  sequence as implemented in EXP-023; the only change vs. EXP-023 is the
  **evaluation method**, not the trade logic. Any position-rule change (e.g.
  pyramid handling) must be predeclared and justified as closer to the original,
  not as a tuning lever.
- **Gate:** opens only if EXP-027 is validated (controlled error + recovery on the
  sparse regime). If EXP-027 fails, EXP-028 does not run under that method.

## 5. Multiplicity & registry gate

The first Phase 006 artifact is a **registry amendment** in
`docs/signal-registry/multiplicity-registry.md` that:

1. opens a Phase 006 batch section and records the Phase 005 halt + supersession;
2. records the supersede-and-retain dispositions for EXP-023/024/025 and the
   shelving of EXP-026 `/EXIT`;
3. registers **EXP-027** as a methodology/calibration experiment (no
   candidate-screening slot);
4. registers **EXP-028** as the evaluation-corrected re-screen of the baseline
   (`CF-AVWAP-001`); it does **not** consume a new candidate-family slot — it
   corrects the HYP-004 baseline screen under a fit-for-purpose method, and is
   registered as such with a note that the strategy is unchanged and the
   evaluation method is the amended item.

No candidate re-screen (EXP-028) is admissible until EXP-027 is validated and the
registry reflects the method and EXP-IDs.

## 6. Methodological guardrails

- The final 30 % global holdout is excluded from all Phase 006 analysis.
- Time bars order by `CloseTime`; cross-view alignment is by timestamp, never bar
  index. All outcomes use **real OHLC** prices only.
- **No tuning against Phase 006 outcomes.** The evaluation method and decision
  rule are predeclared and frozen before EXP-028 reads any real candidate result;
  the strategy parameters are unchanged from the registered baseline. No threshold,
  metric, or parameter sweep; no post-result reselection.
- A failed calibration (EXP-027) or a negative re-screen (EXP-028) is a valid
  result, not permission to silently try another metric or another strategy
  variant.
- The frozen per-bar suite is **not** the qualification vehicle for EXP-028; the
  EXP-027 event-level method is. The per-bar suite remains the programme standard
  for high-activity (≥80 %-active) candidates and is unchanged.

## 7. Phase outcome criteria

| Outcome | Criteria | Consequence |
| --- | --- | --- |
| METHOD_INVALID | EXP-027 fails calibration (uncontrolled error or no recovery on the sparse regime). | No fit-for-purpose yardstick yet; EXP-028 does not run; operator review of how to evaluate sparse signals. |
| EVAL_SUPPORTED | EXP-027 validated; EXP-028 shows event-level edge on ≥1 domain under the predeclared rule. | First fairly-evaluated AVWAP result; proceed to robustness / fresh-regime planning (holdout still sealed). |
| EVAL_REFUTED | EXP-027 validated; EXP-028 shows no event-level edge on any domain. | The faithful selective AVWAP strategy is negative under a fit-for-purpose yardstick — a clean, interpretable negative (unlike EXP-023). Reconsider Stage-C branches or family review. |
| FAMILY_REVIEW | EVAL_REFUTED, with HYP-001 still untested. | Operator decides whether to test HYP-001 directly, explore detectors/anchor, or retire/narrow `CF-AVWAP-001`. |

## 8. Non-goals

- Exit overlays, detector/anchor branches, parameter sweeps (all carried/deferred).
- Re-running or "fixing" EXP-025's confounded metric (its structural issue is
  inherent to scoring bars on AVWAP crossing).
- Any change to the frozen per-bar suite or its calibration.
- Any use of the global holdout.

## 9. Amended phase plan (EXP-029 appended 2026-06-09)

An omission was identified in EXP-028's implementation: it was designed as a Python
re-analysis of upstream artifacts (EXP-020 events, EXP-022 lifetimes) and did **not**
reuse EXP-023's C# `StrategyHost` code or run on cTrader via per-bar streaming.
See `EXP-028-omission.md` in this checkpoint directory.

A new experiment **EXP-029** is added to close this gap:

| Experiment | Purpose | Gate |
|------------|---------|------|
| EXP-027 | Event-level evaluation method definition + calibration (unchanged) | Binding gate for both EXP-028 and EXP-029 |
| EXP-028 | Python-only re-analysis of faithful AVWAP strategy under EXP-027 (completed) | EXP-027 METHOD_VALID |
| **EXP-029** | cTrader per-bar streaming parity: run corrected C# strategy on cTrader, evaluate through EXP-027, confirm parity with EXP-028 | EXP-027 METHOD_VALID + EXP-028 results |

EXP-027 and EXP-028 proceeded as designed (both complete). EXP-029 runs after
EXP-028 results are available (for comparison) and EXP-027 is METHOD_VALID (for the
inference tail).

## 10. Updated next steps (as of 2026-06-09 amendment)

EXP-027 is **METHOD_VALID** and EXP-028 is **EVAL_SUPPORTED** (both complete). The
remaining Phase 006 work is the cTrader parity confirmation (EXP-029):

1. Amend `docs/signal-registry/multiplicity-registry.md` (Phase 006 batch) to
   register **EXP-029** as a parity confirmation of `CF-AVWAP-001/HYP-004-R`
   (0 new candidate-family slots) and to bring the EXP-027/028 statuses current.
2. Correct `StrategyHost/AvwapBounceModel.cs` so pyramid bounces open and track
   independent positions (currently `pyramid_skipped`, single concurrent position),
   and expose `is_pyramid_bounce` on the emitted table EXP-029 consumes.
3. Run the research pipeline for **EXP-029** (Stage 1 scope already drafted):
   run the corrected C# strategy on cTrader via per-bar streaming, evaluate through
   the frozen EXP-027 inference tail, and compare against EXP-028.
4. Apply the EXP-029 parity disposition: CONSISTENT → EXP-028 upgraded to
   cTrader-confirmed; INCONSISTENT → EXP-028 downgraded to `EVAL_UNCONFIRMED`
   pending root-cause.
