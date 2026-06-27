# Analysis Plan: Experiment EXP-098

**Cross-Broker & Aggregation-Method Robustness Replication of the RSI-2 Fade Deployment Portfolio (PPS data)**
Phase 022 · `CF-MR-001` / `HYP-003` (robustness companion) · **non-binding disclosure** · 2026-06-25
Scope: [`scope.md`](scope.md) · opened by [`D0-amendment-002`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/D0-amendment-002.md)

## Objective

Determine whether the **G-022a-frozen** RSI-2 fade deployment portfolio (carry-8 cells; binding-v2 noise-aware
causal ERC + intra-1h MTM; circuit breaker; EXIT-RCT / adverse / cost / band all frozen) — confirmed
`DEPLOYABLE_CONFIRMED` at EXP-097 on the cTrader/INFR-003 broker — **replicates on a completely independent
broker's feed** (`data/timebars/pps/`, same 8 instruments and span), and whether that replication is **robust to
the bar-aggregation timestamping method**. Two overfitting hypotheses, separated by two arms:

- **Broker overfit** (Arm 1 `PPS-CANON`, deployed aggregation): is the confirmed edge specific to the cTrader feed?
- **Aggregation overfit** (Arm 1 vs Arm 2 `PPS-ALTAGG`, last-source-close label): is it an artifact of our
  bucket-boundary timestamping?

The criterion is the **inherited EXP-097 band** — primary Portfolio B: annualized Sharpe LB > 2.00 AND co-binding
Calmar LB > 0 — applied per arm. **Nothing is tuned, re-derived, or re-selected.** The verdict is a robustness
label that **cannot upgrade or revoke** EXP-097's spent, non-upgradable verdict.

This is a **replication/robustness study**, not a new inference: there is no new estimator to calibrate, no new
null, and no selection. The analysis = run the frozen pipeline verbatim on independent data under two aggregations
and read the frozen statistic. The methods below are therefore (i) the verbatim-reused binding statistic, (ii)
descriptive disclosure, and (iii) integrity assertions.

## Methodology

### Step 1 — Independent-data load + two-arm domain-bar construction

- **Method**: Load each instrument's **full** PPS 1-minute file (`data/timebars/pps/timebars_<sym>_*.parquet`),
  sort by `CloseTime`, assert strictly increasing and the 8-column schema. Build domain bars **per arm**:
  - **Arm 1 `PPS-CANON`**: `xen.domain_bars.build_domain_bars(source, period)` verbatim
    (`aggregate_ohlc(min_coverage=0.90)` → bucket-right-boundary `CloseTime` label → analysis-boundary fence
    `CloseTime ≤ source_max`). 1h = 60-min, 4h = 240-min.
  - **Arm 2 `PPS-ALTAGG`**: identical bucketing (`(epoch−1)//period_s`), coverage (0.90), and OHLC reduction
    (first Open / max High / min Low / last Close / summed Volume), but each bar's `CloseTime` = the **actual last
    source 1-minute `CloseTime`** in the bucket (not the boundary), then the same `CloseTime ≤ source_max` fence
    (trivially satisfied — a behavioral difference the arm exists to surface). Implemented as a small
    orchestration-level helper that mirrors `aggregate_ohlc` but swaps the label column; **no `xen/` module is
    mutated**.
- **Why this method**: Arm 1 is the exact deployed construction (true cross-broker replication); Arm 2 isolates
  the single timestamping degree of freedom while holding bucketing/coverage/OHLC and everything downstream fixed.
- **Simpler alternative considered**: a single arm (broker only). Rejected — the operator explicitly requires the
  aggregation-method overfit test, which needs the second arm. No simpler design answers both questions.
- **Assumptions**: PPS bars are real OHLC for the same instruments/span; deterministic aggregation. Holds — schema
  verified, deterministic pure functions.
- **Expected output**: per-arm, per-cell domain-bar frames + a coverage/drop diagnostic (`SourceBars`,
  dropped-window fraction, n_domain_bars, label-vs-boundary offset distribution for Arm 2) written to results.

### Step 2 — Per-cell binding-v2 EXIT-RCT net streams over the full PPS series (per arm)

- **Method**: Reuse the EXP-090/095/096 substrate **verbatim** (`build_cell_context`, exit-path/keep-mask logic,
  `resolve_entry_fills`, `resolve_cell_noise`) to resolve, for each of the 8 cells, the binding-**v2** EXIT-RCT net
  per-event return stream (ATR(14) units): `net = dir·(exit_fill − entry_fill)/atr − cost`, with entry fill =
  next-1m-open + 0.05×ATR adverse slippage, adverse 2.0×ATR + MR-tempo cap, `D0-amendment-003` conservative cost.
  The substrate's `train_edge_epoch` is set to the **file end** so entry-fill + exit walks resolve over the entire
  PPS series (not clipped at an analysis cutoff — there is no held-back slice here).
