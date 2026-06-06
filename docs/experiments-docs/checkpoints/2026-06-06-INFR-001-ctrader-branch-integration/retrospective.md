# INFR-001 — cTrader Branch & Strategy-Host Integration (Retrospective)

**Checkpoint type:** Infrastructure (not an experiment phase). Governed as an
operator-reviewed design + build, gated by VAL-class transcription + integration
validation — not per-hypothesis pre/post governance (design §3).
**Outcome:** **COMPLETE — all four §6 acceptance gates PASS (2026-06-06).**
**Validation vehicle:** VAL-002 (`python/experiments/VAL-002/`).

---

## 1. Objective vs outcome

Build and integrate the cTrader execution branch — strategies run as **real cAlgo
robots in cTrader's engine**, only signal-generation code ported to C#, all strategy
validation staying in Python — proven end-to-end with MA crossover (MA 20/50), whose
suite verdict is already established (EXP-004 `matched_reject`; EXP-009 gate-stack
below every domain MDE). **Achieved in full.**

The load-bearing v2 correction (§0) held: generation/execution lives in cTrader, Python
is validation/ingestion only, and acceptance is **behavioral verdict reproduction, not
byte-identity**. The build delivered the A1 strategy-host + Python ingestion harness
(`xen.signals`), the A2 full C# port (`linebreak`, `renko`, `heiken_ashi`,
`bar_aggregator`, `market_bias`), the A3 MA-crossover cAlgo with dataset emission, the
A4 holdout fence + self-guard, the A5 transcription tests, and the A6 end-to-end
integration run.

## 2. Acceptance gates (design §6)

| # | Gate | Result | Evidence |
|---|---|---|---|
| 1 | **Transcription (A5)** — 5 C# ports vs Python references on fixture/analysis bars | **PASS** — 108/108, 0 failures | `VAL-002/results/parity_checks.csv`, `run_metadata.json` |
| 2 | **End-to-end integration (A6)** — frozen suite on cTrader-emitted MA positions reproduces EXP-004/009 | **PASS** — 24/24 rows REJECT, all gate-stack `below_MDE`, all `matched_reject`, 12/12 cells | `VAL-002/results/suite_reproduction_ctrader.csv`, `ctrader_closure_metadata.json` |
| 3 | **Holdout fence** — emitted max timestamp before `AnalysisEndUtc`; self-guard fails closed | **PASS** — every cell (`holdout_fence_ok = true`); e.g. BTCUSD max `2025-06-17 22:35:00` < fence `22:38:30Z` | same; in-robot self-guard + `assert_run_within_holdout` |
| 4 | **Reproducibility (behavioral)** — recorded config reproduces datasets + verdict | **PASS (behavioral)** — verdict reproduces EXP-004/009 for all 12; 5m matches the independent console oracle to full float precision; per-run config recorded | see §3 |

A failure in any gate would have kept INFR-001 open; none failed.

## 3. The fidelity signal (why this is strong, and its one honest caveat)

Routing the 12 real-engine runs through the frozen suite and comparing the gate-stack
effect to the independent console exporter (same shared C# code, different execution
path **and** different data feed):

- **5m (strict coverage): diff = 0.000000 bps, identical `effective_n`** for all four
  instruments. Two independent paths landing bit-identical is direct evidence of
  deterministic, config-faithful generation.
- **1h: |diff| ≤ 0.18 bps; 4h: |diff| ≤ 1.83 bps** (largest BTCUSD/4h: −10.37 vs −12.20;
  `effective_n` 1105 vs 1335). cTrader's own feed yields slightly different
  `min_coverage=0.90` window membership at 1h/4h than local aggregation — a **feed**
  difference, not non-determinism. Every cell stays far below its domain MDE and the
  classification is invariant.

This is exactly the regime §6.2/fence #2 anticipated when it set the standard to
behavioral reproduction. **Honest caveat:** a *formal twice-run* cTrader determinism
check (running one cell twice in-engine and diffing) was not performed; gate 4 rests on
(a) the bit-identical 5m cross-oracle agreement, (b) recorded per-run config
(`run_metadata.json`), and (c) verdict reproduction. The optional twice-run is a cheap
future confirmation if belt-and-suspenders determinism is ever wanted (operator step in
cTrader, then re-run `screen_ctrader_runs.py`).

## 4. What the operator did vs what was automated

- **Operator (cTrader, manual):** 12 `Mode=StrategyHost` backtests per `ctrader-run.md`
  (fixed MA 20/50, per-domain coverage, per-instrument `AnalysisEndUtc`), emitting
  `data/strategy_runs/<run>/`. A pilot (BTCUSD/5m) validated the path before the other 11.
- **Automated (Python, this pipeline):** `screen_ctrader_runs.py` re-derived each
  instrument's EXP-004 `train_end_ts` from the first-70% analysis slice, screened all 12
  runs through the unchanged frozen suite, classified vs the EXP-003 MDE map, re-asserted
  the holdout fence, and emitted the closure table + metadata.

## 5. Scope discipline

No frozen-suite code was modified. No AVWAP-specific primitives were built. The trade
blotter remained diagnostic only (D-cost). The 1-minute data architecture was not
reopened. MA crossover was used strictly as a known-truth plumbing vehicle and did not
touch any multiplicity/file-drawer registry (a Task-B artifact).

## 6. What this unlocks

On INFR-001 completion the cTrader branch is the realtime-parity generation/execution
substrate: strategies run as real cAlgos in-engine, holdout-fenced, reproducible, with
the signal-gen library available in C#. **The D-seq hard block is lifted — Phase 004 /
AVWAP signal exploration may now open**, behind its mandatory programme-level
**multiplicity / file-drawer registry** precondition (P3-§11), which — with the registry
standard, hypothesis-decomposition methodology, and AVWAP "thick" primitives — is
**Task B** (design §8).

## 7. Deferred / not done (by design)

- Formal twice-run cTrader determinism check (§3 caveat) — optional confirmation.
- A7 reference-doc sweep beyond the index/checkpoint updates (architecture.md /
  dataset-reference.md already carry working-tree edits for the cTrader branch; confirm
  the emitted `strategy_runs` schema is captured there before Task B authors new cAlgos).
- Everything in design §8/§9 Task-B scope (registry, AVWAP primitives, execution-realism
  research, tick data).
