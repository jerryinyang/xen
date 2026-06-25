# EXP-095 — Portfolio Construction & Online-Adaptive Risk Model (RSI-2 Fade, 8 confirmed cells)

**Phase:** 022 (CF-MR-001 batch 3 — Portfolio Construction, Noise Infusion & Global-Holdout Release) ·
**Family / HYP:** `CF-MR-001` / `HYP-003` · **Date:** 2026-06-24
**Stage:** 1 (Scope) · **Type:** portfolio-construction & risk-model build (analysis set, noise-free; 0 counted
reads) — the first of the three Phase-022 experiments; produces the deployment risk model and the calibrated
holdout statistic that `G-022a` will freeze.
**Governing design:** [`design.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/design.md)
§3–§4 (EXP-095 row) · D0 [`D0-predeclarations.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/D0-predeclarations.md)
§D2–§D4, §D6, §D7.

---

## 1. Research question (single, falsifiable)

**Built from the 8 G-021-confirmed cells, does a causal, parameter-free ERC portfolio deliver materially better
risk-adjusted performance (annualized Sharpe, with MaxDD / Calmar co-reported) than the best individual cell —
and does adding an online performance circuit-breaker (Portfolio B) measurably de-risk a deteriorating cell
versus static ERC (Portfolio A)?**

This is the **portfolio-economics leg** of `HYP-003`. It is analysis-set only (noise-free, 0 counted TEST
reads) and decides no holdout verdict. It produces: (a) the deployment risk model (A vs B); (b) the quantified
diversification benefit vs single cells; (c) the **calibrated + bite-checked portfolio-level confirmation
statistic** that `G-022a` freezes before the EXP-097 global-holdout read. The honest prior: diversification
should help, and the circuit-breaker should de-risk the genuinely fragile cells (the 1h mean-carried tier) —
but pure ERC is **expectancy-blind**, so without the breaker a decaying cell keeps its full risk allocation;
EXP-095 measures exactly how much the breaker buys.

## 2. Signal-registry precondition (verified at scope time)

- **Family `ADMITTED` / lever TRADABLE:** `CF-MR-001` is `ADMITTED (BINDING)` at G-020 and **TRADABLE** at G-021
  (bare RSI-2 fade + EXIT-RCT). `HYP-003` (deployment economics & global-holdout-final) is the active
  hypothesis. EXP-095 consumes **0 new candidate slots** (the portfolio/risk model is a deployment wrapper, not
  a new signal candidate).
- **Multiplicity registry:** EXP-095 is the registered first experiment of the **Phase 022 batch**
  (`multiplicity-registry.md`). The portfolio/risk-model hyperparameters and the noise variants are entered
  there at their frozen values; the **portfolio-level holdout confirmation statistic is a NEW binding gate
  statistic** ⇒ EXP-095 includes its synthetic-null calibration + bite-check (D6). No new candidate, variant,
  detector, or parameter branch of the *signal* is introduced.
- **TEST-read ledger — current tally (stated per the Stage-1 precondition):** the 8 deployable cells are all
  within the EXP-093 carried 11, each at **1/2** counted analysis-TEST reads; the other 37 strata are 0/2. **No
  new dataset has a spent holdout shot.** EXP-095 re-combines the **EXP-093 already-resolved analysis-TEST
  per-cell series** into a portfolio curve — a **portfolio-aggregate disclosure** (no new per-stratum selection
  or inference) ⇒ **0 counted reads; no tally moves** (`counted_test_reads=0`, `candidate_slots=0`,
  `holdout_untouched=true`). The final-30% global holdout is **never** loaded.

## 3. Deployable cell set (frozen, D0 §D1 / param #1)

The **8 G-021-confirmed cells** (per-cell EXIT-RCT net per-event return streams reused verbatim from the
EXP-090/093 substrate; no re-resolution here):

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

Correlation structure to respect (the reason ERC, not naive inverse-vol): the **4h JPY cluster**
(EURJPY/GBPJPY/AUDJPY) shares a common JPY factor; EURUSD/USDCHF share USD/EUR. The 3 non-confirming 1h cells
(EURUSD-1h, NZDUSD-1h, GBPUSD-1h) are **excluded** (retained in the file drawer). USTEC-1h / US2000-1h are the
deliberate fragility stress-cases for the circuit-breaker comparison.

## 4. Data views, instruments, slice, exclusions

- **Dataset:** VAL-005-admitted INFR-003 5-year 1-minute bars, holdout-fenced `build_domain_bars`. Domain bars:
  1h = 60-min, 4h = 240-min. Real OHLC only; per-cell returns in **ATR(14) units**, the portfolio curve in
  return/currency units (vol-target-scaled, D0 §D2.3).
- **Instruments / cells:** the 8 deployable cells in §3. No instrument or domain outside the set is read.
- **Slice — TRAIN + analysis-TEST (disclosure):** per-cell return streams over the **full analysis set**
  (`[0, int(total_rows·0.7))`) — the EXP-090–092 TRAIN region plus the **EXP-093 already-resolved analysis-TEST
  stratum** (`[int(int(total·0.7)·0.7), int(total·0.7))`), reused as a **portfolio-aggregate disclosure**. The
  portfolio curve and all weights are built **causally** within this window (trailing estimates only).
