# Analysis Plan: Experiment EXP-015

## Objective

Measure the incremental referee's portfolio-fitness MDE per domain and verify that redundancy-null FPR is controlled under the predeclared R-C dependence grid.

## Methodology

### Step 1: Dependency and Dependence-Grid Manifest

- **Method**: Deterministic dependency and grid verification.
- **Why this method**: EXP-015 is valid only after EXP-013 substrate validation and EXP-014 logic correctness, and the dependence grid is frozen by the checkpoint.
- **Simpler alternative considered**: Generate only a subset of grid cells for speed. That would not test the false-positive mode the checkpoint makes central.
- **Assumptions**: EXP-013/014 artifacts are present and approved; grid labels, numeric acceptance bands, construction diagnostics, and seeds are recorded before measurement.
- **Expected output**: Dependency manifest, grid manifest with realized rho/overlap/lag/reference-strength diagnostics, construction-invalid-cell report, and seed metadata.

### Step 2: Redundancy-Null FPR Across Dependence

- **Method**: Apply the incremental referee to redundancy-null draws in every construction-accepted domain/dependence-grid cell; summarize FPR with Wilson intervals.
- **Why this method**: The checkpoint requires FPR control under shared R-C structure in every qualifying dependence cell, not only in independent cases.
- **Simpler alternative considered**: Pooled FPR across all dependence cells. Pooling could hide a false-positive failure in a high-dependence cell.
- **Assumptions**: Null draws have no marginal edge by construction; bootstrap and any resampling operate on the joint R-C series. Cells outside the predeclared rho/overlap/lag acceptance bands are labeled construction-invalid or under-powered before outcomes are interpreted.
- **Expected output**: Grid-cell FPR table with Wilson half-width, pass/fail/under-powered status, and draw-level verdicts.

### Step 3: Positive Incremental-Edge TPR and MDE

- **Method**: Apply the incremental referee to positive marginal-edge draws over the inherited edge grid; summarize TPR with Wilson intervals and derive `cell_mde_bps` for each qualifying dependence-grid cell.
- **Why this method**: H-incr-floor asks for the smallest incremental net edge the referee reliably detects at controlled FPR.
- **Simpler alternative considered**: Report only average detected effect. That would not produce a portfolio-fitness detection floor.
- **Assumptions**: Positive planted marginal edge is known by construction, and MDE is computed only from cells whose construction diagnostics and denominators meet D-prec. A qualifying cell with FPR control but no finite MDE over the inherited edge grid refutes that domain's calibration for that dependence context.
- **Expected output**: TPR summary, per-cell MDE summary, worst-case domain MDE summary, and under-powered/construction-invalid-cell table.

### Step 4: Dependence Sensitivity and Domain Verdict

- **Method**: Rule-based interpretation of FPR and MDE results against H-incr-floor using the predeclared per-cell and worst-case domain aggregation rules.
- **Why this method**: The checkpoint defines support/refutation in terms of finite MDE and controlled FPR, with under-powered cells reported separately.
- **Simpler alternative considered**: Average dependence-cell results into one score. That would weaken the redundancy-null control.
- **Assumptions**: Domain conclusions explicitly identify which cells were qualifying, failing, construction-invalid, or under-powered. The headline domain MDE is the maximum finite `cell_mde_bps` across qualifying cells, not a pooled or best-case value.
- **Expected output**: Domain-level conclusion table, worst-case MDE table, and dependence-risk summary.

## Visualisations

1. FPR heatmap across the dependence grid by domain - shows shared-structure false-positive risk.
2. MDE summary plot by domain and qualifying dependence context - shows portfolio-fitness detection floors.
3. TPR curves over planted incremental edge by domain - shows detection behavior.
4. Under-powered-cell grid plot - shows where D-prec is unattainable.
5. Incremental-denominator distribution plot - shows how often C changes the book beyond R.

## Interpretation Guide

- If every qualifying dependence cell controls FPR and has finite `cell_mde_bps`, the incremental referee is calibrated for that domain with headline MDE equal to the worst-case finite cell MDE.
- If any qualifying dependence cell exceeds alpha0 FPR, H-incr-floor is refuted for that domain because shared structure creates false positives.
- If any qualifying positive cell has no finite MDE over the inherited edge grid, the domain is refuted for that dependence context and the domain-level calibration is not supported.
- If cells are under-powered or construction-invalid, report them separately with denominators and realized grid diagnostics; do not convert them into pass or fail.

## Complexity Check

- Statistical tests: 4 / 4
- Visualisations: 5 / 5
- New modules: 0-1 / 1

## Data-View Comparison Considerations

### Cross-View Alignment

- Align R, C, and real-price returns by `CloseTime`.
- Do not align signals by bar index or row count.

### Implementation Safety and Performance

- Slice to the first 70% analysis set before synthetic R-C generation.
- Use `tqdm` for domain, instrument, dependence-grid, edge, and draw loops.
- Keep lead/lag construction explicit so C-leading cells do not leak future returns.
- Do not optimize by changing grid membership, draw denominators, temporal order, cost attribution, or MDE definitions.

### Real-Price Outcome Discipline

- All incremental P&L and referee returns use real OHLC domain prices.
- Chart-type construction prices and chart-type candidates are out of scope.

### Event Density Differences

- Report incremental-denominator counts for each grid cell; low C-change density can make cells under-powered.

### Regime Stratification

- No regime stratification is scoped for EXP-015.
