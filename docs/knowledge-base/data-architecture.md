# Data Architecture

> **MIGRATION (INFR-010, 2026-07-14) — everything below the marked line is LEGACY.**
> At the chapter-03 close the programme replaced its substrate
> (`archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-010/design.md`, operator decisions D1–D8):
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
> - **Data — signed bar lane (Chapter 04):** the Bybit trade archives also carry aggressor
>   side. INFR-017 proved the stored `BuyVolume`/`SellVolume` split bit-exact against raw
>   trades on 20/20 symbol-days and materialised engine-readable signed bars. This is real
>   buy-side/sell-side traded volume, not broker tick-count volume and not order-book data.
> - **Secondary-data boundary:** historical MBP/L2 collection remains unavailable and is not
>   a programme direction. `xen.orderflow` contracts/ingestion are reusable infrastructure;
>   no result may imply that an uncollected L1/L2 confirmation will rescue a T1 result.
> - **Cost boundary:** the staging `SpreadBps` field is a same-minute mean-buy-price minus
>   mean-sell-price differential. It is negative in roughly 32–40% of BTC/ETH TRAIN minutes,
>   is pinned `UNUSABLE`, and is neither a quote spread nor a valid execution-cost input.
>   Executable spread must come from an audited external pin or a separately validated
>   reconstruction; until then exact net deployability is unresolved, not zero-cost.
> - **Holdout:** **global calendar fence** (D6) — one TRAIN/TEST/HOLDOUT date pair shared by
>   every symbol, hash-pinned split manifest; catalog query wrapper refuses post-fence reads.
>   A Chapter-04 exception is permanently disclosed: one INFR-017 path scanned a univariate
>   spread-quality column beyond the fence, without prices, returns, P&L or signals; the
>   operator cleared it with zero sanctioned reads consumed. No research outcome was queried.
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

## Retained Chapter-04 data contracts

- **Base catalog:** `data/catalog/`, Nautilus `Bar` OHLCV, global TRAIN/TEST/HOLDOUT calendar
  fence, 894 admitted archive instruments at migration. Query through the fenced catalog path.
- **Signed staging/catalog contract:** the raw signed source is currently readable through the
  mounted archived staging symlink and carries `BuyVolume`, `SellVolume`, `NTrades` and unusable
  print-differential fields; INFR-017 proved the mapping. The full TRAIN signed catalog is verified
  at `data/catalog_sigbar/train/`: 3,731,908 rows across five symbols, tree sha
  `d4b7bbed7e0c…f7d2b9`, zero mapping/config violations and zero TEST/holdout rows in the SPDR-011
  attestation. `Buy+Sell ≡ Volume` remains the required invariant.
- **Pinned Chapter-04 apparatus:** seasonal baseline `1b7244c8…`, signed instrument registry
  `5c386984…`, multi-timeframe baseline manifest `5f170b71…`, and active Bybit/XENA
  calibration registry `abbb184229236a75f624537ca605668a73f6f85138c150e14a3609c4191bf786`
  (CLS-FILTER LOW + CLS-EPISODE LOW; HIGH blocked). These pins preserve apparatus and
  calibration scope; they do not preserve a strategy claim.
- **Coverage is conditioning:** usable signed universes fell 194→72→47→31 across
  1m/5m/15m/1h complete-window requirements; surviving windows carried 2.4×–27× the volume
  of partial windows. Absolute-return reads on complete outcomes therefore describe a selected
  post-entry-activity subset unless availability is reported explicitly.
- **Engine contract:** event-driven, causal by construction; fills reconcile to the emitted
  position ledger. Fill timestamps use the decision-bar close/wall-clock next-bar open
  convention; one `BacktestNode` per process; defer disposal until reports are captured.

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
