# Audit Report: Experiment VAL-004

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Implements the two scoped changes exactly (timeframe set [15,30] + tolerant `min_coverage=0.90` mode); all check logic, probe bounds, negative-control catalogue byte-identical to VAL-001 rev. 3 in strict mode. |
| `code/run_experiment.py` | Edge cases | PASS | `status_from_failures` maps denom ≤ 0 → INCONCLUSIVE; `dropped_window_fraction` maps candidate_windows == 0 → None fractions + INCONCLUSIVE (never 0/0); `synthetic_source` with n_bars=0 would produce empty frame — unused (min n_bars=240 in negative controls, 30/60 in golden fixtures); `positioned_windows` handles n ≤ window_rows as single `full` window; empty chart batches produce zero failure counts with no crash. |
| `code/run_experiment.py` | Type safety | PASS | Typed dataclasses (`ValidationCheck`, `EventDensity`, `CoverageRow`, `AnchorRow`, `ChartSpec`, `AnalysisData`); public functions have type hints; `to_canonical_time` casts only present timestamp columns. |
| `code/run_experiment.py` | NaN handling | PASS | No NaN computation paths; null checks are explicit (`.is_null()` in base_timebar_failures, chart_failures); HA join uses `how="left"` with null guard; dropped fractions are `None` when candidate_windows == 0, filtered out in plotting. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_analysis_data` sorts by `CloseTime`, computes `int(total_rows * 0.7)`, collects only `slice(0, analysis_rows)` — final 30% row contents never materialised. All aggregation, oracle, coverage, chart, fingerprint derive from the first-70% frame. Holdout rule recorded in metadata. |
| `code/run_experiment.py` | Loader ordering | PASS | Lazy scan (`pl.scan_parquet`) → `select(REQUIRED_TIMEBAR_COLUMNS)` (column-pruned) → `sort("CloseTime")` → `slice(0, analysis_rows)` → `collect()`. No full-data collection before holdout cut. |
| `code/run_experiment.py` | Memory/performance | PASS | 1m analysis frames (~0.5–1M rows) collect at most 70%; 15m/30m aggregated frames are 23k–60k rows; chart generators iterate sequentially; prefix stability bounded by `PREFIX_WINDOW_ROWS=150k`; dropped-fraction via single `group_by`. All within safe bounds. |
| `code/run_experiment.py` | Safe optimization | PASS | No vectorization that changes temporal semantics; `dropped_window_fraction` is a pure Polars group-by aggregation (causally safe); prefix stability is sequential by construction; fingerprint is a deterministic canonical sort+CSV+sha256, not a data-transformation optimization. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` on the 17-instrument outer loop and chart-view inner loop; helpers return data rather than printing; per-instrument summary via `tqdm.write()`. |
| `code/run_experiment.py` | Logging/output | PASS | Concise section/subsection logging; per-instrument one-line analysis-slice summary; failures/inconclusives tracked numerically; no noisy per-row output. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Imports → constants → dataclasses → small helpers → pure check functions → loading → orchestration → negatives → output/plots → main; `ensure_output_dirs()` called only in `main()`, never at module level. Clear VAL-001-style section separators (`# ----`). |
| `code/run_experiment.py` | Plot data reuse | PASS | Plot inputs are the small aggregated `coverage_df` (34 rows on 17×2 domains) and an aggregated status grid from `checks_df` — no raw-data conversion, no second heavy generator pass. |
| `code/run_experiment.py` | Docstrings | PASS | Module docstring states scope and the two changes; all public functions have docstrings with Parameters/Returns sections; `independent_resample_oracle` covers the key parameterization logic. |

## Numerical Validation

### Spot Checks

1. **Tolerant floor derivation**: `tolerant_floor(15, 0.90)` = `max(2, ceil(13.5))` = 14; `tolerant_floor(30, 0.90)` = `max(2, ceil(27.0))` = 27. Both match documented `[14,15]` / `[27,30]`. Guard check PASS.

2. **Dropped-window fraction arithmetic**: For AUDJPY-15m: candidate=59,854, retained=59,236, dropped=618, `618/59854 ≈ 0.01033` vs recorded `0.010325124469542554` — matches to display precision. All 34 coverage rows are non-negative, bounded [0, 1].

3. **15m strict determinism anchor — BTCUSD**: `fingerprint_frame` sorts by `CloseTime`, serialises 71,202 rows: hex digest `4847f54d...` recorded in `determinism_anchor.csv`. Two-regeneration deterministic check via `aggregate_timeframe(data.frame, 15, None).equals(agg15_strict)` — PASS.

