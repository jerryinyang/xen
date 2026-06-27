# G-020 Gate Criteria — Mean-Reversion Entry Availability Screen (PENDING — pre-adjudication)

**Date:** 2026-06-23 (gate *definition*; **not yet adjudicated**).
**Gate:** G-020 (Phase 020 terminal gate — admit / exonerate / inconclusive verdict on the CF-MR-001
mean-reversion entry family by a TRAIN-only availability screen; **not** a tradability verdict).
**Status:** **PENDING.** This document fixes the mechanical rubric the future G-020 adjudication applies,
frozen here before EXP-089 runs (freeze the rule, not the story). The adjudication (`G-020-gate-review.md`,
mirroring G-017/G-019) is written **after** EXP-089, reading the realized numbers against this rubric.
Nothing here reads data, spends a slot, or touches the holdout.
**Adjudication basis:** the predeclared **D5 mechanical verdict rule** (`D0-predeclarations.md` §D5) over the
**D2b multiplicity-adjusted permuted-axis admission gate**.

---

## 1. What G-020 decides (and what it does not)

G-020 emits an **admit / exonerate / inconclusive** verdict on CF-MR-001 and, if admitted, **which lever** (the
argmax sub-screen: bare MR, a specific volatility regime, or a variant) opens first. It decides:

- whether the **mean-reversion entry** — bare, vol-regime-partitioned, or with a trend/RSI filter — carries
  signal-conditional favourable availability beyond a multiplicity-adjusted null; and
- if so, the lever that names the first post-admission scope.

It does **not**: make any tradability/edge/pass claim (these are availability disclosures); spend a candidate
slot or counted TEST read (TRAIN-only, holdout sealed); or open batch 2 (that is a future G0/D0 on ADMIT).

## 2. The mechanical rule (from D0 §D5 — reproduced for adjudication)

```
S_ss = #cells beats-random                     for ss in {CORE, CORE+TREND, CORE+FILTER}   (leg 1)
     = #cells (beats-random AND beats-CORE)     for ss in {CORE-VOL-LOW, -MED, -HIGH}        (leg 2, binding)
S_fam = max over the 6 sub-screens of S_ss

  ADMITTED      iff  S_fam > S*  (joint permuted-axis Q95 over the 6 sub-screens, D2b)
                AND  axis perm_p <= 0.05                          (family-level FWER 0.05)
  EXONERATED    iff  every sub-screen S is within the D2a noise band (no sub-screen beats the joint null)
  INCONCLUSIVE  iff  the joint permuted null cannot separate at the realized cell count (no power)
```

No cross-axis Holm (single family; the joint max across the 6 sub-screens absorbs the within-family
multiplicity). The argmax sub-screen names the admitted lever; a **`/VOLREGIME` sub-screen wins only by the
binding beats-random ∧ beats-CORE conjunction** — the regime must ADD favourable availability over the pooled
CORE (leg 2 tested at full strength, not deferred), under a regime-membership-shuffle-within-CORE null.

## 3. Adjudication checklist (what the G-020 review must affirmatively confirm)

Each item is read **per stratum / per cell** (LESSON-001); no collapsed cross-cell boolean is binding.

1. **Bite-check GREEN (precondition).** The D2b gate passed its fixture check at the **6-sub-screen** structure
   and C=46 (`bite-check/bite_check.py` → `bite_check_report.json`, byte-identical second pass): pure-noise
   family admitted ≤ FWER (not vacuous; the 6-sub-screen joint max does not inflate — necessity shown:
   single-sub-screen S\* inflates to 0.40, joint S\* → 0.043); planted non-random family admitted with power
   and the argmax names the lever (not impossible); routing invariant across the FWER band; MC-stable
   1000↔5000. **Leg-2 legs (extended bite, re-confirmed before the run):** a pure-noise regime (random
   membership within CORE) adds **0** conjunctive (beats-random ∧ beats-CORE) wins; a planted additive-edge
   regime is detected with power. The single-test legs were GREEN at G0 (sha256
   `f01a000b1b230cd172cb4a6cde914014f1efb7ba6b5fc92d25376ee0b6ffab65`); the extended report must be GREEN and
   its sha recorded before EXP-089. If the bite was not GREEN, the gate is void.
