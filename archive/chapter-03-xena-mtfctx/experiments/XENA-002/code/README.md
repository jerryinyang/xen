# XENA-002 implementation notes (experiment-developer, 2026-07-11)

## Files

| Artifact | Path |
|---|---|
| C# model (from scratch) | `StrategyHost/MtfCtxMomentumModel.cs` |
| Registration | `Xen.cs` (`XenStrategy.MtfCtxMomentum` = enum value 3; `CreateStrategyModel()`; `BuildStrategyParameters`) |
| Harness conf | `tools/ctrader-cli/experiments/XENA-002.conf` (`STRATEGY_VALUE="3"`) |
| Manifest generator | `tools/ctrader-cli/experiments/gen_xena002_manifest.py` → `data/strategy_runs/XENA-002/universe_manifest.json` (2,736) |

Run (OPERATOR-GATED — blocked on XENA-001 retro read):
`cd tools/ctrader-cli && ./run-experiment.sh XENA-002 all` (or `parallel` / `one <SYM> <DOM>`).

## Design-clause → code map (QA input)

| Design clause | Code location (MtfCtxMomentumModel.cs) |
|---|---|
| §3 entry signal Close[t−1] vs High/Low[t−4..t−2], strict, ties=none | `OnBar` step (b): `_ltfWindow` (4 confirmed bars), `prevClose`/`rangeHigh`/`rangeLow` |
| §3 same-bar-open fill, flat-only, filter mask | `OnBar` step (c): entry sets `EntryFill = bar.Open` |
| §3 exit at open after hold bars | `OnBar` step (c): `_barIndex - EntryBarIndex == HoldBars` → `CloseLeg(exitFill: bar.Open)` |
| §3 hold-exit-before-entry same-bar convention | order inside step (c) loop; interpretation recorded in file header |
| §3 filters ≤ t−1, CloseTime alignment | HTF bucket roll before decisions (step (a)); features from completed buckets only |
| §3 ADX(14) Wilder / ±DI, threshold 25 | `UpdateHtfFeatures` (Wilder smoothing), `VariantAllows`, `DiAllows` |
| §3 median-TR ATR(14) | `UpdateHtfFeatures` (rolling median of 14 TRs) |
| §3 vol regime P-rank 250 + hysteresis 80/65/20/35 | `UpdateVolRegime` |
| §3 variant map V00–V18, combo order | `VariantAllows` (order pin in comment) |
| §3 warmup suppression | entry requires `_medAtrReady` + 4-bar `_ltfWindow`; variant features gate themselves (`_adxReady`/`_volReady`) |
| §3 SlPrice = EntryFill ∓ 2×medATR, sizing-only | entry block; no stop orders anywhere |
| §5 AnalysisEndUtc fence | harness `HoldoutFence`; conf pins 2024-12-11T08:19:00Z all symbols |
| Amendment 1 from-scratch | new file; no code imported from MtfCtxRandomModel; features implemented from family spec (QA spec-equivalence check) |
| Emission contract (positions + cis_trades, finite SlPrice) | `WriteCandidate`/`WritePositions`/`WriteCisTrades` |

## Deviations

None. Interpretations (header `DEVIATIONS` block): hold-exit-before-entry same-bar;
HTF pair map 60→1440/15→240/5→60; entry additionally requires medATR ready (SlPrice
mandatory) + 4 confirmed LTF bars.

## Smoke verification (USTEC 1h cell, 2026-07-11)

- Build: `dotnet build Xen.csproj -c Debug` — 0 warnings, 0 errors.
- Emission: 76 candidate dirs under `data/strategy_runs/XENA-002/` + feed-level
  sentinel dir `mtfctx_c2_ustec_1h_20260711_121327/`. Smoke emission left in place
  for QA's golden-trace diff; the full run overwrites the same deterministic dirs.
- `xen.xena.ingest.gate_universe` on a 76-candidate smoke manifest (temp, deleted):
  **76/76 blocking_pass** — files, schema, non_empty, fence (max ts 08:00 < 08:19),
  causality, stop_contract (finite SlPrice ≠ EntryFill), fill_consistency (max
  |RealizedBps − fills-derived| = 0.0000 bps), oracle_smoke (deterministic).
- Filter masking monotone sanity: H1X trades V00 874 / V03 737 / V06 201.
- Full estimand gate (`xen.estimand_validation --expect` 12 instruments) runs after
  the full emission, per design §7 HARD block.