4. **Negative controls**: All 28/28 controls detected (detected=True). The tolerant-range controls: `resample_tolerant_sourcebars_below_floor_15m` (floor=14, injected 13) detected; `resample_tolerant_sourcebars_above_period_30m` (injected 99 > 30) detected. Both must-not-overfire assertions: `resample_tolerant_inrange_partial_not_flagged` for 15m@0.90 (floor=14, in-range 14) flagged=0, PASS.

5. **Universe reconciliation**: 17/17 expected instruments present, 0 missing/duplicates; 1 unexpected (ANALYSIS70, disclosed, 4 pre-sliced files excluded from processing). `ANALYSIS70` is the correct inferred stem for the `timebars_analysis70_*.parquet` pre-sliced files.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| `SourceBars` (strict agg) | `== period_minutes` | {15} for 15m, {30} for 30m | YES (0 wrong in all cells) |
| `SourceBars` (tolerant agg) | [14,15] for 15m, [27,30] for 30m | [14,15] for 15m, [27,30] for 30m | YES (0 wrong in all cells) |
| `CloseTime` (time bars) | strictly increasing | 0 violations per instrument | YES (0 non-increasing) |
| `OHLC` relationships | High >= max(O,C), Low <= min(O,C) | 0 invalid per instrument | YES (0 invalid OHLC) |
| HA `RealClose` == source Close | exact match | 0 mismatches per cell | YES |
| Dropped fraction tolerant | [0, 1] per domain | [0.003, 0.133] | YES |
| Dropped fraction strict | [0, 1] per domain | [0.012, 0.277] | YES |

### Statistical Sanity

N/A — VAL-004 is a deterministic construction-integrity validation with zero statistical tests.

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| `aggregate_ohlc` with 30m strict | 30 divides 1440 evenly → pandas day-origin grid coincides with production epoch grid | YES | 0 oracle disagreement rows on all 17 instruments (resample_matches_independent_oracle: 0 rows_only_in_production, 0 rows_only_in_oracle, 0 ohlc_mismatch) |
| Tolerant retention | Retained partial windows are correct (SourceBars in [floor, P]) | YES | 0 wrong_sourcebars in all tolerant cells; must-not-overfire assertion PASS; dropped fractions internally consistent (tolerant ≤ strict in every cell) |
| Prefix stability | More data does not change earlier generator output | YES | 0 prefix-stability divergences across all cells and all three positions (head/middle/tail) |
| Determinism | Same input + parameters → identical output | YES | 0 determinism failures; fingerprints reproducible |

## Results Plausibility

- **Dropped fractions**: All 34 cells between 0.003 and 0.133, well below the 0.25 admission gate. Tolerant fractions are consistently lower than strict fractions (as expected — tolerant retains partial windows). Index instruments (DE30, JP225, US500) have higher dropped fractions (~0.08–0.13) reflecting market-hour gaps, which is expected.
- **Chart densities**: Heiken Ashi always 1.0 (same bar count); Line Break ~0.20–0.30 (consistent with Level 3); Renko ~0.22–0.27 (consistent with ATR 14). Values plausible and match prior VAL-001 patterns.
- **Anchor reconciliation**: All 17 instruments PASS prior reconciliation; fingerprints differ by design (new row counts from data refresh), but determinism_status is PASS everywhere.
- **No unexpected FAIL or INCONCLUSIVE check** in any of the 2,279 validation rows.
- **No negative control missed** (28/28 detected).
- **Exit contract**: 0 failures, 0 inconclusive → PASS (exit 0).

## Scope Compliance

- Analysis plan followed: YES
- Deviations: None. The code implements exactly the two scoped changes (timeframe set `[15,30]` + tolerant `min_coverage=0.90` mode), plus the planned additions (coverage_map, determinism_anchor, 30m golden fixture, tolerant range controls). No extra analyses.
- Complexity budget: 0 statistical tests / 0 budgeted; 2 plots / 2 budgeted; 0 new `xen` modules / 0–1 budgeted.
- Holdout exclusion verified: YES — `load_analysis_data` collects only `int(total*0.7)` rows; no holdout row inspected. Fence asserted in metadata.
- 15m strict determinism anchor reconciles to VAL-001/VAL-003 record: YES (all 17 instruments PASS).
- Negative controls all 28/28 detected + both must-not-overfire assertions PASS.

## Issues

### Critical

None.

### Warning

None.

### Info

1. **ANALYSIS70 unexpected universe entries.** Four `timebars_analysis70_*.parquet` files (BTCUSD, EURUSD, USTEC, XAUUSD) are present in `data/timebars/`. The universe reconciliation correctly classifies them as `unexpected_inferred=["ANALYSIS70"]` and excludes them from processing. These are pre-sliced 70% files from prior experiment runs and are not a defect — the F01 pre-execution fix added the 17-instrument `EXPECTED_INSTRUMENTS` precisely to prevent their silent double-counting.

## Re-Audit Requirements

None — PASS.
