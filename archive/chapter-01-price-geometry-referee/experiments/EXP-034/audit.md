# Audit Report: Experiment EXP-034

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 0

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Formulas match plan: net = lifetime_bps - RT - financing; financing via `xen.financing` (shared, self-checked). F01 dual binding rule (boot_p ≤ 0.05 AND ci_low_1s > 0) correctly implemented. |
| `code/run_experiment.py` | Edge cases | PASS | Open-ended lifetimes handled via EXP-030 (reconciliation enforces identical treatment); zero-financing net reconciled to ≤0.01 bps; seed robustness computed for all declared cells. |
| `code/run_experiment.py` | Type safety | PASS | NumPy typed arrays; Polars schema-aware. |
| `code/run_experiment.py` | NaN handling | PASS | `.is_not_null()` on lifetime_bps; `.is_finite()` not needed (no NaN-producing operations on the financing path — elapsed_calendar_days always produces finite output for valid timestamps). |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_analysis_data` applies first-70% slice; holdout never loaded. |
| `code/run_experiment.py` | Loader ordering | PASS | Lazy scan sorts by `CloseTime` before first-70% slicing. |
| `code/run_experiment.py` | Memory/performance | PASS | Single thin event table; vectorized timestamp indexing; no row-by-row Python loops. |
| `code/run_experiment.py` | Safe optimization | PASS | No optimization changes semantics; only new computation is vectorized financing overlay. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` on file rebuild and per-cell inference loop. |
| `code/run_experiment.py` | Logging/output | PASS | Concise INFO-level; helpers return data. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Imports → path → constants → I/O → integrity → rebuild → event table → cost overlay → reconciliation → inference → verdict → disclosures → determinism → plots → orchestration. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots from CSV/JSON outputs; no re-load. |
| `code/run_experiment.py` | Docstrings | PASS | Module docstring and all functions documented. |

## Numerical Validation

### Spot Checks

EURUSD-4h reconciliation: n=39 (EXP-030: 39), net_nofin=12.380613976944032 (EXP-030: 12.380613976944028), abs_diff=3.55e-15 bps — **machine precision**.

CI reconciliation (F04): nofin_ci_low=2.667957424907768 vs EXP-030=2.667957424907768, ci_abs_dev=0.0 — **exact identity**.

EURUSD-4h binding verdict: boot_p=0.009, ci_low_1s=3.90 > 0 → SEQUENCE_PASS_ALPHA05 ✓.

Financing disclosure EURUSD-4h: median_holding_days not seen but mean_financing = 0.61 bps against 12.38 bps gross headroom — consistent with 4h multi-day holds.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Net effect (all cells) | ℝ | [−22.12, +11.77] bps | YES |
| Financing (EURUSD-4h, mean) | Positive small | 0.61 bps | YES |
| Financing (BTCUSD-4h, mean) | Positive large | 10.45 bps | YES (consistent with 10 bps/day rate) |
| Boot p (declared cells) | [0, 1] | [0.009, 0.563] | YES |
| Event counts | ≥ 0 | [36, 4125] | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| EURUSD-4h net | 11.77 bps [ci_low=2.31] | YES | Headroom after financing: pre-financing net was 12.38; 0.61 bps financing leaves 11.77. CI spans 2.31 to 20.74 — wide but above 0. |
| USTEC-4h net | 8.90 bps [ci_low=−21.10] | YES | Per power statement: cannot resolve ≈+10 bps point with n=36. CI matches expected |
| EURUSD-4h boot_p | 0.009 | YES | Below 0.05 threshold, consistent with CI_low > 0 |
| XAUUSD-1h boot_p | 0.563 (not tested) | YES | Predeclared expected fail: point ≈−0.35 with CI spanning [−5.18, 4.51] |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Regime-cluster bootstrap | Regime clusters within (direction) strata capture dependence | YES | Frozen EXP-027 calibration; single-instrument specialization is within-(inst, direction) strata, which reduces to two direction strata with regime clusters. |
| Fixed-sequence FWER | Ordering predeclared before measurement | YES | D0 §1.1-1.2 (2026-06-10). |
| Adverse-side financing | Bounds real swap regardless of direction | YES | Conservative by construction; acknowledged in plan. |

## Results Plausibility

- EURUSD-4h strict pass is the only live question per D0 §1.2. Net 11.77 bps with CI_low=2.31 on n=39 events — the EXP-030 disclosure of EURUSD-4h net_cons +12.38 bps survives the financing deduction of ~0.6 bps/event (multi-day holds). The pass is plausible given the disclosed headroom.
- USTEC-4h INCONCLUSIVE with 36 events — CI half-width 28.1 bps, exactly as the power statement predicted. Cannot resolve.
- XAUUSD-1h not reached by sequence; its pre-financing net was +0.001 bps, with financing (~0.35 bps) pushing it to −0.35 bps. The power statement predicted fail.
- All 12 cells' no-financing nets reconcile with EXP-030 to machine precision, confirming this is purely a financing overlay.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 1 test family / 1 budgeted, 3 plots / 3 budgeted, 1 module / 1 budgeted
- Holdout exclusion verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

None.

## Re-Audit Requirements

None.
