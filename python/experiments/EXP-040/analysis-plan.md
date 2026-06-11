# Analysis Plan: Experiment EXP-040

## Objective

Test HYP-001 directly: is `P(bounce | approach to AVWAP)` greater than
`P(bounce | approach to matched non-AVWAP control levels)` on the 1h and 4h
domains, analysis set, gross real prices? Binding family: the two pooled
domain contrasts, Holm α = 0.05. The bounce-trigger definition appears nowhere
in any metric (EXP-025 conflation inadmissible). Mechanism science: no costs,
no gate consequence.

## Stage-2 parameter fixes (frozen here, before any outcome computation)

| Parameter | Value | Rationale |
|---|---|---|
| ε (approach neighborhood) | 0.25 × contemporaneous MAD band-width | Inside-band proximity scale; well below the ±1.0 band so approach ≠ band touch |
| Hysteresis radius (episode separation) | 2ε | A new episode requires a clean exit; prevents oscillation double-counting (the duplicate-source rule) |
| Episode cap | 24 domain bars | Matches the longest EXP-033 horizon; unresolved-at-cap disclosed, not dropped |
| Materiality band (AGAINST-as-immaterial) | 2 pp | Smallest rate difference worth a mechanism claim |
| Control offsets δ | uniform random in ±[1.5, 3.5] band-width units | Outside the ε- and hysteresis-neighborhoods of the line and clear of the ±1.0 trading band |
| Control level lifetime | 100 domain bars (then resampled anew) | Bounds staleness of a frozen horizontal level |
| Permutations / bootstrap | 2,000 permutations; 1,000 bootstrap resamples | Resolution ≪ α at the Holm-2 level |

These values are now frozen; sensitivity sweeps are out of scope (future
experiment if needed).

## Methodology

### Step 1 — Substrate and state

- **Method**: 1-minute bars → 1h/4h domain bars (analysis set only, lazy slice
  before collection); run the unchanged EXP-020 AVWAP state machine as a
  sequential streaming pass, recording at each domain-bar close: live AVWAP
  value, MAD band-width `BW`, anchor segment id (`regime_id`), trailing
  ATR(14) vol percentile (data ≤ close only). Reconciliation anchor: rebuilt
  domain-bar and anchor-segment counts == EXP-020 metadata, exact; hard-fail
  on mismatch.
- **Why**: the line/band state must be byte-identical to the registered
  definition or the mechanism claim is about a different object.
- **Expected output**: per-bar state table per instrument×domain.

### Step 2 — Approach-episode detection (identical detector, both arms)

- **Method**: a single streaming detector, parameterized only by the level
  series it watches. State: outside/inside the ε-neighborhood, entry
  direction (from above = falling into the level; from below = rising),
  episode age. An episode opens at the first close with
  `|Close − level| ≤ ε·BW` after being beyond the hysteresis radius
  (`> 2ε·BW`); it resolves when the close exits the ε-neighborhood —
  **bounce** iff the exit is opposite to entry direction, **pass-through**
  iff same side as continued travel; **unresolved** at the 24-bar cap, at a
  level-lifetime end, at an anchor-segment end (AVWAP arm), or at the
  analysis boundary (disclosed category, excluded from rates, counted).
  - **AVWAP arm**: level = the live AVWAP line (moving).
  - **Control arm (primary, binding)**: levels = horizontal snapshots
    `AVWAP(t₀) + δ·BW(t₀)`, δ ~ U(±[1.5, 3.5]) with fixed seed, instantiated
    on a regular t₀ grid (every 25 domain bars, 4 concurrent levels), each
    alive 100 bars. Horizontal frozen levels carry zero AVWAP-path
    information beyond the snapshot; offsets keep their neighborhoods
    disjoint from the line's.
  - **Secondary control arm (moving copies, descriptive — design §11/8)**:
    levels = `AVWAP(t) + δ·BW(t)` evaluated contemporaneously (the copy moves
    with the line), with the identical δ construction, spawn grid, and
    lifetime as the primary arm (own fixed seed). |δ| ≥ 1.5 BW keeps the copy
    structurally clear of the line's ε- and hysteresis-neighborhoods at every
    bar, so no clearance filter is needed. Same detector, verbatim.
  Episodes from both arms inherit covariates at episode open: entry
  direction, vol tercile, BW-percentile tercile, distance traveled over the
  prior 5 bars (approach speed tercile).
