# TEST-Read Ledger

**Active ledger:** **INFR-003 5-year dataset** (re-materialized 2026-06-21 on VAL-005
PASS). The new 16-instrument × {15m, 1h, 4h} strata below **govern Phase 018
(CF-CAPGEO-001)**. The pre-INFR-003 (old-dataset) ledger is **retained as historical
record** in the "Archived" section further down and does **not** govern new-dataset reads.
**Originally materialized:** 2026-06-11 (Phase 011 D0; backfill verified against experiment
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

## Active Ledger — INFR-003 5-Year Dataset (governs Phase 018 / CF-CAPGEO-001)

**Re-materialized 2026-06-21 on VAL-005 PASS** (INFR-003 design §4.3). The 5-year
re-collection shifted every chronological 70/30 boundary, so a new-dataset stratum is a
**new stratum population**: every instrument×domain stratum starts at **0 counted reads**.
Domains tracked = CF-CAPGEO-001's **{15m, 1h, 4h}** (15m/30m/5m/2h constructible but out
of CF-CAPGEO-001 scope; materialize on first use). Universe = **16 instruments** (DE30
dropped at INFR-003 ratification — broker m1 stale). TEST stratum = last 30% of the
first-70% analysis slice on each new file's own 2021-06 → 2026-06-21 timeline (1-minute-row
timestamp boundary, R1.3).

**EURUSD — RESOLVED at Phase 018 D0 (2026-06-21): FULLY ELIGIBLE, clean slate.**
EURUSD was TEST-capped instrument-wide on the **old** dataset (holdout-contaminated via
EXP-032, EURUSD-4h). That contamination is on disjoint old-dataset rows and **does not
transfer** to the new dataset (INFR-003 §4.3). Per the Phase 018 D0 operator decision (D8),
EURUSD new-dataset strata are **fully eligible** for stratum-specific counted TEST reads, on
the same footing as every other instrument — **no carried disclosure** (EXP-032 is old enough,
and the methodology has evolved enough, to carry no weight on the new dataset).

| TEST stratum (new dataset) | Counted reads | Cap state | Disclosures |
|---|---|---|---|
| EURUSD-{15m,1h,4h} | 0 | open | none (new dataset) |
| GBPUSD-{15m,1h,4h} | 0 | open | none (new dataset) |
| USDJPY-{15m,1h,4h} | 0 | open | none (new dataset) |
| USDCHF-{15m,1h,4h} | 0 | open | none (new dataset) |
| USDCAD-{15m,1h,4h} | 0 | open | none (new dataset) |
| AUDUSD-{15m,1h,4h} | 0 | open | none (new dataset) |
| NZDUSD-{15m,1h,4h} | 0 | open | none (new dataset) |
| EURJPY-{15m,1h,4h} | 0 | open | none (new dataset) |
| GBPJPY-{15m,1h,4h} | 0 | open | none (new dataset) |
| AUDJPY-{15m,1h,4h} | 0 | open | none (new dataset) |
| XAUUSD-{15m,1h,4h} | 0 | open | none (new dataset) |
| BTCUSD-{15m,1h,4h} | 0 | open | none (new dataset) |
| USTEC-{15m,1h,4h} | 0 | open | none (new dataset) |
| US500-{15m,1h,4h} | 0 | open | none (new dataset) |
| US2000-{15m,1h,4h} | 0 | open | none (new dataset) |
| JP225-{15m,1h,4h} | 0 | open | none (new dataset) |

**DE30:** not in the new dataset (dropped at INFR-003 §3.1); no new-dataset strata. Its
old-dataset rows below are archived history.

**EXP-080 readiness disclosure (2026-06-22, CF-CAPGEO-001 Phase 018 HYP-001).** EXP-080 read the
**full first-70% analysis slice** of all 16×{15m,1h,4h} new-dataset strata for substrate readiness,
determinism, look-ahead invariants, and coverage (the D7 `[15,8000]` bracket + the null-FPR machinery
sanity) — **no strategy estimand, no stratum-specific selection or inference**. Per the readiness
convention (EXP-043/048 precedent) this is a **disclosure, not a counted read**: all 48 strata remain
**0 counted reads / open** (tallies above unchanged). Coverage outcome: **US500-4h and JP225-4h are
`COVERAGE_EXCLUDED`** (4h coverage sparsity) and are excluded from the EXP-081 member set with record;
the other 46 instrument×domain cells are READY. Holdout never read.

