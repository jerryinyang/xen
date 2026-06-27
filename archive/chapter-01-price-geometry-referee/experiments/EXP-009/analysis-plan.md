# Analysis Plan: Experiment EXP-009

## Objective

Characterize the distribution of net (cost-applied) and gross effect sizes of a
broadened set of six untuned, fixed-parameter simple strategies, and locate each
effect relative to the EXP-003 pooled domain gate MDE. Exploratory measurement
(no per-strategy pass/fail); the deliverable is the effect-size distribution with
honest uncertainty.

## Methodology

### Step 1: Dependency gate and MDE map load

- **Method**: Assert `EXP-003/results/run_metadata.json`
  `overall_status == "COMPLETE"` with finite gate-stack MDE rows in
  `mde_summary.csv`; assert `EXP-004/results/run_metadata.json` present (the
  consistency-anchor methodology being extended). Load the pooled domain gate and
  minimal MDEs at the alpha grid.
- **Why this method**: Artifact-based gate, identical in spirit to EXP-004/005.
- **Simpler alternative considered**: Hardcoding `1/4/12 bps` — rejected; the MDE
  is read at runtime and asserted finite so the experiment fails loudly if the
  upstream map is missing or imprecise.
- **Assumptions**: EXP-003 MDE is the frozen reference; no new assumption.
- **Expected output**: Validated MDE map in memory.

### Step 2: Holdout-safe domain construction

- **Method**: For each instrument, `load_analysis_data` (first-70% slice only) →
  `build_domain_frames` for `{5m, 1h, 4h}` (5m strict, 1h/4h `min_coverage=0.90`)
  → `next_log_returns_from_bars` for `t -> t+1` returns and `domain_split_index`
  for the shared `CloseTime` train/test boundary. All from the frozen harness,
  unchanged.
- **Why this method**: Reuses the validated, holdout-safe substrate so EXP-009
  composes with the EXP-003/004 map.
- **Simpler alternative considered**: Re-implementing resampling locally —
  rejected (would risk diverging from the validated `aggregate_ohlc` and trigger
  re-validation).
- **Assumptions**: Chronological ordering by `CloseTime`; cross-domain split
  shared from the 1-minute base (never per-timeframe row fraction).
- **Expected output**: Per-instrument, per-domain return arrays + aligned frames
  + split index.

### Step 3: Strategy position generation (causal)

- **Method**: Compute six position series in `{-1, 0, +1}`, each aligned to the
  `t -> t+1` returns (length `= len(returns)`), using only information at or
  before bar `t`:
  - **Donchian(20)** and **MA(20/50)** — reuse harness
    `donchian_breakout_positions(lookback=20)` and
    `ma_crossover_positions(fast=20, slow=50)` unchanged.
  - **RSI(14) mean-reversion**, **Bollinger(20, 2.0) breakout**,
    **MACD(12,26,9) crossover**, **ROC(20) momentum** — new functions in the
    experiment-local helper `python/experiments/EXP-009/code/strategies.py`, each
    a pure NumPy function with the exact frozen conventions in `scope.md`
    (Wilder RSI; Bollinger population std `ddof=0`; recursive EMAs seeded by first
    value; trend/mean-reversion direction as specified). Each returns positions
    aligned to `t -> t+1` via a trailing `[:-1]` slice, matching the harness
    Donchian/MA convention. Warmup rows are flat (0); NaNs are converted to 0
    explicitly, never propagated.
- **Why this method**: Canonical, well-known indicators at standard fixed
  parameters — the simplest faithful realisation of "untuned breadth"; vectorised
  rolling/EMA computations are causally equivalent to an explicit loop.
- **Simpler alternative considered**: Reusing only Donchian/MA (the EXP-004 pair)
  — rejected; broadening the family set is the experiment's purpose.
- **Assumptions**: Indicators are deterministic functions of past closes; no
  look-ahead. Each indicator's warmup region is treated as flat, not dropped, so
  all six strategies share the same eligible-row denominator per domain.
- **Expected output**: Six aligned position arrays per instrument/domain.

### Step 4: Referee evaluation (gross + net effects)

- **Method**: For each strategy x instrument x domain, call the frozen
  `evaluate_referees(returns, positions, instrument=..., domain=...,
  alpha_values=(0.10,0.05,0.01), n_bootstrap=1000, seed=seed_for(...),
  split_index=domain_split_index(...))`. Record the minimal-baseline (gross)
  effect + CI and the gate-stack (net-of-cost) effect + CI, plus `effective_n`,
  `block_length`, and all five gate legs.
- **Why this method**: The stationary block-bootstrap mean CI is the frozen,
  programme-standard non-parametric uncertainty estimate; reusing
  `evaluate_referees` guarantees identical cost, materiality, and leg semantics to
  EXP-003/004 so effects are directly comparable to the MDE map.
