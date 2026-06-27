# EXP-070 — Pre-Execution Governance Review (Stage 4)

**Experiment:** EXP-070 — Event-Level Method Calibration (EXP-027/044-analog, TRAIN-only)
**Family / candidate:** `CF-HA-HARAMI-001` / `CAND-001` (Phase 016, HYP-023)
**Reviewed artifacts:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**Governing docs ingested:** Phase 016 `design.md` (§5 EXP-070, §7 G-016), `D0-predeclarations.md`
(P1–P15, G0 PASS 2026-06-18), Phase 015 `D0-amendment-001` (native object), `D0-amendment-002`
(EXP-067 drop), `governance-constraints.md`, `_pipeline-config.md`, dataset/architecture refs.
**Date:** 2026-06-18

---

## Registry / file-drawer preconditions (Stage 4 gate)

| Precondition | Status | Evidence |
| --- | --- | --- |
| Candidate family REGISTERED, OPEN | ✅ | `candidate-families/harami.md`; `CF-HA-HARAMI-001` OPEN, CAND-001 active |
| Countable item registered (HYP-023 / EXP-070) | ✅ | `multiplicity-registry.md:553` — Phase 016 batch, `0 / 0 TEST reads`, PENDING→G0 satisfied |
| No new countable item introduced | ✅ | Arm (`N-PARTIAL-V2A`), object (native), conditioning all pre-registered (Phase 015 / EXP-068). The two nulls + planted-edge grid are calibration substrate, not a new variant / detector / parameter branch / candidate |
| TEST stratum read declared with tally | ✅ | Scope: **0 counted TEST reads**, TRAIN-only; six P5 strata at **0 counted reads** confirmed against `test-read-ledger.md` (GBPUSD-{5m,1h}, NZDUSD-{1h,2h}, GBPJPY-30m, US2000-4h, all `0 / open`) |
| G0 ratified before scoping | ✅ | `D0-predeclarations.md` "G0 PASS — 2026-06-18"; EXP-070 explicitly authorised |

Phase alignment: scope/plan match the frozen D0 P5 family (exactly the six cells), P7 four-leg
pass criteria, P12 gross-only posture, and the Amendment-001/002 native-only object. No
misalignment with checkpoint objectives.

## Core constraint review

| Constraint | Verdict | Notes |
| --- | --- | --- |
| 1. Simplicity over complexity | PASS | Reuses frozen EXP-068 machinery by import; only new logic is the two nulls + classifier. Translation-equivariance shortcut avoids re-bootstrapping the edge grid (simpler *and* exact). Simpler alternatives explicitly considered and rejected per plan step. |
| 2. No academic-finance pitfalls | PASS | Non-parametric throughout: moving-block bootstrap, Wilson intervals, empirical FPR/TPR. No normality / stationarity / i.i.d. / constant-vol assumption. Regime-clustered block bootstrap respects temporal structure. |
| 3. Strict scoping | PASS | Single question (per-cell calibration); boundaries, exclusions, success/failure/inconclusive all concrete and measurable. Budget 4 tests / 5 plots / 1 module — **matches code exactly** (5 `plot_*` fns; 4 tests: median+mean bootstrap CI, beats-RM contrast, Wilson FPR/TPR, grid MDE; 1 experiment-local module, `python/src/` git-clean). |
| 4. Framework principles | PASS | Data-driven; non-parametric; real-price outcome discipline (ATR-normalised real-price excursions; HA for detection only; grep confirms no `HAClose`/brick usage); timestamp alignment via exact epoch→grid map (`_map_to_grid`), never bar index. |
| 5. OOS holdout rule | PASS | Loads only via EXP-068 `load_train_1m` = first `floor(0.7·floor(0.7·total))` file-order rows; domain bars fenced to `train_end_epoch`. **TEST (next 21%) and final-30% holdout never loaded.** Chronological by `CloseTime`. |
| 6. Look-ahead prevention | PASS | Inherits EXP-068 causal/streaming machinery unchanged. Planted drift added to event **outcomes only** (translation shortcut), never to placement or matched-control selection; null placement uses only bar-time regime/segment/ATR info. |
| 7. Real-price / synthetic-price discipline | PASS | Every per-event return is a direction-signed ATR-normalised real-price excursion; HA candles for harami detection only; no HA-price metric; gross only (no costs/sizing/financing). |
| 8. Safe performance / memory | PASS | Lazy TRAIN load; bounded plot inputs from collected per-cell summaries (no reloads); per-draw bootstrap chunked (`BOOT_BATCH`); `tqdm` on cell + draw loops, helpers quiet. Translation shortcut is **exact** (percentile-based `median_ci` ⇒ `ci_low_1s(g)=ci_low_1s(0)+g`), so it does not alter sample membership, denominators, or interpretation. |

