# Analysis Plan: Experiment EXP-095

**Title:** Portfolio Construction & Online-Adaptive Risk Model (RSI-2 Fade, 8 confirmed cells)
**Family / HYP:** `CF-MR-001` / `HYP-003` · **Phase:** 022 (batch 3) · **Date:** 2026-06-24
**Scope:** [`scope.md`](scope.md) · **Design:** [`design.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/design.md) · **D0:** [`D0-predeclarations.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/D0-predeclarations.md)
**Reads / slots:** 0 counted TEST reads · 0 candidate slots · final-30% global holdout **NEVER loaded** (EXP-097 only).

---

## Objective

Built from the **8 G-021-confirmed cells**, determine on the **analysis set** (TRAIN + the EXP-093
already-resolved analysis-TEST series, reused as portfolio-aggregate disclosure):

1. **Portfolio economics.** Does a causal, parameter-free **ERC** portfolio deliver materially better
   risk-adjusted performance (annualized **Sharpe**, with MaxDD / Calmar co-reported) than the **best
   individual cell** (and the naive inverse-vol contrast)?
2. **Online adaptability (headline).** Does adding an online performance **circuit-breaker** (Portfolio **B**)
   measurably de-risk a deteriorating cell versus static ERC (Portfolio **A**)?
3. **Gate readiness for G-022a.** Is the **NEW** portfolio-level holdout confirmation statistic
   **calibrated** (synthetic-null FPR ≤ 0.05) and **bite-checked GREEN** for both A and B, so G-022a can
   freeze it before the EXP-097 holdout read?

This plan is **descriptive on the analysis set** — it issues **no holdout verdict**. The binding deployment
read is EXP-097, under the G-022a-frozen rule. No hyperparameter is selected here; every value is frozen at
its D0 ratified-table value and brackets are disclosure only.

---

## Data inputs & provenance

### Per-cell return streams (the portfolio building blocks)

