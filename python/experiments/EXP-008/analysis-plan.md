# Analysis Plan: Experiment EXP-008

## Objective

De-pool the EXP-003 pooled-by-domain gate-stack MDE map into per-instrument MDEs
and test H-pool: whether per-instrument gate MDEs differ from the pooled domain
MDE by at least the frozen margin `max(0.5 bps, 20% of pooled_MDE(domain))` at
`alpha0 = 0.05`. This is a result-level reprocessing of already-holdout-safe
EXP-003 artifacts; no new market data is read and no new module is written.

## Methodology

### Step 1: Dependency gate and artifact load

- **Method**: Assert `EXP-001/results/run_metadata.json` has
  `overall_status == "PASS"`; assert `EXP-003/results/run_metadata.json` has
  `overall_status == "COMPLETE"`; assert `EXP-003/results/draw_verdicts.csv` and
  `mde_summary.csv` exist. Lazily scan `draw_verdicts.csv` with Polars,
  projecting only the columns needed (`instrument, domain, scenario, generator,
  edge_bps, referee, alpha, passed`) before `collect()` to bound memory on the
  142 MB file.
- **Why this method**: Mirrors the artifact-based dependency gate used by
  EXP-004/005/006; fails fast and explicitly if an upstream artifact is missing.
- **Simpler alternative considered**: Reading the full CSV into pandas — rejected
  as wasteful (142 MB, most columns unused) and slower than projected Polars scan.
- **Assumptions**: EXP-003 draws are the frozen, validated substrate; their
  `passed` flags are authoritative. No temporal assumption is introduced (the
  draws already respect chronological splits).
- **Expected output**: A validated, projected verdict frame plus the loaded
  pooled MDE map.

### Step 2: Per-instrument FPR (gate stack)

- **Method**: For null-scenario rows, group by `instrument x domain x referee x
  alpha`; FPR = `passed.sum() / n`; attach the Wilson 95% interval via the frozen
  `xen.referee_calibration.wilson_interval` (reused through `verdict_rate_rows`).
- **Why this method**: Binomial proportion with a Wilson interval is the
  programme-standard non-parametric rate estimator (used by EXP-003/005/006); it
  behaves well at `p -> 0`, which is the expected gate-stack FPR regime.
- **Simpler alternative considered**: Raw proportion without an interval —
  rejected because the D-prec precision gate needs the Wilson half-width.
- **Assumptions**: Draws within a cell are exchangeable Bernoulli trials under the
  null — the same assumption EXP-003 already relied on; no normality or
  stationarity assumption.
- **Expected output**: `per_instrument_fpr_summary.csv` (FPR + Wilson bounds +
  half-width + counts per cell).

### Step 3: Per-instrument TPR (gate stack)

- **Method**: For positive-scenario rows, group by `instrument x domain x referee
  x alpha x edge_bps`; TPR = `passed.sum() / n` with the Wilson interval, same
  helper.
- **Why this method**: Same non-parametric rate estimator; consistent with how
  EXP-003 built its TPR curves.
- **Simpler alternative considered**: Pooled TPR (the EXP-003 object) — rejected
  because de-pooling is the entire point of EXP-008.
- **Assumptions**: As Step 2, per edge.
- **Expected output**: `per_instrument_tpr_summary.csv`.

### Step 4: Per-instrument MDE determination

- **Method**: For each `instrument x domain x alpha`, scan the EXP-003 edge grid
  `{0.5, 1.0, 2.0, 4.0, 8.0, 12.0, 16.0, 24.0, 32.0}` bps in ascending order and
  select the **smallest** edge whose per-instrument TPR `>= 0.80` while the
  per-instrument FPR at that cell is `<= alpha`, **and** the D-prec precision
  target is met there (FPR Wilson half-width `<= 0.03`, TPR Wilson half-width
  `<= 0.05`). Record `mde_bps`, the local grid spacing to the next-lower grid
  point as `mde_grid_uncertainty_bps`, and the TPR Wilson half-width at the MDE.
  If no grid edge satisfies the rule with precision, record the MDE as
  non-finite/`UNDER_POWERED`.
- **Why this method**: This is the exact EXP-003 MDE definition restricted to a
  single instrument — required for an apples-to-apples comparison with the pooled
  MDE.
