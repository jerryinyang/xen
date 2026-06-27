# Audit Report: Experiment EXP-024

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 2
- **Info Notes**: 3

The rerun resolves the prior critical blocker. `exp021_crosscheck.csv` now
recomputes EXP-021 reportable event returns on exact matched event keys, and the
maximum difference is `0.0` bps. `event_join_diagnostics.csv` confirms that the
EXP-020 event to EXP-022 lifetime left join preserves event row counts and has no
duplicate join keys. The implementation and outputs are now trustworthy enough
for Stage 6 interpretation.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | The audit-driven matched EXP-021 cross-check recomputes returns on exact reportable event rows and hard-fails on missing keys or return mismatches. Fork logic matches the predeclared criteria. |
| `code/run_experiment.py` | Edge cases | PASS | Empty/non-reportable horizon cells remain NaN or inconclusive; no zero coercion. |
| `code/run_experiment.py` | Type safety | PASS | Public functions have type hints; Polars/NumPy conversions are explicit. |
| `code/run_experiment.py` | NaN handling | PASS | Completed common-set logic uses finite `lifetime_bps`; horizon-return NaNs are excluded from means/counts. |
| `code/run_experiment.py` | Holdout exclusion | PASS | Domain frames are rebuilt from first-70% analysis slices; horizon returns require `trigger_idx + h <= n - 1`. |
| `code/run_experiment.py` | Loader ordering | PASS | Timebar loading delegates to `load_analysis_data`; EXP-020 metadata equality confirms row counts and time ranges. |
| `code/run_experiment.py` | Memory/performance | PASS | Domain close arrays stay NumPy-backed; plots use already-computed summaries. |
| `code/run_experiment.py` | Safe optimization | PASS | Indexed horizon-return vectorization is causal and uses only trigger and future horizon closes inside the analysis slice. |
| `code/run_experiment.py` | Progress tracking | PASS | Rebuild and per-domain fork loops use `tqdm`. |
| `code/run_experiment.py` | Logging/output | PASS | Concise orchestration-level logging; helpers stay quiet. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Imports, constants, helpers, plotting, orchestration, and `main()` are cleanly sectioned; output dirs are created only in orchestration. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plot files are generated from analysis-pass result objects; no repeated heavy load solely for plotting. |
| `code/run_experiment.py` | Docstrings | PASS | Reusable/public helpers have useful docstrings. |

## Numerical Validation

### Spot Checks

**EXP-021 matched-event cross-check**

- `results/exp021_crosscheck.csv` has 9 rows: 3 domains x horizons `{1,3,6}`.
- Max mean absolute difference: `0.0` bps.
- Max row absolute difference: `0.0` bps.
- Matched event counts reproduce EXP-021 reportable denominators: 5m `16,249`; 1h `1,207`; 4h `246/246/244` across horizons.

This resolves the prior audit failure. EXP-024's all-event `g_all` still differs
from EXP-021 because EXP-021 is a matched-control reportable subset. That
difference is now explicitly contextual, not a failed reconstruction check.

**Event/lifetime join**

- `results/event_join_diagnostics.csv`: row count preserved in all domains.
- Duplicate event join keys beyond first: `0`.
- Duplicate lifetime join keys beyond first: `0`.
- Joined event rows: 5m `19,242`, 1h `1,360`, 4h `309`.
- Completed lifetime rows used by common-set fork logic: 5m `15,037`, 1h `1,033`, 4h `235`.

**Fork verdicts**

