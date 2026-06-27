# Audit Report: Experiment EXP-022

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Formulas, joins, indices, and temporal ordering verified. Target transfer formula matches scope (`favorable_bps = d * 10000 * log(event_favorable_target / event_trigger_close)`). Lifetime scan preserves first-hit-by-time ordering. Trend-change map built with right-to-left pass — look-ahead-safe. |
| `code/run_experiment.py` | Edge cases | PASS | Zero-denominator guard via `np.divide(..., where=den>0)` and explicit null rates. Empty regimes, missing regime LUT entries, and missing future bars all handled with explicit counters. Ties counted and reported (0 observed). |
| `code/run_experiment.py` | Type safety | PASS | Type hints on all public functions. Numpy/Polars/pandas types correctly cast. |
| `code/run_experiment.py` | NaN handling | PASS | `np.divide` with `where` guard; `np.nanmean`; finite checks on localvol. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_analysis_data` slices first 70% via lazy plan before collection. `validate_event_join` hard-fails if `trigger_idx ≥ n`. `validate_regime_join` hard-fails if any regime index ≥ n. Completion scan bounded by `analysis_end_idx = n-1`. |
| `code/run_experiment.py` | Loader ordering | PASS | Lazy scan sorts by `CloseTime` before counting total rows and slicing first 70%. No full-data collection before split. |
| `code/run_experiment.py` | Memory/performance | PASS | Column-pruned reconstruction reused from `referee_calibration`. Bootstrap/permutation chunked. Plot inputs derived from in-memory records. |
| `code/run_experiment.py` | Safe optimization | PASS | Vectorized first-hit (`np.argmax` over post-start segment) preserves first-completed-close-by-time ordering. No row-order or temporal-causality changes. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` over file rebuild, cell processing, and domain inference. |
| `code/run_experiment.py` | Logging/output | PASS | Concise INFO logging. Helper functions return data, not print. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Clear VAL-001-style sectioning. Directories created only in `run()` orchestration. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots drawn from aggregations of in-memory records; no full-frame reconstruction. |
| `code/run_experiment.py` | Docstrings | PASS | All public functions have docstrings with Parameters and Returns. |

## Numerical Validation

### Spot Checks

**Check: BTCUSD/5m/bull/non-pyramid event favorable rate**

From `lifetime_completion_summary.csv`:
- Event: favorable=664, adverse=376, trend_change=195, unfinished=0
- Rate = 664 / (664 + 376) = 664 / 1040 = 63.846%
- CSV reports: 63.84615384615385 ✓

- Control: favorable=2159, adverse=2633, trend_change=561, unfinished=0
- Rate = 2159 / (2159 + 2633) = 2159 / 4792 = 45.054%
- CSV reports: 45.0542570951586 ✓

**Check: 5m domain instrument-averaged rate diff**

From `domain_lifetime_tests.csv`:
- Event fav rate: 68.49%, Control fav rate: 44.56%, diff: 23.94pp
- The diff is the unweighted mean of per-instrument diffs. Rough computation from the 4 instruments' non-pyramid/pyramid pooled rates confirms ≈ 23.9pp. ✓

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Direction | {+1, -1} | [-1, 1] | YES |
| Lifetime bps | ℝ | [-197.4, 105.8] | YES — extreme values in BTCUSD/4h controls, expected for wide targets |
| Favorable bps | > 0 (valid events) | [0.003, 796.3] | YES |
| Adverse bps | < 0 (valid events) | [-842.7, -0.001] | YES |
| Bars to completion | ≥ 1 | [1, 145] | YES |
| Localvol bps | > 0 | [0.177, 53.8] | YES |
| Median vol context ratio | > 0 | [0.851, 1.126] | YES — all well within [0.5, 2.0] confound bounds |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| 5m rate diff CI | [22.7, 25.1] pp | YES | Large effect, tight CI (high N on 5m) |
| 1h rate diff CI | [17.2, 26.6] pp | YES | Wider CI (fewer events), still well above 0 |
| 4h rate diff CI | [17.7, 35.3] pp | YES | Widest CI (fewest events), lower bound still above 0 |
| Holm-adjusted p (all domains) | 0.0003 | YES | All raw p = 0.0001 before adjustment; 3 domains → factor 3 |
| Expectancy diff 5m | 6.5 bps | YES | Positive but modest (many small 5m moves) |
| Expectancy diff 4h | 79.6 bps | YES | Larger per-move bps on wider 4h targets |
| Median vol context ratios | 0.986–1.024 | YES | All near 1.0 — excellent control matching |
| Event unfinished fraction | 0.0 (all domains) | YES | Analysis set spans multiple years; no events reach the end |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Regime-cluster bootstrap | Clusters (regime_id) are independent | YES | Same-regime controls make clusters exact; cross-cluster independence by construction |
| Stratified paired permutation | Event/control exchangeability under null | YES | Within matched set, event slot reassigned uniformly among completed moves; preserves observed denominators |
| Instrument-averaged estimator | Equal-weight per instrument | YES | Explicitly computed; 4/4 instruments reportable in all domains |
| Volatility-context diagnostic | Control faces comparable target difficulty | YES | All median ratios within [0.5, 2.0]; no domain confounded |

## Results Plausibility

All three domains show large positive rate differences (22–26pp) with CIs well above 0 and aligned positive expectancy differences — consistent with EXP-021's fixed-horizon results but with a much stronger lifetime signal. The monotonic increase in expectancy from 5m (6.5 bps) through 1h (27 bps) to 4h (79.6 bps) is plausible: wider targets at longer domains yield larger per-move bps when events resolve favorably. The close-to-1.0 volatility-context ratios indicate matched controls face comparable target difficulty.

Total event counts, control counts, and diagnostic counters all pass eyeball plausibility. The 4604 `invalid_target_events` (events whose targets don't satisfy `favorable_bps > 0 and adverse_bps < 0`) are expected and explicitly counted — they do not bias the sample because the direction-mismatch is a geometrically empty target definition, not a selection effect.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 3/3 tests, 5/5 plots, 0/1 new modules
- Holdout exclusion verified: YES
- Output set complete: `lifetime_observations.csv` (85,816 rows), `lifetime_completion_summary.csv` (96 rows), `domain_lifetime_tests.csv` (4 rows), `control_lifetime_diagnostics.csv` (24 rows), `run_metadata.json`, 5 plot PNGs — all present

## Issues

### Info

1. **Large invalid_target_events count (4604)**
   - Description: 4,604 of the EXP-020 events have targets where `favorable_bps ≤ 0` or `adverse_bps ≥ 0` — geometrically empty target definitions. These are counted and excluded from analysis. The count is high but proportional to the total event pool. The code correctly skips them with explicit counter tracking. No bias introduced.
   - No action required.

2. **Zero tie_completions**
   - Description: The geometrically-impossible case of a single completed close simultaneously crossing both favorable and adverse targets (rounded-price tie) was never observed. This is expected given real price resolution and does not indicate a logic gap.

## Re-Audit Requirements

None.
