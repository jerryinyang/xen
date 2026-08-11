# Orderflow Feature Store & Backtesting Architecture
## L2 MBP Data Reduction Pipeline for Crypto (Bybit) with NautilusTrader Integration

**Version:** 1.0
**Status:** RATIFIED (INFR-010 §6 Phase E, published at INFR-013 2026-07-16; source `.ignore/temp/orderflow_feature_store_architecture.md`)
**Implementation:** contracts + skeleton in `python/src/xen/orderflow/` (INFR-013); bulk collection + detectors DEFERRED to a separate operator-gated INFR

---

## 1. Problem Statement

### 1.1 Objective

Explore, research, and backtest orderflow and liquidity trading concepts on crypto assets (Bybit perpetuals, e.g., BTCUSDT, ETHUSDT), specifically the concept families documented in the reference guides:

1. **Orderflow fundamentals** — footprint, delta, absorption, initiative auction, exhaustion, book sweeping, volume profile (POC, value area, LVNs), auction market theory.
2. **Liquidity heat map** — resting vs. fresh liquidity, reloads, icebergs, spoofing/pulls, book slope / path of least resistance, break-and-protect, liquidity cluster walls.
3. **Models & application** — IVB (initial balance breakout) with statistical excursion targets, Deep-Effort-style effort/result triggers, CVD/price divergence, big-trade filtering, real (volume-based) fair value gaps.

The research output must feed **NautilusTrader** for backtesting and, when strategies mature, transition to live trading against the Bybit feed.

### 1.2 Constraint

Raw L2 market-by-price (MBP) data at full granularity has storage requirements that exceed the available budget. For a liquid Bybit perpetual, raw depth deltas plus trades can run to several GB per day uncompressed, per instrument. Retaining months of history across several assets is infeasible.

### 1.3 Proposed Solution

Operate a **reduce-at-ingest pipeline**:

1. Download / stream raw L2 MBP + trades data.
2. Compute and persist a designed set of features, event detections, and reduced-granularity streams sufficient for the closed set of concepts above **and** for honest trade evaluation in NautilusTrader.
3. Discard the bulk raw data (full depth), retaining only the extracted store plus small raw streams designated as keep-forever.

### 1.4 The Two Questions

- **Q1 — Is this feasible losslessly?**
- **Q2 — If so, what features must be computed?**

Answered in §2 and §4 respectively. A third question emerged during design and is answered in §6:

- **Q3 — Is the retained data sufficient for NautilusTrader to evaluate trades (fills) honestly, and do we store tick bid/ask?**

---

## 2. Feasibility Analysis

### 2.1 Verdict

**Not lossless in the information-theoretic sense; lossless with respect to the closed concept set** defined in §1.1 — provided the feature set is designed and validated *before* raw data is discarded.

Aggregation is irreversible. Any feature not anticipated at ingest time is unrecoverable from the reduced store. The reference documents define a bounded set of questions, which is precisely what makes reduction viable: the loss can be scoped, measured, and accepted deliberately.

### 2.2 Three governing observations

**(a) Trades are small; keep them raw.**
The tick trades stream (timestamp, price, size, aggressor side — Bybit provides aggressor side natively) is typically 1–2 orders of magnitude smaller than L2 depth. Nearly every orderflow concept (footprint, delta, CVD, big-trade filters, sweeps) derives from trades alone. Retaining raw trades preserves the majority of future analytical optionality at low cost. **Designated keep-forever.**

**(b) The book is where storage pain lives — and where irreversible computation must happen.**
Iceberg detection, spoof/pull detection, and reload detection require reconciling executions against *displayed size in real time*. These cannot be recomputed from downsampled snapshots. They must be computed online at ingest and persisted as **event streams** before depth data is discarded.

**(c) Bybit MBP is already lossy relative to true market microstructure.**
The feed is level-aggregated (MBP), not order-by-order (MBO). Individual orders and true queue position are never observable. Some feared "loss" therefore never existed in the source — queue models were always going to be estimates, even from full raw data.

### 2.3 Risk-mitigation policies

