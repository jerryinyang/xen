VERDICT: APPROVE

Reviewed artifacts:
- `python/experiments/EXP-003/scope.md`
- `python/experiments/EXP-003/analysis-plan.md`
- `python/experiments/EXP-003/code/run_experiment.py`
- `python/src/xen/referee_calibration.py`

Governance notes:
- Scope matches active checkpoint EXP-003 keystone calibration.
- EXP-001 and EXP-002 pass metadata are enforced before manual execution.
- Alpha grid, draw counts, edge grid, paired draws, Wilson precision targets, and 1000 bootstrap resamples match `design.md`.
- Final 30% global holdout is excluded before domain construction.
- Effects use real domain Close-to-Close returns only.
- Gate-stack rows record L1-L5 outcomes for per-leg pass-rate diagnostics.
- Code stores verdict-level draw outputs, not per-bar simulated returns.

Static verification:
- `python3 -m py_compile` passed for the new shared module and EXP-003 script.
- `uv run ruff check` passed for the new shared module and EXP-003 script.

---

## Revision 2026-06-02 — post-review remediation (re-reviewed: APPROVE)

The consolidated review found a **blocking feasibility defect** plus design and
completeness gaps. All fixed and verified:

- **C2 (reliability, blocking):** the stationary block bootstrap was a pure-Python
  O(n_test) loop run ~9× per draw; timed at ~38 h (4h), ~138 h (1h), ~1361 h (5m)
  *per (instrument, domain) cell* → the run would not terminate. It is now a
  **vectorized, batched** stationary bootstrap, with the bootstrap-mean
  distribution computed **once per referee per draw and reused across the alpha
  grid** (only the percentile cut changes). Measured speedup: 236–392× per CI
  (e.g. 90.7 s → 0.23 s at n=50k); one full draw (3 alphas × 2 referees) = 0.21 s
  at n_test=15k. Projected full-run time ≈ **5–6 h**. The method, inference unit,
  resample count (≥1000), denominators, and interpretation are unchanged; CI
  distribution matches the analytic normal for iid input.
- **W2 (look-ahead/design, §9):** the train/test cut is now derived from the
  shared 1-minute boundary timestamp (`domain_split_index`) and applied to every
  domain, never a per-timeframe row fraction.
