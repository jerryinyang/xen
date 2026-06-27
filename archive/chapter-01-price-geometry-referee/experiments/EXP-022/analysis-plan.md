# Analysis Plan: Experiment EXP-022

## Objective

Test whether the registered AVWAP band-target/trend-change lifetime method
produces more favorable completed-move outcomes for EXP-020 bounce events than
for matched non-event lifetime analogs. The primary statistic is the domain-level
event minus control favorable target-completion rate.

## Methodology

### Step 1: Dependency Gate and Supported-Cell Load

- **Method**: Load EXP-020 metadata and readiness artifacts. Assert
  `SUPPORTED_FULL`, ready domains `{5m, 1h, 4h}`, zero invariant failures, and
  deterministic replay equality. Load `avwap_events.csv` and
  `avwap_state_summary.csv` only after the gate passes.
- **Why this method**: EXP-022 depends on EXP-020's governed event substrate and
  frozen event target fields.
- **Simpler alternative considered**: Recomputing AVWAP targets independently.
  Rejected because the scope tests the original target fields frozen by EXP-020;
  independent recomputation is useful only as an audit check, not as the primary
  source.
- **Assumptions**: EXP-020 target fields were produced inside the first-70%
  analysis set and are deterministic. This is verified by dependency artifacts
  and event-to-domain joins.
- **Expected output**: Validated event/regime tables and dependency status in
  `run_metadata.json`.

### Step 2: Holdout-Safe Domain Reconstruction

- **Method**: For each instrument, lazy-load the 1-minute source file, sort by
  `CloseTime`, count rows, slice the first 70%, and build 5m, 1h, and 4h domain
  bars with EXP-020 coverage settings. Join event rows to domain bars on
  `instrument`, `domain`, `trigger_idx`, and `trigger_time`.
- **Why this method**: Lifetime completions must be measured on real domain
  closes and must stop before the global holdout.
- **Simpler alternative considered**: Using only EXP-020 event rows. Rejected
  because lifetime completion requires post-trigger real closes inside the
  analysis set.
- **Assumptions**: Domain row indices and `CloseTime` values match EXP-020. Any
  mismatch is a hard failure.
- **Expected output**: Per-cell domain bars, validated event alignments, and
  regime intervals.

### Step 3: Event Lifetime Completion Scan

- **Method**: For each event, scan completed domain closes from `trigger_idx + 1`
  through the analysis-set end. Stop at the first favorable target, adverse
  target, or opposite-regime confirmation. Use EXP-020
  `favorable_target_at_trigger` and `adverse_target_at_trigger` as frozen target
  prices. Record outcome type, completion index/time/close, bars to completion,
  target-distance bps, and lifetime direction-signed return bps.
- **Why this method**: This directly implements the registered original lifetime
  rule without optimizing exits or using intrabar touches.
- **Simpler alternative considered**: Fixed maximum holding period. Rejected
  because EXP-022's purpose is the original lifetime method, not fixed-horizon
  reaction.
- **Assumptions**: Completed `Close` is the only target trigger; intrabar highs
  and lows are deliberately excluded by scope. Future closes are outcomes, not
  signal inputs.
- **Expected output**: Event rows in `lifetime_observations.csv`.

### Step 4: Matched Non-Event Lifetime Analog

- **Method**: Build non-event controls from the event's own `regime_id` (which
  fixes instrument, domain, and regime direction), excluding bounce triggers and
  a 6-bar window around any bounce. Match up to 5 controls per event by nearest
  anchor age and timestamp; the same-regime restriction makes the Step 6 regime
  clusters exact. For each event-control pair, convert the event's favorable and
  adverse target distances to log-return basis points from event trigger close,
  then apply those distances to the control close in the same direction. Scan the
  control's future closes with the same target/trend-change/unfinished rules.
- **Target-distance formula**: With `d = direction`,
  `favorable_bps = d * 10000 * log(event_favorable_target / event_trigger_close)`
  and
  `adverse_bps = d * 10000 * log(event_adverse_target / event_trigger_close)`.
  Then
  `control_favorable_target = control_close * exp(d * favorable_bps / 10000)`
  and
  `control_adverse_target = control_close * exp(d * adverse_bps / 10000)`.
  Valid event targets must have `favorable_bps > 0` and `adverse_bps < 0`.
