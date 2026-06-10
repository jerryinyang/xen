# Pre-Execution Governance Review: EXP-038

**Date:** 2026-06-10
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**References applied:** `research-pipeline/references/governance-constraints.md`,
`experiment-developer/references/code-conventions.md`, Phase 008 checkpoint
`design.md` (§3, §7.3, §8.4 as amended F02), `docs/signal-registry/multiplicity-registry.md`.

## Phase and registry alignment

- Phase 008 §8.4 (F02) explicitly defines this experiment's route: an A1 strict pass
  (EXP-034 EURUSD-4h `SEQUENCE_PASS_ALPHA05`) is necessary-but-not-sufficient; only a
  one-shot TEST-stratum confirmation at one-sided α = 0.05 can satisfy G2. The scope
  implements exactly that route, nothing else. ✅
- Registry: `CF-AVWAP-001/HYP-004-TI-TEST` is REGISTERED + SCOPED (Stage 1,
  2026-06-10), 0 candidate slots, single cell, no Holm, G1 gate review records the
  routing. Scope matches the registry row verbatim (estimand, rule, power statement). ✅
- TRAIN/TEST discipline (design §3/§7.3): no TRAIN fitting exists (estimand has no
  free parameters — freeze-before-TEST satisfied by construction); TEST read once;
  honest non-pristine-TEST caveat recorded in scope. ✅

## Scope checks

- Single falsifiable hypothesis; binding rule measurable (one-sided 95% lower
  bootstrap bound > 0 AND boot_p ≤ 0.05); success/failure/inconclusive all concrete. ✅
- Boundaries explicit: EURUSD-4h only, frozen constants (RT 3.0 bps, financing
  0.6 bps/day adverse-side), frozen EXP-027 tail (pinned `e50873d12a9f68d9`), BTC
  exit (not the FH variant), exclusions enumerated, holdout excluded explicitly. ✅
- Mandatory predeclared power statement present (~12 TEST events;
  INCONCLUSIVE_SPANS_ZERO predeclared as a likely, valid outcome). ✅
- Zero-baseline behavior defined (absolute bps vs 0; no percentage-of-baseline);
  denominators fixed (39 full-cell; TEST count fixed by persisted partition). ✅
- Real-price discipline: `lifetime_bps` is real-OHLC EXP-022 provenance; no
  synthetic prices anywhere in scope. ✅
- Complexity budget: 1 test family / 2 visualisations / 0 new modules — realistic
  and minimal. ✅

## Analysis-plan checks

- Every method documents question, sufficiency, simpler-alternative-considered, and
  assumptions; methods are non-parametric (frozen regime-cluster bootstrap), no
  normality/stationarity/i.i.d. assumptions; Wilcoxon/t-test correctly rejected. ✅
- Guard mapping is faithful to the scope's five integrity guards. Guard 2
  ("per-event net reproduces EXP-034 ≤ 0.01 bps on overlapping events") is
  operationalized as full-cell mean ≤ 0.01 bps **plus** an EXP-034-seed bootstrap
  replay to ≤ 1e-6 on CI/p — acceptable substitution since EXP-034 persists no
  per-event nets, the populations overlap completely, and the seed-pinned replay
  binds the entire estimator construction (strictly stronger than a point check).
  Documented in plan Step 1. ✅
- Partition rule predeclared and causal: boundary = CloseTime of last TRAIN
  1-minute analysis row (`train_rows = int(analysis_rows × 0.7)`, the project
  convention); TEST iff trigger close > boundary; tie rule predeclared (ties →
  TRAIN); membership keyed on the entry-confirmation bar — no look-ahead. ✅
- TRAIN/full descriptive reads are confined to the scope-declared transparency
  visual, labeled NON-BINDING, select nothing — consistent with the scope's "no
  TRAIN read beyond the partition itself" exclusion. ✅
- Interpretation guide predeclared for all three outcomes; no goalpost ambiguity;
  explicit no-second-read, no-cost-iteration, no-repartition commitments. ✅
- Budget: 1 family (TRAIN/full runs are disclosures of the same family, consistent
  with EXP-034 precedent), 2 plots, 0 modules. ✅

## Code checks (`code/run_experiment.py`)

- **Plan compliance:** implements exactly the plan — guards → partition persisted →
  one TEST bootstrap → verdict → disclosures → 2 plots. No bonus analyses. ✅
- **Guard-5 ordering (load-bearing):** `test_partition.csv` is written in `main()`
  before `test_sub` is created and before any TEST statistic or bootstrap; the
  pre-partition computations (full-cell mean, EXP-034-seed replay) are the
  predeclared guards on already-known full-analysis quantities, not TEST reads. ✅
- **Holdout:** the only base-data read goes through `load_analysis_data` (lazy
  scan → CloseTime sort → first-70% slice → collect, column-projected); no other
  Parquet path exists. ✅
- **Look-ahead:** stratum membership and boundary are pure CloseTime comparisons;
  `start_idx`/`completion_idx` lookups are validated by the EXP-020 metadata check
  and the `start_close` reproduction guard (the audited EXP-034 pattern). ✅
- **Timestamp alignment:** no bar-index alignment across views; datetime64[ns]
  units consistent on both sides of the boundary comparison. ✅
- **Frozen machinery:** inference tail imported from the canonical EXP-027 file and
  hash-pinned before anything else runs; `infer_cell` is EXP-034's
  `infer_single_cell` verbatim (single-instrument specialization); constants match
  the frozen values; dependency gate hard-requires EXP-034 `a1_strict_pass` and the
  `SEQUENCE_PASS_ALPHA05` verdict. ✅
