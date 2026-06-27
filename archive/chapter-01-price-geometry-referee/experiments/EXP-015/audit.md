# Audit Report: Experiment EXP-015

> **Re-audited 2026-06-05 after the amendment [A1](../../../docs/experiments-docs/checkpoints/2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md) re-run (F03 per-leg/per-instrument diagnostics, F04 contiguous block — a no-op for the per-row grid construction).** Verdict unchanged: PASS (outputs trustworthy; hypothesis REFUTED). The re-run regenerated all summaries and added `leg_pass_rates.csv` and `tpr_by_instrument.csv`, which now attribute the refutation to the L2 standalone-significance leg driven by BTCUSD.

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 4

The EXP-015 outputs are valid and support interpretation of a refuted hypothesis. The run correctly hard-gated EXP-013, EXP-014, and the EXP-003 strict MDE map, produced the full dependence-grid summaries plus the F03 per-leg and per-instrument diagnostics, preserved construction-invalid cells instead of pooling them, and classified every domain as `REFUTED` because at least one qualifying dependence cell had no finite MDE over the inherited edge grid.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Dependency gate | PASS | `dependency_manifest()` requires EXP-013 PASS, EXP-014 PASS, and the EXP-003 MDE map before measurement at lines 158-186. |
| `python/src/xen/referee_calibration.py` | Holdout exclusion | PASS | `load_analysis_data()` sorts by `CloseTime` and collects only the first 70 percent analysis slice at lines 120-133. |
| `code/run_experiment.py` | Grid construction | PASS | `build_cells()` and task construction enumerate the scoped dependence grid; construction-invalid cells are retained in outputs. |
| `code/run_experiment.py` | FPR/TPR/MDE summaries | PASS | `summarize_fpr()`, `summarize_tpr()`, and `summarize_cell_mde()` generate per-cell summaries without pooling away dependence contexts. |
| `code/run_experiment.py` | F03 leg/instrument diagnostics | PASS | Per-leg pass rates (`leg_pass_rates.csv`) and per-instrument TPR (`tpr_by_instrument.csv`) are written so failing cells are attributable; `POWER_TARGET = 0.80` is the per-cell pooled-TPR floor for a finite MDE (line 73, 827). |
| `code/run_experiment.py` | Domain verdict | PASS | `summarize_domain_mde()` sets domain status to `REFUTED` when any qualifying cell fails at lines 913-957. |
| `code/run_experiment.py` | Output integrity | PASS | `main()` writes dependency, grid, construction, draw, FPR, TPR, MDE, domain, and invalid-cell outputs at lines 1114-1124. |
| `python/src/xen/incremental_referee.py` | Real-price incremental estimator | PASS | Incremental P&L uses scoped real-return arrays and denominator rows; no chart-type prices are in scope. |

## Numerical Validation

### Spot Checks

- `domain_mde_summary.csv`: all three domains are `REFUTED`.
- Finite non-adoptable cell MDEs exist, but every domain has failing cells: 5m has 41 finite PASS cells and 1 `FAIL_NO_FINITE_MDE`; 1h has 40 PASS and 2 failures; 4h has 40 PASS and 2 failures.
- Failing qualifying cells:
  - 5m: high rho / high overlap / synchronous / null_R.
  - 1h: moderate rho / high overlap / synchronous / null_R, and high rho / high overlap / synchronous / null_R.
  - 4h: moderate rho / high overlap / synchronous / null_R, and high rho / high overlap / synchronous / null_R.
- Redundancy-null FPR remains controlled: FPR status counts are 42 PASS and 12 construction-invalid cells per domain; max FPR is `0.01` for 1h/4h and `0.0` for 5m, all below `alpha0 = 0.05`.
- Construction-invalid rows are the expected infeasible high-rho low/medium-overlap combinations: 12 per domain, `target_rho_infeasible_for_overlap`, not silent omissions.
- F03 attribution cross-check: in `leg_pass_rates.csv` at planted edge `32.0` bps the per-cell verdict pass rate equals the L2 pass rate in all five failing cells (5m/high `0.75`, 1h/mod `0.784`, 1h/high `0.716`, 4h/mod `0.63`, 4h/high `0.382`) while L1/L4/L5 are `1.0` and L3 ≥ `0.97`; `tpr_by_instrument.csv` shows BTCUSD at `0.00`–`0.136` in those cells against the other instruments at or near `1.0`. The failures are below the `0.80` power floor, consistent with `domain_mde_summary.csv` `FAIL_NO_FINITE_MDE`.
- Accepted draws total 210,000 per domain, with denominator ranges: 5m `16519` to `102032`, 1h `1384` to `8573`, 4h `301` to `2111`.
- Holdout exclusion verified numerically: `analysis_metadata.csv` `split_index / return_rows` is `0.698`–`0.701` for all 12 instrument/domain cells.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|----------------|--------------|-------|
| FPR | `<= alpha0` for PASS cells | max `0.01` | YES |
| FPR Wilson half-width | `<= 0.03` | max `0.005444` observed in failing-cell rows | YES |
| Domain status | rule-derived | all `REFUTED` due failing cells | YES |
| Construction-invalid accounting | explicit, not pooled | 12/domain | YES |

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none found
- Complexity budget: 4 measurements / 4 budgeted, 5 plots / 5 budgeted, 0 new modules / 1 budgeted
- Holdout exclusion verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Hypothesis refuted by sensitivity, not FPR leakage**
   - Description: Redundancy-null FPR is controlled; refutation comes from failure to reach finite MDE in high-overlap synchronous null-R contexts.

2. **Refutation localized to the L2 leg / BTCUSD (F03)**
   - Description: The F03 diagnostics attribute every failing cell to the L2 standalone-significance leg, driven by BTCUSD's standalone-edge TPR plateau (`0.00`–`0.136` at the 32 bps ceiling). L1/L3/L4/L5 are saturated. This is a diagnostic localization, not a correctness defect — the substrate (EXP-013) and gate logic (EXP-014) are independently validated.

3. **Construction invalidity is expected for some grid points**
   - Description: High-rho with low/medium overlap is infeasible under the accepted construction bands and is reported as construction-invalid, matching scope.

4. **Domain headline finite MDEs are not adopted**
   - Description: `domain_mde_bps` reports worst finite PASS-cell MDEs, but the domain status remains `REFUTED` because failing cells exist.

## Re-Audit Requirements

None.
