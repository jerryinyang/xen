# VAL-002 — cTrader behavioral-closure runbook (operator)

This is the one leg the console smoke cannot stand in for: running the strategy as a
**real cAlgo inside cTrader's engine**, on cTrader's own feed, and confirming its
emitted positions reproduce the EXP-004/009 verdict through the frozen suite
(design.md v2). Generation happens here in cTrader; I validate the output in Python.

## Setup (every run)

- Open the **Xen** cBot on the instrument's **1-minute** chart (the cBot throws if the
  timeframe isn't Minute; it resamples to the trading domain internally).
- Run in **Backtesting**, data mode **"1 minute bars"** (the cBot only consumes
  completed 1-minute bars via `OnBar`; tick mode is unnecessary).
- Backtest **from the data start (≈2023-01-02) over the full range** — the cBot
  **self-fences**: it stops emitting (and stops the backtest) when a bar reaches
  `AnalysisEndUtc`, so the holdout is never generated.
- Output lands in `data/strategy_runs/ma_20_50_<symbol>_<domain>_<stamp>/positions.parquet`.

## Fixed parameters (all 12 runs)

| Parameter | Value |
|---|---|
| `Mode` | `StrategyHost` |
| `Source Parquet Path` | *(leave empty — run on cTrader's feed, not a local file)* |
| `Fast MA` / `Slow MA` | `20` / `50` |
| `Strategy Output Directory` | *(default `data/strategy_runs`)* |

## Per-domain parameters

| Domain | `Domain Minutes` | `Strict Coverage` | `Min Coverage` |
|---|---|---|---|
| 5m | `5` | `true` | *(ignored)* |
| 1h | `60` | `false` | `0.9` |
| 4h | `240` | `false` | `0.9` |

## Per-instrument `Analysis End UTC` (the holdout fence)

Same value for all three domains of an instrument:

| Instrument | `Analysis End UTC` |
|---|---|
| BTCUSD | `2025-06-17T22:38:30Z` |
| EURUSD | `2025-05-09T16:55:30Z` |
| USTEC | `2025-05-12T04:54:30Z` |
| XAUUSD | `2025-05-12T03:35:30Z` |

(Each is just after that instrument's last first-70% analysis bar; on 1-minute bars
any time in the 30 s after the last bar fences identically.)

## Recommended order

1. **Pilot:** run **EURUSD / 5m** only. Tell me when its `positions.parquet` exists;
   I'll screen it and confirm the branch reproduces EXP-004/009 end to end. This
   validates the whole cTrader path before you do the other 11.
2. **Scale:** once the pilot passes, run the remaining 11 (4 instruments × 3 domains).

## What I do after each run

For each emitted run I call `xen.signals.screen_emitted_run(...)` with the matching
`train_end_utc` (the EXP-004 train/test boundary) so the split reproduces the
calibration exactly, then check the gate-stack verdict lands `REJECT` / `below_MDE`
(MA crossover is a known net-loser — a flipped verdict would mean a pipeline defect,
not a real edge). On success VAL-002's behavioral closure is met.
