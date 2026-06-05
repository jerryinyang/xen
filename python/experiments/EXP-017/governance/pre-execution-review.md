# Pre-Execution Governance Review - EXP-017

**Experiment:** EXP-017 - Revised Incremental Referee Golden-Fixture Correctness  
**Stage:** 4 (pre-execution)  
**Date:** 2026-06-05  
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `python/src/xen/incremental_referee.py`  
**Phase:** 2026-06-05-003b-incremental-unit-redesign (ACTIVE)

---

## Verdict

```text
VERDICT: APPROVE
```

The artifacts require no revision. EXP-017 is a deterministic fixture gate for the
confirmed Phase 003b revised incremental unit: L2 is absent, retained legs are
L1/L3/L4_prime/strict-L5, every retained leg is exposed, and the old standalone-L2
failure fixture is expected to pass under the revised formula.

Execution preconditions are hard-gated in `dependency_manifest()`:

1. EXP-013 `overall_status == PASS`.
2. EXP-014 `overall_status == PASS`.
3. Active 003b design records D-revised-legs and D-l4l5-freeze as confirmed by the operator on 2026-06-05.

---

## Constraint checks

| Constraint | Finding | Status |
|---|---|---|
| Phase alignment | Matches active design H-revised-correct and EXP-017 scope: revised gate = L1 and L3 and L4_prime and strict-L5; L2 absent. | PASS |
| Estimator safety | `revised_incremental_gate_row` changes only leg assembly and verdict formula; it reuses `incremental_gate_core`, marginal estimator, contiguous block-length rule, and bootstrap distributions unchanged. EXP-013 does not need rerun. | PASS |
| Fixture coverage | Seven fixtures cover all-pass, L1 fail, former L2 fail now pass, L3 fail, L4_prime fail, strict-L5 fail, and redundant shared-structure rejection. | PASS |
| L2 absence | `l2_absence_check.csv` is produced and fails if any emitted revised gate leg starts with `L2`. | PASS |
| No short-circuit | `evaluate_fixture()` records all four retained legs for every fixture, independent of final verdict. | PASS |
| Holdout / data | In-memory fixtures only; no market Parquet read; final 30% global holdout untouched. | PASS |
| Real-price discipline | Fixture returns represent real-price return contributions; no chart-type construction prices are in scope. | PASS |
| Zero-baseline handling | Exact counts and finite pass/fail flags; no percentage improvement from zero. | PASS |
| Complexity budget | 2 checks / 3 plots / 0 new modules, within the 2/3/1 budget. | PASS |
| Code conventions | Imports before constants; output directories in orchestration; concise logging; sectioned helpers; no helper-level prints; deterministic seeds. | PASS |

## Verification

- Syntax compilation passed with `python3 -m py_compile` for `python/src/xen/incremental_referee.py` and `python/experiments/EXP-017/code/run_experiment.py`.
- The experiment script itself was not executed inside the pipeline.

---

## Manual execution gate

```text
Pre-execution review: APPROVED

Experiment: EXP-017 - Revised Incremental Referee Golden-Fixture Correctness
Code: python/experiments/EXP-017/code/run_experiment.py
Expected output: python/experiments/EXP-017/results/

Replays deterministic revised-gate fixtures and verifies verdict reproduction,
retained-leg exposure, and L2 absence without reading market data.

Please run the experiment code and confirm when complete. EXP-017 must reach
overall_status PASS before EXP-018.
```

---

## Addendum — Amendment B1 refresh (2026-06-05)

Post-approval, [amendment B1](../../../../docs/experiments-docs/checkpoints/2026-06-05-003b-incremental-unit-redesign/amendments/2026-06-05-B1-pre-execution-review-corrections.md) applied **documentation-only** changes to this experiment (F01, F04, F05): the fixtures are now described as *seeded-deterministic* with predeclared hand-reasoned leg states (not "hand-computed/golden"), the construction is described as *adapted from* EXP-014, and L5-strict is named the operationally binding leg with L3 its precondition. No fixture parameter, leg, threshold, or verdict logic changed; `py_compile` re-passes. The verdict remains **APPROVE** and the manual-execution gate above is unaffected.
