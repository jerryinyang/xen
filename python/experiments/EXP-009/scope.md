# Experiment: EXP-009 - Heiken Ashi Direction as a Signal Generator, Evaluated on Real Prices

## Hypothesis

At the 15-minute source timeframe, Heiken Ashi direction changes evaluated on real prices select a subset of the time-bar signal population with a better AE-relative-to-FE trade-off than raw time-bar direction changes.

## Question

Does HA's lower direction-change frequency select a higher-quality subset on FE60/AE60, and is any log FE/AE improvement large enough relative to the coverage reduction to represent a net gain?

## Scope Boundaries

- **Chart Types**: Time Bars and Heiken Ashi.
- **Chart Type Parameters**: 15-minute time bars; Heiken Ashi has no configurable parameters.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set (split 70/30 for train/test); final 30% = global holdout (never used).
- **Global holdout**: The final 30% of the full dataset must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: HA signal generation uses only completed bars at or before each `CloseTime`. Forward windows are used only for outcome measurement.
- **Synthetic price discipline**: HA synthetic prices are used only to define HA direction state. No returns, excursions, or signal-quality outcomes may use HAOpen, HAHigh, HALow, or HAClose.
- **Exclusions**: No strategy P&L, no HA construction-price returns, no Renko or Line Break data, no parameter variation, no predictive model, no 1-minute analysis.

## Success / Failure Criteria

- **Evidence FOR**: At 15-minute, HA direction-change signals improve log FE/AE ratio versus time-bar direction changes on at least 3 of 4 instruments, with bootstrap CIs excluding zero, and FE60/AE60 show that the ratio improvement is not an artefact of collapsing favourable and adverse excursion into one score. Coverage-adjusted FE60 and AE60 for the full time-bar reference population must be reported.
- **Evidence AGAINST**: HA reduces direction-change count without improving log FE/AE ratio on at least 3 instruments, or any apparent improvement is offset by worse coverage-adjusted FE60/AE60.
- **Inconclusive**: HA improves one side of the FE60/AE60 trade-off while worsening the other without a coherent log-ratio pattern, results are instrument-specific only, or low signal counts prevent reliable regime-stratified estimates.

## Complexity Budget

- Max statistical tests: 3 comparison families (HA vs time for FE60/AE60/log FE/AE, coverage-adjusted outcomes, regime contrast).
- Max visualisations: 4.
- Max new code modules: 0 shared modules beyond the EXP-007 framework, plus the experiment runner.

## Data Requirements

Use the EXP-007 signal-quality framework. Load 1-minute time bars, apply holdout exclusion before aggregation, derive 15-minute bars from the analysis set only, generate Heiken Ashi from the 15-minute analysis bars, derive time-bar and HA direction-change signals, and evaluate all outcomes on real 1-minute time-bar prices at identical 15-minute `CloseTime` timestamps.

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

Treat HA as a smoothing-based signal generator, not as a tradable price series. The key trade-off is whether fewer 15-minute HA direction changes improve AE relative to FE after coverage cost; signal-level precision and run continuation are diagnostics only.
