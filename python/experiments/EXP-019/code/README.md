# EXP-019 implementation notes (developer → QA input)

C# refs + conf notes only — NO Python analysis here (analysis = data-analyst's job).

## Files

| Artifact | Path |
|---|---|
| Model (new partial) | `Xen.RandomHold.cs` — DEVIATIONS block D1–D6 at top |
| Robot wiring | `Xen.cs` — enum `RandomHold`(=6), params `RhSchedulePath`/`RhSeed`/`RhMaxOpenLegs`, NativeOrders dispatch (OnStart/OnBar/OnStop), `BuildStrategyParameters` case |
| Schedule generator | `tools/ctrader-cli/experiments/gen_exp019_schedules.py` |
| Confs | `experiments/EXP-019-cal.conf` (16 calendar pre-runs), `EXP-019.conf` (16×25 live, seed via `EXP019_SEED`), `EXP-019-delay1.conf` (NZDUSD +1-bar twin ×25) |
| Campaign driver | `tools/ctrader-cli/run-exp019-all.sh` (phases cal/gen/live/twin/all) |
| Harness change | `run-experiment.sh` — `run_complete` now baseline-aware (repeated same-cell seeded runs no longer stopped early by the previous seed's finished dir) |
| Cost table (A5/D5) | `python/src/xen/evaluation.py` — `FTMO_COSTS`, `round_trip_cost_bps`; raw snapshot `code/ftmo_symbols_snapshot_20260704.json` |

## Design-clause → code map

| Design clause | Code location |
|---|---|
| §4 unconditional market entry at scheduled bar open | `FireRhScheduledEntries` (Xen.RandomHold.cs): fires rows whose `open_time_utc` == the FORMING bar's open → fill at its first m1 tick |
| §4 exit market at open of entry-bar + H, nothing else | `ProcessRhBar` matched-hold block: close at completed bar `EntryH4Index + H` → fill at open of next bar = fill-bar + H; no TP/SL/refresh anywhere in the partial |
| §4 inventory cap 6, skip + `cap_skip` log, never deferred | `FireRhScheduledEntries` cap branch → `SignalEventRecord("cap_skip")` + Print |
| §4 fixed 1-unit sizing | `_rhVolume = NormalizeVolumeInUnits(VolumeInUnitsMin)`, never varied |
| §4 seeded generator, calendar-only | `gen_exp019_schedules.py`: reads ONLY `SourceCloseTime` of `EXP-019-cal` emissions; base seed 20260705, seed_i = base+i; gap U[4,12]; dir coin; hold RR {6,12,24,48}; warmup 50 (A3); drop can't-complete (A2) |
| §4 fence / band | Confs `ANALYSIS_END` = EXP-013/018 49% cutoffs + 5 new same-rule values (A1); `HoldoutFence.ShouldStopBeforeProcessing` in `ProcessRhBar` |
| §3 estimand emission | Per-bar `SignalPositionRecord` (real OHLC, `OpenLegs`, `MtmBps`) + per-leg `CisTradeRecord` (`RealizedBps` gross, `Censored`, `HorizonBars`=hold) — `xen.estimand_validation` unchanged |
| §7 tripwire 1 (regeneration byte-diff) | Rerun `gen_exp019_schedules.py`, diff CSVs (deterministic from seed + calendar emission) |
| §7 tripwire 2 (fill causality) | `EntryTime` vs schedule `open_time_utc` (smoke: 620/727 exact, rest first-tick-of-session lag; 9 Sunday opens ≤ 1h) |
| §7 tripwire 3 (+1-bar twin) | `..._shift1.csv` (generator `shift=1`) + `EXP-019-delay1.conf` |
| §10 golden trace | NOT generated here (QA's job) — emission carries all needed columns |

## Smoke evidence (operator-approved 2026-07-04)

- `EXP-019-cal one NZDUSD 4h` → 5,927 bars, 2020-11-13→2024-09-06 fence, 0 trades.
- `EXP019_SEED=1 EXP-019 one NZDUSD 4h` → 727 legs, all `matched_hold`, holds exactly
  {6:182, 12:182, 24:182, 48:181}, dir 373/354, 0 censored, 0 cap_skips; 17 schedule rows
  stale (pre-2021 m1 feed start — uniform across seeds, disclosed).
- Estimand gate: `results/smoke_estimand_validation.json` → `BLOCKING_PASS: True`.
- `check_no_local_accounting('experiments/EXP-019')` → ok.

## How to run (operator-gated)

```
cd tools/ctrader-cli
./run-exp019-all.sh cal          # 16 calendar pre-runs (no orders)
./run-exp019-all.sh gen          # schedules (no engine)
./run-exp019-all.sh live         # 400 runs (16 × 25 seeds)
./run-exp019-all.sh twin         # 25 NZDUSD delay-twin runs
```

## Campaign note (2026-07-05)

Smoke seed-1 live run moved `data/strategy_runs/EXP-019/…225628` → `data/strategy_runs/EXP-019-smoke/`
before the full campaign launch (avoids a duplicate NZDUSD seed-1 emission in the family root;
QA golden-trace values recorded in qa-review.md reference the moved copy).

## Open item

- `FTMO_COSTS[*].spread_pips` = None: FTMO publishes spread live-only. Pin per-instrument
  spreads (read off https://ftmo.com/en/symbols/) before the binding cost read;
  `round_trip_cost_bps` raises until pinned (guard tested).
