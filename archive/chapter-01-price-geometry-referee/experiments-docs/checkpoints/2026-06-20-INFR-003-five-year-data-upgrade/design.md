# INFR-003 — 5-Year 1-Minute Data Upgrade

**Checkpoint type:** **Infrastructure** — *not* an experiment phase. No falsifiable market
hypothesis and no holdout measurement of a thesis. INFR-003 is governed as an **operator-reviewed
design + build**, gated by **VAL-class validation** (VAL-005), not by per-hypothesis pre/post
governance verdicts. It does **not** flow through the 8-stage experiment pipeline.

**Date scoped:** 2026-06-20.
**Status:** **OPEN — scoped; build pending.** Operator decisions D-span / D-instr / D-tool / D-store
/ D-seal below to be locked before collection begins.
**Sequencing:** **Phase 018 precondition.** Runs in **parallel** with Phase 017 (which uses synthetic
substrates + the current first-49% TRAIN only and touches no holdout). **Phase 018
(CF-CAPGEO-001 screening) is hard-blocked until INFR-003 completes and VAL-005 PASSes.** Phase 017
and INFR-003 are independent and may proceed concurrently.

**Provenance.** `.ignore/dump/re.md` ("Insufficient Data … update cAlgo to load and store 5 years of
1-minute data") and the two-family retrospective power-wall findings (§3.4: 4h reads at 32–86 events,
SEs 7–30 bps, blinded every substrate-bound exit comparison). CF-CAPGEO-001 is exit/capture-geometry
work on {15m, 1h, 4h}; the 4h stratum especially needs more events to resolve.

---

## 1. Objective

Extend the cAlgo 1-minute base-bar collection to **~5 years per instrument** across the full
17-instrument VAL-003 universe, producing a new canonical `data/timebars/` dataset large enough to
power CF-CAPGEO-001's TEST/walk-forward strata — then **re-establish the holdout seal** on the new
dataset and **re-materialize the TEST-read ledger** on the new strata before any Phase 018 analytical
read.

The deliverable is: (a) 5-year 1-minute Parquet per instrument; (b) a VAL-005 validation PASS
(temporal integrity + admission/negative controls + coverage); (c) a re-sealed final-30% holdout and
a re-materialized `test-read-ledger.md`; (d) an updated `docs/references/dataset-reference.md`.

## 2. Why now / why it does not contaminate prior work

- **Power.** Both closed families died partly behind power walls on the slower domains; 5 years of
  1-minute history roughly doubles the new-universe span (current new-universe collection is
  2023-01-03 → 2026-06-11, ~3.4y) and lengthens it further where broker history allows.
- **No retro-contamination.** The closed families (CF-AVWAP-001, CF-HA-HARAMI-001) keep their
  original dataset files for reproducibility; their verdicts stand on the data they were measured on.
  CF-CAPGEO-001 is a **new** family measured on the **new** 5-year dataset. Mixing is not permitted:
  a Phase 018 read uses the 5-year files exclusively.
- **Holdout integrity is the load-bearing constraint** (see §4): re-collection changes the
  chronological 70/30 boundaries, so the new final-30% must be sealed per file at first touch and
  never read — exactly as INFR-002/VAL-003 sealed the new universe at admission.

## 3. Locked scope decisions (operator — to ratify before collection)

