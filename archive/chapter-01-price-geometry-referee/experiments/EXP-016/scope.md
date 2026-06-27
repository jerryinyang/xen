# Experiment: EXP-016 - Assembled Suite Composition Anchor

## Hypothesis

Exploratory measurement only: the assembled suite of strict referee, ratified-loose referee, and incremental fitness unit composes end to end on both paths: a real EXP-009 dogfood negative path and a synthetic positive suite-level fixture.

## Question

Does the concluded qualification suite wire both reject and pass paths end to end before Phase 004 uses it on real signal exploration?

## Scope Boundaries

- **Data Views**: 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains for the real dogfood path, plus deterministic synthetic fixture data for the positive path. No chart-type candidates are in scope.
- **Parameters**: Domains 5m/1h/4h; instruments EURUSD, XAUUSD, BTCUSD, USTEC where inherited from EXP-009 and upstream suite artifacts; strict gate stack frozen from Phase 001; ratified-loose referee from EXP-012 per-domain decisions, including strict fallback where applicable; incremental unit calibrated by EXP-015.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC for the real dogfood path, matching EXP-009.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set; final 30% = global holdout. Within the analysis set, use the mandated 70/30 chronological train/test split where real dogfood data is evaluated.
- **Global holdout**: The final 30% of the full dataset must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: Dogfood signals, synthetic fixture signals, and incremental reference/candidate comparisons use only data available at or before each `CloseTime`.
- **Real-price outcome discipline**: All standalone and incremental return metrics use real OHLC domain prices. No HA, Renko, or other synthetic chart construction price is in scope.
- **Metric denominators**: Standalone referee denominators follow the frozen referee artifacts. Incremental-edge denominator is bars where the combined position differs from R-alone. Suite-path denominator is all scoped dogfood cells for the negative path and all predeclared synthetic positive fixture cells for the positive path. Zero-baseline cells report finite levels/intervals, not percentage improvement from zero.
- **Reference-book execution precondition**: The checkpoint specifies real EXP-009 dogfood "against a reference book" but does not name that reference book. EXP-016 must not invent one during implementation. Before execution, the reference book must be available from upstream approved Phase 003 artifacts or recorded as a design amendment/operator confirmation before results are read.
- **Synthetic positive fixture manifest**: Before execution, the positive path must record a fixture manifest with expected suite outputs. For each domain, construct candidate `C` on deterministic fixture rows using real-price-style return contributions and a non-redundant reference `R`:
  - Standalone planted net edge for `C` is `max(strict_mde_bps(domain), ratified_loose_or_fallback_mde_bps(domain)) + one_edge_grid_step(domain)`, read from approved EXP-012/Phase 001 artifacts.
  - Incremental planted net edge for `C` beyond `R` is `max(EXP-015_domain_headline_mde_bps(domain), materiality_bps(domain)) + one_edge_grid_step(domain)`, read from approved EXP-015 artifacts.
  - Non-redundancy is accepted only if R-C active overlap is `<= 0.10` and signed R-C agreement correlation over active rows has `abs(rho) <= 0.05`.
  - Expected positive-path outputs are: strict referee `PASS`; ratified-loose referee `PASS` or strict-fallback referee `PASS` for domains where loose was not adopted; incremental unit `POSITIVE_INCREMENTAL`; suite path status `PASS_PATH_EXERCISED`.
  A missing, post-hoc, or construction-invalid positive fixture makes EXP-016 inconclusive/blocked rather than evidence of integration completeness.
- **Exclusions**: Real signal exploration beyond the EXP-009 dogfood set; chart-type candidate signals; tuning dogfood strategies or the suite; changing EXP-012 adoption decisions; changing EXP-015 incremental calibration; programme-level multiplicity control; any use of the global holdout.

## Success / Failure Criteria

- **Evidence FOR integration completeness**: The real EXP-009 dogfood negative path runs through the assembled suite and reports standalone rejections and no positive incremental edge, while the synthetic positive path passes both standalone referees and registers a positive incremental edge against a non-redundant reference.
- **Evidence AGAINST integration completeness**: Either path cannot run, upstream suite components cannot be assembled consistently, the synthetic positive path cannot exercise the pass path, or dogfood/reference wiring is undefined at execution time.
- **Inconclusive**: EXP-012 or EXP-015 is incomplete, the ratified-loose per-domain decision is unavailable, the incremental unit is not calibrated, or the dogfood reference book is not defined before execution.

## Complexity Budget

- Max statistical tests: 4
- Max visualisations: 5
- Max new code modules: 1

## Data Requirements

EXP-012, EXP-015, and EXP-009 must be available before EXP-016 executes. The implementation must assemble strict, ratified-loose or strict-fallback, and incremental referee outputs into a single suite-level table. It must run both the dogfood negative path and the predeclared planted-edge synthetic positive fixture calibrated to pass both standalone referees and register positive incremental edge against a non-redundant reference. Required manifests: suite assembly, dogfood reference book, positive fixture construction, expected positive-path outputs, and blocker report for missing upstream artifacts.

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

Treat EXP-016 as an integration anchor, not a market-edge experiment. Its job is to prove the frozen suite can exercise both expected reject and expected pass wiring before Phase 004.
