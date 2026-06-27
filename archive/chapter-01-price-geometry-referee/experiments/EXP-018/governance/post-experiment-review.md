# Post-Experiment Governance Review - EXP-018

**Experiment:** EXP-018 - Revised Incremental Referee Portfolio-Fitness Calibration
**Stage:** 8 (post-experiment)
**Date:** 2026-06-05
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`
**Phase:** 2026-06-05-003b-incremental-unit-redesign

---

## Verdict

```text
VERDICT: APPROVE
```

## Constraint Checks

| Constraint | Finding | Status |
| --- | --- | --- |
| Audit quality | Audit recomputes FPR/TPR counts from draw-level artifacts, verifies revised-gate L2 absence, and records no critical or warning issues. | PASS |
| Results honesty | `results.md` reports finite MDE support only for construction-accepted cells and discloses all construction-invalid cells. | PASS |
| Scope compliance | Interpretation stays within the frozen dependence grid, inherited edge grid, and revised incremental referee. | PASS |
| Holdout exclusion | Code uses the shared first-70% chronological loader before domain construction. | PASS |
| Look-ahead prevention | R/C and returns align by `CloseTime`; lead/lag construction is scoped to synthetic positions, not future returns. | PASS |
| Real-price discipline | Returns are real OHLC domain returns; no chart-type construction prices are in scope. | PASS |
| Documentation | `report.md` is self-contained and index updates record finite 12/16/32 bps revised-unit MDEs. | PASS |

## Conclusion

EXP-018 is post-experiment approved. It validates the revised incremental / portfolio-fitness unit for EXP-019 composition, with construction-invalid cells explicitly disclosed.
