# Experiment Report: VAL-011 — TPO geometry, regime, and all-raid frequency

## Status: COMPLETED — CHARACTERISATION

**Date:** 2026-09-02
**Family:** `CF-LIQSWP-001` (read-only re-analysis of EXP-100)
**Population:** TRAIN; 132 physical settings

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

## Question

Do TPO geometry, vol-state transitions, and all-raid start rates describe different
raid populations — without using start-rate to confirm leftover ATR?

## Method

Left-join profiles; all-raid starts vs preceding marks; leftover contrasts keep ATR,
strong-move, and duration separate. Canonical one cell per BB/LC pair.

## Operator verdict

**Characterisation complete.** Geometry and start-rate are describable. They do **not**
confirm the leftover ATR split. Duration goes the other way on HIGH. Checkpoint 019 closed
without a trade claim.

## Key findings

- Profile join 4,920,239; defined gap span piled at 0.5–1.0 VA.
- Starts / 1,000 preceding marks: HIGH 1451; MID 1277; LOW 1244.
- HIGH vs MID leftover: strong-move **down** 257/264 side-strata; duration **up** 219/264
  (mean Δ +2.2 h). LOW vs MID leftover ATR **up**; duration **down**.
- Confirmation-regime is null in the largest transition buckets.

## Registry disposition

Evidence row only. **0 counted TEST reads.**

## Artifacts

| Artifact | Path |
|----------|------|
| Design | [design.md](design.md) |
| Analysis | [analysis.md](analysis.md) |
| Results | [results/conditioning_summary.json](results/conditioning_summary.json) |
