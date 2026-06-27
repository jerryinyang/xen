# Experiment: EXP-078 — Shape Discrimination + `k`-Sensitivity (`ASS/VAL-003`)

> **Phase 017 — CF-CAPGEO-001 Qualifier & Protocol Validation.** G0 PASS 2026-06-20; D0
> predeclarations frozen (`checkpoints/2026-06-20-017-capgeo-qualifier-validation/D0-predeclarations.md`).
> Gated on **EXP-076 G-017a PASS** (RECOVERY_VALIDATED_G017a) and **EXP-077** (VALIDATED_WITH_GUARDS)
> — both satisfied. This is the **last** Phase 017 experiment owed before terminal **G-017**.
> It validates the **shape-discrimination** leg of `ASS` (closing the EXP-074 tail-shape-blind-guard
> gap) and the **`k`-sensitivity** of the qualifier's one tunable knob.
> **0 candidate slots, 0 counted TEST reads, no market data, holdout never touched** (synthetic only).

## Hypothesis

On synthetic return populations with **known** shape, the `ASS` tail/bimodality diagnostic and the
`ASS` point/edge machinery behave as a trustworthy yardstick:

1. **Shape discrimination (D2.5):** the diagnostic
   `flag = (dip_p < 0.05) OR (|g| > τ_gap)`, where `dip_p` is the Hartigan dip-test p-value and
   `g = (mean − median) / MAD` is the robust mean–median gap, **separates bimodal `B` from
   unimodal `U`** at the frozen operating point `τ_gap = 0.30`: the **false-flag rate on `U` ≤ 0.05**
   and the **detection rate on `B` ≥ 0.80**, per `n` (n ≥ 30).
2. **`k`-sensitivity (D3):** across the pre-registered shrinkage-constant grid
   `k ∈ {0.5×, 1×, 2×}·median-n ∪ {30, 500}`, the `ASS` binding **routing** (the recovery / coverage
   / edge-call dispositions established in EXP-076/077, recomputed per `k`) is **invariant**, or its
   `k`-dependence is **bounded and disclosed** (no flip that would change a Phase-018 verdict).

**Falsified (feeds G-017 `DISCOVERY_ONLY`)** if, at `τ_gap = 0.30`, the false-flag rate on any
unimodal `U` stratum exceeds 0.05 **or** the detection rate on any bimodal `B` stratum (n ≥ 30) falls
below 0.80; **or** if `k`-sensitivity produces an undisclosed routing flip across the pre-registered
grid. **`PROTOCOL_DEFECT`** only if determinism (D6) fails (a second full pass is not byte-identical).

## Question

`ASS` is scored on expectancy + median + a tail diagnostic precisely because the two closed families
died on bimodal/tail structure that a smoothed mean cannot see (retrospective §4.2). EXP-074 showed
the concrete failure: an anti-p-hacking guard that was **structurally blind to tail-shape** vetoed the
one feature (entry exhaustion bimodality) that explained the mean's collapse. EXP-078 asks the direct
question that closes that gap:

> Does the `ASS` shape diagnostic **actually flag** bimodal populations (and the dangerous left-skew
> mean-weak case) versus clean unimodal nulls, at a fixture-calibrated effect-size threshold, with a
> controlled false-flag rate — and is the qualifier's verdict **stable** against its one tunable knob
> `k` across a pre-registered sensitivity band, so that no Phase-018 adjudication hinges on a `k`
> choice?

## Scope Boundaries

- **Data Views**: **Synthetic return populations only** (D0 §D1, reused unchanged from EXP-076/077).
  No market data, no chart-type generators, no real bars are loaded anywhere in this experiment.
  Returns are in **ATR units** (`R = 1.0 ATR`).
- **Synthetic families (frozen, D0 §D1)** — roles in this experiment:
  - **Unimodal `U`** — `N(μ, 1.0²)`: `U0` (0), `U1` (+0.05), `U2` (+0.10), `U3` (+0.20). **The
    should-NOT-flag negatives** for the shape false-flag rate (all unimodal, symmetric).
  - **Bimodal `B`** — mixture `w·N(μ₁,σ₁²)+(1−w)·N(μ₂,σ₂²)`: `B_neg` (mean −0.1725), `B_zero`
    (mean −0.015), `B_pos` (mean +0.045), `B_strong` (mean −0.24). **The should-flag positives** for
    the shape detection rate (median-positive dominant mode + minority catastrophic mode — the
    CF-HA-HARAMI-001 failure shape).
  - **Skew `S`** — skew-normal `SN(ξ,ω,α)`: `Splus` (right-skew), `Sminus` (left-skew, mean≈−0.07),
    `Sminus0` (left-skew, mean≈0). **Disclosed characterization arm, NOT part of the binding
    U-vs-B PASS:** asymmetric-but-unimodal — measures where the `|g|` (mean–median gap) leg lands on
    skew without bimodality (the diagnostic is explicitly named "bimodal/asymmetric"; the dip-test
    leg should largely pass these, the gap leg may flag them — reported, not gated). This resolves how
    the diagnostic treats the dangerous left-skew mean-weak case ahead of Phase 018.
