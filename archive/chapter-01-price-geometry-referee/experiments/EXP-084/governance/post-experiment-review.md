# EXP-084 — Post-Experiment Governance Review (Stage 8)

**Experiment:** EXP-084 — AVWAP-4h Portfolio Confirmation Read (CF-CAPGEO-001 Phase 018 / HYP-004b)
**Reviewed artifacts:** `audit.md`, `results.md`, `report.md`, index + registry updates
**Reference:** `research-pipeline/references/governance-constraints.md`
**Verdict reviewed:** `NOT_CONFIRM` (portfolio unit; 0 counted reads; HYP-004 closes at G-018)
**Date:** 2026-06-22

---

## Checks

| Constraint | Finding |
|---|---|
| **Audit carries verdict forensics** | YES — `audit.md` re-derives the G-018 conjunction leg-by-leg from the raw parquet (reproduces exactly), states the mechanism (TRAIN separation but no OOS edge; selection-overlap reversal), and includes a gate-shape check (S2 genuinely adjudicated at n=152 and passed → "no OOS edge," not a shape-blind gate). Run autonomously, not contingent on anyone questioning the result. |
| **Per-stratum masking check** | YES — the audit re-derives all three member strata (all net-negative on expectancy, exp_lo −2.1/−2.5/−2.9) and the per-fold trajectory, and affirmatively confirms the pooled `NOT_CONFIRM` is not masking a positive stratum. The USTEC median-positive quirk is correctly held as disclosure. The binding unit is the explicit portfolio (per-stratum/per-arm flagged `binding=false`) — no collapsed cross-stratum PASS/FAIL (EXP-076 C1 doctrine satisfied). |
| **Materiality / no down-classification** | YES — 0 Critical, 0 Warning; the 3 Info notes each carry explicit materiality reasoning showing they cannot move a verdict-bearing number (negative `m` only loosens the expectancy leg, which fails anyway; USTEC is a disclosure stratum; the S2-floor HALT did not fire). No verdict-material finding was documented-and-proceeded. |
| **Power adequacy / correct outcome** | YES — `n_oos=151 ≥ 2·MIN_FOLD`, 0 subfloor folds; `NOT_CONFIRM` (not `INCONCLUSIVE_SPANS_ZERO`) is justified per the scope's definitions. |
| **Holdout / look-ahead / real-price** | YES — holdout never built or folded (`holdout_untouched=true`; OOS folds ⊂ analysis set); pooling by event close-time (timestamp, not bar index); ATR-unit real-OHLC returns; no synthetic prices. Re-confirmed at Stage 4 and Stage 5. |
| **Results honesty** | YES — `results.md` and `report.md` anchor to the predeclared interpretation guide, report the failing legs and mechanism plainly, do not overreach (the marginal positive median point estimates are explicitly not robust), and acknowledge the negative-`m` and pooling caveats. |
| **Next steps are new scopes** | YES — EXP-086/087/088 proposed as new experiments with their own G0/D0, not extensions of EXP-084. |
| **Registry disposition recorded** | YES (registry-relevant) — `report.md` records it explicitly; and the updates were applied in this change: `multiplicity-registry.md` EXP-084 → `COMPLETE — NOT_CONFIRM` (0 slots, no new countable item, outcome retained); `candidate-families/cf-capgeo-001.md` → HYP-004 closed at G-018, family stays `REGISTERED`; `test-read-ledger.md` → EXP-084 disclosure against NZDUSD/USDCAD/USTEC-4h, 0 counted reads, all 48 strata stay 0/2 open, the 3 strata disclosed. Refuted item retained, not deleted. |
| **Index updates** | YES — `python/experiments/INDEX.md` row added; `families/cf-capgeo-001/INDEX.md` detailed card + ToC entry added (anchor resolves); master `docs/experiments-docs/INDEX.md` live status (Current Checkpoint Status + Family Indexes EXP range/status) updated with no per-experiment card. |
| **Complexity budget** | YES — 3/3 method families, 4/4 plots, 0 new modules. |
| **Stage-4 fix integrity** | YES — the pre-execution REVISE (unadjudicable-S2 → HALT, not a binding NOT_CONFIRM) is in the executed code; the floor held (n=152) so the HALT path was not exercised, and S2 was genuinely adjudicated. |

## Issues

None. No Critical, Warning. The audit's 3 Info notes are non-material and correctly justified.

---

```text
VERDICT: APPROVE
```

EXP-084 is complete and cleared. The `NOT_CONFIRM` is trustworthy, well-powered, exit-invariant, and not
masking per-stratum or per-fold structure; HYP-004 closes at G-018 with 0 counted reads and the global holdout
untouched.
