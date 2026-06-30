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
| EURUSD-15m | 0 | open | none (new dataset) |
| EURUSD-1h | **1 — EXP-093 (HYP-002, EXIT-RCT)** | open (1 remaining) | EXP-093 TEST CONFIRM-class read (EVIDENCE_AGAINST: net-negative OOS) |
| EURUSD-4h | **1 — EXP-093 (HYP-002, EXIT-RCT)** | open (1 remaining) | EXP-093 TEST CONFIRM (robust core, mean-AND-median +) |
| GBPUSD-15m | 0 | open | none (new dataset) |
| GBPUSD-1h | **1 — EXP-093 (HYP-002, EXIT-RCT)** | open (1 remaining) | EXP-093 TEST read (EVIDENCE_AGAINST: net-negative OOS; pre-disqualified `D0-amendment-006 §2`) |
| GBPUSD-4h | 0 | open | none (new dataset) |
| USDJPY-{15m,1h,4h} | 0 | open | none (new dataset) |
| USDCHF-15m | 0 | open | none (new dataset) |
| USDCHF-1h | 0 | open | none (new dataset) |
| USDCHF-4h | **1 — EXP-093 (HYP-002, EXIT-RCT)** | open (1 remaining) | EXP-093 TEST CONFIRM (robust core, mean-AND-median +) |
| USDCAD-{15m,1h,4h} | 0 | open | none (new dataset) |
| AUDUSD-{15m,1h,4h} | 0 | open | none (new dataset) |
| NZDUSD-15m | 0 | open | none (new dataset) |
| NZDUSD-1h | **1 — EXP-093 (HYP-002, EXIT-RCT)** | open (1 remaining) | EXP-093 TEST read (INCONCLUSIVE: near-zero OOS) |
| NZDUSD-4h | 0 | open | none (new dataset) |
| EURJPY-15m | 0 | open | none (new dataset) |
| EURJPY-1h | 0 | open | none (new dataset) |
| EURJPY-4h | **1 — EXP-093 (HYP-002, EXIT-RCT)** | open (1 remaining) | EXP-093 TEST CONFIRM (robust core, mean-AND-median +) |
| GBPJPY-15m | 0 | open | none (new dataset) |
| GBPJPY-1h | 0 | open | none (new dataset) |
| GBPJPY-4h | **1 — EXP-093 (HYP-002, EXIT-RCT)** | open (1 remaining) | EXP-093 TEST CONFIRM (robust core, mean-AND-median +) |
| AUDJPY-15m | 0 | open | none (new dataset) |
| AUDJPY-1h | 0 | open | none (new dataset) |
| AUDJPY-4h | **1 — EXP-093 (HYP-002, EXIT-RCT)** | open (1 remaining) | EXP-093 TEST CONFIRM (robust core, mean-AND-median +) |
| XAUUSD-15m | 0 | open | none (new dataset) |
| XAUUSD-1h | 0 | open | none (new dataset) |
| XAUUSD-4h | **1 — EXP-093 (HYP-002, EXIT-RCT)** | open (1 remaining) | EXP-093 TEST CONFIRM (robust core, mean-AND-median +) |
| BTCUSD-{15m,1h,4h} | 0 | open | none (new dataset) |
| USTEC-15m | 0 | open | none (new dataset) |
| USTEC-1h | **1 — EXP-093 (HYP-002, EXIT-RCT)** | open (1 remaining) | EXP-093 TEST CONFIRM (mean-carried; TEST median −0.026) |
| USTEC-4h | 0 | open | none (new dataset) |
| US500-{15m,1h,4h} | 0 | open | none (new dataset) |
| US2000-15m | 0 | open | none (new dataset) |
| US2000-1h | **1 — EXP-093 (HYP-002, EXIT-RCT)** | open (1 remaining) | EXP-093 TEST CONFIRM (mean-carried; TEST median ≈ 0) |
| US2000-4h | 0 | open | none (new dataset) |
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

