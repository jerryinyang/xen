# VAL-002 — INFR-001 cTrader Strategy-Branch Validation

**Type:** VAL-class infrastructure validation for INFR-001 (design.md **v2**). Not a
market-hypothesis experiment; does not alter the frozen referee suite.

## Objective

Validate the cTrader strategy branch before any cTrader-sourced output is admitted to
the research pipeline, on the **v2** terms (design.md §0, R1 reconciliation):

1. **Transcription (one-time):** each ported C# generator/indicator reproduces its
   existing Python reference (`generate_linebreak`, `generate_renko`,
   `generate_heiken_ashi`, `aggregate_ohlc`, `compute_market_bias`) on fixture bars.
2. **Behavioral closure (binding):** the cTrader-emitted MA positions, evaluated on
   the **emitted real OHLC**, reproduce the known EXP-004/009 verdict when routed
   through the frozen suite via the `xen.signals` ingestion harness.

Python is validation/ingestion only — it does **not** re-generate the strategy signal.
The removed Python MA generation engine and its byte-parity check are superseded.

## In Scope

- **Transcription** (C# vs existing Python generators), exact for timestamps/
  categoricals/ints/bools, tight float tolerance:
  - Line Break (`level=3`), Renko (`atr_period=14`), Heiken Ashi,
    Bar aggregation `5m/1h/4h`, Market Bias on those domains.
- **Holdout fence:** all emitted timestamps strictly before `AnalysisEndUtc`.
- **Behavioral closure:** cTrader `Mode=StrategyHost` `positions.parquet` (with real
  OHLC) → `xen.signals.screen_emitted_run` → reproduce EXP-004 `matched_reject` and
  EXP-009 gate-stack `below_MDE`.

## Out of Scope

- AVWAP, Phase 004 signal exploration, multiplicity registry.
- Modifying strict/loose/incremental referee code.
- Execution realism (trade blotter remains diagnostic only).
- Byte-parity of a Python MA *generation* engine — removed under v2.

## Data Fence

For each base time-bar Parquet, VAL-002 uses only the first 70% chronological
analysis slice. `AnalysisEndUtc` is one microsecond after the last included analysis
bar, so the full analysis slice is covered without reading the first holdout row.

## Validation Paths

- **Behavioral closure (binding, operator step).** Run `Mode=StrategyHost` in
  cTrader's engine to emit `positions.parquet`; the ingestion harness routes it
  through the frozen suite. This is the v2 closure.
- **Transcription smoke (developer).** `Mode=StrategyHostParity` (or the
  `tools/StrategyHostParity` console exporter over the same shared C# code) writes the
  generator/indicator/MA CSV family that `run_experiment.py` compares to the Python
  references. A developer aid, **not** the closure path.

## Success Criteria

VAL-002 passes only when every transcription and holdout check passes **and** the
cTrader-emitted MA positions reproduce the EXP-004/009 classification through the
frozen suite.

## Status

**COMPLETE — PASS (2026-06-06).** Both legs closed:

1. **Transcription smoke (PASS):** 108/108 parity checks, 0 failures
   (`results/parity_checks.csv`, `results/run_metadata.json`).
2. **Behavioral closure (PASS):** all **12** cells (4 instruments × 3 domains) were run
   as real `Mode=StrategyHost` cTrader backtests; the emitted `positions.parquet`
   (on emitted real OHLC) were routed through the frozen suite via
   `xen.signals.screen_emitted_run` (EXP-004 split + seed). **24/24 rows REJECT, all
   gate-stack `below_MDE`, all `matched_reject`** — reproducing EXP-004/009 for every
   cell. Holdout fence respected (max `SourceCloseTime` < `AnalysisEndUtc`, all cells).
   See `results/suite_reproduction_ctrader.csv`, `results/ctrader_closure_metadata.json`,
   and `report.md`.

Fidelity note: the 5m cells reproduce the independent console table to full float
precision (diff = 0.0); 1h/4h differ by ≤ 1.83 bps (cTrader's own-feed coverage-filtered
windows differ slightly from local aggregation) — well within the **behavioral**, not
byte-identical, standard mandated by design.md v2 (§6.2). All remain far below MDE.
