# Governance Review: Experiment EXP-010 - Post-Experiment

**Date**: 2026-06-04
**Review Type**: Post-Experiment (consolidated, Stage 8)
**Artifacts Reviewed**: `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`

VERDICT: APPROVE

## Executive Summary

EXP-010 completed the corrected split-protocol robustness measurement. The re-audit passes with no critical or warning issues, the single-split reference reproduces EXP-003, FPR remains 0/2000 for every protocol/domain at alpha0, and the corrected interpretation reports H-split as supported on 5m/1h and falsified only on 4h. The 4h falsification is in the more-sensitive direction: walk-forward and purged CV detect 8 bps versus the single split's 12 bps.

## Constraint Checks

| Constraint | Verdict | Notes |
|------------|---------|-------|
| Audit adequacy | PASS | `audit.md` verifies deterministic draw generation, holdout-safe fold construction, corrected pooled-OOS fold combination, streamed output dimensions, reference reproduction, FPR/MDE counts, and CI scaling with pooled OOS size. |
| Results interpretation | PASS | `results.md` clearly supersedes the original artifact-driven 1h/4h inflation, reports 5m/1h split robustness, and labels the 4h shift as protocol-plus-OOS-window sensitivity. |
| Final report | PASS | `report.md` includes the correction note, key FPR/MDE findings, limitations, plots, and artifact links without adopting a protocol change. |
| Index updates | PASS | Both indexes record the corrected result: 5m/1h robust, 4h materially lower under alternative protocols, original walk-forward inflation corrected as a multi-fold CI artifact. |
| Phase alignment | PASS | Finding supplies robustness context for EXP-011 and does not change the frozen referee or mandatory split policy in Phase 002. |
| Governance constraints | PASS | No holdout use, no chart-type/synthetic-price issue, no referee redesign, no scope creep beyond the approved split comparison. |

## Findings

### Critical

None.

### Warnings

None.

### Info

1. The 4h falsification is not FPR inflation or referee logic drift; it is consistent with the larger OOS sample available to the alternative protocols.
2. Any split-policy recommendation or adoption belongs to EXP-011/Phase 003, not EXP-010.
3. Future multi-fold referee wrappers should include a pooled-OOS CI scaling check, because single-split reproduction alone does not exercise the combination path.

## Decision

Post-experiment governance approves EXP-010 as complete under the corrected re-run.
