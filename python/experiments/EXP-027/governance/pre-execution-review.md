# Governance Review: Experiment EXP-027 — Pre-Execution

**Date**: 2026-06-08
**Review Type**: Pre-Execution (consolidated, research-pipeline Stage 4)
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`, `code/event_method.py`,
`code/run_experiment.py`
**Phase**: 2026-06-08-006-avwap-evaluation-correction (ACTIVE)

## Executive Summary

The experiment is well-formed and, crucially, **does not repeat the EXP-023 framing
defect** — there is no per-bar floor or frozen per-bar suite anywhere, the unit of
analysis is per-event end to end, the activity envelope brackets the real ~6% signal,
and the anti-overfitting fence (no real AVWAP event outcomes read) is enforced. One
correctness-critical revision is required: add a runtime equivalence guard for the
vectorized control matching (currently backed only by dead reference code).

## Constraint Checks

### Simplicity Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Single falsifiable question; reuses EXP-021/022 inference; no gratuitous complexity. |
| analysis-plan.md | PASS | EXP-003/005 calibration pattern translated to per-event/sparse; methods are the simplest sufficient (bootstrap/permutation/Wilson/grid-MDE). |
| code | PASS | Precompute-once + vectorized draws; no unnecessary computation. |

### Academic-Finance Pitfall Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| analysis-plan.md | PASS | Non-parametric throughout (regime-cluster bootstrap, sign-permutation, Wilson). No normality/stationarity/i.i.d./constant-vol assumptions in the gate. Two structurally different nulls (placebo-on-real + block-permuted) guard dependence miscalibration. Companion uses Sortino (catalog-preferred over Sharpe). |
| code | PASS | Block-permutation preserves autocorrelation scale; regime-cluster resampling respects event dependence. |

### Scope Compliance Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | One question; boundaries, instruments, grid, exclusions all explicit; holdout excluded; real-price rule stated; criteria measurable and attainable (FPR≤0.05 at n=500 → Wilson half-width ≈0.019; finite MDE attainable within the 64 bps grid). |
| analysis-plan.md | PASS | Budget: 4 tests / 5 viz / 1 helper module — matches code. |
| code | PASS | Implements the plan; the only **deviation** is faithful and disclosed (see Findings/Info 1). No scope creep. |

### Principles Check

| Artifact | Data-Driven | Non-Parametric | Phantom-Price Discipline | Holdout Excluded |
|----------|------------|---------------|--------------------------|-----------------|
| scope.md | PASS | PASS | PASS (real Close only; no per-bar floor) | PASS |
| analysis-plan.md | PASS | PASS | PASS | PASS |
| code | PASS | PASS | PASS | PASS (`load_analysis_data` first-70%; regime-index fence in `_precompute_cell`) |

### Quality Check (calibration/methodology specific)

| Check | Verdict | Notes |
|-------|---------|-------|
| Per-EVENT unit (no per-bar floor) | PASS | No frozen suite / per-bar MDE imported or compared against; denominators are reportable matched events. This is the binding EXP-023 correction. |
| Activity-envelope match | PASS | Grid {0.03,0.06,0.12} brackets the real ~6%; validity declared only over the sparse range. The exact governance miss at EXP-023 is explicitly guarded here. |
| Anti-overfitting fence | PASS | `avwap_events.csv` outcomes are excluded from required artifacts and never loaded; only the regime scaffold + hardcoded ~6% grid constant; signal under test is fully synthetic; method frozen before EXP-028. |
| Decision-rule reuse | PASS | `decide_label` reproduces the EXP-021 Evidence-FOR rule unchanged in structure (incl. secondary-horizon stability); bootstrap/permutation/Holm structurally identical. |
| Zero-baseline handling | PASS | Null excess = 0 bps; Wilson rates; non-finite MDE reported as `null`, never 0. |
| Look-ahead safety | PASS | Placement/matching use bar-time info only; planted drift added to outcomes only; block length estimated on train portion only. |
| Safe optimization / vectorization | **FLAG** | `nearest_controls` is provably equivalent to EXP-021 `select_controls`, but the `reference_select_controls` guard is **unused dead code** — no runtime assertion ties the vectorized path to the reference. This is the linchpin of the whole reused inference and must be guarded (Critical-1). |
| Progress / logging / import side effects | PASS | `tqdm` over draw loops; concise logging; output dirs created only in `run()`; no import-time I/O. |
| Determinism | PASS | All randomness via `seed_for`; `determinism_replay` re-runs a fast cell and asserts identical stats. |

## Findings

### Critical (blocks approval)

1. **Vectorized control matching lacks a runtime equivalence guard; reference port is
   dead code.**
   - Files: `code/event_method.py` (`nearest_controls`, `reference_select_controls`);
     `code/run_experiment.py` (`run`).
   - Issue: `nearest_controls` (the vectorized two-pointer) is the substitute for
     EXP-021's `select_controls` and underpins every paired difference, effect, CI,
     and verdict. `reference_select_controls` was written for an equivalence check but
     is never called — leaving the equivalence asserted only by argument, and the
     reference function flagged as dead code. The entire calibration is invalid if the
     vectorized matcher diverges from the reference ordering.
   - Required fix (route to `experiment-developer`): add a cheap, deterministic
     startup self-check in `run()` (before the calibration loops) that builds a small
     synthetic regime (a sorted eligible-candidate array and a handful of trigger
     indices, including boundary and equal-distance-tie cases) and asserts
     `nearest_controls` reproduces `reference_select_controls` exactly for every
     sample; hard-fail with a clear message on any mismatch. Record the check result
     in `run_metadata.json` (e.g. `control_matching_equivalence_pass`).

### Warnings

None.

### Info (non-blocking; acceptable as-is)

1. **Disclosed faithful deviation — full {1,3,6} horizon family.** Code implements the
   registered EXP-021 horizon family with `decide_label` unchanged (incl. the
   secondary-horizon stability downgrade) instead of the plan's `H_cal=3` +
   `H_cal=6`-FPR-only simplification. This is strictly *more* faithful to "reuse the
   EXP-021 decision rule unchanged," uses the same registered horizon family, and adds
   no new metric. Accepted.
2. **MDE FPR-gate alpha.** `compute_mde` applies the FPR≤0.05 control condition at
   `alpha0=0.05` for all alpha rows; the headline MDE is alpha=0.05 (clean). The
   alpha∈{0.10,0.01} MDE rows are secondary diagnostics. Acceptable; note in results.
3. **Equity companion reporting.** The non-gating companion is summarized via
   cross-draw advantage/Sortino distributions and a null false-advantage rate rather
   than a per-draw bootstrap CI; the exposure-matched baseline (not buy-hold) is the
   comparator, with buy-hold annotated as 100%-exposed context (not drawn). This
   honors the exposure-mismatch-avoidance requirement and stays within budget.
   Optional polish: draw a faint annotated buy-hold context line, or keep annotation
   only. Non-blocking.

## Revision Cycle 1 — Resolution (2026-06-08)

Critical-1 resolved by `experiment-developer`:

- `event_method.py` adds `verify_control_matching()` — a self-contained guard that
  asserts the vectorized `nearest_controls` reproduces `reference_select_controls`
  exactly across one-sided boundary, two-sided equal-distance ties (resolving to the
  lower index), a full-`MAX_CONTROLS` interior trigger, and a fewer-than-`MAX` case.
  It raises `ValueError` on any mismatch, so a divergence aborts the run before any
  draw. `reference_select_controls` is now used (dead code removed).
- `run_experiment.py` calls the guard at the top of `run()` (fail-fast), logs the
  pass, and records `control_matching_equivalence_pass` in `run_metadata.json`.
- Verified: both files `py_compile` cleanly, and the guard executes to `True` in the
  project environment (`python/.venv`), confirming the linchpin equivalence holds.

Info-3 (minor): the optional buy-hold context line was left annotation-only — an
acceptable, non-misleading choice (the exposure-matched baseline remains the
comparator). Info-1 (faithful {1,3,6} deviation) and Info-2 (MDE FPR-gate alpha)
stand as recorded; both are acceptable and will be reflected in interpretation.

All Critical issues are resolved; no Warning-level issues remain.

## Execution-Time Fix (2026-06-08, post-approval)

The first manual run aborted in `_precompute_cell` (BTCUSD/5m regime index outside
the rebuilt first-70% frame). Root cause: `data/timebars/` holds multiple files per
instrument plus an auxiliary `timebars_analysis70_xauusd_*` file; `build_precomputes`
was selecting/validating the wrong (stale/auxiliary) frame per instrument. Fix:
`build_precomputes` now keys one source per instrument by the **Symbol column**
(`data.instrument`) with latest-sorted wins — the exact selection EXP-020/021 used —
and runs the (unchanged) holdout fence only on survivors. Verified in the project
venv: all 4 instruments × 3 domains satisfy `regime_end_max == n-1`, `start ≥ 0`,
`anchor ≥ 0`; selected files are the canonical per-instrument captures. The fence was
**strengthened, not weakened**; the change is a data-source-selection correction with
no effect on the method, denominators, or holdout discipline. Verdict stands.

## Verdict

```
VERDICT: APPROVE
```
