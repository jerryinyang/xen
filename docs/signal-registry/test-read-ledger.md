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

Domains: {5m, 15m, 30m, 1h, 2h, 4h}. AVWAP family: 1h/2h/4h only (5m retired from
primary strategy use, Phase 010/011). HA harami family: all 6 domains admitted by VAL-004
(Phase 014); 5m/15m/30m strata formalized here 2026-06-18 at Phase 016 D0 — see "New
Domains" table below. "Pre-split disclosure" = full-analysis-slice exposure in pre-split
experiments (EXP-022/028/029/030/034 et al. on the old universe; EXP-040 1h/4h mechanism
read).

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

## New Domains — Materialized 2026-06-18 (Phase 016 D0)

5m, 15m, and 30m domains admitted by VAL-004 (Phase 014) but never previously entered as
individual TEST strata. Materialized here at Phase 016 D0 before any harami family binding
TEST read in these domains. Old-universe 5m pre-split disclosures (EURUSD/USTEC/XAUUSD/BTCUSD)
from EXP-021/022/028/029/030/031 entered as disclosures, not counted reads. **EURUSD is
TEST-capped instrument-wide** (holdout-contaminated, EXP-032) and ineligible for any harami
stratum-specific TEST confirmation even where the stratum shows 0 counted reads.

| TEST stratum | Counted reads | Cap state | Disclosures |
|---|---|---|---|
| EURUSD-5m | 0 | open (ineligible for harami TEST — instrument-wide TEST-capped) | pre-split (EXP-021/022/028/029/030/031) |
| EURUSD-15m | 0 | open (ineligible for harami TEST — instrument-wide TEST-capped) | none (first materialization) |
| EURUSD-30m | 0 | open (ineligible for harami TEST — instrument-wide TEST-capped) | none (first materialization) |
| USTEC-5m | 0 | open | pre-split (EXP-021/022/028/029/030/031) |
| USTEC-15m | 0 | open | none (first materialization) |
| USTEC-30m | 0 | open | none (first materialization) |
| XAUUSD-5m | 0 | open | pre-split (EXP-021/022/028/029/030/031) |
| XAUUSD-15m | 0 | open | none (first materialization) |
| XAUUSD-30m | 0 | open | none (first materialization) |
| BTCUSD-5m | 0 | open | pre-split (EXP-021/022/028/029/030/031) |
| BTCUSD-15m | 0 | open | none (first materialization) |
| BTCUSD-30m | 0 | open | none (first materialization) |
| GBPUSD-{5m,15m,30m} | 0 | open | none (first materialization) |
| USDJPY-{5m,15m,30m} | 0 | open | none (first materialization) |
| USDCHF-{5m,15m,30m} | 0 | open | none (first materialization) |
| USDCAD-{5m,15m,30m} | 0 | open | none (first materialization) |
| AUDUSD-{5m,15m,30m} | 0 | open | none (first materialization) |
| NZDUSD-{5m,15m,30m} | 0 | open | none (first materialization) |
| EURJPY-{5m,15m,30m} | 0 | open | none (first materialization) |
| GBPJPY-{5m,15m,30m} | 0 | open | none (first materialization) |
| AUDJPY-{5m,15m,30m} | 0 | open | none (first materialization) |
| US500-{5m,15m,30m} | 0 | open | none (first materialization) |
| US2000-{5m,15m,30m} | 0 | open | none (first materialization) |
| DE30-{5m,15m,30m} | 0 | open | none (first materialization; DE30 truncated-coverage disclosure carries forward) |
| JP225-{5m,15m,30m} | 0 | open | none (first materialization) |

Notes:

- **EXP-039** was TRAIN-only (provisional EXP-041 slot never used) — no entry.
- **5m/15m/30m strata:** materialized 2026-06-18 (Phase 016 D0) in the "New Domains" table
  above. Old-universe 5m pre-split disclosures (EXP-021/022/028/029/030/031 on
  EURUSD/USTEC/XAUUSD/BTCUSD) entered as disclosures only, not counted reads. 5m retired
  from primary AVWAP-family strategy use (Phase 010/011) but active in the harami family
  (VAL-004 admitted); these rows are open effective 2026-06-18.
- **Holdout:** the global holdout (final 30% per instrument) is outside this
  ledger entirely — the single sanctioned holdout shot was SPENT (EXP-032,
  EURUSD-4h, HOLDOUT_INCONCLUSIVE); no holdout read exists for any package.
