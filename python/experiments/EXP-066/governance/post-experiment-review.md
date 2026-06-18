# Post-Experiment Governance Review — EXP-066

**Experiment:** EXP-066 — MA(20,50)-Substrate Position-Management Exits (dual-object, Phase 015 S3)
**Family:** CF-HA-HARAMI-001
**Phase:** 015 — MA-Substrate Conditioned Harami Full Surface
**Checkpoint:** `2026-06-17-015-ma-substrate-conditioned-harami-full-surface`
**Amendment:** D0-Amendment-001 (2026-06-17) — Dual Parallel Substrate
**Reviewer:** research-pipeline (Stage 8)
**Date:** 2026-06-18

---

```
VERDICT: APPROVE
```

---

## Compliance Verification

| Check | Status | Notes |
|---|---|---|
| Scope followed | PASS | Dual-object 12-arm position-management exit grid executed as scoped (Amendment 001). Native and hybrid objects measured individually; never pooled. |
| Analysis plan followed | PASS | 4 statistical methods predeclared and executed: median bootstrap CI (binding), P4 mean diagnostic, arm−RM independent contrast, arm−benchmark paired contrast. P11+P6 non-4h composition per object. |
| Pre-execution corrections applied | PASS | `last_train_idx` fix confirmed present in `matched_random_arm` parameter list and call site (audit cross-checked). |
| P12 reconciliation | PASS | 99/99 cells match EXP-061 M0 (native BENCH) and EXP-061 H0 (hybrid BENCH) to RECON_TOL=1e-9. Populations genuinely distinct. |
| Invariants | PASS | 0/2376 structural invariant violations across all arms and objects. |
| Determinism | PASS | 17/17 instruments byte-identical replay. |
| Causality | PASS | 99/99 member cells pass `_causality_ok`. |
| Holdout exclusion | PASS | TRAIN-only (first 49%, F01 prefix); forward scans clipped to `train_end_ts`. No TEST/holdout rows read. |
| Real-price discipline | PASS | HA candles for detection only; all metrics on real OHLC. MA(20,50) on real close. |
| Slot/read accounting | PASS | 0 candidate slots, 0 TEST reads consumed. No `test-read-ledger.md` entry required. |
| Audit | PASS | 0 Critical, 0 Warning, 2 Info (both benign observations; no action required). |

## Artifact Completeness

| Artifact | Present | Notes |
|---|---|---|
| scope.md | YES | Dual-object under Amendment 001 |
| analysis-plan.md | YES | Forks EXP-064 dual-object pipeline |
| code/run_experiment.py | YES | 12-arm × 2-object grid |
| results/ (all 6 output files) | YES | composition_readout.json, reconciliation.csv, per_cell_expectancy.parquet, position_mgmt_map.csv, readiness.csv, secondary_map.csv, run_metadata.json |
| results.md | YES | Stage-6 artifact; fork-format for dual-object |
| report.md | YES | Stage-7 artifact |
| audit.md | YES | PASS (0C/0W/2I) |
| governance/pre-execution-review.md | YES | APPROVE with pre-approval correction recorded |
| governance/post-experiment-review.md | YES | This document |
| plots/ (5 plots) | YES | per_arm_median_forest.png, arm_contrast_heatmap.png, expectancy_distribution_by_arm.png, p11_wins_map.png, median_vs_mean_p4_preview.png |

## Updated Registries

| Registry | Change | Status |
|---|---|---|
| `python/experiments/INDEX.md` | EXP-066 row added | COMPLETE |
| `docs/experiments-docs/families/cf-ha-harami-001/INDEX.md` | EXP-066 card added | COMPLETE |
| `docs/experiments-docs/INDEX.md` | Phase 015 status updated (EXP-066 COMPLETE) | COMPLETE |
| `docs/signal-registry/multiplicity-registry.md` | HYP-019/EXP-066 PLANNED → CHARACTERISED | COMPLETE |

## Summary

EXP-066 is complete and governance-APPROVED. All scope, analysis-plan, code, and integrity checks pass. The experiment reports:

- **Native object (MA-segment `/STRONG-STAT`, 8360-class): EVIDENCE_FOR** — PARTIAL-V2A (even-thirds favourable scaling) clears the P11+P6 binding conjunction: 21 arm_wins cells over 13 instruments, all 21 non-4h. Also raw-mean-positive in 11 cells over 6 instruments (7 non-4h) — the strongest possible P4 diagnostic for G-015 input.
- **Hybrid object (ZigZag `/STRONG-STAT`, 3202-class): EVIDENCE_AGAINST** — no arm composes the three-way conjunction. Reproduces EXP-061's central finding on the exit axis.
- **Divergence is the deliverable**: the exit-machinery benefit is a matched-substrate conditioning property. TRAIL-*/COMBINED arms uniformly detrimental on both objects.

The experiment feeds the terminal G-015 after EXP-067 (native combined-champion) and EXP-068 (hybrid combined-champion). No closure or candidate registration occurs here.
