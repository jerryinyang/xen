# VAL-005 — 5-Year 1-Minute Dataset Validation (INFR-003 Gate)

**Status:** **PASS (ADMITTED).** All five acceptance gates pass. The re-collected
~5-year 1-minute dataset (16 instruments) is admitted as the canonical dataset for
CF-CAPGEO-001 (Phase 018).
**Date:** 2026-06-21.
**Class:** VAL — data-admission validation, operator-reviewed, **outside the 8-stage
experiment pipeline**. No candidate, no slot, no edge inference.
**Governing checkpoint:** `docs/experiments-docs/checkpoints/2026-06-20-INFR-003-five-year-data-upgrade/design.md`.
**Code:** `python/experiments/VAL-005/code/run_experiment.py`.
**Results:** `python/experiments/VAL-005/results/` (`verdict.json`, `gate_summary.csv`,
`validation_checks.csv`, `negative_controls.csv`, `holdout_seal_manifest.csv`,
`coverage_span.csv`).

---

## 1. Verdict

**PASS (ADMITTED).** G1–G5 all pass on all 16 instruments; 0 instruments missing; 0
holdout rows read; 0 disclosed truncations.

| Gate | Title | Status | Summary |
| --- | --- | --- | --- |
| **G1** | Temporal integrity | **PASS** | 369 checks, 0 FAIL, 0 INCONCLUSIVE |
| **G2** | Negative controls | **PASS** | 23 controls, 0 missed; golden fixture PASS |
| **G3** | Coverage / completeness | **PASS** | 16/16 present; 0 truncations disclosed |
| **G4** | Holdout seal | **PASS** | 16 files sealed; **holdout_rows_read = 0** |
| **G5** | Determinism | **PASS** | 48 two-pass checks, 0 non-identical |

20,793,010 analysis (first-70%) rows validated across 16 instruments; 8,911,301
final-30% holdout rows sealed at first touch and never inspected.

## 2. Scope as executed

- **Instruments (16):** EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY,
  GBPJPY, AUDJPY, XAUUSD, BTCUSD, USTEC, US500, US2000, JP225. **DE30 dropped** at
  INFR-003 operator ratification (2026-06-21): its broker m1 history ended 2026-01-16
  (stale) and cannot supply current-edge rows — see INFR-003 design §3.1. DE30's
  VAL-003 admission and old-dataset files are unaffected.
- **Span (D-span ratified):** ~5-year target from 2021-06-01; every instrument's m1
  history reaches 2021-06-02 — **0 truncations** (the broker supplied the full target
  start for all 16; the INFR-002 DE30 truncation pattern did not recur).
- **Views:** 1-minute base bars; 15m/1h/4h domain bars via `bar_aggregator`
  (clock-aligned, `min_coverage=0.90`) — the deployed CF-CAPGEO-001 path.
- **Slice:** first-70% analysis rows only; final-30% sealed at first touch.
- **Suite reuse:** the VAL-001 rev.3 / VAL-003 pure check functions **and** the full
  negative-control battery are **imported unchanged** from
  `python/experiments/VAL-003/code/run_experiment.py`; VAL-005 adds only 5-year file
  discovery, the deployed-coverage oracle, coverage/span accounting, the holdout-seal
  manifest, and the resample determinism two-pass.

## 3. Per-instrument coverage & seal

| Instrument | Analysis start | Holdout boundary | Total rows | Analysis (70%) | Holdout (30%, sealed) | Analysis span (days) | Session breaks |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| AUDJPY | 2021-06-02 | 2024-12-12 | 1,876,841 | 1,313,788 | 563,053 | 1289 | 185 |
| AUDUSD | 2021-06-02 | 2024-12-11 | 1,867,974 | 1,307,581 | 560,393 | 1289 | 185 |
| BTCUSD | 2021-06-02 | 2025-03-12 | 2,201,358 | 1,540,950 | 660,408 | 1380 | 150 |
| EURJPY | 2021-06-02 | 2024-12-12 | 1,878,966 | 1,315,276 | 563,690 | 1289 | 185 |
| EURUSD | 2021-06-02 | 2024-12-12 | 1,870,801 | 1,309,560 | 561,241 | 1290 | 185 |
| GBPJPY | 2021-06-02 | 2024-12-12 | 1,877,405 | 1,314,183 | 563,222 | 1289 | 185 |
| GBPUSD | 2021-06-02 | 2024-12-12 | 1,871,568 | 1,310,097 | 561,471 | 1289 | 185 |
| JP225  | 2021-06-02 | 2024-12-30 | 1,692,220 | 1,184,554 | 507,666 | 1307 | 188 |
| NZDUSD | 2021-06-02 | 2024-12-11 | 1,868,368 | 1,307,857 | 560,511 | 1289 | 185 |
| US2000 | 2021-06-02 | 2024-12-12 | 1,778,456 | 1,244,919 | 533,537 | 1290 | 184 |
| US500  | 2021-06-02 | 2024-12-19 | 1,749,617 | 1,224,731 | 524,886 | 1297 | 185 |
| USDCAD | 2021-06-02 | 2024-12-11 | 1,866,772 | 1,306,740 | 560,032 | 1289 | 185 |
| USDCHF | 2021-06-02 | 2024-12-13 | 1,862,939 | 1,304,057 | 558,882 | 1290 | 185 |
| USDJPY | 2021-06-02 | 2024-12-11 | 1,872,017 | 1,310,411 | 561,606 | 1289 | 185 |
| USTEC  | 2021-06-02 | 2024-12-11 | 1,784,619 | 1,249,233 | 535,386 | 1289 | 184 |
| XAUUSD | 2021-06-02 | 2024-12-12 | 1,784,390 | 1,249,073 | 535,317 | 1289 | 184 |

