# Results: Experiment EXP-018

## Summary

EXP-018 supports the revised incremental referee calibration for the accepted dependence grid. All 126 construction-accepted dependence cells control redundancy-null FPR and attain finite MDE; no cell fails FPR or MDE criteria. Worst-case headline MDEs are 12 bps on 5m, 16 bps on 1h, and 32 bps on 4h. The EXP-015 stress corner, synchronous/high-overlap/null_R at moderate/high rho, now passes in every domain.

## Detailed Findings

### Accepted Dependence Cells All Passed FPR and MDE Criteria

- **Observation**: 126/126 construction-accepted grid cells have `status = PASS` in `cell_mde_summary.csv`; 36 cells are construction-invalid.
- **Evidence**: `domain_mde_summary.csv` reports, for each domain, 42 finite MDE cells, 0 failing cells, and 12 construction-invalid or underpowered cells out of 54 total cells.
- **Interpretation**: The revised unit has a finite detection floor wherever the predeclared dependence construction is feasible.

### Redundancy-Null FPR Is Controlled

- **Observation**: Accepted-cell FPR ranges from 0.0 to 0.004, below `alpha0 = 0.05`.
- **Evidence**: `fpr_summary.csv` has 126 PASS rows; max Wilson half-width is `0.006684203250090802`, below the 0.03 precision target.
- **Interpretation**: Shared R-C structure does not manufacture false positive incremental passes under the accepted grid.

### Worst-Case Domain MDEs Are Finite But Higher Than Standalone Strict MDEs

- **Observation**: `domain_mde_summary.csv` reports domain MDEs of 12.0 bps (5m), 16.0 bps (1h), and 32.0 bps (4h).
- **Evidence**: These are the maximum finite PASS-cell MDEs across each domain's accepted dependence contexts.
- **Interpretation**: The revised portfolio-fitness unit is calibrated, but conservative; it detects material incremental edges only at or above these worst-case levels.

### EXP-015 Stress Corner Is Resolved

- **Observation**: The synchronous/high-overlap/null_R corner passes across independent, moderate, and high rho in every domain.
- **Evidence**: `binding_corner_summary.csv` reports PASS FPR and PASS cell MDE for all nine domain/rho rows. The moderate/high-rho A1/F03 stress cells have MDEs: 5m `1.0`, 1h `8.0`, 4h `24.0`.
- **Interpretation**: Removing standalone L2 resolves the specific L2/BTCUSD sensitivity failure that refuted EXP-015.

### Construction-Invalid Cells Are Disclosed

- **Observation**: 36 cells are `CONSTRUCTION_INVALID`, all with reason `target_rho_infeasible_for_overlap`.
- **Evidence**: `underpowered_or_invalid_cells.csv` contains 12 invalid cells per domain; construction diagnostics show 180,000 invalid construction rows and 630,000 accepted rows.
- **Interpretation**: These cells are infeasible combinations of high rho with low overlap, not failed inference cells. They should remain excluded from the support claim.

## Hypothesis Verdict

**SUPPORTED**

The revised incremental referee has a finite portfolio-fitness MDE at controlled FPR for every construction-accepted dependence-grid cell in each domain, and the explicit EXP-015 failure corner now passes. EXP-018 therefore validates the revised incremental unit for Phase 003b use, with disclosed construction-infeasible cells.

## Limitations

- The support claim applies to construction-accepted cells; high-rho/low-overlap infeasible cells are not measured.
- Worst-case MDEs are materially higher than the strict standalone MDE map, especially 5m and 4h.
- The experiment calibrates synthetic known-truth dependence draws, not real candidate families.

## Alternative Explanations

- The higher MDE map may reflect the stricter L5 CI-lower materiality requirement and dependence-grid stress, not only intrinsic incremental-unit weakness.
- Construction infeasibility is a property of the predeclared rho/overlap grid; a differently parameterized grid could have different infeasible regions and would require a new scope.

## Recommended Next Steps

1. Use EXP-018 domain MDEs as the revised incremental-unit dependency for EXP-019 composition.
2. Preserve `binding_corner_summary.csv`, `leg_pass_rates.csv`, and `tpr_by_instrument.csv` as diagnostics for any future incremental-unit revision.
