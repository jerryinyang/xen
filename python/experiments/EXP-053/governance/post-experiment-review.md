# Governance Review: Experiment EXP-053 — Post-Experiment

**Date**: 2026-06-15
**Review Type**: Post-Experiment (Stage 8, consolidated)
**Artifacts Reviewed**: `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/families/cf-ha-harami-001/INDEX.md`, `docs/experiments-docs/INDEX.md`, `docs/signal-registry/multiplicity-registry.md`, `docs/signal-registry/candidate-families/harami.md`

## Executive Summary

All post-execution artifacts are complete and consistent. The experiment delivered its scoped conditioned-efficacy readout cleanly: EVIDENCE_FOR with 7 viable cells over 6 instruments (P11 met), 6 over 5 beat both baselines (P11 met), 0 defects, 99/99 powered. This is the first outcome read of the actual conditioned family hypothesis — what 014-A left untested. All index updates and signal-registry dispositions are correctly applied. Verdict: **APPROVE**.

## Artifact Completeness

| Artifact | Status | Notes |
|----------|--------|-------|
| `audit.md` | PASS | 0 Critical, 0 Warnings, 1 Info (DE30 disclosure — immaterial, DE30 not among viable cells). Audit PASS. |
| `results.md` | PASS | Full interpretation with 6 key findings, verdict, limitations, alternative explanations, and recommended next steps. |
| `report.md` | PASS | Follows template. Includes registry disposition, key findings (with plots), limitations, and artifact links. |
| `python/experiments/INDEX.md` | Updated | EXP-053 row inserted after EXP-052 with CONDITIONED_EFFICACY_DELIVERED — EVIDENCE_FOR. |
| `docs/experiments-docs/families/cf-ha-harami-001/INDEX.md` | Updated | EXP-053 card appended after EXP-052 with full five-field schema. |
| `docs/experiments-docs/INDEX.md` | Updated | 014-B checkpoint status updated: EXP-053 CONDITIONED_EFFICACY_DELIVERED noted; remaining slate referenced. |
| `governance/post-experiment-review.md` | Present | This file. |

## Signal-Registry Disposition

The experiment is a characterization readout (0 candidate slots, 0 TEST reads, TRAIN-only). A registry disposition was recorded in `report.md` §Registry Disposition:

1. **`multiplicity-registry.md`**: `CF-HA-HARAMI-001/HYP-006 — EXP-053` advanced from PLANNED to **CHARACTERISED — EVIDENCE_FOR** with per-cell tallies.
2. **`candidate-families/harami.md`**: HYP-006 row added to the hypotheses table (CHARACTERISED — EVIDENCE_FOR).
3. **No TEST reads consumed**: 0 TEST reads, consistent with scope. No `test-read-ledger.md` entry required.
4. **No candidate branch registration**: Characterization only; G2 adjudication deferred until the full 014-B slate.

The disposition is complete and correctly scoped.

## Post-Hoc Constraint Checks

| Check | Verdict | Notes |
|-------|---------|-------|
| Holdout exclusion | PASS | First-49% TRAIN prefix only (0.7 × 0.7); lazy scan+slice before collect; no full-file sort/collect; forward scans clipped to data edge; DATA_CENSORED guard. |
| Real-price discipline | PASS | All outcomes on real prices; HA candles for detection only (`detect_ha_harami`, `annotate_ha_impulse`). |
| Causality | PASS | Live in-progress state from moves confirmed ≤ t_i (`searchsorted side="right"-1`); time-cap from moves confirmed strictly < t_i (`side="left"-1`); M_sofar from C and known start pivot only; P15 scan starts at entry_idx+1. Binding assertion guard in code. |
| G1≡G2 collapse proof | PASS | Single benchmark favourable geometry (proof in analysis-plan Step 3). Code verified: both constructions produce the same target under the current-price M_sofar reference. |
| Determinism | PASS | 17/17 cells (1 per instrument) replay byte-identical. All reconciliation checks pass (fav+adv+timecap=m, pos_returns≥fav, neg_returns≥adv). |
| Scope expansion | NONE | No extra analyses beyond the 4 budgeted stat tests, 4 plots, 1 new module. |
| Code standards | PASS | Import-side effects, lazy Polars + column projection, bounded per-cell memory (del train_1m), explicit bounded loops for P15 resolver and /STRONG-STAT per-entry walk. |
| Documentation accuracy | PASS | All numeric claims in report/results/index match the raw output files (composition_readout.json, outcome_primary.csv). Spot-checked viable cell IDs, cell counts, instrument counts, and reconciliation values. |

## Findings

### Critical

None.

### Warning

None.

### Info

1. **Lead experiment of 014-B complete.** EXP-053 is the first and lead experiment of the 014-B slate — the actual conditioned family hypothesis that 014-A left untested. EVIDENCE_FOR on benchmark geometry means the family's central efficacy claim is supported. The remaining experiments (EXP-054–060) continue characterization of alternative geometries, overlays, and the combined event system before G2.

2. **Concentration pattern.** Only 7/99 cells are viable. This is acceptable per the P11 composition convention but narrows the claim's breadth. The effect is not universal — it concentrates in specific instrument–domain pockets (BTCUSD short-term, EURUSD-1h, EURGBP/USDCHF/EURJPY longer-term). This is consistent with the mechanism relying on strong-move exhaustion, which not every instrument–domain pair produces.

3. **Power is not a concern.** All 99 cells clear the 30-event floor despite /STRONG-STAT retaining only ~8–16% of the unconditioned harami population. Conditioning narrows but does not deplete the population — a material positive for the subsequent 014-B slate.

## Verdict

```
VERDICT: APPROVE
```