- **Why this method**: byte-identical reuse is the whole point of a replication — any deviation would confound
  "broker effect" with "code change."
- **Simpler alternative considered**: none — reuse is mandatory.
- **Assumptions**: the frozen substrate is correct (audited at EXP-090/093/097). Holds.
- **Expected output**: 8 per-cell `CellStream` objects per arm (net, exit_epoch, entry_epoch, exit/entry fills).

### Step 3 — Causal ERC portfolios A & B over the full evaluable grid (per arm)

- **Method**: Reuse `xen.portfolio` via `E95.build_grid` + `PF.build_portfolio` **verbatim**: align the 8 cells on
  the 1h grid with intra-1h MTM; build **Portfolio A** (static ERC, `use_breaker=False`) and **Portfolio B** (ERC
  + circuit-breaker, `use_breaker=True`) from a causal trailing-90-day Ledoit-Wolf covariance, weekly rebalance,
  10% annualized-vol anchor, 1.5× concurrent-risk cap, trailing-50-trade breaker. Also build `naive_inverse_vol`
  as a non-binding contrast. Weights past-only at every step (asserted in Step 6).
- **Evaluable region (binding-metric support)**: the **full PPS grid after the unavoidable estimator burn-in** —
  i.e. exclude only the leading region where the trailing covariance (`LOOKBACK_STEPS`), indicator warmup, and
  breaker-50 state are not yet defined. Operationally, set the metric boundary `H_eval` = the grid epoch at the
  first step where weights are well-defined (the first rebalance with a full lookback window). This is **not a
  holdout** — it is the minimal warmup the estimators require; record `H_eval`, the burn-in step count, and
  `n_weeks` of the evaluable region. (Contrast EXP-097, where the metric was restricted to the *holdout* region
  for contamination reasons; here the entire post-warmup series is legitimately out-of-sample because PPS was
  never used for any selection.)
- **Why this method**: the deployment estimand is the portfolio, not a single cell; verbatim reuse preserves
  comparability to EXP-097.
- **Simpler alternative considered**: per-cell-only replication (skip the portfolio). Rejected — the confirmed
  deployment object *is* the portfolio; per-cell is the disclosure layer (Step 5), not the headline.
- **Assumptions**: hourly grid annualization fixed by `PERIODS_PER_YEAR_HOURLY`; ERC well-conditioned on PPS
  covariance. If a rebalance covariance is degenerate, `_rebalance_weight` falls back per the frozen module
  (recorded), never silently.
- **Expected output**: per-arm A/B/naive return series on the grid + the weight matrices; `H_eval` + evaluable
  `n_weeks` per arm.

### Step 4 — Binding robustness statistic (verbatim EXP-095 statistic; per arm, per portfolio)

- **Method**: `E95.series_risk_metrics` **verbatim** on the **evaluable** portfolio return series (`epoch ≥
  H_eval`) for P ∈ {A, B} (and naive, disclosed): weekly-aggregated annualized Sharpe + Calmar **moving-block
  one-sided lower bounds** (block = `default_block_length(n_weeks)`, `N_BOOT = 10_000`, `α = 0.10` → one-sided 95%
  LB), seeded by `seed_for(EXP-098, "ppsrobust", <arm>_<P>)`. Frozen decision rule:
  `CONFIRM(P) iff Sharpe_LB(P) > band_P AND Calmar_LB(P) > 0`, `band_A = 1.75`, `band_B = 2.00`.
- **Why this method**: it is the *identical* statistic G-022a froze and EXP-097 used; a robustness read must apply
  the same bar. Moving-block bootstrap respects the serial dependence of a time-ordered return series (no i.i.d.
  assumption) — the programme-standard non-parametric interval.
- **Simpler alternative considered**: a plain point-Sharpe comparison. Rejected — it ignores sampling uncertainty;
  the frozen rule is LB-based and must be honored.
- **Assumptions**: weekly blocks capture the dependence scale; one-sided LB is the conservative deployment bar.
  Holds (same as EXP-095/097; serial-dependence-robust).
- **Expected output**: per-arm `{A, B, naive_iv}` metric dict (`ann_sharpe`, `ann_sharpe_lo`, `calmar_lo`,
  `n_weeks`, MaxDD, CVaR5, Ulcer, ann ret/vol, turnover) + `CONFIRM_A`, `CONFIRM_B` per arm.

### Step 5 — Per-cell PPS disclosure + masking check (LESSON-001) + retention companion

