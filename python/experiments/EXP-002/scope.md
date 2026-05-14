# Experiment: EXP-002 - Volatility & Trend Regime Representation

## Hypothesis

Line Break level 3 and Renko ATR-14 represent volatility regime boundaries more cleanly than 1-minute time bars on at least 3 of 4 instruments, measured by lower hybrid rate and lower regime transition lag.

## Question

Do Line Break and Renko align more cleanly with volatility and trend regime transitions than the 1-minute time-bar baseline?

## Scope Boundaries

- **Chart Types**: 1-minute time bars, Line Break, Renko, Heiken Ashi.
- **Chart Type Parameters**: Line Break level 3 only; Renko ATR period 14; Heiken Ashi generated from 1-minute source bars; 1-minute time bars as baseline.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full available dataset per instrument with nested chronological split. First 70% = analysis set; within that, first 70% = train segment and last 30% = test segment. Final 30% = global holdout.
- **Global holdout**: The final 30% of the full chronologically ordered dataset must not be loaded, inspected, summarized, plotted, or used in any capacity.
- **Look-ahead bias prevention**: Regime labels are computed from completed time bars available at or before each timestamp. Chart-type events are aligned by `CloseTime` or `SourceCloseTime`.
- **Synthetic price discipline**: No P&L or strategy-return analysis. Heiken Ashi regime metrics use real source prices where price movement is needed.
- **Exclusions**: No parameter search, no predictive models, no strategy validation, no higher-timeframe regimes, no post-hoc regime definitions based on generated chart-type output.

## Success / Failure Criteria

- **Evidence FOR**: On at least 3 instruments, Line Break level 3 or Renko ATR-14 has at least 20% lower hybrid rate and at least 20% lower median transition lag than time bars, with paired bootstrap 95% confidence intervals excluding zero for the improvement.
- **Evidence AGAINST**: Time bars match or outperform Line Break and Renko on both hybrid rate and transition lag for at least 3 instruments.
- **Inconclusive**: Hybrid-rate and lag results disagree materially, effects are below thresholds, or volatility regime transitions are too sparse to estimate reliably.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 4
- Max new code modules: 1

## Data Requirements

Compute realised volatility on 1-minute time bars within the analysis set only, assign low/medium/high regimes by expanding or rolling train-derived terciles, and apply those labels to chart-type events by timestamp. Define trend direction consistently by chart-type `Direction` where available and by time-bar close-to-close sign for time bars.

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

Measure how often chart bars straddle regime boundaries, how quickly direction/regime labels reflect a new volatility regime, and whether the result is consistent across instruments without adding a forecasting model.
