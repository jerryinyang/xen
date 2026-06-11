# TEST-Read Ledger

**Materialized:** 2026-06-11 (Phase 011 D0; backfill verified against experiment
records per Phase 011 design §7.1).
**Governing rules:** `docs/experiments-docs/checkpoints/2026-06-11-011-per-instrument-foundation/design.md` §7.1.

TEST strata are finite. A "new event population" (band change, new exit) does
**not** reset a stratum. This ledger records, per instrument×domain TEST
stratum (TEST = last 30% of the first-70% analysis slice, 1-minute-row
timestamp boundary per R1.3):

- **Counted reads** — any read where the stratum's events enter a binding
  **stratum-specific** inference. Count toward the cap.
- **Disclosures** — exposures without stratum-level selection or
  stratum-specific inference (pre-split full-slice experiments;
  mechanism-science reads with no strategy estimand). Recorded, not counted.

**Hard cap: 2 lifetime counted reads per stratum.** A second read is disclosed
as weakened-evidence. A stratum at cap is permanently capped — no further
stratum-specific claims (treated like the EURUSD holdout).

**Portfolio-aggregate rule:** a portfolio-level read (e.g., Phase 011 Track C
EXP-018) makes no per-stratum claim; it is entered against every member
stratum as a **disclosure**, not a counted read. At-cap strata may contribute
to a portfolio read (with disclosure) but are ineligible for stratum-specific
confirmation reads (e.g., Track D).

**Maintenance:** every binding TEST read and every portfolio/disclosure
exposure must be entered here in the same change that records the experiment
result. Every scope that intends to read a TEST stratum must state that
stratum's current counted-read tally.

## Ledger

Domains: 1h, 2h, 4h (5m retired from primary strategy use, Phase 010/011;
historical 5m exposures noted below the table). "Pre-split disclosure" =
full-analysis-slice exposure in pre-split experiments (EXP-022/028/029/030/034
et al. on the old universe; EXP-040 1h/4h mechanism read).

| TEST stratum | Counted reads | Cap state | Disclosures |
|---|---|---|---|
| EURUSD-1h | 0 | open | pre-split; EXP-040 |
| EURUSD-2h | 0 | open | none |
| EURUSD-4h | **2 — EXP-037 (FH exit), EXP-038 (BTC-exit baseline)** | **AT CAP** | pre-split; EXP-040. EURUSD additionally holdout-contaminated (EXP-032) → TEST-capped instrument-wide. |
| USTEC-1h | 0 | open | pre-split; EXP-040 |
| USTEC-2h | 0 | open | none |
| USTEC-4h | 1 — EXP-037 | open (1 remaining) | pre-split; EXP-040 |
| XAUUSD-1h | 0 | open | pre-split; EXP-040 |
| XAUUSD-2h | 0 | open | none |
| XAUUSD-4h | 1 — EXP-037 | open (1 remaining) | pre-split; EXP-040 |
| BTCUSD-1h | 0 | open | pre-split; EXP-040 |
| BTCUSD-2h | 0 | open | none |
| BTCUSD-4h | 0 | open | pre-split; EXP-040 |
| GBPUSD-{1h,2h,4h} | 0 | open | none |
| USDJPY-{1h,2h,4h} | 0 | open | none |
| USDCHF-{1h,2h,4h} | 0 | open | none |
| USDCAD-{1h,2h,4h} | 0 | open | none |
| AUDUSD-{1h,2h,4h} | 0 | open | none |
| NZDUSD-{1h,2h,4h} | 0 | open | none |
| EURJPY-{1h,2h,4h} | 0 | open | none |
| GBPJPY-{1h,2h,4h} | 0 | open | none |
| AUDJPY-{1h,2h,4h} | 0 | open | none |
| US500-{1h,2h,4h} | 0 | open | none |
| US2000-{1h,2h,4h} | 0 | open | none |
| DE30-{1h,2h,4h} | 0 | open | none (truncated-coverage disclosure applies to any future entry) |
| JP225-{1h,2h,4h} | 0 | open | none |

Notes:

- **EXP-039** was TRAIN-only (provisional EXP-041 slot never used) — no entry.
- **5m strata (old universe):** exposed in pre-split full-slice experiments;
  5m is retired from primary strategy considerations (reserved for future MTF
  execution-layer use). Any future 5m binding read re-opens 5m rows here first.
- **Holdout:** the global holdout (final 30% per instrument) is outside this
  ledger entirely — the single sanctioned holdout shot was SPENT (EXP-032,
  EURUSD-4h, HOLDOUT_INCONCLUSIVE); no holdout read exists for any package.