| # | Decision | Proposed resolution |
| --- | --- | --- |
| **D-span** | History span | **~5 years per instrument, ending at the collection date**, capped by broker 1-minute history availability. Target start ≈ 2021-06; instruments with shorter broker history collect their maximum and carry a per-instrument truncation disclosure (the INFR-002 DE30 pattern). |
| **D-instr** | Universe | **All 17 VAL-003-admitted instruments** (EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, XAUUSD, BTCUSD, USTEC, US500, US2000, DE30, JP225). |
| **D-tool** | Collection path | cTrader CLI, **`Mode=TimeBars, m1`**, via a `tools/ctrader-cli/run-infr003-collection.sh` analog of the INFR-002 script; deterministic run config recorded. |
| **D-store** | Storage / canonicality | New timestamped files `data/timebars/timebars_<symbol>_<ts>_<ts>.parquet` (the latest-glob convention makes them canonical for new work). **Existing files retained** for closed-family reproducibility; no in-place overwrite. |
| **D-seal** | Holdout seal | **Final-30% per file sealed at first touch** on the new dataset (in-robot self-guard + Python harness re-assertion, the VAL-003 mechanism). The new holdout is never read. The single historical sanctioned holdout shot (EXP-032, EURUSD-4h, old dataset) is unaffected and not transferable. |
| **D-domains** | Domain construction | 15m/1h/4h built from the new 1-minute base via the established `bar_aggregator` (clock-aligned, `min_coverage=0.90`); 5m/30m/etc. constructible but out of CF-CAPGEO-001 scope. |

### 3.1 Operator ratification (2026-06-21)

Locked before collection (per §8 step 1):

- **D-span — RATIFIED as proposed.** ~5-year target, start **2021-06-01**, ending at the
  collection date; each instrument begins wherever its broker m1 history actually starts if later,
  with a per-instrument truncation disclosure (INFR-002 pattern). The new final-30% holdout boundary
  falls on each file's own 2021-06→collection-date timeline.
- **D-instr — DEVIATION from proposal.** **DE30 is DROPPED from this collection.** Rationale: INFR-002
  found DE30's broker m1 history ended 2026-01-16 (already ~5 months stale at the INFR-003 collection
  date) — it cannot supply current-edge m1 rows for CF-CAPGEO-001 and would only enter as a truncated,
  stale-tailed series. Rather than admit it INCONCLUSIVE again, the operator excludes it.
  **CF-CAPGEO-001 runs on 16 instruments** (the VAL-003 universe minus DE30): EURUSD, GBPUSD, USDJPY,
  USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, XAUUSD, BTCUSD, USTEC, US500, US2000, JP225.
  DE30's VAL-003 admission and its old-dataset files are unaffected (retained for closed-family
  reproducibility); DE30 may be re-collected via an alternate broker symbol in a later INFR item if a
  fresh m1 source is found. VAL-005 validates the **16** collected instruments; the "all 17" language
  in §4–§7 and the VAL-005 scope reads as **16** for this build.
- **D-tool / D-store / D-seal / D-domains — RATIFIED as proposed.**

## 4. Holdout & TEST-ledger governance (binding)

Re-collection is a **holdout-governance event**. The following are mandatory:

1. **Per-file first-touch seal.** On first read of each new file, compute the chronological 70/30
   split on that file's own timeline and seal the final 30%; never load, inspect, or aggregate it.
2. **Nested split unchanged in structure:** first 70% = analysis (first 70% of *that* = TRAIN, last
   30% = TEST); final 30% = global holdout. Boundaries are new (longer history) but the rules are the
   programme's existing rules.
3. **Re-materialize `test-read-ledger.md`** on the new strata: every instrument×domain stratum
   starts at **0 counted reads** on the new dataset (a new dataset is a new stratum population). The
   old-dataset ledger is retained as historical record; the new ledger governs Phase 018. The
   EURUSD instrument-wide TEST cap (holdout-contaminated via EXP-032 on the old data) is carried
   forward as a **disclosed** caution but is re-evaluated for the new dataset at the Phase 018 D0
   (EURUSD's old-dataset contamination does not mechanically transfer to disjoint new-dataset rows —
   operator decision required, recorded at Phase 018 D0).
4. **The expanding-window walk-forward (Phase 018) never includes the final-30% holdout** (Phase 017
   D4 rule).

## 5. VAL-005 acceptance gates

INFR-003 is complete only when **VAL-005** passes all gates (mirrors VAL-001 temporal integrity +
VAL-003 admission/negative controls, on the new 5-year dataset):