- 5m best horizon is `h=16`: `g*=0.3704` bps, floor `0.5`, CI `[-0.3956, 1.1636]`, `n=15,037`. Every adequately powered horizon is below the floor, so `FORK_B_DILUTION` is correct.
- 1h best horizon is `h=24`: `g*=4.2485` bps, floor `2.0`, CI `[-10.1905, 18.4174]`, `n=1,033`. Point estimate exceeds floor, but floor clearance is unresolved; `INCONCLUSIVE_UNRESOLVED` is correct.
- 4h best horizon is `h=8`: `g*=8.1374` bps, floor `8.0`, CI `[-22.7687, 39.7473]`, `n=233`. Point estimate barely exceeds floor with huge uncertainty; `INCONCLUSIVE_UNRESOLVED` is correct.
- Phase row: `MIXED_OR_INCONCLUSIVE`, consistent with 5m fork (b) plus unresolved 1h/4h.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|--------------|-------|
| Domain reconstruction | 12/12 EXP-020 metadata checks pass | 12/12 pass | YES |
| Matched EXP-021 return diff | <= `1e-6` bps | `0.0` bps | YES |
| Join duplicate rows | 0 | 0 | YES |
| Common-set N | Positive and bounded by raw event count | 5m 15,035-15,037; 1h 1,033; 4h 232-235 | YES |
| Horizon returns | Real-valued bps with NaN only for non-reportable horizons | Finite reported means/CIs in all output rows | YES |
| Plot outputs | 4 planned plots | 4 plot files present | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| 5m h* CI | `[-0.396, 1.164]` around `0.370` bps | YES | CI straddles the 0.5 bps floor, but point estimate is below floor and all horizons are below floor. |
| 1h h* CI | `[-10.190, 18.417]` around `4.248` bps | YES | Wide interval expected from lower event count and larger 1h volatility. |
| 4h h* CI | `[-22.769, 39.747]` around `8.137` bps | YES | Very wide interval expected with ~233 completed common events. |
| Trend-change means | 5m `-2.79`, 1h `-8.76`, 4h `-17.59` bps | YES | Directionally plausible and consistent with trend-change exits being negative on average. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Domain reconstruction | Rebuilt bars match EXP-020 analysis-set substrate | YES | `domain_reconstruction_check.csv`: 12/12 pass. |
| Matched EXP-021 cross-check | EXP-024 return formula reproduces EXP-021 event returns on identical rows | YES | Max row and mean diff both `0.0` bps. |
| Event/lifetime common-set pairing | Left join does not duplicate or lose EXP-020 event rows | YES | Join diagnostics show row preservation and 0 duplicate keys. |
| Regime-cluster bootstrap | Events in a regime share dependence | YES | Matches EXP-021/022 convention and approved plan. |
| Precision for slower domains | 1h/4h have enough precision to resolve fork | PARTIAL | Counts are above the minimum, but CIs are too wide for floor-clearance decisions. |

## Results Plausibility

Outputs are internally coherent. The primary 5m domain has a large common-set
denominator and all bounded horizons remain below the loose floor. The 1h and 4h
point estimates rise at longer horizons but have confidence intervals too wide
to support floor clearance. Trend-change exits are negative on average in all
domains, and the cost lens confirms net values remain weak after round-trip cost.

The corrected cross-check also clarifies why the old audit failed: EXP-021's
headline reaction evidence is not the same estimand as EXP-024 all-event `g_all`.
EXP-021 measured event-vs-control reaction on reportable matched-control events;
EXP-024 measures all-event and completed-common-set bounded-hold returns.

## Scope Compliance

- **Analysis plan followed**: YES.
- **Deviations**: None after the audit-driven correction; the cross-check now matches the approved "matched event set" language.
- **Complexity budget**: 2/2 statistical tests, 4/4 plots, 0/1 new modules.
- **Holdout exclusion verified**: YES.
- **Real-price discipline**: YES; all returns use real domain close prices.
- **Look-ahead bias**: None identified.

## Issues

### Critical

None.

### Warnings

1. **1h and 4h remain unresolved because confidence intervals are too wide**
   - File: `results/fork_verdict.csv`
   - Description: 1h and 4h have above-floor point estimates at `h*`, but the bootstrap CIs straddle their floors by wide margins.
   - Impact: The phase cannot treat 1h/4h as fork (a), and cannot aggregate to all-domain fork (b).
   - Fix: No code fix. Interpret as predeclared `INCONCLUSIVE_UNRESOLVED`.

2. **Phase-level result requires governance/operator handling before Stage B**
   - File: `results/fork_verdict.csv`
   - Description: Phase verdict is `MIXED_OR_INCONCLUSIVE`, not a clean Stage-B trigger or clean Stage-B skip.
   - Impact: EXP-026 `/EXIT` is not automatically justified by EXP-024 alone; the Phase 005 design says mixed/inconclusive routes to operator decision or scoped-domain governance.
   - Fix: Interpret explicitly in `results.md`; do not silently proceed to EXP-026 as if fork (a) were supported.

### Info

1. **5m raw event count exceeds the scope's preliminary count**
   - Description: Raw 5m events are `19,242`, while EXP-021 matched reportable events are `16,249` and completed common-set rows are `15,037`. The discrepancy is now explained by event-population differences, not duplication.

2. **EXP-021 matched reaction and EXP-024 all-event returns are different estimands**
   - Description: EXP-021 matched event means at `{1,3,6}` are `0.387/1.096/1.793` bps on 5m, while EXP-024 all-event `g_all` is `0.002/0.067/0.148` bps. The matched-event recomputation is exact; the remaining gap is sample-definition/context.

3. **Trend-change exits are negative on average**
   - Description: Trend-change lifetime means are negative on all domains, but this is interpretation material rather than an audit defect.

## Re-Audit Requirements

None. EXP-024 can proceed to Stage 6 interpretation.
