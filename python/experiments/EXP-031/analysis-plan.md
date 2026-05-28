# Analysis Plan: Experiment EXP-031

## Objective

Determine whether the EXP-023 USTEC Candidate A breaker positive replicates at 15-minute bar resolution by running the same sweep-displacement-breaker chain on synthetic 15-minute bars, computing expectancy in R against a same-timeframe displacement-only baseline using real 1-minute prices, and comparing the resulting test-segment point estimate and bootstrap CI to the EXP-023 1-minute USTEC reference. Counts and retention are reported before any expectancy difference.

## Methodology

### Step 1: Holdout-Safe 15-Minute Aggregation and Level Loading

- **Method**: Lazily scan the USTEC 1-minute Parquet, sort by `CloseTime`, slice the first 70 percent chronologically as the analysis set, and resample the analysis-set slice only into synthetic 15-minute OHLC via deterministic clock-aligned non-overlapping windows. Drop partial trailing 15-minute windows. Load the EXP-014 reproducible PDH/PDL/ONH/ONL daily levels covering the analysis-set date range. Retain the 1-minute analysis-set slice in memory for outcome evaluation.
- **Why this method**: Holdout exclusion must apply to the 1-minute series before aggregation per the design.md data-scope rule. Reusing the EXP-029 / EXP-030 `bar_aggregator.py` keeps the resampling deterministic and identical across all three pre-phase experiments.
- **Simpler alternative considered**: Aggregating the full series and re-slicing on the 15-minute side would be one line shorter but is a governance violation.
- **Assumptions**:
  - **Temporal structure**: 1-minute and 15-minute series are chronologically ordered by `CloseTime`.
  - **Cross-view alignment**: 15-minute event `CloseTime` maps to 1-minute `CloseTime` for outcome evaluation; never bar index.
  - **Real-price outcomes**: Outcomes are evaluated on 1-minute real OHLC.
- **Expected output**: One 15-minute USTEC DataFrame, one 1-minute USTEC analysis-set DataFrame, and a daily-levels table joined to NY-time session boundaries.

### Step 2: Sweep, Displacement, and Candidate A Breaker Detection on 15-Minute Bars

- **Method**: Apply the EXP-015 first-touch sweep definition to the 15-minute series with buffer `max(price_precision_step, 0.05 * ATR_14_15m)`. Apply the EXP-018 displacement definition to qualified sweeps on the 15-minute candle sequence. Apply the EXP-022 Candidate A breaker (last-opposite-candle / order-block proxy) to displacement-confirmed events on the 15-minute candle sequence. Record at each step the event timestamp (15-minute `CloseTime` of the confirming candle), boundaries, invalidation, and duplicate handling. Canonical entry timestamp is the displacement-close 15-minute `CloseTime`, matching the EXP-023 displacement-close canonical entry inherited at the lower timeframe.
- **Why this method**: Direct transfer at the rule level is the only fair test of "does the EXP-023 USTEC positive replicate at 15-minute." Using displacement-close as the canonical entry preserves comparability with EXP-023.
- **Simpler alternative considered**: Using second-candle-open as the primary entry would require an additional 15-minute candle and reduce sample size further; it is reserved for stress variants in EXP-034 and excluded here.
- **Assumptions**:
  - **Temporal structure**: All chain stages use only the closing 15-minute bar and prior bars; no future data.
  - **Cross-view alignment**: Level activation aligns to NY-time session boundaries already used in EXP-014.
  - **Real-price outcomes**: Not yet evaluated.
- **Expected output**: Per-stage event tables (sweep, displacement, Candidate A breaker) with timestamps, sides, level types, stops, sweep extremes, and segment labels, plus a sweep -> displacement -> breaker -> risk-feasible event-count waterfall.

### Step 3: Outcome Evaluation on Real 1-Minute Prices With Inherited Stops

- **Method**: All events — both displacement-only baseline and the Candidate A breaker-confirmed subset — use the displacement candle close as the canonical entry, matching EXP-023's 1-minute entry timing. The outcome clock starts at the close of the confirming 15-minute displacement candle for every event. Walk the 1-minute analysis-set series forward strictly after that timestamp. Inherit the stop from the EXP-015 sweep (sweep extreme plus/minus the same `buffer`). Initial risk is the absolute distance from the displacement-close to the stop in 1-minute price units. Compute expectancy in R, average R, drawdown proxy (mean MAE in R), win rate, MAE in R, MFE in R, trade count, and 60-minute forward log return. Mark events whose inherited risk is below the original sweep `buffer` as risk-infeasible and exclude them from R-based summaries while retaining them in retention diagnostics. The breaker subset is defined as the displacement events for which a Candidate A breaker confirms before sweep-stop invalidation within the predeclared post-displacement window; it is a label, not a separate entry timestamp.
- **Why this method**: The EXP-023 inherited-stop convention and displacement-close entry timing are required for direct comparability; expectancy in R is the EXP-023 primary metric. Using the breaker as a label rather than a separate entry preserves comparability with EXP-023's 1-minute result and matches the design.md statement that "EXP-023 measured Candidate A breaker outcomes at displacement-close."
- **Simpler alternative considered**: Entering at the breaker-confirmation candle close would change both the entry timing and the comparator and would not be directly comparable to EXP-023; that variant is reserved for EXP-034 stress-style scope work, not the 15-minute resolution-stability check.
- **Assumptions**:
  - **Temporal structure**: 1-minute outcome walk is strictly forward from the displacement-close timestamp.
  - **Cross-view alignment**: 15-minute displacement `CloseTime` is matched to the first 1-minute bar with `CloseTime` strictly greater than the 15-minute displacement `CloseTime`.
  - **Real-price outcomes**: All outcome metrics use real 1-minute OHLC.
