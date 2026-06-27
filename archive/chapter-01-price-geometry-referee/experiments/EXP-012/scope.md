# Experiment: EXP-012 - Fresh-Draw Loose Referee Ratification

## Hypothesis

On each domain, the EXP-011-recommended loose operating point reproduces its Phase 002 operating characteristics on fresh synthetic draws: gate FPR <= alpha0 at D-prec precision, MDE within one edge-grid step of the Phase 002 value, and economically sub-material pass rate at the operating MDE within +/-0.10 absolute of the Phase 002 value while not exceeding 0.50. The 4h domain must also pass the split-sensitivity gate from the checkpoint design.

## Question

Does the fixed EXP-011 loose referee point, tau 0.75 / 0.25 / 0.5 on 5m / 1h / 4h, earn adoption per domain on fresh seeds, or does the domain fall back to the strict point?

## Scope Boundaries

- **Data Views**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains. The 5m domain uses strict coverage; 1h and 4h use `min_coverage=0.90`.
- **Parameters**: Domains 5m/1h/4h; instruments EURUSD, XAUUSD, BTCUSD, USTEC; alpha grid `{0.10, 0.05, 0.01}` with primary `alpha0 = 0.05`; EXP-011 tau point fixed at 5m `0.75`, 1h `0.25`, 4h `0.5`; precision target 95% Wilson half-width <=0.03 for FPR and <=0.05 for TPR; fresh known-null and known-positive seeds disjoint from Phase 001/002 seeds.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, unchanged from the checkpoint invariants.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set; final 30% = global holdout. Within the analysis set, use the mandated 70/30 chronological train/test split, except the 4h split-sensitivity check also uses the anchored walk-forward K=5 protocol specified by the checkpoint.
- **Global holdout**: The final 30% of the full dataset must not be loaded, inspected, or used in any capacity. Fresh means new seeds, not new real data.
- **Look-ahead bias prevention**: Domain bars are ordered and split by canonical `CloseTime` timestamps from the base 1-minute data. Synthetic draws and referee inputs must use only data available at or before the evaluated timestamp.
- **Real-price outcome discipline**: Direction-adjusted returns and referee effects use real OHLC domain `Close` prices only.
- **Metric denominators**: FPR denominator is fresh null draws for each domain/referee/protocol cell. TPR and MDE denominators are fresh positive draws for each domain/referee/protocol/edge cell. Sub-material pass-rate denominator is the loose-referee gate-passing fresh positive draws at the operating MDE. Zero-pass cells report finite zero rates with Wilson intervals; do not report percentage improvement from a zero baseline.
- **Exclusions**: Re-selecting tau; changing the strict, minimal, or loose referee definitions; tuning thresholds; using Phase 003 measurement to revise the operating point; real candidate signals; chart-type candidates; bid/ask spread inference; any use of the global holdout.

## Success / Failure Criteria

- **Evidence FOR**: Per domain, adopt the loose point iff all checkpoint adoption conditions pass: FPR <= alpha0 at D-prec, fresh-draw MDE within one edge-grid step of the Phase 002 MDE, and sub-material pass rate within +/-0.10 of the Phase 002 value and <=0.50. For 4h, the single chronological split and anchored walk-forward K=5 protocol must also agree: their fresh-draw 4h gate MDEs are within one edge-grid step and both hold FPR <= alpha0 at D-prec.
- **Evidence AGAINST**: Per domain, any failed adoption condition means strict fallback for that domain. For 4h, failed protocol agreement also means strict fallback.
- **Inconclusive**: A domain or protocol cell is inconclusive only when the fresh-draw measurement cannot meet D-prec. Under-powered cells are reported as under-powered, not forced into adoption.

## Complexity Budget

- Max statistical tests: 4
- Max visualisations: 4
- Max new code modules: 1

## Data Requirements

Use the EXP-001-validated substrate and the EXP-003 calibration harness `python/src/xen/referee_calibration.py` unchanged. Reuse the corrected EXP-010 test-size-weighted, stratified pooled-OOS estimator for the 4h anchored walk-forward split-sensitivity gate. Record fresh seeds in `run_metadata.json` and verify they are disjoint from Phase 001/002 seeds.

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

Run one fixed-point ratification measurement. Produce per-domain adoption decisions with FPR, MDE, sub-material pass rate, and 4h protocol agreement stated explicitly. Do not use the fresh measurement to choose a new tau.
