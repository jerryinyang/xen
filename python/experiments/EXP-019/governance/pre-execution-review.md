# Pre-Execution Governance Review - EXP-019

**Experiment:** EXP-019 - Assembled Suite Composition Anchor  
**Stage:** 4 (pre-execution)  
**Date:** 2026-06-05  
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, reused `EXP-009/code/strategies.py`, reused `EXP-012/code/loose_referee.py`, `python/src/xen/incremental_referee.py`  
**Phase:** 2026-06-05-003b-incremental-unit-redesign (ACTIVE)

---

## Verdict

```text
VERDICT: APPROVE
```

The artifacts require no revision. Execution is deliberately conditional: the code
writes BLOCKED metadata rather than measuring if upstream suite artifacts or the
operator-confirmed dogfood reference book are missing.

Execution preconditions are hard-gated in `dependency_manifest()`:

1. EXP-009 `overall_status == COMPLETE`.
2. EXP-012 `overall_status == COMPLETE`.
3. EXP-018 `overall_status == COMPLETE` plus finite domain MDE rows.
4. Dogfood reference book at `python/experiments/EXP-019/inputs/dogfood_reference_book.csv`.

---

## Reference-book precondition

The active 003b design now records D-dogfood-book as confirmed by operator decision
on 2026-06-05: R = EXP-009 Donchian(20) breakout (`donchian_20`), with the remaining
EXP-009 families as candidates. The implementation still refuses to invent or
substitute the book: missing `inputs/dogfood_reference_book.csv` is a blocker, not a
result. The required columns are `instrument`, `domain`, `CloseTime`, and
`reference_position`; alignment is by `CloseTime` and raises on any missing joined row.

---

## Constraint checks

| Constraint | Finding | Status |
|---|---|---|
| Phase alignment | Matches active design EXP-019: assembled strict + EXP-012 ratified-loose + EXP-018 revised incremental suite, with dogfood negative path and synthetic positive path. | PASS |
| Dependency discipline | Code blocks on missing/unfinished EXP-009, EXP-012, EXP-018, EXP-018 domain MDE map, and dogfood reference book. | PASS |
| Revised incremental unit | Calls `revised_incremental_gate_verdict()` for both dogfood and positive paths; old L2 gate is not used. | PASS |
| Reference book not invented | Missing reference book produces BLOCKED metadata; no default MA(20/50) book is silently chosen. | PASS |
| Holdout exclusion | Dogfood path uses `load_analysis_data()` first-70% slice; positive path is in-memory synthetic; final 30% holdout is untouched. | PASS |
| Look-ahead / temporal | Dogfood and reference positions align by `CloseTime`; positive fixture uses deterministic arrays and no future-return position construction. | PASS |
| Real-price discipline | Standalone and incremental returns use real OHLC domain returns; no chart-type prices are in scope. | PASS |
| Positive path | Fixture manifest records targets and non-redundancy diagnostics; if non-redundancy fails the pass path is not faked. | PASS |
| Negative path | Dogfood path reports standalone and incremental denominator outputs; unexpected passes become `UNEXPECTED_DOGFOOD_OUTPUT`, not Phase 004 signal evidence. | PASS |
| Complexity budget | 4 measurements / 5 plots / 0 new modules, within the 4/5/1 budget. | PASS |
| Code conventions | Imports before constants; output dirs in orchestration; `tqdm` on dogfood loop; concise logging; summary-table plotting only. | PASS |

## Verification

- Syntax compilation passed with `python3 -m py_compile` for `python/src/xen/incremental_referee.py` and `python/experiments/EXP-019/code/run_experiment.py`.
- The experiment script itself was not executed inside the pipeline.

---

## Manual execution gate

```text
Pre-execution review: APPROVED (execution deferred until preconditions are met)

Experiment: EXP-019 - Assembled Suite Composition Anchor
Code: python/experiments/EXP-019/code/run_experiment.py
Expected output: python/experiments/EXP-019/results/

Runs the strict + EXP-012 ratified-loose + EXP-018 revised incremental suite on the
EXP-009 dogfood negative path and a synthetic positive fixture, exercising both
reject and pass wiring.

Do NOT run until EXP-018 is COMPLETE with finite domain MDEs and the dogfood
reference book is recorded at python/experiments/EXP-019/inputs/dogfood_reference_book.csv.
The code will BLOCK without measurement until then.
```

---

## Addendum — Amendment B1 refresh (2026-06-05)

Post-approval, [amendment B1](../../../../docs/experiments-docs/checkpoints/2026-06-05-003b-incremental-unit-redesign/amendments/2026-06-05-B1-pre-execution-review-corrections.md) applied these code changes:

- **F02 (clean block):** `dependency_manifest()` now verifies a finite per-domain MDE for every in-scope domain and writes clean `BLOCKED` metadata if any is missing/non-finite — closing the prior path where a COMPLETE-but-partial EXP-018 caused an uncaught `RuntimeError` in `load_suite_manifest`. The review's "plus finite domain MDE rows" precondition is now enforced in `dependency_manifest`, matching the text above.
- **F06 (candidate slate):** the dead `DOGFOOD_STRATEGIES` constant is removed; the optional `reference_family` field of the dogfood reference-book manifest now excludes the family backing R from the candidate slate (design D-dogfood-book), recorded in `run_metadata.json`. The book/family stay operator-provided — nothing is invented.
- **F07 (efficiency):** the revised-verdict calls now skip the unused standalone (L2) bootstrap via the new `compute_standalone=False` default; revised-gate outputs are byte-identical.

`py_compile` re-passes. Verdict remains **APPROVE (execution deferred until preconditions are met)**; D-dogfood-book was later confirmed by operator decision as `donchian_20` before EXP-019.
