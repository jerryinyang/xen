# INFR-010 — Engine & Data Migration: cTrader/C# → NautilusTrader/Python, Bybit Perp Universe

**Type:** infrastructure (master migration plan — spawns INFR-011..013 + VAL)
**Status:** DESIGN v2 (rewritten 2026-07-14 after operator restructure; supersedes v1 in full)
**Author route:** research-pipeline orchestrator, scope-only design entry

---

## 1. Objective

Replace the research substrate in three coupled moves, preserving the governance canon:

1. **Engine:** cTrader C# `StrategyHost` → **NautilusTrader** (Python API, Rust core, event-driven).
2. **Data — PRIMARY (OHLCV):** 1-minute bars **derived from Bybit trades archives**, covering the
   **full Bybit USDT linear perpetual universe including delisted contracts** (strict
   anti-survivorship). Default dataset for ALL experiments (XENA, EXP, SPDR, VAL).
3. **Data — SECONDARY (MBP):** reduce-at-ingest orderflow feature store per
   `docs/references/orderflow-feature-store.md` (ratified from
   `.ignore/temp/orderflow_feature_store_architecture.md`), **BTCUSDT / ETHUSDT / SOLUSDT
   perps only**. Architecture implemented in this INFR (contracts + skeleton); **collection
   and population deferred** to a later, separately-approved INFR. Until then every
   experiment runs on OHLCV.

Programme invariants (holdout fence, causal-by-construction execution, estimand gate, XENA
portfolio adjudication, KB/registry continuity) carry forward; only implementations rebind.

## 2. Operator decisions (locked 2026-07-14)

| # | Decision | Resolution |
|---|----------|------------|
| D1 | Data source | **Bybit official free archives only** (no Tardis/Databento/Amberdata). Binance public archives (`data.binance.vision`) recorded as *fallback* OHLCV source should Bybit archives fail — Binance has **no** free historical L2, so no MBP fallback exists |
| D2 | Primary dataset | OHLCV 1m, **derived from trades archives** (`public.bybit.com/trading/`) — only path that covers delisted symbols; real traded volume; integrity-verifiable (bar ≡ Σ trades) |
| D3 | Universe | **USDT linear perpetuals only**, listed + delisted. No spot, no inverse, no dated futures, no USDC-settled |
| D4 | MBP scope | Secondary; **BTC/ETH/SOL USDT perps**; implement contracts + skeleton now; collection deferred |
| D5 | Legacy stack | **Chapter rollover** — close Chapter 03, archive cTrader C#/CLI; new chapter Nautilus-native |
| D6 | Holdout | **Global calendar fence** — one TRAIN/TEST/HOLDOUT date pair shared by every symbol (cross-sectional leak-safety; late-listed symbols simply have less TRAIN) |
| D7 | Bid/ask for fills | **Pseudo-quotes from aggressor-side trades are sufficient for now.** No live BBO capture, no forward fix approved. Real quotes exist only in the (deferred) MBP trio store |
| D8 | Terminology | Bybit depth data is **MBP/L2** (price-level). MBO/L3 claims are out of scope — Bybit does not publish order-ID data |

## 3. Grounding facts (web-verified 2026-07-14)

**Bybit archives:**
- `public.bybit.com/trading/` — per-symbol trade archives (CSV.gz: ts, price, size, aggressor
  side, id), **~2,000+ symbol folders including delisted** (LUNA2USDT, USTCUSDT, dated
  futures) → the directory listing itself is the anti-survivorship universe census.
- Depth (MBP) archives via portal `bybit.com/derivatives/en/history-data`
  (snapshot+delta JSON zips from `quote-saver.bycsi.com`), history **~July 2023+**,
  UI capped ~7 days/request → scraper required. Scale: BTCPERP full depth ≈ 63 GB
  compressed / ~380 GB raw.
- **No standalone historical BBO/quote archive exists** — historical bid/ask only via
  depth-top-level extraction (heavy → MBP trio only) or paid vendors (declined).

**NautilusTrader capability (confirms operator question):**
- Historical: official `BybitOrderBookDeltaDataLoader` + `OrderBookDeltaDataWrangler` →
  `ParquetDataCatalog`; official tutorial backtests Bybit depth-500 with `book_type=L2_MBP`.
