# Phase 1 Design: Chart-Type Validation

**Phase:** 001 — Chart-Type Validation
**Date:** 2026-05-14
**Status:** Active

**Decision status:** Base architecture confirmed: 1-minute time bars only, deterministic generators by default, optional persisted canonical generated variants.

---

## Phase Objectives

Phase 1 establishes the empirical baseline for the Xen research programme. Before any strategy theories can be tested, we must understand what each chart type (Line Break, Renko, Heiken Ashi) actually does to price data compared to traditional time bars. This phase is purely characterisation: no strategy backtesting, no parameter optimisation, and no P&L evaluation.

The goal is to answer: **what are the measurable, trading-relevant differences between time bars, Line Break bars, Renko bricks, and Heiken Ashi candles?**

---

## Prerequisites

Before any experiments begin, the following must be operational:

### cAlgo Data Collection Robot

The Xen cAlgo robot must be updated from its current skeleton to a working 1-minute bar collector:

1. **1-minute bar capture:** Read completed 1-minute OHLC bars from cTrader/cAlgo
2. **Bar validation:** Enforce chronological ordering and OHLC integrity
3. **Parquet output:** Write time bars to `data/timebars/`
4. **Session management:** Proper file finalization on `OnStop()`

**Key design decisions for cAlgo:**
- Store 1-minute bars only. Do not store or process raw ticks.
- Use 1-minute as the base timeframe for baseline comparisons, ATR calculation, and chart-type generation.
- Do not include adaptive epsilon filtering; it was only relevant to tick-level processing.
- No chart-type generation in cAlgo. Python handles all transformations.
- Persist generated chart-type variants only after they become canonical high-use datasets.

### Python Chart-Type Generators

Before Phase 1 experiments, the following generators must be implemented and validated:

1. **`python/src/linebreak_generator.py`** — Line Break bar generator
   - Input: completed 1-minute time bars
   - Parameter: `level` (default: 3)
   - Output: Line Break bar DataFrame (see dataset-reference.md schema)
   - Must be deterministic and streaming-compatible

2. **`python/src/renko_generator.py`** — Renko brick generator
   - Input: completed 1-minute time bars
   - Parameter: `atr_period` (default: 14)
   - Output: Renko brick DataFrame (see dataset-reference.md schema)
   - ATR must be computed from bars available at that point in time (no look-ahead)
   - Output is close-based Renko from 1-minute bars; tick-derived Renko is out of scope
   - Must be deterministic and streaming-compatible

3. **`python/src/heiken_ashi_generator.py`** — Heiken Ashi candle generator
   - Input: 1-minute time bars
   - Parameter: None
   - Output: Heiken Ashi candle DataFrame (see dataset-reference.md schema)
   - Must carry `RealOpen/High/Low/Close` alongside HA prices
   - Must be deterministic and streaming-compatible

Each generator must include:
- Unit tests verifying deterministic output
- Unit tests verifying streaming compatibility (sequential processing produces same output as batch)
- Unit tests verifying look-ahead bias prevention (no future data used)

---

## Planned Experiments

### EXP-001: Information Density & Ghost Bar Comparison

**Hypothesis:** Line Break, Renko, and Heiken Ashi produce fewer economically empty ("ghost") bars and more information-dense bars than time bars over matched chronological windows.

**Question:** Which chart types waste fewer bars on noise, and how does bar density compare across types?

**Key metrics:** Ghost rate, information content per bar and per unit time, coefficient of variation of bar-level statistics across regimes.

**Instruments:** EURUSD, XAUUSD, BTCUSD, USTEC
**Chart types:** Time (1-minute baseline), Line Break (level 3, 5), Renko (ATR 14), Heiken Ashi
**Timeframes:** 1-minute (time bars); source timeframe for others

---

### EXP-002: Volatility & Trend Regime Representation

**Hypothesis:** Event-based chart types (Line Break, Renko) represent volatility regimes and trend transitions more cleanly than time bars, with fewer hybrid bars at regime boundaries.

**Question:** Do Line Break and Renko bars align more precisely with volatility regime transitions?

**Key metrics:** Regime purity (fraction of bars fully within a single regime), detection lag (bars to reflect a new regime), hybrid rate (bars spanning regime boundaries).

**Instruments:** EURUSD, XAUUSD, BTCUSD, USTEC
**Chart types:** Time, Line Break, Renko, Heiken Ashi

---

### EXP-003: Noise Filtering & Statistical Robustness

