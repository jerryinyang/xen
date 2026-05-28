# Experiment: EXP-030 - 15-Minute Sweep Reversal Behavior

## Hypothesis

First-touch PDH/PDL and ONH/ONL failed-breakout sweeps detected on synthetic 15-minute bars show a measurably different or stronger opposite-direction 60-minute behavior versus non-failed breaches than the EXP-015 1-minute baseline, on at least one of four instruments, using real 1-minute time-bar prices for all outcome evaluation.

## Question

Does PDH/PDL/ONH/ONL sweep reversal behavior at 15-minute resolution show a different or stronger failed-breakout pattern than the EXP-015 1-minute baseline?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/` aggregated into synthetic 15-minute OHLC bars for sweep/breach detection; real 1-minute time bars retained for outcome evaluation. PDH/PDL/ONH/ONL levels inherited from EXP-014 (daily levels are resolution-independent). No Line Break, Renko, or Heiken Ashi inputs.
- **Parameters**: Aggregation is deterministic clock-aligned OHLC resampling (first Open, max High, min Low, last Close, summed TickVolume) over contiguous non-overlapping 15-bar windows; partial trailing windows are dropped. Sweep definitions inherit the EXP-015 framework adapted to 15-minute bar close and body logic: bearish high sweep when 15-minute `High > level + buffer` AND 15-minute `Close < level`; bullish low sweep when 15-minute `Low < level - buffer` AND 15-minute `Close > level`; breach is the inverted close condition (close beyond the level). Buffer is `max(price_precision_step, 0.05 * ATR_14_15m)` where `price_precision_step` follows the EXP-015 convention and `ATR_14_15m` is recomputed on 15-minute bars. First-touch policy: only the first 15-minute event in either direction against each daily level is retained per session. Horizons: 30, 60, 120 minutes of executable wall-clock time measured on the 1-minute series starting at the close of the confirming 15-minute candle. Stop is the sweep extreme plus/minus the same `buffer`. Initial risk is the absolute distance from the confirming 15-minute close to the stop, evaluated in 1-minute price units.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage and EXP-014 level reproducibility.
- **Time range**: Full dataset with nested chronological split applied to the 1-minute series before aggregation. First 70% of the 1-minute series = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used. The 15-minute series is generated only from the analysis-set 1-minute slice.
- **Global holdout**: The final 30% of each chronologically ordered 1-minute instrument dataset is excluded before any aggregation. The full 1-minute dataset must not be aggregated and re-split.
- **Look-ahead bias prevention**: 15-minute aggregation uses only completed 1-minute bars. Sweep and breach events are identified using only 15-minute bars with `CloseTime` at or before the event timestamp. Outcomes use only 1-minute bars with `CloseTime` strictly after the confirming 15-minute candle close; no 1-minute movement inside the confirming 15-minute signal candle is used for outcome paths.
- **Real-price outcome discipline**: All 1R-before-stop probabilities, MAE, MFE, return, and stop-hit outcomes are evaluated on real 1-minute time-bar OHLC prices aligned by `CloseTime`. The 15-minute view supplies only detection. No synthetic chart prices are used for any outcome.
- **Exclusions**: No full ICT model, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data, no premium/discount filter, no macro-window filter, no displacement filter, no IFVG/breaker filter, no exit-rule optimization, no buffer tuning against outcomes, no horizon selection by performance, no 1-hour or other timeframes.

## Success / Failure Criteria

- **Evidence FOR**: 15-minute failed-sweep events improve the primary outcome (1R-before-stop probability at 60 minutes of post-confirmation executable time) versus 15-minute non-failed breaches with a bootstrap CI for the difference excluding zero on at least 1 instrument that did not already show the same effect at 1-minute in EXP-015, with `>= 100` failed-sweep events per train/test segment for that instrument, OR the same EURUSD partial positive replicates with a tighter or stronger interval at 15-minute. The reflection consumes the magnitude and sign per instrument rather than a simple count.
- **Evidence AGAINST**: 15-minute failed-sweep events fail to outperform breaches (bootstrap CI for the difference includes zero) on all 4 instruments, OR the EURUSD partial 1-minute positive disappears at 15-minute with a CI clearly including zero.
- **Inconclusive**: Event counts fall below `>= 100` failed-sweep events per train/test segment on at least 3 of 4 instruments at 15-minute resolution, OR results are mixed in a pattern that does not match either the FOR or AGAINST criteria above. Underpowered comparisons must be classified as inconclusive before direction is interpreted.

## Prerequisites and Sequencing

Requires EXP-014 level reproducibility and the EXP-015 sweep definitional framework, both inherited unchanged at the conceptual level and adapted only to 15-minute bar close and body logic. This is one of three Phase 004A pre-phase experiments. EXP-030 may run independently of EXP-029 and EXP-031; the Phase 004A reflection consumes the combined results.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 4
- Max new code modules: 1

The one new module is shared with EXP-029: `python/src/bar_aggregator.py` for deterministic 15-minute OHLC resampling. If `bar_aggregator.py` was already created and approved in EXP-029, EXP-030 reuses it without modification and creates zero new modules.

## Data Requirements

For each instrument, load the 1-minute time-bar Parquet lazily, sort by `CloseTime`, slice the first 70 percent chronologically as the analysis set, then aggregate the analysis-set 1-minute bars into synthetic 15-minute bars via `bar_aggregator.py`. Load EXP-014 reproducible PDH/PDL/ONH/ONL daily levels for the analysis-set date range. Apply the nested train/test 70/30 split inside the analysis set on the 15-minute series. Detect sweep and breach events on the 15-minute series with the first-touch policy. For each event, evaluate outcome paths on the post-confirmation 1-minute series.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

bars = (
    pl.scan_parquet(path)
    .sort("CloseTime")
    .collect()
)
```

## Suggested Direction

Report event counts before any outcome difference. If 15-minute counts collapse below the 100-event floor on most instruments, classify the comparison as underpowered explicitly before interpreting direction. The reflection needs to know whether a null finding is selectivity or sample-size collapse.