The portfolio requires, **per deployable cell**, the resolved **EXIT-RCT net per-event return (ATR units)**
**timestamped at the event exit `CloseTime`**, over the **full analysis set** (TRAIN region + the EXP-093
analysis-TEST stratum). The 8 cells (D0 §D1 / param #1):

| # | Cell | Domain | G-021 tier |
|---|---|---|---|
| 1 | EURUSD-4h | 4h | robust core (mean-AND-median +) |
| 2 | XAUUSD-4h | 4h | robust core |
| 3 | USDCHF-4h | 4h | robust core |
| 4 | AUDJPY-4h | 4h | robust core |
| 5 | EURJPY-4h | 4h | robust core |
| 6 | GBPJPY-4h | 4h | robust core |
| 7 | USTEC-1h | 1h | mean-carried (TEST median −0.026) |
| 8 | US2000-1h | 1h | mean-carried (TEST median ≈ 0) |

**Provenance constraint (verified at plan time).** EXP-093 / EXP-092 persist only per-cell **summary** CSVs
(`test_per_cell.csv`: `net_mean`, `net_median`, `net_ci_low`, `n_resolved`, …). The **timestamped per-trade
streams** are computed in-memory in the EXP-090 substrate path and **not** persisted as artifacts. Therefore
EXP-095 reconstructs them by **deterministic re-resolution through the identical frozen substrate** — it
imports the EXP-090 module (`build_cell_context`, `resolve_arm`/RCT, `net_return_atr`, the 1-minute intrabar
fill) and the EXP-092/`D0-amendment-003` cost overlay **unchanged**, with the **same entry rule (RSI 2/10/90),
same exit (EXIT-RCT), same adverse (2.0×ATR + MR-tempo cap), same cost table (hash `fa7c887…`, F=0), same data
slices**. Because generation is deterministic, the regenerated streams are **byte-equivalent in substance** to
EXP-093's "reused verbatim" intent.

**Provenance gate (binding, Step 1).** The regenerated **analysis-TEST-stratum** per-cell summary statistics
(`net_mean`, `net_median`, `n_resolved`, `resolved_frac`, `net_ci_low`, `boot_p`) must **reconcile to
EXP-093 `test_per_cell.csv`** for all 8 cells to a tight numerical tolerance (≤ 1e-9 ATR on means / medians;
exact on integer counts). A mismatch is a **provenance failure** → halt and route to governance/developer
(not a silent proceed). The TRAIN-region streams have no prior persisted summary; their reconciliation is
**internal determinism only** (Step 9 second-pass byte-identity).

### Slices & exclusions

- **Analysis set per file:** `[0, int(total_rows·0.7))`. Within it: **TRAIN** `[0, int(int(total·0.7)·0.7))`
  + **analysis-TEST** `[int(int(total·0.7)·0.7), int(total·0.7))`. The portfolio curve and **all** weights are
  built **causally** across this window (trailing estimates only).
- **MANDATORY EXCLUSION:** the final-30% global holdout `[int(total_rows·0.7), total_rows)` — including its
  1-minute bars — is **never loaded, sliced, or materialized**. `holdout_untouched=true` asserted in
  `run_metadata.json`.
- **Dataset:** VAL-005-admitted INFR-003 5-year 1-minute bars, holdout-fenced `build_domain_bars`
  (1h=60-min, 4h=240-min). Real OHLC only.

---

## Methodology

### Step 1 — Per-cell stream regeneration + provenance reconciliation

- **Method:** deterministic re-resolution of EXIT-RCT net per-event returns through the frozen EXP-090/092
  substrate for the 8 cells over the analysis set; reconcile the analysis-TEST summary against EXP-093.
- **Why this method:** the timestamped streams are not persisted; faithful reuse = identical-code regeneration
  with a numeric reconciliation gate. This is the strongest available guarantee of "verbatim" reuse.
- **Simpler alternative considered:** read a persisted per-trade artifact — **does not exist** (only summaries
  persisted), so insufficient.
- **Assumptions:** deterministic generation (no seeds in resolution; fill walk is path-deterministic). Holds
  by construction (programme deterministic-generation principle).
- **Expected output:** 8 per-cell arrays of `(exit_CloseTime, net_return_atr, direction)`; a
  `provenance_reconciliation.csv` (8 rows: regenerated vs EXP-093 stat, abs diff, PASS/FAIL).

### Step 2 — Time-aligned portfolio equity curve (D0 §D2.1)

- **Method:** mark per-cell P&L on the **common wall-clock grid = the finest deployable domain's close (1h)**;
  4h positions are **marked-to-market at each intervening 1h close** and realized at their exit; aggregate
  per-cell marks by **timestamp** into one portfolio return series. Alignment by `CloseTime` epoch, **never**
  bar index.
- **Why this method:** a single timestamp grid is the only causal way to combine 1h and 4h cells without
  bar-count misalignment; MTM gives an interpretable drawdown path.
- **Simpler alternative considered:** event-pooled returns ignoring time (used for the co-binding expectancy
  companion) — insufficient for Sharpe/MaxDD/Calmar, which need a time series; kept as a companion, not the
  curve.
- **Assumptions:** a position's P&L accrues over its holding interval; intermediate 1h marks use the cell's
  own resolved trajectory (MTM from the realized per-event path, not look-ahead to the final exit). Where an
  intermediate-mark trajectory is unavailable, mark the realized return at exit `CloseTime` and hold flat
  between (documented; conservative for drawdown timing) — chosen at implementation, recorded.
- **Expected output:** `portfolio_returns_A.csv` and `portfolio_returns_B.csv` (timestamp-indexed net return
  on the 1h grid), plus per-cell contribution columns.

### Step 3 — Causal ERC weights (D0 §D2.2; params #2/#3/#4)

- **Method:** at each **weekly** rebalance *r*, estimate the 8×8 covariance from the **trailing 90 trading
  days** of per-cell return streams resolved **strictly before** *r* (**Ledoit-Wolf** shrinkage to the
  diagonal, parameter-free); solve **ERC** weights (equal marginal risk contribution) by the standard
  deterministic convex iteration (fixed tolerance, fixed max-iters, no random init); **hold** weights until
  the next rebalance.
- **Why this method:** ERC equalizes covariance-aware marginal risk across a **correlated** set (the 4h JPY
  cluster EURJPY/GBPJPY/AUDJPY; EURUSD/USDCHF), with **no free weight parameter** → no overfitting. Ledoit-Wolf
  stabilizes the 8×8 estimate in the small-sample/high-correlation regime without a tuned ridge.
- **Simpler alternative considered:** naive inverse-vol — over-allocates to the JPY cluster; **kept as a
  disclosed contrast baseline**, not the binding construction.
- **Assumptions:** covariance is locally stable over a quarter; trailing window is representative. Weak in
  regime shifts — mitigated by weekly recompute + shrinkage; **never** full-sample (that is look-ahead).
- **Warmup / INDETERMINATE:** a cell with `< min_trailing_sample` resolved trades at *r* carries **0 weight**
  until it has history (causal warmup, recorded). A rebalance window with `< 2` resolved trades on the
  trailing grid is `INDETERMINATE` for that mark (0 weight, not forced to a number) — scope §8.
- **Expected output:** `weights_timeline.csv` (per rebalance: per-cell ERC weight, effective trailing n);
  covariance-condition diagnostics.

### Step 4 — Global risk anchor + concurrent-risk cap (D0 §D2.3; params #5/#6)

- **Method:** scale all weights by the single global scalar targeting **10% annualized portfolio vol**
  (estimated on the trailing window — causal); cap total open **risk-aware** (correlation-adjusted) exposure
  at **1.5×** the per-rebalance risk budget (a simultaneous JPY-cluster firing counts ≈ one bet); pro-rata
  scale-down at the moment of breach (causal, recorded).
- **Why this method:** the anchor turns ATR-returns into interpretable currency-P&L (MaxDD readable); the cap
  is the principled "max positions" guardrail under correlation.
- **Invariance check:** **Sharpe is invariant** to the global scalar — assert numerically (recompute Sharpe at
  7%/10%/15% → identical to tolerance). This is a correctness check, **not** a bracket selection.
- **Expected output:** the scaled weight path; `risk_anchor_invariance.json`; cap-breach log.

### Step 5 — Online circuit-breaker overlay → Portfolio B (D0 §D3; param #7)

- **Method:** per cell, maintain a **causal trailing-50-resolved-trade mean net return** (ATR units), updated
  only as that cell's trades resolve; allocation multiplier = **0 while that trailing mean < 0**, **1 while
  ≥ 0** (re-allocates on recovery); applied multiplicatively to the ERC weight **before** the risk-anchor
  scaling. **Portfolio A** = multiplier ≡ 1 (vol-adaptive only); **Portfolio B** = with breaker
  (vol- *and* edge-adaptive). Both run in parallel.
- **Why this method:** ERC is **expectancy-blind** (rebalances on vol, not edge) → a mean-decaying cell keeps
  its allocation and bleeds. A parameter-light, conservative trailing-mean breaker is risk management
  (de-risking a decaying book), not return optimization.
- **Simpler alternative considered:** no breaker — that **is** Portfolio A; the A-vs-B contrast is the read.
- **Assumptions:** trailing realized mean is an admissible online edge proxy. Strictly causal (no look-ahead
  into recovery).
- **Expected output:** `circuit_breaker_timeline.csv` (per cell: de-allocation on/off intervals, trailing
  mean); B-weight path.

### Step 6 — Binding metric: risk-adjusted edge vs baselines (D0 §D4)

- **Method (binding):** **annualized Sharpe** of the time-aligned net portfolio return series (after D1 cost),
  with a **moving-block bootstrap one-sided lower bound** via `xen.ass.moving_block_bootstrap_cis` extended to
  the portfolio series, **block length = the rebalance cadence** (weekly, expressed in 1h-grid steps;
  recorded), `N_BOOT = 10_000`, seeded (`seed_for`, master `20260624`). **Co-binding companion:** pooled net
  per-trade **expectancy** one-sided lower bound (same machinery on the event-pooled stream).
- **Sharpe-pitfall reconciliation (explicit).** The methods-catalog flags raw Sharpe (normality / upside
  penalty). D0 **binds** annualized Sharpe as the metric; this plan honors it **without** the parametric
  pitfall by (a) quantifying its uncertainty with the **non-parametric moving-block bootstrap** (no normality
  assumption on the CI; serial dependence preserved), and (b) **co-reporting downside metrics MaxDD / Calmar**
  (addresses the upside-penalty critique). The Sharpe **point** estimate is the binding figure; its **lower
  bound** is the inferential object.
- **Baselines:** the **best individual deployable cell's** annualized Sharpe (point estimate, per-cell) and
  the **naive inverse-vol** portfolio (disclosed contrast). The portfolio "beats" iff its Sharpe **lower
  bound** exceeds the best single cell's **point** estimate by a **material margin** (the margin is reported;
  the G-022a band is set from this estimate — not selected here).
