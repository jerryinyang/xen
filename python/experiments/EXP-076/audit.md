# Audit Report: Experiment EXP-076 (`ASS`/VAL-001 — Synthetic-Substrate Recovery, G-017a)

## Summary

- **Verdict**: **CONDITIONAL PASS** (C1 fixed & re-audited — see "C1 Re-Audit" below). The per-cell
  numbers are correct, reproducible, and the genuine measured outcome (no numerical bug; no binding
  recompute). C1 (collapsed verdict against the per-stratum doctrine) was routed to
  `experiment-developer`, fixed as a representation-only change, and `verdict.json` regenerated via
  `--rebuild-verdict` from the unchanged hash-verified tables. Remaining items are governance/D0
  dispositions (coverage n≥30 binding boundary; downstream propagation guard), carried to Stage 6/8.
  **[History: originally filed as a soft Warning; upgraded to Critical C1 after operator challenge
  (the collapsed verdict violated binding doctrine `cf-capgeo-001.md:137,204`; D0 `:139,171–173`);
  now resolved.]**
- **Critical Issues**: 1 — **C1 RESOLVED** (collapsed cross-cell verdict → per-stratum;
  representation-material, no recompute; re-audited).
- **Warnings**: 2 (coverage n≥30 binding boundary pending D0-amendment; downstream propagation control)
- **Info Notes**: 3

All numbers below were re-derived independently by the auditor from `results/*.csv` and from an
independent (non-experiment) bootstrap micro-simulation.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Recovery/coverage/shrinkage formulas match plan R1–R4; un-pooled recovery legs (`weight=1`); SP pull = closed form. |
| `code/run_experiment.py` | Edge cases | PASS | `PULL_EPS` guard on the pull denominator; median-SE memory-batched; n<2 guarded in `xen.ass`. |
| `src/xen/ass.py` | Correctness | PASS | `direct_expectancy` reduces to `mean(x)` un-pooled (anchor exact); percentile bootstrap 5th/95th per D3; kNN bandwidths floored. |
| both | Holdout exclusion | PASS (N/A) | Synthetic only; no Parquet load, no slice, no holdout path exists. |
| `code/run_experiment.py` | Safe optimization | PASS | New `ProcessPoolExecutor` cell parallelism is **byte-identical** — confirmed: on-disk table hashes equal recorded `table_sha256` (per-cell `rng_for` seeding makes output order-independent). |
| `code/run_experiment.py` | Determinism | PASS | `recovery_match`/`shrinkage_match`/`groundtruth_match` all true; independently re-hashed all four tables → exact match. |
| `code/run_experiment.py` | Progress / logging | PASS | `tqdm` over cells + ground-truth; concise `logging`; helpers return data. |
| both | Organization / import side effects | PASS | Output dirs created only in `main()`; VAL-001 sectioning; no import-time effects. |
| `code/run_experiment.py` | Docstrings / types | PASS | Public functions typed and documented. |

## Numerical Validation

### Spot Checks (auditor-independent)

1. **Anchor (R3).** `integrity.json`: `direct_expectancy == numpy_mean` to `anchor_abs_diff = 0.0`
   (exact by construction — `direct_expectancy` returns `np.mean(x)` when `weight≥1`). KDE-integrated
   expectancy agrees to `1.21e-8` vs the `0.02·σ = 0.02` bound → KDE integration is unbiased for the
   mean on the anchor cell. **PASS.**
2. **Table hashes.** Independent `shasum -a 256` of `ground_truth/recovery/coverage/shrinkage.csv`
   equals the recorded `table_sha256` in `integrity.json` for all four. **PASS** (artifacts are the
   reproducible run; parallelism did not perturb output).
3. **n=2000 shrinkage marginal.** `pull_theory = 0.05660377358490565`, `pull_emp =
   0.056603773584905634` — match to ~1e-16, and both equal `k/(n+k) = 120/2120 = 0.056604`. Exactly
   the predeclared analytic value; implemented shrinkage reproduces the closed form (no weighting
   bug). **PASS.**
