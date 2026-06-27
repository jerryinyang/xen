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

- **The "material" criterion resolves only to one grid step.** The frozen margin
  `max(0.5, 20% of pooled)` is 0.8 bps at 1h and 2.4 bps at 4h, both smaller than one
  geometric grid step (2.0 and 4.0 bps). On this discrete edge grid, "material" is
  therefore operationally equivalent to "the per-instrument MDE lands on a different
  grid point", and all three material cells are exactly one grid step below pooled. The
  verdict establishes the **presence** of per-instrument heterogeneity, not its
  magnitude. It is well-founded — the per-instrument TPR crossings are genuine, not
  marginal (EURUSD/1h TPR 0.858 [0.825, 0.886] at edge 2.0; EURUSD/4h 1.000 at 8.0;
  XAUUSD/4h 0.942 [0.918, 0.959] at 8.0, all with Wilson lower bounds above 0.80) — but
  the margin itself carries no sub-grid resolving power and should not be read as a
  finely-calibrated materiality threshold.
- The MDEs remain grid-defined; differences inside a grid step should not be over-interpreted.
- The experiment reprocesses EXP-003 oracle-style draw verdicts. It does not test real candidate strategies or adopt per-instrument operating points.

## Post-results correction (2026-06-04 adversarial review)

The code was corrected (no change to the frozen predeclared margin or to any numeric
verdict): the `within_grid_resolution` flag now uses the full local grid spacing rather
than the half-step MDE uncertainty (matching analysis-plan Step 5), and a `tpr_monotone`
column was added to `per_instrument_mde_summary.csv` to fulfil the plan's promise to
report any non-monotonicity. On re-run, H-pool remains **SUPPORTED** (12/12 reportable,
3 material), every cell reports `tpr_monotone = true`, and the material cells are
unchanged.

## Alternative Explanations

- The lower EURUSD/XAUUSD MDEs may reflect instrument-specific cost/dispersion and sample behavior inside the EXP-003 synthetic substrate, not a general claim about future real signals.
- A finer edge grid might reveal smaller heterogeneity in currently unchanged cells, but that was outside the approved scope.

## Recommended Next Steps

1. Use the EXP-008 per-instrument map as context in EXP-011's operating-point synthesis.
2. Treat any adoption of per-instrument thresholds as a new Phase 003 decision, not an EXP-008 conclusion.
