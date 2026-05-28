# Audit Report: Experiment EXP-029

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 1
- **Info Notes**: 3

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | FVG detection (`High[i] < Low[i-2]`, `Low[i] > High[i-2]`), lifecycle classification, IFVG inversion logic, and verdict derivation all match the scope and analysis plan exactly. |
| `code/run_experiment.py` | Edge cases | PASS | Empty bars (< 3) guarded in `_candidate_arrays`; `start >= end` guarded in `classify_lifecycle`; NaN ATR guarded with `np.isfinite`. |
| `code/run_experiment.py` | Type safety | PASS | Public functions have type hints and docstrings. Minor: `_candidate_arrays` returns a 7-tuple; type hint reads `tuple[np.ndarray, ...]` which is acceptable. |
| `code/run_experiment.py` | NaN handling | PASS | `ATR14Prior` NaN replaced by 0.0 in `_candidate_arrays` via `np.where(np.isfinite(...))`. `pd.NaT` used for missing timestamps. `fill_null` applied to true-range. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_analysis_timebars` (from `ict_timebar.py`) scans lazily, sorts by `CloseTime`, slices the first 70% before `.collect()`. The 15-minute aggregation receives only the analysis-set 1-minute slice; the holdout is never materialized. |
| `code/run_experiment.py` | Loader ordering | PASS | `scan_parquet → sort("CloseTime") → slice(0, analysis_rows) → collect()` is the correct pattern. The 70/30 train/test split on the 15-minute frame uses `int(aggregated.height * 0.70)` — chronological, not random. |
| `code/run_experiment.py` | Memory/performance | PASS | Polars lazy scan used for 1-minute loading; `aggregate_ohlc` stays in Polars; pandas conversion is bounded to per-instrument PreparedBars arrays and pre-aggregated result tables. |
| `code/run_experiment.py` | Logging/output | PASS | `LOGGER.info` used for per-instrument diagnostics; `print` used only at top-level completion; helper functions return data rather than printing. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Follows imports → path setup → constants → I/O helpers → pure computation → plotting → orchestration → `main()`. `plots_dir.mkdir()` and `results_dir.mkdir()` are called inside `run_experiment()`, not at module level. |
| `code/run_experiment.py` | Plot data reuse | PASS | `events_primary` and `events_sensitivity` from the analysis pass are passed directly to all four plot functions; no second heavy load or re-generation for plotting. |
| `code/run_experiment.py` | Docstrings | PASS | All public functions have docstrings with Parameters and Returns sections. |
| `python/src/bar_aggregator.py` | Correctness | PASS | Clock-aligned bucketing via `(epoch_s - 1) // period_seconds`. Partial windows (< `period_minutes` bars) filtered with `filter(SourceBars == period_minutes)`. OHLC aggregation: first Open, max High, min Low, last Close, summed TickVolume. |
| `python/src/bar_aggregator.py` | Holdout safety | PASS | Module is a pure function; holdout enforcement is the caller's responsibility. `run_experiment.py` correctly applies holdout before calling `aggregate_ohlc`. |

## Numerical Validation

### Spot Checks

**FVG candidate detection — manual verify**

For a bearish FVG at index i: `bearish = High[i] < Low[i-2]`. In `_candidate_arrays`:
- `left_lows = bars.lows[:-2]` → `Low[i-2]` for candidate index `i` ✓
- `current_highs = bars.highs[2:]` → `High[i]` ✓
- `lower = np.where(bearish, current_highs, ...)` = `High[i]` for bearish ✓
- `upper = np.where(bearish, left_lows, ...)` = `Low[i-2]` for bearish ✓
- Zone: [High[i], Low[i-2]] ✓

**IFVG inversion — manual verify**

For a bullish FVG (zone = [lower, upper] = [High[i-2], Low[i]]):
- `inversion_mask = closes < lower` = close below `High[i-2]` = price closed below the gap's bottom ✓
For a bearish FVG (zone = [lower, upper] = [High[i], Low[i-2]]):
- `inversion_mask = closes > upper` = close above `Low[i-2]` = price closed above the gap's top ✓
Both match the EXP-020 "close through the opposite side" definition.

