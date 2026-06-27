# Pre-Execution Governance Review — VAL-004

**Experiment:** VAL-004 — 15m/30m Domain Temporal-Integrity Validation (Phase 014 [VAL] gate)
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**Reviewed against:** `governance-constraints.md`, `_pipeline-config.md`, developer `code-conventions.md`,
and the active checkpoint `2026-06-14-014-ha-harami-substrate-and-capture/design.md` §5.
**Date:** 2026-06-14

---

## Phase alignment

VAL-004 is the §5 **[VAL] New-Domain Construction Gate** of the ACTIVE Phase 014 checkpoint
(G0 PASS 2026-06-14). It is the pre-committed pipeline entry point (`VAL-004 → EXP-048`) and must
PASS before any 15m/30m cell is admitted to EXP-048. Correct entry point; no phase misalignment.

## Scope (scope.md)

| Check | Result |
|---|---|
| Single falsifiable question | PASS — temporal-integrity of 15m/30m strict+tolerant construction across 17 instruments. |
| Boundaries explicit | PASS — instruments, periods {15,30}, modes {None,0.90}, first-70% range, exclusions all stated. |
| Concrete criteria | PASS — per-cell PASS/FAIL/INCONCLUSIVE + COVERAGE_EXCLUDED (>0.25), suite PASS defined. |
| Criteria attainable | PASS — no mathematically-unattainable bar; no percentage-vs-zero-baseline comparison. |
| Complexity budget | PASS — 0 stat tests, 2 plots, 0–1 modules; realistic for a VAL rerun. |
| Holdout exclusion | PASS — final 30% sealed at first touch, fence re-asserted in code. |
| Real-price rule | N/A/PASS — no returns/P&L/excursions; pure construction-integrity validation. |
| Denominators defined | PASS — check-pass denom = checks attempted; dropped-fraction denom = candidate windows; 0 candidate → INCONCLUSIVE, never 0/0. |

## Analysis plan (analysis-plan.md)

| Check | Result |
|---|---|
| Method justification | PASS — each step has why/simpler-alternative/assumptions; VAL-001 reuse rationale explicit. |
| Assumptions for time-ordered data | PASS — notes 30 divides 1440 (oracle grid coincidence), partial-window High/Low understatement disclosed as trade-off not defect. |
| Cross-view alignment | PASS — CloseTime / SourceCloseTime; never bar index. |
| Purposeful visualisations | PASS — dropped-fraction map + check-pass heatmap, both answer a stated sub-question. |
| Pre-defined interpretation | PASS — SUPPORTED / cell-FAIL / run-FAIL / anchor-FAIL / COVERAGE_EXCLUDED / INCONCLUSIVE all pre-registered. |
| Budget compliance | PASS — 0/0 tests, 2/2 plots, 0 new `xen` modules. |
| Tolerant parameterization correctness | PASS — oracle retention predicate must track the generator floor (prevents false-FAIL of legit partials); floor derived from the same expression; range guarded. This is the one substantive change and it is correctly bounded. |

## Code (code/run_experiment.py)

| Check | Result |
|---|---|
| Plan compliance | PASS — implements exactly the two scoped changes + planned additions; nothing extra. |
| Holdout exclusion | PASS — `load_analysis_data` reused verbatim: lazy scan → `sort("CloseTime")` → `slice(0, int(total*0.7))` → collect; holdout never collected. Aggregation/oracle/coverage/fingerprint all derive from the first-70% frame. |
| Look-ahead prevention | PASS — chart generators sequential; prefix-stability probes retained; CloseTime/SourceCloseTime alignment; no bar-index comparison. |
| Real-price discipline | PASS — no returns computed; HA RealOHLC only validated as preserved fields against aggregated-bar OHLC at identical CloseTime. |
| Strict-mode byte-identity | PASS — `min_coverage=None` paths reproduce VAL-001 logic; `15m` token gives a direct anchor match to the VAL-001/VAL-003 record. |
| Tolerant correctness | PASS (empirically verified) — `tolerant_floor` = `max(2, ceil(min_coverage*P))` (same as `aggregate_ohlc`), guarded against documented [14,15]/[27,30]; oracle + output predicate parameterized only by `min_coverage`; oracle independence preserved (pandas path). |
| Detection power | PASS — every check retains a negative control; the parameterized range check gains below-floor + above-period controls plus a must-not-overfire positive assertion; a missed control or fired overfire is a run-level FAIL. |
| Zero-baseline / NaN | PASS — `status_from_failures` denom≤0 → INCONCLUSIVE; candidate==0 → None + `dropped_window_fraction_disclosed` routes to INCONCLUSIVE. |
| Determinism | PASS — generators deterministic; fingerprint via canonical sort + CSV serialization; within-run two-regeneration check for the 15m anchor. |
| Separation / organization / sectioning | PASS — imports → constants → dataclasses → pure helpers → orchestration → plotting → main; VAL-001-style separators. |
| Import side effects | PASS — `ensure_output_dirs()` only in `main()`; module imported cleanly with no IO (confirmed in smoke test). |
| Progress / logging | PASS — `tqdm` on instrument + chart-view loops; concise `logging`; helpers return data. |
| Plot memory / reuse | PASS — plot inputs are the small `coverage_df` and an aggregated status grid; no raw-data conversion, no second heavy pass. |
| Safe optimization / vectorization | PASS — `dropped_window_fraction` is a single `group_by` on the same bucket expression (pure aggregation, causally safe); sequential chart/prefix logic kept explicit and bounded. |

