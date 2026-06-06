# INFR-001 — cTrader Branch & Strategy-Host Integration

**Checkpoint type:** **Infrastructure** — *not* an experiment phase. There is no falsifiable market hypothesis and no holdout measurement of a thesis. INFR-001 is governed as an **operator-reviewed design + build**, gated by **parity and integration validation** (VAL-class), not by per-hypothesis pre/post-execution governance verdicts. It does **not** flow through the 8-stage experiment pipeline.

**Date finalised:** 2026-06-06
**Status:** DESIGN — scope locked by operator decisions 2026-06-06 (D-seq, D-engine, D-port, D-vehicle, D-oracle below).
**Sequencing:** This is **Task A** and the **sole current focus**. **Phase 004, AVWAP, and all signal exploration are hard-blocked until INFR-001 completes.**

**Provenance.** Phase 003b (`2026-06-05-003b-incremental-unit-redesign`) concluded the framework-construction programme and unlocked Phase 004 behind its mandatory programme-level multiplicity-registry precondition (P3-§11). Before opening Phase 004, the operator directs a prior infrastructure task: build and integrate a **cTrader execution branch** into the research pipeline, proven end-to-end against the existing Python validation suite using **MA crossover** as a known-truth test vehicle. The frozen qualification suite — `{strict gate stack, EXP-012 ratified-loose referee, EXP-018 revised incremental/fitness unit}` — is carried in **untouched**; INFR-001 adds a generation/execution substrate in front of it and does not modify any referee.

---

## 1. Objective

Develop and integrate the **cTrader branch** of the research pipeline: a C# strategy host that runs registry strategies **bar-by-bar in realtime parity** (streaming, stateful, look-ahead-free) and emits the signal / position / event / trade datasets the Python validation framework consumes — validated **end-to-end** against the frozen qualification suite using MA crossover, whose suite verdict is already established (EXP-004 `matched_reject`; EXP-009 below every domain MDE).

Three pillars:

1. **Generic streaming signal-adapter framework** (not AVWAP-specific) on both the Python-reference and C# sides: a bar-event loop, a `SignalModel` contract, and a standard signal/position/event output schema.
2. **Full C# port of the existing validated generator/indicator library** — `linebreak`, `renko`, `heiken_ashi`, `bar_aggregator`, `market_bias` — each shipping with a **parity proof** against its Python reference oracle.
3. **End-to-end integration**: C# MA crossover → cTrader-emitted position series → frozen suite reproduces the EXP-004/009 verdict, with the holdout fence and determinism provably intact.

The deliverable is a reusable, parity-validated generation substrate. After INFR-001, a Phase-004 candidate signal can be produced either by the Python reference engine or by the parity-validated cTrader host, and screened through the unchanged suite.

---

## 2. Locked scope decisions (operator, 2026-06-06)

Frozen for the checkpoint. Changing any after build work begins requires a dated amendment recorded before the dependent work is validated.

| # | Decision | Resolution |
|---|---|---|
| **D-seq** | Sequencing | **Task A (cTrader branch) is the sole focus.** AVWAP / Phase 004 / all signal exploration is **hard-blocked** until INFR-001 completes. One task before the other. |
| **D-engine** | Signal-engine scope | **Generic adapter framework only.** Build the reusable streaming bar-loop + `SignalModel` contract + output/event/position schema, exercised **solely by MA crossover**. The AVWAP-specific "thick" primitives (pivot tracker, the four trend-regime detectors, cumulative VWAP accumulator with `w=TVᵅ`, MAD bands, anchor management) are **deferred to Task B**. |
| **D-port** | C# port width | **Full library port now.** Port `linebreak_generator`, `renko_generator`, `heiken_ashi_generator`, `bar_aggregator`, and the `market_bias` indicator to C#, **each with a VAL-class parity proof** against its Python reference. AVWAP primitives are excluded (they do not yet exist in Python — Task B). |
| **D-vehicle** | Test vehicle | **MA crossover (MA 20/50, the EXP-004/009 definition).** This is a **plumbing validation with a pre-known result**, **not** a candidate screen: it does **not** touch and must **not** be counted against the multiplicity / file-drawer registry (a Task-B artifact). |
| **D-oracle** | Source of truth | **Python remains the reference oracle.** C# is validated *against* it. No experiment consumes cTrader-sourced output that has not passed parity. This converts the dual-implementation into a *validated* dual-implementation rather than a second independent source of truth. |
| **D-resample** | Resampling location | **The C# host resamples 1-minute bars to the trading domain (5m/1h/4h) internally**, so a strategy runs on the same domain it would trade live — hence `bar_aggregator` is in the D-port list. Python re-derives the same domains only to check parity. (Operator-default, parity-driven; flagged in §10 for objection.) |

---

## 3. Governance fences (carried from programme invariants — non-negotiable)

