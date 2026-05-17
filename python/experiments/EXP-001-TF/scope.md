# Experiment: EXP-001-TF - Timeframe Replication of Information Density & Ghost Bar Comparison

## Hypothesis

The EXP-001 hypothesis is retested unchanged on 15-minute and 1-hour source bars: Line Break and Renko event bars have higher information density than same-timeframe time bars on at least 3 of 4 instruments, measured as lower ghost rate, better use of remaining directional-entropy headroom, and a practical absolute entropy gain. Heiken Ashi is included as a smoothed time-bar transformation but is not expected to reduce bar count.

## Question

Do the EXP-001 information-density and ghost-bar conclusions replicate when the source time bars are 15-minute and 1-hour aggregates rather than 1-minute bars?

## Scope Boundaries

- **Chart Types**: 15-minute and 1-hour time bars, Line Break, Renko, Heiken Ashi.
- **Chart Type Parameters**: Source timeframes 15-minute and 1-hour; Line Break levels 3 and 5; Renko ATR period 14; Heiken Ashi generated from each aggregated source timeframe.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full available dataset per instrument with nested chronological split. First 70% = analysis set; within that, first 70% = train segment and last 30% = test segment. Final 30% = global holdout.
- **Global holdout**: The final 30% of the full chronologically ordered 1-minute source dataset must not be loaded, inspected, summarized, plotted, aggregated, or used in any capacity.
- **Look-ahead bias prevention**: Apply the 70% source-data cutoff before higher-timeframe aggregation and before chart-type generation. Generate chart types sequentially from completed 15-minute or 1-hour bars only. Use `CloseTime` for time bars and Heiken Ashi, and `SourceCloseTime` for Line Break and Renko temporal alignment.
- **Synthetic price discipline**: This is not a strategy or P&L experiment. Any real-price return or movement proxy uses same-timeframe time-bar `Close` or Heiken Ashi `RealClose`, never `HAClose` or Renko construction prices.
- **Exclusions**: No replacement or modification of EXP-001, no strategy backtesting, no predictive modeling, no parameter optimization, no tick-derived Renko, no source timeframes beyond 15-minute and 1-hour, and no persistence of generated chart-type datasets unless separately justified by the project persistence policy.

## Success / Failure Criteria

- **Evidence FOR**: For each tested timeframe, on at least 3 instruments, Line Break level 3 or Renko ATR-14 has ghost rate at least 25% lower than same-timeframe time bars, captures at least 50% of the remaining directional-entropy headroom toward the binary maximum of 1.0, and increases directional entropy by at least 0.005 bits. Event-chart entropy verdicts use distinct `SourceCloseTime` rows so same-source Renko construction artifacts do not drive the threshold.
- **Evidence AGAINST**: For each tested timeframe, fewer than 2 instruments meet the ghost-rate, entropy-headroom, and absolute entropy-gain thresholds for every primary event chart type.
- **Inconclusive**: Improvements are directionally consistent but below practical thresholds, bootstrap summaries disagree with instrument-level effects, valid data volume is insufficient for at least 3 instruments, or the 15-minute and 1-hour outcomes conflict materially.

## Complexity Budget

- Max statistical tests: 2
- Max visualisations: 4
- Max new code modules: 1

## Data Requirements

Load each instrument's 1-minute time-bar Parquet data lazily, sort by `CloseTime`, determine the chronological 70% analysis cutoff, and materialize only rows before that cutoff. Aggregate the analysis rows into complete 15-minute and 1-hour OHLCV bars using `OpenTime`/`CloseTime` buckets; drop incomplete buckets at the analysis boundary and report dropped counts. For each timeframe, generate Line Break, Renko, and Heiken Ashi from the aggregated analysis bars only.

Define ghost bars consistently before execution: for time bars and Heiken Ashi, near-zero real range or absolute close-to-close movement below one instrument-specific minimum observed non-zero tick increment proxy on the same timeframe; for Line Break and Renko, zero real-price movement between adjacent distinct `SourceCloseTime`-aligned closes. When an event generator emits multiple rows with the same `SourceCloseTime`, exclude same-source duplicate rows from the ghost-rate denominator and emit distinct-source sensitivity metrics for entropy and real-price movement.

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

Produce per-instrument, per-timeframe, per-chart-type summary tables for bar count, bars per elapsed day, ghost rate, directional entropy, real-price movement per bar, distinct-source sensitivity metrics, and a reproducibility manifest. Compare the 15-minute and 1-hour verdicts to EXP-001 without altering the original EXP-001 result.
