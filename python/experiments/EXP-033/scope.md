# Experiment: EXP-033 - 15-Minute IFVG Rule Family Readiness Survey

## Hypothesis

At least one rule family from the predeclared menu of five candidate IFVG/FVG modifications, applied independently to the EXP-020/EXP-029 three-candle FVG and close-through IFVG detector on synthetic 15-minute bars, is deterministic, count-eligible, materially less tautological than the EXP-020/EXP-029 84-85 percent inversion baseline, meaningfully selective relative to the unfiltered 15-minute FVG/IFVG population, and bounded in confirmation delay, on at least two of the four scoped instruments in both train and test segments.

## Question

Does any single predeclared IFVG/FVG rule-family modification produce a deterministic, count-eligible, non-tautological, and meaningfully selective IFVG definition on at least two instruments at 15-minute resolution, qualifying that rule for downstream entry-quality testing in EXP-034? If multiple rules qualify, which has the lowest inversion rate (with absolute event count as the tie-breaker)?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/` aggregated into synthetic 15-minute OHLC bars for FVG, IFVG, displacement, sweep, and zone-location detection. No real 1-minute outcome paths are used in this experiment. No Line Break, Renko, Heiken Ashi, or other chart-type inputs.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC. All four instruments are scoped because Branch B requires a `>=2` instrument qualification rule before EXP-034 may be created and design.md §"Phase 004B" does not narrow Branch B to USTEC.
- **Time range**: Full available dataset per instrument with the nested chronological split applied to the 1-minute series before aggregation. First 70 percent of the 1-minute series is the analysis set, split chronologically 70/30 into train/test after 15-minute aggregation. Final 30 percent is the global holdout and is never loaded, inspected, aggregated, or used.
- **Global holdout**: The final 30 percent of each chronologically ordered instrument 1-minute dataset is excluded before any aggregation, level derivation, sweep detection, or rule evaluation. The full 1-minute dataset must not be aggregated and re-split.
- **Look-ahead bias prevention**: 15-minute aggregation uses only completed clock-aligned 1-minute windows; partial trailing windows are dropped. ATR, body-median, and prior-bar statistics use only completed bars at or before each event timestamp. IFVG inversion search uses only bars after FVG formation; mitigation, displacement, sweep, and zone-location qualifications use only bars at or before the qualifying event timestamp.
- **Real-price outcome discipline**: This experiment evaluates rule readiness only. No Return_R, MAE_R, MFE_R, hit rate, log return, or any entry-quality outcome metric is computed. Real-price outcome rules are inherited from the phase design but are not exercised in EXP-033 because outcome testing is explicitly blocked by the design.md §"Phase Gates" selectivity-before-outcome gate. If implementation requires a price-derived diagnostic (e.g., gap midpoint, ATR, body size), it uses the synthetic 15-minute OHLC for detection only; no claim about tradeability is made.
- **Baseline definition (inherited unchanged)**: The unfiltered 15-minute FVG/IFVG detector matches EXP-029. Bearish FVG: `High[i] < Low[i-2]` on three consecutive 15-minute bars. Bullish FVG: `Low[i] > High[i-2]`. Minimum FVG size: `max(price_precision_step, 0.02 * ATR_14_15m)`. IFVG: the first later bar whose close passes through the opposite side of the FVG. Lifecycle: 120 15-minute bars. This baseline supplies the FVG count and inversion rate against which each candidate rule's selectivity is evaluated.

### Candidate Rule Families (predeclared, fixed before implementation)

The five rule families from design.md §"Candidate Rule Families" are instantiated below. Each rule is applied independently to the baseline detector. Parameters are fixed before implementation and must not be tuned against any result, count, inversion rate, delay, or overlap statistic computed during this experiment.

1. **R1 — Stricter minimum FVG size relative to prior ATR.** Minimum FVG size raised from the baseline `0.02 * ATR_14_15m` to `0.10 * ATR_14_15m` (a 5x stricter floor). The three-candle definition, lifecycle, and IFVG inversion logic are unchanged.
2. **R2 — Shorter lifecycle window before inversion.** Lifecycle reduced from the baseline 120 15-minute bars to 24 15-minute bars (6 elapsed hours). 24 bars is predeclared between the EXP-029 8-bar sensitivity (45-48 percent inversion, judged too near the symmetric midpoint per reflection §8) and the 120-bar baseline (84-86 percent inversion, judged too permissive). FVG definition, minimum size, and IFVG inversion logic are unchanged.
3. **R3 — Displacement-qualified FVG creation.** The third (right) candle of the three-candle FVG pattern must independently satisfy the EXP-018 displacement rule at 15-minute resolution: `BodySize >= 1.5 * BodyMedianPrior` over the prior 100 completed 15-minute bars; bearish-FVG candle close-location in candle range `<= 0.25`; bullish-FVG candle close-location `>= 0.75`. FVG minimum size, lifecycle (120 bars), and IFVG inversion logic are unchanged.
4. **R4 — Mitigation-before-inversion requirement.** The IFVG is valid only if at least one bar between FVG formation and the candidate inversion bar entered or touched the FVG zone (mitigation), and the inversion close-through occurred strictly after that mitigation. Mitigation predeclared as: for a bearish FVG (gap between `High[i]` and `Low[i-2]`), at least one later bar with `High >= High[i]`; for a bullish FVG (gap between `High[i-2]` and `Low[i]`), at least one later bar with `Low <= Low[i]`. FVG definition, minimum size, and lifecycle (120 bars) are unchanged.
5. **R5 — Zone-location filter relative to a swept level.** A FVG counts only if (a) a prior first-touch sweep of a PDH, PDL, ONH, or ONL level under the EXP-015 definition adapted to 15-minute bars occurred within the prior 24 15-minute bars (6 elapsed hours), and (b) the FVG midpoint lies within `1.0 * ATR_14_15m` of the swept level price. Sweep direction does not constrain FVG direction in this readiness scope. EXP-014 reproducible level catalogue supplies PDH/PDL/ONH/ONL. FVG minimum size, lifecycle (120 bars), and IFVG inversion logic are unchanged.

For each rule, a FVG is "rule-eligible" only if it satisfies the modified condition; an IFVG counts toward inversion rate only when its parent FVG is rule-eligible. The baseline detector is evaluated independently for selectivity comparison and overlap measurement.

### Exclusions

- No entry-quality, return, MAE, MFE, hit-rate, log-return, or any P&L-related metric. Outcomes are explicitly blocked by the design.md selectivity-before-outcome gate.
- No Branch A USTEC breaker analysis; Branch A was closed at reflection §10.3.
- No combination of rule families. Each rule is evaluated independently. Combinations are out of scope until a single rule passes readiness.
- No tuning of the five predeclared parameters (`0.10 * ATR`, 24-bar lifecycle, EXP-018 displacement constants, mitigation form, 24-bar zone-location window, `1.0 * ATR` zone radius) based on EXP-033 results.
- No additional rule families beyond the five enumerated in design.md §"Candidate Rule Families".
- No 1-minute, 1-hour, or any non-15-minute timeframe analysis.
- No chart-type generators (Line Break, Renko, Heiken Ashi).
- No tick, bid/ask, spread, commission, or slippage stress.
- No predictive model, no segmentation, no regime stratification.

## Success / Failure Criteria

A rule family passes the readiness gate on a given instrument-segment combination only if all six readiness checks below are satisfied. The aggregate experiment verdict is determined by the per-rule, per-instrument pattern.

### Per-Rule, Per-Instrument-Segment Readiness Checks

1. **Reproducibility**: SHA-256 digest of the rule-eligible FVG and IFVG event tables matches between (a) a fresh load of the 1-minute base data followed by aggregation, levels, sweeps, and rule application, and (b) the same pipeline with the 1-minute input shuffled then re-sorted by `CloseTime` before aggregation. Both train and test segment digests must match independently.
2. **Count floor**: `>= 100` rule-eligible FVGs in each of train and test segments, and `>= 50` rule-eligible IFVG inversions in each of train and test segments. Matches the EXP-020 and EXP-029 floors so failure here cannot be a moved goalpost.
3. **Inversion rate band**: the rule-eligible IFVG count divided by the rule-eligible FVG count must fall inside the predeclared band `[0.55, 0.75]` in both train and test segments. The upper bound `0.75` operationalises design.md §"Readiness Pattern" "materially below the Phase 003 84-85 percent level". The lower bound `0.55` operationalises reflection §8 "must define a meaningful inversion floor above zero, not just a maximum" by keeping the rule meaningfully above the 50 percent symmetric midpoint observed at the EXP-029 8-bar sensitivity.
4. **Selectivity**: the rule-eligible FVG count is `<= 0.80` of the unfiltered baseline 15-minute FVG count in the same segment. This operationalises design.md §"Readiness Pattern" "filters a meaningful share of upstream events rather than retaining nearly everything" by requiring at least a 20 percent reduction from the unfiltered baseline.
5. **Bounded median confirmation delay**: median number of 15-minute bars between FVG formation `CloseTime` and IFVG inversion `CloseTime` is `<= 24` bars (6 elapsed hours) in both train and test segments. R2 inherits this naturally because its lifecycle is 24 bars; R1, R3, R4, R5 must satisfy it as a free check.
6. **Well-defined denominators**: zero `NaN`, zero infinite, and non-zero rule-eligible FVG counts in both segments. No division by zero in the inversion rate. This operationalises design.md §"Readiness Pattern" "defines risk denominators without zero-baseline or infeasible-risk collapse" for the readiness-only context.

### Aggregate Verdict (Predeclared)

- **Evidence FOR a rule family**: the rule passes all six readiness checks on at least two of the four scoped instruments, with both train and test segments satisfied on each qualifying instrument independently.
- **Aggregate experiment passes (Branch B may proceed to new EXP-034)**: at least one rule family is "Evidence FOR" per the per-rule criterion above. If exactly one rule family passes, that rule advances. If two or more pass, the rule with the lowest combined train+test inversion rate across its qualifying instruments advances; ties are broken by absolute rule-eligible IFVG event count summed across qualifying instruments. Return, excursion, hit-rate, and any P&L-derived statistic must not influence selection or tie-breaking under any circumstance.
- **Aggregate experiment fails (Branch B closes at EXP-033 with selectivity-gated no-go)**: no rule family is "Evidence FOR". Branch B records the selectivity-gated no-go per reflection §3 Branch B and the design.md §"Stop Conditions" "no rule is both selective and count-eligible".
- **Inconclusive**: only one instrument qualifies for an otherwise promising rule, baseline 15-minute FVG counts collapse below the EXP-029-confirmed floors before any rule is applied, EXP-014 level reproducibility cannot be re-derived for the analysis-set date range, or the EXP-018 displacement constants at 15-minute cannot be re-derived from analysis-set bars. Inconclusive does not authorize relaxing the readiness checks; it triggers a documented gap and an explicit close-or-rescope decision before any further Branch B scope.

The mathematical attainability of each gate has been verified against EXP-029 baseline counts (3,391-9,283 FVGs and 2,783-7,321 IFVGs per instrument-segment): the 20 percent selectivity filter still leaves `>= 2,712` baseline-equivalent FVGs even on the smallest segment, well above the 100-FVG floor, so the gates are simultaneously satisfiable in principle for each rule.

## Prerequisites and Sequencing

Requires:

- EXP-014 reproducible PDH/PDL/ONH/ONL level catalogue for the analysis-set date range (R5).
- EXP-015 first-touch sweep framework adapted to 15-minute bars (R5).
- EXP-018 displacement definition (`BodySize >= 1.5 * BodyMedianPrior`, close-location thresholds) re-applied to 15-minute bars (R3).
- EXP-020 three-candle FVG and close-through IFVG detector (baseline and R1-R5).
- EXP-029 confirmation that the unfiltered 15-minute baseline produces 3,391-9,283 FVGs per segment (justifies count-floor attainability).

This experiment is the first Branch B Phase 004B experiment after the reflection §10 amendment. No new EXP-034 (entry-quality) scope may be created until EXP-033 completes, passes audit and post-experiment governance, and at least one rule family is selected per the aggregate verdict above.

## Complexity Budget

- Max statistical test families: 1 — block bootstrap on the inversion rate (one per rule × instrument × segment), counted as a single statistical test family because every invocation uses the same method, the same block-size convention from EXP-029 (block = 50, seed = 42, n = 2,000 resamples), and the same descriptive (non-decision) role. Reproducibility digest matching is deterministic and is not counted as a statistical test.
- Max primary visualisations: 4.
- Max new reusable modules: 0. Existing `python/src/bar_aggregator.py` covers 15-minute aggregation. Existing `python/src/ict_timebar.py` covers ATR, level, and bar-diagnostic helpers. FVG/IFVG, displacement, and sweep helpers must be reused from EXP-014, EXP-015, EXP-018, EXP-020, and EXP-029 code paths; if implementation determines that a helper must be extracted into `python/src/` to keep `code/run_experiment.py` orchestrated rather than re-implementing detection, that extraction is a code-organisation move and must be routed back through governance before any new analytical module is added.

## Data Requirements

For each instrument:

1. Load the latest available 1-minute time-bar Parquet via the standard loading pattern. Sort by `CloseTime`. Slice the first 70 percent chronologically as the 1-minute analysis-set slice.
2. Aggregate that 1-minute slice into synthetic 15-minute OHLC via `python.src.bar_aggregator.aggregate_ohlc(period_minutes=15)`. Partial trailing windows are dropped.
3. Apply the nested chronological train/test split (first 70 percent train, last 30 percent test) to the 15-minute aggregated series. Verify the train cutoff against `python.src.ict_timebar.train_cutoff_time` if it is reused; otherwise reimplement the same nested split inline. The train cutoff timestamp must be derived from the 15-minute aggregated series, not the 1-minute series.
4. Derive prior-bar `ATR_14_15m` and `BodyMedianPrior` (100-bar) at 15-minute resolution from the aggregated series, using only completed prior bars. Derive `price_precision_step` per the EXP-015 convention for each instrument.
5. Re-derive the EXP-014 PDH, PDL, ONH, and ONL catalogue for the analysis-set date range (R5 only). Re-derive first-touch sweep events at 15-minute resolution per EXP-015 logic adapted to 15-minute bars (R5 only).
6. Detect baseline FVGs and IFVGs (EXP-020 / EXP-029 detector) on the 15-minute analysis-set series to produce the unfiltered FVG and IFVG counts per segment.
7. For each of R1-R5, apply the rule modification independently to the same 15-minute bars and derive rule-eligible FVG and IFVG event tables per segment.
8. Compute the six readiness checks per rule per instrument-segment.
9. Apply the aggregate verdict logic to select at most one rule family or declare Branch B closed.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD", "USTEC"]

for instrument in INSTRUMENTS:
    path = sorted(DATA_DIR.glob(f"timebars/timebars_*{instrument}*.parquet"))[-1]
    scan = pl.scan_parquet(path).sort("CloseTime")
    analysis_rows = int(scan.select(pl.len()).collect().item() * 0.70)
    bars_1m_analysis = scan.slice(0, analysis_rows).collect()
    # Holdout-exclusion is now complete; never re-scan the full file without the slice.
```

## Suggested Direction

Report the FVG-count waterfall (unfiltered baseline vs each rule) and the per-rule, per-instrument readiness-check matrix before any inversion-rate plot or selection decision. The aggregate verdict should be mechanical: if no rule passes the per-rule criterion on `>= 2` instruments, Branch B closes at EXP-033 and the selectivity-gated no-go is recorded; if exactly one rule passes, it advances unconditionally; if multiple rules pass, the lowest combined train+test inversion rate among qualifying instruments selects, with absolute event count breaking ties. Reproducibility digests and count floors are presented first to make any later anomaly traceable to a specific rule and instrument.