| Policy | Rationale |
|---|---|
| **Rolling raw buffer** (7–14 days of full L2 retained at all times) | Detector bugs and threshold tuning are inevitable. Re-run against recent raw, validate, then trust the historical feature store. Deleting raw behind an untested pipeline is the classic failure mode. |
| **Feature-definition versioning** | Extraction code is schema. Any threshold change (imbalance ratio, size buckets, snapshot rate) creates a dataset discontinuity that must be traceable. Every record carries a `pipeline_version`. |
| **Single implementation, two runtimes** | The same streaming feature code runs (i) in batch over historical raw at ingest and (ii) live as a NautilusTrader Actor. Guarantees backtest/live parity (§7). |

---

## 3. System Architecture Overview

```
                    ┌─────────────────────────────────────────────┐
                    │                 INGEST                       │
   Bybit REST /     │  ┌──────────┐   ┌────────────────────────┐  │
   WebSocket  ───►  │  │ Raw L2 + │──►│  Streaming Feature      │  │
   (raw MBP +       │  │ Trades   │   │  Engine (shared code)   │  │
    trades)         │  │ Landing  │   │  - book reconstruction  │  │
                    │  └────┬─────┘   │  - event detectors      │  │
                    │       │         │  - bar/footprint builder│  │
                    │       │         └──────────┬─────────────┘  │
                    │       │                    │                │
                    │  Rolling 7–14d             │                │
                    │  buffer, then       ┌──────▼─────────────┐  │
                    │  DELETE depth       │  FEATURE STORE      │  │
                    │  (keep trades,      │  (Parquet + zstd,   │  │
                    │   quotes forever)   │  Nautilus catalog)  │  │
                    └─────────────────────┴──────┬──────────────┘  
                                                 │
                          ┌──────────────────────┼──────────────────┐
                          │                      │                  │
                    ┌─────▼──────┐        ┌──────▼──────┐    ┌──────▼──────┐
                    │ Research / │        │ Nautilus    │    │ Nautilus    │
                    │ notebooks  │        │ BACKTEST    │    │ LIVE        │
                    │ (profiles, │        │ (fill sim + │    │ (same Actor │
                    │  IVB stats)│        │  signal lane)│   │  computes   │
                    └────────────┘        └─────────────┘    │  features   │
                                                             │  from feed) │
                                                             └─────────────┘
```

### 3.1 The two-lane principle

The store serves two distinct consumers with different requirements:

| Lane | Consumer | Purpose | Data |
|---|---|---|---|
| **Signal lane** | Strategy logic | Generate entries/exits: absorption triggers, reload detections, IB breakouts, effort/result boxes | Extracted features & events (custom data types) |
| **Execution lane** | Nautilus matching engine | Simulate fills honestly: prices, spreads, queue realism | Raw `TradeTick` + raw `QuoteTick` (+ optional reconstructed depth) |

The central design finding: **feature data alone cannot serve the execution lane.** NautilusTrader does not consume features to evaluate trades — it consumes market data to simulate an exchange. §6 details the consequences.

---

## 4. Feature Catalog

Features are organized by the concept family they serve. Each table lists retention class: **KF** = keep forever (raw), **F** = feature (computed, permanent), **E** = event stream (computed online, permanent, unrecoverable if skipped), **T** = tunable-lossy (granularity is a storage dial).

### 4.0 Raw retained streams

| Stream | Contents | Class | Notes |
|---|---|---|---|
| `trades` | ts_event, ts_recv, price, size, aggressor_side, trade_id | **KF** | Foundation of footprint/delta family and execution lane. Small. |
| `quotes` (BBO / L1) | ts_event, bid_price, bid_size, ask_price, ask_size | **KF** | Top-of-book changes only. Small fraction of full L2; compresses extremely well. Required for honest fill simulation (§6). **Answer to the side question: yes, tick bid/ask (with sizes) is stored, permanently.** |

### 4.1 Family A — Footprint / Delta (from trades)

Bucketed per bar at the finest resolution (recommendation: 1s base bars, aggregate upward to 5s/1m/etc. on read — never store multiple resolutions of derivable data).

| Feature | Definition | Class |
|---|---|---|
| Footprint rows | Per (bar, price level): bid_volume, ask_volume, trade_count, max_single_print | F |
| Bar aggregates | delta, cum_delta (CVD), intrabar min/max delta, total volume, VWAP, OHLC | F |
| Delta by size bucket | delta and volume split by trade-size class (e.g., small / medium / large; thresholds per instrument, versioned) — reconstructs the "big participants only" filtered view | F |
| Imbalance flags | Diagonal bid/ask ratio > threshold (e.g., 3:1) per level; stacked-imbalance runs | F |

