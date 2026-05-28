# Analysis Plan: Experiment EXP-032

## Objective

Determine whether the USTEC Candidate A breaker chain remains eligible for Branch A continuation when moved from the EXP-031 15-minute view to a synthetic 1-hour view. The experiment is a binding magnitude gate: it must show adequate 1-hour counts, positive train and test Return_R_60m differences, a test CI excluding zero positively, and a test point estimate at least 50 percent of EXP-031's 15-minute test effect (`>= 0.918R`) before EXP-033 temporal segmentation can be scoped.

## Methodology

### Step 1: Holdout-Safe 1-Hour Aggregation and Reference Loading

- **Method**: Lazily scan the USTEC 1-minute Parquet, sort by `CloseTime`, slice the first 70 percent chronologically as the analysis set, and pass only that analysis-set slice to `bar_aggregator.aggregate_ohlc(period_minutes=60)`. Drop incomplete 1-hour windows via the aggregator's `SourceBars == 60` rule. Retain the 1-minute analysis-set frame for outcome evaluation. Load EXP-014 PDH/PDL/ONH/ONL levels and EXP-031/EXP-023 reference result tables.
- **Why this method**: The holdout exclusion must happen before aggregation. Reusing `bar_aggregator.py` avoids new shared infrastructure and keeps aggregation identical to the approved Phase 004A pattern.
- **Simpler alternative considered**: Aggregating the full USTEC file and then slicing the 1-hour output is simpler, but it would inspect the final 30 percent holdout and is prohibited.
- **Assumptions**:
  - **Temporal structure**: 1-minute and 1-hour frames are ordered by `CloseTime`.
  - **Cross-view alignment**: 1-hour event times map to real 1-minute `CloseTime`, never row index.
  - **Real-price outcomes**: The 1-hour frame is detection-only; outcomes use real 1-minute OHLC.
- **Expected output**: `coverage_summary`, a holdout-excluded USTEC 1-hour frame, the retained 1-minute analysis-set frame, and loaded EXP-031/EXP-023 reference values.

### Step 2: 1-Hour Sweep, Displacement, and Candidate A Detection

- **Method**: Apply the inherited sweep, displacement, and Candidate A rule family to the 1-hour frame using the elapsed-time-scaled constants from `scope.md`: ATR_14_1h buffer; 25-bar body median; 3-bar max displacement confirmation; 8-bar Candidate A order-block lookback; 30-bar breaker-confirmation lifecycle. Preserve first-touch policy and stop invalidation rules from EXP-031.
- **Why this method**: EXP-032 is a 1-hour analogue of EXP-031. Elapsed-time scaling avoids silently expanding the structural windows from hours to days just because the bar size changed.
- **Simpler alternative considered**: Keeping raw EXP-031 bar counts would use 100 hours for the displacement median, 30 hours for order-block search, and 120 hours for breaker confirmation. That would no longer test an EXP-031 analogue.
- **Assumptions**:
  - **Temporal structure**: Displacement and breaker labels use only the current or prior 1-hour bars at their detection timestamps.
  - **Cross-view alignment**: Daily levels are joined by NY date and level family, not bar index.
  - **Real-price outcomes**: No outcomes are computed in this step.
- **Expected output**: Sweep, displacement, and breaker-labeled event tables with `CloseTime`, side, level type, stop, buffer, displacement timestamp, breaker timestamp, delay bars, and train/test segment.

### Step 3: Real-Price Outcome Evaluation

- **Method**: For all risk-feasible displacement events, use the 1-hour displacement close as the canonical entry timestamp. Candidate A is a retrospective label on that displacement event, matching EXP-031's comparability convention. Walk the 1-minute analysis-set series strictly after the displacement `CloseTime`; exclude any 1-minute movement inside the confirming 1-hour candle. Inherit the EXP-015 sweep stop. Compute Return_R_60m, MAE_R_60m, MFE_R_60m, Hit1R_60m, average R, drawdown proxy, win rate, trade count, and 60-minute forward log return. Mark rows with inherited risk below the sweep buffer as risk-infeasible and exclude them from R-based summaries while retaining them in count diagnostics.
- **Why this method**: It preserves the approved EXP-031 outcome convention and avoids using synthetic 1-hour prices for strategy outcomes.
- **Simpler alternative considered**: Entering at breaker-confirmation close would be more natural for a live strategy, but it would answer a different execution question reserved for later friction/stress work.
- **Assumptions**:
  - **Temporal structure**: Outcome paths use only 1-minute bars after the 1-hour displacement close.
  - **Cross-view alignment**: Matching is by timestamp using `searchsorted(..., side="right")` or equivalent.
  - **Real-price outcomes**: All R-multiple and excursion metrics use real 1-minute OHLC.
- **Expected output**: A per-event outcome table for all displacement events, with breaker label, feasibility flag, Return_R, MAE_R, MFE_R, Hit1R, and segment.

