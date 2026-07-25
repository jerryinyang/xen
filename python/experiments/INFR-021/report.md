# INFR-021 — cTrader timebar catalog ingest

**Status:** COMPLETE  
**Date:** 2026-07-25  
**Verdict:** PASS — EURUSD, XAUUSD, USTEC ingested and round-trip verified.

## What this did

Loaded the archived chapter-03 1-minute timebars into a **separate** Nautilus catalog so they can be used under the current engine/catalog architecture without touching the Bybit universe.

## Locations

| Item | Path |
|------|------|
| Catalog | `data/catalog_ctrader/` (~203 MB) |
| Fence pin | `python/experiments/INFR-021/artifacts/fence-manifest.json` |
| Fence sha256 | `4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0` |
| Ingest log | `python/experiments/INFR-021/results/catalog-ingest.jsonl` |
| Script | `python/experiments/INFR-021/code/ingest_timebars.py` |

## Results

| Symbol | InstrumentId | Type | Bars | First CloseTime | Last CloseTime | Verified |
|--------|--------------|------|------|-----------------|----------------|----------|
| EURUSD | `EURUSD.CTrader` | CurrencyPair | 1,870,801 | 2021-06-02 00:01 | 2026-06-19 20:56 | yes |
| XAUUSD | `XAUUSD.CTrader` | Cfd (COMMODITY) | 1,784,390 | 2021-06-02 00:01 | 2026-06-19 16:58 | yes |
| USTEC | `USTEC.CTrader` | Cfd (INDEX) | 1,784,619 | 2021-06-02 00:01 | 2026-06-19 16:58 | yes |

- Bar type: `{id}-1-MINUTE-LAST-EXTERNAL`
- `ts_event` = source `CloseTime`
- Volume field: **TickVolume** (tick count, not traded contracts)
- Engine fees: 0 (FTMO costs remain analyst-side via `xen.evaluation`)
- Nautilus pin: `1.230.0`

## Fence (chapter-03 only — not the Bybit pin)

| Band | Boundary |
|------|----------|
| analysis_start | 2021-06-02 |
| train_end | 2023-11-22 |
| holdout_start | 2024-12-13 |
| data_end | 2026-06-19 |

Nested 70/30 over the union of the three series. **HOLDOUT from 2024-12-13 onward must not be queried.**  
`xen.nautilus.catalog_fence` still defaults to the Bybit INFR-011 manifest — pass this fence path explicitly for any cTrader catalog read.

## How to query

```python
from nautilus_trader.persistence.catalog import ParquetDataCatalog

catalog = ParquetDataCatalog("data/catalog_ctrader")
bars = catalog.bars(bar_types=["EURUSD.CTrader-1-MINUTE-LAST-EXTERNAL"])
```

**Interchangeability:** for strategies that only need plain OHLCV bars (not signed
buy/sell volume), `data/catalog_ctrader/` and Bybit `data/catalog/` are the same
Nautilus bar contract — swap catalog path, InstrumentId, and fence pin. Signed
volumes remain Bybit-only (`data/catalog_sigbar/`).

Re-run / extend:

```bash
cd python
.venv/bin/python experiments/INFR-021/code/ingest_timebars.py ingest --symbols EURUSD XAUUSD USTEC
```

## Non-claims

- Does not open a research family or authorise strategy runs.
- Does not change Bybit `data/catalog/`.
- Does not spend TEST/holdout reads.
- Volume is tick count; do not treat as real traded volume for liquidity claims.

## Operator notes

Venue string is **`CTrader`** (not `CTRader`). To add more chapter-03 symbols later: extend `SOURCES` / `SPECS` in the ingest script and re-run (wipe or append policy TBD per symbol). Prefer keeping all cTrader data under `data/catalog_ctrader/`.
