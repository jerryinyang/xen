# Experiment: EXP-009 - Heiken Ashi Direction as a Signal Generator, Evaluated on Real Prices

## Hypothesis

Direction signals generated from Heiken Ashi state changes, evaluated on real prices at signal timestamps, show higher forward excursion and/or lower adverse excursion than time-bar direction-change signals because HA smoothing reduces false direction changes.

## Question

When Heiken Ashi direction changes are treated as signal events and evaluated on real prices, do they produce better real-price signal-quality distributions than time-bar direction changes alone?

## Scope Boundaries

- **Chart Types**: Time Bars and Heiken Ashi.
- **Chart Type Parameters**: 1-minute time bars; Heiken Ashi has no configurable parameters.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set (split 70/30 for train/test); final 30% = global holdout (never used).
- **Global holdout**: The final 30% of the full dataset must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: HA signal generation uses only completed bars at or before each `CloseTime`. Forward windows are used only for outcome measurement.
- **Synthetic price discipline**: HA synthetic prices are used only to define HA direction state. No returns, excursions, or signal-quality outcomes may use HAOpen, HAHigh, HALow, or HAClose.
- **Exclusions**: No strategy P&L, no HA construction-price returns, no Renko or Line Break data, no parameter variation, no predictive model.

## Success / Failure Criteria

- **Evidence FOR**: HA direction-change signals improve over time-bar direction-change signals on FE, AE, or signal-level precision on at least 3 of 4 instruments, with bootstrap CIs excluding zero, while signal-count reduction is explicitly quantified.
- **Evidence AGAINST**: HA reduces signal count without improving any primary quality metric on at least 3 of 4 instruments, or worsens AE/precision materially relative to time bars.
- **Inconclusive**: HA improves one metric while worsening another without a consistent instrument-level pattern, or low signal counts prevent reliable regime-stratified estimates.

## Complexity Budget

- Max statistical tests: 3 comparison families (HA vs time for FE/AE, precision/recall, run continuation).
- Max visualisations: 4.
- Max new code modules: 0 shared modules beyond the EXP-007 framework, plus the experiment runner.

## Data Requirements

Use the EXP-007 signal-quality framework. Load 1-minute time bars, apply holdout exclusion, generate Heiken Ashi from the analysis set only, derive time-bar and HA direction-change signals, and evaluate all outcomes on real time-bar prices at identical `CloseTime` timestamps.

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

Treat HA as a smoothing-based signal generator, not as a tradable price series. The key trade-off is whether fewer HA direction changes have better real-price outcomes than noisier time-bar direction changes.
