# Audit Report: Experiment EXP-012

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

EXP-012 can be trusted for interpretation. The rerun produced complete fresh-draw ratification outputs, dependency gates passed, the fresh-seed payloads are disjoint from Phase 001/002 construction inputs, and every adoption-rule component is present in `results/adoption_decisions.csv`.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/src/xen/referee_calibration.py` | Holdout exclusion | PASS | `load_analysis_data()` scans required columns, sorts by `CloseTime`, and collects only `slice(0, analysis_rows)` at lines 120-133. |
| `code/run_experiment.py` | Dependency gate | PASS | `gate_dependencies()` is called before measurement at lines 942-949; metadata records EXP-001 PASS and EXP-003/010/011 COMPLETE. |
| `code/run_experiment.py` | Fresh-seed discipline | PASS | `verify_seed_disjointness()` checks payload-input overlap, not benign 32-bit hash collisions, at lines 239-290; `run_metadata.json` records `payload_overlap_count = 0`. |
| `code/run_experiment.py` | Adoption rule | PASS | `decide_adoption()` records FPR, MDE, sub-material, 4h split, underpower, and final verdict components at lines 677-736. |
| `code/run_experiment.py` | Temporal alignment | PASS | Domain construction uses `load_analysis_data()` and `CloseTime` mapping; no chart-type or bar-index alignment is in scope. |
| `code/run_experiment.py` | Progress/output | PASS | Long draw/load/split loops use `tqdm`; result writing is centralized in `main()` at lines 992-1036. |
| `code/loose_referee.py` | Referee variant | PASS | Reuses frozen gate-stack core and changes only the L5 threshold variant required by the scope. |

## Numerical Validation

### Spot Checks

- `adoption_decisions.csv` has exactly 3 rows, one per domain.
- At `alpha0 = 0.05`, all loose-referee FPR values are `0/4000` with Wilson half-width `0.000479739`, satisfying the `<= 0.03` precision rule.
- Fresh loose MDEs equal the Phase 002 operating-point MDEs exactly: 5m `0.5`, 1h `2.0`, 4h `8.0` bps.
- Sub-material rates reproduce Phase 002 within tolerance: 5m `0.399139` vs `0.397590`, 1h `0.027469` vs `0.026224`, 4h `0.0` vs `0.0`.
- The 4h split gate reports single and anchored walk-forward loose MDEs both `8.0` bps, FPR both `0.0`, and `protocols_agree = true`.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|----------------|--------------|-------|
| FPR | `[0, 1]` | `0.0` all domain/referee/alpha rows | YES |
| Wilson half-width | `<= 0.03` for FPR precision | `0.000479739` all FPR rows | YES |
| MDE | finite grid value or scoped inconclusive | finite for all rows | YES |
| Sub-material rate | `[0, 1]` | `0.0` to `0.399139` | YES |

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none found
- Complexity budget: 4 measurements / 4 budgeted, 4 plots / 4 budgeted, 1 local module / 1 budgeted
- Holdout exclusion verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Benign seed integer collisions recorded**
   - Description: `run_metadata.json` reports 6 benign 32-bit integer collisions against about 7.1 expected by chance. The payload-input overlap is zero, so this is not seed reuse.

2. **Strict rows are diagnostic context**
   - Description: Strict-referee rows remain useful for comparison, but EXP-012's adoption decision is defined only for the fixed EXP-011 loose operating point plus 4h split gate.

## Re-Audit Requirements

None.
