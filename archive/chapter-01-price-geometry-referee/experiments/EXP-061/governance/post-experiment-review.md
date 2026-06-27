# Post-Experiment Governance Review — EXP-061 (dual-object re-run)

**Stage:** 8 (consolidated post-experiment governance) · **Date:** 2026-06-17
**Reviewed:** `audit.md`, `results.md`, `report.md`, index/registry updates, `governance/pre-execution-review.md`.
**Context:** Re-run under `D0-amendment-001-dual-parallel-substrate.md`; **supersedes the prior
single-object (native-only, mislabelled "hybrid") result in place.** This review covers the 6-arm
output (`H0`/`RH0` hybrid, `M0`/`RM0` native, `Z0`/`RZ0` disclosed). The prior post-exec review is void
for the superseded result.

## Verdict

```text
VERDICT: APPROVE
```

## Checks

**Audit (`audit.md`).** PASS — 0 Critical, 0 Warning, 2 Info. No issues block interpretation. The two
Info notes (P15 intrabar approximation — inherited programme convention; DE30 truncated history —
non-binding, no native or hybrid generalisation cell on DE30) are disclosed and acceptable.
Reconciliation under the **corrected P12 roles**: native `M0`↔EXP-060B BENCH-MA and `Z0`↔EXP-053/060B
BENCH-ZZ exact 99/99 at 1e-9; the anchorless hybrid `H0` conditioning mask verified transitively via
`Z0` 99/99 (`h0_has_outcome_anchor=false`, `h0_cond_verified_via_z0=true`). Determinism ✓ (17/17
byte-identical replays), causality ✓ (0 violations), invariants ✓ (matched-count per object OK),
`is_defect: false`. The new hybrid arms (`H0`/`RH0`) use disjoint dedicated RNG purposes; `M0/RM0/Z0/RZ0`
keep the original purposes (byte-identical to EXP-060B).

**Interpretation (`results.md`, `report.md`).** Anchored to the predeclared dual-object analysis fork.
Both objects judged **individually and never pooled** (Amendment 001). Native `M0` generalises branch is
mechanically met (median-viable ∧ beats `RM0` ∧ P11: 8 cells / 6 instruments / 8 non-4h). Hybrid `H0` is
correctly classified **EVIDENCE_AGAINST** (generalises 1 cell; powered grid composes 99 cells ⇒ not
INCONCLUSIVE). The phase verdict = stronger object (native EVIDENCE_FOR), per design §7. No goalpost
movement — binding endpoint stayed the median (P14/P3); the mean was P4 diagnostic only. The headline
correction (prior EVIDENCE_FOR was a native result; the genuine hybrid object does **not** generalise) is
stated plainly and not over-claimed. The lone hybrid cell is explicitly flagged as marginal. Negative/
limiting findings (MODERATE native breadth 8/99, FX-major concentration, hybrid marginal cell, TRAIN-only,
gross-only) are first-class. Follow-ups framed as distinct L2–S4 scopes.

**Holdout / look-ahead / real-price (Core Constraints 5–7).** TRAIN-only; nested `slice(0, train_rows)`
F01 prefix, no full sort/collect, fenced `CloseTime ≤ train_end_ts`; TEST and final-30% holdout never
read. Both conditioning masks (ZigZag for hybrid, MA-segment for native), `M_sofar`, benchmark levels,
and caps reference only pre-entry confirmed pivots (causality gate ✓, 0 violations); matched-random
entries constructed causally. Real-price metrics throughout (MA on real close; HA for detection only —
no HA price in any metric). Compliant.

**Scope discipline (Constraint 3).** The object set is exactly the 6 predeclared objects
(`H0`/`RH0`/`M0`/`RM0`/`Z0`/`RZ0`); hybrid and native never pooled in any metric, contrast, or
composition; no post-result variant or cell selection; no scope expansion after approval. Complexity
within budget (3 methods, 5 plots, 0 new `xen/` modules). Stale superseded outputs from the prior
single-object run (`results/m0_rm0_map.csv` and 3 prior plots) removed; the results/plots directories now
contain only the dual-object outputs the current code emits.

**Signal-registry disposition.** Confirmed. EXP-061 is an intermediate per-object characterisation readout
feeding the terminal G-015 after the full Phase 015 slate — no closure or candidate registration here.
The supersession status, however, **is** bookkeeping-relevant and has been advanced:
- `candidate-families/harami.md`: HYP-014 card advanced SUPERSEDED → **CHARACTERISED (dual-object): native
  EVIDENCE_FOR / hybrid EVIDENCE_AGAINST**; family stays **REGISTERED, OPEN**.
- `multiplicity-registry.md`: `CF-HA-HARAMI-001/HYP-014 — EXP-061` advanced SUPERSEDED → **CHARACTERISED
  (dual-object)**; item retained (never deleted/renamed); G-015 routing note carried.
- `test-read-ledger.md`: unchanged — no HA-harami TEST stratum exists or was touched (0 TEST reads). Verified.
- **0 candidate slots consumed** — registration occurs only at a future G-015 PROCEED. Correct.
- Disposition recorded in `report.md`/`results.md` and encoded in `run_metadata.json` /
  `generalisation_readout.json`.

**Indexes.** `python/experiments/INDEX.md` row updated to the dual-object outcome; master
`docs/experiments-docs/INDEX.md` checkpoint live-status updated (EXP-061 complete, EXP-062/063 still
pending); family detail index `families/cf-ha-harami-001/INDEX.md` ToC + card rewritten for the
dual-object result.

**Phase alignment.** Consistent with Phase 015 design §3–§7, D0-predeclarations P1–P12, and Amendment 001.
EXP-061 is the L1 benchmark-geometry generalisation readout; it does not close the phase or adjudicate G-015.

## Notes for the G-015 desk (not blocking)

The dual-object re-run materially sharpens the MA-substrate case: the edge is a **matched-substrate
conditioning property** — native (MA-segment-conditioned) generalises to the simplest benchmark geometry
(8 cells / 6 instruments), but the genuine hybrid (ZigZag-conditioned) object does **not** (1 cell). This
resolves the prior mislabelling: the family's headline "hybrid" edge was always native. The remaining
L2–S4 slate (EXP-062–068, dual-object) should carry this native/hybrid split through every read before
G-015 adjudicates on the object that actually expresses the edge.
