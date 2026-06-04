# Audit Report: Experiment EXP-011

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

EXP-011 is a deterministic result-level synthesis. The audit did not rerun
`code/run_experiment.py`; it inspected the approved scope, plan, code, saved
results, and plots, then independently recomputed the loss selections from the
saved CSV/JSON artifacts. The saved recommendations are internally consistent
and match the predeclared Loss A/B/C rules.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Scope compliance | PASS | Implements result-level post-processing only: dependencies at lines 63-81, decision table at lines 174-188, sub-material reconstruction at lines 194-250, loss evaluation at lines 359-393, overlays at lines 399-464, outputs at lines 596-696. |
| `code/run_experiment.py` | Holdout exclusion | PASS | No raw market data is loaded. Searches found no `data/timebars`, `scan_parquet`, `read_parquet`, or raw-data glob in EXP-011 code; the script reads only upstream result CSV/JSON artifacts. |
| `code/run_experiment.py` | Draw-key alignment | PASS | The EXP-006 to EXP-003 join uses the full composite key `["instrument", "domain", "scenario", "generator", "edge_bps", "draw", "alpha"]` at line 108 and joins on that key at lines 219 and 227-228; row-loss guards raise on unmatched keys at lines 223-233. |
| `code/run_experiment.py` | NaN and zero-baseline handling | PASS | `sub_rate` is defined as `0.0` when `pass_count == 0` at lines 242-246; saved `sub_material_by_tau.csv` has 23 zero-pass groups and no NaN requirement leak into decisions. |
| `code/run_experiment.py` | Dependency gates | PASS | Core dependencies EXP-003/006/007 hard-fail if incomplete at lines 140-146. This run's metadata records all dependencies EXP-003/005/006/007/008/009/010 as `COMPLETE`. |
| `code/run_experiment.py` | Memory/performance | PASS | The only large step projects and filters draw CSVs before collection at lines 203-217, then aggregates before plotting; plots consume small Step 2-6 tables only. |
| `code/run_experiment.py` | Organization/import side effects | PASS | VAL-style sections are present. Directories are created only inside `main()` at lines 643-644. |
| `code/run_experiment.py` | Plot generation | PASS | Four scoped plots are written at lines 693-696. PNG headers confirm nonempty images: `loss_vs_tau.png` 2233x667, `mde_vs_tau_frontier.png` 2215x667, `consistency_matrix.png` 1132x657, `adoption_overlay.png` 1334x733. |
| `code/loss_functions.py` | Loss-rule correctness | PASS | Frozen frontier and coefficients are named at lines 23-39. Loss A, B, C, and the consistency verdict implement the scope rules at lines 61-160. |

## Numerical Validation

### Spot Checks

Independent result-level checks from saved artifacts found:

- `run_metadata.json`: `overall_status = COMPLETE`, `measurements_produced = true`, `submaterial_repro_check = true`, `inconclusive_domains = []`.
- Dependency tokens in metadata: EXP-003, EXP-005, EXP-006, EXP-007, EXP-008, EXP-009, and EXP-010 all `COMPLETE`; EXP-006 additionally `strict_reference_pass = true`; EXP-007 `structural_equivalence_pass = true`.
- Output dimensions match scope: `decision_table.csv` 21 rows, `sub_material_by_tau.csv` 210 rows, `loss_evaluation.csv` 9 rows, `recommendation.csv` 3 rows.
- Every decision row is reportable: `fpr_wilson_half_width = 0.000479739258416217` and `fpr_wilson_upper = 0.000959478516832434`, both well below the predeclared gates.
- The `sub_rate` used in `decision_table.csv` matches `sub_material_by_tau.csv` at the operating MDE for all 21 decision rows.

Manual recomputation of the three losses reproduced the saved recommendations:

