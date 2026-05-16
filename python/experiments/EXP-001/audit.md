# Audit Report: Experiment EXP-001

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 2
- **Info Notes**: 3

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `run_experiment.py` | Correctness | PASS | All formulas, joins, and lag logic correct. Ghost-rate dispatch, entropy computation, bootstrap, and threshold evaluation implement the analysis plan faithfully. |
| `run_experiment.py` | Edge cases | PASS | Empty DataFrames handled in ghost-rate, entropy, bars-per-day, and bootstrap functions. Division-by-zero guarded in `relative_change` and `entropy_headroom_capture`. |
| `run_experiment.py` | Type hints | PASS | All public functions have type hints on parameters and return values. |
| `run_experiment.py` | NaN handling | PASS | Explicit handling: `fill_null` on ghost masks, `drop_nulls` on diffs, `np.isfinite` guards in threshold logic, `np.nan` returned for undefined cases. |
| `run_experiment.py` | Holdout exclusion | PASS | `load_analysis_timebar_data` lazily scans matching parquet files, sorts by `CloseTime`, computes `int(total_rows * 0.7)` cutoff, and slices before `collect()`. No holdout rows materialized. |
| `run_experiment.py` | Loader ordering | PASS | Lazy scan → sort → slice → collect. No full-dataset `read_parquet`. |
| `run_experiment.py` | Memory/performance | PASS | Movement data sampled to max 50,000 rows for boxplot. Daily counts aggregated before pandas conversion. No repeated heavy loads for plotting. |
| `run_experiment.py` | Logging/output | PASS | Concise `print()` progress per instrument and per output file. Failure traceable via `failure_records`. |
| `run_experiment.py` | Organization/import side effects | PASS | Imports → path setup → constants → I/O helpers → computation helpers → plotting helpers → orchestration → `main()`. `PLOTS_DIR`/`RESULTS_DIR` created in `main()` only. |
| `run_experiment.py` | Plot data reuse | PASS | All four plots use data accumulated during the analysis pass (`summary_df`, `movement_df`, `daily_counts_eurusd`). No regeneration. |
| `run_experiment.py` | Docstrings | PASS | All public functions have docstrings with Parameters and Returns sections. |

## Numerical Validation

### Spot Checks

**EURUSD Time ghost rate**: `summary_metrics.csv` reports 0.0899. With `min_tick` derived from consecutive close differences, ~9% of bars having near-zero range or near-zero close-to-close movement is plausible for a forex major pair on 1-minute bars.

**EURUSD LineBreak3 ghost rate = 0.0**: Line Break only emits confirmed lines when price moves beyond prior levels. Zero ghosts is expected because every emitted line represents a confirmed price movement by construction.

**EURUSD LineBreak3 entropy**: 0.9998 bits (max binary = 1.0). Direction is nearly perfectly balanced between up/down lines, consistent with Line Break's symmetry.

**EURUSD LineBreak3 threshold evaluation**: Ghost reduction = 1.0 (0.0899 → 0.0), entropy increase = 0.0056 (> 0.005 threshold), headroom capture = 0.969 (> 0.50). All three thresholds met — matches `threshold_evaluation.csv` row 1.

**XAUUSD LineBreak3 threshold evaluation**: Entropy increase = -0.0000857 (negative, fails practical threshold). Only EURUSD meets all three thresholds for LineBreak3. Matches `threshold_evaluation.csv` rows 2-4.

**Bootstrap sanity**: LineBreak3 vs Time entropy CI = [-0.0003, 0.0042] includes zero, consistent with mixed instrument-level effects (1 positive on EURUSD, negative on 3 others). Renko vs Time entropy CI = [0.0002, 0.0043] excludes zero but mean 0.0016 < 0.005 practical threshold.

