# Results: Experiment EXP-006

## Summary

EXP-006 successfully characterized the L5 materiality threshold lever. Across all domains, alpha values, and threshold multipliers, FPR remained `0/4000` with Wilson half-width `0.000480`. At the primary `alpha0=0.05`, lowering the threshold below the strict `tau=1.0 x materiality` reference reduced MDE from `1.0 -> 0.5` bps on 5m, `4.0 -> 2.0` bps on 1h, and `12.0 -> 8.0` bps on 4h. Raising the threshold to `tau=2.0` increased MDE to `2.0`, `8.0`, and `16.0` bps respectively.

## Detailed Findings

### Strict Reference Reproduced EXP-003

- **Observation**: The `tau=1.0` reconstruction matched the frozen EXP-003 gate stack exactly.
- **Evidence**: `strict_reference_check.csv` has 9/9 rows with `draw_mismatch_count = 0`, `draws_match = true`, and `mde_match = true`. Reconstructed strict MDEs match EXP-003 at every domain/alpha: 5m `1.0`, 1h `4.0`, 4h `12.0` bps.
- **Interpretation**: The threshold sweep is a valid reconstruction of the frozen gate with only L5's threshold magnitude changed. The experiment meets its main Evidence-FOR correctness gate.

### Lower L5 Thresholds Improved MDE Without FPR Cost

- **Observation**: At `alpha0=0.05`, all swept thresholds had FPR `0.0`, but lower thresholds improved MDE.
- **Evidence**:
  - 5m MDE: `0.5` bps for `tau=0.0` through `0.75`, strict `1.0` bps at `tau=1.0`, and `2.0` bps at `tau=2.0`.
  - 1h MDE: `2.0` bps at `tau=0.0` and `0.25`, strict `4.0` bps at `tau=1.0`, and `8.0` bps at `tau=2.0`.
  - 4h MDE: `8.0` bps at `tau=0.0` through `0.50`, strict `12.0` bps at `tau=1.0`, and `16.0` bps at `tau=2.0`.
  - `threshold_fpr_summary.csv`: every alpha/domain/threshold row has `successes = 0`, `n = 4000`.
- **Interpretation**: In this draw substrate, L5 threshold magnitude is a usable sensitivity lever: moving it downward improves measured sensitivity while the other gate legs keep pooled null FPR at zero.

### Power Curves Show Domain-Specific Lever Strength

- **Observation**: The lower-threshold gain is largest where the strict threshold was binding near the MDE.
- **Evidence**: At `alpha0=0.05`, `tau=0.0` TPR at the new MDE is 5m `1.000` at `0.5` bps, 1h `0.924` at `2.0` bps, and 4h `0.902` at `8.0` bps. Strict-gate TPR at those same edges was 5m `0.027`, 1h `0.3715`, and 4h `0.7295`.
- **Interpretation**: The strict L5 buffer suppresses positive detections near the lower edge grid. Removing that buffer shifts the practical MDE downward, especially on 1h and 4h.

### All Precision Criteria Passed

- **Observation**: Every MDE row is reportable.
- **Evidence**: `threshold_mde_summary.csv` has 63/63 rows with `status = PASS`; FPR denominators are all `4000`, TPR denominators are all `2000`, max FPR half-width is `0.000480`, and max TPR half-width across the table is `0.021892`.
- **Interpretation**: No domain/alpha/threshold cell is inconclusive under the Phase 002 precision targets.

## Hypothesis Verdict

**SUPPORTED (exploratory measurement delivered)**

EXP-006's exploratory question is answered: the L5 lever curve is finite and precise for every scoped cell, and the strict reference reproduces EXP-003 exactly. The measured frontier shows lower L5 thresholds can reduce economic MDE without increasing pooled FPR on the EXP-003 draw substrate. This is a characterization result, not an adoption decision.

## Limitations

- The frontier is grid-resolution limited; MDE values are selected from the EXP-003 edge grid and are not interpolated.
- The analysis uses EXP-003 synthetic draw artifacts, not new market-data candidate signals.
- FPR remaining zero on these paired draws does not prove every future threshold choice will control FPR on fresh draws.
- Results are pooled by domain over four instruments; EXP-008 is still needed for per-instrument MDE heterogeneity.

## Alternative Explanations

- The apparent zero-FPR safety of lower L5 thresholds may be due to L3/L4 binding strongly on the scoped null generators, not because lower materiality thresholds are generally safe.
- Domain-specific MDE steps partly reflect the coarse planted-edge grid, especially for 4h where adjacent grid gaps are larger.

## Recommended Next Steps

1. Use EXP-007 to confirm whether lenient L5 is anything beyond this `tau=0` threshold endpoint and to quantify economically sub-material passes.
2. Use EXP-011 to evaluate candidate operating points under the predeclared loss function; do not adopt a threshold from EXP-006 alone.