| Gate | Criterion |
| --- | --- |
| **G1 — Temporal integrity** | No future timestamps; strictly monotonic `CloseTime` per file; no cross-view (timebar ↔ 15m/1h/4h resample) misalignment; prefix-stability probes (head/mid/tail of the analysis slice) show no structural look-ahead — VAL-001 rev. 3 suite, unchanged. |
| **G2 — Admission / negative controls** | All injected negative controls (gap, dupe, reorder, future-leak, etc.) detected; **0 FAIL / 0 INCONCLUSIVE** — VAL-003 standard. |
| **G3 — Coverage / completeness** | Per-instrument row counts, span, and gap analysis within broker-availability expectations; truncations disclosed per instrument. |
| **G4 — Holdout seal** | Final-30% seal verified per file at first touch (in-robot guard + harness re-assertion); 0 holdout rows read at admission. |
| **G5 — Determinism** | Derived views (resamples) reproduce byte-identically on a second pass; run config recorded. |

A VAL-005 FAIL on any gate blocks Phase 018; fix and re-validate.

## 6. Disclosures & risks

- **Broker history limits.** Some instruments (indices, DE30 in particular — m1 history ended
  2026-01-16 at INFR-002) may not reach a full 5 years; each collects its maximum with a per-
  instrument truncation disclosure (boundaries derive from its own timeline, INFR-002 pattern). An
  alternative-broker-symbol re-collection for DE30 may be considered.
- **Collection time / storage.** ~5y × m1 × 17 instruments is materially larger than INFR-002
  (~1.0–1.28M rows each over ~3.4y); budget collection runtime and disk; lazy Polars scans
  downstream.
- **Crypto/24-7 vs session instruments** differ in bars/day; coverage thresholds applied per the
  existing `min_coverage` convention.
- **No analytical read during collection.** Collection + VAL-005 read only first-70% rows for
  validation; the holdout is sealed, never inspected.

## 7. Deliverables

1. `data/timebars/timebars_<symbol>_<ts>_<ts>.parquet` for all 17 instruments (~5y, m1).
2. `tools/ctrader-cli/run-infr003-collection.sh` (+ recorded run config).
3. **VAL-005** validation experiment (`python/experiments/VAL-005/`) + report; compact row in
   `python/experiments/INDEX.md`; card/row in the infrastructure-validation family index.
4. Re-sealed holdout manifest + **re-materialized `test-read-ledger.md`** on the new strata.
5. Updated `docs/references/dataset-reference.md` (new spans, per-instrument truncation disclosures).
6. Master-index Infrastructure Tasks row moved to COMPLETE on VAL-005 PASS.

## 8. Immediate next steps

1. **Operator ratification** of D-span / D-instr / D-tool / D-store / D-seal / D-domains (§3).
2. Build the `run-infr003-collection.sh` collection path; collect all 17 instruments.
3. **Scope + run VAL-005** (temporal integrity + negative controls + coverage + seal + determinism).
4. On VAL-005 PASS: re-materialize `test-read-ledger.md`, update `dataset-reference.md`, flip the
   master-index Infrastructure Tasks row to COMPLETE.
5. **Gate Phase 018 open** on (INFR-003 COMPLETE ∧ G-017 `ASS_VALIDATED`).

---

*Companion documents: CF-CAPGEO-001 family spec
[`../../../signal-registry/candidate-families/cf-capgeo-001.md`](../../../signal-registry/candidate-families/cf-capgeo-001.md);
Phase 017 design (parallel qualifier validation)
[`../2026-06-20-017-capgeo-qualifier-validation/design.md`](../2026-06-20-017-capgeo-qualifier-validation/design.md);
prior data-collection precedent INFR-002 / VAL-003 (master index Infrastructure Tasks); temporal-
integrity precedent [`../../families/infrastructure-validation/INDEX.md`](../../families/infrastructure-validation/INDEX.md).*
