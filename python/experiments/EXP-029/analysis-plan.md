# Analysis Plan: Experiment EXP-029

## Objective

Determine whether the EXP-020 FVG/IFVG detector applied without modification to synthetic 15-minute bars produces an IFVG inversion rate materially below the Phase 003 1-minute 84-85 percent baseline on at least two instruments while preserving event counts adequate for downstream selectivity testing, and isolate timeframe effects from lifecycle-duration effects via a secondary 8-bar lifecycle sensitivity.

## Methodology

### Step 1: Holdout-Safe 15-Minute Aggregation

- **Method**: For each instrument, lazily scan the 1-minute Parquet, sort by `CloseTime`, slice the first 70 percent chronologically as the analysis set, and resample the analysis-set slice only into synthetic 15-minute OHLC via deterministic clock-aligned non-overlapping windows (first Open, max High, min Low, last Close, summed TickVolume). Partial trailing 15-minute windows that do not contain a full 15 1-minute bars are dropped.
- **Why this method**: Holdout exclusion is mandatory and must be applied before any aggregation, per `_pipeline-config.md` and the checkpoint's data-scope rules. Clock-aligned resampling is the simplest deterministic transformation; it preserves OHLC integrity and is reproducible from identical 1-minute input.
- **Simpler alternative considered**: Aggregating the full 1-minute dataset and then slicing 70/30 on the 15-minute series would be one line shorter but is a holdout-contamination risk and would not match the design.md rule "Apply holdout exclusion to the 1-minute series before aggregation; never aggregate the full dataset and re-split."
- **Assumptions**:
  - **Temporal structure**: 1-minute and 15-minute series are chronologically ordered by `CloseTime`.
  - **Cross-view alignment**: 15-minute events are aligned to real time only via the 15-minute bar `CloseTime`; no bar-index alignment.
  - **Real-price outcomes**: Not applicable in this experiment (detection-only). The 15-minute OHLC is a derived chart-construction view; if any downstream experiment uses 15-minute signals for outcomes, returns must come from real 1-minute prices, but this is out of scope here.
- **Expected output**: One in-memory 15-minute DataFrame per instrument with columns `OpenTime, CloseTime, Open, High, Low, Close, TickVolume`, plus a per-instrument coverage table (1-minute analysis-set bar count, completed 15-minute bar count, dropped-partial-window count).

### Step 2: FVG Detection on 15-Minute Bars

- **Method**: Apply the EXP-020 three-candle FVG detector unchanged: bearish FVG when `High[i] < Low[i-2]`; bullish FVG when `Low[i] > High[i-2]`. Apply the EXP-020 minimum-size filter `max(price_precision_step, 0.02 * ATR_14)` where `price_precision_step` follows the EXP-015 convention (smallest positive observed price increment in the analysis set for that instrument) and `ATR_14` is recomputed on 15-minute bars using only completed 15-minute bars available at the FVG formation timestamp.
- **Why this method**: The checkpoint specifies "the same three-candle FVG and 120-bar lifecycle IFVG rule from EXP-020, applied to 15-minute bars without modification." Recomputing `ATR_14` on the 15-minute series is required because ATR_14 on 1-minute bars would be a tiny intra-15-minute movement that does not size 15-minute gaps proportionally.
- **Simpler alternative considered**: Reusing the 1-minute `ATR_14` directly would be source-valid but would systematically under-filter on 15-minute bars and confound the timeframe comparison.
- **Assumptions**:
  - **Temporal structure**: Candle `i` `CloseTime` is the first 15-minute timestamp at which the FVG is knowable.
  - **Cross-view alignment**: No cross-view alignment is performed in this step.
  - **Real-price outcomes**: Not applicable in this step.
- **Expected output**: Per-instrument FVG table with side, upper bound, lower bound, size, formation `CloseTime`, segment label, and `ATR_14` at formation.

### Step 3: Lifecycle, IFVG Classification, and Lifecycle Sensitivity

- **Method**: For each FVG, walk forward up to the lifecycle limit and label lifecycle state as formed, partially filled, fully filled, inverted, or expired. IFVG requires a later 15-minute close through the opposite side of the FVG after formation. Compute the lifecycle pass twice: once with the primary 120 15-minute bar window (direct EXP-020 transfer) and once with the secondary 8 15-minute bar window (approximating the original 120-minute elapsed-time window). Each pass produces an independent IFVG identity set per FVG.
- **Why this method**: Running both lifecycle windows on the same FVG set is the only way to separate timeframe effects from lifecycle-duration effects, which the checkpoint explicitly calls out as a required sensitivity.
- **Simpler alternative considered**: Running only the 120-bar primary window would conflate timeframe and lifecycle, defeating the reflection's calibration purpose.
- **Assumptions**:
  - **Temporal structure**: Lifecycle is walked forward in `CloseTime` order; first-inversion timestamp is the unique IFVG event timestamp.
  - **Cross-view alignment**: No cross-view alignment in this step.
  - **Real-price outcomes**: Not applicable; IFVG inversion is a price-touch event, not a return.
- **Expected output**: Per-instrument lifecycle table and IFVG identity table for each of the two lifecycle windows, with formation and inversion timestamps and lifecycle terminal state.

### Step 4: Reproducibility, Inversion Rate, Counts, and Selectivity Verdict

