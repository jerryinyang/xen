# Pre-Execution Governance Review: EXP-021

**Experiment**: EXP-021 - IFVG Confirmation Entry Quality
**Artifacts reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**Review date**: 2026-05-26
**Revision cycle**: 2 of 2

---

## Scope Review

| Check | Status | Notes |
|-------|--------|-------|
| Single falsifiable question | PASS | "Does IFVG confirmation improve entry quality enough to offset later entry and fewer signals?" |
| Boundaries defined | PASS | Instruments, time range, chart type, prerequisite IDs all explicit |
| Holdout exclusion stated | PASS | Final 30% excluded from analysis; nested split documented |
| Real-price outcome discipline | PASS | "All outcomes use real time-bar OHLC prices aligned by timestamp" |
| Success/failure criteria measurable | PASS | >= 50 risk-feasible IFVG events per segment on >= 3 instruments; bootstrap CI direction |
| Complexity budget respected | PASS | Tests ≤ 3, plots = 4/5, modules = 1/2 |
| Retest exclusion predeclared | PASS | RETEST_INCLUDED = False matches scope ("retest included only if EXP-020 defines a deterministic rule") |
| EXP-020 prerequisite rationale explicit | PASS | Scope now states EXP-021 is a diagnostic consequence check of the frozen current IFVG rule set, not a deployment-ready promotion |

## Analysis Plan Review

| Check | Status | Notes |
|-------|--------|-------|
| Method justification present | PASS | All 3 steps include "why this method" and "simpler alternative considered" |
| Non-parametric bootstrap | PASS | n=10,000, seed=42, distribution-free |
| Cross-view alignment by timestamp | PASS | Events aligned by CloseTime/InversionTime |
| Visualisations purposeful | PASS | 4 plots each answer a sub-question |
| Interpretation guide predeclared | PASS | FOR/AGAINST/INCONCLUSIVE criteria defined before execution |
| Budget compliance | PASS | 2–3 tests / 3, 4 plots / 5, 2 modules / 2 |

## Code Review (post-revision)

| Check | Status | Notes |
|-------|--------|-------|
| Import side effects absent | PASS | `mkdir` only inside `run_experiment()` |
| Holdout exclusion enforced | PASS | `load_analysis_timebars()` returns 70% analysis set |
| Temporal ordering by CloseTime | PASS | All searchsorted calls use CloseTime nanoseconds |
| Look-ahead bias | PASS | SweepClose uses SweepTime; DisplacementClose uses DisplacementTime; IFVGClose uses InversionTime; SecondCandleOpen uses the bar after InversionTime |
| Real-price outcomes | PASS | `compute_real_price_outcome()` called for all 4 entry variants |
| Bounded plotting | PASS | `PLOT_MAX_POINTS = 5_000`, deterministic `rng.choice()`, `clip()` for R caps |
| Bootstrap parameters match plan | PASS | REPS=10,000, SEED=42, 95% CI, mean difference |
| Organisation | PASS | Import → constants → I/O → computation → plotting → orchestration → main |
| NaN handling | PASS | Bootstrap returns `(nan, nan, nan)` for empty arrays |
| Zero-baseline safety (revised) | PASS | Delayed-entry rows carry `MinRisk1R = EXP-015 Buffer`; rows with inherited `Risk1R < MinRisk1R` are excluded from R-based summaries and bootstraps |
| Type safety (revised) | PASS | Dead `ifvg_ns` parameter removed from `_find_ifvg_for_event()`; call site updated |
| Variable naming (revised) | PASS | Misleading `sweep_close` variable removed; fallback now uses `disp_close` |
| Plan compliance | PASS | Chain construction → outcome computation → bootstrap comparison → plots |

## Issues Resolved

| Issue | Resolution |
|-------|-----------|
| WARNING: Dead `ifvg_ns: np.ndarray` parameter in `_find_ifvg_for_event()`, called with `None` | Parameter removed from function signature and call site (revision cycle 1) |
| INFO: `sweep_close` variable misnaming | Renamed; fallback now uses `disp_close` which correctly falls back to the displacement entry price (revision cycle 1) |
| CRITICAL/WARNING from post-execution audit: near-zero inherited risk invalidated R metrics | Scope and plan now define a Buffer-based inherited-risk feasibility guard; code carries `MinRisk1R` forward and excludes infeasible delayed-entry rows from R-based summaries (revision cycle 2) |

---

## Verdict

```text
VERDICT: APPROVE
```

All critical and warning issues resolved in revision cycle 1. No outstanding issues.
