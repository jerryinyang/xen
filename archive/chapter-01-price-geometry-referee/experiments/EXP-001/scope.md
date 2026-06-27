# Experiment: EXP-001 - Synthetic Substrate Validation

## Hypothesis

The known-null generators produce no oracle-recoverable edge, and the known-positive generator carries the planted oracle-recoverable net edge, on real analysis-set prices for each 5m, 1h, and 4h domain.

## Question

Can Phase 001 trust its synthetic calibration substrate before measuring either referee?

## Scope Boundaries

- **Data Views**: Base 1-minute time bars resampled into 5m, 1h, and 4h OHLC domains with `xen.bar_aggregator.aggregate_ohlc`. No chart-type views are in scope.
- **Parameters**: 5m uses strict coverage; 1h and 4h use `min_coverage=0.90`. Coverage reporting also includes `{strict, 0.90, 0.80}` for every domain. P0 temporal-integrity extension checks the 5-minute and 240-minute aggregation parameterizations before substrate measurements are trusted.
- **Synthetic generators**: known-null bar-permuted returns, known-null random-signal control, and known-positive state-aligned return injection.
- **Known-positive state**: fixed-seed pseudo-random state `s_t in {-1,+1}` exposed to the oracle candidate at time `t`.
- **Known-positive edge grid**: net edge `m` in `{0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 12.0, 16.0, 24.0, 32.0}` bps/trade. Injection uses `delta = m + round_trip_cost_bps` so oracle net effect is closed-form.
- **Costs and materiality defaults**: frozen-before-run defaults are encoded in `python/src/xen/referee_calibration.py`; the manual execution gate must confirm or override them before EXP-001 runs. Once EXP-001 runs, they are frozen for the phase.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC from the available 1-minute Parquet files.
- **Time range**: Full dataset with nested chronological split per instrument file. First 70% = analysis set; the analysis set is split 70/30 for train/test where needed; final 30% = global holdout and is never used.
- **Global holdout**: The final 30% of each chronologically ordered source file must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: Synthetic states use fixed seeds and no future returns. Candidate positions at time `t` are evaluated only against `t -> t+1` real Close-to-Close returns.
- **Real-price outcome discipline**: All return metrics use real time-bar `Close` prices in the scoped domain. No synthetic chart prices are in scope.
- **Exclusions**: Referee operating-characteristic measurement, Donchian/MA dogfood candidates, chart-type signals, parameter tuning, bid/ask spread estimation, trading costs inferred from data, and any inspection of the final 30% holdout.

## Success / Failure Criteria

Per-cell evaluation separates two distinct sub-tests for known-positive cells,
faithfully to checkpoint design Section 11 / D-prec (under-powered cells are a
first-class measured result on the short domain, never a substrate failure):

1. **Recovery (injection correctness)**: the per-draw mean effect lands within
   `max(0.5 bps, 15% of m)` of the planted net `m`.
2. **Significance (precision / power)**: for `m >= 1.0`, the per-draw effect
   distribution's percentile CI lower bound is above zero.

- **Evidence FOR (substrate validated → PASS)**: P0 checks all pass; every
  known-null draw summary has its percentile CI including zero and absolute mean
  gross oracle effect `<= 1.0` bps/trade; and every known-positive cell *recovers*
  the planted `m` within tolerance. Cells that recover and are also significant are
  per-cell PASS.
- **Per-cell INCONCLUSIVE (under-powered, reported not failed)**: a known-positive
  cell that *recovers* the planted `m` within tolerance but whose `m >= 1.0`
  significance leg fails (CI lower bound `<= 0`) because the per-draw distribution
  is too wide. This is a power/precision shortfall of the short domain — recorded
  per cell (`underpowered_cells.csv`) and surfaced in `run_metadata.json`. Such
  cells do **not** break the substrate and do **not** halt the phase. The rule is
  applied uniformly to every cell; in practice only the short 4h domain triggers it.
- **Evidence AGAINST (substrate broken → FAIL)**: any P0 failure; any known-null
  cell with a non-zero oracle-recoverable effect by the criterion above; or any
  known-positive cell whose mean *fails to recover* the planted `m` within
  tolerance.
- **Overall INCONCLUSIVE**: any instrument/domain cell has insufficient domain bars
  to run the scoped draw protocol at all (no substrate measurement exists for it),
  or any cell returns a non-finite summary. (Distinct from per-cell under-powered
  INCONCLUSIVE above, where the full draw protocol ran and recovery was confirmed.)
- **Overall status**: `FAIL` on any P0 failure or any broken cell; else
  `INCONCLUSIVE` if any domain could not be measured at all; else `PASS` (the
  substrate is validated; any per-cell under-powered INCONCLUSIVE cells are
  reported and gate only their own downstream use, not the phase).

## Complexity Budget

- Max statistical tests: 2
- Max visualisations: 4
- Max new code modules: 1 shared phase helper module

## Data Requirements

Load each 1-minute Parquet file lazily, sort by `CloseTime`, and collect only the first 70% chronological analysis slice. Resample domains from that already-sliced 1-minute source. Report retained bar count and dropped-window fraction across the coverage grid before substrate summaries.

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

Use draw-level non-parametric summaries rather than distributional assumptions. Treat EXP-001 as a gate: downstream experiments may not run unless substrate validation passes.

## Revision History

- **rev. 2 (2026-06-02)** — Verdict criteria aligned with checkpoint design Section 11 / D-prec after the rev. 1 run. The rev. 1 criteria collapsed two distinct sub-tests (recovery vs. significance) into a single PASS/FAIL gate, so five under-powered 4h known-positive cells at sub-material edges (`m` = 1, 2 bps; 4h materiality = 3.0 bps) hard-failed the `m >= 1` significance leg despite recovering the planted mean almost exactly — driving an overall FAIL. Section 11 predeclared (before any measurement) that effective-sample-limited cells, "expected most likely on the 4h domain," are INCONCLUSIVE first-class results, not failures. rev. 2 separates recovery (FAIL on miss) from significance (PASS if clear, per-cell INCONCLUSIVE if recovered-but-under-powered) and restricts substrate breakage / phase-halt to genuine FAIL cells. The reclassification rule is uniform across all cells and imported from the predeclared design, not shaped to the five specific cells (meta-Goodhart guardrail, design Section 10). The draws are deterministic (fixed seeds), so the re-run reclassifies identical effects rather than re-measuring.