*Concepts served:* footprint reading, delta footprint, absorption signatures (delta/close mismatch), initiative auction, exhaustion (declining volume), CVD divergence, big-trade confirmation.

### 4.2 Family B — Volume Profile (derived from A)

| Feature | Definition | Class |
|---|---|---|
| Session profile | Per session per price level: total volume. Session = chosen UTC window (crypto is 24/7 — define a "cash session" analog, e.g., UTC day and/or a designated high-volume window; definition is versioned config) | F |
| Profile summary | POC, VAH, VAL, value-area %, profile shape classifier (P / b / D / double-distribution), LVN list (price bands below volume-density threshold) | F |

Fully deterministic from Family A; stored materialized for query convenience. Serves: value-area framing, profile merging, LVN/FVG-void identification, P-shape bias, IVB Model 1 location logic.

### 4.3 Family C — Liquidity Heat Map (from depth; the deliberately-lossy zone)

| Feature | Definition | Class |
|---|---|---|
| Book snapshots | Top-N levels (N = 25–50), sampled at Δt = 100ms–1s; price tick-quantized; size optionally log-quantized. Snapshot rate is the primary storage dial. 1s loses sub-second flicker (largely spoof noise) but preserves every documented heat-map pattern | **T** |
| Level lifecycle events | appeared(price, size) / increased(Δ) / decreased(Δ) / pulled / consumed — compact event encoding computed at ingest | **E** |
| Per-bar book scalars | spread, best-bid/ask size, cumulative depth over N levels per side, **book slope** = depth ratio (path-of-least-resistance number), Order Flow Imbalance (OFI) | F |

*Concepts served:* heat-map visualization and history, resting vs. fresh liquidity distinction, rising/lowered levels, reload patterns, book slope, liquidity cluster walls, "next station" targeting.

### 4.4 Family D — Event Detections (computed online; unrecoverable otherwise)

| Event | Detection sketch | Stored fields |
|---|---|---|
| **Iceberg** | Executed volume at price exceeds displayed size across refills | ts, price, side, visible_size, total_filled, refill_count |
| **Sweep** | Single aggressive sequence consumes ≥ k levels | ts, direction, levels_swept, slippage_ticks, volume |
| **Absorption** | High traded volume at level with price failing to advance (effort/result mismatch beyond thresholds) | ts, price, side_absorbed, absorbed_volume, subsequent_N-bar_return (for validation) |
| **Reload / wall** | Passive size added at/near touch concurrent with same-side aggression (break-and-protect signature); distinguish fresh vs. resting via level lifecycle | ts, price, side, added_size, concurrent_aggression_volume |
| **Pull / spoof-candidate** | Large level removed shortly before price arrival without execution | ts, price, side, size_pulled, distance_at_pull |

All thresholds are versioned config. Every event carries `pipeline_version`.

### 4.5 Family E — Session / Model Features (IVB and regime)

| Feature | Definition | Class |
|---|---|---|
| Initial balance | IB high/low for configured opening window(s); breakout side & timestamp | F |
| Excursion stats | MFE/MAE after breakout; whether protection-level analogs hit; time-to-target | F |
| Session classification | range vs. directional, IB width percentile, realized-volatility regime | F |
| VWAP + bands | session VWAP, ±1/2 SD | F |

Tiny footprint; enables full replication of the IVB statistical study (protection level ≈ 65–70% excursion quantile, extreme average) on crypto sessions.

---

## 5. Storage Design

### 5.1 Format & layout

- **Format:** Apache Parquet, zstd compression, columnar. Book snapshots delta-encode extremely well (most levels unchanged between samples).
- **Layout:** compatible with the **NautilusTrader ParquetDataCatalog** so backtests read the store directly (§6.4).
- **Partitioning:** `instrument_id / data_type / date`. Base bars and events additionally sorted by `ts_event` (Nautilus requires monotonic timestamps within files).

### 5.2 Budget arithmetic (order-of-magnitude, per liquid instrument)

| Component | Raw scale | Retained scale |
|---|---|---|
| Full L2 depth deltas | ~GB/day | **0** after rolling buffer (7–14 days only) |
| Trades (raw, KF) | ~1–5% of raw total | kept fully |
| Quotes / BBO (raw, KF) | small multiple of trades | kept fully |
| 1s top-50 snapshots (T) | — | main tunable block |
| Footprints, profiles, scalars, events (F/E) | — | small |