## Empirical pre-execution verification

A holdout-safe synthetic smoke test (no Parquet read) confirmed 22/22 properties, including:
tolerant oracle zero-disagreement on retained partials; strict predicate flags a 14-bar partial
while the tolerant predicate passes it; `dropped_window_fraction` retained == tolerant agg height;
both golden fixtures PASS; floor guard PASS; all negative controls (incl. tolerant below-floor /
above-period) detected; both must-not-overfire assertions PASS; deterministic fingerprint.

## Revision cycle 1 — review findings resolved

A focused pre-execution review raised four findings (F01–F04). Inspecting the live
data directory confirmed F01 was an *active* defect, not theoretical: `data/timebars/`
currently holds **21** files — the 17 scoped instruments plus 4
`timebars_analysis70_{btcusd,eurusd,ustec,xauusd}` pre-sliced duplicates. Under the
loaded-`Symbol` override, an unguarded glob would have validated those 4 core
instruments **twice** over a different row range. All four findings are resolved:

| ID | Sev | Resolution | Verification |
|---|---|---|---|
| F01 | Major | Added `EXPECTED_INSTRUMENTS` (17) + `reconcile_universe`: exactly-one-file-per-expected-instrument (missing/duplicate ⇒ FAIL), unexpected files disclosed and **not processed**, `loaded_symbol_matches_filename` + `instrument_not_duplicated` content guards, `instrument_universe` in `run_metadata.json`. | Synthetic test: the 4 `analysis70` files excluded → 17 processable; missing ⇒ FAIL; duplicate ⇒ FAIL. |
| F02 | Major | Added `reconcile_15m_anchor`: loads the pinned VAL-001/VAL-003 `15m` records and emits a per-instrument `anchor_15m_reconciles_prior` check that **gates the exit code** (every prior key must be present & PASS); `prior_reconciled` column added to `determinism_anchor.csv`. | Synthetic test: identical rows ⇒ PASS on all 17; injected status flip ⇒ anchor FAIL; no-prior ⇒ NO_PRIOR/INCONCLUSIVE. |
| F03 | Major | Single exit-code contract written into `main()` and aligned across scope.md + analysis-plan.md: PASS(0)=no FAIL & no INCONCLUSIVE; INCONCLUSIVE(2)=PASS-with-deferrals; COVERAGE_EXCLUDED is a recorded exclusion, not a check FAIL. | Contract identical in all three artifacts. |
| F04 | Minor | scope.md Holdout Discipline clarified: schema + total-row **metadata** access is permitted (the sanctioned `scan.select(pl.len())` pattern); only final-30% **row contents** are sealed. | Wording-only; code behavior unchanged. |

Re-compiled clean; 18/18 new synthetic checks pass (no Parquet/holdout read). The
F01 fix materially changed the run: it now refuses to silently double-count the 4
duplicate core-instrument files present in the data directory.

## Info notes (non-blocking)

- `compute_admission` adds an `INTEGRITY_FAIL` status for the edge case of a tolerant cell with a
  failing integrity check, honoring the plan's "ADMITTED requires integrity all PASS" precondition
  and preventing a misleading ADMITTED label. It never fires on clean data and does not alter the
  plan's enumerated ADMITTED/COVERAGE_EXCLUDED/INCONCLUSIVE semantics. Acceptable — a correctness
  guard, not scope creep.
- Two new disclosure files (`coverage_map.csv`, `determinism_anchor.csv`) and the heatmap/dropped-
  fraction plots replace VAL-001's two plots, as the plan specifies; the 9-column
  `validation_checks` schema is preserved (mode encoded in `source_timeframe`).

---

VERDICT: APPROVE (after revision cycle 1 — F01–F04 resolved)
