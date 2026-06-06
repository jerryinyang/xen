# Xen Data-Layer Architecture

## Purpose

The Xen data layer is **thesis-agnostic core infrastructure** for intraday-trading
research. It provides a deterministic, auditable foundation that any experiment can
build on, independent of the particular thesis under test:

1. **Data collection (cAlgo):** completed 1-minute OHLC time bars are collected from
   cTrader and stored as the base dataset.
2. **Chart-type generation (Python, on demand):** deterministic generators transform
   the 1-minute base into derived views — Line Break, Renko, Heiken Ashi — for
   experiments that need them. Traditional time bars (1-minute and clock-aligned
   resamples) are the default view.
3. **Strategy-host generation (cTrader branch):** strategies run as **real cAlgo
   robots inside cTrader's engine**, resample internally to the trading domain, and
   emit signal/position/event/trade datasets carrying the real OHLC the strategy
   executed on. Python ingests and validates only — it never generates strategy
   signals. The ported C# generators are validated **once by transcription** against
   their Python reference, then run in-engine; a run is admitted to experiments by
   **behavioral reproduction** through the frozen suite, not byte-parity.

This document specifies that data layer only. It does **not** prescribe what to study
with it: feature extraction, comparison, signal construction, and strategy validation
are thesis-specific and live under `python/experiments/`.

> This architecture originated in a prior chart-type research thesis. That thesis is
> closed; the data layer it produced is retained as neutral infrastructure for any
> intraday-trading research.

**Guiding principles:**

- **Deterministic generation**: All chart-type transformations must produce identical output from identical input, whether run in batch or streaming mode. No random seeds, no path-dependent state leaks.
- **Streaming compatibility**: Every generator must be implementable as a stateful streaming function that can process 1-minute bars sequentially. This ensures live deployability and prevents look-ahead bias.
- **Synthetic price discipline**: Heiken Ashi prices and Renko brick prices are not directly tradable prices. Any signal generated on a synthetic or transformed chart type must have returns evaluated on time-matched traditional bar prices.
- **Separation of collection, generation, and analysis**: The cAlgo robot collects raw data and, in strategy-host mode, runs strategies in cTrader's engine and emits their datasets. Python is the validation/analysis layer; it ingests emitted runs and never generates strategy signals. Only signal-generation code (chart types, indicators) is ported to C# so cAlgos compute signals natively in-engine; those ports are transcription-validated once against the Python reference.

## Confirmed Architecture Decisions

These decisions are binding for the Xen data layer:

| Decision | Resolution | Rationale |
| --- | --- | --- |
| Base data architecture | Store 1-minute time bars only. Do not store raw ticks. | Tick data is too granular for the intended memory and performance budget. |
| Chart-type generation | Use deterministic Python generator scripts by default. | Generator scripts give maximum flexibility for testing different chart parameters and variants. |
| Generated-data persistence | Persist only frequently reused canonical variants under `data/<chart_type>/` after they prove useful. | Avoids unnecessary storage while allowing practical acceleration for stable variants. |
| Renko source mode | Generate Renko from 1-minute time bars, not ticks. | Accepts the fidelity trade-off to avoid raw tick storage and processing overhead. |
| Adaptive epsilon filtering | Excluded. | Epsilon filtering was relevant only to tick-level processing, which Xen does not do. |
| cAlgo output authority | cAlgo writes base 1-minute bars and, in strategy-host mode, runs strategies in cTrader's engine and emits their datasets; Python ingests and validates. Ported C# generators are transcription-validated once against the Python reference, then run in-engine. | Realtime-parity generation in cTrader with validation kept in Python. |
| Default instrument set | EURUSD, XAUUSD, BTCUSD, USTEC. | A liquid, diverse default; experiments may narrow to subsets. |
| Strategy-host holdout fence | C# strategy output requires explicit `AnalysisEndUtc` and emits no row with `SourceCloseTime >= AnalysisEndUtc`; Python validation reapplies the chronological split. | Prevents accidental final-holdout generation or qualification leakage. |

