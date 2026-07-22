# Chapter 05 Governance — Volatility-to-Direction Conversion

**State:** `PRE-EXPERIMENT / BLOCKED_PRECHECK`

**Governing brief:** `.ignore/what-next/alts/intraday-way-forward-plan.md`

**Proposed family:** `CF-VOLCONV-001` — not yet registered

This file records the approved route and its enforcement boundary. It does not implement the
cost/data patch, register a family, approve an experiment, or expose an outcome.

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

## 2. Blocking preflight

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
7. Verify the five fixed cost pins against the archived INFR-017 hash-pinned artifact at process
   start.
8. Obtain fresh-context QA approval of the patch and focused tests.

This is a bounded infrastructure patch. It is not a research run and must not read outcomes,
analysis-TEST, or the holdout.

## 3. Enforcement

- `docs/experiments-docs/INDEX.md` is the live gate record. It remains
  `BLOCKED ON COST/DATA PREFLIGHT` until evidence for all eight items is linked there.
- `.agents/skills/research-pipeline/_pipeline-config.md` requires this file to be read and forbids
  registration/design/execution while the live gate is blocked.
- After the gate passes, the operator must separately authorise family registration and Run 1.
  Passing infrastructure QA is not research approval.
- The complete signal, cost, controls, report-layer, power, Run 2, risk, and shadow contracts remain
  frozen in the governing brief and must be translated without substantive change into the first
  checkpoint design.
