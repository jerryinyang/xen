# Experiment: EXP-004 - Market Structure Capture Speed & Fidelity

## Hypothesis

Line Break level 3 and Renko ATR-14 detect predefined real-price trend reversals faster than 1-minute time-bar confirmation on at least 3 of 4 instruments, but their precision is not higher than the time-bar baseline.

## Question

What speed-precision trade-off does each chart type exhibit when detecting real-price trend reversals?

## Scope Boundaries

- **Chart Types**: 1-minute time bars, Line Break, Renko, Heiken Ashi.
- **Chart Type Parameters**: Line Break level 3; Renko ATR period 14; Heiken Ashi generated from 1-minute source bars; 1-minute time bars as baseline.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full available dataset per instrument with nested chronological split. First 70% = analysis set; within that, first 70% = train segment and last 30% = test segment. Final 30% = global holdout.
- **Global holdout**: The final 30% of the full chronologically ordered dataset must not be loaded, inspected, summarized, plotted, or used in any capacity.
- **Look-ahead bias prevention**: Reversal labels use only completed time-bar data and confirmation rules that are timestamped when knowable. Chart-type signals are evaluated at their `CloseTime` or `SourceCloseTime`.
- **Synthetic price discipline**: Signal timing may come from chart-type direction changes, but reversal truth and validation use real time-bar prices. No strategy returns or P&L are computed.
- **Exclusions**: No strategy entry/exit testing, no optimisation of reversal thresholds, no predictive model, no bar-index alignment, no use of future windows except to timestamp a reversal after its confirmation point.

## Success / Failure Criteria

- **Evidence FOR**: Line Break or Renko median detection latency is at least 30% lower than the time-bar baseline on at least 3 instruments, while precision is no more than 10 percentage points higher than time bars, confirming a speed trade-off rather than broad dominance.
- **Evidence AGAINST**: Event-based detection latency is not at least 15% lower than time bars on at least 3 instruments, or event-based precision is materially worse by more than 25 percentage points on at least 3 instruments.
- **Inconclusive**: Too few confirmed reversals exist, latency improves but precision collapses beyond threshold, or reversal labels are unstable under a simple sensitivity check.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 5
- Max new code modules: 1

## Data Requirements

Define real-price trend reversals from 1-minute time bars using a single documented swing threshold set before execution, such as rolling ATR-scaled directional movement confirmed at a timestamp. Generate chart-type reversal signals from direction changes and compare each signal to the nearest confirmed real-price reversal within a fixed tolerance window.

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

Build a simple event-matching table: real reversal timestamp, first chart-type signal after the reversal confirmation, latency in minutes, matched/unmatched status, false signal count, and duplicate signal count.
