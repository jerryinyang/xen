# XENA run design template

Copy this file to `python/experiments/XENA-<NNN>/design.md` and complete every field before execution. Blank fields are design failures, not invitations to infer a value from code or an earlier run.

## 0. Registration

| Field | Value |
|---|---|
| Run ID | `XENA-<NNN>` |
| Status | `DESIGN` |
| Question | `<one mechanism-first question>` |
| Operator | `<name / approval record>` |
| Implementation identity | `<commit or immutable code/config identity>` |
| Engine | `Nautilus 1.230.0` unless a new pin is explicitly approved |
| Platform pin | `<platform and runtime>` |
| Planned run destination | `<operator-approved run directory, created for this run>` |

The registered object is this run's universe manifest, candidate inventory, code/config identity, fence, bands, search settings, calibration pins, and gate ledger identity. A post-outcome change creates an amendment or a new run.

## 1. Research boundary

This is a price-primary, event-driven research run. Nautilus emits every candidate once. Python may compose candidates chronologically and analyse the emission, but may not replace engine execution, invent fills, or use hidden account state.

The default cost model is:

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
    in this design before execution.
```

If a nonzero cost model is authorized, complete the exception before running:

| Field | Value |
|---|---|
| Cost authorization | `<operator record>` |
| Cost schedule | `<spread / commission / swap / funding inputs>` |
| Scope | `<layers and populations affected>` |
| Changed estimand | `<exact definition>` |
| Reproducibility identity | `<hash or immutable config>` |

Absent a completed exception, all values are gross and cost-free. `money_per_unit` is a sizing/capital-unit factor, not a cost.

## 2. Estimand and causal rule

| Field | Value |
|---|---|
| Estimand | `<primary effect, units, and sign convention>` |
| Direct baseline | `<predeclared baseline on the same population>` |
| Decision timestamp | `<when the signal is decided>` |
| Feature availability | `<all fields available by ...>` |
| Default lag check | `t-1` confirmed bar unless explicitly justified |
| Entry/exit convention | `<engine order and fill convention>` |
| Outcome unit | `<per trade / per bar / portfolio segment>` |
| Uncertainty | `<method and dependence block or trade-series rule>` |
| Reference Sharpe | `SR* = 0` unless another value is registered |

Overlapping H-bar outcomes use a block bootstrap with block length at least H, or a declared non-overlapping/greedy trade series. A library default is not sufficient.

When a Sharpe-like statistic is reported, compute PSR on the same predeclared per-trade series:

```text
PSR(SR*) = Phi((SR_hat - SR*) * sqrt(n - 1)
               / sqrt(1 - gamma_3 * SR_hat
                       + ((gamma_4 - 1) / 4) * SR_hat^2))
