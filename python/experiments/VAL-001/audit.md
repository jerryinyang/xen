# Audit Report: Experiment VAL-001

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

VAL-001 can be interpreted. The current script and generated outputs match the
approved scope: all validation checks passed, all negative controls were
detected, and no result file reports a FAIL or INCONCLUSIVE status.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Implements the scoped inventory, base integrity checks, independent pandas resample oracle, chart timestamp alignment, prefix stability, determinism checks, negative controls, and two plots. See lines 245-397, 561-669, and 737-878. |
| `code/run_experiment.py` | Edge cases | PASS | Empty charts produce zero-denominator INCONCLUSIVE through `status_from_failures`; unreadable or malformed files are recorded and skipped without hidden success. See lines 135-140 and 414-446. No such edge cases occurred in the output tables. |
| `code/run_experiment.py` | Type safety | PASS | Public helpers and dataclasses use type hints; result schemas are explicit before CSV output. See lines 76-129 and 813-843. |
| `code/run_experiment.py` | NaN/null handling | PASS | Base OHLC/null timestamp checks are explicit; Heiken Ashi source joins count missing source rows separately from real-price mismatches. See lines 245-270 and 346-363. |
| `code/run_experiment.py` | Holdout exclusion | PASS | The loader scans required columns lazily, counts rows from the lazy scan, sorts by `CloseTime`, slices the first 70%, then collects only that analysis slice. See lines 437-450. |
| `code/run_experiment.py` | Loader ordering | PASS | Time bars are sorted by `CloseTime` before the first-70% slice; downstream timeframe and chart views are generated from that sliced frame only. See lines 448-450 and 981-1003. |
| `code/run_experiment.py` | Memory/performance | PASS | The full generated chart view is produced once per chart/timeframe and reused for alignment and density; plots consume aggregated status/density tables. See lines 569-578 and 885-929. |
| `code/run_experiment.py` | Logging/output | PASS | Manual-run output is concise and uses logging/tqdm progress summaries rather than helper-level prints. See lines 171-190 and 1011-1043. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Imports, constants, dataclasses, helpers, checks, orchestration, output, and `main()` are separated. Output directories are created only via `main()` calling `ensure_output_dirs()`. See lines 16-73, 193-195, and 1011-1013. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plot functions use `validation_checks.csv`-level status counts and `chart_view_summary.csv`-level densities, not raw market bars. See lines 887-888 and 911-918. |
| `code/run_experiment.py` | Docstrings | PASS | Core checks and negative-control helpers include useful docstrings explaining the validation contract. See lines 245-397 and 674-790. |

No relevant files under `python/src/xen/` are modified in the current worktree.
The experiment uses existing deterministic generators and `aggregate_ohlc()`.

## Numerical Validation

### Spot Checks

1. **Holdout split and nested split**:
   - BTCUSD total rows: `1,555,658`.
   - Analysis rows: `int(1,555,658 * 0.7) = 1,088,960`, matching `analysis_slice_loaded`.
   - Train rows within analysis: `int(1,088,960 * 0.7) = 762,272`.
   - Test rows: `1,088,960 - 762,272 = 326,688`.

2. **Event-density calculation**:
   - BTCUSD 1m Renko event rows: `301,377`.
   - BTCUSD 1m source rows: `1,088,960`.
   - Density: `301,377 / 1,088,960 = 0.2767567220`, matching `chart_view_summary.csv`.

3. **Resample oracle checks**:
   - 15m and 60m oracle details report `rows_only_in_production=0`,
     `rows_only_in_oracle=0`, and `ohlc_mismatch=0` for BTCUSD, EURUSD, USTEC,
     and XAUUSD.
   - The synthetic golden fixture reports 0 mismatches over 6 expected fields.

4. **Negative controls**:
   - `negative_controls.csv` has 8 rows and every `detected` value is `true`.
   - The look-ahead negative control produced `corrupted_failures=2`, matching
     the two prefix cut points.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|----------------|--------------|-------|
