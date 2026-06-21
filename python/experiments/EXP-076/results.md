# Results Interpretation: EXP-076 (`ASS`/VAL-001 — Synthetic-Substrate Recovery, G-017a)

> Phase 017 CF-CAPGEO-001 qualifier validation. **Read per stratum, not as one pooled verdict**
> (binding doctrine `cf-capgeo-001.md:137,204`; D0 §D1/§D4; `LESSON-001-per-stratum-verdict.md`).
> Source: `results/verdict.json` (per-stratum), the four result tables, `integrity.json`, the 4 plots,
> and `audit.md` (CONDITIONAL PASS, C1 resolved). Synthetic only — 0 slots, 0 TEST reads, holdout
> untouched.

## The binding question

*Before `ASS` is allowed to adjudicate any market signal, can it recover ground truth where ground
truth is known — estimate expectancy and median without material bias, produce calibrated
uncertainty, and shrink sparse types toward the pooled prior as designed?*

**Answer: YES on the binding leg (recovery), with one calibration caveat confined to the n=15 sparse
floor and one predeclared shrinkage marginal — both governance dispositions, neither a defect.**

---

## Stratum 1 — Recovery bias (binding): **SUPPORTED**

| Estimand | Cells | Fails | Worst `median\|err\|/SE` | Band | Verdict |
|----------|-------|-------|--------------------------|------|---------|
| Expectancy | 99 | 0 | **0.722** (`Sminus0`, n=500) | 0.85 | PASS |
| Median | 99 | 0 | **0.702** (`U2`, n=250) | 0.85 | PASS |

`ASS`'s un-pooled estimator core recovers both estimands to within the `0.85·SE_true` band on **every**
`(type, n)` cell across the full unimodal / left-&-right-skew / bimodal / sparse span — including the
**negative-median skews** (`Sminus`, `Sminus0`) whose D1 annotations were inconsistent (the recovery
is computed against the authoritative DGP ground truth, so the annotation mismatch is immaterial here).
The worst observed ratio (0.722) sits comfortably under the band, and well above the unbiased-estimator
floor of `0.6745·SE` — exactly the discriminating window the bite check calibrated (correct estimator
~0.67·SE pass, +1·SE bias fails). *Plots 01/02 (`recovery_bias_*`) show every type's curve under the
0.85 line at all n.*

**This is the core G-017a ask, and it passes cleanly.** The estimator is unbiased for expectancy and
median across all tested shapes and sample sizes.

## Stratum 2 — CI coverage (resolved per-n): **SUPPORTED at n≥30; n=15 expectancy is a disclosed sparse-stress diagnostic**

- **n ≥ 30 (binding region):** the 90% bootstrap CI covers truth in `[0.86, 0.94]` for **both**
  estimands at **every** n from 30 to 8000 (`verdict_n_ge_30 = PASS`; 0/176 cells out of band).
  Coverage rises monotonically toward nominal 0.90 with n (expectancy min by n: 0.872 → 0.876 → 0.885
  → 0.890 → 0.891 → 0.892 → 0.888; median in-band throughout).
- **n = 15 (sparse stress):** 4 expectancy cells fall just below the 0.86 floor — `U0` 0.8595,
  `B_zero` 0.857, `B_pos` 0.8565, `B_neg` 0.833 — while **median coverage is in-band at n=15** (min
  0.876) and the whole n=15 expectancy row is depressed (mean 0.864, straddling the floor within the
  ±0.013 MC band; the pass/fail split among n=15 cells is itself near MC noise). *Plot 03
  (`ci_coverage`) shows the n=15 dip on the expectancy panel only.*

**Mechanism (from the audit, independently reproduced):** this is the textbook small-sample
under-coverage of the **5th/95th percentile bootstrap of the mean** — its coverage error is `O(1/√n)`
and it is not skew-corrected, so at n=15 the skewed sampling distribution of the mean is under-covered.
It is **expectancy-specific** (the median is robust at small n → median coverage holds) and
**shape-ordered** (near-nominal on the clean normal `U0`, worst on the bimodal `B_neg` with its
catastrophic minority mode). The auditor's independent micro-sim reproduced both the under-coverage and
the normal-vs-bimodal ordering (0.871 vs 0.843) — the fingerprint of a genuine statistical effect, **not
a defect in `xen.ass.bootstrap_cis`** (a bug would not spare clean normals or the median).

**Interpretation:** `ASS` produces calibrated expectancy uncertainty wherever it will actually be used
(n≥30); at the n=15 floor its expectancy CI is mildly over-confident. The n≥30-binding / n=15-diagnostic
boundary is a **governance decision, not prejudged here** (`binding_boundary` flagged PENDING).