2. **Permutation null validity.** `N_PERM` at production scale (5000), MC-stable vs 1000; the joint
   permuted-axis statistic distribution well-formed (not degenerate); seed-stream byte-reproducible.
3. **Per-sub-screen and family verdict** by the §2 rule, with realized `S_ss`, `S_fam`, `S*`, and axis
   perm_p quoted; the argmax sub-screen (the lever) named.
4. **Control & leg-2 validity.** Every sub-screen used the same all-bars **direction-matched `SUB-RANDOM`**
   (no regime-matching — ATR-normalisation removes the regime scale; confirm the matched-count reconciliation).
   The three `/VOLREGIME` sub-screens carried the **binding beats-CORE conjunction** (`Δ̂_core > 0`) under the
   regime-membership-shuffle-within-CORE null — confirm a regime counted toward `S` only when it ADDED edge
   over the pooled CORE, not when it merely inherited it.
5. **Member-cell readiness.** RSI-MR event coverage **≥15** per member cell (no upper bound — EXP-080 8000
   ceiling dropped for this dense entry); any `COVERAGE_EXCLUDED` cell recorded; realized counts reported
   (supersede design power figures).
6. **Integrity.** Determinism byte-identical (including the permutation stream); TRAIN-only (analysis-TEST +
   holdout never sliced); `test-read-ledger.md` unchanged; 0 slots / 0 counted reads; real-price metrics only.
7. **No goalpost-moving.** Frozen D1 definitions / D2 thresholds / D3 endpoint not retro-edited after seeing
   any sub-screen's outcome; the honest prior (availability ≈ random) does not bias the mechanical verdict in
   either direction.

## 4. Programme routing (mechanical consequence)

| Adjudicated state | Consequence |
| --- | --- |
| **ADMITTED** (`S_fam > S* ∧ perm_p ≤ 0.05`) | The argmax sub-screen names the lever. **CF-MR-001 consumes its first candidate slot**; a future G0/D0 opens batch 2 (readiness → characterization → capture geometry → TEST), expanding to regime×variant cross-cuts, the 25/75 scheme, and the contrarian arm, best-lever-first. The programme's first non-random price entry. |
| **EXONERATED** (every sub-screen in the D2a band) | Mean-reversion + the global vol filter carry no availability beyond noise on this dataset. The single-series-directional cell is dead under **both** continuation and mean-reversion. The programme returns to the **G-019 terminal frontier — non-price data acquisition** (operator decision), reached at **0 reads / 0 slots**. |
| **INCONCLUSIVE** (joint null cannot separate) | Disclosed; the family is neither admitted nor exonerated; a finer-resolution re-scope is a separate future decision, not an admission. |

## 5. Integrity expectations at adjudication (carried)

- **Holdout sealed** throughout Phase 020; the final-30% global holdout never loaded. TRAIN sub-split only.
- **TEST discipline:** 0 counted TEST reads; analysis-TEST + holdout never sliced; `test-read-ledger.md`
  unchanged (all 48 strata stay 0/2 open).
- **Determinism / anchors:** byte-identical second passes; permuted-axis null reproducible at its fixed seed.
- **No goalpost-moving:** frozen D1/D2/D3 not retro-edited; per-stratum doctrine (LESSON-001) enforced — any
  collapsed convenience flag is NON-BINDING.
- **File drawer:** the screened family outcome (admit / exonerate / inconclusive) and every deferred branch
  are **retained** in the registry, never deleted or reused; an exonerated cell is closed and not silently
  reopened by re-parameterization.

---

*Companion documents: [`design.md`](design.md) §5 · [`D0-predeclarations.md`](D0-predeclarations.md) §D5 ·
family spec [`../../../signal-registry/candidate-families/cf-mr-001.md`](../../../signal-registry/candidate-families/cf-mr-001.md).
The adjudicated outcome is written to `G-020-gate-review.md` (this directory) after EXP-089.*
