# Analysis Plan: Experiment EXP-033

## Objective

Determine whether any of the five predeclared IFVG/FVG rule families (R1 stricter size, R2 shorter lifecycle, R3 displacement-qualified FVG creation, R4 mitigation-before-inversion, R5 zone-location filter) applied independently to synthetic 15-minute bars produces a deterministic, count-eligible, non-tautological, meaningfully selective IFVG definition with bounded confirmation delay on at least two of the four scoped instruments, and if so, mechanically select the single rule with the lowest inversion rate (ties broken by absolute event count). No return, excursion, hit-rate, or P&L metric is computed; selection must not be influenced by such metrics under any condition. The verdict either authorizes the new EXP-034 entry-quality scope or closes Branch B at a selectivity-gated no-go per the design and reflection.

## Methodology

The plan computes, for every `(rule, instrument, segment)` cell, the six readiness checks from `scope.md` §"Per-Rule, Per-Instrument-Segment Readiness Checks". Baseline (unfiltered) FVG and IFVG counts are computed once per `(instrument, segment)` to anchor the selectivity check. The aggregate verdict is applied mechanically once all readiness statistics are tabulated.

### Step 1: Holdout-excluded data load and 15-minute aggregation (per instrument)

- **Method**: Lazy Polars scan of `data/timebars/timebars_*<instrument>*.parquet`, sort by `CloseTime`, chronological slice of the first 70 percent of 1-minute bars, then deterministic clock-aligned aggregation via `python/src/bar_aggregator.aggregate_ohlc(period_minutes=15)`. Partial trailing 15-minute windows are dropped inside the aggregator.
- **Why this method**: Holdout exclusion must be applied on the 1-minute series before aggregation per `_pipeline-config.md` §"OOS Holdout Rules" and `scope.md` §"Global holdout". `bar_aggregator.aggregate_ohlc` is the audited, deterministic helper introduced in EXP-029.
- **Simpler alternative considered**: A full-dataset aggregation followed by a 70/30 split on the 15-minute series. Rejected because it would temporarily materialize the holdout, violating the holdout discipline that no code path may inspect the final 30 percent.
- **Assumptions**:
  - **Temporal structure**: 1-minute `CloseTime` is monotonically increasing within file; `bar_aggregator` enforces this with an internal sort.
  - **Cross-view alignment**: All downstream analyses align by 15-minute `CloseTime` derived inside the aggregator; no bar-index alignment occurs.
  - **Real-price outcomes**: No outcome paths in this experiment, so real-price discipline reduces to a no-op; if any diagnostic uses prices (e.g., gap midpoint), the 15-minute synthetic OHLC is used for detection only.
- **Expected output**: Per instrument, one `bars_15m_analysis` DataFrame (Polars or pandas) containing only the 15-minute bars derived from the 1-minute analysis-set slice.

### Step 2: Nested chronological train/test split (per instrument)

- **Method**: Apply a 70/30 chronological split on `bars_15m_analysis` ordered by `CloseTime`. Record the train cutoff timestamp per instrument and propagate it to all downstream tables (FVG events, IFVG events, sweep events, level catalogues) by `CloseTime <= train_cutoff` for train, `CloseTime > train_cutoff` for test.
- **Why this method**: Matches the nested-split convention used in EXP-029 and EXP-031 so this experiment's segment definitions are directly comparable to those baseline counts. Event-time assignment to segments by the event's own `CloseTime` is the conventional choice and avoids ambiguous interior events.
- **Simpler alternative considered**: A bar-index split on the 15-minute series. Equivalent in result but less robust if any future change makes the series sparse; timestamp-based assignment is the authoritative form.
- **Assumptions**: Same temporal-structure and alignment assumptions as Step 1.
- **Expected output**: Per instrument, `train_cutoff_time_15m`, `bars_15m_train`, `bars_15m_test`.

### Step 3: Baseline (unfiltered) FVG and IFVG detection