**EXP-081 characterization disclosure (2026-06-22, CF-CAPGEO-001 Phase 018 HYP-002).** EXP-081 read the
**TRAIN sub-split only** (`[0, int(analysis_rows*0.7))` = first 70% of each instrument's analysis slice =
first 49% of the full file) of the 46-cell member set for per-substrate realized return-structure
characterization (the frozen D3 inputs). It computed **only TRAIN-only descriptive geometry — no exit, no
strategy estimand, no stratum-specific selection or inference**; the next-21% analysis-TEST stratum and the
final-30% holdout were never sliced or materialized (forward path resolution clips at the TRAIN edge). Per
the TRAIN-only convention (EXP-074/075/080 precedent) this is a **disclosure, not a counted read**: all 48
strata remain **0 counted reads / open** (tallies above unchanged). Holdout never read.

**EXP-082 derivation disclosure (2026-06-22, CF-CAPGEO-001 Phase 018 HYP-003).** EXP-082 read **no market
data at all** — it consumed only EXP-081's already-computed per-cell TRAIN summary
(`EXP-081/results/substrate_cell_summary.parquet`, itself the TRAIN-only disclosure above) and applied the
frozen D0 §D3 mechanical rule to emit 552 triple-barrier exit *definitions* (no exit applied, no return /
P&L / strategy estimand, no stratum-specific selection or inference). No `data/timebars/` read, no TEST
stratum sliced, holdout never touched (`holdout_untouched=true`, `counted_test_reads=0` in
`run_metadata.json`). Per the derivation-off-TRAIN-only-inputs convention (EXP-074/075/081 precedent) this
is a **disclosure, not a counted read**: all 48 strata remain **0 counted reads / open** (tallies above
unchanged). Holdout never read.

**EXP-083 TRAIN-screen disclosure (2026-06-22, CF-CAPGEO-001 Phase 018 HYP-004a).** EXP-083 applied the 3
derived + full benchmark exit grid to the frozen-substrate held positions on the **TRAIN sub-split only**
(`[0, int(analysis_rows·0.7))` = first 49% of each file), ran the G-018a gross screen + the binding
separability gate (S1 ∧ S2), and emitted a hash-pinned valid-candidate set (sha256 `fa4035f3…`) as the
EXP-084 hand-off. It read **no TEST stratum and no holdout** (`test_stratum_touched=false`,
`holdout_untouched=true`, `counted_test_reads=0` in `run_metadata.json`; forward-path resolution clips at
the TRAIN edge). Verdict `SCREEN_DELIVERED` (TRAIN-only eligibility — NOT an edge claim); the **counted-read
`WF-EXPANDING` confirmation is the deferred reserved-conditional EXP-084**, which spends read #1 only on
operator ratification. Per the TRAIN-only convention (EXP-074/075/080/081/082 precedent) this is a
**disclosure, not a counted read**: all 48 strata remain **0 counted reads / open** (tallies above
unchanged). Note: the two entry-identical harami substrates were screened as one stratum (`SUB-HARAMI-V2A`,
audit C1 fix) — no effect on TEST-read accounting (TRAIN-only). Holdout never read.

