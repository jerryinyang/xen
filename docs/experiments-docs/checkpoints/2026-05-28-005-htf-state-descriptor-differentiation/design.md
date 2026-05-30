# Phase 005 Design: Higher-Timeframe Market-State Descriptor Differentiation

**Phase:** 005 - Higher-Timeframe Market-State Descriptor Differentiation
**Date:** 2026-05-28
**Status:** Active
**Predecessor:** 2026-05-26-004-ustec-breaker-ifvg-selectivity

## Decision Status

Phases 003–004 closed the ICT-as-alpha thesis with no candidate manifest. Phases 001–002 closed the event-chart-as-alpha thesis. Both major theses the programme has pursued are now closed. The Phase 004 retrospective directs that Phase 005 start from a genuinely new, falsifiable, single-hypothesis direction with its own design — not an ICT or event-chart continuation.

Phase 005 takes that direction: it tests whether a **simple, predeclared market-state descriptor**, evaluated on `1h`/`4h`/contingent `1d` real-price bars, differentiates executable forward-return behavior. This reframes prior chart-type tools (Heiken Ashi, Renko) and structural levels away from being *signal generators* — which failed — toward being *state descriptors* that condition a real-price trade decision. It also brings one concrete, externally sourced, fixed-parameter indicator (Market Bias / CEREBR) into the same falsification framework.

This design supersedes the Phase 005 planning drafts (`docs/planning/phase-005-thesis-planning-draft.md`, `docs/planning/phase_005_discussion.md`) and the brainstorming output (`_bmad-output/brainstorming/brainstorming-session-2026-05-28-154455.md`). Those documents produced the candidate set; this document locks the search space, the primary edge metric, the gates, and the execution order.

## Phase Thesis

> On `1h`, `4h`, and contingent `1d` real-price bars, does a simple predeclared market-state descriptor differentiate executable direction-adjusted forward return relative to its own neutral baseline state **and** a matched simple control, replicating across train and test on at least two distinct instruments?

This is a single, falsifiable thesis. The candidate descriptors below are predeclared variations of *the same hypothesis* (a state descriptor carries forward-return information), not independent hypotheses. The phase exists to either produce one defensible state descriptor that earns a future holdout-preserving validation, or to close the state-descriptor thesis with a clean, evidence-backed no-go.

Phase 005 is an **edge-discovery gate**, not a final profitability claim. A return-test pass proves only control-adjusted state differentiation on the analysis set. A descriptor becomes an actionable trading-edge candidate only after EXP-038-style robustness checks show that the effect survives temporal segmentation, execution delay, proxy costs, opportunity cadence, and concentration stress without depending on a single instrument or segment.

The preferred outcome is not a positive result. The preferred outcome is a defensible decision.

## Evidence Inherited From Prior Phases

Phase 005 inherits only completed, audited findings. The directly relevant ones:

- **HA smooths but does not signal (EXP-006, EXP-009).** Heiken Ashi compresses volatility ~25% and cuts 15-minute direction-change count to ~48–49% of time bars, but standalone HA direction changes improved log FE/AE on 0/4 instruments. *Implication:* HA is a state descriptor, not an entry signal — which is exactly the reframe Phase 005 tests. The Market Bias candidate is a double-smoothed HA-derived oscillator and is the most direct test of "HA as state."
- **Renko lowers AE but also lowers FE (EXP-003, EXP-008).** Renko direction stability beats time bars on 4/4 instruments and Renko confirmation lowered AE on 4/4 instruments — but it also lowered FE, and primary log FE/AE improved only on USTEC. *Implication:* a Renko AE-control candidate is the most pre-constrained candidate in this phase; EXP-008 is close to a pre-falsification of the FE-non-inferiority guardrail it would need to clear.
- **PDH/PDL/ONH/ONL levels are deterministic and count-eligible (EXP-014).** Prior-range construction is validated infrastructure. *Implication:* a prior-range-location descriptor is the lowest-infrastructure-risk candidate.
- **Higher timeframe is not a free rescue for a weak low-resolution effect (Phase 004A/B).** An effect that concentrates at high resolution and decays an order of magnitude per coarsening is microstructure-sensitive, not structural. *Implication:* a Phase 005 candidate must show its effect at `1h`/`4h`/`1d` natively, not be rescued upward from intraday.
- **Deterministic resampling exists (`python/src/bar_aggregator.py`).** Clock-aligned 1m → N-minute aggregation with holdout exclusion applied before aggregation. *Caveat, see Data Scope:* it retains only windows containing *exactly* N source bars, which is a coverage hazard at `1h`/`4h` and a blocker at `1d`.

