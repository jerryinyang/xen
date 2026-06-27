# EXP-096 — Noise Infusion: Realistic 1-Minute Entry Fill (RSI-2 Fade Portfolio, 8 confirmed cells)

**Phase:** 022 (CF-MR-001 batch 3 — Portfolio Construction, Noise Infusion & Global-Holdout Release) ·
**Family / HYP:** `CF-MR-001` / `HYP-003` · **Date:** 2026-06-25
**Stage:** 1 (Scope) · **Type:** noise / entry-fill robustness re-derivation of the EXP-095 deployment portfolio
(analysis set; 0 counted reads) — the second of the three Phase-022 experiments; stress-tests the EXP-095 risk
model under a realistic 1-minute entry fill and produces the analysis-set portfolio estimate `G-022a` will use to
fix the holdout-frozen deployable set and the predeclared band.
**Governing design:** [`design.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/design.md)
§3–§4 (EXP-096 row), §8 · D0 [`D0-predeclarations.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/D0-predeclarations.md)
§D1, §D5, §D7, §D9 · amendment [`D0-amendment-001.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/D0-amendment-001.md)
(A1 intra-1h MTM, A2/A3 benefit criterion, A4 bite-MDE — **inherited**).

---

## 1. Research question (single, falsifiable)

**Re-resolving each cell's entries under the binding realistic 1-minute entry-fill model (variant 2: next-1m-open
+ 0.05×ATR(14) adverse slippage) and re-deriving the causal ERC portfolio (static A and circuit-breaker B) under
that fill, does the EXP-095 in-sample risk-adjusted diversification benefit survive — and how much does realistic
execution degrade the portfolio edge and each constituent cell?**

This is the **fill-realism leg** of `HYP-003`. It is analysis-set only (TRAIN + the EXP-093 already-resolved
analysis-TEST series reused as portfolio-aggregate disclosure; 0 counted TEST reads) and decides **no holdout
verdict**. It produces: (a) the noise-realistic per-cell net per-event return streams (entry-leg re-resolved
under v1/v2/v3, binding v2); (b) the re-derived A and B portfolios under the binding fill, with the full
inherited binding read (Sharpe LB + co-binding Calmar LB vs the deployment-realistic cross-cell-median baseline,
CVaR/Ulcer co-reported — amendment-001 A2/A3); (c) the noise sensitivity ladder (v1/v2/v3); (d) the per-cell
degradation disclosure that, with the portfolio read, lets **G-022a** fix the holdout-frozen deployable set and
the predeclared band. The honest prior: a modest adverse fill on a short ~3-bar, ~0.28-ATR geometry will cost a
roughly cost-scale fraction of each cell's gross edge (larger relative bite on the cheaper-ATR 1h cells); the
diversification benefit should be more robust than any single cell, but the binding question is whether it
survives at all and whether realistic execution breaks the fragile 1h tier.

## 2. Signal-registry precondition (verified at scope time)

- **Family `ADMITTED` / lever TRADABLE:** `CF-MR-001` is `ADMITTED (BINDING)` at G-020 and **TRADABLE** at G-021
  (bare RSI-2 fade + EXIT-RCT). `HYP-003` (deployment economics & global-holdout-final) is the active
  hypothesis. EXP-096 consumes **0 new candidate slots** (the noise model is an execution-realism wrapper on the
  admitted lever, not a new signal candidate).
- **Multiplicity registry:** EXP-096 is the registered second experiment of the **Phase 022 batch**
  (`multiplicity-registry.md` §"Phase 022 Batch", EXP-096 row, `PLANNED`). The **entry-fill noise ladder is
  entered at its frozen values** (v1 next-1m-open / **v2 next-1m-open + 0.05×ATR(14) adverse slippage, BINDING** /
  v3 worst-of-next-`k=3`); brackets are disclosed, never selection. No new candidate, variant, detector, or
  parameter branch of the *signal* is introduced.
- **TEST-read ledger — current tally (stated per the Stage-1 precondition):** the 8 deployable cells are all
  within the EXP-093 carried 11, each at **1/2** counted analysis-TEST reads; the other 37 strata are 0/2. **No
  new-dataset holdout shot has been spent.** EXP-096 **re-resolves only the entry-fill leg** of the same 8 cells
  on the **same EXP-093 analysis-TEST series** under a perturbed execution model — same cells, same selection, no
  new stratum-specific claim. Per the **portfolio-aggregate rule + the cost-re-resolution precedent (EXP-085)**
  this is a **disclosure, not a counted read** ⇒ **0 counted reads; no tally moves** (`counted_test_reads=0`,
  `candidate_slots=0`, `holdout_untouched=true`). The final-30% global holdout (including its 1-minute bars) is
  **never** loaded. *(This disclosure classification is re-affirmed at Stage-4 governance per D0 §D7.)*

## 3. Deployable cell set (frozen, D0 §D1 / param #1) — operator decision: study all 8, portfolio-only membership

The **8 G-021-confirmed cells** (re-resolved entry-fill leg over the EXP-090/093 substrate; exit target + adverse
stop **unchanged**):

| # | Stratum | Domain | G-021 tier |
|---|---|---|---|
| 1 | EURUSD-4h | 4h | robust core (mean-AND-median +) |
| 2 | XAUUSD-4h | 4h | robust core |
| 3 | USDCHF-4h | 4h | robust core |
| 4 | AUDJPY-4h | 4h | robust core |
| 5 | EURJPY-4h | 4h | robust core |
| 6 | GBPJPY-4h | 4h | robust core |
| 7 | USTEC-1h | 1h | mean-carried (TEST median −0.026) |
| 8 | US2000-1h | 1h | mean-carried (TEST median ≈ 0) |

**Membership rule (operator decision 2026-06-25 — portfolio-only, no per-cell prune):** EXP-096 keeps **all 8**
cells in the portfolio under noise and does **not** drop any cell by a per-cell mechanical rule. Per-cell net
degradation under noise is **disclosed** (LESSON-001) but is **not** a binding membership gate here — this tests
the risk model's online adaptation to a fragile cell rather than pre-pruning it, per the §8 G0 operator
direction ("keep all 8 unless noise demonstrably breaks a cell"). The **G-022a** freeze adjudicates the
holdout-frozen deployable set from EXP-096's **portfolio-level** read (binding) plus the per-cell disclosure;
EXP-096 supplies the evidence, not the membership verdict. The 3 non-confirming 1h cells (EURUSD-1h, NZDUSD-1h,
GBPUSD-1h) stay **excluded** (file drawer).

## 4. Data views, instruments, slice, exclusions

- **Dataset:** VAL-005-admitted INFR-003 5-year 1-minute bars, holdout-fenced `build_domain_bars`. Domain bars:
  1h = 60-min, 4h = 240-min. The entry-fill noise reads the **1-minute** bars at/after each signal domain-bar's
  `CloseTime`. Real OHLC only; per-cell returns in **ATR(14) units**, the portfolio curve in return/currency
  units (10% vol-target-scaled, D0 §D2.3, amendment-001 A1 intra-1h MTM).
- **Instruments / cells:** the 8 deployable cells in §3. No instrument or domain outside the set is read.
- **Slice — TRAIN + analysis-TEST (disclosure):** per-cell entry-fill-re-resolved return streams over the **full
  analysis set** (`[0, int(total_rows·0.7))`) — the EXP-090–092 TRAIN region plus the **EXP-093 already-resolved
  analysis-TEST stratum** (`[int(int(total·0.7)·0.7), int(total·0.7))`), reused as a **portfolio-aggregate
  disclosure**. The portfolio curve and all weights are built **causally** within this window (trailing
  estimates only).
- **MANDATORY EXCLUSION — the final-30% global holdout `[int(total_rows·0.7), total_rows)` is NEVER loaded,
  sliced, or materialized** (including its 1-minute bars). The global-holdout release is EXP-097 only.
  `holdout_untouched=true` asserted in `run_metadata.json`.
- **No look-ahead:** the entry fill at signal *t* uses only 1-minute bars at/after *t*'s domain-bar `CloseTime`,
  clipped by **timestamp** at the active slice's right edge; every portfolio weight, covariance, vol estimate,
  concurrent-risk cap, and circuit-breaker state at curve timestamp *u* uses only per-cell returns resolved
  **strictly before** *u*. Cross-domain alignment by **timestamp** (`CloseTime`), never bar index.

## 5. Frozen parameters (inherited + noise model — NO tuning)

**Inherited (frozen as confirmed at G-021, byte-for-byte):** entry `RSI(2)` 2/10/90; exit **EXIT-RCT**; adverse
`2.0×ATR(14)` + EXP-089 MR-tempo cap; cost = `D0-amendment-003` Phase-021-local conservative round-trip
(`F=0`). **Only the entry execution price changes** (§5 noise); the EXIT-RCT target level (from the signal-bar
Wilder state) and the adverse stop are **unchanged**, and no exit is re-screened or re-selected.

**Portfolio / risk model (frozen, D0 ratified table + amendment-001; brackets disclosed, NEVER selection):**

- **Sizing:** ERC (equal risk contribution), covariance-aware, parameter-free. **Both A (static ERC) and B
  (ERC + circuit-breaker)** are re-derived under noise (operator decision 2026-06-25 — run both; the realistic
  adverse fill on the fragile 1h cells is the regime where B might earn its keep, and A-vs-B-under-noise is the
  clean input to the G-022a A-vs-B decision).
- **Covariance:** trailing rolling **90 trading days**, causal, Ledoit-Wolf shrinkage. Bracket {60, 120}.
- **Rebalance:** **weekly**; weights held between. Bracket {daily, monthly}.
- **Global risk anchor:** scale to **10% annualized vol** (single scalar; Sharpe-invariant — checked). Bracket {7%, 15%}.
- **Concurrent-risk cap:** total open risk-aware (correlation-adjusted) exposure ≤ **1.5×** the rebalance budget. Bracket {1.0×, 2.0×}.
- **Circuit-breaker (Portfolio B):** cell allocation multiplier = **0 while its trailing-50-resolved-trade mean
  net return < 0, else 1** (causal; re-allocates on recovery). Bracket window {30, 100}; halve-not-zero disclosed.
- **Intra-position MTM (amendment-001 A1):** 4h (and 1h) open positions marked-to-market at each intervening 1h
  close from the resolved 1-minute path; conservation invariant Σ(intra-position 1h marks) = realized net
  per-event return (≤1e-9 ATR). Inherited and retained under noise.
- **Inference:** moving-block bootstrap one-sided lower bound on the portfolio metric (`xen.portfolio` /
  `xen.ass` machinery; block length = the rebalance cadence). Seeds fixed; master seed `20260624`.

**Noise / entry-fill model (frozen, D0 §D5 / param #8):**

- **Variant 1 (mild floor):** entry execution price = the **open of the first 1-minute bar after the signal
  domain-bar's `CloseTime`**.
- **Variant 2 (BINDING):** variant 1 **+ adverse slippage 0.05×ATR(14)** (worse for the position).
- **Variant 3 (stress ceiling):** the **worst (most adverse) price across the first `k=3` 1-minute bars** after
  the signal close.
- Realized net return is recomputed as `direction·(exit_fill − entry_fill)/ATR(14) − cost` (`xen.intrabar_fill.
  net_return_atr` with the perturbed `entry_fill` replacing the signal-bar close). The flat round-trip cost (D1)
  is **retained and is not double-counted** by the slippage (cost models spread/commission; the noise models
  latency + adverse-selection on the fill price). EXP-096 **binds variant 2** for the portfolio re-derivation and
  reports v1/v2/v3 as the disclosed sensitivity ladder.

## 6. What EXP-096 computes (analysis-set; no holdout verdict)

```
Entry-fill re-resolution (per cell, per variant v ∈ {v1, v2(binding), v3}):
  recompute the entry execution price from the 1m bars after each signal domain-bar CloseTime (causal)
  recompute net per-event return = direction·(exit_fill − entry_fill)/ATR − cost   (exit/stop unchanged)
  provenance: at zero slippage and a degenerate "fill==signal-close" reference, reconcile back toward the
    EXP-093 / EXP-095 idealized-at-close series (sanity); the realized-event population (keep mask) is unchanged

Portfolio re-derivation under the BINDING variant 2 (A static ERC and B circuit-breaker), with intra-1h MTM:
  annualized Sharpe + moving-block one-sided lower bound; Calmar LB (co-binding); CVaR5 / Ulcer; ann ret/vol;
  MaxDD; turnover (co-reported) — the inherited amendment-001 A2/A3 binding read

Diversification / benefit read (binding, amendment-001 A2/A3):
  portfolio Sharpe LB (and co-binding Calmar LB) vs the deployment-realistic cross-cell-median single-cell LB
    (like-for-like, LB vs LB); disclosed vs the ex-post-best single cell (LB) and vs naive inverse-vol
  verdict labels: a miss inside the metric's one-sided sampling band / inside the disclosed nuisance bracket is
    INCONCLUSIVE / within-noise, not a fail

Noise sensitivity ladder (disclosed):
  the same portfolio metrics under v1 / v2 / v3, and the per-cell net per-event expectancy (mean + median, with
    MBB lower bound) under each variant — the per-cell degradation disclosure feeding the G-022a membership call

Gate-statistic check (inherited m*, per operator decision 2026-06-25):
  re-report the realized variant-2 portfolio Sharpe LB against the EXP-095 inherited MDE m* = 1.75 (A) / 2.00 (B)
    and the realized-edge margin; the A4 MDE-curve is NOT recomputed under noise (treated as calibrated at
    EXP-095). A lightweight synthetic-null FPR sanity on the variant-2 series MAY be reported as disclosure only.

Adaptability (A vs B under noise):
  the A−B difference in Sharpe / MaxDD / Ulcer; the circuit-breaker de-allocation timeline on the fragile cells
    (USTEC-1h, US2000-1h) under the realistic fill — does realistic execution change the EXP-095 "B neutral" read?
```

The portfolio metrics and the ladder are **descriptive on the analysis set** — no binding deployment verdict is
issued here. The binding deployment read is EXP-097 on the global holdout, under the G-022a-frozen rule.

## 7. Measurable criteria

- **Noise survival (the leg's main read):** under the **binding variant 2** with intra-1h MTM, at least one of
  Portfolio A / B retains an annualized-Sharpe lower bound that **exceeds the deployment-realistic cross-cell-
  median single-cell Sharpe lower bound by a material margin** (and is not dominated on the co-binding Calmar LB),
  i.e. the EXP-095 diversification benefit is not erased by realistic execution. Reported per portfolio with the
  full Sharpe/Calmar/CVaR/Ulcer/MaxDD table, the per-cell baselines, and the v1/v2/v3 ladder. A SURVIVES read
  hands G-022a a non-empty deployable set and a noise-realistic band estimate.
- **Cell degradation (disclosure, feeds G-022a membership):** the per-cell net per-event expectancy (mean +
  median, MBB LB) under v2 is reported for all 8 cells; cells whose v2 net expectancy LB falls below their
  EXP-093 margin are **flagged as noise-degraded** (disclosure only — no mechanical drop here; G-022a decides
  membership). This is the operator-chosen portfolio-only-membership path (§3).
- **Adaptability (A vs B under noise):** the A−B comparison + circuit-breaker timeline is reported; "realistic
  execution makes B earn its keep" is supported iff B's MaxDD/Ulcer is materially lower than A's at comparable
  Sharpe under v2 (descriptive; no pass/fail — informs the G-022a A-vs-B decision).
- **Statistic readiness (inherited):** the realized v2 portfolio Sharpe LB is re-reported against the inherited
  m* (1.75 A / 2.00 B); readiness for G-022a is inherited from EXP-095 (FPR-controlled + finite clearable MDE) —
  EXP-096 confirms the realized v2 edge still sits above m*, or flags if noise pulls it below (which would route a
  G-022a band/scale reconsideration, not a silent pass).
- **Inconclusive:** the v2 portfolio lower bound spans zero / falls within the metric sampling band of the
  cross-cell-median baseline — disclosed as within-noise; routes a likely **G-022a HALT** (holdout preserved)
  rather than a spent shot.
- **Integrity (required regardless):** determinism byte-identical second pass (entry-fill walk + ERC convex
  solve + MTM marks + bootstrap) on A and B under v2; **MTM conservation** Σ(marks)=realized net per cell
  (≤1e-9 ATR); causal-fill assertion (entry fill uses only 1m bars at/after the signal close; no future per-cell
  return enters any weight); real-price metrics only; `holdout_untouched=true`, `counted_test_reads=0`,
  `candidate_slots=0` asserted in `run_metadata.json`; no stratum tally moves; the realized-event `keep` mask is
  unchanged from EXP-093 (noise perturbs the fill price, never which events resolve).

## 8. Metric denominators / zero-baseline (defined before implementation)

- **Per-cell return stream:** the entry-fill-re-resolved EXIT-RCT **net per-event return (ATR units)**,
  timestamped at the event exit `CloseTime`; denominator = resolved events (the **identical `keep` mask** as
  EXP-092/093 — the noise changes the entry *price*, never the event population). The exit path and adverse stop
  are reused verbatim; only `entry_fill` differs.
- **Portfolio return series:** net P&L aggregated by timestamp on the **1h common grid** (4h marked-to-market at
  each 1h close, amendment-001 A1), scaled to the 10% vol target. **Annualization factor** fixed by the grid
  (recorded). Sharpe denominator = the portfolio return-series standard deviation over the analysis window.
- **No zero-baseline ratio.** The binding figure (for G-022a) is the portfolio metric's **absolute lower bound**
  vs **0** (edge present) and vs the **deployment-realistic cross-cell-median single-cell LB** (diversification
  benefit, like-for-like). There is no percentage-improvement-over-zero metric. A portfolio window with < 2
  resolved trades on the trailing grid is `INDETERMINATE` for that mark (carries 0 weight; recorded), not forced
  to a number. A cell with no resolved trade in a trailing window carries 0 weight (causal warmup; recorded).
- **Co-reported (non-binding):** MaxDD, CVaR5, Ulcer, annualized return/vol, turnover, per-cell Sharpe + per-cell
  net expectancy under each variant, weight/correlation heatmap, circuit-breaker de-allocation timeline, naive
  inverse-vol contrast, the v1/v2/v3 ladder.

## 9. Complexity budget (D0 §5)

| Item | Budget | EXP-096 plan |
|---|---|---|
| Binding statistical tests | ≤ 2 (noise-survival of the portfolio edge) | 2 — (1) the v2 portfolio Sharpe LB + co-binding Calmar LB vs the deployment-realistic cross-cell-median baseline (noise survival); (2) the v1/v2/v3 sensitivity-ladder read of the same metric. Gate statistic inherited (m* not recomputed). |
| Visualisations | ≤ 5 | (1) v1/v2/v3 noise sensitivity ladder (portfolio Sharpe/Calmar); (2) A/B/best-cell equity curves under v2; (3) per-cell net-expectancy degradation (noise-free → v2, mean+median) bar chart; (4) circuit-breaker de-allocation timeline under v2 (fragile cells); (5) A−B drawdown/Ulcer comparison under v2. |
| New code modules | ≤ 1 (small extension) | **Extend `xen.intrabar_fill`** with an **entry-side fill rule** (entry execution price from the 1m bars after the signal domain-bar close; v1/v2/v3), mirroring the existing exit-side touch logic — causal, real touched prices, timestamp-clipped. **Reuse** `xen.portfolio` (ERC/MTM/cap/breaker/bootstrap — EXP-095 verbatim), `xen.mean_reversion`, `xen.capgeo_cost`/financing, `xen.ass`, and the EXP-090/093 substrate. No new standalone module. |

## 10. Discipline (binding)

- **Causal everything.** The entry fill uses only 1m bars at/after the signal close; weights, covariance, vol,
  the concurrent-risk cap, and the circuit-breaker use past-only information at each curve timestamp. A unit
  test asserts no future bar enters any entry fill and no future per-cell return enters any weight.
- **No optimization.** Every hyperparameter (portfolio + the noise slippage 0.05×ATR / `k=3`) is frozen at its
  D0 value; brackets and the v1/v3 variants are reported as disclosed sensitivity, **never** used to select a
  binding value. The binding variant is v2; no value is chosen because it lifts the curve.
- **Real-price outcomes only;** HA/brick prices never enter a metric; entry and exit fills are real touched 1m
  prices (inherited).
- **No scope expansion after approval:** the G-022a freeze and the global-holdout release (EXP-097) are separate
  experiments; the deferred levers (vol-regime, contrarian, 25/75, 15m, cross-cuts, tuning, expansion,
  faster-cost) are each a separate dated `D0-amendment-*` / slot decision.
- **Deviation handling:** a frozen-design confound found mid-stream → dated `D0-amendment-*` + hard-delete +
  full rerun (programme norm), not a silent follow-up. A verdict-material audit finding → fix + re-run before any
  number stands (the EXP-095 amendment-001 precedent — intra-position MTM is now binding and audited explicitly).
- **Per-cell disclosure (LESSON-001):** the portfolio is the deployment estimand, but every per-cell baseline,
  noise degradation, and circuit-breaker action is disclosed alongside the aggregate — no cell-level result is
  hidden inside the portfolio.

## 11. Out of scope (explicit)

- The final-30% global holdout (sealed; EXP-097 only) and any holdout-release decision.
- The G-022a freeze itself (governance, not this experiment) and the membership verdict (G-022a decides from
  EXP-096's portfolio read + per-cell disclosure).
- Any re-resolution of the EXIT-RCT exit *target* or adverse stop, or re-screening/re-selection of any exit; any
  re-tuning of entry/exit/adverse/cost. Only the entry execution *price* changes.
- Recomputing the A4 bite-MDE / gate statistic under noise (inherited from EXP-095 per operator decision; only
  the realized v2 edge-vs-m* margin is re-reported; an optional FPR sanity is disclosure-only).
- Selecting a binding hyperparameter or noise variant from the sensitivity ladder (ladder/brackets are
  disclosure only; v2 is the binding variant).
- The 3 non-confirming 1h cells; the deferred levers (vol-regime, contrarian, 25/75, 15m, regime×variant
  cross-cuts, parameter tuning, instrument/domain expansion, faster-cost sensitivity).
