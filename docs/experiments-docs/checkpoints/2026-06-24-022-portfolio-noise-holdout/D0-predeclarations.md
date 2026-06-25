# Phase 022 D0 — Predeclarations (CF-MR-001 Portfolio, Noise & Global-Holdout Release)

**Status:** **FROZEN — G0 RATIFIED (2026-06-24, operator-authorized).** This freezes the batch-3
(deployment-economics & OOS-final) design for the bare RSI-2 fade (CORE) + EXIT-RCT confirmed tradable at
G-021. D1–D9 and the ratified-parameter table below are **FROZEN**; no result-producing code (EXP-095) runs
against anything but these. No amendment without a dated `D0-amendment-*` file in this directory (programme
norm).

**A new binding gate statistic is introduced** (the portfolio-level holdout confirmation rule) ⇒ **a
synthetic-null calibration + bite-check is required and is part of EXP-095**, before `G-022a` freezes the rule
(§D6). The terminal holdout rubric (`G-022-gate-criteria.md`) and the pre-holdout freeze
(`G-022a-gate-criteria.md`) are frozen at **G-022a**, not here — they depend on the EXP-095/096 analysis-set
portfolio estimate for the predeclared band (fixing them at G0 would require look-ahead into the band).

**Checkpoint:** `2026-06-24-022-portfolio-noise-holdout` · **Governing design:** `design.md`.
**Family / lever:** CF-MR-001, first candidate slot consumed at G-020, TRADABLE at G-021; lever = **bare RSI-2
fade (CORE) + EXIT-RCT**, intraday. **HYP:** `CF-MR-001/HYP-003` (deployment economics & global-holdout-final).
**Discipline (binding):** causal weights/estimates everywhere; real-price outcomes; deterministic (fixed seeds,
byte-identical second pass); **no optimization** (every hyperparameter predeclared + sensitivity-bracketed,
never tuned to lift the curve); per-cell disclosure alongside the binding portfolio estimand (LESSON-001).
EXP-095/096 are **0 counted TEST reads** (TRAIN + EXP-093 analysis-TEST series as portfolio-aggregate
disclosure). **The final-30% global holdout is loaded only at EXP-097, after the G-022a freeze.**

---

## Ratified parameter table (frozen; conservative defaults + sensitivity brackets — NEVER tuned to the curve)

| # | Parameter | Frozen value (binding) | Sensitivity bracket (disclosed, non-binding) | One-line justification |
| --- | --- | --- | --- | --- |
| 1 | **Deployable set (study)** | the **8 G-021-confirmed cells**: EURUSD/XAUUSD/USDCHF/AUDJPY/EURJPY/GBPJPY-4h + USTEC-1h + US2000-1h | — | the confirmed OOS set; study all 8 to test online adaptation (§8.1). Holdout-frozen set = noise-survivors (decided at G-022a). |
| 2 | **Sizing rule** | **ERC (equal risk contribution / risk parity)**, covariance-aware; **no free weight parameter** | naive inverse-vol (disclosed contrast) | equalizes marginal risk across the correlated set (JPY cluster); parameter-free ⇒ no overfitting. |
| 3 | **Covariance/vol estimator** | **trailing rolling window = 90 trading days**, causal (past-only), shrinkage to diagonal (Ledoit-Wolf, parameter-free) | {60, 120} days | enough samples for a stable 8×8 covariance (~a quarter); shrinkage handles the small-sample / high-correlation regime without a tuned ridge. |
| 4 | **Rebalance cadence** | **weekly** (recompute ERC weights each week; hold between) | {daily, monthly} | recomputing every bar injects estimation noise → spurious turnover/cost; weekly is a conventional stable cadence. |
| 5 | **Global risk anchor** | scale the portfolio to **10% annualized volatility** (single global scalar) | {7%, 15%} | turns ATR-returns into currency-P&L so MaxDD is interpretable. **Sharpe is invariant** to this scalar (sets drawdown/leverage realism only). |
| 6 | **Concurrent-risk cap** | total open **risk-aware** (correlation-adjusted) exposure ≤ **1.5×** the per-rebalance risk budget | {1.0×, 2.0×} | bounds leverage when many (often correlated) cells fire together; the principled form of "max positions." |
| 7 | **Online circuit-breaker (Portfolio B)** | a cell's allocation multiplier = **0 if its trailing-50-resolved-trade mean net return (ATR units) < 0, else 1**; causal, re-allocates on recovery (≥0) | window {30, 100}; halve-not-zero variant | parameter-light edge-decay guardrail (ERC is expectancy-blind); de-risk a deteriorating cell — risk management, not return optimization. |
| 8 | **Noise — binding entry fill** | **next-1m-open + adverse slippage 0.05×ATR(14)** on the entry price (variant 2) | variant 1 next-1m-open (mild floor); variant 3 worst-of-next-`k=3` 1m bars (stress ceiling) | models execution latency (you do not get the signal-bar close) + a modest conservative adverse-selection tick; not overly adverse. |
| 9 | **Holdout confirmation rule** | **portfolio** annualized-Sharpe (or pooled net per-trade expectancy) **one-sided lower bound > the G-022a-predeclared margin band**, moving-block bootstrap, calibrated synthetic-null FPR ≤ 0.05 | — | the binding deployment estimand is the portfolio, not per-cell; band + calibration frozen at G-022a (EXP-032 margin lesson). |

