# G-019 Gate Review — Family-Selection Availability Screen (Terminal)

**Date:** 2026-06-23
**Gate:** G-019 (Phase 019 terminal gate — *selection* of the next entry-side family by family-agnostic
availability screening; **not** candidate screening, **not** a tradability verdict).
**Adjudication basis:** the predeclared **D5 mechanical verdict rule** (`D0-predeclarations.md` §D5) over the
**D2b multiplicity-adjusted permuted-axis admission gate**, applied against the realized EXP-086 (Screen M)
and EXP-087 (Screen X) statistics. Rubric frozen pre-slate in `G-019-gate-criteria.md`.
**Outcome:** **ALL SCREENED AXES NOT ADMITTED → TERMINAL BRANCH.** Both candidate families are **CLOSED**:
**CF-VOLEXP-001 (axis M)** and **CF-XSECT-001 (axis X)**. Screen F (`CF-FLOW-001`, EXP-088) is
**not opened** (reserved-conditional; operator did not request a third comparison). Price-derived
information — single-series **magnitude** *and* cross-sectional **relational** — is **exhausted on this
dataset**; the frontier is **non-price data acquisition** (operator decision), reached at **0 candidate
slots, 0 counted TEST reads**.
**Holdout:** never touched at any point in Phase 019. `test-read-ledger.md` **unchanged** (all 48 strata stay
0/2 open). Operator-directed phase closure ("G-019 review — close both families").

> **Amendment (2026-06-23, operator-directed — scoping, not re-adjudication).** The "price-derived information
> is exhausted" framing above is **scoped** to what Phase 019 (and the four prior closed families) actually
> screened: single-series **magnitude**, cross-sectional **relational**, and single-series directional
> **continuation** entries. A **mean-reversion (fade) entry mechanism was never screened**, so the terminal
> sentence is read as *the screened continuation / magnitude / relational surface is exhausted on this
> dataset* — **not** as a verdict over every price-derived lever. The routing to **non-price data acquisition
> was overridden by operator decision (2026-06-23)** to open **CF-MR-001** (Phase 020), which screens the
> unscreened mean-reversion mechanism plus a strategy-agnostic volatility-regime partition. The mechanical
> adjudication (empty ADMITTED set; CF-VOLEXP-001 and CF-XSECT-001 CLOSED and retained) is **unchanged**; only
> the over-broad framing is narrowed.

---

## 1. Decision

The two screened information axes are adjudicated by the predeclared §2 rule:

| Axis | Family | S_A | S* (Q95) | axis perm_p | **Holm-adj p** | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| **M — single-series magnitude** | CF-VOLEXP-001 | 3 | 2 | 0.0326 | **0.0652** | **NOT ADMITTED** |
| **X — cross-sectional** | CF-XSECT-001 | 1 | 1 | 0.323 | **0.323** | **NOT ADMITTED** |
| F — order-flow | CF-FLOW-001 | — | — | — | — | **NOT OPENED** (reserved-conditional) |

**The ADMITTED set is empty.** Per the D5 programme-routing table this is the **terminal branch**
(stated a priori): no axis earns a candidate slot; both families are CLOSED and retained in the registry;
the programme frontier moves off price-derived information.

## 2. Relationship to the predeclared D5 verdict rule (mechanical)

`D0-predeclarations.md` §D5 / `G-019-gate-criteria.md` §2:

```
ADMITTED(A) iff  S_A > S*  AND  Holm-adjusted axis-level permutation p(A) <= 0.05   (cross-axis FWER 0.05)
```

**Cross-axis Holm step-down** over the realized axis-level permutation p-values (two axes screened; F not run):

- Ordered ascending: `p(M)=0.0326`, `p(X)=0.323`.
- Holm step 1: compare the smallest, `0.0326`, to `α/k = 0.05/2 = 0.025`. **0.0326 > 0.025 → fail to reject → stop.**
- Holm-adjusted: `p_adj(M) = min(1, 2·0.0326) = 0.0652`; `p_adj(X) = max(0.0652, 1·0.323) = 0.323`.

Therefore:

