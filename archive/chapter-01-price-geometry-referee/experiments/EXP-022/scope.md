# Experiment: EXP-022 - AVWAP Original Lifetime Move Study

## Hypothesis

Under the registered band-target/trend-change lifetime definition, AVWAP bounce
events from the supported CF-AVWAP-001 first branch produce more favorable
completed-move outcomes than matched non-event lifetime analogs on at least one
EXP-020 ready domain, without touching the global holdout.

## Question

When an AVWAP bounce triggers, does the original frozen target/trend-change
lifetime method resolve more favorably than the same lifetime challenge started
from comparable non-event bars?

## Scope Boundaries

- **Data Views**: EXP-020 `avwap_events.csv` and `avwap_state_summary.csv` plus
  5m, 1h, and 4h domain OHLC bars rebuilt from 1-minute time bars after the
  first-70% analysis slice is applied. No chart-type views are in scope.
- **Candidate family**: `CF-AVWAP-001/HYP-003`, first branch only, as registered
  in `docs/signal-registry/candidate-families/avwap.md`.
- **Dependency gate**: EXP-020 must have `SUPPORTED_FULL` status, zero invariant
  failures, deterministic replay match, and ready domains `{5m, 1h, 4h}`. If
  EXP-020 artifacts are missing or fail these checks, EXP-022 is blocked.
- **Parameters**:
  - domain bars: 5m strict coverage; 1h and 4h `min_coverage=0.90`;
  - AVWAP branch: MA(20,50) regime detector, typical price, `TickVolume ** 0.75`,
    MAD band multiplier 1.0, and EXP-020 bounce definition unchanged;
  - event favorable/adverse targets: EXP-020
    `favorable_target_at_trigger` and `adverse_target_at_trigger`, frozen at
    trigger time;
  - target completion: completed domain `Close` at or beyond the frozen target;
  - trend-change completion: first completed bar that confirms the opposite
    MA(20,50) regime before either target is reached;
  - unfinished: analysis set ends before target or trend-change completion;
  - matched controls: up to 5 deterministic non-event controls per event from
    the same instrument, domain, regime direction, and analysis slice.
- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD. Use all four because EXP-020
  found every instrument/domain cell reportable.
- **Time range**: Full dataset with nested chronological split. First 70% =
  analysis set; final 30% = global holdout and is never loaded.
- **Global holdout**: The final 30% of each chronologically ordered source file
  must not be loaded, inspected, emitted, plotted, counted, or used in any
  capacity.
- **Look-ahead bias prevention**:
  - event targets are frozen at `trigger_time`;
  - target/trend-change scans start only after the event or control bar;
  - trend-change timestamps come from completed MA(20,50) regime confirmations;
  - controls are selected without using their future target outcomes;
  - all completion scans stop at the analysis-set end.
- **Real-price outcome discipline**: Completion and expectancy outcomes use real
  domain `Close` prices only. This is an event-lifetime component study, not
  strategy P&L; no transaction costs, fills, spreads, stop logic, or position
  sizing are in scope.
- **Exclusions**:
  - fixed-horizon reaction testing, which is EXP-021;
  - cTrader strategy-host screening or frozen-suite candidate qualification;
  - full strategy backtests, optimized exits, stops, pyramiding, risk management,
    or position sizing;
  - alternative AVWAP branches, trend detectors, volume exponents, band
    multipliers, target definitions, or bounce definitions;
  - parameter tuning after reading lifetime outcomes;
  - percentage improvement against a zero baseline.

## Fixed Lifetime and Benchmark Definitions

### Event Lifetime

For each AVWAP bounce event:

1. Start scanning at the first completed domain bar after `trigger_idx`.
2. A favorable completion occurs when `Close` reaches or exceeds the frozen
   favorable target in the event direction.
3. An adverse completion occurs when `Close` reaches or exceeds the frozen
   adverse target in the adverse direction.
4. A trend-change completion occurs when the first opposite MA(20,50) regime is
   confirmed before either target is reached.
5. If none of these happens before the analysis-set end, record `unfinished`.

Intrabar touches do not count. If favorable and adverse targets would both be
crossed by the same completed close, classify by the close-relative condition
that is actually satisfied; exact impossible ties are implementation errors that
must be counted and reported.

### Matched Non-Event Lifetime Analog

Matched controls use the same control-candidate rules as EXP-021:

1. same `regime_id` as the event (which fixes instrument, domain, and regime
   direction);
2. not a bounce trigger;
3. outside a 6-bar exclusion window around any bounce trigger in the same
   instrument/domain cell;
4. computable anchor age;
5. selected by nearest anchor age, then nearest timestamp, up to 5 controls per
   event.

Restricting controls to the event's own regime makes `regime_id` an exact
dependence cluster and keeps the anchor-age match within one AVWAP context.
Events whose own regime cannot supply at least 3 eligible controls are
non-reportable and counted under `insufficient_same_regime_controls`;
reportability thresholds are not relaxed to compensate.

For each event-control pair, convert the event's frozen favorable and adverse
target distances to log-return basis points from the event trigger close, then
apply those distances to the control close in the same direction. This gives the
control a like-for-like target challenge without using future control outcomes or
requiring a new AVWAP target definition at the control bar.

For implementation, with `d = direction`, compute:

