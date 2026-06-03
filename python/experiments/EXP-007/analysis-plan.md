# Analysis Plan: Experiment EXP-007

## Objective

Measure the predeclared lenient-L5 variant on the same draw substrate as the frozen gate and determine whether it lowers MDE at controlled FPR beyond the EXP-006 threshold frontier, while explicitly reporting economically sub-material passes.

## Methodology

### Step 1: Dependency and Frontier Gate

- **Method**: Require supported EXP-001 and EXP-003 metadata, load EXP-003 draw verdicts and strict MDE rows, then require EXP-006 threshold-frontier artifacts with a passing strict-reference check.
- **Why this method**: EXP-007 is interpreted only against the EXP-006 threshold sweep, and the same paired draws preserve within-draw comparability.
- **Simpler alternative considered**: Measuring lenient L5 without EXP-006 would show whether it lowers strict MDE, but not whether the improvement exceeds a simple threshold reduction.
- **Assumptions**: EXP-006 artifacts are pre-results relative to EXP-007 and were produced without reading EXP-007 outcomes.
- **Expected output**: Dependency status in `run_metadata.json`.

### Step 2: Lenient Variant Reconstruction

- **Method**: For each EXP-003 gate-stack draw row, parse `leg_results`, keep L1-L4 unchanged, set `L5_lenient = ci_lower_bps > 0.0`, and recompute the conjoined lenient pass flag.
- **Why this method**: It implements `D-lenientL5` with the smallest possible change to the frozen gate stack.
- **Simpler alternative considered**: Implementing a separate referee in shared code would add surface area and risk drift from the frozen harness.
- **Assumptions**: `ci_lower_bps` is the net-of-cost CI lower bound; the variant is fully predeclared and measured once.
- **Expected output**: `lenient_draw_verdicts.csv`.

### Step 3: Lenient FPR, TPR, and MDE

- **Method**: Compute Wilson-interval FPR on null rows and TPR on positive rows. Define lenient MDE as the smallest planted edge with FPR `<= alpha`, TPR `>= 0.80`, FPR half-width `<= 0.03`, and TPR half-width `<= 0.05`.
- **Why this method**: It matches the EXP-003 and EXP-006 operating-characteristic definitions.
- **Simpler alternative considered**: Comparing only pass counts would not identify economic MDE.
- **Assumptions**: Draw denominators are inherited from EXP-003; grid uncertainty is carried as bps half-step, not interpolated.
- **Expected output**: `lenient_fpr_summary.csv`, `lenient_tpr_summary.csv`, and `lenient_mde_summary.csv`.

### Step 4: Frontier Comparison, Structural-Equivalence Confirmation, and Sub-Material Accounting

- **Method**: Compare lenient MDE/FPR against the frozen strict gate and the EXP-006 acceptable-FPR threshold frontier. As a deterministic consistency check (not a new statistical test), confirm the lenient verdicts equal the L5-removed gate (`L1∧L2∧L3∧L4`) per draw, **and** equal the EXP-006 `τ=0` rows at the **verdict level** — joining EXP-006's `threshold_draw_verdicts.csv` (`multiplier == 0`) to the lenient draws on the shared draw keys and counting per-`(domain, alpha)` pass-flag mismatches and unmatched draws (both expected 0). The lenient-MDE vs EXP-006-`τ=0`-MDE summary equality is retained as a **secondary** check, so a defect in EXP-006's reconstruction, sample membership, or per-draw pass flags is caught even if the final MDE happens to coincide (see scope **Predeclared Structural Relationship**). For lenient positive pass rows, compute sub-material pass rates using `effect_bps < materiality_bps(domain)`.
- **Why this method**: The design requires distinguishing genuine sensitivity from lower MDE bought mostly by economically negligible effects; the equivalence confirmation makes the structural finding (lenient = `τ=0` = drop-L5) auditable rather than asserted.
- **Simpler alternative considered**: Calling any lower MDE a win would ignore the Phase 002 materiality caveat and the fact that the lenient point lies on the EXP-006 frontier by construction.
- **Assumptions**: A sub-material pass rate above 50% at the lenient MDE means the measured sensitivity is sub-material, not a genuine economic sensitivity gain; the lenient–`τ=0`–dropL5 equivalence is exact under the frozen harness.
- **Expected output**: `lenient_vs_frontier.csv`, `structural_equivalence_check.csv`, and `submaterial_pass_rates.csv`.

## Visualisations

1. MDE comparison by domain: strict gate, best acceptable EXP-006 threshold, and lenient L5.
2. FPR comparison by domain at `alpha=0.05`.
3. TPR curves for lenient L5 versus strict gate at `alpha=0.05`.
4. Economically sub-material pass-rate heatmap by domain and edge.

## Interpretation Guide

- **Expected resolution (frozen harness):** the lenient verdicts match the EXP-006 `τ=0` rows and the L5-removed gate exactly, so the lenient MDE equals the EXP-006 zero-buffer endpoint. This is the threshold-reduction (magnitude) result, **not** a structural lenient-mechanism gain; report H-lenient **FALSIFIED** for that domain with the structural reason recorded. This is a legitimate predeclared finding, not an experiment failure.
- If, contrary to the frozen-harness expectation, lenient L5 lowered MDE *strictly below* the best acceptable EXP-006 frontier point at FPR `<= alpha0` with sub-material pass rate `<= 0.50`, H-lenient would be supported for that domain — but the structural-equivalence check would then have to show a mismatch, which would itself be a reconstruction defect to investigate before interpretation.
- If lenient L5 lowers MDE but most passes at that MDE are economically sub-material (`> 0.50`), report sub-material sensitivity and do not count it as a genuine sensitivity gain — this sharpens the falsification with an economic-quality reason.
- If FPR exceeds `alpha0`, the lenient variant is too permissive for that domain.
- If precision targets fail or EXP-006 frontier artifacts are missing/invalid, the domain is inconclusive.

## Complexity Check

- Statistical tests: 4 / 4
- Visualisations: 4 / 4
- New modules: 0 / 0

## Data-View Comparison Considerations

### Cross-View Alignment

- EXP-007 is result-level post-processing of EXP-003 and EXP-006 artifacts; no new market-data view or chart-type event alignment is introduced.
- If any harness replay is required, use `CloseTime` ordering and the same first-70% analysis slice as EXP-003.

### Implementation Safety and Performance

- Do not read or materialize source market data unless a narrow audit check requires it.
- Keep the lenient reconstruction as a pure transformation of verdict rows.
- Use Polars group-by summaries for FPR/TPR/MDE tables; convert only small summaries to pandas for plotting.
- Do not alter L1-L4, costs, materiality constants, alpha grid, edge grid, sample membership, or draw denominators.
- Do not use EXP-007 results to revise the lenient definition or EXP-006 frontier.

### Real-Price Outcome Discipline

- Reused EXP-003 effect fields are already based on real domain `Close` returns.
- No Heiken Ashi, Renko, Line Break, or other chart-type prices are in scope.

### Denominators and Zero-Baseline Behavior

- FPR denominator is null draw verdict count per domain/alpha.
- TPR denominator is positive draw verdict count per domain/alpha/edge.
- Sub-material denominator is lenient positive pass count for the corresponding domain/alpha/edge; if there are zero lenient passes, the sub-material rate is reported as `NaN` and not coerced to zero.
- MDE comparisons are absolute bps comparisons with grid half-step uncertainty. Do not compute percentage improvement from missing, zero, or non-finite baselines.
