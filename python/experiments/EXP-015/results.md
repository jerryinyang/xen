# Results: Experiment EXP-015

> **✓ Re-validated under amendment [A1](../../../docs/experiments-docs/checkpoints/2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md) (F03 + F04).** Re-run 2026-06-05 with per-leg states retained and the new `leg_pass_rates.csv` / `tpr_by_instrument.csv` diagnostics (F03). The contiguous-series block-length fix (F04) is a no-op here because the dependence-grid construction uses per-row positions. The keystone outcome **remains REFUTED** in all three domains. What was previously an opaque "Alternative Explanations" caveat is now **diagnosed**: the failing cells fail on a single gate leg (**L2 standalone significance**) driven by a single instrument (**BTCUSD**), not on the marginal-P&L substrate (EXP-013 PASS) or the gate logic (EXP-014 PASS).

## Summary

EXP-015 refutes the incremental referee's portfolio-fitness calibration claim under the predeclared dependence grid. Redundancy-null FPR remains controlled (max `0.01`, no cell exceeds `alpha0 = 0.05`), but every domain has at least one qualifying dependence cell with no finite MDE over the inherited edge grid (5m: 1 cell, 1h: 2 cells, 4h: 2 cells). The incremental unit therefore does not reach the Phase 003 calibrated fitness-check requirement. The F03 diagnostics localize the failure precisely: in high-overlap synchronous `null_R` contexts the candidate's **standalone significance leg (L2)** cannot clear its CI-lower-bound floor for **BTCUSD** even at the 32 bps edge ceiling, which alone holds the pooled per-cell TPR below the `POWER_TARGET = 0.80` floor.

## Detailed Findings

### FPR Was Controlled Under Accepted Dependence Cells

- **Observation**: Redundancy-null FPR did not exceed `alpha0 = 0.05` in any cell.
- **Evidence**: `fpr_summary.csv` has 42 PASS cells per domain plus 12 construction-invalid cells per domain. Max FPR is `0.0` for 5m and `0.01` for 1h/4h; zero cells exceed `alpha0`.
- **Interpretation**: The failure is not shared-structure false-positive leakage.

### Finite MDE Was Not Available in All Qualifying Cells

- **Observation**: Each domain has at least one `FAIL_NO_FINITE_MDE` cell.
- **Evidence**: `domain_mde_summary.csv` reports:
  - 5m: 41 finite MDE cells, 1 failing cell, 12 construction-invalid cells, status `REFUTED`.
  - 1h: 40 finite MDE cells, 2 failing cells, 12 construction-invalid cells, status `REFUTED`.
  - 4h: 40 finite MDE cells, 2 failing cells, 12 construction-invalid cells, status `REFUTED`.
- **Interpretation**: The predeclared domain-level success rule fails because a single qualifying cell with no finite MDE refutes calibration for that dependence stress.

### Failures Concentrated in High-Overlap Synchronous Null-R Contexts

- **Observation**: Every failing cell is synchronous, high-overlap, `null_R`.
- **Evidence** (`underpowered_or_invalid_cells.csv`, `status = FAIL_NO_FINITE_MDE`):
  - 5m: high rho / high overlap / synchronous / null_R.
  - 1h: moderate rho and high rho, both high overlap / synchronous / null_R.
  - 4h: moderate rho and high rho, both high overlap / synchronous / null_R.
- **Interpretation**: In these contexts, the incremental referee does not reliably reach the power floor within the inherited edge grid, even though FPR is controlled.

### Failure Attributed to the L2 Standalone-Significance Leg (F03)

- **Observation**: In every failing cell, four of the five gate legs pass at ~1.0 even at the 32 bps edge ceiling; only **L2 (standalone candidate net edge CI lower > 0)** sits below the `0.80` power floor and pins the pooled verdict pass rate.
- **Evidence** (`leg_pass_rates.csv`, planted edge `32.0` bps, pooled across instruments, n=500):

  | Domain | rho | L1 | L2 | L3 | L4 | L5 | verdict |
  |--------|-----|----|----|----|----|----|---------|
  | 5m | high | 1.00 | **0.75** | 1.00 | 1.00 | 1.00 | 0.75 |
  | 1h | moderate | 1.00 | **0.784** | 1.00 | 1.00 | 1.00 | 0.784 |
  | 1h | high | 1.00 | **0.716** | 1.00 | 1.00 | 1.00 | 0.716 |
  | 4h | moderate | 1.00 | **0.63** | 0.982 | 1.00 | 1.00 | 0.63 |
  | 4h | high | 1.00 | **0.382** | 0.970 | 1.00 | 1.00 | 0.382 |

- **Interpretation**: The verdict pass rate equals the L2 pass rate in every failing cell — L2 is the single binding leg. L1 (readiness), L4 (cross-market), and L5 (materiality) are saturated, and L3 (incremental-beyond-R control) only dips marginally on 4h. The refutation is a standalone-significance power problem, not a redundancy-control, materiality, or readiness problem.

