# Experiment Report: EXP-104 — Causal volatility regime and later-swing outcomes

## Status: COMPLETED — DESCRIPTIVE ATR / STRONG-MOVE ONLY

**Date:** 2026-09-02
**Family:** `CF-LIQSWP-001/HYP-004`
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

Do calm (LOW) and wild (HIGH) causal volatility states at raid time show different
leftover swings, and different raid-start rates, than the mid state?

## Hypothesis

`HYP-004`: LOW and HIGH differ from MID in later-swing outcomes **and** in
all-raid frequency.

## Method summary

Frozen EXP-100 TRAIN. Outcome contrasts: completed primary, ATR-defined, LOW/HIGH
vs MID in the same named stratum. Frequency is a separate start-rate (preceding
marks vs next-mark starts). Registered CIs/destroy from
`results/analysis_results.json`. VAL-011 rebuilt design-faithful all-raid
frequency on the physical grid and kept ATR, strong-move, and duration separate.

## Operator verdict

**Descriptive on ATR / strong-move only — duration and frequency do not confirm.**
Recorded 2026-09-02: calm completed leftovers are usually larger in ATR; wild
completed leftovers are usually smaller; the clock goes the other way on HIGH
(smaller leftover, longer time); start-rate is highest in HIGH while leftover ATR
is weaker, so frequency cannot confirm the swing story; method copies are not
independent; no family promotion; no TEST, holdout, or tradability claim.

Analyst recommendation in [analysis.md](analysis.md) was **SUPPORTED** (descriptive
HYP-004). The operator narrowed that tag.

## Integrity

| Check | Result |
|---|---|
| Estimand gate | `blocking_pass=true`, 264/264 |
| Zero-cost | PASS; `n_fills=0` |
| Holdout | untouched |
| Destroy on biting outcome contrasts | 0 survivals; collapse \|ratio\| ≤ 0.026 |
| VAL-011 profile join | 4,920,239 physical raids = profiles |

## Key findings

### Finding 1: Completed leftovers differ by regime on ATR / strong-move

Registered: LOW−MID `swing_atr` interval above 0 in 400/528 labelled strata;
HIGH−MID below 0 in 434/528. Strong-move follows the same LOW-up / HIGH-down
pattern (weaker coverage). VAL-011 physical side-strata (132 settings × 2 sides):
HIGH vs MID strong-move down on 257/264 (mean Δ −0.072); leftover ATR down on
258/264 (mean Δ −0.92 ATR). LOW vs MID leftover ATR up on 263/264 (mean Δ +0.85 ATR).

**Interpretation:** among completed primaries, calm leftovers tend to be larger
in ATR units; wild leftovers tend to be smaller. LOW and HIGH move in opposite
directions versus MID — “differ” is true; “wild → bigger leftover” is not.

### Finding 2: Duration goes the other way on HIGH; frequency disagrees with leftovers

VAL-011 HIGH vs MID duration: **longer** on 219/264 strata (mean Δ **+2.2 hours**)
while ATR/strong-move are **weaker**. LOW vs MID duration: **shorter** on 217/264
(mean Δ **−0.9 hours**) while ATR is **larger**. Calm ≈ bigger leftover in less
time; wild ≈ smaller leftover that takes more hours.

All-raid starts per 1,000 preceding marks (VAL-011 physical): HIGH 1451, MID 1277,
LOW 1244. HIGH starts more raids and then shows *weaker* completed leftovers.
Registered live frequency also had construction defects (starts ≠ all-raid starts
on the checked cell). Frequency remains descriptive and is not a confirming channel.

### Finding 3: Method copies and missing confirmation-regime

BB/LC duplicate the same physical setting. VAL-011 confirmation_regime is null in
the largest transition buckets, so a raid→confirmation→endpoint path census is not
usable for most rows.

## Conclusion

**Hypothesis partially described, not mechanism-supported.**

Causal vol state at raid time describes leftover ATR / strong-move among completed
primaries. Duration and start-rate do not tell that same story. This is not a trade
and does not change family status.

## Registry disposition

**Updates applied — evidence rows only.** Family status remains `REGISTERED`.
HYP-004 recorded as descriptive ATR/strong-move only. **0 counted TEST reads,
0 holdout reads, 0 candidate slots.**

## Limitations

- Hypothesis was a conjunction; frequency was the weak half and stays weak.
- XAUUSD / 60m ATR intervals overlap 0 more often than USTEC / 30m.
- No economic object.

## Implications for future research

- Do not read “HIGH vol” as “big leftover, fast.”
- Keep start-rate and leftover-swing tables in separate populations.

## Recommended next experiments

1. None required to close EXP-104.
2. Family action only at checkpoint retrospective.

## Artifacts

| Artifact | Path |
|----------|------|
| Design | [design.md](design.md) |
| QA | [qa-review.md](qa-review.md) |
| Analysis | [analysis.md](analysis.md) |
| Regime / frequency characterisation | [../VAL-011/analysis.md](../VAL-011/analysis.md) |
| Results | [results/](results/) |