- `favorable_bps = d * 10000 * log(event_favorable_target / event_trigger_close)`;
- `adverse_bps = d * 10000 * log(event_adverse_target / event_trigger_close)`;
- `control_favorable_target = control_close * exp(d * favorable_bps / 10000)`;
- `control_adverse_target = control_close * exp(d * adverse_bps / 10000)`.

Valid event targets must produce `favorable_bps > 0` and `adverse_bps < 0`.
Controls must be unique within an event; the same control bar may match multiple
separate events and is handled through event-level clustered uncertainty.

## Success / Failure Criteria

Definitions:

- **Target-completed move**: a move that ends at the favorable or adverse target.
  Trend-change and unfinished moves are reported separately and excluded from the
  favorable-target-rate denominator.
- **Favorable target-completion rate**:
  `favorable_count / (favorable_count + adverse_count)`.
- **Domain rate-difference estimator**: the unweighted mean, across
  lifetime-reportable instruments in the domain, of each instrument's
  (event favorable-target rate minus matched-control favorable-target rate), in
  percentage points. Instruments are equal-weighted so a high-event instrument
  does not dominate the domain claim. The lifetime-expectancy comparison used in
  Evidence FOR/AGAINST is the matching unweighted per-instrument average of the
  event-minus-control bps expectancy difference. When only 3 of 4 instruments are
  reportable, both averages are over those 3.
- **Lifetime expectancy**: direction-signed real-close log return in basis
  points from start close to completion close. Report separately for target
  completions and trend-change completions. Unfinished moves do not have
  realized completion expectancy.
- **Lifetime-reportable domain**: at least 3 of 4 instruments have at least
  30 target-completed event moves and at least 30 target-completed matched-control
  analogs.
- **Zero-denominator behavior**: if `favorable_count + adverse_count == 0`, the
  favorable-target rate is null/non-reportable, never 0. Rate differences are
  reported in percentage points, not as percentage improvement.

- **Evidence FOR**: all of the following:
  - EXP-020 dependency gate passes;
  - at least one lifetime-reportable domain has an event favorable-target rate
    higher than its matched-control rate;
  - the 95% regime-cluster bootstrap CI lower bound for that domain's rate
    difference is above 0 percentage points;
  - the primary domain-level permutation p-value remains `<= 0.05` after Holm
    adjustment across the three domains;
  - event lifetime expectancy is not worse than matched controls in that domain
    on the point estimate.
- **Evidence AGAINST**: any of the following:
  - EXP-020 dependency gate fails;
  - no domain is lifetime-reportable;
  - every lifetime-reportable domain has a favorable-rate-difference CI upper
    bound `<= 0 percentage points`;
  - event lifetime expectancy is worse than matched controls in every
    lifetime-reportable domain.
- **Inconclusive**:
  - no domain meets Evidence FOR, but at least one reportable domain's primary
    CI spans 0 percentage points;
  - target-completed denominators are too sparse after trend-change and
    unfinished outcomes are separated;
  - more than 50% of event moves are unfinished in every lifetime-reportable
    domain;
  - favorable-rate and expectancy evidence point in opposite directions;
  - a domain otherwise meets Evidence FOR, but the median matched-pair
    volatility-context ratio (`control_localvol_bps / event_localvol_bps`,
    20-bar MAD of typical-price log returns) falls outside `[0.5, 2.0]`,
    indicating the control faced the event's frozen target geometry under a
    materially different local volatility; such a domain is
    `volatility-context-confounded` and inconclusive.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 5
- Max new code modules: 1 experiment-local helper module if needed; no shared
  `python/src/xen/` changes unless governance explicitly approves them.

## Data Requirements

Required upstream artifacts:

- `python/experiments/EXP-020/results/run_metadata.json`
- `python/experiments/EXP-020/results/avwap_events.csv`
- `python/experiments/EXP-020/results/avwap_state_summary.csv`
- `python/experiments/EXP-020/results/domain_readiness.csv`
- `python/experiments/EXP-020/results/invariant_checks.csv`
- `python/experiments/EXP-020/results/determinism_check.csv`

EXP-022 must rebuild domain OHLC bars from the first 70% chronological source
slice so all completion outcomes are measured on real prices and never reach the
global holdout. Event rows must be joined back to domain bars by
`instrument`, `domain`, `trigger_idx`, and `trigger_time`, with hard failures
for timestamp or close mismatches.

Primary expected outputs:

- `lifetime_observations.csv` - event and matched-control lifetime records;
- `lifetime_completion_summary.csv` - outcome counts by instrument, domain,
  direction, and `is_pyramid_bounce`;
- `domain_lifetime_tests.csv` - domain-level favorable-rate and expectancy
  comparisons, CIs, p-values, and Holm-adjusted decisions;
- `control_lifetime_diagnostics.csv` - matching counts, target-distance
  diagnostics, volatility-context ratio columns, trend-change counts, unfinished
  counts, and non-reportable reasons (including
  `insufficient_same_regime_controls`);
- `run_metadata.json`.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)
bars = scan.slice(0, analysis_cutoff).collect()
```

## Suggested Direction

Treat EXP-022 as the original AVWAP lifetime-method test, not as an optimized
exit study. The primary comparison is event favorable target-completion rate
against the matched non-event lifetime analog. Trend-change, unfinished, time to
completion, expectancy, direction, and `is_pyramid_bounce` splits explain the
mechanism but must not be used to tune targets or select a variant after
outcomes are known.
