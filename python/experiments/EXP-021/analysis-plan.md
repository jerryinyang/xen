# Analysis Plan: Experiment EXP-021

## Objective

Test whether EXP-020 AVWAP bounce events have better fixed-horizon
direction-signed real-price reaction than matched non-event controls. The
primary confirmatory test is the matched event-control return advantage at 3
completed domain bars after trigger.

## Methodology

### Step 1: Dependency Gate and Supported-Cell Load

- **Method**: Load EXP-020 metadata and readiness artifacts. Assert
  `SUPPORTED_FULL`, ready domains `{5m, 1h, 4h}`, zero invariant failures, and
  deterministic replay equality. Load `avwap_events.csv` and
  `avwap_state_summary.csv` only after the gate passes.
- **Why this method**: EXP-021 is downstream of the substrate gate. If the
  substrate is not supported, reaction testing is not meaningful.
- **Simpler alternative considered**: Rebuilding the AVWAP state machine and
  ignoring EXP-020 status. Rejected because EXP-020 is the governed substrate
  source and already validates determinism and temporal invariants.
- **Assumptions**: EXP-020 artifacts contain only first-70% analysis-set events.
  This is verified by artifact checks and by rejoining events to rebuilt domain
  bars.
- **Expected output**: Validated supported-cell list and event/regime tables in
  memory, plus dependency status in `run_metadata.json`.

### Step 2: Holdout-Safe Domain Reconstruction

- **Method**: For each instrument, lazy-load the 1-minute source file, sort by
  `CloseTime`, count rows, slice the first 70%, and build 5m, 1h, and 4h domain
  bars with the same coverage settings used in EXP-020. Join EXP-020 events to
  domain bars on `instrument`, `domain`, `trigger_idx`, and `trigger_time`.
- **Why this method**: It gives real future `Close` prices for outcome
  measurement while independently reasserting the holdout fence.
- **Simpler alternative considered**: Reading a cached full domain frame if one
  exists. Rejected unless it records the same 70% cutoff, because cached data
  could accidentally contain holdout rows.
- **Assumptions**: `CloseTime` is the temporal authority. Domain row indices must
  match EXP-020 generation; mismatches are implementation errors, not data to be
  repaired silently.
- **Expected output**: Per-cell domain bars with event alignment checks and
  future-close availability flags.

### Step 3: Matched Non-Event Control Construction

- **Method**: Build eligible non-event controls from EXP-020 regime intervals.
  Candidate controls must belong to the same `regime_id` as the event (which
  fixes instrument, domain, and regime direction); must not be bounce trigger
  bars; must be outside a 6-bar exclusion window around any bounce trigger in the
  same cell; must have enough future bars for the horizon; and must have
  computable anchor age. For each event and horizon, select up to 5 controls by
  nearest anchor age and then nearest timestamp. The primary matched test
  requires at least 3 controls. Controls are unique within an event; reuse across
  separate events is allowed only within the same regime, so each control bar
  belongs to exactly one regime and the Step 5 regime clusters are exact.
- **Why this method**: Matching within instrument/domain/direction controls for
  the largest structural differences without introducing a model or parameter
  sweep. Anchor-age matching keeps controls in comparable AVWAP lifecycle
  context.
- **Simpler alternative considered**: Comparing events to all non-event bars in
  the same domain. Rejected because raw pooling would let high-density cells and
  unrelated regime phases dominate the benchmark.
- **Assumptions**: Matching variables are known at or before the candidate
  control timestamp. Control selection does not use future returns.
- **Expected output**: `control_match_diagnostics.csv` and matched event-control
  records for horizons 1, 3, and 6.

### Step 4: Fixed-Horizon Reaction Metrics

- **Method**: Compute direction-signed log returns in basis points for each event
  and each matched control:
  `10000 * direction * log(Close[t+h] / Close[t])`. For each event, average its
  matched-control returns at the same horizon, then compute the paired
  difference `event_return_bps - matched_control_mean_bps`. Summarize by
  instrument, domain, direction, and horizon.
- **Why this method**: Direction-signed real-close returns directly answer
  whether price reacts in the bounce direction. Event-level paired differences
  keep the benchmark denominator aligned to the event denominator.
- **Simpler alternative considered**: Raw future returns without direction
  signing. Rejected because bullish and bearish bounces would cancel by design.
- **Assumptions**: Future closes are outcomes, not signal inputs. Log returns
  avoid asymmetric percent arithmetic and remain comparable across instruments.
- **Expected output**: `reaction_observations.csv` and `reaction_summary.csv`.

### Step 5: Domain-Level Primary Test

- **Method**: For each domain, first compute each reportable instrument's
  event-weighted mean primary-horizon paired difference (both directions pooled
  within the instrument via direction-signing). The domain effect is the
  unweighted mean of those per-instrument means (equal weight per instrument).
  Estimate its 95% CI with a regime-cluster bootstrap that resamples `regime_id`
  clusters within instrument/direction strata, recomputes each per-instrument
  mean, then averages across instruments. Compute a stratified paired
  sign-permutation p-value on the same instrument-averaged statistic (sign flips
  within instrument/direction strata) for the null of zero event-control
  advantage. Apply Holm adjustment to the three domain primary p-values. The
  same-regime control restriction (Step 3) makes the resampled `regime_id`
  clusters exact.