| Domain | Loss A tau* | Loss B tau* | Loss C tau* | Saved verdict | Independent check |
|--------|-------------|-------------|-------------|---------------|-------------------|
| 5m | 0.75 | 0.75 | 0.25 | LOSS_SENSITIVE, spread 2, driver `sub_material` | MATCH |
| 1h | 0.25 | 0.25 | 0.0 | ROBUST, spread 1 | MATCH |
| 4h | 0.5 | 0.5 | 0.0 | LOSS_SENSITIVE, spread 2, driver `blind_band` | MATCH |

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|----------------|--------------|-------|
| `fpr` | [0, 1] | 0.0 for all 21 decision rows | YES |
| `fpr_wilson_upper` | <= 0.05 for selectable rows | 0.000959478516832434 for all rows | YES |
| `mde_bps` | finite grid value | 5m 0.5-2.0, 1h 2.0-8.0, 4h 8.0-16.0 | YES |
| `sub_rate` at operating MDE | [0, 1] | 5m 0.0-0.4965, 1h 0.0-0.054653679653679656, 4h 0.0 | YES |
| `pass_count` in sub-material table | >= 0 | 0-2000 | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| FPR precision | Wilson upper 0.000959478516832434 for all decision rows | YES | FPR is non-binding but retained by predeclaration. |
| 5m sub-material rate at headline tau | 0.39759036144578314 | YES | Below the 0.50 materiality caveat, but high enough to drive loss sensitivity. |
| 1h cross-loss spread | one grid step | YES | Meets the predeclared ROBUST rule. |
| 4h cross-loss spread | two grid steps | YES | Loss C favors the zero-buffer endpoint; Loss A/B prefer tau 0.5 because blind-band cost dominates. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|------------|--------|----------|
| Result-level synthesis | Upstream artifacts are complete and frozen | YES | Metadata tokens all complete; `submaterial_repro_check = true`. |
| Loss A | FPR upper bound gates selectable cells, then MDE/sub-material/tau tie-breaks apply | YES | All cells pass FPR; independent selection reproduces 5m 0.75, 1h 0.25, 4h 0.5. |
| Loss B | Normalized blind-band, FPR, and sub-material terms use unit weights | YES | Independent scalar values match `loss_evaluation.csv`. |
| Loss C | Material-edge prior uses fixed grid points inside `[materiality, 4 * materiality]` | YES | `run_metadata.json` records 5m `{0.5,1.0,2.0}`, 1h `{2.0,4.0}`, 4h `{4.0,8.0,12.0}`. |
| Context overlays | EXP-008/009/010 do not re-select tau | YES | Overlays are written only to `adoption_rule.json`; recommendations come from Loss A. |

## Results Plausibility

The recommendations are plausible against Phase 002 context:

- 5m recommends `tau = 0.75` with MDE `0.5` bps and sub-material rate `0.39759036144578314`; this avoids the higher sub-material burden of `tau = 0`/`0.25` while retaining the lower MDE.
- 1h recommends `tau = 0.25` with MDE `2.0` bps and sub-material rate `0.026223776223776224`; all three losses are within one grid step.
- 4h recommends `tau = 0.5` with MDE `8.0` bps and sub-material rate `0.0`; Loss C prefers `tau = 0`, making the domain loss-sensitive.
- Adoption caveats are present: EXP-005 `DETECTED_FLOOR` for all domains, EXP-009 `n_at_or_above_mde = 0` for all domains, EXP-008 material per-instrument overlays for EURUSD/1h and EURUSD/XAUUSD 4h, and EXP-010 walk-forward materiality on 1h/4h.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none affecting the completed run
- Complexity budget: 2 / 2 statistical operations, 4 / 4 plots, 1 / 1 new modules
- Holdout exclusion verified: YES
- Recommendation status: all three domains `RECOMMENDED`; no inconclusive domains

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Context dependencies are soft-gated in code but complete in this run**
   - File: `code/run_experiment.py`, lines 153-159 and 399-464
   - Description: EXP-005/008/009/010 context artifacts are omitted from overlays if missing instead of making the domain inconclusive.
   - Impact: No impact on the saved EXP-011 results because all four context dependencies were present and `COMPLETE`.
   - Follow-up: If this script is reused as a template, make context-gating semantics match the future scope exactly.

## Re-Audit Requirements

None. The audit passes without required revisions.
