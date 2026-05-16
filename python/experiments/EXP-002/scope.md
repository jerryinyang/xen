# Experiment: EXP-002 - Volatility & Trend Regime Representation

## Hypothesis

Line Break level 3 and Renko ATR-14 are evaluated for volatility-regime boundary cost versus the 1-minute time-bar lower bound, measured by hybrid rate and regime transition lag. Because regimes are defined on 1-minute time bars, the time-bar baseline has zero hybrid rate and zero transition lag by construction; event charts can only match that lower bound or incur additional boundary cost.

## Question

How much boundary cost do Line Break and Renko incur relative to the 1-minute time-bar regime timeline, and is the cost small enough to preserve useful regime representation?

## Scope Boundaries

- **Chart Types**: 1-minute time bars, Line Break, Renko, Heiken Ashi.
- **Chart Type Parameters**: Line Break level 3 only; Renko ATR period 14; Heiken Ashi generated from 1-minute source bars; 1-minute time bars as baseline.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full available dataset per instrument with nested chronological split. First 70% = analysis set; within that, first 70% = train segment and last 30% = test segment. Final 30% = global holdout.
- **Global holdout**: The final 30% of the full chronologically ordered dataset must not be loaded, inspected, summarized, plotted, or used in any capacity.
- **Look-ahead bias prevention**: Regime labels are computed from completed time bars available at or before each timestamp using rolling close-to-close log-return volatility. Chart-type events are aligned by `CloseTime` or `SourceCloseTime`.
- **Synthetic price discipline**: No P&L or strategy-return analysis. Heiken Ashi regime metrics use real source prices where price movement is needed.
- **Exclusions**: No parameter search, no predictive models, no strategy validation, no higher-timeframe regimes, no post-hoc regime definitions based on generated chart-type output.

## Success / Failure Criteria

- **Evidence FOR**: On at least 3 instruments, Line Break level 3 or Renko ATR-14 has hybrid rate no greater than 0.05 and median transition lag no greater than 2 source time bars, with paired bootstrap summaries showing bounded absolute excess versus time bars.
- **Evidence AGAINST**: Line Break and Renko both exceed either the 0.05 hybrid-rate bound or 2-bar median-lag bound on at least 3 instruments.
- **Inconclusive**: Hybrid-rate and lag results disagree materially, effects are below thresholds, or volatility regime transitions are too sparse to estimate reliably.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 4
- Max new code modules: 1

## Data Requirements

Compute realised volatility on 1-minute time bars within the analysis set only as rolling standard deviation of close-to-close log returns, assign low/medium/high regimes by train-derived terciles, and apply those labels to chart-type events by timestamp. Rows without a defined rolling regime are excluded from metric denominators and reported. Define trend direction consistently by chart-type `Direction` where available and by time-bar close-to-close sign for time bars.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
bars = scan.slice(0, int(total_rows * 0.7)).collect()
```

## Suggested Direction

Measure how often chart bars straddle regime boundaries, how quickly chart events confirm a new volatility regime, transition coverage/missed-transition counts, and whether the result is consistent across instruments without adding a forecasting model.
