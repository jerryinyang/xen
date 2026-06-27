# Governance Review: Experiment EXP-054 — Post-Experiment

**Date**: 2026-06-16
**Review Type**: Post-Experiment (Stage 8, consolidated)
**Artifacts Reviewed**: `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/families/cf-ha-harami-001/INDEX.md`, `docs/experiments-docs/INDEX.md`, `docs/signal-registry/multiplicity-registry.md`, `docs/signal-registry/candidate-families/harami.md`

## Executive Summary

All post-execution artifacts are complete and consistent. The experiment delivered its scoped fill-model validation cleanly: FILL_MODEL_CHARACTERISED (IMMATERIAL) with median Δr 0.010, 0/99 G1 VIABLE, 0 TIE_BREAK_SENSITIVE cells. The P15 path-ordered fill model is adopted as the 014-B fill standard with its ~1% effect bounded and documented. All index updates and signal-registry dispositions are correctly applied. Verdict: **APPROVE**.

## Artifact Completeness

| Artifact | Status | Notes |
|----------|--------|-------|
| `audit.md` | PASS | 0 Critical, 0 Warnings, 2 Info (code hardening between review and execution; G2 isolated VIABLE cell). Audit PASS. |
| `results.md` | PASS | Full interpretation with 6 detailed findings, hypothesis verdict, limitations, alternative explanations, and recommended next steps. |
| `report.md` | PASS | Follows template. Includes registry disposition, key findings (with plots), limitations, and artifact links. |
| `python/experiments/INDEX.md` | Updated | EXP-054 row inserted after EXP-053 with FILL_MODEL_CHARACTERISED (IMMATERIAL). |
| `docs/experiments-docs/families/cf-ha-harami-001/INDEX.md` | Updated | EXP-054 card appended after EXP-053 with full five-field schema. |
| `docs/experiments-docs/INDEX.md` | Updated | 014-B checkpoint status updated: EXP-054 FILL_MODEL_CHARACTERISED noted; remaining slate referenced. |
| `governance/post-experiment-review.md` | Present | This file. |

## Signal-Registry Disposition

The experiment is a characterization readout (0 candidate slots, 0 TEST reads, TRAIN-only). A registry disposition was recorded in `report.md` §Registry Disposition:

1. **`multiplicity-registry.md`**: `CF-HA-HARAMI-001/HYP-007 — EXP-054` advanced from PLANNED to **FILL_MODEL_CHARACTERISED (IMMATERIAL) — 2026-06-16** with effect summary.
2. **`candidate-families/harami.md`**: HYP-007 row added to the hypotheses table (FILL_MODEL_CHARACTERISED (IMMATERIAL)).
3. **No TEST reads consumed**: 0 TEST reads, consistent with scope. No `test-read-ledger.md` entry required.
4. **No candidate branch registration**: Characterization only; G2 adjudication deferred until the full 014-B slate.

The disposition is complete and correctly scoped.

## Post-Hoc Constraint Checks

| Check | Verdict | Notes |
|-------|---------|-------|
| Holdout exclusion | PASS | First-49% TRAIN prefix only (0.7 × 0.7); lazy scan+slice before collect; no full-file sort/collect; forward scans clipped to data edge. |
| Real-price discipline | PASS | All outcomes on real prices; barriers and fill resolution use real OHLC. |
| Causality | PASS | Barrier targets from confirmed prior moves only; P15 scan starts at entry_idx+1. |
| EXP-049 reconciliation | PASS | All 99 cells match EXP-049 stored r and counts exactly (max_abs_diff = 0.0). |
| Monotonicity | PASS | Δr ≥ 0, FAV_P15 ≥ FAV_wc, resolved counts equal in all cells. |
| Determinism | PASS | 99/99 cells replay frame-identical. Two-pass comparison. |
| Scope expansion | NONE | No extra analyses beyond the 1 stat method, 4 plots, 0 new modules budget. |
| Code standards | PASS | Lazy Polars, column projection, bounded per-cell memory, explicit docstrings, ruff clean. |
| Documentation accuracy | PASS | All numeric claims in report/results/index match the raw output files (composition_readout.json, fill_compare_map.csv, reconciliation.csv). Spot-checked Δr values, viable counts, dt_frac, and reconciliation results. |

## Findings

### Critical

None.

### Warning

None.

### Info

1. **Lead 2 of 014-B slate complete.** EXP-054 is the second experiment of the 014-B slate — the fill-model correction that was carried from Phase 010 as a deferred item. The P15 path-ordered fill model is now characterised and adopted as the 014-B fill standard with its ~1% effect bounded and documented. No benchmark re-baseline is warranted.

2. **Code hardened between review and execution.** The version that produced results includes DE30 runtime verification (`verify_de30_disclosure`), a session-model microstructure caveat (`SESSION_MODEL_CAVEAT`), split reconciliation booleans, and a loud-failing `_write_csv` schema check — improvements over the pre-execution-reviewed version. None affect analytical correctness.

3. **G2 isolated VIABLE cell (USDCAD-2h).** Under the G2 retracement geometry, 1 cell (USDCAD-2h) is VIABLE under P15 (r=0.55). This is below the P11 3-instrument threshold and consistent with expected false-positive variation at the 5% bootstrap CI level across 99 cells. Does not affect the G1 binding conclusion.

## Verdict

```
VERDICT: APPROVE
```
