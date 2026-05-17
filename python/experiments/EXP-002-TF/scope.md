# Experiment: EXP-002-TF - Timeframe Replication of Volatility & Trend Regime Representation

## Hypothesis

The EXP-002 hypothesis is retested unchanged on 15-minute and 1-hour source bars: Line Break level 3 and Renko ATR-14 are evaluated for volatility-regime boundary cost versus the same-timeframe time-bar lower bound, measured by hybrid rate and regime transition lag. Because regimes are defined on the corresponding time bars, the time-bar baseline has zero hybrid rate and zero transition lag by construction; event charts can only match that lower bound or incur additional boundary cost.

## Question

How much boundary cost do Line Break and Renko incur relative to 15-minute and 1-hour time-bar regime timelines, and does the EXP-002 conclusion replicate beyond 1-minute source bars?

## Scope Boundaries

- **Chart Types**: 15-minute and 1-hour time bars, Line Break, Renko, Heiken Ashi.
- **Chart Type Parameters**: Source timeframes 15-minute and 1-hour; Line Break level 3 only; Renko ATR period 14; Heiken Ashi generated from each aggregated source timeframe.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full available dataset per instrument with nested chronological split. First 70% = analysis set; within that, first 70% = train segment and last 30% = test segment. Final 30% = global holdout.
- **Global holdout**: The final 30% of the full chronologically ordered 1-minute source dataset must not be loaded, inspected, summarized, plotted, aggregated, or used in any capacity.
- **Look-ahead bias prevention**: Apply the 70% source-data cutoff before aggregation. Regime labels are computed from completed aggregated time bars available at or before each timestamp using rolling close-to-close log-return volatility. Chart-type events are aligned by `CloseTime` or `SourceCloseTime`.
- **Synthetic price discipline**: No P&L or strategy-return analysis. Heiken Ashi regime metrics use real source prices where price movement is needed.
- **Exclusions**: No replacement or modification of EXP-002, no parameter search, no predictive models, no strategy validation, no post-hoc regime definitions based on generated chart-type output, and no source timeframes beyond 15-minute and 1-hour.

## Success / Failure Criteria

- **Evidence FOR**: For each tested timeframe, on at least 3 instruments, Line Break level 3 or Renko ATR-14 has hybrid rate no greater than 0.05 and median transition lag no greater than 2 source time bars, with paired bootstrap summaries showing bounded absolute excess versus same-timeframe time bars.
- **Evidence AGAINST**: For each tested timeframe, Line Break and Renko both exceed either the 0.05 hybrid-rate bound or 2-source-bar median-lag bound on at least 3 instruments.
- **Inconclusive**: Hybrid-rate and lag results disagree materially, effects are below thresholds, volatility regime transitions are too sparse to estimate reliably, or replication differs materially between 15-minute and 1-hour source bars.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 4
- Max new code modules: 1

## Data Requirements

Load each instrument's 1-minute time-bar Parquet data lazily, sort by `CloseTime`, determine the chronological 70% analysis cutoff, and materialize only rows before that cutoff. Aggregate the analysis rows into complete 15-minute and 1-hour OHLCV bars, dropping incomplete boundary buckets and reporting dropped counts. Compute realised volatility on each aggregated timeframe within the analysis set only as rolling standard deviation of close-to-close log returns, assign low/medium/high regimes by train-derived terciles, and apply those labels to chart-type events by timestamp. Rows without a defined rolling regime are excluded from metric denominators and reported.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
source_analysis = scan.slice(0, int(total_rows * 0.7)).collect()
```

## Suggested Direction

Measure how often Line Break and Renko bars straddle same-timeframe regime boundaries, how quickly chart events confirm a new volatility regime, transition coverage and missed-transition counts, and whether the timeframe verdict matches or attenuates EXP-002.
