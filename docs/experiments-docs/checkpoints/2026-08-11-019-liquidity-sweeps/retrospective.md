# Checkpoint 019 retrospective — Liquidity sweeps

**Closed:** 2026-09-02
**Family:** `CF-LIQSWP-001`
**Operator disposition:** **RETIRED — CHARACTERISED, NOT TRADABLE**

ZERO-COST-DISCLOSURE
  cost_model: NO_COST_CHARGED
  spread: not modeled
  commissions: not modeled
  swaps/funding: not modeled
  implication: every figure in this document is gross and cost-free; no spread,
    commission, or swap enters any calculation. Realised results would differ
    (likely worse) under any real cost schedule.
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  lifting: only an explicit operator directive may introduce a cost model for a
    scoped experiment; the directive is recorded in that experiment's design.md.

## What this checkpoint asked

Can liquidity levels be recorded as causal objects, and do later leftovers after a
raid differ by level type, repeat count, TPO tightness, or volatility state?

It did **not** ask for a trade, a TEST read, or a live prediction of a raid in progress.

## What was run

| ID | Role | Operator record |
|---|---|---|
| EXP-100 | Apparatus | COMPLETED with ATR-undefined excursion values excluded |
| EXP-101 | Level config vs leftover | INCONCLUSIVE on the **winner-only** leftover slice |
| EXP-102 | Repeat count vs leftover | Descriptive ATR/strong-move only on that same slice |
| EXP-103 | Tight TPO gap vs leftover | INCONCLUSIVE on that same slice |
| EXP-104 | Vol state vs leftover / start-rate | Descriptive ATR/strong-move only; duration and start-rate disagree |
| VAL-009 | Selection census | Completed primaries are ~8% of raid rows; ~44% confirm but are not primary |
| VAL-010 | Leftover anatomy | Repeat drop sits in a larger first push / smaller leftover; duration does not confirm |
| VAL-011 | Geometry / frequency | HIGH starts more raids then shows a smaller leftover; confirmation-regime mostly missing |

No TEST. No holdout. Independent physical settings collapse BB/LC (~132, not 264 methods).

## Binding lesson

The leftover numbers in EXP-101–104 describe **the raid that won primary after confirmation**,
not the raid a trader would have been sitting in. About five confirmed-not-primary raids exist
for each completed primary. “Which raid is last” is not known while the raid is live.

AMENDMENT-17 was specified to attach the shared leftover to every eligible confirmed raid on
the frozen emission (no EXP-100 rerun). The full 10k-resample rebuild was **stopped**. Those
tables were not produced. Code for the attach remains in `xen.liqswp_analysis.leftover`.

## Family decision (operator-signed)

**RETIRED — CHARACTERISED, NOT TRADABLE.**

Grounds:

1. The streaming apparatus works (EXP-100), with a scoped ATR-undefined exclusion.
2. Winner-only leftover differences are not a live-raid object and are not an edge.
3. Duration and start-rate do not confirm the ATR/strong-move descriptions.
4. The live-object amendment was not computed.
5. Re-opening requires a leftover estimand that does **not** peek at who later won primary
   (eligible-at-confirmation, or earlier). It does not require a new exit, cost model, or
   EXP-100 rerun of the same winner-only tables.

HYP-005 (breakout-causing levels) remains deferred and was not run.

Counted TEST reads: **0**. Candidate slots: **0**.
