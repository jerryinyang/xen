# Phase 022 Retrospective — Portfolio Construction, Noise Infusion & Global-Holdout Release (CF-MR-001 batch 3)

> ## ⚠ RETRACTED — REFUTED (2026-06-26): EXIT-RCT exit look-ahead
> **The Phase 022 `DEPLOYABLE_CONFIRMED` outcome below is RETRACTED.** The deployment portfolio and the EXP-097
> global-holdout confirmation inherit the EXP-093 EXIT-RCT one-bar exit look-ahead (`arm_levels` rests
> `rct_target[di]` — bar `di`'s own close — during bar `di`; live-actable is `rct[di-1]`;
> `EXP-090/code/run_experiment.py:305-310`, `mean_reversion.py:174`). Causalized, the bare RSI-2 fade is
> net-negative even gross; exposed by the cTrader port + forward test
> (`XRSI-V1/DIAGNOSIS-real-entry-slippage-omission.md`). **The single global-holdout shot (EXP-097) stays SPENT —
> spent-on-defect, non-refundable; G-022a freeze + G-022 RETRACTED.** **CF-MR-001 CLOSED — REFUTED**;
> EXP-089/G-020 availability stands. Full scope: `docs/experiments-docs/families/cf-mr-001/INDEX.md` §CLOSURE.
> *Text below retained verbatim.*

**Phase:** 022 · **Family:** CF-MR-001 (bare RSI-2 fade, CORE + EXIT-RCT) · **HYP:** `CF-MR-001/HYP-003`
(deployment economics & global-holdout-final confirmation)
**Opened:** 2026-06-24 (G0 RATIFIED, D0 FROZEN) · **Pre-holdout freeze:** 2026-06-25 (G-022a FREEZE) ·
**Closed:** 2026-06-25 at **G-022 — DEPLOYABLE_CONFIRMED** ([`G-022-gate-review.md`](G-022-gate-review.md)).
**One-line outcome:** deployed as a carry-8 causal ERC portfolio with an online circuit-breaker (Portfolio B),
binding-v2 1-minute entry fill, and conservative cost, the bare RSI-2 fade **confirms a positive risk-adjusted
edge on the single sanctioned final-30% global holdout** (B Sharpe LB 4.76 > band 2.00, Calmar LB 10.7) — the
**programme's first deployment-grade price strategy**.

---

## 1. Objectives vs outcomes

| Phase question (design §1) | Outcome |
| --- | --- |
| **Portfolio economics** — does combining the deployable cells into a time-aligned, equal-risk portfolio with cross-instrument correlation beat any single cell on risk-adjusted terms, and can the risk model adapt online to a decaying cell? | **YES.** EXP-095: causal ERC of the 8 cells delivers portfolio Sharpe LB ≫ any single cell (benefit +2.3…+2.6 above the cross-cell-median single-cell LB, beyond the sampling band); Portfolio **B** (ERC + circuit-breaker) measurably de-risks the fragile 1h cells vs static-A. The confirmation statistic was calibrated (synthetic-null FPR ≤ 0.002) with a finite, clearable MDE (m\* = 1.75/2.00). |
| **Fill realism** — does the edge survive a realistic 1-minute entry fill (the one unmodeled G-021 execution gap)? | **YES.** EXP-096: under the binding **v2** next-open+slippage fill all 8 cells stay net-positive (per-cell Sharpe LB > 0, min 0.130 EURJPY-4h); portfolio v2 Sharpe LB A 5.147 / B 4.897 ≫ 0, clearing m\* by +2.9…+3.4. EURJPY-4h flagged `NOISE_DEGRADED` but net-positive → carried (no un-predeclared noise-driven prune). |
| **Deployment-grade OOS-final** — does the finalized, noise-aware portfolio confirm on the final-30% global holdout (the sanctioned one-shot, à la EXP-032)? | **YES.** EXP-097: primary B Sharpe LB **4.762 > 2.00** (+2.76, ≈2.4×), Calmar LB 10.7 > 0, on n=80 fresh holdout weeks → **DEPLOYABLE_CONFIRMED**. |

