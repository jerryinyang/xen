# EXP-071 — Post-Experiment Governance Review (Stage 8)

```text
VERDICT: APPROVE
```

**Date:** 2026-06-19 · **Reviewer:** research-pipeline (consolidated Stage 8 governance)
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, index + registry updates.

## Checks

| Constraint | Finding |
| --- | --- |
| Holdout untouched | PASS — final 30% never loaded (`load_test_1m` slices `[0, analysis_cutoff)`); audit confirmed. |
| Freeze-before-TEST (D0 P8) | PASS — `frozen_selection.json` hash-pinned (`ca16bcd…`) before any TEST row; loader hard-gates on its presence. |
| TEST-family integrity (D0 P5) | PASS — EXP-068 g015 PARTIAL-V2A set ex-EURUSD == 6 P5 cells (asserted); freeze byte-identical. |
| P12 reconciliation (D0 P1) | PASS — max_abs_diff 0.0 @1e-9, all 6 cells. |
| Determinism (D0 P7) | PASS — full second pass byte-identical; 0 mismatches. |
| Real-price discipline | PASS — outcomes on RealOHLC; HA used for detection only; no HA-price metric. |
| Gross-only posture (D0 P12) | PASS — no costs/financing/sizing; costs deferred to EXP-072. |
| Verdict mechanically correct (D0 P9) | PASS — independently reproduced: 0/6 clear, 4/6 median CI_low ≤ 0 → TEST_NOT_CONFIRMED. |
| Composite is a disclosure, not a gate | PASS — non-binding; the verdict keys on per-cell composition only. The event-pooled / GBPUSD-5m-dominated caveat (audit WARNING-1) is disclosed in `results.md`, `report.md`, and all index cards. |
| Single hypothesis / no scope creep | PASS — one TEST-confirmation question; no post-result re-scope or tuning. |
| **Signal-registry disposition recorded** | PASS — registry-relevant result, updated in the same change: candidate-family status advanced (`SCREENED — TEST_NOT_CONFIRMED`, harami.md); multiplicity-registry CAND-001 + HYP-024 outcome recorded with the slot retained (refuted-on-scope, not deleted); **6 counted TEST reads entered** in `test-read-ledger.md` (each binding stratum 1/2) plus the portfolio composite as a disclosure against all 6 strata. |
| TEST-read ledger same-commit rule (D0 P6) | PASS — counted reads and disclosure entered alongside the result; EURUSD excluded (TEST-capped) recorded no read. |
| Follow-up routing | PASS — EXP-074/HYP-027 (TRAIN-only, no slot, no TEST contact) flagged ROUTED; EXP-072/073 correctly NOT opened (conditional on TEST_CONFIRMED). |

## Disposition

The experiment is correct, governance-clean, and faithfully documented. The negative verdict is
the predeclared mechanical outcome of the D0 P9 rule, independently reproduced. The one WARNING
(event-pooled composite labelling) is a documentation-disclosure matter, fully addressed in the
interpretation and all indexes — not a correctness defect. All registry obligations for a
registry-relevant result are met.

**APPROVE.** EXP-071 complete. G-016 desk adjudication of the TEST_NOT_CONFIRMED readout and the
EXP-074 routing remains an operator gate, outside the per-experiment pipeline.