- **Why this method**: running the *identical* detector over both arms means
  any definitional artifact (ε geometry, hysteresis, cap) cancels in the
  contrast — the only systematic difference is whether the level is the AVWAP.
- **Simpler alternative considered**: shifted copies of the moving AVWAP
  (AVWAP ± δ·BW) as the sole control — same smoothness. Rejected as
  *primary*: shifted lines remain in the band-geometry family (the ±1.0 band
  is itself a target in the registered strategy), so a null would be
  ambiguous between "line not special" and "the whole band family is
  reactive." **Adopted as the descriptive secondary arm** (design §11/8): the
  two controls have complementary confounds (static arm: kinematics; moving
  arm: band-family geometry) and together bracket the estimand. Neither
  ambiguity is eliminated by a single arm; the joint pattern is what gets
  interpreted (§Interpretation, caveat 4).
- **Assumptions**: bar-close granularity (intrabar touches invisible — equal
  for both arms); 1-minute data could refine but is out of scope for parity
  with the strategy's domain-bar semantics.
- **Expected output**: episode table
  `(instrument, domain, arm, level_id, regime_id, open_ts, entry_direction,
  vol_tercile, bw_tercile, speed_tercile, outcome ∈ {bounce, pass, unresolved},
  bars_to_resolve)`.

### Step 3 — Covariate matching

- **Method**: stratify episodes by
  (instrument, entry_direction, vol_tercile, speed_tercile). Within each
  stratum, retain control episodes by random subsampling (fixed seed) to the
  AVWAP-arm stratum proportions, so both arms share the covariate
  distribution. Strata with < 5 episodes in either arm are excluded
  (disclosed). Matching is run **independently per control arm** with the
  identical machinery and its own fixed seed (the static-arm match feeds the
  binding contrast; the moving-arm match feeds only the descriptive Δ_m);
  balance rows carry a `control_arm` column. Matching balance table
  reported. `bw_tercile` is collected and
  reported in the balance table but is **not** a stratum key (a fourth tercile
  key triples the stratum count at a fixed floor and discards data); residual
  band-width imbalance is disclosed, not matched away.
- **Why**: removes the trivial confound that AVWAP approaches happen in
  systematically different regimes/directions than arbitrary levels.
- **Simpler alternative considered**: unmatched pooled contrast. Rejected —
  direction/regime imbalance alone could fabricate or mask Δ.
- **Expected output**: matched episode set + `results/matching_balance.csv`.

### Step 4 — Binding contrast (per domain)

- **Method**:
  0. **Power statement (ordering-enforced, before any contrast read)**:
     persist `results/power_statement.csv` from matched episode **counts
     only** (no outcome column touched): per contrast×domain (binding
     AVWAP-vs-static and descriptive AVWAP-vs-moving rows, flagged), realized
     n and the implied minimal detectable Δ (worst-case p = 0.5 unclustered
     binomial bound, flagged optimistic under clustering), with per-cell
     flags for verdict classes structurally unreachable at realized n (scope
     §Power; verdict flags apply to the binding rows only). Write-timestamp
     assertion: power file mtime precedes the contrast computation.
  1. **Point estimate**: Δ_d = stratum-weighted mean of
     (bounce-rate_AVWAP − bounce-rate_control), weights = AVWAP-arm stratum
     proportions, pooled over instruments. Reported in **percentage points**.
  2. **95% cluster bootstrap CI**: resample clusters with replacement —
     AVWAP arm by anchor-segment (`regime_id`), control arm by `level_id` —
     within (instrument, entry_direction) strata; recompute Δ_d; percentile
     CI, N = 1,000. Clusters absorb within-segment/within-level episode
     dependence.
  3. **Permutation p (one-sided, Δ > 0)**: permute arm labels among episodes
     **within matched strata** (2,000 permutations, fixed seed); to respect
     dependence, permutation is at the cluster level (whole segments/levels
     swap arms within strata where cluster counts allow; episode-level
     fallback flagged if any stratum lacks ≥2 clusters per arm).
  4. **Holm across the 2 domains** at α = 0.05.
  5. Verdict per scope: FOR ⇔ Δ > 0 ∧ CI_low > 0 ∧ Holm-p ≤ 0.05;
     AGAINST ⇔ CI entirely ≤ 0, or (CI_high < +2 pp ∧ CI_low ≤ 0)
     (immaterial-null — symmetric in the point estimate: a tight CI around an
     immaterially positive Δ is AGAINST, not INCONCLUSIVE); else INCONCLUSIVE.
     Reportability floor: ≥ 100 matched episodes per arm per domain, else no
     verdict.