## Stratum 3 — Shrinkage behaviour (binding): **SUPPORTED, with the predeclared n=2000 marginal disclosed**

- **Monotone** weight `n/(n+k)` in n: confirmed (implemented pull reproduces the closed form
  `k/(n+k)` to ~1e-16 — no weighting bug).
- **Sparse pull (n ≤ 30) ≥ 0.25:** satisfied (pull 0.889 at n=15, 0.80 at n=30).
- **Rich stability (n ≥ 2000) < 0.05:** the **single** literal breach is the **predeclared analytic
  marginal** at n=2000 — `pull = 120/2120 = 0.0566`, ~0.7pp over the literal bound, an exact
  consequence of `k = median-n = 120`. It is surfaced via `marginals` (not silently passed); n=8000
  pull is 0.0148 (well under). *Plot 04 (`shrinkage`) marks the n=2000 point against the 0.25/0.05
  reference lines.*

Shrinkage behaves exactly as designed: it pulls sparse types hard toward the pooled prior and leaves
rich types nearly untouched, with the one boundary cell behaving as the plan predicted in advance.

## Integrity

- **Anchor:** `xen.ass` un-pooled direct expectancy `== numpy.mean` to `diff = 0.0`; KDE-integrated
  expectancy agrees to `1.2e-8` (≪ the `0.02·σ` flag) → KDE integration is unbiased for the mean.
- **Determinism:** all three tables (recovery / shrinkage / ground-truth) byte-identical on the second
  pass; on-disk CSV SHA-256s match `integrity.json::table_sha256` (re-verified by the audit, and
  unchanged across the `--rebuild-verdict` regeneration).

## Audit caveats carried

- Verdict is reported **per stratum**; the collapsed `collapsed_convenience_flag` (value `false`) is
  **non-binding** and must not be read as a blanket FAIL (audit C1, resolved).
- The n=15 expectancy under-coverage and the n=2000 shrinkage marginal are the **genuine measured
  outcome**, not implementation defects; no estimator change was made at this step.

---

## What G-017a should conclude

**`ASS` recovers ground truth — the binding G-017a question is answered YES.** The estimator core is
unbiased for expectancy and median across the entire synthetic shape span (Stratum 1), produces
calibrated CIs everywhere it will be used (Stratum 2, n≥30), and shrinks as designed (Stratum 3). The
two open items are **governance dispositions on disclosed, mechanism-explained boundary behaviour**, not
recovery failures. `ASS` is a trustworthy *estimator*; calibration under the live protocol and
shape-sight remain owed by EXP-077/078 (below).

## Governance dispositions for Stage 8

**(a) Coverage binding boundary (dated `D0-amendment`).** Ratify coverage as binding at **n ≥ 30**, with
**n = 15 expectancy** recorded as a **disclosed sparse-stress diagnostic** (the percentile mean-bootstrap
floor, not an `ASS` defect; median coverage holds at n=15). Justification: n=15 is explicitly
"sparse-stress" in D1, and the under-coverage is mathematically intrinsic to the bootstrap, independently
reproduced. Alternative readings (e.g. binding only the n≥8000 rich anchor for the related shrinkage
bound) are equivalent in outcome. **Do not** change the frozen percentile-bootstrap estimator at this
step — see (b) for the actual downstream control.

**(b) Downstream propagation guard + n=2000 reading.**
- Carry a **binding constraint** into EXP-077 / Phase-018: **no expectancy edge-calls on signal types
  with effective n < 30** (or treat them as weakened evidence / defer to the median leg), since that is
  where the expectancy CI under-covers.
- Add a **small-n FPR stratum to EXP-077**: empirically confirm — on real data under the moving-block
  bootstrap — that the under-coverage does **not** inflate the false-edge rate. That empirical FPR
  signal, not this synthetic n=15 coverage floor, is the correct trigger for any future estimator change
  (BCa/studentized) — which would be a separate D0-amendment + re-run, premature now.
- **n=2000 rich-pull marginal:** read the rich-stability bound as "monotone-decreasing, ≤~6% at n=2000,
  <2% by n=8000" (binding rich anchor n≥8000), **or** set `k` / the rich anchor explicitly via the same
  `D0-amendment`. It is the predeclared analytic marginal, not a failure.

## Follow-up (new scopes, not extensions of EXP-076)

- **EXP-077** (`ASS`/VAL-002): dogfood + calibration under `WF-EXPANDING`, with the **small-n FPR
  stratum** added per (b). Owes FPR/MDE/`P(>X)` reliability and the moving-block coverage check.
- **EXP-078** (`ASS`/VAL-003): shape discrimination + `k`-sensitivity sweep. Owes shape-sight; will also
  exercise the rich-pull bound across the `k`-grid, informing the (b) `k`/anchor decision.
