# Experiment: EXP-007 - Multi-State Signal-Quality Baseline

## Hypothesis

Real-price signal quality cannot be adequately characterized by binary direction alone. A multi-state signal-quality framework measuring forward excursion, adverse excursion, run continuation, signal-level precision, and event-level recall in ATR units on the real-price timeline produces pre-specified differentiation across chart types and volatility regimes.

## Question

What does the signal-quality distribution look like for each chart type when measured on real prices at signal emission timestamps, and is binary direction entropy an adequate summary of that distribution?

## Scope Boundaries

- **Chart Types**: Time Bars, Line Break, Renko, Heiken Ashi.
- **Chart Type Parameters**: Time bars at 1-minute and 15-minute source timeframes; Line Break level 3; Renko ATR period 14; Heiken Ashi no parameters.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set (split 70/30 for train/test); final 30% = global holdout (never used).
- **Global holdout**: The final 30% of the full dataset must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: Signal generation, ATR calibration, regime labels, and confirmation eligibility must use only information known at or before the signal timestamp. Forward windows are used only for post-signal outcome measurement.
- **Synthetic price discipline**: No returns, excursions, or signal-quality metrics may use Heiken Ashi synthetic prices, Renko construction prices, or Line Break construction prices. All outcome metrics resolve from SourceCloseTime/CloseTime-aligned 1-minute real time-bar prices.
- **Metric denominators**: Signal-level precision denominator = emitted signals. Event-level recall denominator = qualifying real-price moves in the analysis segment. Missing-signal states must be represented explicitly and not dropped from denominators.
- **Exclusions**: No strategy P&L, no parameter optimization, no predictive models, no chart-combination logic, no 1-hour Block B signal-quality analysis.

## Success / Failure Criteria

- **Evidence FOR proceeding to EXP-008 through EXP-011**: Any one of the following holds at either 1-minute or 15-minute:
  - For FE or AE at the 60-minute window, the difference between at least one event chart type and the time-bar baseline is in a consistent direction on at least 3 of 4 instruments, with a bootstrap CI (10,000 resamples, seed 42) excluding zero.
  - For signal-level precision, at least one event chart type differs from time bars by at least 5 percentage points on at least 3 of 4 instruments, with a bootstrap CI excluding zero.
  - For run-continuation rate, at least one event chart type differs from time bars by at least 3 percentage points on at least 3 of 4 instruments, with a bootstrap CI excluding zero.
- **Evidence AGAINST proceeding**: None of the three proceed criteria is met at either timeframe.
- **Inconclusive**: A primary metric cannot be computed for enough instrument/timeframe/chart-type strata to evaluate the proceed criteria, or audit finds denominator, holdout, look-ahead, or real-price alignment violations.

## Complexity Budget

- Max statistical tests: 4 primary comparison families (FE, AE, precision, run continuation).
- Max visualisations: 6.
- Max new code modules: 1 shared reusable signal-quality framework module, plus the experiment runner.

## Data Requirements

Load each instrument's 1-minute time bars lazily, sort by `CloseTime`, and apply the global 70% analysis split before any aggregation or chart generation. Aggregate complete 15-minute OHLCV bars from the analysis set only. Generate Line Break level 3, Renko ATR-14, and Heiken Ashi from the relevant source timeframe. All signal outcomes are measured from 1-minute real time-bar prices.

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

Implement and validate the shared signal-quality framework first, then run chart-type signal extraction through that framework. Treat EXP-007 as a measurement gate: non-discriminating metrics are dropped from downstream experiments, while any metric meeting a pre-specified proceed criterion carries forward.
