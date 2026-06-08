VERDICT: APPROVE

# Post-Experiment Governance Review: EXP-025

**Experiment:** EXP-025 — AVWAP Line Support/Resistance Direct Test
**Review date:** 2026-06-08
**Reviewed artifacts:**

- `python/experiments/EXP-025/scope.md`
- `python/experiments/EXP-025/analysis-plan.md`
- `python/experiments/EXP-025/code/run_experiment.py`
- `python/experiments/EXP-025/results/`
- `python/experiments/EXP-025/plots/`
- `python/experiments/EXP-025/audit.md`
- `python/experiments/EXP-025/results.md`
- `python/experiments/EXP-025/report.md`
- `python/experiments/EXP-025/governance/pre-execution-review.md`
- `python/experiments/INDEX.md`
- `docs/experiments-docs/INDEX.md`
- `docs/experiments-docs/checkpoints/2026-06-08-005-avwap-exit-and-branch-exploration/design.md`
- `.agents/skills/research-pipeline/references/governance-constraints.md`

## Decision

APPROVED. All post-experiment governance checks pass. No Critical or Warning issues remain. EXP-025 is complete.

## Governance Checks

### Audit Report

| Check | Result | Details |
|-------|--------|---------|
| Thoroughness | PASS | Correctness, edge cases, type safety, NaN handling, holdout exclusion, look-ahead bias, synthetic-price discipline all checked. |
| Evidence specificity | PASS | Spot-check with observation-row calculation (line 2 of observations CSV), line-number references for warnings. |
| Severity classification | PASS | 0 Critical, 2 Warning, 6 Info — correctly calibrated. No over- or under-classification. |
| Numerical validation | PASS | Spot-check matches code formula; range checks pass; statistical sanity table consistent with outputs. |
| Scope compliance | PASS | Confirms implementation matches analysis plan exactly; no scope deviations. |
| Real-price outcome | PASS | Verified use of real domain High/Low/Close; AVWAP is a reference line, not a trade price. |
| Timestamp alignment | PASS | Verified CloseTime ordering, trigger_time join validation, causal AVWAP replay. |

### Results Interpretation

| Check | Result | Details |
|-------|--------|---------|
| Honest reporting | PASS | Reports negative result opposite to hypothesis without spin. Acknowledges structural metric issue. |
| Uncertainty acknowledged | PASS | CIs for all effects; balance limitation on 1h/4h; small n caveat for 4h; BTCUSD 5m proximity imbalance flagged. |
| No overreaching | PASS | Verdict INCONCLUSIVE is correctly bounded. Does not claim extra significance from negative 5m result. |
| Verdict supported | PASS | INCONCLUSIVE justified: no Evidence FOR (all effects negative), Evidence AGAINST blocked by 4h CI spanning zero. |
| Next steps reasonable | PASS | Recommends registry entry only; no follow-up experiment to fix metric; requires operator governance for Stage B/C. |
| Real-price discipline | PASS | All metrics use real OHLC. No synthetic prices. |

### Final Report

| Check | Result | Details |
|-------|--------|---------|
| Self-contained | PASS | Question, hypothesis, method summary, results, plots, conclusion all present. Understandable with project context. |
| Key visualisations included | PASS | Domain effect forest (primary result) and score component decomposition (explains mechanism) embedded. |
| Honest about limitations | PASS | Six explicit limitations including the structural metric-design issue. |
| Artifacts linked | PASS | Full relative-path table linking scope, plan, code, audit, results, governance, plots. |
| Index updates | PASS | See below. |

### Index Updates

| Check | Result | Details |
|-------|--------|---------|
| `python/experiments/INDEX.md` | PASS | EXP-025 row inserted between EXP-024 and VAL-001 with correct status, finding, and date. |
| `docs/experiments-docs/INDEX.md` | PASS | EXP-025 section appended with full 5-field structure (Hypothesis, Scope, Results, Conclusion, Agnostic Observations). Checkpoint status updated. |

### Core Constraints

| Constraint | Result | Details |
|------------|--------|---------|
| Simplicity over complexity | PASS | Matched-control design with bootstrap CI and permutation test; no unnecessary complexity. |
| No academic-finance pitfalls | PASS | Non-parametric bootstrap and permutation; no normality/stationarity/i.i.d. assumptions. |
| Strict experiment scoping | PASS | Single question (direct line-S/R), defined boundaries, concrete criteria, budget respected (2/2 tests, 4/4 plots, 0/0 modules). |
| Framework principles | PASS | Data-driven, non-parametric, real-price discipline, timestamp alignment by CloseTime. |
| OOS holdout rule | PASS | `load_analysis_data()` applies first-70% chronological slice; domain reconstruction validates against EXP-020; all 12 cells PASS. Holdout never loaded. |
| Look-ahead bias prevention | PASS | Event-bar h=0 horizon; causal AVWAP replay per regime; controls selected without future return knowledge. |
| Real-price / synthetic-price discipline | PASS | Uses real domain High/Low/Close. No synthetic prices. No strategy P&L. |
| Safe optimization | PASS | Polars lazy scans; NumPy vectorized score computations (causally equivalent); plotting from computed records. No unsafe shortcuts. |

## Notes

- The experiment result (INCONCLUSIVE) is the correct classification under the predeclared criteria: the negative effects prevent Evidence FOR, while 4h's CI spanning zero prevents clean Evidence AGAINST.
- The structural confound between trigger definition and line-rejection signal is well documented and does not invalidate the experiment — it correctly identifies a limitation of the metric design for this specific question.
- Phase 005 Stage A now closes with three diagnostics: EXP-023 REFUTED, EXP-024 MIXED_OR_INCONCLUSIVE, EXP-025 INCONCLUSIVE. Stage B/C decisions require operator governance.
