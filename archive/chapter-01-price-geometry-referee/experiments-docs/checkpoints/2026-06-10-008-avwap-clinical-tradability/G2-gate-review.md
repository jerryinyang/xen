# G2 Gate Review — Phase 008 (Clinical Tradability)

**Date:** 2026-06-10
**Design reference:** `design.md` §8.4 (R1.1 — phase-level G2 multiplicity family)
**Experiments in scope:** EXP-037 (3 cells), EXP-038 (1 cell)
**Family composition:** 4 members (B2_NO_ROBUST_HSTAR not triggered)

---

## Binding rule (per §8.4, R1.1 + R1.2)

A cell passes G2 iff **both** conditions hold:
1. Phase-family Holm-adjusted one-sided bootstrap p ≤ 0.05
2. Margin-adjusted one-sided 95% CI lower bound clears: `ci_low_1s > m_cell` (R1.2)

---

## Family data

| # | Cell | boot_p | Holm-4 adj_p | ci_low_1s (bps) | margin m (bps) | Margin check | G2 PASS? |
|---|------|--------|-------------|-----------------|----------------|-------------|----------|
| 1 | EXP-038 EURUSD-4h (TEST subsample, BTC exit) | 0.001 | 0.004 | 15.43 | 3.78 | ✓ 15.43 > 3.78 | **YES** |
| 2 | EXP-037 EURUSD-4h (TEST, FH H*=12 exit) | 0.001 | 0.004 | 21.94 | 8.42 | ✓ 21.94 > 8.42 | **YES** |
| 3 | EXP-037 XAUUSD-4h (TEST, FH H*=12 exit) | 0.001 | 0.004 | 11.45 | 54.2 | ✗ 11.45 < 54.2 | **NO** |
| 4 | EXP-037 USTEC-4h (TEST, FH H*=12 exit) | 0.244 | 0.244 | −72.6 | 30.3 | — (adj_p > 0.05) | **NO** |

**Procedure notes:**
- Holm step-down with monotonicity enforcement: the three tied minima (raw boot_p = 1/1001 ≈ 0.000999) all receive adj_p = 4 × 0.000999 ≈ 0.004 (the step-down multipliers 4p/3p/2p are dominated by the rank-1 value under the running-maximum rule); USTEC receives max(0.004, 1 × 0.244) = 0.244. (Corrected 2026-06-10 during the binding desk adjudication: an earlier draft listed the raw rank-multipliers 0.004/0.003/0.002 without monotonicity; no pass/fail state changes.)
- Mollifier: all three top cells share boot_p = 1/1001 (minimum resolvable). Under the most conservative tie treatment (all rank 1 with denominator 4), p=0.001 < 0.0125; Holm order does not affect the verdict.
- Within-route Holm was applied inside each experiment as a provisional diagnostic; the phase-level Holm-4 recomputation above is the binding gate.
- USTEC boot_p=0.244 > 0.05 — no need to check margin.

---

## Verdict

**G2 SATISFIED — CLINICAL_TRADABLE.** Two cells in the phase-level Holm-4 family pass both conditions.

Per design §9:
> ≥1 A1 cell or Tier-B variant passes G2 (strict). → **CLINICAL_TRADABLE**

**Consequence:** EXP-032 (holdout-release checkpoint) becomes admissible. The operator may select **one** fully predeclared package for the single holdout shot. The holdout is never released to confirm gross, descriptive, lenient-gate, or in-sample-only results.

---

## Admissible packages for EXP-032

The operator selects one of:

| Package | Description | Evidence |
|---------|-------------|----------|
| **A** | EURUSD-4h baseline (BTC exit, same estimand as EXP-034/038) | A1 strict pass + TEST-stratum subsample confirmation (EXP-038) |
| **B** | EURUSD-4h FH exit at H*=12, all_legs policy (same estimand as EXP-037) | TRAIN-frozen H* + TEST one-shot pass (EXP-037) |

The two packages are not independent (same events, same instrument-domain, different exit rules), so only one may be selected for holdout release.

**Recommendation:** Package B (FH exit at H*=12) has the larger estimated effect (+40.56 bps vs +24.27 bps net on TEST) and the mechanism is better understood (exit-drag replacement confirmed across EXP-031/033/037). Package A (BTC exit) is the original baseline. Both have one-shot TEST evidence; the operator should weigh mechanism confidence vs simplicity.

---

## Phase outcome (design §9)

| Outcome | Definition | Phase 008 status |
|---------|-----------|------------------|
| CLINICAL_TRADABLE | ≥1 A1 cell or Tier-B variant passes G2 (strict) | **✓ CURRENT** |
| CHARACTERISED_NOT_CONFIRMED | G1 qualified ≥1 item but nothing passed G2 | — |
| NOT_CLINICAL_TRADABLE | G1 nothing qualifies (FLAT) | — |

## Operator decision (recorded 2026-06-10)

**Package B selected** — EURUSD-4h with the TRAIN-frozen fixed-horizon exit at
H\*=12, `all_legs` pyramid policy (the EXP-037 estimand). Rationale: larger TEST
effect (+40.56 bps net, ci_low_1s 21.94 > margin 8.42) and the exit-drag-replacement
mechanism is confirmed across EXP-031/033/037. Package A (BTC-exit baseline) is
**not** released to holdout; the two packages share events, so this selection is
exclusive and final for EXP-032.

## Next steps

1. ~~Operator decision~~ — **done: Package B** (above).
2. **EXP-032 registration:** own checkpoint (design §10), scope, analysis plan, governance gate for the single holdout shot. The predeclared estimand is fixed by Package B; no parameter may change between this record and the holdout read.
3. **If holdout confirms:** first net-positive cTrader-confirmed AVWAP strategy candidate. Programme synthesis update.
4. **If holdout refutes:** return to characterisation. Tier C fallback (Stage-C branches or HYP-001) per design §9.
