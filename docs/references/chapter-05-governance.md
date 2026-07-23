# Chapter 05 Governance — Volatility-to-Direction Conversion

**State:** `CHECKPOINT-016 OPEN / RUN-1 A7/A8 IMPLEMENTATION + FRESH QA`

**Governing brief:** `.ignore/what-next/alts/intraday-way-forward-plan.md`

**Family:** `CF-VOLCONV-001` — `REGISTERED` 2026-07-22

This file records the approved route and its enforcement boundary. The cost/data preflight is
revised by the operator to omit spread cost and approved by fresh QA. The family/checkpoint are now
registered/open; no run is approved and no outcome has been exposed.

The outcome-free census and final `SPDR-011/design.md` are complete. The raw five-symbol signed
source is mounted/readable and the full TRAIN custom catalog is verified: 3,731,908 rows, 90 files,
tree sha `d4b7bbed…f7d2b9`, zero TEST/holdout reads. Fresh QA is now the pre-execution gate.

## 1. Fixed route

- Exactly two historical TRAIN-only runs: one SPDR characterisation, then one frozen Nautilus
  EXP strategy replay if the operator authorises it.
- The operator-approved route exception is `SPDR → EXP`; XENA is not used because there is no
  candidate grid or portfolio search.
- DESIGN report layers are read sequentially from one frozen Run-1 artifact. Each layer requires
  an operator decision before the next is opened.
- Run 1 executes DESIGN only. One rule is frozen before a separately authorised CONFIRM execution
  and read. CONFIRM cannot select a replacement.
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

- `docs/experiments-docs/INDEX.md` is the live gate record. The family is registered and
  checkpoint-016 is open; Run-1 execution still requires separate operator authorisation.
- `.agents/skills/research-pipeline/_pipeline-config.md` requires this file to be read. The family is
  registered; execution remains forbidden until the design, fresh QA and separate approval complete.
- The operator authorised the A7/A8 repair, fresh QA, and a clean Run 1 on 2026-07-23. Outcome
  execution remains conditional on fresh QA APPROVE; CONFIRM remains unexecuted and unauthorised.
- The complete signal, cost, controls, report-layer, power, Run 2, risk, and shadow contracts remain
  frozen in the governing brief and must be translated without substantive change into the first
  checkpoint design.
