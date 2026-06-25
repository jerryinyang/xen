# Analysis Plan: Experiment EXP-097

**Title:** Global-Holdout Release — One-Shot OOS-Final Confirmation of the RSI-2 Fade Deployment Portfolio
**Family / HYP:** `CF-MR-001` / `HYP-003` · **Phase:** 022 (batch 3) · **Date:** 2026-06-25
**Scope:** [`scope.md`](scope.md) · **G-022a freeze:** [`G-022a-gate-criteria.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/G-022a-gate-criteria.md)
· **terminal rubric:** [`G-022-gate-criteria.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/G-022-gate-criteria.md)
· **D0:** [`D0-predeclarations.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/D0-predeclarations.md)
§D1/§D4/§D7/§D9 · amendment [`D0-amendment-001.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/D0-amendment-001.md).
**Reads / slots:** **1 global-holdout shot** (one holdout-governance event, à la EXP-032) · **0 counted
analysis-TEST reads** (11 carried strata stay 1/2) · **0 candidate slots** · non-repeatable / non-upgradable.

> **This plan operationalizes the G-022a-frozen rule. It introduces no new design choice** — the deployable set
> (carry-8), construction (binding-v2 ERC + intra-1h MTM), primary (B), bands (A 1.75 / B 2.00), and confirmation
> rule are all frozen. The only new act is **loading the final-30% global holdout once** and applying the frozen
> statistic to the **holdout-region** portfolio series.

---

## Objective

Spend the single sanctioned global-holdout shot to adjudicate the binding deployment verdict (G-022):
**deployed as the G-022a-frozen, noise-aware (binding v2 entry fill) causal ERC portfolio with intra-1h
mark-to-market, does the primary Portfolio B confirm a positive risk-adjusted edge on the fully-fresh final-30%
global holdout** — `Sharpe_LB(B) > 2.00 AND Calmar_LB(B) > 0`? Portfolio A is co-adjudicated and disclosed on the
**same single materialization** (operator decision 2026-06-25, one read), but cannot rescue the family verdict via
an OR. The read is descriptive of nothing beyond the deployment claim; the verdict is mechanical and pre-frozen.

---

## Data inputs & provenance

### The slice + the causal-warmup discipline (the crux)

The binding slice is the **final-30% global holdout per file**, `holdout = [int(total_rows·0.7), total_rows)`,
**loaded for the first time** (the sanctioned shot). The **analysis set** `[0, int(total_rows·0.7))` is loaded as
**strictly past-only causal warmup** — it supplies (a) indicator warmup (ATR/RSI/EMA), (b) the trailing-90-day
covariance/vol the ERC weights need, (c) the trailing-50-trade circuit-breaker mean, and (d) the per-cell return
history the weights consume at the holdout's left edge. This is the **EXP-093 pattern** (TRAIN loaded as causal
warmup; binding inference on the held-back stratum only). Re-loading the analysis set is **not** a new holdout
read — it is already-spent data used past-only.

**Holdout-region boundary `H` (binding-metric region).** Each file has its own analysis cutoff
`H_cell = CloseTime[int(total_rows_cell·0.7)]` (EXP-096 metadata: the 8 cutoffs cluster ~2024-12-11…-13). Define
the **single global boundary `H = max over the 8 cells of H_cell`**. The **binding portfolio metric is computed on
the holdout-region series = grid steps with epoch ≥ H** — so that **every** per-cell return contributing to the
binding metric is a holdout event (at `u ≥ H` every cell is past its own cutoff). The ~2-day transition zone
`[min H_cell, H)` is **excluded** from the binding metric (conservative — it never lets an analysis-set return
into the holdout statistic). `H` and the per-file cutoffs are recorded; `n_holdout_weeks` ≈ 78 (matches the
m\*-calibration holdout-equivalent n ≈ 79).

### Construction reused verbatim (no re-derivation)

