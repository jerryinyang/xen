# Experiment: EXP-023 - AVWAP Baseline Candidate Screen

## Hypothesis

The registered CF-AVWAP-001 baseline signal can qualify under at least one
component of the frozen Phase 004 suite - standalone strict, standalone
ratified-loose/fallback, or revised portfolio-fitness against the existing
D-dogfood-book reference - while reporting the original AVWAP strategy metric
book, without touching the global holdout.

## Question

After EXP-020, EXP-021, and EXP-022 supported the baseline AVWAP component
evidence, does the full baseline signal survive the cTrader strategy-host screen
and the frozen qualification suite when evaluated on emitted real OHLC prices?

## Scope Boundaries

- **Data Views**: cTrader `Mode=StrategyHost` output for the baseline AVWAP
  signal, including `positions.parquet`, `events.parquet`,
  `trade_blotter.parquet`, and `run_metadata.json` where available. Fixed
  first-70% source-Parquet smoke output may be used only to validate the C# AVWAP
  port against the Python reference before admitting cTrader-feed runs. No
  chart-type views are in scope.
- **Candidate family**: `CF-AVWAP-001/HYP-004`, first branch only, as registered
  in `docs/signal-registry/candidate-families/avwap.md`.
- **Dependency gate**:
  - EXP-020 must be `SUPPORTED_FULL`, with zero invariant failures,
    deterministic replay match, and ready domains `{5m, 1h, 4h}`;
  - EXP-021 must be `SUPPORTED`;
  - EXP-022 must be `SUPPORTED`;
  - VAL-002 must remain `SUPPORTED (PASS)` for the cTrader strategy-host branch;
  - EXP-012, EXP-018, and EXP-019 must identify the frozen suite components and
    the existing D-dogfood-book reference.
- **Parameters**:
  - domain bars: 5m strict coverage; 1h and 4h `min_coverage=0.90`;
  - instruments: BTCUSD, EURUSD, USTEC, XAUUSD;
  - regime detector: simple MA crossover, fast 20 / slow 50, on domain
    `RealClose`;
  - AVWAP source: typical price `(RealHigh + RealLow + RealClose) / 3`;
  - AVWAP weight: `TickVolume ** 0.75`;
  - band spread: median absolute deviation from the anchored typical-price path;
  - band multiplier: 1.0;
  - bounce trigger and re-arm rule: unchanged from EXP-020.
- **Baseline strategy-position rule**:
  - When the strategy is flat and a completed domain bar confirms an AVWAP
    bounce trigger, emit `Position = direction` at that trigger
    `SourceCloseTime`; the suite evaluates the position on the next completed
    real-close return.
  - Hold one unit in the bounce direction until the registered EXP-022
    completion rule fires: favorable target, adverse target, or opposite
    MA(20,50) regime confirmation on a completed domain close.
  - When completion is confirmed at bar `t`, emit flat `Position = 0` at
    `SourceCloseTime[t]` so no return after the completion close is assigned to
    the completed move.
  - If another bounce appears while a position is active, do not add size and do
    not open a second position; record it as a non-executed pyramid opportunity.
    If a later bounce appears after the prior move completed and the strategy is
    flat, it may open a new one-unit position, with `is_pyramid_bounce` preserved
    as event metadata.
  - If the analysis set ends before completion, record the open move as
    unfinished. Do not force an artificial target or trend-change exit.
- **Reference book for portfolio fitness**: Use the existing D-dogfood-book
  reference from EXP-019: Donchian(20) breakout (`donchian_20`). The reference
  positions must be aligned to the same `SourceCloseTime` and emitted
  `RealClose` return basis as the AVWAP candidate. If an aligned cTrader-emitted
  or otherwise governance-approved same-feed reference artifact is unavailable,
  EXP-023 is blocked rather than silently choosing a new reference book.
- **Time range**: Full available cTrader backtest range, fenced by
  `AnalysisEndUtc` so only the first 70% chronological analysis slice is emitted.
  Within that emitted analysis set, use the required 70/30 chronological
  train/test split for referee evaluation.
- **Global holdout**: The final 30% of each chronologically ordered source file
  must not be loaded, inspected, emitted, plotted, counted, or used in any
  capacity. cTrader strategy-host runs must emit no row at or after
  `AnalysisEndUtc`.
- **Look-ahead bias prevention**:
  - all signal state uses completed domain bars only;
  - MA regimes, viable pivots, AVWAP, bands, arming, triggers, and completions
    use only information available at or before their `SourceCloseTime`;
  - target values are frozen at trigger time;
  - future closes are used only as measured outcomes;
  - Python analysis ingests cTrader-emitted signals and must not regenerate the
    AVWAP candidate signal.
- **Real-price outcome discipline**: Standalone suite returns, incremental
  returns, strategy expectancy, and risk-adjusted metrics use cTrader-emitted
  real OHLC prices only. Synthetic chart prices are not in scope.
- **Exclusions**:
  - alternative AVWAP branches, trend detectors, MA period maps, volume
    exponents, band multipliers, or bounce definitions;
  - parameter tuning or domain/instrument selection after reading EXP-023
    outcomes;
  - Heiken Ashi, Renko, Line Break, Market Bias, ATR-pivot, cross-timeframe, or
    granular-entry variants;
  - unregistered exit overlays, stop optimization, target optimization, trailing
    exits, position sizing, pyramiding, portfolio weighting, or risk management;
  - changing strict, ratified-loose, or revised incremental referee logic;
  - changing the D-dogfood-book reference;
  - execution-realism claims from fills, spread, slippage, order type, or
    latency.

## Metric Denominators and Zero-Baseline Behavior