## Artifact-specific checks

**scope.md** — Hypothesis testable/falsifiable; success/failure/inconclusive concrete (FPR ≤ α₀
on the binding median leg under two nulls; finite CI + finite MDE @ TPR≥0.80; byte-identical
replay). Data views, parameters (all inherited/frozen), instruments (exactly six P5 cells),
TRAIN-only time range, holdout + TEST exclusions all explicit. Metric denominators defined
(reportable matched events / reportable draws — never bars); zero-baseline handled (null
per-event location = exactly 0; beats-RM against the `RM-native` distribution, not zero; no
percentage-over-zero anywhere). PASS.

**analysis-plan.md** — Each step carries method justification + "simpler alternative considered."
Reused-vs-new component table is explicit and matches the code. Interpretation guide pre-defines
outcomes (CALIBRATION_DELIVERED / METHOD_DEFECT / INCONCLUSIVE) and four predeclared caveats
(median leg is absolute not excess; Null B is a different dependence structure; block-length
diagnosis; MDE units). Cross-view alignment by timestamp specified. Budget 4/4, 5/5, 1/1. PASS.

**code/run_experiment.py** — Implements exactly the plan, nothing more. Holdout/TEST excluded
(see constraint 5). Look-ahead prevented (constraint 6). Real-price outcomes (constraint 7).
Type hints + docstrings on public functions; VAL-001-style sectioning; **no import-time side
effects** (dirs created only in `run()`; the import-time `_load_exp068()` executes only the
dependency module's own thread-pins/Agg/imports — no data read, no mkdir, no write — and is the
sanctioned reuse mechanism, equivalent to an import); explicit NaN/empty/below-floor handling
(below-floor draws → `reportable=False` with finite disposition; no silent zeros/NaN
propagation); deterministic seeding via EXP-068 `_rng([BASE_SEED, cell_index, purpose])` with
EXP-070-dedicated purpose blocks ≥ 1_000_000 (verified disjoint from every EXP-068 block, max
300_000+offsets); no magic numbers (constants inherited from EXP-068 or fixed pre-measurement in
this file); 0 lines > 100 chars; compiles; all 30 reused EXP-068 symbols resolve. P12
reconciliation against EXP-068 `per_cell_expectancy.parquet` at 1e-9 is wired as a hard
fail-fast gate, using the same `cell_index` seeds so reproduction is exact. PASS.

## Notes (Info — non-blocking)

