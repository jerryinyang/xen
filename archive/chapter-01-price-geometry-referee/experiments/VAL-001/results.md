# Results: Experiment VAL-001 (rev. 3)

## Summary

VAL-001 rev. 3 supports the data-architecture readiness hypothesis. Across
BTCUSD, EURUSD, USTEC, and XAUUSD, the run produced 416 validation rows and every
row reported PASS. All 23 negative controls were detected, so the positive checks
have demonstrated failure-detection power rather than merely passing by
construction. rev. 3 closes the three detection-power gaps found after rev. 2: a
negative control now backs every data-integrity and alignment check (8 → 23), the
determinism control routes an actually non-deterministic generator through the
real check, and no-look-ahead is probed at the head, middle, and tail of each
analysis slice rather than only its head.

## Detailed Findings

### Finding 1: All scoped validation checks passed

- **Observation**: `validation_checks.csv` contains 416 PASS rows, 0 FAIL, 0
  INCONCLUSIVE.
- **Evidence**: Each real instrument has 98 PASS checks (BTCUSD, EURUSD, USTEC,
  XAUUSD); the synthetic group has 24 PASS checks (23 negative controls + 1
  golden fixture).
- **Interpretation**: Satisfies the "Evidence FOR" criterion — every scoped
  instrument, source timeframe, and chart-type view passed all critical checks.

### Finding 2: Detection power is now complete and demonstrated

- **Observation**: `negative_controls.csv` contains 23 controls and every
  `detected` value is `true`.
- **Evidence**: Controls cover base time-bar integrity (null / non-increasing /
  duplicate `CloseTime`, invalid OHLC, null OHLC), resample oracle agreement and
  the three resample output-side checks, all sparse-chart alignment checks
  (missing / null / future source time, `CloseTime != SourceCloseTime`, negative
  and first-event-zero `SourceCount`), Heiken Ashi real-price / row-count /
  mapping / source-count checks, the chart schema check, the look-ahead generator
  (prefix stability, `corrupted_failures=3`), and an actually non-deterministic
  generator (determinism).
- **Interpretation**: This is the decisive detection-power result and the central
  improvement over rev. 2. Under the plan, an undetected control invalidates the
  suite regardless of real-data results; none was missed, and coverage now spans
  every data-integrity and alignment check rather than a subset.

### Finding 3: Holdout-safe analysis slices covered all available base files

- **Observation**: Four base files were validated from the first-70% analysis
  slice only (counts unchanged from rev. 2; loader untouched).
- **Evidence**:

| Instrument | Total Rows | Analysis Rows | Train Rows | Test Rows | Analysis End |
|------------|------------|---------------|------------|-----------|--------------|
| BTCUSD | 1,555,658 | 1,088,960 | 762,272 | 326,688 | 2025-06-17 22:38 |
| EURUSD | 1,246,061 | 872,242 | 610,569 | 261,673 | 2025-05-09 16:55 |
| USTEC | 1,186,488 | 830,541 | 581,378 | 249,163 | 2025-05-12 04:54 |
| XAUUSD | 1,186,674 | 830,671 | 581,469 | 249,202 | 2025-05-12 03:35 |

- **Interpretation**: The global holdout boundary was preserved; train/test counts
  are reported for auditability only, with no training or optimization.

### Finding 4: Resampled timeframes matched the independent oracle

- **Observation**: 15-minute and 60-minute resamples matched the independent
  pandas oracle for every instrument — zero rows-only-in-production, zero
  rows-only-in-oracle, zero OHLC mismatches across all eight comparisons — and
  the golden fixture matched a hand-computed window (0/6).
- **Interpretation**: Scoped timeframe aggregation preserves clock-aligned
  timestamp and OHLC integrity under the strict full-window rule.

### Finding 5: Chart-type views preserved timestamp alignment, reproducibly

- **Observation**: Heiken Ashi, Line Break, and Renko checks passed for all
  instrument/timeframe combinations, and every event count and density is
  byte-identical to rev. 2.
- **Evidence**: Heiken Ashi density 1.0 across all 12 combos; Line Break density
  0.195149–0.275556; Renko density 0.222171–0.298266. Renko produced 107,824
  duplicate `SourceCloseTime` groups and 128,556 extra same-source rows across all
  scoped outputs, explicitly reported, not deduplicated.
- **Interpretation**: Sparse chart-type denominators behave as expected, and
  identical output on an independent re-run is direct evidence of deterministic
  generation.

### Finding 6: No structural look-ahead at head, middle, or tail

- **Observation**: All 60 prefix-stability checks passed (head 12, middle 12,
  tail 12 for 1-minute views; `full` 24 for 15m/60m views whose slice fits the
  probe window), and all 36 deterministic-regeneration checks passed.
- **Evidence**: Every `diverged_cuts` value was 0 across three cut points per
  window; the injected look-ahead generator was detected at all three cuts
  (`corrupted_failures=3`).
- **Interpretation**: Within probe windows positioned across the slice — not only
  its head — chart generators showed no row-level look-ahead, and repeated
  generation was stable.

## Hypothesis Verdict

**SUPPORTED**

The data supports the hypothesis that the available Xen data architecture
preserves temporal alignment across scoped time-bar, timeframe, and chart-type
views — with no future-timestamp or cross-view misalignment in any emitted row,
and no structural look-ahead at the head/middle/tail probe windows — when every
derived view is generated only from the first-70% chronological analysis slice.
The support is deterministic rather than statistical: it rests on zero observed
validation failures plus detection of every injected fault, now across the full
set of data-integrity and alignment checks.

## Limitations

- Covers the four base files present at run time. A future data file, generator
  change, or aggregation change could introduce an issue not present here.
- Structural no-look-ahead and determinism are probed on bounded windows
  (`150,000` rows for prefix stability at head/middle/tail, `50,000` for
  determinism). Full generated outputs are still checked for timestamp alignment
  on every row, but the structural-look-ahead claim is scoped to the probe
  windows by design.
- A few structural/informational checks (`required_columns_present`,
  `single_symbol_per_file`, `timeframe_source_is_base`, `analysis_slice_loaded`)
  have no negative control; the audit classifies this as non-blocking because they
  are availability/informational checks, not core integrity assertions.
- Validates architecture integrity only — not predictive signal quality, returns,
  P&L, execution costs, or strategy robustness.
- No active checkpoint `design.md` exists, so the result maps to the scope's
  thesis-readiness gate, not a specific phase objective.
- `run_metadata.json` records parameters and inputs but not a code hash.

## Alternative Explanations

- The result validates the current code and currently available files, not all
  future states. Negative controls reduce — but cannot eliminate — the risk that
  an undetectable defect exists outside the injected fault set.
- Prefix stability falsifies look-ahead when future data changes earlier emitted
  rows; the head/middle/tail positioning widens positional coverage but still
  cannot prove every conceivable implementation defect impossible.

## Recommended Next Steps

1. Create the first active thesis checkpoint now that the base data layer has
   passed the strengthened readiness gate.
2. Treat future changes to chart generators, `aggregate_ohlc()`, or data-loading
   conventions as requiring a fresh VAL rerun before downstream work relies on them.
3. Consider adding script-hash metadata and (optionally) controls for the
   remaining structural checks if reproducibility/coverage auditing becomes a
   recurring requirement.
