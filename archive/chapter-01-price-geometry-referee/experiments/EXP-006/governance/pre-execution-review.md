# EXP-006 — Pre-Execution Governance Review

**Experiment:** EXP-006 — L5 Materiality Threshold Sweep (Phase 002 lever curve)
**Stage:** 4 (pre-execution)
**Reviewed artifacts:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**Checkpoint:** `2026-06-03-002-referee-refinement-and-stringency` (ACTIVE)
**Date:** 2026-06-03

```text
VERDICT: APPROVE
```

---

## Phase alignment

EXP-006 is design §8's planned threshold-sweep lever curve (`MDE(tau)` / `FPR(tau)`
for the L5 materiality leg). It is an **exploratory measurement** (design §4: "no
pass/fail, measurement only"), depends on EXP-001 + EXP-003, and runs before
EXP-007 (which reads its frontier). Reuses the EXP-003-validated draw substrate
unchanged (D-reuse) — no loader/harness code changed, so no P0 re-validation is
triggered.

## Correctness verification performed (pre-execution, not the experiment run)

The reconstruction mechanism was verified directly against the frozen harness and
the EXP-003 draws before approval:

- **Frozen L5 confirmed** at `referee_calibration.py:1038`: `l5 = ci_neutral.lower
  > materiality_bps`, recorded as the top-level `ci_lower_bps`. The scope's
  `L5_tau = ci_lower_bps > tau` with `tau = multiplier · materiality_bps` is
  faithful, and `tau = 1.0 · materiality` is exactly the frozen strict leg.
- **Exact strict reproduction** (the scope's Evidence-FOR / Evidence-AGAINST
  hinge): recomputing `passed` at `tau = 1.0` reproduced the frozen `passed` for
  **all 216,000** gate-stack draw rows with **0 mismatches**. The strict-reference
  check is therefore an exact equality check, not an approximate one — attainable,
  not a mathematically-impossible criterion.
- **Idioms validated** on the real artifact: lazy `scan_csv` projection +
  `json_decode` of the L1–L4 / `materiality_bps` subset, cross-join sweep
  (216k × 7 = 1.51M rows), and group-by Wilson aggregation all behave as coded.
- **Branch coverage** of the pure MDE/frontier helpers was exercised on synthetic
  inputs (FPR-precision, FPR-uncontrolled, no-crossing, PASS) with the expected
  statuses; tiny-sample cells correctly fall to `INCONCLUSIVE_FPR_PRECISION`
  (n=4000 nulls in the real run meet the half-width ≤ 0.03 target).
- `py_compile` + `ruff` clean; module import creates **no** directories
  (`ensure_output_dirs()` only in `main()`).

---

## Artifact review against governance constraints

### Scope (`scope.md`)

| Check | Result |
| --- | --- |
| Single question | PASS — one exploratory question: how do gate FPR/MDE vary as the L5 threshold is swept. |
| Concrete criteria | PASS — Evidence-FOR/AGAINST/Inconclusive defined; the strict-reference reproduction is the binding correctness gate (verified exact). |
| Boundaries (views, params, exclusions) | PASS — multipliers `{0,0.25,0.5,0.75,1,1.5,2}`, α grid, edge grid, pooled-by-domain denominators, and exclusions (lenient mechanism, near-MDE candidates, per-instrument de-pooling, adoption) all explicit. |
| Complexity budget | PASS — 3 tests / 4 plots / 0 modules; within the checkpoint's comparative budget (~2–3 / 3–4 / 0–1). |
| Holdout exclusion | PASS — result-level post-processing of EXP-003 artifacts (already first-70%-only); the standard loading pattern is a documented unused fallback. |
| Real-price outcome rule | PASS — reused EXP-003 effect/CI fields are net-of-cost real-`Close` returns; no synthetic chart prices in scope. |

### Analysis plan (`analysis-plan.md`)

| Check | Result |
| --- | --- |
| Method justification | PASS — each step documents method, rationale, simpler-alternative, assumptions, expected output. |
| Assumptions valid for time-ordered data | PASS — non-parametric Wilson intervals; denominators inherited from EXP-003; no normality/stationarity assumption introduced. |
| Cross-view alignment | PASS (N/A) — no new market-data alignment; reuses EXP-003 `CloseTime` draws. |
| Visualisations purposeful | PASS — 4 plots map to sub-questions (FPR(τ), MDE(τ), TPR curves, MDE–FPR frontier). |
| Interpretation guide pre-defined | PASS — if-then lever interpretation predeclared. |
| Budget compliance | PASS — 3/4/0. |

### Code (`code/run_experiment.py`)

| Check | Result |
| --- | --- |
| Plan compliance | PASS — implements the four plan steps and emits the named artifacts; no out-of-scope analyses. |
| Holdout exclusion | PASS — only `pl.scan_csv` of EXP-003 `draw_verdicts.csv`; no timebars/holdout path exists. |
| Look-ahead prevention | PASS (N/A) — pure post-processing; reuses EXP-003 `t→t+1` draws. |
| Real-price discipline | PASS — reuses net-of-cost real-`Close` effects/CIs. |
| Frozen-harness reuse | PASS — imports `wilson_interval` / `write_json` only; `referee_calibration` unchanged → no re-validation. |
| Determinism | PASS — pure deterministic transforms; no RNG. |
| Type hints / docstrings | PASS — public functions typed and documented. |
| NaN / edge handling | PASS — empty-frame guard; finite-MDE guards; grid-uncertainty from prior grid edge; missing-FPR / no-crossing statuses explicit. |
| Separation of concerns | PASS — dependency gate / load / sweep / summaries / MDE / strict-check / plotting / orchestration / `main()` sectioned VAL-001 style. |
| No magic numbers | PASS — multipliers, α0, power/precision targets named; edge grid derived from the data. |
| Import side effects | PASS — verified none. |
| Progress / logging | PASS — concise INFO summary; no qualifying multi-minute Python loop exists (single vectorized collect + Polars cross-join/group-by), so `tqdm` is correctly not used. |
| Plot memory | PASS — all four plots consume bounded summary frames (≤ 63 FPR/MDE cells, ≤ 567 TPR cells); no millions-row pandas conversion. |
| Safe optimization / vectorization | PASS — the sweep is a vectorized cross-join preserving sample membership, denominators, and the recorded effect/CI; no row loops over large frames. |
| Duplicate-source denominators | N/A — referee draws, not chart-type events. |

---

## Info notes (non-blocking)

- `threshold_draw_verdicts.csv` is the large auditable artifact (~1.51M rows,
  comparable order to EXP-003's `draw_verdicts.csv`). It is written **once** as a
  Polars frame (not accumulated in a loop) and is the plan's Step-2 deliverable;
  bounded, not unbounded.
- `overall_status` is `COMPLETE` / `FAILED_REPRODUCTION` (a measurement run). A
  `FAILED_REPRODUCTION` would mean the τ=1.0 reconstruction did not reproduce
  EXP-003 — pre-verified not to occur (0/216,000 mismatches), but the gate is kept
  so EXP-007's dependency check is meaningful.
- Forward note for EXP-007: the τ=0 sweep endpoint (`ci_lower > 0`) is, by the
  frozen mechanism, identical to EXP-007's lenient leg; EXP-007 reads this frontier
  and confirms the equivalence numerically.

---

## Conclusion

Scope, analysis-plan, and code satisfy all governance constraints with no Critical
or Warning issues. The reconstruction reproduces the frozen EXP-003 gate exactly.
**APPROVE** — proceed to the manual execution gate.
