# Phase 004 - AVWAP Signal Exploration

**Checkpoint type:** Research phase design.
**Date finalized:** 2026-06-07.
**Status:** ACTIVE - design opened; no Phase 004 candidate result exists.
**First candidate family:** `CF-AVWAP-001` - Anchored VWAP on regime pivots.

## 1. Provenance

Phase 003b completed the framework-construction programme and froze the
three-component qualification suite:

- strict gate stack;
- EXP-012 ratified-loose referee;
- EXP-018 revised portfolio-fitness unit.

INFR-001 then validated the cTrader strategy-host branch through VAL-002. That
lifted the cTrader hard block. Phase 004 can therefore begin, but only behind
the programme-level multiplicity/file-drawer registry required by the Phase
003b retrospective.

That registry is now the first Phase 004 artifact:

- `docs/signal-registry/README.md`
- `docs/signal-registry/multiplicity-registry.md`
- `docs/signal-registry/candidate-families/avwap.md`

## 2. Objective

Start real signal exploration with one registered candidate family, AVWAP, while
preserving the framework's anti-overfitting discipline:

1. define the candidate family before measurement;
2. decompose the broad AVWAP thesis into one experiment per falsifiable question;
3. test component readiness before full strategy screening;
4. use the cTrader branch only when a strategy candidate is ready for suite
   validation;
5. keep the final 30 percent global holdout sealed.

## 3. Multiplicity Gate

Phase 004 Batch 004-A is restricted to one candidate family:

| Field | Value |
| --- | --- |
| Candidate family | `CF-AVWAP-001` |
| Registry file | `docs/signal-registry/multiplicity-registry.md` |
| Family spec | `docs/signal-registry/candidate-families/avwap.md` |
| First branch | MA(20,50)-regime AVWAP with `TickVolume ** 0.75` and MAD band multiplier 1.0 |
| Candidate-screening status | Not started |

The original AVWAP lifetime method and metric book are registered in Batch
004-A. Original non-baseline AVWAP concepts are registered in
`docs/signal-registry/candidate-families/avwap.md`; each requires a dedicated
scope before measurement. Any separate signal family, unregistered exit overlay,
or unregistered position-management rule requires a dated amendment or explicit
scope update before measurement. Negative, blocked, and inconclusive outcomes
stay in the registry.

## 4. Frozen First-Branch Definition

The first AVWAP branch is fixed in the registry and summarized here:

- source bars: 1-minute time bars;
- domain bars: 5m, 1h, 4h;
- domain construction: 5m strict coverage; 1h/4h `min_coverage=0.90`;
- instruments: BTCUSD, EURUSD, USTEC, XAUUSD;
- regime detector: simple MA crossover, fast 20 / slow 50, on domain `Close`;
- anchor rule: bullish regimes anchor to the latest viable pivot low; bearish
  regimes anchor to the latest viable pivot high;
- AVWAP source: typical price `(High + Low + Close) / 3`;
- AVWAP weight: `TickVolume ** 0.75`;
- band spread: median absolute deviation from the anchored typical-price path,
  multiplier 1.0;
- bounce event: close crosses AVWAP in the regime direction after first moving
  to the opposite side.

These definitions may be clarified for implementation precision before EXP-020
code, but may not be changed after EXP-020 pre-execution approval without a
registry amendment.

## 5. Planned Experiment Chain

| EXP | Title | Purpose | Gate |
| --- | --- | --- | --- |
| EXP-020 | AVWAP Event-Substrate Readiness | Verify deterministic, look-ahead-safe AVWAP state generation and usable event coverage. | Required before reaction or strategy tests. |
| EXP-021 | AVWAP Bounce Reaction Study | Test whether bounce events show better fixed-horizon direction-signed real-price reaction than matched controls, using the metric family registered in `docs/signal-registry/candidate-families/avwap.md`. | Required before candidate-suite screening. |
| EXP-022 | AVWAP Original Lifetime Move Study | Test the brainstorming document's band-target/trend-change move-completion method and lifetime metrics. | Required before candidate-suite screening. |
| EXP-023 | AVWAP Baseline Candidate Screen | If component evidence supports proceeding, screen the baseline AVWAP signal through the frozen suite and report the original strategy metric book. | Requires cTrader strategy-host generation. |

The phase does not start with a full strategy backtest. A full screen without
component evidence would mix definition, event prevalence, signal quality,
lifetime behavior, and portfolio fitness into one uninterpretable result.

