# Instrument-ID convention (INFR-010 Phase B)

**Pinned format:** `{archive_symbol}-LINEAR.BYBIT`

| Layer | Example |
|-------|---------|
| Bybit trades archive folder (INFR-011 census) | `BTCUSDT` |
| Nautilus `InstrumentId` string | `BTCUSDT-LINEAR.BYBIT` |
| Symbol component | `BTCUSDT-LINEAR` |
| Venue | `BYBIT` |
| Product type | `LINEAR` (USDT linear perpetual only — D3) |

## Mapping

```
archive_symbol  →  InstrumentId
BTCUSDT         →  BTCUSDT-LINEAR.BYBIT
ETHUSDT         →  ETHUSDT-LINEAR.BYBIT
SOLUSDT         →  SOLUSDT-LINEAR.BYBIT
XRPUSDT         →  XRPUSDT-LINEAR.BYBIT
LUNA2USDT       →  LUNA2USDT-LINEAR.BYBIT
```

Helpers: `xen.nautilus.instrument_ids`
- `archive_symbol_to_instrument_id_str("BTCUSDT")` → `"BTCUSDT-LINEAR.BYBIT"`
- `instrument_id_to_archive_symbol("BTCUSDT-LINEAR.BYBIT")` → `"BTCUSDT"`

## Out of scope (rejected by helpers)

- Spot, inverse (`*USD` not ending `USDT`), USDC `*PERP`, dated futures
- Matches INFR-011 census filter (910 USDT linear perps)

## Census alignment

INFR-011 `artifacts/universe-census.md` / `candidate_symbols.txt` use bare archive
names (`BTCUSDT`). Catalog ingest (A4) must write instruments under the Nautilus
id; emission metadata carries the full map.
