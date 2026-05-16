# Post-Experiment Governance Review: EXP-002

## Artifacts Reviewed

- `python/experiments/EXP-002/audit.md` (PASS, 0 critical, 0 warnings, 3 info notes)
- `python/experiments/EXP-002/results.md` (REFUTED verdict)
- `python/experiments/EXP-002/report.md` (COMPLETED status)
- `python/experiments/EXP-002/results/` (7 result files)
- `python/experiments/EXP-002/plots/` (4 plots)
- `python/experiments/INDEX.md` (EXP-002 status updated to COMPLETED)
- `docs/experiments-docs/INDEX.md` (EXP-002 section updated with correct hypothesis and results)

## Governance Checks Applied

### Core Constraints

| Constraint | Status | Notes |
|---|---|---|
| No Holdout Leakage | PASS | Code uses `scan.slice(0, int(source_rows * 0.7))` before `.collect()`. Holdout is never materialized. Validation table confirms 70.00% analysis split on all instruments. |
| No Synthetic Price P&L | PASS | No strategy returns computed. Heiken Ashi uses `RealClose` for regime alignment. All metrics are descriptive (hybrid rate, lag), not P&L. |
| Timestamp Alignment Correct | PASS | Time bars use `CloseTime`; Line Break and Renko use `SourceCloseTime`. Regime joins are timestamp-based, never bar-index-based. |
| Scope Not Expanded | PASS | Only scoped chart types (Time, LineBreak3, Renko, HeikenAshi), instruments (EURUSD, XAUUSD, BTCUSD, USTEC), and parameters (LB level 3, Renko ATR 14) were used. No parameter search, no predictive models, no strategy validation. |
| Code Conventions Followed | PASS | Imports grouped, type hints on all public functions, docstrings with Parameters/Returns, lazy Polars scans, column projection, bounded plotting, concise logging, deterministic bootstrap seed. |
| Phase 1 Characterisation Boundaries | PASS | Descriptive metrics and bootstrap intervals only. No strategy optimisation, no parameter tuning, no predictive modelling. |

### Audit Consistency

- Audit verdict: PASS (0 critical, 0 warnings).
- Results.md verdict: REFUTED — consistent with code output (`hypothesis_verdict.csv`).
- Report.md conclusion: REFUTED — consistent with results.md.
- All three artifacts agree on the finding.

### Index Updates

- `python/experiments/INDEX.md`: EXP-002 status changed from PLANNED to COMPLETED with accurate one-line finding. PASS.
- `docs/experiments-docs/INDEX.md`: EXP-002 section replaced with correct hypothesis (boundary cost, not regime homogeneity), accurate results tables, and REFUTED conclusion. PASS.

### Data Integrity

- Validation table confirms 70% analysis split on all instruments (ratio = 0.7000).
- Dropped regime rows are minimal (3–20 per chart type, < 0.006% of generated rows).
- Bootstrap seed (42) and N (10,000) recorded in manifest.
- Git commit, package versions, and file hashes recorded for reproducibility.

## Issues Found

### Critical

None.

### Warning

None.

### Info

1. The previous `docs/experiments-docs/INDEX.md` entry for EXP-002 contained an outdated hypothesis formulation ("more homogeneous volatility regimes"). This has been corrected to match the executed scope ("boundary cost versus time-bar lower bound").
2. `lag_data.csv` contains 591,311 rows, of which 166,677 are Time bar entries with lag = 0.0. These carry no information but are harmless.

---

VERDICT: APPROVE

All governance checks pass. The experiment was conducted within scope, code conventions were followed, holdout exclusion was enforced, results are numerically consistent, and documentation artifacts are accurate and complete. The REFUTED finding is a valid research outcome — it eliminates a hypothesized advantage of event charts for regime representation.