No event-chart or ICT result carries forward as a positive candidate.

## Candidate Universe (Predeclared Search Space)

Per the hard constraint that any data-mining workflow must predeclare its search space, selection budget, correction method, and follow-up protocol, the Phase 005 candidate universe is **locked at exactly four descriptors**, listed in priority order. No descriptor may be added after this design is finalized; a new descriptor requires a new checkpoint.

| Priority | Candidate | Descriptor | Role | Primary risk |
| --- | --- | --- | --- | --- |
| 1 | **Prior-Range Location** | Normalized close location inside a prior same-timeframe range | Simplest, lowest-infrastructure-risk, conceptually independent of all prior failures | Extreme buckets may be sparse; effect may be a known mean-reversion/continuation artifact |
| 2 | **Market Bias (CEREBR)** | Fixed `100/100/7` double-smoothed HA oscillator state | Concrete externally sourced fixed-parameter indicator; supersedes generic HA run-state | Long double-EMA memory → few independent episodes, esp. at `1d`; port determinism |
| 3 | **Range Compression/Expansion** | `bar_range / ATR14_prior` or train-frozen percentile | Simple non-directional volatility-state descriptor | Likely re-confirms volatility clustering (a known stylized fact) with no directional tradability |
| 4 | **Renko AE-Control** | Same-or-prior Renko confirmation state on matching source timeframe | Empirically anchored but narrowest | EXP-008 already showed Renko lowers FE alongside AE — near pre-falsification of its own guardrail |

**Selection budget:** four candidates. **Correction method:** per-candidate train/test sign-preservation replication on ≥2 **distinct instruments** (instrument is the independence unit; multiple timeframes from one instrument do not count as independent replication), plus the predeclared priority order and the matched-control requirement in the primary metric. **Follow-up protocol:** any descriptor that passes the primary return test advances to a stress/robustness experiment before any candidate-manifest language; no descriptor reaches the global holdout in this phase.

**Cross-candidate discipline:** candidate priority and selection are fixed by this document and by readiness gates only. Which candidate advances to a return test may never be chosen using test-segment return performance.

### HA run-state is merged, not dropped

Generic "Heiken Ashi run-state maturity" from the brainstorm is **not** a separate candidate. Market Bias is itself a sourced, fixed-parameter, HA-derived state descriptor and subsumes it. Generic HA run-length or raw HA direction may appear only as secondary diagnostics inside the Market Bias readiness/return path, never as an independent checkpoint.

## Locked Primary Edge Metric

The single primary edge metric for the **directional** candidates (Prior-Range Location, Market Bias) is locked before any experiment runs:

> **Executable direction-adjusted next-bar log return relative to the candidate's predeclared neutral/baseline state and matched simple control**, evaluated on real OHLC, with bootstrap confidence intervals, requiring train/test sign preservation on at least two distinct instruments.

- *Executable* means the descriptor is observed only after the current higher-timeframe bar closes; the earliest allowed entry is the **next same-timeframe bar open**; the primary exit is that next bar's close. Close-to-close returns may be reported only as diagnostics. Exactly **one** longer holding horizon is predeclared as a secondary co-test (see below); no other holding horizon may be introduced inside EXP-036/037 as a sensitivity search.
- *Direction-adjusted* means the executable log return is signed by the state's predeclared directional implication (bull/top state → long-direction return; bear/bottom state → short-direction return), so opposing states are pooled into one "state-aligned return" comparison against the neutral state within a cell. Results are evaluated by cell and replication count, not by one pooled cross-instrument p-value.
- *Neutral baseline* is the descriptor's own middle state (middle range-location bucket; flat/near-zero bias), not a zero baseline. Percentage improvement against a zero baseline is prohibited; comparisons are absolute return differences with CIs.
- *Matched simple controls* are binding:
  - Prior-Range Location must beat a same-timeframe **prior-bar momentum sign** control.
  - Market Bias must beat a real-price **EMA200 trend-sign** control.
  Passing against neutral but not against the matched control is recorded as state differentiation, not as an edge candidate.