- **Parameters (frozen, D0 §D1/§D2.5/§D3)**:
  - Sample sizes `n ∈ {15, 30, 60, 120, 250, 500, 1000, 2000, 8000}` (n<30 = sparse stress, disclosed
    not gated for the shape leg; the binding detection floor is n ≥ 30).
  - Replicates `R_REP = 2000` independent draws per `(type, n)`; master seed `20260620`; per-draw
    seed = deterministic hash of `(type_id, n, replicate)` (extended with a `k`-tag for the sweep so
    each `k` re-uses the **same** draws — paired comparison, no fresh sampling noise across `k`).
  - **Shape diagnostic (D2.5):** `dip_p` = Hartigan dip-test p-value; `g = (mean − median)/MAD` with
    `MAD = median_abs_deviation(x, scale=1.0)`; **flag iff `dip_p < 0.05` OR `|g| > τ_gap`**;
    **`τ_gap = 0.30`** (frozen — the bite-check ROC operating point; the bite confirmed @0.30
    false-flag 0.000 / detection 0.999, feasible window [0.105, 0.435]). `τ_gap` is **not** re-tuned
    here; it is applied as frozen and its operating characteristics measured at production scale.
  - **`ASS` config (D3):** kNN bandwidth `k_bw = max(5, round(√n))`; shrinkage `weight = n/(n+k)`;
    bootstrap `N_BOOT = 10_000`, CI = 5th/95th pct; synthetic iid → simple within-type resample.
  - **`k`-grid (D3, pre-registered sweep, NOT a selection):** `k ∈ {0.5×, 1×, 2×}·median-n` plus the
    fixed anchors `{30, 500}`. `median-n` = the median sample size across the swept `(type, n)` grid
    (recorded at run time). The default `k = median-n` (= `1×`) is the EXP-076/077 operating point.
- **Instruments**: none (synthetic). N/A.
- **Time range**: N/A — no dataset is loaded. The nested-chronological-split / 70% rules apply to
  market data; this experiment touches none.
- **Global holdout**: trivially excluded — no market data of any kind is loaded, sliced, or inspected.
  The final-30% holdout and the next-21% TEST stratum are out of scope by construction.
- **Look-ahead bias prevention**: N/A (no time-ordered market data). Determinism enforced via fixed
  seeds (D0 §D6): a second full pass is byte-identical.
- **Real-price outcome discipline**: synthetic returns are in ATR units by construction; **no HA or
  Renko brick prices** appear anywhere. (Real-price discipline binds Phase 018 market reads, not this
  synthetic shape check.)
- **Exclusions**:
  - **No `τ_gap` re-tuning.** `τ_gap = 0.30` is frozen at D0; this experiment **measures** its
    false-flag/detection characteristics, it does not search for a new operating point. (If `τ_gap`
    turned out infeasible at production scale, that is a FAIL/disposition to G-017, **not** an in-place
    re-anchor.)
  - **No `k` tuning / selection.** The `k`-grid is a pre-registered **sensitivity sweep**; the
    deployed `k = median-n` is unchanged. No `k` is chosen on the basis of these results.
  - **No FPR / MDE / `P(return>X)` reliability re-measurement** — those are EXP-077. (The `k`-sweep
    re-runs the *existing* EXP-076/077 disposition checks across `k` to test routing invariance; it
    does not introduce new error-control endpoints.)
  - **No market data, no dogfood, no `WF-EXPANDING` folds** — the protocol legs are EXP-077.
  - **No candidate screening, no slot, no real TEST/holdout contact.**
  - **No EXP-079** (reserved-inactive; out of scope).

## Success / Failure Criteria

Pass criteria are the D0 §D2.5 (shape) and D3/§7 (`k`-sensitivity) bands. **Reported PER STRATUM**
(per type / per `n` / per `k`) — no single collapsed cross-cell boolean is binding (LESSON-001; D0 §8
per-stratum doctrine; EXP-076 audit C1). Pooled summaries are disclosures.

