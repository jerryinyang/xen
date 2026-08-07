# INFR-021 — cTrader timebar catalog ingest (EURUSD, XAUUSD, USTEC)

**Type:** infrastructure (data path only; no strategy, no TEST read, no family work)  
**Date:** 2026-07-25  
**Status:** COMPLETE (2026-07-25)

## Question

Can the archived chapter-03 1-minute timebars for **EURUSD, XAUUSD, USTEC** be loaded into a Nautilus `ParquetDataCatalog` under the current data architecture (instrument objects + 1m bars + fence pin), without touching the Bybit catalog?

## Scope (fixed)

| Item | Choice |
|------|--------|
| Symbols | EURUSD, XAUUSD, USTEC only |
| Source | Full 5y chapter-03 parquets under `archive/chapter-03-xena-mtfctx/data/timebars/` (`*_20210602_*`) |
| Catalog root | `data/catalog_ctrader/` — **separate** from Bybit `data/catalog/` |
| InstrumentId | `{SYMBOL}.CTrader` (e.g. `EURUSD.CTrader`) |
| Instrument types | EURUSD → `CurrencyPair`; XAUUSD/USTEC → `Cfd` |
| Bar type | `{id}-1-MINUTE-LAST-EXTERNAL` |
| Timestamps | `ts_event = ts_init = CloseTime` (confirmed bar; decisions at next open use ≤ t−1) |
| Volume | `TickVolume` (tick count, not traded contracts — disclosed) |
| Engine fees | 0 (costless engine; FTMO costs analyst-injected via `xen.evaluation`) |
| Fence | Nested 70/30 calendar fence over **union** of the three symbols' CloseTime ranges; HOLDOUT never queried by experiment code |
| Out of scope | Other symbols; strategy runs; Bybit catalog changes; holdout reads; cost pinning |

## Source files (pinned)

| Symbol | Path |
|--------|------|
| EURUSD | `archive/chapter-03-xena-mtfctx/data/timebars/timebars_eurusd_20210602_000000_20260621_183431.parquet` |
| XAUUSD | `archive/chapter-03-xena-mtfctx/data/timebars/timebars_xauusd_20210602_000000_20260621_190824.parquet` |
| USTEC | `archive/chapter-03-xena-mtfctx/data/timebars/timebars_ustec_20210602_000000_20260621_190833.parquet` |

Schema (all three): `Symbol, OpenTime, CloseTime, Open, High, Low, Close, TickVolume`.

## Specs (encoding + FTMO table)

| Symbol | kind | price digits | tick | size step | lot size | FTMO note |
|--------|------|--------------|------|-----------|----------|-----------|
| EURUSD | FX spot (CurrencyPair) | 5 | 0.00001 | 0.01 | 100_000 | flat $5/lot RT commission table in `xen.evaluation` |
| XAUUSD | metal CFD | 2 | 0.01 | 0.01 | 100 | percent commission table |
| USTEC | index CFD | 2 | 0.01 | 0.01 | 1 | commission 0 (spread-only; spread unpinned) |

## Invariants (admission-blocking)

1. `CloseTime` strictly increasing per symbol  
2. OHLC: `High >= max(Open,Close)`, `Low <= min(Open,Close)`  
3. Non-null OHLC; volume ≥ 0  
4. Row count after wrangle equals source row count  
5. Round-trip catalog query returns same first/last CloseTime and row count

## Fence (catalog-local)

Same nested calendar rule as INFR-011, **independent pin** (do not reuse Bybit fence):

```
analysis_start = min(first CloseTime)
data_end       = max(last CloseTime)
holdout_start  = floor_day(start + 0.70 * span)
train_end      = floor_day(start + 0.49 * span)   # 0.70 * 0.70 of span
```

Artifact: `python/experiments/INFR-021/artifacts/fence-manifest.json`  
Schema: `xen-fence-manifest/v1` (same fields as Bybit pin).  
Holdout obligations on chapter-03 data remain binding.

## Deliverables

| Artifact | Path |
|----------|------|
| Ingest script | `python/experiments/INFR-021/code/ingest_timebars.py` |
| Catalog | `data/catalog_ctrader/` |
| Ingest log | `python/experiments/INFR-021/results/catalog-ingest.jsonl` |
| Fence | `python/experiments/INFR-021/artifacts/fence-manifest.json` |
| Report | `python/experiments/INFR-021/report.md` |

## Interchangeability (plain bars)

`data/catalog_ctrader/` and Bybit `data/catalog/` both expose standard Nautilus
`Bar` objects via `ParquetDataCatalog`. Strategies / experiments that only need
OHLCV (not signed buy/sell volume) can use either catalog the same way: set
catalog path + InstrumentId + the matching fence pin. They are **not** the same
files or IDs — but they share the same bar contract for engine replay.

Signed aggressor volumes live only in `data/catalog_sigbar/` (Bybit SignedBar)
and are **not** available for cTrader symbols.

## Non-claims

- Not a new research universe for Chapter 05–06 Bybit work.  
- Not an authorisation to open families or spend TEST/holdout reads.  
- Catalog stores full history; **reads** must honour the chapter-03 fence.
