# Experiment Report: EXP-100 — Liquidity-sweep streaming apparatus

## Status: COMPLETED — HYP-000 UPHELD

**Date:** 2026-08-13  
**Family:** `CF-LIQSWP-001/HYP-000`  
**Population:** cTrader TRAIN only — `EURUSD`, `XAUUSD`, `USTEC`  
**Scope:** 264 AMENDMENT-13 cells; 15m/30m observations confirm on 1H, 1h observations confirm on 1H and 4H

## Question

Does the causal streaming apparatus preserve the identity and chronology of
liquidity levels, excursions, raids, confirmation, breakout/failure states,
TPO profiles, and later-swing fields across the frozen 264-cell TRAIN matrix?

## Hypothesis and mechanism

`CF-LIQSWP-001/HYP-000`: the streaming state machine preserves those objects
causally and reproducibly on the AMENDMENT-13 definition. A completed
observation bar that goes strictly beyond a level starts a live raid; a same-bar
return is recorded but does not close it. Confirmation/fail on the reference
clock settles the object, and the later opposing event closes the primary swing.

This is a measurement-validity experiment, not a value, tradability, or
deployment experiment.

## Method

- Nautilus `BacktestNode` emitted the frozen cTrader TRAIN matrix from 1-minute
  real OHLCV input.
- Raid start/return/beyond were evaluated on the completed observation bar;
  TPO bins, maximum-excursion reset, and later swing fields used 1-minute input.
- The family estimand gate was run over all 264 published cells. Independent
  analysis scripts re-derived coverage, object identity, chronology, method
  overlap, trading-clock, TPO, and future-destroy checks.
- Results are reported per cell and per declared stratum. No TEST or holdout
  data was loaded, and no new EXP-100 emission is required.

## Integrity gate

| Check | Observed result | Evidence |
|---|---|---|
| Family estimand validation | `blocking_pass: true`; 264 cells | [estimand_validation.json](results/estimand_validation.json) |
| Per-cell validity | 264/264 `blocking_pass: true` | [full cell gates](results/execution/full/) |
| Fence and holdout | Pinned cTrader TRAIN fence; no holdout timestamps | [analysis.md](analysis.md) §1, Q25/Q29 |
| Causal provenance | Signal fields end before TRAIN boundary; only endpoint/censor stamps reach it | [analysis.md](analysis.md) §1, Q25/Q29 |
| Future-destroy validity | 264/264 changed; zero fixed points; non-vacuous outcome change | [analysis.md](analysis.md) §1, Q13 |
| Reconciliation / object identity | No leg ledger by design; duplicate and orphan checks are zero | [analysis.md](analysis.md) Q1–Q3, Q24 |
| Zero-cost compliance | `NO_COST_CHARGED`; no non-zero cost columns | [analysis.md](analysis.md) §1, Q11 |
| Local accounting | No experiment-local accounting definitions | [analysis.md](analysis.md) §1 |

## Evidence for the hypothesis

1. **Complete matrix:** 264 cells are present: 66 at 15m, 66 at 30m, and 132
   at 1h. The 11 level configurations and the 1H/4H confirmation grid are
   present; no cell is empty.
2. **Object identity:** 9,840,478 raids were emitted. Duplicate level IDs and
   raid IDs are zero; missing/extra profile joins are zero; unknown status
   values are absent; no active level or raid remains unsettled at the run end.
3. **Chronology:** excursion ≤ return, confirmation follows the sweep, endpoint
   follows confirmation, and timestamp-grid checks are all zero-failure.
4. **AMENDMENT-13:** 7,669,654 same-bar returns are recorded without closing
   the raid; the golden trace keeps the raid live and reports no ambiguity.
5. **Future-destroy:** every cell changes under the zero-fixed-point destroy;
   mean absolute swing change is at least `2.8 × SE` in every cell. This is a
   validity result, not an economic score.
