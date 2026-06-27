# G-019 Gate Criteria — Family-Selection Availability Screen (PENDING — pre-adjudication)

**Date:** 2026-06-22 (gate *definition*; **not yet adjudicated**).
**Gate:** G-019 (Phase 019 terminal gate — *selection* of the next entry-side family by family-agnostic
availability screening; **not** candidate screening, and **not** a tradability verdict).
**Status:** **PENDING.** This document fixes the **mechanical rubric** the future G-019 adjudication will
apply, frozen here before the slate runs (freeze the rule, not the story — retrospective §2.1). The
adjudication itself (a `G-019-gate-review.md`, mirroring the G-017 format) is written **after**
EXP-086/087 (and EXP-088 if opened), reading the realized numbers against this rubric. Nothing here reads
data, spends a slot, or touches the holdout.
**Adjudication basis:** the predeclared **D5 mechanical verdict rule** (`D0-predeclarations.md` §D5) over
the **D2b multiplicity-adjusted admission gate**.

---

## 1. What G-019 decides (and what it does not)

G-019 emits a **ranked admit / exonerate / inconclusive inventory** over the screened information axes —
single-series **magnitude** (M, EXP-086), **cross-sectional** (X, EXP-087), and optionally **order-flow**
(F, EXP-088). It decides:

- **which untested cells of the availability 2×2 (design §2) carry signal-conditional availability beyond a
  multiplicity-adjusted null**, and therefore earn a candidate family; and
- **in what order** those families are opened (best-first by the frozen Δ-over-random ranking metric).

It does **not**:

- make any tradability, edge, or pass/fail claim about a strategy (these are availability disclosures);
- spend a candidate slot or a counted TEST read (TRAIN-only, holdout sealed);
- open any family — each `ADMITTED` axis is promoted to its **own** CF-XXX spec and checkpoint at a
  **future G0/D0**, not here.

## 2. The mechanical rule (from D0 §D5 — reproduced for adjudication)

```
For each information axis A in {M, X, (F)}:

  ADMITTED(A)      iff  realized S_A > S*  (permuted-axis Q95 ceiling at the realized cell count, D2b)
                   AND  Holm-adjusted axis-level permutation p(A) <= 0.05   (cross-axis FWER 0.05)
  EXONERATED(A)    iff  S_A within the D2a null band on EVERY read (Screen M: BOTH typical-range AND tail)
  INCONCLUSIVE(A)  iff  the permuted null cannot separate at the realized cell count (no power)
```

**Screen-M shape rule (binding):** a Screen-M admission earned on the **tail/bimodality** read alone is a
**long-vol** admission — it is queued as a *volatility-expansion* family (CF-VOLEXP-001) under the
two-sided-cost harvest model (design §4.4), **never** as a directional edge. A typical-range admission is
queued as a directional/range family. The distinction is recorded explicitly in the gate review.

## 3. Adjudication checklist (what the G-019 review must affirmatively confirm)

Each item is read **per stratum / per cell** (LESSON-001); no collapsed cross-cell boolean is binding.

1. **Bite-check GREEN (precondition).** The D2b admission gate passed its fixture check before G0: pure-noise
   axis admitted ≤ FWER (not vacuous); planted non-random axis admitted with power (not impossible); routing
   invariant across the pre-registered sensitivity band. If the bite was not GREEN at G0, the gate is void.
2. **Permutation null validity.** `N_PERM` at production scale; the permuted-axis statistic distribution is
   well-formed (not degenerate); the cross-axis Holm step-down is applied over the three axis-level
   permutation p-values.
3. **Per-axis verdict** by the §2 rule, with the realized `S_A`, `S*`, and Holm-adjusted p quoted.
4. **Screen-M split honoured.** Typical-range and tail reads reported **separately**; no pooled `|move|`
   number drove any admission; any magnitude admission carries the magnitude-budget (two-sided-cost) result.
5. **Ranking.** Admitted axes ordered by the frozen metric (axis-level permutation z-score, tie-broken by
   trimmed-mean per-cell Δ); the order is the exploration queue.
6. **Integrity.** Determinism byte-identical (including the permutation stream at fixed seed); TRAIN-only
   (analysis-TEST + holdout never sliced); `test-read-ledger.md` unchanged; 0 slots / 0 counted reads;
   real-price metrics only.
7. **No goalpost-moving.** The frozen D2 thresholds and D3 endpoints were not retro-edited after seeing any
   axis's outcome.

## 4. Programme routing (mechanical consequence)

| Adjudicated state | Consequence |
| --- | --- |
| **≥1 axis `ADMITTED`** | Open the **top-ranked** admitted family next at its own G0/D0 (promote its CF-XXX spec from `candidate-families/family-selection-phase-019.md`, with its own readiness/characterization slate). Queue the remaining admitted axes best-first — **every admitted axis is eventually opened** (ranking orders the queue; it never prunes it). A tail-only Screen-M admission opens as CF-VOLEXP-001 under the harvest model. |
| **All axes `EXONERATED`** | **Terminal branch (stated a priori).** Price-derived information — single-series **and** relational — is exhausted on this dataset. The frontier is **non-price data acquisition** (order book, cross-asset, fundamentals) — a *data* decision, not a modelling one — escalated to the operator. Reached having spent **0 reads and 0 slots**. |
| **Any axis `INCONCLUSIVE`** | Disclosed; the axis is neither admitted nor exonerated; a finer-resolution re-scope is a separate future decision, not an admission. |

## 5. Integrity expectations at adjudication (carried)

- **Holdout sealed** throughout Phase 019; the final-30% global holdout never loaded. TRAIN sub-split only.
- **TEST discipline:** 0 counted TEST reads; the analysis-TEST stratum and final-30% holdout never sliced.
  `test-read-ledger.md` unchanged (all 48 strata stay 0/2 open).
- **Determinism / anchors:** byte-identical second passes; the permuted-axis null reproducible at its fixed
  seed-stream.
- **No goalpost-moving:** frozen D2 thresholds / D3 endpoints not retro-edited; the per-stratum doctrine
  (LESSON-001) enforced — any collapsed convenience flag is NON-BINDING.
- **File drawer:** every screened axis outcome (admit / exonerate / inconclusive) is **retained** in the
  registry, never deleted or reused; an `EXONERATED` cell is closed and not silently reopened.

---

*Companion documents: [`design.md`](design.md) §7 (gate criteria) · [`D0-predeclarations.md`](D0-predeclarations.md)
§D5 (mechanical rule) · candidate families under consideration
[`../../../signal-registry/candidate-families/family-selection-phase-019.md`](../../../signal-registry/candidate-families/family-selection-phase-019.md).
The adjudicated outcome will be written to `G-019-gate-review.md` (this directory) after the slate.*