- **Method (per-cell, per arm)**: for each of the 8 cells over the full evaluable region (`exit_epoch ≥ H_eval`),
  report net mean / median / one-sided 95% MBB LB (`moving_block_bootstrap_cis(..., n_boot=10_000, α=0.10)`) and a
  `net_negative` flag. **Masking check**: confirm no single cell carries the portfolio label (drop-one
  sensitivity: does removing the largest-|contribution| cell flip CONFIRM_B?) and no net-negative cell is hidden
  inside a positive aggregate.
- **Method (retention companion, descriptive, non-binding)**: read EXP-097's **committed** outputs
  (`python/experiments/EXP-097/results/holdout_metrics.csv`, `per_cell_holdout.csv`) — **the INFR-003 data is NOT
  re-read** — and tabulate the PPS-vs-INFR-003 retention: PPS Portfolio B Sharpe LB ÷ EXP-097 holdout B Sharpe LB,
  and per-cell PPS net mean/ci_low vs the EXP-097 holdout per-cell values. This quantifies *how much* of the edge
  is broker/aggregation-portable (a context number, not a gate).
- **Why this method**: LESSON-001 — a pooled portfolio headline must be shown not to mask heterogeneity; the
  retention companion turns "robust/degraded" into an interpretable magnitude.
- **Simpler alternative considered**: portfolio-only reporting. Rejected — masking checks are mandatory in this
  programme.
- **Assumptions**: EXP-097 committed CSVs are the authoritative INFR-003 reference (they are — audited, post-exec
  APPROVE). Different broker ⇒ different resolved-event counts per cell; report n per cell and never align by index.
- **Expected output**: `per_cell_pps_<arm>.csv`, the masking-check result (drop-one flip = yes/no per arm), and a
  `retention.json` companion.

### Step 6 — Integrity assertions (real-price, causal, deterministic, conserving)

- **Method**: reuse the EXP-096/097 integrity battery per arm: (i) **determinism replay** — second pass of the
  entry-fill walk + ERC solve + MTM + bootstrap returns byte-identical A/B series and identical Sharpe/Calmar LBs;
  (ii) **MTM conservation** — Σ(intra-1h marks) = realized net per cell (≤ 1e-9 ATR); (iii) **causal-weight
  assertion** — perturbing grid rows strictly after a rebalance does not change that rebalance's weight; (iv)
  **causal-fill assertion** — perturbing a 1-minute bar strictly before a signal close does not change that
  event's entry fill; (v) **real-price only** — all P&L from real domain & 1-minute OHLC; no HA/Renko; (vi)
  **independent-data assertion** — `infr003_holdout_loaded = false`, only PPS files opened; `counted_test_reads =
  0`, `candidate_slots = 0`, `exp097_verdict_unchanged = true`.
- **Why this method**: a replication's credibility rests entirely on it being the *same* computation on *different*
  data; these assertions certify that.
- **Assumptions**: none beyond determinism of the frozen code.
- **Expected output**: `integrity.json` (all pass/fail flags) + per-cell conservation table per arm.

### Step 7 — Robustness adjudication (mechanical, frozen, non-binding)

- **Method**: per arm, label the **primary Portfolio B**: `ROBUST` iff `CONFIRM_B`; `DEGRADED` iff
  `Sharpe_pt(B) ≤ 2.00 OR Sharpe_LB(B) ≤ 0`; `INCONCLUSIVE` otherwise. Overall: `CROSS_BROKER_ROBUST` iff Arm 1
  (PPS-CANON) is ROBUST; `AGGREGATION_ROBUST` iff **both** arms are ROBUST. A is co-reported (no OR rescue). The
  label is recorded as a registry **robustness governance disclosure**; it does **not** alter EXP-097.
- **Expected output**: `verdict.json` (per-arm B/A confirm + labels + overall) + `run_metadata.json`.

## Visualisations (≤ 5)

1. **PPS equity curves, A vs B vs naive (+ 8 per-cell), faceted by arm** — replication shape on independent data;
   shows whether the diversified portfolio behaves like EXP-097's holdout curve.
2. **Sharpe LB & Calmar LB vs band, both arms (A & B), with EXP-097 holdout reference markers** — the binding read
   at a glance: does each arm's B clear band 2.00 / Calmar 0, and how far below the INFR-003 holdout value.
3. **Per-cell PPS net (mean; whisker = MBB LB) per arm, vs EXP-097 holdout per-cell net** — masking + retention:
   which cells port, which decay, is any single cell carrying/hiding the label (red = net-negative).
4. **A vs B drawdown (underwater), faceted by arm** — does the circuit breaker still control drawdown on the new
   broker; MaxDD comparability to EXP-097.