**Verdict:** objectives met. The honest prior (*the holdout may decay further beyond TRAIN→TEST shrinkage*) was
tested and did **not** materialize at the portfolio level — diversification + the online breaker absorbed the
heterogeneous per-cell decay. The deployment claim is supported OOS-final and the holdout shot is spent.

## 2. The experiment arc (EXP-095 → 098)

| EXP | Role | Reads / slots | Outcome |
| --- | --- | --- | --- |
| EXP-095 | Portfolio construction & online-adaptive risk model (analysis set, noise-free) | 0 / 0 | Built the causal ERC portfolio (static **A** vs circuit-breaker **B**); portfolio beats best single cell; B de-risks decaying cells; confirmation statistic calibrated (FPR ≤ 0.002, MDE m\* = 1.75/2.00). `D0-amendment-001` rerun, re-audit PASS. |
| EXP-096 | Noise infusion — realistic 1-minute entry fill (analysis set) | 0 / 0 | Binding-v2 fill: all 8 cells net-positive; portfolio edge survives, clears m\*; decided the holdout-frozen deployable set = **carry-8**. Audit PASS 0C/0W/5I. |
| **G-022a** | Pre-holdout freeze | — | **FREEZE** — all 4 D0 §D9 preconditions met; froze set (carry-8), construction (binding-v2 ERC + MTM), primary = B, statistic + bands (A 1.75 / B 2.00), read accounting. Holdout NOT loaded. |
| **EXP-097** | **Global-holdout release — one-shot OOS-final** | **1 global-holdout shot / 0 slots** | **`DEPLOYABLE_CONFIRMED`** — B Sharpe LB 4.76 > 2.00, Calmar LB 10.7; 7/8 cells positive-LB; shot spent, non-repeatable. Audit PASS 0C/0W/4I. |
| EXP-098 | Cross-broker & aggregation robustness (PPS, non-binding) | 0 / 0 | **`CROSS_BROKER_ROBUST` ∧ `AGGREGATION_ROBUST`** — both arms confirm on independent PPS data (B Sharpe LB 5.97 / 6.10); 8/8 cells net-positive (incl. EURJPY-4h positive on PPS); EXP-097 verdict unchanged. INFR-003 holdout never loaded. Audit PASS 0C/0W/3I. |

Audits: all PASS, no verdict-material findings. EXP-095 carried one D0-amendment rerun; the binding holdout read
(EXP-097) and the robustness companion (EXP-098) both reproduced their headlines bit-for-bit.

## 3. Lessons learned

1. **The circuit-breaker earned its place exactly where the design predicted.** Pure ERC is expectancy-blind;
   Portfolio B (ERC + online breaker) was chosen primary *pre-holdout* on the analysis-set adaptability argument.
   On the holdout the bet paid: B's Sharpe LB shrank only **−0.135** (4.897 → 4.762) vs A's **−0.897** (5.147 →
   4.250) — the breaker de-allocated the fragile 1h cells during their weak stretches. This is the rare case where
   a deployment guardrail's value was *predeclared* and then *confirmed* on fresh data, not rationalized after.
2. **Diversification absorbed heterogeneous per-cell decay — the portfolio is the right estimand.** Per-cell
   decay was real but offsetting: the 3 strongest 4h cells (EURUSD/XAUUSD/USDCHF) *improved* OOS while the
   JPY-cluster and 1h-index cells decayed. A per-cell-only read would have looked mixed; the portfolio LB was
   near-flat. LESSON-001 (disclose per-cell alongside the binding aggregate) kept both readings honest — including
   that **EURJPY-4h is a confirmed OOS-final loser inside the book**, surviving only by diversification.
3. **Freezing the rule before the holdout (G-022a) is what made the one-shot legitimate.** The statistic, bands
   (= the A4-calibrated m\*), primary (B), and construction were all frozen with the holdout unloaded; the
   realized B LB landed ~2.76 above its band — *in-family* with the analysis-set distribution the band was
   calibrated against (EXP-032 over/under-confirmation lesson), not a regime surprise. No goalpost moved.
