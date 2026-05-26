# Pre-Execution Governance Review — EXP-027

**Reviewer**: Research Pipeline  
**Date**: 2026-05-26  
**Artifacts reviewed**:
- `python/experiments/EXP-027/scope.md`
- `python/experiments/EXP-027/analysis-plan.md`
- `python/experiments/EXP-027/code/run_experiment.py`

---

## Scope Review

| Check | Status | Notes |
|-------|--------|-------|
| Single falsifiable question | PASS | "Does the predeclared full-model variant survive analysis-set testing after costs?" |
| All five survival criteria predeclared | PASS | Positive median expectancy, trade count floors, instrument diversity, no dominance, train/test stability |
| Frozen model manifest required | PASS | Raises FileNotFoundError if EXP-026 manifest is absent; writes INCONCLUSIVE if the manifest lacks a current eligible-candidate contract |
| Global holdout exclusion stated | PASS | Analysis-set only; events from prior experiments |
| Real-price outcome rule stated | PASS | "All outcomes use real time-bar OHLC prices aligned by timestamp" |
| Cost scenarios from EXP-012 | PASS | LIGHT_COST_PROXY as primary; all EXP-012 scenarios loaded |
| Complexity budget | PASS | 3 tests, 5 plots, 2 modules — within budget |
| No parameter tuning | PASS | Manifest is frozen before code execution |

---

## Analysis Plan Review

| Check | Status | Notes |
|-------|--------|-------|
| Method justification provided | PASS | Three-step plan (manifest check, simulation, criteria) documented |
| Manifest compliance before execution | PASS | Validation against MANIFEST_REQUIRED_FIELDS at load time plus `candidate_eligible` and `positive_lower_ci_v2` gate before trade simulation |
| Bootstrap non-parametric | PASS | 10k reps, seed=42 per instrument and overall |
| Interpretation guide predeclared | PASS | FOR requires all 5 criteria; AGAINST if any fail; INCONCLUSIVE if count floor not met |

---

## Code Review

### Organization
| Check | Status | Notes |
|-------|--------|-------|
| Import order correct | PASS | imports → path setup → constants → helpers |
| No loading at import time | PASS | All loads inside run_experiment() or invoked helpers |
| run_experiment() structure | PASS | mkdir → load manifest → load scenarios → load events → cost haircut → aggregate → bootstrap → criteria → load baseline → write |

### Holdout Exclusion
| Check | Status | Notes |
|-------|--------|-------|
| Event source from analysis set only | PASS | EXP-025/EXP-024/EXP-018 result files are analysis-set products |
| load_events_from_manifest respects holdout | PASS | Reads from prior experiment CSVs, not raw bars |
| EXP-012 cost scenarios loaded correctly | PASS | cost_proxy_scenarios.json read from results dir |

### Real-Price Discipline
| Check | Status | Notes |
|-------|--------|-------|
| 2R gross return computation | PASS | _compute_2r_gross_return uses Hit2R_60m + MAE_R_60m + Return_R_60m from real prices |
| EXP-025 2R_R column used when available | PASS | Prefers EXP-025 exit_outcomes (bar-walked from OHLC) |
| No HA/Renko prices | PASS | Not in scope |

### Code Quality
| Check | Status | Notes |
|-------|--------|-------|
| Type hints on all public functions | PASS | All public functions annotated |
| Docstrings with Parameters/Returns | PASS | All major functions documented |
| NaN handling explicit | PASS | np.isfinite guards; pd.to_numeric errors="coerce" throughout |
| Empty input handling | PASS | Empty DataFrames handled in criteria evaluation |
| LOGGER not print() in helpers | PASS | print() only in main() and run_experiment() |
| Plotting receives pre-computed data | PASS | load_displacement_baseline() called in run_experiment(), not inside plot function |
| No repeated heavy loads for plotting | PASS | Baseline loaded once; passed to write_outputs |

### Plan Compliance
| Check | Status | Notes |
|-------|--------|-------|
| Frozen manifest validated | PASS | MANIFEST_REQUIRED_FIELDS check at load; stale or ineligible manifests stop as INCONCLUSIVE before event loading |
| Event source priority: EXP-025 → EXP-024 → EXP-018 | PASS | load_events_from_manifest fallback chain implemented |
| Cost haircut formula correct | PASS | total_bps * Entry / (10000 * Risk1R) as specified |
| 5 survival criteria evaluated | PASS | All 5 criteria with PASS/FAIL and reason strings |
| model_verdict.json written | PASS | For EXP-028 to read |
| 5 plots produced | PASS | trade count, R distribution, expectancy intervals, contribution, baseline comparison |
| Output files match plan | PASS | trade_table.csv, performance_summary.csv, bootstrap_result.csv, results.json, model_verdict.json, numerical_summary.txt |

### Checkpoint Alignment
| Check | Status | Notes |
|-------|--------|-------|
| Phase 003 full-model test gate | PASS | EXP-027 is the predeclared gated full-model test |

---

## Summary

One warning was identified and fixed during review: `plot_baseline_comparison` originally loaded EXP-018 data inside the plotting function (violating the "plotting functions never reload" convention). This was corrected by extracting `load_displacement_baseline()` as a separate I/O helper called in `run_experiment()`, with pre-computed means passed to the plot function.

All constraints now pass.

Post-review revision: EXP-027 now fails closed when EXP-026 does not provide a current eligible full-model manifest. This prevents a stale or negative-control ablation manifest from being treated as an approved full-model candidate.

VERDICT: APPROVE
