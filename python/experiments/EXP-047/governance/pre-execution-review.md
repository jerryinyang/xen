# Governance Review: Experiment EXP-047 — Pre-Execution

**Date**: 2026-06-12
**Review Type**: Pre-Execution
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`,
`code/move_size.py`, modified `python/src/xen/avwap.py`,
new `python/tests/test_avwap_anchor_param.py`; checked against the Phase 013
checkpoint `design.md` + ratified `D0-predeclarations.md` and the bundled
governance constraints.

## Executive Summary

All checks pass: the scope restates the ratified D0 verbatim (nothing
data-derived), the plan is descriptive/non-parametric with a mechanical
predeclared verdict rule, and the implementation is TRAIN-only with the P8
regression gate enforced in-code before the first data read. APPROVE.

## Constraint Checks

### Simplicity Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | One falsifiable question (anchor placement vs intrinsic ceiling); two mechanical sub-steps of it, no compound hypotheses. |
| analysis-plan.md | PASS | Medians/IQR/bootstrap SE only; simpler alternatives documented (fixed-horizon expectancy rejected at design level — already measured flat). |
| code | PASS | One helper module + orchestration; anchor logic lives behind default-preserving parameters in the existing `xen.avwap`. |

### Academic-Finance Pitfall Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| analysis-plan.md | PASS | Distribution-free location statistics; bootstrap SEs explicitly descriptive (non-i.i.d. acknowledged); no significance claims (0 binding tests); unpaired-population honesty stated. |
| code | PASS | No parametric assumptions anywhere; verdicts are mechanical threshold counts. |

### Scope Compliance Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Restates D0 P1–P8 exactly (`ATR_period=14`, `k=1.0`, `M=2`, ≥30 floor, ≥5 cells/≥3 instruments); exclusions match design §4; gross-only, floor never subtracted. |
| analysis-plan.md | PASS | No method outside scope; matched-control arm is the scoped context read, descriptive only. |
| code | PASS | Outputs exactly the scoped tables/plots (4/4 visualisations, 0 binding tests, 1 new module); no net columns anywhere; floor appears only as comparison threshold (`shift_verdict` leg 2, plot reference lines). |

### Principles Check

| Artifact | Data-Driven | Non-Parametric | Phantom Price Discipline | Holdout Excluded |
|----------|------------|---------------|--------------------------|-----------------|
| scope.md | PASS | PASS | PASS (real domain-bar OHLC only) | PASS |
| analysis-plan.md | PASS | PASS | PASS | PASS |
| code | PASS | PASS | PASS (no synthetic views in scope) | PASS (`head(train_rows)` lazy slice bound to EXP-043 certified `train_end_ts`; analysis/TEST/holdout rows never materialised) |

### Chart-Type Comparison Check

| Artifact | Timestamp Alignment | Bar Count Adjustment | Generator Determinism |
|----------|-------------------|---------------------|---------------------|
| code | PASS (`CloseTime` sort enforced; cross-arm comparison is distributional, no event pairing) | N/A (no chart-type views) | PASS (double-generation replay per cell per arm; P8 suite pins fixture invariance) |

### Quality Check (type-specific)

| Artifact | Verdict | Notes |
|----------|---------|-------|
| `xen.avwap` anchor parameterisation | PASS | Default `anchor_mode="running_extreme"` reproduces the frozen baseline bit-for-bit (15/15 regression tests green, incl. the pre-existing band/α/MA suite); `/ANCHOR` is an explicit sequential state update — segment window + trailing-TR deque, all completed bars ≤ confirmation bar; tie-break and running-extreme fallback (`anchor_fallback` disclosure) implemented per P1. |
| `test_avwap_anchor_param.py` | PASS | Covers all three P8-required legs: baseline fixture invariance at defaults, look-ahead-safety truncation probe + determinism smoke, fallback path; suite green. |
| run_experiment.py | PASS | P8 gate enforced in-code (`run_p8_regression_gate` aborts before any TRAIN read); blocking reconciliation vs EXP-043 counts and EXP-046 baseline gross(H=8) at 1e-9 bps; output dirs created in `main()`; `tqdm` outer loop; helpers return data; NaN/empty-arm handling explicit; fixed seeds; plotting consumes bounded summary tables only. |
| move_size.py | PASS | Pure, typed, docstringed; per-event excursion loop is bounded (hundreds of events/cell) and causally retrospective; matched controls deterministic and capped (`CONTROL_MAX`); P5 legs implemented verbatim. |

## Findings

### Critical

None.

### Warnings

None.

### Info

1. The look-ahead probe regenerates on bounded prefixes (≤3 regimes/cell) —
   accepted cost; the structural guarantee is additionally pinned by the P8
   truncation-probe test.
2. EXP-043 `power_statement.csv` covers all 51 cells, so the count
   reconciliation binds grid-wide; the gross(H=8) anchor binds on the 37
   EXP-046 baseline cells, per the scope's integrity-anchor definition.
3. The floor used in P5 leg 2 derives from the `/ANCHOR` arm's median lifetime
   (the population being classified), with the baseline floor tabulated for
   disclosure — consistent with P4 as restated in the approved plan.

## Revision Record (2026-06-12, pre-data, adversarial review applied)

Two external review sets were adjudicated before any TRAIN read; all changes
below are pre-data and none derives from Phase 013 data.

Accepted and fixed:
- **MFE/MAE excursion convention** (Major): excursions are now floored at 0
  (the lifetime path includes the entry point); fixture cases
  (all-favorable / all-adverse / empty-window) verified.
- **Matched-control convention** (Major): controls now implement the actual
  EXP-021/027 rule (same `regime_id`, 6-bar trigger exclusion, up to 5 by
  nearest anchor age then timestamp, minimum 3), replacing random
  same-regime sampling; the same-sub-segment circularity is disclosed in the
  plan as a descriptive-only limitation.
- **P5 leg-2 floor** (Major): binding floor = max of the two arms'
  lifetime-derived floors (conservative; both disclosed), removing the
  lifetime-shift confound.
- **P1 candidate-set ambiguity** (Major): the scope now states the
  multi-candidate pivot reading explicitly (the design §5.1 reading and the
  only non-vacuous one) and flags it for operator confirmation at the
  manual execution gate.
- Minor disclosures: leg-1 relabelled a noise guard with a
  `leg1_borderline` brittleness flag; look-ahead probe scaled to
  `max(3, √n_regimes)`; unreconciled cells listed in run metadata;
  non-binding P6 threshold-sensitivity flags added.

Rejected with rationale:
- **Relaxing the 1e-9 bps reconciliation tolerance**: the anchor is an
  identical recompute of the EXP-046 baseline path (same ops, order, and
  aggregation code; CSV float64 round-trips exactly) and 1e-9 is the frozen
  Phase 012 convention that EXP-046 passed 259/259; relaxing it would
  weaken a validated integrity pattern.
- **Drawing controls from a different regime**: would deviate from the
  ratified EXP-021/027 convention and require a design amendment; resolved
  by implementing the real convention plus explicit labeling instead.

P8 suite re-run after all changes: 15/15 green. Verdict unchanged.

## Verdict

```
VERDICT: APPROVE
```
