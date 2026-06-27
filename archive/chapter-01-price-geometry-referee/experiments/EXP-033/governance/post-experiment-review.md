# EXP-033 — Post-Experiment Governance Review (Stage 8)

**Date:** 2026-06-10
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`
**Phase alignment:** `2026-06-10-008-avwap-clinical-tradability` (design.md §5 EXP-033, DIAG-004).

---

## VERDICT: APPROVE

All governance constraints pass. No Critical or Warning issues. No Info notes.

## Constraint checks

### Audit (audit.md)
- **Thoroughness** ✓ — correctness, edge cases, type safety, NaN handling, holdout exclusion, temporal alignment, real-price discipline all checked with specific file/line references.
- **Numerical validation** ✓ — reconciliation anchors reproduce EXP-031 H=1/5m exactly (0.0 bps drift); containment accounting verified; B2 one-SE selection mechanically confirmed.
- **Severity classification** ✓ — 0 Critical, 0 Warning, 0 Info.
- **Scope compliance** ✓ — code matches analysis plan; both diagnostic deliverables produced (attribution crossover + FH net curve + B2 selections).

### Results (results.md)
- **Honest reporting** ✓ — 4h attribution UNPOWERED disclosed; 4h H\* fragility flag (`h_star_stable = false`) documented; 5m/1h B2-ineligible stated clearly.
- **Uncertainty acknowledged** ✓ — split-half stability is point-estimate-only (no test family); all TRAIN-only caveats documented.
- **Verdict supported** ✓ — MEASUREMENT_COMPLETE justified: both deliverables produced, all evidence supports the stated findings.
- **Next steps** ✓ — EXP-037 (/EXIT-FH) scoping recommendation with fragility caveat.
- **Real-price discipline** ✓ — all returns inherit EXP-022 real domain Close; no synthetic prices.

### Report (report.md)
- **Self-contained** ✓ — readable without pre-reading other artifacts.
- **Key plots** ✓ — s_entry sweep, FH net curves, pyramid policy comparison referenced with captions.
- **Limitations** ✓ — four limitations documented (TRAIN-only, 4h UNPOWERED, BTCUSD exclusion, stability flag).
- **Artifacts linked** ✓ — all relative paths to scope, plan, code, audit, results, governance, plots.
- **Indexes updated** ✓ — both `python/experiments/INDEX.md` and `docs/experiments-docs/INDEX.md` updated.

### Scope compliance
- **Diagnostic objectives** ✓ — both DIAG-004 deliverables produced (attribution crossover characterisation + FH(H) net curve with B2 selections).
- **Boundaries respected** ✓ — instruments, domains, H grid, costs, financing, exclusions as scoped.
- **Complexity budget** ✓ — 2 test families / 2 budgeted, 4 plots / 4 budgeted, 1 module / 1 budgeted.
- **Holdout exclusion** ✓ — TRAIN nested 70% of first-70% slice; containment invariant verified; 30% holdout never loaded.

### Programme principles
- **Simplicity** ✓ — deterministic additive decomposition + mechanical one-SE rule; simplest sufficient method.
- **Non-parametric** ✓ — regime-cluster bootstrap; no normality/i.i.d./stationarity assumptions.
- **Real-price outcome discipline** ✓ — real domain Close returns inherited from EXP-022.
- **Timestamp alignment** ✓ — inherited from EXP-022 (CloseTime-ordered lifetimes).
- **No academic-finance pitfalls** ✓ — bootstrap makes no distributional assumptions.

## No REVISE / REJECT triggers

No holdout contamination, no look-ahead bias, no synthetic-price P&L, no bar-index alignment, no scope creep, no unsafe optimization, no dishonest results.

---

## Review notes

- The attribution crossover resolves EXP-031's horizon-dependent flip: 5m H=3, 1h H=4 (STABLE_CROSSOVER). This is a clean mechanism finding that constrains future exit redesign: any fix must account for the short-horizon loss-cutter / long-horizon trend-truncator trade-off.
- The FH(H) net curve provides actionable Tier-B planning: 5m/1h B2-ineligible (no fixed-horizon exit can rescue absolute net), 4h B2-eligible with documented fragility. The fragility flag (`h_star_stable = false`) is a descriptive disclosure that EXP-037 scope should weigh before consuming a Tier-B slot.
- DIAG-004 completes without consuming any 008-type multiplicity slot (0 slots per design §5).
- Phase 008 Tier A continues with EXP-034 and EXP-035 running in parallel.
