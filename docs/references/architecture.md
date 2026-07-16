# Xen Data-Layer Architecture v2

**Version:** v2 (INFR-012, 2026-07-15) — NautilusTrader + Bybit USDT-perp catalog
**Supersedes:** v1 cTrader/FX-indices architecture (archived at `archive/chapter-03-xena-mtfctx/`)

## Purpose

Thesis-agnostic research infrastructure for **24/7 crypto perpetual futures**:

1. **Primary lane (T1 — OHLCV):** 1-minute bars derived from Bybit trades archives, full USDT
   linear perpetual universe (listed + delisted), ingested to a Nautilus `ParquetDataCatalog`.
2. **Secondary lane (T2 — MBP, deferred):** orderflow feature store for BTC/ETH/SOL perps only
   (`docs/references/orderflow-feature-store.md`); contracts now, collection later.
3. **Engine:** NautilusTrader event-driven `BacktestNode` — strategies run in-engine; Python
   ingests emissions and adjudicates only.

Programme principles (holdout fence, bar-open decisions, open-to-open returns, estimand gate,
operator verdicts) are unchanged; implementations rebind per INFR-010 §6 Phase C.

## Two-lane data model (binding)

| Lane | Tier | Data | Fill/cost | Default |
|------|------|------|-----------|---------|
| **Primary** | T1 | 1m OHLCV + per-symbol pseudo-quote spread series (aggressor-side trades) | Engine costless-honest; spread + fees + funding injected at analysis (`xen.evaluation`) | **All experiments** |
| **Secondary** | T2 | MBP/L2 quotes + trades + feature store (BTC/ETH/SOL) | Honest L1 fills in-engine; passive through-price rule | Post-collection INFR only |

**Spread-scale routing (§4):** gross edge within ~3× estimated round-trip spread is
**undecidable on T1** — verdict-bearing confirmation requires T2 (BTC/ETH/SOL) or park
`AWAITING_MBP`. Pooled T1 reads on such candidates are disclosure-only.

## High-level architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: DATA INGEST (INFR-011, streaming raw-less)                        │
│  • Census: public.bybit.com/trading/ → 910 USDT linear perps (anti-survivorship) │
│  • Trades → 1m OHLCV + pseudo-quote spreads (bar volume ≡ Σ trades)         │
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
│  • T1 cost injection: Bybit fees + funding + pseudo-quote spread            │
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
└── staging/                          # INFR-011 transient (not analysis input)
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

Spec: `python/experiments/INFR-010/code/emission_contract_v1.md`.

- **Phase B smokes** may carry `fence_attestation.status: STUB` — estimand gate v2 **rejects** these for real experiments.
- **Production emissions** must attest the INFR-011 A6 `fence-manifest.json` sha256.

## Cost model (T1 analysis injection)

Engine runs costless-honest (INFR-009 P5 discipline). Analysis layer applies:

- Bybit USDT-perp maker/taker schedule (`xen.evaluation.BYBIT_USDT_PERP_FEES`)
- Funding accrual (history gaps flagged per R7; conservative assumption when missing)
- T1 pseudo-quote spread (per-symbol series, tick-floor, conservative bias)
- Netted-turnover rule carries from legacy programme

FTMO cost table is **archived** — retained in `xen.evaluation.FTMO_COSTS` for chapter-03
VAL re-analysis only.

## Confirmed decisions (INFR-010 D1–D8)

| # | Decision |
|---|----------|
| D1 | Bybit official archives only (Binance fallback noted, no MBP fallback) |
| D2 | OHLCV from trades archives (not klines) |
| D3 | USDT linear perps only (910 census) |
| D4 | MBP secondary; BTC/ETH/SOL; collection deferred |
| D5 | Chapter rollover — cTrader archived |
| D6 | Global calendar fence |
| D7 | Pseudo-quotes sufficient for T1 (no live BBO) |
| D8 | MBP/L2 terminology; no MBO/L3 claims |

## What this document is not

- Not a strategy thesis — experiments live under `python/experiments/`.
- Not the MBP feature-store spec — see `orderflow-feature-store.md`.
- Not the XENA adjudication spec — see `xena-lane.md` v2 (registry VOID on new data).