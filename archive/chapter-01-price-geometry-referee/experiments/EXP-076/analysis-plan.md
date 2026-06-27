# Analysis Plan: Experiment EXP-076

> `ASS/VAL-001` — `ASS` synthetic-substrate recovery (Phase 017 CF-CAPGEO-001 qualifier validation,
> G-017a cheap screen). Scope: `python/experiments/EXP-076/scope.md`. Frozen D0:
> `checkpoints/2026-06-20-017-capgeo-qualifier-validation/D0-predeclarations.md` (§D1, §D2.1, §D3, §D6).
> Synthetic only — 0 slots, 0 TEST reads, no market data, holdout untouched.

## Objective

Establish, on synthetic populations with **known** expectancy/median/shape, that the `ASS` qualifier's
estimator core recovers ground truth to the D0 §D2.1 fixture-calibrated tolerance, produces calibrated
90% bootstrap CIs, and shrinks sparse signal types toward the pooled prior as designed. This is the
necessary precondition (G-017a) before `ASS` is calibrated under `WF-EXPANDING` (EXP-077) and tested
for shape discrimination (EXP-078). The deliverable is a machine-readable PASS/FAIL recovery table
plus four diagnostic plots; the verdict is mechanical against the three D2.1 bands.

We must determine three things, each a frozen D2.1 criterion:
1. **Recovery bias** of expectancy and median, per `(type, n)`, vs `0.85·SE_true(n)`.
2. **CI coverage** of the 90% bootstrap CI for expectancy and median, per type, vs `[0.86, 0.94]`.
3. **Shrinkage behaviour** on the `SP` mixed-`n` population: monotonicity in `n`, sparse pull ≥25%,
   rich move <5%.

---

## Resolved design decisions (predeclared, before any results)

### R1 — Which estimate the recovery band applies to (the recovery-vs-shrinkage tension)

The scope flags that shrinkage *deliberately* biases sparse cells toward the pooled prior, which would
make a literal "shrunk-estimate recovers its own cell's truth" criterion **self-contradictory** for
sparse cells (shrinkage is a bias-for-variance trade — a sparse cell is *supposed* to be pulled off
its own noisy estimate). Resolution, predeclared:

- **Recovery legs (Check 1 + Check 2) are applied to the per-type _un-pooled_ `ASS` estimate** — each
  `U/S/B` type at each `n` is scored from its own `R_REP` draws with **cross-type shrinkage disabled**
  (equivalently `weight = 1`, i.e. the standalone within-type KDE→expectancy/median→bootstrap).
  Rationale: recovery measures the *estimator core* (adaptive KDE + bootstrap), which must be ~unbiased
  on a single known type given its own data. This is the quantity for which "recovers truth" is a
  coherent ask, and it matches the bite-check reference (which used the un-pooled sample statistic).
- **Shrinkage behaviour (Check 3) is the _only_ leg that exercises pooling**, and it runs on the `SP`
  population (where a genuine multi-type pool exists). There it is *correct* for sparse members to be
  pulled toward the prior; that pull is the thing being measured, not a recovery failure.
- **Consistency cross-check (rich cells, non-gating):** for rich members (`n ≥ 2000`) the shrinkage
  weight `n/(n+k) ≈ 1`, so the shrunk and un-pooled estimates nearly coincide; we additionally report
  shrunk-estimate recovery for the rich cells and confirm it still satisfies the band (it must, because
  the estimate barely moves — this links the two legs without making sparse cells fail by construction).

This keeps the two criteria orthogonal and non-contradictory: un-pooled recovery isolates estimator
quality; SP shrinkage isolates pooling behaviour.

### R2 — `SE_true(n)` definitions (the recovery-band denominators)

- **Expectancy:** `SE_true(n) = σ_type / √n`, with `σ_type` the **known closed-form SD** of the DGP:
  - `U`: `σ = 1.0`.
  - Skew-normal `S`: `σ = ω · √(1 − 2δ²/π)`, `δ = α/√(1+α²)` (closed form).
  - Bimodal `B`: `σ = √(E[X²] − E[X]²)`, `E[X²] = w(μ₁²+σ₁²) + (1−w)(μ₂²+σ₂²)`, `E[X] = wμ₁+(1−w)μ₂`
    (closed form).
  Each `σ_type` is recorded in the ground-truth table and **MC-cross-checked** (10⁷ draws) to ≤1%.
- **Median:** `SE_true(n) = MC_median_SE(type, n)`, defined as the **standard deviation of the sample
  median over `N_MED_SE` independent size-`n` draws** from the known DGP (`N_MED_SE = 10_000`, fixed
  seed, distribution-free — no `1/(2f(m)√n)` parametric form, which would assume a density estimate).
  Recorded per `(type, n)` in the ground-truth table at ratification.

