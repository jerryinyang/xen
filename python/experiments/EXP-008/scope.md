# Experiment: EXP-008 - Renko as a Precision Gate Over Time-Bar Signals

## Hypothesis

Time-bar direction signals confirmed by a Renko ATR-14 emission within a fixed tolerance window show materially higher real-price forward excursion and/or lower adverse excursion than the full set of time-bar direction signals, without reducing signal quality relative to raw Renko signals alone.

## Question

Does using Renko as a precision filter over the time-bar signal pool improve the real-price signal-quality distribution of the filtered subset compared with both unfiltered time-bar signals and raw Renko signals?

## Scope Boundaries

- **Chart Types**: Time Bars and Renko.
- **Chart Type Parameters**: Time bars at 1-minute and 15-minute source timeframes; Renko ATR period 14 generated from the matching source timeframe.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set (split 70/30 for train/test); final 30% = global holdout (never used).
- **Global holdout**: The final 30% of the full dataset must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: Time-bar candidate signals and Renko confirmations use only timestamps at or before the confirmation decision. Forward windows are used only for outcome measurement.
- **Synthetic price discipline**: Renko construction prices are never used for returns, excursions, or P&L. All signal outcomes resolve from 1-minute real time-bar prices.
- **Primary confirmation window**: 15 minutes. Sensitivity windows: 5 and 30 minutes. Windows are not optimized or selected after results are seen.
- **Exclusions**: No strategy P&L, no parameter optimization, no tick-level data, no Line Break or Heiken Ashi analysis, no selection of a best timeframe.

## Success / Failure Criteria

- **Evidence FOR**: At the primary 15-minute confirmation window, Renko-confirmed time-bar signals improve over unfiltered time-bar signals on FE, AE, or signal-level precision on at least 3 of 4 instruments at either timeframe, with bootstrap CIs excluding zero; and the confirmed subset is not worse than raw Renko signals by more than 5 percentage points in signal-level precision on at least 3 of 4 instruments.
- **Evidence AGAINST**: Renko-confirmed time-bar signals fail to improve over unfiltered time-bar signals on all primary metrics, or the confirmed subset loses material quality versus raw Renko signals while only reducing coverage.
- **Inconclusive**: Improvements are instrument-specific only, sensitivity windows reverse the primary conclusion, or denominator/missing-signal issues prevent reliable comparison.

## Complexity Budget

- Max statistical tests: 4 comparison families (confirmed vs time, confirmed vs Renko, confirmed vs non-confirmed, timeframe contrast).
- Max visualisations: 5.
- Max new code modules: 0 shared modules beyond the EXP-007 framework, plus the experiment runner.

## Data Requirements

Use the EXP-007 signal-quality framework. Load 1-minute time bars, apply holdout exclusion before aggregation, derive 15-minute bars from the analysis set only, generate Renko ATR-14 per timeframe, and derive time-bar direction signals. Confirmation is tested by timestamp only, never by bar index.

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

Report 1-minute and 15-minute results separately. The 1-minute analysis quantifies the latency-cost trade-off; the 15-minute analysis tests whether Renko's simultaneous speed-and-precision advantage translates into better real-price outcomes.
