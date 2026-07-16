# INFR-011 A5 — Admission Report

**Census:** 910 | ADMITTED: 894 | FAIL_CORRUPT: 1 | NO_BARS: 1 | OMITTED_OPERATOR: 5 | SPEC_INCOMPLETE: 9
**Overall:** PASS_WITH_EXCLUSIONS
**Total bars (admitted + spec-incomplete):** 672,138,742

## Invariants
- Structural re-verification on local parquets: 903 symbols pass
- Failures: 1 — ['KASUSDT']
- Volume ≡ Σ trade sizes verified at derivation (raw discarded by design); carried from symbol-status rows; Buy+Sell ≡ Volume re-verified here.

## Collection repair (2026-07-16, operator-approved)
- EC2 bulk run had left 23,450 day-files as HTTP-403 `error` across 740 symbols while marking symbols ok (day-level failures were never retried).
- Repaired locally by `patch_missing_days.py` (re-download + merge + invariant re-run per symbol).
- Unresolved error days remaining after repair: 1205 (symbols with COLLECTION_GAP minutes: ['AAVEUSDT', 'ALPHAUSDT', 'APTUSDT', 'AVAXUSDT', 'BCHUSDT', 'CELOUSDT', 'CTSIUSDT', 'DENTUSDT', 'ETHFIUSDT', 'FITFIUSDT', 'FLMUSDT', 'FORTHUSDT', 'FXSUSDT', 'GLMRUSDT', 'GRIFFAINUSDT', 'HFTUSDT', 'HIFIUSDT', 'HOMEUSDT', 'KAVAUSDT', 'KITEUSDT', 'KNCUSDT', 'L3USDT', 'LDOUSDT', 'LINAUSDT', 'LOOKSUSDT', 'LQTYUSDT', 'LRCUSDT', 'LSKUSDT', 'LYNUSDT', 'MANTAUSDT', 'MASAUSDT', 'MAVIAUSDT', 'MAVUSDT', 'MBOXUSDT', 'MDTUSDT', 'MERLUSDT', 'MINAUSDT', 'MKRUSDT', 'MMTUSDT', 'MOBILEUSDT', 'MONUSDT', 'MOVRUSDT', 'MUBARAKUSDT', 'MUSDT', 'NEOUSDT', 'OGNUSDT', 'OMGUSDT', 'OMNIUSDT', 'ONEUSDT', 'PARTIUSDT', 'PENDLEUSDT', 'PENGUUSDT', 'PEOPLEUSDT', 'POPCATUSDT', 'PROMPTUSDT', 'QIUSDT', 'RAREUSDT', 'RAVEUSDT', 'RENDERUSDT', 'RIFUSDT', 'ROSEUSDT', 'SAFEUSDT', 'SAHARAUSDT', 'SANDUSDT', 'SCAUSDT', 'SCRUSDT', 'SHIB1000USDT', 'SIRENUSDT', 'SLERFUSDT', 'SLPUSDT', 'SNXUSDT', 'SOONUSDT', 'SPELLUSDT', 'SPXUSDT', 'STGUSDT', 'STORJUSDT', 'SXPUSDT', 'TAOUSDT', 'THETAUSDT', 'TIAUSDT', 'TLMUSDT', 'TRUMPUSDT', 'TRUTHUSDT', 'TRXUSDT', 'TWTUSDT', 'VANRYUSDT', 'VELVETUSDT', 'VETUSDT', 'WUSDT', 'XAIUSDT'])

## Gap classification (INFORMATIVE — no veto on raw totals)
- Consensus exchange-outage windows (≥10 near-continuous symbols gapping ≥10m together): 0

| Symbol | fill ratio | no-trade min | collection min | outage min | max run |
|---|---|---|---|---|---|
| PAXGUSDT | 0.574373 | 895,450 | 0 | 0 | 251 |
| SUNUSDT | 0.601401 | 838,583 | 0 | 0 | 242 |
| REQUSDT | 0.601588 | 837,836 | 0 | 0 | 119 |
| USDEUSDT | 0.19243 | 821,602 | 0 | 0 | 672 |
| JSTUSDT | 0.611745 | 816,826 | 0 | 0 | 152 |
| BOBAUSDT | 0.626273 | 786,262 | 0 | 0 | 154 |
| SCUSDT | 0.64903 | 738,067 | 0 | 0 | 206 |
| XNOUSDT | 0.589776 | 732,556 | 0 | 0 | 271 |
| 1000XECUSDT | 0.661152 | 712,881 | 0 | 0 | 143 |
| 1000BTTUSDT | 0.661797 | 711,524 | 0 | 0 | 205 |

## Delist tails
- Delisted symbols with trimmed tails (last bar day ≠ last archive day): 0 (all intact)

## Instrument specs
- API specs (listed): 612
- SPEC_INFERRED (delisted, from bar price/size grids): 282
- SPEC_INCOMPLETE (return-level reads only): 9 — ['BTTUSDT', 'COCOSUSDT', 'FDUSDUSDT', 'LTOUSDT', 'PIXFIUSDT', 'RAYUSDT', 'RONUSDT', 'STRAXUSDT', 'ZCXUSDT']

## Explicit non-admitted rows
- OMITTED_OPERATOR (5): MYRIAUSDT SFPUSDT TACUSDT TRIAUSDT UNIUSDT — no data collected (403 both EC2 passes). Operator 2026-07-16: fails intended universe selection rules; retryable later if ever needed.
- The 9 K-cluster symbols originally omitted are ADMITTED (operator revision 2026-07-16): their collections completed with passing invariants + verified parquets; the 'failed both passes' premise was a duplicate worker's .tmp rename error row.
- NO_BARS (1): DATAOLD01USDT — dead placeholder archive.
- FAIL_CORRUPT (1): ['KASUSDT'] — parquet unreadable; checksum matches the EC2 manifest, so the file was corrupt at source (concurrent .tmp rename race). Not admitted; re-collect later if wanted (operator declined further downloads 2026-07-16).

Ledger: `artifacts/admission-ledger.jsonl` (910 rows). Specs: `artifacts/instrument-specs.json`.