- **MANDATORY EXCLUSION — the final-30% global holdout `[int(total_rows·0.7), total_rows)` is NEVER loaded,
  sliced, or materialized** (including its 1-minute bars). The global-holdout release is EXP-097 only.
  `holdout_untouched=true` asserted in `run_metadata.json`.
- **No look-ahead:** every portfolio weight, covariance, vol estimate, concurrent-risk cap, and circuit-breaker
  state at curve timestamp *t* uses only per-cell returns resolved **strictly before** *t*. Cross-domain
  alignment by **timestamp** (`CloseTime`), never bar index.

## 5. Frozen parameters (inherited + portfolio model — NO tuning)

**Inherited (frozen as confirmed at G-021):** entry `RSI(2)` 2/10/90; exit **EXIT-RCT**; adverse `2.0×ATR(14)` +
EXP-089 MR-tempo cap; cost = `D0-amendment-003` Phase-021-local conservative round-trip (`F=0`). The per-cell
net return streams are reused verbatim — EXP-095 does **not** re-resolve any exit.

**Portfolio / risk model (frozen, D0 ratified table; brackets are disclosed sensitivity, NEVER selection):**

- **Sizing:** ERC (equal risk contribution), covariance-aware, parameter-free in the weights.
- **Covariance:** trailing rolling **90 trading days**, causal, Ledoit-Wolf shrinkage to the diagonal. Bracket {60, 120}.
- **Rebalance:** **weekly**; weights held between. Bracket {daily, monthly}.
- **Global risk anchor:** scale to **10% annualized vol** (single scalar; Sharpe-invariant — checked). Bracket {7%, 15%}.
- **Concurrent-risk cap:** total open risk-aware (correlation-adjusted) exposure ≤ **1.5×** the rebalance budget. Bracket {1.0×, 2.0×}.
- **Circuit-breaker (Portfolio B):** cell allocation multiplier = **0 while its trailing-50-resolved-trade mean
  net return < 0, else 1** (causal; re-allocates on recovery). Bracket window {30, 100}; halve-not-zero variant disclosed.
- **Inference:** moving-block bootstrap one-sided lower bound on the portfolio metric (`xen.ass` machinery
  extended to the portfolio series; block length = the rebalance cadence). Seeds fixed; master seed `20260624`.

## 6. What EXP-095 computes (analysis-set; no holdout verdict)

```
For Portfolio A (static ERC) and Portfolio B (ERC + circuit-breaker):
  build the causal time-aligned net portfolio return series over the analysis set (D0 §D2)
  annualized Sharpe + moving-block one-sided lower bound; MaxDD, Calmar, ann. return/vol, turnover (co-reported)

Diversification read:
  compare each portfolio's Sharpe lower bound to the best individual deployable cell's annualized Sharpe
  and to the naive equal-weight inverse-vol portfolio (disclosed contrast)

Adaptability read (A vs B):
  the A-minus-B difference in Sharpe / MaxDD; the circuit-breaker de-allocation timeline on the fragile
  cells (USTEC-1h, US2000-1h) — does B de-risk a deteriorating cell that A holds?

Confirmation-statistic calibration (for G-022a; D0 §D6):
  synthetic-null FPR of the portfolio confirmation rule (per-cell returns block-permuted / zero-expectancy,
  covariance + autocorrelation preserved — the null_b_block_permute_returns form, NOT a path rotation)
    -> require FPR <= 0.05 at the realized holdout-equivalent sample size / block structure, for A and B
  bite-check GREEN: a planted-edge vs no-edge two-sample check at the materiality scale separates a real
    portfolio edge from the null and does NOT bite on the null (null NOT built around a signal-derived target)
```

The portfolio metric and the calibration are **descriptive on the analysis set** — no binding deployment verdict
is issued here. The binding deployment read is EXP-097 on the global holdout, under the G-022a-frozen rule.

## 7. Measurable criteria