6. **Independent probes:** three completed raids re-derived from raw `bar_marks`
   reproduce emitted maximum excursion exactly. BREAKOUT_BAR and LEVEL_CLOSE
   agree on 132/132 shared method pairs; the overlap is disclosed, not pooled.
7. **Clock/profile invariants:** 1D anchors are 640–644 per cell, 1W anchors are
   129, weekend-dated anchor keys are zero, TPO conservation failures are zero,
   and the tightness/gap-mass rules match the frozen definitions.

## Evidence against or limiting the hypothesis

- The golden probe's aggregate booleans `t1_one_completed_or_settled` and
  `t2_exists` are false, and `t1_non_primary_if_both_confirmed` is null. The
  raw terminal summaries show the intended AMENDMENT-6/13 states, but the probe
  indexed the first raid per level after a synthetic feed re-pierced the level.
  This remains a probe limitation until a per-raid assertion is run.
- The emission does not retain the full 1-minute path from raid to confirmation
  or from confirmation to swing end. A later question about retracement into a
  gap box cannot be answered from `swing_extreme` alone.
- This apparatus emits no orders, fills, or P&L ledger (`n_fills: 0`), so no
  mean-trade/leg bps read exists and PSR is not applicable.
- 46,410 profiles are undefined (0.47%) and their reason distribution was not
  separately summarized. Right-censoring affects 30,520 excursions, 626
  confirmations, and 506 endpoints at the TRAIN boundary.
- Same-bar returns are common: the median fraction is 0.780, with a full-cell
  range of 0.752–0.799. This is a coverage observation under AMENDMENT-13, not
  a machine disposition.

## Analyst recommendation (not the operator verdict)

The analyst recommends **upholding HYP-000**: the state machine is
measurement-valid and coverage-complete for the frozen 264-cell TRAIN object.
The evidence is strongest in the clean family/per-cell validity gates, zero
fixed-point future-destroy results, AMENDMENT-13 replay, and independent raw-bar
recomputation.

## Operator verdict

**HYP-000 UPHELD — operator-confirmed (2026-08-13).** Operator decision recorded
verbatim: “EXP-100 approved as recommended and confirmed.” This is the
experiment-level verdict. The `CF-LIQSWP-001` family remains `REGISTERED`; no
candidate-family status transition, TEST read, or holdout action is recorded.

## Zero-cost disclosure

```text
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
```

## Registry and read accounting

- Candidate-family status: unchanged — `CF-LIQSWP-001` remains `REGISTERED`.
- Evidence disposition: `EXP-100` complete; HYP-000 upheld by operator confirmation.
- Counted TEST reads: 0.
- Holdout: sealed and untouched.
- Follow-on hypotheses `EXP-101`–`EXP-104` remain separate experiments; this
  report does not open, close, or promote any family branch.

## Limitations and follow-up

1. If desired, run a new analysis-only per-raid golden assertion for the probe
   indexing caveat; do not re-emit or read TEST/holdout.
2. A future experiment may predeclare a TRAIN regime split or undefined-TPO
   reason analysis; neither is silently added to EXP-100.
3. Under the current checkpoint handoff, EXP-101–104 use the validated EXP-100
   emission for their separate questions. Their fresh-context QA and operator
   progression gates remain independent.

## Artifacts

| Artifact | Path |
|---|---|
| Design | [design.md](design.md) |
| QA history | [qa-review.md](qa-review.md) |
| Analysis | [analysis.md](analysis.md) |
| Analysis code | [analysis_code/](analysis_code/) |
| Family estimand gate | [results/estimand_validation.json](results/estimand_validation.json) |
| Analysis results | [results/analysis/](results/analysis/) |
| Execution journal | [results/execution/full-journal.jsonl](results/execution/full-journal.jsonl) |
| Published cell gates | [results/execution/full/](results/execution/full/) |
| Plots | None generated; coverage tables are the primary evidence |
| Strategy/runner code | [code/](code/) |