4. **Independent under-coverage micro-sim** (auditor's own code, n=15, 5th/95th percentile bootstrap
   of the mean): clean N(0,1) coverage **0.871**, bimodal B_neg coverage **0.843** (nominal 0.90),
   under-covering and worse for bimodal — reproducing the experiment's U0=0.8595 / B_neg=0.833
   ordering. Confirms the miss is an intrinsic small-sample property of the percentile mean-bootstrap,
   **not** a defect in `xen.ass.bootstrap_cis`.

### Range / sanity

| Statistic | Value | Sensible? | Notes |
|-----------|-------|-----------|-------|
| Check 1 recovery, all cells | 198/198 pass; worst ratio 0.72 (`Sminus0` exp /n=500; `U2` med /n=250) | YES | Comfortably under the 0.85·SE band; unbiased on every U/S/B type incl. negative-median skews. |
| Check 2 coverage, n≥30 | 0/176 fail | YES | Calibrated everywhere except the sparse floor. |
| Check 2 coverage, n=15 expectancy | mean 0.864, min 0.833 (B_neg) | YES | Systemically depressed row straddling the 0.86 floor; converges to ~0.90 by n≥120. |
| Check 2 coverage, n=15 median | min 0.876, 0 fails | YES | Median robust at small n; effect is expectancy-specific. |
| Check 3 shrinkage | monotone weight ✓; sparse pull (n≤30) 0.80–0.89 ✓; rich n=8000 0.0148 ✓ | YES | Only literal breach is n=2000 (0.0566). |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Percentile bootstrap | Nominal coverage at the tested n | PARTIAL | Holds for n≥30 and for the median at all n; under-covers for the **mean at n=15** (O(1/√n) skew error) — independently reproduced. |
| MC ground truth | 10⁷ draws ≈ exact vs the bands | YES | σ closed-form vs MC within tol; median-SE distribution-free. |
| Within-type iid resample | Valid for synthetic iid | YES | Synthetic iid by construction; moving-block variant is EXP-077. |

## Verdict Forensics (mandatory)

### Per-stratum re-derivation & masking check

| Stratum | Per-stratum verdict | Agrees with pooled headline? | Notes |
|---------|---------------------|------------------------------|-------|
| Recovery (Check 1), all 198 cells | PASS (all) | — | Binding leg fully passes incl. n=15 and all skew/bimodal medians. |
| Coverage, n≥30 (176 cells) | PASS (all) | NO — pooled says FAIL | Calibrated; the pooled FAIL does not come from here. |
| Coverage, n=15 expectancy (11 cells) | 4 fail / 7 pass, whole row depressed (0.833–0.876) | This **is** the pooled driver | Pass/fail split here is itself near MC noise (U0 0.8595 fails, Splus 0.861 passes — 0.0015 gap vs ±0.0131 MC band). |
| Coverage, n=15 median (11 cells) | PASS (all) | NO | Median calibrated at n=15. |
| Shrinkage (Check 3) | monotone+sparse PASS; rich literal fail only at n=2000 (0.0566, predeclared) | partial driver | Exact analytic marginal, not a failure of the implementation. |

- **Pooled headline**: `overall_pass_literal=false` (AND-of-all-cells). **Is it masking
  heterogeneity? YES — emphatically.** 194/198 cells pass; the literal FAIL is produced by **4 cells,
  all at n=15, all expectancy**, plus the **single** predeclared n=2000 shrinkage marginal. The pooled
  boolean conflates a near-universally-calibrated estimator with its documented small-sample-floor
  behaviour. A pooled AND is a disclosure here, not a verdict.

### Mechanism