**EXP-090 exit-substrate readiness & calibration disclosure (2026-06-24, Phase 021, CF-MR-001/HYP-002; amended
`D0-amendment-002`).** EXP-090 read the **TRAIN sub-split only** (`[0, int(int(total_rows·0.7)·0.7))` = first 49%
of each file) of the 32-cell member set (16 × {15m,1h}) to establish exit-substrate readiness (bare-fade entries
+ the new 1-minute intrabar fill engine `xen.intrabar_fill` resolving five frozen exit arms — deterministic,
timestamp-aligned, causal, fenced, real fill prices) and the per-cell inference calibration of the binding mean
net-expectancy moving-block bootstrap lower bound (FPR / event-level MDE). It computed **only readiness records,
raw per-cell event counts, and a synthetic null/planted-edge estimator calibration — no exit screened, no net or
gross strategy expectancy, no stratum-specific selection or inference**; the **real CORE fade outcomes were never
resolved or read** (`real_fade_outcomes_resolved=false` — the calibration used matched-random-entry exit-resolved
returns only, the EXP-044 anti-overfitting fence). The 1-minute fill walk uses only bars at/after entry within
the cap, clipped at the TRAIN edge; the next-21% analysis-TEST stratum and the final-30% holdout were never
sliced or materialized (`holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0` in
`run_metadata.json`). Per the TRAIN-only / readiness-disclosure convention
(EXP-074/075/080/081/082/083/085/086/087/089 precedent) this is a **disclosure, not a counted read**: all 48
strata remain **0 counted reads / open** (tallies above unchanged). Verdict `READINESS_CALIBRATION_DELIVERED`
(20 MEMBER / 12 COVERAGE_EXCLUDED); the carried per-cell MDEs are the EXP-093 margins. No counted read is spent
until the one-shot EXP-093 TEST.

**EXP-091 exit/capture-geometry screen disclosure (2026-06-24, Phase 021, CF-MR-001/HYP-002; `D0-amendment-003`
cost).** EXP-091 read the **TRAIN sub-split only** of the 20 EXP-090 member cells (16×{15m,1h}) to screen the
frozen exit slate net of the Phase-021 conservative cost (`SCREEN_DELIVERED`, non-empty: EXIT-RCT passes 5/5, 1h).
No analysis-TEST or holdout slice; per the TRAIN-only convention this is a **disclosure, not a counted read** — all
48 strata remain **0 counted reads / open**; `holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`.

**EXP-094 4h readiness + falsification re-screen disclosure (2026-06-24, Phase 021, CF-MR-001/HYP-002;
`D0-amendment-004` opens 4h + `D0-amendment-005` corrects the binding null).** EXP-094 read the **TRAIN sub-split
only** of the 13 cost-table instruments × **4h** to (a) establish 4h member readiness + per-cell EXIT-RCT MDE
(EXP-090 analog → 6 MEMBER / 7 COVERAGE_EXCLUDED), (b) run the frozen net exit screen on the members, and (c)
falsify the 4h edge against a **matched favourable-target-distance oscillation null** (real vs random-time limit;
binding) + a realized-capture sensitivity + SUB-RANDOM companion + a 1h positive control. Verdict **`ADMIT_4H`**
(real beats both binding and sensitivity nulls 6/6; bite-check GREEN). It computed readiness records, screen/net
expectancy, and the falsification paired-Δ on the **TRAIN region only**; the next-21% analysis-TEST stratum and the
final-30% holdout were never sliced (`holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`). Per
the TRAIN-only convention this is a **disclosure, not a counted read**: all 48 strata — **including the six powered
4h strata now admitted (AUDJPY/EURJPY/EURUSD/GBPJPY/USDCHF/XAUUSD-4h)** — remain **0 counted reads / open (0/2)**.
The 4h admission opens these strata for the EXP-092 sequence; the first counted 4h read (if any) is spent only at
the one-shot EXP-093 TEST.

**EXP-092 per-instrument cost-bearing sequence disclosure (2026-06-24, Phase 021, CF-MR-001/HYP-002).** EXP-092
read the **TRAIN sub-split only** of EXIT-RCT's 11 carried cells (5×1h EXP-091 survivors + 6×4h EXP-094 members)
to re-derive the binding net per-event-expectancy lower bound, certify each cell's `SEQUENCE_PASS`, and emit the
**hash-pinned candidate set (sha256 `f6427e83…`) + sized phase Holm rule** for EXP-093 (`SEQUENCE_DELIVERED`,
11/11 PASS). It computed only TRAIN net expectancy + the sequence/hash-pin/margin-preread — **no analysis-TEST or
holdout slice, no stratum-specific TEST inference** (the binding TEST read is the deferred EXP-093). Per the
TRAIN-only convention (EXP-090/091/094 precedent) this is a **disclosure, not a counted read**:
`holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`; **all 48 strata — including the 11 carried
(EURUSD/GBPUSD/NZDUSD/US2000/USTEC-1h + AUDJPY/EURJPY/EURUSD/GBPJPY/USDCHF/XAUUSD-4h) — remain 0 counted reads /
open (0/2).** The first counted read is spent only at the one-shot EXP-093 TEST (≤1/carried-stratum; EURUSD-1h
and EURUSD-4h are distinct strata).

