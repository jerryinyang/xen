# Pre-Execution Governance Review: EXP-037 — `/EXIT-FH` Fixed-Horizon-Exit Variant (4h, one-shot TEST)

**Date:** 2026-06-10
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**References:** governance-constraints.md, `_pipeline-config.md`, Phase 008 `design.md`
(§3, §5/B2, §7, §8.3, §8.4), developer code-conventions.md, EXP-033 `b2_selection.json`
/ `fh_net_curve.csv`, EXP-034 plan and implementation.

## Checks

### Phase alignment and gate provenance

- Tier-B slot activation verified: EXP-033 `b2_selection.json` records 4h
  `b2_eligible: true` (grid max +45.79 bps, H\*=8 one-SE, all_legs,
  `h_star_stable: false`); 5m/1h grid maxima ≤ 0 → correctly out of scope. The
  scope's tie-break is the operator's predeclared remedy for the disclosed H\*
  fragility, recorded as data-dependent design. PASS.
- G2 routing matches design §8.4 as amended (F02): a Tier-B TEST pass with Holm is
  the gate; the code emits `g2_satisfied` only on `EXIT_FH_TEST_PASS`. PASS.

### Scope

- Single falsifiable question; measurable success/failure/inconclusive criteria plus
  the honest `B2_NO_ROBUST_HSTAR` no-read outcome; predeclared power statement
  marking all-cell INCONCLUSIVE as expected. PASS.
- Holdout exclusion explicit; zero-baseline behavior (absolute bps vs 0) defined;
  real-price discipline explicit (real-OHLC FH returns, no synthetic prices in
  scope). PASS.
- Complexity budget 1 test family / 3 plots / 1 module — realistic and respected
  downstream. PASS.

### Analysis plan

- Methods justified with simpler alternatives considered at every step (frozen
  regime-cluster bootstrap vs Wilcoxon/t-test; max-min tie-break vs plain argmax vs
  carrying EXP-033's H\*=8; per-event financing vs flat constant). Non-parametric,
  dependence-aware, identical to the frozen Phase 007/008 machinery — no
  academic-finance pitfalls. PASS.
- The guard-1 / guard-2 population tension is resolved correctly: a code-path
  reproduction anchor on EXP-033's containment population (≤ 0.01 bps, exact
  per-instrument counts 27/25/34), with the binding tie-break on the trigger-keyed
  population that tiles the EXP-030 cells (39/36/42). This mirrors EXP-033's own
  Step-1(c) relaxed-rule anchor pattern. PASS.
- Interpretation criteria predeclared before results; the FH-vs-BTC companion is
  explicitly non-binding and cannot alter a verdict. PASS.
- Budget: 1 test family (bootstrap CI + one-sided p, Holm across 3 TEST cells; the
  TRAIN policy SE reuses the same frozen machinery as selection input, EXP-033
  precedent), 3 plots, 1 orchestration module. PASS.

### Code

- **Plan compliance:** every plan step maps to a function (guards 1–3 →
  `reproduce_exp033_curve` / `partition_strata` / `verify_frozen_inference`;
  tie-break → `train_tiebreak`; policy → `select_pyramid_policy`; guard 5 →
  `freeze_selection`; one-shot TEST → `run_test_stage`; guard 4 →
  `determinism_replay`; companion → `attach_btc_net`). No bonus analyses. PASS.
- **Freeze-before-TEST (load-bearing):** structural, not procedural — FH/net
  columns are attached to TRAIN rows only in the TRAIN stage; the TEST frame
  receives outcome columns exclusively inside `run_test_stage`, which hard-asserts
  `frozen_selection.json` exists, reads H\*/policy/membership only from it, and
  verifies the live TEST keys equal the frozen stratum manifest. The
  `B2_NO_ROBUST_HSTAR` path writes the freeze record with `h_star = null` and never
  reaches the TEST stage (its determinism replay re-runs the TRAIN tie-break only).
  PASS.
