# INFR-011 Invariant Summary + Gap Ledger + Storage

**Generated:** 2026-07-14T23:23:38.885488+00:00
**Pipeline:** streaming raw-less (zero raw retained, incl. BTC/ETH/SOL)
**History cap:** trailing 1461 days (~4y)

## Counts
- Symbols processed (status rows): 1
- OK: 1
- Empty/no bars: 0
- Fail/error/invariant_fail: 0
- Total 1m bars: 2,103,447
- Total gap minutes (vs continuous grid): 393

## Invariants (OK symbols)
- Volume ≡ Σ trades failures: 0
- Monotonic ts failures: 0
- OHLC bound failures: 0

## Storage
- Staging dir: `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/python/experiments/INFR-011/data/staging/bars`
- Parquet files: 1
- Total Parquet size: 0.104 GB (111,378,293 bytes)
- Peak raw: one day-file in memory (discarded); **zero permanent raw**

## Failures (if any)
_none_

## Gap ledger (top 20 by gap minutes)
| Symbol | Gap minutes | Bars | First | Last |
|--------|-------------|------|-------|------|
| SOLUSDT | 393 | 2103447 | 2022-07-14T00:00:00 | 2026-07-13T23:59:00 |
