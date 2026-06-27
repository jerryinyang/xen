# Audit Report: Experiment EXP-077

**Experiment**: `ASS`/VAL-002 — Dogfood + Calibration under `WF-EXPANDING` (Phase 017, CF-CAPGEO-001)
**Audit date**: 2026-06-20
**Artifacts**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `results/*`,
`python/src/xen/wf.py` (new), `python/src/xen/ass.py` (moving-block extension)
**Pre-execution governance**: APPROVED (`governance/pre-execution-review.md`)

## Summary

- **Verdict**: **PASS** (implementation faithful; results trustworthy; both leg-level FAILs are
  correctly computed against the predeclared D2.2/D2.4 gates — they are real outcomes, not bugs).
- **Critical Issues**: 0
- **Warnings**: 1
- **Info Notes**: 3

The reported per-stratum verdict (FPR=FAIL, reliability=FAIL, MDE=PASS, accounting=PASS,
dogfood=PASS; anchor+determinism PASS) is a **faithful pure function of the result tables** — every
headline number re-derives exactly. The two FAILs are correctly computed against the frozen D0 gates;
their *meaning* is characterized in Verdict Forensics and handed to Stage 6 (the auditor does **not**
retro-edit a frozen gate).

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | FPR/MDE/reliability/accounting/dogfood legs re-derived from tables; all match. |
| `code/run_experiment.py` | Edge cases | PASS | `<2`-point guards in `score`/`bootstrap_cis`/`aggregate_walk_forward`; sub-floor folds disclosed not dropped; thin deciles guarded (`np.unique` edges, per-decile `n`). |
| `code/run_experiment.py` | Type safety | PASS | Hints on public functions; dataclasses for specs/outcomes. |
| `code/run_experiment.py` | NaN handling | PASS | `dogfood_returns` drops non-finite via `np.isfinite`; finite-flag asserted per dogfood cell. |
| `code/run_experiment.py` | Holdout exclusion | PASS | Dogfood lazy scan stops at `train_cutoff=int(int(total*0.7)*0.7)` (first-49%); TEST/holdout never sliced (verified, §F below). Synthetic legs touch no market data. |
| `code/run_experiment.py` | Loader ordering | PASS | `scan_parquet → select cols → sort("CloseTime") → slice(0, train_cutoff) → collect`; sort precedes slice; sortedness re-asserted in `load_train_1m`. |
| `code/run_experiment.py` | Memory/performance | PASS | Batched bootstrap (`BOOT_BATCH`); lazy scan + column projection; plots consume bounded tables. |
| `code/run_experiment.py` | Safe optimization | PASS | Process-pool over FPR/MDE cells is order-preserving and per-cell seeded → byte-identical at any worker count (determinism flags all True). Per-replicate loop kept explicit (no RNG-sequence-altering vectorization). |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` on FPR/MDE/reliability/dogfood loops; helpers quiet. |
| `code/run_experiment.py` | Logging/output | PASS | Concise `logger` lines; per-stratum verdict logged with NON-BINDING caveat on collapsed flag. |
| `code/run_experiment.py` | Organization/import side effects | PASS | imports→paths→constants→DGPs→pure computation→plotting→orchestration→`main()`; dirs created only in `main()`/`rebuild`. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots read the already-computed tables; no heavy recompute for plotting. |
| `code/run_experiment.py` | Docstrings | PASS | Module + function docstrings with parameters/returns. |
| `xen/wf.py` | Correctness | PASS | `make_folds` tiles `(0.50,1.0]` with no gap/overlap, last fold ends at `n`; fold-clustered moving-block aggregation; D4.1 accounting reproduces the 8-scenario table exactly. |
| `xen/wf.py` | Causality | PASS | Completed test fold rolls into next train (historical at next train time — not leakage); holdout never a fold (caller passes in-analysis series only; `holdout_used_as_fold` rejected). |
| `xen/ass.py` | Correctness | PASS | Direct expectancy/median/`P(>X)` exact; un-pooled anchor `expectancy_direct == np.mean` to 0.0. Moving-block extension (`default_block_length`, `moving_block_bootstrap_cis`, `_resample_fold(kind="block")`) preserves serial order via overlapping length-`b` blocks. |

## Numerical Validation

### Spot Checks (independent re-derivation; `/tmp/audit_077{,b,c}.py`)

- **FPR** (`fpr.csv`, 22 rows): recomputed `fpr=edges/r_rep`, Wilson-95%-upper, and
  `pass = (fpr≤0.05 AND wilson_hi≤0.075)` for every row → **0 mismatches**. Binding-flag semantics
  reproduce exactly with `binding = (read=="wf" AND n≥30)` (single_window always non-binding) →
  **0 mismatches**. Binding-fail set = **5 cells** (matches `verdict.json`); `n_binding_cells=16`
  (matches).
- **MDE** (`mde_tpr.csv`→`mde.csv`, 8 N-rows): recomputed `MDE(N)` = smallest μ with TPR≥0.80 via the
  same monotone interpolation → **0 mismatches**; all N≥30 finite → PASS confirmed.
- **Reliability** (`reliability_deciles.csv`→`reliability_verdict.csv`): recomputed per-X max-gap,
  OLS slope, decile count → **0 mismatches**. X∈{0,0.05,1.0} PASS; X=2.0 FAIL on slope only.
- **Accounting** (`accounting.csv`): all 8 scenarios `pass=True`; cap-honoring trace blocks the 3rd
  read → PASS confirmed.
- **Dogfood** (`dogfood.csv`): 12/12 completed, all folds finite, all cutoff asserts OK, reads=0.
- **Determinism/anchor**: persisted-CSV sha256 for fpr/mde/reliability/accounting/dogfood **all match**
  `integrity.json.table_sha256`; anchor `|direct − np.mean| = 0.0`; all 5 determinism flags True.

### Range Checks

| Metric | Expected | Actual | Pass? |
|--------|----------|--------|-------|
| FPR rate | [0,1], ~0.05 under null | [0.001, 0.071] | YES |
| Wilson-hi | ≥ FPR | all ≥ point, ≤0.083 | YES |
| TPR | [0,1], ↑ in μ and N | monotone, →1.0 | YES |
| MDE(N) | finite, ↓ in N | 0.644→0.050 | YES |
| Reliability gap | small if calibrated | ≤0.0286 all X | YES |
| Dogfood `train_cutoff/total` | <0.49 | 0.4900 all cells | YES |
| Counted reads | 0 (TRAIN-only) | 0 | YES |

### Statistical Sanity

| Statistic | Value | Sensible? | Notes |
|-----------|-------|-----------|-------|
| U0 wf FPR | 0.044–0.052 | YES | Scattered around 0.05 construction target (see Mechanism). |
| B_zero wf FPR | 0.059→0.001 as N↑ | YES | Mild small/mid-n inflation that decays sharply — expected for the bimodal mean-null. |
| X=2.0 slope | 0.652 | YES (as computed) | Ill-conditioned over a 0.056-wide predicted range (gate-shape, not miscalibration). |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Margin calibration | calibration/validation draws disjoint (no FPR↔MDE circularity) | YES | `TAG_CAL=1`, `TAG_VAL=2`, `TAG_EFF=3` disjoint seed streams; `m` from TAG_CAL nulls, FPR on TAG_VAL nulls, MDE on TAG_EFF effects with rule `CI_low>0` (≠ margin rule). |
| iid WF aggregation (synthetic) | exchangeable population → flat-iid ≡ fold-clustered | YES (by construction) | Synthetic draws iid; documented approximation (Info 2). Real dogfood uses true fold-clustered moving-block (`kind="block"`). |
| Wilson interval | finite, non-normal-approx FPR uncertainty | YES | `wilson_upper` matches recomputation exactly. |
| Moving-block (dogfood) | preserves within-fold serial dependence | YES | `b=round(m^(1/3))`, overlapping blocks, real `Close`/ATR only. |

## Results Plausibility

All outputs sit in expected domains. The FPR curve's shape (U0 hovering at 0.05; B_zero high at small N
then collapsing) is exactly what a margin calibrated to a 0.05 construction target produces, with the
bimodal null's known small-n instability superimposed. MDE decreases monotonically with N. Reliability is
excellent in absolute terms for every X (max-gap ≤0.029). Dogfood expectancy CIs straddle 0 (no edge
claimed — consistent with a pipeline-smoke series).

## Verdict Forensics (run autonomously)

### Per-stratum re-derivation & masking check

| Leg / stratum | Per-stratum verdict | Agrees with pooled? | Notes |
|---------------|--------------------|--------------------|-------|
| FPR U0 n=30/60/250/500/8000 (wf) | PASS | n/a (no pooling) | within MC band. |
| FPR U0 n=120/1000/2000 (wf) | FAIL (point>0.05) | — | MC noise (see Mechanism). |
| FPR B_zero n=30/60 (wf) | FAIL | — | genuine small/mid-n inflation. |
| FPR B_zero n≥120 (wf) | PASS | — | inflation decays (z→−10). |
| FPR small-n single_window (non-binding) | disclosed | — | B_zero n=30 sw=0.071 (wil 0.083) breaches even Wilson ceiling — the EXP-076 n<30 under-coverage, **disclosed** in `small_n_stratum`, correctly non-binding. |
| MDE per N≥30 | all PASS (finite) | — | no degenerate cell. |
| Reliability X=0/0.05/1.0 | PASS | — | wide predicted range, slope 0.92–0.95. |
| Reliability X=2.0 | FAIL (slope) | — | gate-shape artifact (see below). |
| Accounting per scenario (8) | all PASS | — | cap honored. |
| Dogfood per cell (12) | all PASS | — | fence held, reads=0. |

- **Collapsed headline**: `collapsed_convenience_flag=false`, explicitly captioned **NON-BINDING**.
  **Is it masking heterogeneity? NO** — every leg is adjudicated per stratum; the binding-fail set is
  computed via the per-row `binding` column (`build_verdict`, `run_experiment.py:622-631`), never an
  AND across N. The masking risk is *structurally absent*: there is no pooled pass/fail standing in for
  a stratum that flips. The one cell that breaches the Wilson ceiling (B_zero n=30 single_window) is a
  predeclared **non-binding** diagnostic and is fully disclosed, not silently dropped.

### Mechanism

- **FPR FAIL is driven by two distinct mechanisms, correctly separated by the per-stratum report.**
  1. **U0 (n=120/1000/2000): Monte-Carlo noise around the 0.05 construction target.** The margin is
     `m=Q95(ci_low_1s | null)`, so the null edge-rate is *calibrated to* 0.05; on an independent draw it
     fluctuates with SE≈√(0.05·0.95/2000)=0.00487. The three "failures" sit at z=+0.31/+0.21/+0.41 with
     one-sided binomial P(X≥edges | p=0.05) = 0.39/0.43/0.36 — i.e. **fully consistent with true FPR =
     0.05**. The whole U0 row lies inside the [0.040, 0.060] MC band. These are point-estimate crossings
     of a hard cut, not error-control failures.
  2. **B_zero (n=30/60): a genuine but mild and decaying small/mid-n inflation.** FPR=0.059 at both
     (z=+1.85, P=0.039 — beyond pure noise) then drops monotonically (0.050→0.001 for n≥120, z down to
     −10). This is the bimodal mean-null (mean≈−0.015, median +0.15) interacting with the percentile
     bootstrap's known **n<30 under-coverage** (EXP-076 disposition (b)). The single-window sub-read makes
     it starkest: B_zero n=30 single_window FPR=0.071 (Wilson 0.083). The mechanism is the qualifier's
     mild one-sided CI under-coverage on a bimodal null at small effective sample size — exactly the
     stratum EXP-076 flagged.
- **Reliability FAIL is driven entirely by X=2.0, and only by the slope sub-gate, not calibration
  error.** Absolute calibration at X=2.0 is excellent: max-gap=0.0168, every decile gap ≤0.10,
  corr(predicted,realized)=0.934. The failure is the OLS slope (0.652) computed over a **compressed
  predicted range** — predicted P(>2R) ties heavily near zero, so the decile quantile edges collapse
  (10→6 unique bins; decile-0 absorbs 102,497 of ~210k points), and the slope is fit over a predicted
  span of only 0.056. Dropping the large near-zero bucket makes the slope *worse* (0.378), confirming the
  instability is the compressed-range geometry, not a single leverage point. The qualifier is **well
  calibrated** at 2R in every metric except a slope statistic that is ill-posed at this probability scale.

### Gate-shape check

- **FPR gate** `fpr≤0.05 (point) AND wilson_hi≤0.075`. The **point** sub-gate is the wrong instrument for
  a margin estimator *calibrated to* 0.05: such an estimator exceeds 0.05 on roughly half of independent
  draws by construction, so a hard point cut at 0.05 manufactures ~50%-rate "failures" indistinguishable
  from noise. The **Wilson-hi≤0.075** sub-gate is the MC-uncertainty-aware part, and it is satisfied by
  **every binding cell** (max 0.0702). Net: the U0 binding failures are "no effect" misread as failure by
  the point sub-gate; the B_zero small/mid-n failures are a real, shape-appropriate signal (the gate *can*
  see this one). Recorded for the interpreter — **the frozen gate is not retro-edited here.**
- **Reliability slope gate** `slope∈[0.85,1.15]`. This gate is well-posed only when predicted
  probabilities span a wide range (X=0/0.05/1.0, ptp 0.33–0.54: slope behaves, leg passes). It is
  **structurally ill-conditioned for compressed-probability strata** (X=2.0, ptp 0.056), where OLS slope
  has no stable meaning and the max-gap is the trustworthy calibration statistic. This is a gate-shape
  mismatch: "effect (good calibration) of a shape the slope gate cannot see," not miscalibration.
  Recorded for the interpreter / any follow-up scope (e.g. slope guarded by a minimum predicted-range or
  per-X applicability condition) — **not** edited here.

## Scope Compliance

- Analysis plan followed: **YES** (5 legs + determinism, all per-stratum; `xen.wf` new module + `xen.ass`
  moving-block extension exactly as scoped).
- Deviations: **one** (see Warning 1 — reliability predicted uses un-pooled `shrink=False`, vs the plan's
  "shrinkage-weighted" wording).
- Complexity budget: 4/4 validation checks, 5/5 plots, 1/1 new module (`xen.wf`) + in-family `xen.ass`
  extension — **within budget**.
- Holdout exclusion verified: **YES** — first-49% TRAIN-only; every dogfood `train_cutoff` equals
  `int(int(total*0.7)*0.7)` with read fraction 0.4900 < 0.491; TEST/holdout never sliced; 0 counted reads.

## Issues

### Critical

None. No finding can move sample membership, a denominator, a metric value, temporal/causal validity, the
binding stratum, or any leg verdict. No fix-and-rerun is required.

### Warning

1. **Reliability predicted probability is un-pooled (`shrink=False`), vs the plan's "shrinkage-weighted"
   wording.**
   - File: `code/run_experiment.py:286` (`sc = ass.score(train, shrink=False, ...)`); plan
     `analysis-plan.md` Step 5 ("the `ASS` shrinkage-weighted **predicted** `P(return>X)`").
   - Description: `ASS` shrinkage is a cross-*type* empirical-Bayes blend that requires a pooled
     all-types sample and `k_shrink`; the reliability loop scores each `(type, N, rep, fold)` train slice
     in isolation with no cross-type pool available, so shrinkage is structurally inapplicable per fold.
     The code's un-pooled raw `P(>X)` is the coherent predictor for a per-fold calibration check; the
     plan's wording is imprecise rather than the code being wrong.
   - **Materiality (non-blocking)**: cannot move the reliability leg verdict. The leg is FAIL solely via
     X=2.0's slope; shrinkage toward the (small) pooled `P(>2R)` would *compress* the predicted range
     further, worsening — never repairing — the slope, and would not flip X=0/0.05/1.0 (slopes 0.92–0.95
     over wide ranges with large margin). Document-and-proceed; flag the wording to Stage 6/7.

### Info

1. **FPR point sub-gate vs construction target** — recorded under Gate-shape. The binding U0 failures are
   MC noise around a 0.05-calibrated margin; the Wilson-hi guard (the uncertainty-aware sub-gate) passes
   on all binding cells. For the interpreter, not a code issue.
2. **iid flat-bootstrap for synthetic WF aggregation** (`wf.aggregate_walk_forward(kind="iid")`) — a
   documented, statistically-equivalent fast path on the exchangeable synthetic population; the real
   dogfood uses the true fold-clustered moving-block (`kind="block"`). Matches pre-exec Info 2.
3. **Determinism replay scope** — covers reliability, accounting, and one FPR + one MDE probe cell
   (hash-identical), not the full multi-hour FPR/MDE grid; the accepted EXP-076 pattern. A fuller replay
   was not warranted: all five determinism flags are True, the process pool is per-cell seeded and
   order-preserving, and the persisted-table hashes reconcile with `integrity.json`.

## Materiality & Re-Audit Requirements

- **Every finding is non-blocking.** For Warning 1 and all Info notes, the explicit reasoning above shows
  the finding cannot change sample membership, a denominator, a metric value, temporal/causal validity,
  the binding stratum, or any leg verdict.
- **No re-execution required.** `verdict.json` is a verified faithful pure function of the result tables;
  the two leg-level FAILs are correctly computed against the frozen D0 gates and are handed, with full
  mechanism + gate-shape characterization, to Stage 6 (`experiment-quant-analyst`) for interpretation.
  The frozen gates are **not** edited by this audit.
