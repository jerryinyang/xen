# Experiment: EXP-029 - 15-Minute FVG IFVG Selectivity Check

## Hypothesis

Applying the EXP-020 three-candle FVG and 120-bar close-through IFVG rules without modification to synthetic 15-minute bars produces an IFVG inversion rate materially below the Phase 003 1-minute baseline of 84-85 percent on at least two of four instruments, while preserving FVG and IFVG event counts adequate for downstream selectivity testing.

## Question

Does the existing IFVG detector become materially less tautological at 15-minute resolution, and does FVG/IFVG event coverage remain adequate for downstream entry-quality testing?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/` aggregated into synthetic 15-minute OHLC bars; no Line Break, Renko, or Heiken Ashi inputs.
- **Parameters**: Aggregation is deterministic clock-aligned OHLC resampling (first Open, max High, min Low, last Close, summed TickVolume) over contiguous non-overlapping 15-bar windows aligned to clock boundaries; partial trailing windows are dropped. FVG and IFVG rules are inherited unchanged from EXP-020: bearish FVG `High[i] < Low[i-2]`; bullish FVG `Low[i] > High[i-2]`; FVG size must be at least `max(price_precision_step, 0.02 * ATR_14)` using the EXP-015 price precision convention with ATR_14 recomputed on 15-minute bars; IFVG requires a later close through the opposite side after formation; lifecycle states are formed, partially filled, fully filled, inverted, and expired. Primary lifecycle window is 120 15-minute bars (direct timeframe transfer of the EXP-020 rule). Secondary lifecycle sensitivity is 8 15-minute bars (approximating the original 120-minute elapsed-time window).
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, subject to available time-bar coverage.
- **Time range**: Full dataset with nested chronological split applied to the 1-minute series before aggregation. First 70% of the 1-minute series = analysis set, split 70/30 into train/test; final 30% = global holdout, never loaded, inspected, or used. The 15-minute series is generated only from the analysis-set 1-minute slice.
- **Global holdout**: The final 30% of each chronologically ordered 1-minute instrument dataset is excluded before any aggregation. The full 1-minute dataset must not be aggregated and re-split.
- **Look-ahead bias prevention**: 15-minute aggregation uses only completed 1-minute bars. FVG and IFVG events are identified using only 15-minute bars with `CloseTime` at or before the event timestamp. ATR_14 on 15-minute bars uses only completed 15-minute bars available at the FVG formation timestamp.
- **Real-price outcome discipline**: This experiment is detection-only and does not compute trade returns, MAE, or MFE. Selectivity is measured on detection counts. Any overlap diagnostic with displacement-confirmed events uses 15-minute bar `CloseTime` for alignment; no synthetic chart prices are used for any metric.
- **Exclusions**: No full ICT model, no parameter tuning against outcomes, no event-chart features, no tick/1-second/bid-ask data, no IFVG rule redesign (rule transfer is unmodified), no 1-hour or other timeframe variants, no entry-quality or excursion outcomes, no return-based rule selection.

## Success / Failure Criteria

- **Evidence FOR**: Primary 120-bar IFVG inversion rate is materially below 50 percent on at least 2 of 4 instruments at 15-minute resolution, AND FVG counts meet `>= 100` per train/test segment with IFVG counts meeting `>= 50` per train/test segment on the same instruments, AND detection is deterministic across fresh-reload and shuffled-resort invariance checks (SHA-256 digest match on FVG identity columns) on all instruments.
- **Evidence AGAINST**: Primary 120-bar IFVG inversion rate remains at or near the Phase 003 84-85 percent baseline (within 5 percentage points) on at least 3 of 4 instruments, OR detection is non-deterministic on any instrument.
- **Inconclusive**: IFVG inversion rate drops on some instruments but FVG or IFVG counts fall below the predeclared floors on those instruments, OR exactly 1 of 4 instruments meets both selectivity and count gates, OR the primary 120-bar result and the 8-bar lifecycle sensitivity disagree in direction by more than 10 percentage points without a clear timeframe-vs-lifecycle attribution.

## Prerequisites and Sequencing

Requires EXP-020 FVG/IFVG detector rules and EXP-015 price precision convention, both inherited unchanged. This is the first of three Phase 004A pre-phase experiments. EXP-030 and EXP-031 may be scoped in parallel but the Phase 004A reflection directive depends on the combined results of EXP-029, EXP-030, and EXP-031.

## Complexity Budget

- Max statistical tests: 1
- Max visualisations: 4
- Max new code modules: 1

The single new module is `python/src/bar_aggregator.py` providing deterministic 15-minute OHLC resampling from 1-minute bars. The FVG/IFVG detector from EXP-020 is reused without modification.

## Data Requirements

For each instrument, load the 1-minute time-bar Parquet file lazily, sort by `CloseTime`, slice the first 70 percent chronologically as the analysis set without materialising the holdout, then aggregate the analysis-set 1-minute bars into synthetic 15-minute bars via `bar_aggregator.py`. Apply the nested train/test 70/30 split inside the analysis set on the 15-minute series. Run the EXP-020 detector unchanged on the 15-minute frames. Compute the secondary 8-bar lifecycle sensitivity on the same 15-minute event set. Run the EXP-020 fresh-reload and shuffled-resort invariance checks on the 15-minute pipeline.

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

Report event counts and inversion rates by instrument and segment before any cross-instrument synthesis. The reflection consumes the actual inversion-rate values, not a binary pass/fail; surface the full per-instrument table and both lifecycle variants so the reflection can calibrate the Branch B directive against the 1-minute baseline.
