# Analysis Plan: Experiment EXP-018

## Objective

Measure the revised incremental referee's portfolio-fitness MDE per domain and verify that redundancy-null FPR is controlled across the unchanged P3-D-dependence grid, especially at the synchronous-high-overlap-null_R corner that refuted EXP-015.

## Methodology

### Step 1: Dependency, Revision, and Grid Manifest

- **Method**: Deterministic dependency, revised-gate, and dependence-grid verification.
- **Why this method**: EXP-018 is valid only after EXP-013 substrate validation and EXP-017 revised logic correctness, and the active checkpoint freezes both the revised gate and the dependence grid.
- **Simpler alternative considered**: Generate only a subset of grid cells for speed. That would not test the false-positive and power mode the checkpoint makes central.
- **Assumptions**: EXP-013/017 artifacts are present and approved; the revised gate is `L1 and L3 and L4' and L5`; L2 is absent; grid labels, construction diagnostics, seeds, and inherited edge grid are recorded before measurement.
- **Expected output**: Dependency manifest, revised-gate manifest, grid manifest with realized dependence diagnostics, construction-invalid-cell report, seed metadata, and `run_metadata.json`.

### Step 2: Redundancy-Null FPR Across Dependence

- **Method**: Apply the revised incremental referee to redundancy-null draws in every construction-accepted domain/dependence-grid cell; summarize FPR with Wilson intervals.
- **Why this method**: H-revised-floor requires redundancy-null FPR control under shared R-C structure in every qualifying dependence cell, not only in independent cases.
- **Simpler alternative considered**: Pooled FPR across all dependence cells. Pooling could hide a false-positive failure in the high-overlap stress corner.
- **Assumptions**: Null draws have no marginal edge by construction; bootstrap and any embargo operate on the joint R-C series. Cells outside predeclared dependence construction acceptance are labeled construction-invalid or under-powered before outcomes are interpreted.
- **Expected output**: Grid-cell FPR table with Wilson half-width, pass/fail/under-powered status, draw-level verdicts, and a highlighted synchronous-high-overlap-null_R report.

### Step 3: Positive Incremental-Edge TPR and MDE

- **Method**: Apply the revised incremental referee to positive marginal-edge draws over the inherited edge grid; summarize TPR with Wilson intervals and derive `cell_mde_bps` for each qualifying dependence-grid cell.
- **Why this method**: H-revised-floor asks for the smallest incremental net edge the revised unit reliably detects at controlled FPR.
- **Simpler alternative considered**: Report only average detected effect. That would not produce a portfolio-fitness detection floor.
- **Assumptions**: Positive planted marginal edge is known by construction, and MDE is computed only from cells whose construction diagnostics and denominators meet D-prec. A qualifying cell with FPR control but no finite MDE over the inherited edge grid refutes that domain's calibration for that dependence context.
- **Expected output**: TPR summary, per-cell MDE summary, worst-case domain MDE summary, and under-powered/construction-invalid-cell table.

### Step 4: Retained-Leg and Instrument Diagnostics

- **Method**: Retained-leg pass-rate and per-instrument TPR summaries by domain, dependence cell, and edge level.
- **Why this method**: The checkpoint repair is targeted at EXP-015's L2/BTCUSD failure. If EXP-018 refutes again, it must identify the new binding retained leg, domain, or instrument rather than only reporting the final verdict.
- **Simpler alternative considered**: Final verdict rates only. That would repeat the pre-A1 diagnosability gap.
- **Assumptions**: Draw-level outputs include retained leg states, instrument label, domain, dependence-cell labels, edge level, and final verdict.
- **Expected output**: Retained-leg pass-rate table, per-instrument TPR table, and binding-failure attribution table.

### Step 5: Dependence Sensitivity and Domain Verdict

- **Method**: Rule-based interpretation of FPR and MDE results against H-revised-floor using the predeclared per-cell and worst-case domain aggregation rules.
- **Why this method**: The checkpoint defines support/refutation in terms of finite MDE and controlled FPR, with under-powered cells reported separately.
- **Simpler alternative considered**: Average dependence-cell results into one score. That would weaken redundancy-null control and hide dependence-corner failures.
- **Assumptions**: Domain conclusions explicitly identify qualifying, failing, construction-invalid, and under-powered cells. The headline domain MDE is the maximum finite `cell_mde_bps` across qualifying cells, not a pooled or best-case value.
- **Expected output**: Domain-level conclusion table, worst-case MDE table, dependence-risk summary, and explicit EXP-015-corner summary.

## Visualisations

1. FPR heatmap across the dependence grid by domain - shows shared-structure false-positive risk.
2. MDE summary plot by domain and qualifying dependence context - shows portfolio-fitness detection floors.
3. TPR curves over planted incremental edge by domain - shows detection behavior under the revised gate.
4. Retained-leg pass-rate heatmap by edge and dependence cell - shows which retained leg binds if a cell fails.
5. Under-powered or construction-invalid cell grid plot - shows where D-prec is unattainable.

## Interpretation Guide

- If every qualifying dependence cell controls FPR and has finite `cell_mde_bps`, the revised incremental referee is calibrated for that domain with headline MDE equal to the worst-case finite cell MDE.
- If any qualifying dependence cell exceeds `alpha0` FPR, H-revised-floor is refuted for that domain because shared structure creates false positives.
- If any qualifying positive cell has no finite MDE over the inherited edge grid, the domain is refuted for that dependence context and the domain-level calibration is not supported.
- If the synchronous-high-overlap-null_R corner controls FPR and attains finite MDE, the specific EXP-015 failure mode is resolved for that domain.
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
- Do not optimize by changing grid membership, draw denominators, temporal order, cost attribution, MDE definitions, or retained-leg semantics.
- Preserve the EXP-013 estimator and CI paths unless a required EXP-013 re-run is explicitly triggered.

### Real-Price Outcome Discipline

- All incremental P&L and referee returns use real OHLC domain prices.
- Chart-type construction prices and chart-type candidates are out of scope.

### Event Density Differences

- Report incremental-denominator counts for each grid cell; low C-change density can make cells under-powered.

### Regime Stratification

- No regime stratification is scoped for EXP-018.
