# Xen Data-Layer Architecture v2

**Version:** v2 (INFR-012, 2026-07-15) — NautilusTrader + Bybit USDT-perp catalog
**Supersedes:** v1 cTrader/FX-indices architecture (archived at `archive/chapter-03-xena-mtfctx/`)

## Purpose

Thesis-agnostic research infrastructure for **24/7 crypto perpetual futures**:

1. **Primary lane (T1 — OHLCV):** 1-minute bars derived from Bybit trades archives, full USDT
   linear perpetual universe (listed + delisted), ingested to a Nautilus `ParquetDataCatalog`.
2. **Signed-bar lane:** exact taker buy/sell volume plus a quarantined legacy mean-price-skew
   storage field. The skew is not an execution-cost input.
3. **Engine:** NautilusTrader event-driven `BacktestNode` — strategies run in-engine; Python
   ingests emissions and adjudicates only.

Programme principles (holdout fence, bar-open decisions, open-to-open returns, estimand gate,
operator verdicts) are unchanged; implementations rebind per INFR-010 §6 Phase C.

## Two-lane data model (binding)

| Lane | Tier | Data | Fill/cost | Default |
|------|------|------|-----------|---------|
| **Primary** | T1 | 1m OHLCV from Bybit trades | **Zero-cost model** (`NO_COST_CHARGED`): engine costless-honest; no fees/funding/spread injected at analysis; ZERO-COST-DISCLOSURE caveat on every report | **All experiments** |
| **Signed bar** | T1 diagnostic | Exact taker buy/sell volume; stored mean-price skew | Skew quarantined as `MeanPriceSkewBps / UNUSABLE_AS_SPREAD`; never cost input | Approved flow diagnostics only |
| **Secondary** | T2 | MBP/L2 contracts only; no collected dataset | Unavailable | **Not a programme direction** |

**Spread boundary (INFR-022):** no valid spread observation or secondary-data rescue exists; the
retired cost stack (fees/funding injection, spread-scale routing) is archived in
`xen/evaluation_cost_legacy.py` and not callable from any live path.

**Current signed-data materialisation:** the raw signed source is currently readable through the
mounted archived staging symlink. The full TRAIN signed catalog is verified at
`data/catalog_sigbar/train/`: 3,731,908 rows across five symbols, with tree sha
`d4b7bbed7e0c…f7d2b9` and a zero-TEST/holdout SPDR-011 attestation. The OHLCV catalog is unaffected.

## High-level architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: DATA INGEST (INFR-011, streaming raw-less)                        │
│  • Census: public.bybit.com/trading/ → 910 USDT linear perps (anti-survivorship) │
│  • Trades → 1m OHLCV + signed volume + quarantined mean-price skew          │
│  • ParquetDataCatalog at data/catalog/ (instrument_id/data_type/date)       │
│  • Global calendar fence manifest (A6, hash-pinned)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  STAGE 2: STRATEGY EXECUTION (NautilusTrader, INFR-010)                     │
│  • BacktestNode on catalog bars; event-sequenced deterministic replay       │
│  • Emission contract v1 → data/nautilus_runs/<run_id>/                    │
│  • Shim: xen.nautilus.adjudication_shim → xen.adjudication                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  STAGE 3: ANALYSIS (Python only — no price-strategy vectorised backtest)    │
│  • xen.estimand_validation v2 (blocking)                                    │
│  • T1 cost model: ZERO-COST (NO_COST_CHARGED) — no fees/funding/spread injected   │
│  • xen.evaluation evidence → operator verdict                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

Chart-type generators (Line Break, Renko, Heiken Ashi) remain **dormant** on the new stack
until explicitly ported.

## Catalog layout

```text
data/
├── catalog/                          # Nautilus ParquetDataCatalog (primary)
│   └── <instrument_id>/bars/...      # Partitioned by date; ns timestamps
├── nautilus_runs/                    # Emission contract v1 outputs
│   └── <run_id>/
│       ├── run_metadata.json
│       ├── bar_marks.parquet
│       ├── positions_ledger.parquet
│       ├── fills.parquet
│       ├── orders.parquet
│       ├── event_log.jsonl
│       ├── instrument_id_map.json
│       └── fence_attestation.json
└── staging/                          # active transient space; Chapter-04 bars archived
```

**Archived (chapter-03, obligations persist on that data):**
`archive/chapter-03-xena-mtfctx/data/timebars/`, `data/strategy_runs/` (cTrader emissions).

## Instrument identity

Archive symbol `BTCUSDT` → Nautilus `InstrumentId` `BTCUSDT-LINEAR.BYBIT`.
Convention: `xen.nautilus.instrument_ids` (`{sym}-LINEAR.BYBIT`).

## Temporal discipline (principle rebind)