- **Why this method**: It supplies the benchmark required by the Phase 004
  checkpoint and keeps the control challenge comparable to the event's frozen
  target geometry without defining a new AVWAP target at non-event bars.
- **Simpler alternative considered**: Reporting unbenchmarked event lifetime
  metrics only. Rejected because the active checkpoint says unbenchmarked
  lifetime results are descriptive and cannot authorize screening.
- **Assumptions**: Target-distance transfer uses only event-time and control-time
  information, not future control outcomes. Matching variables are known at the
  control timestamp.
- **Expected output**: Matched-control rows in `lifetime_observations.csv` and
  `control_lifetime_diagnostics.csv`, the latter gaining `event_localvol_bps`,
  `control_localvol_bps`, and `vol_context_ratio` columns (20-bar MAD of
  typical-price log returns ending at and including the reference bar,
  look-ahead-safe, fixed window, no tuning) for the volatility-context
  diagnostic.

### Step 5: Completion-Rate and Expectancy Metrics

- **Method**: Summarize outcome counts by instrument, domain, direction, and
  `is_pyramid_bounce`. Compute favorable target-completion rate as
  `favorable / (favorable + adverse)` for event and controls separately. Report
  trend-change and unfinished rates outside that denominator. Compute
  direction-signed lifetime expectancy in basis points for target completions and
  trend-change completions separately.
- **Why this method**: It follows the registry's denominator rule and prevents
  unfinished observations from being mislabeled as losses or wins.
- **Simpler alternative considered**: Counting trend-change completions as
  failures in the target-completion rate. Rejected because the registry requires
  trend-change completions to be reported separately.
- **Assumptions**: Completed target outcomes are comparable between events and
  matched controls because target distances are normalized in log-return basis
  points.
- **Expected output**: `lifetime_completion_summary.csv` and expectancy columns
  in `domain_lifetime_tests.csv`.

### Step 6: Domain-Level Primary Test

- **Method**: For each lifetime-reportable domain, first compute each reportable
  instrument's event-minus-control favorable target-completion rate in percentage
  points; the domain rate difference is the unweighted mean of those
  per-instrument differences (equal weight per instrument). Estimate its 95% CI
  with a regime-cluster bootstrap resampling `regime_id` clusters within
  instrument/direction strata, recomputing each per-instrument difference and
  averaging across instruments; the same-regime control restriction (Step 4)
  makes these clusters exact. Compute a stratified paired permutation p-value on
  the same instrument-averaged statistic for the null of no event-control rate
  advantage. Apply Holm adjustment across the three domain primary p-values.
  Report the instrument-averaged lifetime-expectancy advantage (bps) as a
  required consistency check, not as a second way to pass the primary test.
- **Why this method**: It is non-parametric, respects repeated events within
  regimes, and handles bounded rate outcomes without assuming normality.
- **Simpler alternative considered**: A two-proportion z-test. Rejected because
  it assumes independent Bernoulli observations and ignores event clustering. An
  event-weighted pool across instruments was also rejected so a high-event
  instrument cannot dominate the domain rate, consistent with EXP-008's
  per-instrument heterogeneity finding.
- **Assumptions**: Regime clusters are the practical dependence unit. Instrument
  strata are preserved so high-event instruments do not silently redefine the
  domain result.
- **Expected output**: `domain_lifetime_tests.csv` with rate difference, CI,
  p-values, Holm-adjusted decision, target-completion denominators, and
  expectancy consistency fields.

### Step 7: Censoring and Stratification Diagnostics

- **Method**: Report unfinished rates, trend-change rates, bars-to-completion
  distributions, target-distance distributions, and descriptive splits by
  direction and `is_pyramid_bounce`. Also report the per-domain distribution and
  median of the matched-pair volatility-context ratio
  (`control_localvol_bps / event_localvol_bps`), folded into the existing
  target-distance diagnostic so no new plot is added. The volatility-context
  ratio is descriptive, but it feeds the predeclared volatility-context
  inconclusive trigger defined in the scope and interpretation guide; the other
  diagnostics do not change the primary decision.
- **Why this method**: Lifetime tests can look favorable simply because many
  observations are censored or because only one event subtype works. The
  diagnostics reveal those failure modes.
- **Simpler alternative considered**: Reporting only the primary rate. Rejected
  because EXP-022 must preserve the original metric book context for EXP-023.