- **Method (reproducibility)**: For each instrument, run two invariance checks on the 15-minute pipeline and compare SHA-256 digests of the FVG identity columns. (a) Fresh disk reload of the 1-minute Parquet, re-aggregate, redetect. (b) Shuffle the input 1-minute rows with a fixed seed, resort by `CloseTime`, re-aggregate, redetect. Both digests must match the first pass. A same-process repeat is not a meaningful reproducibility test and is not used.
- **Method (inversion rate)**: For each instrument and segment, compute `IFVGRate = IFVG_N / FVG_N` for both lifecycle windows.
- **Method (counts)**: For each instrument and segment, count FVGs and IFVGs against the predeclared floors (`>= 100` FVGs per train/test segment; `>= 50` IFVGs per train/test segment).
- **Method (selectivity verdict)**: Apply the success/failure criteria from the scope using only the primary 120-bar IFVG rate for the pass/fail decision; the 8-bar secondary serves only as a tie-breaker and attribution check between timeframe-transfer effects and lifecycle-duration effects. No statistical test is run on the inversion rate itself; the comparison against the 84-85 percent 1-minute baseline is a predeclared point comparison with the 50 percent materiality threshold from the design.md.
- **Optional bootstrap diagnostic**: A single non-parametric block bootstrap (block size = 50 contiguous events, 2000 resamples, seed = 42) on the primary IFVG rate per instrument may be reported as a confidence-interval diagnostic only. This counts as the experiment's one statistical test and is not used to override the point-comparison verdict.
- **Method (overlap diagnostic)**: For each FVG and IFVG event, flag whether a displacement-confirmed event from EXP-018 within the same instrument's analysis set overlaps the formation or inversion `CloseTime` mapped to the 15-minute grid. Report the share of FVGs and IFVGs that overlap displacement events.
- **Why this method**: EXP-021 depends on IFVG events that are deterministic and selective; the original detector ran at 1-minute and was tautological. The checkpoint requires the reflection to consume actual inversion-rate values rather than a binary pass/fail, so the diagnostic surface must include rates, counts, lifecycle sensitivity, overlap with displacement, and reproducibility evidence.
- **Simpler alternative considered**: Reporting only the inversion rate would obscure whether the drop is real (selectivity gain) or driven by IFVG-count collapse (sample-loss artifact).
- **Assumptions**:
  - **Temporal structure**: Reproducibility checks preserve `CloseTime` ordering after resort; randomness uses a fixed seed.
  - **Cross-view alignment**: Overlap with displacement is via 15-minute bar `CloseTime` mapping, not bar index.
  - **Real-price outcomes**: Not applicable.
- **Expected output**: Per-instrument table with `FreshReloadMatches`, `ShuffledResortMatches`, FVG count, IFVG count, primary inversion rate, 8-bar sensitivity inversion rate, displacement-overlap share, count-floor pass/fail, selectivity pass/fail, and overall verdict; plus a one-row cross-instrument summary against the success criteria.

## Visualisations

1. **IFVG inversion rate by instrument and lifecycle window** — grouped bar plot comparing 15-minute primary (120 bars), 15-minute sensitivity (8 bars), and the Phase 003 1-minute baseline reference at 84-85 percent, with the 50 percent selectivity threshold marked.
2. **FVG and IFVG event counts by instrument and segment** — grouped bar plot with horizontal reference lines at the `>= 100` FVG and `>= 50` IFVG floors per train/test segment.
3. **FVG size distribution by instrument** — histogram or violin plot of 15-minute FVG sizes in ATR units to confirm the size filter is not collapsing the population.
4. **Displacement-overlap share by instrument** — bar plot showing share of 15-minute IFVGs that overlap EXP-018 displacement events, to flag whether IFVG selectivity is redundant with the displacement filter at this timeframe.

## Interpretation Guide

- **Support**: Primary 120-bar IFVG inversion rate is materially below 50 percent on at least 2 of 4 instruments, FVG and IFVG counts meet the floors on those instruments, detection is deterministic on all instruments, and the 8-bar sensitivity confirms direction. The reflection then has evidence that the existing rule may become selective at 15-minute resolution.
- **Against**: Primary 120-bar IFVG inversion rate stays at or near 84-85 percent on at least 3 of 4 instruments, or detection is non-deterministic. The reflection then concludes that timeframe change does not solve IFVG selectivity and Branch B must proceed as a rule-design redesign.
- **Inconclusive**: Selectivity drops on some instruments but counts collapse, or only one instrument meets both gates, or the 120-bar and 8-bar windows disagree by more than 10 percentage points without clear attribution. The reflection records the partial finding and chooses between continuing at 15-minute with weaker support and pursuing rule redesign.

## Complexity Check

- Statistical tests: 1 (optional block bootstrap diagnostic) / 1
- Visualisations: 4 / 4
- New modules: 1 (`python/src/bar_aggregator.py`) / 1

## Data-View Comparison Considerations

### Cross-View Alignment
- The 15-minute view is a derived OHLC resampling, not a chart-type event view, so it is aligned to real time by its `CloseTime` only; no `SourceCloseTime` is required.
- Overlap with EXP-018 displacement events is computed by mapping each 15-minute `CloseTime` to the matching 1-minute `CloseTime` and testing membership in the displacement event set; never by bar index.
- Coverage diagnostics report dropped partial 15-minute windows so the reflection can distinguish detection differences from coverage differences.

### Real-Price Outcome Discipline
- EXP-029 is detection-only and computes no returns, MAE, MFE, P&L, stops, or targets.
- The 15-minute OHLC is a synthetic chart-construction view: it must not be used for trade outcomes anywhere downstream without mapping events back to 1-minute real prices.

### Event Density Differences
- 15-minute FVG counts are expected to be substantially lower than 1-minute FVG counts; this is the intended selectivity gain but also the count-floor risk.
- Per-instrument counts are reported before any inversion-rate or selectivity claim, per the checkpoint's "report event counts before effect sizes" standard.

### Regime Stratification
- This experiment does not stratify by volatility regime. Selectivity at the rule level is the question; regime stratification belongs to outcome experiments (EXP-035 and beyond) only after a selective rule passes the readiness gate.
