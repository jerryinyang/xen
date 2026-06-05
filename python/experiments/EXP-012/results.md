# Results: Experiment EXP-012

## Summary

EXP-012 supports adoption of the fixed EXP-011 loose referee point in all three domains. On fresh seeds, the loose point kept FPR at `0/4000` for 5m, 1h, and 4h at `alpha0 = 0.05`, reproduced the Phase 002 MDEs exactly, reproduced the Phase 002 sub-material pass rates within tolerance, and passed the 4h single-vs-walk-forward split gate.

## Detailed Findings

### Fresh FPR Control Held

- **Observation**: Loose-referee FPR was `0.0` in every domain at `alpha0 = 0.05`.
- **Evidence**: `fresh_fpr_summary.csv` reports `successes = 0`, `n = 4000`, and Wilson half-width `0.000479739` for 5m, 1h, and 4h.
- **Interpretation**: The fixed loose point satisfies the predeclared FPR and D-prec condition on fresh draws.

### Fresh MDE Reproduced Phase 002

- **Observation**: Fresh loose MDEs match the Phase 002 operating-point MDEs exactly.
- **Evidence**: `adoption_decisions.csv` reports 5m `0.5` vs `0.5`, 1h `2.0` vs `2.0`, and 4h `8.0` vs `8.0` bps.
- **Interpretation**: The sensitivity improvement chosen in EXP-011 reproduced on fresh seeds instead of degrading by more than one edge-grid step.

### Sub-Material Rates Stayed Within the Adoption Rule

- **Observation**: Sub-material pass rates stayed within +/-0.10 absolute of Phase 002 and below the 0.50 ceiling.
- **Evidence**: 5m `0.399139` vs `0.397590`, 1h `0.027469` vs `0.026224`, and 4h `0.0` vs `0.0`.
- **Interpretation**: The main risk of the loose point - sub-material passes - did not worsen on fresh draws.

### 4h Passed the Split-Sensitivity Gate

- **Observation**: The 4h loose referee MDE was `8.0` bps under both the single split and anchored walk-forward K=5 protocol.
- **Evidence**: `split_gate_comparison.csv` reports `protocols_agree = true`, `single_fpr = 0.0`, and `walk_forward_fpr = 0.0`.
- **Interpretation**: The 4h adoption is not blocked by the corrected EXP-010 split-sensitivity rule.

## Hypothesis Verdict

**SUPPORTED**

All three domains satisfy the frozen adoption rule. The Phase 003 suite therefore adopts the EXP-011 loose operating point at tau multipliers 5m `0.75`, 1h `0.25`, and 4h `0.5`, with no strict-fallback domain.

## Limitations

- Fresh means fresh synthetic seeds on the same first-70-percent real-price analysis slice, not fresh market data.
- The result ratifies the fixed EXP-011 point; it does not authorize new tau search or per-instrument threshold selection.
- **Limited discriminating power of the FPR/MDE conditions (adversarial-review F05).** Fresh-draw FPR is identically `0/4000` (Wilson half-width 0.00048) for every domain, referee, and alpha, and the fresh loose MDE reproduces the Phase 002 value *exactly* in every domain. This is the expected behaviour of an honest detection floor — the loose and strict referees share legs L1–L4, which fail first under the null, so loosening L5 cannot raise the null pass-rate — but it means two of the three adoption conditions (FPR ≤ α₀; MDE within one edge-grid step) hold trivially and could not realistically have refuted any domain. Adoption was therefore effectively decided by the **sub-material condition alone** (5m sub-rate 0.399 vs the 0.50 ceiling; within ±0.10 of the Phase 002 0.398). The ratification confirms the operating point on fresh seeds but does not stress-test it on FPR or MDE; readers should not over-read the FPR/MDE agreement as independent robustness evidence.

## Alternative Explanations

- The exact MDE reproduction could reflect the coarse edge grid, but the adoption rule explicitly accepts one-grid-step agreement and all domains matched exactly.
- The zero FPR result is consistent with prior strict and loose frontier behavior; it does not prove FPR is zero in all possible future candidate screens.

## Recommended Next Steps

1. Carry the adopted loose operating point into suite documentation and any later Phase 004 registry plan.
2. Do not run additional tau tuning under Phase 003; any new threshold question should be a separate experiment.