- **Standalone suite denominator**: chronological next-step real-close return
  rows produced from cTrader-emitted `positions.parquet`; the final emitted bar
  has no forward return and is dropped by the frozen ingestion harness.
- **Trade denominator**: executed one-unit AVWAP entries. Non-executed pyramid
  opportunities are counted separately and do not enter trade-return
  denominators.
- **Completed-move denominator**: executed moves ending at favorable or adverse
  target. Trend-change and unfinished moves are reported separately, matching
  EXP-022 conventions.
- **Incremental denominator**: bars where the clipped combined book
  `clip(R + C, -1, +1)` differs from reference book `R` alone.
- **Raw/traditional return denominator**: same emitted real-close return rows as
  the standalone suite, with `raw_return_bps = 10000 * log(RealClose[t+1] /
  RealClose[t])`.
- **Zero-baseline behavior**: Report absolute bps, rate differences in
  percentage points, and risk-adjusted metric levels/differences. Do not compute
  percentage improvement when a baseline mean, rate denominator, or risk metric
  is zero or near zero. Any zero denominator is null/non-reportable, never a
  zero effect.

## Success / Failure Criteria

Definitions:

- **Admitted cTrader run**: a run with valid schema, frozen parameters, non-empty
  chronological positions, emitted real OHLC columns, and every
  `SourceCloseTime < AnalysisEndUtc`.
- **Reportable suite cell**: one admitted AVWAP candidate run for an
  instrument/domain, an aligned reference position series for portfolio fitness,
  finite standalone and incremental denominators, and no dependency or holdout
  violation.
- **Suite pass**: any of the following on a reportable instrument/domain cell:
  - strict standalone gate stack `PASS`;
  - effective ratified-loose-or-strict-fallback standalone referee `PASS`;
  - revised portfolio-fitness unit `POSITIVE_INCREMENTAL` against the
    D-dogfood-book reference.

- **Evidence FOR**:
  - all dependency gates pass;
  - all 12 instrument/domain AVWAP cTrader runs are admitted;
  - the D-dogfood-book reference is aligned on the same emitted return basis;
  - at least one reportable instrument/domain cell has a suite pass;
  - the original metric book is produced with finite, non-missing strategy
    expectancy and raw-return risk-adjusted comparison for every reportable cell.
  - Label the support path as `SUPPORTED_STANDALONE`,
    `SUPPORTED_INCREMENTAL`, or `SUPPORTED_MIXED`.
- **Evidence AGAINST**:
  - all dependencies and run-admission checks pass;
  - no reportable instrument/domain cell passes any suite component;
  - standalone candidate effects and incremental effects are below their frozen
    domain detection floors in every reportable cell.
- **Inconclusive / blocked**:
  - any dependency gate is missing, incomplete, or contradicted;
  - cTrader AVWAP runs cannot be admitted for at least 3 of 4 instruments in
    every domain;
  - the aligned D-dogfood-book reference is unavailable;
  - suite evaluation cannot run without changing sample membership,
    denominators, cost logic, or referee logic;
  - metric-book denominators are too sparse or non-finite even though the suite
    can run;
  - cTrader/Python fixed-Parquet smoke validation fails for the AVWAP port.

## Complexity Budget

- Max statistical tests: 4
- Max visualisations: 5
- Max new code modules: 3
  - C# AVWAP strategy-host model/adapter;
  - C# or emitted-reference path for Donchian(20) aligned to the same return
    basis;
  - one experiment-local Python screening/summary harness.

## Data Requirements

Required upstream artifacts:

- `python/experiments/EXP-020/results/run_metadata.json`
- `python/experiments/EXP-020/results/avwap_events.csv`
- `python/experiments/EXP-020/results/avwap_state_summary.csv`
- `python/experiments/EXP-021/results.md`
- `python/experiments/EXP-022/results.md`
- `python/experiments/EXP-003/results/mde_summary.csv`
- `python/experiments/EXP-012/results/adoption_decisions.csv`
- `python/experiments/EXP-012/results/fresh_mde_summary.csv`
- `python/experiments/EXP-018/results/domain_mde_summary.csv`
- `python/experiments/EXP-019/inputs/dogfood_reference_book_manifest.json`
- cTrader strategy-host run directories for every scoped instrument/domain.

Required EXP-023 outputs:

- `run_manifest.csv` - admitted cTrader run paths, parameters, row counts, and
  holdout-fence checks;
- `suite_manifest.csv` - strict, ratified-loose/fallback, and revised
  incremental settings by domain;
- `standalone_suite_verdicts.csv` - strict and ratified-loose/fallback rows;
- `portfolio_fitness_verdicts.csv` - revised incremental rows against
  Donchian(20);
- `strategy_metric_book.csv` - prevalence, executed trade counts, completed
  move rates, expectancy, raw-return risk metrics, and split diagnostics;
- `event_trade_diagnostics.csv` - event, entry, exit, unfinished, trend-change,
  and non-executed pyramid counts;
- `run_metadata.json`.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

run_dir = Path("data/strategy_runs/<avwap_baseline_run>")
positions = pl.scan_parquet(run_dir / "positions.parquet").sort("SourceCloseTime")
max_time = positions.select(pl.col("SourceCloseTime").max()).collect().item()
# assert max_time < AnalysisEndUtc before collecting any reportable data
```

## Suggested Direction

Treat EXP-023 as a candidate screen, not a tuning or strategy-improvement
experiment. First admit cTrader outputs and the aligned Donchian reference, then
run the frozen suite unchanged, then report the registered metric book. Any
failure is a valid Phase 004 result and does not authorize changing AVWAP
parameters inside this experiment.
