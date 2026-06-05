# Analysis Plan: Experiment EXP-016

## Objective

Run the assembled strict, ratified-loose, and incremental suite end to end on both the real EXP-009 dogfood negative path and a synthetic positive suite-level fixture.

## Methodology

### Step 1: Suite Assembly and Upstream Artifact Check

- **Method**: Deterministic artifact manifest and compatibility check.
- **Why this method**: EXP-016 depends on EXP-012 adoption/fallback decisions, EXP-015 incremental calibration, and EXP-009 dogfood definitions. The suite cannot be tested until those components are frozen and compatible.
- **Simpler alternative considered**: Recompute or infer missing upstream choices. That would violate the checkpoint freeze.
- **Assumptions**: Upstream artifacts identify strict referee, ratified-loose or strict fallback per domain, standalone MDEs, incremental unit, EXP-015 headline domain MDEs, and dogfood strategy definitions. The dogfood reference book and positive fixture manifest must be defined before execution.
- **Expected output**: Suite manifest, dependency table, dogfood reference-book manifest, positive fixture manifest, expected-output matrix, and blocker report if any upstream component is unavailable.

### Step 2: Real Dogfood Negative Path

- **Method**: Apply the assembled standalone referees and incremental unit to the EXP-009 dogfood set against the predeclared reference book.
- **Why this method**: The checkpoint names the EXP-009 dogfood set as the real negative path and expects standalone rejections and no incremental edge.
- **Simpler alternative considered**: Use only synthetic negative fixtures. That would not test composition on the real dogfood artifact chain.
- **Assumptions**: Dogfood signals and reference-book positions are aligned by `CloseTime`; incremental denominator is bars where C changes the combined book relative to R-alone.
- **Expected output**: Dogfood suite verdict table, standalone referee outputs, incremental edge table, and denominator summary.

### Step 3: Synthetic Positive Suite-Level Fixture

- **Method**: Run the predeclared planted-edge candidate from the positive fixture manifest: standalone edge above the maximum strict/ratified-loose-or-fallback MDE plus one grid step, and incremental edge above the maximum EXP-015 headline MDE/materiality plus one grid step, against a non-redundant reference with active overlap `<= 0.10` and `abs(rho) <= 0.05`.
- **Why this method**: The checkpoint requires the pass path to be exercised, and EXP-009 is expected to be a negative path.
- **Simpler alternative considered**: Treat a successful dogfood rejection as enough. That would leave positive-path wiring untested.
- **Assumptions**: The planted-edge fixture is predeclared before execution, its expected suite outputs are recorded before replay, and it uses real-price-style return contributions rather than chart-type construction prices.
- **Expected output**: Positive fixture suite verdict table, expected-versus-observed output matrix, non-redundancy diagnostics, and incremental edge summary.

### Step 4: Composition and Wiring Summary

- **Method**: Rule-based integration summary comparing observed path behavior to checkpoint expectations.
- **Why this method**: EXP-016 is exploratory integration, not a new operating-characteristic calibration.
- **Simpler alternative considered**: Produce a single pass/fail statistic. That would obscure which suite element or path failed to wire.
- **Assumptions**: Missing reference-book definition is a blocker, not a result.
- **Expected output**: Suite composition table with path, domain, referee outputs, incremental outputs, denominators, and integration status.

## Visualisations

1. Suite verdict matrix by path, domain, and referee - shows reject/pass wiring.
2. Incremental edge interval plot for dogfood and synthetic positive paths - shows fitness-unit behavior.
3. Denominator and active-change plot for incremental comparisons - shows where C changes the book.
4. Per-domain ratified-loose versus strict outcome plot - shows how EXP-012 decisions flow into the suite.
5. Integration status dashboard table or plot - shows blockers, completed paths, and unexpected outputs.

## Interpretation Guide

- If the dogfood path rejects standalone and shows no positive incremental edge, the negative path wiring is consistent with the checkpoint expectation.
- If the synthetic positive fixture matches the predeclared expected-output matrix, passes both standalone referees, and shows positive incremental edge against a non-redundant reference, the pass path wiring is exercised.
- If either path cannot run because a dependency or reference book is missing, EXP-016 is inconclusive or blocked rather than interpreted as market evidence.
- If the dogfood path unexpectedly shows positive standalone or incremental evidence, report it as an integration observation only; do not treat it as Phase 004 real signal exploration.

## Complexity Check

- Statistical tests: 4 / 4
- Visualisations: 5 / 5
- New modules: 0-1 / 1

## Data-View Comparison Considerations

### Cross-View Alignment

- Align dogfood, reference-book, and return rows by `CloseTime`.
- Do not align domains or suite outputs by row index.

### Implementation Safety and Performance

- Slice to the first 70% analysis set before real dogfood evaluation.
- Use `tqdm` for domain, instrument, strategy, fixture, and suite-component loops.
- Do not recompute or alter upstream adoption decisions, MDE maps, or dogfood definitions.
- Keep outputs concise and traceable to upstream artifacts.

### Real-Price Outcome Discipline

- All standalone and incremental returns use real OHLC domain prices.
- Chart-type candidates and construction prices are out of scope.

### Event Density Differences

- Report dogfood active-bar denominators and incremental C-change denominators separately.

### Regime Stratification

- No regime stratification is scoped for EXP-016.