**EXP-085 cost-read-gate disclosure (2026-06-22, CF-CAPGEO-001 Phase 018 HYP-004 cost read-gate).** EXP-085
applied a predeclared conservative round-trip + holding-time financing model (operator-ratified Stage 4) to
the realized exit paths of the 26 EXP-083 hash-pinned survivors on the **TRAIN sub-split only**
(`[0, int(analysis_rows·0.7))`), re-evaluating **net** per-event expectancy + median per stratum. It read
**no TEST stratum and no holdout** (`test_stratum_touched=false`, `holdout_untouched=true`,
`counted_test_reads=0` in `run_metadata.json`; the survivor exit paths were re-resolved from the same
TRAIN region and reconciled to EXP-083 to 1e-9). Verdict `NET_SURVIVES` (21/26 NET_POS), but **per-stratum
masked** — all 21 NET_POS are S2-DEFERRED low-n 4h `SUB-AVWAP` cells; the only S2-PASS well-powered stratum
(AUDUSD-1h, n=988) is NET_INCONCLUSIVE. It is a **read-gate input to G-018 and authorizes nothing** (an
EXP-084 counted read opens only on operator ratification at EXP-084's D0). Per the TRAIN-only convention
(EXP-074/075/080/081/082/083 precedent) this is a **disclosure, not a counted read**: all 48 strata remain
**0 counted reads / open** (tallies above unchanged).

**EXP-084 portfolio-aggregate disclosure (2026-06-22, CF-CAPGEO-001 Phase 018 HYP-004b confirmation read).**
EXP-084 was the single sanctioned out-of-sample confirmation read for HYP-004, reframed by D0-amendment-003
(operator-ratified) to a **portfolio** unit: `SUB-AVWAP` 4h events pooled across **NZDUSD-4h + USDCAD-4h +
USTEC-4h**, exited by the pinned parameter-free `AVWAP-FH`, NET of the EXP-085 cost model, adjudicated by one
frozen `WF-EXPANDING` run (which reached the analysis-TEST stratum of the pooled series, [50%,100%] of the
analysis set) + the D4 G-018 conjunction. The read makes a **portfolio claim only** (no per-stratum or per-arm
binding inference), so per the **portfolio-aggregate rule** (Phase 011 Track-C EXP-018 precedent; this file's
rule above) it is entered as a **disclosure** against each of the three member strata, **not a counted read**:
**NZDUSD-4h, USDCAD-4h, USTEC-4h tallies stay 0/2 and all 48 strata remain 0 counted reads / open.** The three
strata become **disclosed** (basket-claim-only; a future *clean* per-instrument counted read on them is
permanently mildly weakened, EXP-032 precedent). Verdict **`NOT_CONFIRM`** (basket separates on TRAIN — S2
finally adjudicated at pooled n=152 and passes — but all three economic OOS legs fail; the apparent edge was
selection-region overlap and reverses in the genuinely held-back folds). **HYP-004 closes at G-018.** The
**final-30% global holdout was never built, sliced, or folded** (`holdout_untouched=true`,
`counted_test_reads=0` in `run_metadata.json`; the WF caller passes only the in-analysis series). Holdout
**not** released.

**EXP-086 Screen-M availability disclosure (2026-06-22, Phase 019 Family-Selection, axis M,
CF-VOLEXP-001/HYP-001).** EXP-086 read the **TRAIN sub-split only**
(`[0, int(int(total_rows·0.7)·0.7))` = first 70% of the analysis set = first 49% of each file) of the 46-cell
EXP-080-READY member set for a family-agnostic single-series **magnitude availability** screen (two compression
primitives — raw HA-harami inside-bar + real-OHLC NR7 — vs the matched `SUB-RANDOM` control and the D2b
permuted-axis admission gate). It computed **only TRAIN-only Δ-over-random availability statistics — no exit, no
strategy estimand, no stratum-specific selection or inference**; the per-cell beats-random tests aggregate to an
**axis-level** statistic and the binding admit/exonerate is the terminal G-019 gate, not any per-stratum claim.
The next-21% analysis-TEST stratum and the final-30% holdout were never sliced or materialized (forward path
resolution clips at the TRAIN edge; `holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0` in
`run_metadata.json`). Per the TRAIN-only / availability-disclosure convention (EXP-074/075/080/081/082/083/085
precedent) this is a **disclosure, not a counted read**: all 48 strata remain **0 counted reads / open** (tallies
above unchanged). Verdict `SCREEN_DELIVERED` + provisional `ADMITTED` (NON-BINDING). Holdout never read.

**EXP-087 Screen-X availability disclosure (2026-06-22, Phase 019 Family-Selection, axis X,
CF-XSECT-001/HYP-001).** EXP-087 read the **TRAIN sub-split only**
(`[0, int(int(total_rows·0.7)·0.7))` = first 70% of the analysis set = first 49% of each file) of the 46-cell
EXP-080-READY member set for a family-agnostic **cross-sectional relative-strength directional-favourable
availability** screen (two conditioning primitives — trailing-20-bar-return rank `COND-XSRANK` + divergence-
from-equal-weight-basket `COND-XSDIV` — over a causal forward-filled union grid across the 16 instruments, vs
the matched `SUB-RANDOM` control and the D2b permuted-axis admission gate). It computed **only TRAIN-only
Δ-over-random availability statistics — no exit, no strategy estimand, no stratum-specific selection or
inference**; the per-cell beats-random tests aggregate to an **axis-level** statistic and the binding
admit/exonerate is the terminal G-019 gate, not any per-stratum claim. The cross-section's union grid is built
from TRAIN-only domain-bar `CloseTime`s; the forward-fill consults no TEST/holdout bar; the next-21%
analysis-TEST stratum and the final-30% holdout were never sliced or materialized (forward path resolution
clips at the TRAIN edge; `holdout_untouched=true`, `causal_fill_ok=true`, `counted_test_reads=0`,
`candidate_slots=0` in `run_metadata.json`). Per the TRAIN-only / availability-disclosure convention
(EXP-074/075/080/081/082/083/085/086 precedent) this is a **disclosure, not a counted read**: all 48 strata
remain **0 counted reads / open** (tallies above unchanged). Verdict `SCREEN_DELIVERED` + provisional
`NOT_ADMITTED` (NON-BINDING, below D2a band). Holdout never read.

**EXP-089 mean-reversion availability disclosure (2026-06-23, Phase 020, CF-MR-001/HYP-001; amended
`D0-amendment-001`).** EXP-089 read the **TRAIN sub-split only** (`[0, int(int(total_rows·0.7)·0.7))` = first
70% of the analysis set = first 49% of each file) of the 46-cell EXP-080-READY member set for the CF-MR-001
RSI-2 mean-reversion **favourable-excursion availability** screen (6 single-test sub-screens — `CORE`,
`CORE-VOL-{LOW,MED,HIGH}`, `CORE+TREND`, `CORE+FILTER` — over a causal MR-tempo cap, leg-1 Δ-over-random vs a
matched `SUB-RANDOM` control, regime-matched for the `/VOLREGIME` sub-screens, and the D2b joint-max
permuted-axis admission gate). It computed **only TRAIN-only Δ-over-random availability statistics — no exit, no
strategy estimand, no stratum-specific selection or inference**; the per-cell beats-random tests aggregate to a
family-level statistic and the binding admit/exonerate is the terminal G-020 gate, not any per-stratum claim.
The MR-tempo cap and forward path use only bars at/after entry within the cap, clipped at the TRAIN edge; the
next-21% analysis-TEST stratum and the final-30% holdout were never sliced or materialized
(`holdout_untouched=true`, `regime_match_recon_ok=true`, `counted_test_reads=0`, `candidate_slots=0` in
`run_metadata.json`). Per the TRAIN-only / availability-disclosure convention
(EXP-074/075/080/081/082/083/085/086/087 precedent) this is a **disclosure, not a counted read**: all 48 strata
remain **0 counted reads / open** (tallies above unchanged). Verdict `SCREEN_DELIVERED`; **G-020 ADMITTED
(BINDING) 2026-06-23** (driver = bare RSI-2 fade, vol-regime inert). **G-020 admission consumed a candidate slot,
NOT a counted TEST read** — all 48 strata stay 0/2 open; holdout never read.

**The global holdout (final 30% per new file) is outside this ledger entirely** and was
sealed at first touch in VAL-005 (0 holdout rows read). No new-dataset holdout shot exists;
the single historical sanctioned shot (EXP-032, old dataset) is spent and non-transferable.

---

## Archived Ledger — OLD (pre-INFR-003) Dataset — HISTORICAL RECORD ONLY

> Retained for closed-family reproducibility (CF-AVWAP-001, CF-HA-HARAMI-001). **Does not
> govern Phase 018 or any new-dataset read.** The tables below reflect the old ~3.3y
> dataset strata as of 2026-06-19.

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
| GBPUSD-1h | **1 — EXP-071 (HYP-024, N-PARTIAL-V2A)** | open (1 remaining) | EXP-071 portfolio composite (disclosure) |
| GBPUSD-{2h,4h} | 0 | open | none |
| USDJPY-{1h,2h,4h} | 0 | open | none |
| USDCHF-{1h,2h,4h} | 0 | open | none |
| USDCAD-{1h,2h,4h} | 0 | open | none |
| AUDUSD-{1h,2h,4h} | 0 | open | none |
| NZDUSD-1h | **1 — EXP-071 (HYP-024, N-PARTIAL-V2A)** | open (1 remaining) | EXP-071 portfolio composite (disclosure) |
| NZDUSD-2h | **1 — EXP-071 (HYP-024, N-PARTIAL-V2A)** | open (1 remaining) | EXP-071 portfolio composite (disclosure) |
| NZDUSD-4h | 0 | open | none |
| EURJPY-{1h,2h,4h} | 0 | open | none |
| GBPJPY-{1h,2h,4h} | 0 | open | none |
| AUDJPY-{1h,2h,4h} | 0 | open | none |
| US500-{1h,2h,4h} | 0 | open | none |
| US2000-1h | 0 | open | none |
| US2000-2h | 0 | open | none |
| US2000-4h | **1 — EXP-071 (HYP-024, N-PARTIAL-V2A)** | open (1 remaining) | EXP-071 portfolio composite (disclosure) |
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
| GBPUSD-5m | **1 — EXP-071 (HYP-024, N-PARTIAL-V2A)** | open (1 remaining) | EXP-071 portfolio composite (disclosure) |
| GBPUSD-{15m,30m} | 0 | open | none (first materialization) |
| USDJPY-{5m,15m,30m} | 0 | open | none (first materialization) |
| USDCHF-{5m,15m,30m} | 0 | open | none (first materialization) |
| USDCAD-{5m,15m,30m} | 0 | open | none (first materialization) |
| AUDUSD-{5m,15m,30m} | 0 | open | none (first materialization) |
| NZDUSD-{5m,15m,30m} | 0 | open | none (first materialization) |
| EURJPY-{5m,15m,30m} | 0 | open | none (first materialization) |
| GBPJPY-30m | **1 — EXP-071 (HYP-024, N-PARTIAL-V2A)** | open (1 remaining) | EXP-071 portfolio composite (disclosure) |
| GBPJPY-{5m,15m} | 0 | open | none (first materialization) |
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
- **EXP-071 (2026-06-19, HYP-024) — first counted TEST reads in the harami family.** Six
  counted reads, one per binding stratum (GBPUSD-5m, GBPUSD-1h, NZDUSD-1h, NZDUSD-2h,
  GBPJPY-30m, US2000-4h); each stratum now at **1/2** lifetime counted reads, all still open.
  Verdict TEST_NOT_CONFIRMED. The EXP-071 equal-weight **portfolio composite** is entered as a
  **disclosure** against all 6 strata (per the portfolio-aggregate rule), not a counted read.
  EURUSD strata were excluded (TEST-capped instrument-wide); they recorded no read.
- **EXP-074 (2026-06-19, HYP-027) — TRAIN-only diagnostic, NO counted reads.** The
  99-cell MA-native loss-tail characterization read the **TRAIN stratum only**
  (`[0, train_cutoff)`); the next-21% TEST stratum and the final-30% holdout were never
  sliced or materialized (forward resolution clips at the TRAIN edge). **0 counted TEST
  reads spent; this ledger is unchanged by EXP-074.** No stratum tally moves.
- **EXP-075 (2026-06-19, HYP-028) — TRAIN-only design, NO counted reads.** The exhaustion-cap
  TRAIN-design-and-lock read the **TRAIN stratum only** (`[0, train_cutoff)`); the cap is an
  entry-time boolean subset that only removes entries (never reaches forward), and the next-21% TEST
  stratum + final-30% holdout were never sliced or materialized. Verdict FILTER_INEFFECTIVE; the
  locked filter is frozen but NON-CONFIRMATORY and carried nowhere — no holdout read warranted.
  **0 counted TEST reads spent; this ledger is unchanged by EXP-075.** No stratum tally moves.
- **EXP-077 (2026-06-20, `ASS/VAL-002`, Phase 017) — methodology validation, NO counted reads.** The
  binding FPR/MDE/reliability/accounting legs ran on **synthetic** populations (no market data); the
  real-bar dogfood read the **first-49% TRAIN region only** (`train_cutoff = int(int(total·0.7)·0.7)`,
  read fraction 0.4900, asserted in code), so the next-21% TEST stratum and the final-30% holdout were
  never sliced or materialized. The `WF-EXPANDING` per-fold counted-read accounting **rule** was
  validated as a function (cap honored, 8/8 scenarios) but **not exercised against any live stratum**.
  **0 counted TEST reads spent; this ledger is unchanged by EXP-077.** No stratum tally moves.
- **Holdout:** the global holdout (final 30% per instrument) is outside this
  ledger entirely — the single sanctioned holdout shot was SPENT (EXP-032,
  EURUSD-4h, HOLDOUT_INCONCLUSIVE); no holdout read exists for any package.
