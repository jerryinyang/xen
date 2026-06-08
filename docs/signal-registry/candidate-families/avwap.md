# Candidate Family: CF-AVWAP-001 - Anchored VWAP on Regime Pivots

**Status:** REGISTERED for Phase 004 Batch 004-A.
**Primary registry:** `docs/signal-registry/multiplicity-registry.md`
**First EXP:** EXP-020

## Thesis

An anchored VWAP reset at deterministic trend-regime pivots may act as a useful
support/resistance reference. The first branch tests whether this idea can be
defined without look-ahead and whether its bounce events show measurable
real-price reaction before any full strategy screen.

This is a candidate family, not a proven strategy.

## Brainstorming Provenance

This registry entry preserves the original AVWAP brainstorming direction while
splitting it into falsifiable experiments for multiplicity control:

| Original idea | Registry treatment |
| --- | --- |
| AVWAP from HLC3, anchored to dynamic trend-regime pivots and weighted by volume. | Preserved in the fixed first branch. |
| Streaming viable-pivot tracking with a separate temporary cache before regime confirmation. | Preserved as an implementation requirement for anchor selection. |
| Pivots as highest highs or lowest lows between regime changes. | Preserved as the first-branch anchor rule. |
| Multiple trend detectors: MA crossover, Line Break, Market Bias, ATR pivot reversal. | MA(20,50) is the baseline detector; Line Break, Market Bias, and ATR pivot reversal are registered non-baseline Phase 004 branches requiring separate scopes before measurement. |
| Domain-dependent MA periods. | Registered as `CF-AVWAP-001/MA-DOMAIN`; the brainstorm did not define the period map, so the map must be specified in scope before measurement. |
| Nonlinear tick-volume weighting, with alpha near 0.75 as a practical default. | Preserved as frozen `TickVolume ** 0.75` for the baseline branch; alpha sensitivity is a registered non-baseline branch. |
| MAD bands around the anchored VWAP. | Preserved with multiplier 1.0 in the first branch. |
| Bounce as close crossing AVWAP in the trend direction after moving to the opposite side. | Preserved as the baseline event definition. |
| Original HYP-001: AVWAP acts as support/resistance and price reacts from it. | Split into EXP-020 substrate readiness, EXP-021 fixed-horizon reaction, and EXP-022 original lifetime move efficacy. The readiness split is a pipeline gate, not a replacement of the original thesis. |
| Band-target or trend-change move completion. | Registered for Phase 004 as EXP-022, using deterministic target and trend-change rules below. |
| Performance metrics: successful bounce rate, bounce expectancy, risk-adjusted model comparison, and prevalence. | Prevalence is EXP-020; fixed-horizon expectancy is EXP-021; lifetime success rate and expectancy are EXP-022; strategy-level risk-adjusted model-vs-raw comparison is EXP-023. |
| Multi-bounce and "pyramid bounce" tagging. | Preserved as event metadata in EXP-020 and required as a stratification diagnostic in EXP-022/EXP-023; no position-size pyramiding is introduced without a separate scope. |
| Unfinished observations at end of sample. | Registered for EXP-022: unfinished lifetime observations are counted and excluded from completed-move efficacy denominators. |
| Cross-timeframe relationship and more precise entries. | Registered as `CF-AVWAP-001/XTF`; the original note excludes it from the first stage, so it requires a separate concrete scope before measurement. |

## Fixed First-Branch Definition

### Data Views

- Base source: 1-minute time bars from `data/timebars/`.
- Domain bars: 5m, 1h, and 4h OHLC bars built from the first 70 percent
  analysis slice.
- Domain construction: 5m strict coverage; 1h and 4h with `min_coverage=0.90`,
  matching the EXP-004/009 domain convention.
- Instruments: BTCUSD, EURUSD, USTEC, XAUUSD.

The final 30 percent global holdout is not loaded, inspected, run in cTrader, or
used for any registry decision.

### Regime Detector

The first branch uses the simple moving-average crossover convention already
validated in the project:

- fast SMA: 20 domain bars;
- slow SMA: 50 domain bars;
- bullish regime: fast SMA > slow SMA;
- bearish regime: fast SMA < slow SMA;
- neutral/warmup/tie: no active regime and no signal.

