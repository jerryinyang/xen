# Pre-Execution Governance Review - EXP-018

**Experiment:** EXP-018 - Revised Incremental Referee Portfolio-Fitness Calibration  
**Stage:** 4 (pre-execution)  
**Date:** 2026-06-05  
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `python/src/xen/incremental_referee.py`  
**Phase:** 2026-06-05-003b-incremental-unit-redesign (ACTIVE)

---

## Verdict

```text
VERDICT: APPROVE
```

The artifacts require no revision. EXP-018 reuses the prior EXP-015 dependence-grid
calibration harness and replaces only the gate row with the Phase 003b revised
formula: L1 and L3 and L4_prime and strict-L5; L2 absent.

Execution preconditions are hard-gated in `dependency_manifest()`:

1. EXP-013 `overall_status == PASS`.
2. EXP-017 `overall_status == PASS`.
3. EXP-003 strict gate-stack MDE map present for the `R_at_strict_mde` reference strength.

---

## Constraint checks

| Constraint | Finding | Status |
|---|---|---|
| Phase alignment | Matches active design H-revised-floor and EXP-018 scope: unchanged P3-D-dependence grid, binding synchronous/high-overlap/null_R corner retained, worst-case per-cell MDE aggregation. | PASS |
| Revised gate | Calls `revised_incremental_gate_row()` and records retained leg columns `L1_readiness`, `L3_reference_control`, `L4_no_material_sign_reversal`, and `L5_strict_materiality`; old L2 diagnostics are absent from draw rows. | PASS |
| Estimator safety | Uses `incremental_gate_core`, `marginal_net_series`, `per_bar_incremental_cost`, and `incremental_edge_ci` paths unchanged; no shared estimator or CI path is modified. | PASS |
| Holdout exclusion | Uses `load_analysis_data()` first-70% chronological analysis slice before domain construction; no code path reads the final 30% global holdout. | PASS |
| Look-ahead / temporal | R/C positions are generated from seeded latent state and aligned to real domain returns by `CloseTime`; lead/lag applies to synthetic C positions, not future returns. | PASS |
| Real-price discipline | Reference and incremental edges are planted/evaluated on real OHLC domain returns only. No HA/Renko/chart-type prices are in scope. | PASS |
| Dependence grid | Full grid over rho, overlap, lag, and reference strength is retained with acceptance bands and construction-invalid reporting before outcome interpretation. | PASS |
| MDE aggregation | FPR and TPR are summarized per dependence cell; domain MDE is the maximum finite qualifying cell MDE, not a pooled average. | PASS |
| Diagnostics | Retained-leg pass rates and per-instrument TPR outputs preserve the A1/F03 diagnosability requirement for any second refutation. | PASS |
| Progress / bounded outputs | `tqdm` wraps load and draw loops; plot inputs are summary tables, not full large frames. | PASS |
| Complexity budget | 4 measurements / 5 plots / 0 new modules, within the 4/5/1 budget. | PASS |
| Code conventions | Imports before constants; output dirs in orchestration; sectioned helpers; concise logging; no silent deduplication; no repeated heavy plotting loads. | PASS |

## Verification

- Syntax compilation passed with `python3 -m py_compile` for `python/src/xen/incremental_referee.py` and `python/experiments/EXP-018/code/run_experiment.py`.
- The experiment script itself was not executed inside the pipeline.

---

## Manual execution gate

```text
Pre-execution review: APPROVED

Experiment: EXP-018 - Revised Incremental Referee Portfolio-Fitness Calibration
Code: python/experiments/EXP-018/code/run_experiment.py
Expected output: python/experiments/EXP-018/results/

Constructs known-truth R/C draws across the unchanged dependence grid on the
first-70% analysis slice, applies the revised incremental referee, and reports
per-cell FPR, TPR, finite MDE, retained-leg diagnostics, and worst-case domain MDE.

Please run the experiment code after EXP-017 reports overall_status PASS and confirm
when complete. EXP-018 must validate before EXP-019 can measure composition.
```

---

## Addendum — Amendment B1 refresh (2026-06-05)

Post-approval, [amendment B1](../../../../docs/experiments-docs/checkpoints/2026-06-05-003b-incremental-unit-redesign/amendments/2026-06-05-B1-pre-execution-review-corrections.md) applied these code changes, all verdict-neutral or strictly more conservative:

- **F02 (verdict rollup):** `overall_status = COMPLETE` now requires **every** in-scope domain to conclude SUPPORTED with a finite worst-case MDE (any REFUTED → REFUTED; any INCONCLUSIVE → INCONCLUSIVE). Matches design §9; strictly more conservative, so it cannot manufacture a pass.
- **F03 (binding corner):** new `binding_corner_summary.csv` + `binding_corner_status` metadata explicitly report the synchronous/high-overlap/null_R corner across all three ρ levels, flagging the moderate/high-ρ A1/F03 stress cells. Added reporting only — budget unchanged (4/5/1).
- **F07 (efficiency):** the draw loop passes `compute_standalone=False`; the skipped standalone (L2) bootstrap is unused by the revised gate and every result is byte-identical (independent per-bootstrap seeds). No estimator/CI path changed → no EXP-013 re-run.

`py_compile` re-passes. Verdict remains **APPROVE**; the manual-execution gate above is unaffected.
