# Results: Experiment EXP-013

> **✓ Re-validated under amendment [A1](../../../docs/experiments-docs/checkpoints/2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md) (F01 + F04).** Re-run 2026-06-04 with the corrected machinery: the redundancy-null verdict now uses the **across-draw distribution** with an explicit `UNDER_POWERED` class (F01), and the bootstrap block length is estimated on the **contiguous marginal series** (F04). The substrate remains **PASS**. Three cells (BTCUSD/1h, BTCUSD/4h, USTEC/4h) are now correctly labeled `UNDER_POWERED` rather than mislabeled cost-dominated negatives, the binding control is powered in **9/12** cells, and no cell shows a phantom positive edge. Numbers below reflect the re-run outputs.

## Summary

EXP-013 supports the incremental substrate. All 108 planted marginal-edge cells recovered the known edge within the predeclared tolerance, and the redundancy null did not manufacture a phantom positive incremental edge from shared R-C structure. Under the corrected across-draw verdict, the binding redundancy control is adequately powered in 9 of 12 cells (8 clean PASS plus 1 cost-dominated negative); the remaining 3 cells are honestly flagged `UNDER_POWERED` — their across-draw CI half-width exceeds the cell materiality buffer, so they cannot rule a phantom in or out, but none reads positive.

## Detailed Findings

### Positive Marginal Edge Was Recovered

- **Observation**: Every positive known-truth recovery cell passed.
- **Evidence**: `positive_recovery.csv` has 108/108 `PASS` rows. The largest absolute recovery error is `0.396082` bps in BTCUSD/4h at planted `4.0` bps, below the `0.6` bps tolerance.
- **Interpretation**: The marginal-P&L estimator recovers known edge magnitude across instruments, domains, and the inherited edge grid.

### Redundancy Null Produced No Phantom Positive Edge

- **Observation**: No redundancy-null cell was classified as `PHANTOM_EDGE`. Every cell's across-draw mean incremental edge is negative (cost-driven); the most positive across-draw mean is `-0.0412` bps (EURUSD/5m), so no cell even has a positive point estimate, let alone a CI that excludes zero positively.
- **Evidence**: `redundancy_null.csv` records 8 `PASS`, 3 `UNDER_POWERED`, and 1 `NULL_COST_DOMINATED` rows; 0 `PHANTOM_EDGE`. `run_metadata.json` reports `phantom_edge = false` and `powered_null_cells = 9`.
- **Interpretation**: Shared R-C structure did not create false positive incremental fitness in the substrate gate. The verdict is now drawn from the distribution of per-draw means (`across_draw_*` columns) rather than a single bootstrap draw, so it reflects the reproducibility of the null across draws, not one resample.

### Three High-Cost Cells Are Under-Powered, Not Cost-Dominated Negatives

- **Observation**: BTCUSD/1h, BTCUSD/4h, and USTEC/4h have across-draw CI half-widths (`1.63`, `7.02`, `3.99` bps) that meet or exceed their cell materiality buffers (`1.5`, `3.0`, `3.0` bps), so a phantom edge of materiality size could not have been detected even if present.
- **Evidence**: `redundancy_null.csv` `status = UNDER_POWERED` with `across_draw_half_width_bps >= materiality_bps` in these three cells; `run_metadata.json` lists them under `underpowered_null_cells`.
- **Interpretation**: These were previously (pre-F01) mislabeled "cost-dominated negatives" on a single noisy draw. They are correctly recorded as low-power controls: the substrate is not refuted (no positive edge appears), but these specific dependence contexts cannot serve as binding redundancy tests at the present draw count. One cell (XAUUSD/4h) is genuinely `NULL_COST_DOMINATED` — adequately powered (half-width `2.71` < materiality `3.0`) with a point estimate at the predeclared cost drag.

### Denominator Construction Matched the Scope

- **Observation**: The C-change denominator stayed near the predeclared one-quarter mask share.
- **Evidence**: `substrate_integrity.csv` reports denominator fractions from `0.249834` to `0.250452`.
- **Interpretation**: The substrate is measuring the intended rows where C changes the combined book relative to R-alone.

### Holdout Discipline Preserved

- **Observation**: Only the first 70 percent analysis slice was loaded.
- **Evidence**: `analysis_metadata.csv` shows analysis windows ending in 2025 (e.g. BTCUSD ends `2025-06-17`) while source files extend into 2026; the analysis-row fraction is `0.7000` for all four instruments.
- **Interpretation**: The final 30 percent holdout was never read, consistent with the governance OOS rule.

## Hypothesis Verdict

**SUPPORTED**

The Track B P0 substrate is validated: known marginal edge is recoverable to tolerance, and the redundancy null does not create a phantom positive incremental edge. The binding control is powered in 9/12 cells with zero phantom positives; the 3 under-powered cells are disclosed, not silently passed. EXP-014/015 may rely on this substrate.

## Limitations

- The 3 `UNDER_POWERED` cells (BTCUSD/1h, BTCUSD/4h, USTEC/4h) cannot, at the present 100 redundancy draws, bound a phantom edge below their materiality buffer. They are not evidence against the substrate, but they are not binding redundancy tests either; raising draw counts in these high-cost low-effective-n contexts would be required to convert them to powered controls.
- The single-draw bootstrap (`boot_*` columns, block length estimated on the contiguous series per F04) is retained as a diagnostic only and is no longer the verdict basis.
- The substrate validates known-truth mechanics, not the eventual operating-characteristic MDE under all dependence contexts (that is EXP-015's scope).

## Alternative Explanations

- Recovery precision is strongest in 5m and weaker in 4h, consistent with denominator size and effective-n. The positive recovery criterion is across-draw magnitude recovery, not single-draw detectability — which is exactly why the redundancy verdict was moved to the across-draw distribution under F01.

## Recommended Next Steps

1. Use EXP-014 to verify incremental referee logic on deterministic fixtures (re-confirmed PASS under F04).
2. Use EXP-015 to test whether the validated substrate supports controlled-FPR finite MDE calibration under dependence stress.