These are inherited unchanged from the data-layer architecture and the OOS holdout rules, and are binding on every INFR-001 artifact.

1. **Holdout.** The C# host takes an explicit `AnalysisEndUtc` derived from the frozen first-70% cutoff and **refuses to emit any event at or after it**; the Python validation layer **also** re-applies the chronological split. The sealed final 30% is never generated over, loaded, or inspected. Belt-and-suspenders by design.
2. **Determinism / reproducibility.** cTrader runs operate over the **fixed collected Parquet bars** (not a live feed), with recorded configuration, and reproduce. The Python reference is byte-deterministic. Parity is checked at byte/tolerance level (§6).
3. **Single source of truth (D-oracle).** Python is the reference oracle; C# is validated against it; the parity gate precedes any admission of cTrader output to an experiment.
4. **Real-price outcome discipline & MDE comparability.** The suite consumes the **position series evaluated on next-step real-price returns with the flat scoped cost** — the basis on which the frozen 1/4/12, 0.5/2/8, and 12/16/32 MDE maps were calibrated. Any richer cTrader fill/spread/slippage blotter is **diagnostic only** and is **not** admitted into qualification until an explicit execution-realism scope says so (a later, separate question). Heiken Ashi and Renko construction prices are never used for P&L.
5. **Streaming / causal semantics.** The host runs strategies bar-by-bar, look-ahead-free, mirroring live execution. Timestamp alignment (`CloseTime` / `SourceCloseTime`) over bar count, always.

---

## 4. Deliverables & work streams

| # | Stream | Side | Output |
|---|---|---|---|
| **A1** | **Adapter framework** — streaming bar-event loop, `SignalModel` contract (`on_bar(bar) → state/emit`), standard signal/position/event/trade output schema, real-time alignment, determinism + look-ahead-free guarantees | Python (reference) + C# (host/interface mirror) | `python/src/xen/signals/` package; C# strategy-host scaffolding in the cAlgo project |
| **A2** | **C# library port (full)** — `linebreak`, `renko`, `heiken_ashi`, `bar_aggregator`, `market_bias` ported to C#, mirroring the validated Python algorithms | C# | C# generator/indicator modules under the cAlgo project |
| **A3** | **C# MA-crossover strategy + dataset emission** — MA(20/50) as the first adapter client; emits signal/position/event/trade Parquet via the existing ZSTD writer pattern | C# | C# strategy module + Parquet datasets |
| **A4** | **Holdout fence + determinism** — `AnalysisEndUtc` enforcement; fixed-bar reproducible run mode; recorded run config/metadata | C# | Fence + run-metadata emission |
| **A5** | **Parity validations (VAL-class)** — per-port parity proofs (A2: five modules) + MA-crossover parity (A3) vs the Python reference oracle | Python | VAL-class validation artifacts (candidate VAL-002+) |
| **A6** | **End-to-end integration test** — cTrader-sourced MA positions → frozen suite → must reproduce EXP-004/009 (REJECT, below every domain MDE) | Python | Integration validation artifact |
| **A7** | **Reference/architecture/config updates** — `architecture.md`, `dataset-reference.md`, pipeline config, skills: dual-substrate reality, adapter contract, new dataset schemas, the parity gate, the C# port library | docs | Updated reference docs |

### 4.1 C# library port targets (A2) and their reference oracles

| Module | Python reference | Parity basis |
|---|---|---|
| Line Break | `xen.linebreak_generator` (`level`, default 3) | identical confirmed-line sequence + schema on identical 1-min bars |
| Renko (ATR) | `xen.renko_generator` (`atr_period`, default 14) | identical brick sequence; ATR computed causally; identical `SourceCloseTime` |
| Heiken Ashi | `xen.heiken_ashi_generator` | identical HA + Real OHLC columns |
| Bar aggregator | `xen.bar_aggregator` (N-min clock-aligned OHLC; `min_coverage`) | identical 5m/1h/4h OHLC + coverage/dropped-window behaviour |
| Market Bias | `xen.indicators.market_bias` (CEREBR port; EMA/HA recursion; warmup) | identical state labels beyond the deterministic warmup floor |

Each port's parity proof is a self-contained VAL-class check: identical inputs in, byte/tolerance-identical outputs out, with negative controls where applicable (cf. VAL-001's 23/23 negative-control detections).

---

## 5. New dataset schema (strategy-host output)

The C# host emits a per-run dataset family under a path pattern to be fixed in A1 (candidate `data/strategy_runs/<strategy>_<symbol>_<domain>_<...>.parquet`), carrying at minimum:

- **Signal/position series:** `SourceCloseTime` (real-time anchor), `Domain`, `Position ∈ {−1,0,+1}`, raw signal value(s), warmup/flat flags.
- **Event log:** discrete strategy events (e.g. crossover events) with real-time timestamps.
- **Trade blotter (diagnostic):** entries/exits/fills/notional — **diagnostic only** under fence #4, not a qualification input in INFR-001.
- **Run metadata:** strategy + parameters, `AnalysisEndUtc`, domain/coverage config, generator versions, seed/determinism markers, source-file provenance.