The per-cell stream, grid, ERC build, MTM, and the binding statistic are the **EXP-095/096 frozen machinery**,
imported and reused unchanged so the holdout read is computed by the *identical* function that produced the
analysis-set LBs and the m\* calibration:

- **EXP-096 module** (`E96`) → `resolve_cell_noise` (the binding-**v2** per-cell stream: exit path + keep mask
  reused verbatim from the frozen substrate; `entry_fill = v2`; `net = dir·(exit_fill − entry_fill)/atr − cost`).
- **EXP-095 module** (via `E96.E95`) → `build_grid`, `mtm_marks` (intra-1h MTM, amendment-001 A1),
  `series_risk_metrics` (the **binding Sharpe/Calmar MBB lower-bound machinery** — weekly-aggregated, block =
  `default_block_length(n_weeks)`, N_BOOT=10_000, α=0.10), `causal_weight_assertion`, `determinism_replay`.
- **`xen.portfolio`** (`pf`) → `build_portfolio` (ERC/LW-90d/weekly/10%-vol/1.5×-cap/breaker), `aggregate_to_cadence`,
  `naive_inverse_vol` (disclosed contrast only); **`xen.ass`** → `moving_block_bootstrap_cis`,
  `default_block_length`; the EXP-090 substrate (`E96.E90`) + `xen.capgeo_cost` cost overlay (`F=0`), unchanged.

The **only new code** is a **full-file loader** (`load_full_1m`: lazy scan → sort `CloseTime` → slice
`[0, total_rows)` → collect; records `H_cell`) and the **holdout-region metric extraction** in orchestration. No
new module; no re-fit; no re-tune.

### Slices & exclusions

- **Loaded:** the full file `[0, total_rows)` per cell (analysis warmup + the holdout shot). `train_edge_epoch`
  for the substrate = the file's last 1-minute close (so entry-fill + exit walks resolve through the holdout).
- **Binding metric region:** grid steps with epoch `≥ H` (holdout-only, all cells).
- **No further reserve:** nothing beyond each file's end is read; the holdout is the end of the file.

---

## Methodology

### Step 1 — Load full files + build per-cell binding-v2 streams (warmup + holdout)

- **Method:** for each of the 8 cells, `load_full_1m` → `E96.E90.build_cell_context(full_1m, instrument, domain)`
  → `E96.resolve_cell_noise(ctx, …)`; take the **v2** stream (binding entry fill). Record `H_cell`. Compute
  `H = max H_cell`.
- **Why:** identical substrate + entry-fill machinery as EXP-096, now over the full file so holdout events resolve
  causally; the v2 stream is the frozen deployment construction.
- **Causality / fence:** the v2 entry fill consults only 1-minute bars at/after each signal close (clipped at the
  file end); exits resolve forward only. No future bar enters any fill.
- **Expected output:** 8 per-cell v2 streams `(entry_epoch, exit_epoch, net, mark_epoch, mark_return)` spanning
  warmup+holdout; `holdout_boundary.json` (`H`, per-cell `H_cell`, `n_holdout_weeks`, per-file row counts).

### Step 2 — Build the causal ERC portfolios A and B over the full grid (weights past-only)

- **Method:** `E95.build_grid(v2_streams)` → `grid_start, n_steps, pnl_mat (MTM increments), trade_mat (per-trade)`;
  `pf.build_portfolio(..., use_breaker=False)` → **A**, `pf.build_portfolio(..., use_breaker=True)` → **B**, with
  the frozen D0 params (LW-90d covariance, weekly rebalance, 10%-vol anchor, 1.5× cap, trailing-50 breaker,
  intra-1h MTM). Weights at every grid timestamp use only per-cell returns resolved **strictly before** it
  (the EXP-095/096 causal invariant).