- **Holdout:** rebuilt 4h series uses the same fenced loader as EXP-020/033/034,
  hard-validated against EXP-020 analysis metadata; FH truncation indexes
  `min(start_idx + H, n_analysis − 1)` so the holdout is never indexed. TRAIN/TEST
  split is chronological inside the analysis set. PASS.
- **Look-ahead:** stratum membership keyed on the causal entry bar (index on the
  CloseTime-sorted series, per the scope's predeclared rule); TRAIN events whose
  FH window crosses the cutoff are scope-predeclared and disclosed per H
  (`boundary_spill`). No cross-view comparisons; no bar-index alignment across
  views. PASS.
- **Population integrity:** guard-1 membership equivalence holds — events
  pre-filtered by full-set control counts then re-filtered by contained-control
  counts ≥ 3 yields exactly EXP-033's population, because contained controls are a
  subset of full-set controls; exact count checks (27/25/34) plus ≤ 0.01 bps value
  reproduction enforce this at runtime. Guard 2 hard-stops on any count drift or
  duplicated event key. PASS.
- **Inference:** frozen tail imported from the canonical EXP-027 file with the
  pinned hash `e50873d12a9f68d9` checked before any computation; single-instrument
  specialization and the one-sided 5th-percentile bound replicate EXP-034 (F01);
  Holm via the frozen `holm_adjust`; with 1000 resamples the p resolution (≈0.001)
  resolves the smallest Holm level (0.0167). PASS.
- **Conventions:** VAL-001 sectioning; output dirs created in orchestration only;
  no import-time data loads or directory creation (frozen-tail module load at
  import matches the approved EXP-033/034 pattern); `tqdm` on the file-rebuild and
  TEST-cell loops; helpers return data; vectorized NumPy FH construction with no
  per-event Python loops; bounded plot inputs (small row lists, no pandas
  conversion of large frames); no `.unique()`/silent dedup; explicit hard-fails on
  NaN/empty/out-of-range conditions; absolute-bps zero baseline throughout; CSV
  row schemas consistent per file. Syntax check passes; no lines > 100 chars. PASS.

### Info notes (non-blocking)

1. The chronological half-split compares int64-ns triggers against a float median
   (EXP-033-identical construction); float64 precision (~hundreds of ns at this
   epoch) could only matter for an event within microseconds of the median, and the
   construction is deterministic across replays. Accepted as the predeclared
   EXP-033 construction.
2. A few functions exceed the ~30-line guideline (`run_test_stage`,
   `add_fh_net_columns`); consistent with the approved EXP-033/034 precedent and
   internally sectioned. Accepted.
3. `select_pyramid_policy` hard-errors if no policy keeps all three instruments
   above the 15-event floor; `all_legs` always has the maximal counts, so this only
   fires on a degenerate TRAIN population — a loud stop is the correct behavior.

## Verdict (original, superseded by Revision 1 below)

```text
VERDICT: APPROVE
```

All hard constraints pass: holdout untouched, no look-ahead, real prices only,
timestamp ordering, frozen costs/financing/inference, mechanical predeclared
selection, structural freeze-before-TEST, complexity budget respected, and the
one-shot TEST read is governed by integrity guards 1–5 with hard stops.

---

# Revision 1 Review (2026-06-10, pre-execution — adversarial review findings F01–F06)

**Trigger:** external adversarial review of EXP-037/EXP-038 before any TEST read.
All six findings implemented via design amendment R1 (design.md §11), registry
update, and revisions to `scope.md`, `analysis-plan.md`, `code/run_experiment.py`.
No TEST row had been read; all changes are pre-execution.

## Finding-by-finding verification

- **F01 (Major — uncalibrated small-n bootstrap):** Step 3b / `null_calibration()`
  implements the R1.2 synthetic-null calibration: TEST entry-attribute cluster
  layout, contained-TRAIN dispersion via the predeclared method-of-moments
  estimator, R=2000 replicates through the frozen bootstrap, margin
  `m_cell = max(0, Q95 null ci_low_1s)` binding on the bound. Persisted to
  `null_calibration.csv` and embedded in `frozen_selection.json` **before** the
  freeze barrier; `run_test_stage` hard-fails without margins. Verified in code:
  calibration touches `net_{H*}` of contained-TRAIN rows and TEST
  direction/regime_id only. PASS.
- **F02 (Major — H\* rule outside amendability window):** design.md §11/R1.4 now
  records the tie-break as a §5/B2 amendment with the F02/F08 standing; the
  registry row labels it SECOND-GENERATION DATA-DEPENDENT and notes the data-shaped
  slot-consumption probability. Scope carries the provenance paragraph. PASS.
- **F03 (Major — conflicting TEST boundary conventions):** binding partition now
  uses the loader's 1-minute `train_end_ts` per instrument (TEST iff trigger close
  > boundary, ties → TRAIN — byte-identical rule to EXP-038); the bar-index cutoff
  survives only inside guard 1's EXP-033 reproduction anchor; per-cell membership
  divergence between conventions disclosed in `reconciliation.csv`. Verified:
  `partition_strata` keys on `trigger_ns` vs `boundary_ns`. PASS.
