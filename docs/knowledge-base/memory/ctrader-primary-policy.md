---
name: ctrader-primary-policy
description: Price-primary (edge-generating) experiments run in the cTrader engine; Python is analysis-only
metadata: { type: project, chapter: 02 }
---

Chapter 02 policy: any experiment that generates signals/entries/positions/edges from price is
**price-primary** and runs in the cTrader engine (StrategyHost mode) via `tools/ctrader-cli`,
emitting `data/strategy_runs/` parquet under the `AnalysisEndUtc` fence. Python is **analysis-only**
on emitted runs — never regenerates signals, no vectorized backtest of a price strategy. This makes
look-ahead impossible by construction (the structural fix for [[look-ahead-rct-pattern]]). Harness:
generic StrategyHost template + parameterized `run-experiment.sh`.
