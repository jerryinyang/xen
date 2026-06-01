# Analysis Plan: Experiment VAL-001

## Objective

Determine whether the available Xen data architecture preserves timestamp
alignment and row-level no-look-ahead guarantees across base time bars,
clock-aligned timeframes, and deterministic chart-type views, while excluding the
final 30% global holdout from every loaded and generated view.

## Methodology

### Step 1: Holdout-Safe Data Inventory

- **Method**: Deterministic file inventory and lazy Polars loading summary.
- **Why this method**: The question is architectural. A direct inventory of
  available base files, row counts, analysis cutoffs, and analysis-set timestamp
  ranges is sufficient.
- **Simpler alternative considered**: Reading one latest file only. That would
  be simpler but would not validate the architecture across all available
  instruments.
- **Assumptions**: Row counts may be computed from lazy scans, but row values
  beyond the 70% cutoff must not be collected or reported. This fits the
  project convention for chronological holdout exclusion.
- **Expected output**: `run_metadata.json` and per-instrument rows in
  `validation_checks.csv` with total rows, analysis rows, train/test counts, and
  analysis-set timestamp boundaries.

### Step 2: Base Time-Bar Integrity Checks

- **Method**: Rule-based validation of required columns, strict `CloseTime`
  ordering, duplicate timestamps, null timestamps, and OHLC consistency.
- **Why this method**: These are deterministic schema and integrity properties,
  so statistical tests are unnecessary.
- **Simpler alternative considered**: Only checking schema. That would miss
  temporal and OHLC violations that directly affect alignment reliability.
- **Assumptions**: Base time bars are expected to be one completed 1-minute OHLC
  bar per row, ordered by `CloseTime`. The checks do not assume stationarity,
  normality, or independent returns.
- **Expected output**: PASS/FAIL rows in `validation_checks.csv` for each base
  file.

### Step 3: Timeframe Resampling Alignment Checks (independent oracle)

- **Method**: Generate strict 15-minute and 60-minute OHLC resamples from each
  analysis set with `aggregate_ohlc()`, then compare them against an
  **independent** pandas oracle (`resample(closed="right", label="right")`,
  retaining only full `period`-bar windows). Failures are counted from rows
  present in only one side and from any OHLC/timestamp disagreement on matched
  rows. A small hand-anchored golden fixture additionally asserts the first
  window of a known 30-bar series equals values computed in plain Python.
  Output-side properties (no future `CloseTime`, strict `SourceBars`, unique
  `CloseTime`) are also recorded.
- **Why this method**: The earlier plan compared `aggregate_ohlc` against a
  near-verbatim reimplementation of its own bucket formula, so it could not
  catch a shared alignment error. A different library (pandas) and a
  hand-computed fixture are genuinely independent oracles; OHLC values are direct
  source selections, so equality is exact rather than approximate.
- **Simpler alternative considered**: Reusing the production bucket formula as
  the expected value. Rejected as tautological — it verifies the function
  against a copy of itself.
- **Assumptions**: A resampled bar is only valid at its close timestamp. Periods
  (15, 60) divide the trading day evenly, so the pandas day-origin grid and the
  production epoch grid coincide; this is confirmed by the golden fixture and by
  zero oracle disagreement on clean data.
- **Expected output**: PASS/FAIL rows in `validation_checks.csv` and
  `timeframe_summary.csv`.

### Step 4: Chart-Type Timestamp Alignment Checks

- **Method**: Generate Line Break (`level=3`), Renko (`atr_period=14`), and
  Heiken Ashi views from each scoped source timeframe. Validate that governing
  chart timestamps map back to source timeframe `CloseTime` values and never
  exceed the analysis-set source maximum.
- **Why this method**: Timestamp mapping is the required cross-view alignment
  mechanism. Direct timestamp membership checks are simpler and more reliable
  than index-based comparisons.
- **Simpler alternative considered**: Comparing chart rows to source rows by
  position. That is explicitly invalid because sparse chart types have different
  event counts and may emit multiple rows from the same source timestamp.
- **Assumptions**: Line Break and Renko are sparse event streams; duplicate
  `SourceCloseTime` rows are allowed and counted as emitted rows, with distinct
  source timestamps reported separately. Heiken Ashi is one row per source bar.
- **Expected output**: PASS/FAIL rows in `validation_checks.csv`,
  `chart_view_summary.csv`, and chart event-density records.

### Step 5: No-Look-Ahead via Prefix Stability + Determinism

- **Method**: For each chart-type generator and source timeframe, take a bounded
  leading window and assert that `generate(source[:k])` is an exact prefix of
  `generate(source)` at several cut points `k` (`equals` comparison on the first
  `len(prefix)` rows). Separately, assert that two regenerations of the same
  slice are byte-identical.
- **Why this method**: Prefix stability is the operational definition of "no
  look-ahead": if a generator used any future row, giving it more future data
  would change earlier emitted rows. It compares two genuinely different inputs,
  unlike the previous batch-vs-streaming replay, which re-ran the same loop the
  batch path already used and therefore passed by construction. Streaming/batch
  API equivalence is already covered by the `xen` package unit tests.