A regime change is confirmed only at a completed domain bar close. Signals
derived from the new regime may occur only after the confirmation bar.

### Anchor Rule

During each active regime the state machine tracks both viable pivots from
completed bars:

- viable bullish anchor: lowest `Low` since the prior confirmed regime change;
- viable bearish anchor: highest `High` since the prior confirmed regime change.

When a new bullish regime is confirmed, the AVWAP anchor is the latest viable
low. When a new bearish regime is confirmed, the AVWAP anchor is the latest
viable high. The implementation must maintain the temporary cache needed to
compute the anchored series from the selected pivot without backtracking through
future information.

### AVWAP and Bands

- Price source: typical price, `(High + Low + Close) / 3`.
- Weight: `TickVolume ** 0.75`.
- AVWAP: cumulative weighted average from the active anchor through the current
  completed domain bar.
- Band spread: median absolute deviation of typical price from the anchored
  AVWAP path since the active anchor.
- First-branch band multiplier: 1.0.

Tick volume is a proxy, not true traded volume. The exponent compresses volume
spikes and is frozen for Batch 004-A.

### Bounce Event

The first branch treats a bounce as a confirmed close crossing the AVWAP in the
active regime direction after price has first moved to the opposite side:

- bullish regime: arm when a completed close is below AVWAP; trigger when a
  later completed close crosses back above AVWAP;
- bearish regime: arm when a completed close is above AVWAP; trigger when a
  later completed close crosses back below AVWAP.

Only completed bars count. Intrabar touches do not count. Multiple bounces in a
single regime are allowed only after the event re-arms.

## Hypotheses and Experiment Sequence

| Hypothesis | Question | EXP | Gate |
| --- | --- | --- | --- |
| HYP-001 | Can the first-branch AVWAP state machine be deterministic, look-ahead-safe, and non-degenerate across the analysis set? | EXP-020 | Required before reaction or strategy tests. |
| HYP-002 | Do AVWAP bounce events show better fixed-horizon direction-signed real-price reaction than matched non-event controls? | EXP-021 | Required before candidate-suite screening. |
| HYP-003 | Under the original band-target/trend-change lifetime definition, do AVWAP bounces produce favorable completed-move outcomes? | EXP-022 | Required before candidate-suite screening. |
| HYP-004 | Does the baseline AVWAP signal pass standalone or portfolio-fitness qualification under the frozen suite, while reporting the original strategy metric book? | EXP-023 | Requires component evidence from EXP-021 and EXP-022. |

Registry HYP numbering is local to this family. The brainstorming document's
HYP-001 (AVWAP as support/resistance with price reaction) maps to registry
HYP-002 and HYP-003; its HYP-002 (full signal-model viability) maps to registry
HYP-004.

### HYP-002 Reaction Metric Family

EXP-021 is allowed to test event reaction only, not full strategy P&L. The
registered reaction metric family is:

- event unit: EXP-020 bounce events from supported instrument/domain cells;
- return basis: real domain OHLC only, using trigger-close to future-close
  direction-signed returns;
- fixed horizons: 1, 3, and 6 completed domain bars after the trigger;
- comparison set: matched non-event eligible bars from the same
  instrument/domain/regime direction within the analysis set;
- denominator: report event counts and matched-control counts by instrument,
  domain, direction, and horizon; zero denominators are non-reportable;
- primary interpretation: EXP-021 must predeclare its primary horizon and
  multiple-comparison handling in its scope before measurement.

HYP-002 is a short-horizon reaction test. A negative HYP-002 result rejects only
the fixed-horizon reaction operationalization; it does not refute HYP-003's
original lifetime operationalization.

### HYP-003 Original Lifetime Metric Family

EXP-022 tests the original move-lifetime model from the brainstorming document.
It is allowed to use only EXP-020 events from supported instrument/domain cells
and real domain OHLC prices.

Completion rule:

- long/bullish bounce favorable target: the upper MAD band value frozen at the
  trigger bar;
- long/bullish bounce adverse target: the lower MAD band value frozen at the
  trigger bar;
- short/bearish bounce favorable/adverse targets are reversed;
- a target is reached only by a completed close at or beyond the frozen target;
  intrabar touches do not count;
- a trend-change completion occurs at the first completed bar that confirms the
  opposite MA(20,50) regime before either target is reached;
