# Experiment: EXP-019 - Assembled Suite Composition Anchor

## Hypothesis

Exploratory measurement only: conditional on EXP-018 validation and a confirmed dogfood reference book, the assembled suite of frozen strict referee, EXP-012 ratified-loose referee, and revised incremental fitness unit composes end to end on both paths: an EXP-009 dogfood negative path and a synthetic positive suite-level fixture.

## Question

Does the concluded qualification suite wire both reject and pass paths end to end before Phase 004 uses it on real signal exploration?

## Scope Boundaries

- **Data Views**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains for the real dogfood path, plus deterministic synthetic fixture data for the positive path. No chart-type candidates are in scope.
- **Parameters**: Domains 5m/1h/4h; instruments EURUSD, XAUUSD, BTCUSD, USTEC where inherited from EXP-009 and upstream suite artifacts; frozen Phase 001 strict gate stack; EXP-012 ratified-loose referee; revised incremental unit calibrated by EXP-018; dogfood reference book governed by D-dogfood-book.
- **D-dogfood-book precondition**: The active checkpoint records D-dogfood-book as confirmed by operator decision on 2026-06-05: R = EXP-009 Donchian(20) breakout (`donchian_20`), and candidates C = the remaining EXP-009 families (`ma_20_50`, `rsi_14`, `bollinger_20_2`, `macd_12_26_9`, `roc_20`) on the same instruments/domains. EXP-019 must not execute unless the corresponding reference-book input and manifest are present. This scope does not silently choose the book.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC for the real dogfood path, matching EXP-009.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set; final 30% = global holdout. Within the analysis set, use the mandated 70/30 chronological train/test split where real dogfood data is evaluated.
- **Global holdout**: The final 30% of the full dataset must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: Dogfood signals, synthetic fixture signals, and incremental reference/candidate comparisons use only data available at or before each `CloseTime`.
- **Real-price outcome discipline**: All standalone and incremental return metrics use real OHLC domain prices. No HA, Renko, or other synthetic chart construction price is in scope.
- **Metric denominators**: Standalone referee denominators follow the frozen referee artifacts. Incremental-edge denominator is bars where the combined position differs from R-alone. Suite-path denominator is all scoped dogfood cells for the negative path and all predeclared synthetic positive fixture cells for the positive path. Zero-baseline cells report finite levels and intervals, not percentage improvement from zero.
- **Negative path expectation**: EXP-009 dogfood against the confirmed D-dogfood-book reference R is expected to produce standalone rejections and no material positive incremental edge because EXP-009 established the family sits below every MDE. This is a composition-path expectation, not new signal exploration.
- **Synthetic positive fixture manifest**: Before execution, the positive path must record a fixture manifest with exact rows, expected suite outputs, non-redundant R/C relationship, standalone planted edge sufficient to pass both standalone referees, and incremental planted edge sufficient to register positive incremental fitness against R. Expected positive-path outputs are strict referee PASS, ratified-loose referee PASS, revised incremental unit POSITIVE_INCREMENTAL, and suite path status PASS_PATH_EXERCISED.
- **Dependencies**: EXP-012, EXP-018, and EXP-009 must be available. EXP-018 must validate the revised unit before EXP-019 executes. If EXP-019 is dropped, the active checkpoint requires the positive-path composition check to migrate into EXP-018 rather than remain untested.
- **Exclusions**: Real signal exploration beyond the EXP-009 dogfood set; chart-type candidate signals; tuning dogfood strategies or the suite; changing EXP-012 adoption decisions; changing EXP-018 incremental calibration; programme-level multiplicity control; any use of the global holdout.

## Success / Failure Criteria

- **Evidence FOR integration completeness**: The real EXP-009 dogfood negative path runs through the assembled suite and reports standalone rejections and no positive incremental edge, while the synthetic positive path passes both standalone referees and registers a positive incremental edge against a non-redundant reference.
- **Evidence AGAINST integration completeness**: Either path cannot run after dependencies and D-dogfood-book are confirmed, upstream suite components cannot be assembled consistently, the synthetic positive path cannot exercise the pass path, or dogfood/reference wiring produces undefined suite outputs.
- **Inconclusive / blocked**: EXP-012 or EXP-018 is incomplete, the ratified-loose per-domain decision is unavailable, the revised incremental unit is not calibrated, or the dogfood reference book is not defined before execution.

## Complexity Budget

- Max statistical tests: 4
- Max visualisations: 5
- Max new code modules: 1

## Data Requirements

EXP-012, EXP-018, and EXP-009 must be available before EXP-019 executes. The implementation must assemble strict, ratified-loose, and revised incremental referee outputs into a single suite-level table. It must run both the dogfood negative path against the confirmed D-dogfood-book reference and the predeclared synthetic positive fixture. Required manifests: suite assembly, dogfood reference book, candidate slate, positive fixture construction, expected positive-path outputs, and blocker report for missing upstream artifacts.

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

Treat EXP-019 as an integration anchor, not a market-edge experiment. Its job is to prove the frozen suite can exercise both expected reject and expected pass wiring before Phase 004.
