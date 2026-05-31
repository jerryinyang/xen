# Experiment: EXP-037 - Null Calibration of Frozen Reference Stack

## Hypothesis

The frozen EXP-036 reference stack can be calibrated under a dependence-preserving null: after the Prior-Range Location descriptor stream is decoupled from the return/control stream while preserving each stream's relevant dependence structure, EXP-037 can estimate the stack's empirical full-stack false-positive rate and per-leg false-pass profile on the second-order calibration holdout for at least one predeclared null block length.

## Question

Under the frozen Part A null construction in `docs/experiments-docs/checkpoints/2026-05-31-006-thesis-qualification-referee-calibration/reference-stack-spec.md`, what is the EXP-036 reference stack's empirical false-positive rate at kappa = 0, and which evidentiary legs leak or over-reject?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`, holdout-excluded before any aggregation; strict clock-aligned `1h` and `4h` real OHLC bars via `python/src/bar_aggregator.aggregate_ohlc`; Prior-Range Location bucket/direction stream transcribed from EXP-036; next-bar and 4-bar real-return/control stream transcribed from EXP-036.
- **Reference stack**: The frozen EXP-036 stack described in `reference-stack-spec.md`: admissibility layer fixed, evidentiary floors, neutral baseline, matched control, episode bootstrap, train/test sign preservation, k = 2 distinct instruments, secondary 4-bar horizon, and verdict ladder. No threshold, leg, or admissibility rule may change.
- **Parameters**:
  - Instruments: EURUSD, XAUUSD, BTCUSD, USTEC.
  - Timeframes: `1h` (60 minutes) and `4h` (240 minutes), strict aggregation only (`min_coverage=None`).
  - Prior-range lookback: 20 completed same-timeframe bars.
  - Buckets: bottom `<= 0.20`, middle `(0.20, 0.80)`, top `>= 0.80`; direction `d = +1` for top, `d = -1` for bottom, `d = 0` for middle.
  - Train/test split: 70/30 chronological split inside the holdout-excluded analysis set, after strict aggregation.
  - Return horizons: next-bar primary and fixed 4-bar secondary, both from aggregated real OHLC only.
  - Inference: episode bootstrap, B = 10,000, seed 42 with deterministic offsets, 95% empirical CIs, 2,000,000 index-cell cap.
  - Representation floors: rows >= 100 train / >= 50 test; episodes >= 30 train / >= 15 test.
  - Null return-stream mean block lengths: L in `{20, 60, 240}` bars.
  - Part A null realizations: 150 full-stack equivalents per block length unless the predeclared compute profile downscale is triggered.
  - Calibration battery partition: even seed indices = development battery; odd seed indices = second-order holdout. Trusted operating characteristics come only from odd seed indices.
- **Null construction**:
  - Descriptor stream `(Bucket, D)` is resampled independently in complete state-episode blocks within each instrument/timeframe/segment, preserving descriptor run structure.
  - Return/control stream `(RetNextBar, RetFourBar, Control)` is resampled in circular/stationary time blocks with common block starts across instruments for each timeframe/segment/block length, preserving serial dependence, volatility clustering, calendar/session structure as represented by the aggregated rows, and cross-instrument return correlation.
  - Descriptor and return/control RNG streams are independent, so the state-to-return conditioning relationship is broken.
- **Time range**: Full available dataset per instrument with the nested chronological split. The first 70% of each CloseTime-sorted 1-minute series is the analysis set. The final 30% global holdout is never loaded, inspected, aggregated, resampled, or used.
- **Global holdout**: Excluded before aggregation, feature construction, null resampling, diagnostics, plotting, and output generation.
- **Look-ahead bias prevention**: Prior-Range Location at bar `i` uses only completed bars through `i`; executable returns start at the next same-segment bar. Resampling pairs already-causal descriptor observations with resampled return/control observations and never uses future information to form a descriptor.
- **Real-price outcome discipline**: All measured returns use aggregated real OHLC. No Heiken Ashi, Renko, or other synthetic chart prices are in scope.
- **Exclusions**:
  - No Stage B power calibration, no planted synthetic effects, no MDE estimate, and no H0/H1 founding-thesis ruling.
  - No successor-stack design, no threshold loosening, no gate removal, and no alternative referee.
  - No re-run, re-score, or rescue of any closed trading thesis.
  - No transaction-cost, slippage, spread, or materiality-survival gate in the frozen-stack FPR. Proxy costs remain frozen in the reference spec for later power reporting but are not applied to the EXP-037 kappa = 0 stack verdict.
  - No tolerant aggregation, no timeframe sweep, no bucket/lookback variation, and no descriptor other than the frozen Prior-Range Location stream.
  - Naive row shuffles are diagnostic-only if emitted; they cannot contribute to trusted FPR.

## Success / Failure Criteria