- **Conventions:** sectioned VAL-001 style; output dirs created in orchestration
  only; no import-time side effects beyond the frozen-tail module load (EXP-034
  precedent, required for the hash pin); helpers typed/docstringed and return data;
  no `.unique()`/silent dedup; NaN/NaT/null are hard stops; `tqdm` on the only
  repeated loop; plot inputs bounded (≤ 39 events); plot jitter seeded;
  deterministic seeds via `seed_for` throughout; compile check passes. ✅
- **Verdict integrity:** `decide_verdict` reads only frozen constants and the
  Step-3 output; no result-aware branching upstream of `test_inference.csv`;
  determinism replay (guard 4) hard-fails on drift. ✅
- Minor note (Info, no action): `build_eurusd_series` and `main` slightly exceed
  the ~30-line guidance — both are orchestration/validation sequences in the
  established EXP-034 style; splitting would not improve reviewability.

## Verdict (original, superseded by Revision 1 below)

```text
VERDICT: APPROVE
```

All governance constraints pass: single registered question, frozen estimand and
inference, predeclared one-shot TEST rule with causal stratum membership, holdout
fenced, no look-ahead, real-price outcomes, budget respected, and the load-bearing
partition-before-read ordering enforced in code. Proceed to the manual execution
gate.

---

# Revision 1 Review (2026-06-10, pre-execution — adversarial review findings F01–F05)

**Trigger:** external adversarial review of EXP-037/EXP-038 before any TEST read.
All five findings implemented via design amendment R1 (design.md §11), registry
update, and revisions to `scope.md`, `analysis-plan.md`, `code/run_experiment.py`.
No TEST row had been read; all changes are pre-execution.

## Finding-by-finding verification

- **F01 (Major — dependent subsample framed as out-of-sample confirmation):**
  R1.7 relabel applied everywhere (scope title/framing, plan, registry, code
  docstring and `route_label` metadata): "TEST-stratum temporal-stability
  subsample check", with the dependence explicitly stated (TEST events are ~30%
  of the EXP-034 estimate and inside D0's selection read). The nomination
  precondition is implemented: `train_consistent = (TRAIN-stratum net point > 0)`
  recorded in metadata; the operator may nominate the package for the holdout
  only if it holds. PASS.
- **F02 (Major — uncalibrated small-n bootstrap):** `null_calibration()`
  implements R1.2 — TEST entry-attribute cluster layout, TRAIN-stratum dispersion
  via the predeclared method-of-moments estimator, R=2000 replicates through the
  frozen bootstrap; measured FPR and margin
  `m = max(0, Q95 null ci_low_1s)` persisted to `null_calibration.csv` **before**
  the TEST bootstrap; `decide_verdict` binds the bound against `m`. The
  TRAIN-dispersion read is a scope-amended, mechanical calibration input. PASS.
- **F03 (Major — uncorrected cross-route G2 multiplicity):** design §8.4/R1.1 —
  this cell's raw p enters the phase-level Holm family with EXP-037's realized
  p's; code emits `A1_CELL_TEST_PASS_PROVISIONAL` /
  `PENDING_PHASE_FAMILY_HOLM` and never `g2_satisfied`; final adjudication in
  `G2-gate-review.md`. The route dependence (same EURUSD-4h events under two
  exits) is disclosed in scope and plan so a joint pass cannot masquerade as
  independent corroboration. PASS.
- **F04 (Minor — boundary-convention divergence vs EXP-037):** resolved at the
  phase level by R1.3 — EXP-037 now uses this experiment's 1-minute `train_end_ts`
  timestamp rule for its binding partition (EXP-038's own rule was already the
  project convention and is unchanged); with one boundary, EXP-037-TRAIN ∩
  EXP-038-TEST = ∅ on EURUSD-4h by construction, so execution order is moot;
  EXP-037 discloses the convention divergence counts. PASS.
- **F05 (Minor — no predeclared influence diagnostic):** `loco_diagnostic()`
  implements the R1.7 leave-one-cluster-out check — per-drop `ci_low_1s` with
  deterministic seeds, `above_margin` flags, `loco_summary` (min bound, all-above)
  in metadata; persisted to `loco_diagnostic.csv`; accompanies, never gates. PASS.

## Re-checks after revision

- Guard-5 ordering extended and still load-bearing: partition write (now
  byte-idempotent under rerun, R1.6) → calibration write → no-second-read check →
  TEST bootstrap. No TEST outcome statistic upstream of the persisted partition +
  margin. ✅
- New R1.6 guard verified: existing `test_inference.csv` hard-stops before
  inference; existing partition must byte-match the recomputed one. ✅
- Holdout fence, frozen tail/constants (pinned hash), EXP-034 reconciliation
  guards, zero-baseline, NaN hard-stops unchanged. ✅
- Complexity budget: still 1 test family (calibration = synthetic-data
  verification; LOCO = predeclared fragility diagnostic of the same family),
  2 plots, 0 new modules. ✅
- `python3 -m py_compile` passes; no stale `binding_pass`/`g2_satisfied`
  references. ✅

## Verdict

```text
VERDICT: APPROVE
```

Revision 1 implements all five findings without weakening any original control.
The route is now honestly framed, the bound is calibrated for the ~12-event
regime, the binding decision is external (phase-family Holm in
`G2-gate-review.md`), and recovery/no-second-read semantics are structural.
Proceed to the manual execution gate.
