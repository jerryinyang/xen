# Experiment: EXP-018 - Revised Incremental Referee Portfolio-Fitness Calibration

## Hypothesis

The revised incremental referee has a finite portfolio-fitness MDE at FPR <= alpha0 on each domain across the unchanged P3-D-dependence grid, and redundancy-null FPR remains controlled at the synchronous-high-overlap-null_R corner where EXP-015 failed.

## Question

After removing L2 and freezing L4'/L5, what incremental net edge beyond a reference signal can the revised unit reliably detect per domain, and does shared R-C structure cause false positives?

## Scope Boundaries

- **Data Views**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains. The 5m domain uses strict coverage; 1h and 4h use `min_coverage=0.90`. No chart-type candidates are in scope.
- **Parameters**: Domains 5m/1h/4h; instruments EURUSD, XAUUSD, BTCUSD, USTEC; alpha grid `{0.10, 0.05, 0.01}` with primary `alpha0 = 0.05`; precision target 95% Wilson half-width <= 0.03 for FPR and <= 0.05 for TPR; revised gate `L1 and L3 and L4' and L5`; L2 absent; L5 strict `ci_lower_bps > materiality`; EXP-013 substrate and D-incr-form estimator reused unchanged; inherited edge grid from the Phase 003 calibration artifacts reused without expansion or retuning.
- **Dependence grid**: Reused unchanged from P3-D-dependence: shared-latent-state strength `{independent, moderate about 0.4, high about 0.8}`; active-overlap `{low, medium, high}`; lead/lag `{synchronous, C lags R by 1 bar, C leads R by 1 bar}`; reference strength `{null R, R at domain MDE}`.
- **Binding stress corner**: The synchronous, high-overlap, null_R corner that refuted EXP-015 must be reported explicitly for every domain.
- **Dependence-grid construction**: Each domain/instrument/grid-cell seed uses the reused EXP-013 latent-state substrate and the unchanged P3-D-dependence construction rules. Cells outside predeclared construction acceptance bands are reported as construction-invalid or under-powered before outcome measurement, not silently pooled.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, unchanged from checkpoint invariants.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set; final 30% = global holdout. Within the analysis set, use the mandated 70/30 chronological train/test split.
- **Global holdout**: The final 30% of the full dataset must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: R and C are generated and evaluated only from information available at or before each `CloseTime`. Lead/lag cells must be constructed without using information after the evaluated timestamp.
- **Real-price outcome discipline**: Incremental returns use real OHLC domain prices only.
- **Metric denominators**: Redundancy-null FPR denominator is null draws within each domain/dependence-grid cell. TPR/MDE denominator is positive draws within each domain/dependence-grid/edge cell. Incremental-edge denominator remains bars where the combined position differs from R-alone. Zero-pass cells report finite zero rates with Wilson intervals, not percentage improvement from zero.
- **MDE aggregation rule under dependence**: Compute `cell_mde_bps` separately for every dependence-grid cell that meets construction acceptance and D-prec. A cell has finite MDE only if FPR `<= alpha0` with Wilson half-width `<= 0.03` and TPR reaches `>= 0.80` with Wilson half-width `<= 0.05` over the inherited edge grid. The domain headline MDE is the maximum finite `cell_mde_bps` across qualifying cells, not a pooled average. A qualifying cell with FPR control but no finite MDE refutes that domain's calibration for the dependence stress; under-powered cells are reported separately and never converted to pass/fail.
- **Diagnostics required by the redesign**: Report retained-leg pass rates, verdict pass rates, and per-instrument TPR diagnostics by dependence cell so any second refutation identifies the binding retained leg or instrument rather than only the final verdict.
- **Dependencies**: EXP-013 substrate and EXP-017 revised logic correctness must pass. EXP-003 provides the inherited strict-gate MDE reference used in the dependence grid. If the revised implementation touches shared estimator/CI code paths, EXP-013 must be re-run before EXP-018.
- **Exclusions**: Real candidate signals; chart-type candidates; re-tuning the revised gate against EXP-015 or EXP-018 output; changing the strict gate or EXP-012 ratified-loose referee; suite integration dogfood; using linear residualization as qualifying evidence; any use of the global holdout.

## Success / Failure Criteria

- **Evidence FOR**: For each domain, every qualifying dependence-grid cell controls redundancy-null FPR at `<= alpha0`, every qualifying positive cell has finite `cell_mde_bps`, the synchronous-high-overlap-null_R corner controls FPR and attains finite MDE, and the reported domain MDE is the worst-case finite cell MDE across qualifying cells.
- **Evidence AGAINST**: A domain has no finite MDE at D-prec, any qualifying positive grid cell has no finite MDE over the inherited edge grid, or dependence drives redundancy-null FPR above `alpha0` in any qualifying grid cell.
- **Inconclusive**: Any cell that cannot meet D-prec is reported as under-powered. Under-powered 4h or dependence-corner cells are disclosed with denominators and are not forced to a verdict.

## Complexity Budget

- Max statistical tests: 4
- Max visualisations: 5
- Max new code modules: 1

## Data Requirements

EXP-013 and EXP-017 must pass before EXP-018 executes. The implementation must generate known-truth R-C cases across the unchanged checkpoint dependence grid, apply the revised incremental referee, produce draw-level verdicts and retained-leg states, summarize FPR/TPR/MDE with Wilson intervals, explicitly report the synchronous-high-overlap-null_R corner, and disclose under-powered or construction-invalid cells.

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

Treat the dependence stress as the core calibration, not an appendix. Report domain MDEs together with the dependence cells and retained legs that pass, fail, or are under-powered, with special attention to the EXP-015 failure corner.
