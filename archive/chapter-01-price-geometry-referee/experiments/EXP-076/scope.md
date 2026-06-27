# Experiment: EXP-076 — `ASS` Synthetic-Substrate Recovery (`ASS/VAL-001`)

> **Phase 017 — CF-CAPGEO-001 Qualifier & Protocol Validation.** G0 PASS 2026-06-20; D0
> predeclarations frozen (`checkpoints/2026-06-20-017-capgeo-qualifier-validation/D0-predeclarations.md`).
> This is the **cheap G-017a screen** — it must PASS before EXP-077 (dogfood/calibration) runs.
> **0 candidate slots, 0 counted TEST reads, no market data, holdout never touched** (synthetic only).

## Hypothesis

On synthetic return populations with **known** expectancy, median, and shape (unimodal, left/right
skew, bimodal, and sparse/uneven sample sizes), the `ASS` qualifier (adaptive kNN-bandwidth KDE →
empirical-Bayes shrinkage → bootstrap CI) **recovers each estimand to the D0 fixture-calibrated
tolerance**: per-replicate recovery bias within `0.85·SE_true(n)` for expectancy *and* median on every
`(type, n)`; its 90% bootstrap CI covers the ground-truth estimand in `[0.86, 0.94]` of replicates;
and its shrinkage weight `n/(n+k)` is monotone non-decreasing in `n`, pulling sparse types (`n ≤ 30`)
≥ 25% toward the pooled prior while leaving rich types (`n ≥ 2000`) < 5% moved.

Falsified if any estimand's recovery bias exceeds the band on any type, or CI coverage falls outside
`[0.86, 0.94]`, or shrinkage is non-monotone / violates the sparse-pull / rich-stability bounds.

## Question

Before `ASS` is allowed to *adjudicate* any market signal, can it recover ground truth where ground
truth is known? Does it estimate expectancy and median without material bias, produce calibrated
uncertainty, and shrink sparse signal types toward the pooled prior the way the design intends —
across the full unimodal/skew/bimodal/sparse synthetic span?

## Scope Boundaries

- **Data Views**: **Synthetic return populations only** (D0 §D1). No market data, no chart-type
  generators, no real bars are loaded in this experiment. Returns are in **ATR units** (`R = 1.0 ATR`).
- **Synthetic families (frozen, D0 §D1)**:
  - **Unimodal `U`** — `N(μ, 1.0²)`: `U0` (μ=0, null), `U1` (+0.05), `U2` (+0.10), `U3` (+0.20).
  - **Skew `S`** — skew-normal `SN(ξ,ω,α)`: `Splus` (right-skew, mean≈+0.62/med≈+0.40),
    `Sminus` (left-skew, mean≈−0.07/med≈+0.17), `Sminus0` (left-skew mean≈0/med≈+0.24).
  - **Bimodal `B`** — mixture `w·N(μ₁,σ₁²)+(1−w)·N(μ₂,σ₂²)`: `B_neg` (med+, mean−0.1725),
    `B_zero` (med+, mean−0.015), `B_pos` (med+, mean+0.045), `B_strong` (med+, mean−0.24).
  - **Sparse/uneven `SP`** — a *population* of `U`/`S`/`B` members instantiated at mixed `n` with
    **median sample size ≈ 120** (so the default `k = median-n = 120` is exercised). This is the
    population that drives the shrinkage-behaviour check.
- **Parameters (frozen, D0 §D1/§D3)**:
  - Sample sizes `n ∈ {15, 30, 60, 120, 250, 500, 1000, 2000, 8000}` (n<30 = sparse stress).
  - Replicates `R_REP = 2000` independent draws per `(type, n)`.
  - Master seed `20260620`; per-draw seed = deterministic hash of `(type_id, n, replicate)`.
  - Median ground truth = 10⁷-draw Monte-Carlo estimate (recorded at ratification); expectancy/shape
    ground truth closed-form where available.
  - `ASS` config: kNN bandwidth `k_bw = max(5, round(√n))`; shrinkage `weight = n/(n+k)`,
    `k` default = median sample size; bootstrap `N_BOOT = 10_000`, CI = 5th/95th pct; synthetic iid
    data → **simple within-type resample** (the real-data moving-block variant is EXP-077, not here).
- **Instruments**: none (synthetic). N/A.
- **Time range**: N/A — no dataset is loaded. The nested-chronological-split / 70% rules apply to
  market data; this experiment touches none.
- **Global holdout**: trivially excluded — no market data of any kind is loaded, sliced, or inspected.
- **Look-ahead bias prevention**: N/A (no time-ordered market data). Determinism enforced via fixed
  seeds (D0 §D6): a second full pass is byte-identical.
- **Real-price outcome discipline**: synthetic returns are in ATR units by construction; no HA or
  Renko brick prices appear anywhere. (Real-price discipline binds the Phase 018 market reads, not
  this synthetic recovery check.)
- **Exclusions**:
  - **No FPR / MDE / `P(return>X)` reliability** — those are EXP-077 (under `WF-EXPANDING`).
  - **No shape-discrimination / `k`-sensitivity sweep** — that is EXP-078.
  - **No market data, no dogfood** — the current-data TRAIN-only dogfood belongs to EXP-077.
  - **No `k` tuning.** `k = median-n` is frozen; this experiment does not search over `k`.
  - No `WF-EXPANDING` folds (single-population recovery only).

## Success / Failure Criteria

The pass criteria are the D0 §D2.1 fixture-calibrated bands (bite-check GREEN, `bite_check_report.json`,
2026-06-20). This is the binding **G-017a** screen.

