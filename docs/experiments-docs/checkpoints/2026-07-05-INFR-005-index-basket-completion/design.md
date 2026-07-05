# INFR-005 — Indices-Basket Completion (5-Year 1-Minute Collection)

**Checkpoint type:** **Infrastructure** — *not* an experiment phase. No falsifiable market
hypothesis, no holdout measurement of a thesis. Governed as an **operator-reviewed
design + build**, gated by **VAL-class validation** (VAL-007). Does **not** flow through
the 8-stage experiment pipeline.

**Date scoped:** 2026-07-05.
**Status:** **OPEN — scoped; collection pending.** Broker symbol-string confirmation
(§3, D-names) resolves at collection; VAL-007 gate below binds admission.
**Provenance:** operator request — complete the full indices basket and separate/document
the currencies vs indices baskets in the data architecture.

---

## 1. Objective

Complete the **Indices basket** to its 10-symbol target by collecting the **6 index
symbols missing** from the INFR-003 5-year dataset, into the same canonical
`data/timebars/` set on the same ~5-year window — then **seal the new final-30% holdout**
per file and **extend the TEST-read ledger** with the 6 new instrument×domain strata
before any analytical read.

**Basket state (see `docs/references/dataset-reference.md` "Instruments (baskets)"):**

- **Currencies basket (10):** complete, all Loaded/VAL-005. No action.
- **Indices basket (10):** 4 Loaded (USTEC=US100, US500, US2000, JP225) · **6 to collect**:
  AUS200, US30, EU50, GER40, HK50, UK100.
- **Other:** XAUUSD (metal), BTCUSD (crypto) — Loaded. Not part of either basket.

Deliverable: (a) 5-year m1 Parquet for the 6 new index symbols; (b) a VAL-007 PASS
(temporal integrity + admission/negative controls + coverage + seal + determinism);
(c) a re-sealed final-30% holdout + the 6 new strata added to `test-read-ledger.md`;
(d) updated `docs/references/dataset-reference.md` + `_pipeline-config.md` (done at scope).

## 2. Why now / why it does not contaminate prior work

- **Additive only.** INFR-005 collects **new symbols**; it does **not** re-collect or
  overwrite the 16 INFR-003 instruments. Their VAL-005 admission stands untouched.
- **Same dataset, same window, same rules.** The 6 land in the INFR-003 canonical set on
  the same 2021-06 → collection-date window (latest-glob convention). Mixing rule unchanged:
  a read uses the 5-year files exclusively.
- **Holdout integrity is the load-bearing constraint** (see §4): each new file's final 30%
  is sealed per file at first touch and never read — the INFR-003/VAL-005 mechanism.

## 3. Locked scope decisions (operator)