- **Why these methods**: rate difference + cluster bootstrap + within-stratum
  permutation is the simplest assumption-light stack for a clustered binary
  outcome; it is the same inferential family the programme has validated
  (EXP-021/027 conventions) applied to rates.
- **Simpler alternative considered**: chi-square / two-proportion z-test.
  Rejected — assumes episode independence, violated by segment/level
  clustering.
- **Assumptions**: clusters capture the dominant dependence; matching
  covariates are the relevant confounders (others disclosed as residual
  risk); exchangeability of arm labels within strata under the null.
  **Named residual confound (unmatched by construction):** control approaches
  occur with price stretched 1.5–3.5 band-widths from the contemporaneous
  VWAP, a location regime AVWAP approaches (distance ≈ 0) never occupy and
  matching cannot equalize. Generic mean reversion toward the line inflates
  control bounce rates for outside-in approaches, so the expected bias
  direction is **against** HYP-001 — conservative for a FOR, but it weakens
  the interpretability of an AGAINST (disclosed in caveats).
- **Expected output**: `results/contrast_results.csv`
  `(domain, delta_pp, ci_low, ci_high, perm_p, holm_p, n_avwap, n_control,
  n_strata, verdict)`.

### Step 5 — Descriptive decompositions (no new tests)

- **Method**: per-instrument×domain Δ with cluster-bootstrap CIs (descriptive,
  multiplicity-uncontrolled, never promoted); Δ by entry direction; bounce
  rates by bars-to-resolve; chronological split-half of the analysis set —
  sign(Δ) per half per domain (stability disclosure, non-binding).
  **Moving-copy contrast Δ_m (descriptive — design §11/8)**: per domain,
  the stratum-weighted rate difference between the AVWAP arm and the matched
  moving-copy arm, with the same cluster-bootstrap CI machinery (moving-copy
  clusters = copy levels). **No permutation p, no Holm membership** — the
  binding family is untouched. Δ_m is reported alongside Δ in the forest
  plot (subordinated) and interpreted only jointly with Δ per the
  predeclared reading (scope §Secondary control).
  **Censoring sensitivity bound (non-binding)**: the two arms censor
  differently (anchor-segment ends are informative trend-change events on the
  AVWAP arm; control-level lifetime ends at a fixed 100 bars are not), so
  excluding unresolved episodes can shift Δ directionally. Recompute the point
  estimate Δ_d per domain under the two extreme imputations — all unresolved
  episodes counted as bounces, then all as passes, applied per arm — and
  report the resulting [Δ_min, Δ_max] bracket alongside unresolved counts per
  arm. Point estimates only; reuses the Step 4 aggregator, no new test.
- **Expected output**: `results/contrast_by_instrument.csv`,
  `results/split_half.csv`, `results/censoring_sensitivity.csv`,
  `results/moving_control_contrast.csv`.

### Step 6 — Determinism

- **Method**: all randomness (control offsets, matching subsample, bootstrap,
  permutation) via `seed_for(EXPERIMENT_ID, domain, purpose)`; one-domain
  same-seed replay must be byte-identical; recorded in `run_metadata.json`.

## Visualisations (4 / 4)

1. `plots/episode_accounting.png` — episode counts by arm/outcome/domain
   (all three arms), incl. unresolved and floor status. Answers: is the
   denominator healthy.
2. `plots/delta_forest.png` — binding pooled Δ per domain with CI and Holm-p;
   descriptive moving-copy Δ_m and per-instrument cells alongside, visually
   subordinated. Answers: the headline HYP-001 read and its kinematic
   bracket.
3. `plots/direction_breakdown.png` — bounce rates by arm × entry direction per
   domain. Answers: is any S/R effect symmetric (support vs resistance).