The binding miss is **Check 2 (coverage)**; the driving cells are the **n=15 expectancy** cells.
Driver: the **5th/95th percentile bootstrap of the sample mean under-covers at n=15** because the
sampling distribution of the mean is skewed at small n and the percentile interval is not
skew/bias-corrected (coverage error O(1/√n)). It is **expectancy-specific** (the median is robust at
small n → median coverage fine) and **shape-ordered** (near-nominal on clean normals, worst on
bimodal `B_neg` whose catastrophic minority mode fattens the small-n mean's tail). The auditor's
independent micro-sim reproduces both the under-coverage and the normal-vs-bimodal ordering — the
fingerprint of a genuine statistical effect; an implementation bug in `bootstrap_cis` would not
preferentially spare clean normals or the median. The n=2000 shrinkage breach is a pure analytic
consequence of `k = median-n = 120` (`120/2120 = 0.0566`), predeclared.

### Gate-shape check

- **Binding gate**: uniform all-cells AND of coverage ∈ [0.86, 0.94], applied identically at every n
  including n=15. **Effect shape**: a sample-size-dependent small-sample under-coverage of the
  *mean*, confined to the sparsest cell.
- **Is the gate the wrong instrument? PARTIALLY — granularity mismatch.** The gate conflates two
  regimes: (a) n≥30, where coverage is genuinely calibrated, and (b) the n=15 "sparse-stress" floor,
  where percentile mean-bootstrap under-coverage is mathematically expected a priori. The uniform
  conjunction cannot distinguish "`ASS` is miscalibrated" from "`ASS` hit the known small-sample floor
  of its own bootstrap." This is **"effect of a shape the pooled gate over-aggregates,"** not "`ASS`
  fails calibration." Recorded for the interpreter and governance; **not** retro-edited here.

## Scope Compliance

- Analysis plan followed: **YES** (R1 un-pooled recovery, R2 SE definitions, R3 dual-form anchor, R4
  per-draw seeding, SP shrinkage construction all as predeclared).
- Deviations: none. The two post-approval edits (disclosure wording; cell parallelism) were
  re-reviewed in `governance/pre-execution-review.md` and are byte-identical (hashes confirm).
- Complexity budget: 3/3 checks, 4/4 plots, 1/1 module.
- Holdout exclusion verified: **YES** (synthetic only; no market data touched).

## Issues

### Critical

1. **Collapsed cross-cell/cross-check verdict violates the binding per-stratum doctrine.**
   - File: `code/run_experiment.py` `main()` verdict block, lines ~462–488 (`cov_pass =
     bool(cov_df["pass"].all())` and `overall = rec_pass and monotone and … and (cov_pass in
     (True, None))`); emitted as `results/verdict.json::overall_pass_literal`. Scope framing
     (`scope.md` "Evidence FOR (PASS): *all three* hold … on **every** (type, n) cell") invited it.
   - Doctrine: `cf-capgeo-001.md:137` ("Default to per-stratum adjudication; any pooled statistic is
     a disclosure until cross-cell homogeneity is itself demonstrated"); `:204` ("No pooling across
     … cells without a demonstrated-homogeneity claim"); D0 `:139` ("Scoring outputs … none
     collapsed"); D0 `:171–173` ("exactly one verdict per stratum. The Phase 018 verdict
     **conjunction** is a Phase 018 D0 item"). The cross-stratum conjunction is explicitly **reserved
     for Phase 018** and a collapsed cross-cell verdict is a *disclosure*, never the verdict.
   - Description: `overall_pass_literal` (and the per-check `.all()` collapses feeding it) reduce 198
     per-cell results to one boolean and present it as the headline verdict — the exact cross-cell
     conjunction the doctrine prohibits/defers. No cross-cell homogeneity claim accompanies it (and
     none holds — the strata are demonstrably heterogeneous: recovery PASS-all, coverage binding only
     at n≥30, one shrinkage marginal).
   - Impact: **verdict-shape material** — it changes what "the verdict" *is* and which stratum binds.
     It made a near-universally-calibrated estimator read as a blanket FAIL and required the auditor
     to reconstruct the per-stratum picture the doctrine says should be primary.
   - Materiality class: **representation-material, NOT number-material.** Every per-cell value is
     correct and hash-verified (see Info 2); **no recompute of the binding bootstrap is required.**
   - Fix (route to `experiment-developer`): restructure the verdict object to **per-stratum primary** —
     a recovery verdict (all cells), a coverage verdict **resolved by n** (PASS n≥30; n=15 reported as
     a disclosed sparse-stress diagnostic), and a shrinkage verdict (monotone + sparse PASS; n=2000
     predeclared marginal). Remove `overall_pass_literal`, or demote it to a clearly non-binding
     convenience flag annotated "collapsed — not the binding verdict; see per-stratum verdicts; no
     cross-cell homogeneity claimed." Regenerate `verdict.json` from the existing, hash-verified
     per-cell tables (deterministic — the binding numbers do not change). Also tighten `scope.md`'s
     PASS framing so it does not read as an `.all()` mandate.

### Warning

1. **Residual gate-granularity even within the per-stratum layer.**
   - File: `code/run_experiment.py` coverage pass column; `verdict.json`.
   - Description: even after C1's per-stratum restructuring, the coverage stratum boundary (binding at
     n≥30 vs n=15-as-diagnostic) is a governance/D0 reading, not yet ratified.
   - Impact: which n-cells are *binding* for coverage is a D0 decision; until ratified, the coverage
     stratum verdict is provisional.
   - Fix: ratify the n≥30 coverage binding via dated `D0-amendment` (see Disposition). No code change
     beyond C1.

2. **n=15 expectancy CI under-coverage — downstream propagation risk.**
   - File: `src/xen/ass.py::bootstrap_cis` (method property, not a bug).
   - Description: `ASS` expectancy CIs under-cover (down to 0.833) at n=15; nominal by n≥30.
   - Impact: if EXP-077/Phase-018 make **expectancy** edge-calls on signal types with effective
     n<~30, false-edge rate could exceed nominal. (Operator's stated concern.)
   - Fix: bind a downstream control (see Disposition) — not an estimator change at this step.

### Info

1. **n=2000 shrinkage rich-pull = 0.0566** is exactly the predeclared analytic `k/(n+k)` marginal
   (plan §R3/Step 5; pre-exec disclosure #3), surfaced via `marginal_flag`, not a silent pass.
2. **Determinism + anchor independently confirmed**: all four table hashes match recorded values;
   anchor exact; KDE gap 1.2e-8. The new process-pool parallelism is byte-identical.
3. **Recovery on negative-median skews passes** (`Sminus`/`Sminus0` medians within band), confirming
   the earlier D1 median-sign disclosure does not affect recovery validity.

## Materiality & Re-Audit Requirements

- **C1 (Critical) is blocking but representation-only.** It is verdict-shape material — it changes
  what "the verdict" is and which stratum binds — so it blocks advancing the verdict object to
  Stage 6 until fixed. It is **representation-material, not number-material**: every per-cell value is
  correct, reproducible, and hash-verified, so **the binding bootstrap is NOT re-run**; the fix edits
  the verdict-assembly in `main()` (and the `scope.md` PASS framing) and regenerates `verdict.json`
  deterministically from the existing per-cell tables. This is the one exception to "document-and-
  proceed" here: it cannot be down-classified, because a binding doctrine (per-stratum adjudication)
  is violated by the emitted verdict object.
- **The Warnings are non-blocking**: numbers are correct and independently reproduced; they concern
  governance reading (coverage stratum boundary) and downstream propagation control, neither of which
  changes a computed value.
- **Re-audit / rerun**: route **C1** to `experiment-developer` for the verdict-representation fix;
  **re-audit is limited to confirming the restructured `verdict.json` is per-stratum and regenerated
  from the unchanged, hash-matching CSVs** — no re-execution of the multi-hour coverage pass. The
  coverage FAIL itself is the genuine measured outcome (sense ii), not a numerical defect; the
  estimator is not changed at this step (see Disposition).

## C1 Re-Audit (2026-06-20 — RESOLVED, no recompute)

Routed C1 to `experiment-developer`; verified the fix:

- **Verdict object is now per-stratum.** `results/verdict.json` carries `strata.recovery`
  (PASS, 198/0, worst ratio 0.722 exp / 0.702 med), `strata.coverage` resolved **per-n** (`by_n` for
  all 9 n; `verdict_n_ge_30: PASS`; n=15 expectancy listed under `sparse_stress_diagnostic`;
  `binding_boundary` marked "PENDING D0-amendment ratification — not prejudged"), and
  `strata.shrinkage` (monotone+sparse PASS; n=2000 predeclared marginal flagged). `overall_pass_literal`
  is removed; the only collapsed field is `collapsed_convenience_flag` (value `false`), explicitly
  captioned NON-BINDING with the `cf-capgeo-001.md:137` citation. **Doctrine-compliant.**
- **No recompute.** Regenerated via `--rebuild-verdict`, which reads the existing tables +
  `integrity.json` and rewrites only `verdict.json`. The four table SHA-256s are **byte-identical
  before and after** the rebuild (re-verified) and still match `integrity.json::table_sha256`. The
  binding bootstrap was not re-run.
- **Numbers reconcile.** Every per-stratum value in the regenerated verdict matches the auditor's
  independent re-derivation from the CSVs (recovery worst ratios; n=15 expectancy fail set U0/B_neg/
  B_zero/B_pos; `verdict_n_ge_30=PASS`; n=2000 pull 0.0566).
- **Code:** `build_verdict` is a pure function of the tables; `py_compile` + `ruff` clean; scope/bands/
  seeding untouched.

**C1 status: RESOLVED.** No blocking finding remains. The substantive disposition below is unchanged
(it was always the per-stratum view) and now matches the emitted verdict object.

## Disposition (auditor's call — operator steer weighed)

The operator favours (c) an estimator change now, citing downstream propagation. I weighed that and
**recommend (b) + a binding downstream guard, holding (c) in reserve** — not (a) bare disclosure, not
(c) immediate estimator surgery.

**Recommended (routes to Stage 8 governance + operator for a dated D0-amendment):**

1. **Bind Check-2 coverage at n≥30** (keep n=15 in the **recovery** leg, which passes, and report
   n=15 coverage as a disclosed sparse-stress diagnostic). Justification: n=15 is explicitly
   "sparse stress" in D1; the percentile mean-bootstrap under-covers there by mathematical necessity
   (independently reproduced), so binding [0.86,0.94] at n=15 tests the bootstrap's known floor, not
   `ASS`'s calibration. Verified: **0 coverage fails at n≥30** → under this reading Check 2 PASSES.
2. **Read the rich-stability bound** as "monotone-decreasing, ≤~6% at n=2000, <2% by n=8000" (binding
   rich anchor n≥8000), or set `k`/the rich anchor explicitly — the n=2000 cell is the predeclared
   analytic marginal, not a failure.
3. **Convert the operator's propagation concern into a checkable gate (mandatory carry-forward):** the
   amendment must record a **binding** constraint that EXP-077/Phase-018 expectancy edge-calls on
   types with effective n<30 are prohibited or treated as weakened evidence / deferred to the median
   leg, **and** that EXP-077's FPR leg (D2.2) include a small-n stratum to empirically confirm the
   under-coverage does not inflate FPR under the moving-block bootstrap.

**Why not (c) now:** an estimator change (BCa/studentized) amends a **frozen** pipeline (D3) and forces
a multi-hour EXP-076 re-run to fix a regime (n=15, mean only) that (i) is a known statistical floor,
not an `ASS` defect; (ii) is governed downstream on real data by the moving-block bootstrap and the
FPR gate, where the actual edge-calls live; and (iii) where BCa's acceleration estimate is itself
fragile at n=15. It is disproportionate and premature at a characterisation/validation step. **Escalate
to (c) only if EXP-077's small-n FPR stratum shows inflated false edges** — that empirical signal, not
this synthetic coverage floor, is the correct trigger.

**Routing:** pass to **Stage 6 (interpretation)** and **Stage 8 (governance)** with this disposition;
the gate-granularity amendment and the binding downstream carry-forward are governance/operator
ratifications (dated `D0-amendment-*`), not code fixes. The literal `overall_pass_literal=false` stands
as the honest literal result; the recommendation is the qualified PASS-at-n≥30 reading plus the
downstream guard.