- **F04 (Major — uncorrected cross-route G2 multiplicity):** design §8.4/R1.1
  defines the single phase-level Holm family over all realized binding TEST p's
  (≤4); code emits raw p's, a clearly-labeled within-route Holm-3 disclosure, and
  `route_pass_provisional`; `g2_satisfied` removed — metadata records
  `PENDING_PHASE_FAMILY_HOLM`. Family membership is fixed pre-TEST (B2_NO_ROBUST_HSTAR
  is TRAIN-determined). PASS.
- **F05 (Minor — unbounded boundary spill in the freeze):** R1.5 containment —
  tie-break/policy/calibration all run on the contained TRAIN subset (FH(12) exit
  ≤ boundary; constant population across H, the EXP-033/F08 pattern); spill counts
  disclosed (`n_spill_excluded`); binding membership unchanged. Verified:
  `contained_train_subset` is applied before any outcome column exists, and
  `add_fh_net_columns` runs only on the contained frame in the TRAIN stage. PASS.
- **F06 (Minor — undefined post-freeze recovery):** R1.6 — `select_pyramid_policy`
  requires every TEST cell non-empty under a candidate policy (entry attributes
  only); `freeze_selection` is idempotent under rerun (content-hash assert,
  mismatch = hard stop); `run_test_stage` refuses to run when `test_verdicts.csv`
  exists. Recovery semantics predeclared in scope. PASS.

## Re-checks after revision

- Freeze-before-TEST remains structural: calibration writes precede
  `freeze_selection`; TEST outcome columns are still attached only inside
  `run_test_stage`, which now also reads margins exclusively from the frozen file. ✅
- Holdout fence, real-price discipline, frozen constants/tail (pinned hash),
  zero-baseline, and population reconciliation guards unchanged. ✅
- Complexity budget: still 1 test family (calibration is synthetic-data
  verification of the frozen family), 3 plots, 1 module. ✅
- `python3 -m py_compile` passes; no stale references to the removed binding
  flags (`exit_fh_test_pass`, `g2_satisfied`, `boundary_spill`). ✅
- Look-ahead: `attach_trigger_ns` and the feasibility/calibration structure reads
  are entry-attribute-only; no TEST outcome reachable before the freeze. ✅

## Verdict

```text
VERDICT: APPROVE
```

Revision 1 implements all six findings without weakening any original control.
The binding G2 decision is now correctly external to this run (phase-family Holm
in `G2-gate-review.md`), the bound is calibrated for the ~11–13-event regime, and
the freeze is strictly TEST-price-blind. Proceed to the manual execution gate.
