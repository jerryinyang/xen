# INFR-011 Universe Census — Bybit USDT Linear Perpetuals (incl. delisted)

**REVISED 2026-07-14** (post-operator review)  
**Generated:** 2026-07-14  
**Source:** https://public.bybit.com/trading/ (Apache directory listing)  

**Filter (D3 + INFR-010 §6 A1, corrected):**  
**Strictly folders ending `USDT/` only.**  
- Exclude all `*PERP/` (these are USDC-settled perpetuals — explicitly excluded by design D3/D6 and §6 A1 "exclude *PERP USDC contracts").  
- Exclude dated futures (`-DDMMMYY` patterns, `WC_*`).  
- Exclude inverse (`*USD` not ending USDT).  
- Exclude USDC-settled.

**Total directories on server:** 1763  
**Corrected candidates (USDT-only):** **910**

**Candidate list:** `candidate_symbols.txt` (910 lines, sorted)

## Sample Date Ranges (observed; 4y processing cap applied)
| Symbol     | Observed First | Observed Last | Observed Days | Capped First (trailing 4y) | Capped Days |
|------------|----------------|---------------|---------------|----------------------------|-------------|
| BTCUSDT   | 2020-03-25    | 2026-07-13   | 2302         | 2022-07-14                | ~1460      |
| ETHUSDT   | 2020-10-21    | 2026-07-13   | 2092         | 2022-07-14                | ~1460      |
| SOLUSDT   | 2021-06-29    | 2026-07-13   | 1841         | 2022-07-14                | ~1460      |
| LUNA2USDT | 2022-05-31    | 2026-07-13   | 1505         | 2022-07-14                | ~1460      |
| USTCUSDT  | 2023-11-27    | 2026-07-13   | 960          | 2023-11-27                | 960        |

**Important correction on delisted examples:** LUNA2USDT and USTCUSDT both have `last_archive=2026-07-13`. They are **still-listed contracts** on the archive. The prior age heuristic produced zero verified delisted samples. The announcement reconciliation is load-bearing work.

**Delisting cross-check (BLOCKING before A5 admission gate):**  
- Must reconcile every symbol (or statistically significant sample + all thin tails) against Bybit announcements (announcements.bybit.com, blog, support).  
- For each: set accurate `listed`/`delisted` flag.  
- Recover tick size + lot size best-effort. Mark `SPEC_INCOMPLETE` where unrecoverable (exclude from T1 fill-sensitive analysis).  
- Parallel with bulk OK; **complete before step 5 admission**.

## Amended Execution Constraints (2026-07-14, supersede prior)
From operator review + INFR-010 design amendment:

1. **4-year history cap** — trailing 4 years per symbol for derivation + global fence. Long-lived symbols (BTC etc.) use the most recent ~1460 days.
2. **Streaming, raw-less pipeline — ZERO permanent raw** (incl. BTC/ETH/SOL; keep-forever deferred to MBP INFR):
   - Per day-file: download → decompress in-stream → aggregate to 1m OHLCV + pseudo-quote spreads → Parquet staging → discard immediately.
   - Peak raw = **one file in flight** (memory). Permanent raw GB = 0.
3. Downloader: plain Python + resumable checksum manifest. Nautilus only at catalog ingest.
4. Step 4 (catalog ingest) blocked until Phase B pins `nautilus_trader`.

## Storage Estimate (post-amendment)
- **N symbols:** 910
- **Permanent raw:** 0 GB
- **Peak in-flight:** one day-file
- **Final Parquet:** single-digit GB target

**Bulk download is now approved** subject to:
- Refilter (this document) complete.
- Streaming/raw-less + 4y cap enforced in implementation.
- Delisting reconciliation complete before A5 admission.
- No counted TEST / research use until full Phase A verify.

## Next (post this revised census)
- Implement streaming downloader + in-stream aggregator (steps 2+3 combined).
- Run bulk under the new constraints.
- Complete delist reconciliation in parallel.
- Hold catalog ingest (step 4) until Phase B pins Nautilus.
- Stop at verify block.

**Risks (R1/R2):** Filter defect now fixed. Census is the authoritative source + announcement reconciliation is mandatory pre-admission.

*Blocking census revised and presented. Ready for amended bulk execution.*