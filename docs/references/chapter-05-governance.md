# Chapter 05 Governance — Volatility-to-Direction Conversion

**State:** `PRE-EXPERIMENT / PREFLIGHT_PASSED / AWAITING_FAMILY_REGISTRATION`

**Governing brief:** `.ignore/what-next/alts/intraday-way-forward-plan.md`

**Proposed family:** `CF-VOLCONV-001` — not yet registered

This file records the approved route and its enforcement boundary. The cost/data preflight is
revised by the operator to omit spread cost and approved by fresh QA; no family is registered, no
experiment is approved, and no outcome has been exposed.

## 1. Fixed route

- Exactly two historical TRAIN-only runs: one SPDR characterisation, then one frozen Nautilus
  EXP strategy replay if the operator authorises it.
- The operator-approved route exception is `SPDR → EXP`; XENA is not used because there is no
  candidate grid or portfolio search.
- DESIGN report layers are read sequentially from one frozen Run 1 artifact. Each layer requires
  an operator decision before the next is opened.
- One rule is frozen before one CONFIRM read. CONFIRM cannot select a replacement.
- Historical analysis-TEST and the global holdout are not loaded. Independent confirmation, if
  authorised after Run 2, is forward shadow only.
- Drift and beta are controls/benchmarks. No multi-day drift product, secondary/L2 branch,
  indicator search, model zoo, exit optimisation, threshold grid, or cheaper-execution rescue.

## 2. Preflight — no-spread amendment passed 2026-07-22

Before family registration, checkpoint design, event census, or outcome-bearing execution:

1. Correct `bybit_round_trip_cost_bps`: stress applies once and disclosed components sum to total.
2. Make `t1_round_trip_spread_bps` reject non-finite or negative spread input.
3. Add discrete funding-stamp counting for the fixed four-hour episode.
4. Add regression tests covering taker/taker composition, stress `0.5/1/2`, invalid spread, and
   component reconciliation.
5. Correct `docs/references/dataset-reference.md` and `docs/references/architecture.md`: stored
   `SpreadBps` is an unusable mean-price skew with no tick floor.
6. Quarantine that field in the signed-bar/staging access path; preserve stored bytes and expose it
   only as `MeanPriceSkewBps` with status `UNUSABLE_AS_SPREAD`.
7. Verify the archived INFR-017 hash-pinned artifact only to enforce the `UNUSABLE` quarantine.
   Expose no spread cost pins. Chapter-05 accounting charges fees plus discrete funding only;
   spread cost is unavailable and not charged, so reported cost understates total cost and every
   strategy report must disclose that implication.
8. Obtain fresh-context QA approval of the patch and focused tests.

This is a bounded infrastructure patch. It is not a research run and must not read outcomes,
analysis-TEST, or the holdout.

Evidence: [`chapter-05-cost-data-preflight.md`](chapter-05-cost-data-preflight.md) and fresh-context
QA history and amendment approval live in
[`chapter-05-cost-data-preflight-qa.md`](chapter-05-cost-data-preflight-qa.md).

## 3. Enforcement

- `docs/experiments-docs/INDEX.md` is the live gate record. The preflight passed; family
  registration still requires separate operator authorisation.
- `.agents/skills/research-pipeline/_pipeline-config.md` requires this file to be read. Research
  design/execution remains forbidden until the family is registered and separately authorised.
- After the gate passes, the operator must separately authorise family registration and Run 1.
  Passing infrastructure QA is not research approval.
- The complete signal, cost, controls, report-layer, power, Run 2, risk, and shadow contracts remain
  frozen in the governing brief and must be translated without substantive change into the first
  checkpoint design.