| Validation status | PASS / FAIL / INCONCLUSIVE | 377 PASS, 0 FAIL, 0 INCONCLUSIVE | YES |
| Instrument checks | 92 per real instrument | BTCUSD 92, EURUSD 92, USTEC 92, XAUUSD 92 | YES |
| Synthetic detection checks | All controls detected | 9 synthetic PASS rows, including 8 negative controls and 1 golden fixture | YES |
| Heiken Ashi density | 1 row per source row | 1.0 for all 12 instrument/timeframe combinations | YES |
| Line Break density | Non-negative event/source ratio | 0.195149 to 0.275556 | YES |
| Renko density | Non-negative event/source ratio | 0.222171 to 0.298266 | YES |
| Renko duplicate-source rows | Allowed and explicitly reported | 107,824 duplicate groups; 128,556 extra same-source rows | YES |
| Plot artifacts | 2 scoped PNG plots | `validation_status_by_view.png`, `chart_event_density.png` | YES |

### Statistical Sanity

No statistical tests were scoped or run. This is appropriate because VAL-001 is a
deterministic architecture validation, not a market-behavior or predictive-power
experiment.

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|------------|--------|----------|
| Holdout-safe inventory | Row counts may be computed from lazy scans, but only first-70% rows may be collected for analysis | YES | Loader uses lazy scan, timestamp sort, first-70% slice, then collect at lines 437-450. |
| Resample oracle comparison | Pandas right-closed/right-labelled resampling is an independent oracle for strict full windows | YES | All 15m and 60m oracle comparisons report zero row or OHLC mismatches. |
| Chart timestamp alignment | `SourceCloseTime`/`CloseTime` membership is the correct alignment rule | YES | All chart timestamp mapping checks passed; no bar-index alignment is used. |
| Prefix stability | Comparing generated prefixes against full-generation prefixes can falsify look-ahead | YES | All 36 prefix-stability checks passed; the look-ahead negative control was detected. |
| Determinism | Same input plus same generator parameters produces identical output | YES | All 36 deterministic-regeneration checks passed; sensitivity control was detected. |
| Real-price discipline | No P&L, returns, stops, targets, or signal outcomes are in scope | YES | Code computes architecture integrity only; synthetic prices are not used for tradable outcomes. |

## Results Plausibility

The outputs are plausible for the scoped data layer. Heiken Ashi emits one row
per source bar, Line Break emits sparse event rows, and Renko emits sparse rows
with explicitly reported duplicate `SourceCloseTime` groups. The duplicate Renko
rows are expected because a single source bar can cross multiple brick
thresholds; the scope and code both count emitted rows rather than silently
deduplicating.

The two plots are consistent with the tables: the validation-status plot shows
only PASS bars by view, and the event-density plot matches the density ranges in
`chart_view_summary.csv`.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none found
- Complexity budget: 0 statistical tests / 0 budgeted, 2 plots / 2 budgeted, 0 new modules / 0 budgeted
- Holdout exclusion verified: YES
- Timestamp alignment verified: YES
- Real-price outcome discipline verified: YES
- Detection-power requirement verified: YES, all negative controls detected

## Issues

### Critical

None.

### Warning

None.

### Info

1. **No active checkpoint available**
   - Description: `docs/experiments-docs/checkpoints/` has no `design.md`, so
     phase alignment cannot be cross-checked beyond the scope's own statement
     that VAL-001 is a thesis-readiness gate.

2. **Run metadata does not record a code hash**
   - Description: `run_metadata.json` records source files and parameters, but
     not the exact script hash. File timestamps show the result artifacts were
     written after the current script, so this does not block interpretation.
     Adding a script hash would improve future reproducibility audits.

## Re-Audit Requirements

None. Re-audit is only required if `code/run_experiment.py`, result CSVs, or plot
artifacts are regenerated or modified.