- *Inference unit* is independent state episodes or non-overlapping blocks when row-level observations are serially dependent. Naive row bootstrap is diagnostic only for persistent descriptors.
- *Secondary diagnostics only:* MFE/MAE (FE/AE) in ATR units, hit rate, turnover, persistence. These never override the primary metric and never serve as the pass/fail gate.

**Predeclared secondary holding horizon (locked).** The next-bar primary is the most stringent possible horizon: single-bar real-price returns of liquid instruments at `1h`/`4h` have near-zero serial correlation, so a state descriptor that carries genuine *multi-bar* drift could show nothing next-bar. To prevent a single hostile horizon from being silently reported as thesis-level refutation, exactly one longer horizon is predeclared now: **enter at the next same-timeframe bar open and exit at the close of the 4th subsequent same-timeframe bar** (a fixed 4-bar hold, ~`4h` at `1h` and ~`16h` at `4h`). The integer `4` is fixed a priori by rationale (a short, bounded, still-executable multi-bar window); it is the only additional horizon permitted and may not be re-tuned. This secondary uses the identical machinery as the primary — direction-adjusted, signed by the state's predeclared directional implication, evaluated against the same neutral baseline **and** the same matched control, with bootstrap CIs and train/test sign preservation on ≥2 distinct instruments. Gate semantics are asymmetric and predeclared: the secondary **cannot manufacture an edge claim** — only the next-bar primary can produce candidate-manifest language in this phase — but a descriptor that fails the next-bar primary while passing the 4-bar secondary against both neutral and control is recorded as **horizon-dependent state differentiation**, which reopens the thesis at the longer horizon through a new predeclared experiment and is explicitly *not* recorded as thesis refutation. Failing both horizons against the matched control is a clean refutation of that descriptor.

The two **non-directional** candidates use different primaries by construction and are therefore demoted to contingent status:

- **Range Compression/Expansion** primary = future absolute movement / `max(FE, AE)` in ATR units by compression bucket. Because this is volatility prediction, a positive result risks being a trivial re-confirmation of volatility clustering; it is only meaningful if paired with a directional or asymmetry claim, which it is not in this phase.
- **Renko AE-Control** primary = adverse-excursion reduction with FE non-inferiority as a binding guardrail.

This mismatch is the explicit reason Compression and Renko are candidates 3 and 4: they do not fit the locked primary thesis metric, so they run only if the directional candidates fail and the phase still has budget. Neither can produce a candidate manifest in Phase 005 unless a later reflection explicitly reframes it as a risk-management component attached to a directional source.

## Data Scope

Primary data view:

- 1-minute time bars from `data/timebars/`, aggregated to higher timeframes.

**Higher-timeframe aggregation:**

- `1h` and `4h` bars are generated from 1-minute base bars using `python/src/bar_aggregator.aggregate_ohlc` (clock-aligned, deterministic). **The final 30% global holdout is excluded from the 1-minute series before aggregation.** The full dataset must never be aggregated and re-split.
- **Coverage hazard (mandatory readiness check).** `aggregate_ohlc` retains only windows containing *exactly* `period_minutes` 1-minute bars. For `1h` (60 bars) and `4h` (240 bars), any window missing even one 1-minute bar around session gaps or low-liquidity periods is dropped. The first readiness experiment must report the dropped-window rate per instrument and timeframe and decide, by a **predeclared** rule (not tuned on outcomes), whether a minimum-coverage tolerance (e.g., retain windows with ≥ a fixed fraction of expected bars) is required. Any tolerance rule must be fixed before any return test.
- **`1d` is contingent for two reasons: aggregation and power.** A clock-aligned 1440-minute window on gapped forex/index markets (weekends, daily session breaks) will almost never contain exactly 1440 1-minute bars, so the existing aggregator cannot produce daily bars for EURUSD, XAUUSD, or USTEC. `1d` also risks inadequate post-warmup train/test observations, especially for Market Bias after stacked EMA-100 smoothing. `1d` requires both a separate, predeclared **calendar/session daily aggregation rule** and the same numeric readiness floors used for `1h`/`4h`. Until both pass, `1d` is readiness-only and out of scope for return testing. `1h`/`4h` are the primary timeframes.

