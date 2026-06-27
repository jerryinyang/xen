# EXP-034 — Post-Experiment Governance Review (Stage 8)

**Date:** 2026-06-10
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`
**Phase alignment:** `2026-06-10-008-avwap-clinical-tradability` (design.md §5 EXP-034, HYP-004-TI).

---

## VERDICT: APPROVE

All governance constraints pass. No Critical or Warning issues. No Info notes.

## Constraint checks

### Audit (audit.md)
- **Thoroughness** ✓ — correctness, edge cases, type safety, NaN handling, holdout exclusion, temporal alignment, real-price discipline all checked with specific file/line references.
- **Numerical validation** ✓ — reconciliation against EXP-030 no-financing nets to machine precision (max abs diff 3.55e-15 bps); CI reconciliation exact identity; binding verdict mechanistically confirmed (boot_p=0.009 AND ci_low_1s=3.90 > 0).
- **Severity classification** ✓ — 0 Critical, 0 Warning, 0 Info.
- **Scope compliance** ✓ — code matches analysis plan; fixed-sequence procedure correctly implemented with F01 dual binding rule.

### Results (results.md)
- **Honest reporting** ✓ — A1 strict pass clearly labelled as necessary-but-not-sufficient for holdout; USTEC-4h INCONCLUSIVE documented as predeclared power-limited; XAUUSD-1h NOT_TESTED correctly stated.
- **Uncertainty acknowledged** ✓ — EURUSD-4h n=39 precision caveat; financing rate constant caveat; analysis-set read caveat.
- **Verdict supported** ✓ — A1_STRICT_PASS justified by boot_p=0.009 and CI_low_1s=3.90 > 0 with reconciliation verified.
- **Next steps** ✓ — Tier-B TEST confirmation recommended; holdout-release checkpoint (EXP-032) conditional on G2.
- **Real-price discipline** ✓ — all returns inherit EXP-022 real domain Close; no synthetic prices.

### Report (report.md)
- **Self-contained** ✓ — readable without pre-reading other artifacts.
- **Key plots** ✓ — declared cells net, financing waterfall referenced with captions.
- **Limitations** ✓ — three limitations documented (small sample, analysis-set read, financing constants).
- **Artifacts linked** ✓ — all relative paths to scope, plan, code, audit, results, governance, plots.
- **Indexes updated** ✓ — both `python/experiments/INDEX.md` and `docs/experiments-docs/INDEX.md` updated.

### Scope compliance
- **Single hypothesis** ✓ — per-instrument cost-bearing net expectancy in declared family with FWER control.
- **Boundaries respected** ✓ — instruments, domains, cost table, financing rates, α, sequence order, exclusions as scoped.
- **Complexity budget** ✓ — 1 test family / 1 budgeted, 3 plots / 3 budgeted, 1 module / 1 budgeted.
- **Holdout exclusion** ✓ — inherited fence; event counts match EXP-030 first-70% exactly; no new bar loads.

### Programme principles
- **Simplicity** ✓ — deterministic cost+financing overlay on validated data; simplest sufficient method.
- **Non-parametric** ✓ — regime-cluster bootstrap; no normality/i.i.d./stationarity assumptions.
- **Real-price outcome discipline** ✓ — real domain Close returns inherited from EXP-022.
- **Timestamp alignment** ✓ — inherited from EXP-022 (CloseTime-ordered lifetimes).
- **No academic-finance pitfalls** ✓ — bootstrap makes no distributional assumptions; fixed-sequence controls FWER.

## No REVISE / REJECT triggers

No holdout contamination, no look-ahead bias, no synthetic-price P&L, no bar-index alignment, no scope creep, no unsafe optimization, no dishonest results.

---

## Review notes

- EURUSD-4h net +11.77 bps (boot_p=0.009) is a clean A1 strict pass. The financing deduction (mean 0.61 bps/event) is small relative to the gross headroom (12.38 bps), so the pass is robust to reasonable financing rate variation.
- Per design §8.4 as amended 2026-06-10 (F02): this A1 pass is necessary-but-not-sufficient for holdout release. G2 requires one-shot Tier-B TEST confirmation of the same registered baseline estimand on the held-back TEST segment. Only that result can make EXP-032 admissible.
- The instrument-selection lever (lever 2 of the three clinical levers) is resolved: only EURUSD-4h carries a net-positive cell. The selectivity lever (EXP-035) and capture-efficiency lever (EXP-033 4h B2) are the remaining paths.
- HYP-004-TI completes with this A1 pass. Phase 008 Tier A continues with EXP-033 and EXP-035 (parallel diagnostics).
