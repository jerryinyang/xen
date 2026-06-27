# Experiment: EXP-015 - Incremental Referee Portfolio-Fitness Calibration

## Hypothesis

The incremental referee has a finite portfolio-fitness MDE at FPR <= alpha0 on each domain, and its redundancy-null FPR remains controlled under the checkpoint's reference/candidate dependence grid.

## Question

What incremental net edge beyond a reference signal can the incremental referee reliably detect per domain, and does shared R-C structure cause false positives?

## Scope Boundaries

- **Data Views**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains. The 5m domain uses strict coverage; 1h and 4h use `min_coverage=0.90`.
- **Parameters**: Domains 5m/1h/4h; instruments EURUSD, XAUUSD, BTCUSD, USTEC; alpha grid `{0.10, 0.05, 0.01}` with primary `alpha0 = 0.05`; precision target 95% Wilson half-width <=0.03 for FPR and <=0.05 for TPR; inherited incremental edge grid from EXP-003/EXP-012 calibration artifacts; fixed incremental estimator and leg mapping from EXP-013/014.
- **Dependence grid**: R-C position agreement / shared-latent-state strength `{independent, moderate rho about 0.4, high rho about 0.8}`; active-overlap fraction `{low, medium, high}`; lead/lag alignment `{synchronous, C lags R by 1 bar, C leads R by 1 bar}`; reference edge strength `{null R, R at its domain MDE}`.
- **Dependence-grid construction**: Each domain/instrument/grid-cell seed uses the EXP-013 latent-state substrate, then applies deterministic mask reshaping until realized diagnostics meet these predeclared acceptance bands before measurement:
  - Position agreement/shared-state strength is measured as signed R-C agreement correlation over rows where either R or C is active: independent `abs(rho) <= 0.05`, moderate `0.40 +/- 0.05`, high `0.80 +/- 0.05`.
  - Active-overlap fraction is `both_active / max(C_active, 1)`: low `0.20 +/- 0.05`, medium `0.50 +/- 0.05`, high `0.80 +/- 0.05`.
  - Lead/lag alignment is exact after timestamp ordering: synchronous uses `R_t` with `C_t`; `C lags R by 1 bar` uses `C_t` aligned to `R_{t-1}`; `C leads R by 1 bar` uses `C_t` aligned to `R_{t+1}` but generated from seed/latent state only, never from future returns.
  - Reference edge strength is implemented as either no planted reference drift (`null R`) or planted R-alone net edge equal to the domain's inherited strict gate-stack MDE at `alpha0`.
  Cells outside these acceptance bands after deterministic construction attempts are reported as construction-invalid/under-powered before outcome measurement, not silently pooled.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, unchanged from checkpoint invariants.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set; final 30% = global holdout. Within the analysis set, use the mandated 70/30 chronological train/test split.
- **Global holdout**: The final 30% of the full dataset must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: R and C are generated and evaluated only from information available at or before each `CloseTime`. Lead/lag cells must be constructed without using information after the event timestamp.
- **Real-price outcome discipline**: Incremental returns use real OHLC domain prices only.
- **Metric denominators**: Redundancy-null FPR denominator is null draws within each domain/dependence-grid cell. TPR/MDE denominator is positive draws within each domain/dependence-grid/edge cell. Incremental-edge denominator remains bars where the combined position differs from R-alone. Zero-pass cells report finite zero rates with Wilson intervals, not percentage improvement from zero.
- **MDE aggregation rule under dependence**: Compute `cell_mde_bps` separately for every dependence-grid cell that meets construction acceptance and D-prec. A cell has finite MDE only if FPR `<= alpha0` with Wilson half-width `<= 0.03` and TPR reaches `>= 0.80` with Wilson half-width `<= 0.05` over the inherited edge grid. The domain headline MDE is the maximum finite `cell_mde_bps` across qualifying cells, not a pooled average. A qualifying cell with FPR control but no finite MDE refutes that domain's calibration for the dependence stress; under-powered cells are reported separately and never converted to pass/fail.
- **Exclusions**: Real candidate signals; chart-type candidates; re-tuning the incremental estimator or leg mapping; standalone referee ratification; suite integration dogfood; using linear residualization as qualifying evidence; any use of the global holdout.

## Success / Failure Criteria

- **Evidence FOR**: For each domain, every qualifying dependence-grid cell controls redundancy-null FPR at `<= alpha0`, every qualifying positive cell has finite `cell_mde_bps`, and the reported domain MDE is the worst-case finite cell MDE across those cells.
- **Evidence AGAINST**: A domain has no finite MDE at D-prec, any qualifying positive grid cell has no finite MDE over the inherited edge grid, or dependence drives redundancy-null FPR above alpha0 in any qualifying grid cell.
- **Inconclusive**: Any cell that cannot meet D-prec is reported as under-powered. Under-powered 4h cells are not forced to a verdict.

## Complexity Budget

- Max statistical tests: 4
- Max visualisations: 5
- Max new code modules: 1

## Data Requirements

EXP-013 and EXP-014 must pass before EXP-015 executes. The implementation must generate known-truth R-C cases across the checkpoint dependence grid, apply the incremental referee, produce draw-level verdicts, summarize FPR/TPR/MDE with Wilson intervals, and report under-powered cells.

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

Treat dependence stress as core calibration. Report domain MDEs together with the dependence cells that pass, fail, or are under-powered rather than collapsing shared-structure risk into a single easy average.