- **Method**: Apply the EXP-020 three-candle FVG detector and the close-through IFVG inversion rule unchanged to `bars_15m_train` and `bars_15m_test` per instrument. FVG minimum size: `max(price_precision_step, 0.02 * ATR_14_15m)` per the inherited convention. IFVG lifecycle: 120 15-minute bars. ATR_14 is computed from 15-minute completed prior bars, identical to the EXP-029 baseline.
- **Why this method**: Required as the anchor for the selectivity check (`scope.md` Readiness Check 4): each rule's eligible FVG count must be `<= 0.80 *` the baseline FVG count in the same segment. Without this anchor, selectivity cannot be evaluated.
- **Simpler alternative considered**: Reuse EXP-029's published baseline counts as a fixed constant. Rejected because reuse without re-derivation would weaken the experiment's self-contained reproducibility audit; recomputing inside this run also ensures any change in dependency versions surfaces immediately.
- **Assumptions**:
  - **Look-ahead bias prevention**: FVG formation uses only the three-candle pattern at and before the formation `CloseTime`. IFVG inversion search uses only bars strictly after FVG formation.
  - **Determinism**: The detector is a pure function of the input bars; the same input must produce the same FVG and IFVG tables.
- **Expected output**: Per instrument-segment, `baseline_fvgs_<seg>` (FVG event table with `FormationCloseTime`, `Direction`, `Top`, `Bottom`, `Size`) and `baseline_ifvgs_<seg>` (IFVG inversion event table with parent-FVG link and `InversionCloseTime`).

### Step 4: Rule R1-R5 application (independent, per rule)

- **Method**: For each candidate rule, apply the scope-predeclared modification independently to the baseline detector and produce the rule-eligible FVG and IFVG tables per instrument-segment. The five rules are:
  - **R1 Stricter size**: minimum FVG size raised to `max(price_precision_step, 0.10 * ATR_14_15m)`; lifecycle 120 bars; three-candle definition unchanged; close-through IFVG unchanged.
  - **R2 Shorter lifecycle**: minimum size unchanged at `0.02 * ATR_14_15m`; lifecycle reduced to 24 15-minute bars; close-through IFVG unchanged.
  - **R3 Displacement-qualified FVG creation**: the third (right) candle of the three-candle pattern must satisfy `BodySize >= 1.5 * BodyMedianPrior` (100-bar window of completed prior 15-minute bars), close-location `<= 0.25` for bearish FVGs, `>= 0.75` for bullish FVGs (EXP-018 definition adapted to 15-minute bars); minimum size and lifecycle unchanged.
  - **R4 Mitigation-before-inversion**: a candidate IFVG inversion is valid only if at least one bar between FVG formation and the inversion bar entered or touched the gap. For a bearish FVG (gap between `High[i]` and `Low[i-2]`), mitigation requires at least one later bar with `High >= High[i]`. For a bullish FVG (gap between `High[i-2]` and `Low[i]`), mitigation requires at least one later bar with `Low <= Low[i]`. Mitigation must occur strictly before the inversion bar. Other parameters unchanged.
  - **R5 Zone-location filter**: a baseline FVG is rule-eligible only if (a) a prior first-touch sweep of a PDH, PDL, ONH, or ONL level under the EXP-015 sweep definition adapted to 15-minute bars occurred within the prior 24 15-minute bars relative to the FVG formation `CloseTime`, and (b) the FVG midpoint `(Top + Bottom) / 2` lies within `1.0 * ATR_14_15m` of the swept level price. EXP-014 reproducible level catalogue supplies PDH/PDL/ONH/ONL. Sweep direction does not constrain FVG direction in this readiness scope. Other parameters unchanged.
