# Experiment: EXP-006-TF - Timeframe Replication of Heiken Ashi Synthetic Price Distortion Quantification

## Hypothesis

The EXP-006 hypothesis is retested unchanged on 15-minute and 1-hour source bars: Heiken Ashi synthetic prices compress realised return magnitude and volatility by at least 30% versus real same-timeframe prices on all 4 instruments, making HA-price-derived returns unsuitable for strategy evaluation.

## Question

How large is the distortion between Heiken Ashi synthetic prices and real prices on 15-minute and 1-hour source bars, and does the EXP-006 synthetic-price conclusion replicate beyond 1-minute bars?

## Scope Boundaries

- **Chart Types**: 15-minute and 1-hour time bars and Heiken Ashi only.
- **Chart Type Parameters**: Source timeframes 15-minute and 1-hour; Heiken Ashi generated from each aggregated source timeframe.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full available dataset per instrument with nested chronological split. First 70% = analysis set; within that, first 70% = train segment and last 30% = test segment. Final 30% = global holdout.
- **Global holdout**: The final 30% of the full chronologically ordered 1-minute source dataset must not be loaded, inspected, summarized, plotted, aggregated, or used in any capacity.
- **Look-ahead bias prevention**: Apply the 70% source-data cutoff before aggregation. Heiken Ashi is computed sequentially from completed aggregated source bars. Distortion is evaluated at each source bar's `CloseTime`. Regime labels are calibrated on the train segment and applied only to later timestamps.
- **Synthetic price discipline**: This experiment intentionally measures HA synthetic-price distortion. It must not treat HA returns as tradable returns or use them for strategy P&L.
- **Exclusions**: No replacement or modification of EXP-006, no Line Break or Renko analysis, no strategy backtesting, no predictive modelling, no higher timeframes beyond 15-minute and 1-hour, and no claim that lower HA volatility is improved risk.

## Success / Failure Criteria

- **Evidence FOR**: For each tested timeframe, on all 4 instruments, absolute HA close-to-close return volatility is at least 30% lower than real same-timeframe close-to-close return volatility, and median absolute HA return magnitude is at least 20% lower than real return magnitude.
- **Evidence AGAINST**: For each tested timeframe, fewer than 3 instruments meet either compression threshold, or HA compression is negligible with bootstrap confidence intervals overlapping zero on most instruments.
- **Inconclusive**: Compression is present but below threshold, regime-specific effects dominate the aggregate result, data quality prevents valid HA generation for at least 3 instruments, or the 15-minute and 1-hour outcomes conflict materially.

## Complexity Budget

- Max statistical tests: 2
- Max visualisations: 4
- Max new code modules: 1

## Data Requirements

Load each instrument's 1-minute time-bar Parquet data lazily, sort by `CloseTime`, determine the chronological 70% analysis cutoff, and materialize only rows before that cutoff. Aggregate the analysis rows into complete 15-minute and 1-hour OHLCV bars, dropping incomplete boundary buckets and reporting dropped counts. Generate Heiken Ashi from each aggregated analysis timeframe only. Compare `HAClose` changes to `RealClose` changes at identical `CloseTime` values. Stratify by low/medium/high volatility regimes derived from real same-timeframe returns, with thresholds calibrated on the train segment and applied only to the later evaluation segment.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
source_analysis = scan.slice(0, int(total_rows * 0.7)).collect()
```

## Suggested Direction

Report compression ratios for return magnitude, realised volatility, high-low range, and direction-change frequency by instrument and timeframe. Keep the conclusion tightly framed around synthetic-price distortion and whether the EXP-006 warning generalizes to higher source timeframes.