- **Simpler alternative considered**: Interpolating a continuous MDE between grid
  points — rejected as overreach; the calibration is grid-defined and
  interpolation would invent precision the draws do not support.
- **Assumptions**: TPR is monotone non-decreasing in edge (verified in EXP-003);
  the plan reports any non-monotonicity beyond Monte-Carlo precision rather than
  silently picking the first crossing.
- **Expected output**: `per_instrument_mde_summary.csv`.

### Step 5: Material-difference comparison

- **Method**: For each `instrument x domain` at `alpha0=0.05`, read the pooled
  gate MDE from EXP-003 `mde_summary.csv` (`referee=gate_stack, alpha=0.05`;
  assert finite), compute `delta = per_instrument_MDE - pooled_MDE`, compute the
  frozen margin `max(0.5, 0.20 * pooled_MDE)`, and set
  `material = |delta| >= margin`. When `|delta|` is below the larger of the two
  cells' local grid spacings, additionally tag `within_grid_resolution = true` so
  a one-grid-step difference is not over-interpreted as material.
- **Why this method**: Directly operationalises the frozen H-pool criterion;
  absolute-bps margin with a 20%-of-baseline floor avoids any zero-baseline ratio
  (pooled MDE is 1/4/12 bps, strictly positive).
- **Simpler alternative considered**: Percent-difference only — rejected because a
  pure ratio is unstable near small MDEs and the design froze the additive-floor
  form.
- **Assumptions**: None beyond the grid-quantisation caveat already stated.
- **Expected output**: `mde_pool_comparison.csv` (delta, margin, `material`,
  `within_grid_resolution`) and `run_metadata.json` recording the H-pool roll-up.

## Visualisations

1. **Per-instrument vs pooled MDE, faceted by domain** — dot/bar plot of each
   instrument's gate MDE with the pooled MDE drawn as a reference line and the
   frozen margin band shaded; answers "which instruments fall outside the margin".
2. **Per-instrument TPR vs edge, faceted by domain** — four instrument curves
   overlaid with the 0.80 target line and each instrument's selected MDE marked;
   shows where each instrument crosses detection.
3. **Per-instrument FPR at `alpha0`, faceted by domain** — bar plot with the
   `alpha0` line and Wilson error bars; confirms FPR control survives de-pooling.
4. **Material-flag matrix** — instrument x domain grid coloured by
   `material / within_grid_resolution / under_powered`; the headline summary.

## Interpretation Guide

- If at least one reportable `instrument x domain` cell at `alpha0` has
  `material = true`, **H-pool is SUPPORTED** — the pooled MDE masks instrument
  heterogeneity, and EXP-011 must treat per-instrument MDE as first-class.
- If every reportable cell at `alpha0` is within the margin
  (`material = false`), **H-pool is REFUTED** — the pooled domain MDE is an
  adequate per-instrument proxy.
- If most/all 4h per-instrument cells miss D-prec (no finite MDE with precision),
  those cells are **INCONCLUSIVE / under-powered**, reported with honest Wilson
  half-widths; the experiment is overall inconclusive only if no cell is
  reportable at `alpha0`.

## Implementation Safety Constraints (for experiment-developer)

- **Holdout**: Do not load any raw Parquet beyond the EXP-003 artifacts; if any
  raw replay is unavoidable, use the first-70% slice only. EXP-003 outputs are
  already holdout-safe.
- **Denominators**: Use raw draw-verdict counts per cell; never deduplicate or
  drop draws. Report `n` on every rate row.
- **Zero-baseline**: `margin = max(0.5, 0.20 * pooled_MDE)` is defined even if a
  pooled MDE were 0 (floor 0.5); assert pooled MDE finite before comparison.
- **Bounded memory**: Project columns in the lazy scan before `collect()`;
  aggregate with Polars `group_by` rather than materialising per-draw Python
  loops over the 216k rows.
- **Determinism**: Pure post-processing — output is a deterministic function of
  the EXP-003 CSVs; no RNG.
- **Progress**: The single grouped aggregation pass is fast; `tqdm` is optional
  and only over the small domain/instrument summary loops if used at all.

## Complexity Check

- Statistical tests: 3 / 3 (per-instrument FPR Wilson; per-instrument TPR
  Wilson / MDE; material-difference comparison)
- Visualisations: 4 / 4
- New modules: 0 / 0