The band is **SE-relative**, so it auto-widens for small `n` (e.g. `n=15` sparse stress gets a
proportionally larger absolute allowance); an unbiased estimator passes at every `n` by construction,
which is exactly the discriminating property the bite check confirmed (correct estimator 0.67·SE pass,
+1·SE systematic bias fail).

### R3 — Integrity anchor (production estimator ↔ bite-check reference)

`ass.md` step 4 states the shrunk-KDE expectancy may be computed either by integrating `x·pdf̃(x)` or
by the algebraically-equivalent **weighted-blended sample mean** (simpler). `xen.ass` emits **both**
forms. The anchor, on a fixed deterministic array for one shared cell (`U2`, `n=250`, replicate 0,
recorded seed):
- **`xen.ass` un-pooled direct-mean expectancy == `numpy.mean(x)` to ≤ 1e-12** (matches the
  bite-check `expectancy_hat`). This is a hard integrity assertion.
- The **KDE-integrated** expectancy is compared to the direct-mean form on the same array; the
  (small) smoothing/boundary gap is **reported as a diagnostic**, not gated. If the gap exceeds a
  recorded sanity bound (e.g. >0.02·σ on this cell) it is flagged for the audit, since it would imply
  the KDE integration is materially shifting the estimand.

### R4 — Determinism (D6)

Master seed `20260620`; per-draw seed = a deterministic function of `(type_id, n, replicate)` (e.g.
`numpy.random.SeedSequence([master, type_id, n, replicate])` → `default_rng`). A full second pass of
the experiment must be **byte-identical** on all emitted tables (asserted by re-run hash compare).

---

## Methodology

### Step 1 — Ground-truth table (closed-form + MC), frozen at ratification

- **Method:** for every D1 type, record closed-form expectancy and `σ_type` (R2); record the median
  ground truth as a **10⁷-draw MC estimate** (D1) and `MC_median_SE(type, n)` (R2) for every `n`.
- **Why sufficient:** ground truth must exist before recovery can be measured; closed-form where
  available, MC where not (skew/bimodal medians). Distribution-free, no parametric SE assumption.
- **Simpler alternative considered:** analytic median SE `1/(2f(m)√n)` — rejected: requires a density
  value `f(m)`, reintroducing the estimation error we are trying to measure against. MC is exact for
  the known DGP.
- **Assumptions:** the DGP samplers are correct (re-used from `bite_check.py`, audited) and MC at 10⁷
  draws has negligible error vs the 0.85·SE bands. No time-ordering — synthetic iid.
- **Expected output:** `results/ground_truth.csv` (type, μ_truth, σ_type closed-form & MC,
  median_truth, MC_median_SE per `n`), persisted for the audit to re-derive.

### Step 2 — `xen.ass` qualifier (the one new module)

- **Method:** implement the `ASS` pipeline (D3 / `ass.md`): adaptive **kNN-bandwidth KDE**
  (`k_bw = max(5, round(√n))`) → empirical-Bayes **shrinkage** toward the pooled (all-types) KDE
  (`weight = n/(n+k)`, `k` = median sample size) → **bootstrap CI** (`N_BOOT = 10_000`, 5th/95th pct,
  within-type resample). Outputs (none collapsed): expectancy (both KDE-integrated and direct
  weighted-mean forms), median, expectancy/median bootstrap CIs, shrinkage weight (diagnostic). A
  `shrink=False` / un-pooled mode is exposed for the recovery legs (R1).
- **Why this method:** it is the family's binding qualifier under validation; building it as a reusable
  module (reused unchanged by EXP-077/078 + Phase 018) is the correct home, not experiment-local code.
- **Simpler alternative considered:** a fixed-bandwidth KDE or raw sample statistics — rejected: the
  whole point of `ASS` is adaptive bandwidth + shrinkage; we must validate the actual pipeline, not a
  proxy (the bite-check proxy already served its threshold-calibration purpose).
- **Assumptions:** within-type iid resample is valid for the synthetic iid draws (the real-data
  moving-block variant is EXP-077, explicitly out of scope here). KDE is non-parametric — no
  distribution shape assumed (programme principle).
- **Expected output:** `xen.ass` module with documented public functions + the dual expectancy forms.

### Step 3 — Check 1: Recovery bias (expectancy + median), un-pooled

- **Method:** for each `(type ∈ U∪S∪B, n)`, draw `R_REP = 2000` replicates; on each, compute the
  **un-pooled** `ASS` expectancy and median; record `bias_med = median_over_replicates(|estimate −
  truth|)`. **PASS** iff `bias_med ≤ 0.85·SE_true(n)` for **both** estimands on **every** cell.
