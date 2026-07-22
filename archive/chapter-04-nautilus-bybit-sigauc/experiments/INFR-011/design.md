# INFR-011 — OHLCV Primary Dataset (Phase A of INFR-010)

**Type:** infrastructure (data substrate)  
**Status:** SPAWNED — executing Phase A per parent  
**Parent:** `python/experiments/INFR-010/design.md` §6 Phase A (read in full; this is a derived stub)  
**Decisions:** D1–D8 and §4 fill tiers **locked and binding** (no re-derivation).  
**Entry:** research-pipeline orchestrator per INFR-010 spawn rule.  
**Scope:** Execute the six enumerated steps of Phase A only. No scope expansion. Stop at verify block.

## 1. Objective (verbatim from INFR-010)
Replace research substrate data layer with Bybit USDT linear perpetual trades archives → 1m OHLCV + pseudo-quote spreads, full anti-survivorship universe (listed + delisted), ingested to ParquetDataCatalog under global calendar fence.

## 2. Locked Constraints (D1–D8 + §4)
See INFR-010 §2 and §4 for full text. Summary binding for this execution:
- D1: Bybit official free archives only (`public.bybit.com/trading/`).
- D2: Primary = 1m OHLCV **derived from trades** (volume integrity verifiable).
- D3: **USDT linear perpetuals only** (listed + delisted). Exclude spot, inverse (USD), dated futures, USDC.
- D4: MBP secondary, deferred (BTC/ETH/SOL only; not in scope here).
- D6: Global calendar fence (single TRAIN/TEST/HOLDOUT dates for whole universe).
- D7: Pseudo-quotes from aggressor-side sufficient for T1.
- D8: MBP/L2 terminology.
- §4 T1 lane: OHLCV + pseudo-quote spreads; cost/spread injected at analysis (no in-engine fill simulation for this INFR).

## 3. Phase A Steps — Amended (2026-07-14)
**Amended constraints (operator review, superseding original wording):**
- **4-year history cap** — trailing 4y per symbol (long symbols use most recent ~1460 days). Fence on capped range.
- **Streaming, raw-less pipeline — ZERO raw retained (incl. BTC/ETH/SOL):**
  - Per day-file: download → decompress in-stream → 1m bars + pseudo spreads → Parquet staging → discard.
  - Peak raw disk = one file in flight (memory).
  - Trio keep-forever **deferred** to future MBP collection INFR (archives re-downloadable).
- Plain Python downloader + manifest. Nautilus only at catalog ingest.
- Resumable + checksum manifest required.

1. **BLOCKING universe census** (revised): strictly `*USDT/` folders only (exclude all `*PERP` USDC-settled perps per D3 + §6 A1). 910 candidates after correction. Cross-checked vs announcements (reconciliation BLOCKING pre A5).
2. Streaming downloader + in-stream derivation (combined) with manifest + checksums.
3. Invariants (blocking): bar volume ≡ Σ trades, monotonic ts, OHLC bounds, gap ledger.
4. ParquetDataCatalog ingest (blocked until Phase B pins nautilus_trader).
5. VAL-style admission gate (BLOCKED until delist reconciliation complete).
6. Global calendar fence (4y-capped) → hash-pinned split manifest + enforcing wrapper.

**Raw handling:** ZERO permanent raw (all day-files discarded after aggregation).

## 4. Artifacts (this INFR-011)
```
python/experiments/INFR-011/
├── design.md
├── universe-census.md          # revised 910, USDT-only, 4y cap + streaming notes
├── artifacts/
│   ├── candidate_symbols.txt   # 910 strict USDT
│   ├── universe-census.json
│   ├── checksum-manifest.json  # (populated during streaming run)
│   ├── split-manifest.json (hash-pinned)
│   └── admission-report.md
├── data/                       # Parquet staging only (no raw except keep-forever)
└── scripts/
```

## 5. Verify Block (stop here)
- Corrected census (910 USDT-only) presented.
- Streaming/raw-less + 4y cap implemented.
- Admission PASS (after delist reconciliation).
- Fence manifest pinned.
- Storage sane (~30 GB peak, single-digit GB Parquet).
- No bulk proceeds without approval after revised census.
- Step 4 blocked on Phase B Nautilus pin.
- This INFR does not open Chapter 04 or touch XENA/EXP/VAL research.

**Reference:** INFR-010/design.md §6 Phase A, §8 risks (R1–R2 census critical), §9 execution gate.

**Next after verify:** Operator sign-off → proceed to scraper bulk (resumable) or parallel Phase B.

---
*Stub created 2026-07-14 per user/research-pipeline invocation. All substance locked in parent.*