- **Axis M — NOT ADMITTED.** The per-axis count conjunct holds (`S_M=3 > S*=2`), **but the binding cross-axis
  Holm conjunct fails** (`p_adj = 0.0652 > 0.05`). EXP-086's provisional `ADMITTED` was an explicitly
  **single-axis, NON-BINDING** disposition; once the cross-axis multiplicity control that the slate exists to
  enforce is applied, the borderline NR7-tail signal does not separate from a best-of-axes noise selection.
  The family index and registry foresaw exactly this ("cross-axis Holm can only raise perm_p=0.0326; little
  headroom under 0.05") — Holm raises it across the 0.05 line. **The closure is the predeclared mechanical
  consequence of the D5 rule, not operator discretion** (the operator's "close both families" direction
  coincides with the rule's output, it does not override it).
- **Axis X — NOT ADMITTED.** Fails the count conjunct outright (`S_X=1 ≤ S*=1`) and the Holm conjunct
  (`p_adj=0.323`). Provisional `NOT_ADMITTED` confirmed binding.

### 2.1 Per-axis closure framing (typical-range vs tail; dead-by-absence vs exonerated)

- **CF-VOLEXP-001 (M) — single-series-magnitude cell CLOSED.** The two D3.M reads are reported separately
  (D5 split honoured, §3.4): the **typical-range read is dead on both primitives** (NR7 conditioned median
  range *below* random, Δ̂ med ≈ −0.28 ATR — within/below the null band); the **tail/bimodality read** carried
  the only non-null thread (NR7/tail `S=3`, single-axis perm_p 0.0066) but **does not survive cross-axis
  FWER** (Holm-adj 0.0652) and is tiny (~0.5–1.1 extra catastrophe events/100) and **tail-only ⇒ long-vol**
  by the harvest-model guard, never directional. With neither read clearing the binding gate, the
  single-series × magnitude cell of the availability 2×2 is **closed**: no admissible availability. (The
  conservative/anti-masking caveat — tailmass Δ>0 broadly present but only 15m-powered — is recorded; it does
  not change the FWER-controlled verdict and is the disclosed boundary for any future re-scope.)
- **CF-XSECT-001 (X) — cross-sectional × directional cell CLOSED, dead-by-absence.** `S_X=1` falls **below**
  the D2a coin-flip band [17,28] (underperforms even a coin flip); cross-sectional conditioning **degrades**
  favourable availability at fast domains (per-domain mean Δ̂ 15m −0.26 / 1h −0.15 / 4h ≈0), homogeneous and
  audit-confirmed **not masking**. The a-priori mechanism favourite earns no admission. This is
  **`dead-by-absence`, distinct from `EXONERATED`** (which requires sitting *within* the band): the cell is
  closed and not silently reopened, but it underperformed rather than merely matched the null.

Both families' downstream stacks (exit, sizing, P&L) were never invoked — these are availability screens, and
the levers are exonerated upstream (EXP-084). No re-parameterization of either cell reopens it; reopening
requires a genuinely new information source under its own D0/G0.

## 3. Adjudication checklist (G-019-gate-criteria §3) — affirmative confirmation

1. **Bite-check GREEN (precondition) — PASS.** The D2b gate passed its fixture check at G0 (`bite-check/`,
   report sha256 `208dfb3f…`, byte-identical 2nd pass): pure-noise axis admitted 0.0248 ≤ FWER 0.05 (not
   vacuous); planted +0.20-ATR/8-cell axis power 1.0 (not impossible); routing invariant across
   FWER {0.025,0.05,0.10}; self-calibrating under inflated per-cell FP; Holm step-down verified correct. The
   gate is valid; G-019 is not void.
2. **Permutation null validity — PASS.** Both screens ran the permuted-axis null at production scale
   (`N_PERM=5000`, MC-stable vs 1000); distributions well-formed (M null mean ≈2.27 matching `C·Φ(−1.645)`;
   X non-degenerate); the cross-axis Holm step-down applied over the realized axis-level permutation p-values
   (§2). Both screens deterministic (byte-identical second pass, permutation stream included).
3. **Per-axis verdict — recorded (§1, §2)** with realized `S_A`, `S*`, and Holm-adjusted p quoted.
4. **Screen-M split honoured — PASS.** Typical-range and tail reads reported separately; **no pooled `|move|`
   number drove any disposition** (prohibited by D3.M); the magnitude-budget (two-sided-cost) result was
   carried as necessary-not-sufficient disclosure only. No magnitude admission is made.
5. **Ranking — N/A (empty admitted set).** No axis admitted; no exploration queue to order. For the record the
   frozen ranking metric (axis-level permutation z) would have placed M (z=2.62) ahead of X (z=1.26); neither
   clears admission.
6. **Integrity — PASS.** EXP-086 audit PASS (0C/2W/4I, both Warnings non-material); EXP-087 audit PASS
   (0C/0W/2I). Determinism byte-identical; TRAIN sub-split only (analysis-TEST + final-30% holdout never
   sliced); `test-read-ledger.md` unchanged; 0 slots / 0 counted reads; real-price metrics only.
7. **No goalpost-moving — PASS.** The frozen D2 thresholds and D3 endpoints were not retro-edited after seeing
   any axis outcome; the per-stratum doctrine (LESSON-001) was enforced and every collapsed convenience flag
   treated NON-BINDING. The binding rule was frozen in `G-019-gate-criteria.md` before the slate ran.

## 4. Programme routing (mechanical consequence — D5 / gate-criteria §4)

**ADMITTED set empty ⇒ terminal branch.** This was stated a priori:

> *Price-derived information — single-series **and** relational — is exhausted on this dataset. The frontier is
> **non-price data acquisition** (order book, cross-asset, fundamentals) — a data decision, not a modelling
> one — escalated to the operator. Reached having spent 0 reads and 0 slots.*

Concretely, re-derived from primary evidence across four closed families:

| Cell of the availability 2×2 | Status after G-019 |
| --- | --- |
| single-series × **directional** (price geometry) | dead — CF-AVWAP-001 (ANCHOR_MOVE_FLAT, EXP-047), CF-HA-HARAMI-001 (CLOSE_FAMILY), CF-CAPGEO-001 (NOT_CONFIRM, EXP-084); availability ≈ random, exit-invariant. |
| single-series × **magnitude** | **CLOSED at G-019** — CF-VOLEXP-001: typical-range dead, NR7-tail long-vol thread fails cross-axis FWER (Holm-adj 0.0652). |
| **cross-sectional** × directional | **CLOSED at G-019** — CF-XSECT-001: dead-by-absence (`S=1` below coin-flip band; degrades availability at fast domains). |
| order-flow × {directional, magnitude} | **NOT screened** — CF-FLOW-001 reserved-conditional, not opened. The one price-adjacent cell left unmeasured; tick-volume is broker-dependent and was found inert once (EXP-046). Available as a future cheap screen if the operator wants to exhaust it before pivoting to non-price data; **not** required to reach the terminal verdict on the *price-geometry + relational* surface. |

**Action:** Phase 019 is **CLOSED** with **no family promoted**. CF-VOLEXP-001 and CF-XSECT-001 are retired to
the registry file-drawer (retained, never deleted or reused). The next programme decision is an **operator data
decision** — acquire a genuinely orthogonal non-price information source (order book / cross-asset structure /
fundamentals), or optionally run the reserved Screen F first — **not** another re-parameterization of any
exhausted cell. No candidate slot or counted read is spent to reach this frontier.

## 5. Integrity expectations at adjudication (carried)

- **Holdout sealed** throughout Phase 019; the final-30% global holdout never loaded. TRAIN sub-split only.
- **TEST discipline:** 0 counted TEST reads; analysis-TEST and final-30% holdout never sliced;
  `test-read-ledger.md` unchanged (all 48 strata stay 0/2 open).
- **Determinism / anchors:** byte-identical second passes confirmed in both screens, permutation null included.
- **No goalpost-moving:** frozen D2 thresholds / D3 endpoints not retro-edited; LESSON-001 per-stratum doctrine
  enforced.
- **File drawer:** both screened axis outcomes (NOT ADMITTED — M tail-only-fails-FWER, X dead-by-absence) are
  **retained** in the registry and the multiplicity-registry Phase 019 batch, never deleted or reused; both
  cells are closed and not silently reopened.

---

*Companion documents: [`design.md`](design.md) · [`D0-predeclarations.md`](D0-predeclarations.md) §D5 ·
[`G-019-gate-criteria.md`](G-019-gate-criteria.md) · candidate families
[`../../../signal-registry/candidate-families/family-selection-phase-019.md`](../../../signal-registry/candidate-families/family-selection-phase-019.md) ·
multiplicity registry Phase 019 batch · EXP-086 / EXP-087 reports.*