1. **`RETAINED_FPR_TOLERANCE` verdict label** (developer-flagged). The scope enumerates PASS /
   FPR_EXCLUDED / MDE_UNRESOLVED / CALIBRATION_UNDERPOWERED; PASS is strictly defined as median-leg
   FPR ≤ α₀ under both nulls, while FPR_EXCLUDED is FPR > 0.06. The (α₀, 0.06] band is described
   by both the scope ("FPR exceeds 0.06 … excluded" implies ≤0.06 retained) and plan Step 4
   ("Cells with FPR in (0.05, 0.06] are retained") and D0 P7 Leg 1 ("Any cell with FPR ≤ 0.06 is
   retained"). The added label names that already-in-scope band honestly rather than mislabel such
   a cell PASS (false α₀-clean certification) or FPR_EXCLUDED (wrongly dropped). It introduces no
   new measurement, denominator, or question — **not scope creep**. Metadata carries
   `fpr_controlled_both` (≤α₀) and `fpr_retained_both` (≤0.06) and a `verdict_label_map`, so the
   EXP-071 D0 P8 freeze file can record the disposition unambiguously. Acceptable.

2. **Null B price-level behaviour** (developer-flagged). Null B is the literal whole-bar
   block-circular rotation the **approved** plan specifies (per-bar OHLC validity preserved; real
   entries/barriers held; forward path permuted). Its distortion under few blocks is **pre-registered**
   (plan caveats 2–3) with a built-in two-null disagreement diagnostic (Step 4: grade Null-B excess
   against event/segment count; `block_len` recorded per cell — the code records it). This is an
   approved, documented null construction, not a hidden defect; it breaches no core constraint
   (TRAIN-only null permutation; outcomes-only drift; returns on real OHLC). The Stage-6
   interpretation must apply the disagreement diagnostic before reading any Null-B FPR excess as a
   method failure. Carried forward as an interpretation obligation, not a code fix.

## Verdict

```text
VERDICT: APPROVE
```

All core constraints and artifact-specific checks pass. Registry/file-drawer preconditions are
satisfied (HYP-023 registered; six P5 strata at 0 counted reads; G0 PASS). No Critical or Warning
issues; two Info notes carried forward (one labeling refinement already covered by metadata; one
pre-registered Null-B interpretation obligation for Stage 6).

---

## Addendum — Stage-4 re-review of a performance change (2026-06-18)

**Trigger:** operator request to optimise `code/run_experiment.py` for speed *without affecting
the integrity of the experiment or the reliability of the results*. Two safe, output-preserving
changes were applied; this addendum re-runs consolidated Stage-4 governance on the modified code.

**Changes applied (no other lines touched):**

1. **Determinism replay reuses the production pass (Leg 3).** `determinism_replay()` previously
   computed each of the two `DETERMINISM_CELLS` (US2000-4h, GBPUSD-1h) **from scratch twice**,
   even though `_run_cells` had already computed both cells in `results` — i.e. each determinism
   cell was computed three times. It now takes the production result as pass-`a` and runs a single
   independent recompute as pass-`b`. The Leg-3 check remains a comparison of **two independent
   computations** (`_draws_equal` + `_scalars_equal`, unchanged).
2. **The remaining recompute is parallel.** A new `_resolve_cells(cells, workers, desc)` helper
   (extracted verbatim from the prior `_run_cells` pool boilerplate) runs the determinism recompute
   through the process pool when `workers > 1`. `_run_cells` now delegates to it; `run()` passes
   `(results, workers)` into `determinism_replay`.

**Integrity / reliability verification:**

| Axis | Verdict | Basis |
| --- | --- | --- |
| Sample membership / denominators / metric defs | UNCHANGED | No statistical code touched; only orchestration/replay plumbing. `process_cell`, the nulls, the bootstrap primitives, FPR/TPR/MDE, and the writers are byte-for-byte identical. |
| RNG streams / reproducibility | UNCHANGED | Every value is seeded by `(cell_index, purpose, draw)` and is process-independent (already the basis of the "byte-identical for any workers" guarantee). Reusing the production pass cannot mask non-determinism — a non-deterministic `process_cell` would still diverge between the two independent passes. |
| Leg-3 determinism guarantee | PRESERVED (strengthened) | Still two independent passes. When `workers > 1` the two passes now run in **different processes**, so cross-process reproducibility is exercised rather than within-process-only as before. |
| Holdout / TEST fence | UNCHANGED | No load path touched; TRAIN-only slice and the sealed TEST/holdout strata are untouched. 0 counted TEST reads. |
| Code conventions | PASS | Imports/path/constants order intact; no import-time side effects added; `tqdm` progress retained (`desc="determinism replay"`); helpers return data; compiles clean; 0 lines > 100 chars. |
| Output bytes | UNCHANGED | The seven headline outputs and `run_metadata.json` (incl. the `determinism` block keys `determinism_pass` / `cells_checked` / `non_deterministic` and the SHA-256 hash-pin) are produced from identical values. |

**Effect:** removes one full recomputation per determinism cell (2 of the 4 redundant cell-runs)
and overlaps the remaining recompute with idle cores. No statistical object, denominator, seed,
ordering, or output value changes.

```text
VERDICT: APPROVE
```

Re-review clean. The change is confined to redundant-work elimination and parallel scheduling;
it does not compromise correctness, reliability, temporal causality, or the byte-identical Leg-3
replay. Cleared for the manual execution gate.

---

## Addendum 2 — Stage-4 re-review of draw-level parallelism (2026-06-18)

**Trigger:** the one-process-per-cell schedule left GBPUSD-5m (the highest bar/event-count cell)
running alone on a single core (~6.5 s/draw, ~108 min) while the five finished cells' cores idled.
Operator requested draw-level parallelism so the heavy cell uses every core. This re-review covers
that restructuring.

**Changes applied:**

1. **Per-cell computation split into setup + draws + assembly.** The old `process_cell` (build
   context → real arms → serial 2×`N_DRAWS` draw loop → aggregate) is replaced by `_cell_setup`
   (context + real arms, hence `draw_count`), `_draw_chunk` (resolve draws `[lo, hi)` for one
   (cell, null)), and `_assemble_cell` (reassemble draws in index order + the **unchanged**
   FPR/TPR/MDE/verdict/walk-forward aggregation).
2. **`compute_cells` scheduler.** A single `ProcessPoolExecutor` spans two phases: setup tasks
   (needed first because `draw_count` fixes the matched draw size), then `DRAW_CHUNK`-sized draw
   units (`_chunk_specs`, grouped by cell→null). Replaces `_resolve_cells`/`_run_cells`. `run()`
   and `determinism_replay` both route through it.
3. **`DRAW_CHUNK = 25`** new execution-only constant; **`--workers` default lifted** from
   ≤6 (cell count) to all cores, clamp in `run()`/`main()` relaxed to `max(1, workers)`.
4. **Per-process size-1 context cache** (`_CTX_CACHE` + `_build_ctx_cached`) so a worker rebuilds
   a cell's context at most once and memory stays bounded to one context per worker.

**Integrity / reliability verification:**

| Axis | Verdict | Basis |
| --- | --- | --- |
| Frozen statistical objects | UNCHANGED | `signal_arm` / `matched_random_arm` / bootstrap primitives / `null_a_draw` / `null_b_draw` / `fpr_from_draws` / `tpr_curve` / `mde_from_tpr` / `classify_cell` / `walk_forward` are untouched. Only the *scheduling* of independent draws and the *assembly* changed. |
| Byte-identical outputs | PRESERVED | Each draw is seeded by `(cell_index, purpose, draw)` with no cross-draw state, so it is invariant to which worker/chunk runs it. `_assemble_cell` concatenates chunks by ascending `lo` → draws in index order 0..N_DRAWS-1, identical to the serial list. All aggregates, `draw_verdicts.parquet` (per-draw rows keyed by `enumerate` index), and the SHA-256 hash-pin are therefore unchanged. Verified the assembled result dict matches the prior single-cell dict key-for-key, incl. `draw_count = real_partial.m`. |
| RNG / reproducibility / worker-count independence | UNCHANGED | "Byte-identical for any workers" guarantee retained and extended to any `DRAW_CHUNK`. Lifting the worker cap changes only core utilisation, not values. |
| Leg-3 determinism | PRESERVED (strengthened) | `determinism_replay` recomputes the two cells via the same `compute_cells` path and compares to the production result; cross-process reproducibility exercised when `workers > 1`. The mandatory full second pass run on this code reproducing the first pass's bytes is itself an end-to-end equivalence check of the refactor. |
| Context cache safety | PASS | Draws treat the context read-only: `block_rotate` returns fresh arrays (`{k: v[idx] …}`); the resolvers build new arrays and never mutate `ctx`. The prior code already reused one `ctx` across all of a cell's draws, so read-only-ness was already relied upon. |
| Holdout / TEST fence | UNCHANGED | Loading still goes through EXP-068 `load_train_1m` (first `floor(0.7·floor(0.7·total))` rows) inside `_build_ctx_cached`; TEST/holdout never read; 0 counted TEST reads. |
| Real-price discipline | UNCHANGED | Per-event returns remain ATR-normalised real-price excursions; HA detection-only; gross. |
| Code conventions | PASS | No import-time side effects (cache is a literal dict; no I/O at import); `tqdm` on both `cell setup` and `draw chunks`; helpers return data; spawn-safe (top-level worker fns; `RealArm`/dict/ndarray payloads picklable); thread-pin env set at import in every spawned process; compiles clean; 0 lines > 100 chars; no dangling refs to the removed `process_cell`/`_resolve_cells`/`_run_cells`. |

**Effect:** the heavy cell's draws fan out across all cores (≈ `n_cores`× speedup on GBPUSD-5m,
the wall-clock bottleneck), with no change to any seed, denominator, ordering, statistical object,
or output byte.