**EXP-093 one-shot TEST confirmation — FIRST COUNTED TEST READS on the new dataset (2026-06-24, Phase 021,
CF-MR-001/HYP-002; carried set per `D0-amendment-006`).** EXP-093 resolved the real bare-fade EXIT-RCT exits on
the **analysis-TEST stratum** (`[int(int(total·0.7)·0.7), int(total·0.7))` = last 30% of the first-70% analysis
set; 1-minute-row timestamp boundary R1.3) of the **11 carried strata** and ran the binding per-cell inference
(moving-block net `ci_low_1s` + one-sided bootstrap p → phase Holm-11 → D6/4c adjudication). This is a
**stratum-specific binding inference** on each of the 11 strata ⇒ **11 counted TEST reads, one per stratum, each
0→1** (cap 2/stratum; one read preserved per stratum). Strata: **EURUSD-1h, GBPUSD-1h, NZDUSD-1h, US2000-1h,
USTEC-1h, AUDJPY-4h, EURJPY-4h, EURUSD-4h, GBPJPY-4h, USDCHF-4h, XAUUSD-4h** (tallies above updated to 1/2;
EURUSD-1h and EURUSD-4h are distinct strata). The TRAIN region was loaded only as causal indicator warmup (no
TRAIN entry entered the binding estimand); the 1-minute fill walk clipped at the analysis edge by timestamp.
**The final-30% global holdout was never loaded, sliced, or materialized** (`holdout_untouched=true`,
`counted_test_reads=11`, `candidate_slots=0` in `run_metadata.json`; ~561k holdout rows per file confirmed not
read). Verdict **`TEST_CONFIRMED`** — 8/11 CONFIRM (six 4h mean-AND-median-positive robust core + USTEC-1h/
US2000-1h mean-carried), GBPUSD-1h/EURUSD-1h EVIDENCE_AGAINST, NZDUSD-1h INCONCLUSIVE → routes G-021 TRADABLE.
The other 37 strata stay 0/2. Audit PASS. This is the first time any CF-MR-001 stratum has spent a counted read.

**Phase 022 read plan (CF-MR-001 batch 3 — portfolio / noise / global-holdout; G0 RATIFIED 2026-06-24).**
EXP-095 (portfolio construction) and EXP-096 (noise infusion) build a deployment portfolio from the **8
G-021-confirmed cells** (all within the EXP-093 carried 11) by **re-combining the EXP-093 already-resolved
analysis-TEST per-cell series** (EXP-096 additionally re-resolves only the *entry-fill leg* under a perturbed
1-minute fill model — same cells, same selection, no new stratum-specific inference). Per the
**portfolio-aggregate rule** + the cost-re-resolution precedent (EXP-085), both are **disclosures, not counted
reads**: **all 48 strata are unchanged — the 11 carried strata stay 1/2, the other 37 stay 0/2**;
`counted_test_reads=0`, `candidate_slots=0`, `holdout_untouched=true` in both `run_metadata.json`. **EXP-097 is
the single sanctioned final-30% global-holdout release** (the deployment OOS-final), gated behind the G-022a
pre-holdout freeze — it is **outside this ledger entirely** (see the global-holdout note below) and recorded as
a holdout-governance event in the same change that records its result.

**EXP-095 portfolio-construction disclosure (2026-06-24, Phase 022, CF-MR-001/HYP-003) — COMPLETE, tally
unchanged.** EXP-095 built the causal ERC portfolio (A static / B circuit-breaker) of the 8 G-021-confirmed cells
by **re-combining the EXP-093 already-resolved analysis-TEST per-cell series** (regenerated byte-equivalently
through the frozen EXP-090/092 substrate; provenance reconciled to EXP-093 at abs-diff 0.0 on all 8 cells) plus
the TRAIN region, on the **analysis set only**. It makes a **portfolio-aggregate claim** (no new per-stratum
selection or stratum-specific inference — the binding per-stratum reads were spent at EXP-093) and the
final-30% global holdout was never loaded (`holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`
in `run_metadata.json`). Per the portfolio-aggregate rule + the cost-re-resolution precedent (EXP-084/085), this
is a **disclosure, not a counted read**: **all 48 strata unchanged — the 11 carried strata stay 1/2, the other 37
stay 0/2.** Verdict (analysis-set, no holdout verdict; **corrected at the D0-amendment-001 amend-in-place rerun
2026-06-25**, re-audit PASS): the rerun restored the D0 §D2.1 intra-1h mark-to-market (the prior flat-at-exit
booking was a verdict-material defect) → **portfolio benefit SUPPORTED** (A Sharpe LB 10.24 clears every baseline;
genuine diversification of 8 low-correlation cells); **ERC ≈ naive-IV** (prior refutation overturned);
**circuit-breaker NEUTRAL** (A ≈ B within noise; no material de-risking — prior "de-risks −22.4%" was a
flat-at-exit artifact); the NEW portfolio-level
confirmation statistic is **READY** (`statistic_ready_for_g022a=true` — FPR controlled, MDE m*=1.75/2.00 finite and
cleared by the realized edge; G-022a must freeze the band ≥ m*). Disclosure status and tally are unchanged by the
correction (still 0 counted reads; 11 carried strata stay 1/2). The first counted holdout shot remains the gated
**EXP-097** global-holdout release.