Synthetic-price discipline:

- Heiken Ashi and Renko construction prices are non-tradable synthetic values. Market Bias and Renko descriptors are computed from those construction values, but **all forward-return, FE/AE, and P&L outcomes use real OHLC** (`Open/High/Low/Close` of the aggregated real bar, or `RealOpen/...RealClose` for HA-derived frames). No outcome is ever computed from HA or Renko prices.

Instruments:

- EURUSD, XAUUSD, BTCUSD, USTEC for all readiness experiments. Outcome tests may narrow only through predeclared eligibility gates, never by return performance.

Mandatory exclusions:

- The final 30% global holdout remains excluded from all analysis, applied chronologically to the 1-minute series before any aggregation or descriptor computation.
- No tick, bid/ask, spread, commission, or slippage fields are assumed available. Cost-sensitive claims use explicit proxy scenarios only.

## Phase Gates

1. **Readiness-before-return gate.** No candidate may be return-tested until it passes readiness: deterministic computation, valid post-warmup coverage, and adequate state representation. The locked primary metric is computed only after readiness passes.
2. **Numeric count and independent-episode gate.** Every return-tested cell must report raw rows and independent state episodes by segment. A cell is eligible only if each compared state and its neutral baseline have at least `100` train rows, `50` test rows, `30` train independent episodes, and `15` test independent episodes. For descriptors with long memory (Market Bias above all), independent episodes — maximal runs of consecutive same-state bars — are the binding denominator, not raw post-warmup rows.
3. **Single-timeframe-before-MTF gate.** Each descriptor is tested single-timeframe first. Market Bias runs in chart-timeframe mode only (see its spec). No multitimeframe combination is built until single-TF behavior is understood.
4. **Matched-control gate.** A directional descriptor that beats only its neutral state does not become an edge candidate. It must also beat its candidate-specific simple control on the same executable primary metric, with train/test sign preservation on at least two distinct instruments.
5. **Holdout gate.** No Phase 005 experiment may inspect or use the final 30% global holdout. A future checkpoint decides whether any surviving candidate is strong enough to spend holdout.
6. **No-test-selection gate.** No parameter, threshold, bucket boundary, warmup length, coverage tolerance, or candidate selection may be chosen using test-segment return performance. All such choices are fixed on train or predeclared.
7. **Mid-phase reflection gate.** After the readiness stage, a reflection document decides which candidate(s) earned a return test, confirms the locked primary metric applies, and assigns return-test experiment IDs. No return-test scope is created before this directive.

## Planned Experiment Roadmap

The next experiment ID is `EXP-034`. Candidate IDs below are planning placeholders; each scope is still created one at a time through the research pipeline and may be split if it exceeds the complexity budget.

### Stage A: Readiness (runs first)

| Candidate ID | Candidate | Question | Decision use |
| --- | --- | --- | --- |
| EXP-034 | Prior-Range Location | At `1h`/`4h`, what is the range-location distribution and the top/middle/bottom bucket count per instrument and segment, what is the outside-range rate, and do states meet the numeric row/episode floors? Also: what is the `bar_aggregator` dropped-window rate at `1h`/`4h`, and is a predeclared coverage tolerance required? | Establishes the simplest candidate's count-eligibility and locks the shared aggregation coverage rule for the phase. |
| EXP-035 | Market Bias (CEREBR) | Does a deterministic Python implementation of Market Bias reproduce any available reference output, and in chart-timeframe mode do the sign-only and four-way states have adequate **independent-episode** counts at `1h`/`4h` per instrument and segment? | Settles port determinism, reference-fidelity wording, and the episode-count constraint before any return claim; likely confirms or refutes `1d` feasibility. |

