# XENA lane — portfolio construction

**Status:** Binding live lane rules

XENA is the portfolio-construction lane. It generates candidate strategies once in the event-driven engine, composes candidate subsets chronologically in Python, and reports search, certification, and gate evidence for operator review. It is not a licence to search indefinitely, qualify candidates on their own outcomes, or treat a portfolio score as an economic verdict.

## 1. Responsibilities and boundary

- Every structurally complete registered model × parameter × instrument × domain combination is a candidate. Candidate-level performance gates are prohibited.
- Nautilus executes each candidate once under the catalog fence and emits the engine record.
- Python performs chronological portfolio composition, sizing under the registered rule, reconciliation, and analysis. It does not alter entry/exit decisions or invent account state.
- A candidate that depends on account state for its own signal logic cannot use the price-primary carve-out below.
- The operator authorizes the universe, search spend, TEST read, cost exception, and final disposition.

The registered object is the XENA run: universe manifest, code/config identity, catalog and fence, predeclared bands, search settings, candidate accounting, and any calibration or threshold pin. A later threshold change is a new registered run or a documented pre-execution amendment.

## 2. Pipeline

```text
1. Universe assembly ... manifest and one-time Nautilus candidate emissions
2. Candidate gate ...... structural contract and candidate inventory
3. Search .............. predeclared chronological TRAIN search and restarts
4. Certification ....... plateau, fold, attribution, sign, and stability reports
    [OPERATOR — reviews the evidence package and approves gate spend]
5. Final gate ........... one counted gross TEST walk-forward per authorized slot
    [OPERATOR — assigns the final disposition]
```

The candidate gate checks completeness and structural identity; it does not select a candidate on performance. Search and certification are TRAIN activities. The final gate is a TEST activity, is counted in the universe ledger, and is not used for post-outcome re-search.

## 3. Validity attestations

These are hard checks. A failure makes the affected emission or layer invalid (`VOID`); it is not evidence that the strategy has no value:

- **Fence:** all reads and emitted timestamps are inside the registered band and carry the pinned attestation.
- **Causality:** the signal uses only information available by the registered boundary, normally `t-1` for bar decisions.
- **Estimand reconciliation:** orders, fills, positions, marks, and derived returns reconcile to the registered estimand.
- **Non-stub output:** required files contain finite, non-degenerate observations.
- **No local accounting:** Python does not create an unrecorded account or P&L ledger.
- **Structural computability:** every candidate and subset has the required fields, finite sizing inputs, and declared exclusions.
- **Oracle determinism:** the same bitmask, segment, seed, and pinned inputs produce the same decision-relevant composition.
- **Future-destroy integrity:** deliberately destroying future-only information invalidates or materially destroys the affected edge. An edge that survives only because leakage was not tested is not cleared.

## 4. Value report layers

Value and quality reads are report layers, not automatic gates. Every layer contains `observed`, `ideal`, and `interpretation` fields or their equivalent and does not machine-drop a candidate because a value is inconvenient.

The evidence package may include:

- sample-size context: counts, per-leg volatility, and any design minimum noted as context only;
- cadence coverage and missingness;
- search score and restart dispersion;
- purged fold stability and worst/median ranking;
- stage-2 bounds for every declared subset and per-cell result;
- within-sample attribution and derangement diagnostics;
- sign battery with effect, one-sided probability, confidence interval, and count;
- PSR beside every mean-trade or leg-bps read on the same series;
- gross walk-forward results, decay windows, rank correlation, and seed spread;
- evaluation counts and distinct-subset counts.

Interpretation bands such as `SUPPORTED`, `WASH`, `CONTRADICTED`, `SUGGESTIVE`, or `STRONG` are operator-only labels. They are never machine-assigned and never gate a run. No layer may use MDE, power, detection floors, powered/unpowered labels, or an outcome-derived threshold.

The sign battery is a robustness read, not a pass/fail test. Its seed count, effect, probability, interval, and interpretation are reported together. A small or wide result is not hidden, and a large count is not proof of adequacy.

## 5. Price-primary carve-out

### Engine-side candidate emission

All signal logic runs in Nautilus once per candidate. The emission includes the bar grid and marks plus the per-leg position ledger. Every leg must carry a finite `SlPrice` field. The price may be a synthetic sizing-only stop; a live stop order is not required. The sizing denominator is `|EntryFill - SlPrice|`. Missing or non-finite `SlPrice` invalidates the candidate emission.

