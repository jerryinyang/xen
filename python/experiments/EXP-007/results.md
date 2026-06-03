# Results: Experiment EXP-007

## Summary

EXP-007 refutes H-lenient's structural-gain claim. The lenient rule lowered strict MDE at controlled FPR, but it did so exactly by matching the EXP-006 `tau=0` zero-buffer endpoint and the L5-removed gate. At `alpha0=0.05`, lenient MDEs were 5m `0.5`, 1h `2.0`, and 4h `8.0` bps with FPR `0/4000` in every domain. These equal the best acceptable EXP-006 frontier MDEs, so there is no gain beyond a threshold-magnitude reduction.

## Detailed Findings

### Structural Equivalence Was Exact

- **Observation**: Lenient L5 equals both drop-L5 and EXP-006 `tau=0` on the shared draw substrate.
- **Evidence**: `structural_equivalence_check.csv` has 9/9 rows with `lenient_vs_dropl5_mismatch = 0`, `lenient_vs_exp006_tau0_mismatch = 0`, `lenient_vs_exp006_tau0_unmatched = 0`, `draws_match_dropl5 = true`, `draws_match_exp006_tau0 = true`, and `lenient_eq_tau0_mde = true`.
- **Interpretation**: The predeclared "structurally lenient" mechanism is not distinct under the frozen harness. It is the zero-buffer endpoint of the EXP-006 threshold sweep.

### Lenient L5 Lowered Strict MDE, But Not Beyond the Frontier

- **Observation**: At `alpha0=0.05`, lenient MDE improved relative to strict but equaled EXP-006 `tau=0` and the best acceptable EXP-006 frontier.
- **Evidence**:
  - 5m: strict `1.0` bps, lenient `0.5` bps, best EXP-006 frontier `0.5` bps.
  - 1h: strict `4.0` bps, lenient `2.0` bps, best EXP-006 frontier `2.0` bps.
  - 4h: strict `12.0` bps, lenient `8.0` bps, best EXP-006 frontier `8.0` bps.
  - `lenient_vs_frontier.csv`: `improves_beyond_frontier = false` and `verdict = EVIDENCE_AGAINST_NO_STRUCTURAL_GAIN` in all 9 domain/alpha rows.
- **Interpretation**: The measured sensitivity gain is real relative to strict L5, but it is fully explained by reducing the L5 threshold magnitude to zero. It is not a separate mechanism-level improvement.

### FPR Stayed Controlled

- **Observation**: The lenient variant had zero pooled null passes in every domain and alpha.
- **Evidence**: `lenient_fpr_summary.csv`: lenient FPR `0.0`, `successes = 0`, `n = 4000`, Wilson half-width `0.000480` for every domain/alpha row.
- **Interpretation**: In these draws, removing the L5 materiality buffer did not increase null false positives because the remaining gate legs still blocked null rows.

### Sub-Material Pass Rates Were Mixed But Did Not Drive the Headline Verdict

- **Observation**: At the alpha0 lenient MDE, sub-material pass rates were below or equal to the predeclared `0.50` limit, but 5m was close.
- **Evidence**:
  - 5m at `0.5` bps: `993 / 2000`, rate `0.4965`.
  - 1h at `2.0` bps: `101 / 1848`, rate `0.054654`.
  - 4h at `8.0` bps: `0 / 1804`, rate `0.0`.
- **Interpretation**: EXP-007 is not refuted because MDE passes were mostly sub-material. It is refuted because lenient L5 does not improve beyond the EXP-006 threshold frontier. The 5m sub-material rate is close enough to the cutoff that future synthesis should avoid treating the 5m zero-buffer endpoint as an unqualified economic improvement.

### All Precision Criteria Passed

- **Observation**: The measurement deliverable is complete.
- **Evidence**: `lenient_mde_summary.csv` has 18/18 strict/lenient rows with `status = PASS`; FPR denominators are all `4000`, TPR denominators are all `2000`, and alpha0 TPR half-widths at lenient MDE are 5m `0.000959`, 1h `0.011631`, and 4h `0.013041`.
- **Interpretation**: The refutation is not an inconclusive precision artifact.

## Hypothesis Verdict

**REFUTED**

H-lenient claimed a structurally lenient L5 would lower economic MDE at controlled FPR beyond the EXP-006 threshold frontier. The lenient variant controlled FPR and lowered strict MDE, but it equaled the EXP-006 `tau=0` endpoint exactly at the verdict and MDE levels. Therefore the structural-gain claim is refuted by the predeclared Evidence-AGAINST criterion.

## Limitations

- The result uses the same EXP-003 paired synthetic draws as EXP-006 for comparability; fresh-draw adoption remains deferred to Phase 003.
- MDE is grid-resolution limited, especially on 4h where edge gaps are wide.
- The economically sub-material test uses net effect below `materiality_bps(domain)`; it does not replace EXP-011's predeclared loss-function synthesis.
- This experiment does not evaluate new real candidate signals or per-instrument MDE heterogeneity.

## Alternative Explanations

- The zero FPR under lenient L5 may reflect other gate legs being highly restrictive on the scoped null generators, rather than a guarantee that the zero-buffer endpoint is generally safe.
- The 5m sub-material rate being just below 0.50 suggests the lower MDE could include a meaningful fraction of economically marginal passes even though it did not cross the predeclared sub-material-failure threshold.

## Recommended Next Steps

1. In EXP-011, treat lenient L5 as the EXP-006 zero-buffer endpoint plus sub-material accounting, not as a distinct referee mechanism.
2. Preserve the Phase 002 rule that no variant is adopted here; any operating-point adoption should be ratified on fresh draws in Phase 003.