- **Assumptions**: Subgroup diagnostics are hypothesis-generating unless a later
  scope predeclares them.
- **Expected output**: Diagnostic rows in `lifetime_completion_summary.csv`,
  `control_lifetime_diagnostics.csv`, and plots.

## Visualisations

1. **Outcome composition stacked bars** by domain for events and controls -
   shows favorable, adverse, trend-change, and unfinished shares.
2. **Favorable target-completion rate forest plot** by domain with event-control
   differences and CIs - the headline lifetime result.
3. **Lifetime expectancy forest plot** by domain and completion type - checks
   whether favorable-rate evidence agrees with realized move size.
4. **Bars-to-completion distribution plot** for events and controls - shows
   whether results depend on long-lived unresolved moves.
5. **Direction and pyramid-bounce diagnostic heatmap** - shows whether the
   result is concentrated in one direction or repeated-bounce subtype.

## Interpretation Guide

- If at least one lifetime-reportable domain has a favorable-rate difference
  above 0 percentage points, CI lower bound above 0, Holm-adjusted p-value
  `<= 0.05`, and non-worse lifetime expectancy point estimate, interpret
  EXP-022 as supporting the original lifetime operationalization for that
  domain.
- If every lifetime-reportable domain has a favorable-rate-difference CI upper
  bound `<= 0`, or if event expectancy is worse than controls in every reportable
  domain, interpret EXP-022 as refuting the original lifetime operationalization.
- If denominators are sparse, censoring is severe, or rate and expectancy point
  in opposite directions, interpret EXP-022 as inconclusive.
- The favorable-rate edge is conditional on comparable target difficulty. Report
  the volatility-context ratio with every domain result. If a domain otherwise
  passes but its median matched-pair ratio
  (`control_localvol_bps / event_localvol_bps`) is outside `[0.5, 2.0]`, downgrade
  it to inconclusive (`volatility-context-confounded`): the favorable-target rate
  cannot be cleanly attributed to a bounce edge versus an event-vs-control
  volatility mismatch.
- Trend-change and unfinished observations are meaningful outcomes for method
  diagnosis, but they are not part of the favorable target-completion
  denominator.
- Do not infer that a favorable lifetime component result is a strategy
  qualification. EXP-023 remains required for any cTrader/frozen-suite screen.

## Implementation Safety Constraints

- **Holdout**: Slice source data to the first 70% before collecting or building
  domain bars. Completion scans must stop at the analysis-set end.
- **Look-ahead**: Targets are frozen at event/control start. Matching uses no
  future outcomes. Future closes are used only for lifetime outcome measurement.
- **Real-price discipline**: Use real domain `Close` prices only. No synthetic
  chart prices, intrabar touches, or strategy P&L.
- **Denominators**: Report favorable, adverse, trend-change, and unfinished
  counts separately. Zero target-completion denominators produce null rates, not
  zeros.
- **Control benchmark**: Target-distance transfer must be deterministic and
  recorded. Do not tune target distances or exclusion windows after outcomes are
  computed.
- **Duplicate handling**: If controls tie on anchor age and timestamp, use row
  index as a deterministic final sort key. Do not silently drop events.
- **Bounded plotting**: Plot aggregated lifetime outputs; do not convert full
  source bars to pandas.
- **Progress**: Use `tqdm` over instrument/domain and event/control lifetime
  scan loops.
- **Vectorization**: Domain joins and target-condition arrays may be vectorized
  when they preserve first-hit ordering. First completion must remain the first
  completed close by time, never a vectorized shortcut that changes tie or order
  semantics.

## Complexity Check

- Statistical tests: 3 / 3 (rate-difference regime-cluster bootstrap; paired
  permutation with Holm adjustment; expectancy consistency CI)
- Visualisations: 5 / 5
- New modules: 1 / 1 (experiment-local helper only if needed)

## Expected Output Files

```text
python/experiments/EXP-022/results/
- lifetime_observations.csv
- lifetime_completion_summary.csv
- domain_lifetime_tests.csv
- control_lifetime_diagnostics.csv
- run_metadata.json

python/experiments/EXP-022/plots/
- lifetime_outcome_composition.png
- favorable_completion_forest.png
- lifetime_expectancy_forest.png
- bars_to_completion_distribution.png
- direction_pyramid_diagnostics.png
```