```

Use `SR* = 0` unless another reference is registered. Emit `psr` and `psr_n` beside every mean-trade or leg-bps read; emit `NaN` with a reason when `n < 2` or required moments/denominator are invalid.

## 3. Data and fence

| Field | Value |
|---|---|
| Primary catalog | `data/catalog/` |
| Signed diagnostic catalog | `<none or data/catalog_sigbar/train/>` |
| Compatibility catalog | `<none or data/catalog_ctrader/>` |
| Universe manifest | `<immutable manifest identity>` |
| Catalog identity | `<path/version/hash>` |
| Analysis start | `2021-06-29T06:53:00Z` or narrower predeclared value |
| TRAIN end | `2023-12-18T00:00:00Z` or narrower predeclared value |
| TEST end / HOLDOUT start | `2025-01-08T00:00:00Z` |
| Data end | `2026-07-14T23:59:00Z` or earlier |
| Fence manifest SHA-256 | `35d3375ec5ec18b3c6e4c5eec814ade4d492bd60e3fb694fed19e16bc2c00448` |

The sanctioned data-read bands are TRAIN and TEST. HOLDOUT is sealed and must not be queried. Every read uses the fence wrapper and every emission carries a pinned fence attestation.

## 4. Universe and candidate inventory

### Universe definition

```text
universe_id: <stable name>
source: <catalog and selection rule>
instruments: <immutable list or manifest path>
instrument_id_convention: {SYMBOL}-LINEAR.BYBIT
inclusion: <rule>
exclusion: <rule and recorded reason>
```

### Candidate definition

| Field | Value |
|---|---|
| Candidate axes | `<model × parameters × instrument × domain>` |
| Candidate count | `<count before execution>` |
| Candidate identity | `<stable hash rule>` |
| Signal inputs | `<fields and timestamps>` |
| Account-state dependency | `NO` unless a different lane is approved |
| `SlPrice` | finite field on every leg; synthetic sizing-only stop is allowed |
| Sizing denominator | `abs(EntryFill - SlPrice)` |

Every structurally complete candidate enters the engine run. There are no candidate-level performance qualification gates. Missing or non-finite required fields invalidate the candidate emission.

## 5. Portfolio oracle

```text
portfolio_multiplier FM(t): <definition>
candidate weights w_i: <definition and constraints>
per-candidate return r_i: <definition>
portfolio return R_i: r_i * FM(t) * w_i
global R_max admission: <definition>
rejected-signal event: <required fields>
segment-end censoring: <rule>
reconciliation invariant: <equation and failure action>
determinism identity: (bitmask, segment, seed) -> <record>
```

Python performs only chronological composition and the registered gross accounting. It cannot change a candidate's entry or exit, create a local account, or silently introduce costs.

## 6. TRAIN search and certification

| Field | Value |
|---|---|
| Search band | `<contiguous TRAIN interval>` |
| Ranking folds | `<disjoint chronological purged intervals>` |
| Search restarts | `<predeclared count and seeds>` |
| Objective | `<definition and units>` |
| Plateau rule | `<predeclared diagnostic, not an economic verdict>` |
| Stage-2 bounds | `<all subsets and per-cell rule>` |
| Attribution control | `<derangement / null / other>` |
| Sign battery | `<seed count, effect, one-sided probability, CI, n>` |
| PSR series | `<same per-trade series as reported Sharpe>` |
| Evaluation accounting | `<evaluation_count and distinct_subsets rule>` |

Search and certification emit evidence layers. They do not machine-assign `SUPPORTED`, `WASH`, `CONTRADICTED`, `SUGGESTIVE`, `STRONG`, or any other economic label. They do not use MDEs, power curves, detection floors, or powered/unpowered fields.

## 7. TEST gate and ledger

| Field | Value |
|---|---|
| Gate population | `<fresh TEST interval>` |
| Gate protocol | `<single gross walk-forward definition>` |
| Gate threshold | `<predeclared threshold and identity>` |
| Gate budget | `maximum two final-gate slots per universe unless newly authorized` |
| Gate ledger | `<append-only ledger destination>` |
| Exact failed-subset retry | `refused unless operator-signed new-data attestation exists` |
| Operator approval | `<record before TEST read>` |
| Machine `passed` meaning | selection-machinery/reconciliation field only; never economic verdict |

Both passes and failures consume a gate slot. No threshold, baseline, population, or search setting changes after a gate outcome. Similarity to a previous failed subset is reported; exact identity is refused by default.

## 8. Validity checklist

Mark each item only after evidence exists:

- [ ] Fence reads and emission timestamps are inside the registered band.
- [ ] Causal feature lag is asserted at the decision boundary.
- [ ] Orders, fills, positions, marks, and estimand reconcile.
- [ ] Required artifacts are non-stub, finite, and non-degenerate.
- [ ] No local Python account or P&L replaces engine state.
- [ ] Every candidate has a finite `SlPrice` and valid sizing denominator.
- [ ] Candidate and oracle composition are deterministic under the pin.
- [ ] Future-destroy invalidation materially destroys the affected edge or marks it `VOID`.
- [ ] The emission includes metadata, instrument map, fence attestation, output counts, and event-log hash.
- [ ] Every mean-trade or leg-bps value carries adjacent `psr` and `psr_n` from the same series.
- [ ] The cost disclosure is present in every money-bearing output.

A failed hard check invalidates the observation. It is not negative evidence about the mechanism.

## 9. Neutral report and operator handoff

The report must contain observed values separately from inferred explanations, all populations and exclusions, the direct baseline comparison, effect and uncertainty in stated units, counts, sign distribution, PSR context, controls, validity findings, cost disclosure, and unresolved limitations.

The operator records exactly one disposition for the registered question:

```text
WORTH_EXPLORING | NOT_WORTH | INCONCLUSIVE
```

The disposition reason is written after the evidence review. Registration, a machine `passed` field, a gate score, a PSR, or a count does not assign it.

## 10. Amendments

| Date | Change | Reason | Affected population | Restart required? | Operator record |
|---|---|---|---|---|---|
| `<UTC>` | `<change>` | `<reason>` | `<scope>` | `<yes/no>` | `<record>` |

An amendment cannot make a post-outcome change look predeclared. If the estimand, population, causal rule, comparator, cost model, or gate protocol changes, create a new run unless the operator explicitly records why the original evidence remains valid.