- **Portfolio benefit (the leg's main read):** at least one of Portfolio A / B has an annualized-Sharpe lower
  bound that **exceeds the best individual deployable cell's annualized-Sharpe point estimate by a material
  margin** (margin reported; the G-022a band is set from this estimate). Reported per portfolio, with the full
  Sharpe/MaxDD/Calmar table and the per-cell baselines.
- **Adaptability (A vs B):** the A−B comparison is reported with the circuit-breaker de-allocation timeline;
  "B de-risks" is supported iff B's MaxDD (or trailing drawdown on the fragile cells) is materially lower than
  A's where a fragile cell deteriorates, at comparable Sharpe. (Descriptive; no pass/fail.)
- **Statistic readiness (gate for G-022a):** the portfolio confirmation rule is **calibrated (synthetic-null
  FPR ≤ 0.05)** and **bite-checked GREEN** for both A and B. A rule that fails FPR control or bites on the null
  is a **REVISE** (the holdout cannot be gated on an uncalibrated statistic).
- **Inconclusive:** the analysis-set portfolio lower bound spans zero / is power-limited at the realized series
  length — disclosed; routes a likely **G-022a HALT** (holdout preserved) rather than a spent shot.
- **Integrity (required regardless):** determinism byte-identical second pass (ERC convex solve + bootstrap +
  any intrabar reuse) on Portfolio A and B; causal-weight assertion (no future per-cell return enters any weight
  at its timestamp); real-price metrics only; `holdout_untouched=true`, `counted_test_reads=0`,
  `candidate_slots=0` asserted in `run_metadata.json`; no stratum tally moves.

## 8. Metric denominators / zero-baseline (defined before implementation)

- **Per-cell return stream:** the resolved EXIT-RCT **net per-event return (ATR units)**, timestamped at the
  event exit `CloseTime`; denominator = resolved events (identical `keep` mask to EXP-092/093). Reused verbatim.
- **Portfolio return series:** net P&L aggregated by timestamp on the **1h common grid** (4h marked-to-market at
  each 1h close), scaled to the 10% vol target. **Annualization factor** fixed by the grid (1h bars/year on the
  instrument's active calendar; recorded). Sharpe denominator = the portfolio return-series standard deviation
  over the analysis window (causal where used in weights; full-window for the reported descriptive Sharpe).
- **No zero-baseline ratio.** The binding figure (for G-022a) is the portfolio metric's **absolute lower bound**
  vs **0** (edge present) and vs the **best-single-cell point estimate** (diversification benefit) — there is no
  percentage-improvement-over-zero metric. A portfolio window with < 2 resolved trades on the trailing grid is
  `INDETERMINATE` for that mark (carries 0 weight; recorded), not forced to a number.
- **Co-reported (non-binding):** MaxDD, Calmar, annualized return/vol, turnover, per-cell Sharpe, weight /
  correlation heatmap, circuit-breaker de-allocation timeline, the naive inverse-vol contrast.

## 9. Complexity budget (D0 §5)

| Item | Budget | EXP-095 plan |
|---|---|---|
| Binding statistical tests | 1 (portfolio risk-adjusted vs single-cell) + the confirmation-statistic calibration | 1 — the portfolio Sharpe/expectancy lower bound vs the best single cell; + the synthetic-null FPR calibration + bite-check (gate readiness for G-022a) |
| Visualisations | ≤ 5 | A/B/best-cell equity curves; weight + correlation heatmap; circuit-breaker de-allocation timeline (fragile cells); A−B drawdown comparison; synthetic-null FPR / bite-check distribution |
| New code modules | 1 | `xen.portfolio` — causal ERC weights from a trailing Ledoit-Wolf covariance, vol-target scaling, concurrent-risk cap, circuit-breaker overlay, timestamp-aligned multi-domain equity-curve aggregation. Reuse the EXP-090/093 per-cell return streams, `xen.ass` (bootstrap), and standard numerical libs (covariance/ERC solve). |

## 10. Discipline (binding)

- **Causal everything.** Weights, covariance, vol, the concurrent-risk cap, and the circuit-breaker use
  past-only information at each curve timestamp. A unit test asserts no future per-cell return enters any weight.
- **No optimization.** Every hyperparameter is frozen at its D0 value; brackets are reported as disclosed
  sensitivity, **never** used to select a binding value. No value is chosen because it lifts the curve.
- **Real-price outcomes only;** HA/brick prices never enter a metric; fills are real touched prices (inherited).
- **No scope expansion after approval:** the noise infusion (EXP-096), the G-022a freeze, and the global-holdout
  release (EXP-097) are separate experiments; the deferred levers (vol-regime, contrarian, 25/75, 15m,
  cross-cuts, tuning, expansion, faster-cost) are each a separate dated `D0-amendment-*` / slot decision.
- **Deviation handling:** a frozen-design confound found mid-stream → dated `D0-amendment-*` + hard-delete +
  full rerun (programme norm), not a silent follow-up. A verdict-material audit finding → fix + re-run before any
  number stands.
- **Per-cell disclosure (LESSON-001):** the portfolio is the deployment estimand, but every per-cell baseline
  and outcome is disclosed alongside the aggregate — no cell-level result is hidden inside the portfolio.

## 11. Out of scope (explicit)

- The final-30% global holdout (sealed; EXP-097 only) and any holdout-release decision.
- The noise / entry-fill model (EXP-096) — EXP-095 is noise-free (idealized at-close entry, as G-021).
- Any re-resolution of the EXIT-RCT exits, or re-tuning of entry/exit/adverse/cost.
- Selecting a binding hyperparameter from its sensitivity bracket (brackets are disclosure only).
- The 3 non-confirming 1h cells; the deferred levers (vol-regime, contrarian, 25/75, 15m, regime×variant
  cross-cuts, parameter tuning, instrument/domain expansion, faster-cost sensitivity).
