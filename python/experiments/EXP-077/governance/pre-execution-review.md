# Governance Review: Experiment EXP-077 — Pre-Execution

**Date**: 2026-06-20
**Review Type**: Pre-Execution (Stage 4)
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`,
`python/src/xen/wf.py` (new), `python/src/xen/ass.py` (moving-block extension)
**Governing checkpoint**: `2026-06-20-017-capgeo-qualifier-validation` (G0 PASS; D0 frozen)

## Executive Summary

**APPROVE.** Scope, plan, and code faithfully implement the D0-predeclared `ASS/VAL-002` legs
(FPR/MDE/reliability/counted-read accounting under `WF-EXPANDING` + a current-data TRAIN-only dogfood).
Holdout discipline is strong (synthetic + first-49% only; TEST/holdout never sliced, asserted in
code). The per-stratum verdict doctrine (LESSON-001 / EXP-076 audit C1) is correctly enforced. All
binding thresholds are D0/bite-calibrated or margin-calibrated on nulls — no unjustified magic
constants. Four Info notes; no Critical or Warning issues.

## Constraint Checks

### Simplicity Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Comparative-tier validation; 4 checks / 5 plots / 1 module — minimal sufficient. |
| analysis-plan.md | PASS | Non-parametric throughout (empirical FPR/TPR, Wilson, reliability diagram, fold-clustered bootstrap). Each method carries a "simpler alternative considered". |
| code | PASS | Flat-iid bootstrap on exchangeable synthetic data (equivalent to, and cheaper than, fold-clustering) is the simpler sufficient choice; the true fold-clustered moving-block is reserved for the real dogfood. Counted-read accounting is a pure logic table, not a model. |

### Academic-Finance Pitfall Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| analysis-plan.md | PASS | No normality/stationarity/iid assumption imposed on real data: synthetic populations are iid **by construction** (declared ground truth); the real dogfood preserves serial dependence via moving-block bootstrap. FPR/MDE/reliability are empirical, distribution-free. |
| code | PASS | Wilson (not normal-approx) for FPR uncertainty; empirical Q95 margin; moving-block for real bars. |

### Scope Compliance Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| Single question | PASS | One coherent methodology-validation question — "do `ASS`+`WF-EXPANDING` control error / stay reliable / honor the read cap?" — whose PASS is the D5 conjunction of its legs. Mirrors the multi-leg single-keystone precedent (EXP-003, EXP-076 recovery/coverage/shrinkage). Not compound, not scope creep. |
| Boundaries | PASS | Data views, parameters, instruments (4-core dogfood), time range (first-49% only), exclusions (EXP-078 shape/`k`; no candidate screening; no TEST/holdout) all explicit. |
| Criteria | PASS | Measurable: FPR ≤ 0.05 & Wilson-hi ≤ 0.075; MDE finite ∀ N≥30; gap ≤ 0.10 & slope ∈ [0.85,1.15]; accounting scenarios; 0 counted reads; byte-identical determinism. |
| Budget | PASS | 4 validation checks / 5 plots / 1 new module (`xen.wf`) + an in-family `xen.ass` extension — matches scope. |
| No scope creep | PASS | Code implements exactly the five planned legs; no bonus analyses. |

### Principles Check

| Artifact | Data-Driven | Non-Parametric | Real-Price Discipline | Holdout Excluded |
|----------|------------|---------------|--------------------------|-----------------|
| scope.md | PASS | PASS | PASS (dogfood real `Close`; no HA/Renko) | PASS (first-49% only; TEST/holdout never sliced) |
| analysis-plan.md | PASS | PASS | PASS | PASS |
| code | PASS | PASS | PASS | PASS (asserted in `load_train_1m` / `dogfood_cell`) |

### Gate-Threshold Calibration (key check)

| Threshold | Verdict | Basis |
|-----------|---------|-------|
| FPR ≤ 0.05, Wilson-hi ≤ 0.075 | PASS | D2.2 (bite-GREEN; 0.075 from EXP-070 lineage). |
| margin `m(type,N)` | PASS | **Calibrated on TAG_CAL nulls** as `max(0, Q95(ci_low_1s))` (m_cell analog, EXP-008/070/032 lineage); FPR validated on **independent** TAG_VAL nulls. Reported, not hand-set. |
| TPR floor 0.80 | PASS | D2.3 programme standard. |
| reliability gap 0.10 / slope [0.85,1.15] | PASS | D2.4. |
| accounting cap = 2 | PASS | TEST-read-ledger rule. |

### Look-Ahead / Timestamp Alignment

| Check | Verdict | Notes |
|-------|---------|-------|
| WF causality | PASS | Completed test fold rolls into next train (historical at next train time — not leakage; documented in `xen.wf`). |
| Dogfood causality | PASS | Forward-H return drops trailing H bars; ATR(14) via trailing cumsum (no future). Ordered by `CloseTime`; no bar-index alignment. |

### Verdict Representation (per-stratum — LESSON-001)

| Check | Verdict | Notes |
|-------|---------|-------|
| Per-stratum binding verdict | PASS | `build_verdict` emits FPR per `(type,N,read)`, MDE per `N`, reliability per `X`, accounting per scenario, dogfood per cell. The single cross-leg AND is named `collapsed_convenience_flag` and **explicitly captioned NON-BINDING**. Directly honors the EXP-076 C1 precedent. |

### Safe Performance / Determinism

| Check | Verdict | Notes |
|-------|---------|-------|
| Efficient Polars | PASS | Lazy scan → select cols → sort `CloseTime` → first-49% slice → collect. |
| Bounded memory | PASS | Batched bootstrap; result tables written once; plots consume bounded tables. |
| Determinism | PASS | All draws seeded via `SeedSequence([MASTER_SEED, *key])`; process-pool cells order-preserving + seed-independent (byte-identical at any worker count). A non-deterministic `hash(instrument)` seed was caught and fixed → `DOG_INSTRUMENT_ID`. |
| Import side effects | PASS | Verified empirically — import creates no `results/` and loads no data; dirs created in `main()`. |
| Progress | PASS | `tqdm` on FPR/MDE/reliability/dogfood loops; helpers quiet. |

## Findings

### Critical

None.

### Warnings

None.

### Info

1. **MDE probe grid (`MU_GRID = {0.05…1.0}`)** extends the U-location family beyond the D1-declared
   `U0–U3` (μ ≤ 0.20). These are **evaluation points of the same `N(μ, 1²)` DGP family** to trace the
   TPR curve and locate the 0.80 crossing — **not new registered types** (they carry no FPR/recovery
   verdict and use a disjoint effect seed-id). Necessary for the finiteness gate at small `N`;
   mechanical ladder, not tuned. Within-family, disclosed.
2. **Synthetic WF aggregation uses the flat-iid bootstrap** (`kind="iid"`), statistically equivalent
   to fold-clustering on an exchangeable population (documented in `xen.wf.aggregate_walk_forward`);
   the true **fold-clustered moving-block** path (`kind="block"`) runs on the real dogfood. The WF
   *structure* (expanding train, pooled out-of-train test, one stratum verdict) is preserved in both.
3. **Determinism re-run** covers the cheap legs (reliability, accounting) plus one FPR and one MDE
   **probe cell** — it does not re-run the full multi-hour FPR/MDE grid or the dogfood, matching the
   accepted EXP-076 pattern. The Stage-5 auditor may run a fuller determinism replay if warranted.
4. **Dogfood return series** (`DOG_FWD_H=6`, `DOG_ATR_PERIOD=14`) are **non-binding pipeline-smoke
   constants** carrying no market-edge claim (H=6 from the family's prior cap lineage, ATR(14) the
   programme default); the dogfood PASS is pipeline integrity + the fence assertion, not a numeric edge.

## Phase-Alignment Check

EXP-077 is the explicit next slate item in the active checkpoint (EXP-076 → **EXP-077** → EXP-078),
gated on EXP-076 G-017a PASS (satisfied). 0 candidate slots, 0 counted TEST reads, holdout untouched —
consistent with the Phase 017 discipline. Registry precondition satisfied: `ASS/VAL-002`/EXP-077 is
registered in the Phase 017 multiplicity batch; no TEST stratum is read (ledger unchanged).

## Verdict

```
VERDICT: APPROVE
```