After the baseline chain, Phase 004 may continue with the registered
non-baseline AVWAP branches from the family spec:

- `CF-AVWAP-001/LB` - Line Break direction regime detector;
- `CF-AVWAP-001/MB` - Market Bias regime detector;
- `CF-AVWAP-001/ATR` - ATR pivot-reversal regime detector;
- `CF-AVWAP-001/ALPHA` - predeclared tick-volume exponent sensitivity;
- `CF-AVWAP-001/BAND` - predeclared band-multiplier sensitivity;
- `CF-AVWAP-001/MA-DOMAIN` - domain-scaled MA period map, once specified;
- `CF-AVWAP-001/XTF` - cross-timeframe relationship and more granular entry
  refinements;
- `CF-AVWAP-001/EXIT` - exit overlays, only after concrete rules are scoped.

Each non-baseline branch must be split into one falsifiable pipeline experiment
at a time before any result-producing code. Registration here is not permission
to sweep parameters or select variants after outcomes.

## 6. EXP-020 Scope Summary

EXP-020 is the active next experiment. It answers:

> Can the first-branch AVWAP state machine be implemented as a deterministic,
> look-ahead-safe event substrate with enough bounce coverage to justify a
> reaction study?

EXP-020 is a readiness and substrate experiment. It does not claim a market edge
and does not run the frozen qualification suite.

Expected artifacts:

- `python/experiments/EXP-020/scope.md`
- `python/experiments/EXP-020/analysis-plan.md`
- later, after implementation: `code/run_experiment.py`, `results/`, `audit.md`,
  `results.md`, `report.md`, and governance reviews.

## 7. Methodological Guardrails

- The final 30 percent global holdout is excluded from all analysis.
- Time bars order by `CloseTime`; cTrader strategy runs emit `SourceCloseTime`.
- Strategy and reaction outcomes use real OHLC prices only.
- Tick volume is treated as a proxy for traded volume.
- AVWAP component characterization may be implemented in Python, but candidate
  strategy screening must use the cTrader strategy-host branch.
- No threshold, detector, or parameter tuning is allowed against Phase 004
  outcomes.
- A failed substrate, reaction, or lifetime test is a valid result, not
  permission to silently try a new AVWAP variant.
- A negative fixed-horizon EXP-021 result refutes only that operationalization;
  it does not refute the original lifetime method, which is tested separately in
  EXP-022.
- A favorable EXP-022 lifetime result must be measured against a look-ahead-safe
  benchmark (matched control, random-anchor, or regime-drift baseline); an
  unbenchmarked lifetime result is descriptive only and cannot authorize the
  cTrader screen.

## 8. Phase Outcome Criteria

| Outcome | Criteria | Consequence |
| --- | --- | --- |
| PROCEED_TO_SCREEN | EXP-020 supports substrate readiness, EXP-021 and EXP-022 are completed, and at least one registered reaction/lifetime operationalization supports proceeding under predeclared criteria against a look-ahead-safe benchmark (matched non-event control, random-anchor, or regime-drift baseline). A lifetime (EXP-022) result without such a benchmark is descriptive only and cannot by itself authorize the screen. | Implement cTrader AVWAP baseline and run EXP-023. |
| NARROW_DOMAINS | EXP-020 supports only a predeclared subset of domains with no invariant failures. | Governance may approve EXP-021 only on supported domains. |
| COMPONENT_REFUTED | EXP-020 finds invariant failure/severe degeneracy, or both registered reaction/lifetime operationalizations fail on the supported domains. | Retire or amend `CF-AVWAP-001` before any new branch. |
| INCONCLUSIVE | Coverage or uncertainty is insufficient but no correctness failure is found. | Record inconclusive result; new scope required for any follow-up. |

## 9. Non-Goals

- Exit overlays, stop optimization, target optimization beyond the registered
  lifetime method, position-size pyramiding, or risk-management optimization.
- Multi-signal reference books beyond the existing dogfood reference setup.
- Execution-realism research using real fills/spread/slippage as qualification
  inputs.
- Any use of the global holdout.

## 10. Immediate Next Step

Proceed through the research pipeline for EXP-020:

1. approve the scope;
2. implement the analysis plan;
3. create `code/run_experiment.py`;
4. run pre-execution governance;
5. stop for the manual execution gate.
