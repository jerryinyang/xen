# Pre-Execution Governance Review — EXP-016

**Experiment:** EXP-016 — Assembled Suite Composition Anchor (framework conclusion)
**Stage:** 4 (pre-execution)
**Date:** 2026-06-04
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py` (+ reused `EXP-009/code/strategies.py`, `EXP-012/code/loose_referee.py`, `xen.incremental_referee`)
**Phase:** 2026-06-04-003-ratification-and-incremental-unit (ACTIVE)

---

## Verdict

```text
VERDICT: APPROVE
```

The artifacts require no revision. Execution is gated on three manual/operator
preconditions (all enforced by the code, which writes BLOCKED metadata rather than
proceeding):

1. **EXP-012 COMPLETE** (per-domain ratified-loose / strict-fallback decisions).
2. **EXP-015 COMPLETE** (incremental portfolio-fitness MDE map; finite domain MDE
   required — `load_suite_manifest` raises otherwise).
3. **Operator-defined dogfood reference book** at
   `python/experiments/EXP-016/inputs/dogfood_reference_book.csv`
   (columns `instrument, domain, CloseTime, reference_position`).

> EXP-009 COMPLETE and the Track B token (transitively, via the incremental unit) are
> also required; EXP-009 is already COMPLETE.

---

## Reference-book precondition (operator decision — DEFERRED)

The design specifies the real dogfood "against a reference book" but never names R.
EXP-016 **correctly refuses to invent one**: `dependency_manifest()` lists the missing
`inputs/dogfood_reference_book.csv` as a blocker and `main()` BLOCKS. On **2026-06-04**
the operator **deferred** the R definition to before EXP-016 runs (EXP-016 is the last
experiment, after EXP-012/EXP-015). Before EXP-016 may execute, R must be supplied as an
approved artifact or a dated design amendment recorded **before results are read**. No
`inputs/` directory exists yet — this is the binding open item for EXP-016.

---

## Constraint checks

| Constraint | Finding | Status |
|---|---|---|
| Holdout exclusion | Dogfood path uses `load_analysis_data` first-70% slice; positive fixture is in-memory synthetic; holdout never loaded. | PASS |
| Look-ahead / temporal | Dogfood strategy positions are EXP-009 look-ahead-safe definitions; reference aligned by `CloseTime`; positive-fixture positions synthetic, drift planted causally. | PASS |
| Real-price discipline | Standalone + incremental returns on real domain `Close`; positive fixture uses real-price-style return contributions; no HA/Renko prices. | PASS |
| Timestamp alignment | `align_reference_positions` joins reference book to domain rows by `CloseTime` and **raises on any unmatched row** (no silent gaps, no bar-index alignment). | PASS |
| Reference book not invented | Missing reference book → BLOCKED, per scope's explicit prohibition. | PASS |
| Positive fixture predeclared | Targets = max(strict, loose/fallback MDE)+grid-step (standalone) and max(EXP-015 domain MDE, materiality)+grid-step (incremental), read from approved upstream artifacts; non-redundancy enforced (overlap ≤ 0.10, |rho| ≤ 0.05); construction-invalid → path not exercised → INCONCLUSIVE, not faked. | PASS |
| Suite assembly fidelity | `load_suite_manifest` routes ADOPT_LOOSE→loose τ vs STRICT_FALLBACK→materiality from EXP-012 decisions; no upstream decision recomputed/altered. | PASS |
| Exploratory honesty | Unexpected dogfood PASS → `UNEXPECTED_DOGFOOD_OUTPUT` → INCONCLUSIVE (reported as integration observation, not treated as a Phase 004 discovery). | PASS |
| Zero-baseline handling | Finite levels/intervals; no percentage-of-zero. | PASS |
| Complexity budget | 4 measurements (dogfood path, positive path, composition, expected-matrix) / 5 plots / 0 new modules — within 4/5/1. | PASS |
| Code conventions | Imports→constants→manifests→referees→paths→summary→plotting→`main()`; output dirs in orchestration; `tqdm` on dogfood loop; cross-experiment reuse (EXP-009 strategies, EXP-012 loose_referee) verified to resolve. | PASS |
| Phase alignment | Matches design §8 EXP-016 (conclusion), §4 exploratory both-path anchor, §9 FULL_FRAMEWORK_CONCLUDED dependency. | PASS |

## Notes for the auditor (Stage 5, non-blocking)

- The reference book R determines whether the dogfood incremental denominators are
  non-trivial; once R is defined, confirm denominators are reported and not near-empty
  (which would make the dogfood incremental path vacuous).
- Module-level `sys.path.insert` + imports from sibling experiments occur before the
  dependency gate; if EXP-009 `strategies.py` or EXP-012 `loose_referee.py` were absent
  the script would ImportError instead of writing BLOCKED metadata. Both are present, so
  this is informational only.

---

## Manual execution gate

```text
Pre-execution review: APPROVED (execution deferred — see preconditions)

Experiment: EXP-016 - Assembled Suite Composition Anchor
Code: python/experiments/EXP-016/code/run_experiment.py
Expected output: python/experiments/EXP-016/results/

Runs the assembled strict + ratified-loose/fallback + incremental suite on the EXP-009
dogfood negative path and a synthetic positive fixture, confirming both reject and pass
wiring compose end to end.

Do NOT run until: EXP-012 and EXP-015 are COMPLETE, and the dogfood reference book is
recorded at python/experiments/EXP-016/inputs/dogfood_reference_book.csv. The code will
BLOCK (no measurement) until then.
```