- **Why this method**: Each rule is a single, predeclared, falsifiable modification. Independent application matches `scope.md` §"Exclusions" "No combination of rule families" and `reflection.md` §5 "Each candidate rule produces: reproducibility digest, FVG count, IFVG count, train/test inversion rate, train/test event floor flag, overlap with displacement-confirmed events, and median confirmation delay".
- **Simpler alternative considered**: Combining rules to reduce candidates. Rejected because design.md §"Candidate Rule Families" predeclares the menu of five; combinations would change the search space mid-experiment and are out of scope.
- **Assumptions**:
  - **Look-ahead bias prevention**: All ATR, body-median, sweep, and level inputs use only data at or before the qualifying event timestamp. R5 uses sweeps with `CloseTime <= FormationCloseTime - 1 bar` and EXP-014 levels valid on the FVG formation date.
  - **Determinism**: Each rule modification is a pure function of the input bars, levels, and rule constants; the same input must produce the same rule-eligible tables.
  - **R3 BodyMedianPrior denominator**: 100 completed prior 15-minute bars match the elapsed-time equivalent of EXP-018's 100-bar 1-minute window scaled to 15-minute resolution where the same number of bars is the conservative inherited choice.
- **Expected output**: Per rule per instrument-segment, `rule_<R>_fvgs_<seg>` and `rule_<R>_ifvgs_<seg>` event tables.

### Step 5: Per-rule per-instrument-segment readiness statistics

