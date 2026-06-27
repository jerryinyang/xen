# Results: Experiment EXP-005

## Summary

EXP-005 supports the Phase 002 keystone claim for the scoped realistic-candidate class. At `alpha0 = 0.05`, the frozen Phase 001 gate stack kept pooled-domain FPR at `0.0000` in every domain and detected the realistic candidate at the exact EXP-003 gate MDE with pooled TPR `1.0000` on 5m, `0.9850` on 1h, and `0.9465` on 4h. Candidate sanity checks passed, result tables passed audit, and all per-instrument headline rows also classified as `DETECTED_FLOOR`.

## Detailed Findings

### The Gate Stack Detects the 1.0x MDE Candidate in Every Domain

- **Observation**: The headline 1.0x MDE rows all clear the predeclared TPR target of `>= 0.80` with Wilson half-width `<= 0.05`.
- **Evidence**:

| Domain | MDE bps | Gate FPR | FPR half-width | Gate TPR at 1.0x MDE | TPR half-width | Status |
|--------|---------|----------|----------------|----------------------|----------------|--------|
| 5m | 1.0 | 0.0000 | 0.000480 | 1.0000 | 0.000959 | DETECTED_FLOOR |
| 1h | 4.0 | 0.0000 | 0.000480 | 0.9850 | 0.005403 | DETECTED_FLOOR |
| 4h | 12.0 | 0.0000 | 0.000480 | 0.9465 | 0.009890 | DETECTED_FLOOR |

- **Interpretation**: Under the predeclared imperfect-candidate construction, the oracle-calibrated EXP-003 MDE map behaves as an honest pooled-domain detection floor. The gate is not structurally blind to this weak-but-real candidate at the mapped MDE.

### Sub-MDE Detection Is Not Uniform, but It Was Not Required

- **Observation**: At `0.5x` MDE, gate-stack TPR is below the target in all domains: 5m `0.024`, 1h `0.371`, and 4h `0.502`. At `1.5x` and `2.0x`, TPR is effectively saturated in every domain.
- **Evidence**: `tpr_summary.csv`; `plots/tpr_vs_multiplier.png`.
- **Interpretation**: The gate has a sharp transition around the calibrated MDE for this candidate. EXP-005 supports the MDE floor claim, but it does not show that the strict gate reliably detects materially sub-MDE realistic edges.

### False Positives Remain Controlled

- **Observation**: Gate-stack pooled FPR is `0/4000` null verdicts in every domain at `alpha0 = 0.05`; the Wilson half-width is `0.000480`. The minimal baseline diagnostic FPR is near nominal but below `alpha0`: 5m `0.02375`, 1h `0.02350`, 4h `0.02500`.
- **Evidence**: `fpr_summary.csv`; `plots/fpr_by_domain_referee.png`.
- **Interpretation**: The EXP-005 candidate/noise construction did not break the Phase 001 stringency property. The gate maintained the conservative false-positive behavior measured in EXP-003.

### Candidate Construction Passed the Sanity Gate

- **Observation**: Overall active rate is `0.799997` and active match rate is `0.750005`; every aggregated cell stays within the predeclared `+/- 0.02` tolerance. Positive calibration absolute error ranges from `0.000005` to `0.129769` bps.
- **Evidence**: `candidate_sanity.csv`; `plots/candidate_diagnostics.png`; audit range checks.
- **Interpretation**: The measured detection result is attributable to the predeclared realistic candidate, not an accidental oracle-like signal or an inactive/noisy construction failure.

### Per-Instrument Rows Do Not Reveal Masked Blindness

- **Observation**: All 12 per-instrument headline rows at `1.0x` MDE classify as `DETECTED_FLOOR` with `under_powered=false`. The weakest headline cell is BTCUSD/4h with TPR `0.828` and half-width `0.0330`; it still clears the predeclared target.
- **Evidence**: `per_instrument_detection.csv`; `plots/pooled_vs_instrument_tpr.png`.
- **Interpretation**: The pooled-domain pass is not hiding a failed instrument under the approved precision rule. Some instruments are easier than the pooled map suggests, but no scoped instrument contradicts the headline finding.

## Hypothesis Verdict

**SUPPORTED**

The frozen Phase 001 gate stack detected the imperfect realistic candidate at or above each domain's EXP-003 gate MDE while keeping FPR within the predeclared bound. EXP-005 closes the Phase 001 open keystone for this candidate class: the calibrated MDE map is an honest detection floor here, not evidence of structural blindness.

## Limitations

- The candidate is synthetic but intentionally realistic: imperfect, noisy, and active only 80% of eligible rows. This supports the referee calibration question, not live strategy profitability.
- The result applies to the predeclared `p_active = 0.80`, `q_match = 0.75` candidate class. A weaker, more intermittent, or regime-dependent real candidate could still behave differently.
- All block-bootstrap verdict rows used `block_length = 1`; the audit accepts this because the frozen harness estimated it from train data, but dependence-sensitive follow-up remains EXP-010's role.
- `status` in `detection_summary.csv` is cell-level and repeated across multiplier rows; use `tpr_meets_target` for row-level multiplier interpretation.

## Alternative Explanations

- The exact-MDE success may partly reflect the closed-form edge calibration: the candidate was constructed to have the target expected net edge under the harness cost model. That is by design for this keystone anchor, but it means EXP-005 tests referee sensitivity to a controlled candidate, not organic alpha discovery.
- The stronger-than-target 5m and 1h detection could reflect large sample sizes rather than a generally lenient gate. The 0.5x MDE failures show the gate remains stringent below the mapped floor.

## Recommended Next Steps

1. Continue the Phase 002 spine with EXP-006 and EXP-007 to characterize whether the L5 stringency lever can improve sensitivity below the strict MDE without increasing FPR.
2. Run EXP-008 to de-pool MDE by instrument; EXP-005 found no per-instrument headline failure, but per-instrument MDEs may still differ materially from the pooled map.
3. Preserve EXP-010 as the dependence/split-protocol stress test, because EXP-005's realized block length collapsed to 1 across verdict rows.