- **Why sufficient:** the median-absolute-error vs an SE-relative band is exactly the D2.1 criterion the
  bite check calibrated; it separates a correct estimator from a ≥1·SE systematic bias.
- **Simpler alternative considered:** signed-mean bias `|mean(estimate−truth)| ≤ 0.1·SE` (the D2.1
  operator alternative) — we **also emit** signed bias as a secondary diagnostic column so the audit
  can see bias-vs-noise directly, but the **binding** form is the median-|error| band the bite script
  tested (avoids re-anchoring a frozen criterion).
- **Assumptions:** `R_REP=2000` gives a stable replicate-median (MC noise on the band ≪ the band).
- **Expected output:** `results/recovery.csv` (type, n, estimand, truth, bias_med, signed_bias,
  SE_true, band=0.85·SE, pass) + the headline pass/fail.

### Step 4 — Check 2: CI coverage (expectancy + median)

- **Method:** across the same `R_REP` replicates, coverage = fraction whose 90% bootstrap CI contains
  the ground-truth estimand. **PASS** iff `coverage ∈ [0.86, 0.94]` for expectancy and median on every
  type. Report the MC band (`±1.96·√(p(1−p)/R_REP) ≈ ±0.013`, widened to ±0.04 in D2.1 to absorb
  estimator imperfection).
- **Why sufficient:** direct empirical coverage is the definitional check of bootstrap-CI calibration;
  no parametric coverage formula is trustworthy for skew/bimodal.
- **Simpler alternative considered:** report CI width only — rejected: width without coverage does not
  test calibration.
- **Assumptions:** bootstrap percentile CI is the D3-specified interval; `N_BOOT=10_000` is the
  programme convention (sufficient for stable 5th/95th pct).
- **Expected output:** `results/coverage.csv` (type, n, estimand, coverage, mc_band, pass).

### Step 5 — Check 3: Shrinkage behaviour (SP population)

- **Method:** assemble the `SP` population (mixed-`n` members across the grid, median-`n` ≈ 120 → `k`
  ≈ 120). For each member compute the **pull fraction** `pull = (1 − weight) = k/(n+k) = |shrunk −
  raw| / |pooled_prior − raw|`. Verify: (a) `weight = n/(n+k)` **monotone non-decreasing in `n`**
  (computed, not assumed — guards an implementation bug); (b) **sparse** members (`n ≤ 30`) have
  `pull ≥ 0.25`; (c) **rich** members (`n ≥ 2000`) have `pull < 0.05`.
- **Why sufficient:** the pull fraction is the exact, parameter-free realisation of the D2.1 sparse/rich
  bounds and is symmetric across both (both phrased as "fraction of the way toward the prior").
- **Predeclared analytic prediction + a flagged marginal (no goalpost moving):** with `k = median-n ≈
  120`, the pull fraction `k/(n+k)` is `≈0.80` at `n=30` and `≈0.89` at `n=15` (both ≫ 0.25 ✓), and
  `≈0.0148` at `n=8000` (≪ 0.05 ✓) — **but `≈0.0566` at `n=2000`, which exceeds the literal `<0.05`
  rich bound by ~0.7pp.** This is an analytic consequence of `k=120`, not a code defect, and the D2.1
  shrinkage bounds were **not** part of the 2026-06-20 bite check (only recovery/coverage/FPR/shape
  were). The plan therefore: (i) reports the exact pull at every `n`; (ii) evaluates the literal
  bounds; (iii) if the **only** rich exceedance is the `n=2000` cell at ~0.057, records it as a
  **predeclared known-marginal** and routes the disposition to Stage-4/Stage-8 governance — either
  read the rich-stability bound as "monotone-decreasing, ≤~6% at n=2000 and <2% by n=8000" (the
  binding rich anchor being `n≥8000`), or open a dated `D0-amendment` setting `k` or the rich anchor
  explicitly. **The verdict will not be silently reinterpreted; the marginal is surfaced, quantified,
  and adjudicated.**
- **Simpler alternative considered:** assert the closed-form `k/(n+k)` only — rejected: we must confirm
  the *implemented* shrinkage reproduces the closed form (catches a weighting bug), so we compute it
  empirically and reconcile to `k/(n+k)`.
- **Assumptions:** the `SP` pooled prior is the all-member pooled KDE (D3 shrinkage target analogue).
- **Expected output:** `results/shrinkage.csv` (member, n, weight, pull, monotone_ok, sparse_ok,
  rich_ok, marginal_flag).

### Step 6 — Determinism + integrity anchor