- **Method**: For each `(rule, instrument, segment)` cell, compute the seven descriptive statistics from `reflection.md` §5 (the six readiness inputs plus the overlap-with-displacement descriptor):
  1. `rule_eligible_fvg_count`
  2. `rule_eligible_ifvg_count`
  3. `inversion_rate = ifvg_count / fvg_count` (set to `NaN` if `fvg_count == 0` and recorded as a denominator failure)
  4. `selectivity_ratio = rule_eligible_fvg_count / baseline_fvg_count_same_segment`
  5. `median_confirmation_delay_bars` over rule-eligible IFVG events, computed as 15-minute bars between FVG formation `CloseTime` and IFVG inversion `CloseTime`
  6. `denominator_valid` boolean: `True` iff `fvg_count > 0` and `inversion_rate` is finite
  7. `overlap_with_displacement_share` = share of rule-eligible FVGs whose `FormationCloseTime` matches a R3-eligible FVG in the same segment (descriptive only — R3's value is 1.0 by construction; not a binding gate)
- **Why this method**: Tabular descriptive statistics are the simplest sufficient summary; no parametric assumption is required. The aggregate verdict is mechanical once these tables are in hand.
- **Simpler alternative considered**: Skipping the overlap descriptor. Rejected because `reflection.md` §5 explicitly lists it as a required per-rule output for the Branch B record, even though it does not gate selection.
- **Assumptions**:
  - **Event-level independence is not required**: median, count, and ratio statistics do not assume i.i.d. observations.
  - **NaN handling**: explicit. A `NaN` inversion rate or median delay is recorded as a denominator-validity failure (readiness check 6), never silently propagated.
- **Expected output**: A 40-row readiness table (5 rules × 4 instruments × 2 segments) with the seven columns above plus a per-cell `readiness_check_<1..6>` boolean and `passes_all_six_checks` boolean. A reduced per-rule-per-instrument table marks `passes_on_instrument_both_segments`.

### Step 6: Reproducibility digest (readiness check 1, deterministic)

- **Method**: For each `(rule, instrument, segment)` cell, recompute the rule-eligible FVG and IFVG tables twice with the same code path: (a) fresh `pl.scan_parquet` load and standard chronological sort, and (b) `pl.scan_parquet` load, deterministic permutation by row index using `numpy.random.default_rng(seed=42).permutation`, then `sort("CloseTime")` to re-establish the canonical ordering before aggregation. Compute the SHA-256 digest of the serialized rule-eligible FVG table and of the rule-eligible IFVG table for each path. The check passes when the digests are byte-identical across both load paths and both digests (FVG, IFVG) match.
- **Why this method**: SHA-256 over a deterministic serialization is the canonical reproducibility check used in EXP-020 and EXP-029. Shuffling and resorting probes whether any code path depends on input row order beyond what the canonical sort enforces.
- **Simpler alternative considered**: Comparing FVG counts only. Rejected because two distinct event sets can have the same count; full-table digest catches mis-ordered or substituted rows.
- **Assumptions**: The serialization is canonical (column order fixed, numeric formatting deterministic). The implementation should serialize to Parquet with fixed column ordering and compute the digest on the file bytes, or equivalently to a deterministic CSV via Polars `write_csv` with explicit column order. NaN handling must be explicit and consistent across paths.
- **Expected output**: A 40-row reproducibility table with columns `fvg_digest_canonical`, `fvg_digest_shuffled`, `ifvg_digest_canonical`, `ifvg_digest_shuffled`, and `digests_match` boolean.

### Step 7: Block bootstrap on inversion rate (single statistical test family)

- **Method**: For each `(rule, instrument, segment)` cell with `denominator_valid == True`, draw `n = 2000` block-bootstrap resamples of the rule-eligible FVG event sequence ordered by `FormationCloseTime`. Block size = 50 events; sampling with replacement of contiguous blocks until the resample matches the original FVG count. For each resample, compute the resampled inversion rate as (resampled rule-eligible IFVG count) / (resampled FVG count) where IFVG status is carried along with the FVG row. Report mean, 2.5th, and 97.5th percentiles per cell. Use `numpy.random.default_rng(seed=42)` for the bootstrap RNG.
- **Why this method**: Block bootstrap preserves local temporal dependence in event sequences without assuming stationarity or i.i.d. structure — the methods catalog "Bootstrap / Resampling Methods" entry and `_pipeline-config.md` §"Programme Principles" "Non-parametric by default" both authorise this choice. EXP-029 used the same block size and seed for its inversion-rate bootstrap; reusing the convention keeps the readiness CIs directly comparable to the EXP-029 baseline.
- **Simpler alternative considered**: Wilson or Agresti-Coull binomial CIs treating each FVG as an i.i.d. Bernoulli trial. Rejected because the inversion outcomes for adjacent FVGs are temporally dependent (overlapping bar contexts, regime persistence), violating the i.i.d. assumption.
- **Assumptions**:
  - **Local exchangeability within blocks**: 50-event blocks are short enough to preserve clustering but long enough that block boundaries do not dominate the resample variance.
  - **Stationarity is not assumed**: bootstrap is descriptive of analysis-set sampling variability under the resampling scheme, not of an inferred population.
  - **CI role**: the 95 percent bootstrap CI is reported as uncertainty quantification on the inversion rate point estimate; the readiness verdict (check 3) uses the point estimate per `scope.md`. CIs that straddle a band boundary are flagged in results as descriptive context only.
- **Expected output**: A 40-row table with `inversion_rate_mean_boot`, `inversion_rate_ci_lower`, `inversion_rate_ci_upper`, `n_resamples`, `block_size`, `seed`, and `ci_within_band` (boolean — descriptive only).

### Step 8: Aggregate verdict (mechanical selection)

- **Method**: Apply the verdict logic from `scope.md` §"Aggregate Verdict (Predeclared)" in this exact order:
  1. For each rule, count the instruments where `passes_all_six_checks_train == True AND passes_all_six_checks_test == True`. Call this `qualifying_instrument_count_<rule>`.
  2. Rules with `qualifying_instrument_count >= 2` are "rules in contention".
  3. If `len(rules_in_contention) == 0`: verdict is "Branch B closes at EXP-033 with selectivity-gated no-go".
  4. If `len(rules_in_contention) == 1`: that rule advances; verdict is "rule `<R>` selected, new EXP-034 may be scoped".
  5. If `len(rules_in_contention) >= 2`: compute `combined_inversion_rate = mean(inversion_rate across qualifying instruments and both train and test segments)` for each rule in contention. Select the rule with the lowest `combined_inversion_rate`. If two or more rules tie on `combined_inversion_rate` to within `1e-6`, select the rule with the largest `combined_rule_eligible_ifvg_count = sum over qualifying instruments of (train + test rule-eligible IFVG count)`. If a tie persists at the count level, declare an explicit tie-break failure in `results.md` and route the decision back to checkpoint reflection before any new EXP-034 scope; this last-resort branch is not expected with the predeclared parameter set but is recorded for completeness.
- **Why this method**: The verdict is mechanical and pre-registered. Selection by lowest inversion rate is required by `reflection.md` §3 Branch B and §5 EXP-036. The tie-break by absolute event count is also required there. Return, excursion, hit-rate, or any P&L-derived statistic is excluded from the selection by both `scope.md` and the reflection.
- **Simpler alternative considered**: Selecting by highest selectivity ratio (lowest retention). Rejected because the design and reflection predeclare lowest inversion rate as the primary criterion; deviating would constitute moving goalposts.
- **Assumptions**: None beyond determinism of the readiness tables.
- **Expected output**: A `verdict.json` (or equivalent) capturing `rules_in_contention`, the per-rule `combined_inversion_rate` and `combined_rule_eligible_ifvg_count`, the `selected_rule` (or `None`), and the `verdict_text` (one of three predeclared strings).

## Visualisations

1. **FVG-count waterfall by rule and instrument** (1 figure with 4 subplots, one per instrument). For each instrument, six bars: baseline FVG count, then R1, R2, R3, R4, R5 rule-eligible FVG count. Train and test segments stacked or side-by-side. The 100-FVG count floor and the `0.80 * baseline` selectivity ceiling are drawn as horizontal reference lines per subplot. Purpose: shows simultaneously the absolute count floor (readiness check 2) and the selectivity ceiling (readiness check 4), with the baseline anchor visible.
2. **Inversion-rate readiness matrix** (1 figure, heatmap-style). Rows: 5 rules. Columns: 4 instruments × 2 segments = 8 columns. Cell value: point-estimate inversion rate. Bootstrap CI endpoints shown numerically inside each cell. Horizontal band overlay shading the `[0.55, 0.75]` predeclared band for visual readiness check 3. Purpose: shows the band-pass status simultaneously for all 40 cells.
3. **Median confirmation delay matrix** (1 figure, heatmap-style). Same row/column layout as plot 2. Cell value: median bars from FVG formation to IFVG inversion. Reference line at the 24-bar bound for readiness check 5. Purpose: shows the delay-bound status for all 40 cells; R2's natural conformance is visible.
4. **Readiness-gate pass/fail grid** (1 figure, 6-panel grid). One small panel per readiness check (checks 1-6). Each panel: 5 rules × 4 instruments × 2 segments = 40 cells colored pass/fail. Purpose: makes the aggregate verdict mechanically auditable from a single figure — a reader can trace any "fails on instrument X" claim back to the specific gate.

No additional plots. Overlap-with-displacement share is reported in the readiness table; it does not drive selection and would consume a fifth plot slot.

## Interpretation Guide

- **If at least one rule has `qualifying_instrument_count >= 2` and the selection logic identifies a unique rule**, it means that rule passes all six readiness checks on at least two instruments in both train and test segments, has the lowest combined inversion rate among contention rules (with absolute event count breaking ties if needed), and is the only rule eligible to carry into a new EXP-034 entry-quality scope. Branch B advances. Record the selected rule, its qualifying instruments, and per-cell readiness statistics in `results.md`.
- **If no rule has `qualifying_instrument_count >= 2`**, it means none of the five predeclared candidates is simultaneously deterministic, count-eligible, in the inversion-rate band, selective, delay-bounded, and denominator-valid on two or more instruments. Branch B closes at EXP-033 with a selectivity-gated no-go per `reflection.md` §3 Branch B and `design.md` §"Stop Conditions" — no rule is both selective and count-eligible. The result is REFUTED for the experiment's hypothesis, and the checkpoint records a clean Branch B no-go.
- **If exactly one rule qualifies on a single instrument but not a second**, the result is INCONCLUSIVE for that rule; the single-instrument pass is recorded but does not authorize EXP-034 per `reflection.md` §3 Branch B and §5 EXP-036. If no other rule qualifies on `>= 2` instruments, the aggregate verdict is the selectivity-gated no-go above.
- **If baseline 15-minute FVG counts collapse below the 100-FVG floor in any segment** before any rule is applied, the experiment is INCONCLUSIVE because the baseline anchor for selectivity (readiness check 4) cannot be established; document the gap and route back to checkpoint reflection before any further Branch B scope. This branch is not expected given EXP-029's 3,391-9,283 baseline FVG counts per segment but is enumerated to keep the interpretation guide exhaustive.
- **If EXP-014 level reproducibility cannot be re-derived for the analysis-set date range or EXP-018 displacement constants at 15-minute cannot be re-derived from analysis-set bars**, R5 or R3 (respectively) is INCONCLUSIVE for the affected instrument; the remaining rules' verdicts stand. If the affected rule was a unique selection candidate, the aggregate verdict reverts to the selectivity-gated no-go.
- **If the inversion-rate point estimate is inside `[0.55, 0.75]` but the bootstrap 95 percent CI extends outside the band**, the readiness verdict still uses the point estimate per `scope.md`; the CI extension is reported as descriptive context only and does not change the readiness check 3 outcome. This avoids moving the goalpost based on uncertainty quantification that was not predeclared as a gate.

## Complexity Check

- **Statistical tests**: 1 family planned / 1 budgeted — block bootstrap on inversion rate per `(rule, instrument, segment)` cell using the EXP-029 convention (block = 50, seed = 42, n = 2000). The reproducibility digest match is deterministic and is not a statistical test.
- **Visualisations**: 4 planned / 4 budgeted — FVG-count waterfall, inversion-rate matrix, median-delay matrix, and 6-panel readiness-gate grid.
- **New modules**: 0 planned / 0 budgeted — reuse `python/src/bar_aggregator.py` for aggregation, `python/src/ict_timebar.py` for ATR / level / bar-diagnostic helpers, and the FVG / IFVG / displacement / sweep helpers from EXP-014, EXP-015, EXP-018, EXP-020, and EXP-029 code paths. If implementation determines that an existing detection helper must move into `python/src/` to keep `code/run_experiment.py` purely orchestrated, that is a code-organisation extraction (no new analytical logic) and must be routed back through governance before any new module is added.

## Data-View Comparison Considerations

### Cross-View Alignment

- All comparisons across the five rules use the same 15-minute aggregated bars per instrument, derived from a single holdout-excluded 1-minute slice. There is no cross-timeframe or cross-chart-type alignment in this experiment.
- Train and test segments are assigned by the event's own `CloseTime` against the per-instrument `train_cutoff_time_15m`, never by bar index.

### Real-Price Outcome Discipline

- This experiment computes no strategy returns, signal returns, excursion metrics, hit rates, or P&L statistics. The synthetic 15-minute OHLC is used for detection only. If a downstream auditor or interpretation reader wants to validate the lack of outcome leakage, the readiness table has no return or excursion columns by construction; any such column appearing in code or output is a scope violation and must be flagged.

### Event Density Differences

- Rules R1, R3, and R5 are expected to reduce FVG counts relative to baseline. R2's count is approximately equal to baseline (lifecycle change does not affect FVG counts, only IFVG counts). R4 may slightly reduce IFVG counts while leaving FVG counts unchanged. The selectivity check (readiness check 4) explicitly tests count reduction relative to baseline; the count floor (readiness check 2) explicitly tests absolute event sufficiency. The two checks together prevent both "retained everything" and "filtered too aggressively" failure modes.

### Regime Stratification

- Out of scope. Regime stratification is not part of the predeclared rule menu and would constitute scope creep. Any regime-driven differences in inversion rate are absorbed into the per-segment statistics and the block bootstrap CIs.