- **Evidence FOR (PASS — shape discrimination + `k`-sensitivity validated):** *both* of —
  1. **Shape discrimination (binding, U-vs-B):** at the frozen `τ_gap = 0.30`, the combined-rule
     **false-flag rate on every unimodal `U` stratum ≤ 0.05** (with Wilson upper-95% reported) **and**
     the **detection rate on every bimodal `B` stratum ≥ 0.80**, for every `n ≥ 30`. The full
     false-flag-/detection-vs-`n` curve is reported per type; the per-leg contribution (`dip_p` leg vs
     `|g|` leg) is decomposed so the audit can see which leg carries the discrimination.
  2. **`k`-sensitivity (binding):** across the pre-registered `k`-grid, the `ASS` binding **routing**
     (EXP-076 recovery/coverage dispositions and EXP-077 edge-call/FPR dispositions, recomputed per
     `k` on the same draws) is **invariant** — no disposition flips — **or** any `k`-dependence is
     **bounded** (quantified: max change in the disposition-bearing quantity across the grid) **and
     disclosed**, with the conclusion that no Phase-018 verdict would flip within the band.
- **Evidence AGAINST (FAIL → feeds G-017 `DISCOVERY_ONLY`):** any `U` stratum false-flag > 0.05, OR
  any `B` (n ≥ 30) detection < 0.80 at `τ_gap = 0.30`, OR an undisclosed/unbounded routing flip across
  the `k`-grid — recorded per stratum, no clean PASS.
- **`PROTOCOL_DEFECT`:** the determinism (D6) second pass is not byte-identical → fix and re-run.
- **Inconclusive:** a `(type, n)` cell too sparse (e.g. n = 15) to estimate a stable dip-test or
  detection rate is **disclosed per stratum**, never silently passed; an inconclusive **binding**
  stratum (n ≥ 30 on a `U` or `B` type) blocks the clean PASS and is surfaced to G-017. The `S`-family
  arm is characterization-only and cannot, by itself, block PASS.

**Metric denominators & zero-baseline behavior (define before implementation):**
- **False-flag rate** denominator = `R_REP` replicates of that `U` `(type, n)` cell; numerator =
  replicates where `flag == True`. **Detection rate** denominator = `R_REP` replicates of that `B`
  `(type, n)` cell; numerator = replicates where `flag == True`. Both are proper rates in `[0,1]` with
  fixed denominators — no zero-baseline ratio, no percentage-of-zero.
- **`g`** is undefined when `MAD == 0` (degenerate sample). This cannot occur for the continuous `U`/
  `S`/`B` DGPs at n ≥ 15 with probability 1, but the implementation must define the `MAD == 0` branch
  explicitly (treat as `g = 0` / non-flag-by-gap, deferring to the dip leg) and **assert** zero such
  occurrences in the run, reported as an integrity count (never silent).
- **`k`-sensitivity magnitude** is an **absolute** change in the disposition-bearing quantity (e.g.
  Δ false-flag rate, Δ coverage, Δ edge-call rate) across the grid — never a percentage change against
  a possibly-zero baseline.

**Cross-leg tension to resolve in the analysis plan (Stage 2):**
1. **Skew routing.** The `S` family is unimodal but asymmetric; the `|g|` leg is *designed* to flag
   left-tail asymmetry. The plan must state precisely that `S` is **characterization-only** (the
   binding PASS is U-vs-B), and report where `Sminus/Sminus0` land — so the diagnostic's treatment of
   the dangerous mean-weak skew is on the record without contaminating the binding false-flag rate
   (which uses `U` only).
2. **`k`-sensitivity ↔ shape independence.** The D2.5 diagnostic is computed on the **raw sample**
   (dip-test, mean, median, MAD), so it is *a priori* independent of the shrinkage `k`. The plan must
   state this explicitly and confine the `k`-sweep to the quantities that **do** depend on `k` (the
   shrunk point estimates, coverage, and edge-calls), re-running the EXP-076/077 dispositions per `k`
   — not re-deriving the shape flag per `k` (which would be vacuous). Resolve before implementation —
   do not hand-wave.

## Complexity Budget

Comparative-tier (shape ROC across types/`n` + a `k`-sweep re-running prior dispositions).

- **Max statistical / validation checks: 3** — (1) shape discrimination at `τ_gap = 0.30`
  (false-flag on `U`, detection on `B`, per `n`, with per-leg decomposition), (2) `k`-sensitivity
  routing-invariance across the pre-registered grid, (3) `S`-family asymmetry characterization
  (disclosed, non-binding). (Determinism is a procedural integrity check, not a hypothesis test.)
