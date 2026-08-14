# Experiment Report: EXP-100 — Liquidity-sweep streaming apparatus

## Status: COMPLETED — OPERATOR-APPROVED WITH SCOPED EXCLUSION

**Date:** 2026-08-13
**Family:** `CF-LIQSWP-001/HYP-000`
**Population:** cTrader TRAIN only — `EURUSD`, `XAUUSD`, `USTEC`
**Scope:** 264 AMENDMENT-14 cells; 15m/30m observations confirm on 1H, 1h observations confirm on 1H and 4H

## Question and hypothesis

Does the causal streaming apparatus preserve the identity and chronology of liquidity levels,
excursions, raids, confirmation, breakout/failure states, TPO profiles, and later-swing fields
across the frozen 264-cell TRAIN matrix?

`CF-LIQSWP-001/HYP-000` proposed that the state machine preserves those objects causally and
reproducibly. A completed observation bar beyond a level starts a live raid; same-bar return is
recorded but does not close it; confirmation/fail settles the object; the later opposing event
closes the primary swing. This is a measurement-validity experiment, not a value, trading, or
deployment experiment.

## Scope and method

- Nautilus `BacktestNode` emitted 264 cTrader TRAIN cells from real 1-minute OHLCV input.
- The matrix covers three instruments, 15m/30m/1h observation bars, two confirmation methods,
  1H/4H reference strata, and eleven level configurations.
- Independent analysis re-derived coverage, object identity, chronology, method overlap,
  trading-clock behavior, TPO fields, lifecycle/status/attribution rules, AMENDMENT-14 retrace
  fields, and the future-destroy control from the retained emission.
- No TEST or holdout data was loaded. No orders, fills, trade ledger, P&L, or PSR estimand exists.
- No implementation change, rerun, or new emission is part of this disposition.

## Integrity and retained findings

| Check | Observed result | Interpretation boundary |
|---|---|---|
| Published estimand gate | `blocking_pass=true`; 264/264 cells | The supplied gate passes, but the independent ATR follow-up below overrides interpretation of the affected excursion values. |
| Fence / holdout | Pinned cTrader TRAIN fence; no post-TRAIN or holdout rows | Retained. |
| Identity and joins | 9,840,478 raids; duplicate raid/level IDs, missing/extra profile joins, and active residuals all 0 | Retained. |
| Chronology / lifecycle / status / attribution | Chronology and timestamp-grid failures 0; status totals reconcile; attribution checks 0 failures | Retained. |
| Future-destroy control | 264/264 cells changed; zero fixed points; 0 block-fragile cells | Retained for the declared finite normalized population only. |
| TPO / amendment mechanics | 9,794,210 defined profiles; 46,268 undefined (`45,400 GAP_UNDEFINED`, `868 ATR_UNDEFINED`); TPO conservation and AMENDMENT-14 field checks 0 failures | Retained except ATR-undefined excursion values. |
| Method comparison | 132/132 BREAKOUT_BAR/LEVEL_CLOSE pairs have identical IDs, statuses, and counts | Retained as measurement equivalence, not a ranking. |
| Trading path | No orders, fills, leg ledger, return, P&L, or PSR | No economic or deployment inference. |

Additional retained observations:

- All 264 declared cells are populated: 66 at 15m, 66 at 30m, and 132 at 1h.
- Pooled lifecycle totals are 4,702,900 `FAILED_BREAKOUT`, 4,316,600
  `CONFIRMED_NON_PRIMARY`, 789,326 `COMPLETED`, and 30,520/626/506
  excursion/confirmation/endpoint right-censors.
- Same-bar returns total 7,669,654; this is valid under AMENDMENT-13 and does not itself close a raid.
- AMENDMENT-14 retrace states are 728,936 `DEFINED`, 53,496
  `AMBIGUOUS_SAME_BAR`, and 7,400 `NO_POST_CONFIRMATION_MFE`.
- Calendar and profile findings remain valid: no weekend-dated 1D/1W anchor keys; TPO
  conservation, VA-mass, and tightness-rule failure counts are 0.

## Mandatory ATR-undefined exclusion