### Mid-Phase Reflection

After EXP-035, a reflection document issues a directive before any return-test scope is written. It must specify, per candidate: proceed to return test, defer, or close; the instrument–timeframe cells eligible for testing; and the confirmed coverage/aggregation rule. It may also direct readiness for Compression and/or Renko only if the directional candidates are both ineligible and phase budget remains.

### Stage B: Return Tests (contingent on reflection directive)

| Candidate ID | Candidate | Question | Decision use |
| --- | --- | --- | --- |
| EXP-036 | Highest-priority readiness-passing directional candidate | Does the descriptor's executable state-aligned next-bar log return beat its neutral baseline and matched simple control on the locked primary metric, with bootstrap CIs and train/test sign preservation on ≥2 distinct instruments? | First real edge test of the state-descriptor thesis. |
| EXP-037 | Second readiness-passing directional candidate (if any) | Same locked primary metric, applied independently. | Independent replication of the thesis on a different descriptor. |
| EXP-038 | Any EXP-036/037 survivor | Does the surviving descriptor's edge survive segmentation (temporal halves first), bucket-boundary perturbation, execution delay, proxy-cost stress, opportunity-cadence checks, and concentration stress without depending on one instrument or one segment? | Decides whether a descriptor can become a future candidate manifest. |

Compression (candidate 3) and Renko AE-control (candidate 4) receive IDs only if the reflection explicitly activates them; they are not assumed to run.

## Candidate Specifications

### Candidate 1: Prior-Range Location

- **Feature:** `range_location = (Close − prior_low) / (prior_high − prior_low)`, where `prior_high`/`prior_low` are the high/low of the prior `20` completed same-timeframe bars. Clipped to `[0, 1]` with a separate outside-range flag.
- **Directional framing (locked):** **continuation from extremes**, not reversal — the sweep-reversal path was refuted (EXP-015, EXP-030). Top bucket → long-direction bias; bottom bucket → short-direction bias; middle bucket → neutral baseline.
- **Buckets:** bottom `<= 0.20`, middle `(0.20, 0.80)`, top `>= 0.80`. These are fixed thresholds, not data-driven terciles.
- **Matched control:** same-timeframe prior-bar momentum sign using the same executable next-bar return convention. If Prior-Range beats neutral but not this control, it records descriptive state differentiation only.
- **Readiness (EXP-034):** range-location distribution, top/middle/bottom counts by instrument/timeframe/segment, outside-range rate, aggregation coverage rate. **Coverage-rule feature-interaction check (required):** because any partial-window coverage tolerance retains windows with understated `High`/`Low`, it directly perturbs the `20`-bar `prior_high`/`prior_low` that normalizes `range_location`. EXP-034 must report the range-location distribution and bucket counts under **both** strict (exactly-`N`-bar) and the candidate tolerant aggregation, and the coverage tolerance is admissible for the phase only if the bucket assignment is stable between the two. If the feature is unstable to the tolerance choice, strict aggregation is retained even at the cost of coverage.
- **Fast stop:** stop if extreme buckets are not count-eligible, if outside-range/middle states dominate so heavily that extremes cannot be tested, or if train/test bucket assignment is unstable.

### Candidate 2: Market Bias (CEREBR)

Source: `docs/planning/market-bias.txt` (TradingView Pine v5, MPL-2.0). Core: `o,c,h,l = EMA(OHLC, 100)` → Heiken-Ashi-style transform → `o2,c2 = EMA(haopen/haclose, 100)` → `osc_bias = 100·(c2 − o2)`, `osc_smooth = EMA(osc_bias, 7)`. Four-way state: strong/weak bull/bear by sign of `osc_bias` and its relation to `osc_smooth`.