**Train/test split**: EURUSD Time 872,242 × 0.7 = 610,569 train, 261,673 test. Matches `summary_metrics.csv`.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Direction | {+1, -1} | Computed from Close/Open, cast Int32 | YES |
| GhostRate | [0, 1] | [0.0, 0.0899] | YES |
| DirectionalEntropy | [0, 1] bits | [0.9942, 0.99998] | YES |
| BarsPerDay | > 0 | [147.4, 1212.7] | YES |
| MedianAbsMovement | > 0 | [5e-05, 46.8] | YES |
| CV by tercile | ≥ 0 | [0.28, 3.32] | YES |
| SourceCloseTime | Monotonically increasing | Verified by generator design | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| Bootstrap N | 10,000 | YES | Standard for percentile CI |
| Bootstrap seed | 42 | YES | Deterministic, documented in manifest |
| N_Instruments | 4 | YES | All four instruments produced valid data |
| Ghost-rate reduction CI | All exclude zero | YES | Event charts consistently have lower ghost rates |
| Entropy increase CI (Renko) | [0.0002, 0.0043] | YES | Small but consistent positive effect |
| Entropy increase CI (LB3) | [-0.0003, 0.0042] | YES | Includes zero, consistent with mixed effects |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Holdout split | Chronological, 70% cutoff | YES | `load_analysis_timebar_data` sorts by CloseTime, slices first 70% |
| Ghost-rate definition | min_tick proxy from consecutive closes | YES | `compute_min_tick_proxy` finds minimum positive diff; robust for all instruments |
| Event ghost denominator | Distinct SourceCloseTime only | YES | `compute_ghost_rate_event` deduplicates before computing rate |
| Directional entropy | Shannon entropy on +1/-1 directions | YES | `directional_entropy` uses value_counts, handles edge cases |
| Volatility terciles | Based on analysis set only | YES | `add_volatility_terciles` uses only analysis_set closes |
| Bootstrap | Descriptive, not inferential | YES | Treated as uncertainty estimate for 4 instrument units |
| Cross-chart alignment | By timestamp, not bar index | YES | `CloseTime` for Time/HA, `SourceCloseTime` for LB/Renko |

## Results Plausibility

All outputs are within expected domain ranges. Key patterns are sensible:
- Event charts (LineBreak, Renko) produce far fewer bars than time bars (compression factor 3-4x).
- Ghost rates are near-zero for event charts, non-zero for time bars.
- Directional entropy is near-maximum for all chart types (direction is roughly balanced).
- Heiken Ashi has identical bar count and ghost rate to time bars (1:1 mapping, real prices unchanged).
- Renko produces same-source duplicates (13% for EURUSD), handled correctly by distinct-source logic.
- The REFUTED verdict is numerically justified: only EURUSD meets all three thresholds for any primary event type.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 2 statistical comparisons (bootstrap + sign count) / 2 budgeted, 4 plots / 4 budgeted, 0 new reusable modules / 1 budgeted
- Holdout exclusion verified: YES
- Synthetic price discipline: YES — all movement metrics use `RealClose` or time-bar `Close`
- No strategy backtesting, no parameter optimization, no predictive modeling: YES

## Issues

### Critical

None.

### Warning

1. **`decide_hypothesis_verdict` exceeds ~30 line guideline**
   - File: `code/run_experiment.py`, lines 553-639 (87 lines)
   - Description: The verdict decision function is complex with nested conditionals for multiple chart types and criteria.
   - Impact: Readability and maintainability; no correctness impact.
   - Fix: Consider extracting per-chart-type evaluation into a helper function.

2. **No column projection on lazy scans**
   - File: `code/run_experiment.py`, line 167
   - Description: `pl.scan_parquet(matches).sort("CloseTime")` loads all 8 columns. For holdout exclusion only `CloseTime` is needed for the sort, but all columns are required for subsequent analysis so this is a minor concern.
   - Impact: Slightly higher memory during the sort/collect step. Acceptable for the dataset sizes observed (~13-22 MB files).
   - Fix: Could add `.select([...])` before `.collect()` if memory becomes a constraint.

### Info

1. **Bar density timeline limited to EURUSD** — Per analysis plan plot 4, only EURUSD is shown. This is by design and within scope.

2. **Ghost-rate definition uses `< min_tick` rather than literal zero** — This is a robust approximation noted in the pre-execution review. No action needed.

3. **`main()` function is ~150 lines** — Acceptable for an orchestration function that iterates over instruments and chart types. The complexity is structural, not algorithmic.

## Re-Audit Requirements

None. All checks pass. No revision required.