- **Method:** run the integrity anchor (R3) and assert the 1e-12 reconciliation; re-run the full
  experiment a second time and assert byte-identical output tables (hash compare).
- **Expected output:** `results/integrity.json` (anchor diff, kde_vs_directmean_gap, second_pass_hash
  match).

---

## Visualisations

1. **Expectancy recovery bias vs `n`, by type** — `bias_med` and the `0.85·SE` band per type; shows the
   estimator is within band at every `n` (or where it breaches). Answers Check 1 (expectancy).
2. **Median recovery bias vs `n`, by type** — same, against the MC-median-SE band. Answers Check 1
   (median); separated because the median band uses a different SE definition (R2).
3. **CI coverage vs `n`, by type** (expectancy + median series) — with the `[0.86, 0.94]` band marked.
   Answers Check 2; visualises under-/over-coverage directly.
4. **Shrinkage weight `n/(n+k)` and pull fraction `(1−w)` vs `n` on `SP`** — with the 0.25 (sparse) and
   0.05 (rich) reference lines and the flagged `n=2000` marginal annotated. Answers Check 3.

## Interpretation Guide

- **PASS (→ G-017a clear, EXP-077 authorized):** all three checks pass on every binding cell — recovery
  bias ≤ `0.85·SE` for expectancy *and* median on every `(type,n)`; coverage ∈ `[0.86, 0.94]` for both
  estimands on every type; SP shrinkage monotone with sparse pull ≥0.25 and rich pull <0.05 (subject to
  the `n=2000` marginal disposition). Means the `ASS` estimator core is unbiased, calibrated, and shrinks
  as designed — it is a trustworthy *estimator* (calibration under the protocol and shape-sight are still
  owed by EXP-077/078).
- **FAIL on recovery/coverage (→ feeds G-017 `DISCOVERY_ONLY` or a fix):** if `bias_med > 0.85·SE` on
  any cell, the estimator carries material bias on that shape (most likely on the skew/bimodal medians or
  the KDE boundary) → `ASS` cannot be trusted to adjudicate that shape; record which type/estimand and
  route. If coverage < 0.86 the bootstrap CI is over-confident (false edges downstream); > 0.94 it is
  conservative (misses real edges).
- **Shrinkage anomaly:** non-monotone weight ⇒ implementation bug (fix-and-rerun, verdict-material).
  Sparse pull <0.25 ⇒ shrinkage too weak (sparse cells trust their own noise — the exact failure ASS is
  meant to prevent). The `n=2000` rich pull ~0.057 is the predeclared known-marginal, adjudicated, not
  silently passed.
- **Inconclusive:** a cell where `MC_median_SE` is itself unstable (e.g. extreme bimodal multi-modality
  at `n=15`) → report the cell, do not let it silently pass; an inconclusive *binding* cell blocks the
  clean PASS and is disclosed to G-017.

## Implementation Safety Constraints (for `experiment-developer`)

- **No market data, no Parquet load, no holdout split** — synthetic generation only. The standard
  first-70% loader is intentionally absent.
- **Determinism (D6):** every RNG draw seeded from `(master, type_id, n, replicate)` via `SeedSequence`;
  no un-seeded `default_rng()` / global `numpy.random`. Second pass byte-identical (Step 6).
- **Bounded iteration:** the grid is `len(types) × len(n) × R_REP = ~11 × 9 × 2000` replicate draws,
  each with `N_BOOT = 10_000` resamples — the dominant cost. Vectorize the bootstrap (resample-index
  matrix → batched statistic) in NumPy; this is **causally safe** (synthetic iid, no temporal ordering
  to preserve). Use `tqdm` over the `(type, n)` outer loop.
- **Denominators / zero-baseline:** recovery uses absolute error in ATR units and an SE-relative band —
  **no percentage-improvement-against-zero metric** anywhere. The pull fraction's denominator
  `|pooled_prior − raw|` can be ~0 when raw ≈ prior (a rich cell already at the pool); guard the divide
  with a finite-fallback (if `|prior − raw| < ε`, the move is 0 by definition → pull = 0, rich-stable)
  and record the guard, never emit NaN/inf silently.
- **Separation:** synthetic generators → pure `xen.ass` computation → recovery/coverage/shrinkage checks
  → plotting → orchestration → `main()`; helpers return data, `main` logs concisely.
- **Real-price discipline:** N/A (synthetic ATR-unit returns); no HA/Renko prices anywhere.
- **No `k` tuning:** `k = median-n` is frozen; the `k`-grid sweep is EXP-078, not here.

## Complexity Check

- Statistical/validation checks: **3** / 3 (recovery bias, CI coverage, shrinkage behaviour).
- Visualisations: **4** / 4.
- New modules: **1** / 1 (`xen.ass`).
