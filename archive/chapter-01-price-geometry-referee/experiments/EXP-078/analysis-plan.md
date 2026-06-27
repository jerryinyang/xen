# Analysis Plan: Experiment EXP-078 — Shape Discrimination + `k`-Sensitivity (`ASS/VAL-003`)

> Phase 017 — CF-CAPGEO-001 Qualifier & Protocol Validation. Last experiment before terminal G-017.
> Synthetic only; 0 candidate slots, 0 counted TEST reads, holdout never touched.
> All thresholds frozen at D0 (`D0-predeclarations.md` §D2.5, §D3) — this experiment **measures**
> their operating characteristics; it does not tune them.

## Objective

Validate two things about the `ASS` qualifier on synthetic populations with known shape:

1. **Shape discrimination (binding, D2.5):** the frozen diagnostic
   `flag = (dip_p < 0.05) OR (|g| > τ_gap=0.30)`, with `dip_p` = Hartigan dip-test p-value and
   `g = (mean − median)/MAD`, **separates bimodal `B` (should-flag) from unimodal `U` (should-not-flag)**
   — false-flag on every `U` stratum ≤ 0.05, detection on every `B` stratum ≥ 0.80, for each `n ≥ 30`.
   This directly closes the EXP-074 gap where the anti-p-hacking guard was structurally blind to
   tail-shape (bimodal) effects.
2. **`k`-sensitivity (binding, D3/§7):** across the pre-registered shrinkage-constant grid
   `k ∈ {0.5×, 1×, 2×}·median-n ∪ {30, 500}`, the `ASS` binding **routing** (the EXP-076 recovery/
   coverage dispositions and the EXP-077 FPR/edge-call dispositions, recomputed per `k`) is
   **invariant**, or its `k`-dependence is **bounded and disclosed** such that no Phase-018 verdict
   would flip within the band.

Plus the `S`-family (skew) **disclosed characterization arm** (non-binding): where the asymmetric-but-
unimodal `Sminus/Sminus0/Splus` land on each diagnostic leg.

Everything is reported **per stratum** (per type / per `n` / per `k`); no collapsed cross-cell boolean
is binding (LESSON-001; D0 §8; EXP-076 audit C1). Collapsed summaries are captioned non-binding.

---

## Methodology

The harness reuses the frozen EXP-076 D1 generators and deterministic-seed machinery
(`gen_unimodal/gen_skewnormal/gen_bimodal`, `build_type_registry`, `rng_for(*key)` via
`SeedSequence([MASTER_SEED, *key])`, `MASTER_SEED = 20260620`, `N_GRID = (15,30,60,120,250,500,1000,
2000,8000)`, `R_REP = 2000`). The `ASS` core (`xen.ass`) is reused **unchanged** for all point/CI
estimands; the only code addition is one in-family `shape_diagnostic` function in `xen.ass` (Step 0).

### Step 0 — `xen.ass.shape_diagnostic` (the one in-family extension)

- **What it adds:** a pure function
  `shape_diagnostic(x, *, tau_gap=0.30, dip_alpha=0.05) -> ShapeDiag` returning
  `dip_stat`, `dip_p`, `g = (mean − median)/MAD`, the two per-leg booleans (`dip_flag`,
  `gap_flag`), and the combined `flag = dip_flag OR gap_flag`. `MAD = median_abs_deviation(x,
  scale=1.0)` (scipy). It is computed on the **raw sample** `x` only — it does **not** depend on the
  shrinkage `k`, the pool, or the KDE (recorded explicitly; see Step 3 rationale).
- **Why here, not in `code/`:** the diagnostic is a core qualifier output reused unchanged by all of
  Phase 018 (the co-primary tail diagnostic of CF-CAPGEO-001), exactly as the moving-block bootstrap
  was added to `xen.ass` by EXP-077. The module docstring already reserves "the density object reused
  by the EXP-078 shape diagnostics."
- **`MAD == 0` branch (zero-baseline discipline):** when `MAD == 0` (a degenerate sample, e.g. all
  ties), `g` is undefined → set `g = 0.0` and `gap_flag = False` (defer to the dip leg), and
  **increment an integrity counter** `mad_zero_count`. The continuous `U/S/B` DGPs at `n ≥ 15` give
  `MAD > 0` with probability 1, so the run must **assert `mad_zero_count == 0`** and report it; a
  nonzero count is surfaced, never silently passed.

#### Step 0a — dip-test implementation decision (resolved here)

