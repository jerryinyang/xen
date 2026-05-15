# Experiment: EXP-003 - Noise Filtering & Statistical Robustness

## Hypothesis

Under controlled source-bar noise injection, Line Break level 3 and Renko ATR-14 preserve directional and distributional statistics more stably than 1-minute time bars on at least 3 of 4 instruments, while Heiken Ashi reduces variance but increases synthetic price distortion.

## Question

How robust are each chart type's descriptive statistics when the source 1-minute bars are perturbed by predefined synthetic noise?

## Scope Boundaries

- **Chart Types**: 1-minute time bars, Line Break, Renko, Heiken Ashi.
- **Chart Type Parameters**: Line Break level 3; Renko ATR period 14; Heiken Ashi generated from 1-minute source bars; 1-minute time bars as baseline.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full available dataset per instrument with nested chronological split. First 70% = analysis set; within that, first 70% = train segment and last 30% = test segment. Final 30% = global holdout.
- **Global holdout**: The final 30% of the full chronologically ordered dataset must not be loaded, inspected, summarized, plotted, or used in any capacity.
- **Look-ahead bias prevention**: Noise is applied only to source bars within the analysis set, then chart types are regenerated sequentially from perturbed bars.
- **Synthetic price discipline**: No strategy P&L. Heiken Ashi synthetic returns may be measured only as distortion diagnostics against `RealClose`, not as tradable returns.
- **Exclusions**: No stochastic simulation sweep beyond fixed deterministic perturbation definitions, no strategy testing, no parameter optimization, no tick-level noise model.

## Success / Failure Criteria

- **Evidence FOR**: At the 20% noise level, Line Break or Renko has at least 25% lower relative drift than time bars in at least two of three metrics: direction stability, variance ratio stability, and complexity stability; this must hold on at least 3 instruments.
- **Evidence AGAINST**: Time bars have equal or lower relative drift than Line Break and Renko in at least two of three metrics on at least 3 instruments.
- **Inconclusive**: Stability rankings change materially across noise types, effects are below threshold, or perturbation produces invalid OHLC bars after repair for more than 5% of rows.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 5
- Max new code modules: 1

## Data Requirements

Use deterministic perturbations at 0%, 10%, 20%, and 30% of eligible source bars. Perturb close values or direction signs according to a documented deterministic seed derived from instrument and timestamp, then repair OHLC integrity so `High >= max(Open, Close)` and `Low <= min(Open, Close)`. All perturbation happens after holdout exclusion.

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

Compare each perturbed dataset to its unperturbed baseline per instrument and chart type. Focus on relative drift in simple descriptive metrics rather than modelling the noise process.
