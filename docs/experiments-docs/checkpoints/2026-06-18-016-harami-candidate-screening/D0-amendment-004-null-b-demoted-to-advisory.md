# D0-amendment-004 — Null-B demoted to advisory (structural geometry bias)

**Date:** 2026-06-18
**Checkpoint:** `2026-06-18-016-harami-candidate-screening`
**Authority:** This amendment supersedes the named clauses of `D0-predeclarations.md`
(per P15). The base document is not retroactively edited.
**Trigger:** After the EXP-070 second run (post D0-amendment-003, 2026-06-18) returned
`METHOD_DEFECT` with Null-A conjunction FPRs all ≤ 0.035 but Null-B conjunction FPRs
inflated in 5 of 6 cells (0.161–0.773), an investigation established that the Null-B
inflation is a **structural geometry artifact that cannot be corrected by a code fix or
re-run**: the block-rotation path scramble does not eliminate the systematic difference
in barrier geometry between STRONG-STAT-conditioned entries and the general matched pool.
Operator reviewed a three-option decision and **directed Option 3** on 2026-06-18:
demote Null-B to advisory and accept Null-A as the sole binding FPR-control null.

---

## Root cause: structural geometry bias in Null-B

The STRONG-STAT conditioning gate (`m_sofar ≥ p75` of trailing-20 MA segments) selects
entries at a more extreme point in strong moves — specifically, entries where the
favourable distance `m_sofar` and the barrier geometry (fav_dist, adv) are systematically
larger than those of the general matched-pool entries (`m_sofar > 0`). This geometry
difference is **not** introduced by the forward path: it is a property of the entry
point itself.

Block rotation (Null-B) scrambles the **forward path** (contiguous OHLC blocks are
circularly rotated) but preserves the **entry geometry** — the real harami close,
`m_sofar`, ATR, and barrier distances at the entry bar are unchanged. As a result:

- The Null-B signal arm retains the real STRONG-STAT geometry advantage (larger
  fav_dist, larger adv) while walking forward on a scrambled path.
- The Null-B matched-random (RM) arm draws from the general pool, which has
  structurally smaller fav_dist/adv, and walks forward on the same scrambled path.
- The geometry gap → `beats-RM` fires systematically even under Null-B, because the
  signal's barrier reaches further than the random draw's barrier regardless of path.

This bias is **timeframe-graded**: longer timeframes exhibit more extreme STRONG-STAT
conditioning (higher median `m_sofar`), a wider geometry gap, and correspondingly higher
Null-B conjunction FPRs (observed: 5m → 0.027 controlled; 30m → 0.161; 1h → 0.340–0.363;
2h → 0.759; 4h → 0.773).

The bias is not a code error. The amended `_resolve_matched_draw` signature correctly
separates `geom_ohlc` (real entry geometry) from `path_ohlc` (rotated path). The
inflation survives because the geometry difference is real and structural — the STRONG-STAT
conditioning **creates** the barrier advantage, not the forward path.

---

## What changed

### Change — Null-B demoted from binding co-null to advisory contextual diagnostic

**Before (D0 P7 Leg 1, as amended by D0-amendment-003):** both Null-A and Null-B must
exhibit conjunction-FPR ≤ α₀ = 0.05 for a cell to pass FPR control. A cell with
conjunction-FPR > 0.06 under **either** null is `FPR_EXCLUDED`. `METHOD_DEFECT` fires
if ≥ 5 of 6 cells fail under **either** null.

**After:** **Null-A (matched-random placement on the real path) is the sole binding null**
for FPR control. All thresholds (α₀ = 0.05, 0.06 tolerance, >2/3 defect rule) apply
exclusively to Null-A conjunction FPR. Null-B conjunction FPR remains **computed and
reported** as an **advisory contextual diagnostic** only: it characterises the geometry
structure of the STRONG-STAT conditioning but does **not** gate cell classification or
experiment verdict.

**Why Null-A is the appropriate sole binding null:**

1. **Null-A tests the correct null.** Null-A scrambles placement — i.e., it tests whether
   the event timing within the real path provides a detectable edge. This is the genuine
   causal claim for a pattern-entry signal: entering at the harami bar (rather than a
   random moment on the same path) produces positive conjunction expectancy. Null-A's
   FPR directly bounds the probability that this causal claim fires falsely.

2. **Null-B's geometric inflation is a known structural artifact, not a signal.** Null-B
   was designed as a path-continuity null (does the signal need a coherent forward path,
   or does any path-like sequence suffice?). It never intended to equate the entry
   geometry of STRONG-STAT events with the geometry of general pool entries. The inflation
   is a design limitation, not evidence against the signal.

