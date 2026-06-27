# Analysis Plan: Experiment EXP-013

## Objective

Validate the incremental known-truth substrate by testing whether it recovers planted marginal edge beyond R and reads approximately zero incremental edge for a redundancy null with shared R-C structure.

## Methodology

### Step 1: Governance Freeze and Substrate Manifest

- **Method**: Deterministic governance and construction-manifest check before any measurement output is produced. Require the Stage 4 token `PHASE003-TRACKB-PREDECLARATION-CONFIRMED`, covering `D-incr-form`, `D-incr-substrate`, and `D-incr-legs`, plus a manifest of the seeded R/C substrate parameters.
- **Why this method**: The checkpoint requires all Track B defaults or overrides to be confirmed before EXP-013 executes, and the substrate construction is the object being validated.
- **Simpler alternative considered**: Treating the scope defaults as implicit confirmation. That would not satisfy the checkpoint's explicit operator-confirmation gate.
- **Assumptions**: The governance artifact is dated before any EXP-013 measurement exists; if it is absent, the run is blocked rather than inconclusive.
- **Expected output**: `run_metadata.json` freeze block, substrate construction manifest, and blocker report if the governance token is absent.

### Step 2: Construct the Incremental Return Series

- **Method**: Deterministic known-truth generation of joint `(R, C)` signals and model-free marginal net P&L calculation.
- **Why this method**: The checkpoint fixes the primary estimator as combined-book-with-C minus combined-book-without-C, with incremental turnover cost attribution.
- **Simpler alternative considered**: Standalone C return or linear residualization against R. Standalone C does not answer portfolio fitness, and residualization is only a secondary diagnostic if it first passes the redundancy and dependence nulls.
- **Assumptions**: R and C positions are chronological, real-price returns are available by `CloseTime`, and the denominator is the predeclared `C_change` mask where the combined position differs from R-alone.
- **Expected output**: Incremental return series, denominator counts, turnover/cost attribution table, realized mask fractions, and seed metadata.

### Step 3: Positive Planted-Edge Recovery

- **Method**: Compare observed mean marginal net edge against the planted marginal edge using the checkpoint tolerance `max(0.5 bps, 15% of m)`.
- **Why this method**: It exactly matches H-incr-substrate's positive recovery requirement and mirrors the EXP-001 tolerance family named by the checkpoint.
- **Simpler alternative considered**: A significance-only test against zero. That would not verify that the substrate recovers the known magnitude.
- **Assumptions**: The planted marginal edge is known by construction because gross drift is solved after the scoped incremental-turnover cost function so net marginal P&L on `C_change` equals `m` in expectation.
- **Expected output**: Recovery table by domain, instrument, and planted edge, including absolute error and pass/fail status.

### Step 4: Redundancy Null Check

- **Method**: Estimate incremental edge for shared-structure R-C redundancy cases and report bootstrap intervals on the marginal-P&L series.
- **Why this method**: The checkpoint identifies the redundancy null as the binding Track B control: C must not look useful merely because it shares structure with R.
- **Simpler alternative considered**: Check only independent nulls. That would miss the false-positive mode this track exists to control.
- **Assumptions**: Bootstrap resampling is applied to the joint R-C marginal-P&L series and does not break the scoped denominator or temporal membership. Redundancy passes only if the point estimate is within the predeclared null tolerance and the 95% CI lower bound is `<= 0`.
- **Expected output**: Redundancy-null edge table with intervals, denominator counts, null-tolerance status, and phantom-edge verdict.

### Step 5: Substrate Integrity Summary

- **Method**: Descriptive checks on sample membership, denominator rates, zero-baseline handling, and cost attribution.
- **Why this method**: EXP-013 is Track B's P0 gate, so substrate mechanics must be auditable before EXP-014/015.
- **Simpler alternative considered**: Only report the final hypothesis verdict. That would hide whether a pass depends on denominator or cost accounting errors.
- **Assumptions**: All checks use the first 70% analysis slice only.
- **Expected output**: `run_metadata.json`, denominator summary, and integrity table.

## Visualisations

1. Recovered-versus-planted marginal edge plot by domain - shows magnitude recovery.
2. Absolute recovery error plot with tolerance bands - shows pass/fail distance.
3. Redundancy-null incremental edge interval plot - shows whether shared structure creates phantom edge.
4. Denominator and incremental-turnover summary plot - shows where C actually changes the book.

## Interpretation Guide

- If positive cells recover planted marginal edge within tolerance and redundancy-null cells show no spurious positive incremental edge, EXP-013 supports the substrate and Track B can proceed.
- If positive recovery fails, the marginal-P&L substrate is not measuring known edge reliably and Track B halts.
- If the redundancy null shows phantom incremental edge, the unit is unsound for portfolio fitness and Track B halts.
- If denominator or effective sample is too small, report the affected cells as under-powered rather than force support/refutation.

## Complexity Check

- Statistical tests: 3 / 3
- Visualisations: 4 / 4
- New modules: 1 / 1

## Data-View Comparison Considerations

### Cross-View Alignment

- All R-C and return rows align by `CloseTime`.
- Do not align domains or signals by row index.

### Implementation Safety and Performance

- Load only the first 70% analysis slice before generating R-C substrate rows.
- Use `tqdm` for instrument, domain, edge, and synthetic-case loops.
- Keep stateful R-C construction explicit where vectorization would alter causality.
- Do not optimize by changing denominator membership, incremental turnover accounting, temporal order, or planted-edge definitions.

### Real-Price Outcome Discipline

- Combined-book returns, R-alone returns, and incremental edge use real OHLC domain prices only.
- Chart-type prices and chart-type candidate signals are out of scope.

### Event Density Differences

- Report the fraction of bars where C changes the combined book relative to R-alone. This is the primary denominator for incremental edge.

### Regime Stratification

- No regime stratification is scoped for EXP-013.
