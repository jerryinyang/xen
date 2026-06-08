# Experiment: EXP-021 - AVWAP Bounce Reaction Study

## Hypothesis

AVWAP bounce events from the supported CF-AVWAP-001 first branch show better
fixed-horizon direction-signed real-price reaction than matched non-event
controls on at least one EXP-020 ready domain, without touching the global
holdout.

## Question

After a registered AVWAP bounce triggers, do real domain closes move farther in
the bounce direction over a fixed short horizon than comparable non-event bars
from the same instrument, domain, and regime direction?

## Scope Boundaries

- **Data Views**: EXP-020 `avwap_events.csv` plus 5m, 1h, and 4h domain OHLC
  bars rebuilt from 1-minute time bars after the first-70% analysis slice is
  applied. No chart-type views are in scope.
- **Candidate family**: `CF-AVWAP-001/HYP-002`, first branch only, as registered
  in `docs/signal-registry/candidate-families/avwap.md`.
- **Dependency gate**: EXP-020 must have `SUPPORTED_FULL` status, zero invariant
  failures, deterministic replay match, and ready domains `{5m, 1h, 4h}`. If
  EXP-020 artifacts are missing or fail these checks, EXP-021 is blocked.
- **Parameters**:
  - domain bars: 5m strict coverage; 1h and 4h `min_coverage=0.90`;
  - AVWAP branch: MA(20,50) regime detector, typical price, `TickVolume ** 0.75`,
    MAD band multiplier 1.0, and EXP-020 bounce definition unchanged;
  - fixed horizons: 1, 3, and 6 completed domain bars after trigger;
  - primary confirmatory horizon: 3 completed domain bars;
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
  - event definitions and regime intervals come from the EXP-020
    look-ahead-safe substrate;
  - domain bars are ordered by `CloseTime`;
  - event construction uses only information available at or before
    `trigger_time`;
  - future closes are used only as measured outcomes;
  - controls are selected using timestamp, regime direction, anchor age, and
    non-event status only, never future returns.
- **Real-price outcome discipline**: Reaction outcomes use real domain `Close`
  prices only. The primary return is direction-signed log return in basis points:
  `10000 * direction * log(Close[t+h] / Close[t])`. This is not strategy P&L;
  no transaction costs, stops, targets, fills, spreads, or position sizing are in
  scope.
- **Exclusions**:
  - cTrader strategy-host screening or frozen-suite candidate qualification;
  - lifetime target/trend-change outcomes, which are EXP-022;
  - full strategy backtests, exits, stops, pyramiding, risk management, or
    position sizing;
  - alternative AVWAP branches, trend detectors, volume exponents, band
    multipliers, or bounce definitions;
  - parameter tuning or horizon selection after reading outcomes;
  - percentage improvement against a zero baseline.

## Fixed Control Definition

For each instrument/domain/direction cell, candidate controls are completed
domain bars that:

1. fall inside the same EXP-020 regime interval (`regime_id`) as the event (same
   instrument, domain, and regime direction by construction);
2. are not AVWAP bounce trigger bars;
3. are not within 6 completed domain bars of any AVWAP bounce trigger in the
   same instrument/domain cell;
4. have enough future completed bars inside the analysis set for the horizon
   being evaluated;
5. have a computable control anchor age from the EXP-020 regime summary.

For each event, select up to 5 controls from the candidate set by deterministic
nearest matching on anchor age first and timestamp second. If fewer than 3
controls are available for the primary 3-bar horizon, that event is
non-reportable for the primary matched test but still counted in denominator
diagnostics. Controls must be unique within an event; the same control bar may
match multiple separate events and is handled through event-level clustered
uncertainty.

Restricting controls to the event's own regime makes `regime_id` an exact
dependence cluster (no control is shared across regimes) and keeps anchor-age
matching within one AVWAP context. Events whose own regime cannot supply at
least 3 eligible controls at the primary horizon are non-reportable for the
matched test and counted under the reason code
`insufficient_same_regime_controls`; reportability thresholds are not relaxed to
compensate.

## Success / Failure Criteria

Definitions:

- **Reportable matched event**: an event with a valid future close for the
  horizon and at least 3 matched non-event controls for that horizon.
- **Reaction-reportable instrument/domain cell**: at least 30 reportable matched
  events at the primary horizon, with at least 8 bullish and 8 bearish events.
- **Reaction-reportable domain**: at least 3 of 4 instruments are
  reaction-reportable at the primary horizon.
- **Primary effect (domain estimator)**: the unweighted mean, across
  reaction-reportable instruments in the domain, of each instrument's
  event-weighted mean direction-signed paired difference (event return minus
  matched-control mean return) at the 3-bar horizon, in basis points.
  Instruments are equal-weighted so no single high-volatility, high-count
  instrument dominates the domain claim; per-instrument effects are reported
  alongside. When only 3 of 4 instruments are reportable, the average is over
  those 3.
- **Zero-baseline behavior**: the null advantage is exactly 0 bps. Report
  absolute bps differences and confidence intervals; do not compute percentage
  improvement when the control mean is zero or near zero.

- **Evidence FOR**: all of the following:
  - EXP-020 dependency gate passes;
  - at least one reaction-reportable domain has primary effect greater than
    0 bps;
  - the 95% regime-cluster bootstrap CI lower bound for that domain's primary
    effect is above 0 bps;
  - the primary domain-level permutation p-value remains `<= 0.05` after
    Holm adjustment across the three domains.
- **Evidence AGAINST**: any of the following:
  - EXP-020 dependency gate fails;
  - no domain is reaction-reportable at the primary horizon;
  - every reaction-reportable domain has a primary-effect CI upper bound
    `<= 0 bps`.
- **Inconclusive**:
  - no domain meets Evidence FOR, but at least one reaction-reportable domain's
    primary CI spans 0 bps;
  - matched-control denominators are insufficient after the fixed exclusion
    window;
  - a domain meets the primary Evidence FOR rule, but both secondary horizons
    for that same domain have point estimates `< 0 bps`.

## Complexity Budget

- Max statistical tests: 2
- Max visualisations: 4
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

EXP-021 must rebuild domain OHLC bars from the first 70% chronological source
slice so future-close outcomes are measured on real prices and never reach the
global holdout. Event rows must be joined back to domain bars by
`instrument`, `domain`, `trigger_idx`, and `trigger_time`, with hard failures
for timestamp or close mismatches.

Primary expected outputs:

- `reaction_observations.csv` - event/control matched records by horizon;
- `reaction_summary.csv` - event and control returns by instrument, domain,
  direction, and horizon;
- `domain_reaction_tests.csv` - primary and secondary domain-level effects,
  CIs, p-values, and Holm-adjusted primary decisions;
- `control_match_diagnostics.csv` - event counts, control counts, and
  non-reportable reasons (including `insufficient_same_regime_controls`);
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

Treat this as an event-reaction component study, not as a trading-system screen.
The 3-bar horizon is the confirmatory read; 1-bar and 6-bar horizons are
predeclared stability diagnostics. A favorable EXP-021 result can support
proceeding to the baseline screen only together with EXP-022 or an explicit
governance decision; a negative result refutes only this fixed-horizon reaction
operationalization.
