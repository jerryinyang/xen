# Experiment: EXP-006 - Heiken Ashi Synthetic Price Distortion Quantification

## Hypothesis

Heiken Ashi synthetic prices compress realised return magnitude and volatility by at least 30% versus real 1-minute prices on all 4 Phase 1 instruments, making HA-price-derived returns unsuitable for strategy evaluation.

## Question

How large is the distortion between Heiken Ashi synthetic prices and real prices, and does it vary by volatility regime?

## Scope Boundaries

- **Chart Types**: 1-minute time bars and Heiken Ashi only.
- **Chart Type Parameters**: Heiken Ashi generated from 1-minute source bars; 1-minute time bars as real-price baseline.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full available dataset per instrument with nested chronological split. First 70% = analysis set; within that, first 70% = train segment and last 30% = test segment. Final 30% = global holdout.
- **Global holdout**: The final 30% of the full chronologically ordered dataset must not be loaded, inspected, summarized, plotted, or used in any capacity.
- **Look-ahead bias prevention**: Heiken Ashi is computed sequentially from completed source bars. Distortion is evaluated at each source bar's `CloseTime`.
- **Synthetic price discipline**: This experiment intentionally measures HA synthetic-price distortion. It must not treat HA returns as tradable returns or use them for strategy P&L.
- **Exclusions**: No Line Break or Renko analysis, no strategy backtesting, no predictive modelling, no higher timeframe HA, no claim that lower HA volatility is improved risk.

## Success / Failure Criteria

- **Evidence FOR**: On all 4 instruments, absolute HA close-to-close return volatility is at least 30% lower than real close-to-close return volatility, and median absolute HA return magnitude is at least 20% lower than real return magnitude.
- **Evidence AGAINST**: Fewer than 3 instruments meet either compression threshold, or HA compression is negligible with bootstrap confidence intervals overlapping zero on most instruments.
- **Inconclusive**: Compression is present but below threshold, regime-specific effects dominate the aggregate result, or data quality prevents valid HA generation for at least 3 instruments.

## Complexity Budget

- Max statistical tests: 2
- Max visualisations: 4
- Max new code modules: 1

## Data Requirements

Generate Heiken Ashi from analysis-set 1-minute time bars only. Compare `HAClose` changes to `RealClose` changes at identical `CloseTime` values. Stratify by low/medium/high volatility regimes derived from real time-bar returns.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
bars = scan.slice(0, int(total_rows * 0.7)).collect()
```

## Suggested Direction

Report compression ratios for return magnitude, realised volatility, high-low range, and direction-change frequency. Keep the conclusion tightly framed around synthetic-price distortion and risk of misusing HA prices.
