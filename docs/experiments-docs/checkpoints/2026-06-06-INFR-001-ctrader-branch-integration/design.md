# INFR-001 — cTrader Branch & Strategy-Host Integration

**Checkpoint type:** **Infrastructure** — *not* an experiment phase. There is no falsifiable market hypothesis and no holdout measurement of a thesis. INFR-001 is governed as an **operator-reviewed design + build**, gated by **transcription and integration validation** (VAL-class), not by per-hypothesis pre/post-execution governance verdicts. It does **not** flow through the 8-stage experiment pipeline.

**Date finalised:** 2026-06-06 (revised 2026-06-06 to correct the execution model — see §0).
**Status:** **COMPLETE — all four §6 acceptance gates PASS (2026-06-06)** via VAL-002. Scope was locked by operator decisions 2026-06-06 (D-seq, D-engine, D-port, D-vehicle, D-exec, D-parity, D-cost below); closure recorded in [retrospective.md](retrospective.md).
**Sequencing:** This is **Task A** and the **sole current focus**. **Phase 004, AVWAP, and all signal exploration are hard-blocked until INFR-001 completes.**

**Provenance.** Phase 003b concluded the framework-construction programme and unlocked Phase 004 behind its mandatory programme-level multiplicity-registry precondition (P3-§11). Before opening Phase 004, the operator directs a prior infrastructure task: build and integrate a **cTrader execution branch** into the research pipeline, proven end-to-end against the existing Python validation suite using **MA crossover** as a known-truth test vehicle. The frozen qualification suite — `{strict gate stack, EXP-012 ratified-loose referee, EXP-018 revised incremental/fitness unit}` — is carried in **untouched**.

---

## 0. Execution model (the load-bearing correction)

The cTrader branch means **strategies run as real cAlgo robots inside cTrader's algo engine** (Automate / backtester), driven by cTrader's own data feed and execution model, emitting datasets during the run — exactly as `Xen.cs` runs in cTrader to generate the `timebars` dataset. It does **not** mean reimplementing the library in C# and running it locally over the collected Parquet for byte-parity. Explicitly:

- **Generation/execution lives in cTrader.** Python never executes a strategy.
- **Only signal-generation code is ported to C#** (chart types + indicators), so cAlgo strategies compute signals natively in-engine without a Python runtime dependency.
- **All strategy validation stays in Python** — the frozen suite and characterization layer consume the cTrader-emitted datasets.

This matches `signal-registry/README.md` concern #4 verbatim ("employ cTrader's backtester to run strategies and generate data… replicate only signal-generation code to C#… all strategy validation tests remain in python"). A prior draft of this design leaned the other way (local C# reimplementation validated byte-for-byte against a Python generation oracle); that framing is **superseded** by this section.

---

## 1. Objective

