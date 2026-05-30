# Governance Review: Experiment EXP-036 - Post-Experiment

**Date**: 2026-05-29
**Review Type**: Post-Experiment
**Artifacts Reviewed**: `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`

## Executive Summary

The post-execution package is complete and consistent with the approved scope. The audit passes with no critical or warning issues. The interpretation applies the predeclared verdict mechanically: no next-bar instrument-timeframe cell passes both neutral and matched-control contrasts, and the 4-bar secondary has only one both-contrast passing instrument. The report and indexes record the result as `REFUTED` without opening EXP-038.

## Constraint Checks

| Check | Verdict | Notes |
| --- | --- | --- |
| Audit thoroughness | PASS | `audit.md` checks scope compliance, holdout exclusion, code standards, numerical consistency, adjudicability floors, and gap diagnostics. |
| Interpretation fidelity | PASS | `results.md` anchors to the approved gates and reports both negative and localized positive results without moving thresholds. |
| Final report completeness | PASS | `report.md` includes question, hypothesis, method summary, quantitative findings, limitations, implications, and artifact links. |
| Index updates | PASS | Both experiment indexes include EXP-036 with `REFUTED` status and the key finding. |
| Scope discipline | PASS | No new descriptor, timeframe, horizon, or robustness perturbation was introduced after results. |
| Holdout discipline | PASS | Post-experiment artifacts rely only on generated analysis-set outputs; no holdout inspection occurred. |
| Real-price discipline | PASS | Reported outcomes use strict aggregated real OHLC returns only. |
| Governance continuity | PASS | EXP-038 is not opened because EXP-036 does not meet the survival gate. |

## Findings

### Critical

None.

### Warning

None.

### Info

1. The audit notes that the fourth plot visualizes the 4-bar neutral panel only; 4-bar control results are still tabular and are included in the verdict. This does not affect interpretation.
2. `4h` gap-spanning entries remain an executability caveat, but no survivor exists to justify opening the planned robustness experiment.

## Verdict

```text
VERDICT: APPROVE
```