The full file spans ~5y (to the 2026-06-21 collection date); the table's "holdout
boundary" is the last **analysis-slice** timestamp (the 70% cut). The analysis slice
itself is ~3.5–3.8y (1289–1380 days) — roughly **double** the old-dataset analysis
window (~2.3y), the power upgrade INFR-003 targeted (4h strata previously blinded at
32–86 events). Median inter-bar gap is 60s for every instrument (clean 1-minute
cadence); BTCUSD's longer span / fewer session breaks reflect its 24/7 schedule.

## 4. G1 finding — trailing-window holdout fence (resolved)

The first VAL-005 run flagged **4 G1 failures** (1 each: GBPUSD-4h, EURJPY-15m,
EURJPY-4h, US500-1h) on `resample_no_future_timestamp`. Root cause, confirmed by
per-window re-derivation:

- Each is the **single final row** of a deployed (`min_coverage=0.90`) resample — a
  **trailing partial window** (e.g. 232/240 bars, ≥90% coverage) that the
  coverage-tolerant mode retains.
- Its right-labelled `CloseTime` is the nominal grid-boundary (e.g. 04:00), which sits
  **< one window** past the last real source bar (e.g. 03:52). The aggregated OHLC uses
  **only analysis-slice bars** — fully causal, no look-ahead — but the nominal label
  crosses into holdout-minute timestamps.
- VAL-003 never saw this: it validated only the **strict** resample mode (drops all
  partial windows). VAL-005 deliberately validates the **deployed** coverage path
  CF-CAPGEO-001 uses, which exposes the label convention.

**Resolution (operator decision 2026-06-21): fence-drop.** The canonical deployed
domain construction (`build_domain_bars`) drops any resample window whose label exceeds
the analysis-slice max. This is a 1-bar-per-instrument-per-timeframe effect, immaterial
to power, and makes the domain bars unambiguously holdout-fence-clean. The fence is
applied identically to the production frame, the independent oracle, and the G5
determinism pass. Re-run: **G1 clean (0 FAIL).**

**Inherited rule for CF-CAPGEO-001:** domain bars on a holdout-fenced analysis slice
must drop the final partial window whose label crosses the slice boundary — recorded in
`dataset-reference.md` and the Phase 018 design.

## 5. Detection power (G2)

The VAL-001 rev.3 / VAL-003 negative-control battery ran **unchanged** on deterministic
synthetic data: **23/23 injected faults detected** (null/duplicate/non-monotonic
CloseTime, invalid/null OHLC, resample value-corruption / dropped-row / future-timestamp
/ wrong-sourcebars / duplicate-close, sparse-chart future/unmapped/null source-time, HA
real-price corruption, look-ahead generator, non-deterministic generator) plus the
resample golden fixture. A clean real-data run therefore reflects real detection power,
not pass-by-construction.

## 6. Discipline statement

- **Holdout never inspected.** Only the first-70% analysis slice was materialized per
  file; the harness re-asserts `holdout_rows_read = 0` for all 16 (`holdout_seal_manifest.csv`).
  The new final-30% boundary is sealed per file on its own 2021-06 → collection-date
  timeline. The single historical sanctioned holdout shot (EXP-032, EURUSD-4h, old
  dataset) is unaffected and not transferable.
- **Deterministic.** Deployed resamples reproduce byte-identically on a second pass
  (G5 48/48). Run config recorded in `verdict.json`.
- **Real timestamps; no bar-index alignment.** All checks align by `CloseTime`.
- **No edge or candidate inference.** Data admission only.

## 7. On-PASS actions (completed in this change)

1. **`test-read-ledger.md` re-materialized** on the new 16-instrument × {15m,1h,4h}
   strata (all 0 counted reads); old-dataset ledger retained as history; EURUSD
   instrument-wide cap carried forward as a **disclosed** caution, re-evaluated at
   Phase 018 D0 (INFR-003 §4.3 — does not mechanically transfer to disjoint new-dataset
   rows).
2. **`dataset-reference.md` updated** — new 5-year spans, DE30-dropped disclosure, the
   trailing-window fence rule.
3. **Master-index Infrastructure Tasks INFR-003 row → COMPLETE**; live status updated.
4. **INDEX rows** added (`python/experiments/INDEX.md`; infrastructure-validation family
   index card flipped from PENDING).
5. **Phase 018 design** universe corrected to **16 instruments** (DE30 dropped).

## 8. Registry disposition

`registry: not applicable as a candidate read — VAL-class data admission.` No candidate
family screened, no multiplicity item consumed, **0 counted TEST reads**. The
registry-governance action triggered by this PASS is the **re-materialization of
`test-read-ledger.md`** on the new strata (§7.1), recorded in the same change.

## 9. Gate to Phase 018

With **G-017 resolved `DISCOVERY_ONLY`** (2026-06-21) and **INFR-003 COMPLETE ∧ VAL-005
PASS** (this report), **both Phase 018 preconditions are now met.** CF-CAPGEO-001
screening (EXP-080 onward) is unblocked on the 5-year, 16-instrument canonical dataset,
with the frozen referee suite binding and `ASS` a non-binding discovery overlay.
