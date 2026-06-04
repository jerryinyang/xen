# Results: Experiment EXP-008

## Summary

EXP-008 supports H-pool. All 12 instrument/domain cells at `alpha0 = 0.05` are reportable, and 3 cells differ materially from the EXP-003 pooled domain MDE under the frozen margin. The material differences are lower per-instrument MDEs: EURUSD at 1h, EURUSD at 4h, and XAUUSD at 4h.

## Detailed Findings

### H-pool is supported by three material cells

- **Observation**: 3 of 12 alpha0 cells are material differences versus the pooled domain MDE.
- **Evidence**: `mde_pool_comparison.csv` reports:
  - EURUSD/1h: per-instrument MDE 2.0 bps vs pooled 4.0 bps; delta -2.0 bps; margin 0.8 bps.
  - EURUSD/4h: per-instrument MDE 8.0 bps vs pooled 12.0 bps; delta -4.0 bps; margin 2.4 bps.
  - XAUUSD/4h: per-instrument MDE 8.0 bps vs pooled 12.0 bps; delta -4.0 bps; margin 2.4 bps.
- **Interpretation**: The pooled domain MDE masks instrument heterogeneity in at least these cells. The direction is sensitivity-positive: the pooled map is more conservative than the per-instrument map for those instruments/domains.

### The 5m pooled MDE is a good per-instrument proxy

- **Observation**: BTCUSD, EURUSD, USTEC, and XAUUSD all have 5m per-instrument gate MDE = 1.0 bps, matching the pooled 5m MDE.
- **Evidence**: All four 5m rows in `mde_pool_comparison.csv` have `delta_bps = 0.0`, `material = false`, and `within_grid_resolution = true`.
- **Interpretation**: No 5m heterogeneity is visible at the EXP-003 grid resolution.

### No per-instrument cell is under-powered

- **Observation**: Every instrument/domain/alpha MDE row has status `PASS`.
- **Evidence**: `per_instrument_mde_summary.csv` has 36/36 PASS rows. At alpha0, FPR is 0/1000 for each instrument/domain cell, Wilson half-width is 0.001913, and TPR rows use `n=500` with max Wilson half-width 0.043182.
- **Interpretation**: The H-pool conclusion is not driven by missing precision or forced reportability.

## Hypothesis Verdict

**SUPPORTED**

The predeclared Evidence-FOR criterion is met: at least one reportable `instrument x domain` cell differs from the pooled MDE by at least `max(0.5 bps, 20% of pooled_MDE)`. EXP-008 therefore shows that the pooled EXP-003 MDE map should not be treated as a complete per-instrument substitute.

## Limitations

- The MDEs remain grid-defined; differences inside a grid step should not be over-interpreted.
- The experiment reprocesses EXP-003 oracle-style draw verdicts. It does not test real candidate strategies or adopt per-instrument operating points.

## Alternative Explanations

- The lower EURUSD/XAUUSD MDEs may reflect instrument-specific cost/dispersion and sample behavior inside the EXP-003 synthetic substrate, not a general claim about future real signals.
- A finer edge grid might reveal smaller heterogeneity in currently unchanged cells, but that was outside the approved scope.

## Recommended Next Steps

1. Use the EXP-008 per-instrument map as context in EXP-011's operating-point synthesis.
2. Treat any adoption of per-instrument thresholds as a new Phase 003 decision, not an EXP-008 conclusion.
