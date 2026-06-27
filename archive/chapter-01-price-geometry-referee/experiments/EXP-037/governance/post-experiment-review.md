# EXP-037 — Post-Experiment Governance Review (Stage 8)

**Date:** 2026-06-10
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`
**Phase alignment:** `2026-06-10-008-avwap-clinical-tradability` (design.md §5 EXP-037, Tier-B B2 `/EXIT-FH`).

---

## VERDICT: APPROVE

All governance constraints pass. No Critical or Warning issues. No Info notes.

## Constraint checks

### Audit (audit.md)
- **Thoroughness** ✓ — correctness, edge cases, type safety, NaN handling, holdout exclusion, temporal alignment, real-price discipline all checked with specific file/line references.
- **Numerical validation** ✓ — null calibration margins reconciled against FPR tables; within-route Holm recomputation verified; TRAIN/TEST barrier confirmed 0 violations; H\* tie-break reproducibility checked; FH-vs-BTC companion verified against EXP-031 decomposition.
- **Severity classification** ✓ — 0 Critical, 0 Warning, 0 Info.
- **Scope compliance** ✓ — code matches analysis plan; freeze-before-TEST barrier enforced; R1.2 null calibration implemented correctly; R1.5 tie-break spill containment verified.

### Results (results.md)
- **Honest reporting** ✓ — EURUSD provisional pass, USTEC inconclusive, XAUUSD margin-bound all stated with exact CIs and margins; `B2_NO_ROBUST_HSTAR` not triggered disclosed.
- **Uncertainty acknowledged** ✓ — small-n caveat for all cells; H\* stability fragility (`h_star_stable = false` from EXP-033) recorded; margin calibration conservatism noted.
- **Verdict supported** ✓ — ROUTE_PASS_PROVISIONAL justified by ci_low_1s 21.94 > margin 8.42 and boot_p=0.001 with within-route Holm p=0.003.
- **Next steps** ✓ — binding G2 verdict deferred to G2-gate-review.md; phase-level Holm family adjudication required.
- **Real-price discipline** ✓ — all returns from rebuilt 4h Close on real domain bars; no synthetic prices.

### Report (report.md)
- **Self-contained** ✓ — readable without pre-reading other artifacts.
- **Key plots** ✓ — test verdicts, FH-vs-BTC comparison referenced with captions.
- **Limitations** ✓ — three limitations documented (small TEST strata, single-shot read, 5m/1h not tested, XAUUSD below-expected event count).
- **Artifacts linked** ✓ — all relative paths to scope, plan, code, audit, results, governance, plots.
- **Indexes updated** ✓ — both `python/experiments/INDEX.md` and `docs/experiments-docs/INDEX.md` updated.

### Scope compliance
- **Single hypothesis** ✓ — FH(H\*) net per-event expectancy on 4h domain with one-shot TEST read, within-route Holm, provisionally flagged.
- **Boundaries respected** ✓ — instruments (3/4; BTCUSD excluded), domain (4h only), H grid {4,6,8,12}, cost+financing constants, TRAIN/TEST split, freeze barrier as scoped.
- **Complexity budget** ✓ — 1 test route / 1 budgeted, 2 test families (within-route + phase-level deferred) / 2 budgeted, plots 4 / 4 budgeted.
- **Holdout exclusion** ✓ — TRAIN nested 70% of first-70% slice; TEST within analysis set (next 30%); final 30% global holdout never loaded.

### Programme principles
- **Simplicity** ✓ — single TRAIN-frozen H\*, mechanical tie-break, one-shot TEST read; simplest sufficient capture-efficiency test.
- **Non-parametric** ✓ — regime-cluster bootstrap; Gaussian cluster-model for null calibration; no normality/i.i.d./stationarity assumptions on raw returns.
- **Real-price outcome discipline** ✓ — real domain Close returns from rebuilt 4h series.
- **Timestamp alignment** ✓ — CloseTime ordering for TRAIN/TEST partition; SourceCloseTime temporal alignment.
- **No academic-finance pitfalls** ✓ — bootstrap makes no distributional assumptions; freeze-before-TEST prevents overfitting; null calibration corrects anti-conservatism; within-route Holm controls multiplicity.

## No REVISE / REJECT triggers

No holdout contamination, no look-ahead bias, no synthetic-price P&L, no bar-index alignment, no scope creep, no unsafe optimization, no dishonest results.

---

## Review notes

- EURUSD-4h TEST provisional pass is the only cell that clears the route gate. The +16.29 bps FH-vs-BTC companion gap on TEST events confirms the exit-drag mechanism on an independent TEST slice.
- Both USTEC (n=11) and XAUUSD (n=8) are correctly handled by the null calibration — XAUUSD raw boot_p=0.001 would have been a false pass without the margin correction, validating the R1.2 guardrail against small-n anti-conservatism.
- H\*=12 all_legs is the only feasible policy (n≥15 floor). The `h_star_stable = false` caveat from EXP-033 means the TRAIN argmax is split-half fragile, but the one-SE rule selected within the stable eligibility set and `B2_NO_ROBUST_HSTAR` was not triggered. This trade-off is disclosed; it is the operational consequence of the small TRAIN sample (~90 events).
- The phase-level G2 Holm family (≤4 cells: EXP-037's 3 + EXP-038's 1) is the binding adjudication step. If any cell in the family passes the Holm-adjusted α=0.05, the phase verdict is PASS_PROVISIONAL; if all fail, it is G2_FAIL. The G2-gate-review.md desk artifact will resolve this.
- EXP-037 consumes its single Tier-B B2 slot. EXP-036's B1 slot was not consumed (precondition not met).
