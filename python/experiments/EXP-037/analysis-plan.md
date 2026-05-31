# Analysis Plan: Experiment EXP-037

## Objective

Estimate the frozen EXP-036 reference stack's false-positive behavior under the Phase 006 Part A null. The experiment must break the Prior-Range Location state-to-return conditioning relationship while preserving the relevant dependence structure of the descriptor stream and return/control stream. The output is a trusted FPR envelope across valid block lengths, plus a per-leg leak/over-reject profile. It is not a power experiment and does not change the stack.

## Methodology

### Step 1: Holdout-Excluded Load and Frozen Feature Construction

- **Method**: For each instrument, load only the first 70% of CloseTime-sorted 1-minute bars through `load_analysis_timebars(DATA_DIR, instrument)`. Strict-aggregate to 60- and 240-minute bars with `aggregate_ohlc(..., min_coverage=None)`. Reconstruct the EXP-036 Prior-Range Location descriptor and return/control columns exactly: shifted 20-bar prior range, fixed 0.20/0.80 buckets, `d` direction, next-bar and 4-bar real OHLC returns, and prior-bar momentum-sign control.
- **Why this method**: The calibration target is the frozen EXP-036 stack. Reusing the same feature, return, and control definitions makes EXP-037 measure that stack rather than a similar one.
- **Simpler alternative considered**: Calibrate on the already written EXP-036 result tables. Rejected because those tables contain one observed run, not the per-realization null streams needed to measure FPR and diagnostics.
- **Assumptions**:
  - **Temporal structure**: Data is ordered by `CloseTime`; holdout exclusion occurs before aggregation.
  - **Cross-view alignment**: No chart-type comparison is in scope; all forward returns come from same-segment row adjacency after chronological sorting.
  - **Real-price outcomes**: All returns use aggregated real OHLC; no synthetic price path exists.
  - **Predeclaration**: All constants are read from the frozen reference-stack spec and EXP-036 transcription.
- **Expected output**: Observed instrument/timeframe cell frames with `CloseTime`, `Segment`, `Bucket`, `D`, `RetNextBar`, `RetFourBar`, `Control`, entry-gap diagnostics, and observed descriptor/return diagnostics.

### Step 2: Compute Observed Diagnostics and Observed Stack Verdict

- **Method**: Before null resampling, run the frozen stack once on the observed cells and compute the observed descriptor episode counts, median and p90 episode lengths, return lag-1/lag-5 autocorrelation signs, and cross-instrument return-correlation matrices by timeframe.
- **Why this method**: Null diagnostics are judged against observed structure. The observed verdict also confirms the harness reproduces the frozen stack's ordinary input path.
- **Simpler alternative considered**: Skip the observed run and compare null diagnostics only to hard-coded thresholds. Rejected because the thresholds are relative to the observed stream.
- **Assumptions**: The observed run is a reference check, not a new thesis result; it does not re-score or rescue closed theses.
- **Expected output**: `observed_verdict.json`, `observed_diagnostics.csv`, and observed correlation matrices.

### Step 3: Generate Dependence-Preserving Null Realizations

- **Method**: For each block length `L in {20, 60, 240}` and seed index:
  - resample each descriptor stream `(Bucket, D)` independently in complete state-episode blocks inside each instrument/timeframe/segment;
  - resample each return/control stream `(RetNextBar, RetFourBar, Control)` in circular/stationary time blocks with common block starts and lengths across instruments for each timeframe/segment;
  - pair the independent descriptor and return/control streams row-wise, preserving segment labels and cell lengths.
- **Why this method**: The descriptor and return/control streams keep their internal structure while their conditioning relationship is broken. Common return-stream indices across instruments preserve cross-market return correlation better than independent return resampling.
- **Simpler alternative considered**: Naive row shuffle of bucket labels. Rejected as trusted calibration because it destroys state episode lengths and can manufacture an optimistic FPR. It may only be a diagnostic outside the trusted denominator.
- **Assumptions**:
  - The null is trusted only to the extent that its diagnostics pass; failed diagnostics invalidate or caveat the FPR.
  - Segment-preserving resampling keeps the frozen train/test sign-preservation structure intact while breaking within-segment descriptor-to-return conditioning.
- **Expected output**: Per-realization null cell frames and a manifest of block length, seed index, battery partition, and RNG seeds.

### Step 4: Null-Validity Diagnostics

- **Method**: Compare each null realization to the observed diagnostics:
  - descriptor episode count within +/-5%;
  - descriptor median and p90 episode length within +/-10%;
  - lag-1 and lag-5 return autocorrelation signs unchanged;
  - cross-instrument return-correlation matrix Frobenius distance <= 0.20.
- **Why this method**: These are the reference-stack-spec validity gates. They verify that the null destroys the descriptor-to-return link without destroying the structures the null is supposed to preserve.
- **Simpler alternative considered**: Trust all block lengths by construction. Rejected because null realism is the key validity requirement of Stage A.
- **Assumptions**: Diagnostics are descriptive validity checks rather than a search for the most favorable block length. The headline is the envelope across valid block lengths, not a selected best result.
- **Expected output**: `null_diagnostics.csv`, per-L pass rates, and validity flags used to define trusted denominators.

### Step 5: Run the Frozen Stack on Null Realizations