3. **The three conjunction legs under Null-B are perfectly co-determined.** For all six
   cells, `fpr_med_mean_nullB = fpr_full_conj_nullB` (dropping `beats-RM` from the Null-B
   conjunction changes nothing — the geometry advantage drives all three legs
   simultaneously). This confirms the inflation is not a legs-specific artefact; removing
   any individual leg would not improve Null-B control.

4. **Null-B remains informative as a path-scramble diagnostic.** It is retained in
   reported output to characterise the signal's dependence on path continuity and the
   magnitude of the geometry gradient across timeframes. It is disclosed in the EXP-071
   freeze file (P8) as context for TEST interpretation.

---

## Revised verdict structure

Under this amendment, the per-cell classification and experiment-level verdict use
**Null-A conjunction FPR only** as the binding gate:

| Criterion | Rule |
| --- | --- |
| Cell PASS | Null-A conjunction FPR ≤ 0.05 **and** non-degenerate CI **and** finite MDE |
| Cell retained-with-record | Null-A conjunction FPR ∈ (0.05, 0.06] |
| Cell FPR_EXCLUDED | Null-A conjunction FPR > 0.06 |
| METHOD_DEFECT | ≥ 5 of 6 cells have Null-A conjunction FPR > 0.06, or any PASS cell has a degenerate CI, or determinism fails |
| CALIBRATION_DELIVERED | all 6 cells classified (PASS or retained), Null-A FPR controlled in all, P12 reconciliation ≤ 1e-9, determinism PASS |

**Null-B FPR** is reported in `fpr_per_cell.csv`, `calibration_map.csv`, and
`results.md` with the label `advisory` and is explicitly excluded from the gating logic.

---

## Per-cell outcome under this amendment

| Cell | Null-A conj FPR | Null-B conj FPR (advisory) | Cell verdict | Temporal flag | MDE |
| --- | --- | --- | --- | --- | --- |
| GBPUSD-5m | 0.035 | 0.027 | PASS | GROWING | 0.025 ATR |
| GBPUSD-1h | 0.014 | 0.363 | PASS | DECAYING | 0.025 ATR |
| NZDUSD-1h | 0.031 | 0.340 | PASS | DECAYING | 0.025 ATR |
| NZDUSD-2h | 0.031 | 0.759 | PASS | STABLE | 0.025 ATR |
| GBPJPY-30m | 0.014 | 0.161 | PASS | DECAYING | 0.025 ATR |
| US2000-4h | 0.018 | 0.773 | PASS | STABLE | 0.025 ATR |

**Experiment-level verdict: CALIBRATION_DELIVERED.**

---

## Multiplicity / TEST-read impact (P15-required)

- **New multiplicity slot consumed:** No. HYP-023 remains a single method-calibration
  item. No new candidate, variant, detector, or parameter branch is introduced. No re-run
  is required; this amendment changes the interpretation and documentation of existing
  results only. `multiplicity-registry.md` HYP-023 row is annotated to note the amendment.
- **New TEST read consumed:** No. EXP-070 remains TRAIN-only (first 49% per file).
  `test-read-ledger.md` is unchanged. No TEST or holdout row is loaded.
- **TEST family (P5):** Unchanged — six cells, all PASS under the amended rule.
  The EXP-071 binding family is therefore **all six P5 cells**: GBPUSD-5m, GBPUSD-1h,
  NZDUSD-1h, NZDUSD-2h, GBPJPY-30m, US2000-4h (ex-EURUSD).
- **Calibrated margins (P9 condition 4):** Unchanged — derived from the same Null-A
  draws that were already run. All six cells' calibrated margins are finalized in the
  EXP-071 freeze file.

## Affected artifacts (to be updated in this change)

- `python/experiments/EXP-070/scope.md` — amendment header updated.
- `python/experiments/EXP-070/analysis-plan.md` — amendment header updated.
- `python/experiments/EXP-070/results.md` — full rewrite: all 6 cells PASS,
  CALIBRATION_DELIVERED, Null-B advisory with geometry-bias explanation.
- `python/experiments/EXP-070/report.md` — new document reflecting final verdict.
- `python/experiments/EXP-070/governance/post-experiment-review.md` — Stage 8 review.
- `python/experiments/INDEX.md` — EXP-070 row added.
- `docs/experiments-docs/families/cf-ha-harami-001/INDEX.md` — EXP-070 card added.
- `docs/experiments-docs/INDEX.md` — Phase 016 checkpoint status updated.

## Operator sign-off

Operator directed this amendment on 2026-06-18 after reviewing the structural
geometry-bias analysis and selecting Option 3: accept Null-A as the sole binding null;
demote Null-B to advisory; change verdicts accordingly; no re-run. This entry
constitutes the P15 sign-off record. The D0-predeclarations.md "both-nulls" clause is
superseded by this amendment on the terms above. All other D0 items (P1–P6, P8–P14) and
all D0-amendment-003 provisions (except the "both-nulls" binding gate) stand unchanged.