The candidate does not size itself and does not see portfolio account state. A signal may not change because another candidate was selected, because cash was consumed, or because a portfolio-level stop fired.

### Python oracle

`xen.xena.oracle` performs chronological composition only. For each time step it applies the registered portfolio multiplier and weights, for example `R_i = r · FM · w_i`, applies the global `R_max` admission rule, logs rejected signals as first-class events, censors at segment ends, and raises on reconciliation failure. It must be deterministic for the registered bitmask, segment, and seed.

The oracle uses gross accounting by default. It may not alter an entry or exit decision, introduce a hidden cost, or transform a portfolio composition result into a tradability claim.

## 6. Search, certification, and TEST gate

- Search uses only the registered TRAIN search band and predeclared restart/perturbation settings.
- Ranking uses disjoint chronological, purged TRAIN folds. The search band and ranking folds do not overlap.
- Certification examines every declared subset and cell, not only the top candidate.
- The final gate uses a fresh TEST walk-forward and gross accounting once per authorized slot.
- The global HOLDOUT remains sealed and is refused by the access layer.
- Gate thresholds, objective definitions, segment layouts, and seed budgets are pinned before the corresponding read.
- A gate read is a selection-machinery event. A gate result is not an economic, tradability, or deployability verdict.

No historical frozen registry is binding for the live lane. If a calibrated threshold or other calibrated value is needed, the run design must name its calibration population, method, result, and hash before execution. It must not re-derive the value after looking at the live universe or gate outcome.

## 7. Gate ledger

The universe gate ledger is append-only and records every final-gate attempt, pass or fail, with the run identity, subset identity, TEST band, threshold pin, and evidence hashes.

- There are at most two final-gate slots per universe unless the operator records a new scope with a new data attestation.
- A slot is spent on both a pass and a fail.
- An exact repeat of a failed subset is refused unless the operator supplies a signed new-data attestation.
- Similarity to prior failed subsets is reported for operator review; only exact identity is an automatic refusal.
- No threshold revision, baseline change, or re-search is permitted after a gate outcome.
- `evaluation_count` (all oracle calls) and `distinct_subsets` travel with every reported number.

A failed gate is a failed selection attempt, not a machine economic verdict. The operator records what the failure means for the registered question.

## 8. Temporal mapping

The default global fence is:

```text
analysis_start  = 2021-06-29T06:53:00Z
train_end       = 2023-12-18T00:00:00Z
holdout_start   = 2025-01-08T00:00:00Z
data_end        = 2026-07-14T23:59:00Z
```

TRAIN is partitioned into a search band and disjoint chronological ranking folds. TEST is reserved for the counted final gate. The lifetime HOLDOUT is sealed. A universe design may choose narrower boundaries inside these values, but it must pin them before search and preserve them through the gate.

## 9. Cost and claim boundary

Every XENA selection, certification, and final gate is gross and cost-free by default:

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
  lifting: only an explicit operator authorization may introduce a cost model
    for a scoped experiment; that authorization and its schedule are recorded
    in the experiment design before execution.
```

`money_per_unit` is a sizing or capital-unit factor, not a cost. A nonzero cost model requires a pre-execution operator authorization that names the schedule, scope, and changed estimand. It cannot be introduced as a post-hoc interpretation.

## 10. Neutral analysis and operator handoff

The analyst reports observed values separately from inference, shows supportive and adverse evidence symmetrically, names every population and exclusion, and reports counts as context. Each mean-trade or leg-bps value carries `psr` and `psr_n` from the same predeclared per-trade series; PSR is never a gate.

For observed Sharpe `SR_hat`, reference `SR*`, sample size `n`, empirical skewness `gamma_3`, empirical kurtosis `gamma_4`, and standard-normal CDF `Phi`, the paired PSR is:

```text
PSR(SR*) = Phi((SR_hat - SR*) * sqrt(n - 1)
               / sqrt(1 - gamma_3 * SR_hat
                       + ((gamma_4 - 1) / 4) * SR_hat^2))
```

It uses the same predeclared per-trade series and population as the reported Sharpe, defaults to `SR* = 0`, and emits `NaN` with an explicit reason when `n < 2` or the required moments/denominator are invalid. `psr` and `psr_n` sit beside every mean-trade or leg-bps read.

The handoff includes the registered question, actual run identity, fence, engine, causal rule, candidate/subset accounting, effect and uncertainty, validity findings, cost disclosure, unresolved limitations, and the requested operator disposition. No machine field, including `passed`, can substitute for that handoff.
