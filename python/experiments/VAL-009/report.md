# Experiment Report: VAL-009 — Raid selection and lifecycle

## Status: COMPLETED — CHARACTERISATION

**Date:** 2026-09-02
**Family:** `CF-LIQSWP-001` (read-only re-analysis of EXP-100)
**Population:** cTrader TRAIN; physical grid 132 settings (264 source cells are BB/LC copies)

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

How do raid lifecycle, primary selection, level age, and exact prior-raid count look in
the frozen EXP-100 TRAIN emission?

## Method

Read-only TRAIN scan of `raids.parquet`. Physical grid collapses only BREAKOUT_BAR /
LEVEL_CLOSE. No engine rerun. Gate: `results/estimand_validation.json` `blocking_pass=true`.

## Operator verdict

**Characterisation complete.** Completed primaries are a selected slice, not “all raids.”
Checkpoint 019 closed this as evidence, not as a trade. See
[analysis.md](analysis.md).

## Key findings

Physical grid, 4,920,239 raid rows:

| Status | Rows | Share |
|---|---:|---:|
| FAILED_BREAKOUT | 2,351,450 | 47.8% |
| CONFIRMED_NON_PRIMARY | 2,158,300 | 43.9% |
| COMPLETED | 394,663 | 8.0% |

- 394,916 selection sets; **exactly one primary** in every set; 76.2% of sets compete.
- Exact prior count: 0 = 11.4%; 1 = 10.3%; 2+ = 78.2% of **all** raid rows.
- Level age: median 7.5 h; mean 8.65 d (long tail).
- Raw source rows are exactly 2× physical.

**Confirmed-not-primary** means: eligible at the same confirmation as a newer raid, closed
without owning the leftover. That 44% is the live-looking object EXP-101–104 did not score.

## Registry disposition

Evidence row only. Family closed at checkpoint 019 as characterised, not tradable.
**0 counted TEST reads, 0 holdout reads.**

## Artifacts

| Artifact | Path |
|----------|------|
| Design | [design.md](design.md) |
| Analysis | [analysis.md](analysis.md) |
| Results | [results/selection_summary.json](results/selection_summary.json) |
