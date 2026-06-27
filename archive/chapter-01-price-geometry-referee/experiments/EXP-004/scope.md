# Experiment: EXP-004 - Real Dogfood Consistency Anchor

## Hypothesis

Real Donchian-channel breakout and MA-crossover verdicts are consistent with where their measured net effect sizes fall on the calibrated per-domain MDE map from EXP-003.

## Question

Do real, simple price-based candidates behave consistently with the synthetic referee calibration map?

## Scope Boundaries

- **Data Views**: Base 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains. No chart-type views are in scope.
- **Candidate strategies**: Donchian breakout with lookback 20; MA crossover with fast window 20 and slow window 50. These parameters are fixed and not tuned.
- **Referees**: Minimal baseline referee and 5-check gate-stack referee at `alpha=0.05`.
- **Calibration reference**: EXP-003 `mde_summary.csv`.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Dependencies**: EXP-003 must have produced an MDE summary. EXP-004 is inconclusive where EXP-003 MDE is missing or imprecise.
- **Time range**: Full dataset with nested chronological split per instrument file. First 70% = analysis set; final 30% = global holdout and is never used.
- **Global holdout**: The final 30% of each source file must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: Donchian uses only prior highs/lows; MA signals use closes available at bar `t`; both are evaluated on `t -> t+1` real Close-to-Close returns.
- **Real-price outcome discipline**: All strategy returns use real domain `Close` prices and flat scoped cost defaults. No synthetic chart prices are in scope.
- **Exclusions**: Parameter optimization, strategy improvement, chart-type candidates, stop/target logic, walk-forward validation, and any revision of referee rules based on dogfood results.

## Success / Failure Criteria

- **Evidence FOR**: For each strategy/domain/referee cell with finite MDE, a pass occurs when the measured-effect CI lower bound is at or above MDE, a reject occurs when the measured-effect point estimate is below MDE, and either verdict is accepted inside the predeclared grey band of one MDE grid half-step.
- **Evidence AGAINST**: A pass with measured effect materially below MDE or a reject with measured effect materially above MDE.
- **Inconclusive**: EXP-003 has no finite MDE for the domain/referee cell, the candidate has insufficient effective sample, or the result falls in the grey band.

## Complexity Budget

- Max statistical tests: 2
- Max visualisations: 3
- Max new code modules: 0

## Data Requirements

Load only the first 70% chronological analysis slice from each 1-minute source file. Resample domains after holdout exclusion. Generate candidate positions from real domain bars only.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)
bars = scan.slice(0, analysis_cutoff).collect()
```

## Suggested Direction

Treat inconsistencies as a synthetic-vs-real DGP gap, not as a prompt to tune the referee inside this phase.

