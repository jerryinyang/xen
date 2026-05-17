# Experiment: EXP-008 - Renko as a Precision Gate Over Time-Bar Signals

## Hypothesis

At the 15-minute source timeframe, time-bar direction signals confirmed by a same-or-prior Renko ATR-14 emission within a fixed tolerance window show a better AE-relative-to-FE trade-off than the full set of time-bar direction signals, after accounting for Renko's coverage cost.

## Question

Does Renko confirmation select a subset of time-bar signals with a meaningfully better log FE/AE ratio than the unfiltered time-bar signal pool, and is that improvement large enough relative to the coverage reduction to represent a net gain on the full signal-opportunity population?

## Scope Boundaries

- **Chart Types**: Time Bars and Renko.
- **Chart Type Parameters**: Time bars at 15-minute source timeframe for confirmatory analysis; 1-minute source timeframe retained as exploratory only. Renko ATR period 14 generated from the matching source timeframe.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set (split 70/30 for train/test); final 30% = global holdout (never used).
- **Global holdout**: The final 30% of the full dataset must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: A time-bar candidate can be Renko-confirmed only by a same-direction Renko emission at or before the candidate timestamp within the fixed tolerance window. Forward windows are used only for outcome measurement.
- **Synthetic price discipline**: Renko construction prices are never used for returns, excursions, or P&L. All signal outcomes resolve from 1-minute real time-bar prices.
- **Primary confirmation window**: 15 minutes. Sensitivity windows: 5 and 30 minutes. Windows are not optimized or selected after results are seen.
- **Exclusions**: No strategy P&L, no parameter optimization, no tick-level data, no Line Break or Heiken Ashi analysis, no selection of a best timeframe. The 1-minute arm cannot support the hypothesis verdict.

## Success / Failure Criteria

- **Evidence FOR**: At the 15-minute source timeframe and primary 15-minute confirmation window, Renko-confirmed time-bar signals improve log FE/AE ratio versus unfiltered time-bar signals on at least 3 of 4 instruments, with bootstrap CIs excluding zero, and the improvement is supported by FE60 and AE60 moving in a coherent direction rather than by an artefact of one extreme metric alone. Coverage-adjusted FE60 and AE60 for the full time-bar opportunity population must be reported.
- **Evidence AGAINST**: The confirmed subset does not improve log FE/AE ratio versus unfiltered time-bar signals on at least 3 instruments, or the coverage-adjusted outcome shows lower FE60 without a compensating AE60 reduction.
- **Inconclusive**: The 15-minute result is instrument-specific only, FE60 and AE60 move in opposing ways that make the log ratio hard to interpret, sensitivity windows reverse the primary conclusion, or denominator/missing-signal issues prevent reliable comparison.

## Complexity Budget

- Max statistical tests: 4 comparison families (confirmed vs time, confirmed vs Renko, confirmed vs non-confirmed, timeframe contrast).
- Max visualisations: 5.
- Max new code modules: 0 shared modules beyond the EXP-007 framework, plus the experiment runner.

## Data Requirements

Use the EXP-007 signal-quality framework. Load 1-minute time bars, apply holdout exclusion before aggregation, derive 15-minute bars from the analysis set only, generate Renko ATR-14 per timeframe, and derive time-bar direction signals. Confirmation is tested by same-or-prior timestamp only, never by bar index. FE60, AE60, and log FE/AE are the confirmatory metrics at 15-minute; precision, recall, run continuation, and 1-minute results are descriptive diagnostics.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

bars = (
    pl.scan_parquet(path)
    .select(["Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume"])
    .sort("CloseTime")
)
source_rows = int(bars.select(pl.len()).collect().item())
analysis_rows = int(source_rows * 0.70)
analysis_bars = bars.slice(0, analysis_rows).collect()
```

## Suggested Direction

Report 15-minute results as confirmatory and 1-minute results as exploratory. The 15-minute analysis tests whether Renko confirmation improves the AE-relative-to-FE trade-off after coverage cost; the 1-minute analysis is retained only to document whether the earlier latency-cost trade-off shows the same pattern descriptively.
