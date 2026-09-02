# Experiment Report: EXP-102 — Repeated raids and prior-raid count

**SUPERSEDED 2026-09-02.** AMENDMENT-17 rebuilds the later-swing population on
every raid eligible at confirmation. Numbers below are the old primary-only
slice and must not be used. Replacement analysis is in progress.

## Status: COMPLETED — DESCRIPTIVE ATR / STRONG-MOVE ONLY — SUPERSEDED

**Date:** 2026-09-02
**Family:** `CF-LIQSWP-001/HYP-002`
**Population:** cTrader TRAIN only — `EURUSD`, `XAUUSD`, `USTEC`
**Scope:** 264 AMENDMENT-14 cells; analysis-only re-read of frozen EXP-100

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

After a level has already been raided, is the leftover swing on the next completed
primary different from the first raid on that level?

## Hypothesis

`HYP-002`: prior-raid count bands `1` and `2+` differ from count `0` in later-swing
ATR, duration, or strong-move rate, within the same named stratum.

## Method summary

Frozen EXP-100 TRAIN. Outcome: completed primary, ATR-defined. Direct comparisons
are 1-vs-0 and 2+-vs-0 only. Registered bootstrap and destroy numbers are from
`results/analysis_results.json` (not recomputed). One cell matched 20/20 live means.
VAL-010 decomposed the same leftover into first push, leftover, surplus, and clock.

## Operator verdict

**Descriptive on ATR / strong-move only — not a mechanism, not an edge.** Recorded
2026-09-02: later completed raids usually show a smaller leftover swing and a lower
strong-move rate than first raids; duration does not confirm; independent settings
are the physical grid (method copies are not extra agreement); no family promotion;
no TEST, holdout, or tradability claim.

Analyst recommendation in [analysis.md](analysis.md) was **SUPPORTED**. The operator
narrowed that tag.

## Integrity

| Check | Result |
|---|---|
| Estimand gate | `blocking_pass=true`, 264/264 |
| Zero-cost | PASS; `n_fills=0` |
| Holdout | untouched |
| Future-destroy | `destroyed_survives=0` on registered biting rows |
| One-cell raw match | 20/20 |

## Key findings

### Finding 1: Later raids show a smaller leftover and fewer strong moves

Registered 1-vs-0 `strong_move`: 438/528 labelled strata have bootstrap 95% CI below
0; **0** above; median contrast about −0.245. 2+-vs-0 `swing_atr`: 354/528 CIs below
0 vs 2 above; median contrast about −1.23 ATR.

VAL-010 physical grid (132 settings × 2 sides = 264 side-strata, not 264 method
copies): 1-vs-0 strong-move lower on 255/264 (mean Δ −0.240); leftover ATR lower on
237/264 (mean Δ −1.11 ATR). Anatomy: first raids have a small initial push and a
large surplus; second raids often have a large initial push and a small or negative
surplus.

**Interpretation:** the leftover after confirmation is usually smaller on later
completed raids. That is a description of selected completed primaries.

### Finding 2: Duration does not confirm

Registered duration mostly overlaps 0. VAL-010 1-vs-0 duration: 130 strata shorter /
134 longer; median Δ +0.03 h around a ~5 h median. The clock is not the same story
as ATR / strong-move.

### Finding 3: Method copies and selection

BB/LC pairs are the same physical raids. Labelled 528 strata overstate independent
agreement by about 2×. VAL-009: completed primaries are ~8% of all raid rows; this
contrast is not a census of every raid start.

## Conclusion

**Hypothesis partially described, not mechanism-supported.**

Later completed primaries usually leave a smaller ATR leftover and trigger
`strong_move` less often than first raids. Duration does not move with that
pattern. This is not a trade and does not change family status.

## Registry disposition

**Updates applied — evidence rows only.** Family status remains `REGISTERED`.
HYP-002 recorded as descriptive ATR/strong-move only. **0 counted TEST reads,
0 holdout reads, 0 candidate slots.**

## Limitations

- Duration was a declared later-swing channel and does not separate cleanly.
- Band 2+ is not a monotone continuation of band 1 (strong-move partially recovers).
- No economic object.

## Implications for future research

- Keep first-vs-later as a characterisation of completed leftovers, not as an entry rule.
- Do not use duration or raid-start rate to “confirm” this pattern.

## Recommended next experiments

1. None required to close EXP-102.
2. Family action only at checkpoint retrospective.

## Artifacts

| Artifact | Path |
|----------|------|
| Design | [design.md](design.md) |
| QA | [qa-review.md](qa-review.md) |
| Analysis | [analysis.md](analysis.md) |
| Anatomy characterisation | [../VAL-010/analysis.md](../VAL-010/analysis.md) |
| Results | [results/](results/) |
