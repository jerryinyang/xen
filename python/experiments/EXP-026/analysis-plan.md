# Analysis Plan: Experiment EXP-026

## Objective

Measure which validated ICT components contribute net value when combined incrementally before any full-model test is allowed.

## Methodology

### Step 1: Component Eligibility Audit

- **Method**: Read completed EXP-015 through EXP-025 outputs and classify each component as eligible, negative-control only, or excluded using its predeclared scope criteria.
- **Why this method**: The phase gate requires documented definition, sample size, and contribution before combined modeling.
- **Simpler alternative considered**: Including all components would ignore failed prerequisites.
- **Assumptions**: Eligibility is based on prior experiment verdicts, not new outcome inspection.
- **Expected output**: Component eligibility matrix.

### Step 2: Fixed-Order Incremental Chain

- **Method**: Add eligible components in the scoped order: sweep, macro, premium/discount, displacement, IFVG, breaker, execution rule, risk model. Record event counts and dropped-event reasons at each step.
- **Why this method**: It measures marginal contribution and sample-size loss one component at a time.
- **Simpler alternative considered**: Jumping directly to a full model would violate the ablation gate.
- **Assumptions**: Components not eligible are skipped or labelled negative controls before execution.
- **Expected output**: Component contribution table.

### Step 3: Marginal Contribution Analysis

- **Method**: Bootstrap differences in expectancy, drawdown proxy, and event retention between adjacent chain steps; compare train/test direction.
- **Why this method**: It tests net value after sample-size costs.
- **Simpler alternative considered**: Raw cumulative performance cannot identify which component adds or removes value.
- **Assumptions**: No component order is changed after seeing results.
- **Expected output**: Eligible model-variant recommendation for EXP-027 or no-go verdict.

## Visualisations

1. Event-count waterfall by component.
2. Marginal expectancy interval plot.
3. Component retention percentage plot.
4. Train/test contribution table or heatmap.

## Interpretation Guide

- Support: at least one component adds net expectancy or risk-adjusted improvement beyond sample loss and survives train/test comparison.
- Against: gains disappear when components combine or sample size collapses.
- Inconclusive: too few components have prior evidence to form a chain.

## Complexity Check

- Statistical tests: 2-3 / 3
- Visualisations: 4 / 5
- New modules: 2 / 2