- **Method**: Apply the unchanged EXP-036 frozen stack to every null realization. Preserve floors, neutral baseline, matched-control gate, two-sample episode bootstrap for `Delta_neutral`, paired episode bootstrap for `Delta_control`, train/test sign preservation, k = 2 distinct-instrument replication, secondary 4-bar semantics, and the verdict ladder.
- **Why this method**: The experiment calibrates the existing referee. Any altered bootstrap, threshold, or verdict rule would measure a different referee.
- **Simpler alternative considered**: Estimate per-leg false-pass using simpler row-level means without the frozen bootstrap. Rejected because that does not measure the object that issued the prior closures.
- **Assumptions**:
  - Episode bootstrap handles serial dependence better than row bootstrap.
  - Financial returns are not assumed normal, stationary, or iid.
  - The CI procedure is part of the frozen object, so B remains 10,000 unless a pre-execution compute stop is reached before long execution.
- **Expected output**: `realization_summary.csv`, `cell_passes.csv`, `leg_counts.csv`, and `verdict_ladder_rates.csv`.

### Step 6: Estimate FPR and Per-Leg False-Pass Rates

- **Method**: For each block length and battery partition, compute empirical rates with Wilson intervals for realization-level proportions:
  - full-stack FPR: `FOR` verdict rate on valid null realizations;
  - verdict ladder rates;
  - representation/adjudicability rates;
  - cell-level neutral/control false-pass rates among adjudicable cells;
  - both-contrast cell false-pass rate;
  - aggregate E5/E6 k = 2 conjunction false-pass rates.
- **Why this method**: Empirical rates directly answer the calibration question. Wilson intervals give bounded finite uncertainty summaries for proportions without normal-return assumptions.
- **Simpler alternative considered**: A single pooled p-value. Rejected because the calibration target is an operating-characteristic surface by block length and battery partition, not a hypothesis test against one scalar p-value.
- **Assumptions**:
  - Realization-level rates are conditional on the fixed null family and seed partition.
  - Trusted rates use only odd seed-index second-order holdout cases whose diagnostics pass.
  - Denominator zero is reported as undefined/null, never as a zero rate.
- **Expected output**: `fpr_envelope.json`, `rate_summary.csv`, and `leg_rate_summary.csv`.

### Step 7: Compute Profile and Predeclared Downscale/Stop Rule

- **Method**: Profile the first 10 full-stack equivalents before the long run. If median runtime exceeds 84 CPU-seconds/FSE, downscale Part A from 150 to 100 realizations per block length. If the downscaled profile still breaches the 30 CPU-hour target, stop and report compute infeasibility.
- **Why this method**: The compute budget is part of the frozen reference-stack specification. A calibration regime that exceeds the research budget is a design finding, not an invisible overrun.
- **Simpler alternative considered**: Always run the full 450 FSE. Rejected because it ignores the predeclared compute gate.
- **Assumptions**: Profiling does not inspect outcomes for threshold tuning; it is operational and uses the fixed execution path.
- **Expected output**: `profile_summary.csv`, selected realization count per L, and compute feasibility status.

## Visualisations

1. **FPR envelope by block length** - trusted second-order-holdout full-stack FPR with Wilson intervals for valid L values; development rates shown as lighter context.
2. **Verdict ladder distribution** - stacked rates of `FOR`, `STATE_DIFFERENTIATION_ONLY`, `HORIZON_DEPENDENT`, `INCONCLUSIVE`, and `AGAINST` by block length and battery partition.
3. **Per-leg false-pass rates** - neutral, control, both-contrast, and k = 2 aggregate rates by block length.
4. **Null-validity diagnostic summary** - pass share and key diagnostic distances by block length.

No unbounded detail plots. Plot inputs are aggregated rate tables, not raw row-level series.

## Interpretation Guide

- If at least one block length has passing second-order-holdout diagnostics, report the trusted FPR envelope across valid block lengths and identify leaking/over-rejecting legs from per-leg rates. This supports EXP-037's measurement-success hypothesis.
- If no block length passes diagnostics, do not report a trusted FPR. Interpret EXP-037 as evidence that the predeclared null construction failed its realism requirement.
- If the compute profile triggers the stop rule, report compute infeasibility before long execution. Do not silently reduce the bootstrap B or drop mechanisms/legs.
- If full-stack FPR is near zero but cell-level false-pass rates are high, interpret the stack as conjunctively strict: individual legs leak, but the replication conjunction over-rejects or blocks promotion.
- If full-stack FPR is high on trusted nulls, interpret the stack as permissive under the null family and flag the leaking legs that drive `FOR`.
- If diagnostics pass on development but not second-order holdout, label development rates in-sample only and withhold trusted operating-characteristic claims.
- If valid block lengths disagree materially, report the envelope and do not select the most favorable L.

## Complexity Check

- **Statistical tests**: 3 planned / 3 budgeted - null-validity diagnostics, empirical rate estimates, Wilson intervals for realization-level rates.
- **Visualisations**: 4 planned / 4 budgeted.
- **New modules**: 1 planned / 1 budgeted - `python/src/referee_calibration.py` as the reusable calibration harness for Stage B.

## Data-View Comparison Considerations

### Cross-View Alignment

There is one real-price aggregated data view per timeframe. No chart-type comparison is performed. Return/control stream resampling is by row position within already sorted segment streams; cross-instrument preservation uses common return-stream block indices by timeframe and segment.

### Real-Price Outcome Discipline

All returns are computed from aggregated real OHLC. No HA, Renko, Line Break, or other synthetic construction price appears in the return, control, FPR, or per-leg calculations.

### Event Density Differences

Descriptor episodes are not evenly spaced events; they are state runs on strict aggregated bars. EXP-037 reports representation floors and adjudicability before false-pass rates so count-driven over-rejection is visible.

### Regime Stratification

Out of scope. The block-length grid is a null-construction parameter, not a market-regime stratification or parameter search.
