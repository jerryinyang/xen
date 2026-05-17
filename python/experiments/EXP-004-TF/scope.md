# Experiment: EXP-004-TF - Timeframe Replication of Market Structure Capture Speed & Fidelity

## Hypothesis

The EXP-004 hypothesis is retested unchanged on 15-minute and 1-hour source bars: Line Break level 3 and Renko ATR-14 detect predefined real-price trend reversals faster than same-timeframe time-bar confirmation on at least 3 of 4 instruments, but their precision is not higher than the time-bar baseline.

## Question

What speed-precision trade-off does each chart type exhibit when detecting real-price trend reversals on 15-minute and 1-hour source bars, and does the EXP-004 conclusion replicate beyond 1-minute bars?

## Scope Boundaries

- **Chart Types**: 15-minute and 1-hour time bars, Line Break, Renko, Heiken Ashi.
- **Chart Type Parameters**: Source timeframes 15-minute and 1-hour; Line Break level 3; Renko ATR period 14; Heiken Ashi generated from each aggregated source timeframe.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full available dataset per instrument with chronological holdout exclusion. First 70% = analysis set used for characterisation; final 30% = global holdout. No nested train/test split is used because this experiment fits no predictive model.
- **Global holdout**: The final 30% of the full chronologically ordered 1-minute source dataset must not be loaded, inspected, summarized, plotted, aggregated, or used in any capacity.
- **Look-ahead bias prevention**: Apply the 70% source-data cutoff before aggregation. Reversal labels use only completed aggregated time-bar data and confirmation rules that are timestamped when knowable. Chart-type signals are evaluated at their `CloseTime` or `SourceCloseTime`.
- **Synthetic price discipline**: Signal timing may come from chart-type direction changes, but reversal truth and validation use real same-timeframe time-bar prices. No strategy returns or P&L are computed.
- **Exclusions**: No replacement or modification of EXP-004, no strategy entry/exit testing, no optimisation of reversal thresholds, no predictive model, no bar-index alignment, no use of future windows except to timestamp a reversal after its confirmation point, and no source timeframes beyond 15-minute and 1-hour.

## Success / Failure Criteria

- **Evidence FOR**: For each tested timeframe, Line Break or Renko median detection latency is at least 30% lower than the same-timeframe time-bar baseline on at least 3 instruments, while total signal precision (`matched / total signals`, including duplicate same-direction signals in the denominator) is no more than 10 percentage points higher than time bars, confirming a speed trade-off rather than broad dominance.
- **Evidence AGAINST**: For each tested timeframe, event-based detection latency is not at least 15% lower than same-timeframe time bars on at least 3 instruments, or event-based precision is materially worse by more than 25 percentage points on at least 3 instruments.
- **Inconclusive**: Too few confirmed reversals exist, latency improves but precision collapses beyond threshold, reversal labels are unstable under the sensitivity check, or the 15-minute and 1-hour outcomes conflict materially.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 5
- Max new code modules: 1

## Data Requirements

Load each instrument's 1-minute time-bar Parquet data lazily, sort by `CloseTime`, determine the chronological 70% analysis cutoff, and materialize only rows before that cutoff. Aggregate the analysis rows into complete 15-minute and 1-hour OHLCV bars, dropping incomplete boundary buckets and reporting dropped counts. Define real-price trend reversals separately for each timeframe using the same documented ATR-scaled swing threshold convention as EXP-004, such as rolling ATR-scaled directional movement confirmed at a timestamp. Generate chart-type reversal signals from direction changes and compare each signal to the first same-direction confirmed real-price reversal within the fixed 120-minute forward tolerance window. Reversal-label sensitivity must compare the primary threshold (`1.5 x ATR`) with the alternate threshold (`2.0 x ATR`) and report overlap stability.

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

Build a timeframe-aware event-matching table: real reversal timestamp, first chart-type signal after reversal confirmation, latency in clock minutes and source bars, matched/unmatched status, false signal count, and duplicate signal count. Compare the higher-timeframe latency and precision trade-off to EXP-004 without changing the original EXP-004 verdict.