- **Why a bounded window**: No-look-ahead and determinism are structural
  properties of a sequential generator, so a representative leading window
  falsifies them without a pure-Python pass over millions of rows. Per-row
  alignment properties (Step 4) are still checked on the full generated output.
- **Simpler alternative considered**: Re-running the batch-vs-streaming replay.
  Rejected as tautological. Spot-checking sampled rows was also rejected as
  insufficient to falsify look-ahead.
- **Assumptions**: Deterministic generation; no reliance on return
  distributions, stationarity, or i.i.d. observations.
- **Expected output**: PASS/FAIL rows for prefix stability and determinism per
  chart type, instrument, and source timeframe.

### Step 6: Negative Controls (detection power)

- **Method**: On a deterministic synthetic series, inject faults and require the
  matching check function to report a failure: (a) a look-ahead generator that
  encodes the next bar's value, checked by prefix stability; (b) future,
  unmapped, and `CloseTime != SourceCloseTime` chart timestamps; (c) a corrupted
  Heiken Ashi real price; (d) a corrupted resample value and a dropped resample
  row, checked by the oracle; (e) a perturbed regeneration, checked by the
  determinism comparison. A control whose injected fault is *not* detected is
  recorded as a FAIL.
- **Why this method**: A suite where every assertion passes by construction gives
  false confidence. Negative controls demonstrate that each check can actually
  fail for the fault it guards against, so a clean run on real data is
  meaningful.
- **Simpler alternative considered**: Trusting the positive checks without
  controls. Rejected — that was the core weakness of the prior design.
- **Expected output**: `negative_controls.csv` plus one `negative_control` row
  per control in `validation_checks.csv` (PASS = fault detected).

### Step 7: Result Tables and Plots

- **Method**: Aggregate validation records into compact CSV summaries and two
  bounded plots.
- **Why this method**: The validation outcome should be auditable without
  loading large result artifacts into a notebook.
- **Simpler alternative considered**: Only printing pass/fail to stdout. That
  would not leave enough audit trail for governance or later thesis design.
- **Assumptions**: Plot inputs are aggregated result tables, not full market
  data. No price outcome or model performance metric is plotted.
- **Expected output**:
  - `results/validation_checks.csv`
  - `results/instrument_summary.csv`
  - `results/timeframe_summary.csv`
  - `results/chart_view_summary.csv`
  - `results/negative_controls.csv`
  - `results/run_metadata.json`
  - `plots/validation_status_by_view.png`
  - `plots/chart_event_density.png`

## Visualisations

1. Validation status by view and check category, including the
   `negative_control` view - shows whether any failures or inconclusive checks
   concentrate in a specific layer, and that the negative-control group is all
   PASS (every injected fault detected).
2. Chart event density by instrument, source timeframe, and chart type - shows
   event-row denominators and duplicate-source behavior without deduplication.

## Interpretation Guide

- The result is only meaningful if **every negative control is detected**. If any
  control is missed, the suite cannot be trusted and the whole run is treated as
  FAIL regardless of the positive checks, because a real fault could pass
  unnoticed.
- Given all negative controls detected: if every critical check reports PASS and
  no scoped view is inconclusive, the validation supports the
  architecture-readiness hypothesis. Each PASS now reflects an independent
  property — agreement with the pandas oracle, prefix stability against a
  different input, deterministic regeneration, and timestamp mapping — rather
  than a check that could only pass.
- If any critical check reports FAIL, the validation contradicts the hypothesis:
  a resample disagrees with the oracle, a generator violates prefix stability
  (look-ahead), regeneration is non-deterministic, or a row violates a
  timestamp/real-price contract.
- If required columns/files are missing, or a chart/timeframe combination has too
  few source rows to emit any chart output (e.g., a source timeframe shorter than
  the Renko ATR warm-up), the result is inconclusive for that component.
- Same-source duplicate Line Break or Renko rows are not failures by themselves;
  they are reported as denominator context. A `SourceCount` of 0 is legitimate
  for a same-source duplicate brick; only the first event at each
  `SourceCloseTime` must consume at least one source bar.

## Complexity Check

- Statistical tests: 0 / 0
- Visualisations: 2 / 2
- New modules: 0 / 0

## Data-View Comparison Considerations

### Cross-View Alignment

- Base and resampled time bars align by `CloseTime`.
- Line Break and Renko align by `SourceCloseTime`, never by row number.
- Heiken Ashi aligns by source `CloseTime` and preserves real OHLC columns for
  future real-price outcome discipline.

### Real-Price Outcome Discipline

No strategy P&L, signal returns, or forward outcomes are computed in this
validation. Synthetic chart prices are validated only as generator output fields.

### Event Density Differences

Line Break and Renko may emit fewer rows than source time bars, and Renko may
emit multiple rows at one `SourceCloseTime`. The implementation must report both
emitted-row counts and distinct-source timestamp counts.

### Regime Stratification

No market-regime stratification is in scope. This is an architecture validation,
not a market behavior study.
