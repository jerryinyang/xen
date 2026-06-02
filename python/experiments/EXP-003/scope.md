# Experiment: EXP-003 - Referee Operating-Characteristic Calibration

## Hypothesis

The 5-check gate stack has a measurable empirical economic MDE at `FPR <= alpha0 = 0.05` on each domain, and its measured operating characteristics can be compared against the minimal baseline referee without touching the global holdout.

## Question

What are the per-domain FPR, TPR curve, economic MDE, and gate-leg pass rates for the minimal baseline referee and the 5-check gate stack?

## Scope Boundaries

- **Data Views**: Base 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains. No chart-type views are in scope.
- **Parameters**: 5m strict coverage; 1h and 4h `min_coverage=0.90`; alpha grid `{0.10, 0.05, 0.01}`; edge grid `{0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 12.0, 16.0, 24.0, 32.0}` bps/trade; `>=1000` null draws per domain/referee split across two null generators; `>=500` positive draws per edge-grid point; `>=1000` inner block-bootstrap resamples per verdict.
- **Referees**: minimal baseline referee and 5-check gate-stack referee with all five legs evaluated unconditionally.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Dependencies**: EXP-001 and EXP-002 must both have `overall_status == "PASS"`.
- **Time range**: Full dataset with nested chronological split per instrument file. First 70% = analysis set; final 30% = global holdout and is never used.
- **Global holdout**: The final 30% of each source file must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: Candidate states at time `t` are generated without future data and evaluated only against `t -> t+1` Close-to-Close returns. Bootstrap block length is estimated on train returns only.
- **Real-price outcome discipline**: All effects use real domain `Close` prices. No synthetic chart prices are in scope.
- **Exclusions**: Real Donchian/MA dogfood interpretation, referee redesign, loss-function tuning, walk-forward validation, chart-type candidates, and parameter optimization.

## Success / Failure Criteria

- **Evidence FOR**: For each reportable domain/referee cell, FPR Wilson half-width <= 0.03, TPR Wilson half-width <= 0.05 at the operating point, FPR <= alpha, and a finite MDE exists where TPR >= 0.80.
- **Evidence AGAINST**: FPR cannot be held at the alpha operating point, or no edge-grid point reaches TPR >= 0.80 with usable precision.
- **Inconclusive**: Effective sample or Monte Carlo precision is insufficient, especially on 4h, or dependency artifacts are missing/not passing.

## Complexity Budget

- Max statistical tests: 4
- Max visualisations: 5
- Max new code modules: 1 shared phase helper module

## Data Requirements

Load only the first 70% chronological analysis slice from each 1-minute source file. Resample domains after holdout exclusion. Use identical synthetic draws for both referees so baseline-vs-stack comparisons are paired.

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

Summarize rates with Wilson intervals and define MDE as the smallest planted net edge whose measured TPR reaches 0.80 while FPR is controlled at the scoped alpha.