### The Binding Leg Is Driven by a Single Instrument (BTCUSD)

- **Observation**: The pooled L2/verdict shortfall is almost entirely one instrument: BTCUSD's standalone-edge TPR plateaus far below the power floor in high-overlap synchronous cells, while the other three instruments mostly saturate.
- **Evidence** (`tpr_by_instrument.csv`, per-instrument TPR at planted edge `32.0` bps):

  | Domain / rho | BTCUSD | EURUSD | USTEC | XAUUSD | pooled |
  |--------------|--------|--------|-------|--------|--------|
  | 5m / high | **0.00** | 1.00 | 1.00 | 1.00 | 0.75 |
  | 1h / moderate | **0.136** | 1.00 | 1.00 | 1.00 | 0.784 |
  | 1h / high | **0.00** | 1.00 | 0.864 | 1.00 | 0.716 |
  | 4h / moderate | **0.04** | 1.00 | 0.528 | 0.952 | 0.63 |
  | 4h / high | **0.008** | 1.00 | 0.128 | 0.392 | 0.382 |

- **Interpretation**: On 5m and 1h, BTCUSD alone caps the cell — the other three instruments reach 1.0, so a single instrument stuck at 0.0 pulls the pooled rate to 0.75, just under the 0.80 floor. On 4h, the weakest domain, USTEC and XAUUSD also begin to fall, so the shortfall is broader but still BTCUSD-led. The most likely mechanism: in high-overlap synchronous `null_R` construction the highest-volatility instrument's *standalone* net-edge bootstrap CI lower bound cannot clear zero at the tested edge magnitudes, so L2 rejects the candidate even when its planted marginal edge is large.

### Construction-Invalid Cells Were Reported, Not Pooled

- **Observation**: Each domain has 12 construction-invalid cells.
- **Evidence**: `underpowered_or_invalid_cells.csv` lists `CONSTRUCTION_INVALID` for high-rho low/medium-overlap combinations (`target_rho_infeasible_for_overlap`).
- **Interpretation**: The implementation respected the scope by refusing impossible grid points rather than silently changing the dependence grid.

### Holdout Discipline Preserved

- **Observation**: Only the first 70 percent analysis slice was loaded per instrument/domain.
- **Evidence**: `analysis_metadata.csv` `split_index / return_rows` is `0.698`–`0.701` across all 12 cells; train windows end mid-2024/2025 while sources extend into 2026.
- **Interpretation**: The final 30 percent holdout was never read, consistent with the governance OOS rule.

## Hypothesis Verdict

**REFUTED**

H-incr-floor is refuted in all three domains. The incremental referee controls redundancy-null FPR in accepted cells, but it does not produce finite MDE coverage across the required dependence grid. The Phase 003 Track B calibrated fitness-check unit is therefore not validated. The F03 diagnostics localize the cause to the L2 standalone-significance leg under high-overlap synchronous `null_R` stress, driven principally by BTCUSD.

## Limitations

- The finite MDE values reported for PASS cells — 5m `32.0`, 1h `24.0`, 4h `32.0` bps as worst finite PASS-cell MDEs — are not adoptable domain MDEs because failing cells exist.
- Construction-invalid high-rho low/medium-overlap cells identify infeasible construction targets under the chosen bands; they are not statistical failures but they narrow what the grid can test.
- The attribution is descriptive: it identifies *which* leg and instrument fail, not a proof that an L2 redesign would lift the cell above the power floor. That would require a new predeclared scope.

## Alternative Explanations

- The failure could in principle be a property of the high-overlap synchronous *construction* (concentrating the candidate's standalone signal into few independent bars) rather than the L2 leg definition per se. The two are coupled: L2 evaluates standalone significance, and the construction is what starves it of independent observations for high-volatility instruments. Either framing leaves the incremental unit unvalidated under the predeclared grid.
- The marginal-P&L substrate is not implicated: EXP-013 supports it (108/108 recovery, 0 phantom) and EXP-014 supports the gate logic (7/7 verdicts, 35/35 leg states). The failure is in operating-characteristic power, not mechanics.

## Recommended Next Steps

1. Do not freeze the incremental fitness unit for Phase 004 use from this experiment.
2. Record Phase 003 as unable to reach `FULL_FRAMEWORK_CONCLUDED`; outcome is `PARTIAL_SUCCESS` (Track A ratified, Track B not validated).
3. Any incremental-unit redesign should target the L2 standalone-significance power gap in high-overlap synchronous contexts (e.g. an instrument-aware edge grid, longer windows for high-volatility instruments, or an L2 reformulation) under a **new** predeclared scope — not an EXP-015 reinterpretation.
