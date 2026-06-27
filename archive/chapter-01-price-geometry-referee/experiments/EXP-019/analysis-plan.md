# Analysis Plan: Experiment EXP-019

## Objective

Conditional on EXP-018 validation and D-dogfood-book confirmation, run the assembled strict, ratified-loose, and revised incremental suite end to end on both the real EXP-009 dogfood negative path and a synthetic positive suite-level fixture.

## Methodology

### Step 1: Suite Assembly, Dependency, and D-dogfood-book Check

- **Method**: Deterministic artifact manifest and compatibility check.
- **Why this method**: EXP-019 depends on EXP-012 adopted-loose decisions, EXP-018 revised incremental calibration, EXP-009 dogfood definitions, and the still-pending D-dogfood-book decision. The suite cannot be tested until those components are frozen and compatible.
- **Simpler alternative considered**: Recompute or infer missing upstream choices. That would violate the checkpoint freeze.
- **Assumptions**: Upstream artifacts identify strict referee, ratified-loose referee, standalone MDEs, revised incremental unit, EXP-018 headline domain MDEs, EXP-009 dogfood strategy definitions, and a pre-results-confirmed dogfood reference book.
- **Expected output**: Suite manifest, dependency table, D-dogfood-book confirmation status, dogfood reference-book manifest, candidate slate manifest, positive fixture manifest, expected-output matrix, and blocker report if any upstream component is unavailable.

### Step 2: Real Dogfood Negative Path

- **Method**: Apply the assembled standalone referees and revised incremental unit to the EXP-009 dogfood set against the confirmed D-dogfood-book reference R.
- **Why this method**: The checkpoint names the EXP-009 dogfood set as the real negative path and expects standalone rejections and no incremental edge.
- **Simpler alternative considered**: Use only synthetic negative fixtures. That would not test composition on the real dogfood artifact chain.
- **Assumptions**: Dogfood signals and reference-book positions are aligned by `CloseTime`; incremental denominator is bars where C changes the combined book relative to R-alone; the reference book and candidate slate were fixed before results are read.
- **Expected output**: Dogfood suite verdict table, standalone referee outputs, revised incremental edge table, and denominator summary.

### Step 3: Synthetic Positive Suite-Level Fixture

- **Method**: Run the predeclared planted-edge candidate from the positive fixture manifest through all suite components.
- **Why this method**: The checkpoint requires both reject and pass paths to be exercised, and the EXP-009 dogfood set is expected to be a negative path.
- **Simpler alternative considered**: Treat successful dogfood rejection as enough. That would leave positive-path wiring untested.
- **Assumptions**: The planted-edge fixture is predeclared before execution, its expected suite outputs are recorded before replay, it uses real-price-style return contributions rather than chart-type construction prices, and C is not redundant with R.
- **Expected output**: Positive fixture suite verdict table, expected-versus-observed output matrix, non-redundancy diagnostics, and incremental edge summary.

### Step 4: Composition and Wiring Summary

- **Method**: Rule-based integration summary comparing observed path behavior to checkpoint expectations.
- **Why this method**: EXP-019 is exploratory integration, not a new operating-characteristic calibration.
- **Simpler alternative considered**: Produce a single pass/fail statistic. That would obscure which suite element or path failed to wire.
- **Assumptions**: Missing D-dogfood-book confirmation is a blocker, not a result.
- **Expected output**: Suite composition table with path, domain, referee outputs, incremental outputs, denominators, and integration status.

## Visualisations

1. Suite verdict matrix by path, domain, and referee - shows reject/pass wiring.
2. Incremental edge interval plot for dogfood and synthetic positive paths - shows revised fitness-unit behavior.
3. Denominator and active-change plot for incremental comparisons - shows where C changes the book.
4. Per-domain ratified-loose versus strict outcome plot - shows how EXP-012 decisions flow into the suite.
5. Integration status dashboard table or plot - shows blockers, completed paths, and unexpected outputs.

## Interpretation Guide

- If the dogfood path rejects standalone and shows no positive incremental edge, the negative path wiring is consistent with the checkpoint expectation.
- If the synthetic positive fixture matches the predeclared expected-output matrix, passes both standalone referees, and shows positive incremental edge against a non-redundant reference, the pass path wiring is exercised.
- If D-dogfood-book is not confirmed or any dependency is missing, EXP-019 is inconclusive or blocked rather than interpreted as suite evidence.
- If the dogfood path unexpectedly shows positive standalone or incremental evidence, report it as an integration observation only; do not treat it as Phase 004 real signal exploration.

## Complexity Check

- Statistical tests: 4 / 4
- Visualisations: 5 / 5
- New modules: 0-1 / 1

## Data-View Comparison Considerations

### Cross-View Alignment

- Align dogfood, reference-book, candidate, and return rows by `CloseTime`.
- Do not align domains or suite outputs by row index.

### Implementation Safety and Performance

- Slice to the first 70% analysis set before real dogfood evaluation.
- Use `tqdm` for domain, instrument, strategy, fixture, and suite-component loops.
- Do not recompute or alter upstream adoption decisions, MDE maps, dogfood definitions, D-dogfood-book choices, or revised incremental calibration.
- Keep outputs concise and traceable to upstream artifacts.

### Real-Price Outcome Discipline

- All standalone and incremental returns use real OHLC domain prices.
- Chart-type candidates and construction prices are out of scope.

### Event Density Differences

- Report dogfood active-bar denominators and incremental C-change denominators separately.

### Regime Stratification

- No regime stratification is scoped for EXP-019.
