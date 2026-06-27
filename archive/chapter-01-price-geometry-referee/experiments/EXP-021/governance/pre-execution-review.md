# Governance Review: Experiment EXP-021 - Pre-Execution

**Date**: 2026-06-08
**Review Type**: Pre-Execution (consolidated, Stage 4)
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, EXP-020 dependency artifacts, active checkpoint `docs/experiments-docs/checkpoints/2026-06-07-004-avwap-signal-exploration/design.md`

## Executive Summary

EXP-021 is aligned with Phase 004 and the registered `CF-AVWAP-001/HYP-002`
fixed-horizon reaction question. The scope is a single falsifiable event-reaction
test, not a strategy screen. The analysis plan uses real domain closes,
timestamp/index revalidation against the governed EXP-020 substrate, same-regime
matched controls, non-parametric uncertainty, and Holm adjustment across the
three primary domain tests.

During review, one pre-approval implementation gap was corrected in
`code/run_experiment.py`: the dependency gate now verifies the required EXP-020
readiness, invariant, and determinism artifacts directly instead of trusting only
`run_metadata.json`. Control diagnostics were also made more auditable by
emitting matched-control indices, control returns, and aggregate control counts.
No approved metric, denominator, matching rule, inference rule, or scope boundary
was changed.

## Constraint Checks

| Check | Verdict | Notes |
| --- | --- | --- |
| Active checkpoint alignment | PASS | Phase 004 lists EXP-021 as the required AVWAP bounce reaction study after EXP-020 substrate readiness. |
| Registry alignment | PASS | Scope is limited to `CF-AVWAP-001/HYP-002`, first branch only. No non-baseline branches, parameter sweeps, exits, or strategy P&L are introduced. |
| Single question | PASS | Tests whether bounce events outperform matched non-event controls over fixed horizons. |
| Holdout exclusion | PASS | Domain bars are rebuilt through `load_analysis_data()`, which sorts by `CloseTime` and collects only the first 70% analysis slice. Events are hard-joined back to the rebuilt domain frames by trigger index/time/close. |
| Look-ahead prevention | PASS | EXP-020 supplies the governed causal event substrate; EXP-021 control selection uses same-regime metadata, anchor age, timestamp, and non-event status only. Future closes are used only as outcomes. |
| Real-price discipline | PASS | Outcomes are direction-signed log returns from real domain `Close` prices. No synthetic chart prices, P&L, costs, fills, stops, or targets are used. |
| Metric denominators | PASS | Reportable events, insufficient-future events, insufficient same-regime controls, per-event control counts, and aggregate matched-control counts are emitted. Zero denominators remain non-reportable, not zero-valued metrics. |
| Statistical method | PASS | Bootstrap CI and sign-permutation test are non-parametric; no normality, stationarity, constant-volatility, or iid return assumption is used for the headline claim. |
| Multiple comparisons | PASS | Primary 3-bar p-values are Holm-adjusted across the three domains. Secondary 1-bar and 6-bar horizons are diagnostics only. |
| Complexity budget | PASS | Tests: 2/2. Plots: 4/4. New shared modules: 0/1. |
| Code organization | PASS | Imports precede constants; output directories are created only in orchestration; functions are sectioned; helper functions return data rather than printing. |
| Safe performance | PASS | Source data loading is lazy and sliced before collection; plotting uses records/summaries, not full source bars; long outer loops use `tqdm`; explicit loops are bounded to event/control matching. |
| Scope compliance | PASS | Implementation stays within the approved EXP-021 event-reaction component study and does not expand into EXP-022 lifetime outcomes or EXP-023 cTrader screening. |

## Verification

- `python3 -m py_compile python/experiments/EXP-021/code/run_experiment.py` completed successfully.
- The experiment code was not executed, in compliance with the manual execution gate.

## Residual Notes

1. EXP-021 depends on EXP-020's event substrate. The revised dependency gate now
   blocks if required EXP-020 artifacts are missing, if ready domains differ
   from `{5m, 1h, 4h}`, if any invariant violation exists, or if determinism
   replay fails.
2. The same-regime control restriction may reduce 4h reportability. This is
   explicitly scoped and will be visible in `control_match_diagnostics.csv`; it
   is not a governance issue.
3. EXP-021 can support only the fixed-horizon reaction operationalization. It
   cannot by itself authorize EXP-023 screening; Phase 004 still requires EXP-022
   or an explicit governed decision.

## Verdict

```text
VERDICT: APPROVE
```
