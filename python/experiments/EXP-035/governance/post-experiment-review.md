# EXP-035 — Post-Experiment Governance Review (Stage 8)

**Date:** 2026-06-10
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`
**Phase alignment:** `2026-06-10-008-avwap-clinical-tradability` (design.md §5 EXP-035, DIAG-005).

---

## VERDICT: APPROVE

All governance constraints pass. No Critical or Warning issues. No Info notes.

## Constraint checks

### Audit (audit.md)
- **Thoroughness** ✓ — correctness, edge cases, type safety, NaN handling, holdout exclusion, temporal alignment, real-price discipline all checked with specific file/line references.
- **Numerical validation** ✓ — 5m/c1 SNR=1.42 spot-checked with correct materiality failure (candidate net −7.07 ≤ 0); 4h CI half-widths consistent with ~10 events/tercile; permutation p for 5m/c1 (0.010) verified correct; TRAIN containment accounting checked.
- **Severity classification** ✓ — 0 Critical, 0 Warning, 0 Info.
- **Scope compliance** ✓ — code matches analysis plan; all three covariates constructed per plan; G1 conjunction correctly implemented with hard no-selection rule.

### Results (results.md)
- **Honest reporting** ✓ — zero qualified dimensions stated directly; 5m/c1 gradient correctly labelled as relative separation (hypothesis-generating, not a rule); 4h underpowered disclosed.
- **Uncertainty acknowledged** ✓ — TRAIN-only caveat; 4h power limitation; permutation p anti-conservatism acknowledged; cost-model sensitivity noted as alternative explanation.
- **Verdict supported** ✓ — CHARACTERISATION_DELIVERED justified: all 9 cells fail materiality, no G1-qualified dimension.
- **Next steps** ✓ — FLAT path per design §9: B1 (/COND) does not open; B2 (/EXIT-FH) and Tier C recommended.
- **Real-price discipline** ✓ — all returns inherit EXP-022 real domain Close; no synthetic prices.

### Report (report.md)
- **Self-contained** ✓ — readable without pre-reading other artifacts.
- **Key plots** ✓ — qualification matrix, C1 bin means referenced with captions.
- **Limitations** ✓ — three limitations documented (TRAIN-only, 4h underpowered, no interaction analysis).
- **Artifacts linked** ✓ — all relative paths to scope, plan, code, audit, results, governance, plots.
- **Indexes updated** ✓ — both `python/experiments/INDEX.md` and `docs/experiments-docs/INDEX.md` updated.

### Scope compliance
- **Diagnostic objectives** ✓ — DIAG-005 deliverable produced: G1 qualification assessment across all 9 domain×dimension cells with hard no-selection rule enforced.
- **Boundaries respected** ✓ — instruments, domains, cost table, financing rates, α_G1, dimensions, exclusions as scoped.
- **Complexity budget** ✓ — 3 test families / 3 budgeted, 5 plots / 5 budgeted, 1 module / 1 budgeted.
- **Holdout exclusion** ✓ — TRAIN nested 70% of first-70% slice; containment rule verified; 30% holdout never loaded.

### Programme principles
- **Simplicity** ✓ — predeclared tercile splits on three causally-available covariates; simplest sufficient characterisation.
- **Non-parametric** ✓ — regime-cluster bootstrap; stratified permutation; no normality/i.i.d./stationarity assumptions.
- **Real-price outcome discipline** ✓ — real domain Close returns inherited from EXP-022.
- **Timestamp alignment** ✓ — inherited from EXP-022 (CloseTime-ordered lifetimes).
- **No academic-finance pitfalls** ✓ — bootstrap makes no distributional assumptions; hard no-selection rule prevents post-hoc fishing.

## No REVISE / REJECT triggers

No holdout contamination, no look-ahead bias, no synthetic-price P&L, no bar-index alignment, no scope creep, no unsafe optimization, no dishonest results.

---

## Review notes

- Zero G1-qualified dimensions is a clean, admissible negative outcome. The selectivity lever (B1 /COND) does not open per design §9.
- The 5m/c1 gradient (higher %completion → less negative) is real and stable (structure+stability+multiplicity all pass) but the best bin is −7.07 bps — a relative separation within a net-negative regime. This is hypothesis-generating only; the hard no-selection rule prevents promotion without a fresh TEST read.
- Per design §9, the zero-qualified outcome maps to FLAT: Tier B reduces to B2 (/EXIT-FH) only, and Tier C (Stage-C branches or HYP-001) becomes the next direction if B2 fails G2.
- DIAG-005 completes without consuming any 008-type multiplicity slot (0 slots per design §5).
- Phase 008 Tier A is now complete: all three parallel tracks (EXP-033 diagnostic, EXP-034 A1 screen, EXP-035 diagnostic) have delivered their expected outputs. The G1 gate review now determines whether Tier B slots may be spent.
