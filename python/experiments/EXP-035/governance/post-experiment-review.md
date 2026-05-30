# Governance Review: Experiment EXP-035 — Post-Experiment

**Date**: 2026-05-29
**Review Type**: Post-Experiment
**Artifacts Reviewed**: `audit.md` (incl. re-audit), `results.md`, `report.md`, `results/verdict.json`, `python/experiments/INDEX.md`, and `docs/experiments-docs/INDEX.md`.

## Constraint Checks

| Check | Verdict | Notes |
|-------|---------|-------|
| Audit completeness | PASS | Original audit found a Critical no-collapse inversion; the appended Re-Audit (2026-05-29) verifies the patched predicate on regenerated, post-patch-timestamped outputs and carries a PASS. Both the bug record and its resolution are preserved. |
| Bug-fix discipline | PASS | The fix (`np.isfinite(dominant_share) and dominant_share <= 0.95`) was implemented, the experiment was rerun manually at the execution gate, and results/plots were regenerated — not edited in place. Re-audit confirms freshness by timestamp. |
| Results interpretation | PASS | `results.md` and `report.md` interpret only readiness/count/determinism evidence; no return, edge, or P&L claim is made. The conditional, aggregation-dependent, instrument-concentrated nature of the pass is stated plainly rather than smoothed over. |
| Final report | PASS | Self-contained, links artifacts and the three key plots, and labels the status SUPPORTED (conditional) with the binding caveats in the title line. |
| Index updates | PASS | Both the brief table and the detailed index carry EXP-035 with the conditional status and the readiness-cell qualification. |
| Holdout rule | PASS | All artifacts state the final 30% global holdout was excluded before aggregation via `load_analysis_timebars`; no code path references it. |
| Scope discipline | PASS | No post-hoc return test, no neutral-band construct, no added timeframe, no MTF Pine mode, no parameter tuning. The verdict cell (`1h/tolerant`) is the predeclared mechanical outcome (`scope.md` lines 23, 49, 68), not a post-hoc selection — Gate 6 holds. |
| Fidelity claim | PASS | The deterministic-only re-implementation claim and the unverified-fidelity caveat are carried consistently across `verdict.json`, `results.md`, `report.md`, and both indexes, per amendment 4. |

## Findings

### Critical

None.

### Warnings

None.

### Info

- **Aggregation-canonicity decision is deferred to the mid-phase reflection, correctly.** Market Bias passes readiness only under tolerant aggregation; under the strict rule EXP-034 selected for Prior-Range Location it is single-instrument (inconclusive). The scope predeclared that the binding canonical rule is locked at the reflection, so this is a legitimate inherited decision, not an unresolved inconsistency. The reflection must record the rule choice and its effect on both descriptors before any return test opens.
- **Mid-phase reflection precondition now met.** Both Stage A experiments (EXP-034 SUPPORTED; EXP-035 SUPPORTED-conditional) are documented and governed, so the reflection that EXP-034's post-experiment review was waiting on can proceed.
- Reference fidelity remains unverified; a single exported TradingView series under `docs/planning/` before a return test would lift the caveat.

## Verdict

```text
VERDICT: APPROVE
```