- **Why:** the portfolio is one continuous causal curve from warmup through the holdout; the binding metric (Step 3)
  is restricted to the holdout region. Building continuously (not "restarting" at H) is what makes the holdout
  weights properly warmed-up and causal (the analysis tail is the weights' history).
- **Warmup sufficiency:** the first holdout rebalance has the entire analysis tail (≫ 90 trading days) available →
  no cold-start; cells with < min trailing sample at a rebalance carry 0 weight (recorded), per EXP-095.
- **Expected output:** `res_A`, `res_B` (returns, weights, rebalance_idx); `portfolio_returns_A/B.csv` (full grid,
  with a `in_holdout` flag column for `epoch ≥ H`).

### Step 3 — BINDING read: holdout-region Sharpe LB + co-binding Calmar LB (frozen statistic)

- **Method (binding statistic):** restrict to the **holdout region** `holdout_mask = grid_epochs ≥ H`; for
  P ∈ {A, B} compute `E95.series_risk_metrics(res_P.returns[holdout_mask], rng_P, n_boot=10_000)` — the **same
  frozen function** that produced the analysis-set LBs and the m\* calibration (weekly-aggregated annualized
  **Sharpe** + **Calmar** moving-block one-sided lower bounds, block = `default_block_length(n_holdout_weeks)`,
  α = 0.10, seeded off master `20260624`). Co-reported from the same call: MaxDD, CVaR₅, Ulcer, ann return/vol,
  turnover.
- **Frozen confirmation rule (no re-definition):**
  ```
  CONFIRM(P)  iff  Sharpe_LB(P) > band_P  AND  Calmar_LB(P) > 0      band_A = 1.75 , band_B = 2.00
  ```
- **Why this statistic:** the methods-catalog flags raw Sharpe (normality/upside penalty); honored without the
  pitfall by the **non-parametric moving-block** LB (no normality; serial dependence preserved) + the **co-binding
  Calmar** downside leg — identical to EXP-095/096. Using the *same function* guarantees the holdout statistic is
  the one the band (= m\*) was calibrated against; no statistic is re-implemented or re-tuned.
- **Disclosed contrast (non-binding):** naive-inverse-vol holdout Sharpe LB (`pf.naive_inverse_vol` on the holdout
  region) — to read ERC-vs-naive on the holdout, as EXP-095/096; never binding.
- **Expected output:** `holdout_metrics.json` / `holdout_metrics.csv` (A, B, naive-IV × {ann Sharpe, Sharpe lo,
  Calmar, Calmar lo, MaxDD, CVaR5, Ulcer, ann ret/vol, turnover, n_holdout_weeks}); `confirm_A`, `confirm_B`.

### Step 4 — Terminal G-022 adjudication (mechanical, keyed off primary B)

- **Method (frozen rubric — `G-022-gate-criteria.md` §2):**
  ```
  DEPLOYABLE_CONFIRMED  iff CONFIRM(B)
  DECAYED/NOT_CONFIRMED iff Sharpe_pt(B) <= band_B  OR  Sharpe_LB(B) <= 0
  INCONCLUSIVE          iff not CONFIRM(B) and not DECAYED   (Sharpe_pt(B) > band_B but Sharpe_LB(B) <= band_B,
                                                              or Calmar_LB(B) <= 0 while Sharpe holds)
  ```
  Portfolio A's CONFIRM status is recorded and **disclosed**; an A-confirm with a B-fail does **not** promote the
  family verdict (no OR).
- **Expected output:** `verdict.json` (`g022_state`, `confirm_B`, `confirm_A`, the Sharpe/Calmar LB + point + band
  per portfolio, the rule trace).

### Step 5 — Per-cell holdout disclosure + masking check (LESSON-001, non-binding)

- **Method:** for each of the 8 cells, the holdout net per-event stream = events with `exit_epoch ≥ H`; compute
  net mean, median, and one-sided 95% MBB lower bound (`moving_block_bootstrap_cis`, N_BOOT=10_000, α=0.10 — the
  EXP-096 `_per_event_expectancy` machinery). **Masking check:** is the binding portfolio verdict broad-based or
  driven by one cell; is any cell **net-negative** on the holdout; does the portfolio LB exceed the per-cell LBs
  (diversification) — exactly the EXP-096 forensic, now on holdout data.
- **Why:** the binding estimand is the primary-B portfolio, but no cell result may be hidden inside the aggregate;
  this surfaces heterogeneity (e.g. whether the flagged EURJPY-4h or any cell broke OOS-final).
- **Expected output:** `per_cell_holdout.csv` (per cell: n_holdout_events, net_mean, net_median, net_ci_low_1s,
  net_negative flag).

### Step 6 — Shrinkage companion (descriptive, against the honest prior)

- **Method:** report the **analysis→holdout shrinkage**: holdout Sharpe LB vs the EXP-096 **v2 analysis-set** LB
  (A 5.147 / B 4.897); per-cell holdout net mean/median/ci_low vs the EXP-096 v2 analysis per-cell values (read
  from `EXP-096/results/per_cell_degradation.csv`, the `v2_*` columns). Frame against the programme prior (G-021
  uniform TRAIN→TEST shrinkage Δ net_ci_low −0.005…−0.107; EXP-096 v2 ≈ halving of the noise-free LB).
- **Why:** makes the holdout read interpretable — distinguishes "decayed within the expected shrinkage band" from
  "collapsed" — without moving any goalpost (the band is fixed at m\*; this is context, not a criterion).
- **Expected output:** `shrinkage.json` (portfolio + per-cell analysis-v2 → holdout deltas).

### Step 7 — Integrity, causality, one-read discipline

- **Determinism:** a full **second pass** (entry-fill walk + ERC solve + MTM + the holdout-region bootstrap) is
  **byte-identical** for A and B — `E95.determinism_replay` on the full build + a re-call of `series_risk_metrics`
  on the holdout slice (identical RNG seed → identical LB).
- **MTM conservation (binding):** the global per-position invariant Σ(all marks) = realized net per cell (≤1e-9
  ATR), per EXP-096 (the holdout-region metric slices this mark series; the invariant itself is global).
- **Causal-weight assertion (binding):** perturb a cell's per-cell returns strictly **after** a **holdout**
  rebalance `r`; assert the weight vector at `r` is unchanged (`E95.causal_weight_assertion`, exercised at a
  holdout `r`).
- **Causal-fill assertion (binding):** perturb a 1-minute bar strictly **before** a holdout signal close; assert
  that event's entry fill is unchanged (the EXP-096 `causal_entry_fill_assertion`, exercised on a holdout event).
- **One-read / holdout discipline:** `run_metadata.json` records `global_holdout_shot_spent=true`,
  `holdout_first_touch=EXP-097`, `counted_test_reads=0` (analysis-TEST ledger untouched, 11 carried strata stay
  1/2), `candidate_slots=0`, `n_holdout_rows_read` per file, `H`, `n_holdout_weeks`. The holdout-governance event
  is recorded in `test-read-ledger.md` + `multiplicity-registry.md` **in the same change** as the result.
- **Real-price only:** all P&L on real domain & 1-minute OHLC; entry/exit fills real touched prices; no HA/Renko.

---

## Visualisations (≤ 5; budget = 5)

1. **Holdout equity curves** — Portfolio A, B, naive-IV (and the 8 per-cell contributions), cumulative net over the
   holdout region. *Shows the realized OOS-final deployment path.*
2. **Holdout Sharpe / Calmar LB vs band** — A and B holdout Sharpe LB and Calmar LB as bars with the **band lines**
   (Sharpe band_A 1.75 / band_B 2.00; Calmar 0) and the EXP-096 v2 analysis-set LB markers. *Shows CONFIRM/DECAYED
   at a glance and the shrinkage.*
3. **Per-cell holdout net (mean/median/ci_low) vs analysis-v2** — per cell, holdout vs EXP-096 v2 analysis values,
   net-negative cells highlighted. *Shows the per-cell masking/shrinkage; whether any cell broke OOS-final.*
4. **A/B holdout drawdown (underwater)** — A and B drawdown curves on the holdout region. *Shows the realized
   downside and whether the circuit-breaker engaged.*
5. **Circuit-breaker de-allocation timeline (holdout)** — Portfolio B de-allocation intervals on the fragile 1h
   cells over the holdout. *Shows whether B's tail-insurance mechanism fired OOS-final.*

---

## Interpretation Guide (pre-registered — mirrors the FROZEN G-022 rubric exactly; no goalpost movement)

| Outcome | Condition (binding, primary = Portfolio B) | Programme consequence |
|---|---|---|
| **DEPLOYABLE_CONFIRMED** | `Sharpe_LB(B) > 2.00 AND Calmar_LB(B) > 0` | The bare RSI-2 fade is the programme's **first deployment-grade price strategy**; the frozen spec (carry-8, ERC + breaker B, v2 fill, cost) is the production deployment. A's confirm status disclosed. Deferred levers become expansion candidates (each own slot/D0). |
| **DECAYED / NOT_CONFIRMED** | `Sharpe_pt(B) ≤ 2.00` **OR** `Sharpe_LB(B) ≤ 0` | The analysis-TEST edge did not survive OOS-final as a deployable portfolio. Recorded permanently; deployment claim unsupported OOS-final; the G-021 TRADABLE verdict + per-cell file drawer stand. |
| **INCONCLUSIVE** | not CONFIRM and not DECAYED (point clears band but LB ≤ band, or Calmar leg fails while Sharpe holds) | Disclosed; neither confirmed nor refuted as a deployment; the shot is spent (one-shot, non-upgradable, EXP-032 precedent). |

- **Per-cell disclosure (non-binding):** report every cell's holdout outcome + the masking check; the binding
  estimand is the primary-B portfolio. A net-negative cell or a one-cell-driven aggregate is **disclosed**, not a
  re-adjudication.
- **A co-reported (non-binding):** A's CONFIRM status is reported; it never rescues a B-fail (no OR).
- **Shrinkage is context, not a criterion:** the analysis-v2 → holdout deltas are reported to situate the read
  against the honest prior; the band stays fixed at m\*.
- **Integrity (required regardless):** determinism byte-identical; MTM conservation ≤1e-9; causal-weight +
  causal-fill assertions PASS; real-price only; the single holdout shot recorded; `counted_test_reads=0`,
  `candidate_slots=0`. Any integrity failure → **REVISE** (fix before the verdict stands) — but note the
  **holdout-read-once** rule: a confound found *after* the read is a permanent caveat, not a re-read.

---

## Metric denominators / zero-baseline (frozen; defined before the read)

- **Per-cell return stream:** binding-v2 EXIT-RCT net per-event return (ATR units), timestamped at the event exit
  `CloseTime`; holdout denominator = resolved events with `exit_epoch ≥ H` (the v2 keep mask; noise perturbs the
  entry price, not the population).
- **Binding portfolio series:** net P&L on the 1h grid (4h marked-to-market each 1h close), 10%-vol-scaled,
  **restricted to `epoch ≥ H`** for the binding metric. Annualization factor fixed by the grid (recorded);
  weekly-aggregation block = `default_block_length(n_holdout_weeks)`; Sharpe/Calmar denominators are the
  holdout-region series statistics.
- **No zero-baseline ratio.** The binding figure is the absolute lower bound vs the predeclared band
  (`Sharpe_LB(B)` vs 2.00; `Calmar_LB(B)` vs 0). A holdout trailing window with < 2 resolved trades is
  `INDETERMINATE` (0 weight, recorded). Guard Sharpe/Calmar against zero vol / zero MaxDD → `NaN` + flag, never
  `inf`.
- **Co-reported (non-binding):** MaxDD, CVaR5, Ulcer, ann ret/vol, turnover, per-cell holdout net, A's status,
  naive-IV contrast, the shrinkage deltas, the holdout equity/drawdown/breaker curves.

---

## Implementation safety constraints (for experiment-developer)

- **Holdout-once:** load the full file `[0, total_rows)`; this is the **only** experiment permitted to read the
  final-30%. Assert no prior stage touched it; record the shot in `run_metadata.json` + the ledger (same change).
  Do **not** add any second holdout pass.
- **Reuse, don't re-derive:** import the EXP-096 module; reuse `resolve_cell_noise` (v2), `E95.build_grid`,
  `E95.series_risk_metrics`, `E95.mtm_marks`, `pf.build_portfolio`, `pf.naive_inverse_vol`, the substrate + cost
  overlay **verbatim**. The frozen statistic = `E95.series_risk_metrics` (do not re-implement the LB). No new
  module; the only new code is `load_full_1m` + the `epoch ≥ H` holdout-region slicing in orchestration.
- **Boundary `H`:** `H = max over cells of CloseTime[int(total_rows·0.7)]`; binding metric on `grid_epochs ≥ H`;
  per-cell holdout events `exit_epoch ≥ H`. Record `H`, per-file cutoffs, `n_holdout_weeks`.
- **Causality:** weights/cov/vol/cap/breaker at grid timestamp `u` consume only returns with exit `CloseTime < u`
  (continuous build over warmup+holdout); entry fill uses only 1m bars at/after the signal close; alignment by
  `CloseTime` epoch, never bar index; the assertions (Step 7) exercised at a **holdout** rebalance/event.
- **Determinism:** seeds off master `20260624`; `series_risk_metrics` RNG seeded per portfolio; second pass
  byte-identical.
- **Bounded / progress:** `tqdm` over the 8 cells; bootstrap memory-batched; no row loops over the large 1m frames
  (searchsorted + vectorized per EXP-096). Full-file loads are larger than EXP-096 (they include the holdout) —
  keep lazy scan → sort → collect; column-project where practical.
- **NaN / zero-baseline:** guard Sharpe/Calmar against zero vol / zero MaxDD (`NaN` + flag, never `inf`);
  INDETERMINATE marks carry 0 weight.

---

## Notes for Stage 4 governance (consolidated; not run here)

1. **The shot.** EXP-097 is the single sanctioned global-holdout release — verify `global_holdout_shot_spent=true`,
   `holdout_first_touch=EXP-097`, the holdout-governance event recorded in `test-read-ledger.md` +
   `multiplicity-registry.md` in the same change; `counted_test_reads=0` (analysis-TEST ledger untouched, 11
   carried strata stay 1/2); `candidate_slots=0`; non-repeatable.
2. **Frozen-rule fidelity.** Confirm the deployable set (carry-8), construction (binding-v2 ERC + MTM), primary
   (B), bands (A 1.75 / B 2.00), and the confirmation rule are exactly G-022a's — nothing re-derived/re-tuned; the
   binding statistic is `E95.series_risk_metrics` verbatim (the m\*-calibrated function). No goalpost-moving.
3. **Holdout-region honesty.** Confirm the binding metric uses `epoch ≥ H` only (no analysis-set return enters the
   holdout statistic); warmup is past-only.
4. **Per-stratum doctrine.** Per-cell holdout outcomes disclosed alongside the primary-B portfolio; A co-reported,
   no OR rescue.

---

## Complexity Check

- **Statistical tests:** 1 binding (primary-B holdout Sharpe LB + co-binding Calmar LB vs the frozen band) +
  descriptive companions (A disclosed; per-cell; shrinkage; naive-IV contrast). / **budget 1** ✓
- **Visualisations:** 5 / **budget 5** ✓
- **New modules:** 0 (`load_full_1m` + holdout-region slicing in orchestration; all statistics/construction reused
  verbatim). / **budget 0** ✓