- Live: Bybit adapter (instruments/data/execution clients) subscribes `OrderBookDeltas` /
  trades; `StreamingConfig` persists live streams to catalog. **Capability confirmed;
  live capture NOT approved for use (D7).**
- Catalog: Rust-backed Parquet, ns timestamps (`ts_event`/`ts_init`), monotonic-ts
  requirement per file; custom `Data` subclasses register into the same catalog.
- Engine: single-threaded event-sequenced → deterministic replay (verified in Phase B).

## 4. Fill-simulation & cost tiers (binding rule)

| Tier | Data | Fill/cost treatment | Applies to |
|------|------|--------------------|-----------|
| **T1 — OHLCV lane** | 1m bars (+ per-symbol pseudo-quote spread estimates derived from aggressor-side trades: Buy print ≈ ask, Sell print ≈ bid) | Engine costless-honest; **spread + fees + funding injected at analysis layer** (programme discipline, INFR-009 P5 precedent). Spread model = pseudo-quote estimate with tick-size floor, conservative bias | All experiments by default |
| **T2 — MBP trio** | Real `QuoteTick` (keep-forever stream extracted from depth) + trades + feature store | Honest L1 fills in-engine; passive fills via conservative through-price rule (feature-store doc §6.3) | Only after MBP collection INFR approved + executed |

**Spread-scale routing rule:** any candidate whose gross edge is within ~3× the estimated
round-trip spread (XENA-003 class: 1.96 bps gross vs 0.71 bps breakeven) is **undecidable
on T1** — verdict-bearing confirmation requires T2 (must be BTC/ETH/SOL, post-collection)
or the candidate parks as `AWAITING_MBP`. Pooled T1 reads on such candidates are
disclosure-only.

## 5. What carries forward vs what is archived

| Asset | Fate |
|-------|------|
| `docs/knowledge-base/` (L-01..L-27, pitfalls, methodology canon) | **Carries forward** — append-merged at rollover |
| `docs/signal-registry/` (multiplicity, test-read ledger, families) | **Carries forward** — never reset |
| Governance principles (holdout, bar-open decisions, open-to-open returns, estimand-before-hypothesis, future-destroy controls, operator gates) | **Carry forward** — re-expressed for Nautilus in INFR-012 |
| `xen.evaluation`, `xen.adjudication` (stats/estimand logic) | **Carry forward** — feed shims rewritten for Nautilus emissions |
| `xen.xena.*` + Rust `xena_fold` | **Carry forward** — ingest contract rebound; **frozen registry VOID on new stack** (§8 R4) |
| Xen.cs, `StrategyHost/`, `tools/ctrader-cli/`, C# generators | **Archived** at chapter close (tagged, dead) |
| `data/timebars/` (815 MB m1 FX/indices), `data/strategy_runs/` (13 GB) | **Archived** — FX/indices holdout obligations remain binding on that data forever |
| Chart-type generators (linebreak/renko/HA) | **Dormant** — port only on demand |
| FTMO cost table | **Replaced** — Bybit USDT-perp maker/taker fees + funding accrual + T1 spread model |
| `.ignore/temp/orderflow_feature_store_architecture.md` | **Ratified** → `docs/references/orderflow-feature-store.md` (Phase E) |

## 6. Phased plan

```
Phase 0  Chapter-03 close (rollover ritual)                 → operator-signed retro + tag
Phase A  INFR-011: OHLCV primary dataset                    → admitted catalog + fence manifest
Phase B  INFR-010 exec: engine foundation + smoke           → deterministic BacktestNode runs
Phase C  INFR-012: governance rebind                        → docs/skills/gates ported
Phase D  VAL-0xx: end-to-end pipeline dry run               → leak controls proven on new stack
Phase E  INFR-013: MBP feature-store contracts + skeleton   → code + schemas; NO collection
```

A ∥ B after Phase 0 (B smokes on tutorial-scale sample before A completes). E can trail
anytime after B; D requires A+B+C.

### Phase 0 — Chapter 03 close
- Close checkpoint-012 retrospective (INFR-009 restoration already ratified).
- Archive per precedent: `archive/chapter-03-.../`, tag `chapter-03-close`; invoke
  `chapter-rollover` skill (Extract / Archive / Renew — Renew change-set = this migration).
- Fix stale `python/experiments/INDEX.md` INFR-009 row (COMPLETE 2026-07-14, not IN PROGRESS).
- **Verify:** tag exists; KB INDEX updated; tree carries only forward-assets.

