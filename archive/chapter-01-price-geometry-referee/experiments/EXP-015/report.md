# Experiment Report: EXP-015 - Incremental Referee Portfolio-Fitness Calibration

## Status: REFUTED

**Date**: 2026-06-04 (re-validated 2026-06-05 under amendment [A1](../../../docs/experiments-docs/checkpoints/2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md), F03 + F04; outcome unchanged, failure now attributed)
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains; incremental R/C dependence-grid known-truth draws

---

## Question

What incremental net edge beyond a reference signal can the incremental referee reliably detect per domain, and does shared R-C structure cause false positives?

## Hypothesis

The incremental referee has a finite portfolio-fitness MDE at FPR <= `alpha0` on each domain, and redundancy-null FPR remains controlled under the predeclared dependence grid.

## Method Summary

The experiment generated redundancy-null and positive marginal-edge R/C draws across the rho, overlap, lag, and reference-strength grid. It summarized FPR and TPR per dependence cell and derived finite cell MDEs only where construction and precision requirements were met.

## Key Findings

### Finding 1: FPR Was Controlled

Accepted-cell FPR did not exceed `alpha0 = 0.05`. Max FPR was `0.0` on 5m and `0.01` on 1h/4h. This means the failure is not a redundancy-null false-positive problem.

### Finding 2: All Domains Have Failing MDE Cells

`results/domain_mde_summary.csv` reports all domains `REFUTED`:

| Domain | Finite MDE Cells | Failing Cells | Construction-Invalid Cells | Status |
|--------|------------------|---------------|----------------------------|--------|
| 5m | 41 | 1 | 12 | REFUTED |
| 1h | 40 | 2 | 12 | REFUTED |
| 4h | 40 | 2 | 12 | REFUTED |

The failing cells are high-overlap synchronous `null_R` contexts: high rho/high overlap on 5m, moderate and high rho/high overlap on 1h and 4h.

### Finding 3: Construction-Invalid Cells Were Explicit

Each domain had 12 construction-invalid cells due `target_rho_infeasible_for_overlap`, concentrated in high-rho low/medium-overlap combinations. These were reported rather than pooled or forced.

### Finding 4: Failure Attributed to the L2 Leg and BTCUSD (F03)

The F03 diagnostics (`results/leg_pass_rates.csv`, `results/tpr_by_instrument.csv`) localize the refutation. In every failing cell, at the 32 bps edge ceiling, the per-cell verdict pass rate equals the **L2 standalone-significance** pass rate (5m/high `0.75`, 1h/mod `0.784`, 1h/high `0.716`, 4h/mod `0.63`, 4h/high `0.382`) while L1, L4, and L5 are saturated at `1.0` and L3 is `≥ 0.97`. The shortfall is driven by **BTCUSD**, whose standalone-edge TPR plateaus at `0.00`–`0.136` in these high-overlap synchronous cells while the other instruments reach or approach `1.0`. On 5m and 1h, BTCUSD alone holds the pooled rate at `0.75`, just under the `POWER_TARGET = 0.80` floor. The refutation is an operating-characteristic power gap in one leg for one instrument, not a substrate or gate-logic defect (EXP-013 and EXP-014 both PASS).

## Conclusion

**Hypothesis REFUTED.**

The incremental referee controls FPR in accepted cells, but it does not provide finite MDE coverage across the required dependence grid. The Track B portfolio-fitness unit is not validated or frozen for Phase 004 use.

## Limitations

- Worst finite PASS-cell MDEs (`32.0`, `24.0`, `32.0` bps for 5m/1h/4h) are diagnostic only and are not adoptable because failing cells exist.
- The result refutes this confirmed implementation and grid; it does not prove no incremental unit can be built.

## Implications for Future Research

- Phase 003 cannot reach `FULL_FRAMEWORK_CONCLUDED` with a validated fitness unit; the phase outcome is `PARTIAL_SUCCESS` (Track A ratified, Track B not validated).
- Any future incremental-unit work needs a new predeclared scope, now targetable at a specific failure mode: the L2 standalone-significance power gap for high-volatility instruments under high-overlap synchronous dependence.

## Recommended Next Experiments

1. **Follow-up incremental-unit redesign**: Target the L2 power gap — e.g. an instrument-aware edge grid, longer windows for high-volatility instruments, or an L2 reformulation — before rerunning calibration, under a new predeclared scope.
2. **Standalone-only phase decision**: If the operator wants to proceed without a fitness unit, record an explicit Phase 004 rescope.

## Artifacts

| Artifact | Path |
|----------|------|
| Scope | [scope.md](scope.md) |
| Analysis Plan | [analysis-plan.md](analysis-plan.md) |
| Code | [code/](code/) |
| Audit | [audit.md](audit.md) |
| Results | [results.md](results.md) |
| Governance Reviews | [governance/](governance/) |
| Plots | [plots/](plots/) |
