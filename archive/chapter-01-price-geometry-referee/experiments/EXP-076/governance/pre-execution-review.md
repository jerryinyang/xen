# Pre-Execution Governance Review — EXP-076 (`ASS`/VAL-001)

**Reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `python/src/xen/ass.py`
against the bundled governance constraints and the active Phase 017 D0 (§D1/§D2.1/§D3/§D6).
**Date:** 2026-06-20. **Stage:** 4 (pre-execution).

## Constraint checks

| Constraint | Result |
| --- | --- |
| OOS holdout untouched | **PASS** — synthetic only; no Parquet load, no slice, no holdout path exists. |
| Look-ahead / temporal causality | **PASS (N/A)** — synthetic iid; no time-ordered market data. Determinism via fixed `SeedSequence` seeds (D6). |
| Real-price discipline | **PASS (N/A)** — synthetic ATR-unit returns; no HA/Renko prices anywhere. |
| Single hypothesis / scope boundaries | **PASS** — one question (does `ASS` recover known truth?); boundaries explicit; exclusions list FPR/MDE/shape/`k`-tuning to EXP-077/078. |
| Complexity budget | **PASS** — 3 checks / 4 plots / 1 new module (`xen.ass`), exactly as budgeted. |
| Gate-threshold calibration | **PASS** — the 0.85·SE recovery band, [0.86,0.94] coverage band, and 0.25/0.05 shrinkage bounds are fixture/bite-calibrated (2026-06-20 GREEN), not magic constants. |
| Scope criteria attainable | **PASS** — recovery band is SE-relative (auto-widens at small `n`; unbiased estimator floors at 0.6745·SE < 0.85); no percentage-vs-zero metric; pull denominator guarded (`PULL_EPS`). |
| Code conventions | **PASS** — output dirs created only in `main()`; no import side effects; VAL-001 sectioning; `tqdm` on the long loops; bootstrap vectorized+batched (causally safe — synthetic iid); concise `logging`; type hints + docstrings; ruff clean. |
| Plan compliance | **PASS** — R1 (un-pooled recovery legs), R2 (closed-form σ + MC median-SE), R3 (dual-form expectancy anchor), R4 (per-draw seeding), and the SP shrinkage construction are implemented as predeclared. |
| Registry precondition | **PASS** — `CF-CAPGEO-001` REGISTERED; item `ASS/VAL-001`/EXP-076 in the multiplicity registry; **0 candidate slots, 0 counted TEST reads** (synthetic). |

## Disclosures carried to the manual gate / Stage 8 (not blocking)

1. **D1 skew-family fixture inconsistency (operator adjudication).** The frozen `(ξ,ω,α)`
   parametrization is authoritative for ground truth (scope rule: "ground truth closed-form/MC
   from the DGP"; matches `bite_check.py`). The D1 *informal* `≈mean/≈median` annotations for the
   two **left-skew** members are inconsistent with those params: `Sminus` computes median
   **−0.124** / mean −0.224 (annotated "+0.17 / −0.07"), and `Sminus0`'s annotated "mean≈0 &
   median +0.24" is internally impossible for SN(−4), where mean−median is fixed at **−0.0998**
   (so mean≈0 forces median ≈ +0.10, not +0.24). The two left-skew members are therefore
   median-**negative**; **`Splus` (right-skew) remains median-positive (median +0.674)** — it is
   *not* the whole "S family" that flips sign, only the two left-skew members. They do retain
   `median > mean` (the dangerous ordering), but the median-positive / mean≤0 trap is realized by
   the **B** family, not S. **Recovery validity is unaffected** (an unbiased estimator recovers the
   true value of whatever DGP is frozen, ground truth is computed from the authoritative params,
   and the `≈mean/≈median` text is never read by any computation). Surfaced for the operator to
   either accept the computed ground truth or issue a dated `D0-amendment` correcting the `ξ`
   values if median-positive **left-skew** shapes are required. This is a frozen-D0 issue,
   **not** a code defect — no specialist REVISE routes here.
2. **Frozen-scale runtime.** At R_REP=2000 / N_BOOT=10000 the per-replicate coverage bootstrap
   over the full `n`-grid (up to n=8000) is the dominant cost (multi-hour), inherent to the frozen
   recipe (the plan flagged it). `--smoke` and `--no-coverage` knobs exist but are **non-binding**;
   the binding G-017a verdict requires the frozen-scale run. Reducing N_BOOT/R_REP is a
   D0-amendment decision, not a code change.
3. **Predeclared n=2000 shrinkage rich-pull marginal.** Confirmed numerically: pull = 0.0566 at
   n=2000 (analytic `k=120` consequence), exceeding the literal `<0.05` rich bound by ~0.7pp. This
   is the plan's predeclared known-marginal; `verdict.json` surfaces it (`marginal_flag`) for
   Stage-8 adjudication, not a silent pass.

## Stage-4 re-review addendum (2026-06-20, code change)

Two post-approval edits were made and re-reviewed; **APPROVE stands** (no verdict-bearing number
or invariant changes).

1. **Disclosure wording corrected (docs + code comment).** Disclosure #1 above and the matching
   `run_experiment.py` comment now state precisely that only the **two left-skew** members
   (`Sminus`, `Sminus0`) are median-negative while **`Splus` is median-positive (+0.674)** — the
   earlier "S family is median-negative" overstated it. Documentation-only; no computation touched.
2. **Cell-level process parallelism added (`--workers`, default = all cores).** The 99 `(type, n)`
   cells are dispatched to a `ProcessPoolExecutor` and reassembled in canonical cell order. This is
   a **safe** optimization under the governance rule: each cell/replicate is seeded by
   `rng_for(tag, type_id, n, replicate)` independent of execution order, so output is
   **byte-identical** at any worker count — sample membership, denominators, metric definitions,
   statistical interpretation, and the D6 determinism hash are all unchanged. The per-replicate
   bootstrap loop was deliberately **not** collapsed across replicates (that would change the exact
   RNG draws and break byte-identical D6). `py_compile` + `ruff` clean. The binding G-017a verdict
   is unaffected by worker count; `--workers 1` reproduces the serial result exactly.

```text
VERDICT: APPROVE
```