Develop and integrate the **cTrader branch**: a cAlgo **strategy-host / adapter model** that runs registry strategies **bar-by-bar in realtime parity** (cTrader's native event loop, look-ahead-free) and emits the signal / position / event / trade datasets the Python validation framework consumes — validated **end-to-end** against the frozen qualification suite using MA crossover, whose suite verdict is already established (EXP-004 `matched_reject`; EXP-009 below every domain MDE).

Three pillars:

1. **cAlgo strategy-host / adapter model** — a reusable cTrader-side base that any strategy plugs into, handling the event loop, holdout fence, deterministic run config, and dataset emission. Plus a thin **Python ingestion harness** that reads emitted datasets and routes the position series to the frozen suite.
2. **Full C# port of the existing validated generator/indicator library** — `linebreak`, `renko`, `heiken_ashi`, `bar_aggregator`, `market_bias` — as **cAlgo-API-agnostic C# classes** (so they unit-test standalone and the robot is a thin shell), each with a **one-time transcription test** against its Python reference (D-parity).
3. **End-to-end integration** — MA crossover as a real cAlgo, run in the cTrader backtester over the analysis window, emitting a position series that the frozen suite screens to **reproduce the EXP-004/009 verdict**, with the holdout fence and reproducibility intact.

The deliverable is a realtime-parity generation/execution substrate in cTrader, feeding the unchanged Python validation layer.

---

## 2. Locked scope decisions (operator, 2026-06-06)

Frozen for the checkpoint. Changing any after dependent build work begins requires a dated amendment recorded before that work is validated.

| # | Decision | Resolution |
|---|---|---|
| **D-seq** | Sequencing | **cTrader branch is the sole focus.** AVWAP / Phase 004 / all signal exploration **hard-blocked** until INFR-001 completes. |
| **D-exec** | Execution model | **Strategies run as real cAlgo robots in cTrader's engine** (Automate/backtester), on cTrader's feed, emitting datasets during the run (§0). Python = validation/analysis only; it never executes a strategy. |
| **D-engine** | Signal-engine scope | **Generic adapter/host only.** Build the reusable cAlgo strategy-host + the Python ingestion harness, exercised **solely by MA crossover**. AVWAP-specific "thick" primitives (pivot tracker, the four regime detectors, cumulative VWAP `w=TVᵅ`, MAD bands, anchor management) are **deferred to Task B**. |
| **D-port** | C# port width | **Full library port now**, as cAlgo-API-agnostic C# classes: `linebreak`, `renko`, `heiken_ashi`, `bar_aggregator`, `market_bias`. AVWAP primitives excluded (not yet in Python — Task B). |
| **D-parity** | Port validation | **One-time transcription test per port.** Each C# class is unit-tested against its Python reference on fixture bars (correct transcription), then deployed in cTrader. Operating-mode validation is **behavioral** (the suite reproduces the known result), since a cTrader run over its own feed will not byte-match a local Python run. |
| **D-cost** | Integration cost basis | The cAlgo emits a **clean position series**; the Python suite applies its **flat scoped cost** — apples-to-apples with the EXP-004/009 calibrated MDE map. cTrader's real fills / spread / slippage are captured **as a separate diagnostic blotter**, not a qualification input here. |
| **D-vehicle** | Test vehicle | **MA crossover (MA 20/50, EXP-004/009 definition).** A plumbing validation with a pre-known result — **not** a candidate screen; does **not** touch the multiplicity / file-drawer registry (a Task-B artifact). |
| **D-resample** | Domain construction | The cAlgo resamples 1-minute bars to 5m/1h/4h **using the ported `bar_aggregator`** (clock-aligned, `min_coverage` per the existing convention), so domain construction matches EXP-004/009 rather than relying on cTrader's native higher-timeframe bars (which may use different session/aggregation rules). |

---

## 3. Governance fences (carried from programme invariants — non-negotiable)

1. **Holdout.** The backtest is **date-bounded to `AnalysisEndUtc`** (the frozen first-70% cutoff), and the cAlgo **self-guards** (refuses to process or emit any bar at/after `AnalysisEndUtc`) as a fail-safe. The Python ingestion harness re-asserts the bound. The sealed final 30% is never run over, emitted, or inspected.
2. **Reproducibility.** cTrader backtests are run over a **fixed symbol / timeframe / date-range / data source with recorded config**, so they reproduce. Acceptance is **behavioral reproduction** (the suite verdict), not byte-identity — the realistic standard once cTrader's engine is in the loop.
3. **Generation in cTrader, validation in Python (D-exec).** Python consumes emitted datasets; it does not regenerate signals as an authority. The one-time transcription tests (D-parity) are the only place the Python generators serve as a reference, and only on fixture bars.
4. **Real-price outcome discipline & MDE comparability.** The cAlgo **emits the real OHLC it executed on** alongside the position series, so the suite evaluates positions on cTrader's own prices (self-consistent), with the flat scoped cost (D-cost) preserving comparability to the frozen 1/4/12, 0.5/2/8, 12/16/32 maps. HA/Renko construction prices are never used for P&L.
5. **Streaming / causal semantics.** The cAlgo runs in cTrader's native bar/tick event loop — inherently look-ahead-free and realtime-faithful. Timestamp alignment (`CloseTime` / `SourceCloseTime`) over bar count, always.

---

## 4. Deliverables & work streams

| # | Stream | Where | Output |
|---|---|---|---|
| **A1** | **Strategy-host / adapter model** (cAlgo base: event loop, fence, deterministic run config, dataset emission) **+ Python ingestion harness** (read emitted Parquet → position-series + real-return format → route to frozen suite) | cTrader (C#) + Python | cAlgo host classes in the cAlgo project; `xen` ingestion module |
| **A2** | **C# library port (full)** as cAlgo-API-agnostic classes — `linebreak`, `renko`, `heiken_ashi`, `bar_aggregator`, `market_bias` — callable by cAlgo robots and unit-testable standalone | cTrader (C#) | C# generator/indicator classes |
| **A3** | **MA-crossover cAlgo + dataset emission** — MA(20/50) as the first strategy on the adapter; runs on resampled 5m/1h/4h domains (D-resample); emits position series + real OHLC + event log + diagnostic trade blotter + run metadata | cTrader (C#) | cAlgo strategy + emitted Parquet datasets |
| **A4** | **Holdout fence + reproducibility** — `AnalysisEndUtc` date-bound + in-robot self-guard; recorded backtest config / data-source / generator versions | cTrader (C#) | fence + run-metadata emission |
| **A5** | **Transcription tests (VAL-class)** — one-time per-port logic-parity unit tests (A2: five classes) vs Python reference on fixture bars, to predeclared tolerance | C# test project + Python fixtures | per-port transcription proofs (candidate VAL-002+) |
| **A6** | **End-to-end integration test** — run the MA-crossover cAlgo in the backtester over the analysis window; ingest its position series; frozen suite must reproduce EXP-004/009 (REJECT, below every domain MDE) | cTrader run + Python | integration validation artifact |
| **A7** | **Reference/architecture/config updates** — `architecture.md`, `dataset-reference.md`, pipeline config, skills: the cTrader execution branch, adapter model, emitted dataset schemas, the transcription-test gate, the C# port library | docs | updated reference docs |

### 4.1 C# port targets (A2) and their transcription references

| Module | Python reference | Transcription basis (on fixture bars) |
|---|---|---|
| Line Break | `xen.linebreak_generator` (`level`, default 3) | identical confirmed-line sequence + schema |
| Renko (ATR) | `xen.renko_generator` (`atr_period`, default 14) | identical brick sequence; causal ATR; `SourceCloseTime` |
| Heiken Ashi | `xen.heiken_ashi_generator` | identical HA + Real OHLC columns |
| Bar aggregator | `xen.bar_aggregator` (N-min clock-aligned; `min_coverage`) | identical 5m/1h/4h OHLC + coverage/dropped-window behaviour |
| Market Bias | `xen.indicators.market_bias` (CEREBR; EMA/HA recursion; warmup) | identical state labels beyond the warmup floor |

Ports are cAlgo-API-agnostic so the transcription tests run in a standalone C# test project against Python-exported expected fixtures — mirroring how `Xen.cs` separates bar capture from the Parquet writer.

---

## 5. Emitted dataset schema (cAlgo output)

Each backtest run emits a dataset family (path pattern fixed in A1; candidate `data/strategy_runs/<strategy>_<symbol>_<domain>_<serverStamp>_<localStamp>.parquet`), carrying:

- **Position series:** `SourceCloseTime` (real-time anchor), `Domain`, `Position ∈ {−1,0,+1}`, raw signal value(s), warmup/flat flags.
- **Real OHLC executed on:** the actual bar prices the strategy saw at each step (for self-consistent suite evaluation — fence #4).
- **Event log:** discrete strategy events (e.g. crossover events) with real-time timestamps.
- **Diagnostic trade blotter:** cTrader fills / spread / notional — **diagnostic only** (D-cost), not a qualification input in INFR-001.
- **Run metadata:** strategy + parameters, `AnalysisEndUtc`, domain/coverage config, port/generator versions, data-source + backtest config, reproducibility markers.

Only the **position series on the emitted real OHLC** is routed into the frozen suite. Schemas recorded in `dataset-reference.md` (A7).

---

## 6. Validation gates (acceptance criteria)

INFR-001 is **COMPLETE** only when all pass:

1. **Transcription tests (A5):** each of the five C# ports reproduces its Python reference on fixture bars to a predeclared tolerance (byte-identical for integer/categorical fields; tight float tolerance with recorded rationale). Known traps checked explicitly: warmup/NaN handling (positions flat, not dropped — per EXP-009), `market_bias` EMA-seed warmup floor, Renko ATR causality, aggregator coverage/dropped-window rules.
2. **End-to-end integration (A6):** the frozen suite, fed the **cTrader-emitted** MA position series on its emitted real OHLC, reproduces EXP-004/009 — REJECT with measured effect below every domain MDE — within reproduction tolerance. (MA crossover is a robust net-loser well below MDE in EXP-009, so this is a *forgiving* check; a flipped verdict would signal a real pipeline defect.)
3. **Holdout fence:** the emitted data's max timestamp is provably before `AnalysisEndUtc`; the in-robot self-guard fails closed past it.
4. **Reproducibility:** re-running the backtest with the recorded config reproduces the datasets and the downstream verdict (behavioral).

A failure in any gate keeps INFR-001 open.

---

## 7. Sequencing & critical path

```
A1 (cAlgo strategy-host/adapter + Python ingestion harness)
        │
        ├─► A2 (C# library port) ──► A5 transcription tests ◄── Python references (fixtures)
        │
        └─► A3 (MA-crossover cAlgo + emission) + A4 (fence/reproducibility)
                        │
                        └─► A6 backtest run → ingest → frozen suite → reproduce EXP-004/009 → A7 docs
```

A1 (the adapter model + ingestion harness) and the Python references (for transcription fixtures only) are the keystones; every cTrader artifact is exercised through A6's behavioral check.

---

## 8. Relationship to Phase 004 / Task B

On INFR-001 completion the cTrader branch is the **realtime-parity generation/execution substrate**: strategies run as real cAlgos in-engine, holdout-fenced, reproducible, with the signal-gen library available in C#. Phase-004 candidate families are then authored as cAlgos, run in cTrader, and screened through the unchanged frozen suite via the Python ingestion harness.

**Deferred to Task B (Phase 004), explicitly out of INFR-001:**

- Registry-document standard + templates (README concern #1).
- Hypothesis-decomposition methodology (characterization-before-system) + noise-robustness guardrails (concerns #2/#3).
- **Multiplicity / file-drawer registry** — the mandatory programme-level Phase-004 precondition (P3-§11).
- AVWAP-specific "thick" primitives (D-engine), built on the A1 host + A2 C# library when AVWAP begins.
- Closure of the AVWAP doc's `[REQUIRES_DEFINITION]` tokens.

---

## 9. Non-goals (deferred)

- **AVWAP and any signal exploration** (D-seq) — hard-blocked until INFR-001 completes.
- **Execution-realism research** — intrabar fills, spread/slippage as a *qualification* input. The cTrader trade blotter is diagnostic only here (D-cost).
- **AVWAP-specific primitives** (D-engine) — Task B.
- **Multiplicity registry / registry standard / hypothesis-decomposition methodology** — Task B.
- **Tick data / data-architecture reopening** — out of scope; the 1-minute base stands.
- **Any modification to the frozen suite** — the three referees are carried in untouched.
- **Local C# reimplementation as the operating mode** — superseded (§0); the C# port runs in cTrader, validated locally only as a one-time transcription test.

---

## 10. Summary

INFR-001 builds the cTrader branch the operator placed ahead of signal exploration: a cAlgo **strategy-host / adapter model** that runs strategies as real cAlgo robots in cTrader's engine and emits the datasets Python validates, a full C# port of the existing signal-generation library (validated once by transcription test, then run in-engine), and a holdout-fenced, reproducible run mode — all proven end-to-end by running MA crossover through the cTrader backtester and confirming the frozen suite reproduces its already-known verdict (EXP-004/009). Generation/execution is in cTrader; validation stays in Python; only signal-gen code is ported. AVWAP and Phase 004 remain hard-blocked until this branch is complete.
