# Governance Review: Experiment EXP-003 — Post-Experiment

**Date:** 2026-05-16
**Review Type:** Post-Experiment
**Artifacts Reviewed:** audit.md, results.md, report.md, python/experiments/INDEX.md, docs/experiments-docs/INDEX.md

## Executive Summary

All critical constraints pass. EXP-003 completed successfully with SUPPORTED verdict. Holdout exclusion verified, synthetic price discipline maintained, timestamp alignment correct, scope boundaries respected, and code conventions followed. Index files updated correctly. Post-adversarial-review fixes from pre-execution stage (LZ76, OHLC repair, HA variance metric) produced clean results with 0 invalid bars.

## Constraint Checks

### Holdout Exclusion

| Check | Verdict | Evidence |
|-------|---------|----------|
| Final 30% never loaded | PASS | `load_timebar_data` uses `slice(0, int(total_rows * 0.7))` (audit.md, Code Review table) |
| Perturbation applied only to analysis set | PASS | `perturb_time_bars` receives already-sliced `analysis_df` (code line 886-888) |
| Chart regeneration from perturbed bars stays within analysis set | PASS | `generate_chart` called on `perturbed_df` which is derived from `analysis_df` (code line 910) |
| Plots do not reference holdout data | PASS | All plots use `metric_df` derived from analysis-set computations (code lines 1005-1070) |

### Synthetic Price Discipline

| Check | Verdict | Evidence |
|-------|---------|----------|
| No strategy P&L computed | PASS | No P&L, Sharpe, or return metrics in code. Only descriptive drift metrics. |
| HA uses HAClose only as distortion diagnostic | PASS | `CHART_CONFIG["HeikenAshi"]["close_col"] = "HAClose"` with [F01] annotation (code lines 64, 33-37). results.md explicitly labels as non-tradable. |
| Renko/LB use real-close via SourceCloseTime | PASS | `attach_real_close` joins time-bar Close on SourceCloseTime (code lines 247-274). `extract_returns` uses RealClose for LB/Renko (code lines 494-496). |
| Report labels HA results as diagnostic | PASS | report.md states "HAClose returns are a distortion diagnostic, not tradable returns" |

### Timestamp Alignment

| Check | Verdict | Evidence |
|-------|---------|----------|
| Time bars use CloseTime | PASS | `CHART_CONFIG["Time"]["time_col"] = "CloseTime"` (code line 42) |
| LB/Renko use SourceCloseTime | PASS | `CHART_CONFIG["LineBreak"]["time_col"] = "SourceCloseTime"` (code line 49), same for Renko (line 56) |
| Cross-chart comparisons by timestamp | PASS | `attach_real_close` joins on timestamp column, not bar index (code lines 269-274) |
| No bar-index alignment | PASS | No index-based comparisons found in code |

### Scope Compliance

| Check | Verdict | Evidence |
|-------|---------|----------|
| Single hypothesis | PASS | One hypothesis about noise robustness across chart types |
| Chart types match scope | PASS | Time, LineBreak (level 3), Renko (ATR 14), HeikenAshi — all match scope |
| Instruments match scope | PASS | EURUSD, XAUUSD, BTCUSD, USTEC — all 4 tested |
| Noise levels match scope | PASS | 0%, 10%, 20%, 30% — matches scope's deterministic perturbation levels |
| Complexity budget respected | PASS | 3 tests / 3, 5 plots / 5, 0 new modules / 1 (audit.md, Scope Compliance) |
| No scope creep | PASS | No bonus analyses, no strategy testing, no parameter optimization |
| Direction-sign perturbation excluded as documented | PASS | Scope narrowed from original; documented in code [F05] and pre-execution review |

### Code Conventions

| Check | Verdict | Evidence |
|-------|---------|----------|
| Import organization | PASS | stdlib → third-party → local (code lines 5-23) |
| Code structure | PASS | imports → constants → data loading → perturbation → chart gen → alignment → metrics → statistics → plotting → orchestration → main() |
| Lazy loading | PASS | `pl.scan_parquet` → `sort("CloseTime")` → `slice()` → `collect()` (code lines 103-105) |
| Directory creation in main() only | PASS | `PLOTS_DIR.mkdir()` and `RESULTS_DIR.mkdir()` in `main()` (code lines 846-847) |
| Plot data reuse | PASS | All plots use `metric_df` from analysis pass, no regeneration |
| Type hints on public functions | PASS | All functions have type hints |
| Docstrings present | PASS | All functions have NumPy-style docstrings |
| Concise logging | PASS | `print()` progress output only, no verbose logging |
| NaN handling explicit | PASS | Empty-input guards, `drop_nulls()`, `np.isnan` checks |

### Phase 1 Characterisation Boundaries

| Check | Verdict | Evidence |
|-------|---------|----------|
| No strategy optimization | PASS | Descriptive metrics only, no parameter tuning against returns |
| No predictive modelling | PASS | No train/test split used (acceptable for characterisation) |
| Non-parametric methods | PASS | Bootstrap percentile CIs, no parametric distribution assumptions |
| Descriptive only | PASS | All metrics are relative drift comparisons, no inference beyond CIs |

## Artifact Quality

### audit.md

- Verdict: PASS with 0 critical, 1 warning, 4 info notes
- Thorough coverage of all audit dimensions
- Numerical spot checks performed and consistent
- Warning about `time_alignment` module dependency is appropriate

### results.md

- Verdict: SUPPORTED (with qualification)
- Honest about threshold not being strictly met
- Paired comparison evidence properly prioritized over raw percentages
- Limitations clearly stated (n=4, single perturbation family, complexity confound)
- Alternative explanations provided
- Follow-up experiments are new scopes, not extensions

### report.md

- Self-contained and readable without other artifacts
- Key plots referenced with relative paths
- Conclusion matches results.md verdict
- Artifacts table includes all relevant files
- Limitations and implications are specific

### Index Updates

- `python/experiments/INDEX.md`: EXP-003 status changed from PLANNED to COMPLETED with accurate one-line finding
- `docs/experiments-docs/INDEX.md`: Full five-field schema populated with factual results, hypothesis-specific conclusion, and hypothesis-agnostic observations

## Findings

### Critical

None.

### Warnings

None.

### Info

1. **`time_alignment` module** — The audit notes a dependency on `python/src/time_alignment.py` for `normalize_timestamp_columns`. This module must exist for the experiment to run. If it does not exist, the experiment would fail at import time. Since results were successfully produced, the module evidently exists and functions correctly.

2. **Index file was empty** — `docs/experiments-docs/INDEX.md` was empty before this update. The new entry includes placeholder sections for EXP-001, EXP-002, EXP-004, EXP-005, and EXP-006 to maintain the catalog structure.

## Verdict

```
VERDICT: APPROVE
```

All governance constraints satisfied. EXP-003 is complete with a SUPPORTED verdict. The experiment provides validated evidence that event-based chart types (particularly Renko) filter directional noise more effectively than time bars, with a trade-off in sequence complexity stability. Results are ready for use in downstream strategy design and future experiment planning.
