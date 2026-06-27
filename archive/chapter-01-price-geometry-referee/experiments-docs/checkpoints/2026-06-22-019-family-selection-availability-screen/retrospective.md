# Phase 019 Retrospective — Family-Selection Availability Screen (CLOSED)

**Phase:** 019 — family-agnostic availability screening to *select* the next entry-side family.
**Closed:** 2026-06-23 at **G-019** ([`G-019-gate-review.md`](G-019-gate-review.md)).
**Outcome:** **ALL SCREENED AXES NOT ADMITTED → TERMINAL BRANCH, NO FAMILY PROMOTED.**
**Cost:** 0 candidate slots, 0 counted TEST reads, holdout never touched, `test-read-ledger.md` unchanged
(all 48 strata stay 0/2 open). 2 screens run (EXP-086 M, EXP-087 X); Screen F (EXP-088) reserved, not opened.

> **Amendment (2026-06-23, operator-directed — scoping).** The terminal "price-derived information exhausted →
> non-price frontier" verdict is **scoped** to the screened surface (single-series magnitude, cross-sectional
> relational, and single-series directional **continuation** entries). A **mean-reversion (fade) mechanism was
> never screened**; the non-price routing was **overridden by operator decision (2026-06-23)** to open
> **CF-MR-001** (Phase 020). The mechanical Phase-019 adjudication is unchanged. See
> [`G-019-gate-review.md`](G-019-gate-review.md) amendment.

---

## 1. Objectives vs outcomes

| Objective (design.md) | Outcome |
| --- | --- |
| Screen untested cells of the availability 2×2 *before* committing a slot — institutionalise "measure availability first". | Done. Two untested cells screened TRAIN-only against the bite-checked D2b permuted-axis gate; the third (order-flow) reserved. |
| Emit a ranked admit/exonerate/inconclusive inventory at G-019. | Done. **Admitted set empty**: M NOT ADMITTED (Holm-adj p=0.0652>0.05), X NOT ADMITTED dead-by-absence (S=1≤S*=1, p=0.323). Ranking moot (no admits). |
| Select the next family if any axis admits; else reach the a-priori terminal branch. | **Terminal branch reached.** No family promoted; price-derived information exhausted on this dataset; frontier = non-price data acquisition (operator decision). |

## 2. What the phase established

1. **The cross-axis multiplicity control did its job.** Screen M produced a *single-axis* provisional ADMIT
   (`S_M=3 > S*=2`, perm_p=0.0326) on a borderline, tail-only NR7 signal. The binding cross-axis Holm
   step-down — the exact device the slate exists to enforce against "best-of-N noise axes" — raised the
   adjusted p to 0.0652, above 0.05. The gate prevented promoting a family on a borderline single-axis read.
   This is the methodology working as designed, not a near-miss to be relitigated.
2. **The single-series quadrant is now fully closed.** Directional was already dead three times
   (CF-AVWAP-001, CF-HA-HARAMI-001, CF-CAPGEO-001). Screen M closes the magnitude cell: typical-range dead,
   tail-only long-vol thread does not clear FWER. Single-series price geometry carries no admissible
   availability on this dataset.
3. **The relational cell is dead-by-absence, not merely null.** Cross-sectional conditioning *degraded*
   favourable availability at fast domains (mean Δ̂ 15m −0.26 / 1h −0.15) — the a-priori mechanism favourite
   underperformed a direction-matched random clock (late entry after the relative move). The programme's
   strongest non-price-geometry prior did not survive contact with its own data.
4. **Reached the frontier at zero cost.** The terminal verdict — price-derived information (single-series
   *and* relational) exhausted — was established with 0 slots, 0 counted reads, holdout sealed. The
   "availability first" discipline delivered its promised efficiency: a programme-level pivot decision bought
   without spending confirmation capital.

## 3. Lessons

- **LESSON (carry forward): a provisional single-axis disposition is not a result.** EXP-086's `ADMITTED` was
  explicitly NON-BINDING; the binding rule is the cross-axis conjunction. Future selection phases should keep
  the per-screen disposition visibly subordinate to the terminal cross-axis adjudication to avoid premature
  reading of a provisional flag as an admission.
- **The "measure availability first" institutional fix is validated.** Phases 004–018 measured availability
  late and repeatedly spent slots/reads discovering the entry had no edge. Phase 019 inverted this and reached
  a terminal programme decision for free. This pattern should govern the opening of any future family.
- **The order-flow cell (CF-FLOW-001) remains the one unmeasured price-adjacent axis.** Not required for the
  terminal verdict on price-geometry + relational, but it is the cheapest remaining screen if the operator
  wants to exhaust the price-adjacent surface before committing to non-price data acquisition. (Disclosure:
  tick volume is broker-dependent and was found inert once, EXP-046.)

## 4. Programme routing (next decision)

Per the predeclared D5 terminal branch and `G-019-gate-review.md` §4:

- **No family is opened.** CF-VOLEXP-001 and CF-XSECT-001 are CLOSED and retained (file-drawer; never reopened
  by re-parameterization). CF-FLOW-001 stays reserved.
- **The next decision is an operator data decision**, not a modelling one: acquire a genuinely orthogonal
  **non-price** information source (order book / cross-asset structure / fundamentals), or optionally run the
  reserved Screen F first to close the price-adjacent surface. No slot or counted read is spent to reach this.
- **Holdout remains globally sealed**; the 2-lifetime-per-stratum counted-read budget is fully intact
  (all 48 strata 0/2 open).

---

*Companion: [`design.md`](design.md) · [`D0-predeclarations.md`](D0-predeclarations.md) ·
[`G-019-gate-criteria.md`](G-019-gate-criteria.md) · [`G-019-gate-review.md`](G-019-gate-review.md) ·
candidate slate [`../../../signal-registry/candidate-families/family-selection-phase-019.md`](../../../signal-registry/candidate-families/family-selection-phase-019.md).*
