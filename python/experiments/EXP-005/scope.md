# Experiment: EXP-005 - Cross-Chart-Type Alignment & Regime Correspondence

## Hypothesis

Line Break level 3 and Renko ATR-14 show stronger trend-direction agreement with each other than either does with 1-minute time bars during medium- and high-volatility regimes, measured by timestamp-aligned agreement within a fixed tolerance window.

## Question

Do chart types agree on trend direction and trend-change timing, and does agreement vary by volatility regime?

## Scope Boundaries

- **Chart Types**: 1-minute time bars, Line Break, Renko, Heiken Ashi.
- **Chart Type Parameters**: Line Break level 3; Renko ATR period 14; Heiken Ashi generated from 1-minute source bars; 1-minute time bars as baseline.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full available dataset per instrument with nested chronological split. First 70% = analysis set; within that, first 70% = train segment and last 30% = test segment. Final 30% = global holdout.
- **Global holdout**: The final 30% of the full chronologically ordered dataset must not be loaded, inspected, summarized, plotted, or used in any capacity.
- **Look-ahead bias prevention**: Direction labels use only information available at each event timestamp. Regime labels come from time-bar realised volatility known at or before the timestamp.
- **Synthetic price discipline**: No strategy P&L or signal return validation. Agreement is based on direction labels and timestamps, not synthetic chart prices.
- **Exclusions**: No claim that agreement implies profitability, no predictive modelling, no optimisation of tolerance windows, no bar-index alignment.

## Success / Failure Criteria

- **Evidence FOR**: In medium- and high-volatility regimes, Line Break/Renko timestamp-aligned direction agreement is at least 10 percentage points higher than each chart type's agreement with time bars on at least 3 instruments, with paired bootstrap intervals excluding zero.
- **Evidence AGAINST**: Line Break/Renko agreement is not higher than agreement with time bars on at least 3 instruments or is below 50% in medium/high regimes.
- **Inconclusive**: Agreement varies strongly by instrument, tolerance-window sensitivity reverses the ranking, or event overlap is too sparse for at least 3 instruments.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 5
- Max new code modules: 1

## Data Requirements

Generate chart-type event direction tables and align them by timestamp using a predeclared tolerance window, such as nearest event within 5 source minutes for event-based chart types and exact `CloseTime` for time-bar/Heiken Ashi comparisons where possible. Volatility regimes are derived from time bars and applied uniformly by timestamp.

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

Create pairwise chart-type agreement matrices by instrument and regime. Report both direction agreement and temporal overlap rate so sparse event alignment is visible.