- **Why this method:** moving-block bootstrap is the programme-standard distribution-free uncertainty for
  serially dependent return series (EXP-077/093 precedent). Comparison-to-best-single-cell is the
  diversification estimand.
- **Expected output:** `portfolio_metrics.csv` (A, B, best-cell, naive-IV × {ann Sharpe, Sharpe lo, pooled
  expectancy lo, MaxDD, Calmar, ann return, ann vol, turnover}); the margin vs best single cell.

### Step 7 — Adaptability read: A vs B (D0 §D4)

- **Method:** report the **A−B difference** in Sharpe / MaxDD; overlay the circuit-breaker de-allocation
  timeline on the **fragile cells** (USTEC-1h, US2000-1h). Descriptive — **no pass/fail**.
- **Interpretation:** "B de-risks" is supported iff B's MaxDD (or trailing drawdown where a fragile cell
  deteriorates) is **materially lower** than A's **at comparable Sharpe**. If B reduces Sharpe with no MaxDD
  benefit, the breaker is reported as **not helpful on this analysis set** (honest negative).
- **Expected output:** the A−B table; the de-allocation overlay (plot 4).

### Step 8 — NEW gate statistic: synthetic-null FPR calibration + bite-check (D0 §D6, BINDING for G-022a)

The portfolio holdout confirmation rule (param #9: portfolio Sharpe / pooled-expectancy moving-block one-sided
lower bound > band) is **new** ⇒ it must be calibrated **before G-022a freezes it**.