### Phase A — INFR-011: OHLCV primary dataset
1. **Universe census (blocking first step):** enumerate `public.bybit.com/trading/` listing;
   filter to USDT linear perps (regex + instrument metadata; exclude spot dirs, `*PERP`
   USDC contracts, inverse `USD` contracts, dated futures). Cross-check against Bybit
   delisting announcements. Output `universe-census.md`: symbol, first/last archive date,
   listed/delisted flag. **Delisted-symbol contract specs** (tick size, lot) recovered
   best-effort (archives + announcements) — gaps recorded, not guessed.
2. **Scraper:** resumable trades downloader, checksum manifest, polite rate limits.
   Raw CSV.gz retained compressed **until** bar derivation + invariants pass, then deleted
   (archives remain re-downloadable at Bybit) — **except the MBP trio's trades: keep-forever**
   (feature-store §4.0 KF class).
3. **Derivation:** trades → 1m OHLCV bars (real volume; open/close from first/last print) +
   per-symbol pseudo-quote spread series (aggressor-side straddle, tick-floor). Invariants:
   bar volume ≡ Σ trade sizes; monotonic ts; OHLC bounds; gap ledger (24/7 market → gaps are
   outages/delistings, all logged).
4. **Catalog ingest:** instrument definitions + `Bar` objects → `ParquetDataCatalog` at
   `data/catalog/`, partitioned `instrument_id/data_type/date`.
5. **Admission (VAL-style, blocking):** invariant report, cross-symbol sanity (BTC vs ETH
   correlation-window smoke), delisting-tail inspection (death spirals present, not trimmed).
6. **Global calendar fence:** single date pair (TRAIN/TEST cut + HOLDOUT start) computed from
   admitted range, written to a hash-pinned split manifest (absolute dates). Catalog query
   wrapper refuses post-fence reads outside sanctioned paths. Final 30% never queried.
- **Verify:** census complete; admission PASS; fence manifest pinned; storage sane
  (bars for full universe ≈ single-digit GB Parquet; transient raw ≈ 100s of GB peak).

### Phase B — INFR-010 execution: engine foundation
1. Pin `nautilus_trader` version (uv env under `python/`); record version + platform
   (one-platform rule inherited from INFR-007 caveat).
2. Smoke strategy (trivial MA-cross) through `BacktestNode` on sample bars; plus one
   depth-sample L2_MBP smoke (tutorial data) to prove the MBP path compiles end-to-end.
3. **Determinism check:** identical config → identical fills/P&L, byte-level event-log
   compare, 3 repeats.
4. **Emission contract v1:** standardized post-run artifact set (fills, positions, order
   events, run metadata incl. config hash + catalog version + fence attestation) — Nautilus
   equivalent of `data/strategy_runs/<ID>/`; what `xen.estimand_validation` v2 gates.
- **Verify:** deterministic; emission parses into `xen.adjudication` via new shim.

### Phase C — INFR-012: governance rebind
1. Rewrite binding docs: `architecture.md` v2 (catalog + two-lane data model),
   `dataset-reference.md` v2 (Bybit perp universe), `_pipeline-config.md` (paths, universe,
   execution stage → Nautilus runner), skills (quant-designer / qa-compliance / data-analyst /
   experiment-developer execution references).
2. Principle rebind — exact mappings:
   - "cTrader engine, no Python backtest" → **"Nautilus event-driven engine only; no
     vectorised Python backtest of a price strategy"** (principle = causal-by-construction
     event sequencing, not C#).
   - `AnalysisEndUtc` fence → catalog fence wrapper + emission attestation.
   - `CloseTime`/`SourceCloseTime` alignment → `ts_event` ns discipline; decisions on
     confirmed data ≤ t−1 only; document + test Nautilus no-lookahead guarantees.
   - Open-to-open returns → unchanged for bar-domain strategies.
3. `xen.estimand_validation` v2: reconciliation invariant vs Nautilus position/fill events;
   `check_no_local_accounting` unchanged.
4. **Cost model:** Bybit USDT-perp maker/taker schedule + funding accrual + T1 spread
   injection (§4) → new table in `xen.evaluation`; netted-turnover rule carries.
   Spread-scale routing rule (§4) codified in quant-designer + qa-compliance checklists.