**ATR look-ahead verification**

`_add_atr_15m` computes `rolling_mean(window_size=14, min_samples=14).shift(1)`. After shift, `ATR14Prior[i]` = rolling mean of TrueRange[i-14..i-1]. FVG at bar i uses `atr14_prior = bars.atr14_prior[2:]`, so FVG at index i uses ATR14Prior[i] which covers only bars before i. No look-ahead. ✓

**Verdict derivation — spot check**

From results:
- `passing = 0` → not FOR
- `reproducible_count = 4` → first AGAINST branch skipped
- `near_baseline_count = 4` (all instruments: EURUSD 0.853, XAUUSD 0.836, BTCUSD 0.832, USTEC 0.848 — all ≥ 0.79 = 0.84 − 0.05)
- `near_baseline_count >= 3` → verdict = AGAINST ✓

**Inversion rate cross-check**

From `count_readiness.csv`:
- EURUSD all: IFVG_N / FVG_N = (7321 + 3156) / (8583 + 3683) = 10477 / 12266 = 0.854 → matches `bootstrap_inversion_rate.csv` PrimaryIFVGRate = 0.854 ✓
- BTCUSD all: (7671 + 3491) / (9283 + 4129) = 11162 / 13412 = 0.832 ✓

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| IFVGRate (primary 120-bar) | (0, 1] | [0.821, 0.857] | YES |
| IFVGRate (8-bar sensitivity) | (0, 1] | [0.454, 0.479] | YES |
| FVG_N per segment | > 0 | [3391, 9283] — all ≥ floor 100 | YES |
| IFVG_N per segment | > 0 | [2783, 7321] — all ≥ floor 50 | YES |
| Bootstrap CI width | Reasonable | ~0.009–0.019 pp wide (tight, expected given N=11–13K) | YES |
| Lifecycle DifferencePP | Finite | [37.55, 38.63] pp — very consistent across instruments | YES |
| Reproducibility | All True | 4/4 instruments: all digest pairs match | YES |
| Coverage: aggregated_bars_out | > 0 | [54,143–71,202] per instrument | YES |

### Statistical Sanity

| Statistic | Value | Makes sense? | Notes |
|-----------|-------|-------------|-------|
| Bootstrap 95% CI for EURUSD primary IFVG rate | [0.846, 0.865] | YES | Tight CI expected given N=12,266; excludes 0.84 lower baseline. |
| XAUUSD CI [0.825, 0.846] | YES | Just touches the 0.84 lower boundary, confirming the "near baseline" classification. |
| Lifecycle sensitivity DifferencePP ~38pp | YES | The 120-bar window gives a much longer observation window, dramatically increasing the chance of a close-through event; the 8-bar sensitivity correctly isolates lifecycle duration as the dominant driver. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| 15-min aggregation | Full 15-bar windows only | YES | `filter(SourceBars == period_minutes)` enforced in `aggregate_ohlc`; coverage diagnostics report dropped bars. |
| FVG detection | No look-ahead via ATR | YES | ATR14Prior uses `rolling_mean.shift(1)` — only prior bars. |
| Reproducibility | Deterministic pipeline | YES | SHA-256 digests match on fresh-reload and shuffled-resort for all 4 instruments. |
| Lifecycle | First inversion terminates forward scan | YES | `scan_stop = inversion_pos + 1` limits partial/full-fill search to pre-inversion bars. |
| Segment assignment | Chronological 70/30 on 15-min frame | YES | `int(aggregated.height * 0.70)` used as row cutoff on the time-sorted 15-min frame. |
| Block bootstrap | Temporal block structure ≈ 50 contiguous FVGs | PARTIAL | Block size = 50 FVGs is predeclared by scope. FVG temporal spacing is variable, so this approximates but does not guarantee a specific time window. Acceptable given the analysis plan's documented scope. |

## Results Plausibility