- **Synthetic-null FPR calibration.** Generate matched **no-edge** nulls by **block-permuting / sign-flipping
  the per-cell return streams to zero expectancy while preserving the empirical cross-cell covariance and
  within-cell autocorrelation** — the `null_b_block_permute_returns` / EXP-001/027/044 form, **NOT a price-path
  rotation** (rotation blows up cross-regime variance under a mean statistic — recorded lesson). Run the **full
  portfolio construction (A and B) + the confirmation rule** on each null replicate at the **realized
  holdout-equivalent sample size and block structure**; require **FPR ≤ 0.05** for **both** A and B.
  `N_NULL ≥ 1000` replicates (Wilson upper bound on the FPR reported). Seeds fixed.
  - **Block-permutation construction:** resample/permute in blocks of the **same block length** as the metric
    (rebalance cadence) so autocorrelation up to ~b lags survives; flip signs / re-center each cell to
    **zero mean** (the no-edge condition) **without** distorting its variance or the cross-cell correlation
    (permute a common time index across cells to preserve the contemporaneous covariance).
- **Bite-check GREEN.** A **planted-edge vs no-edge two-sample** check at the **materiality scale**: inject a
  known small positive expectancy (at the band scale) into the null streams and confirm the rule (i) **fires**
  on the planted-edge series (detects a real portfolio edge at the holdout sample size) and (ii) **does NOT
  fire** on the zero-edge null. The planted target is a **generic materiality-scale edge**, **NOT** built
  around any signal-derived/realized value (the `falsification_null_design` lesson — a null/target built around
  the observed edge biases toward confirmation). Two-sample separation checked **per the √2 two-sample scale**,
  reported as the bite margin.
- **Gate semantics:** FPR ≤ 0.05 **AND** bite-check GREEN for **both** A and B ⇒ statistic is **READY** for
  G-022a to freeze. **Fail either ⇒ REVISE** (the holdout cannot be gated on an uncalibrated/biting statistic)
  — this is a Stage-readiness gate, not a holdout verdict.
- **Expected output:** `null_fpr_calibration.json` (FPR + Wilson-hi for A and B), `bite_check.json` (planted
  vs null fire rates, bite margin), and the null-distribution plot (plot 5).

### Step 9 — Determinism, causality assertions, real-price discipline (D0 §D8)

- **Determinism:** a full **second pass** (ERC convex solve, bootstrap streams, null replicates, any intrabar
  reuse) is **byte-identical** — assert on `portfolio_returns_A/B`, `portfolio_metrics`, and the calibration
  JSONs.