- **Chart-timeframe mode only (locked for this phase).** Set the indicator timeframe equal to the bar timeframe. With `ha_htf` = chart TF, `indexHighTF` and `indexCurrTF` both become 0 and `f_no_repaint_request` collapses to the identity of its expression — the `request.security` calls are no-ops. This removes all multitimeframe and lookahead-offset semantics; the only port risk is local EMA/HA recursion, including the recursive HA-open seeding (`haopen` depends on `xhaopen[1]`). No MTF import is built in Phase 005.
- **Sign-only state is primary; four-way is secondary.** The strong/weak axis is `osc_bias` versus its own EMA-7 — an acceleration/momentum-of-momentum sign likely to churn and add little information. The primary descriptor is **bull vs bear** (sign of `osc_bias`); the four-way state is reported as a secondary diagnostic only.
- **Episode-count readiness, not row count.** Because of the stacked EMA-100s, the state has very long memory and will persist for long stretches. Readiness (Gate 2) counts independent state episodes, not post-warmup rows. `1d` is expected to be sample-constrained and is likely deferred regardless of the daily-aggregator question.
- **Warmup (predeclared rule, not a discretionary EXP-035 choice):** the stacked EMA-100 → EMA-100 → EMA-7 chain is doubly recursive, so `300` bars (3× the nominal period) is a floor, not necessarily sufficient. The warmup length `W` is therefore a deterministic function of the data fixed in advance: compute the four-way state label sequence under two EMA seedings — Pine's `ta.ema` convention (SMA of the first `length` values) and a cold first-value seed — and set `W` to the smallest bar index beyond which the two seedings produce an **identical state-label sequence for all subsequent bars**, floored at `300`. Discard the first `W` same-timeframe bars before any readiness or return metric. If the two seedings never converge to an identical label sequence within the available pre-test (train) history, Market Bias **fails readiness** and is not return-tested. No `W` may be chosen by inspecting return performance.
- **Port determinism and reference fidelity:** the Python implementation must reproduce the published formula deterministically. Two specific port hazards are flagged from the source audit: (a) the HA-open recursion in `market-bias.txt` keys off `xhaopen[1]` (the prior bar's `(o+c)/2`), **not** the standard `haopen[1]`, so the conventional Heiken-Ashi recursion must not be assumed; and (b) Pine's `ta.ema` seeds with an SMA of the first `length` values, a convention easy to mis-port and material to the warmup rule above. **Preferred path:** obtain even a short exported TradingView reference series before EXP-035 scope approval and compare bar-for-bar. **If no reference values can be sourced, this is pre-committed now:** EXP-035 may claim only "deterministic re-implementation of the published Pine formula," may not claim Pine-equivalence, and any negative Market Bias return result in EXP-036/037 must carry an explicit attribution caveat that the null cannot be separated from unverified port fidelity. A deterministic-but-unverified port is not, by itself, grounds to close the Market Bias branch of the thesis.
- **Matched control:** real-price EMA200 trend sign on the same higher-timeframe bars, using the same `300`-bar warmup and executable next-bar return convention. Raw HA direction may be reported as a secondary diagnostic only.
- **Readiness (EXP-035):** deterministic port confirmation; valid post-warmup rows and **independent-episode counts** for sign-only and four-way states by instrument/timeframe/segment; transition counts and persistence.
- **Fast stop:** stop before any return test if the port cannot be made deterministic, if independent-episode counts are inadequate on ≥2 distinct instruments, or if state collapses into one dominant state.

### Candidate 3: Range Compression/Expansion (contingent)

- **Feature:** one predeclared compression measure — `bar_range / ATR14_prior`, or a train-frozen rolling percentile of that ratio.
- **Primary:** future absolute movement or `max(FE, AE)` in ATR units by compression/middle/expansion bucket. Directional P&L is not primary.
- **Known risk:** a positive result likely re-confirms volatility clustering and carries no directional tradability.
- **Fast stop:** stop if compression only predicts lower realized movement, if the effect is one-instrument-only, or if bucket thresholds need tuning to look useful.

### Candidate 4: Renko AE-Control (contingent)

- **Feature:** binary same-or-prior Renko confirmation on the matching `1h`/`4h` source timeframe (`python/src/renko_generator.py`, `atr_period=14`). Returns evaluated on real prices via `SourceCloseTime` alignment.
- **Primary:** adverse-excursion reduction, with FE non-inferiority as a binding guardrail. Coverage cost is first-class.
- **Known risk:** EXP-008 already found Renko confirmation lowered AE *and* FE on 4/4 instruments — the FE-non-inferiority guardrail is close to pre-falsified.
- **Fast stop:** stop if coverage is too low, if FE compression exceeds the predeclared bound, or if AE reduction does not replicate beyond one instrument.

## Methods Standards

- Chronological analysis-set slicing with the final 30% global holdout excluded; holdout exclusion applied to the 1-minute series before aggregation.
- Nested 70/30 train/test split inside the analysis set.
- Real OHLC for all return, FE, AE, and P&L outcomes. Never compute outcomes from HA or Renko construction prices.
- Descriptor observed at higher-timeframe bar close; primary executable return enters at the next same-timeframe bar open and exits at the next same-timeframe bar close.
- Timestamp alignment by `CloseTime` (aggregated real bars) or `SourceCloseTime` (chart-type events); never by bar index.
- No future data after a descriptor's evaluation timestamp.
- Predeclare bucket boundaries, warmup lengths, lookbacks, and coverage tolerances before results are inspected. No parameter search against outcome performance.
- Prefer descriptive diagnostics, paired comparisons, bootstrap intervals, and the locked simple matched controls. Non-parametric by default.
- Report event/episode counts and coverage before effect sizes. Define metric denominators and zero-baseline behavior before implementation.
- Treat transaction costs as proxy stress only.

## Complexity Budget

Per experiment:

- Maximum statistical test families: 3.
- Maximum primary plots: 4.
- Maximum new reusable modules: 1, and only if existing modules (`bar_aggregator.py`, `heiken_ashi_generator.py`, `renko_generator.py`, or a new `python/src/market_bias.py` port) cannot support the scope cleanly. A deterministic daily-session aggregator, if needed, is a candidate for the one new module.
- Outcome tests use bounded tables and plots; never materialize the holdout or unbounded detail tables for plotting.

For the checkpoint:

- Readiness target: 2 experiments (`EXP-034`, `EXP-035`).
- Return-test target: up to 3 experiments (`EXP-036`–`EXP-038`), contingent on the reflection directive.
- Contingent candidates (Compression, Renko) add experiments only if explicitly activated by the reflection.
- No exit-model or sizing experiment unless a descriptor first produces a robust directional edge. Continuous sizing must never be used to rescue an uninformative descriptor.
- No full-model experiment in this checkpoint.

## Explicit Non-Goals

- No reopening of the ICT chain, USTEC breaker, IFVG confirmation, or EURUSD sweep as positive candidates.
- No event-chart pattern mining as alpha.
- No multitimeframe combination in this phase; Market Bias runs chart-TF only.
- No reversal framing for Prior-Range Location; continuation is locked.
- No use of HA or Renko construction prices for any outcome.
- No `1d` return testing until a predeclared daily-session aggregator passes readiness and the numeric row/episode floors pass.
- No candidate added beyond the locked four-descriptor universe.
- No parameter, bucket-boundary, warmup, or coverage-tolerance tuning against analysis-set return performance.
- No global-holdout access.

## Expected Phase Outcomes

One of the following is sufficient and useful:

1. **A directional state descriptor survives.** Prior-Range Location or Market Bias beats its neutral baseline and matched simple control on the locked executable primary metric with train/test sign preservation on ≥2 distinct instruments and survives stress — Phase 005 creates a narrow state-descriptor candidate manifest for future holdout validation.
2. **A descriptor passes readiness but fails the return test.** The state-descriptor thesis is refuted for that descriptor with clean, holdout-preserving evidence.
3. **Readiness fails.** A descriptor cannot be made count-eligible (e.g., Market Bias has too few independent episodes; extreme range-location buckets are too sparse) — recorded as a readiness-gated no-go.
4. **The thesis closes.** No descriptor produces a robust edge; Phase 005 closes the state-descriptor thesis before holdout and Phase 006 starts from a new domain.

## Resolved Draft Gaps

This revision resolves the draft gaps that would otherwise make Phase 005 too loose for actionable edge discovery:

1. **Forward-return horizon and execution convention locked.** Directional return tests use executable next-open to next-close same-timeframe log returns. Longer horizons are not sensitivity knobs inside EXP-036/037.
2. **Replication unit tightened.** A candidate must replicate across at least two distinct instruments, not merely two correlated instrument–timeframe cells.
3. **Matched controls made binding.** Prior-Range must beat prior-bar momentum; Market Bias must beat EMA200 trend sign. Neutral-state differentiation alone is not enough for candidate language.
4. **Power and `1d` clarified.** `1d` is contingent on both a valid daily-session aggregator and numeric row/episode floors. `1h`/`4h` are the primary return-test timeframes.
5. **Market Bias reference claim downgraded when needed.** Pine-equivalence requires exported reference values; otherwise the experiment may claim only deterministic formula re-implementation.
6. **Actionability ladder made explicit.** A Phase 005 return-test pass is not a profitability claim. Candidate-manifest language requires robustness, delay, cost, cadence, and concentration stress.
7. **Serial-dependence risk addressed.** Persistent state descriptors use independent state episodes or non-overlapping blocks for inference; row-level bootstrap is diagnostic only.

## Predeclared Amendments (2026-05-28, before EXP-034 scope)

These amendments were folded in after a pre-commencement readiness review and **before any EXP-034 artifact was created**, so every choice below remains predeclared (no result was inspected). They tighten four places where a degree of freedom or a thesis-level false negative could otherwise leak.

1. **Secondary holding horizon locked.** A single fixed 4-bar hold is predeclared alongside the next-bar primary (see *Locked Primary Edge Metric*). It cannot manufacture an edge claim; it exists only so a hostile single-bar horizon cannot be reported as thesis-level refutation. A descriptor that passes the secondary but not the primary is recorded as horizon-dependent state differentiation, not refutation.
2. **Market Bias warmup is now a predeclared deterministic rule** (two-seeding convergence, floored at `300`), replacing the prior discretionary "revise inside EXP-035" clause. Non-convergence within train history fails readiness.
3. **EXP-034 must report Prior-Range Location readiness under both strict and tolerant aggregation.** The coverage tolerance is admissible only if range-location bucket assignment is stable to it; otherwise strict aggregation is retained.
4. **Market Bias reference-fidelity fallback pre-committed.** Two port hazards (non-standard `xhaopen[1]` recursion; Pine `ta.ema` SMA seeding) are flagged. Absent an exported reference series, EXP-035 may claim only deterministic re-implementation, and any negative Market Bias return result must carry an unverified-fidelity attribution caveat rather than closing the branch.

No candidate was added, no metric was loosened, and the candidate universe remains locked at four. These amendments only constrain or clarify; they do not expand scope.

## Immediate Next Step

Scope `EXP-034` (Prior-Range Location readiness) as the first experiment. Beyond the candidate's own readiness, EXP-034 also establishes the shared `1h`/`4h` aggregation coverage rule (dropped-window rate and any predeclared coverage tolerance) that every subsequent Phase 005 experiment inherits. It must report readiness against the fixed `20`-bar prior range, `0.20/0.80` buckets, and numeric row/episode floors above. `EXP-035` (Market Bias port + readiness) follows. No return-test scope is created until the mid-phase reflection issues its directive.

Note on ordering: all four candidates are predeclared, so the readiness order (Prior-Range Location first, then Market Bias) can be swapped before `EXP-034` is scoped without violating predeclaration — Prior-Range Location leads because it is the cleanest, lowest-infrastructure-risk path to the locked return test and is conceptually independent of every prior failure.