**Operator note (carried into Stage 6 / the byte-identical second pass):** the in-flight
production run was started on the prior (cell-level) code. Running this draw-level code as the
required Leg-3 second pass should reproduce the first pass's outputs byte-for-byte; a mismatch
would indicate either true non-determinism or a refactor defect and must be investigated before
any TEST contact — it is not auto-attributable to the optimisation.

```text
VERDICT: APPROVE
```

Re-review clean. Draw-level parallelism is a scheduling/assembly change that preserves every
seed, statistical object, denominator, ordering, and output byte, and the byte-identical Leg-3
guarantee. Cleared for the manual execution gate.

---

## Addendum 3 — Stage-4 re-review after D0-amendment-003 (binding object + symmetric Null B, 2026-06-18)

**Trigger:** the v1 run returned `METHOD_DEFECT`. The EXP-070 audit (`audit.md`, verdict PASS —
faithful implementation) found the verdict was driven by the **median-leg** FPR, which the design
itself predeclared would inherit substrate drift (caveat 1), exposing a **design-criteria
inconsistency** between D0 P7 Leg 1 (calibrated the median sub-leg) and D0 P4/P9 (gate the EXP-071
cell-acceptance on the **full conjunction**), plus a Null-B `beats-RM` arm **asymmetry** (Warning 2).
The operator reviewed the accept-vs-amend options and **directed the amendment + re-run**, selecting
the **full-conjunction** binding object. Governing authority:
`D0-amendment-003-binding-fpr-object-and-symmetric-null-b.md` (P15 sign-off recorded). This addendum
re-runs consolidated Stage-4 governance on the amended `scope.md`, `analysis-plan.md`, and
`code/run_experiment.py`.