- if the analysis set ends before a target or trend-change completion, the move
  is recorded as unfinished and excluded from completed-move efficacy
  denominators.

Targets are frozen at the trigger bar so completion is deterministic and
reproducible, operationalizing the brainstorming document's requirement for
deterministically defined targets for live trading.

Metrics:

- completed-move count and unfinished count by instrument, domain, direction,
  and `is_pyramid_bounce`;
- successful bounce rate: favorable-target completions divided by completed
  target completions, with trend-change completions reported separately;
- lifetime expectancy: direction-signed real-close return from trigger close to
  completion close, net of the scoped cost convention if EXP-022 defines one;
- trend-change completion return distribution;
- benchmark requirement: the favorable-outcome metrics above must be compared
  against at least one look-ahead-safe benchmark on the same
  instrument/domain/direction cells - a matched non-event control, a
  random-anchor lifetime analog, or a regime-drift baseline. If EXP-022 cannot
  define any such benchmark without using future information, its lifetime
  metrics are descriptive only: they may be reported, but an unbenchmarked
  EXP-022 result cannot by itself satisfy PROCEED_TO_SCREEN (see the Phase 004
  checkpoint outcome criteria).

### HYP-004 Strategy Metric Book

EXP-023 is the first full candidate screen. It must run through the cTrader
strategy-host branch and the frozen Python suite. In addition to suite verdicts,
it must report the original brainstorming metric book:

- valid bounce prevalence inherited from EXP-020;
- successful-bounce rate and lifetime expectancy inherited or reproduced from
  EXP-022;
- strategy return expectancy on real domain prices;
- risk-adjusted model return metric compared with raw/traditional domain
  returns;
- diagnostics split by instrument, domain, direction, and `is_pyramid_bounce`.

## Baseline Exclusions

- Strategy stop/target optimization, trailing exits, position sizing, and
  position-size pyramiding. The registered lifetime targets are event-completion
  metrics, not optimized trade-management rules.
- Optimization against analysis-set outcomes.
- Any use of Heiken Ashi or Renko construction prices for P&L.
- Any cTrader candidate screen before the component characterization gates are
  satisfied.

## Registered Non-Baseline Branches

The following are part of the Phase 004 AVWAP concept registry, but not part of
the immediate baseline chain EXP-020 through EXP-023. Each requires a separate
scope before measurement and must keep negative, blocked, and inconclusive
outcomes in the file-drawer ledger:

- `CF-AVWAP-001/LB`: Line Break direction as the regime detector.
- `CF-AVWAP-001/MB`: Market Bias as the regime detector.
- `CF-AVWAP-001/ATR`: ATR pivot-reversal regime detector.
- `CF-AVWAP-001/ALPHA`: alpha sensitivity over predeclared tick-volume
  exponents, with no post-result selection.
- `CF-AVWAP-001/BAND`: band-multiplier sensitivity over predeclared values,
  with no post-result selection.
- `CF-AVWAP-001/MA-DOMAIN`: domain-scaled MA periods. The original note says MA
  periods may depend on timeframe, but does not define the period map; any map
  must be specified in a new scope before measurement.
- `CF-AVWAP-001/XTF`: cross-timeframe relationship and more granular entry
  refinements.
- `CF-AVWAP-001/EXIT`: exit overlays (time-stop, revised trend-change handling,
  adverse-band stop, or price-action/Heiken Ashi exits). Phase 005 scopes these
  from the EXP-024 dissipation diagnostic; concrete rules are predeclared before
  any screen, never swept.
- `CF-AVWAP-001/ANCHOR`: significant-pivot anchor (structural swing / ATR-reversal
  pivot) versus the baseline running-extreme anchor (gaps analysis #1). Registered
  2026-06-08 (Phase 005); requires a dedicated scope before measurement.

## Implementation Path

1. Python characterization builds the state machine and event tables for EXP-020
   through EXP-022.
2. If the component evidence justifies a candidate screen, the same signal logic
   and registered lifetime rules are ported to the cTrader strategy-host branch.
3. cTrader emits positions and events; Python validates through the frozen suite
   and reports the registered metric book.

Python may characterize the component, but strategy-generation and candidate
screening must use the cTrader branch once the work reaches suite validation.