- **Simpler alternative considered**: A plain t-interval on per-bar returns —
  rejected (assumes normality/independence; violates programme principles).
- **Assumptions**: Block bootstrap captures residual serial dependence; EXP-003/4
  found `block_length = 1` (near-iid per-bar strategy returns), reported per cell.
- **Expected output**: `strategy_effects.csv`, `strategy_verdicts.csv`.

### Step 5: Effect-vs-MDE location

- **Method**: For each cell at `alpha0`, classify the net gate effect as
  `below_MDE` (effect + its CI upper bound < domain MDE), `near_MDE` (within the
  EXP-003 grid uncertainty of the MDE), or `at_or_above_MDE` (effect ≥ MDE).
  Report the signed gap `net_effect - domain_MDE`.
- **Why this method**: Turns the continuous effect into the categorical read the
  question asks for, anchored to the calibrated MDE rather than to 0.
- **Simpler alternative considered**: Comparing effect to 0 only — rejected; the
  question is about position relative to the *MDE*, not statistical positivity.
- **Assumptions**: Domain MDE is finite (asserted Step 1).
- **Expected output**: `effect_vs_mde.csv`.

### Step 6: Distribution summary

- **Method**: Summarise the net-effect distribution per domain across all
  strategy x instrument cells (median, IQR, min, max, count `below/near/at_or_above`)
  and per strategy family across instruments (median net effect, dispersion).
  Descriptive only.
- **Why this method**: Directly answers "how is the distribution shaped"; medians
  and percentiles are distribution-free.
- **Simpler alternative considered**: Mean ± SD — rejected (mean/SD assume light
  tails; medians/IQR are robust).
- **Assumptions**: None (descriptive).
- **Expected output**: `effect_distribution_summary.csv`, `run_metadata.json`.

## Visualisations

1. **Forest plot of net effect ± CI per strategy x instrument, faceted by domain**,
   with the domain MDE drawn as a vertical reference line — the headline "where do
   effects sit vs MDE" view.
2. **Gross vs net effect scatter**, coloured by domain, with the identity line —
   shows the cost drag separating gross edge from net edge.
3. **Net-effect distribution per domain** (strip/box over the strategy x instrument
   cells) with the MDE marker — the distribution shape.
4. **Effect-vs-MDE classification matrix** (strategy x instrument per domain,
   coloured below/near/at_or_above) — categorical summary.
5. **Per-family net-effect distribution** (box per strategy across instruments,
   faceted by domain) — family-level dispersion.

## Interpretation Guide

- If every reportable cell's net effect (and CI upper bound) sits `below_MDE`, the
  broadened untuned set **strengthens the EXP-004 null/lower anchor** — simple
  untuned edges live below every domain MDE; no structural-blindness concern is
  raised by real simple strategies.
- If one or more cells are `at_or_above_MDE` with a CI excluding the MDE, that is a
  **measured candidate** worth a dedicated future experiment (recorded as a new
  EXP-ID), not acted on here.
- Cells whose effective sample misses D-prec (likely 4h) are **under-powered**;
  their effect CIs are reported but excluded from the distribution roll-up's
  precision claims.
- The experiment is **measurement-complete** when every reportable cell has a
  gross/net effect, CI, and MDE location.

## Implementation Safety Constraints (for experiment-developer)

- **Holdout**: Build domains only from the first-70% slice; never read past the
  analysis cutoff.
- **Look-ahead**: Every indicator uses only closes/highs/lows at or before `t`;
  positions align to `t -> t+1`. Verify each new indicator's first non-flat bar
  index ≥ its warmup length.
- **Real-price discipline**: Returns and effects come only from real domain
  `Close` via the frozen harness; no HA/Renko prices.
- **Determinism**: `evaluate_referees` is seeded via `seed_for(...)`; record the
  seed scheme. Indicators are deterministic.
- **NaN handling**: Explicit conversion of warmup/NaN to flat positions; assert no
  NaN reaches `strategy_return_bps`.
- **Denominators**: Eligible rows = domain bars with a defined `t -> t+1` return;
  all six strategies share this denominator per domain (flat warmup, not dropped).
- **Bounded plotting**: Pass aggregated effect rows (≤ 6 x 4 x 3 = 72 cells) to
  plots; no re-loading of bars or re-running bootstraps for plotting.
- **Progress**: `tqdm` over the instrument x domain x strategy loop.
- **Vectorization**: Rolling/EMA/RSI computations may be vectorised (causally
  equivalent); keep any genuinely sequential recursion (EMA) explicit and bounded.

## Complexity Check

- Statistical tests: 3 / 3 (block-bootstrap effect CIs; effect-vs-MDE
  classification; distribution summary)
- Visualisations: 5 / 5
- New modules: 1 / 1 (experiment-local `strategies.py`; Donchian/MA reused from
  the harness; no shared `python/src/xen` change)