**Metric-shopping / file-drawer gate (the load-bearing check).**

| Check | Verdict | Basis |
| --- | --- | --- |
| New countable item introduced? | **NO** | The binding object is the **conjunction `median CI_low>0 ∧ raw-mean CI_low>0 ∧ beats-RM CI_low>0`** — ratified at **G0** in P4/P9 **before any EXP-070 result existed**, and already computed + reported in v1 as the predeclared "disclosed secondary FPR." The amendment *elevates an already-predeclared object*; it adds no new variant, detector, parameter branch, arm, statistic, or candidate. |
| New multiplicity slot? | **NO** | HYP-023 stays a single calibration item; `multiplicity-registry.md` row to be annotated in place (no new/renamed row). Documentation action carried to Stage 7. |
| New TEST read / holdout contact? | **NO** | EXP-070 remains TRAIN-only (first 49%); six P5 strata stay at **0 counted reads**; TEST/holdout never loaded. |
| Threshold goal-posts moved? | **NO** | α₀=0.05, 0.06 tolerance, >2/3 (≥5) defect rule **carry over unchanged**; only the *object* they apply to changes (median sub-leg → P4/P9 conjunction). |
| Median leg suppressed? | **NO** (anti-suppression preserved) | Median-leg FPR remains fully computed and reported as the disclosed diagnostic in `fpr_per_cell.csv`, `calibration_map.csv`, `run_metadata.json`, and the headline FPR plot (faint reference series). |
| Process discipline | **PASS** | Change is via a **dated D0-amendment with operator sign-off** (P15), not an in-flight edit; v1 `METHOD_DEFECT` record preserved (archived to `results_v1/`). This is the sanctioned correction path, the opposite of metric-shopping. |

