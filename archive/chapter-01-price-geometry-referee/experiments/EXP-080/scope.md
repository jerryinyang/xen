# Experiment: EXP-080 — Phase 018 Substrate/Exit Readiness (4 Frozen Substrates × 16 × {15m,1h,4h})

**Phase:** 018 (CF-CAPGEO-001 data-derived exit / capture geometry; checkpoint
`2026-06-20-018-capgeo-exit-geometry`, **G0 PASS 2026-06-21**) · **HYP:** HYP-001 ·
**Registry:** `CF-CAPGEO-001` Phase 018 batch (multiplicity-registry) ·
**Candidate slots:** 0 (readiness) · **TEST reads:** 0 counted (readiness/coverage exposure =
disclosure per the ledger; no stratum-specific strategy inference).

**Counted-read precondition (Stage-1 check):** the INFR-003 5-year ledger
(`test-read-ledger.md`, re-materialized 2026-06-21 on VAL-005 PASS) shows **all 16 instruments ×
{15m,1h,4h} = 48 strata at 0/2 counted reads, open** (EURUSD fully eligible, clean slate — D8).
EXP-080 spends **0 counted reads**: it computes only readiness, determinism, look-ahead invariants,
and raw per-cell event counts (the D7 bracket) — no strategy estimand, no stratum-specific selection
or inference — so its analysis-set exposure is a **disclosure**, entered against each stratum at
completion (Stage 7).

**Analog:** EXP-020 / EXP-043 / EXP-048 substrate-readiness pattern (determinism + causality +
coverage map; no edge/return/capture/P&L). **Gating precondition:** **VAL-005 PASS 2026-06-21** —
the 5-year 1-minute dataset on 16 instruments admitted on all 5 gates (temporal integrity 369/369,
holdout re-sealed 0 rows read); `build_domain_bars` holdout fence ratified (VAL-005 G1). All 48
instrument×domain cells are domain-eligible at scope time.

**Context:** First experiment of Phase 018. Validates the **four frozen entry substrates** — the
closed axis of CF-CAPGEO-001 — can each be reproduced **deterministically**, **look-ahead-safe**,
and with **adequate per-cell coverage** on the *new* 5-year data, before any return-structure
characterization (EXP-081), exit derivation (EXP-082), or screening (EXP-083). **No exit is applied
here** (exits are EXP-082/083); EXP-080 produces only the frozen-entry event populations and their
readiness/coverage map. **No edge, return, capture, expectancy, or P&L metric is computed.**

## Hypothesis

Exploratory readiness question (no market-edge claim): for every one of the **192 substrate-cells**
(4 substrates × 16 instruments × {15m, 1h, 4h}), the frozen entry detector can be computed
**deterministically**, **look-ahead-safe**, and **invariant-clean** on the 5-year first-70% analysis
slice under the holdout-fenced `build_domain_bars` construction; and each cell's **realized entry
event count** is produced as a coverage map and checked against the Phase-017-validated `ASS`-discovery
sample-size bracket **[15, 8000]** (D7).

## Question

For each substrate-cell: (a) does the holdout-fenced domain-bar construction from 1-minute source
bars pass integrity checks on the analysis slice; (b) does the frozen entry detector produce
**deterministic**, **causally-confirmed**, **invariant-clean** entry events (entry timestamps strictly
within the analysis span, never derived from post-entry data, `SUB-RANDOM` reproducible from its fixed
seed); (c) how many entry events does each cell yield (count + events per 1,000 domain bars), and does
that count fall **inside [15, 8000]** (D7 bracket — inside → `ASS` discovery is in its validated
regime; outside → `ASS` discovery excluded for that cell with disclosure, frozen suite binding
regardless); (d) does the moving-block bootstrap control FPR on a 5-year null slice at the new data
scale (readiness-level machinery sanity, no strategy estimand); and (e) do the two harami substrates
share an identical entry event population (entry-level disclosure — they differ only by their later
benchmark exits)?

## Scope Boundaries

- **Data Views**: 1-minute time bars from the **VAL-005-admitted 5-year dataset**
  (`data/timebars/timebars_<SYMBOL>_*.parquet`, 2021-06-02 → 2026-06-21), aggregated to **15m, 1h,
  4h** clock-aligned domain bars via the **holdout-fenced `build_domain_bars`** rule:
  `min_coverage=0.90` **plus** drop any resample window whose label crosses the analysis-slice
  boundary (VAL-005 G1 finding — inherited by CF-CAPGEO-001). Heiken Ashi candles (for the harami
  substrates) generated from the domain bars via `xen.heiken_ashi_generator`. No Line Break / Renko.