- **Expected output**: Per-event outcome row joined to the Step 2 chain tables, marked baseline (all displacement events) or breaker-confirmed (the subset where Candidate A breaker formed within the window).

### Step 4: Counts, Comparison, and Resolution-Stability Verdict

- **Method (counts and retention first)**: Report the sweep -> displacement -> Candidate A breaker -> risk-feasible event-count waterfall per segment. Compare risk-feasible breaker-labeled counts against the predeclared `>= 50` train/test floor. Compute the 15-minute / 1-minute retention ratio against EXP-023 displacement counts; if it falls below 30 percent, mark the comparison as resolution-cost-limited.
- **Method (primary expectancy comparison)**: For each segment, compute the difference in expectancy in R between the Candidate A breaker-labeled subset and the full displacement-only baseline using only risk-feasible rows. Because the breaker subset is a strict subset of the baseline (same entry, same forward window, different label), inference uses a label-stratified bootstrap: in each of 10,000 resamples with fixed seed 42, resample the displacement event set with replacement and recompute both the baseline mean and the breaker-subset mean from the resampled events, then take the difference. This preserves the subset relationship within each replicate. Statistical test 1.
- **Method (secondary diagnostics)**: For each segment, compute the differences in average R, drawdown proxy, and 60-minute forward log return using the same bootstrap procedure. Win rate and MAE are reported as descriptives without bootstrap. Statistical tests 2 and 3 (counted jointly as a single secondary diagnostic family).
- **Method (timeframe comparability)**: Report the 15-minute USTEC test-segment expectancy difference and CI side by side with the EXP-023 1-minute USTEC point estimate and CI. The reflection uses both rows; no statistical test is run on the cross-timeframe difference because the two samples are not independent.
- **Why this method**: Paired bootstrap matches EXP-023's bootstrap family and preserves comparability. R-based exclusion of infeasible rows matches EXP-023's inherited-stop convention.
- **Simpler alternative considered**: An unpaired bootstrap would inflate variance because the breaker subset is a strict subset of the displacement baseline.
- **Assumptions**:
  - **Temporal structure**: Bootstrap resamples preserve segment ordering; pairing preserves the subset relationship.
  - **Cross-view alignment**: All comparisons are by timestamp via the 15-minute `CloseTime` mapping.
  - **Real-price outcomes**: All differences are computed on 1-minute real-price R-multiple outcomes.
- **Expected output**: USTEC table with sweep / displacement / breaker / risk-feasible counts per segment, retention vs EXP-023, primary expectancy difference and CI per segment, secondary diagnostic differences and CIs, 15-minute-vs-1-minute side-by-side, and a verdict per the success criteria.

## Visualisations

1. **Event-count waterfall** for USTEC: sweep -> displacement -> Candidate A breaker -> risk-feasible, with the 50-event floor marked on the risk-feasible step.
2. **Expectancy in R interval plot**: displacement-only baseline versus Candidate A breaker on train and test, with the EXP-023 1-minute USTEC point and CI overlaid for direct comparison.
3. **R-multiple distribution** by event class (baseline vs breaker), test segment, as paired violin or box plots.
4. **Drawdown-proxy interval plot** (mean MAE in R): baseline vs breaker on train and test with bootstrap CIs.

## Interpretation Guide

- **Support**: Test-segment expectancy difference CI excludes zero in the same direction as EXP-023, point estimate is within `+/- 50` percent of the EXP-023 1-minute USTEC point estimate or stronger, and risk-feasible counts meet the 50-event floor on train and test. The reflection treats this as "USTEC breaker positive survives" and authorizes Branch A to proceed at 15-minute per the design.md decision matrix.
- **Against**: Test-segment CI includes zero, OR point estimate reverses sign, with adequate counts. The reflection treats this as a 1-minute resolution artifact and tells Branch A to close or reframe per the design.md decision matrix.
- **Inconclusive**: Risk-feasible breaker counts fall below 50 on train or test, or the 15-minute / 1-minute retention ratio falls below 30 percent. The reflection records the resolution cost and does not interpret direction; per the design.md, inadequate 15-minute counts close the affected structural branch or explicitly reframe it as a 1-minute microstructure proxy, but do not automatically justify returning to a 1-minute structural claim.

## Complexity Check

- Statistical tests: 3 (primary expectancy bootstrap; secondary average-R / drawdown-proxy / log-return bootstrap family; retention diagnostic) / 3
- Visualisations: 4 / 4
- New modules: 0-1 (`python/src/bar_aggregator.py`, reused from EXP-029 or EXP-030 if already created; optional 15-minute breaker helper only if existing 1-minute helper cannot accept the 15-minute frame cleanly) / 1

## Data-View Comparison Considerations

### Cross-View Alignment
- Detection uses 15-minute `CloseTime`; outcome walks use 1-minute `CloseTime` strictly after the confirming 15-minute candle close.
- The breaker subset is paired to its parent displacement event by event identity, not by bar index.
- Coverage diagnostics report dropped partial 15-minute windows.

### Real-Price Outcome Discipline
- Expectancy in R, drawdown proxy, MAE, MFE, and 60-minute log return are all computed on real 1-minute OHLC.
- The inherited EXP-015 stop is a real-price stop; the buffer is computed in real-price units.
- The 15-minute view supplies only detection and never outcome prices.

### Event Density Differences
- 15-minute event counts are expected to be lower than 1-minute event counts; the count floor and retention ratio are checked before any expectancy difference is interpreted.
- A null result with collapsed counts is classified inconclusive, not refuting, per the design.md's resolution-cost rule.

### Regime Stratification
- This experiment does not stratify by direction, session, volatility regime, or level family. Those segmentation tests are EXP-032's job in Branch A under Phase 004B. EXP-031 is a feasibility check on resolution stability only.
