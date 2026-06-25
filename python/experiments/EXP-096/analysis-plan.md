# Analysis Plan: Experiment EXP-096

**Title:** Noise Infusion — Realistic 1-Minute Entry Fill (RSI-2 Fade Portfolio, 8 confirmed cells)
**Family / HYP:** `CF-MR-001` / `HYP-003` · **Phase:** 022 (batch 3) · **Date:** 2026-06-25
**Scope:** [`scope.md`](scope.md) · **Design:** [`design.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/design.md)
· **D0:** [`D0-predeclarations.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/D0-predeclarations.md)
(§D1/§D5/§D7/§D9) · **Amendment:** [`D0-amendment-001.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/D0-amendment-001.md)
(A1 intra-1h MTM, A2/A3 benefit criterion, A4 bite-MDE — **inherited**).
**Reads / slots:** 0 counted TEST reads · 0 candidate slots · final-30% global holdout **NEVER loaded** (EXP-097 only).

---

## Objective

Re-resolving each of the **8 G-021-confirmed cells'** entries under a realistic 1-minute entry-fill model and
re-deriving the causal ERC portfolio (A static, B circuit-breaker) under the **binding variant 2** with intra-1h
mark-to-market, determine on the **analysis set** (TRAIN + the EXP-093 already-resolved analysis-TEST series,
reused as portfolio-aggregate disclosure):

1. **Noise survival (binding).** Does the EXP-095 in-sample diversification benefit — the portfolio Sharpe lower
   bound (with co-binding Calmar LB) exceeding the deployment-realistic cross-cell-median single-cell LB —
   **survive** the binding fill? How much does realistic execution degrade the portfolio edge?
2. **Per-cell degradation (disclosure).** How much does each cell's net per-event expectancy degrade under the
   fill ladder (v1/v2/v3), and which cells fall below their EXP-093 margin (flagged, **not** dropped — operator
   decision: portfolio-only membership; G-022a adjudicates the holdout-frozen set)?
3. **Adaptability under noise (descriptive).** Does realistic execution change the EXP-095 "circuit-breaker
   NEUTRAL" read — does B (vs A) measurably de-risk the fragile 1h cells under an adverse fill?
4. **Gate-statistic re-check (inherited).** Does the realized v2 portfolio Sharpe LB still clear the **inherited**
   EXP-095 MDE m* = 1.75 (A) / 2.00 (B)? (The A4 MDE-curve is **not** recomputed under noise — operator decision.)

This plan is **descriptive on the analysis set** — it issues **no holdout verdict**. The binding deployment read
is EXP-097, under the G-022a-frozen rule. No hyperparameter or noise variant is selected here; every value is
frozen at its D0 ratified-table value; the v1/v3 variants and the {60,120}-cov bracket are disclosure only.

---

## Data inputs & provenance

### The key structural fact (drives the whole method)

Under D0 §D5 **only the entry execution price changes**. The EXIT-RCT favourable target level (`P*_t = Close_t +
(AL_t − AG_t)`, built from the **signal-bar close + Wilder state**) and the adverse stop (`2.0×ATR(14)` + MR-tempo
cap) are **frozen** — they are the strategy's resting orders and do not move because the fill was worse.
Therefore, in `xen.intrabar_fill.resolve_exit_paths`, the inputs `fav_level`, `fav_close_fire`, `adv_level`,
`cap` are **unchanged**, so the resolved exit path is **identical**: `fill_price` (the **exit** fill), `kind`,
`exit_domain_idx`, `direction`, `atr_entry`, and the resolved-event (`keep`) mask are all **reused verbatim** from
the frozen substrate. **EXP-096 does NOT re-run the exit walk to perturb it.** It re-resolves the substrate
deterministically (to obtain those arrays, which are not persisted — EXP-095 precedent), then computes a **new
entry fill** per event and recomputes the net return:

```
net_return_atr(v) = direction · (exit_fill − entry_fill(v)) / atr_entry − cost      # exit_fill, atr, cost frozen
```

(`xen.intrabar_fill.net_return_atr` already accepts `fill_price=exit_fill` and an entry reference; EXP-096 passes
`entry_close = entry_fill(v)` in place of the signal-bar close.) The realized-event population (denominator) is
**unchanged** because the exit resolution is unchanged.

**Why the entry-fill window is never empty for a kept event (keep-mask invariance).** The exit walk for a
resolved event consumed ≥1 domain bar at `entry_idx+1` (off ≥ 1), whose constituent 1-minute bars lie strictly
after the signal-bar close. The entry fill is taken from the **first 1-minute bar after the signal-bar close** —
the same bars the exit walk already used — so every event that resolved an exit has ≥1 post-signal 1-minute bar
available for the entry fill. The plan asserts this (Step 6 integrity): `entry_fill` finite for **every** kept
event; cell event counts identical to EXP-093.

### Per-cell substrate regeneration (8 cells, D0 §D1 / param #1)

| # | Cell | Domain | G-021 tier | EXP-093 per-cell margin (flag threshold) |
|---|---|---|---|---|
| 1 | EURUSD-4h | 4h | robust core | 0.025 |
| 2 | XAUUSD-4h | 4h | robust core | 0.025 |
| 3 | USDCHF-4h | 4h | robust core | 0.025 |
| 4 | AUDJPY-4h | 4h | robust core | 0.025 |
| 5 | EURJPY-4h | 4h | robust core | 0.025 |
| 6 | GBPJPY-4h | 4h | robust core | 0.025 |
| 7 | USTEC-1h | 1h | mean-carried | 0.0125 |
| 8 | US2000-1h | 1h | mean-carried | 0.0125 |

*(Margins are the EXP-090/094-calibrated EXIT-RCT per-cell margins carried into EXP-092/093: 1h = 0.0125,
4h = 0.025 ATR. They are the **flag** thresholds for the per-cell degradation disclosure, not a drop rule.
The developer reads them from the EXP-092/093 artifacts; if a per-cell value differs from the domain default it
takes the artifact value.)*

- **Substrate import (unchanged):** the EXP-090 substrate path (`build_cell_context`, the EXIT-RCT arm builder,
  `xen.intrabar_fill.resolve_exit_paths` / `net_return_atr`) and the EXP-092/`D0-amendment-003` cost overlay
  (`xen.capgeo_cost`, hash `fa7c887…`, `F=0`, **never mutated**), with the same entry rule (RSI 2/10/90), exit
  (EXIT-RCT), adverse (2.0×ATR + MR-tempo cap), data slices, and master seed `20260624`.
- **Slices & exclusions:** analysis set per file `[0, int(total_rows·0.7))` = **TRAIN** `[0, int(int(total·0.7)·0.7))`
  + **analysis-TEST** `[int(int(total·0.7)·0.7), int(total·0.7))`. The portfolio curve and all weights are built
  **causally** across this window. The **final-30% global holdout is never loaded/sliced/materialized** (incl.
  1-minute bars); `train_edge_epoch` = the analysis edge; `holdout_untouched=true` asserted.

---

## Methodology

### Step 1 — Substrate regeneration + idealized provenance gate (binding)

- **Method:** deterministically re-resolve EXIT-RCT exits through the frozen EXP-090/092 substrate for the 8
  cells over the analysis set. Compute the **idealized** net per-event return with `entry_fill = entry_close`
  (the signal-bar close — the EXP-093/095 idealized at-close fill) and **zero slippage**, then reconcile the
  **analysis-TEST-stratum** per-cell summary (`net_mean`, `net_median`, `n_resolved`, `net_ci_low`) to EXP-093
  `test_per_cell.csv` for all 8 cells.
- **Why:** the per-trade streams are not persisted; faithful reuse = identical-code regeneration with a numeric
  reconciliation gate (EXP-095 Step 1 precedent). This verifies the substrate **before** any noise is applied, so
  any later degradation is attributable to the fill model, not to a regeneration drift.
- **Provenance gate (binding):** abs diff ≤ **1e-9 ATR** on means/medians, **exact** on integer counts, for all
  8 cells. A mismatch → **halt and route to governance/developer** (no silent proceed).
- **Expected output:** 8 per-cell arrays `(exit_CloseTime, exit_fill, direction, atr_entry, entry_close, keep)`;
  `provenance_reconciliation.csv` (8 rows: regenerated vs EXP-093, abs diff, PASS/FAIL).

### Step 2 — Entry-fill model: v1 / v2(binding) / v3 (D0 §D5; new `xen.intrabar_fill` entry-side rule)

- **Method:** add a causal **entry-side fill** function to `xen.intrabar_fill` (mirroring the exit-side touch
  logic). For each event, locate the **first 1-minute bar after the signal-bar close** by `searchsorted` on
  `minute_close_epoch` (side="right"), clipped at `train_edge_epoch`. Then:
  - **v1 (mild floor):** `entry_fill = minute_open[first]` (the open of that first post-signal 1-minute bar).
  - **v2 (BINDING):** `entry_fill = v1 + direction · 0.05 · atr_entry` (adverse: a long pays *more*, a short
    sells *lower* — both worsen the position).
  - **v3 (stress ceiling):** over the first `k=3` post-signal 1-minute bars (clipped to availability / the edge),
    the **most adverse touched price**: `max(minute_high[window])` for a long, `min(minute_low[window])` for a
    short (real touched prices; the worst plausible fill).
- **Causality / fence:** only 1-minute bars with `minute_close_epoch > signal_close_epoch` **and** `≤
  train_edge_epoch` are consulted; no future bar, no holdout minute. `searchsorted` gives the first index; the
  v3 worst-of-k is a **bounded** (≤3) reduction. `atr_entry` is the **same** ATR(14)-at-signal-bar used by the
  substrate (consistent normalization and slippage scale).
- **Why:** v2 models execution latency (you do not get the signal-bar close — you get the next 1-minute open) +
  a modest conservative adverse-selection tick; v1/v3 bracket it. The slippage is added to the **price**, so it
  is **not double-counted** with the flat round-trip cost (which models spread/commission).
- **Expected output:** per cell, per variant, `entry_fill(v)` aligned to the kept events; `entry_fill_audit.csv`
  (per cell: n_kept, n_fence_clipped [expect 0 for kept], mean v2−v1 slippage in ATR, mean v1−entry_close gap).

### Step 3 — Net per-event return streams under the ladder (D0 §D5)

- **Method:** for each cell × variant, `net(v) = direction·(exit_fill − entry_fill(v))/atr_entry − cost` via
  `net_return_atr` (exit_fill, atr, cost all frozen). Timestamp each net return at the event **exit `CloseTime`**
  (identical to EXP-095). The **binding** stream for the portfolio is **v2**; v1/v3 are the disclosed ladder.
- **Sanity (recorded, non-gating):** at v1 with the slippage set to 0 and `entry_fill = entry_close`, `net`
  reproduces the Step-1 idealized exactly (degenerate check that the entry-fill plumbing is a pure perturbation).
- **Expected output:** `cell_net_streams_{v1,v2,v3}.parquet` (per cell: exit_CloseTime, net, direction);
  `per_cell_expectancy_ladder.csv` (per cell × variant: net_mean, net_median, net_ci_low_1s, n).

### Step 4 — Portfolio re-derivation under the binding v2, A and B (D0 §D2/§D3; amendment-001 A1; `xen.portfolio`)

- **Method:** build the causal time-aligned portfolio on the **1h common grid** with **intra-1h
  mark-to-market** (amendment-001 A1), reusing `xen.portfolio` **verbatim** (EXP-095 construction):
  - **ERC weights** (`erc_weights`) from a **trailing 90-day Ledoit-Wolf covariance** (`ledoit_wolf_shrinkage`),
    **weekly** rebalance, held between (`build_portfolio` with the EXP-095 frozen settings).
  - **10% annualized-vol** anchor (`vol_anchor_scalar`; Sharpe-invariance asserted) + **1.5×** concurrent
    risk-aware cap (`concurrent_risk_scale`).
  - **Portfolio A** = static ERC (breaker multiplier ≡ 1); **Portfolio B** = ERC × circuit-breaker
    (`breaker_multipliers`, trailing-50-trade mean < 0 → 0, applied before the anchor). Both run in parallel.
  - **Intra-1h MTM (A1):** mark each open position's per-1h unrealized-P&L **increment**
    `direction·(price_u − price_{u-1})/atr` at each intervening 1h close, with the **first** increment measured
    from `entry_fill(v2)` (so the cost basis is the noise entry). Because the increments telescope, only the
    first increment shifts under noise and **Σ(marks) = net(v2) realized total per event** (incl. cost) by
    construction — the A1 conservation invariant against the **v2** realized net.
- **Why:** identical construction to EXP-095 keeps the noise read **comparable** (only the input streams changed,
  via the entry leg). MTM makes Sharpe/MaxDD economically comparable across 1h/4h (the amendment-001 lesson).
- **Causality:** every weight/covariance/vol/cap/breaker state at grid timestamp *u* uses only per-cell returns
  with exit `CloseTime` **strictly < u** (the EXP-095 invariant; re-asserted in Step 6).
- **Expected output:** `portfolio_returns_A.csv`, `portfolio_returns_B.csv` (1h-grid net return under v2, per-cell
  contribution columns); `weights_timeline.csv`; `circuit_breaker_timeline.csv`; `mtm_conservation.csv`.

### Step 5 — Binding read: noise survival of the risk-adjusted edge (amendment-001 A2/A3)

- **Method (binding statistic #1):** on the **v2** portfolio return series, compute **annualized Sharpe** with a
  **moving-block bootstrap one-sided lower bound** (`moving_block_sharpe_lower_bound`), **block = the rebalance
  cadence** (weekly, in 1h-grid steps), `N_BOOT = 10_000`, α = 0.10, seeded off master `20260624` — for **both A
  and B**. **Co-binding:** the **Calmar** moving-block one-sided lower bound (`moving_block_calmar_lower_bound`,
  same block/N_BOOT). **Co-reported (non-binding):** MaxDD, CVaR₅ (`cvar`), Ulcer (`ulcer_index`), annualized
  return/vol, turnover, pooled net per-trade expectancy LB.
- **Baseline (deployment-realistic, A2):** the **cross-cell median single-cell Sharpe lower bound** — compute
  each of the 8 cells' standalone v2 Sharpe LB on its own 1h-grid MTM return series (same machinery), take the
  **median across cells**. The co-binding analog is the **cross-cell median single-cell Calmar LB**.
  **Like-for-like (LB vs LB).**
- **Disclosed contrasts (non-binding):** the ex-post-**best** single cell's v2 Sharpe LB; the **naive
  inverse-vol** portfolio's v2 Sharpe LB (`naive_inverse_vol`); the **idealized EXP-095** A Sharpe LB (the
  noise-free reference, to quantify the noise gap).
- **Why:** this is the inherited amendment-001 A2/A3 binding read, re-run on the noise-realistic streams. The
  cross-cell-median baseline is the honest "pick one cell ex ante" counterfactual; the ex-post-best is
  selection-inflated and demoted to disclosure.
- **Sharpe-pitfall reconciliation (explicit):** D0 binds annualized Sharpe; the methods-catalog flags raw Sharpe
  (normality/upside penalty). Honored without the pitfall by (a) the **non-parametric moving-block** LB (no
  normality; serial dependence preserved) and (b) the **co-binding Calmar + CVaR/Ulcer** downside reads. The
  point Sharpe is the headline; its LB is the inferential object.
- **Expected output:** `benefit_v2.json` + `portfolio_metrics.csv` (A, B, cross-cell-median, best-cell, naive-IV,
  idealized-EXP-095 × {ann Sharpe, Sharpe lo, Calmar, Calmar lo, MaxDD, CVaR5, Ulcer, ann ret, ann vol,
  turnover}); the portfolio−baseline margins and the one-sided sampling band (point − LB).

### Step 6 — Noise sensitivity ladder (disclosed; binding statistic #2 = the ladder read)

- **Method:** re-run the Step-5 portfolio metric (A and B Sharpe LB + Calmar LB) under **v1** and **v3** (full
  portfolio re-derivation per variant — entry leg only changes), producing the **v1 → v2 → v3** ladder. Also
  report the **per-cell** net per-event expectancy ladder (Step 3: net_mean, net_median, net_ci_low_1s at α=0.05
  per cell × variant) — the **per-cell degradation disclosure**.
- **Disclosed nuisance bracket:** the v2 portfolio Sharpe LB under the covariance window {60, 90, 120} days
  (reuse `build_portfolio` brackets) — reported to size the nuisance spread for the within-noise band (Step 8).
  **Disclosure only — never used to select a binding value.**
- **Per-cell flag rule (disclosure, NOT a drop):** flag a cell `NOISE_DEGRADED` iff its **v2** net per-event
  expectancy `net_ci_low_1s` (α=0.05) falls **below** its EXP-093 margin (table above). Flagged cells are
  **retained** in the portfolio (operator decision: portfolio-only membership). G-022a adjudicates membership.
- **Expected output:** `noise_ladder.csv` (portfolio A/B Sharpe LB + Calmar LB × {v1,v2,v3}); `cov_bracket.csv`
  (v2 Sharpe LB × {60,90,120}); `per_cell_degradation.csv` (per cell × variant + flag).

### Step 7 — Adaptability under noise: A vs B (descriptive; D0 §D3)

- **Method:** report the **A−B difference** in Sharpe LB / MaxDD / Ulcer under **v2**; overlay the
  circuit-breaker de-allocation timeline on the **fragile cells** (USTEC-1h, US2000-1h). Compare against the
  EXP-095 noise-free "B neutral" read.
- **Interpretation (descriptive — no pass/fail):** "realistic execution makes B earn its keep" is supported iff B's
  MaxDD/Ulcer is **materially lower** than A's **at comparable Sharpe** under v2 (material = the difference
  exceeds the A/B sampling-band overlap). If B reduces Sharpe with no MaxDD/Ulcer benefit, or A≈B within noise →
  **breaker still neutral under noise** (the EXP-095 read persists). Informs the G-022a A-vs-B decision.
- **Expected output:** `adaptability_v2.json` (A−B Sharpe/MaxDD/Ulcer, fragile-cell de-allocation %); plots 4–5.

### Step 8 — Gate-statistic re-check (inherited m*; D0 §D6 / amendment-001 A4 — NOT recomputed)

- **Method:** **inherit** the EXP-095 MDE m* = **1.75 (A) / 2.00 (B)** and FPR-controlled readiness
  (`statistic_ready_for_g022a` was true at EXP-095). Re-report the **realized v2** portfolio Sharpe LB against
  m*: `edge_vs_mstar = v2_Sharpe_LB − m*` for A and B. The A4 MDE-curve is **not** recomputed under noise
  (operator decision 2026-06-25).
- **Optional (disclosure only):** a lightweight synthetic-null FPR sanity on the v2 series
  (`block_permute_zero_mean` zero-mean null, `wilson_upper` on the fire rate, ~N_NULL=1000) — reported as a
  disclosure that noise did not break FPR control; it does **not** re-gate readiness.
- **Routing:** if the realized v2 Sharpe LB **≥ m*** for at least one portfolio → the inherited statistic remains
  clearable under noise (hands G-022a a band ≥ m*). If noise pulls **both** below m* → **flag** for a G-022a
  band/scale reconsideration (not a silent pass; the holdout band must stay ≥ the gate's MDE).
- **Expected output:** `gate_recheck.json` (m* inherited, v2 Sharpe LB, edge_vs_mstar, clears/flag; optional v2
  null FPR + Wilson-hi, disclosure).

### Step 9 — Determinism, causality, real-price, read-accounting (D0 §D8)

- **Determinism:** a full **second pass** (entry-fill walk + ERC convex solve + MTM marks + bootstrap + any null
  replicate) is **byte-identical** on `portfolio_returns_A/B`, `portfolio_metrics`, `noise_ladder`,
  `gate_recheck`.
- **MTM conservation (binding):** for every position, Σ(intra-1h marks) = `net(v2)` realized total (incl. cost),
  abs diff ≤ **1e-9 ATR**, per cell. Recorded in `mtm_conservation.csv`.
- **Causal-fill / causal-weight assertions (binding):** (i) every `entry_fill(v)` uses only 1-minute bars with
  `minute_close_epoch ∈ (signal_close, train_edge]` — perturb a 1-minute bar **before** the signal close and
  assert `entry_fill` unchanged; (ii) no future per-cell return enters any weight — perturb a cell's returns
  strictly **after** rebalance *r* and assert the weight vector at *r* unchanged (EXP-095 test).
- **Keep-mask invariance (binding):** per-cell resolved-event counts under noise are **identical** to EXP-093
  (the noise perturbs the entry *price*, never the event population); assert equality and `entry_fill` finite for
  every kept event.
- **Real-price only:** all P&L / drawdown on real domain & 1-minute OHLC; entry and exit fills are real touched
  prices; no HA/brick prices.
- **Read accounting:** `run_metadata.json` asserts `counted_test_reads=0`, `candidate_slots=0`,
  `holdout_untouched=true`, max-touched `CloseTime` < analysis edge; no stratum tally moves.

---

## Visualisations (≤ 5; budget = 5)

1. **Noise sensitivity ladder** — Portfolio A & B annualized-Sharpe LB (and Calmar LB) under v1 / v2 / v3, with
   the cross-cell-median single-cell LB baseline and the inherited m* (1.75/2.00) as reference lines. *Shows
   whether the edge survives the binding fill and how the stress ceiling (v3) bites.*
2. **Equity curves under v2** — Portfolio A, B, best single cell, naive-IV, and the idealized EXP-095 A overlay
   (cumulative net P&L). *Shows the diversification benefit under noise and the noise gap vs idealized.*
3. **Per-cell net-expectancy degradation** — per cell, net_mean with MBB-LB whiskers for idealized → v1 → v2 →
   v3, each cell's EXP-093 margin line, flagged (`NOISE_DEGRADED`) cells highlighted. *Shows which cells realistic
   execution degrades and by how much.*
4. **Circuit-breaker de-allocation timeline (v2)** — the fragile cells (USTEC-1h, US2000-1h): trailing-50 mean and
   on/off allocation intervals under the adverse fill. *Shows whether B de-risks a deteriorating cell A holds.*
5. **A−B drawdown / Ulcer comparison (v2)** — underwater (drawdown) curves for A and B under noise. *Shows whether
   realistic execution makes the breaker materially de-risk, or the EXP-095 neutral read persists.*

---

## Interpretation Guide (pre-registered — descriptive, no holdout verdict)

| Read | SURVIVES / SUPPORTED | WITHIN-NOISE / INCONCLUSIVE | BREAKS / NOT SUPPORTED |
|---|---|---|---|
| **Noise survival (binding)** | ≥1 of A/B has v2 Sharpe LB > cross-cell-median single-cell Sharpe LB by a margin **exceeding the one-sided sampling band** (point − LB), **and** is not dominated on the co-binding Calmar LB | the margin is **inside** the sampling band or inside the disclosed cov-window {60,120} nuisance bracket → within-noise (routes a likely **G-022a HALT**, holdout preserved) | v2 portfolio Sharpe LB ≤ 0, or below the baseline by **more** than the sampling band → diversification erased by execution (**G-022a HALT**) |
| **Per-cell degradation (disclosure)** | — | cells flagged `NOISE_DEGRADED` are reported (retained, not dropped); G-022a decides membership | — |
| **Adaptability A vs B (descriptive)** | B's MaxDD/Ulcer materially lower than A at comparable Sharpe under v2 → breaker earns its keep under noise | A≈B within the sampling-band overlap → **breaker neutral under noise** (EXP-095 read persists) | B costs Sharpe with no MaxDD/Ulcer gain → breaker not helpful |
| **Gate re-check (inherited)** | ≥1 portfolio v2 Sharpe LB ≥ m* → inherited statistic clearable under noise (band ≥ m*) | — | both < m* → flag G-022a band/scale reconsideration |
| **Integrity (required regardless)** | determinism byte-identical; MTM conservation ≤1e-9; causal-fill + causal-weight + keep-mask assertions PASS; provenance gate PASS; real-price only; `holdout_untouched=true`, 0 reads / 0 slots; no tally moves | — | any failure → **REVISE** (fix + re-run before any number stands) |

**Honest prior (binding on interpretation):** a 0.05×ATR adverse tick + next-open latency removes a roughly
cost-scale fraction of each cell's ~0.28-ATR gross edge — a **larger relative bite on the cheaper-ATR 1h cells**
than the 4h core. The diversification benefit should be **more robust** than any single cell, but the binding
question is whether the portfolio Sharpe LB still clears the cross-cell-median baseline by more than its sampling
band. Magnitudes ~11–12 Sharpe are **in-sample favorable-selected** (EXP-095 caveat) — read the **survival/gap**,
not the absolute level; the binding deployment estimate is EXP-097.

---

## Metric denominators / zero-baseline (scope §8; defined before implementation)

- **Per-cell return stream:** entry-fill-re-resolved EXIT-RCT **net per-event return (ATR units)**, timestamped at
  event exit `CloseTime`; denominator = resolved events (**identical `keep` mask** to EXP-092/093 — asserted
  Step 9; the noise changes the entry *price*, never the population). exit_fill, adverse stop, atr, and cost
  reused verbatim.
- **Portfolio return series:** net P&L aggregated by timestamp on the **1h common grid** (4h marked-to-market at
  each 1h close, A1), scaled to the 10% vol target. **Annualization factor** fixed by the 1h grid (recorded in
  `run_metadata.json`). Sharpe denominator = the portfolio return-series std over the analysis window.
- **No zero-baseline ratio.** The binding figure is the portfolio metric's **absolute lower bound vs 0** (edge
  present) and **vs the cross-cell-median single-cell LB** (diversification benefit, like-for-like). No
  percentage-improvement-over-zero metric. A portfolio window with `< 2` resolved trades on the trailing grid is
  `INDETERMINATE` (0 weight, recorded); a cell with no resolved trade in a trailing window carries 0 weight
  (causal warmup, recorded). Guard Sharpe/Calmar when vol or MaxDD = 0 → `NaN` with a flag, never `inf`.
- **Co-reported (non-binding):** MaxDD, CVaR₅, Ulcer, ann return/vol, turnover, per-cell Sharpe + per-cell net
  expectancy per variant, weight/correlation heatmap (if produced), de-allocation timeline, naive-IV contrast,
  the v1/v2/v3 ladder, the idealized-EXP-095 overlay.

---

## Implementation safety constraints (for experiment-developer)

- **Reuse, don't re-derive the exit.** Import the EXP-090/092 substrate + `xen.portfolio` **unchanged**; do
  **not** mutate `fav_level`/`adv_level`/`cap`/`fav_close_fire` or re-walk the exit to perturb it — the noise is
  a **pure entry-leg perturbation** on the frozen resolved exits. Assert the provenance gate (Step 1) **before**
  any noise math; assert keep-mask invariance (Step 9).
- **Entry-side fill = the only new code.** Add one causal function to `xen.intrabar_fill` (e.g.
  `resolve_entry_fills`) returning `entry_fill` for v1/v2/v3; `searchsorted` for the first-bar index, a **bounded**
  (≤k) reduction for v3. No import-time side effects; pure-computation returns arrays; orchestration/`main()`
  does I/O + plotting.
- **Causality / fence:** entry fill consults only 1-minute bars in `(signal_close, train_edge]`; clip all walks
  at the analysis edge; never `scan`/`read` rows ≥ `int(total_rows·0.7)`; assert max-touched `CloseTime` < edge.
- **Adverse sign:** v2 slippage = `+direction·0.05·atr_entry` (worsens the position); v3 = adverse extreme (high
  for long / low for short). Use the **same** `atr_entry` as the substrate.
- **Determinism:** no unseeded RNG; ERC convex iteration fixed init/tol/max-iters; all bootstrap/null RNG via
  `seed_for` off master `20260624`; second pass byte-identical.
- **Bounded iteration / progress:** `tqdm` on the outer loops (cells × variants; cells × rebalances; any null
  replicates). Keep the bootstrap memory-batched; do not vectorize the entry-fill / MTM in a way that crosses the
  causal grid or shuffles event order.
- **MTM under noise:** the first per-position mark increment is measured from `entry_fill(v2)` (the noise cost
  basis); subsequent increments are price-to-price (entry-independent) so Σ(marks) = net(v2). Assert conservation.
- **INDETERMINATE / zero-baseline:** finite handling for `< 2`-trade windows (0 weight, recorded); guard
  Sharpe/Calmar against zero vol / zero MaxDD (`NaN` + flag, never `inf`).

---

## Notes for Stage 4 governance (consolidated; not run here)

1. **Read accounting (D0 §D7).** EXP-096 re-resolves only the **entry-fill leg** of the same 8 cells on the same
   EXP-093 analysis-TEST series under a perturbed execution model — **same cells, same selection, no new
   stratum-specific inference**. Per the **portfolio-aggregate rule + the cost-re-resolution precedent
   (EXP-085)**, this is a **disclosure, not a counted read**: 11 carried strata stay **1/2**, 37 stay 0/2;
   `counted_test_reads=0`, `candidate_slots=0`, `holdout_untouched=true`. Re-affirm at Stage 4.
2. **Holdout.** No global-holdout bar (incl. 1-minute) is loaded. Assert `holdout_untouched=true` + max-touched
   `CloseTime` < the analysis edge.
3. **No new binding statistic.** The portfolio confirmation rule was calibrated/bite-checked at EXP-095; EXP-096
   **inherits** m* (operator decision) and only re-reports the realized v2 edge vs m*. Any optional v2 null FPR
   is **disclosure**, and (if computed) must use the `block_permute_zero_mean` / `null_b_block_permute_returns`
   form — **not** a target built around the realized edge (`falsification_null_design`).
4. **No optimization.** All params at D0 frozen values; v1/v3 variants and the {60,120}-cov bracket are
   **disclosure only**; the binding variant is v2; no value is selected because it lifts the curve.
5. **Membership.** Operator decision 2026-06-25 — **portfolio-only, no per-cell mechanical drop**; per-cell
   `NOISE_DEGRADED` flags are disclosure; G-022a adjudicates the holdout-frozen set.

---

## Complexity Check

- **Statistical tests:** 2 binding — (1) the v2 portfolio Sharpe LB + co-binding Calmar LB vs the cross-cell-median
  baseline (noise survival); (2) the v1/v2/v3 sensitivity-ladder read of the same metric. Gate statistic
  **inherited** (m* not recomputed; optional FPR sanity is disclosure). / **budget ≤ 2** ✓
- **Visualisations:** 5 / **budget 5** ✓
- **New modules:** 0 new modules — **1 small entry-side extension** to `xen.intrabar_fill`; `xen.portfolio`
  reused verbatim. / **budget ≤ 1** ✓