- **Evidence FOR measurement success**: At least one block length L has second-order-holdout null realizations whose diagnostics pass the predeclared validity gates, and EXP-037 emits a complete trusted FPR and per-leg false-pass profile for that L. This does not mean the stack is good or bad; it means the trustworthy null-calibration half is measured for at least one valid L.
- **Evidence AGAINST measurement validity**: No block length L has trusted second-order-holdout realizations passing null-validity diagnostics, or the predeclared compute profile/downscale rule stops the run before long execution. In that case EXP-037 reports null-calibration invalidity or compute infeasibility rather than an FPR.
- **Inconclusive**: Some diagnostics pass only on the development battery, pass on too few trusted realizations for stable rates, or produce inconsistent validity across instruments/timeframes such that the FPR envelope is labelled partial rather than trustworthy.

### Metric Denominators and Zero-Baseline Behavior

- **Trusted realization denominator**: odd seed-index realizations for a block length whose null-validity diagnostics pass. Development-battery estimates are labelled in-sample.
- **Full-stack FPR numerator**: trusted valid realizations where the unchanged frozen verdict ladder emits `FOR` on the next-bar primary. Denominator = trusted valid realizations for that block length.
- **Verdict-ladder rates**: rates of `FOR`, `STATE_DIFFERENTIATION_ONLY`, `HORIZON_DEPENDENT`, `INCONCLUSIVE`, and `AGAINST` over the same trusted valid realization denominator.
- **Representation/adjudicability rates**: denominator = scoped cells where a leg could be assessed; numerator = cells meeting the relevant floor/adjudicability condition. Report by block length, battery partition, segment, horizon, contrast, instrument, and timeframe where useful.
- **Cell-level false-pass rates**: denominator = adjudicable instrument/timeframe/horizon/contrast cells; numerator = cells where test CI lower bound > 0 and train point estimate > 0 under the null.
- **Both-contrast cell pass rate**: denominator = adjudicable instrument/timeframe/horizon cells for both neutral and control; numerator = cells where both contrasts false-pass in the same cell.
- **Aggregate E5/E6 false-pass rate**: denominator = trusted valid full-stack realizations; numerator = realizations reaching the k = 2 distinct-instrument replication conjunction for the named leg/horizon.
- Any denominator of zero is reported as undefined/null, never as 0%, 100%, or a percentage improvement.

## Null-Validity Diagnostics

Before an FPR is trusted, EXP-037 reports diagnostics for each block length:

- descriptor episode count within +/-5% of observed;
- descriptor median and p90 episode length within +/-10% of observed;
- return lag-1 and lag-5 autocorrelation signs unchanged per instrument/timeframe;
- cross-instrument return-correlation matrix Frobenius distance <= 0.20 versus observed per timeframe.

A descriptor diagnostic failure invalidates trusted FPR for the affected block length. A return diagnostic failure labels that block length's FPR untrusted. The headline output is the FPR envelope across valid block lengths only.

## Complexity Budget

- Max statistical test families: 3.
  1. Null-validity diagnostics.
  2. Empirical false-pass/FPR rate estimates by block length and battery partition.
  3. Wilson intervals for realization-level rates.
- Max visualisations: 4.
- Max new code modules: 1 (`python/src/referee_calibration.py`), because EXP-037 creates the shared calibration harness reused by Stage B.

## Data Requirements

1. Load only the holdout-excluded first 70% of CloseTime-sorted 1-minute bars for each instrument.
2. Strict-aggregate to 60- and 240-minute OHLC.
3. Construct the frozen Prior-Range Location descriptor stream and executable return/control stream exactly as EXP-036.
4. Build observed diagnostics before null resampling.
5. For each block length and seed, generate a null realization by independently resampling descriptor and return/control streams, then run the unchanged frozen stack.
6. Emit machine-readable outputs under `python/experiments/EXP-037/results/` and bounded plots under `python/experiments/EXP-037/plots/`.

### Standard Loading Pattern

```python
from pathlib import Path

from ict_timebar import INSTRUMENTS, load_analysis_timebars
from bar_aggregator import aggregate_ohlc

DATA_DIR = Path("data")

for instrument in INSTRUMENTS:
    loaded = load_analysis_timebars(DATA_DIR, instrument)  # first 70% only
    bars_1m = loaded.frame
    bars_1h = aggregate_ohlc(bars_1m, period_minutes=60, min_coverage=None)
```

## Suggested Direction

Build a reusable calibration harness around the EXP-036 stack rather than rewriting an independent referee. Keep the run outputs layered: profile first, observed-stack baseline, null-validity diagnostics, then FPR/per-leg rates by block length and battery partition. The final interpretation must treat null calibration as the trustworthy half only when diagnostics pass; it must not make any power, MDE, or successor-stack claim.