- **Why this method**: It is non-parametric, respects repeated events inside a
  regime better than row-wise iid resampling, and preserves instrument/direction
  strata.
- **Simpler alternative considered**: A t-test on paired differences. Rejected
  because return differences need not be normal or independent. An event-weighted
  raw-bps pool was also rejected: it is dominated by the highest-volatility,
  highest-event-count instrument (BTCUSD) and would reduce the domain claim to an
  instrument claim, contradicting EXP-008's per-instrument heterogeneity finding;
  per-instrument standardization was rejected for adding an estimated scale and
  discarding economic bps interpretability.
- **Assumptions**: Regime clusters are a practical dependence unit for AVWAP
  bounce events. With only four instruments, instrument-level bootstrap alone
  would be too coarse, so instrument/direction strata are preserved rather than
  resampled as the only uncertainty unit.
- **Expected output**: `domain_reaction_tests.csv` with primary effect, CI,
  raw p-value, Holm-adjusted p-value, and support/refute/inconclusive label.

### Step 6: Secondary Horizon and Stability Diagnostics

- **Method**: Repeat the domain-level summaries for 1-bar and 6-bar horizons as
  predeclared diagnostics. Report instrument-level and direction-level summaries
  descriptively; do not use them to override the 3-bar primary decision.
- **Why this method**: The registry fixed horizons 1, 3, and 6. Secondary
  horizons show whether any primary result is a one-horizon artifact.
- **Simpler alternative considered**: Testing only the primary 3-bar horizon.
  Rejected because the registered metric family includes the adjacent horizons,
  and they are useful for interpretation.
- **Assumptions**: Secondary diagnostics are not a license to pick a winning
  horizon after seeing outcomes.
- **Expected output**: Secondary rows in `reaction_summary.csv` and
  `domain_reaction_tests.csv`.

## Visualisations

1. **Domain effect forest plot** for 1-, 3-, and 6-bar event-control advantage,
   with the primary 3-bar horizon highlighted - shows the headline reaction
   estimate and uncertainty.
2. **Event vs matched-control distribution plot** at the 3-bar horizon, faceted
   by domain - shows distribution shape and tail behavior.
3. **Instrument-direction heatmap** of primary paired advantage - shows whether
   domain evidence is broad or concentrated.
4. **Control-match diagnostics chart** of reportable events and controls by
   instrument/domain - verifies denominator health.

## Interpretation Guide

- If at least one reaction-reportable domain has a positive 3-bar paired
  advantage, CI lower bound above 0 bps, and Holm-adjusted p-value `<= 0.05`,
  interpret EXP-021 as supporting the fixed-horizon reaction operationalization
  for that domain.
- If every reaction-reportable domain has a 3-bar CI upper bound `<= 0 bps`,
  interpret EXP-021 as refuting the fixed-horizon reaction operationalization.
- If no domain supports the hypothesis and at least one reportable domain spans
  0 bps, interpret EXP-021 as inconclusive rather than negative.
- If a domain passes the primary rule but both 1-bar and 6-bar point estimates
  are below 0 bps in that same domain, interpret the result as inconclusive
  because the horizon pattern is unstable.
- Never compute percentage improvement over a zero or near-zero control mean;
  report bps differences and confidence intervals.

## Implementation Safety Constraints

- **Holdout**: Slice source data to the first 70% before collecting or building
  domain bars. Event and control outcomes must not read beyond the analysis set.
- **Look-ahead**: Event and control selection uses only trigger/control timestamp
  metadata and regime state known at that timestamp. Future closes are used only
  as outcomes.
- **Real-price discipline**: Use real domain `Close` prices only. No synthetic
  chart prices and no strategy P&L.
- **Denominators**: Report event counts, matched-control counts, and
  non-reportable reasons by instrument, domain, direction, and horizon. Zero
  denominators produce null metrics, not zeros. Report events made non-reportable
  specifically by the same-regime control restriction
  (`insufficient_same_regime_controls`) so its cost to coverage is visible,
  especially at 4h.
- **Duplicate handling**: If multiple controls tie on anchor age and timestamp,
  apply a deterministic secondary sort by row index; do not silently drop event
  rows.
- **Bounded plotting**: Plot aggregated summaries or bounded paired records; do
  not convert full source bars to pandas for plotting.
- **Progress**: Use `tqdm` over instrument/domain and horizon loops.
- **Vectorization**: Return calculations and joins may be vectorized. Control
  matching may use sorted joins or explicit bounded loops, provided sample
  membership and deterministic ordering are preserved.

## Complexity Check

- Statistical tests: 2 / 2 (regime-cluster bootstrap CI; stratified paired
  permutation with Holm adjustment for the primary domain family)
- Visualisations: 4 / 4
- New modules: 1 / 1 (experiment-local helper only if needed)

## Expected Output Files

```text
python/experiments/EXP-021/results/
- reaction_observations.csv
- reaction_summary.csv
- domain_reaction_tests.csv
- control_match_diagnostics.csv
- run_metadata.json

python/experiments/EXP-021/plots/
- domain_reaction_forest.png
- event_control_distributions.png
- instrument_direction_heatmap.png
- control_match_diagnostics.png
```
