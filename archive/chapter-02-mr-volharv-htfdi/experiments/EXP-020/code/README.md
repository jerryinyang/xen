# EXP-020 implementation notes (experiment-developer, 2026-07-05)

C# models + confs for design.md (incl. A1 params, §3 unwind + twin clarifications).

## Files

| File | What |
|---|---|
| `Xen.StructureHarvest.cs` | ARM R `rebalance_harvest` + ARM G `grid_harvest` (partial class, Mode=NativeOrders) |
| `Xen.cs` | enum `RebalanceHarvest`/`GridHarvest`; params `ShTwin`/`ShBandW`/`ShGridBps`/`ShDelayBars`; start/OnBar/OnStop routing; run_metadata provenance |
| `StrategyHost/SignalRecords.cs` + `StrategyRunParquetWriter.cs` | +3 per-bar columns `PortWeight`/`PortUnits`/`PortCash` (ARM R path estimand; NaN for all other models) |
| `tools/ctrader-cli/experiments/EXP-020-{R,R-twin,G,G-invert,R-delay1,G-delay1}.conf` | 6 confs = 68 cells; per-symbol `--ShBandW`/`--ShGridBps` verbatim from `results/exp020_params.csv` |
| `code/derive_exp020_params.py` | §11.1 param derivation (pre-existing; QA byte-diff = tripwire 2) |

Run: `tools/ctrader-cli/run-experiment.sh EXP-020-R` (etc., one per conf) → family roots
`data/strategy_runs/EXP-020-R/` … one root per arm.

## Design-clause → code map (QA input)

| Design clause | Code |
|---|---|
| §3 R trigger `|w−w*|≥b` at t−1 close, trade at open t | `ProcessRebBar` (decision on completed bar `effIdx=i−delay`, market order fills first m1 tick of forming bar) |
| §3 R twin never rebalances | `!ShTwin` guard on the trigger block; init identical |
| §3 R per-bar path + trade ledger | `EmitRebBar` (`PortWeight/PortUnits/PortCash`, `MtmBps`= portfolio bps vs V0) + `RebBookTrade` → trade_blotter (PositionDelta = signed Δunits); `cis_trades` intentionally EMPTY (path object, not legs) |
| §3 G anchor = prev-month close, monthly reset, inventory carried | `ProcessGridBar` boundary detection (forming-bar month change) → `_gridAnchor=Close[boundary]`; `CancelGridEntryOrders` cancels ENTRY orders only; legs+TPs untouched |
| §3 G levels A±k·g, k=1..4, 1 unit, native pending | `ArmGridLevels` + `GridLevel`; `PlaceLimitOrder`/`PlaceStopOrder`, min volume |
| §3 G unwind buy A−k·g → sell A−(k−1)·g (T2) | `GridLevel` MR branch; TP set at fill (`ModifyTakeProfitPrice`) |
| §3 G inverted twin: stops, unwind one level AWAY (2026-07-05 clarification) | `GridLevel` twin branch |
| §3/T3 cap 8: would-be order NOT placed, logged | `ArmGridLevels` cap check (`open legs + pending ≥ 8` → `cap_skip` event) |
| §2 fills = m1 touch (tripwire 3 substrate) | native pending orders/TP, Mode=3; fill timestamps + prices in cis_trades |
| §7 tripwire 1 (+1 delay, both arms) | `ShDelayBars` shifts every decision index (`effIdx`, boundary reset, arm validity close) |
| §7 tripwire 2 (param provenance) | conf values verbatim `repr()` of `exp020_params.csv`; rerun byte-diff verified at derivation |
| VAL-006 censoring | `FlushGridCensored` → `open_at_end`, `Censored=1`, marked to last close |
| Fence | `HoldoutFence.ShouldStopBeforeProcessing` per bar; EXP-019 `AnalysisEndUtc` verbatim per symbol |

## Sizing note (ARM R)

Real position, virtual cash leg. `RebInitialUnits` = normalize(10·volStep/b_w) ⇒ smallest
band-triggered trade ≈ 2·b_w·u0 ≈ 20 volume steps (granularity <~5%/trade; scale cancels in
the log-return path). Sub-min-volume trades skipped + logged `min_vol_skip` (disclosure).

## Deviations

None in strategy semantics. Recorded (also in the model-file DEVIATIONS block):
1. Conf packaging: 6 multi-symbol confs (one family root per arm), not 68 single-symbol
   confs — the EXP-019 D6 operator-approved pattern; same 68 cells.
2. Design §3 clarifications folded in pre-implementation (dated in design.md): T2 unwind
   arithmetic; inverted-twin stop entries + unwind-away rule (only non-degenerate mirror of
   B-6). Operator ratifies at the execution gate.

## Smoke / estimand validation

NOT run: execution is credentialed + operator-gated. First action after gate approval:
one smoke cell (suggest `EXP-020-G` NZDUSD) then
`python -m xen.estimand_validation data/strategy_runs/EXP-020-G --out python/experiments/EXP-020/results/smoke_estimand_validation.json`.
Build verified: `dotnet build Xen.csproj -c Debug` → success.
