# Experiment: EXP-013 - Incremental Substrate Validation

## Hypothesis

The incremental substrate recovers a planted marginal edge within `max(0.5 bps, 15% of m)` and reads incremental edge approximately zero for the redundancy null where reference signal R and candidate signal C share structure but C adds no marginal edge.

## Question

Can the Track B incremental substrate measure known marginal edge beyond a reference signal without manufacturing phantom edge from shared R-C structure?

## Scope Boundaries

- **Data Views**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains. The 5m domain uses strict coverage; 1h and 4h use `min_coverage=0.90`.
- **Parameters**: Domains 5m/1h/4h; instruments EURUSD, XAUUSD, BTCUSD, USTEC; fixed known-truth R and C construction; additive position blend clipped to the per-domain position bound; cost charged on incremental turnover induced by C relative to R-alone; primary estimator is model-free marginal net P&L.
- **Incremental substrate construction**: For each instrument/domain/seed, generate a blockwise latent state `S_t in {-1,+1}` over eligible `t -> t+1` real-return rows, with deterministic episode lengths `{5m: 24, 1h: 8, 4h: 4}` bars and episode signs drawn from the recorded seed. Partition eligible rows into four seeded masks before returns are read: `R_only`, `C_change`, `overlap`, and `inactive`, targeting 25% / 25% / 25% / 25% of eligible rows within each latent-state sign where sample size permits. Set `R_t = S_t` on `R_only` and `overlap`, else 0. Set `C_t = S_t` on `C_change` and `overlap`, else 0. The additive-and-clipped combined book differs from R-alone only on `C_change`; that mask is the primary incremental-edge denominator.
- **Positive known-truth case**: On `C_change` rows only, plant gross drift in the direction of `C_t` so that, after applying the scoped incremental-turnover cost function, expected net marginal P&L on the denominator equals planted incremental edge `m`. Use inherited edge-grid magnitudes in bps and report the solved gross drift, incremental turnover cost, observed net marginal edge, and absolute recovery error.
- **Redundancy-null case**: Use the same latent state and R/C mask construction, but plant no marginal drift on `C_change` rows. R and C therefore share latent structure and overlap while C adds no known marginal edge. Any positive reading must come from estimator/referee behavior or random real-return noise, not planted edge.
- **Null and recovery thresholds**: Positive recovery passes when `abs(observed_net_bps - m) <= max(0.5 bps, 15% of m)`. The redundancy null passes only when `abs(observed_net_bps) <= max(0.5 bps, 15% of materiality_bps(domain))` and the 95% block-bootstrap CI lower bound is `<= 0`. It fails as phantom edge if the CI lower bound exceeds `materiality_bps(domain)` or the point estimate breaches the null tolerance with an entirely positive CI.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, unchanged from checkpoint invariants.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set; final 30% = global holdout. Within the analysis set, use the mandated 70/30 chronological train/test split.
- **Global holdout**: The final 30% of the full dataset must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: R and C are generated and evaluated only from information available at or before each `CloseTime`. The joint R-C series is ordered chronologically.
- **Real-price outcome discipline**: Incremental returns use real OHLC domain prices only. Incremental edge is `(combined book with C) - (combined book without C)` on real-price return contributions.
- **Metric denominators**: Primary denominator is bars where the combined position differs from R-alone. Zero-baseline cells use finite guards and report levels/intervals, not percentage improvement from zero.
- **Pre-execution confirmation gate**: The checkpoint requires operator confirmation or override of `D-incr-form`, `D-incr-substrate`, and `D-incr-legs` before EXP-013 executes. This scope records the checkpoint defaults and does not replace that confirmation. Stage 4 governance must record a dated confirmation/amendment and the token `PHASE003-TRACKB-PREDECLARATION-CONFIRMED` before any Track B measurement is produced.
- **Exclusions**: Calibration of the incremental referee; golden-fixture correctness; real candidate signals; chart-type candidates; linear residualization as a qualifying estimator; parameter tuning; any change to loader, `aggregate_ohlc`, generators, or frozen harness without re-validation; any use of the global holdout.

## Success / Failure Criteria

- **Evidence FOR**: Positive known-truth cases recover planted marginal edge within `max(0.5 bps, 15% of m)`, and the redundancy null reports no spurious positive incremental edge despite shared R-C structure.
- **Evidence AGAINST**: Any planted marginal edge cannot be recovered within tolerance, or the redundancy null shows a positive incremental edge that would qualify as phantom edge.
- **Inconclusive**: Effective sample or denominator is too small to evaluate the positive or redundancy case at the scoped precision. Under-powered cells are reported as such.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 4
- Max new code modules: 1

## Data Requirements

Track B may introduce new incremental machinery, `python/src/xen/incremental_referee.py` or equivalent. The implementation must produce the combined-with-C and R-alone net real-price return series, incremental turnover, eligible denominator, substrate construction manifest, planted-edge recovery table, redundancy-null table, and metadata documenting seeds, dependencies, denominators, threshold constants, and finite zero-baseline handling.

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

Build the smallest substrate test that proves the marginal-P&L estimator can recover known incremental edge and reject redundancy-null phantom edge before any incremental referee calibration is attempted.
