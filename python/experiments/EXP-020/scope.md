# Experiment: EXP-020 - AVWAP Event-Substrate Readiness

## Hypothesis

The Phase 004 Batch 004-A AVWAP definition can be implemented as a
deterministic, look-ahead-safe event substrate with usable bounce-event coverage
on at least one predeclared domain, without touching the global holdout.

## Question

Can the first-branch AVWAP state machine produce temporally valid anchors,
AVWAP values, bands, and bounce events with enough coverage to justify a
follow-up real-price reaction study?

## Scope Boundaries

- **Data Views**: 1-minute time bars resampled into 5m, 1h, and 4h domain OHLC
  bars. No chart-type views.
- **Candidate family**: `CF-AVWAP-001`, first branch only, as registered in
  `docs/signal-registry/candidate-families/avwap.md`.
- **Parameters**:
  - domain bars: 5m strict coverage; 1h and 4h `min_coverage=0.90`;
  - regime detector: simple MA crossover, fast 20 / slow 50, on domain `Close`;
  - AVWAP source: typical price `(High + Low + Close) / 3`;
  - AVWAP weight: `TickVolume ** 0.75`;
  - band spread: median absolute deviation from the anchored typical-price path;
  - band multiplier: 1.0.
- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD. Use all four because Phase 004
  candidate screening must know whether the event substrate is instrument-wide
  or domain/instrument-specific.
- **Time range**: Full dataset with nested chronological split. First 70% =
  analysis set; final 30% = global holdout and is never loaded.
- **Global holdout**: The final 30% of each chronologically ordered source file
  must not be loaded, inspected, emitted, plotted, counted, or used in any
  capacity.
- **Look-ahead bias prevention**:
  - all ordering uses domain-bar `CloseTime`;
  - MA values use completed domain closes only;
  - regime changes are confirmed only after a completed domain bar;
  - anchors are selected from viable pivots observed before or at the regime
    confirmation timestamp;
  - bounce events may occur only after the confirmation bar and only after the
    opposite-side arming condition has occurred on completed bars.
- **Real-price outcome discipline**: EXP-020 does not compute returns, P&L,
  stops, targets, or excursions. Later reaction or signal metrics must use real
  domain OHLC prices.
- **Exclusions**:
  - market-edge claims;
  - frozen-suite candidate screening;
  - cTrader strategy-host runs;
  - alternative trend detectors;
  - volume exponent sweeps;
  - band multiplier sweeps;
  - exits, stops, targets, pyramiding, risk management, or position sizing;
  - chart-type signals;
  - any parameter change after reading EXP-020 results.

## Fixed Event Definitions

### Regime Detector

- Fast SMA = trailing mean of the last 20 domain closes.
- Slow SMA = trailing mean of the last 50 domain closes.
- Regime = +1 when fast SMA > slow SMA; -1 when fast SMA < slow SMA; 0 during
  warmup or exact ties.
- Initial transition from 0 to +1/-1 establishes the first active regime.
- A confirmed sign change between +1 and -1 resets the active AVWAP anchor.

### Anchor Rule

The state machine tracks viable pivots using completed domain bars only:

- bullish anchor = lowest `Low` observed since the prior active regime start or
  regime change;
- bearish anchor = highest `High` observed since the prior active regime start
  or regime change.

When a bullish regime is confirmed, the active AVWAP anchor is the viable low.
When a bearish regime is confirmed, the active AVWAP anchor is the viable high.
The implementation must maintain enough temporary state to compute the anchored
series from the chosen pivot without using future bars.

### Bounce Rule

- Bullish regime: arm when a completed close is below AVWAP; trigger when a
  later completed close crosses back above AVWAP.
- Bearish regime: arm when a completed close is above AVWAP; trigger when a
  later completed close crosses back below AVWAP.
- Only confirmed closes count. Intrabar touches do not count.
- After a trigger, the event cannot trigger again until it re-arms.

## Success / Failure Criteria

Definitions:

- **Reportable instrument-domain cell**: at least 30 total bounce events, with at
  least 8 bullish-trigger events and at least 8 bearish-trigger events.
- **Ready domain**: at least 3 of 4 instruments are reportable.
- **Invariant failure**: any temporal, anchor, arming, weight, determinism, or
  holdout check fails.

- **Evidence FOR**:
  - all invariant checks pass for every instrument/domain;
  - deterministic replay produces identical event tables and summary hashes;
  - at least one domain is ready.
  - Label `SUPPORTED_FULL` if all three domains are ready; label
    `SUPPORTED_NARROW` if one or two domains are ready.
- **Evidence AGAINST**:
  - any invariant failure;
  - deterministic replay mismatch;
  - no ready domain;
  - any event row at or beyond the first-70% analysis cutoff.
- **Inconclusive**:
  - no invariant failure, but no domain reaches the ready-domain threshold while
    at least one domain has exactly two reportable instruments;
  - severe directional imbalance prevents reportable cells even though total
    event counts are non-zero.

## Complexity Budget

- Max statistical tests: 1 readiness classification table.
- Max visualisations: 4.
- Max new code modules: 1 AVWAP state-machine module, if implementation needs a
  reusable helper under `python/src/xen/`.

## Data Requirements

- Load each source file lazily, sort by `CloseTime`, count rows, and slice only
  the first 70% before any collection.
- Build domain bars with the existing project domain-construction convention.
- Preserve `CloseTime`, `Open`, `High`, `Low`, `Close`, and `TickVolume`.
- Treat missing or non-positive `TickVolume` explicitly:
  - missing volume is an implementation error for this experiment;
  - zero volume is allowed but contributes zero weight and must not create
    division-by-zero output.
- Store event denominators by instrument, domain, and direction.
- Percentage metrics with zero denominators must be reported as null/non-
  reportable, not as zero-percent improvement.
- Store enough event metadata to support later reaction-study scopes without
  regenerating definitions: `regime_id`, `bounce_index_in_regime`, `direction`,
  `anchor_time`, `anchor_price`, `armed_time`, `trigger_time`, `trigger_close`,
  `avwap_at_trigger`, `upper_band_at_trigger`, `lower_band_at_trigger`, and
  `anchor_age_bars`.
- Store the derived lifetime-study fields needed by EXP-022 without computing
  outcomes in EXP-020: `favorable_target_at_trigger`,
  `adverse_target_at_trigger`, and `is_pyramid_bounce` where
  `is_pyramid_bounce` is true for subsequent bounces in the same active regime.

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

Implement the AVWAP state machine sequentially, because the anchor, temporary
cache, arming state, and replay determinism are the object under test. Use
vectorized Polars only for safe source loading, domain construction, and summary
aggregation after event tables are produced.
