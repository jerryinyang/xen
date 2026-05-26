# Pre-Execution Governance Review — EXP-026

**Reviewer**: Research Pipeline  
**Date**: 2026-05-26  
**Artifacts reviewed**:
- `python/experiments/EXP-026/scope.md`
- `python/experiments/EXP-026/analysis-plan.md`
- `python/experiments/EXP-026/code/run_experiment.py`

---

## Scope Review

| Check | Status | Notes |
|-------|--------|-------|
| Single falsifiable question | PASS | "Which validated components contribute net value when combined incrementally?" |
| Success/failure criteria concrete | PASS | Candidate selection now requires eligible components with positive test MeanDiff and CI_Lo > 0 on ≥3 instruments; otherwise manifest is marked ineligible |
| Data views defined | PASS | 1-minute time bars plus prior EXP result CSVs |
| Global holdout exclusion stated | PASS | Final 30% explicitly excluded; prior EXP CSVs were analysis-set only |
| Real-price outcome rule stated | PASS | Returns from prior experiments computed on real prices |
| Chain order fixed | PASS | Predeclared order specified; no reordering after results inspection |
| Complexity budget | PASS | 3 tests, 4 plots, 2 modules — within budget |

---

## Analysis Plan Review

| Check | Status | Notes |
|-------|--------|-------|
| Method justification provided | PASS | Each chain step documents why incremental ablation is the right approach |
| Eligibility criteria from prior verdicts | PASS | Components classified from completed EXP-015–025 outputs; refuted components remain negative controls and are not eligible for candidate selection |
| Bootstrap non-parametric | PASS | 10k reps, seed=42 |
| Interpretation guide predeclared | PASS | Selection criteria fixed before execution |

---

## Code Review

### Organization
| Check | Status | Notes |
|-------|--------|-------|
| Import order correct | PASS | imports → path setup → ict_timebar → constants → eligibility table → helpers |
| No loading at import time | PASS | All loads in run_experiment() or explicitly invoked helpers |
| run_experiment() structure | PASS | mkdir → load eligibility → load each step → aggregate → bootstrap → manifest → write |

### Holdout Exclusion
| Check | Status | Notes |
|-------|--------|-------|
| Prior EXP CSVs are analysis-set only | PASS | All source files (EXP-015 through EXP-025) produced from analysis set |
| EXP-025 optional inclusion | PASS | Handled gracefully with None return if file absent |
| No raw bar loading | PASS | EXP-026 does not load time bars; uses only prior experiment result files |

### Real-Price Discipline
| Check | Status | Notes |
|-------|--------|-------|
| No new outcome computation | PASS | All Return_R_60m values inherited from prior experiments (computed on real prices) |
| Proxy expectancy documented | PASS | 2*MeanHit1R-1 clearly labelled as proxy for steps 1-3 |

### Code Quality
| Check | Status | Notes |
|-------|--------|-------|
| Type hints on all public functions | PASS | All public functions annotated |
| Docstrings with Parameters/Returns | PASS | All major functions documented |
| NaN handling explicit | PASS | fillna(False) for join flags; np.isfinite guards in bootstrap |
| Empty input handling | PASS | Empty bootstrap_marginal → "No bootstrap data" in plot |
| LOGGER not print() in helpers | PASS | print() only in main() and run_experiment() |
| Plotting receives pre-computed data | PASS | All plot functions take pre-computed DataFrames; no file reloading in plots |

### Plan Compliance
| Check | Status | Notes |
|-------|--------|-------|
| 8-step chain implemented | PASS | Steps 1-7 mandatory; step 8 conditional on EXP-025 availability |
| Sub-chain A (steps 1-3) uses proxy | PASS | Hit1R_60m → proxy expectancy correctly labelled |
| Sub-chain B (steps 4-7) uses Return_R | PASS | Return_R_60m available and used for steps 4-7 |
| Bootstrap marginal for adjacent B steps | PASS | compute_marginal_bootstrap covers pairs (4,5), (5,6), (6,7), (7,8) |
| Model manifest written | PASS | model_manifest.json with selected_components, exit_variant, stop_rule, cost_scenario, candidate_eligible, source_verdict, and selection_rule_version |
| Minimum viable chain fallback | PASS | If no optional component meets the positive lower-CI rule, no eligible full-model candidate is selected |
| 4 plots produced | PASS | waterfall, marginal expectancy, retention, contribution heatmap |
| Output files match plan | PASS | component_eligibility.csv, chain_steps.csv, bootstrap_marginal.csv, model_manifest.json, results.json, numerical_summary.txt |

### Checkpoint Alignment
| Check | Status | Notes |
|-------|--------|-------|
| Phase 003 ablation gate | PASS | EXP-026 is the predeclared ablation step before full-model test |

---

## Summary

Post-review revision: candidate selection was tightened after adversarial review. The script now enforces nested event-chain identity for execution steps, keeps refuted components as negative controls rather than candidate rules, requires the current EXP-025 `superiority_v2` verdict contract before selecting `RiskModel_2R`, and fails closed with an ineligible manifest when the ablation gate is not met. Existing result files predate this revision and must be regenerated before downstream use.

VERDICT: APPROVE