---

## D1 — Inherited frozen substrate, dataset, deployable cells

**Signal / exit / adverse / cost — inherited byte-for-byte from Phase 021 D0 (NO re-tuning):** entry `RSI(2)`
Wilder 2/10/90; exit **EXIT-RCT** (`P*_t = Close_t + (AL_t − AG_t)` long / symmetric short, trailing, resolved
by `xen.intrabar_fill`); adverse `2.0×ATR(14)` + EXP-089 MR-tempo cap; cost = `D0-amendment-003` Phase-021-local
conservative round-trip table (hash `fa7c887…`, `F=0`), `xen.capgeo_cost.COST_CONSTANTS` not mutated.

**Dataset:** VAL-005-admitted INFR-003 5-year 1-minute bars, holdout-fenced `build_domain_bars`. Domain bars:
1h=60-min, 4h=240-min. Real OHLC; metrics in **ATR(14) units** (per-cell) and **currency/return units** (the
portfolio equity curve). Master seed `20260624`.

**Deployable cells (param #1):** the 8 G-021-confirmed cells. The 3 non-confirming 1h cells are excluded
(retained in the file drawer). All 8 are within the EXP-093 carried 11 (each at 1/2 counted analysis-TEST reads)
— so EXP-095/096's reuse of their analysis-TEST resolved returns is a **re-combination of already-spent reads**
(portfolio-aggregate disclosure), not a new counted read (§D7).

**Slices.**
- EXP-095/096 — **TRAIN** (`[0, int(int(total·0.7)·0.7))`) for construction + **analysis-TEST**
  (`[int(int(total·0.7)·0.7), int(total·0.7))`) reused via the EXP-093 already-resolved series as
  portfolio-aggregate **disclosure**. The final-30% global holdout is **never sliced**.
- EXP-097 — the **final-30% global holdout** (`[int(total·0.7), total]`) per file, loaded for the first time,
  after the G-022a freeze. The single sanctioned one-shot release.

## D2 — Portfolio construction (frozen; new module `xen.portfolio`)

The per-cell return stream for each of the 8 cells is the **resolved EXIT-RCT net per-event return (ATR units),
timestamped at the event's exit `CloseTime`** — reused verbatim from the EXP-090/093 substrate (no
re-resolution in EXP-095; EXP-096 re-resolves only the entry-fill leg, §D5).

### D2.1 — Time-aligned equity curve
- Mark P&L on a **common wall-clock grid = the finest deployable domain's close (1h)**; 4h positions are
  marked-to-market at each intervening 1h close, realized at their exit. Cross-domain alignment by **timestamp**,
  never bar index.
- The curve aggregates per-cell P&L by timestamp into one portfolio return series; annualized Sharpe, MaxDD, and
  Calmar are computed from it. The denominator and annualization factor are fixed at D5.

### D2.2 — ERC weights (param #2/#3/#4, causal)
- At each weekly rebalance *r*, estimate the 8×8 covariance from the **trailing 90 trading days** of per-cell
  return streams available **strictly before** *r* (Ledoit-Wolf shrinkage to the diagonal — parameter-free).
- Solve the ERC weights (equal marginal risk contribution; standard convex iteration, deterministic,
  fixed tolerance/seed). Hold weights until the next rebalance. A cell with < a minimum trailing sample at *r*
  carries **0 weight** until it has history (causal warmup; recorded).

