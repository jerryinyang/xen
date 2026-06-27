# Audit Report: Experiment EXP-033

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 0

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Formulas match plan (FH log-return, attribution decomposition, s_entry guard). Reconciliation anchors reproduce EXP-031 H∈{1,6} effects exactly (0.0–1e-15 bps drift). |
| `code/run_experiment.py` | Edge cases | PASS | s_entry marked ill-defined where `|X_full| <= SE`; unreportable cells (<30/15 events) skipped with disclosure; unpowered domains classified `UNPOWERED` in crossover. |
| `code/run_experiment.py` | Type safety | PASS | NumPy typed arrays; Polars schema-aware; `ensure_bool()` handles CSV Boolean coercion. |
| `code/run_experiment.py` | NaN handling | PASS | `.is_finite()` guards on FH returns; containment invariant asserts all grid horizons finite; `is_not_null()` on lifetime_bps. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_analysis_data` applies first-70% slice; TRAIN cutoff is nested 70% of domain bars; holdout never loaded. |
| `code/run_experiment.py` | Loader ordering | PASS | Lazy scan sorts by `CloseTime` before first-70% slicing. |
| `code/run_experiment.py` | Memory/performance | PASS | Vectorized shifted-Close FH joins (one pass per cell for all H); no row-by-row Python loops over event frames. |
| `code/run_experiment.py` | Safe optimization | PASS | Shared bootstrap seed across H preserves curve coherence; no vectorized shortcut violates temporal causality. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` on file rebuild, attribution sweep, FH net curve, policy comparison. |
| `code/run_experiment.py` | Logging/output | PASS | Concise INFO-level; helpers return data, no helper-level printing. |
| `code/run_experiment.py` | Organization/import side effects | PASS | VAL-001-style sections; directories created in `main()`. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots consume CSV/JSON output rows, no re-load of heavy data. |
| `code/run_experiment.py` | Docstrings | PASS | Module docstring, functions documented. |

## Numerical Validation

### Spot Checks

Reconciliation at H=1/5m: full effect rebuild = 5.778539546952982 bps vs EXP-031 = 5.778539546952982 bps — **exact match**.

Containment accounting (EURUSD/5m events): 2886 before, 886 excluded_window, 0 excluded_lifetime, 2000 after — consistent (2000 = 2886 − 886).

B2 selection (4h): H*=8 (first within one SE of max), net_at_H* = 31.30 bps, policy = all_legs — mechanically correct per one-SE rule.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| FH returns | ℝ | [−∞, +∞] (finite per invariant) | YES |
| s_entry | [−∞, +∞] or None | [−2.9, +2.1] | YES |
| Net (FH curve) | ℝ | [−3.72, +45.79] bps (objective) | YES |
| Event counts | ≥ 0 | [25, 2898] (TRAIN) | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| 5m crossover | H=3 | YES | Mid-short horizon crossover resolves EXP-031's H=1/H=6 flip |
| 1h crossover | H=4 | YES | Shifted right from 5m, consistent with slower domain |
| 4h powered | False | YES | 4h TRAIN events ~120 across 4 instruments — underpowered for attribution |
| 5m FH max | −3.72 bps | YES | Consistent with EXP-030 negative on 5m |
| 4h FH max | +45.79 bps | YES | Consistent with EXP-030 4h headroom |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Regime-cluster bootstrap | Clusters capture within-stratum dependence | YES | Frozen EXP-027 calibration |
| Matched-control exchangeability | Controls exchangeable within (inst, dir) | YES | Standing EXP-021/027/028 assumption |
| Additivity | X_full = X_entry + X_exit | YES | Exact by construction on common-control set |

## Results Plausibility

- STABLE_CROSSOVER on 5m (H=3) and 1h (H=4) resolves EXP-031's horizon-dependent flip: entry dominates at longer horizons, exit at short — consistent with exit cutting early losers (H=1 benefit) but truncating trends (H=6 drag).
- 5m/1h not B2-eligible: grid max ≤ 0 confirms the fixed-horizon exit cannot rescue net on powered domains under frozen costs+financing.
- 4h B2-eligible (H*=8, all_legs) but `h_star_stable = false` — the selection is fragile on ~90 TRAIN events, as the F07 disclosure flags.
- All outputs consistent with Phase 007/008 disclosures.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 2 test families / 2 budgeted, 4 plots / 4 budgeted, 1 module / 1 budgeted
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