The Hartigan dip statistic + p-value is **not** in numpy/scipy, and `diptest` is **not installed**
(pyproject has numpy ≥ 2.4.4, scipy ≥ 1.18.0 only). The D0 bite-check validated the `|g|` leg only and
explicitly deferred the dip leg to EXP-078.

- **Decision: add the `diptest` PyPI package as a project dependency** (preferred path (i) in the
  scope). Rationale: `diptest` wraps Hartigan & Hartigan's original reference C implementation of the
  dip statistic and the standard uniform-null p-value table/interpolation — it is the auditable,
  literature-standard computation. Hand-rolling the dip + a bootstrap-null p-value (path (ii)) is
  error-prone for a *binding* gate and would itself need a golden-value test against the same
  reference; adding the vetted package is the simpler, more robust choice and is consistent with the
  programme's "simplicity over complexity / justify complexity before using it" principle.
- **Determinism:** `diptest`'s p-value is computed from the analytic/interpolated uniform-null
  distribution (Hartigan table), **not** a random bootstrap — so it is **deterministic given `x`** (no
  seed needed for the p-value). The only RNG in the experiment is the sample draws (seeded by
  `rng_for`). Record the installed `diptest` version in `results/integrity.json`. A second full pass
  is byte-identical (Step 6).
- **Governance note (Stage 4):** adding `diptest` is a tooling/dependency change, **not** a D0
  amendment — the diagnostic *definition* (`dip_p < 0.05 OR |g| > 0.30`) is already frozen in D2.5.
  The pre-execution review ratifies the dependency addition and confirms it is pinned in
  `pyproject.toml` + `uv.lock`.
- **Golden anchor:** regardless of path, the implementation emits the dip statistic on a fixed
  reference vector (e.g. the published Hartigan example or a fixed seeded `U`/`B` sample) to
  `integrity.json` so the audit can re-derive it.

### Step 1 — Shape discrimination: false-flag (`U`) and detection (`B`) per `(type, n)` — BINDING

- **Method:** for each binding `(type, n)` with `type ∈ {U0,U1,U2,U3}` (negatives) and
  `type ∈ {B_neg,B_zero,B_pos,B_strong}` (positives) and each `n ∈ N_GRID`, draw `R_REP = 2000`
  independent replicate samples (`draw_cell_samples`, seed `rng_for(TAG_SAMPLE, type_id, n, rep)` —
  the **same** seed scheme as EXP-076, so cells reconcile), compute `shape_diagnostic` on each
  replicate, and form:
  - **false_flag_rate** (`U` types) = `#{flag == True} / R_REP` — a rate with fixed denominator
    `R_REP`, in `[0,1]`. No zero-baseline ratio.
  - **detection_rate** (`B` types) = `#{flag == True} / R_REP` — same fixed-denominator rate.
  - Each rate carries a **Wilson 95% interval** (binomial, the EXP-077 convention) so MC noise at
    `R_REP = 2000` is visible (half-width ≈ 0.01–0.02 near the boundaries).
- **Per-leg decomposition:** alongside the combined `flag`, record the **dip-only** rate
  (`#{dip_flag}/R_REP`) and the **gap-only** rate (`#{gap_flag}/R_REP`) per cell, so the audit can see
  which leg carries discrimination on each family (expectation: dip leg carries bimodal detection; gap
  leg carries left-skew asymmetry — confirmed, not assumed).
- **`τ_gap = 0.30` is FROZEN** — applied as the D0 operating point; this step measures its realized
  false-flag/detection, it does **not** search for a new `τ_gap`. (The D0 bite-check already fixed it
  at the `U`-vs-`B` ROC operating point: @0.30 false-flag 0.000 / detection 0.999, feasible window
  [0.105, 0.435].)
- **Why this method (sufficiency):** the question is a directly-measurable operating characteristic of
  a frozen classifier on labelled synthetic populations — a Monte-Carlo false-positive/true-positive
  rate with a binomial CI is exactly sufficient and maximally transparent. No model is needed.
- **Simpler alternative considered:** a single point estimate without the Wilson CI — rejected because
  boundary rates (≈0 false-flag, ≈1 detection) need their MC uncertainty shown to defend the
  per-stratum PASS, exactly as EXP-077 used Wilson on the FPR crossings.
- **Assumptions:** replicates are iid draws from the frozen DGP (true by construction); the binomial/
  Wilson interval assumes independent Bernoulli flags across replicates (true — independent seeds). No
  market-data / stationarity assumption applies (synthetic).
