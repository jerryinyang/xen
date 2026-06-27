# Results: Experiment EXP-010

> **2026-06-04 re-run under the corrected multi-fold estimator.** The original run
> combined folds by *concatenating* the per-fold bootstrap-mean distributions, which
> attached a per-fold-sized CI to a pooled-OOS point estimate and spuriously inflated
> the walk-forward MDE (2026-06-04 adversarial review F01). The wrapper now combines
> folds as a **test-size-weighted, per-resample average** of the per-fold bootstrap
> means (a stratified bootstrap of the pooled OOS mean), so the CI scales with the
> pooled OOS size. The single-split arm is bit-identical to the frozen referee and still
> reproduces EXP-003. This page reflects the corrected numbers.

## Summary

EXP-010 partially refutes H-split, but the corrected estimator **reverses the original
reading**. The single-split reference still reproduces EXP-003 and all protocols keep
gate-stack FPR at 0.0. 5m and 1h are now **split-robust** (every protocol matches the
single split). 4h is the only domain where H-split is falsified — and there the
alternative protocols give a **lower** MDE (8.0 vs single 12.0), because they score more
out-of-sample rows than the single split's last-30% test window. This is an
OOS-sample-size effect (the single split is the most conservative arm at the data-poorest
domain), not the referee logic changing or any false-positive inflation.

## Detailed Findings

### The single-split reference reproduces EXP-003

- **Observation**: The single-split arm is statistically consistent with EXP-003 for all domain/alpha cells.
- **Evidence**: `reference_reproduction_check.csv` has `fpr_consistent = true` and `mde_consistent = true` for all 9 rows. At alpha0, single-split MDEs are 1.0 bps (5m), 4.0 bps (1h), and 12.0 bps (4h), matching EXP-003. The wrapper reduces bit-identically to the frozen `evaluate_referees` for the single contiguous fold.
- **Interpretation**: The regenerated draw substrate and corrected split wrapper are faithful, so protocol deltas are interpretable.

### FPR is stable across protocols

- **Observation**: Gate-stack FPR is 0/2000 for every domain/protocol at alpha0.
- **Evidence**: `protocol_fpr_summary.csv` reports FPR 0.0 with Wilson half-width 0.000959 for single, walk-forward, and purged CV across 5m, 1h, and 4h.
- **Interpretation**: The split-protocol shifts are not caused by false-positive inflation.

### 5m and 1h are split-robust

- **Observation**: At alpha0 the gate MDE is identical across all three protocols on 5m (1.0 bps) and 1h (4.0 bps).
- **Evidence**: `protocol_comparison.csv` reports `delta_mde_bps = 0.0` and `material = false` for both alternative protocols on 5m and 1h.
- **Interpretation**: H-split is **SUPPORTED** on 5m and 1h. The original run reported 1h as falsified (walk-forward MDE 8.0); that was the concatenation artifact and is gone under the corrected estimator (walk-forward 1h MDE is now 4.0, matching single).

### 4h: alternative protocols detect a smaller edge than the single split

- **Observation**: At 4h, single MDE is 12.0 bps while both walk-forward and purged CV give 8.0 bps.
- **Evidence**: `protocol_comparison.csv` reports 4h walk-forward and purged-CV `delta_mde_bps = -4.0` vs margin 2.4 bps, `material = true`.
- **Interpretation**: H-split is **FALSIFIED** on 4h under the frozen (direction-symmetric) material criterion. The shift is toward **better** detection: walk-forward (~0.5n OOS) and purged CV (~all-n OOS) pool more out-of-sample rows than the single split's last-30% window (~0.3n), and 4h is the data-poorest domain, so the single split's MDE is the most conservative. Both alternative protocols agree at 8.0 bps, consistent with this being an OOS-sample-size effect (adversarial-review F02), not referee instability.

## Hypothesis Verdict

**PARTIALLY REFUTED**

H-split is SUPPORTED on 5m and 1h and FALSIFIED on 4h. Unlike the original run, the
falsification is now a single domain and is in the direction of more-OOS protocols
detecting a one-grid-step smaller edge — a sample-size/OOS-window property of the
comparison, not a referee-logic change. The result is robustness context for EXP-011,
not a protocol adoption decision.

## Limitations

- **OOS window/size is confounded with protocol (F02).** The three protocols inherently
  score different out-of-sample windows and row counts (single ~0.3n, walk-forward
  ~0.5n, purged CV ~all n). The 4h shift is consistent with that sample-size difference
  rather than a change in referee mechanics; a common-OOS-window ablation would isolate
  the two but is out of the predeclared scope. The finding is therefore reported as
  protocol-plus-OOS-window sensitivity.
- EXP-010 uses 250 draws per generator/edge, reduced from EXP-003's 500 for tractability. D-prec is still met for all alpha0 MDE/FPR rows.
- The multi-fold referee wrapper is experiment-local; its per-fold disjointness and the bit-identical single-split reproduction are the guardrails. (The corrected combination is now additionally checked to scale with pooled OOS size — see audit re-audit addendum.)
- The finding applies to the frozen known-null/known-positive substrate, not real strategy candidates.

## Alternative Explanations

- At 4h the single chronological split is the most under-powered arm (smallest OOS), so its grid MDE is conservative; protocols that score more OOS rows clear the 8-bps edge at TPR>=0.80. This is the most likely explanation and is symmetric across both alternative protocols.
- FPR is controlled (0/2000) everywhere, so the 4h shift is not false-positive driven.

## Recommended Next Steps

1. Feed the corrected per-domain robustness picture into EXP-011: 5m/1h split-robust; 4h split-sensitive in the more-sensitive direction.
2. Do not change the mandatory split protocol inside EXP-010; any split-policy recommendation belongs to synthesis or a future decision phase, and should account for the OOS-window confound (F02).
