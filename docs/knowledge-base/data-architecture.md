# Data Architecture

> **MIGRATION (INFR-010, 2026-07-14) — everything below the marked line is LEGACY.**
> At the chapter-03 close the programme replaced its substrate
> (`python/experiments/INFR-010/design.md`, operator decisions D1–D8):
>
> - **Engine:** cTrader C# `StrategyHost` → **NautilusTrader** (Python API, Rust core,
>   event-driven, single-threaded deterministic replay). The principle is
>   causal-by-construction **event sequencing**, not C# — vectorised Python backtests of
>   price strategies remain forbidden.
> - **Data — primary:** 1m OHLCV **derived from Bybit trades archives**
>   (`public.bybit.com/trading/`), full **USDT linear perpetual universe including delisted
>   contracts** (strict anti-survivorship; the archive listing is the universe census).
>   Real traded volume; bar ≡ Σ trades integrity invariant. Ingested to a NautilusTrader
>   `ParquetDataCatalog` at `data/catalog/`.
> - **Data — secondary (deferred):** MBP/L2 orderflow feature store, BTC/ETH/SOL perps only
>   (`docs/references/orderflow-feature-store.md`); contracts + skeleton in INFR-013,
>   **no collection** until a separately-approved INFR.
> - **Fill/cost tiers:** **T1** (OHLCV lane) = engine costless-honest, spread (pseudo-quote
>   from aggressor-side trades, tick-floor) + fees + funding injected at analysis; **T2**
>   (MBP trio) = honest L1 fills, post-collection only. **Spread-scale routing rule:** gross
>   edge within ~3× estimated RT spread is undecidable on T1 (XENA-003 class) — confirm on
>   T2 or park `AWAITING_MBP`.
> - **Holdout:** **global calendar fence** (D6) — one TRAIN/TEST/HOLDOUT date pair shared by
>   every symbol, hash-pinned split manifest; catalog query wrapper refuses post-fence reads.
>   Final 30% never queried.
>
> Enforcement lands per INFR-010 §6: fence manifest + admission gate (Phase A / INFR-011),
> emission contract + determinism check (Phase B), doc/skill/cost-model rebind (Phase C /
> INFR-012), leak battery (Phase D). Until a phase lands, its legacy counterpart below is
> the reference for *mechanism*, not for paths.
>
> The FX/indices data and cTrader stack are archived at `archive/chapter-03-xena-mtfctx/`
> (`data/timebars/`, `data/strategy_runs/`, `ctrader-stack/`). **Holdout obligations on the
> archived FX/indices data remain binding forever.** The XENA frozen registry is **VOID on
> the new stack** (fresh CAL cycle required).

---

## LEGACY (chapters 01–03, cTrader/FX-indices) — kept for archived-data obligations

Thesis-agnostic data layer. Full detail: `docs/references/architecture.md` and
`docs/references/dataset-reference.md`. This is the compressed canon.

## Three stages

1. **Collection (cAlgo):** completed **1-minute OHLC time bars** only (no ticks), one Parquet
   per symbol/session under `data/timebars/`. Schema: `Symbol, OpenTime, CloseTime, Open,
   High, Low, Close, TickVolume`. Order by `CloseTime`.
2. **Derived views (Python, on-demand, deterministic):** Line Break (`level`, default 3),
   Renko (`atr_period`, default 14), Heiken Ashi (no params). Each carries `SourceCloseTime`
   linking synthetic events to real time for return evaluation. Persist under
   `data/<view>/` only when a variant is reused and versioned.
3. **Strategy-host (cTrader engine; Python validates):** strategies run as real cAlgo robots
   in cTrader's engine (`StrategyHost` mode), resample internally, enforce `AnalysisEndUtc`,
   and emit `data/strategy_runs/` (positions w/ real OHLC, events, trades, metadata). **Python
   ingests and validates only — it never generates strategy signals.** Ported C# generators are
   transcription-validated once against the Python reference; a run is admitted by **behavioral
   suite reproduction** (VAL-002), not byte-parity.

> Chapter 02 makes stage 3 the **primary** path for any price-primary (edge-generating)
> experiment — see [methodology-canon.md](methodology-canon.md) and the pipeline skills.

## Holdout fence (non-negotiable)

Nested chronological split, ordered by `CloseTime`/`SourceCloseTime`:

```
Full file → first 70% = ANALYSIS (first 70% TRAIN / last 30% analysis-TEST)
          → final 30%  = GLOBAL HOLDOUT (never loaded outside a sanctioned release)
```

- Never load/inspect the final 30%. The C# host emits **no** row with
  `SourceCloseTime >= AnalysisEndUtc`; Python re-applies the split.
- "first 49%" = TRAIN sub-split (`int(int(total·0.7)·0.7)`); "analysis-TEST" = the next 21%;
  these phrases recur throughout the registry.

## Synthetic-price discipline

Heiken Ashi prices and Renko brick prices are **synthetic** — never use for strategy P&L or
signal-return evaluation. HA returns use `RealOpen/High/Low/Close`; Renko/LB signals align to
real prices via `SourceCloseTime`. `HAClose` returns are allowed **only** for an explicitly
scoped, non-tradable HA distortion diagnostic.

## strategy_runs parquet contract (formalize/extend in Chapter 02)

The cTrader StrategyHost emits (see `StrategyHost/StrategyRunParquetWriter.cs`,
`SignalRecords.cs`):
- **positions** — entry/exit with the **real OHLC the strategy executed on**, direction, size;
- **events** — per-bar signal/regime detail;
- **trades** — diagnostic blotter;
- **metadata** — run config, `AnalysisEndUtc`, instrument/domain, model + parameters.

Python reads these via `xen.signals.ingestion` (read/validate-only). The C2 renewal scaffolds
a generic experiment template on this contract — see the cTrader harness in `tools/ctrader-cli/`
and `StrategyHost/`.

## Indices basket (INFR-005, complete 2026-07-06)

The 10-symbol Indices basket is complete in canonical `data/timebars/` on the ~5-year window
(all reach 2021-06-02): USTEC, US500, US2000, JP225 + collected AUS200, US30, `STOXX50`
(EU50), `DE40` (GER40), HK50, UK100. Broker-string auto-fallback lives in
`tools/ctrader-cli/run-infr005-collection.sh`. Per-file holdout sealed at first touch;
VAL-007 PASS (all 5 gates, `holdout_rows_read=0`).

## Universe (17 instruments; 16 on the INFR-003 5-year dataset)

EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, XAUUSD, BTCUSD,
USTEC, US500, US2000, JP225 (+ DE30 on the old dataset only — dropped at INFR-003, broker m1
history stale). Default core: EURUSD, XAUUSD, BTCUSD, USTEC. Two datasets exist: the old ~3.3y
universe (CF-AVWAP/HA-HARAMI families) and the **INFR-003 5-year re-collection** (2021-06 →
2026-06, governs CF-CAPGEO/MR and all new work). A new-dataset stratum is a **new stratum** —
ledgers do not transfer (INFR-003 §4.3).
