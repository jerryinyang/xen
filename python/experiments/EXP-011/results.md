# Results: Experiment EXP-011

## Summary

EXP-011 delivered the Phase 002 synthesis recommendation under the predeclared loss family. The primary Loss A recommends L5 threshold multipliers of `0.75` for 5m, `0.25` for 1h, and `0.5` for 4h. The 1h recommendation is robust across the three losses within the predeclared one-grid-step rule; 5m and 4h are loss-sensitive. These are recommendations only: adoption is deferred to Phase 003 fresh-draw ratification.

## Detailed Findings

### All dependency and precision gates passed

- **Observation**: EXP-011 produced complete result tables for all three domains with no inconclusive domain.
- **Evidence**: `run_metadata.json` records `overall_status = COMPLETE`, `measurements_produced = true`, `submaterial_repro_check = true`, and `inconclusive_domains = []`. Dependency tokens for EXP-003, EXP-005, EXP-006, EXP-007, EXP-008, EXP-009, and EXP-010 are all `COMPLETE`.
- **Interpretation**: The operating-point read is valid under the scoped dependency and precision gates. The audit independently confirmed the saved loss selections from the result CSVs.

### Primary recommendations

- **Observation**: Loss A selected a lower-than-strict L5 threshold on every domain.
- **Evidence**:

| Domain | Headline tau* | MDE at tau* | Sub-material rate | Cross-loss verdict |
|--------|---------------|-------------|-------------------|--------------------|
| 5m | 0.75 | 0.5 bps | 0.39759036144578314 | LOSS_SENSITIVE |
| 1h | 0.25 | 2.0 bps | 0.026223776223776224 | ROBUST |
| 4h | 0.5 | 8.0 bps | 0.0 | LOSS_SENSITIVE |

- **Interpretation**: Under the primary predeclared loss, the strict reference `tau = 1.0` is not loss-minimising. The loss favors sensitivity headroom, but the amount of cross-loss support differs by domain.

### Cross-loss robustness differs by domain

- **Observation**: Only the 1h recommendation is robust by the predeclared one-grid-step rule.
- **Evidence**: `recommendation.csv` reports:
  - 5m: Loss A `0.75`, Loss B `0.75`, Loss C `0.25`; index spread `2`; driver `sub_material`.
  - 1h: Loss A `0.25`, Loss B `0.25`, Loss C `0.0`; index spread `1`; `ROBUST`.
  - 4h: Loss A `0.5`, Loss B `0.5`, Loss C `0.0`; index spread `2`; driver `blind_band`.
- **Interpretation**: The 1h choice is not very sensitive to loss specification. The 5m choice depends on how much sub-material admission is penalized, while the 4h choice depends on the trade-off between reducing the blind band and Loss C's material-edge prior.

### Adoption caveats are material for 1h and 4h

- **Observation**: The read-only overlays do not change the headline tau*, but they materially condition adoption.
- **Evidence**: `adoption_rule.json` records:
  - EXP-005 `DETECTED_FLOOR` for 5m, 1h, and 4h.
  - EXP-009 `n_at_or_above_mde = 0` for every domain.
  - EXP-008 material per-instrument overlays for EURUSD/1h and EURUSD/XAUUSD 4h.
  - EXP-010 walk-forward materiality `false` for 5m and 1h and `true` for 4h (corrected estimator; 1h is now split-robust, and the 4h shift is toward a *lower* MDE under more-OOS protocols).
- **Interpretation**: Lower tau is not a remedy for demonstrated strict-gate blindness, because EXP-005 already showed the strict gate is an honest detection floor on the scoped candidate. For 4h, any Phase 003 adoption should explicitly re-confirm the recommendation under walk-forward conditions; for all domains, consider per-instrument masking. The adoption caveats are now composed from the loaded overlays, not asserted as a fixed narrative.

## Hypothesis Verdict

**RECOMMENDATION DELIVERED (exploratory)**

EXP-011 has no SUPPORTED/REFUTED hypothesis. Its scoped success criterion was to name a predeclared-loss-minimising operating point per domain, record cross-loss robustness, and attach the conditional adoption rule. That deliverable is complete for all three domains.

## Limitations

- The recommendation is computed on shared Phase 002 draws and is explicitly not an adoption decision.
- Loss C can prefer lower tau values because it integrates missed material edges but does not directly price sub-material admissions; this drives the 5m and 4h loss sensitivity. On this zero-FPR substrate Loss C is monotone toward the lenient endpoint, so it is a **weak independent corroborator** — the cross-loss verdict largely reflects how far Loss A/B sit from maximal leniency (`run_metadata.method_notes.loss_c_degeneracy`).
- Loss A minimises MDE before the sub-material tie-break, so a tau* can carry a non-trivial operating sub-material rate (5m tau*=0.75 has sub=0.398 under the 0.50 cap). Read tau* with its sub_rate (`run_metadata.method_notes.loss_a_submaterial`).
- Under the corrected EXP-010 estimator, only the **4h** recommendation is conditional on the single chronological split; 5m and 1h are split-robust. The 4h shift is toward a lower MDE (more-OOS protocols), an OOS-sample-size effect.
- Per-instrument overlays are caveats, not headline re-selection inputs.
- All scoped context dependencies (EXP-005/008/009/010) are hard-gated to COMPLETE; a missing/incomplete overlay now fails the run rather than silently producing a recommendation without its predeclared caveats.

## Alternative Explanations

- The lower tau recommendations may reflect synthetic calibration substrate geometry rather than practical real-strategy benefit; EXP-009 found no scoped untuned strategy effect at or above any domain MDE.
- 5m's recommendation may be especially sensitive to the predeclared sub-material penalty because low tau values cluster just under the `0.50` sub-material cutoff.

## Recommended Next Steps

1. In Phase 003, ratify any proposed tau* on fresh synthetic draws using the recorded conditional adoption rule: FPR Wilson upper `<= 0.05`, `sub <= 0.50` at the operating MDE, and EXP-005-style TPR `>= 0.80`.
2. Re-check the 4h recommendation under walk-forward before any adoption, because corrected EXP-010 found a material 4h split shift toward a lower MDE under more-OOS protocols; 5m and 1h are split-robust.
3. Keep EXP-011 as a recommendation artifact only; do not freeze a new referee inside Phase 002.