- **Substrates (four, frozen at D1; none tuned)** — each carries the **entry event only**:
  1. **`SUB-AVWAP`** — the CF-AVWAP-001 final candidate (faithful selective AVWAP bounce; EXP-028/029
     cTrader-confirmed; frozen parameters). Detector on **real** domain OHLC; reuse `xen.avwap`.
  2. **`SUB-HARAMI-PARTIAL-V2A`** — the CF-HA-HARAMI-001 `N-PARTIAL-V2A` entry population:
     MA(20,50)-native `/STRONG-STAT`-conditioned HA harami at trend exhaustion (entry frozen; the
     PARTIAL-V2A *exit* is a later benchmark arm, not applied here). Harami detected on HA candles;
     all gating (MA(20,50), `/STRONG-STAT`) recomputed on real domain bars (frozen from
     EXP-060B/068).
  3. **`SUB-HARAMI-V2A-ADVNONE`** — the CF-HA-HARAMI-001 `N-V2A×ADV-NONE` entry population (same
     conditioned-harami entry; the V2A×ADV-NONE *exit* is a later benchmark arm). **EXP-080 reports
     whether (2) and (3) yield identical entry events** (expected, since they differ only by exit) —
     a disclosure, not assumed.
  4. **`SUB-RANDOM`** — fixed-seed random entry, the attribution null. **Predeclared matching rule:**
     for each (instrument × domain), draw random entry timestamps **at completed domain-bar closes
     only** (look-ahead-safe), seed fixed at `SEED_RANDOM` (D-frozen below), count **matched per cell
     to each real substrate's realized count** (so each real substrate's matched-random comparison at
     EXP-081/083 uses an equal-count random control). Determinism: identical seed → byte-identical
     entry set.
- **Grid (192 substrate-cells)**: 4 substrates × 16 instruments × {15m, 1h, 4h}, organized as 48
  instrument×domain cells each carrying the 4 substrate populations. **Instruments (16):** EURUSD,
  GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, XAUUSD, BTCUSD, USTEC,
  US500, US2000, JP225 — the VAL-003 universe **minus DE30** (dropped at INFR-003 §3.1; broker m1
  stale). No DE30.
- **Time range**: **first-70% analysis slice only** of each 5-year file (chronological by 1-minute
  row order; VAL-005 / `build_domain_bars` convention). Readiness, counts, and the D7 bracket are on
  the analysis set (the span `WF-EXPANDING` will use); **no strategy inference, so 0 counted reads**.
  The nested analysis-set partitions are not separately selected or inferred upon here.
- **Global holdout**: the final 30% of each file is **never** loaded, inspected, counted, plotted, or
  used. Only Parquet **metadata** (schema + total row count via `scan.select(pl.len())`) locates the
  split; no holdout row value is materialized. Holdout-fence assertion is itself a checked readiness
  invariant (no domain-bar label crosses the analysis-slice boundary).
- **Look-ahead bias prevention**:
  - Domain aggregation emits only completed windows; HA generation is a sequential rolling transform.
  - The AVWAP and conditioned-harami detectors are sequential/streaming over completed domain bars;
    every entry event's operative timestamp uses only data at or before that bar close.
  - `SUB-RANDOM` entries land only on completed-bar closes; the RNG never consults future data.
  - All ordering/alignment use `CloseTime` (real time), never bar index.
- **Real-price discipline**: AVWAP and all gating/thresholds computed on **real** domain OHLC; the
  harami detector runs on HA (synthetic) candles — permitted because **EXP-080 computes no return,
  capture, excursion, or P&L metric of any kind**. Every *outcome* metric in this family (EXP-081 on)
  is on real prices; none appears here.
- **Exclusions**: no exit/barrier/capture/return/MFE/MAE/expectancy/tail metric (EXP-081 on); no
  exit derivation (EXP-082); no benchmark or derived exit application; no separability gate, frozen
  suite, or `ASS` discovery scoring run (those are EXP-082/083); no parameter sweep or tuning of any
  substrate (all frozen); no cross-instrument/cross-domain pooling; no TEST-stratum-specific inference
  or holdout contact; nothing tuned or frozen against any EXP-080 output.

## Per-Cell Checks (the measurement)

1. **Construction integrity** (per instrument × domain, analysis slice): OHLC consistency
   (`High ≥ max(Open,Close)`, `Low ≤ min(Open,Close)`); strictly increasing `CloseTime`;
   clock-aligned window boundaries; **holdout-fence** (no emitted window's label crosses the
   analysis-slice boundary); **dropped-window fraction** under `build_domain_bars`. **Frozen
   thresholds (predeclared, carried from EXP-043/048/VAL-005):** dropped fraction `< 0.10` clean;
   `0.10–0.25` flagged disclosure (READY-eligible); `> 0.25` construction FAIL → cell
   `COVERAGE_EXCLUDED`.
