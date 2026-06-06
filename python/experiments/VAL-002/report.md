# VAL-002 — INFR-001 cTrader Strategy-Branch Validation (Report)

**Type:** VAL-class infrastructure validation for INFR-001 (design.md v2). Not a
market-hypothesis experiment; the frozen referee suite is unchanged.
**Status:** **COMPLETE — PASS** (2026-06-06).

## Question

Before any cTrader-sourced output is admitted to the research pipeline, does the
cTrader strategy branch (a) transcribe the ported C# generator/indicator library to
its Python references, and (b) reproduce the established EXP-004/009 MA-crossover
verdict when MA positions are generated **in cTrader's own engine** and screened
through the frozen suite?

## Method (design.md v2)

1. **Transcription smoke** (`code/run_experiment.py`, console exporter over the shared
   C# code): each C# port (`linebreak`, `renko`, `heiken_ashi`, `bar_aggregator`,
   `market_bias`) compared to its Python reference on the first-70% analysis slice —
   exact for timestamps/categoricals/ints/bools, 1e-8 float tolerance — plus a holdout
   fence on every emitted timestamp.
2. **Behavioral closure** (`code/screen_ctrader_runs.py`): for all 12 cells, a real
   `Mode=StrategyHost` cTrader backtest emitted `data/strategy_runs/<run>/positions.parquet`
   (position series + the real OHLC executed on). Each run was routed through the
   **unchanged** frozen suite via `xen.signals.screen_emitted_run`, building next-step
   returns from the **emitted `RealClose`** (fence #4), reproducing the EXP-004
   within-analysis split (`train_end_ts`) and EXP-004 seeding, then classified against
   the EXP-003 MDE map with the same helpers `run_experiment.py` uses (so the table is
   directly comparable to the console reference).

## Results

| Leg | Artifact | Outcome |
|---|---|---|
| Transcription | `results/parity_checks.csv`, `results/run_metadata.json` | **108/108 PASS**, 0 failures |
| Behavioral closure | `results/suite_reproduction_ctrader.csv`, `results/ctrader_closure_metadata.json` | **24/24 rows PASS** (12 cells × 2 referees) |

- Every cell: `verdict = REJECT`, `exp004_consistency_status = PASS` /
  `matched_reject`, gate-stack `exp009_location_vs_mde = below_MDE`. Reproduces
  EXP-004 (`matched_reject`) and EXP-009 (gate-stack `below_MDE`) for all 12 cells.
- **Holdout fence:** max `SourceCloseTime` strictly before `AnalysisEndUtc` in every
  cell (`holdout_fence_ok = true`); the in-robot self-guard stopped emission at the
  fence.
- **Fidelity vs the independent console oracle (gate-stack effect):**
  - **5m: diff = 0.000000 bps, identical `effective_n`** for all four instruments —
    cTrader's own feed reproduces local 5m-strict aggregation bit-for-bit, and the two
    independent execution paths over the shared C# code agree to full float precision.
  - **1h: |diff| ≤ 0.18 bps; 4h: |diff| ≤ 1.83 bps** (largest BTCUSD/4h: −10.37 vs
    −12.20, `effective_n` 1105 vs 1335). cTrader's own feed yields slightly different
    `min_coverage=0.90` window membership at 1h/4h than local aggregation. Every cell
    stays far below its domain MDE; the *classification* is invariant.

The bit-identical 5m agreement and the per-run recorded config are direct evidence of
deterministic, config-faithful cTrader generation; the 1h/4h deltas are a *feed*
difference, not non-determinism — exactly the regime design.md v2 anticipated when it
set the acceptance standard to **behavioral verdict reproduction, not byte-identity**.

## Conclusion

**PASS.** The cTrader strategy branch transcribes correctly and reproduces the known
EXP-004/009 verdict end-to-end from real in-engine runs, with the holdout fence intact.
cTrader-emitted output is admissible to the research pipeline. This closes the binding
v2 behavioral gate (INFR-001 design §6.2).

## Reproduce

```bash
cd python
# Transcription smoke (console exporter over shared C# code):
uv run python experiments/VAL-002/code/run_experiment.py --skip-suite
# Behavioral closure over the emitted cTrader runs:
uv run python experiments/VAL-002/code/screen_ctrader_runs.py
```

cTrader runs themselves are operator-generated in cTrader's backtester per
`ctrader-run.md` (fixed per-cell params + per-instrument `AnalysisEndUtc`).