**Hypothesis:** Under synthetic noise injection, Line Break and Renko maintain more stable statistical properties (autocorrelation, variance ratios) than time bars, while Heiken Ashi smooths noise at the cost of synthetic price distortion.

**Question:** How does each chart type respond to added noise, and which properties are robust vs fragile?

**Key metrics:** Bar-to-bar return autocorrelation, variance ratio, Lempel-Ziv complexity, structural stability under noise.

**Instruments:** EURUSD, XAUUSD, BTCUSD, USTEC
**Noise levels:** 0%, 10%, 20%, 30% source-bar close perturbation or direction flips, defined in the experiment scope

---

### EXP-004: Market Structure Capture Speed & Fidelity

**Hypothesis:** Line Break and Renko detect trend reversals earlier than time bars (lower detection latency) but may produce more false signals (lower precision).

**Question:** What is the speed-precision trade-off for each chart type?

**Key metrics:** Detection latency (time from actual trend change to chart-type signal), precision (fraction of chart-type signals that correspond to real trend changes), split rate (fraction of real events that produce multiple chart-type signals).

**Instruments:** EURUSD, XAUUSD, BTCUSD, USTEC

---

### EXP-005: Cross-Chart-Type Alignment & Regime Correspondence

**Hypothesis:** Chart types with higher information density and cleaner regime boundaries will show stronger agreement on trend direction (cross-validation), while time bars will show higher noise-driven disagreement.

**Question:** Do chart types agree on when trends change direction, and which types are most reliable?

**Key metrics:** Alignment rate (fraction of direction signals that agree across chart types), temporal alignment tolerance, direction agreement across low/medium/high volatility regimes.

**Instruments:** EURUSD, XAUUSD, BTCUSD, USTEC

---

### EXP-006: Heiken Ashi Synthetic Price Distortion Quantification

**Hypothesis:** Heiken Ashi synthetic prices systematically distort return magnitudes (compressing volatility and smoothing trends), making HA-derived returns unreliable for strategy evaluation.

**Question:** How much does Heiken Ashi distort returns compared to real prices, and is this distortion regime-dependent?

**Key metrics:** Return compression ratio (HA returns vs real returns), volatility compression factor, trend smoothing distortion, synthetic-to-real price ratio by regime.

**Instruments:** EURUSD, XAUUSD, BTCUSD, USTEC

---

## Phase Scope Boundaries

**In scope:**
- Statistical characterisation of chart types vs time bars
- Regime labeling using realised volatility terciles
- Cross-chart-type comparison on the same time period
- Noise injection experiments
- Timeframe as a hyperparameter (experiments may be repeated on different timeframes)

**Out of scope (for Phase 1):**
- Strategy backtesting
- Return/P&L calculations on chart-type signals
- Parameter optimisation (best level for Line Break, best ATR period for Renko)
- Predictive models or machine learning
- Live trading integration
- Any analysis that uses out-of-sample strategy returns
- Any strategy P&L computed from synthetic chart prices

**Global holdout:** The final 30% of the dataset (by time) is excluded from all analysis. Only the first 70% is used.

---

## Success Criteria for Phase 1

Phase 1 is successful if it produces:

1. **Validated generators** — All three chart-type generators pass unit tests for determinism, streaming compatibility, and look-ahead bias prevention.
2. **Characterisation results** — For each experiment, a clear SUPPORTED / REFUTED / INCONCLUSIVE verdict with quantitative evidence.
3. **Instrument differentiation** — Identification of which instruments each chart type performs better/worse on.
4. **Trade-off mapping** — Clear documentation of what each chart type gains and loses vs time bars (e.g., "Line Break gains X detection speed but loses Y precision").
5. **Phase 2 direction** — Enough evidence to guide strategy theory exploration in Phase 2.

---

## Estimated Timeline

| Week | Task | Deliverable |
|------|------|-------------|
| **1** | cAlgo 1-minute bar collector implementation + Parquet output | Working data collector, stored time-bar Parquet files |
| **2** | Python chart-type generator implementation + unit tests | Tested Line Break, Renko, Heiken Ashi generators |
| **3** | EXP-001 (Information Density) + EXP-006 (HA Distortion) | Two completed experiments |
| **4** | EXP-002 (Regime Representation) + EXP-003 (Noise Robustness) | Two completed experiments |
| **5** | EXP-004 (Structure Capture) + EXP-005 (Cross-Type Alignment) | Two completed experiments |
| **6** | Phase 1 retrospective + Phase 2 design | Retrospective document, Phase 2 checkpoint |
