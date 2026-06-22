# EXP-080 — Stage 8 Post-Experiment Governance Review

**Experiment:** EXP-080 — Phase 018 CF-CAPGEO-001 Substrate/Exit Readiness (HYP-001)
**Reviewed:** 2026-06-22
**Artifacts:** `audit.md` (+ Re-Audit), `results.md`, `report.md`, index + signal-registry updates.

---

## VERDICT

```text
VERDICT: APPROVE
```

The experiment is sound, the verdict (`READINESS_DELIVERED`) is mechanistically justified and
per-stratum, both verdict-material audit findings were fixed and re-run (not down-classified), the
audit carried full verdict forensics, and the signal-registry disposition is recorded across all
relevant surfaces. No REVISE/REJECT condition is present.

---

## Governance checks

| Check | Finding |
|---|---|
| **Signal-registry disposition recorded** | YES. Registry-relevant readiness result. `multiplicity-registry.md` (Phase 018 batch) records EXP-080 COMPLETE — READINESS_DELIVERED with the 2 `COVERAGE_EXCLUDED` cells **retained** (never deleted); `candidate-families/cf-capgeo-001.md` status + HYP-001 row advanced (readiness complete → characterization next); `test-read-ledger.md` records the readiness exposure as a **disclosure, 0 counted reads** (all 48 strata remain 0/open). `report.md` has an explicit Registry Disposition section. |
| **Verdict forensics present (audit)** | YES, run autonomously. Original audit + Re-Audit both carry: per-stratum re-derivation with an explicit masking check (184 READY across all instruments/domains; 8 NOT_READY = 2 unique 4h index cells × 4 substrates; pooled headline shown **not** masking heterogeneity — exclusions are correctly stratified to the 4h cash-equity-index corner); a mechanism statement (READY = coverage PASS ∧ 0 invariant ∧ determinism; the halt legs all clear); and a gate-shape check (the 0.25 gate now measures coverage, the correct quantity; null-FPR gate resolved at validated scale). |
| **Materiality & blocking honored** | YES. Both Critical findings were **fixed + re-run** before interpretation (the dropped-fraction metric and the null-FPR probe scale), not documented-and-proceeded. Re-audit verdict PASS (0C/0W). No verdict-material finding was down-classified. |
| **Per-stratum verdict (not collapsed)** | YES. Code emits a `CellRecord` per substrate-cell (192 rows); READY/NOT_READY/COVERAGE_EXCLUDED is per cell. `SUBSTRATE_REFUTED` is a disjunction of predeclared *systematic* triggers, not a pooled statistic. |
| **Honest reporting** | YES. `results.md`/`report.md` state the readiness verdict without overreach (explicitly "not a market-edge claim"), carry every audit caveat (US500-4h borderline; small-n null-FPR disclosed; null-FPR scale sensitivity; AVWAP sparser stream), and document the full audit trail (initial SUBSTRATE_REFUTED → fixes → re-run → re-audit PASS). |
| **Real-price discipline** | YES. No return/capture/P&L computed; the only return series is the explicitly non-tradable, mean-centered null-FPR machinery probe. Harami detection on HA candles is permitted (no returns). |
| **Holdout / look-ahead / determinism** | YES. Metadata + first-70% only; fence applied; regression vs VAL-005 frame-identical; 0 invariant/causality failures; 0 nondeterministic cells; seeds recorded. |
| **Predeclaration integrity** | YES. The Stage-4 reconciliation (null-FPR halt bound to D0 §D9 operating floor n≥120) is reflected consistently in scope, plan, code, results, and report; the validated-scale rescale (audit Critical-2) kept the 0.075 gate and n≥120 floor unchanged — no goalpost movement. |
| **Index updates** | YES. `python/experiments/INDEX.md`, `families/cf-capgeo-001/INDEX.md` (Phase 018 section + detailed card), and master `INDEX.md` (Family Indexes row + Current Checkpoint Status row) all updated; master carries no per-experiment card (correct). |
| **Complexity budget** | Within budget (1 statistical test, 4 plots, 2 new modules). |

## Notes for the next experiment (EXP-081, HYP-002)

- Operate on the **46-cell member set** (excluding US500-4h, JP225-4h with record).
- Carry the disclosed caveats: US500-4h knife-edge exclusion; small-n (n<120) null-FPR inflation
  (defer to median / disclose per D0 §D6 Guard (i)); evaluate the null-FPR machinery at the validated
  N_BOOT=10,000 scale; AVWAP's wider per-cell intervals from its sparser entry stream.

**Stage 8: APPROVED. EXP-080 is complete.**