| # | Decision | Resolution |
| --- | --- | --- |
| **D-instr** | Symbols | The **6** missing index symbols: AUS200, US30, EU50, GER40, HK50, UK100. Completes the 10-symbol Indices basket (with the 4 INFR-003-loaded). |
| **D-names** | Broker strings | Primaries as listed; index-CFD names vary by broker. Known alternates: EU50→STOXX50/EUSTX50, GER40→DE40, US30→DJ30/WS30, UK100→FTSE100, AUS200→AU200, HK50→HSI50. Resolved at collection via `run-infr005-collection.sh one <BROKER_SYMBOL>` or `INFR005_SYMBOLS` override. Record the resolved strings in the VAL-007 report. |
| **D-de40** | German index | **GER40/DE40 collected fresh** as the live-history broker symbol. It is **not** the retired DE30 (broker m1 stale to 2026-01-16, dropped INFR-003 §3.1). DE30's VAL-003 admission + old-dataset files retained for closed-family reproducibility only. |
| **D-span** | History | ~5-year target from 2021-06-01 → collection date (`INFR005_START`/`INFR005_END`); each symbol begins where its broker m1 history actually starts if later — **per-instrument truncation disclosed in VAL-007 G3** (index CFDs are the truncation-prone class; disclose, don't fail). |
| **D-tool** | Collection path | cTrader CLI, `Mode=1, m1`, via `tools/ctrader-cli/run-infr005-collection.sh` (INFR-003 analog). Operator-gated: broker credentials + compute. |
| **D-store** | Storage | New timestamped files in canonical `data/timebars/`; latest-glob makes them canonical for the completed basket. Existing files untouched. |
| **D-seal** | Holdout seal | Final-30% per file sealed at first touch on the new symbol's own timeline; never read. INFR-003/VAL-005 mechanism. |

## 4. Holdout & TEST-ledger governance (binding)

1. **Per-file first-touch seal.** On first read of each new file, compute the 70/30 split
   on that file's own timeline and seal the final 30%; never load/inspect/aggregate it.
2. **Nested split unchanged in structure:** first 70% = analysis (first 70% = TRAIN, last
   30% = TEST); final 30% = global holdout.
3. **Extend `test-read-ledger.md`** with the 6 new instrument×domain strata (15m/1h/4h),
   each at **0 counted reads**. A new symbol is a new stratum population; the existing 16
   instruments' ledger rows are unchanged.
4. **No analytical read during collection.** Collection + VAL-007 read only first-70% rows
   for validation; the holdout is sealed, never inspected.

## 5. VAL-007 acceptance gates (VAL-005 analog, 6 new symbols)

INFR-005 is complete only when **VAL-007** passes all gates. VAL-007 reuses the VAL-005 /
VAL-003 check + negative-control suite **unchanged**; it adds only 6-symbol file discovery,
coverage/span accounting, the holdout-seal manifest, and the resample determinism two-pass.

| Gate | Criterion |
| --- | --- |
| **G1 — Temporal integrity** | No future timestamps; strictly monotonic `CloseTime` per file; no timebar↔{15m,1h,4h} resample misalignment; the deployed-coverage trailing-window fence applied (VAL-005 §4 inherited rule). |
| **G2 — Admission / negative controls** | Full injected-fault battery detected; 0 FAIL / 0 INCONCLUSIVE; golden fixture PASS. |
| **G3 — Coverage / completeness** | Per-symbol row counts, span, gaps within broker-availability expectations; per-instrument truncation disclosed (index CFDs may not reach the full 5y). |
| **G4 — Holdout seal** | Final-30% seal verified per file at first touch; **0 holdout rows read** at admission. |
| **G5 — Determinism** | Derived resamples reproduce byte-identically on a second pass; run config recorded. |

A VAL-007 FAIL on any gate blocks admission of that symbol; fix/re-collect and re-validate.
Partial PASS is allowed per symbol — admit the symbols that pass; hold the rest.

## 6. Disclosures & risks

- **Broker symbol strings unconfirmed** (D-names). Index CFD names vary; a rejected symbol
  is resolved at collection, not a design defect.
- **Index-CFD history may truncate** short of 5y (the truncation-prone class); each collects
  its maximum with a per-instrument disclosure. Holdout boundary derives from its own timeline.
- **Session instruments** (indices, ~exchange hours) differ in bars/day from FX/crypto;
  `min_coverage` convention applies per existing rules.

## 7. Deliverables

1. `data/timebars/timebars_<symbol>_<ts>_<ts>.parquet` for the 6 new index symbols (~5y, m1).
2. `tools/ctrader-cli/run-infr005-collection.sh` **(done at scope)** + recorded run config.
3. **VAL-007** validation experiment (`python/experiments/VAL-007/`) + report; INDEX rows.
4. Re-sealed holdout manifest + 6 new strata added to `test-read-ledger.md`.
5. Updated `docs/references/dataset-reference.md` + `_pipeline-config.md` basket tables
   **(done at scope — pending symbols marked; flip to Loaded on VAL-007 PASS)**.
6. Master-index Infrastructure Tasks INFR-005 row → COMPLETE on VAL-007 PASS.

## 8. Immediate next steps

1. **Confirm broker symbol strings** for the 6 (cTrader app); note in the run config.
2. `dotnet build Xen.csproj -c Debug`, then `./tools/ctrader-cli/run-infr005-collection.sh`
   (operator-gated: credentials + compute). Re-run rejects with `one <BROKER_SYMBOL>`.
3. **Scope + run VAL-007** (integrity + negative controls + coverage + seal + determinism).
4. On VAL-007 PASS: extend `test-read-ledger.md`, flip the basket-table statuses to Loaded,
   flip the master-index INFR-005 row to COMPLETE, write the retrospective.

---

*Companion: collection script `tools/ctrader-cli/run-infr005-collection.sh`; precedent
INFR-003 / VAL-005 (`archive/chapter-01-price-geometry-referee/.../2026-06-20-INFR-003-five-year-data-upgrade/design.md`,
`.../VAL-005/report.md`); dataset architecture `docs/references/dataset-reference.md`.*
