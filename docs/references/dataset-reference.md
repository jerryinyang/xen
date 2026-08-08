# Xen Dataset Reference v2

**Version:** v2 (INFR-012, 2026-07-15)
**Generator:** INFR-011 streaming pipeline → Nautilus `ParquetDataCatalog`
**Base data unit:** 1-minute OHLCV bars derived from Bybit trades archives
**Universe:** Bybit USDT linear perpetuals (listed + delisted), census-based anti-survivorship

**Supersedes:** v1 cTrader/FX-indices dataset reference. Archived data obligations:
`archive/chapter-03-xena-mtfctx/data/timebars/` — holdout rules on that data remain binding.

---

## Universe (census-based, binding)

| Field | Value |
|-------|-------|
| Source listing | `https://public.bybit.com/trading/` (Apache directory) |
| Filter | Folders ending `USDT/` only — excludes `*PERP/` (USDC), inverse `*USD`, dated futures |
| Census artifact | `archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/artifacts/universe-census.md` |
| Symbol count | **910** (2026-07-14 census) |
| History cap | Trailing **4 years** per symbol (operator amendment 2026-07-14) |
| Delisted | Included when present in archive listing; `listed`/`delisted` flags from announcement reconciliation |
| Spec gaps | `SPEC_INCOMPLETE` — excluded from fill-sensitive reads, included in return-level reads |

**InstrumentId convention:** `{SYMBOL}-LINEAR.BYBIT` (e.g. `BTCUSDT-LINEAR.BYBIT`).
Module: `xen.nautilus.instrument_ids`.

### Sample symbols (illustrative)

| Symbol | Role | Notes |
|--------|------|-------|
| BTCUSDT | liquid anchor | ~4y capped from 2022-07-14 |
| ETHUSDT | liquid anchor | idem |
| SOLUSDT | liquid anchor | idem |
| LUNA2USDT | delist tail test | archive present through 2026-07-13 |
| USTCUSDT | younger listing | shorter capped range |

Full candidate list: `archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/artifacts/candidate_symbols.txt`.

---

## Data locations

| Dataset | Path | Status |
|---------|------|--------|
| Primary catalog (bars) | `data/catalog/` | INGESTED (A4, 2026-07-16; 894 ADMITTED + 9 SPEC_INCOMPLETE) |
| Signed staging fields | `archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/data/staging/bars/` | The raw signed source is currently readable through the mounted `/Volumes/SSID/Xen/data/bars`; provenance/admission is recorded for all five Chapter-05 symbols |
| Signed custom catalog | `data/catalog_sigbar/train/` | The full TRAIN signed catalog is verified: 3,731,908 rows, five symbols, 90 files; tree sha `d4b7bbed7e0c…f7d2b9`; SPDR-011 attestation records zero TEST/holdout rows and zero mapping violations |
| Mean-price skew fields | same external signed staging files (`SpreadAbs`/`SpreadBps`/`MeanBuy`/`MeanSell`) | **UNUSABLE AS SPREAD** — analytical access renames the bps field to `MeanPriceSkewBps` and stamps `UNUSABLE_AS_SPREAD` |
| Strategy emissions | `data/nautilus_runs/<run_id>/` | emission contract v1 |
| Fence manifest (A6) | `archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/artifacts/fence-manifest.json` | **PINNED** 2026-07-16 |
| Admission ledger (A5) | `archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/artifacts/admission-ledger.jsonl` | 910 census rows, explicit exclusions |
| Instrument specs | `archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/artifacts/instrument-specs.json` | API (612) + INFERRED (282) |

**Archived cTrader paths (VAL carve-out on old emissions only):**
`archive/chapter-03-xena-mtfctx/data/timebars/`,
`archive/chapter-03-xena-mtfctx/data/strategy_runs/`.

