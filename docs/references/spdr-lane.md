# SPDR lane — screening and exploration

**Status:** Binding live lane rules

SPDR (`SPDR-###`) is a lightweight, TRAIN-only screening lane. It answers whether a registered mechanism or rule produces a measurable, signal-conditional change worth investigating in a full price-primary experiment. It does not make a tradability, deployability, profitability, or family-status claim.

## 1. Purpose and boundary

SPDR may scan a predeclared grid of components, devices, combinations, instruments, and holds. It reports availability, lift, distributional change, and diagnostics against matched controls. Its output is evidence and an operator-routing disposition.

The following boundary is hard:

| Rule | Requirement |
|---|---|
| Population | TRAIN only; use the first 70% of the first 70% of the analysis range unless the design predeclares a narrower window. No TEST or lifetime-HOLDOUT read. |
| Causality | A decision at bar `t` uses only information available by the registered boundary, normally confirmed bars through `t-1`. Open-to-open outcomes and limit simulations must resolve causally on one-minute data. |
| Comparator | Treatment is compared with a matched baseline on the same eligible population and timestamps. Random controls use a regenerated battery of at least 25 seeds and report the rank/percentile read. |
| Reporting | Every instrument × domain pair × filter variant × hold stratum is visible. Pooled summaries are disclosure only. Multiplicity and cell counts are stated. |
| Accounting | No local P&L or account-state primitive is used to manufacture a verdict. Screen metrics are availability/lift measures and distributional diagnostics. |
| Uncertainty | Overlapping H-bar outcomes use a dependence-matched block bootstrap with block length at least H, or a non-overlapping/greedy trade series. A library default is not a design choice. |
| Claim | No SPDR output is net performance, tradability, deployability, or a family verdict. |

Everything outside this boundary is a design choice that must be predeclared. A change to the boundary requires a new full experiment or an operator-recorded amendment before execution.

## 2. Dispositions

SPDR may report one of these operator-facing routing labels per registered series:

| Label | Meaning |
|---|---|
| `WORTH_EXPLORING` | A measurable change relative to the matched baseline merits a full price-primary investigation. |
| `NOT_WORTH` | The registered screen provides no useful change relative to its matched baseline for the stated question. |
| `INCONCLUSIVE` | Counts, coverage, uncertainty, or implementation limits leave the question unresolved. This is descriptive, not a negative finding and not a row-hiding rule. |

The labels are assigned by the operator after reviewing the complete evidence. `WORTH_EXPLORING` is a routing signal, never a verdict. A multi-leg series receives one disposition after its final leg; individual legs remain characterisation evidence.

## 3. Characterisation contract

- The grid, strata, devices, holds, controls, and outcome units are predeclared.
- Every stratum names its exact direct comparison and emits its own estimate and uncertainty.
- All strata are reported. Winner-only pruning and experiment-wide supported/refuted labels are prohibited.
- Individual component × device strata remain visible before any combination is interpreted.
- Outcomes are device-native; one universal score must not replace the question each device actually asks.
- Every adaptive or conditioned arm carries the same device unconditioned on the same eligible population as its direct comparator.
- Event count and effective count are sample-size metadata. They remain visible next to every row and do not create positive/negative labels, prune rows, or gate a companion experiment.
- The analyst reports magnitudes and uncertainty rather than qualifier-shaped conclusions such as “wash”, “at chance”, or “no systematic effect”. A pooled line may orient the reader, but the per-stratum table is the evidence.
- The base strategy's own distribution is characterised separately from the conditional effect. A failing base does not prove that the filter is ineffective, and a distributional shift on a weak base is still reported as a measured shift.

## 4. Neutral evidence contract

SPDR reports the following directly:

- code emits observations and diagnostics; the operator decides;
- observed values and inferred explanations are labelled separately;
- counts are shown as context, never as an adequacy or success gate;
- the direct predeclared comparator and named population are visible;
- supportive, null, adverse, and ambiguous evidence is retained symmetrically;
- validity failures are separated from value findings; invalid observations are `VOID`, not negative evidence;
- the analyst works from the raw screen output in a fresh context and records unresolved limitations;
- every money-bearing table carries the zero-cost disclosure below;
- the handoff is complete enough to reproduce the population, estimator, comparator, uncertainty, exclusions, and validity checks;
- the final label is operator-only.

When a Sharpe-like statistic is reported, the same predeclared per-trade series carries adjacent `psr` and `psr_n` fields. PSR is nonannualized per trade by default, uses `SR* = 0` unless registered otherwise, and emits `NaN` with an explicit reason when `n < 2`, required moments are non-finite, or the denominator is invalid. It is context, not a gate.

For observed Sharpe `SR_hat`, reference `SR*`, sample size `n`, empirical skewness `gamma_3`, empirical kurtosis `gamma_4`, and standard-normal CDF `Phi`:

```text
PSR(SR*) = Phi((SR_hat - SR*) * sqrt(n - 1)
               / sqrt(1 - gamma_3 * SR_hat
                       + ((gamma_4 - 1) / 4) * SR_hat^2))
```

The report uses the same series and population as the reported Sharpe, and places `psr` beside the mean-bps read with `psr_n`.

The default zero-cost disclosure is:

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

SPDR never uses MDEs, power curves, detection floors, powered labels, minimum-effect gates, or post-outcome thresholds. It may report effect estimates, uncertainty, sign distributions, observed counts, and the direct baseline comparison.

## 5. Lean stages

```text
1. Design ........ mechanism, grid, controls, units, and screen boundary → design.md
2. Self-check .... code asserts TRAIN fence, causal lag, and seed regeneration
3. Screen ........ registered evaluator on TRAIN → results/ and plots/
4. Summary ....... neutral quantification → screen.md
5. Fresh analysis  independent raw-output review → analysis.md
6. Operator ...... disposition and next action
```

The fresh analysis is mandatory. It covers every declared facet, effect magnitude, uncertainty, distribution shape, dose/hold response, and heterogeneity. It resolves open data questions in its own analysis code and does not turn the screen summary into a machine verdict.

Stage 2 is a code-asserted self-check, not a replacement for a full experiment's fresh-context compliance review. The screen must assert its TRAIN-only fence, causal lag, and random-control regeneration before emitting a result.

## 6. Artifacts and identity

An SPDR run is created under:

```text
python/experiments/SPDR-###/
├── design.md
├── screen_code/
├── analysis_code/
├── results/
├── plots/
├── screen.md
└── analysis.md
```

IDs are zero-padded and never reused. The design names the data catalog, code/config identity, population, bands, comparator, estimator, units, uncertainty method, multiplicity treatment, and all exclusions. The screen does not use a price-emission estimand gate to assign an economic result; its integrity substitute is the code-asserted fence, lag, and control checks above.

## 7. Graduation

`WORTH_EXPLORING` routes the mechanism to a full price-primary experiment with a new registered design, fresh-context compliance review, event-driven engine execution, neutral raw-data analysis, and operator disposition. The full experiment must re-establish the estimand, causal convention, cost boundary, and TEST authorization; an SPDR screen does not carry a hidden performance claim forward.

If a screen effect is later converted into bps or money, the graduation design must state the normalizer object exactly: indicator, period, timeframe, and lag. It must measure the TRAIN conversion value from the target data and show the resulting units. No conversion may be asserted from memory, and no cost floor gates the SPDR disposition.