5. **Arm 1 vs Arm 2 metric comparison (Sharpe LB, Calmar LB, MaxDD, n_weeks, n_domain_bars)** — the
   aggregation-sensitivity panel: how much the last-source-close label moves the headline.

## Interpretation Guide (pre-registered, before results exist)

- **CROSS_BROKER_ROBUST** if Arm 1 (PPS-CANON) Portfolio B clears Sharpe LB > 2.00 AND Calmar LB > 0 → the
  confirmed edge replicates on an unrelated broker; it is not a cTrader-feed artifact. (Some decay vs the 4.762
  INFR-003 holdout LB is expected and acceptable — the bar is the absolute band, not parity.)
- **AGGREGATION_ROBUST** if **both** arms' Portfolio B confirm → the edge is invariant to the timestamping rule;
  not an artifact of bucket-boundary labeling.
- **AGGREGATION-SENSITIVE (disclosed)** if Arm 1 confirms but Arm 2 does not (or vice-versa) → the edge depends on
  the aggregation method; report the mechanism (drop-behavior / label-offset differences from Step 1 diagnostics).
- **DEGRADED** on an arm if B's Sharpe point ≤ 2.00 or Sharpe LB ≤ 0 → the edge does not replicate on that
  broker/aggregation; recorded permanently as a robustness limit. **EXP-097 is unchanged.**
- **INCONCLUSIVE** on an arm if B is neither (point > 2.00 but LB ≤ 2.00, or Calmar fails while Sharpe holds) →
  power-limited / spans the band; disclosed.
- **Masking caveat**: if the drop-one check flips CONFIRM_B, the arm's "robust" label is downgraded to
  **one-cell-dependent (disclosed)** regardless of the pooled number.
- **Retention reading**: PPS/INFR-003 Sharpe-LB ratio near 1 = broker-portable; ≪ 1 but still > band = portable
  but feed-sensitive; < band = broker-specific. Per-cell retention names which instruments travel.

## Implementation safety constraints (for `experiment-developer`)

- **Timestamp ordering**: sort every PPS file by `CloseTime`; assert strictly increasing; align cells across
  domains by `CloseTime` epoch, **never by bar index**. Arm 2's last-source-close label must still yield a
  `CloseTime`-sorted domain frame (assert).
- **Full-timeline, no holdout slice**: load the **full** PPS file; do **not** apply a 0.7 cutoff (there is no
  held-back slice). `H_eval` is the estimator-warmup boundary only — derive it from `LOOKBACK_STEPS` /
  first-full-lookback rebalance, not from a data fraction. Assert `infr003_holdout_loaded = false` and that only
  `data/timebars/pps/` files are opened.
- **Denominators**: per-cell net denominator = resolved PPS events (v2 keep mask); portfolio metric denominator =
  the evaluable-region grid statistics. Report n_events per cell and n_weeks per arm. A grid window with < 2
  resolved trades on the trailing grid is `INDETERMINATE` (0 weight, recorded).
- **Zero-baseline / NaN**: no zero-baseline ratio for the binding figure (absolute LB vs band). Guard
  Sharpe/Calmar against zero vol / zero MaxDD → `NaN` with a flag, never `inf`. Never let NaN propagate silently
  into a metric.
- **Bounded iteration / progress**: `tqdm` over the 8 cells × 2 arms; `N_BOOT = 10_000` fixed; no unbounded loops;
  no full-data pandas conversion for plots beyond the bounded series already in memory.
- **Vectorization safety**: Arm 2's alternate aggregation is a Polars group-by (same as `aggregate_ohlc`) — safe
  to vectorize. The entry-fill walk and ERC/breaker state are **sequential/causal** and must stay as the frozen
  module implements them; do not re-vectorize them.
- **No `xen/` mutation**: all new logic (PPS discovery override, Arm-2 aggregation helper, two-arm driver) lives
  in `code/run_experiment.py`. Reuse `E95`/`E96`/`E90`/`PF`/`xen.ass`/`xen.domain_bars`/`xen.bar_aggregator`
  verbatim.
- **Real-price discipline**: every return/drawdown from real OHLC; no synthetic prices.

## Complexity Check

- **Statistical tests**: 1 binding statistic (portfolio B Sharpe LB + co-binding Calmar LB vs band) evaluated
  **per arm** (2 evaluations of one frozen rule) + per-cell MBB intervals (descriptive disclosure) — within the
  scope budget.
- **Visualisations**: 5 / ≤ 5.
- **New modules**: 0 new `xen` modules / target 0 (orchestration-only changes in `code/run_experiment.py`).