- **Expected output:** `results/shape_rates.csv` (one row per `(type, n)`: combined/dip-only/gap-only
  rate + Wilson lo/hi + `n` + role), and a binding **per-stratum** PASS/FAIL column
  (`U`: rate ≤ 0.05 ∧ Wilson_hi reported; `B`, `n ≥ 30`: rate ≥ 0.80).

### Step 2 — `S`-family asymmetry characterization — DISCLOSED, NON-BINDING

- **Method:** identical machinery as Step 1 applied to `type ∈ {Splus, Sminus, Sminus0}` across
  `N_GRID`; report the combined/dip-only/**gap-only** flag rates. These are unimodal but asymmetric, so
  the **gap leg is expected to flag the left-skew mean-weak cases (`Sminus`, `Sminus0`)** while the dip
  leg should largely *not* (unimodal). This puts on record how the diagnostic treats the dangerous
  left-skew shape that broke prior families' means, **before** Phase 018.
- **Not part of the binding PASS:** the binding false-flag rate uses **`U` only**; `S` cannot block or
  grant PASS. It is reported as characterization (`results/shape_skew.csv`) with an explicit
  non-binding caption.
- **Interpretation framing (pre-registered):** flagging `Sminus/Sminus0` is the **intended**
  behaviour (the diagnostic is named "bimodal/**asymmetric**") — it is reported as a *feature*
  (the gap leg sees left-skew), not a false positive. A high gap-flag rate on `S` is **consistent**,
  not contradictory.

### Step 3 — `k`-sensitivity sweep — BINDING

**Pre-registered rationale (resolves the scope's cross-leg tension #2):** the Step-0 shape diagnostic
is computed on the **raw sample** (dip, mean, median, MAD) and is therefore **a priori independent of
the shrinkage constant `k`**. Re-running the shape flag per `k` would be vacuous. The sweep is
**confined to the `k`-dependent quantities** — the shrunk point estimates and the dispositions built
on them (EXP-076 coverage + recovery; EXP-077 FPR edge-call) — recomputed per grid `k` on the **same
paired draws**.

- **Grid (frozen, D3):** `k ∈ {0.5×, 1×, 2×}·median-n ∪ {30, 500}`. `median-n` = the median of
  `N_GRID` actually swept (recorded at run time in `integrity.json`); `1×` = the EXP-076/077 default
  operating point. Five `k` values total (the `2×·median-n` may coincide with an anchor — dedupe and
  disclose).
- **Paired draws (no fresh sampling noise):** all grid-`k` evaluations reuse the **same** `R_REP`
  replicate draws per `(type, n)` — the seed scheme `rng_for(TAG_SAMPLE, type_id, n, rep)` is **not**
  perturbed by `k` (a `k` is a scoring parameter, not a draw parameter). The across-`k` comparison is
  therefore paired: any movement is attributable to `k`, not to resampling.
- **What is recomputed per `k`** (the `ASS` shrinkage uses `score(..., shrink=True, pool=<SP pool>,
  k_shrink=k)` and the shrinkage-shifted bootstrap, exactly as EXP-076/077):
  1. **Shrinkage weight** `w = n/(n+k)` and the **shrunk expectancy/median** point estimates on the
     `SP` mixed-`n` population (the EXP-076 shrinkage-behaviour object).
  2. **CI coverage** of the shrunk-expectancy 90% bootstrap CI on the binding types (EXP-076 D2.1
     coverage disposition), per `n`.
  3. **FPR edge-call disposition** (EXP-077 D2.2): the margin-calibrated `expectancy CI_low > m` rate
     on the null types `U0`/`B_zero` — recomputed per `k`. (The margin `m` is held at the EXP-077
     production-calibrated value; the sweep tests whether the *disposition* — controlled vs inflated —
     is stable across `k`, not a re-calibration of `m`.)
- **Routing-invariance definition (binding, precise):** for each disposition above, the **binding
  routing** is the per-stratum verdict label it produces (e.g. coverage `IN_BAND` vs `SUB_BAND`; FPR
  `CONTROLLED` (rate ≤ 0.05 ∧ Wilson_hi ≤ 0.075) vs `INFLATED`; shrinkage `monotone ∧ sparse-pull ≥
  0.25 ∧ rich-move < 0.05` PASS vs FAIL). **Routing-invariant** ⟺ for every binding stratum, the
  verdict label is **identical at all five grid `k`**.
- **Bounded-disclosure fallback (pre-registered):** if any label flips across the grid, report (a) the
  **`k` values** at which it flips, (b) the **absolute** magnitude of the driving quantity's change
  across the grid (Δ coverage, Δ FPR rate, Δ shrinkage weight — **absolute**, never a percentage of a
  possibly-zero baseline), and (c) an explicit assessment of whether the flip falls **inside** the
  band the default `k = median-n` already sits comfortably within. A flip is **bounded-and-disclosed
  PASS** iff (i) it occurs only at an extreme grid anchor (`k = 30` or `k = 500`) that is **not** the
  deployed `k`, **and** (ii) at the deployed `k = median-n` the disposition is unambiguously on the
  PASS side with margin. Otherwise it is an **undisclosed/unbounded routing flip → FAIL** (feeds
  G-017 `DISCOVERY_ONLY`).
- **Why this method:** `k`-sensitivity is a robustness question — does the single tunable knob move the
  conclusion? Re-running the existing, already-validated dispositions across a pre-registered grid on
  paired draws is the direct, simplest sufficient test; it introduces **no new endpoint**, only the
  `k` axis on existing ones.
- **Simpler alternative considered:** sweeping `k` on a single summary statistic (e.g. just the
  shrinkage weight) — rejected because the binding question is whether a *verdict* flips, which lives
  in the dispositions, not in `w` alone.
- **Assumptions:** the EXP-077 margin `m` is a fixed constant (true — carried from EXP-077 results);
  the `SP` pool is the frozen D1 mixed-`n` population (true). No new distributional assumption.
- **Expected output:** `results/k_sensitivity.csv` (one row per `(disposition, stratum, k)` with the
  driving quantity + the verdict label), and a binding **per-disposition** routing-invariance verdict
  with the bounded-disclosure annotations.

### Step 4 — Integrity anchor + determinism

- **Integrity anchor (1e-9):** at the default `k = median-n` (= `1×`), reconcile the `ASS`
  expectancy/median/coverage on the shared anchor cell `U2 / n = 250 / rep = 0` (the EXP-076 R3 anchor
  constants `ANCHOR_TYPE, ANCHOR_N, ANCHOR_REP`) against the EXP-076 recorded value to **≤ 1e-9** —
  confirming the shape extension did not perturb `xen.ass` behaviour. Also reconcile one EXP-077
  edge-call cell at the default `k`. Record both diffs in `integrity.json`.
- **Determinism (D6):** every RNG seed fixed via `rng_for`; emit a `sha256` of each results CSV
  (`_sha256_df`, the EXP-076 helper) to `integrity.json`. A second full pass via the
  `--verify-determinism` mode recomputes the hashes and asserts byte-identity; any mismatch →
  `PROTOCOL_DEFECT`.

---

## Visualisations (4 / 4 budget)

1. **Shape false-flag & detection vs `n`** (`plots/shape_rates_vs_n.png`): two panels — `U` false-flag
   rate (with the 0.05 line) and `B` detection rate (with the 0.80 line) vs `n`, one line per type,
   Wilson bands shaded. Answers: does the frozen `τ_gap=0.30` rule hit its operating targets at every
   `n ≥ 30`?
2. **`dip_p` and `|g|` distributions by family** (`plots/diag_distributions.png`): at a representative
   `n` (e.g. 500), violin/strip of `|g|` per type with the `τ_gap=0.30` line, and the share of
   `dip_p < 0.05` per type — the U-vs-B/S separation panel. Answers: how cleanly do the two legs
   separate the families, and where does `S` sit?
3. **`k`-sensitivity routing stability** (`plots/k_sensitivity.png`): the disposition-bearing
   quantities (coverage; null FPR rate; sparse-pull shrinkage) vs `k` across the grid, with PASS-band
   shading and the deployed `k = median-n` marked. Answers: does any verdict label flip across `k`?
4. **`dip_p` vs `|g|` scatter colored by family** (`plots/dip_vs_gap_scatter.png`): per-replicate (or
   per-cell-mean) scatter at a representative `n`, the `dip_p=0.05` and `|g|=0.30` decision lines
   drawn, points colored by `{U, S, B}`. Answers: visual confirmation that the combined OR-rule
   regions cleanly contain `B` (and `S` on the gap axis) while excluding `U`.

---

## Interpretation Guide (pre-registered, before results exist)

- **PASS (→ feeds G-017 `ASS_VALIDATED` on this leg)** iff **both**:
  - **Shape:** false-flag ≤ 0.05 on **every** `U` stratum (Wilson_hi reported) **and** detection ≥ 0.80
    on **every** `B` stratum at `n ≥ 30`, at `τ_gap = 0.30`; **and**
  - **`k`-sensitivity:** every binding disposition's routing label is invariant across the grid, **or**
    any flip is bounded-and-disclosed PASS (extreme-anchor-only, deployed-`k` unambiguous with margin).
- **FAIL (→ feeds G-017 `DISCOVERY_ONLY`)** if any `U` stratum false-flag > 0.05 (or Wilson_hi >
  0.075 on a binding stratum), OR any `B` (n ≥ 30) detection < 0.80, OR an undisclosed/unbounded
  routing flip across the `k`-grid. Recorded per stratum; no clean PASS.
- **`PROTOCOL_DEFECT`** only if the determinism second pass is not byte-identical.
- **INCONCLUSIVE (per stratum, never silent):** a cell too sparse to estimate a stable rate (e.g.
  `n = 15`, disclosed not gated for the shape leg; binding floor is `n ≥ 30`); a binding `U`/`B`
  (`n ≥ 30`) cell that cannot be estimated blocks the clean PASS and is surfaced to G-017. The `S` arm
  cannot, by itself, render the experiment inconclusive.
- **Reading `S` results:** a high gap-flag rate on `Sminus/Sminus0` **supports** the design (the gap
  leg sees the dangerous left-skew); it is **not** evidence against the diagnostic. A high *dip* rate
  on `S` (unimodal) would be a mild over-sensitivity worth noting (disclosed), since `S` is not bimodal.
- **Per-stratum doctrine:** the binding verdict is the **set** of per-stratum PASS/FAIL labels; any
  single collapsed "EXP-078 PASS" boolean is a **non-binding disclosure caption** only (LESSON-001).

## Implementation Safety Constraints (for `experiment-developer`)

- **No market data, no holdout, no temporal ordering** — synthetic iid draws only; the standard
  first-70% loader is intentionally absent (cross-check: the script must not import the timebars
  loader at all).
- **Determinism:** all randomness via `rng_for(*key)` (`SeedSequence([MASTER_SEED, *key])`); **`k` is a
  scoring parameter and must NOT enter any sample-draw seed** (paired draws). Record every seed; emit
  per-CSV `sha256`; `--verify-determinism` second pass asserts byte-identity.
- **Denominators:** false-flag/detection are `#{flag}/R_REP` with **fixed** denominator `R_REP=2000`
  (in `[0,1]`); the `k`-sensitivity magnitudes are **absolute** deltas of the driving quantity. No
  percentage-of-zero ratios anywhere.
- **`MAD == 0` branch:** explicit (`g=0`, `gap_flag=False`, increment `mad_zero_count`); **assert
  `mad_zero_count == 0`** and report it.
- **Reuse, don't re-derive:** reuse `xen.ass.score/bootstrap_cis` unchanged; reuse the EXP-076 D1
  generators, `build_type_registry`, `rng_for`, `_sha256_df`, and the `U2/250/0` anchor constants
  (import or copy verbatim with attribution — do not silently re-implement the DGPs differently).
- **Bounded iteration / progress:** the grids are bounded (`|types| × |N_GRID| × R_REP` for shape ≈
  11×9×2000; `× 5 k × dispositions` for the sweep). Use `tqdm` over the outer `(type, n)` / `(k)`
  loops. Vectorize replicate scoring with NumPy where the computation is genuinely independent
  (the dip-test is per-sample and may stay a bounded Python loop over replicates — keep explicit, do
  not force a vectorization that changes the statistic).
- **Sectioning:** VAL-001-style separators (imports → path setup → constants → DGP/registry →
  pure `ASS`/shape computation → dispositions → plotting → orchestration → `main()`); no import-time
  side effects (no dir creation / writes at import); helper functions return data, `main()` prints
  concise progress.
- **`xen.ass` extension only:** add `shape_diagnostic` (+ `ShapeDiag` dataclass) to `xen.ass`; do not
  modify the existing scoring/bootstrap functions. Add `diptest` to `pyproject.toml` + lockfile.

## Complexity Check

- **Statistical / validation checks: 3 / 3** — (1) shape discrimination (false-flag `U` + detection
  `B` at `τ_gap=0.30`, per-leg decomposed), (2) `k`-sensitivity routing-invariance, (3) `S`-family
  asymmetry characterization (disclosed, non-binding). (Integrity anchor + determinism are procedural
  integrity checks, not hypothesis tests.)
- **Visualisations: 4 / 4** — as listed.
- **New code modules: 0 new / budget 0** — one in-family `xen.ass.shape_diagnostic` extension
  (the docstring-reserved addition) + the experiment harness in `code/`. One new project dependency
  (`diptest`), ratified at Stage 4.