Net: retained store typically lands around **3–10% of raw volume** before compression, and compresses further. Across a handful of assets this converts "impossible" into "fits on a laptop / small VPS."

### 5.3 What is knowingly lost

Documented explicitly so the loss is a decision, not an accident:

- Sub-snapshot-interval depth dynamics beyond what level-lifecycle events capture (mostly HFT flicker/spoof noise at 1s sampling).
- Depth beyond top-N levels.
- Any future feature requiring full historical depth replay (mitigated by: trades+quotes kept raw; rolling buffer for recent validation; ability to widen retention going forward if a need is discovered).

---

## 6. NautilusTrader Data-Model Mapping

### 6.1 Why features alone cannot evaluate trades

NautilusTrader's backtest venue is a **simulated exchange**: its matching engine fills orders against the market-data stream it is fed. With **trades-only** data:

- **Aggressive orders** (market/stop): the engine has no bid/ask at decision time; fills model off last trade price, systematically *understating spread cost*. For tick-scale scalping strategies, spread cost can equal the entire edge.
- **Passive orders** (limit): the documented setups are predominantly *passive entries at absorption/reload levels* — i.e., joining the queue behind the very wall being traded. Trades-only simulation typically fills a limit when price *touches* the level; in reality, touch ≠ fill. The perfect absorption trades (touched-and-rejected) are exactly the ones least likely to have filled. Trades-only backtests of passive strategies are structurally optimistic **for these specific setups**.

Hence the two-lane split and the keep-forever `quotes` stream.

### 6.2 Mapping table

| Store table | Nautilus type | Lane | Usage |
|---|---|---|---|
| `trades` | `TradeTick` | Execution + Signal | Matching-engine fills; last-price logic; also drives live feature computation |
| `quotes` | `QuoteTick` | **Execution** | Upgrades fill model to proper L1: market orders fill on correct side at prevailing quote; spread always known; slippage measured, not assumed |
| `snapshots` (top-N) | `OrderBookDepth10` (top-10 slice) or `OrderBookDeltas` reconstruction | Execution (optional) | Approximate-depth fill simulation for intraday-scale strategies; too coarse for sub-second scalping (which raw MBP never truly supported either) |
| `footprint_bars`, `bar_aggregates` | `Bar` (standard) + custom `Data` subclass for footprint rows | Signal | Strategy indicators; profile construction |
| `session_profiles`, `profile_summary` | custom `Data` (e.g., `SessionProfileData`) | Signal | Bias/location logic (IVB Model 1, LVN targeting) |
| `book_scalars` (slope, OFI, depth ratio) | custom `Data` (e.g., `BookStateData`) | Signal | Path-of-least-resistance filters |
| `events_*` (iceberg, sweep, absorption, reload, pull) | custom `Data` subclasses (e.g., `AbsorptionEvent`, `ReloadEvent`) | Signal | Entry triggers & trade-management signals |
| `ib_sessions` | custom `Data` (`InitialBalanceData`) | Signal | IVB breakout direction, protection-level targets |

Custom types subclass `nautilus_trader.core.data.Data`, carry `ts_event`/`ts_init`, are registered with the serialization layer, written into the same ParquetDataCatalog, and subscribed to by strategies exactly like native data. In backtests they arrive interleaved with `TradeTick`/`QuoteTick` in timestamp order.

### 6.3 Fill-model policy (escalating realism for passive entries)

| Level | Rule | Data required | Recommendation |
|---|---|---|---|
| **L1-conservative** | Passive fill only when price trades **through** the level (not touch) | trades + quotes | **Default.** Pessimistic bias is the correct bias; strategies surviving it are robust |
| **Queue-probabilistic** | Fill iff traded volume at price ≥ displayed size ahead at arrival (estimated from snapshot depth + footprint volume-at-price) | + snapshots + footprints | Custom `FillModel`; use when conservative rule is demonstrably too punishing |
| **Reconstructed depth** | Replay top-N snapshots as depth stream | + snapshots | Intraday-scale only; do not use to justify sub-second scalping conclusions |

### 6.4 Catalog integration

- Write all streams (native + custom) via Nautilus data wranglers / catalog writers into one `ParquetDataCatalog` rooted per environment.
- Backtest configuration selects instrument, date range, and the data types to load; the engine merges streams by timestamp.
- Keep `ts_event` = exchange timestamp, `ts_init` = ingest timestamp throughout, so latency assumptions are explicit and adjustable.

