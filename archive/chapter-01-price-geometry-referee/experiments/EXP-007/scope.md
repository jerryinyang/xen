# Experiment: EXP-007 - Lenient-L5 Referee Variant

## Hypothesis

The predeclared structurally lenient L5 variant lowers the gate stack's economic MDE relative to the frozen strict gate while holding `FPR <= alpha0 = 0.05`, beyond what is achieved by the EXP-006 threshold-magnitude frontier.

## Question

Does replacing the strict L5 materiality requirement with statistical net-positivity after costs create a genuine sensitivity gain, or does it merely admit economically sub-material positives?

## Predeclared Structural Relationship (frozen-harness clarification — 2026-06-03)

This clarification is derived **solely from the frozen Phase 001 harness** (`xen.referee_calibration.gate_stack_row`) and the existing EXP-003 draw artifacts — both Phase 001 products. It references **no Phase 002 measurement** (EXP-005/EXP-006 outcomes) and is authored **before any EXP-006 or EXP-007 result exists**, so it complies with the §2 ⚠ predeclaration-freeze discipline of the active checkpoint. The predeclared lenient-L5 **definition is unchanged** (`L5_lenient = ci_lower_bps > 0.0`).

In the frozen gate stack, L5 is `ci_lower_bps > materiality_bps` and L3 is `ci_lower_bps > 0 AND ci_vs_naive_lower_bps > 0`. Two exact consequences follow on the shared draws (verified across all 216,000 frozen gate-stack rows, 0 exceptions):

1. **Lenient L5 ≡ EXP-006 `τ=0` endpoint.** EXP-006 sweeps `L5_τ = ci_lower_bps > τ`, `τ = mult × materiality_bps`. At `mult=0` this is `ci_lower_bps > 0`, identical to the lenient leg. The lenient variant therefore **lies on the EXP-006 threshold frontier (its zero-buffer endpoint) and cannot strictly improve beyond that frontier.**
2. **Lenient gate ≡ gate with L5 removed.** Because L3 already requires `ci_lower_bps > 0`, the lenient leg is redundant whenever L3 passes: `L1∧L2∧L3∧L4∧(ci_lower>0) = L1∧L2∧L3∧L4`. Maximal L5 leniency equals dropping L5, with L3 becoming the binding net-positivity gate.

