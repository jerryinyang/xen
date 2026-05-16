# Experiment: EXP-001 - Information Density & Ghost Bar Comparison

## Hypothesis

Line Break and Renko event bars have higher information density than 1-minute time bars on at least 3 of 4 instruments, measured as lower ghost rate, better use of remaining directional-entropy headroom, and a practical absolute entropy gain. Heiken Ashi is included as a smoothed time-bar transformation but is not expected to reduce bar count.

## Question

Which Phase 1 chart types spend fewer bars on economically empty movement, and how does their information density compare over the same chronological analysis windows?

## Scope Boundaries

- **Chart Types**: 1-minute time bars, Line Break, Renko, Heiken Ashi.
- **Chart Type Parameters**: Line Break levels 3 and 5; Renko ATR period 14; Heiken Ashi generated from 1-minute source bars; 1-minute time bars as baseline.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC. Use every instrument with available valid time-bar data.
- **Time range**: Full available dataset per instrument with nested chronological split. First 70% = analysis set; within that, first 70% = train segment and last 30% = test segment. Final 30% = global holdout.
- **Global holdout**: The final 30% of the full chronologically ordered dataset must not be loaded, inspected, summarized, plotted, or used in any capacity.
- **Look-ahead bias prevention**: Generate chart types sequentially from completed 1-minute bars only. Use `CloseTime` for time bars and Heiken Ashi, and `SourceCloseTime` for Line Break and Renko temporal alignment.
- **Synthetic price discipline**: This is not a strategy or P&L experiment. Any real-price return or movement proxy uses time-bar `Close` or Heiken Ashi `RealClose`, never `HAClose` or Renko construction prices.
- **Exclusions**: No strategy backtesting, predictive modeling, parameter optimization, higher-timeframe comparison, tick-derived Renko, or persistence of generated chart-type datasets.

## Success / Failure Criteria

- **Evidence FOR**: On at least 3 instruments, Line Break level 3 or Renko ATR-14 has ghost rate at least 25% lower than time bars, captures at least 50% of the remaining directional-entropy headroom toward the binary maximum of 1.0, and increases directional entropy by at least 0.005 bits. Event-chart entropy comparisons for this verdict use distinct `SourceCloseTime` rows so same-source Renko construction artifacts do not drive the threshold. Bootstrap summaries are descriptive consistency checks and are not sufficient on their own to support the hypothesis.
- **Evidence AGAINST**: Fewer than 2 instruments meet the ghost-rate, entropy-headroom, and absolute entropy-gain thresholds for every primary event chart type.
- **Inconclusive**: Improvements are directionally consistent but below practical thresholds, bootstrap summaries disagree with the instrument-level effects, or valid data volume is insufficient for at least 3 instruments.

## Complexity Budget

- Max statistical tests: 2
- Max visualisations: 4
- Max new code modules: 1

## Data Requirements

Load each instrument's 1-minute time-bar Parquet data, sort by `CloseTime`, apply the 70% analysis cutoff before any chart generation, then generate Line Break, Renko, and Heiken Ashi from the analysis set only. Define ghost bars consistently before execution: for time bars and Heiken Ashi, near-zero real range or absolute close-to-close movement below one instrument-specific minimum observed non-zero tick increment proxy; for Line Break and Renko, zero real-price movement between adjacent distinct `SourceCloseTime`-aligned closes. When an event generator emits multiple rows with the same `SourceCloseTime`, exclude same-source duplicate rows from the ghost-rate denominator rather than counting construction artifacts as market ghosts, and emit distinct-source sensitivity metrics for entropy and real-price movement so construction artifacts remain auditable.

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

Produce per-instrument, per-chart-type summary tables for bar count, bars per day, ghost rate, directional entropy, real-price movement per bar, distinct-source sensitivity metrics, and a reproducibility manifest. Compare event-based chart types to time bars using paired instrument-level effect sizes, sign counts, and descriptive bootstrap confidence intervals.
