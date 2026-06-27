# EXP-038 — Post-Experiment Governance Review (Stage 8)

**Date:** 2026-06-10
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`
**Phase alignment:** `2026-06-10-008-avwap-clinical-tradability` (design.md §8 EXP-038, Tier-B subsample robustness check, R1.7).

---

## VERDICT: APPROVE

All governance constraints pass. No Critical or Warning issues. No Info notes.

## Constraint checks

### Audit (audit.md)
- **Thoroughness** ✓ — correctness, edge cases, type safety, NaN handling, holdout exclusion, temporal alignment, real-price discipline all checked with specific file/line references.
- **Numerical validation** ✓ — full-cell reproduction vs EXP-034 verified to 0.0 bps; bootstrap CI replay with EXP-034's seed verified to ≤ 8.9e-16; null calibration margin recomputed and confirmed; LOCO diagnostics spot-checked; seed robustness CI ranges verified.
- **Severity classification** ✓ — 0 Critical, 0 Warning, 0 Info.
- **Scope compliance** ✓ — code matches analysis plan; TRAIN/TEST partition by CloseTime correctly implemented with tie-break; R1.2 null calibration correct; R1.7 dependent-subsample caveat documented in verdict.

### Results (results.md)
- **Honest reporting** ✓ — provisional pass clearly labelled with R1.7 caveat (dependent subsample, not independent OOS confirmation); LOCO and seed-robustness reported; TRAIN net point disclosed for nomination precondition.
- **Uncertainty acknowledged** ✓ — small TEST n (12) precision caveat; temporal non-stationarity note (later events had larger effects); single-cell, single-domain limitation.
- **Verdict supported** ✓ — A1_CELL_TEST_PASS_PROVISIONAL justified by ci_low_1s 15.43 > margin 3.78 and boot_p=0.001, with LOCO and seed-robustness supporting robustness.
- **Next steps** ✓ — binding verdict deferred to G2-gate-review.md; phase-level Holm family adjudication required.
- **Real-price discipline** ✓ — all returns inherit EXP-034/EXP-022 real domain Close; no synthetic prices.

### Report (report.md)
- **Self-contained** ✓ — readable without pre-reading other artifacts.
- **Key plots** ✓ — TEST stratum distribution, stratum comparison referenced with captions.
- **Limitations** ✓ — five limitations documented (dependent subsample, small n, single cell/domain, temporal non-stationarity, no generalization).
- **Artifacts linked** ✓ — all relative paths to scope, plan, code, audit, results, governance, plots.
- **Indexes updated** ✓ — both `python/experiments/INDEX.md` and `docs/experiments-docs/INDEX.md` updated.

### Scope compliance
- **Single hypothesis** ✓ — TEST-stratum net expectancy on EURUSD-4h with one-shot read and null calibration.
- **Boundaries respected** ✓ — instrument (EURUSD-4h only), domain (4h only), cost+financing constants from EXP-034, TRAIN/TEST partition boundary, frozen inference tail hash-pinned.
- **Complexity budget** ✓ — 1 test / 1 budgeted, 2 plots / 2 budgeted, 1 module / 1 budgeted.
- **Holdout exclusion** ✓ — TRAIN+TEST within first-70% analysis slice; events partitioned by trigger close time; final 30% global holdout never loaded.

### Programme principles
- **Simplicity** ✓ — single-cell dependent subsample check; reuses EXP-034 pipeline verbatim with only partition and null calibration added; simplest sufficient temporal-stability test.
- **Non-parametric** ✓ — regime-cluster bootstrap; Gaussian cluster-model for null calibration; no normality/i.i.d./stationarity assumptions.
- **Real-price outcome discipline** ✓ — real domain Close returns inherited from EXP-034/EXP-022.
- **Timestamp alignment** ✓ — CloseTime ordering for TRAIN/TEST partition; SourceCloseTime temporal alignment.
- **No academic-finance pitfalls** ✓ — bootstrap makes no distributional assumptions; R1.7 dependent-subsample caveat prevents overconfident interpretation; LOCO prevents single-regime-driven verdict.

## No REVISE / REJECT triggers

No holdout contamination, no look-ahead bias, no synthetic-price P&L, no bar-index alignment, no scope creep, no unsafe optimization, no dishonest results.

---

## Review notes

- TEST effect (+24.27 bps) is roughly 2× the full-cell effect (+11.77 bps), suggesting later-period events were more favorable. The one-shot TEST read is on the realized distribution, so this is a valid subsample check — but the R1.7 caveat is critical: this is NOT an independent out-of-sample confirmation. The EXP-034 A1 pass selected EURUSD-4h as the best cell; the TEST events contributed to that selection. The check demonstrates temporal stability, not independence.
- LOCO robustness (min ci_low_1s 13.25 across all 9 cluster drops, all well above the 3.78 bps margin) is the strongest diagnostic in this experiment. It rules out single-regime-driven fragility.
- Seed robustness (ci_low_1s range 14.59–15.66 across 8 seeds) is tight and all sign-stable — the pass is not a sampling artifact.
- Per R1.1, EXP-038 enters the phase-level Holm family alongside EXP-037's 3 cells. Whether its TEST-stratum pass counts as a distinct hypothesis for Holm purposes is an operator determination for G2-gate-review.md. The family size is ≤4; at α=0.05, the Bonferroni bound is α/4=0.0125 for the strongest cell.
- This experiment does NOT consume a Tier-B slot (it is a subsample robustness check, not a new TEST confirmation of a fresh estimand). The single consumed Tier-B slot is EXP-037's B2 (/EXIT-FH).
