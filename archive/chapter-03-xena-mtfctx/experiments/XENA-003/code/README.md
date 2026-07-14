# XENA-003 implementation notes (experiment-developer, 2026-07-11)

## Files

| Artifact | Path |
|---|---|
| C# model (entry/exit logic from scratch) | `StrategyHost/MtfCtxReversionModel.cs` |
| Native-order robot partial (NEW mode) | `Xen.NativeReversion.cs` (`XenMode.NativeOrders` = enum 3) |
| Registration | `Xen.cs` (`XenStrategy.MtfCtxReversion` = enum value 4; OnStart/OnBar/OnStop native branches) |
| Harness conf | `tools/ctrader-cli/experiments/XENA-003.conf` (`STRATEGY_VALUE="4"`, `MODE="3"`, `BALANCE=1e8`) |
| Manifest generator | `tools/ctrader-cli/experiments/gen_xena003_manifest.py` → `data/strategy_runs/XENA-003/universe_manifest.json` (2,736) |

Run (OPERATOR-GATED — execution approval required):
`cd tools/ctrader-cli && ./run-experiment.sh XENA-003 all` (or `parallel` / `one <SYM> <DOM>`).

## Execution architecture (EXP-013 carve-out)

Model computes quotes/exits only; the robot partial owns ALL broker interaction:
real `PlaceLimitOrder` / `ModifyTargetPrice` / `Cancel` per candidate side (label =
candidate id), engine m1 fills, `Positions.Opened/Closed` events routed back via
`INativeQuoteExecutor` + `OnEntryFilled`/`OnExitFilled`. `OnBar` replay path throws —
this model can never run self-adjudicated (EXP-013 guard). Fence stop: censor first
(model ledger), then cancel/flatten engine (events suppressed via `_nativeStopping`).

## Design-clause → code map (QA input)

| Design clause | Code location |
|---|---|
| §3 two-sided trailing quotes at min/max of last 3 CONFIRMED bars | `MtfCtxReversionModel.OnLtfBarCompleted` step (c): `_ltfWindow` (3 bars), `rangeLow`/`rangeHigh` |
| §3 crossed-limit rule (Amendment 1: passive-only) | quote block: `rangeLow < bid` / `rangeHigh > ask`; rejected engine orders simply absent that bar (`NativeQuoteExecutor.SyncQuote`) |
| §3 filters mask quoting per side; resting order cancelled when mask off | quote block: `VariantAllows(v, side)`; `SyncQuote(..., null)` cancels |
| §3 engine-native fills, one position at a time, other side cancelled on fill | `Xen.NativeReversion.OnNativePositionOpened`: `CancelSide(-side)`; `OnEntryFilled` |
| §3 exit 1: hold-period, market at open of fill_bar+hold | exits block: `held >= HoldBars` → `CloseCandidate("hold_period")` (fires at LTF bar roll = first m1 of the bar) |
| §3 exit 2: floating profit exit ≥ 0.5× CURRENT HTF medATR, no adverse target | exits block: `profitDist >= ProfitAtrMultiple * _medAtr` on `Close[t−1]`; `_medAtr` = latest confirmed HTF value (never entry-frozen) |
| §3 filters ≤ t−1, CloseTime alignment | HTF bucket roll before decisions (step (a)); features from completed buckets only |
| §3 ADX(14) Wilder / ±DI 25; median-TR ATR(14); vol P-rank 250 + hysteresis | `UpdateHtfFeatures` / `UpdateVolRegime` / `VariantAllows` (spec-identical family block — XENA-002 Amendment 2 scope) |
| §3 warmup suppression | quoting requires `_medAtrReady` + 3-bar `_ltfWindow`; variant features self-gate |
| §3 SlPrice = EntryFill ∓ 2×medATR at fill, sizing-only, no live stops | `OnEntryFilled` (uses ArmedAtr); `PlaceLimitOrder(..., candidateId)` passes NO SL/TP |
| §5 AnalysisEndUtc fence | `HoldoutFence` in `OnNativeBar` (m1 + LTF level); conf pins 2024-12-11T08:19:00Z all symbols |
| §7 censoring at fence | `CensorOpenLegs` (last mark = final bar open, NaN P&L) before engine flatten |
| Emission contract (positions grid + cis_trades, finite SlPrice) | `WriteCandidate`/`WritePositions`/`WriteCisTrades` |

## Deviations

None. Interpretations (header `DEVIATIONS` block in model file): decisions pinned to
"bar t open" execute at the first m1 tick after LTF bar completion (native-execution
reality; physicality tripwire audits fills vs raw m1); hold-exit-before-requote same-bar;
HTF pair map 60→1440/15→240/5→60; quoting requires medATR ready (SlPrice mandatory).
Crossed-limit rule = design Amendment 1 (operator-elicited before coding, per the
silent-deviation rule).

## Smoke verification (USTEC 1h cell, 2026-07-11)

- Build: `dotnet build Xen.csproj -c Debug` — 0 warnings, 0 errors.
- Emission: 76 candidate dirs under `data/strategy_runs/XENA-003/` + feed-level sentinel
  dir `mtfctx_c3_ustec_1h_20260711_142728/`. Smoke left in place for QA's golden-trace
  diff; the full run overwrites the same deterministic dirs.
- `xen.xena.ingest.gate_universe` on a 76-candidate smoke manifest (temp, deleted):
  **76/76 blocking_pass** — files, schema, non_empty, fence (max ExitTime 08:00 < 08:19),
  causality, stop_contract (finite SlPrice ≠ EntryFill), fill_consistency, oracle_smoke.
- Native-fill sanity (C3-USTEC-1D1H-H1X-V00): 1,087 trades; exits hold_period 625 /
  profit_exit 461 / censored_end 1; entry times at m1 granularity mid-LTF-bar
  (05:52 / 08:20 / 11:24 …) — real limit fills, not bar-open self-fills.
- Full estimand gate (`xen.estimand_validation --expect` 12 instruments) runs after the
  full emission, per design §7 HARD block.
