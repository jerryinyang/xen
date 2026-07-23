# Chapter 05 Research Status

## Current checkpoint status

**CHECKPOINT-016 OPEN — RUN-1 A11 REPAIR / FRESH QA PENDING.** `CF-VOLCONV-001` is
registered. The outcome-free census located 1,390 DESIGN events on 148 dates; no outcome artifact,
SPDR execution, EXP execution, historical TEST read, holdout read, or forward shadow is active.

The governing route is [Chapter 05 governance](../references/chapter-05-governance.md). The
five-symbol signed TRAIN catalog is verified; complete fresh QA, then request separate Run-1
execution authority.

## Current infrastructure tasks

| Task | Status | Exit condition |
|---|---|---|
| Chapter 05 cost/data preflight | **PASSED / NO-SPREAD AMENDMENT QA APPROVED** | 53 focused and 224 retained tests pass; spread proxies removed; partial-cost caveat enforced; QA run 10 approves |

Implementation evidence: [Chapter 05 cost/data preflight](../references/chapter-05-cost-data-preflight.md).

## Family indexes

- [`CF-VOLCONV-001`](../signal-registry/candidate-families/cf-volconv-001.md) — `REGISTERED`;
  checkpoint-016; `SPDR-011 → EXP-099` conditional route; 0 counted reads.

## Current checkpoint

- [Checkpoint 016 design](checkpoints/2026-07-22-016-volatility-direction-conversion/design.md) —
  OPEN; the next clean Run-1 exposed one adapter order larger than its execution tick; A11 is
  operator-authorised and
  must receive fresh QA APPROVE before the clean DESIGN-only rerun.

## Checkpoint retrospectives

None in Chapter 05.
