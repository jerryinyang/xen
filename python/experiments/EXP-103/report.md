# Experiment Report: EXP-103 — TPO value gaps and tight-gap outcomes

**Checkpoint 019 closed 2026-09-02.** Numbers below are the **winner-only** leftover
slice (completed primaries). AMENDMENT-17 was specified and then stopped. Operator:
inconclusive on that slice; not a live-raid object; not a trade.

## Status: INCONCLUSIVE — WINNER-ONLY SLICE; CHECKPOINT CLOSED

**Date:** 2026-09-02
**Family:** `CF-LIQSWP-001/HYP-003`
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

When the TPO profile of a completed primary raid is labelled tight-gap, is the
leftover swing different from other defined profiles in the same stratum?

## Hypothesis

`HYP-003`: tight DEFINED profiles differ from same-stratum non-tight DEFINED
profiles on later-swing ATR and duration (co-primary), with strong-move as a
companion channel.

## Method summary

Frozen EXP-100 TRAIN. Join `tpo_profiles.parquet` on `(raid_id, profile_generation)`.
Comparator is non-tight DEFINED in the same named stratum. Registered CIs and
destroy from `results/analysis_results.json`. One cell matched live means.
VAL-011 described continuous gap span on the same profiles.

## Operator verdict

**INCONCLUSIVE.** Recorded 2026-09-02: complete EXP-103; a smaller mean ATR on the
tight arm is not enough while duration does not separate, the tight arm is rare,
and method copies double-count agreement; no family promotion; no TEST, holdout,
or tradability claim.

Analyst recommendation in [analysis.md](analysis.md) was also **INCONCLUSIVE**.

## Integrity

| Check | Result |
|---|---|
| Estimand gate | `blocking_pass=true`, 264/264 |
| Zero-cost | PASS; `n_fills=0` |
| Holdout | untouched |
| Profile join (VAL-011 physical) | raids = profiles = 4,920,239 |
| Destroy on biting ATR | 0 survivals; median \|collapse\| ≈ 0.005 |

## Key findings

### Finding 1: Tight-gap completed leftovers are usually smaller in ATR

504/528 labelled strata have tight mean `swing_atr` below non-tight; 344/528
bootstrap 95% CIs entirely below 0; 0 entirely above. Tight n ≈ 46,528 vs
non-tight ≈ 742,516 (~6% of the outcome population).

### Finding 2: Duration does not jointly move; strong-move even disagrees

Duration CIs overlap 0 in 436/528 strata. Strong-move point estimates are
*positive* in 382/528 (tight more often flagged strong-move) while mean ATR is
*smaller* — mixed internals, not one “tight gap → continued displacement”
story. VAL-011: `gap_span_va` itself piles up between 0.5 and 1.0, so continuous
span is not a wide discriminator.

### Finding 3: Method copies and confounding

264/264 BB/LC pairs are identical HYP-003 contrasts. A 6% tight slice can differ
because it selected a different excursion-to-confirm geometry, not because the
later path *responds* to tightness.

## Conclusion

**Hypothesis INCONCLUSIVE.**

Tight defined profiles often show a smaller leftover ATR. That is not the
declared later-swing pair, it is a rare arm, and it is not an edge.

## Registry disposition

**Updates applied — evidence rows only.** Family status remains `REGISTERED`.
HYP-003 recorded INCONCLUSIVE. **0 counted TEST reads, 0 holdout reads,
0 candidate slots.**

## Limitations

- Median tight `arm_n` is small (about 61; 106 strata < 30). Intervals are wide;
  they were reported, not dropped.
- 184/528 ATR intervals still overlap 0.
- Confirmation-path regime is mostly missing in VAL-011; not used here.

## Implications for future research

- Do not treat `tight_gap` as a later-swing trigger without a geometry-matched
  comparison (e.g. similar VA width).
- Continuous gap span did not open a new separator on this emission.

## Recommended next experiments

1. None required to close EXP-103.
2. A VA-width-matched contrast would be a new experiment if wanted.

## Artifacts

| Artifact | Path |
|----------|------|
| Design | [design.md](design.md) |
| QA | [qa-review.md](qa-review.md) |
| Analysis | [analysis.md](analysis.md) |
| Geometry characterisation | [../VAL-011/analysis.md](../VAL-011/analysis.md) |
| Results | [results/](results/) |