- **Causal-weight unit assertion (binding).** A unit test asserts **no future per-cell return enters any
  weight, covariance, vol estimate, concurrent-risk cap, or circuit-breaker state at its timestamp** — e.g.
  perturb a cell's returns strictly **after** rebalance *r* and assert the weight vector at *r* is unchanged.
- **Real-price only:** all P&L / drawdown on real domain & 1-minute OHLC; no HA/brick prices in any metric.
- **Read-accounting assertion:** `run_metadata.json` asserts `counted_test_reads=0`, `candidate_slots=0`,
  `holdout_untouched=true`; no stratum tally moves.

---

## Visualisations (≤ 5; budget = 5)

1. **Equity curves** — Portfolio A, Portfolio B, best individual cell, naive inverse-vol (cumulative net P&L
   over the analysis set). *Shows the diversification benefit and the A/B path divergence.*
2. **Weight + correlation heatmap** — ERC weight path (cells × rebalances) alongside the trailing
   correlation matrix. *Shows ERC down-weighting the JPY cluster vs naive IV.*
3. **A−B drawdown comparison** — underwater (drawdown) curves for A and B. *Shows whether the breaker reduces
   drawdown.*
4. **Circuit-breaker de-allocation timeline** — on the fragile cells (USTEC-1h, US2000-1h): trailing-50 mean
   and on/off allocation intervals. *Shows whether B de-risks a deteriorating cell A holds.*
5. **Synthetic-null FPR / bite-check distribution** — null lower-bound distribution vs the band, with the
   planted-edge overlay, for A and B. *Shows calibration (FPR ≤ 0.05) and bite separation.*

---

## Interpretation Guide (pre-registered; mirrors scope §7 — descriptive, no holdout verdict)

- **Portfolio benefit (main read):** *supported* if **at least one of A / B** has an annualized-Sharpe
  **lower bound** that **exceeds the best individual deployable cell's annualized-Sharpe point estimate by a
  material margin** (margin reported; sets the G-022a band). Reported per portfolio with the full
  Sharpe/MaxDD/Calmar table and per-cell baselines.
- **Adaptability (A vs B):** *"B de-risks" supported* iff B's MaxDD (or fragile-cell trailing drawdown) is
  **materially lower** than A's where a fragile cell deteriorates, **at comparable Sharpe**. Descriptive — no
  pass/fail. If B costs Sharpe with no MaxDD gain → reported as breaker-not-helpful on this set.
- **Statistic readiness (gate for G-022a):** *READY* iff the confirmation rule is **calibrated (synthetic-null
  FPR ≤ 0.05)** **and** **bite-checked GREEN** for **both** A and B. *A rule that fails FPR control or bites
  on the null ⇒ **REVISE*** (holdout cannot be gated on it).
- **Inconclusive:** the analysis-set portfolio lower bound **spans zero / is power-limited** at the realized
  series length — disclosed; routes a likely **G-022a HALT** (holdout preserved), not a spent shot.
- **Integrity (required regardless):** determinism byte-identical second pass; causal-weight unit assertion
  passes; real-price metrics only; `holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`;
  provenance reconciliation PASS (Step 1); no stratum tally moves.

---

## Metric denominators / zero-baseline (scope §8; defined before implementation)

- **Per-cell return stream:** resolved EXIT-RCT **net per-event return (ATR units)**, timestamped at event
  exit `CloseTime`; denominator = resolved events (identical `keep` mask to EXP-092/093; reconciled in Step 1).
- **Portfolio return series:** net P&L aggregated by timestamp on the **1h common grid** (4h marked-to-market
  at each 1h close), scaled to the 10% vol target. **Annualization factor** fixed by the grid (1h bars/year on
  the instrument's active calendar; recorded in `run_metadata.json`). Sharpe denominator = the portfolio
  return-series standard deviation over the analysis window (causal where used in weights; full-window for the
  reported descriptive Sharpe).
- **No zero-baseline ratio.** The binding figure is the portfolio metric's **absolute lower bound vs 0** (edge
  present) and **vs the best-single-cell point estimate** (diversification benefit). No
  percentage-improvement-over-zero metric. A portfolio window with `< 2` resolved trades on the trailing grid
  is `INDETERMINATE` (0 weight, recorded), never forced to a number.
- **Co-reported (non-binding):** MaxDD, Calmar, annualized return/vol, turnover, per-cell Sharpe, weight /
  correlation heatmap, circuit-breaker de-allocation timeline, naive inverse-vol contrast.