The primary IFVG rate of 83–86% across all four instruments directly matches the Phase 003 1-minute baseline of 84–85%. The 120-bar lifecycle window gives each FVG up to 120 × 15 = 1,800 minutes (30 hours) to experience a close-through event, which is long enough to make inversion nearly inevitable for most FVGs. The 8-bar sensitivity (2 hours elapsed) drops the rate to 45–48%, confirming that lifecycle duration — not the FVG rule itself — drives the high inversion rate.

All FVG counts (3,391–9,283 per segment) far exceed the predeclared floors (100 FVGs, 50 IFVGs per segment), confirming adequate 15-minute coverage. The ATR-based size filter does not collapse the population.

Coverage diagnostics are internally consistent: EURUSD drops 43,792 bars vs 8,736 for USTEC, consistent with EURUSD having more session-boundary gaps.

AGAINST verdict is correctly derived and reflects a clear finding: the 120-bar IFVG inversion rate at 15-minute resolution replicates the 1-minute baseline within 2pp on all 4 instruments.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 1 statistical test / 1 budgeted; 4 visualisations / 4 budgeted; 1 new module (`python/src/bar_aggregator.py`) / 1 budgeted
- Holdout exclusion verified: YES — holdout never loaded; 15-minute aggregation applied only to analysis-set 1-minute slice

## Issues

### Critical

None.

### Warning

1. **Displacement overlap diagnostic returns 0.0 across all instruments due to potential timestamp timezone mismatch**
   - File: `code/run_experiment.py`, `displacement_overlap_share`, lines 605–649
   - Description: `load_displacement_events_1m` reads EXP-018 CSVs and converts `DisplacementTime` via `pd.to_datetime()`, producing timezone-naive Timestamps. The FVG `CreationTime` values originate from Polars UTC-aware datetime columns; when passed through `pd.to_datetime(frame["CloseTime"]).to_numpy()` and then `pd.Timestamp(bars.close_times[idx])`, the resulting Timestamps are UTC-aware. Comparing a UTC-aware Timestamp against a set of naive Timestamps always returns False in pandas ≥ 2.0, silently yielding 0.0 for all instruments despite 289–437 displacement events being loaded.
   - Impact: The displacement overlap diagnostic is meaningless and reports zero when the true overlap may be non-zero. However, the analysis plan and scope explicitly designate this as a "soft" diagnostic that is "not used for the verdict." The verdict, inversion rates, counts, and reproducibility checks are entirely unaffected.
   - Fix: In `displacement_overlap_share`, localize `inst_events["CreationTime"]` timestamps to UTC before set membership: `ts_utc = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")`. Or normalize both sides to naive UTC via `.tz_localize(None)` consistently.

### Info

1. **ATR14Prior is NaN for the first 14 15-minute bars per instrument**
   - Description: `rolling_mean(window_size=14, min_samples=14).shift(1)` yields NaN for bar indices 0–13. FVG candidates at indices 2–13 use `min_size = precision_step` as the fallback. This represents a tiny fraction of the total 54K–71K 15-minute bars and is the intended behavior per the analysis plan's "ATR_14 recomputed on 15-minute bars" specification.

2. **EURUSD has disproportionately more dropped partial-window bars than other instruments**
   - Description: EURUSD drops 43,792 1-minute bars (5.0% of 872,242) vs 8,736 (1.0%) for USTEC. This is expected for a forex pair with weekend/session gaps that create incomplete 15-minute windows at session boundaries. The analysis-set sizes are still large (55,230–71,202 15-minute bars), and no count floors are threatened.

3. **`side` assignment in `_candidate_arrays` defaults to "Bullish" when neither condition holds**
   - Description: `side = np.where(bearish, "Bearish", "Bullish")` assigns "Bullish" for rows where both `bearish` and `bullish` are False. However, `keep = (bearish | bullish) & ...` eliminates all such rows before they enter the output. No incorrect FVG events are produced.

## Re-Audit Requirements

None — verdict is PASS with no critical issues.
