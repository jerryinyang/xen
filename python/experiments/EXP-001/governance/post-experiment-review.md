# Post-Experiment Governance Review: EXP-001

## Artifacts Reviewed

- `python/experiments/EXP-001/scope.md`
- `python/experiments/EXP-001/analysis-plan.md`
- `python/experiments/EXP-001/code/run_experiment.py`
- `python/experiments/EXP-001/audit.md`
- `python/experiments/EXP-001/results.md`
- `python/experiments/EXP-001/report.md`
- `python/experiments/EXP-001/results/` (all CSV and JSON files)
- `python/experiments/EXP-001/plots/` (all 4 PNG files)
- `python/experiments/INDEX.md` (updated)
- `docs/experiments-docs/INDEX.md` (created)

## Governance Checks Applied

### Core Constraints

| Constraint | Status | Notes |
|---|---|---|
| Simplicity Over Complexity | PASS | Descriptive metrics, effect sizes, sign counts, and descriptive bootstrap intervals. No unnecessary modeling. |
| No Academic-Finance Pitfalls | PASS | Non-parametric bootstrap; no normality/stationarity/i.i.d. assumptions. Bootstrap treated as descriptive, not inferential. |
| Strict Experiment Scoping | PASS | Single hypothesis answered. No scope creep. Complexity budget respected (2 tests, 4 plots, 0 new reusable modules). |
| Framework Principles | PASS | Data-driven, non-parametric, synthetic price discipline, timestamp alignment. |
| OOS Holdout Rule | PASS | Lazy scan → sort by CloseTime → slice first 70% → collect. No holdout rows materialized, inspected, or plotted. Verified in audit.md. |
| Look-Ahead Bias Prevention | PASS | Generators called on pre-holdout analysis set. Cross-chart alignment by CloseTime/SourceCloseTime, never bar index. |
| Synthetic Price Discipline | PASS | Heiken Ashi metrics use RealClose. Event charts join RealClose via SourceCloseTime. No strategy P&L computed. HAClose never used for returns. |

### Artifact-Specific Checks

**Audit Report (audit.md)**
- Thoroughness: PASS — covers correctness, edge cases, type safety, NaN handling, holdout exclusion, synthetic price discipline, timestamp alignment, numerical spot checks.
- Evidence: PASS — specific line numbers, value ranges, and code excerpts provided.
- Severity classification: PASS — 0 Critical, 2 Warning, 3 Info. Appropriate distribution.
- Numerical validation: PASS — spot checks on ghost rates, entropy, train/test split, bootstrap CIs all verified.

**Results Interpretation (results.md)**
- Honest reporting: PASS — clearly states REFUTED verdict with supporting evidence. Does not inflate weak findings.
- Uncertainty acknowledged: PASS — bootstrap CIs reported, limitations section covers instrument sample size, entropy ceiling, and descriptive-only bootstrap framing.
- No overreaching: PASS — does not generalise EURUSD-specific findings to all instruments.
- Verdict supported: PASS — REFUTED conclusion matches the pre-defined interpretation guide and the code's hypothesis_verdict.csv output.
- Next steps reasonable: PASS — suggests new experiments (multi-state entropy, higher-timeframe baseline), not scope extensions.

**Final Report (report.md)**
- Self-contained: PASS — includes hypothesis, method, findings, conclusion, limitations, and artifact links.
- Key visualisations: PASS — references 2 of 4 plots that materially support findings.
- Honest about limitations: PASS — dedicated limitations section.
- Artifacts linked: PASS — all relative paths correct.

**Index Updates**
- `python/experiments/INDEX.md`: PASS — EXP-001 status changed from PLANNED to COMPLETED with accurate one-line finding.
- `docs/experiments-docs/INDEX.md`: PASS — Created with all five required fields (Hypothesis Tests, Scope, Results/Observations, Hypothesis-Specific Conclusion, Hypothesis-Agnostic Observations).

### Phase 1 Characterisation Boundaries

| Boundary | Status | Notes |
|---|---|---|
| No strategy backtesting | PASS | No signals, entries, exits, or P&L computed. |
| No parameter optimization | PASS | LineBreak levels 3/5 and Renko ATR 14 are fixed research decisions, not tuned. |
| No predictive modeling | PASS | Descriptive comparison only. |
| Characterisation only | PASS | Metrics describe chart-type properties, not trading performance. |

### Code Conventions

| Convention | Status | Notes |
|---|---|---|
| Import organization | PASS | stdlib → third-party → local, grouped correctly. |
| Lazy loading | PASS | scan_parquet → sort → slice → collect pattern. |
| Plot memory bounds | PASS | Movement sampled to 50,000; daily counts aggregated. |
| Concise logging | PASS | Print-based progress output, traceable failures. |
| Duplicate-source handling | PASS | Event ghost denominators exclude same-SourceCloseTime rows; distinct-source sensitivity emitted. |
| Zero-baseline handling | PASS | Ghost reduction uses absolute difference; relative_change guards against zero denominator. |
| Type hints and docstrings | PASS | All public functions covered. |

## Issues Found

### Critical

None.

### Warning

None.

### Info

1. **`decide_hypothesis_verdict` function length** (audit Warning, line 553-639): 87 lines exceeds the ~30 line guideline. Does not affect correctness. Could be refactored in a future cleanup pass.
2. **No column projection on lazy scans** (audit Warning, line 167): All 8 columns loaded when only a subset is needed for holdout slicing. Minor memory impact for current file sizes (~13-22 MB).

## Verdict Assessment

The REFUTED verdict is numerically and logically justified:
- Pre-defined success criteria: >= 3 instruments meet all three thresholds for a primary event type.
- Actual result: 1 instrument (EURUSD) meets all thresholds for LineBreak3 and Renko.
- The "evidence against" criterion (fewer than 2 instruments meet thresholds for every primary event type) is satisfied: 0 instruments meet thresholds for both LineBreak3 and Renko simultaneously.
- Bootstrap summaries are consistent: LineBreak3 entropy CI includes zero; Renko entropy mean below practical threshold.

No goalpost movement detected. The interpretation in results.md and report.md faithfully reflects the pre-defined interpretation guide from analysis-plan.md.

---

VERDICT: APPROVE

All governance checks pass. No Critical or Warning issues. The experiment is complete with a defensible REFUTED verdict. Artifacts are self-consistent, index files are updated, and the findings are ready for Phase 2 planning reference.
