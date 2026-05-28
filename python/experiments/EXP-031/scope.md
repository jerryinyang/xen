# Experiment: EXP-031 - 15-Minute USTEC Breaker Chain

## Hypothesis

On USTEC, the EXP-022 Candidate A breaker confirmation applied to sweep-plus-displacement events detected on synthetic 15-minute bars improves trade-quality expectancy versus the same-timeframe displacement-only baseline at a magnitude comparable to or stronger than the EXP-023 1-minute USTEC point estimate, using real 1-minute time-bar prices for all outcome evaluation.

## Question

Does the USTEC Phase 003 Candidate A breaker positive replicate at 15-minute bar resolution, or was it a 1-minute resolution artifact?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/` aggregated into synthetic 15-minute OHLC bars for the full sweep-displacement-breaker detection chain; real 1-minute time bars retained for outcome evaluation. PDH/PDL/ONH/ONL levels inherited from EXP-014. No Line Break, Renko, or Heiken Ashi inputs.
- **Parameters**: Aggregation is deterministic clock-aligned OHLC resampling (first Open, max High, min Low, last Close, summed TickVolume) over contiguous non-overlapping 15-bar windows; partial trailing windows are dropped. Sweep, displacement, and Candidate A breaker definitions are inherited from EXP-015, EXP-018, and EXP-022 respectively and adapted only to 15-minute bar close and body logic. Sweep buffer is `max(price_precision_step, 0.05 * ATR_14_15m)`. First-touch sweep policy is preserved. Displacement is the EXP-018 definition computed on 15-minute bars. Candidate A breaker is the EXP-022 last-opposite-candle/order-block proxy applied to the 15-minute candle sequence after a displacement event. Canonical entry timestamp is the displacement-close at 15-minute resolution (matches EXP-023's canonical entry inherited at the lower timeframe). The pre-breaker baseline is the displacement-only 15-minute event set (the same family EXP-023 used at 1-minute). Stops, targets, and risk denominators follow EXP-023's inherited-stop convention: stops are inherited from the EXP-015 sweep, and any breaker entry whose inherited risk falls below the original sweep `Buffer` is marked risk-infeasible and excluded from R-based outcome and bootstrap summaries while retained in retention diagnostics. Reported outcome metrics are expectancy in R, average R, drawdown proxy, win rate, MAE, trade count, and 60-minute forward log return.
- **Instruments**: USTEC only, matching the Phase 003 USTEC-only positive from EXP-023.
- **Time range**: Full dataset with nested chronological split applied to the 1-minute series before aggregation. First 70% of the 1-minute series = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used. The 15-minute series is generated only from the analysis-set 1-minute slice.
- **Global holdout**: The final 30% of the chronologically ordered 1-minute USTEC dataset is excluded before any aggregation. The full 1-minute dataset must not be aggregated and re-split.
- **Look-ahead bias prevention**: 15-minute aggregation uses only completed 1-minute bars. Sweep, displacement, and breaker events are identified using only 15-minute bars with `CloseTime` at or before the event timestamp. Outcomes use only 1-minute bars with `CloseTime` strictly after the confirming 15-minute candle close; no 1-minute movement inside the confirming 15-minute signal candle is used for outcome paths.
- **Real-price outcome discipline**: All expectancy, average R, drawdown proxy, win rate, MAE, return, and stop-hit outcomes are evaluated on real 1-minute time-bar OHLC prices aligned by `CloseTime`. The 15-minute view supplies only detection.
- **Exclusions**: No full ICT model, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data, no second-candle-open as primary entry, no premium/discount filter, no macro-window filter, no IFVG filter (Branch B-only), no Candidate B breaker (refuted in EXP-022 train/test floors), no buffer or displacement tuning against outcomes, no segmentation by time/direction/session/regime (reserved for EXP-032), no proxy-cost stress (reserved for EXP-034), no instruments other than USTEC.

## Success / Failure Criteria

- **Evidence FOR**: Candidate A breaker improves train-and-test expectancy versus the displacement-only baseline on USTEC with a paired bootstrap CI for the expectancy difference excluding zero on the test segment, AND `>= 50` risk-feasible breaker-confirmed events on each of train and test, AND the test-segment point estimate is within `+/- 50` percent of the EXP-023 1-minute USTEC point estimate or stronger in the same direction. The reflection consumes the magnitude and CI per segment rather than a binary outcome.
- **Evidence AGAINST**: The expectancy difference CI includes zero on the test segment, OR the point estimate reverses sign versus the EXP-023 1-minute USTEC result, AND counts are adequate (`>= 50` risk-feasible breaker-confirmed events on test). This refutes the resolution-stability claim and tells the reflection to close or reframe Branch A.
- **Inconclusive**: Risk-feasible breaker-confirmed events on train or test fall below `>= 50`, classified as underpowered before direction is interpreted, OR retention diagnostics show that the 15-minute breaker chain retains fewer than 30 percent of the displacement events that EXP-023 retained at 1-minute, which the reflection records as a resolution-cost limitation per the design.md's "event count gate" rule.

## Prerequisites and Sequencing

Requires EXP-014 level reproducibility, EXP-015 sweep framework, EXP-018 displacement definition, and EXP-022 Candidate A breaker definition, all inherited unchanged at the conceptual level and adapted only to 15-minute bar close and body logic. Inherits the EXP-023 inherited-stop convention and canonical displacement-close entry timing. This is one of three Phase 004A pre-phase experiments and must complete before any Phase 004B branch scope is written. The Phase 004A reflection uses EXP-031 alongside EXP-029 and EXP-030 to issue branch-specific directives.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 4
- Max new code modules: 1

The one new module is shared with EXP-029 and EXP-030: `python/src/bar_aggregator.py` for deterministic 15-minute OHLC resampling. If `bar_aggregator.py` was already created and approved in EXP-029 or EXP-030, EXP-031 reuses it without modification and creates zero new modules. A small new helper for the EXP-022 breaker on 15-minute bars (`python/src/ict_timebar.py` extension or a new `ict_breaker_15m.py`) may be added if the existing 1-minute helper cannot accept the 15-minute frame cleanly; this is in scope only if reuse is not feasible.

## Data Requirements

Load the USTEC 1-minute time-bar Parquet lazily, sort by `CloseTime`, slice the first 70 percent chronologically as the analysis set, then aggregate the analysis-set 1-minute bars into synthetic 15-minute bars via `bar_aggregator.py`. Load EXP-014 reproducible PDH/PDL/ONH/ONL daily levels for the analysis-set date range. Apply the nested train/test 70/30 split inside the analysis set on the 15-minute series. Detect the sweep-displacement-breaker chain on the 15-minute series. For each event, evaluate outcome paths on the post-confirmation 1-minute series using the inherited EXP-015 stop and EXP-023 risk-feasibility convention.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*USTEC*.parquet"))[-1]

bars = (
    pl.scan_parquet(path)
    .sort("CloseTime")
    .collect()
)
```

## Suggested Direction

Run the event-count waterfall (sweep -> displacement -> Candidate A breaker -> risk-feasible) before any outcome difference. If risk-feasible breaker counts collapse below the 50-event floor on train or test, classify the comparison as underpowered explicitly before interpreting direction. The reflection needs to distinguish a true 15-minute null from a sample-size collapse.