The **position series on real-price returns** is the only object routed into the frozen suite. Schemas are recorded in `dataset-reference.md` (A7).

---

## 6. Validation gates (acceptance criteria)

INFR-001 is **COMPLETE** only when all of the following pass:

1. **Per-port parity (A2/A5):** each of the five C# ports reproduces its Python reference output to a predeclared tolerance (byte-identical for integer/categorical fields; tight numeric tolerance for floats, with the tolerance and rationale recorded). The known parity traps are checked explicitly: warmup/NaN handling (positions flat, not dropped — per EXP-009), `market_bias` EMA-seed warmup floor, Renko ATR causality, aggregator coverage/dropped-window rules.
2. **MA-crossover parity (A3/A5):** C# MA(20/50) positions equal the Python reference positions bar-for-bar on each domain.
3. **End-to-end integration (A6):** the frozen suite, fed the **cTrader-sourced** positions, reproduces the EXP-004/009 result — REJECT with measured effect below every domain MDE — within reproduction tolerance. Any deviation is a pipeline defect (the strategy's answer is already known).
4. **Holdout fence:** emitted data is provably bounded before `AnalysisEndUtc`; an attempt to emit past it fails closed. Verified by checking max emitted timestamp against the cutoff.
5. **Determinism:** a re-run reproduces the datasets and the downstream verdict.

A failure in any gate keeps INFR-001 open; it is not "completed partially."

---

## 7. Sequencing & critical path

Strictly chained, Python-reference-first within each port (the oracle must exist before the C# port can be validated against it):

```
A1 (adapter framework: Python reference contract + C# host scaffold)
        │
        ├─► A2 (C# library port) ──► A5 per-port parity ◄── Python reference oracles
        │
        └─► A3 (C# MA crossover + emission) + A4 (fence/determinism)
                        │
                        └─► A5 MA parity ──► A6 end-to-end integration ──► A7 docs
```

The Python adapter contract and the Python reference oracles are the keystone: every C# artifact earns admission only by passing parity against them.

---

## 8. Relationship to Phase 004 / Task B

On INFR-001 completion the cTrader branch is the **realtime-parity generation substrate**, parity-validated against the Python reference, holdout-fenced, and deterministic. Phase-004 candidate families can then be generated via cTrader (admitted by parity) or via the Python reference, and screened through the unchanged frozen suite.

**Deferred to Task B (Phase 004), explicitly out of INFR-001:**

- Registry-document standard + templates (signal-registry README concern #1).
- Hypothesis-decomposition methodology — characterization-before-system — and the noise-robustness guardrails for empirical component development (concerns #2/#3).
- **Multiplicity / file-drawer registry** — the mandatory programme-level Phase-004 precondition (P3-§11).
- AVWAP-specific "thick" primitives (D-engine), now buildable on top of the A1 framework and the A2-ported C# library when AVWAP work begins.
- Closure of the AVWAP doc's `[REQUIRES_DEFINITION]` tokens.

---

## 9. Non-goals (deferred)

- **AVWAP and any signal exploration** (D-seq) — hard-blocked until INFR-001 completes.
- **Execution-realism research** — intrabar fills, spread/slippage as a *qualification* input. The trade blotter is diagnostic only here.
- **AVWAP-specific primitives** (D-engine) — Task B.
- **Multiplicity registry / registry standard / hypothesis-decomposition methodology** — Task B.
- **Tick data / data-architecture reopening** — out of scope; the 1-minute base stands.
- **Any modification to the frozen suite** — the three referees are carried in untouched.

---

## 10. Flagged implementation detail (operator may override)

**D-resample** sets the C# host to resample to the trading domain internally so strategies run live-faithfully on 5m/1h/4h (matching EXP-004/009), which is why `bar_aggregator` is a port target. The alternative — emit only 1-minute signals and resample in Python — is lighter C# work but breaks realtime parity for domain-based strategies and is therefore not recommended. Recorded here for objection before A1 begins.

---

## 11. Summary

INFR-001 builds the cTrader branch the operator placed ahead of signal exploration: a generic streaming signal-adapter framework, a full parity-validated C# port of the existing generator/indicator library, and a holdout-fenced, deterministic strategy host — all proven end-to-end by running MA crossover through the new substrate and confirming the frozen suite reproduces its already-known verdict (EXP-004/009). Python stays the reference oracle; C# earns admission by parity. AVWAP and Phase 004 remain hard-blocked until this branch is complete. On completion, the research pipeline has a realtime-parity generation substrate, and signal exploration (Task B) can begin against the unchanged qualification suite.
