# Governance Review: Experiment EXP-056 — Post-Experiment

**Date**: 2026-06-16
**Review Type**: Post-Experiment (Stage 8, consolidated)
**Artifacts Reviewed**: `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/families/cf-ha-harami-001/INDEX.md`, `docs/experiments-docs/INDEX.md`, `docs/signal-registry/multiplicity-registry.md`, `docs/signal-registry/candidate-families/harami.md`

## Executive Summary

All post-execution artifacts are complete and consistent. The experiment delivered its scoped favourable-target geometry characterisation cleanly: **EVIDENCE_AGAINST** with 0/8 alternative variants clearing P11 WIN. No volume-profile level (`/VPTARGET`) or trailing-magnitude distance (`/MAGTARGET`) systematically improves conditioned capture over the adaptive 50%-of-`M_sofar` benchmark. 99/99 cells powered on all 8 variants — the failure is systematic, not power-limited. All index updates and signal-registry dispositions are correctly applied. Verdict: **APPROVE**.

## Artifact Completeness

| Artifact | Status | Notes |
|----------|--------|-------|
| `audit.md` | PASS | 0 Critical, 0 Warnings, 0 Info. Audit PASS. |
| `results.md` | PASS | Full interpretation with 5 findings, hypothesis verdict (EVIDENCE_AGAINST), limitations, alternative explanations, and recommended next steps. |
| `report.md` | PASS | Follows template. Includes registry disposition, key findings (with plot references), limitations, and artifact links. |
| `python/experiments/INDEX.md` | Updated | EXP-056 row inserted after EXP-055 with EVIDENCE_AGAINST. |
| `docs/experiments-docs/families/cf-ha-harami-001/INDEX.md` | Updated | EXP-056 card appended after EXP-054, with full hypothesis tests, scope, results, and observations. |
| `docs/experiments-docs/INDEX.md` | Updated | 014-B checkpoint status updated: EXP-056 EVIDENCE_AGAINST noted; remaining slate (EXP-057–060) in progress. |
| `governance/post-experiment-review.md` | Present | This file. |

## Signal-Registry Disposition

The experiment is a characterisation readout (0 candidate slots, 0 TEST reads, TRAIN-only). A registry disposition was recorded in `report.md` §Registry Disposition:

1. **`multiplicity-registry.md`**: `CF-HA-HARAMI-001/HYP-009 — EXP-056` advanced from PLANNED to **CHARACTERISED — EVIDENCE_AGAINST (2026-06-16)** with effect summary (0/8 variants clear P11 WIN; 99/99 cells powered; favourable-target lever measured and closed). Branch entries for `/VPTARGET` and `/MAGTARGET` remain REGISTERED — exercised but not promoted to candidate status.
2. **`candidate-families/harami.md`**: HYP-009 row added with verdict, 0-slot/0-TEST-read accounting.
3. **No TEST reads consumed**: 0 TEST reads, consistent with scope. No `test-read-ledger.md` entry required.
4. **No candidate branch registration**: Characterisation within an open family; G2 adjudication deferred until the full 014-B slate.

The disposition is complete and correctly scoped.

## Post-Hoc Constraint Checks

| Check | Verdict | Notes |
|-------|---------|-------|
| Holdout exclusion | PASS | First-49% TRAIN prefix only (0.7 × 0.7); lazy scan+slice before collect; no full-file sort/collect; forward scans clipped to data edge. |
| Real-price discipline | PASS | All outcomes on real prices; HA candles for harami detection only. TickVolume proxy disclosed in all outputs. |
| Causality | PASS | VP reference moves are confirmed completed moves strictly before entry; MAG magnitudes from moves confirmed strictly before the harami; no look-ahead. |
| EXP-053 reconciliation | PASS | All 99 cells match EXP-053 event counts exactly (m and median at diff 0.0). |
| Determinism | PASS | 17/17 cells (first usable per instrument) re-run byte-identical. |
| Scope expansion | NONE | No extra analyses beyond the 4 stat methods, 5 plots, 1 new module budget. |
| Code standards | PASS | Lazy Polars, column projection, bounded per-cell memory, explicit type hints, ruff clean. |
| Documentation accuracy | PASS | All numeric claims in report/results/index match the raw output files (`composition_readout.json`, `favourable_target_map.csv`, `per_cell_expectancy.parquet`, `population_reconciliation.csv`). Spot-checked WIN cell counts, viable cell counts, powered cells, CI values, and BENCH reconciliation. |

## Findings

### Critical

None.

### Warning

None.

### Info

1. **Surface read 1 of 4 post-lead slate complete — favourable-target lever closed.** EXP-056 measures and closes the `/VPTARGET` and `/MAGTARGET` branches under the benchmark 1:1 adverse model. The adaptive 50%-of-`M_sofar` benchmark is competitive with or superior to all 8 tested alternatives on this entry substrate — a robust finding that the favourable target is not the binding constraint.

2. **The adaptation-enriched benchmark is hard to beat.** The 50%-of-in-progress-magnitude-so-far level adapts to the current move's size in real time. Every alternative tested (static VP levels from the prior move, trailing-magnitude distances) lacks this in-event adaptation — and the benchmark won in every comparison. This is a methodological insight worth carrying forward: in-event adaptive targets are structurally harder to beat than static or prior-move-derived alternatives.

3. **No correctness defects for 7 consecutive 014-B experiments (EXP-053–056).** Across conditioned efficacy, fill-model characterisation, long-horizon availability, and favourable-target geometry, every cell has passed determinism replay, causality window invariants, and EXP-053 population reconciliation — the ATR-ZigZag substrate and conditioned-signal construction are stable and verified across 4 independent outcome reads.

## Verdict

```
VERDICT: APPROVE
```
