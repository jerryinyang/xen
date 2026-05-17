# Experiment: EXP-010 - Line Break as a Confirmation Layer Over Renko Signals

## Hypothesis

At the 15-minute source timeframe, Renko signals confirmed by a same-or-prior Line Break level 3 emission show a better AE-relative-to-FE trade-off than the full Renko signal set, after accounting for the additional coverage reduction imposed by Line Break.

## Question

Does Line Break confirmation select a Renko subset with a meaningfully better log FE/AE ratio than the full Renko signal set at 15-minute, and is that improvement large enough relative to the additional coverage reduction to represent a net gain over Renko alone?

## Scope Boundaries

- **Chart Types**: Renko and Line Break. Time bars are used only as the real-price outcome anchor and volatility-regime reference.
- **Chart Type Parameters**: 15-minute source timeframe for confirmatory analysis; 1-minute source timeframe retained as exploratory only. Renko ATR period 14; Line Break level 3.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set (split 70/30 for train/test); final 30% = global holdout (never used).
- **Global holdout**: The final 30% of the full dataset must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: A Renko primary signal can be Line Break-confirmed only by a same-direction Line Break emission at or before the Renko signal timestamp within the fixed tolerance window. Forward windows are used only for outcome measurement.
- **Synthetic price discipline**: Renko and Line Break construction prices are never used for returns, excursions, or P&L. Outcomes resolve from 1-minute real time-bar prices at Renko signal timestamps.
- **Primary confirmation window**: 15 minutes. Sensitivity windows: 5 and 30 minutes. Windows are not optimized or selected after results are seen.
- **Exclusions**: No strategy P&L, no time-bar or HA signals in primary analysis, no parameter optimization, no selection of a best timeframe. The 1-minute arm cannot support the hypothesis verdict.

## Success / Failure Criteria

- **Evidence FOR**: At the 15-minute source timeframe and primary 15-minute confirmation window, Line Break-confirmed Renko signals improve log FE/AE ratio versus all Renko signals on at least 3 of 4 instruments, with bootstrap CIs excluding zero, and FE60/AE60 show that the ratio improvement is not an artefact of collapsing favourable and adverse excursion. Coverage-adjusted FE60 and AE60 for the full Renko signal population must be reported.
- **Evidence AGAINST**: Confirmed Renko signals do not improve log FE/AE ratio versus all Renko signals on at least 3 instruments, or the additional coverage reduction worsens full-population FE60/AE60 without a compensating AE-relative-to-FE gain.
- **Inconclusive**: The 15-minute result is instrument-specific only, FE60 and AE60 move in opposing ways that make the log ratio hard to interpret, sensitivity windows reverse the primary conclusion, or non-confirmed denominators are too small for reliable comparison.

## Complexity Budget

- Max statistical tests: 4 comparison families (confirmed vs all Renko, confirmed vs non-confirmed, timeframe contrast, regime contrast).
- Max visualisations: 5.
- Max new code modules: 0 shared modules beyond the EXP-007 framework, plus the experiment runner.

## Data Requirements

Use the EXP-007 signal-quality framework. Load 1-minute time bars, exclude holdout before aggregation, create 15-minute bars from the analysis set only, generate Renko ATR-14 and Line Break level 3 per source timeframe, and evaluate outcomes on real 1-minute time-bar prices. FE60, AE60, and log FE/AE are the confirmatory metrics at 15-minute; precision, recall, run continuation, and 1-minute results are descriptive diagnostics.

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

Treat Renko as the primary signal layer and Line Break as a coverage-selection stratifier. At 15-minute, where matched LB/Renko direction agreement is expected to be perfect, assess whether Line Break selects a higher-quality subset of Renko events. At 1-minute, report the same stratification descriptively only.
