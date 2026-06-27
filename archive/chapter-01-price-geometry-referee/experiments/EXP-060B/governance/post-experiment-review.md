# Post-Experiment Governance Review — EXP-060B

**Stage:** 8 (consolidated post-experiment governance) · **Date:** 2026-06-17
**Reviewed:** `audit.md`, `results.md`, `report.md`, index/registry updates, `governance/pre-execution-review.md`.

## Verdict

```text
VERDICT: APPROVE
```

## Checks

**Audit (`audit.md`).** PASS — 0 Critical, 2 Warning, 3 Info. No Critical/defect blocks interpretation. The two
Warnings (W1 lead narrow/4h-concentrated; W2 median overstates tradeable expectancy) are interpretive
disclosures, both carried forward into `results.md` and `report.md`. Reconciliation exact 99/99
(Z3↔EXP-060-A3, M3↔EXP-060-maseg, exit weights); determinism ✓, causality ✓ (0 violations), invariants ✓,
`is_defect: false`. The decisive new computation (RM3) was verified non-degenerate and apples-to-apples; the
new mean bootstrap verified reproduction-safe (dedicated RNG). I3 (plan mislabeled the M3−RM3 contrast as
paired; code correctly used independent `contrast_ci`) is recorded in audit, results, and report — code is
correct, plan note flagged. Acceptable.

**Interpretation (`results.md`).** Anchored to the predeclared analysis-plan §6 fork; the `SUBSTRATE_LEAD_FOUND`
branch is mechanically met (M3 median-viable ∧ beats RM3 ∧ mean-viable composes P11: 14 cells/9 instruments).
No goalpost movement — the binding endpoint stayed the **median** (P14); the mean was used only to make the
"lead" criterion stricter (conservative), exactly as predeclared. Negative/limiting findings (mean ≈0;
4h-concentration) are stated as first-class, not buried. Evidence and interpretation separated; audit caveats
included. Follow-ups are framed as new scopes, not extensions.

**Report (`report.md`).** Uses the approved, predeclared result category (`SUBSTRATE_LEAD_FOUND`). Quantitative
results carry sample sizes (m, cell/instrument counts), effect sizes (median/mean, contrast CI_low), and audit
caveats. No claims absent from `results.md`/`audit.md`/raw outputs. Links to all artifacts.

**Holdout / look-ahead / real-price (Core Constraints 5–7).** TRAIN-only; nested `slice(0, train_rows)` prefix,
no full sort/collect, fenced `CloseTime ≤ train_end_ts`; TEST and final-30% holdout never read. MA(20,50) and
RM3 construct state/caps from pre-entry confirmed crossovers only (causality gate ✓, 0 violations). Real-price
metrics throughout (MA on real close; HA for detection only — no HA price in any metric). Compliant.

**Scope discipline (Constraint 3).** Single diagnostic question; the object set is exactly the 10 predeclared
objects; no post-result variant selection; no scope expansion after approval. Complexity within budget
(4 methods, 5 plots, 0 new `xen/` modules — local helpers only).

**Signal-registry disposition (recorded, registry-relevant).** Confirmed present and consistent:
- `multiplicity-registry.md`: `CF-HA-HARAMI-001/HYP-013b — EXP-060B` advanced **PLANNED → CHARACTERISED —
  SUBSTRATE_LEAD_FOUND**; the G2 routing note updated to the actual outcome (do not close without a scoped
  MA-substrate follow-up targeting the skew/mean).
- `candidate-families/harami.md`: 014-B slate status updated to the EXP-060B outcome; family stays
  **REGISTERED, OPEN**.
- `test-read-ledger.md`: unchanged — no HA-harami TEST stratum exists or was touched (0 TEST reads). Verified.
- **0 candidate slots consumed** — no candidate registered here (registration occurs only at a future G2
  PROCEED on an MA-substrate scope). Correct.
- Disposition explicitly recorded in `report.md`.

**Indexes.** `python/experiments/INDEX.md` row added; master `docs/experiments-docs/INDEX.md` family-table
EXP-range (EXP-048–060B) and checkpoint live-status updated; family detail index
`families/cf-ha-harami-001/INDEX.md` ToC + five-field card added. (Note: EXP-060 itself lacks a family detail
card — a pre-existing gap from its own documentation stage, outside EXP-060B's remit; flagged for back-fill.)

**Phase alignment.** Consistent with 014-B design §4 (no intermediate gates; EXP-060B feeds the single G2) and
§8 routing. EXP-060B emits a characterisation readout only; it does not adjudicate G2 or close the phase.

## Notes for the G2 desk (not blocking)

EXP-060B materially changes the G2 input: EXP-060's CHARACTERISED_NOT_VIABLE rationale ("MA dominance is a
substrate property") is now qualified — the MA edge is partly a real signal effect (M3 beats own-substrate
random 85/99), so a clean closure is no longer well-supported. But the lead is median-only/narrow; the binding
obstacle is the skew/mean. The recommended route is a scoped MA-substrate follow-up with a bounded-downside
geometry, not closure and not a re-run of V2A×ADV-NONE.
