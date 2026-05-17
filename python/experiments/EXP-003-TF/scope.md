# Experiment: EXP-003-TF - Timeframe Replication of Noise Filtering & Statistical Robustness

## Hypothesis

The EXP-003 hypothesis is retested unchanged on 15-minute and 1-hour source bars: under controlled source-bar noise injection, Line Break level 3 and Renko ATR-14 preserve directional and distributional statistics more stably than same-timeframe time bars on at least 3 of 4 instruments, while Heiken Ashi reduces variance but increases synthetic price distortion.

## Question

Do the EXP-003 noise-robustness findings replicate when deterministic perturbations are applied to 15-minute and 1-hour aggregated source bars?

## Scope Boundaries

- **Chart Types**: 15-minute and 1-hour time bars, Line Break, Renko, Heiken Ashi.
- **Chart Type Parameters**: Source timeframes 15-minute and 1-hour; Line Break level 3; Renko ATR period 14; Heiken Ashi generated from each aggregated source timeframe.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full available dataset per instrument with nested chronological split. First 70% = analysis set; within that, first 70% = train segment and last 30% = test segment. Final 30% = global holdout.
- **Global holdout**: The final 30% of the full chronologically ordered 1-minute source dataset must not be loaded, inspected, summarized, plotted, aggregated, perturbed, or used in any capacity.
- **Look-ahead bias prevention**: Apply the 70% source-data cutoff before higher-timeframe aggregation. Noise is applied only to aggregated source bars within the analysis set, then chart types are regenerated sequentially from perturbed bars.
- **Synthetic price discipline**: No strategy P&L. Heiken Ashi synthetic returns may be measured only as distortion diagnostics against `RealClose`, not as tradable returns.
- **Exclusions**: No replacement or modification of EXP-003, no stochastic simulation sweep beyond fixed deterministic perturbation definitions, no strategy testing, no parameter optimization, no tick-level noise model, and no source timeframes beyond 15-minute and 1-hour.

## Success / Failure Criteria

- **Evidence FOR**: For each tested timeframe, at the 20% noise level, Line Break or Renko has at least 25% lower relative drift than same-timeframe time bars in at least two of three metrics: direction stability, return variance stability, and complexity stability; this must hold on at least 3 instruments. For Heiken Ashi, return variance stability uses HAClose returns as a non-tradable distortion diagnostic per synthetic price discipline.
- **Evidence AGAINST**: For each tested timeframe, same-timeframe time bars have equal or lower relative drift than Line Break and Renko in at least two of three metrics on at least 3 instruments.
- **Inconclusive**: Stability rankings change materially across noise levels, effects are below threshold, perturbation produces invalid OHLC bars after repair for more than 5% of rows, or the 15-minute and 1-hour outcomes conflict materially.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 5
- Max new code modules: 1

## Data Requirements

Load each instrument's 1-minute time-bar Parquet data lazily, sort by `CloseTime`, determine the chronological 70% analysis cutoff, and materialize only rows before that cutoff. Aggregate the analysis rows into complete 15-minute and 1-hour OHLCV bars, dropping incomplete boundary buckets and reporting dropped counts. Use deterministic perturbations at 0%, 10%, 20%, and 30% of eligible aggregated source bars. Perturb close values according to an instrument-timeframe deterministic seed. After perturbation, repair full OHLC integrity so that `High >= max(Open, Close)` and `Low <= min(Open, Close)` for every aggregated bar. All perturbation happens after holdout exclusion and aggregation.

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

Compare each perturbed timeframe dataset to its unperturbed baseline per instrument and chart type. Focus on relative drift in simple descriptive metrics and explicitly compare whether the EXP-003 Renko and HA observations are preserved or attenuated at higher timeframes.
