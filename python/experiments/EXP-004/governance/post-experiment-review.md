# Governance Review: Experiment EXP-004 — Post-Experiment

**Date:** 2026-05-16
**Review Type:** Post-Experiment
**Artifacts Reviewed:**
- `python/experiments/EXP-004/audit.md`
- `python/experiments/EXP-004/results.md`
- `python/experiments/EXP-004/report.md`
- `python/experiments/EXP-004/results/` (all CSV files)
- `python/experiments/EXP-004/plots/` (all 5 PNG files)
- `python/experiments/INDEX.md` (updated)
- `docs/experiments-docs/INDEX.md` (created)

## Constraint Checks

### Holdout Leakage

| Check | Verdict | Evidence |
|-------|---------|----------|
| Final 30% never loaded | PASS | `load_timebar_data()` uses `scan.slice(0, int(total_rows * 0.7))` on lazy scan |
| Final 30% never inspected | PASS | No code path accesses rows beyond the 70% cutoff |
| Holdout excluded from plotting | PASS | All plots built from analysis-set records only |

### Synthetic Price Discipline

| Check | Verdict | Evidence |
|-------|---------|----------|
| No synthetic price P&L | PASS | No strategy returns computed; reversal reference uses real Close/High/Low |
| HA signals use real prices | PASS | HA direction changes timestamped by CloseTime; no HAClose used for validation |
| Renko signals use SourceCloseTime | PASS | `CHART_CONFIG["Renko"]["time_col"] = "SourceCloseTime"` |
| Line Break signals use SourceCloseTime | PASS | `CHART_CONFIG["LineBreak"]["time_col"] = "SourceCloseTime"` |

### Timestamp Alignment

| Check | Verdict | Evidence |
|-------|---------|----------|
| CloseTime used for time bars | PASS | `detect_swing_reversals` uses `CloseTime` column |
| SourceCloseTime used for LB/Renko | PASS | `CHART_CONFIG` maps correctly; `extract_direction_changes` uses configured time_col |
| No bar-index alignment | PASS | Event matching uses `timedelta64` comparisons on timestamp arrays |

### Scope Compliance

| Check | Verdict | Evidence |
|-------|---------|----------|
| Chart types match scope | PASS | Time, LineBreak (level 3), Renko (ATR-14), Heiken Ashi |
| Instruments match scope | PASS | EURUSD, XAUUSD, BTCUSD, USTEC |
| Thresholds match scope | PASS | Primary 1.5x ATR, alternate 2.0x ATR, 120-min tolerance |
| No scope expansion | PASS | No predictive models, no strategy testing, no parameter optimization |
| Complexity budget respected | PASS | 3 evaluations / 3 budgeted, 5 plots / 5 budgeted, 0 new modules / 1 budgeted |

### Phase 1 Characterisation Boundaries

| Check | Verdict | Evidence |
|-------|---------|----------|
| No strategy optimization | PASS | Pure event detection and matching; no entry/exit rules |
| No predictive modeling | PASS | No train/test split (correct per scope); no model fitting |
| No parameter tuning against returns | PASS | Parameters fixed by scope; no return-based optimization |

### Code Conventions

| Check | Verdict | Evidence |
|-------|---------|----------|
| Import organization | PASS | stdlib -> third-party -> local |
| Lazy loading | PASS | `pl.scan_parquet` with column projection |
| Type hints | PASS | All public functions annotated |
| Docstrings | PASS | Parameters and Returns sections present |
| Concise logging | PASS | Per-instrument progress, summary statistics |
| Bounded plotting | PASS | Plots use aggregated records, not raw event tables |

## Index Updates Verified

| File | Status | Notes |
|------|--------|-------|
| `python/experiments/INDEX.md` | UPDATED | EXP-004 status changed from PLANNED to COMPLETED with one-line finding |
| `docs/experiments-docs/INDEX.md` | CREATED | First comprehensive index entry with all five fields populated |

## Audit Findings Review

- **Critical issues**: 0 — no blockers.
- **Warnings**: 1 — sensitivity check has limited discriminative power due to wide tolerance window. This does not affect the validity of the primary findings.
- **Info notes**: 3 — ATR method choice, bootstrap vs exact binomial substitution, no nested split. All acceptable.

## Results Integrity

- Numerical spot checks pass (audit.md confirms precision, recall, false count arithmetic).
- Support summary correctly shows 0 faster instruments for all chart types.
- Results are internally consistent across all CSV files.
- All 5 plots generated and saved.

## Verdict

```text
VERDICT: APPROVE
```

All governance constraints are satisfied. The experiment executed within scope, produced consistent and auditable results, and generated a definitive (negative) finding. The REFUTED verdict is well-supported by the data and honestly reported. No revision cycle is needed.