2. **Entry-detector invariant battery** (per substrate-cell): all entry timestamps strictly within
   the analysis span; entries on completed bar closes only; no entry uses post-entry data (causality);
   detector-specific structural invariants hold (AVWAP: anchor/bounce conditions; harami:
   `BODY_MAX_1 > BODY_MAX_0 ∧ BODY_MIN_1 < BODY_MIN_0` with the reduced-form agreement, MA(20,50) and
   `/STRONG-STAT` gating reproduced from EXP-068); no NaN/null in any emitted entry field; events
   ordered monotone in `CloseTime`.
3. **Determinism**: a full second regeneration of every substrate-cell's domain bars, HA candles
   (where applicable), and entry events; the entry-event table must compare **frame-identical** (exact)
   to the first pass. `SUB-RANDOM` byte-identical from its fixed seed.
4. **Entry coverage & D7 bracket** (descriptive; denominators fixed below): per substrate-cell — entry
   count and entries per 1,000 domain bars; **bracket flag**: `IN_BRACKET` iff `15 ≤ count ≤ 8000`,
   else `OUT_LOW` (< 15) / `OUT_HIGH` (> 8000). Out-of-bracket cells are recorded and carried to the
   EXP-081/083 disclosure (`ASS` discovery excluded for that cell; the **frozen referee suite is the
   binding gate regardless**).
5. **Moving-block null-FPR sanity** (machinery readiness, no strategy estimand): on a **5-year null
   slice** (a return series with no edge — e.g. `SUB-RANDOM` outcomes or a block-permuted real-price
   series), confirm the moving-block bootstrap `CI_low > 0` false-positive rate is controlled (≤ 0.05,
   Wilson-hi ≤ 0.075) at the new 5-year data scale — re-confirming the inference machinery holds at the
   ~2× longer span before any real read. **The control is binding only in the operating regime
   `n ≥ 120` (D0 §D9 frozen floor);** rows at `n < 120` are recorded as disclosure
   (`small_n_disclosed`) — the small-`n` percentile-bootstrap inflation is the known Phase-017
   EXP-077/078 property (D0 §D6 Guard (i)), not a control failure. Bounded check; not a per-cell
   calibration (that is the EXP-027/070-analog suite step at EXP-083).
6. **Harami entry-population identity** (disclosure): report whether `SUB-HARAMI-PARTIAL-V2A` and
   `SUB-HARAMI-V2A-ADVNONE` produce identical entry event sets per cell (expected; differ only by
   exit). If identical, disclose that their entry-level counted-read accounting coincides.

## Metric Denominators & Zero-Baseline (predeclared, before implementation)

- **Entry rate** = entry events / 1,000 analysis-slice domain bars; denominator = the cell's
  analysis-slice domain-bar count (disclosed). A cell with 0 entries reports rate `0.0` with its
  denominator shown — never `0/0`.
- **D7 bracket** = raw count compared to `[15, 8000]`; reported as `IN_BRACKET / OUT_LOW / OUT_HIGH`
  with the count and denominator. Never expressed as a percentage over a baseline.
- **Null-FPR** = (count of null replicates with bootstrap `CI_low > 0`) / (total null replicates),
  with Wilson 95% upper bound; denominator = replicate count (disclosed). 0 false positives → `0.0`
  with denominator and Wilson-hi shown.
- **Empty-construction guard**: a cell whose analysis slice has fewer domain bars than the detector
  warmup (ATR/MA windows) — so no entry state can form — is reported `CONSTRUCTED_EMPTY`, **not**
  NOT_READY (a coverage outcome, not a failure).

## Frozen constants (predeclared at D0/G0; recorded here pre-data-contact)

- **Substrate parameters:** AVWAP — CF-AVWAP-001 final (EXP-028/029); harami — MA(20,50)-native
  `/STRONG-STAT`-conditioned HA harami (EXP-068 frozen). No substrate parameter is varied.
- **`SEED_RANDOM`** (the `SUB-RANDOM` seed) and the bootstrap/null seeds: fixed and recorded in
  `run_metadata.json`; a second pass is byte-identical (D10).
- **Domain construction:** `build_domain_bars`, `min_coverage=0.90` + analysis-slice boundary fence.

## Success / Failure Criteria

- **Substrate-cell READY**: construction integrity PASS (dropped ≤ 0.25, fence held) ∧ zero
  entry-detector invariant violations ∧ determinism PASS. Entry count / bracket flag do **not** affect
  READY (lenient, per the EXP-043/048 readiness convention; sparse, dense, or out-of-bracket cells are
  disclosures, not failures).
- **Substrate-cell NOT_READY**: any invariant violation, non-deterministic output, or
  construction-integrity FAIL (incl. `COVERAGE_EXCLUDED`); recorded with the failing check. NOT_READY /
  `COVERAGE_EXCLUDED` cells are excluded from EXP-081 with record.