---

## Implementation safety constraints (for experiment-developer)

- **Timestamp ordering:** sort by `CloseTime`; slice the analysis set by **row index on the sorted frame**
  (D0 §D1); align cells across domains by **`CloseTime` epoch**, never bar index. Clip all 1-minute fill walks
  at the active slice's right edge (no holdout minute is touched).
- **Holdout fence:** never `scan`/`read` rows at or beyond `int(total_rows·0.7)`; assert the max touched
  `CloseTime` < the analysis edge in `run_metadata.json`.
- **Causality:** every estimator (covariance, vol, ERC solve, risk anchor, concurrent-risk cap, breaker) at
  rebalance/curve timestamp *t* consumes only per-cell returns with exit `CloseTime` **strictly < t**. Encode
  as a hard invariant + the Step-9 unit test.
- **Determinism:** no unseeded RNG; ERC convex iteration uses fixed init/tolerance/max-iters; all bootstrap /
  null RNG via `seed_for` off master `20260624`. Second pass byte-identical.
- **Bounded iteration / progress:** `tqdm` on the outer loops (cells × rebalances; null replicates ≥ 1000).
  Keep the bootstrap memory-batched (`BOOT_BATCH`); keep null construction vectorized **without** breaking the
  block structure (block permutation must preserve serial order within blocks and the common time index across
  cells — do **not** vectorize in a way that shuffles across the causal grid).
- **Substrate reuse:** import the EXP-090 module and EXP-092/`D0-amendment-003` cost overlay **unchanged**
  (no mutation of `xen.capgeo_cost.COST_CONSTANTS`); do **not** re-resolve exits beyond the deterministic
  regeneration; assert the provenance gate (Step 1) before any portfolio math.
- **New module:** `xen.portfolio` — causal ERC weights from a trailing Ledoit-Wolf covariance, vol-target
  scaling, concurrent-risk cap, circuit-breaker overlay, timestamp-aligned multi-domain equity-curve
  aggregation. Pure-computation functions return data; orchestration/`main()` does I/O and plotting; no
  import-time side effects. Reuse `xen.ass` (moving-block bootstrap) and standard numerical libs
  (covariance / Ledoit-Wolf / ERC solve) — do not hand-roll what a vetted routine provides, but keep the ERC
  solve explicit and deterministic.
- **INDETERMINATE / zero-baseline:** finite handling for windows with `< 2` resolved trades (0 weight,
  recorded); never divide by a zero denominator (guard Sharpe/Calmar when vol or MaxDD = 0 → report `NaN` with
  a flag, not `inf`).

---

## Notes for Stage 4 governance (consolidated; not run here)

1. **Read accounting.** EXP-095 reads TRAIN + **re-resolves the analysis-TEST stratum** through the identical
   frozen substrate to rebuild the per-cell streams (the streams were not persisted). This reproduces an
   **already-spent** per-stratum read with **no new per-stratum selection or inference** (the binding reads
   were spent at EXP-093) → **portfolio-aggregate disclosure, 0 counted reads** (D0 §D7; EXP-085
   cost-re-resolution precedent). The 11 carried strata stay **1/2**; 37 stay 0/2. Confirm at Stage 4.
2. **Holdout.** No global-holdout bar (incl. 1-minute) is loaded. Assert `holdout_untouched=true`.
3. **New binding statistic.** The portfolio confirmation rule's calibration + bite-check (Step 8) is the D6
   precondition for G-022a; verify the null is the `null_b_block_permute_returns` form and **not** built
   around a signal-derived target (`falsification_null_design`).
4. **No optimization.** All params at D0 frozen values; brackets {60/120 cov, daily/monthly rebalance, 7/15%
   anchor, 1.0/2.0× cap, 30/100 breaker window, halve-not-zero} are **disclosure only** — never used to select
   a binding value.

---

## Complexity Check

- **Statistical tests:** 1 binding (portfolio risk-adjusted lower bound vs best single cell) + the
  confirmation-statistic calibration (synthetic-null FPR + bite-check) / **budget 1 + calibration** ✓
- **Visualisations:** 5 / **budget 5** ✓
- **New modules:** 1 (`xen.portfolio`) / **budget 1** ✓
