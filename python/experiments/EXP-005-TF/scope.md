# Experiment: EXP-005-TF - Timeframe Replication of Cross-Chart-Type Alignment & Regime Correspondence

## Hypothesis

The EXP-005 hypothesis is retested unchanged on 15-minute and 1-hour source bars: Line Break level 3 and Renko ATR-14 show stronger trend-direction agreement with each other than either does with same-timeframe time bars during medium- and high-volatility regimes, measured by timestamp-aligned agreement within a fixed tolerance window.

## Question

Do chart types agree on trend direction and trend-change timing on 15-minute and 1-hour source bars, and does the EXP-005 agreement verdict replicate beyond 1-minute bars?

## Scope Boundaries

- **Chart Types**: 15-minute and 1-hour time bars, Line Break, Renko, Heiken Ashi.
- **Chart Type Parameters**: Source timeframes 15-minute and 1-hour; Line Break level 3; Renko ATR period 14; Heiken Ashi generated from each aggregated source timeframe.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full available dataset per instrument with nested chronological split. First 70% = analysis set; within that, first 70% = train segment and last 30% = test segment. Final 30% = global holdout.
- **Global holdout**: The final 30% of the full chronologically ordered 1-minute source dataset must not be loaded, inspected, summarized, plotted, aggregated, or used in any capacity.
- **Look-ahead bias prevention**: Apply the 70% source-data cutoff before aggregation. Direction labels use only information available at each event timestamp. Regime labels come from same-timeframe time-bar realised volatility known at or before the timestamp, with volatility tercile thresholds calibrated on the train segment and applied only to the later evaluation segment.
- **Synthetic price discipline**: No strategy P&L or signal return validation. Agreement is based on direction labels and timestamps, not synthetic chart prices.
- **Exclusions**: No replacement or modification of EXP-005, no claim that agreement implies profitability, no predictive modelling, no optimisation of tolerance windows, no bar-index alignment, and no source timeframes beyond 15-minute and 1-hour.

## Success / Failure Criteria

- **Evidence FOR**: For each tested timeframe, in medium- and high-volatility regimes, Line Break/Renko timestamp-aligned direction agreement is at least 10 percentage points higher than each chart type's agreement with same-timeframe time bars on at least 3 instruments, with paired bootstrap intervals excluding zero.
- **Evidence AGAINST**: For each tested timeframe, Line Break/Renko agreement is not higher than agreement with same-timeframe time bars on at least 3 instruments or is below 50% in medium/high regimes.
- **Inconclusive**: Agreement varies strongly by instrument, tolerance-window sensitivity reverses the ranking, event overlap is too sparse for at least 3 instruments, or the 15-minute and 1-hour outcomes conflict materially.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 5
- Max new code modules: 1

## Data Requirements

Load each instrument's 1-minute time-bar Parquet data lazily, sort by `CloseTime`, determine the chronological 70% analysis cutoff, and materialize only rows before that cutoff. Aggregate the analysis rows into complete 15-minute and 1-hour OHLCV bars, dropping incomplete boundary buckets and reporting dropped counts. Generate chart-type event direction tables and align them by timestamp using the EXP-005 predeclared tolerance windows: nearest event within 5 minutes as primary and 15 minutes as sensitivity, with exact `CloseTime` alignment for time-bar/Heiken Ashi comparisons where possible. Collapse repeated event-chart rows at the same `SourceCloseTime` to one state per source timestamp before pairwise comparison. Volatility regimes are derived from same-timeframe time bars, calibrated on the train segment, and applied only to later timestamps.

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

Create pairwise chart-type agreement matrices by instrument, timeframe, and regime. Report both direction agreement and temporal overlap rate so sparse event alignment is visible, then classify the EXP-005 finding as replicated, attenuated, or not replicated for each higher timeframe.
