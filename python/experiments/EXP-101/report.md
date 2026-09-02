# Experiment Report: EXP-101 — Level configuration and later-swing outcomes

**Checkpoint 019 closed 2026-09-02.** Numbers below are the **winner-only** leftover
slice (completed primaries). AMENDMENT-17 (every eligible confirmed raid) was specified
and then stopped; those tables were not produced. Operator: this slice is not a
live-raid object and is not a trade.

## Status: INCONCLUSIVE — WINNER-ONLY SLICE; CHECKPOINT CLOSED

**Date:** 2026-09-02
**Family:** `CF-LIQSWP-001/HYP-001`
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

Do higher-degree or longer-window liquidity levels show a different leftover swing
after a completed primary raid than their short baselines?

## Hypothesis

`HYP-001`: later-swing magnitude, duration, or strong-move rate differs across
level-configuration families versus the declared same-stratum comparators
(Family A `PREVIOUS_1H`, Family B `PREVIOUS_ASIA`, Family C `ROLLING_7`).

## Method summary

Frozen EXP-100 TRAIN raids only. Outcome rows: completed, primary, ATR-defined.
Each arm is read against its fixed comparator in the same named stratum. Integrity
uses the registered future-destroy artifact (not recomputed). Independent means
were checked on two cell-groups. VAL-009/010 later characterised selection and
anatomy on the same emission; they do not change this experiment’s estimand.

## Operator verdict

**INCONCLUSIVE.** Recorded 2026-09-02: complete EXP-101; do not treat a strong-move
pattern on some families as a general level-degree mechanism; do not promote the
family; no TEST, holdout, or tradability claim.

Analyst recommendation in [analysis.md](analysis.md) was also **INCONCLUSIVE**. They
match.

## Integrity

| Check | Result |
|---|---|
| Estimand gate (EXP-100 copy) | `blocking_pass=true`, 264/264 |
| Zero-cost | PASS; `n_fills=0` |
| Holdout | untouched |
| Future-destroy | 0 survivals on biting rows; median collapse ~0.002 |
| Local accounting | none |

## Key findings

### Finding 1: Strong-move rate falls on longer previous-period and rolling windows

Family A vs `PREVIOUS_1H`: 144/144 registered strata have a bootstrap 95% CI below 0
on `strong_move`. Family C vs `ROLLING_7`: 132/144 CIs below 0. Example EURUSD 15m
1H LOW: 1H 0.902 → 4H 0.849 → 1D 0.777 → 1W 0.744. Destroy collapses biting rows.

**Interpretation:** a descriptive rate drop exists on those two families. It is not
a larger leftover swing.

### Finding 2: Session family and the declared mean channels do not carry it

Family B vs `PREVIOUS_ASIA`: strong-move CIs exclude 0 in 2/96 strata. Mean
`swing_atr` overlaps 0 in 346/384 strata; mean duration overlaps 0 in 368/384.
Where duration does separate it is often *longer*; where ATR separates it is
*smaller*. VAL-010: that composition sits in a larger first push and a smaller
leftover, not in a shorter clock.

### Finding 3: 528-style counts double-count method copies

BREAKOUT_BAR and LEVEL_CLOSE contrasts are identical. Independent grids are about
half the labelled strata (physical settings, not 264 independent methods).

## Conclusion

**Hypothesis INCONCLUSIVE.**

Some configs differ on the strong-move *rate*. The declared later-swing pair
(ATR size and duration) does not move together, session “degree” does not
separate, and method copies inflate agreement counts. That is not a general
higher-degree leftover-swing mechanism, and it is not a trade.

## Registry disposition

**Updates applied — evidence rows only.** `CF-LIQSWP-001` status remains
`REGISTERED`. HYP-001 recorded INCONCLUSIVE in
`docs/signal-registry/multiplicity-registry.md` and
`docs/signal-registry/candidate-families/cf-liqswp-001.md`. **0 counted TEST
reads, 0 holdout reads, 0 candidate slots.**

## Limitations

- Completed primaries are ~8% of emitted raids (VAL-009). This is a selected slice.
- Full 264-cell raw recompute of live means was not rerun (two cell-groups matched).
- No P&L, occupancy, or PSR object exists.

## Implications for future research

- Do not treat “higher-degree level” as a single later-swing story.
- Any follow-up that needs a new question is a new experiment. HYP-005 remains deferred.

## Recommended next experiments

1. None required to close EXP-101.
2. Family action only at an operator-signed checkpoint retrospective.

## Artifacts

| Artifact | Path |
|----------|------|
| Design | [design.md](design.md) |
| QA | [qa-review.md](qa-review.md) |
| Analysis | [analysis.md](analysis.md) |
| Characterisation used by the operator | [../VAL-009/analysis.md](../VAL-009/analysis.md), [../VAL-010/analysis.md](../VAL-010/analysis.md) |
| Results | [results/](results/) |