4. `plots/split_half_stability.png` — Δ per analysis-set half per domain.
   Answers: temporal stability of the contrast.

## Interpretation Guide

- ≥1 domain FOR → **HYP-001 SUPPORTED** on that domain: approaches to the
  AVWAP line resolve away from it more often than matched arbitrary levels —
  the line behaves as S/R beyond level-geometry baseline. Strengthens the
  mechanistic case for line-anchored signal/exit design (Phase 011 / Stage-C
  prior). **Scope of the claim:** a FOR establishes the AVWAP line reacts
  beyond *frozen-level* baseline. The descriptive moving-copy contrast Δ_m
  then locates the effect: Δ_m ≈ 0 (CI spanning zero, tight) → the FOR is
  consistent with moving price-tracking (MA-family) kinematics generally,
  not the line specifically; Δ_m > 0 (CI_low > 0, descriptive) → the
  pattern supports line-specific S/R beyond both level geometry and
  kinematics. Δ_m never changes the verdict class (caveat 4).
- Both domains AGAINST (incl. immaterial-null) → **HYP-001 REFUTED** at this
  framing: the line is a trigger location, not a barrier; the Phase 006–008
  edge reads as relative momentum / continuation around pivots. Stage-C
  detector work should not privilege line-reactivity features.
- Otherwise → **INCONCLUSIVE**: the framing is sound but this sample cannot
  separate the arms; recorded, no re-parameterization within this scope.
- Caveats to carry verbatim into results.md: (1) bar-close granularity hides
  intrabar touches (symmetric across arms, but attenuates both rates);
  (2) the horizontal-snapshot control tests "AVWAP line vs frozen nearby
  level," not "vs every conceivable structural level" — a FOR is specific,
  a null is not a proof of no structure anywhere; (3) Δ is a conditional
  rate difference, not a tradable quantity — no economic claim attaches;
  (4) **moving-vs-static kinematic confound**: the AVWAP arm's level moves
  each bar while the binding control is frozen, which mechanically alters
  episode dynamics (the line can drift toward or away from price)
  independent of any S/R property — Δ > 0 against the static arm alone is
  ambiguous between "the AVWAP line is S/R" and "moving price-tracking
  levels differ kinematically from static levels." The descriptive
  moving-copy arm (Δ_m, design §11/8) brackets this: the static arm carries
  the kinematic confound, the moving arm carries the band-family-geometry
  confound, and only the joint Δ/Δ_m pattern is interpreted — neither arm
  alone resolves both ambiguities; (5) the control
  arm's price-stretch regime (1.5–3.5 BW from the VWAP) is unmatched by
  construction, with expected bias against HYP-001 (Step 4 assumptions).

## Implementation Safety Constraints

- Analysis set only (first 70%); holdout never loaded; episode covariates and
  control levels computable strictly at or before episode-open timestamps;
  alignment by `CloseTime` only.
- Episodes are the denominator (never bars); hysteresis is the
  duplicate-source rule; unresolved episodes excluded from rates but counted
  and disclosed; no silent deduplication; Δ in percentage points (zero-
  baseline rule — no relative-% of a small base rate).
- Detector is a single explicit sequential pass (state machine); shared
  verbatim between arms; no vectorization of the episode state logic.
  Vectorized pre-computation of distances/terciles is admissible (stateless).
- Bounded iterations: ≤ 4 concurrent control levels; caps on episode length;
  `tqdm` over instrument×domain and over bootstrap/permutation loops; helpers
  return data; output dirs in orchestration only; per-instrument memory
  bounds.
- The EXP-020 bounce-trigger machinery must not be imported into any metric
  path (lint-level assertion: no reference to trigger functions in the
  episode/outcome code path).

## Complexity Check

- Statistical tests: **2 binding / 2 budget** — the two pooled domain
  contrasts against the static control (bootstrap CI + within-stratum
  permutation + Holm are one machinery per contrast). Descriptive
  decompositions, the censoring bracket, and the moving-copy Δ_m (bootstrap
  CI only, no permutation, no Holm) reuse it and add no binding test.
- Visualisations: 4 / 4.
- New code modules: 2 / 2 — `python/src/xen/line_approach.py` (episode
  detector + control construction) and
  `python/experiments/EXP-040/code/run_experiment.py`.