- **Evidence FOR (PASS — recovery validated):** *all three* hold —
  1. **Recovery bias:** `median_over_replicates(|estimate − truth|) ≤ 0.85·SE_true(n)` for **both**
     expectancy and median on **every** `(type, n)` cell, where `SE_true(n) = σ_type/√n` for
     expectancy and the MC median-SE for the median.
  2. **Coverage:** the `ASS` 90% bootstrap CI covers the ground-truth estimand in **`[0.86, 0.94]`**
     of replicates, for expectancy and median, on every type.
  3. **Shrinkage behaviour (on `SP`):** weight `n/(n+k)` monotone non-decreasing in `n`; sparse
     members (`n ≤ 30`) shrunk ≥ 25% from raw toward the pooled prior; rich members (`n ≥ 2000`)
     moved < 5%.
- **Evidence AGAINST (FAIL → feeds G-017 `DISCOVERY_ONLY` or a fix):** any estimand's recovery bias
  exceeds `0.85·SE_true` on any cell, OR coverage falls outside `[0.86, 0.94]` on any type, OR
  shrinkage is non-monotone / violates the sparse-pull or rich-stability bounds.
- **Inconclusive:** a cell is too sparse to estimate a stable MC median-SE, or a synthetic family's
  ground truth is itself ambiguous at the tested `n`. Report the affected cell, do not let it silently
  pass; an inconclusive cell on a *binding* type blocks the clean PASS and is disclosed to G-017.

**Recovery-vs-shrinkage tension (flag for the analysis plan):** shrinkage deliberately biases sparse
cells toward the pooled prior, which can push a sparse cell's recovery bias up while satisfying the
≥25%-pull behaviour. The analysis plan (Stage 2) must define **exactly which estimate the D2.1
recovery band is applied to** (e.g. the per-type un-pooled `ASS` estimate for the recovery legs, with
shrinkage assessed separately on `SP`) so the two criteria are not mutually contradictory by
construction. Resolve this before implementation — do not hand-wave it.

## Complexity Budget

- Max statistical/validation checks: **3** (recovery-bias band, CI-coverage band, shrinkage-behaviour
  bounds). These are calibration checks against known truth, not market hypothesis tests.
- Max visualisations: **4** (recovery bias vs `n` by type; CI coverage vs `n` by type; shrinkage
  weight `n/(n+k)` curve over `n` with sparse/rich bounds marked; optional ground-truth-vs-estimate
  scatter or KDE-overlay sanity panel).
- Max new code modules: **1** — a reusable `xen.ass` module implementing the `ASS` pipeline (adaptive
  KDE, EB shrinkage, bootstrap CI, expectancy/median/`P(>X)` outputs). Justified: it is the family's
  core qualifier and is reused unchanged by EXP-077, EXP-078, and all of Phase 018. The synthetic
  DGPs and recovery harness live in the experiment's `code/` (may share the D1 generators already
  prototyped in `bite_check.py`).

## Data Requirements

- **No market data.** Synthetic generation only, per D0 §D1. Reuse the D1 samplers prototyped in
  `checkpoints/2026-06-20-017-capgeo-qualifier-validation/bite_check.py` (`gen_unimodal`,
  `gen_skewnormal`, `gen_bimodal`) and the MC median ground-truth pattern, lifted into the
  experiment's `code/` and/or `xen.ass`.
- Ground-truth table (per type): closed-form expectancy/median where available; MC median (10⁷ draws,
  recorded seed) otherwise. Persist the ground-truth table to `results/` for the audit to re-derive.
- Determinism: every RNG seed fixed and recorded; a full second pass must be byte-identical (D0 §D6).

### Standard Loading Pattern

Not applicable — no Parquet/market data is loaded. The standard holdout-split loader is intentionally
absent because this experiment touches no real dataset. (EXP-077's TRAIN-only dogfood will use the
standard first-70% lazy slice; this one does not.)

## Suggested Direction

Non-binding. Build `xen.ass` first (KDE → shrinkage → bootstrap; emit expectancy, median, CI,
shrinkage weight). Then, per `(type, n)`, draw `R_REP=2000` replicates, score with `ASS`, and tabulate
median `|estimate − truth|` against `0.85·SE_true(n)` and CI coverage against `[0.86, 0.94]`. Assess
shrinkage on the `SP` mixed-`n` population (monotonicity + sparse-pull/rich-stability). Keep the
synthetic generators, the recovery harness, and the `xen.ass` qualifier cleanly separated
(generation → pure ASS computation → recovery checks → plotting → orchestration), with `tqdm` over the
`(type, n, replicate)` grid. Emit a single machine-readable PASS/FAIL recovery table to `results/` that
G-017a can read directly. Reconcile the production-scale `ASS` expectancy estimator against the
bite-check reference estimator on at least one shared `(type, n)` cell as an integrity anchor.

## Registry Disposition (Stage 1 precondition — satisfied)

- **Family** `CF-CAPGEO-001`: `REGISTERED` (SCREENING-GATED) — `candidate-families/cf-capgeo-001.md`.
- **Countable item** `ASS/VAL-001` / EXP-076: registered in `multiplicity-registry.md` Phase 017
  batch (status PENDING → in-progress at this scope). Component `ASS` registered in
  `components/global-techniques.md`.
- **TEST-read ledger:** no TEST stratum is read (synthetic only) — **0 counted reads**; ledger
  unchanged. No stratum tally to state.
- **Slots:** 0 candidate slots (methodology validation, not candidate screening).