| Legacy (cTrader) | v2 (Nautilus) |
|----------------|---------------|
| `AnalysisEndUtc` fence in run metadata | Catalog fence wrapper + `fence_attestation.json` hash-pinned to INFR-011 A6 manifest |
| `CloseTime` / `SourceCloseTime` alignment | `ts_event` ns monotonicity; decisions on confirmed data ≤ t−1 only |
| Open-to-open returns | **Unchanged** for bar-domain strategies |
| cTrader engine only | **Nautilus event-driven engine only** — no vectorised Python backtest of a price strategy |

No-lookahead is structural: single-threaded event sequencing in `BacktestNode`; analysis
uses `[t-1]` lag on bar marks. Phase D leak battery proves this on the new stack.

## Global calendar fence (D6)

One TRAIN/TEST/HOLDOUT date pair shared by every symbol (cross-sectional leak-safety).
Late-listed symbols have shorter TRAIN; fence computed from admitted catalog range end
(INFR-011 A6). Final 30% never queried. Catalog query wrapper refuses post-fence reads.

## Holdout split (unchanged semantics)

```
Admitted catalog range (per symbol, capped 4y)
├── First 70% chronologically = ANALYSIS
│   ├── First 70% of analysis = TRAIN
│   └── Last 30% of analysis = TEST
└── Final 30% = GLOBAL HOLDOUT (never loaded)
```

Fence dates are **absolute calendar dates** in the pinned manifest, not row fractions on
the live catalog.

## Emission contract v1

Spec: `archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-010/code/emission_contract_v1.md`.

- **Phase B smokes** may carry `fence_attestation.status: STUB` — estimand gate v2 **rejects** these for real experiments.
- **Production emissions** must attest the INFR-011 A6 `fence-manifest.json` sha256.

## Cost model (ZERO-COST — INFR-022, supersedes the T1 analysis injection)

**All lanes default to `NO_COST_CHARGED` (binding, INFR-022 directive 1):** no spread,
commission, or swap enters any calculation in any experiment type unless an explicit operator
cost directive requests costs (recorded in the experiment's design.md before execution; QA
traces it). "Zero" is a model, not a measurement — every money-bearing report/analysis/results
artifact carries the ZERO-COST-DISCLOSURE caveat verbatim (`docs/references/neutrality-standard.md`
§ N9). Non-zero `--cost-bps` / `charge_costs=True` raise unless `operator_cost_directive.json`
(operator-signed reason + scope) is present. `money_per_unit` is a sizing/capital-unit factor,
not a cost.

**Retired cost stack (historical record — chapter-04/05).** The former T1 analysis injection —
Bybit maker/taker schedule (`BYBIT_USDT_PERP_FEES`), timestamp-counted funding,
`bybit_round_trip_cost_bps` with `spread_rt_bps=None` / `PARTIAL_FEES_FUNDING_ONLY` and the
understatement caveat, `t1_round_trip_spread_bps`, `spread_scale_route` — moved to
`xen/evaluation_cost_legacy.py` (ARCHIVED banner; not callable from any live path; only an
operator cost directive may re-enable it, recorded in the design).

The stored `SpreadBps` bytes have no tick floor and are not spread. Live access goes through
`xen.sigbar.quarantine_mean_price_skew`, which exposes `MeanPriceSkewBps` with status
`UNUSABLE_AS_SPREAD` — a data-provenance quarantine, kept live (not a cost read). FTMO cost
table is **archived** in the legacy module for chapter-03 VAL re-analysis only.

## Cost directive mechanism (INFR-022 §3.4)

* Design clause in `design.md` naming the directive, functions, and scope.
* Run-dir / universe-root file `operator_cost_directive.json` (operator-signed reason
  string + scope).
* QA traces both. Estimand `--cost-bps != 0` fails without the file; oracle
  `charge_costs=True` raises without the directive object/path.

## Confirmed decisions (INFR-010 D1–D8)

| # | Decision |
|---|----------|
| D1 | Bybit official archives only (Binance fallback noted, no MBP fallback) |
| D2 | OHLCV from trades archives (not klines) |
| D3 | USDT linear perps only (910 census) |
| D4 | **Superseded for Chapter 05:** MBP/L2 is unavailable; no secondary confirmation branch |
| D5 | Chapter rollover — cTrader archived |
| D6 | Global calendar fence |
| D7 | **Superseded by INFR-017:** stored mean-price skew is unusable; Chapter-05 T1 uses five audited conservative pins |
| D8 | MBP/L2 terminology; no MBO/L3 claims |

## What this document is not

- Not a strategy thesis — experiments live under `python/experiments/`.
- Not an MBP collection plan; secondary data is unavailable for the active programme.
- Not the XENA adjudication spec — see `xena-lane.md` v2 (registry VOID on new data).