**cTrader Nautilus catalog (INFR-021, 2026-07-25):** `data/catalog_ctrader/` — EURUSD, XAUUSD, USTEC as `{SYMBOL}.CTrader` 1m bars from chapter-03 timebars. Fence pin (independent of Bybit): `python/experiments/INFR-021/artifacts/fence-manifest.json`. Volume = TickVolume (no signed buy/sell). Same standard Nautilus `Bar` contract as Bybit `data/catalog/` for plain-OHLCV strategies (swap catalog path + InstrumentId + fence); not interchangeable with `data/catalog_sigbar/` (SignedBar). Not the Chapter 05–06 primary universe.

---

## Primary lane: 1-minute OHLCV (T1)

Derived from trades archives (not klines — klines lack aggressor side and drop delisted symbols).

### Bar invariants (admission-blocking)

- Bar volume ≡ Σ trade sizes for the minute
- `ts_event` strictly monotonic per instrument file
- OHLC bounds: `High >= max(Open, Close)`, `Low <= min(Open, Close)`
- Gap ledger: all outages/delistings logged (24/7 market)

### Nautilus `Bar` schema (catalog)

Timestamps in **nanoseconds** (`ts_event`, `ts_init`). Access via `ParquetDataCatalog` or
approved query wrapper that enforces the global fence.

| Field | Description |
|-------|-------------|
| `open`, `high`, `low`, `close` | OHLC from first/last trade prints |
| `volume` | Real traded volume (contracts/coin per instrument spec) |
| `bar_type` | 1-MINUTE-LAST |

### Mean-price skew quarantine (not a cost input)

The stored `SpreadBps` field is
`1e4 × (MeanBuy − MeanSell) / ((MeanBuy + MeanSell) / 2)`. The producing code applies no
tick floor. Because the two means cover different trades at different times, the value is an
intraminute mean-price skew and may be negative; it is not a quote or effective spread.

Stored bytes and fence pins remain unchanged. `xen.sigbar.quarantine_mean_price_skew` is the
only live analytical access seam: it verifies the INFR-017 pin, removes the misleading storage
name, exposes the value as `MeanPriceSkewBps`, and attaches `MeanPriceSkewStatus =
UNUSABLE_AS_SPREAD`. Passing this field to any cost function is prohibited.

---

## Secondary lane: MBP/L2 contracts (inactive)

Historical contracts describe BTCUSDT, ETHUSDT and SOLUSDT depth data, but no bulk collection
exists and secondary data is an established programme limitation. Chapter 05 cannot route an
unresolved T1 result into a T2 rescue branch.

Spec: `docs/references/orderflow-feature-store.md`.

---

## Emission contract v1 (strategy runs)

Root: `data/nautilus_runs/<run_id>/`

| File | Required | Role |
|------|----------|------|
| `run_metadata.json` | yes | config hash, catalog version, nautilus pin, platform |
| `bar_marks.parquet` | yes | bar OHLC marks → adjudication `positions` |
| `positions_ledger.parquet` | yes | closed legs → `cis_trades` via shim |
| `fills.parquet` | yes | economic fills |
| `orders.parquet` | yes | order lifecycle |
| `event_log.jsonl` | yes | UUID-stripped deterministic log |
| `instrument_id_map.json` | yes | archive symbol ↔ InstrumentId |
| `fence_attestation.json` | yes | analysis fence; **STUB invalid for real experiments** |

Shim: `xen.nautilus.adjudication_shim.adjudicate_emission(run_dir)`.

### `bar_marks` columns (minimum for gate)

| Column | Type | Description |
|--------|------|-------------|
| `SourceCloseTime` | datetime[ns] | Bar close known at decision time |
| `RealOpen` | float | Execution mark (open-to-open discipline) |
| `RealHigh`, `RealLow`, `RealClose` | float | optional OHLC |
| `Position`, `OpenLegs` | int | optional position state |

### `positions_ledger` → `cis_trades`

| Nautilus | Adjudication |
|----------|--------------|
| `ts_opened` | `EntryTime` |
| `ts_closed` | `ExitTime` |
| `avg_px_open` | `EntryFillPrice` |
| `avg_px_close` | `ExitFillPrice` |
| `entry` (BUY/SELL) | `Direction` (+1/-1) |

