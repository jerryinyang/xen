# cTrader-CLI Experiment Harness (Chapter 02 — price-primary)

The reusable harness for **price-primary** experiments: any experiment that generates
signals/entries/positions/edges from price runs **in the cTrader engine**, not in Python.
Python is **analysis-only** on the emitted runs. This is the structural fix for the Chapter-01
look-ahead leak (`docs/knowledge-base/lessons-and-amendments.md` L-01): a model's `OnBar()` sees
only the current and past bars, and `HoldoutFence` refuses to emit any row at/after
`AnalysisEndUtc`, so look-ahead and holdout contamination are impossible by construction.

## Recipe — add a price-primary experiment

1. **Write the C# model.** Implement `ISignalModel` in `StrategyHost/<YourModel>.cs`. Copy
   `StrategyHost/DonchianBreakoutModel.cs` as the simplest template. `OnBar(bar, domain)`
   returns a `SignalUpdate`; it may use only `bar` and the model's own accumulated past state
   — **never a future bar**. Emit positions with the **real domain-bar OHLC** the strategy
   executed on (the `SignalPositionRecord` fields), per the contract below.
2. **Register it.** Add an entry to the `XenStrategy` enum and the `CreateStrategyModel()`
   switch in `Xen.cs`, and any `[Parameter]` your model needs.
3. **Build.** `dotnet build Xen.csproj -c Debug`.
4. **Configure the cells + fence.** Copy `experiments/EXAMPLE.conf` to `experiments/<EXP-ID>.conf`
   and set `STRATEGY`, `STRATEGY_VALUE`, `SYMBOLS`, `DOMAINS`, and the per-symbol
   `ANALYSIS_END` (= each file's first-70% analysis cutoff) and `BACKTEST_END`.
5. **Run.** `./run-experiment.sh <EXP-ID> all` (or `parallel`, or `one <SYMBOL> <DOMAIN>`).
   Outputs land under `data/strategy_runs/<EXP-ID>/<strategy>_<symbol>_<domain>/`.
6. **Ingest + analyse in Python.** Read the emitted parquet via `xen.signals.ingestion`
   (read/validate-only). All downstream analysis (returns, costs, expectancy, portfolio,
   referee) is Python on these extracts — never a re-generated signal.

## strategy_runs emission contract

Each run directory contains (see `StrategyHost/StrategyRunParquetWriter.cs`,
`StrategyHost/SignalRecords.cs`):

| File | Content |
|------|---------|
| `run_metadata.json` | run config: strategy + params, instrument/domain, `AnalysisEndUtc`, coverage, row counts |
| `positions.parquet` | per-bar position with the **real** domain-bar OHLC executed on (`SignalPositionRecord`) — the only valid price source for return/P&L |
| `trade_blotter.parquet` | diagnostic trade actions (`StrategyTradeRecord`) |
| `<events>.parquet` | optional per-bar signal/regime detail (`SignalEventRecord`) for model-specific diagnostics |

A run is **admitted** to an experiment by behavioral-suite reproduction (VAL-002), not byte
parity. Returns/P&L use the emitted real OHLC — never synthetic chart prices.

## Causal guarantee (why this is leak-resistant)

- **Streaming:** `StrategyHostRunner` feeds bars sequentially; `OnBar` cannot see the future.
- **Fence:** `HoldoutFence.AssertCanEmit` throws on any emission at/after `AnalysisEndUtc`;
  `ShouldStopBeforeProcessing` halts the run at the fence. The final 30% global holdout is
  never processed.
- **No vectorized outcome module:** there is no Python `rct[di]`-style favourable-index pass to
  leak through (L-01). Outcomes are the engine's realized fills.

## Reusable collection scripts (kept from Chapter 01)

`run-infr002-collection.sh`, `run-infr003-collection.sh`, `run-pps-collection.sh` — 1-minute
data collection (Mode=TimeBars). Per-experiment backtest scripts from Chapter 01 are archived
under `archive/chapter-01-price-geometry-referee/ctrader-cli/`.
