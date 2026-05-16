# Governance Review: Experiment EXP-006 — Post-Experiment

**Date**: 2026-05-16
**Review Type**: Post-Experiment
**Artifacts Reviewed**:
- `python/experiments/EXP-006/audit.md`
- `python/experiments/EXP-006/results.md`
- `python/experiments/EXP-006/report.md`
- `python/experiments/EXP-006/results/distortion_metrics.json`
- `python/experiments/EXP-006/plots/` (4 plots)
- `python/experiments/INDEX.md` (updated)
- `docs/experiments-docs/INDEX.md` (updated)

---

## Constraint Checks

### Holdout Exclusion

| Check | Verdict | Notes |
|-------|---------|-------|
| Code loads only first 70% | PASS | `load_and_holdout()` slices before collect (run_experiment.py:86) |
| No holdout data in results | PASS | distortion_metrics.json contains only analysis-set metrics |
| No holdout in plots | PASS | All plots sourced from analysis frame |

### Synthetic Price Discipline

| Check | Verdict | Notes |
|-------|---------|-------|
| HA returns used only for distortion diagnostics | PASS | `ha_return` computed solely for compression ratio comparison against `real_return` |
| Real prices used for real-return comparisons | PASS | `real_return` uses `RealClose` (run_experiment.py:300-302) |
| No strategy P&L from HA prices | PASS | No P&L, signal validation, or tradable-return metrics in results |
| HA distortion clearly labeled non-tradable | PASS | Scope, audit, results, and report all label HA returns as diagnostic/non-tradable |

### Timestamp Alignment

| Check | Verdict | Notes |
|-------|---------|-------|
| HA rows aligned to source bars by CloseTime | PASS | HA generator produces 1:1 rows with source bars, matched by CloseTime |
| No bar-index alignment | PASS | All comparisons at identical CloseTime values |

### Scope Compliance

| Check | Verdict | Notes |
|-------|---------|-------|
| Single hypothesis | PASS | One question: HA distortion magnitude and regime dependence |
| No scope creep | PASS | Code implements exactly the approved plan; no extra analyses |
| Complexity budget respected | PASS | 2 tests/2, 4 plots/4, 1 module/1 |
| Exclusions honored | PASS | No Line Break, Renko, strategy backtesting, or predictive modelling |
| Phase 1 characterisation boundaries | PASS | Descriptive only; no strategy optimisation or parameter tuning |

### Code Conventions

| Check | Verdict | Notes |
|-------|---------|-------|
| Import organization | PASS | stdlib → third-party → local grouping |
| Lazy loading | PASS | Polars scan with column projection before collect |
| Bounded plotting | PASS | Subsampling (20K) and windowing (500 bars) before pandas conversion |
| Concise logging | PASS | Per-instrument progress with key metrics |
| Zero-baseline handling | PASS | Guards against zero baselines in compression ratios |
| Type hints and docstrings | PASS | All public functions documented |
| Function size | PASS | All functions within ~30-line guideline |

### Audit Caveats Addressed

| Audit Finding | Status | Notes |
|---------------|--------|-------|
| Warning 1: Regime calibration segment | ACKNOWLEDGED | Results interpretation notes this; does not affect aggregate compression results or REFUTED verdict |
| Info 1: Diagnostic HA returns | ACKNOWLEDGED | Consistent with pre-execution review; properly labeled |
| Info 2: sns.set_theme at module level | ACKNOWLEDGED | Cosmetic only; no data impact |

### Index Updates

| Index | Updated? | Correct? |
|-------|----------|----------|
| python/experiments/INDEX.md | YES | Status changed from PLANNED to COMPLETED; finding summary accurate |
| docs/experiments-docs/INDEX.md | YES | Five-field schema populated; conclusion matches results.md |

---

## Findings

### Critical

None.

### Warnings

None.

### Info

1. **Regime calibration Warning acknowledged but not actioned** — The audit identified that regime thresholds were calibrated on 70% of the analysis set rather than the train segment (49% of full dataset). This was acknowledged in results.md and report.md limitations. Since it does not affect the aggregate compression results or the REFUTED verdict, and re-running the experiment would consume resources for no interpretive gain, this is accepted as-is.

---

## Verdict

```text
VERDICT: APPROVE
```

All core constraints pass. Holdout exclusion verified. Synthetic price discipline maintained. Results are numerically validated, honestly interpreted, and properly documented. The REFUTED verdict is justified by the evidence: zero of four instruments meet the 30% volatility compression threshold. Index files are updated correctly. The experiment is complete.