### Step 4: Counts, Bootstrap Intervals, and Branch Gate Verdict

- **Method (counts first)**: Report sweep -> displacement -> breaker-labeled -> risk-feasible breaker counts by train/test segment. Check the `>= 50` feasible breaker floor in each segment. Compute 1-hour / EXP-031 15-minute displacement retention and breaker-feasible retention ratios; flag any ratio below 30 percent before interpreting effect direction.
- **Method (primary statistical test)**: Use a label-stratified bootstrap with 10,000 resamples and seed 42 on risk-feasible displacement events. In each segment, resample displacement events with replacement, recompute baseline mean Return_R_60m and breaker-subset mean Return_R_60m within the same resample, and record breaker-minus-baseline difference. This is statistical test family 1.
- **Method (secondary diagnostics)**: Use the same bootstrap family for MAE_R_60m and MFE_R_60m differences by segment. Report Hit1R_60m and log-return differences descriptively. This is statistical test family 2.
- **Method (reference comparison)**: Compare the 1-hour test Return_R_60m diff to EXP-031's 15-minute test diff (`+1.836R`) and EXP-023's 1-minute test diff (`+4.176R`). The hard magnitude gate is `>= 0.918R` (50 percent of EXP-031). The `>= 2.088R` EXP-023 half-band is reported as a stricter non-binding reference. This is a deterministic threshold comparison, not an additional inferential test.
- **Why this method**: The bootstrap preserves the subset relationship between breaker-labeled events and the displacement baseline. The hard threshold makes the Branch A continuation decision reproducible before seeing results.
- **Simpler alternative considered**: An unpaired bootstrap or t-test would ignore the subset relationship and impose assumptions that are not needed for this event study.
- **Assumptions**:
  - **Temporal structure**: Bootstrap intervals estimate event-level uncertainty but do not make i.i.d. market claims; train/test chronology remains the main guardrail.
  - **Cross-view alignment**: Reference comparisons are by scoped metrics and segment, not by matching individual events across timeframes.
  - **Real-price outcomes**: All compared metrics use real-price outcomes.
- **Expected output**: `event_waterfall.csv`, `outcome_summary.csv`, `bootstrap_primary.csv`, `bootstrap_secondary.csv`, `reference_comparison.csv`, `coverage_summary.csv`, `results.json`, and a concise `numerical_summary.txt`.

## Visualisations

1. **Event-count waterfall**: sweep -> displacement -> breaker-labeled -> risk-feasible breaker by train/test, with the 50-event floor marked.
2. **Return_R_60m interval plot**: baseline and breaker means plus breaker-minus-baseline diff by segment, with EXP-031 and EXP-023 reference bands shown separately.
3. **Test-segment R-multiple distribution**: baseline versus breaker-labeled events, capped for readability but with uncapped values retained in tables.
4. **MAE_R_60m interval plot**: breaker-minus-baseline MAE difference by segment, showing whether the structural drawdown improvement from EXP-031 persists.

## Interpretation Guide

- **FOR Branch A continuation**: Event floors pass, train/test Return_R_60m diffs are positive, test CI excludes zero positively, and test diff is `>= 0.918R`. If this occurs, EXP-033 temporal segmentation may be scoped; do not claim a candidate is validated.
- **AGAINST Branch A continuation**: Event floors pass but any hard gate fails. This means the higher-timeframe magnitude check did not support continuation; Branch A stops before EXP-033 unless a new reflection explicitly reframes it with weaker claims.
- **INCONCLUSIVE**: Event floors fail, retention falls below 30 percent, or references are unavailable. This records a resolution-cost limitation and still blocks automatic EXP-033 scoping.
- **Secondary MAE reading**: Lower MAE_R_60m in both segments strengthens the structural interpretation. Worse MAE does not override a hard Return_R pass by itself, but must be flagged as a material caveat.

## Complexity Check

- Statistical tests: 2 / 3
- Visualisations: 4 / 4
- New modules: 0 / 0

## Data-View Comparison Considerations

### Cross-View Alignment

- Detection uses 1-hour `CloseTime`; outcomes use real 1-minute bars strictly after the 1-hour displacement `CloseTime`.
- The breaker subset is paired to its parent displacement event by event identity and timestamp.
- Reference comparisons use metric-level comparisons to EXP-031 and EXP-023, not event-level matching across timeframes.

### Real-Price Outcome Discipline

- Return_R, MAE_R, MFE_R, Hit1R, and log returns are computed from real 1-minute OHLC prices.
- The synthetic 1-hour bars are only a detection view.
- The inherited stop and buffer are in real-price units.

### Event Density Differences

- 1-hour events may be much sparser than 15-minute events. Count floors and retention ratios are checked before interpreting effects.
- Count collapse is not a reason to return to 1-minute structural claims; it triggers stop-or-reframe review.

### Scope Control

- No segmentation, control matching, cost stress, or execution-delay variants are included here. Those remain downstream only if EXP-032 passes.
