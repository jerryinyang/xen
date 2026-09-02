# Experiment Report: VAL-010 — Later-swing anatomy

## Status: COMPLETED — CHARACTERISATION

**Date:** 2026-09-02
**Family:** `CF-LIQSWP-001` (read-only re-analysis of EXP-100)
**Population:** TRAIN completed primaries, ATR-defined; physical grid

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

When leftover strong-move rates differ by repeat band, is that a smaller leftover, a
larger first push, or a shorter clock?

## Method

Completed primary, ATR-defined rows. Physical unique on `physical_cell, raid_id`.
Contrast keys are physical setting × side (264 = 132 × 2, not BB/LC copies).

## Operator verdict

**Characterisation complete.** Repeat-band ATR/strong-move differences sit in excursion
and surplus, **not** duration. This still describes the 8% winner slice. Checkpoint 019
closed without treating it as an edge.

## Key findings

Physical completed primaries n=394,607: mean first push 1.60 ATR; mean leftover 3.69 ATR;
mean surplus 2.08 ATR; strong-move 0.831; median clock 5 h.

1 vs 0, 264 side-strata: strong-move down 255/264 (mean Δ −0.240); leftover ATR down
237/264 (mean Δ −1.11); duration 130 shorter / 134 longer.

## Registry disposition

Evidence row only. **0 counted TEST reads.**

## Artifacts

| Artifact | Path |
|----------|------|
| Design | [design.md](design.md) |
| Analysis | [analysis.md](analysis.md) |
| Results | [results/anatomy_summary.json](results/anatomy_summary.json) |
