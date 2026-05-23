# Analysis Plan: Experiment EXP-027

## Objective

Run the first allowed full-model analysis-set test for one EXP-026-selected, predeclared ICT variant, after costs and without touching the global holdout.

## Methodology

### Step 1: Frozen Variant Manifest Check

- **Method**: Verify that the EXP-026-selected manifest lists every included component, parameter, entry, stop, target, and EXP-012 cost scenario before execution.
- **Why this method**: Full-model testing is only allowed after components are justified and frozen.
- **Simpler alternative considered**: Reconstructing the variant during implementation risks post-hoc rule selection.
- **Assumptions**: Any missing manifest field makes the experiment inconclusive until corrected.
- **Expected output**: Manifest compliance table.

### Step 2: Full-Variant Event and Trade Simulation

- **Method**: Apply the frozen rule chain to analysis-set train/test only, using real time-bar OHLC prices, approved cost scenarios, and no parameter tuning.
- **Why this method**: It tests whether the selected complete variant survives realistic constraints inside the analysis set.
- **Simpler alternative considered**: A component-only summary cannot answer the full-model survival question.
- **Assumptions**: Same-bar target/stop ambiguity is handled by the predeclared convention from prerequisite experiments.
- **Expected output**: Trade-level and aggregate performance tables.

### Step 3: Survival Criteria Assessment

- **Method**: Report expectancy after costs, median R, trade count, train/test direction, instrument contribution share, and comparison to simpler EXP-026 baselines.
- **Why this method**: The scope requires positive after-cost performance without single-instrument dependence or domination by simpler baselines.
- **Simpler alternative considered**: A single pooled expectancy would hide instability.
- **Assumptions**: This remains analysis-set testing; no global holdout rows are loaded.
- **Expected output**: Full-model go/no-go verdict for EXP-028.

## Visualisations

1. Trade-count and event-count waterfall.
2. After-cost R distribution.
3. Train/test expectancy interval plot.
4. Instrument contribution plot.
5. Comparison to simpler EXP-026 baselines.

## Interpretation Guide

- Support: positive median expectancy after costs, required trade counts, stable train/test direction, and no single instrument > 60 percent of net R.
- Against: non-positive after-cost expectancy, instability, or domination by simpler baselines.
- Inconclusive: EXP-026 does not identify an eligible frozen model.

## Complexity Check

- Statistical tests: 2-3 / 3
- Visualisations: 5 / 5
- New modules: 2 / 2
