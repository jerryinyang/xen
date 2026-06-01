# Audit Report: Experiment VAL-001 (rev. 3)

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 3

VAL-001 rev. 3 can be interpreted. The re-run with strengthened detection-power
coverage and multi-position look-ahead probing matches the approved rev. 3 scope
and plan: all validation checks passed, all negative controls were detected, and
no result file reports a FAIL or INCONCLUSIVE status. Generator outputs reproduce
the rev. 2 run exactly, confirming deterministic generation.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Inventory, base integrity, independent pandas resample oracle, output-side resample checks, chart timestamp alignment, multi-position prefix stability, determinism, 23 negative controls, golden fixture, and two plots all implemented. |
| `code/run_experiment.py` | Negative-control integrity | PASS | Every control routes its corrupted input through the *same* function used on real data: `base_timebar_failures`, `resample_failures`, `resample_output_failures`, `sparse_chart_failures`, `ha_failures`, `schema_failures`, `prefix_stability_failures`, `determinism_failures`. No control re-implements the check it guards. |
| `code/run_experiment.py` | Gap-2 fix | PASS | `determinism_sensitivity` now routes an actually non-deterministic generator (mutable call counter) through `determinism_failures`, which returns 1; it no longer tests `DataFrame.equals` in isolation. |
| `code/run_experiment.py` | Gap-3 fix | PASS | `positioned_windows` yields head/middle/tail windows for slices larger than `PREFIX_WINDOW_ROWS` and a single `full` window otherwise; `PREFIX_FRACTIONS` has three cut points. `tail` windows are taken from the analysis-slice frame, never the holdout. |
| `code/run_experiment.py` | Holdout exclusion | PASS | Loader unchanged: lazy scan → `sort("CloseTime")` → `slice(0, int(0.7*total))` → collect. Derived timeframes/charts and all probe windows are built from that slice only. |
| `code/run_experiment.py` | Edge cases / NaN | PASS | Zero-denominator → INCONCLUSIVE; empty charts handled; explicit null OHLC / null-timestamp checks. No such edge cases occurred in output. |
| `code/run_experiment.py` | Organization / import side effects | PASS | New pure helpers placed in the checks section; `positioned_windows` beside the prefix probe. Output directories created only in `main()`. |
| `code/run_experiment.py` | Plot reuse / memory | PASS | Plots consume aggregated status/density tables; the full chart is generated once per chart/timeframe and reused. |
| `code/run_experiment.py` | Static checks | PASS | `py_compile` clean; `ruff check` clean; `xen` unit tests 8/8. |

No files under `python/src/xen/` were modified. The experiment uses existing
deterministic generators and `aggregate_ohlc()`.

## Numerical Validation

### Spot Checks

1. **Holdout / nested split (unchanged from rev. 2)**: BTCUSD `int(1,555,658 * 0.7) = 1,088,960`
   analysis rows; `int(1,088,960 * 0.7) = 762,272` train; `326,688` test — matches
   `analysis_slice_loaded`. Analysis-set end `2025-06-17 22:38:00` sits before the holdout.
2. **Deterministic reproduction**: every `chart_view_summary.csv` event count and
   density is byte-identical to rev. 2 (e.g. BTCUSD 1m Renko `301,377` rows,
   density `0.2767567220099912`; Renko duplicate totals `107,824` groups /
   `128,556` extra rows). Identical output on an independent run is direct
   evidence of deterministic generation.
3. **Resample oracle**: all eight 15m/60m comparisons report
   `rows_only_in_production=0`, `rows_only_in_oracle=0`, `ohlc_mismatch=0`; golden
   fixture 0/6 mismatches.
4. **Negative controls**: `negative_controls.csv` has 23 rows, every `detected`
   is `true`. The look-ahead control reports `corrupted_failures=3` (one per cut
   point); the determinism control reports `1`.

### Range Checks

| Metric | Expected | Actual | Pass? |
|--------|----------|--------|-------|
| Validation status | PASS/FAIL/INCONCLUSIVE | 416 PASS, 0 FAIL, 0 INCONCLUSIVE | YES |
| Checks per real instrument | 98 | BTCUSD/EURUSD/USTEC/XAUUSD = 98 each | YES |
| Synthetic checks | 23 controls + 1 golden | 24 (SYNTHETIC) | YES |
| Negative controls detected | 23 / 23 | 23 / 23 | YES |
| Prefix-stability checks | head 12, middle 12, tail 12, full 24 | identical | YES |
| Determinism checks | 36 | 36 | YES |
| Heiken Ashi density | 1.0 | 1.0 across all 12 combos | YES |
| Line Break density | non-negative ratio | 0.195149–0.275556 | YES |
| Renko density | non-negative ratio | 0.222171–0.298266 | YES |
| Plot artifacts | 2 PNGs | regenerated 08:50 | YES |

### Statistical Sanity

No statistical tests were scoped or run. Appropriate: VAL-001 is a deterministic
architecture validation, not a market-behavior or predictive-power experiment.

## Scope Compliance

- Analysis plan (rev. 3) followed: YES
- Deviations: none found
- Complexity budget: 0 statistical tests / 0, 2 plots / 2, 0 new modules / 0
  (new pure helpers live inside the experiment script)
- Holdout exclusion verified: YES
- Timestamp alignment verified: YES (full-output alignment on every emitted row;
  bar-index alignment not used)
- Real-price outcome discipline verified: YES (no returns/P&L/signal outcomes)
- Detection-power requirement verified: YES — every base-integrity, resample,
  sparse-chart, HA, schema, look-ahead, and determinism check has a control, all
  detected

## Issues

### Critical
None.

### Warning
None.

### Info

1. **A few structural/informational checks remain without controls.**
   `required_columns_present` and `single_symbol_per_file` (loader-structural) and
   the informational markers `timeframe_source_is_base` and `analysis_slice_loaded`
   (whose `failures` are hard-wired to 0 and carry counts, not falsifiable
   assertions) have no negative control. These fall within the scope's
   "availability/IO defensive checks" exclusion in spirit; the core
   data-integrity and alignment assertions are all controlled. Non-blocking.

2. **No active checkpoint available.** `docs/experiments-docs/checkpoints/` has no
   `design.md`, so phase alignment is limited to the scope's thesis-readiness
   framing.

3. **Run metadata records no code hash.** `run_metadata.json` records parameters,
   probe positions/fractions, and source files, but not a script hash. Result
   artifacts (08:50) post-date the rev. 3 script edits, so this does not block
   interpretation; a script hash would aid future reproducibility audits.

## Re-Audit Requirements

None. Re-audit is required only if `code/run_experiment.py`, the result CSVs, or
the plots are regenerated or modified.
