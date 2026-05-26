# Pre-Execution Governance Review — EXP-028

**Reviewer**: Research Pipeline  
**Date**: 2026-05-26  
**Artifacts reviewed**:
- `python/experiments/EXP-028/scope.md`
- `python/experiments/EXP-028/analysis-plan.md`
- `python/experiments/EXP-028/code/run_experiment.py`

---

## Scope Review

| Check | Status | Notes |
|-------|--------|-------|
| Single falsifiable question | PASS | "Does the candidate survive robustness and falsification checks?" |
| Success/failure criteria predeclared | PASS | 4 robustness criteria fixed; all must pass for FOR |
| Segments with < 30 trades = InsufficientSample | PASS | `Eligible` flag correctly applied; not treated as failures |
| ATR14 tercile calibrated on train only | PASS | `compute_atr14_tercile_boundaries` filters train trades before computing percentiles |
| Global holdout exclusion stated | PASS | EXP-027 trade_table.csv is analysis-set only; bars loaded via load_analysis_timebars |
| Real-price discipline stated | PASS | Delay re-walk uses time-bar OHLC arrays |
| EXP-012 cost scenarios used | PASS | Cost stress applies all three EXP-012 scenarios |
| Early exit if EXP-027 not eligible | PASS | Writes only the early-inconclusive contract (`results.json`, `numerical_summary.txt`) and returns cleanly |

---

## Analysis Plan Review

| Check | Status | Notes |
|-------|--------|-------|
| Method justification provided | PASS | Three-step plan (segmentation, stress, verdict) documented |
| Delay stress documented | PASS | 0/1/2 bars with re-walk from delayed entry bar open |
| Bootstrap not required here | INFO | No bootstrap specified in plan; deterministic segment means used |
| Interpretation guide predeclared | PASS | FOR requires all 4 criteria; no post-hoc threshold adjustment |

---

## Code Review

### Organization
| Check | Status | Notes |
|-------|--------|-------|
| Import order correct | PASS | imports → path setup → polars/ict_timebar → constants → helpers |
| No loading at import time | PASS | All loads inside run_experiment() or invoked helpers |
| run_experiment() structure | PASS | Early-exit check → mkdir → load bars → ATR14 → segment → delay stress → cost stress → verdict → write |

### Holdout Exclusion
| Check | Status | Notes |
|-------|--------|-------|
| load_analysis_timebars for bars | PASS | Returns only first 70% of chronological data |
| EXP-027 trade_table.csv is analysis-set | PASS | Written by EXP-027 from analysis-set events only |
| ATR14 tercile boundaries from train only | PASS | compute_atr14_tercile_boundaries filters Segment=="Train" before percentile computation |

### Look-Ahead Bias
| Check | Status | Notes |
|-------|--------|-------|
| ATR14Prior is prior-period ATR | PASS | add_bar_diagnostics shifts by 1: ATR14Prior = rolling_mean.shift(1) |
| Daily ATR14 joined by NYDate | PASS | mean ATR14Prior per date; joined to trades by (Instrument, NYDate) |
| Delay stress walks from delayed entry | PASS | _walk_2r_outcome starts from delayed_close_ns (after entry bar closes) |

### Real-Price Discipline
| Check | Status | Notes |
|-------|--------|-------|
| Delay stress uses time-bar OHLC | PASS | highs/lows/closes/open arrays from analysis bars |
| Cost stress applies to EXP-027 gross R | PASS | GrossReturn_R from trade_table; no price recomputation in cost stress |

### Code Quality
| Check | Status | Notes |
|-------|--------|-------|
| Type hints on all public functions | PASS | All major public functions annotated |
| Docstrings with Parameters/Returns | PASS | All non-trivial functions documented |
| NaN handling explicit | PASS | dropna(), pd.isna() guards, np.isfinite() throughout |
| Empty input handling | PASS | Empty DataFrame checks before plots; graceful fallbacks in verdict |
| LOGGER not print() in helpers | PASS | print() only in main() and run_experiment() |
| Plotting receives pre-computed DataFrames | PASS | All plot functions take DataFrames computed in run_experiment() |
| No magic numbers | PASS | MIN_SEGMENT_TRADES=30, MIN_POSITIVE_SEGMENT_FRACTION=2/3 are named constants |

### Plan Compliance
| Check | Status | Notes |
|-------|--------|-------|
| Segment types implemented | PASS | InstrumentSegment, Year, Year_Segment, ATR14Tercile, ATR14Tercile_Segment |
| Execution delay 0/1/2 implemented | PASS | compute_delay_stress iterates delays |
| EXP-012 cost scenarios applied | PASS | compute_cost_stress applies all scenarios |
| 4 robustness criteria evaluated | PASS | All criteria with reason strings |
| 5 plots produced | PASS | segment heatmap, delay stress, cost stress, year contribution, positive share |
| Output files match plan | PASS | Full robustness path writes segment_results.csv, delay_stress.csv, cost_stress.csv, robustness_summary.csv, results.json, numerical_summary.txt; early-inconclusive path writes only results.json and numerical_summary.txt |

### Checkpoint Alignment
| Check | Status | Notes |
|-------|--------|-------|
| Phase 003 falsification gate | PASS | EXP-028 is the predeclared robustness/falsification step |

---

## Summary

No critical issues. One minor style note: `compute_segment_results` uses a closure (`_agg`) that captures `net_col` from the outer scope — this is functionally correct and a standard Python pattern. The early-exit path for INCONCLUSIVE/AGAINST EXP-027 correctly short-circuits before creating plot files and records that the full robustness outputs are not expected on that path.

All constraints pass.

VERDICT: APPROVE
