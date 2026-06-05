# Experiment Report: EXP-013 - Incremental Substrate Validation

## Status: SUPPORTED

**Date**: 2026-06-04 (re-validated under amendment [A1](../../../docs/experiments-docs/checkpoints/2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md), F01 + F04)
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains; seeded R/C incremental known-truth substrate

---

## Question

Can the Track B incremental substrate measure known marginal edge beyond a reference signal without manufacturing phantom edge from shared R-C structure?

## Hypothesis

The incremental substrate recovers planted marginal edge within `max(0.5 bps, 15% of m)` and reads no phantom positive incremental edge for the redundancy null.

## Method Summary

The experiment built seeded R/C substrates where C changes the combined book on a predeclared denominator. Positive cases planted known marginal net edge on that denominator; redundancy-null cases shared R-C structure but planted no marginal edge.

## Key Findings

### Finding 1: Planted Marginal Edge Recovered

`results/positive_recovery.csv` has 108/108 PASS rows. The largest absolute recovery error was `0.396082` bps, still below its `0.6` bps tolerance.

### Finding 2: Redundancy Null Did Not False Positive

`results/redundancy_null.csv` has 0 `PHANTOM_EDGE` rows under the corrected across-draw verdict (F01). Eight cells PASS directly, one is `NULL_COST_DOMINATED` in the expected negative direction (XAUUSD/4h), and three high-cost low-effective-n cells (BTCUSD/1h, BTCUSD/4h, USTEC/4h) are honestly flagged `UNDER_POWERED` — their across-draw CI half-width exceeds the cell materiality buffer. The binding control is therefore powered in 9/12 cells, and no cell has even a positive point estimate (the most positive across-draw mean is `-0.0412` bps).

### Finding 3: Denominator Construction Matched the Design

The C-change denominator fraction stayed near 25 percent in all instrument/domain cells (`0.249834` to `0.250452`), matching the predeclared mask construction.

## Conclusion

**Hypothesis SUPPORTED.**

The incremental known-truth substrate is validated as Track B's P0 gate. It recovers known marginal edge and does not manufacture phantom positive incremental edge from shared R-C structure.

## Limitations

- Cost-dominated and under-powered nulls are expected under the confirmed amortized incremental cost model and should not be read as positive evidence. The 3 `UNDER_POWERED` cells cannot, at 100 redundancy draws, bound a phantom edge below their materiality buffer; they are disclosed, not binding.
- This validates the substrate, not the full incremental referee operating-characteristic map.

## Implications for Future Research

- EXP-014 can test deterministic incremental-referee logic on golden fixtures.
- EXP-015 can use this substrate to test dependence-grid FPR and MDE behavior.

## Recommended Next Experiments

1. **EXP-014**: Incremental referee golden-fixture correctness.
2. **EXP-015**: Dependence-grid portfolio-fitness calibration.

## Artifacts

| Artifact | Path |
|----------|------|
| Scope | [scope.md](scope.md) |
| Analysis Plan | [analysis-plan.md](analysis-plan.md) |
| Code | [code/](code/) |
| Audit | [audit.md](audit.md) |
| Results | [results.md](results.md) |
| Governance Reviews | [governance/](governance/) |
| Plots | [plots/](plots/) |