The retained emission has a scoped defect when `profile_undefined_reason=ATR_UNDEFINED`: the
initial observation's later source-minute extreme can be larger than the emitted maximum
excursion. These values are invalid for interpretation and are excluded from every excursion,
normalized-excursion, strong-move, and excursion-derived reading.

| Population | Result |
|---|---:|
| Emitted raid rows materially affected | **780 / 9,840,478 (0.007926%)** |
| Unique affected objects after confirmation-method deduplication | **390** |
| Affected primary/completed rows | **84** |
| Median relative understatement among affected rows | **71.43%** |

Supporting context: 868 emitted rows enter the ATR-undefined path; 780 are materially
understated and 88 show zero reconstructed initial-observation difference. After method
deduplication, 434 objects are exposed and 390 are affected. The full source-minute path and
any still-later maximum after the initial completed observation are not reconstructible from the
frozen emission.

The future-destroy control is unaffected because every ATR-undefined row is excluded from its
finite normalized population (`max_excursion_atr` is null). This excludes 112 primary rows,
including the 84 affected completed rows; none enters the 789,646 aligned finite-primary pairs.
The control therefore supports only that finite population and cannot validate the excluded
excursion values.

**Disposition boundary:** ATR-undefined excursion values are excluded. Coverage, chronology,
lifecycle, status, attribution, finite-population future-destroy, and other unaffected findings
are retained.

## Evidence for and against HYP-000

### Evidence for

- Complete declared matrix, clean identity/join reconciliation, and no chronology/status failures.
- Correct close-all-eligible attribution and same-bar-live lifecycle behavior in corrected golden fixtures.
- Broad state-object coverage across every declared grid value and every calendar year in scope.
- Non-vacuous, zero-fixed-point future-destroy behavior on the finite normalized population.
- AMENDMENT-14 retrace ambiguity and no-MFE states are explicit rather than silently numeric.

### Evidence against / limitations

- Maximum-excursion state is not exact on the ATR-undefined path; affected values are unusable.
- Same-bar returns dominate returned raids, so longer-lived return paths are a minority.
- Counts are concentrated by timeframe/configuration and are not exposure-normalized rates.
- Undefined profiles and ambiguous/no-MFE retraces cannot be treated as measured numeric values.
- No economic observation exists; nothing here supports profitability, tradability, or deployment.

## Analyst recommendation (not the operator verdict)

The analyst assigned no replacement verdict. The analysis recommends stopping interpretation of
ATR-undefined maximum-excursion values, retaining the unaffected counts, chronology, lifecycle,
status, attribution, and finite-primary control findings, and making no strategy, emission, or
verdict change. It states that the exact-state hypothesis is not clean for the excluded maximum-
excursion path.

## Operator verdict

The binding operator verdict is recorded verbatim:

> “retain the current run; ATR-undefined excursion values are limited/invalid and must be excluded from all interpretations; make no implementation changes; perform no reruns/emissions.”

This verdict completes and approves **EXP-100** with the scoped exclusion above. It is an
experiment-level decision only. `CF-LIQSWP-001` remains `REGISTERED`; the operator did not promote,
retire, or close the family, and no checkpoint family decision is inferred.

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

- Experiment disposition: `EXP-100` complete and operator-approved with ATR-undefined exclusion.
- Candidate-family status: unchanged — `CF-LIQSWP-001` remains `REGISTERED`.
- Candidate slots consumed: 0.
- Counted TEST reads: 0; holdout sealed and untouched.
- `EXP-101`–`EXP-104` remain separate experiments with independent decisions.

## Artifacts

| Artifact | Path |
|---|---|
| Design | [design.md](design.md) |
| QA history | [qa-review.md](qa-review.md) |
| Analysis | [analysis.md](analysis.md) |
| Analysis code | [analysis_code/](analysis_code/) |
| Family estimand gate | [results/estimand_validation.json](results/estimand_validation.json) |
| Analysis results | [results/analysis/](results/analysis/) |
| ATR-undefined prevalence | [results/analysis/atr_undefined_prevalence.json](results/analysis/atr_undefined_prevalence.json) |
| Execution journal | [results/execution/full-journal.jsonl](results/execution/full-journal.jsonl) |
| Published cell gates | [results/execution/full/](results/execution/full/) |
| Strategy/runner code | [code/](code/) |
| Plots | None generated; tables are the primary evidence |