## Generated Data Persistence Policy

Default to deterministic generation from 1-minute bars. Persist a generated chart-type dataset only when all of the following are true:

1. The variant is repeatedly used across experiments or governance checks.
2. The generator version and parameters are recorded with the persisted file.
3. The persisted dataset can be invalidated when generator logic changes.
4. The storage cost is lower than the repeated regeneration cost.

Recommended persisted directory pattern:

```text
data/
├── timebars/
├── linebreak/
├── renko/
└── heiken_ashi/
```

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: DATA COLLECTION (cAlgo)                                          │
│  • Read completed 1-minute bars from cTrader/cAlgo                         │
│  • Store 1-minute OHLC bars as the base dataset                            │
│  • Do not store or process raw ticks                                       │
│  • Finalize one Parquet file per symbol/session                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  STAGE 2: CHART-TYPE GENERATION (Python, on-demand)                        │
│  • Line Break generator (configurable level parameter)                     │
│  • Renko generator from 1-minute source bars                               │
│  • Heiken Ashi generator (no parameters)                                    │
│  • Each generator output includes: chart-type bars + mapping to real        │
│    price/time coordinates for return evaluation                             │
│  • All generators must be deterministic and streaming-compatible           │
├─────────────────────────────────────────────────────────────────────────────┤
│  STAGE 3: STRATEGY-HOST GENERATION (cTrader engine; Python validates)      │
│  • Strategies run as real cAlgo robots in cTrader's engine                  │
│  • Resample 1-minute bars internally to the trading domain                  │
│  • Emit positions (with real OHLC), events, diagnostic trades, metadata     │
│  • Enforce AnalysisEndUtc before output emission                            │
│  • Admit runs to experiments by behavioral suite reproduction               │
└─────────────────────────────────────────────────────────────────────────────┘
```

Everything downstream of these generation stages — feature extraction, cross-view
comparison, signal construction, and strategy validation — is **thesis-specific**.
Those steps are defined per experiment under `python/experiments/`, not by this
data layer.

---

## Detailed Pipeline Specification

### Stage 1: Data Collection (cAlgo)

**Input:** Completed 1-minute OHLC bars from cTrader/cAlgo.

**Operations:**

1. **Bar capture:** Collect completed 1-minute bars after close.
2. **Timestamp integrity:** Enforce strictly increasing `CloseTime`. Mark session gaps.
3. **OHLC integrity:** Validate `High >= max(Open, Close)` and `Low <= min(Open, Close)`.
4. **Session finalization:** Write finalized Parquet files on `OnStop()` or session rollover.

**Output:** One base Parquet file per symbol/session:
- 1-minute time bars: `data/timebars/timebars_<instrument>_<serverTime>_<localTime>.parquet`

**cAlgo parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `TimeBarInterval` | 1 | Bar interval in minutes for base time bars |

No tick-level cleansing or adaptive epsilon filter is part of the Xen data collector.

**Strategy-host modes:** the same cAlgo assembly exposes a `Mode` parameter. The
default `TimeBars` mode preserves the 1-minute collector. `StrategyHost` mode runs
a strategy in cTrader's engine bar-by-bar, resamples internally to the configured
domain, enforces an explicit `AnalysisEndUtc`, and writes a strategy-run dataset
(positions with real OHLC, events, diagnostic trade blotter, run metadata) under
`data/strategy_runs/`. Setting `Source Parquet Path` replays the same strategy over
a fixed time-bar file as a deterministic developer smoke path. `StrategyHostParity`
mode writes the generator/indicator/MA CSV family used as a developer **transcription
smoke**; the binding validation is **behavioral suite reproduction** (VAL-002), not
byte-parity.

---

### Stage 2: Chart-Type Generation (Python, On-Demand)

Generators operate on completed 1-minute time bars. This is an intentional performance and storage trade-off: intrabar events that would be visible from ticks are out of scope unless a later experiment explicitly reopens the data architecture. Each generator is a pure function with internal state that produces chart-type bars deterministically.

#### Line Break Bars

**Reference:** [TradingView: Line Break Charts](https://www.tradingview.com/support/solutions/43000502273-introduction-to-line-break-charts/)

**Parameter:** `level` (default: 3). The number of previous lines whose high/low must be broken for a reversal.

**Algorithm:**
1. Use the first source close to initialise the first confirmed line.
2. For each subsequent 1-minute source close:
   - if the close extends the current direction, draw a new line in the same direction;
   - if the close breaks below the low of the previous `level` confirmed lines, draw a new down-line;
   - if the close breaks above the high of the previous `level` confirmed lines, draw a new up-line;
   - otherwise, draw no new line.
3. Do not emit projected or unconfirmed lines in historical research data.

**Output schema (per bar):**

| Column | Type | Description |
|--------|------|-------------|
| `OpenTime` | datetime | Source timestamp that opened the line |
| `CloseTime` | datetime | Source timestamp that confirmed the line |
| `Open` | float | Opening price of the line |
| `High` | float | Highest price during the line |
| `Low` | float | Lowest price during the line |
| `Close` | float | Closing price of the line |
| `Direction` | int | +1 (up-line) or -1 (down-line) |
| `Level` | int | The level parameter used |
| `SourceCount` | int | Number of source 1-minute bars consumed since the prior confirmed line |
| `SourceCloseTime` | datetime | Time-matched real bar close timestamp for return evaluation |

**Streaming compatibility:** Line Break generation is naturally stateful — it maintains the last `level` lines. The generator can process bars sequentially without look-ahead.

**Look-ahead bias prevention:** Using only completed source closes ensures the generator sees exactly what a live system would know at each point in time.

---

#### Renko Bars (ATR-Based)

**Reference:** [TradingView: Understanding Renko Charts](https://www.tradingview.com/support/solutions/43000502284-understanding-renko-charts/)

**Parameter:** `atr_period` (default: 14). ATR period for adaptive brick sizing.

**Algorithm:**
1. Compute ATR over the specified period from completed 1-minute bars available at that timestamp.
2. Brick size = the latest available ATR value, rounded only if the experiment scope defines an instrument price-step rule.
3. Process 1-minute source closes sequentially. A new up-brick forms when price rises by at least one brick size above the current Renko close.
4. A new down-brick forms when price falls by at least one brick size below the current Renko close.
5. If a single 1-minute source close crosses multiple brick thresholds, emit all fully crossed bricks in order, each with the same source timestamp.

**ATR computation detail:**
- ATR is computed from completed time bars using a rolling window.
- The ATR value is recalculated at each bar close.
- The brick size used for a source update must be the value known before or at that source timestamp.
- **Streaming note:** ATR at bar N uses only bars up to and including N. No look-ahead.

**Output schema (per bar):**

| Column | Type | Description |
|--------|------|-------------|
| `OpenTime` | datetime | Source timestamp that opened the brick sequence |
| `CloseTime` | datetime | Source timestamp that confirmed the brick |
| `Open` | float | Opening price of the brick |
| `High` | float | Highest price during the brick |
| `Low` | float | Lowest price during the brick |
| `Close` | float | Closing price of the brick |
| `Direction` | int | +1 (up-brick) or -1 (down-brick) |
| `BrickSize` | float | ATR-derived brick size at time of creation |
| `ATRPeriod` | int | ATR period used |
| `SourceCount` | int | Number of source 1-minute bars consumed since the prior confirmed brick |
| `SourceCloseTime` | datetime | Time-matched real bar close timestamp |

**Streaming compatibility:** Renko generation maintains only the current brick state and rolling ATR. Fully deterministic from sequential bar input.

**Synthetic price warning:** Renko brick open/close levels are chart-construction levels, not guaranteed executable market prices. Strategy returns must be evaluated on real time-matched prices.

**Look-ahead bias prevention:** ATR at each step uses only completed historical bars. Brick thresholds are set before or at the source timestamp that creates the brick.

---

#### Heiken Ashi Candles

**Parameters:** None (no configurable parameters).

**Algorithm:**
1. HA-Close = (Open + High + Low + Close) / 4
2. HA-Open = (previous HA-Open + previous HA-Close) / 2
3. HA-High = max(High, HA-Open, HA-Close)
4. HA-Low = min(Low, HA-Open, HA-Close)

**Critical constraint:** Heiken Ashi prices are **synthetic prices**; they do not correspond to real traded prices. Strategy returns MUST be evaluated on time-matched traditional bar prices.

**Output schema (per bar):**

| Column | Type | Description |
|--------|------|-------------|
| `OpenTime` | datetime | Real bar open timestamp |
| `CloseTime` | datetime | Real bar close timestamp |
| `HAOpen` | float | Heiken Ashi open |
| `HAHigh` | float | Heiken Ashi high |
| `HALow` | float | Heiken Ashi low |
| `HAClose` | float | Heiken Ashi close |
| `RealOpen` | float | Actual (real) bar open |
| `RealHigh` | float | Actual bar high |
| `RealLow` | float | Actual bar low |
| `RealClose` | float | Actual bar close |
| `Direction` | int | +1 if HA-Close >= HA-Open, else -1 |
| `SourceCount` | int | Number of source bars in this HA candle, normally 1 |

**Streaming compatibility:** Heiken Ashi is a simple rolling transformation. Only the previous HA-Open and HA-Close are needed as state. Fully deterministic and streaming-compatible.

**Look-ahead bias prevention:** HA calculations use only data available at bar close time. The `RealOpen/High/Low/Close` columns carry the actual prices for return evaluation.

---

## Synthetic-Price Discipline

This is a data-layer constraint, not a thesis choice: any signal derived from a
synthetic or transformed chart type must have its returns evaluated on
**time-matched traditional bar prices**.

- Heiken Ashi signals → evaluate returns on `RealClose` at the corresponding timestamp.
- Line Break signals → evaluate returns on `SourceCloseTime`-aligned real prices.
- Renko signals → evaluate returns on `SourceCloseTime`-aligned real prices.

This keeps any positive finding economically meaningful rather than an artifact of synthetic chart prices.

---

## Parameter Governance Table

All free parameters are classified and owned:

| Parameter | Type | Derivation Method | Update Frequency |
|-----------|------|-------------------|------------------|
| `TimeBarInterval` | Governance | Research decision; default 1 minute | Per experiment |
| LineBreak `level` | Governance | Research decision; default 3 | Per experiment |
| Renko `atr_period` | Governance | Research decision; default 14 | Per experiment |

Generator parameters are research decisions fixed per experiment scope; they are never tuned against out-of-sample strategy returns. Parameter-sensitivity studies are explicit research questions, not optimisation targets.

---

## Critical Constraints

| Constraint | Description |
|-----------|-------------|
| **No look-ahead in generation** | All chart-type generators process data sequentially. No future data is used in any bar computation. |
| **Deterministic output** | Given the same input data and parameters, generators produce identical output. No random seeds. |
| **Synthetic price discipline** | Heiken Ashi and Renko chart prices are never used for strategy P&L. All returns use time-matched real prices. |
| **Streaming compatibility** | Every generator must be implementable as a stateful streaming function. |
| **Time-matched returns** | Cross-view comparisons use the same chronological time periods. Charts are aligned by timestamps, not by bar count. |
| **Separation of collection and analysis** | cAlgo collects raw data only. All chart-type generation and analysis happens in Python. |

---

## What This Data Layer Is Not

- **Not a trading system:** the cAlgo robot is a data collector, not a strategy executor.
- **Not a parameter optimizer:** generator parameters are research decisions or derived from data, never tuned against out-of-sample returns.
- **Not tied to any single thesis:** no chart type is assumed superior. Which views matter, and what to measure, is decided per experiment — not by this layer.
