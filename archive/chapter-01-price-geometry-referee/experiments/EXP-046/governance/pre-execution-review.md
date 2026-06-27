# Governance Review: Experiment EXP-046 — Pre-Execution

**Date**: 2026-06-12
**Review Type**: Pre-Execution (consolidated, Stage 4)
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`,
`code/variant_screen.py`, modified `python/src/xen/avwap.py`, extended
`python/tests/test_avwap_band_param.py`, Phase 012 `design.md` +
`D0-predeclarations.md` (RATIFIED), multiplicity registry Phase 012 batch.

## Executive Summary

APPROVE — the screen implements exactly the ratified D0 rules, TRAIN-only and
gross-only, with 0 TEST reads by construction; one pre-data-contact
documentation defect (variant count 8→7) was found and corrected across all
artifacts; the P8 regression gate is green (24/24).

## Constraint Checks

### Simplicity Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Single falsifiable question; OAT (not cross-grid) explicitly justified; no net machinery built. |
| analysis-plan.md | PASS | Descriptive means + one descriptive SE + mechanical rule; 0 binding tests; every method carries "simpler alternative considered". |
| code | PASS | One new module; domain bars aggregated once per cell and reused across variants; no abstraction beyond need. |

### Academic-Finance Pitfall Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| analysis-plan.md | PASS | No normality/stationarity/i.i.d. assumption; cluster bootstrap SE (frozen EXP-027 structure) used as a noise yardstick only; the EXP-044 N1>N2 offset disclosed as irrelevant (no null-calibrated inference run). |
| code | PASS | `cluster_bootstrap_se` replicates the EXP-045 implementation exactly (regime clusters within direction strata, event-weighted mean). |

### Scope Compliance Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md vs design/D0 | PASS | All grids, horizons, floor formula, margin, event floor, composition threshold restated verbatim from the RATIFIED D0; nothing data-derived added. |
| code vs plan | PASS | Steps 1–5 mapped 1:1; no bonus analyses. Two minor documented deviations (Info-1/2 below), neither changes a metric or threshold. |
| Complexity budget | PASS | 0 binding tests / 0; 4 plots / 4 (a fifth reconciliation plot was drafted and removed pre-review); 1 new module / 1. |

### Principles Check

| Artifact | Data-Driven | Non-Parametric | Phantom Price Discipline | Holdout Excluded |
|----------|------------|---------------|--------------------------|-----------------|
| scope.md | PASS | PASS | PASS (real domain-bar closes only; no synthetic views in scope) | PASS |
| analysis-plan.md | PASS | PASS | PASS | PASS |
| code | PASS | PASS | PASS | PASS (F01 `head(train_rows)` from metadata counts; no full-file sort; TRAIN end asserted against the EXP-043 `train_end_ts`; TEST/holdout rows never collected) |

### Chart-Type Comparison Check

| Artifact | Timestamp Alignment | Bar Count Adjustment | Generator Determinism |
|----------|-------------------|---------------------|---------------------|
| code | PASS (single view; ordering by `CloseTime`; fixed-offset horizon indexing is within one chronologically sorted domain frame — no cross-view bar-index use) | N/A | PASS (sequential frozen generator; per-cell×variant double-generation digest compare; bootstrap seeded via `seed_for`) |

### Quality Check (type-specific)

| Artifact | Verdict | Notes |
|----------|---------|-------|
| `xen.avwap` parameterization | PASS | α/MA threaded with validated bounds; defaults reproduce the baseline bit-for-bit (pinned fixture test); P8 suite green 24/24 — the precondition for any TRAIN read is satisfied. |
| code conventions | PASS | Sectioning, import-time purity, dirs created in `main()`, `tqdm` outer loop, quiet helpers, bounded plot inputs from result rows, explicit NaN/None handling, no magic numbers (all constants D0-sourced). |
| Look-ahead | PASS | Horizon closes are the outcome window (post-event by definition, scoped); the H_MAX evaluability fence keeps every outcome window inside TRAIN — no TEST leakage through the forward window; one population per cell×variant across horizons (denominator fixed before metrics). |
| Zero-baseline / denominators | PASS | Per-event means with counts always reported; no ratio-vs-zero metrics; `n=0` → null means, BELOW_FLOOR verdicts; variant-vs-floor (not variant-vs-baseline) comparisons as scoped. |
| Baseline reconciliation | PASS (design) | Blocking anchor: EXP-043 event counts + EXP-045 FH net at θ∈{4,8,16} recomputed under EXP-045's exact conventions (full population, forced-clip, exact fractional-day financing), tolerance 1e-9 bps. This is the only place net arithmetic appears, and it exists solely as an integrity check against a persisted anchor — not a result column. |

## Findings

### Critical

None.

### Warnings

None outstanding. (W-1, found in review and fixed pre-data-contact: the
design/scope/registry prose stated "8 variants incl. baseline" while the
frozen P1/P2 grids define 7 distinct OAT variants — α=0.0 was double-counted.
Corrected 2026-06-12 in design §3/§4/§5.1/§7, scope, registry batch,
analysis-plan, and code docstrings. No frozen grid value changed; no data was
read under either count.)

### Info

1. The descriptive H=8 SE is reported in `clearance_table.csv` rather than
   appended to `gross_table.csv` (plan Step 3 wording). Same content, one
   location; acceptable.
2. Plan Step 5 says the reconciliation applies "the same evaluable-event
   convention to both sides"; the implementation instead anchors on EXP-045's
   own full-population/forced-clip convention applied identically to both
   sides — a stricter, exactly-defined variant of the same intent (the only
   persisted anchor uses that convention). Acceptable; the auditor should
   verify the reconciliation passes at the stated tolerance.
3. The G1 verdict is computed as a mechanical readout in `run_metadata.json`
   but adjudication is reserved to the Phase 012 checkpoint
   `G1-gate-review.md`, per the design. Correct division of authority.

## Verdict

```
VERDICT: APPROVE
```

## Addendum — Revision 1 (2026-06-12, adversarial review; pre-data-contact)

Two independent adversarial review sets (A: implementation; B: methodology)
were adjudicated. All fixes applied before any TRAIN read; no frozen D0
value changed. Verdict unchanged: APPROVE.

| Finding | Adjudication | Action |
|---|---|---|
| A.F01 integrity failure did not suppress G1 readout | VALID (Major) | `g1_mechanical_readout = INCONCLUSIVE_INTEGRITY_FAIL` and empty `variants_meeting_composition` on any reconciliation/determinism failure. |
| A.F02 reconciliation did not validate the binding gross/evaluable path | VALID in substance (Major) | Scope/plan amended to document the FH-net anchor as legs 1–2 (the only persisted external reference, EXP-045 conventions on both sides) + new leg 3: internal cross-check of the exact `evaluable_mask`/`gross_at_horizons` clearance path. |
| A.F03 stale counts / plot-list ambiguity | VALID (Minor) | scope.md "variant (8)"→(7); visualisation list aligned to the four implemented plots (reconciliation CSV-only). |
| A.F04 determinism digest omitted scoring fields | VALID (Minor) | Determinism now asserted by full-frame equality (events + regimes); digest extended to trigger_idx/time, direction, regime_id, anchor_idx as the persisted audit fingerprint. |
| B.F01 cluster SE may miss between-regime overlap correlation | PARTIALLY VALID | The 1×SE multiplier is a frozen D0 value — no inflation factor or new estimator post-G0. Disclosed in plan Step 3 + metadata; `n_regimes_evaluable` added to `events_summary.csv` so cluster counts are read alongside any clearance. |
| B.F02 composition FPR under cross-cell correlation unquantified | PARTIALLY VALID | Estimating cross-cell correlations is outside the approved scope (0 binding tests). Recorded as G1-adjudication caveat 1 (plan interpretation guide): correlated-bloc clearing sets read with elevated-FPR context. |
| B.F03 plan/implementation reconciliation-convention mismatch | VALID (Minor) | Plan Step 5 rewritten to match the implementation exactly (three legs, conventions stated). Supersedes review Info-2. |
| B.F04 calendar-day floor understates weekend financing | VALID as disclosure (Minor) | P4 formula is frozen — not replaced. Bias direction (floor too low for weekend-spanning holds, largest on 4h index cells) documented in plan caveat 2 and `run_metadata.json`; clearing index cells carry it at G1. |
| B.F05 composition threshold inherited without search-space re-derivation | VALID (Minor) | Design §7 multiplicity posture extended: per-variant evaluation = 6 chances; absorbed by selected-on-TRAIN treatment — G1 authorizes a follow-on phase, never a claim; threshold is a breadth floor, not FDR control. |