### D2.3 — Global risk anchor + concurrent-risk cap (param #5/#6)
- Scale all weights by the single global scalar that targets **10% annualized portfolio vol** (estimated on the
  trailing window — causal). Sharpe is invariant to this scalar (recorded as an invariance check).
- Cap total open **risk-aware** exposure at **1.5×** the per-rebalance risk budget (correlation-adjusted, so a
  simultaneous JPY-cluster firing counts near one bet); excess is scaled down pro-rata at the moment of the
  breach (causal, recorded).

## D3 — Online circuit-breaker (Portfolio B; param #7)

- For each cell, maintain a **causal trailing-50-resolved-trade mean net return** (ATR units), updated only as
  that cell's trades resolve. The cell's allocation multiplier is **0 while that trailing mean < 0**, **1 while
  ≥ 0** (re-allocates on recovery). Applied multiplicatively to the ERC weight before the risk-anchor scaling.
- **Portfolio A = no circuit-breaker** (multiplier ≡ 1, vol-adaptive only). **Portfolio B = with circuit-breaker**
  (vol- *and* edge-adaptive). Both run in parallel; A-vs-B is the EXP-095 adaptability comparison.
- Strictly causal (trailing realized P&L only). No look-ahead into a cell's future recovery.

## D4 — Endpoint / metrics (frozen)

- **Binding portfolio metric:** annualized Sharpe of the time-aligned net portfolio return series (after D1
  cost), with a **moving-block bootstrap one-sided lower bound** (`xen.ass` machinery extended to the portfolio
  series; block length = the rebalance cadence). Co-binding companion: pooled net per-trade expectancy lower
  bound.
- **Co-reported (non-binding):** MaxDD, Calmar, annualized return/vol, turnover, per-cell Sharpe (the
  single-cell baselines the portfolio is compared against), the A−B difference (adaptability), circuit-breaker
  de-allocation timeline, weight/correlation heatmap, and the noise sensitivity ladder (EXP-096).
- **Comparison baseline:** the **best individual deployable cell's** annualized Sharpe (and the equal-weight
  naive-inverse-vol portfolio, disclosed). The portfolio "beats" iff its Sharpe lower bound exceeds the best
  single cell's point estimate by a material margin (band fixed at G-022a).

## D5 — Noise infusion (frozen; entry-fill model — EXP-096)