- **Max visualisations: 4** — (a) shape false-flag (`U`) and detection (`B`) rate vs `n`, with the
  0.05 / 0.80 lines and the per-leg split; (b) `dip_p` and `|g|` distributions by type at a
  representative `n` (with the `τ_gap = 0.30` line) — the U-vs-B/S separation panel; (c) `k`-sensitivity:
  the disposition-bearing quantities (e.g. coverage, edge-call/false-flag rate) vs `k` across the grid,
  routing-stability highlighted; (d) optional `dip_p` vs `|g|` scatter colored by type (clean
  visualization of where each family sits relative to both legs).
- **Max new code modules: 0 new modules — one in-family extension.** Add a `shape_diagnostic`
  function (Hartigan dip-test p-value + robust mean–median gap `g`, returning the combined flag) to
  the existing **`xen.ass`** core — the module docstring already reserves this as "EXP-078 shape
  diagnostics." This is an addition to the family's core qualifier (the same pattern as EXP-077's
  moving-block extension), not a new module. The synthetic DGPs (reused from EXP-076 D1) and the
  shape/`k`-sweep harness live in the experiment's `code/`.

  **Dependency decision (flag for Stage 2/3 + governance):** `diptest` (the Hartigan dip-test) is
  **not currently installed** (`pyproject.toml` has numpy/scipy only); the D0 bite-check validated the
  `|g|` leg only and explicitly deferred the dip-test leg to EXP-078. The analysis plan must choose
  **either** (i) add the well-established `diptest` package (wraps the original Hartigan reference
  implementation) as a project dependency — preferred for correctness/auditability — **or** (ii)
  implement Hartigan's dip statistic + a calibrated bootstrap p-value in `xen.ass` with a golden-value
  test against published reference values. Whichever is chosen must be deterministic (fixed seed for
  any bootstrap p-value), recorded, and re-derivable by the audit. This decision is made in Stage 2
  and ratified at Stage 4 pre-execution governance (it is a tooling choice, not a D0 amendment — the
  diagnostic definition is already frozen in D2.5).

## Data Requirements

- **Synthetic only:** reuse the frozen D1 generators / type registry from EXP-076
  (`gen_unimodal/gen_skewnormal/gen_bimodal`, closed-form moments, MC ground truth). Persist the
  realized per-`(type, n)` shape false-flag/detection tables, the per-leg (`dip_p` / `|g|`)
  decomposition, the `S`-family characterization table, and the full `k`-sweep disposition tables to
  `results/` for the audit to re-derive. Emit a single machine-readable PER-STRATUM PASS/FAIL table
  that G-017 can read directly.
- **`k`-sweep pairing:** the same `R_REP` draws are scored across all grid `k` values (the `k`-tag in
  the seed selects a fixed draw set, not a fresh sample) so the across-`k` comparison is paired and
  free of fresh sampling noise.
- **Integrity anchor:** reconcile the production-scale `ASS` outputs at the default `k = median-n`
  against the EXP-076/077 recorded values on at least one shared `(type, n)` cell (diff at the
  programme 1e-9 tolerance) — confirming `xen.ass` is unchanged behaviorally by the shape extension.
- **Determinism (D6):** every RNG seed fixed and recorded (sampling, bootstrap, and any dip-test
  bootstrap p-value); a full second pass must be byte-identical (hash-compared, EXP-076/077 pattern).

### Standard Loading Pattern

Not applicable — no Parquet/market data is loaded. The standard holdout-split loader is intentionally
absent because this experiment touches no real dataset (synthetic shape validation only).

## Registry Disposition (Stage 1 precondition — satisfied)

- **Family** `CF-CAPGEO-001`: `REGISTERED` (SCREENING-GATED) — `candidate-families/cf-capgeo-001.md`.
- **Countable item** `ASS/VAL-003` / EXP-078: registered in `multiplicity-registry.md` Phase 017
  batch (status PENDING → in-progress at this scope; G0 PASS 2026-06-20 satisfied). Components `ASS`
  and `WF-EXPANDING` registered in `components/global-techniques.md`. No new countable item is
  introduced (the `k`-grid is a pre-registered sensitivity sweep, not a new branch/variant).
- **TEST-read ledger:** **no TEST stratum is read** (synthetic only) — **0 counted reads**; ledger
  unchanged. No stratum tally to state. (The 2-read-cap accounting rule is validated in EXP-077 and
  exercised against the live ledger only in Phase 018 on the post-INFR-003 5-year strata.)
- **Slots:** 0 candidate slots (methodology validation, not candidate screening).