4. **High Sharpe is structural, and the audit forced us to say why.** A ~6 Sharpe / ~4.8 LB on a diversified
   8-cell book vol-anchored to 10% is geometry, not a bug — the same construction produced ~4.9 LB on the
   analysis set, and the naive inverse-vol contrast also cleared. Verdict forensics (per-cell masking check +
   mechanism + gate-shape) confirmed no single cell carried the verdict and the gate fit the effect shape.
5. **An independent broker replication is cheap insurance worth taking.** EXP-098 (PPS, both aggregation arms)
   reproduced the confirm on a completely independent feed — and EURJPY-4h, the INFR-003 holdout loser, is
   net-positive on PPS — separating broker-overfit and aggregation-overfit hypotheses that the single INFR-003
   holdout read could not. Non-binding, but it materially de-risks the deployment claim at zero holdout cost.

## 4. Programme state after Phase 022

- **CF-MR-001 is the programme's first DEPLOYABLE price strategy.** Status advanced to
  **`DEPLOYABLE (G-022 DEPLOYABLE_CONFIRMED)`**. The frozen production spec: carry-8 cells (EURUSD/XAUUSD/USDCHF/
  AUDJPY/EURJPY/GBPJPY-4h + USTEC/US2000-1h), bare RSI-2 fade + EXIT-RCT, binding-v2 1-minute entry fill,
  conservative round-trip cost, causal ERC (LW-90d covariance / weekly rebalance / 10% vol anchor / 1.5×
  concurrent-risk cap / intra-1h MTM) + online circuit-breaker (Portfolio B).
- **Reads / holdout:** the **single sanctioned final-30% global-holdout shot is SPENT** (EXP-097); recorded
  outside the analysis-TEST ledger. The 11 carried analysis-TEST strata stay **1/2**, the other 37 stay 0/2.
  **0 counted analysis-TEST reads and 0 candidate slots** consumed in Phase 022 (the portfolio is a deployment
  wrapper, not a new candidate). PPS is now "touched" as a robustness dataset; any future *binding* PPS use needs
  its own governance.
- **File drawer:** Portfolios A and B holdout/PPS outcomes, every guardrail-sensitivity result (v1/v3 fills, the
  covariance-window bracket — all disclosure-only), and every per-cell outcome (incl. EURJPY-4h) are retained.
  The 3 non-confirming 1h cells and all deferred levers remain registered-but-deferred.

## 5. Proposed next direction (each its own checkpoint/D0 — not opened here)

1. **Deployment engineering — EURJPY-4h drop / book-trim re-cost.** EURJPY-4h is a confirmed OOS-final loser
   inside the book; dropping it would have improved the holdout result. A production decision (re-cost, re-size),
   **not** a holdout re-read; its own dated item.
2. **Deferred-lever expansion candidates.** Now that the base fade is deployment-grade, the registered-but-deferred
   levers become expansion candidates, each under its own slot/D0: vol-regime partition, contrarian arm, 25/75
   regime sizing, 15m capture, regime×variant cross-cuts, faster-cost sensitivity, RSI/EMA/ATR/window tuning,
   instrument/domain expansion.
3. **Live/paper deployment readiness.** Translate the frozen spec into the execution stack (cTrader/DWX),
   reconciling the binding-v2 entry-fill model against live fills — an engineering track, not a research gate.

---

*Phase 022 CLOSED at G-022 DEPLOYABLE_CONFIRMED (2026-06-25). Terminal gate review:
[`G-022-gate-review.md`](G-022-gate-review.md). Pre-holdout freeze: [`G-022a-gate-review.md`](G-022a-gate-review.md).
Design: [`design.md`](design.md). D0: [`D0-predeclarations.md`](D0-predeclarations.md) + amendments 001–002.
Experiments: EXP-095/096/097/098.*