- **Experiment verdict — READINESS_DELIVERED**: the 192-substrate-cell READY / NOT_READY /
  `COVERAGE_EXCLUDED` / `CONSTRUCTED_EMPTY` map, the per-cell entry-count + D7-bracket table, the
  null-FPR sanity result, and the harami entry-identity disclosure are produced, whatever the mix.
- **Evidence AGAINST (substrate-level — SUBSTRATE_REFUTED)**: a **systematic** failure indicating a
  detector/aggregation/port bug rather than a data quirk — **predeclared threshold:** non-determinism
  on **any** cell, **or** the same invariant violated on **≥ 3 instruments** for any one substrate,
  **or** the moving-block null-FPR uncontrolled (Wilson-hi > 0.075) **at any `n ≥ 120` (the operating
  regime; D0 §D9 frozen floor)** at the 5-year scale. Null-FPR rows at `n < 120` are disclosed
  (`small_n_disclosed`), **not** halt-binding — the small-`n` inflation is the ratified Phase-017
  EXP-077/078 property (D0 §D6 Guard (i)); halting on it would contradict binding D0 constants. This
  halts Phase 018 pending a fix.
- **Inconclusive (cell-level only)**: a `CONSTRUCTED_EMPTY` cell; recorded, not counted NOT_READY.

## Complexity Budget

- Max statistical tests: **1** (the moving-block null-FPR sanity; descriptive otherwise).
- Max visualisations: **4** — (i) 16×3 READY-status heatmap per substrate (small-multiple, 4 panels);
  (ii) entry-rate heatmap (entries/1k bars) by substrate; (iii) D7-bracket map (IN/OUT_LOW/OUT_HIGH);
  (iv) entry-count distribution vs the [15,8000] bracket band.
- Max new code modules: **≤ 2** under `python/src/xen/` — only if logic does not fit cleanly in the
  experiment script: (a) a frozen **substrate-entry harness** wrapping the existing `xen.avwap` +
  harami detectors behind a uniform `entries(domain_bars) -> events` interface, and (b) a fixed-seed
  **matched-random entry generator**. Reuse `xen.bar_aggregator`, `xen.heiken_ashi_generator`,
  `xen.avwap`, `xen.zigzag` unchanged (no generator edits). Reuse the EXP-068 harami-entry logic
  (port, do not re-derive).

## Data Requirements

Per instrument: lazy `pl.scan_parquet` of the single VAL-005-admitted 5-year file; read total row
count from metadata; compute `analysis_rows = int(total_rows * 0.7)`; collect only the first
`analysis_rows` file-order 1-minute rows; assert sorted by `CloseTime`; set the analysis-slice
boundary timestamp; build domain bars via `build_domain_bars` (fence drops boundary-crossing windows);
generate HA candles (harami substrates); run each substrate's frozen entry detector; collect per-cell
check records, entry tables, and counts; run the bounded null-FPR sanity. A second full pass per cell
supplies the determinism comparison. Outputs: a results parquet (per-substrate-cell summary), a
READY-map CSV, an entry-count + D7-bracket CSV, a null-FPR JSON, `run_metadata.json` (seeds, hashes,
versions), and the four bounded plots from the already-collected summaries (no reloads). Expected
runtime: minutes–tens-of-minutes (192 substrate-cells × 2 passes); `tqdm` over the outer loop. Keep
per-cell memory bounded (do not retain all domain frames simultaneously).

### Standard Loading Pattern (analysis-slice, holdout-fenced)

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob(f"timebars/timebars_{symbol}_*.parquet"))[-1]

total_rows = pl.scan_parquet(path).select(pl.len()).collect().item()
analysis_rows = int(total_rows * 0.7)               # first 70% = analysis set
analysis = pl.scan_parquet(path).slice(0, analysis_rows).collect()
assert analysis.get_column("CloseTime").is_sorted()
analysis_end_ts = analysis.get_column("CloseTime")[-1]
# build_domain_bars(analysis, tf, min_coverage=0.90, fence=analysis_end_ts)
# final-30% holdout never read
```

## Suggested Direction (non-binding)

Mirror EXP-048 structure. Wrap the three real entry detectors behind one frozen `entries()` interface
so readiness, determinism, and counting are uniform across substrates; port the EXP-068 conditioned-
harami entry exactly (the entry is the object under test, not a re-derivation). Run one readiness pass
per substrate-cell (`tqdm` over 192), then one full determinism pass, then the bounded null-FPR sanity,
then the four plots from collected summaries. Report the harami entry-population identity explicitly.
Everything gross-free: no exit, no return, no edge — only that the frozen entries reproduce, are
causal, and have the coverage `ASS` discovery / the frozen suite will rely on downstream.
