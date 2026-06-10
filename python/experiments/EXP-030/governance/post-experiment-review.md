# EXP-030 — Post-Experiment Governance Review (Stage 8)

**Date:** 2026-06-10
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`
**Phase alignment:** `2026-06-09-007-avwap-tradability-and-isolation` (design.md §5 EXP-030).

---

## VERDICT: APPROVE

All governance constraints pass. No Critical or Warning issues. Minor Info notes are present.

## Constraint checks

### Audit (audit.md)
- **Thoroughness** ✓ — correctness, edge cases, type safety, NaN handling, holdout exclusion, temporal alignment, real-price discipline all checked with specific file/line references.
- **Numerical validation** ✓ — spot checks confirm `net = gross_abs − mean_inst(RT_cons)` to machine epsilon; commute check, reconciliation guard verified.
- **Severity classification** ✓ — 0 Critical, 0 Warning, 1 Info (frozen inference hash self-consistency bound, already resolved by F02 pin).
- **Scope compliance** ✓ — code matches analysis plan; binding metric = absolute net (correctly distinguished from excess-minus-cost).

### Results (results.md)
- **Honest reporting** ✓ — states INCONCLUSIVE phase outcome; no domain forced into FOR/AGAINST.
- **Uncertainty acknowledged** ✓ — 4h CI half-width (~17 bps, n=187), BTCUSD cost dominance, absolute-vs-relative estimand distinction all documented.
- **Verdict supported** ✓ — INCONCLUSIVE justified by evidence: 5m/1h CIs entirely below 0, 4h CI spans 0.
- **Next steps** ✓ — EXP-031 (parallel, not gated), per-instrument tradability test (new scope), family review per Phase 007 design §9.
- **Real-price discipline** ✓ — all returns inherit EXP-022 real domain Close; no synthetic prices.

### Report (report.md)
- **Self-contained** ✓ — readable without pre-reading other artifacts.
- **Key plots** ✓ — net expectancy forest, break-even heatmap, verdict summary referenced with captions.
- **Limitations** ✓ — five limitations documented (BTCUSD cost dominance, 4h power, financing exclusion, operator-declared costs, 5m gross near zero).
- **Artifacts linked** ✓ — all relative paths to scope, plan, code, audit, results, governance, plots.
- **Indexes updated** ✓ — both `python/experiments/INDEX.md` and `docs/experiments-docs/INDEX.md` updated.

### Scope compliance
- **Single hypothesis** ✓ — cost-bearing net per-event expectancy on ≥1 domain.
- **Boundaries respected** ✓ — instruments, domains, cost table, α₀, seeds, exclusions as scoped.
- **Complexity budget** ✓ — tests 1/3, plots 4/4, modules 1/1.
- **Holdout exclusion** ✓ — inherited fence; event counts match EXP-028 first-70% exactly; no new bar loads.

### Programme principles
- **Simplicity** ✓ — deterministic cost overlay on validated data; simplest sufficient method.
- **Non-parametric** ✓ — regime-cluster bootstrap; no normality/i.i.d./stationarity assumptions.
- **Real-price outcome discipline** ✓ — real domain Close returns inherited from EXP-022.
- **Timestamp alignment** ✓ — inherited from EXP-022 (CloseTime-ordered lifetimes).
- **No academic-finance pitfalls** ✓ — bootstrap makes no distributional assumptions.

## No REVISE / REJECT triggers

No holdout contamination, no look-ahead bias, no synthetic-price P&L, no bar-index alignment, no scope creep, no unsafe optimization, no dishonest results.

---

## Review notes

- The INCONCLUSIVE phase outcome correctly reflects the scope's predeclared criteria: no domain FOR (5m/1h AGAINST, 4h power-limited). The holdout-release gate (EXP-032) is not passed.
- The non-binding attribution companion (net matched-control excess FOR on 1h/4h) is correctly labelled and not promoted to a verdict — the binding absolute metric and the companion measure different estimands, and the pre-execution revision's F07 guard prevents grep-based misreading.
- The pre-execution revision's conditions (re-run, carry-forward notes on financing and per-instrument multiplicity) are satisfied and documented.
- Phase 007 remains ACTIVE with EXP-031 (edge isolation) pending. Phase outcome per design §9: the tradability path is NOT_TRADABLE/INCONCLUSIVE, triggering the pivot to mechanism information (EXP-031) and family review.