---

## 7. Backtest / Live Parity Architecture

Going live is operationally simple — live Nautilus consumes the real Bybit adapter feed directly; storage decisions do not constrain it. The genuine risk is **signal-lane parity**: in backtest the strategy reads *precomputed* events; live, they must be computed on the fly. Any divergence (threshold drift, timing, a look-ahead bug in the batch extractor) means live behavior differs from what was validated.

**Design rule — one implementation, two runtimes:**

1. Implement every feature/detector as **streaming logic packaged as a NautilusTrader Actor / indicator** operating on `TradeTick`, `QuoteTick`, and book updates.
2. The **batch ingest pipeline runs this exact Actor code** over historical raw data (replayed in event order) to produce the feature store.
3. Consequently, stored features are *by construction* identical to what live computation would have produced. Backtests may consume either the stored events (fast) or recompute via the Actor (slow, used periodically as a parity audit).

Additional parity safeguards:

- **No look-ahead by construction:** detectors emit events only from information available at `ts_event`; validation fields (e.g., absorption's subsequent-return) are stored separately and flagged research-only.
- **Parity CI test:** replay a golden day of raw data through both runtimes; assert byte-identical event streams before any `pipeline_version` is promoted.
- **Config as code:** all thresholds live in versioned config consumed identically by both runtimes.

---

## 8. Operational Pipeline

1. **Acquire:** Bybit historical downloads + live WebSocket capture (depth deltas + trades) into the raw landing zone.
2. **Reconstruct:** maintain the full book in memory from deltas; validate with sequence numbers / periodic snapshots from the feed.
3. **Extract:** run the shared streaming engine → emit footprint bars, scalars, snapshots, lifecycle events, detections, session features.
4. **Write:** Parquet into the Nautilus catalog layout, partitioned per §5.1, stamped with `pipeline_version`.
5. **Verify:** invariant checks (e.g., Σ footprint volume ≡ Σ raw trade volume per bar; snapshot best bid/ask ≡ quotes stream at sample times; event counts within historical bands).
6. **Expire:** delete raw depth older than the rolling buffer window. **Never** expire `trades` or `quotes`.
7. **Audit (periodic):** golden-day parity replay (§7); re-derive one session's profile from raw buffer and diff against the store.

---

## 9. Decision Log (summary of the discussion)

| # | Question | Decision |
|---|---|---|
| 1 | Lossless reduction possible? | No (information-theoretic); **yes relative to the closed concept set**, with detections computed online before deletion |
| 2 | What to keep raw? | `trades` and `quotes` (tick BBO with sizes) — keep-forever; full depth only in a 7–14 day rolling buffer |
| 3 | Store tick bid/ask? | **Yes** — the `QuoteTick` stream is mandatory for honest fill simulation and is cheap |
| 4 | Is trades data enough to evaluate trades in Nautilus? | **No.** Sufficient for the signal lane; insufficient for the execution lane (spread cost, passive-fill realism). Trades + quotes + conservative through-price fill rule is the sound baseline |
| 5 | Passive-fill realism beyond L1? | Escalate: conservative rule → queue-probabilistic custom FillModel (inputs already in the store) → reconstructed top-N depth (intraday only) |
| 6 | Live-trading path? | Live consumes the Bybit feed directly; parity ensured by single shared streaming implementation + golden-day CI audit |
| 7 | Main storage dial? | Snapshot interval and top-N depth of the heat-map layer (deliberately, tunably lossy) |
| 8 | Failure-mode protections? | Rolling raw buffer, versioned features, invariant checks, parity audits |

---

## 10. Open Items / Next Steps

- [ ] Fix per-instrument config v1: tick size, size buckets, imbalance ratio, absorption thresholds, snapshot Δt and N, session window definition.
- [ ] Implement book reconstruction + sequence-gap handling for Bybit depth stream.
- [ ] Implement detector Actors (iceberg, sweep, absorption, reload, pull) + unit tests on synthetic books.
- [ ] Define and register custom Nautilus `Data` subclasses; write wranglers for catalog ingestion.
- [ ] Implement conservative FillModel configuration; prototype queue-probabilistic FillModel.
- [ ] Golden-day parity test harness.
- [ ] Measure real compression ratios on 1–2 weeks of captured data; finalize the storage budget per instrument.
