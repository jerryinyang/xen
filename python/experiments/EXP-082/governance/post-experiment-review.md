# Post-Experiment Governance Review — EXP-082

**Phase:** 018 (CF-CAPGEO-001) · **HYP:** HYP-003 (derive) · **Reviewer:** research-pipeline Stage 8 ·
**Date:** 2026-06-22 · **Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, and the index +
signal-registry updates.

## Constraint checks

| Constraint | Verdict | Evidence |
| --- | --- | --- |
| Holdout untouched | PASS | No market data read at all (only EXP-081 result files); `holdout_untouched=true`, `counted_test_reads=0` asserted on the EXP-081 fingerprint and recorded in `run_metadata.json`. Audit re-confirmed no `data/timebars/` path is reachable. |
| Look-ahead / causality | PASS | Pure function of TRAIN-only summary statistics; causal by construction (per-cell, no forward/cross-fold dependency) — the property that lets EXP-083 re-fit per fold-TRAIN without leakage. |
| Real-/synthetic-price discipline | PASS | No return/P&L/excursion computed; barriers carried in EXP-081 ATR units; no HA/Renko/synthetic price anywhere. |
| Single hypothesis / scope | PASS | One question (apply frozen D3 rule → triples); no scope creep (structural-guard read is explicitly disclosure-only); budget 0/0 tests, 3/≤3 plots, 1/≤1 module. |
| Determinism | PASS | Byte-identical replay; `derive_barriers` sha256-pinned; EXP-081 summary sha256 pinned. |
| Per-stratum verdict (EXP-076 C1 doctrine) | PASS | The verdict is a process-level completeness/determinism flag, not a collapsed cross-stratum edge PASS/FAIL; per-(cell,candidate) `disposition`/`valid` emitted; no pooled edge statistic presented as a verdict (there is no edge). Audit independently re-derived per stratum and confirmed no masking. |

## Verdict-forensics confirmation (Stage 8 mandatory)

- **Per-stratum re-derivation with masking check — PRESENT.** The audit independently re-derived all 552
  triples from the raw EXP-081 summary (0/552 mismatches), recounted the `m_anti`/`MAE_q90` split and the
  D1-vs-D2 divergence per stratum, and affirmatively confirmed the pooled headlines ("552/552 valid",
  "D1≡D2 184/184", "1 `m_anti` / 183 `MAE_q90`") are genuine per-stratum facts, not aggregates hiding
  heterogeneity (the lone US500-1h-AVWAP resolver is named, not buried). ✓
- **Mechanism statement — PRESENT and substantive.** The audit explains *why* DERIVATION_DELIVERED (all
  inputs comfortably interior), *why* D2's lever is dormant (`m_anti` resolves once and below `MAE_q90`),
  and *why* the catastrophe guard is inert (the catastrophe is a continuous tail, not a separated mode) —
  not merely that the numbers cleared. This is the "explain the why, not just re-derive" standard. ✓
- **Gate-shape check — PRESENT.** The audit records that the rule's adverse instrument (`m_anti`, a
  separated-mode detector) is the wrong instrument for the shape EXP-081 found (a continuous tail) — the
  same blind-spot family G-017 flagged for `ASS` — and distinguishes "the rule failed" (it did not) from
  "the rule's intended differentiation is inactive on this data shape". Gate not retro-edited (frozen at
  D0). ✓
- **Materiality discipline — CORRECT.** The single Warning (the derived stop does not engage the
  catastrophe) is shown to move **no** EXP-082 verdict-bearing number (the rule is faithfully applied; all
  552 triples reproduce exactly; the verdict holds regardless of stop width) → correctly classified
  Warning (document-and-proceed), not down-classified from a Critical. No verdict-material finding was
  documented-and-proceeded. No fix-and-rerun owed. ✓

## Signal-registry disposition confirmation (Stage 8 mandatory)

- **Disposition recorded** in `report.md` (Registry Disposition section): registry-relevant, updates
  applied. ✓
- **Candidate-family status advanced:** `cf-capgeo-001.md` HYP-003 row **GATED → COMPLETE —
  DERIVATION_DELIVERED**; family stays `REGISTERED`/SCREENING (derivation only — correct, no PROCEED). ✓
- **Multiplicity-registry outcome recorded:** Phase 018 batch EXP-082 row records the derivation that
  **locks the parameterization** of the already-registered `/EXIT-DERIVED` items; **no new countable
  item, no item refuted** (correct — a derivation does not create or kill a countable item). The D1≡D2
  coincidence and the sha256 pin are recorded; no item deleted/renamed. ✓
- **Test-read-ledger:** EXP-082 entered as a **disclosure, not a counted read** (no market data read);
  all 48 strata tallies unchanged, holdout sealed (EXP-074/075/081 precedent). ✓

## Notes

- The two Stage-4 Info flags (the D2 "tightened to the dip" operationalization as `min(m_anti, MAE_q90)`;
  the anticipated D1≡D2 numerical coincidence) carried through cleanly: both are documented in scope,
  plan, audit, results, report, and the registry, and the operator had visibility at the manual execution
  gate. The D2 operationalization is a faithful reading of frozen D0 §D3 prose (no new constant, distinct
  function from D1), so it required no D0-amendment.

## Verdict

```text
VERDICT: APPROVE
```

The derivation is faithful (independent re-derivation 0/552 mismatches), deterministic, holdout-clean,
and hash-pinned; the audit carries full verdict forensics (per-stratum re-derivation + masking check,
substantive mechanism statement, gate-shape check) with correct materiality classification; and the
signal-registry disposition is complete and correct across all three registry files. No revision cycle
required.
