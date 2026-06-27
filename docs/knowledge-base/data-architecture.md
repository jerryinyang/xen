# Data Architecture (Frozen Core)

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

## Universe (17 instruments; 16 on the INFR-003 5-year dataset)

EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, XAUUSD, BTCUSD,
USTEC, US500, US2000, JP225 (+ DE30 on the old dataset only — dropped at INFR-003, broker m1
history stale). Default core: EURUSD, XAUUSD, BTCUSD, USTEC. Two datasets exist: the old ~3.3y
universe (CF-AVWAP/HA-HARAMI families) and the **INFR-003 5-year re-collection** (2021-06 →
2026-06, governs CF-CAPGEO/MR and all new work). A new-dataset stratum is a **new stratum** —
ledgers do not transfer (INFR-003 §4.3).