5. XENA lane doc v2: fills contract from Nautilus emissions; frozen registry marked
   **VOID for new data** — fresh calibration cycle (CAL discipline: n_null sizing,
   design/confirm bank split, predeclared n) required before any crypto universe.
- **Verify:** doc set consistent; QA subagent dry-reads new pipeline docs for contradictions.

### Phase D — VAL: end-to-end dry run
1. One registered throwaway hypothesis through the full pipeline on new stack: design → QA →
   execute (Nautilus) → estimand gate → analysis → operator verdict → document.
2. **Leak battery:** future-destroy control must collapse the edge; deliberately-planted
   lookahead strategy must be caught (test masking, don't assert it — L-13).
3. TRAIN-only; no counted TEST reads; disposition informative-only.
- **Verify:** artifacts complete; planted leak caught; controls collapse.
**Chapter 04 opens** (checkpoint-013 design) only after Phase D passes.

### Phase E — INFR-013: MBP feature-store contracts + skeleton (NO collection)
Per ratified `orderflow-feature-store.md`. In scope NOW:
1. Custom Nautilus `Data` subclasses + serialization registration (footprint rows,
   `SessionProfileData`, `BookStateData`, event types) + catalog schemas.
2. Config-as-code format (per-instrument thresholds, snapshot Δt/N, session windows) with
   `pipeline_version` stamping.
3. Book reconstruction + sequence-gap handling for Bybit depth stream (unit-tested on
   synthetic books + one sample archive day).
4. Ingest-pipeline skeleton (landing → shared streaming engine slot → catalog writer)
   with the five detector slots stubbed.
DEFERRED (to the collection INFR, operator-gated): bulk depth download (BTC/ETH/SOL),
detector implementations (iceberg/sweep/absorption/reload/pull), queue-probabilistic
FillModel, golden-day parity harness, rolling raw-buffer ops, quotes-stream extraction.
- **Verify:** schemas round-trip through catalog; reconstruction passes synthetic + sample-day
  tests; zero bulk data on disk.

## 7. Explicit non-goals

- **No MBP bulk collection/population** — separate INFR, separate operator approval.
- **No live trading, no live data capture** (D7: capability noted, use not approved).
- No spot, inverse, USDC, or dated-futures instruments.
- No vendor subscriptions; no MBO/L3 claims.
- No new research hypotheses inside the migration (Phase D vehicle is a pipeline test only).
- No porting of chart-type generators, retired referee stack, or SPDR internals until demanded.
- No XENA registry recalibration inside this INFR (declared follow-up).

## 8. Risks / open items

| # | Risk | Handling |
|---|------|----------|
| R1 | Universe census wrong (missed delisted symbols, misfiltered contract types) → survivorship bias re-enters silently | Census is blocking step A1 with dual source (archive listing × delisting announcements); census file is a permanent audit artifact |
| R2 | Delisted-symbol specs (tick size/lot) unrecoverable for some symbols | Record gaps explicitly; affected symbols flagged `SPEC_INCOMPLETE`, excluded from fill-sensitive reads, included in return-level reads |
| R3 | T1 pseudo-quote spread model too optimistic on thin/delisted tails | Conservative tick-floor + §4 spread-scale routing rule; per-stratum reads keep thin tails visible |
| R4 | XENA frozen registry engine+data-specific → **VOID on new stack** | Marked VOID Phase C; fresh calibration INFR before any crypto universe |
| R5 | Nautilus version churn | Hard pin; upgrade only by INFR amendment |
| R6 | Trades-archive quality (gaps, schema drift across years, outages) | Derivation invariants + gap ledger blocking at admission (Phase A5) |
| R7 | Funding-rate history needed for perp cost model (incl. delisted symbols) | Phase C4 sources Bybit funding archives/API; coverage gaps recorded; symbols without funding history get conservative funding assumption, flagged |
| R8 | Depth history only ~July 2023+ → future MBP store shorter than OHLCV history | Accepted; MBP lane is confirm-stage (T2), not screening substrate |
| R9 | Global calendar fence + 24/7 market: fence dates must respect archive end, not calendar today | Fence computed from admitted range end at Phase A6; manifest pins absolute dates |

## 9. Execution gate

Per pipeline: **operator approval required before Phase 0 executes** (archive + tag is
destructive-adjacent). Phases A–E each end at their verify block; INFR-011/012/013 get their
own design.md stubs derived from §6 at spawn time.
