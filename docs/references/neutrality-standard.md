# Neutrality and evidence standard

**Status:** Binding live rules

This is the complete operating standard for neutral reporting. It applies to every lane, run, result table, chart, and operator handoff. It does not assign the final disposition; it defines what the evidence must contain and what the machine is forbidden to claim.

## 1. Core neutrality rules

### N1 — no machine verdict

Code may emit observations, diagnostics, integrity findings, and routing metadata. It must not emit an economic verdict such as “worth pursuing”, “not worth pursuing”, “profitable”, or “failed” as the final decision. The operator assigns the disposition after reviewing the complete evidence.

### N2 — observed versus inferred

Observed values are labelled as observed: counts, timestamps, prices, fills, returns, deltas, missingness, and test outcomes. Mechanism explanations, generalisation claims, and recommendations are labelled as inference. A computed statistic is not evidence that its proposed mechanism is true.

### N3 — counts are context, not a gate

Reports show the number of observations, trades, candidates, seeds, folds, strata, exclusions, and attempted comparisons relevant to the estimand. Counts cannot be hidden, used to suppress an inconvenient result, or converted into an automatic adequacy or success label.

### N4 — direct predeclared comparison

The primary comparison is against the design's predeclared baseline on the same population, timestamps, execution convention, and estimator. Retrospective baselines, selected windows, and post-outcome comparator changes are secondary context only.

### N5 — population clarity

Every number is attached to a named population: TRAIN, TEST, HOLDOUT, fold, seed, candidate, symbol, stratum, or aggregate. Aggregation must not erase population membership. A TEST result cannot be used to tune a TRAIN decision after the fact.

### N6 — controls are informative

Controls are selected to reveal leakage, implementation effects, null behaviour, and mechanism dependence. A control is reported as evidence about that question; it is not silently made into a pass threshold.

### N6b — future-destroy is a validity check

The future-destroy test deliberately removes or corrupts future-only information. It is a hard integrity check, not an economic score. The default integrity bite is:

```text
integrity_bite = INTEGRITY_Z * bootstrap_SE
INTEGRITY_Z = 2.8
```

The same estimator and population used for the reported effect must be used for the bootstrap standard error. If the invalidation does not materially destroy the affected result, or if the check cannot run, the affected observation is invalid rather than negative evidence.

### N7 — symmetric evidence

Supportive, null, adverse, and ambiguous results receive the same reporting prominence. The analyst must show the evidence that would weaken the mechanism as well as the evidence that appears to support it.

### N8 — fresh analyst

The person or process that adjudicates raw emissions must not be the implementation author for that run. The analyst works from the emission and registered design, not from an implementation narrative that selectively omits inconvenient output.

### N9 — zero-cost disclosure

Every money-bearing document carries this exact disclosure unless a scoped nonzero cost model has been explicitly authorized and recorded before execution:

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
  lifting: only an explicit operator authorization may introduce a cost model for
    a scoped experiment; the authorization is recorded in that experiment's design.md.
```

The disclosure is a boundary, not a disclaimer to be removed from a favourable result. A nonzero schedule must state its inputs, timing, scope, and effect on the estimand before the run executes.

### N10 — complete handoff

The report names its source data, code/config identity, population, estimator, comparator, uncertainty method, exclusions, validity findings, cost model, and unresolved limitations. Missing metadata is a completeness failure, not an invitation to infer the missing fact.

### N11 — operator labels

`WORTH_EXPLORING`, `NOT_WORTH`, and `INCONCLUSIVE` are operator labels. They are recorded after the evidence review and include a short reason. No threshold, score, p-value, PSR, or sample count assigns them automatically.

## 2. Probabilistic Sharpe ratio

When a Sharpe ratio is reported, the probabilistic Sharpe ratio (PSR) is computed on the same predeclared per-trade return series and population. It is a context statistic, not a gate.

For an observed nonannualized Sharpe estimate \(\widehat{SR}\), reference Sharpe \(SR^*\), sample size \(n\), empirical skewness \(\gamma_3\), empirical kurtosis \(\gamma_4\), and standard normal CDF \(\Phi\):

\[
PSR(SR^*) = \Phi\left(
\frac{(\widehat{SR} - SR^*)\sqrt{n-1}}
{\sqrt{1 - \gamma_3\widehat{SR} + \frac{\gamma_4-1}{4}\widehat{SR}^{2}}}
\right)
\]

The implementation rules are:

- use the same per-trade series as the reported Sharpe ratio;
- use the population and exclusions declared by the estimand;
- use empirical skewness and kurtosis from that series;
- use a nonannualized per-trade Sharpe by default;
- use `SR* = 0` by default unless the design predeclares another reference;
- report `psr` and `psr_n` adjacent to every mean-bps or Sharpe-bearing result;
- if `n < 2`, a required moment is non-finite, or the denominator is invalid, emit `psr = NaN` and state the reason in `psr_n` or the accompanying metadata;
- never translate PSR into “significant”, “powered”, “safe”, “profitable”, or another machine verdict.

The report must state whether the series is per-trade, per-bar, or another unit. A change of unit changes the estimand and requires a new predeclared analysis.

## 3. Powering strip

The following are prohibited as research acceptance machinery:

- minimum detectable effect or MDE claims;
- power curves, powered/unpowered labels, or post-hoc power calculations;
- detection floors or minimum-effect thresholds created from the observed data;
- significance cutoffs used as a binary economic gate;
- sample-size rules that hide, discard, or downgrade an observed result;
- post-outcome selection of the baseline, population, uncertainty method, or metric;
- language that presents a gross result as net, cost-complete, tradable, deployable, or investment performance.

The following are required and permitted:

- observed counts and coverage, including exclusions;
- the direct predeclared baseline comparison;
- effect estimates with uncertainty and units;
- the full sign distribution and relevant diagnostics;
- PSR with its exact series and `psr_n` context where Sharpe-like evidence is used;
- an explicit statement of what the data cannot establish.

## 4. Validity and value

Validity checks answer whether the observation can be trusted as an execution of the registered design: fence, causal lag, reconciliation, non-stub output, determinism, future-destroy integrity, and metadata completeness. A failed validity check produces `VOID` for the affected observation.

Value analysis answers what a valid observation says about the mechanism: effect direction, size, uncertainty, controls, strata, and limitations. Value analysis never repairs a validity failure, and a valid null or adverse result remains evidence.

## 5. Minimum neutral report

Before the operator assigns a disposition, the report contains:

1. the registered question and estimand;
2. the actual population, dates, band, instruments, and exclusions;
3. the causal and execution convention;
4. the direct comparator and estimator;
5. counts and missingness;
6. effect estimates, units, uncertainty, and sign distribution;
7. PSR and `psr_n` where applicable;
8. controls and future-destroy integrity findings;
9. the exact cost disclosure;
10. unresolved limitations and the proposed operator-only disposition.

The analyst must show both what the data support and what they do not support. The final label is a governance action, not a statistical conclusion.