**Core constraints (delta only; all others unchanged from the base review + Addenda 1–2):**

| Constraint | Verdict | Basis |
| --- | --- | --- |
| 3. Strict scoping / budget | PASS | Budget unchanged **4/4 tests, 5/5 plots, 1/1 module**: the conjunction-FPR is a Boolean of the median (test 1), raw-mean (test 1), and beats-RM (test 2) legs already computed; `calibrated_margin_atr` is an empirical quantile of already-computed Null-A draw medians (no new bootstrap/test); the symmetric Null-B RM arm reuses the same frozen resolver. No new plot file (the two headline plots re-point to the binding series; median kept as disclosed reference). |
| 5/6/7. Holdout / look-ahead / real-price | PASS (unchanged) | No load path, temporal-ordering, or return-definition change. Symmetric Null-B RM arm still resolves real-price ATR-normalised returns; planted drift still outcomes-only. |
| 8. Safe optimisation / determinism | PASS | Null A re-verified **byte-identical** (`_resolve_matched_draw` called with `geom_ohlc is path_ohlc = ctx.ohlc` reproduces the v1 single-arg behaviour line-for-line). Per-draw median point estimate is computed **without consuming RNG** and the bootstrap calls are unchanged in order/seed, so no RNG stream shifts and Leg-3 determinism + worker-count independence are preserved. Null-B RM arm output **intentionally changes** (the Warning-2 fix). |

**P9 calibrated margin.** EXP-070 now emits `calibrated_margin_atr` per cell = empirical
`(1−α₀)` quantile of the Null-A pseudo-signal median point estimate over reportable draws — the
R1.2-analog mechanical margin P9 condition 4 references as an EXP-070 Leg-1 output. Predeclared at
G0 (P9 names it), budget-neutral, recorded for the EXP-071 freeze file. PASS.

**Artifact-specific:** scope.md, analysis-plan.md, and code carry the amendment banner and cite
`D0-amendment-003`; binding/disclosed inversion is consistent across all three; the amended plan's
caveat 1 correctly reframes the median leg's substrate drift as the *reason* it is non-binding and
the conjunction (with the true-null-0 `beats-RM` excess) as the correct binding object. AST parse,
import smoke test, and a synthetic exercise of `fpr_from_draws`/`calibrated_margin` pass (per the
developer report). PASS.

**Notes carried forward:**
1. Info note 2 from the base review (Null-B two-null disagreement diagnostic) **still applies** to
   Stage 6 — but the symmetric RM arm should substantially reduce the v1 count-graded Null-B
   inflation; whether residual Null-B excess remains a rotation artifact vs a genuine signal is the
   Stage-6 interpretation obligation.
2. Info: `_scalars_equal` (determinism replay) does not compare `calibrated_margin_atr`; the margin
   is deterministic from the already-compared draws, so Leg-3 remains validly proven. Non-blocking.
3. **Execution-gate instruction:** before re-running, archive the v1 artifacts —
   `mv results results_v1` and `mv plots plots_v1` (the code reads only EXP-068 artifacts + `data/`,
   never its own prior `results/`, so this is clean). The byte-identical Leg-3 second pass is now
   judged against the **amended** code, not v1.

```text
VERDICT: APPROVE
```

Re-review clean. The amendment is a properly-authorised D0-level correction (operator-signed, P15)
that binds calibration to the already-predeclared P4/P9 conjunction and symmetrises the Null-B
contrast — no new countable item, no TEST/holdout contact, no threshold change, budget unchanged,
Null-A byte-identity and Leg-3 determinism preserved. Cleared for the manual execution gate.
