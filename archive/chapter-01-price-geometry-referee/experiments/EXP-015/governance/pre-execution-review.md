# Pre-Execution Governance Review — EXP-015

**Experiment:** EXP-015 — Incremental Referee Portfolio-Fitness Calibration (Track B keystone)
**Stage:** 4 (pre-execution)
**Date:** 2026-06-04
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `python/src/xen/incremental_referee.py`
**Phase:** 2026-06-04-003-ratification-and-incremental-unit (ACTIVE)

---

## Track B predeclaration confirmation (operator-gated)

On **2026-06-04** the operator confirmed **D-incr-form / D-incr-substrate /
D-incr-legs** as implemented (full record in EXP-013's review). EXP-015 inherits the
frozen estimator and leg mapping unchanged and adds the predeclared **D-dependence**
grid. The confirmation is enforced transitively: EXP-015 hard-gates on EXP-013 and
EXP-014 `overall_status == PASS`, neither of which is reachable without the token.

```text
PHASE003-TRACKB-PREDECLARATION-CONFIRMED
```

---

## Verdict

```text
VERDICT: APPROVE
```

Execution preconditions (all hard-gated in `dependency_manifest()` → BLOCKED
otherwise): EXP-013 PASS, EXP-014 PASS, and EXP-003 `mde_summary.csv` present (inherited
strict-gate MDE map for the `R_at_strict_mde` reference strength).

---

## Constraint checks

| Constraint | Finding | Status |
|---|---|---|
| Holdout exclusion | `load_analysis_data` first-70% slice; `analysis_metadata.csv` records `analysis_end`; holdout never loaded. | PASS |
| Look-ahead / lead-lag (critical) | `_apply_lag` shifts the **synthetic** C positions (derived from seeded latent state, not returns); marginal P&L = marginal_position_t × real_return_t stays causal. `_diagnostic_arrays` measures the structural correlation by un-doing the lag. Planted drift added to scoped returns in the direction of the already-shifted marginal position — no future-return information enters any position. | PASS |
| Real-price discipline | Reference + incremental edges planted on real domain `Close` returns; incremental edge from `marginal_net_series`. No HA/Renko prices. | PASS |
| Timestamp alignment | R/C/returns aligned by `CloseTime`; split via `domain_split_index`; no bar-index alignment. | PASS |
| Dependence grid (D-dependence) | Full grid {rho×overlap×lag×reference-strength} per domain; construction acceptance bands (rho ±0.05, overlap ±0.05) enforced before measurement; infeasible cells reported `CONSTRUCTION_INVALID`/under-powered, never silently pooled. | PASS |
| Redundancy-null FPR is core | FPR summarized **per grid cell** (not pooled); cells with `R_at_strict_mde` test whether R's edge is mis-attributed to C. Reference edge on opposite-sign overlap rows contributes *negatively* to the marginal (correct: cancelling R's edge is negative fitness) — cannot manufacture a false positive. | PASS |
| MDE aggregation (worst-case) | `summarize_domain_mde` = `max(finite cell MDEs)` across qualifying cells; REFUTED if any qualifying cell has uncontrolled FPR or no finite MDE; under-powered cells reported separately. Matches scope's worst-case rule. | PASS |
| Zero-baseline handling | Wilson intervals on finite zero rates; empty-cell guards; no percentage-of-zero. | PASS |
| Complexity budget | 4 measurements (FPR, TPR, cell-MDE, domain verdict) / 5 plots / 0 new modules — within 4/5/1. | PASS |
| Code conventions | Imports→constants→construction→workers→summaries→plotting→`main()`; output dirs in orchestration; `tqdm` on draws; seed-deterministic `mp.Pool`; bounded plot inputs. | PASS |
| Phase alignment | Matches design §8 EXP-015 (Track B keystone), §4 H-incr-floor, D-dependence. | PASS |

## Notes for the auditor (Stage 5, non-blocking)

- Confirm the lead/lag cells introduce **no return look-ahead** by spot-checking that a
  C-leading positive draw's recovered edge matches the planted edge within tolerance
  (a leak would inflate it).
- Confirm high-rho/low-overlap cells are reported `CONSTRUCTION_INVALID`
  (`target_rho_infeasible_for_overlap`) rather than forced, and that 4h joint-(R,C)
  effective-N under-powered cells are reported, not converted to pass/fail.

---

## Manual execution gate

```text
Pre-execution review: APPROVED

Experiment: EXP-015 - Incremental Referee Portfolio-Fitness Calibration
Code: python/experiments/EXP-015/code/run_experiment.py
Expected output: python/experiments/EXP-015/results/

Constructs known-truth R/C draws across the dependence grid on the first-70% slice,
applies the incremental referee, and reports per-cell redundancy-null FPR and positive
TPR/MDE with Wilson intervals, aggregating to a worst-case domain portfolio-fitness MDE.

Please run the experiment code and confirm when complete.
```
