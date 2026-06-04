# Results: Experiment EXP-010

## Summary

EXP-010 partially refutes H-split. The single-split reference arm reproduces EXP-003, and all protocols keep gate-stack FPR at 0.0. However, anchored walk-forward materially raises the gate-stack MDE on 1h and 4h, while 5m stays unchanged and purged CV matches the single split across all domains.

## Detailed Findings

### The single-split reference reproduces EXP-003

- **Observation**: The single-split arm is statistically consistent with EXP-003 for all domain/alpha cells.
- **Evidence**: `reference_reproduction_check.csv` has `fpr_consistent = true` and `mde_consistent = true` for all 9 rows. At alpha0, single-split MDEs are 1.0 bps (5m), 4.0 bps (1h), and 12.0 bps (4h), matching EXP-003.
- **Interpretation**: The regenerated draw substrate and experiment-local split wrapper are faithful enough for protocol deltas to be interpreted.

### FPR is stable across protocols

- **Observation**: Gate-stack FPR is 0/2000 for every domain/protocol at alpha0.
- **Evidence**: `protocol_fpr_summary.csv` reports FPR 0.0 with Wilson half-width 0.000959 for single, walk-forward, and purged CV across 5m, 1h, and 4h.
- **Interpretation**: The split-protocol shifts are not caused by false-positive inflation.

### Walk-forward materially increases 1h and 4h MDE

- **Observation**: Anchored walk-forward raises MDE from 4.0 to 8.0 bps on 1h and from 12.0 to 24.0 bps on 4h.
- **Evidence**: `protocol_comparison.csv` reports:
  - 1h walk-forward delta +4.0 bps vs margin 0.8 bps, `material = true`.
  - 4h walk-forward delta +12.0 bps vs margin 2.4 bps, `material = true`.
- **Interpretation**: H-split is falsified on 1h and 4h. The inference protocol itself changes measured detection sensitivity on those domains.

### 5m and purged CV are robust

- **Observation**: 5m MDE remains 1.0 bps under all protocols. Purged CV matches the single split on all domains.
- **Evidence**: `protocol_mde_summary.csv` reports purged CV MDEs of 1.0, 4.0, and 12.0 bps for 5m/1h/4h, all status PASS.
- **Interpretation**: Split sensitivity is not universal. It is specific to the anchored walk-forward protocol on the slower domains.

## Hypothesis Verdict

**PARTIALLY REFUTED**

H-split is supported on 5m, but falsified on 1h and 4h because walk-forward materially changes the gate-stack economic MDE under the frozen criterion. The result is a measured robustness limitation for EXP-011 synthesis, not a protocol adoption decision.

## Limitations

- EXP-010 uses 250 draws per generator/edge, reduced from EXP-003's 500 for tractability. D-prec is still met for all alpha0 MDE/FPR rows.
- The multi-fold referee wrapper is experiment-local and governed by the pre-results amendment; the passing single-split reproduction is the main guardrail.
- The finding applies to the frozen known-null/known-positive substrate, not real strategy candidates.

## Alternative Explanations

- Walk-forward may reduce effective detection power on 1h/4h because its expanding OOS folds partition the slower-domain sample differently, not because the referee logic changed.
- Purged CV matching single split suggests the material shift is not simply "any cross-validation" but the specific anchored walk-forward partition.

## Recommended Next Steps

1. Feed the 1h/4h walk-forward MDE sensitivity into EXP-011 as robustness context.
2. Do not change the mandatory split protocol inside EXP-010; any split-policy recommendation belongs to synthesis or a future decision phase.