- The entry execution price replaces the idealized signal-bar **close** with a realistic 1-minute fill:
  - **Variant 1 (mild floor):** the **open of the first 1-minute bar after the signal domain-bar's CloseTime**.
  - **Variant 2 (BINDING, param #8):** variant 1 **+ adverse slippage 0.05×ATR(14)** (worse for the position).
  - **Variant 3 (stress ceiling):** the **worst (most adverse) price across the first `k=3` 1-minute bars** after
    the signal close.
- Only the **entry execution price** changes; the EXIT-RCT target level (from the signal-bar Wilder state) and
  the adverse stop are unchanged. Realized net return is recomputed as `direction·(exit_fill − entry_fill)/ATR −
  cost`. The flat round-trip cost (D1) is **retained** and is *not* double-counted by the slippage (the cost
  models spread/commission; the noise models latency + adverse-selection on the fill price).
- Implemented as a small **entry-side** extension to `xen.intrabar_fill`, mirroring the existing exit-side touch
  logic; causal (only 1m bars at/after the signal close), real touched prices, clipped by timestamp at the
  active slice's right edge. EXP-096 re-derives the portfolio (A and B) under the binding variant 2 and reports
  the full ladder.

## D6 — New gate statistic: calibration + bite-check (binding; part of EXP-095)

The **portfolio-level holdout confirmation statistic** (the Sharpe / pooled-expectancy moving-block lower bound,
param #9) is **new** ⇒ before `G-022a` may freeze the holdout rule:

- **Synthetic-null FPR calibration.** Under a matched no-edge null (per-cell returns block-permuted /
  sign-flipped to zero expectancy, preserving the empirical covariance and autocorrelation — the EXP-001/027/044
  + `null_b_block_permute_returns` form, NOT a path rotation), the portfolio confirmation rule must have
  **FPR ≤ 0.05** at the realized holdout-equivalent sample size and block structure. Recorded per construction
  (A and B).
- **Bite-check GREEN.** A planted-edge / no-edge two-sample bite-check at the materiality scale confirms the
  rule separates a real portfolio edge from the null at the holdout sample size, and does **not** bite on the
  null. (Programme norm: a new binding statistic is bite-checked GREEN before it gates anything;
  `falsification_null_design` — the null is **not** built around any signal-derived target.)
- The **predeclared band** (the margin the holdout lower bound must clear) is set at **G-022a** from the
  EXP-095/096 analysis-set portfolio estimate (with the expected TRAIN→TEST→holdout shrinkage subtracted
  conservatively), so the holdout read can be over- *or* under-confirmed (EXP-032 margin lesson).

## D7 — Read accounting / holdout discipline (binding)

- **EXP-095 / EXP-096: 0 counted TEST reads.** They read TRAIN and **reuse the EXP-093 already-resolved
  analysis-TEST per-cell series** to build the portfolio curve — a **portfolio-aggregate disclosure** (no new
  per-stratum selection or inference; the per-stratum binding reads were spent at EXP-093). Per the
  portfolio-aggregate rule (`test-read-ledger.md`), no stratum tally moves; the 11 carried strata stay **1/2**,
  the other 37 stay 0/2. `holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0` asserted.
  - **Governance note (to be ratified at Stage 4):** EXP-096 re-resolves the **entry-fill leg** of the 8 cells on
    the analysis-TEST series under a new fill model. This is a **robustness re-derivation of an already-spent
    read under a perturbed execution model — same cells, same selection, no new stratum-specific claim** (the
    EXP-085 cost-re-resolution precedent) ⇒ **disclosure, not a new counted read.** Confirmed at pre-execution
    governance.
- **EXP-097: the single sanctioned global-holdout release.** The final-30% global holdout is loaded for the
  first time, for the **portfolio estimand only** (per-cell results disclosed, non-binding). This is **outside
  the analysis-TEST ledger entirely** — a holdout-governance event recorded in `test-read-ledger.md` and the
  multiplicity registry in the same change (à la EXP-032). **One shot; non-upgradable; non-repeatable.** It runs
  only after the **G-022a** freeze. No holdout bar — including 1-minute bars — is loaded at any earlier stage.
- **0 additional candidate slots** (no new signal candidate; the portfolio/risk model is a deployment wrapper).

## D8 — Determinism, causality, real-price discipline

- All seeds fixed/recorded (master `20260624`); a second full pass (ERC convex solve, bootstrap streams,
  intrabar walks) is **byte-identical**.
- **Causal at every point of the equity curve:** covariance, vol, correlation, the concurrent-risk cap, and the
  circuit-breaker use only information available strictly before the marked timestamp. No full-sample or future
  bar enters any weight. Cross-domain alignment by timestamp.
- **Real prices only** (`RealOpen/High/Low/Close`, real 1m OHLC for fills); no HA/Renko synthetic-price returns.
- **No tuning:** every parameter in the ratified table is frozen; brackets are reported as disclosed sensitivity,
  never used to select a binding value. The deferred levers (vol-regime, contrarian, 25/75, 15m, cross-cuts,
  parameter tuning, instrument/domain expansion) remain **registered-but-deferred** (multiplicity ledger);
  opening any requires a dated `D0-amendment-*` + slot decision.

## D9 — Gates within the phase

- **G-022a (pre-holdout freeze; after EXP-095/096, before EXP-097).** Requires, all affirmatively: (i) a
  non-empty noise-survivor deployable set; (ii) an analysis-set portfolio edge (the binding metric's lower bound
  clears 0 with a material margin on the analysis set); (iii) the confirmation statistic **calibrated (FPR≤0.05)
  + bite-checked GREEN** (D6); (iv) the predeclared holdout band fixed from the analysis-set estimate. Freezes
  `G-022a-gate-criteria.md` + `G-022-gate-criteria.md`. **Fail any ⇒ HALT, holdout preserved.**
- **G-022 (terminal; after EXP-097).** Mechanical adjudication of the holdout read against the G-022a band:
  **DEPLOYABLE_CONFIRMED / DECAYED / INCONCLUSIVE** (design §6). No threshold/band/rule re-edited after seeing
  the holdout outcome (no goalpost-moving).

## Slot & read accounting (summary)

- **0 additional candidate slots** (deployment wrapper on the admitted lever).
- **0 counted TEST reads** in EXP-095/096 (portfolio-aggregate disclosure; 11 carried strata stay 1/2).
- **EXP-097 spends the one-shot final-30% global-holdout release** (outside the analysis-TEST ledger; recorded
  as a holdout-governance event), only after the G-022a freeze.
