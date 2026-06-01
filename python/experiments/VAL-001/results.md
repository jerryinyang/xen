# Results: Experiment VAL-001

## Summary

VAL-001 supports the data-architecture readiness hypothesis. Across BTCUSD,
EURUSD, USTEC, and XAUUSD, the run produced 377 validation rows and every row
reported PASS. All eight negative controls were detected, so the positive
checks have demonstrated failure-detection power rather than merely passing by
construction.

## Detailed Findings

### Finding 1: All scoped validation checks passed

- **Observation**: `validation_checks.csv` contains 377 PASS rows, 0 FAIL rows,
  and 0 INCONCLUSIVE rows.
- **Evidence**: Each real instrument has 92 PASS checks: BTCUSD, EURUSD, USTEC,
  and XAUUSD. The synthetic control group has 9 PASS checks.
- **Interpretation**: This satisfies the predefined "Evidence FOR" criterion:
  every scoped instrument, source timeframe, and chart-type view passed all
  critical checks.

### Finding 2: Negative controls were detected

- **Observation**: `negative_controls.csv` contains 8 controls and every
  `detected` value is `true`.
- **Evidence**: The detected controls covered corrupted resample values, dropped
  resample rows, future source timestamps, unmapped source timestamps,
  `CloseTime != SourceCloseTime`, corrupted Heiken Ashi real prices, an
  intentionally look-ahead generator, and determinism sensitivity.
- **Interpretation**: This is the decisive detection-power result. Under the
  analysis plan, an undetected negative control would invalidate the suite even
  if real-data checks passed. No control was missed.

### Finding 3: Holdout-safe analysis slices covered all available base files

- **Observation**: Four base files were validated from the first 70% analysis
  slice only.
- **Evidence**:

| Instrument | Total Rows | Analysis Rows | Train Rows | Test Rows |
|------------|------------|---------------|------------|-----------|
| BTCUSD | 1,555,658 | 1,088,960 | 762,272 | 326,688 |
| EURUSD | 1,246,061 | 872,242 | 610,569 | 261,673 |
| USTEC | 1,186,488 | 830,541 | 581,378 | 249,163 |
| XAUUSD | 1,186,674 | 830,671 | 581,469 | 249,202 |

- **Interpretation**: The run covered the expected instrument set while preserving
  the global holdout boundary. The train/test counts were reported only for
  auditability; no model training or optimization was performed.

### Finding 4: Resampled timeframes matched the independent oracle

- **Observation**: 15-minute and 60-minute OHLC resamples matched the independent
  pandas oracle for every instrument.
- **Evidence**: Every oracle comparison reported zero rows only in production,
  zero rows only in oracle, and zero OHLC mismatches. Oracle row counts were:
  BTCUSD 71,202 / 16,597, EURUSD 55,230 / 12,628, USTEC 54,787 / 13,228, and
  XAUUSD 54,143 / 12,616 for 15m / 60m respectively.
- **Interpretation**: The scoped timeframe aggregation preserves clock-aligned
  timestamp and OHLC integrity under the strict full-window rule.

### Finding 5: Chart-type views preserved timestamp alignment

- **Observation**: Heiken Ashi, Line Break, and Renko checks passed for all
  instrument/timeframe combinations.
- **Evidence**: Heiken Ashi emitted one row per source row in all 12
  instrument/timeframe combinations. Line Break densities ranged from 0.195149
  to 0.275556 event rows per source row. Renko densities ranged from 0.222171 to
  0.298266 event rows per source row.
- **Evidence**: Renko produced 107,824 duplicate `SourceCloseTime` groups and
  128,556 extra same-source rows across all scoped outputs; these were explicitly
  reported, not deduplicated.
- **Interpretation**: Sparse chart-type outputs behaved as expected: Line Break
  and Renko have different event denominators than time bars, and Renko can emit
  multiple rows at one source timestamp without violating the scoped denominator
  rule.

### Finding 6: Prefix stability and deterministic regeneration passed

- **Observation**: All 36 prefix-stability checks and all 36 deterministic
  regeneration checks passed.
- **Evidence**: Prefix stability used two cut points per chart
  instrument/timeframe combination; every `diverged_cuts` value was 0. The
  intentionally look-ahead generator produced 2 corrupted failures and was
  detected.
- **Interpretation**: Within the scoped bounded probes, chart generators did not
  show row-level evidence of look-ahead behavior, and repeated generation was
  stable for the same input.

## Hypothesis Verdict

**SUPPORTED**

The data supports the hypothesis that the available Xen data architecture
preserves temporal alignment across scoped time-bar, timeframe, and chart-type
views when every derived view is generated only from the first 70% chronological
analysis slice. The support is deterministic rather than statistical: it rests on
zero observed validation failures plus successful detection of injected faults.

## Limitations

- This validation covers the available files present at run time:
  `timebars_btcusd_20230102_000000_20260514_203813.parquet`,
  `timebars_eurusd_20230102_000000_20260514_203330.parquet`,
  `timebars_ustec_20230102_230000_20260514_204410.parquet`, and
  `timebars_xauusd_20230102_230200_20260514_204148.parquet`.
- Prefix stability and determinism are tested with bounded leading windows
  (`150,000` rows for prefix stability and `50,000` rows for determinism), while
  full generated outputs are still checked for timestamp alignment.
- This experiment validates architecture integrity only. It does not test
  predictive signal quality, returns, P&L, execution costs, or strategy
  robustness.
- No active checkpoint `design.md` exists, so this result cannot be mapped to a
  specific current phase objective beyond the scope's thesis-readiness gate.
- `run_metadata.json` records parameters and input files but not a code hash.
  The audit found this non-blocking for interpretation because result artifacts
  were written after the current script.

## Alternative Explanations

- A future data file, generator change, or aggregation change could introduce a
  temporal-integrity issue not present in this run. The result validates the
  current code and current available files, not all future states.
- Prefix stability can falsify look-ahead when future data changes earlier
  emitted rows, but it cannot prove every conceivable implementation defect is
  impossible. The negative controls reduce this risk by showing the checks can
  fail on representative injected faults.

## Recommended Next Steps

1. Create the first active thesis checkpoint now that the base data layer has
   passed the readiness gate.
2. Treat future changes to chart generators, `aggregate_ohlc()`, or data-loading
   conventions as requiring a fresh VAL rerun before downstream thesis work
   relies on them.
3. Add script-hash metadata in a future validation scope if reproducibility
   auditing becomes a recurring requirement.