- **W3 (design, §6.1):** minimal baseline now gross (no cost gate).
- **W4 (correctness of status):** `overall_status` is now **COMPLETE** when the
  operating-characteristic map is produced (design §11 "success = stating the
  characteristics"), with per-cell `mde_status_counts`. It no longer mislabels a
  successful run — where the minimal baseline is permissive and 4h is
  underpowered — as a failure. EXP-004 gates on the MDE artifact existing, not on
  this status.
- **W5 (completeness):** added FPR, gate-leg pass-rate, and effective-sample
  plots (5/5 planned). The large verdict set is aggregated in Polars before the
  bounded pandas conversion for plotting.
- **I1 (acknowledged, not a code change):** gate leg **L2_integrity is a
  structural guarantee evaluated as constant-True**, so its per-leg pass rate is
  trivially 100% — to be stated as such when EXP-003 results are interpreted.

Verdict after remediation: **APPROVE**.

---

## Revision 2026-06-02 — performance optimization re-review (re-reviewed: APPROVE)

The prior approved code did not terminate within an acceptable wall-clock window
(operator ended it after >2h; the 5m bootstrap is ~90% of runtime). A
**speed-only** revision was implemented by `experiment-developer` and re-reviewed
against governance constraint §8 (Safe Performance and Memory Optimization) and
the code "Safe optimization" / "Vectorization discipline" checks.

Changes reviewed (`python/src/xen/referee_calibration.py`,
`python/experiments/EXP-003/code/run_experiment.py`):

1. **`finite_values()`** — removed a `list()` round-trip for ndarray inputs
   (~57× faster on 55k arrays). Bit-identical output for all input types.
2. **`int32` bootstrap indices** (`_stationary_block_indices`,
   `block_bootstrap_means`) — every domain has n < 2³¹, so `int32` selects the
   same rows as `int64`; only index dtype/bandwidth changes.
3. **Process-level parallelism** of draw evaluation (stdlib `multiprocessing`,
   default = all cores, `EXP003_WORKERS` override) replacing the serial draw
   loop, followed by a deterministic sort of `draw_verdicts` before any summary.

Governance verification — **no change** to research semantics:
- **Counts/grids unchanged:** 500 null draws/generator (1000/domain), 500
  positive draws/edge over the full 10-point grid incl. 0.0 (5000/domain), 1000
  bootstrap resamples, α grid, edge grid — `build_draw_tasks` reproduces the
  prior enumeration exactly.
- **Method/inference unchanged:** stationary block bootstrap, train/test cut via
  `domain_split_index`, two-referee independent seeding (`seed` vs
  `seed+100000`), denominators, and verdict thresholds are untouched;
  `_evaluate_draw_task` reuses the unchanged `add_referee_rows` /
  `evaluate_referees`.
- **Holdout (§5):** load path unchanged (`load_analysis_data` first-70% lazy
  slice); workers receive only post-holdout return arrays. No holdout access.
- **Look-ahead/temporal (§6):** ordering and split logic unchanged.
- **Real-price discipline (§7):** real domain Close-to-Close returns only.
- **Determinism/reproducibility:** each draw is a pure, seed-deterministic
  function of its labels; output is independent of worker count and made
  reproducible by the final canonical sort. Verified empirically under the macOS
  `spawn` start method — serial vs 4-worker output byte-identical (180/180 rows),
  and the worker reproduces the original per-draw logic exactly.
- **Progress visibility / import side-effects:** `tqdm` preserved over the
  parallel stream; no directory creation or I/O at import (safe under `spawn`).
- Static checks: `py_compile` and `uv run ruff check` pass on both files.

**Info (carry to audit/results):** the `int32` index dtype changes the RNG
byte-stream relative to the *pre-revision* `int64` code, so the revised numbers
are not byte-comparable to a hypothetical earlier int64 run. No completed
`results/` exist, the statistical method/distribution/resample-count/denominators
are unchanged, and the revised code is itself fully deterministic — so this is an
acceptable, expected consequence, not a violation. The auditor should not expect
int64-stream reproduction.

Verdict after performance revision: **APPROVE**.

---

## Revision 2026-06-02 — independent verification of the performance revision (re-reviewed: APPROVE)

Independent pipeline re-review of the speed-only revision
(`python/src/xen/referee_calibration.py`,
`python/experiments/EXP-003/code/run_experiment.py`) against `design.md`,
governance §8 (Safe Performance), and the "Safe optimization" /
"Vectorization discipline" code checks. `results/` is empty — Stage-4
re-confirmation, not a post-experiment review. Static checks re-run
independently: `py_compile` and `ruff check` both pass on the two files.

Per-optimization findings:
1. **`finite_values` ndarray fast-path** (`referee_calibration.py:607`) —
   bit-identical: `np.asarray(arr, float)` ≡ `np.asarray(list(arr), float)` for
   the 1-D float arrays at every call site.
2. **`int32` indices** (`_stationary_block_indices:647`, `block_bootstrap_means:696`)
   — every domain has `n < 2**31`; `base + (cols − controlling) ≤ 2(n−1)` cannot
   overflow int32. Politis–Romano construction faithfully vectorized.
3. **Vectorized batched bootstrap + α-grid reuse** — the mean distribution is
   α-independent, so reading per-α percentiles (`ci_from_means:741`) is exactly
   equivalent to per-α recomputation at the same seed.
4. **Process parallelism** (`run_draw_tasks:256`, `_evaluate_draw_task:171`) —
   **provably result-identical to serial, not merely sampled.** Each task is a
   pure function of its tuple plus read-only `cell_data`, derives its own
   `seed_for` seed, and runs its own RNG with no cross-task shared state; the
   final canonical sort (`run_experiment.py:680`) on a key that uniquely
   identifies every row removes all `imap_unordered` ordering nondeterminism.
   Parallel output ≡ serial output by construction, independent of worker count.
   This strengthens the prior 180-row empirical equivalence to a structural one.

`design.md` compliance — scheduling/numeric-realization changes only, no frozen
research semantics touched: holdout (first-70% lazy slice, final 30% never
collected), shared train/test boundary (`domain_split_index` off the 1m
`train_end_ts`), block-bootstrap inference unit with train-only block length,
real-price Close-to-Close returns, frozen draw/grid/resample counts, and
unconditional five-leg evaluation are all unchanged.

**Widened Info caveat (carry to audit/results):** the RNG-realization note is not
limited to the int32 dtype — **batching (`batch_cells=2_000_000`) and the per-α
reuse also fix the Monte-Carlo realization**, so the index dtype, `batch_cells`,
and the batch schedule are now part of the reproducibility surface. Changing any
of them changes the *draw*, not the *distribution*; forward reproducibility is
intact for a fixed seed/n. Since no `results/` exist, the auditor should not
expect int64 / non-batched / different-`batch_cells` stream reproduction. The
L2_integrity-constant-`True` note (I1) stands.

Verdict after independent verification: **APPROVE**.

