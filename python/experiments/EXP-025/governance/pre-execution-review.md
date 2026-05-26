# Pre-Execution Governance Review — EXP-025

**Reviewer**: Research Pipeline  
**Date**: 2026-05-26  
**Artifacts reviewed**:
- `python/experiments/EXP-025/scope.md`
- `python/experiments/EXP-025/analysis-plan.md`
- `python/experiments/EXP-025/code/run_experiment.py`

---

## Scope Review

| Check | Status | Notes |
|-------|--------|-------|
| Single falsifiable question | PASS | "Is the fixed 1:2 risk/reward target justified versus alternatives?" |
| Success/failure criteria concrete | PASS | FOR now requires positive 2R superiority evidence, no domination, and valid scoped comparators on ≥3 instruments; AGAINST: dominated on ≥2 comparable instruments; INCONCLUSIVE: insufficient sample/comparator coverage or no positive justification |
| Data views defined | PASS | 1-minute time bars, real OHLC prices explicitly stated |
| Instruments defined | PASS | EURUSD, XAUUSD, BTCUSD, USTEC |
| Global holdout exclusion stated | PASS | Final 30% explicitly excluded in scope |
| Real-price outcome rule stated | PASS | "All outcomes use real time-bar OHLC prices aligned by timestamp" |
| Complexity budget realistic | PASS | 3 tests, 5 plots, 2 modules — within budget |
| No scope creep | PASS | Exit experiment only; no new entry filters or stop retuning |

---

## Analysis Plan Review

| Check | Status | Notes |
|-------|--------|-------|
| Method justification provided | PASS | Each step has "why this method" and alternatives considered |
| Assumptions stated | PASS | Temporal ordering, same-bar ambiguity handling documented |
| Bootstrap non-parametric | PASS | Distribution-free; 10k reps, seed=42 |
| Interpretation guide predeclared | PASS | FOR/AGAINST/INCONCLUSIVE criteria fixed before results; post-review code uses `superiority_v2` to avoid treating non-dominance as support |
| Budget compliance | PASS | 3 statistical tests (bootstrap per variant/instrument), 5 plots |

---

## Code Review

### Organization
| Check | Status | Notes |
|-------|--------|-------|
| Import order correct | PASS | imports → path setup → polars → ict_timebar → constants → helpers |
| No loading at import time | PASS | All loads inside `run_experiment()` |
| run_experiment() structure correct | PASS | mkdir → load → compute → write (plots inside write_outputs) |

### Holdout Exclusion
| Check | Status | Notes |
|-------|--------|-------|
| load_analysis_timebars used | PASS | Loads first 70% only via ict_timebar |
| EXP-024 input already analysis-set | PASS | entry_timing_outcomes.csv was produced from analysis set |
| No holdout access path | PASS | No global file reads outside analysis-set sources |

### Real-Price Discipline
| Check | Status | Notes |
|-------|--------|-------|
| Outcomes from OHLC prices | PASS | simulate_all_exits walks time-bar High/Low/Close arrays |
| No HA/Renko prices | PASS | No synthetic chart prices in scope or code |
| Liquidity levels from analysis bars | PASS | load_instrument_data uses load_analysis_timebars |

### Code Quality
| Check | Status | Notes |
|-------|--------|-------|
| Type hints on all public functions | PASS | All 10 public functions have annotated signatures |
| Docstrings with Parameters/Returns | PASS | All public functions documented |
| NaN handling explicit | PASS | np.isfinite() guards throughout; dropna() before aggregation |
| Empty input handling | PASS | n_bars == 0 → NaN; empty arrays → NaN in bootstrap |
| LOGGER not print() in helpers | PASS | print() only in main() and run_experiment() |
| Plotting receives pre-computed data | PASS | write_outputs passes outcomes/summary/bootstrap — no reloading |
| No magic numbers undocumented | PASS | All thresholds (TRAIN_FLOOR=100, TEST_FLOOR=50, PLOT_R_CAP=6.0) are named constants |

### Plan Compliance
| Check | Status | Notes |
|-------|--------|-------|
| All 6 exit variants implemented | PASS | 1R, 1.5R, 2R, 3R, TimeStop60, NearestLiquidity; NYDate normalization added so computed liquidity levels can join prerequisite entry rows |
| Single bar walk for all exits | PASS | simulate_all_exits walks once, updates all targets per bar |
| Bootstrap 2R vs alternatives | PASS | run_bootstrap_comparisons tests each alternative |
| 5 plots produced | PASS | distribution, expectancy intervals, hit rate, hold time, heatmap |
| Output files match plan | PASS | exit_outcomes.csv, exit_summary.csv, bootstrap_comparison.csv, results.json, numerical_summary.txt |

### Checkpoint Alignment
| Check | Status | Notes |
|-------|--------|-------|
| Phase 003 ICT validation objective | PASS | Exit rule justification is explicitly scoped in Phase 003 |

---

## Summary

Post-review revision: the verdict logic was tightened after adversarial review. The script now uses `superiority_v2`, requires positive evidence that 2R beats at least one comparator, requires no comparator to dominate 2R, requires scoped comparator coverage, and normalizes NYDate values before joining computed liquidity targets.

All governance constraints pass for the revised pre-execution code. Existing result files predate this revision and must be regenerated before audit, interpretation, report, and post-experiment governance.

VERDICT: APPROVE
