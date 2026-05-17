# Experiment: EXP-010 - Line Break as a Confirmation Layer Over Renko Signals

## Hypothesis

Renko signals that are also confirmed by a Line Break level 3 emission within a fixed tolerance window show materially higher real-price forward excursion and/or lower adverse excursion than the full set of Renko signals, enough to justify Line Break's coverage reduction.

## Question

Does Line Break confirmation add measurable real-price signal quality beyond Renko alone, and if so, what coverage cost does that confirmation impose?

## Scope Boundaries

- **Chart Types**: Renko and Line Break. Time bars are used only as the real-price outcome anchor and volatility-regime reference.
- **Chart Type Parameters**: 1-minute and 15-minute source timeframes; Renko ATR period 14; Line Break level 3.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set (split 70/30 for train/test); final 30% = global holdout (never used).
- **Global holdout**: The final 30% of the full dataset must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: Renko primary signals and Line Break confirmations use native event timestamps only. Forward windows are used only for outcome measurement.
- **Synthetic price discipline**: Renko and Line Break construction prices are never used for returns, excursions, or P&L. Outcomes resolve from 1-minute real time-bar prices at Renko signal timestamps.
- **Primary confirmation window**: 15 minutes. Sensitivity windows: 5 and 30 minutes. Windows are not optimized or selected after results are seen.
- **Exclusions**: No strategy P&L, no time-bar or HA signals in primary analysis, no parameter optimization, no selection of a best timeframe.

## Success / Failure Criteria

- **Evidence FOR**: At the primary 15-minute confirmation window, Line Break-confirmed Renko signals improve over all Renko signals on FE, AE, or signal-level precision on at least 3 of 4 instruments at either timeframe, with bootstrap CIs excluding zero, while coverage cost is explicitly reported.
- **Evidence AGAINST**: Confirmed Renko signals do not improve any primary metric versus all Renko signals, or quality gains are too inconsistent to justify coverage reduction.
- **Inconclusive**: Directional filtering at 1-minute and coverage selection at 15-minute produce contradictory results, sensitivity windows reverse the primary conclusion, or non-confirmed denominators are too small for reliable comparison.

## Complexity Budget

- Max statistical tests: 4 comparison families (confirmed vs all Renko, confirmed vs non-confirmed, timeframe contrast, regime contrast).
- Max visualisations: 5.
- Max new code modules: 0 shared modules beyond the EXP-007 framework, plus the experiment runner.

## Data Requirements

Use the EXP-007 signal-quality framework. Load 1-minute time bars, exclude holdout before aggregation, create 15-minute bars from the analysis set only, generate Renko ATR-14 and Line Break level 3 per source timeframe, and evaluate outcomes on real 1-minute time-bar prices.

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

Treat Renko as the primary signal layer and Line Break as a confidence stratifier. At 1-minute, assess whether confirmation adds directional quality. At 15-minute, where matched LB/Renko direction agreement is expected to be perfect, assess whether Line Break selects a higher-quality subset of Renko events.