`RealizedBps = Direction * (Exit - Entry) / Entry * 1e4`

---

## Global calendar fence

Single date set for all symbols (INFR-011 A6, **pinned 2026-07-16**,
manifest sha256 `35d3375ec5ec18b3c6e4c5eec814ade4d492bd60e3fb694fed19e16bc2c00448`):

| Key | Value |
|-----|-------|
| `analysis_start_utc` | 2021-06-29T06:53:00Z |
| `train_end_utc` | 2023-12-18T00:00:00Z (end of TRAIN band; TEST starts here) |
| `holdout_start_utc` | 2025-01-08T00:00:00Z (global holdout — never queried) |
| `data_end_utc` | 2026-07-14T23:59:00Z |

Manifest is hash-pinned (`manifest_sha256` in each emission's `fence_attestation.json`).
Computed from admitted catalog range end — not calendar today (R9).
Wrapper: `xen.nautilus.catalog_fence` (`load_fence_manifest`, `fenced_bar_query`,
`fence_attestation_payload`). Note: symbols listed after `holdout_start_utc` have
zero readable bars until a future fence renewal — accepted consequence of the
global-fence design.

---

## Holdout rules (non-negotiable)

1. Never load, inspect, or use the final 30% of the admitted range.
2. Catalog queries must pass through the fence wrapper.
3. Emissions must not contain bar marks after `analysis_end_utc`.
4. Phase B `STUB` attestations fail estimand gate v2.

---

## Loading patterns (T1)

```python
from pathlib import Path
from nautilus_trader.persistence.catalog import ParquetDataCatalog

from xen.nautilus.catalog_fence import fenced_bar_query, load_fence_manifest

catalog = ParquetDataCatalog(Path("data/catalog"))
fence = load_fence_manifest()
bars = fenced_bar_query(
    catalog,
    ["BTCUSDT-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"],
    start=fence.analysis_start_utc,
    end=fence.train_end_utc,
    band="TRAIN",  # "TEST" only under operator-approved counted reads
)
```

For emissions:

```python
from xen.nautilus.adjudication_shim import adjudicate_emission

bundle = adjudicate_emission("data/nautilus_runs/<run_id>")
```

---

## Cost reads (ZERO-COST — INFR-022)

**The programme is zero-cost (`NO_COST_CHARGED`):** no spread, commission, or swap enters any
calculation in any experiment type unless an explicit operator cost directive requests costs
(recorded in the experiment's design.md before execution). There are no live cost reads; the
retired Bybit fee/funding functions (`bybit_round_trip_cost_bps`, `count_bybit_funding_stamps`,
`spread_scale_route`, FTMO table) live in `xen/evaluation_cost_legacy.py` under an ARCHIVED
banner — not callable from any live path.

```python
# Zero-cost disclosure (canonical caveat for every money-bearing artifact)
from xen.evaluation import zero_cost_caveat
print(zero_cost_caveat())

# Legacy data-provenance check — KEPT LIVE (verifies only that the legacy field
# remains unusable; not a cost read)
from xen.evaluation import verify_chapter05_spread_quarantine
verify_chapter05_spread_quarantine()
```

The stored mean-price skew is never a cost input and no substitute spread proxy exists. A
costed read without a recorded operator cost directive (design clause +
`operator_cost_directive.json`) is a governance violation; deployability/tradability claims
remain refused by rule.

For the fixed Chapter-05 four-hour episode, settlement timestamps are counted in `(entry, exit]`;
continuous `hold_hours / 8` prorating is forbidden. The adverse missing-history charge is 1.0 bps
per crossed 00:00/08:00/16:00 UTC timestamp.

---

## Legacy reference (archived FX/indices)

Chapter-03 instruments (EURUSD, USTEC, etc.) and `data/timebars/` schemas remain documented in
`archive/chapter-03-xena-mtfctx/docs/references/` for reproducibility. New experiments use
the Bybit universe only.