Consequently the design D-lenientL5 framing of a "structurally distinct mechanism, not merely a smaller number" **does not hold under the frozen harness**: the lenient leg is the `τ→0` magnitude limit of the same CI-lower-bound mechanism. (D-lenientL5's prose describing the strict leg as a *point-estimate* test is inconsistent with the frozen code, which is CI-lower-bound-based; the frozen code governs.) EXP-007's informative, attainable deliverable is therefore (a) the lenient operating characteristics at Phase-002 precision, (b) the **economically sub-material pass-rate** accounting at the lenient MDE (not produced by EXP-006), and (c) numerical confirmation of the two equivalences above. H-lenient's structural-gain claim is expected to resolve **FALSIFIED** (a magnitude change, not a distinct mechanism) — a legitimate, predeclared finding that closes the lever-characterization deliverable.

## Scope Boundaries

- **Data Views**: EXP-003 draw-level verdict artifacts and EXP-006 threshold-frontier artifacts are the primary data views. No new market-data measurement is required. If implementation replays any harness step, it must use only the first 70% analysis slice.
- **Lenient-L5 definition**: L5 passes if the lower bound of the net-of-cost effect CI exceeds zero: `L5_lenient = ci_lower_bps > 0.0`. L1-L4 remain unchanged from the frozen gate stack. This variant is measured once and is not adopted in Phase 002.
- **Comparison references**:
  - Frozen strict gate stack from EXP-003.
  - EXP-006 threshold sweep frontier.
  - Minimal baseline only as optional context, not as the decision object.
- **Economic sub-material pass definition**: A lenient pass is economically sub-material when the net-of-cost point estimate is below the frozen domain materiality buffer, `effect_bps < materiality_bps(domain)`. If a gross-effect diagnostic is emitted, the equivalent gross condition is `gross_effect_bps < cost_bps + materiality_bps(domain)`.
- **Sub-material denominator**: Report the economically sub-material pass rate among lenient positive-scenario pass rows, both at the lenient MDE edge and across all positive lenient passes. If more than 50% of lenient passes at the MDE are sub-material, any lower MDE is classified as sub-material sensitivity rather than genuine economic sensitivity.
- **Parameters**: Domains 5m, 1h, 4h; alpha grid `{0.10, 0.05, 0.01}` with primary `alpha0=0.05`; EXP-003 planted edge grid; EXP-006 threshold multipliers as context.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, pooled by domain to match EXP-003 and EXP-006. Per-instrument rows may be emitted as diagnostics but are not headline.
- **Dependencies**: EXP-001 and EXP-003 must be supported. EXP-006 must have produced a valid threshold frontier and strict-reference reproduction before EXP-007 is interpreted.
- **Pre-execution confirmation**: Before EXP-007 execution, Stage 4 governance must record operator confirmation or a pre-results design amendment for `D-lenientL5`. No EXP-007 measurement may be used to alter the lenient definition.
- **Time range**: Full dataset with nested chronological split per instrument file as already applied by EXP-003. First 70% = analysis set; final 30% = global holdout and is never used.
- **Global holdout**: The final 30% of each source file must not be loaded, inspected, or used in any capacity. Result-level post-processing of EXP-003/EXP-006 artifacts is preferred.
- **Look-ahead bias prevention**: No new signal construction is in scope. Existing EXP-003 draws used only `t -> t+1` real Close-to-Close returns and train-only block-length estimation.
- **Real-price outcome discipline**: All effect and CI fields reused from EXP-003 are based on real domain `Close` prices. No synthetic chart prices are in scope.
- **Exclusions**: Adoption/freezing of the lenient variant, loss-function selection, changing L1-L4, changing costs/materiality constants, adding new thresholds after reading EXP-006, chart-type signals, and any referee redesign.

## Success / Failure Criteria

The structural-gain branch of H-lenient is retained for falsifiability but, per the **Predeclared Structural Relationship** above, is **not attainable under the frozen harness**; the experiment is expected to resolve Evidence-AGAINST. Every branch requires the measurement deliverable.

- **Measurement deliverable (required for a usable result, independent of pass/fail)**: lenient FPR/TPR/MDE per domain/alpha at the Phase 002 precision target (FPR Wilson half-width `<= 0.03`; TPR Wilson half-width `<= 0.05` at the MDE); the economically sub-material pass-rate at the lenient MDE and across all positive lenient passes; and numerical confirmation that lenient verdicts equal the EXP-006 `τ=0` rows and the L5-removed gate (`L1∧L2∧L3∧L4`) on the shared draws.
- **Evidence FOR (H-lenient supported — structural sensitivity gain)**: at `alpha0=0.05`, the lenient variant has FPR `<= 0.05` (half-width `<= 0.03`), a finite MDE (TPR half-width `<= 0.05`), an MDE **strictly below the best acceptable EXP-006 threshold-frontier MDE**, and economically sub-material pass rate `<= 0.50` at the lenient MDE. *Not attainable under the frozen harness — the lenient point is the EXP-006 `τ=0` frontier endpoint; this branch is retained only so H-lenient stays falsifiable.*
- **Evidence AGAINST (H-lenient falsified — expected resolution)**: the lenient MDE equals the EXP-006 `τ=0` (zero-buffer) endpoint (no gain beyond a threshold-magnitude reduction), OR FPR `> alpha0`, OR no finite MDE, OR economically sub-material pass rate `> 0.50` at the lenient MDE. The expected headline is the first clause: the predeclared "structurally-lenient" leg is the `τ→0` magnitude limit of the frozen CI-lower-bound mechanism, equivalent to removing L5.
- **Inconclusive**: EXP-006 frontier artifacts are missing/invalid, the strict-reference reproduction failed, or the lenient FPR/TPR precision targets are not met.

## Complexity Budget

- Max statistical tests: 4
- Max visualisations: 4
- Max new code modules: 0

## Data Requirements

Use existing verdict-level artifacts:

- `python/experiments/EXP-003/results/draw_verdicts.csv`
- `python/experiments/EXP-003/results/mde_summary.csv`
- `python/experiments/EXP-006/results/threshold_mde_summary.csv`
- `python/experiments/EXP-006/results/threshold_fpr_summary.csv`
- `python/experiments/EXP-006/results/strict_reference_check.csv`
- `python/experiments/EXP-006/results/threshold_draw_verdicts.csv` (the `multiplier == 0` rows are the **verdict-level** reference for the lenient leg)

Parse EXP-003 gate-stack `leg_results`, keep L1-L4 fixed, replace only L5 with `ci_lower_bps > 0.0`, then compute lenient FPR, TPR, MDE, and sub-material pass rates. The per-draw lenient verdicts are persisted to `lenient_draw_verdicts.csv` and cross-checked, verdict-level, against EXP-006's independently reconstructed `τ=0` draws (`threshold_draw_verdicts.csv`) on the shared draw keys, so reconstruction drift between the two experiments is caught rather than hidden by a coincidental MDE-summary match.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)
bars = scan.slice(0, analysis_cutoff).collect()
```

Result-level post-processing is preferred for EXP-007. The loading pattern above is included only as the mandatory safety pattern if implementation must replay the harness.

## Suggested Direction

Treat EXP-007 as a variant characterization, not a policy decision. A lower MDE is useful only if it is not just the EXP-006 zero-buffer endpoint and is not mostly economically sub-material.