**EXP-096 noise-infusion disclosure (2026-06-25, Phase 022, CF-MR-001/HYP-003) — COMPLETE, tally unchanged.**
EXP-096 re-derived the deployment portfolio under a realistic 1-minute **entry-fill** model (v1/v2-binding/v3) — a
**pure entry-leg perturbation** of the EXP-095 construction: only the entry execution price changes, while the
EXIT-RCT exit path, adverse stop, cost, and the resolved-event **keep mask are reused verbatim from EXP-093**
(provenance reconciled abs-diff 0.0 on all 8 cells; `n_entry_unavailable_on_keep=0`). It re-resolves the entry leg
of the **same 8 cells on the same EXP-093 analysis-TEST series under a perturbed execution model — same cells, same
selection, no new stratum-specific inference** — and makes a **portfolio-aggregate claim** only. Per the
**portfolio-aggregate rule + the cost-re-resolution precedent (EXP-084/085)** this is a **disclosure, not a counted
read**: **all 48 strata unchanged — the 11 carried strata stay 1/2, the other 37 stay 0/2.** The final-30% global
holdout (incl. 1-minute bars) was never loaded (`holdout_untouched=true`, `counted_test_reads=0`,
`candidate_slots=0` in `run_metadata.json`; max-touched `CloseTime` < the analysis edge). Verdict (analysis-set, no
holdout verdict): the fill-realism leg **SURVIVES** at the binding v2 (portfolio benefit ADDS_VALUE, broad-based,
v2 A/B Sharpe LB ≥ inherited m*); circuit-breaker NEUTRAL at v2 / tail-protective at v3; EURJPY-4h flagged
NOISE_DEGRADED but retained (G-022a membership input). The first counted holdout shot remains the gated **EXP-097**
global-holdout release.

