# Programme governance

**Status:** Binding live rules

This document governs every current Xen research lane and run. It is written to stand alone; a historical result, experiment plan, or temporary implementation note cannot weaken these rules.

## 1. Research boundary

The default programme cost model is gross and cost-free:

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

This boundary applies to every money-bearing report, table, chart, and label. A gross research result is not trading performance, and no result may be described as deployable or tradable by implication.

The programme does not use research powering. It does not derive or publish MDEs, detection floors, power curves, powered machine labels, or minimum-effect gates. A run may report its observed count, uncertainty, and direct comparison to a predeclared baseline; those are context and evidence, not automatic acceptance rules.

## 2. Authority and operator control

- The live reference set is the governing specification. Historical material is explanatory context only.
- Registration records intent. It does not authorize execution, consume a gate, or establish a result.
- The operator authorizes execution, any TEST read, any cost-model exception, and the final disposition.
- A machine field named `passed`, `accepted`, or similar is a workflow or reconciliation field unless the report explicitly defines it otherwise. It is never an economic verdict by itself.
- Family status is not inferred automatically from a run. The operator records `WORTH_EXPLORING`, `NOT_WORTH`, or `INCONCLUSIVE` with a brief evidence-based reason.
- Gate ledgers are append-only. Counts are not reset by a new document, code refactor, or renamed experiment.
- Any amendment after registration is recorded with its reason, affected scope, and whether the run must be restarted.

## 3. Execution and data boundary

- Price-primary experiments run through the event-driven Nautilus engine. Strategies observe engine events and emit engine-native fills, orders, positions, and marks.
- Python may adjudicate emitted artifacts, compose candidates chronologically, and produce reports. It may not replace the engine with a vectorized price backtest or perform hidden local accounting.
- Every data read is bounded by the pinned chronological fence. TRAIN and TEST are explicit bands; the lifetime HOLDOUT is sealed and refused by sanctioned access code.
- Causality is evaluated at the time a value becomes known. A feature used at decision time `t` must be available by the predeclared causal boundary, normally the close of `t-1` for bar decisions.
- The event stream, fills, orders, positions ledger, bar marks, instrument map, fence attestation, run metadata, and deterministic event log are the minimum emission identity for a price-primary run.
- A run with a missing, stubbed, non-deterministic, non-reconciled, or non-causal required artifact is invalid. It is not evidence for or against the research idea.

## 4. Validity before value

The following checks are hard validity checks:

1. **Fence:** every read and emission is inside the authorized band and carries the pinned fence attestation.
2. **Causality:** feature timestamps, decision timestamps, and fills obey the registered lag rule.
3. **Reconciliation:** orders, fills, positions, and marks reconcile without hidden local P&L or unexplained rows.
4. **Non-stub and non-degenerate:** required artifacts contain real, finite observations with nonzero activity where the design requires it.
5. **Determinism:** repeated execution under the same pinned inputs produces the same decision-relevant records, subject to the declared platform pin.
6. **Future-destroy test:** deliberately invalidating future-only information must invalidate the affected observation or materially destroy its result. A result that survives only because leakage was not tested is not cleared.
7. **Contract completeness:** metadata names the run configuration, catalog identity, engine version, platform, instrument map, and output counts.

Validity findings are reported separately from value findings. A valid but weak result is evidence against the mechanism; an invalid result is `VOID`.

## 5. Evidence and neutrality

Every lane applies these rules directly:

- **N1 — no verdict from a machine:** code emits observations and diagnostics; the operator assigns the disposition.
- **N2 — observed versus inferred:** counts, values, and test outcomes are labelled as observed; interpretations and mechanism claims are labelled as inference.
- **N3 — counts are context:** sample size, trial counts, and coverage are always reported. They do not hide a result, create a gate, or prove adequacy.
- **N4 — direct comparator:** the primary comparison is against the predeclared baseline on the same population and decision rule.
- **N5 — population clarity:** TRAIN, TEST, HOLDOUT, folds, candidates, and strata are named separately. Aggregation cannot erase a population boundary.
- **N6 — informative controls:** controls expose mechanics, leakage, implementation effects, and null behaviour. A control is not silently treated as a success threshold.
- **N6b — future-destroy validity:** the future-destroy result is a hard integrity check only. The default bite is `integrity_bite = INTEGRITY_Z * bootstrap_SE` with `INTEGRITY_Z = 2.8`, using the same estimator as the reported effect.
- **N7 — symmetric evidence:** supportive, null, adverse, and ambiguous observations are retained and reported with the same prominence.
- **N8 — fresh analysis:** the analyst who adjudicates the raw emission must not be the implementation author for that run.
- **N9 — cost disclosure:** every money-bearing output carries the exact zero-cost disclosure above, or the explicitly authorized scoped exception.
- **N10 — completeness:** a report names its inputs, population, estimator, comparator, uncertainty method, exclusions, validity findings, and unresolved limitations.
- **N11 — operator labels:** disposition labels are human decisions recorded after the evidence review, never model output.

Reported effects include their sign, units, population, observation count, and uncertainty. When Sharpe-like evidence is used, the report also includes the predeclared per-trade series and its PSR context; neither is converted into a machine verdict.

PSR uses the same series as the reported Sharpe. With observed `SR_hat`, reference `SR*`, sample size `n`, empirical skewness `gamma_3`, empirical kurtosis `gamma_4`, and standard-normal CDF `Phi`:

```text
PSR(SR*) = Phi((SR_hat - SR*) * sqrt(n - 1)
               / sqrt(1 - gamma_3 * SR_hat
                       + ((gamma_4 - 1) / 4) * SR_hat^2))
```

The default is nonannualized per trade with `SR* = 0`; `psr` and `psr_n` are adjacent to every mean-bps read. Invalid `n`, moments, or denominator produce `NaN` with an explicit reason.

## 6. Lane responsibilities

| Lane | Role | Permitted output |
|---|---|---|
| SPDR | Lightweight screening of a mechanism or rule | Matched, causal, TRAIN-only evidence and a routing disposition |
| XENA | Portfolio construction and candidate-composition research | Chronological candidate portfolio evidence, certification diagnostics, and operator-gated TEST evidence |
| Full experiment | Confirmatory price-primary research | A complete registered design, valid engine emission, referee analysis, and operator disposition |

SPDR is not a substitute for a full experiment. XENA is not permission to search indefinitely or to treat a portfolio score as a verdict. A lane may route follow-up work, but only the operator can authorize that follow-up.

## 7. Minimum operator handoff

Before accepting a result for review, the handoff must state:

- what was registered and what actually ran;
- the data catalog, band, fence, engine, platform, and code identity;
- the causal rule and the estimand;
- observation counts, exclusions, comparator, effect, uncertainty, and PSR context where applicable;
- every validity failure, unresolved limitation, and cost disclosure;
- the requested operator disposition and the evidence supporting it.

The final handoff is a record of human judgment over complete evidence. It is not a machine-generated claim of profitability, tradability, deployability, or statistical proof.
