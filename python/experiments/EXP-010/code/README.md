# EXP-010 CONC-1 T1 — code map (price-primary; edge is IN-ENGINE)

The edge/anchor/fills are **C# in-engine** (L-01). Python here is analysis-only.

| Piece | Path |
|---|---|
| C# signal model (S5 exec-grid-β MR limit) | `StrategyHost/CrossDomainMrLimitModel.cs` |
| Basket feed abstraction | `StrategyHost/IBasketFeed.cs` |
| Multi-symbol feed impl (`MarketData.GetBars`, XRSI pattern) + wiring | `Xen.cs` (`MarketDataBasketFeed`, `CreateCrossDomainMrLimitModel`, enum `CrossDomainMrLimit`) |
| Provenance emission (EntryFillPrice/Anchor/Dev/Z/Vr/Hl/Beta) | `StrategyHost/SignalRecords.cs`, `StrategyRunParquetWriter.cs` |
| Live cells (5) + per-symbol fences + basket mates | `tools/ctrader-cli/experiments/EXP-010.conf` |
| Leak tripwire (phase-shifted basket) | `tools/ctrader-cli/experiments/EXP-010-shuffle.conf` (`--BasketPhaseShiftHours=2000`) |
| Ingest + validate + frozen-referee adjudication + Holm(5) + tripwire check | `code/run_experiment.py` |

## Run (Stage 3 — operator-gated, credentialed/cost cTrader)
```
dotnet build Xen.csproj -c Debug
tools/ctrader-cli/run-experiment.sh EXP-010 all           # live 5 cells
tools/ctrader-cli/run-experiment.sh EXP-010-shuffle all   # leak tripwire
python python/experiments/EXP-010/code/run_experiment.py  # analysis -> results/verdict.json
```

## Operationalizations flagged for audit (design left implicit)
1. **Entry-limit price = band-edge** `exp(a[t-1] ± Z*·σ[t-1])` (the "z=±2 band mapped to price").
2. **Mate causal read** = CloseTime ≤ traded bar (vs EXP-008 per-mate-own-first-49% slice; cutoffs near-identical → negligible).
3. **Leak tripwire** = basket phase-shift (decorrelates basket from price; destroys cross-domain co-movement, preserves marginals) rather than a full per-bar block shuffle.
4. **UNVERIFIED**: C# anchor/selector numerical parity vs `xen.cross_domain_mr` — audit-stage check (needs emissions).