**EXP-097 GLOBAL-HOLDOUT-GOVERNANCE EVENT — the new-dataset holdout shot is SPENT (2026-06-25, Phase 022,
CF-MR-001/HYP-003).** EXP-097 loaded the **final-30% global holdout for the first time** (per file,
`[int(total·0.7), total)` on each file's 2021-06 → collection-date timeline) and applied the G-022a-frozen rule to
the deployment portfolio. This is the **single sanctioned global-holdout release** (à la EXP-032), recorded here as
a **holdout-governance event — outside the analysis-TEST 48-stratum ledger**. Per the operator decision 2026-06-25,
**reading both Portfolio A and Portfolio B from one holdout materialization is ONE read** (both are weightings of
the same streams from a single materialization; the A-vs-B choice was fixed pre-holdout; the terminal verdict keys
off B only — no OR-multiplicity). **The analysis-TEST ledger is untouched: the 11 carried strata stay 1/2, the
other 37 stay 0/2; `counted_test_reads=0`, `candidate_slots=0` in `run_metadata.json`.** The analysis set was
loaded only as past-only causal warmup (EXP-093 pattern). Verdict **`DEPLOYABLE_CONFIRMED`** (primary B holdout
Sharpe LB 4.762 > band 2.00 AND Calmar LB 10.731 > 0; A co-confirms, no OR rescue). **Non-repeatable,
non-upgradable** — any confound found hereafter is a permanent caveat, not a re-read. Audit PASS (0C/0W/4I).

**CF-MR-001 CLOSED — REFUTED (2026-06-26): the EXP-093 reads and the EXP-097 holdout shot were SPENT-ON-DEFECT
(non-refundable).** An uncaught one-bar look-ahead in the EXIT-RCT favourable limit (`arm_levels` rests
`rct_target[di]` — computed from bar `di`'s own close — as the intrabar limit during bar `di`; the live-actable
limit is `rct_target[di-1]`; `EXP-090/code/run_experiment.py:305-310`, `mean_reversion.py:174`) inflated the
captured edge by ~+0.25 ATR/trade. Causalized, the bare RSI-2 fade + EXIT-RCT is net-negative even gross; exposed
by the cTrader port + forward test (`XRSI-V1/DIAGNOSIS-real-entry-slippage-omission.md`). **Both the 11 EXP-093
counted TEST reads (each carried stratum stays 1/2) and the EXP-097 global-holdout shot remain SPENT** — a defect
discovered after the fact does **not** refund a read or a holdout shot. They are now flagged **spent-on-defect**:
the strata tallies and the spent global-holdout shot are unchanged (the budget consequences stand), but no
CF-MR-001 net-tradable/deployment claim rests on them. **G-021 TRADABLE and G-022 DEPLOYABLE_CONFIRMED are
RETRACTED.** EXP-089/G-020 availability (gross MFE_med, no RCT limit) is unaffected. Full mechanism + scope:
`candidate-families/cf-mr-001.md` §CLOSURE + the Phase 021/022 banners in `multiplicity-registry.md`.

**EXP-006 CF-MR-002 D-benchmark causal-screen disclosure (2026-06-30, Phase 001, CF-MR-002/HYP-001) —
NO counted reads.** EXP-006 ran the causal RSI-2 fade in the cTrader StrategyHost over 17×{1h,4h} and
adjudicated the emissions under three frozen referees on the **first-70% analysis slice only** (the
referee's internal train/test split operates within the analysis set; the final-30% global holdout was
**never loaded** — `AnalysisEndUtc` fence verified 0/34 runs over the cutoff). This is an **honest-prior
causal tradability screen** (admit/exonerate, no binding stratum-specific confirmation estimand), so per
the screen/disclosure convention (EXP-089/094 precedent) it is a **disclosure, not a counted read**:
`counted_test_reads=0`, `candidate_slots=0`, holdout sealed. Verdict **NOT-TRADABLE 34/34 — CF-MR-002
EXONERATED**; the gates were frozen (E5/E6) before this read (L-12 honored). No stratum tally moves
(CF-MR-002 strata are the same INFR-003 instrument×domain populations; none enter a binding inference
here). A future counted read would open only on a TRAIN admit (none occurred).

**The global holdout (final 30% per new file) is outside this ledger entirely** and was
sealed at first touch in VAL-005 (0 holdout rows read). The single historical sanctioned shot (EXP-032, old
dataset) is spent and non-transferable; **the new-dataset holdout shot has now been spent at the gated Phase 022
EXP-097 global-holdout release** (2026-06-25, after the G-022a freeze; one-shot, non-upgradable, non-repeatable, à
la EXP-032) — see the EXP-097 holdout-governance event note above.

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
- **EXP-098 (2026-06-25, `CF-MR-001/HYP-003`, Phase 022 — robustness disclosure, NO counted reads, NO
  holdout shot).** Cross-broker & aggregation-method robustness replication of the G-022a-frozen RSI-2 fade
  deployment portfolio on an **independent broker dataset** (`data/timebars/pps/`, the 8 carry-8 instruments).
  PPS is **outside this ledger entirely** (the 48 strata are defined on the INFR-003 dataset) and **outside the
  INFR-003 global holdout** — which was **NOT loaded** (`infr003_holdout_loaded=false`, asserted in code). Recorded
  here as a **robustness governance disclosure**: `counted_test_reads=0`, `candidate_slots=0`; **no stratum tally
  moves** (the 11 carried CF-MR-001 strata stay 1/2, the other 37 stay 0/2). Outcome `CROSS_BROKER_ROBUST` ∧
  `AGGREGATION_ROBUST` (both arms); EXP-097 `DEPLOYABLE_CONFIRMED` unchanged. **PPS is now "touched" as a
  robustness dataset** — any *future binding* use of PPS (e.g. a sanctioned second-feed holdout) requires its own
  governance and read accounting.
- **Holdout (CF-MR-001 / current 5-year dataset):** the single sanctioned final-30% global-holdout shot was
  **SPENT at EXP-097 (2026-06-25, RSI-2 fade ERC portfolio → `DEPLOYABLE_CONFIRMED`)** as a holdout-governance
  event (non-repeatable, non-upgradable). EXP-098 did **not** load it.
- **Holdout (legacy / old dataset):** the global holdout (final 30% per instrument) is outside this
  ledger entirely — the prior single sanctioned holdout shot was SPENT (EXP-032,
  EURUSD-4h, HOLDOUT_INCONCLUSIVE) on the old dataset; no other holdout read exists for any package.
