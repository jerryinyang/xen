# Results: EXP-097 — Global-Holdout Release (RSI-2 Fade Deployment Portfolio)

**Family / HYP:** `CF-MR-001` / `HYP-003` · **Phase:** 022 (batch 3) · **Date:** 2026-06-25
**Role:** the single sanctioned global-holdout release (OOS-final deployment confirmation, à la EXP-032) ·
**Audit:** PASS (0 Critical, 0 Warning) · **Read accounting:** 1 holdout-governance event; 0 counted analysis-TEST
reads; 0 candidate slots; non-repeatable / non-upgradable.

> The verdict is mechanical against the **pre-frozen** G-022 rubric (set, construction, primary B, bands A 1.75 /
> B 2.00, rule). Nothing below re-derives or re-tunes anything; this is the realized read of the frozen rule on the
> final-30% global holdout, loaded for the first time.

---

## 1. Headline

**G-022 = `DEPLOYABLE_CONFIRMED`.** The primary **Portfolio B** confirms on the fully-fresh holdout:

| Portfolio | ann Sharpe (pt) | **Sharpe LB (binding)** | band | Calmar LB | CONFIRM | role |
|-----------|----:|----:|----:|----:|:--:|------|
| **B** (ERC + breaker) | 6.639 | **4.762** | **2.00** | 10.731 | **YES** | **primary / binding** |
| A (static ERC) | 6.055 | 4.250 | 1.75 | 8.296 | YES | co-adjudicated, disclosed |
| naive inverse-vol | 6.030 | 4.261 | — | 8.351 | — | non-binding contrast |

The binding leg (B Sharpe LB 4.762) clears its band by **+2.76** (a 2.4× margin), and the co-binding downside leg
(Calmar LB 10.731 > 0) holds comfortably. n = 80 holdout weeks (final 30% per file, boundary 2024-12-13 →
2026-06-19). The audit re-derived the point statistics bit-for-bit from the saved return series.

**Consequence (pre-registered):** the bare RSI-2 fade, deployed as the G-022a-frozen carry-8 causal ERC portfolio
with circuit breaker and binding-v2 entry fill under conservative round-trip cost, is the programme's **first
deployment-grade price strategy**. The frozen spec is the production deployment.

---

## 2. Verdict against the pre-registered interpretation guide

| Outcome | Condition (primary B) | Realized? |
|---|---|:--:|
| **DEPLOYABLE_CONFIRMED** | Sharpe LB(B) > 2.00 AND Calmar LB(B) > 0 | **✔ 4.762 > 2.00 and 10.731 > 0** |
| DECAYED / NOT_CONFIRMED | Sharpe pt(B) ≤ 2.00 OR Sharpe LB(B) ≤ 0 | ✘ (pt 6.639, LB 4.762) |
| INCONCLUSIVE | neither | ✘ |

A's confirm status is **co-reported, not promoting** (no OR): even with A failing, B alone adjudicates; here both
confirm, which is concordant but immaterial to the terminal state.

---

## 3. Why it confirmed — mechanism (not just "the number cleared")

**(a) The Sharpe magnitude (~6.6) is structural, not anomalous.** The binding estimand is a *diversified* ERC book
of 8 weakly-correlated cells, vol-anchored to 10%. Single-cell net expectancies are 0.03–0.13 ATR; diversification
lifts the portfolio's risk-adjusted return well above any cell. The identical construction produced Sharpe ≈ 6 /
LB ≈ 4.9 on the analysis set, and the bands (m\*) were calibrated against *this* construction — the holdout number
is in-family with what the band anticipated. Realized holdout vol is 11.4% (the 10% anchor is respected).

**(b) The portfolio did not decay, because decay was heterogeneous and offsetting.** The honest prior expected
uniform TRAIN→TEST shrinkage (G-021 Δ net_ci_low −0.005…−0.107; EXP-096 v2 fill ≈ halving). What actually occurred:

| Cell | analysis-v2 → holdout Δ net mean (ATR) | holdout net ci_low | OOS-final read |
|------|----:|----:|------|
| EURUSD-4h | **+0.033** | +0.104 | improved |
| XAUUSD-4h | **+0.031** | +0.082 | improved |
| USDCHF-4h | +0.015 | +0.066 | improved |
| GBPJPY-4h | −0.0003 | +0.017 | flat |
| US2000-1h | −0.005 | +0.037 | flat |
| AUDJPY-4h | −0.009 | +0.040 | flat |
| USTEC-1h | −0.021 | +0.014 | decayed, still positive |
| EURJPY-4h | −0.034 | **−0.031** | **net-negative (pre-flagged)** |

The three strongest 4h FX/commodity cells *improved* OOS-final; the JPY crosses and 1h index cells decayed modestly;
the gainers offset the decayers, so the portfolio Sharpe LB moved only **−0.135** (B: 4.897 → 4.762).

**(c) The circuit breaker is why B beat A (and why B was the right primary).** Portfolio A absorbed the full decay
of the weak 1h cells (A LB 5.147 → 4.250, Δ −0.897); B's trailing-50-trade breaker de-allocated the fragile cells
(USTEC/US2000) during their weak stretches — its designed tail-insurance role — landing higher (LB 4.762) and
shrinking by only −0.135. The breaker delivered exactly the protection the programme made it primary for.

---

## 4. Masking / per-cell disclosure (LESSON-001)

The verdict is **broad-based, not masking heterogeneity**: 7 of 8 cells carry a *positive* one-sided lower bound on
the holdout. The single net-negative cell, **EURJPY-4h**, is precisely the cell pre-flagged `NOISE_DEGRADED` at
G-022a (EXP-096 v2 ci_low 0.0079) and carried under portfolio-only membership; it is the *smallest* positive
contributor (sum_marks 37.9 vs EURUSD 224.9, US2000 461.0), so removing it would **improve**, not rescue, the
portfolio. No healthy verdict is propped up by one cell; no broken cell is hidden in the aggregate. EURJPY breaking
OOS-final is disclosed, was anticipated, and is **not** re-adjudicated (frozen-set discipline).

---

## 5. Integrity

| Check | Result |
|---|---|
| MTM conservation Σ(marks)=realized net per cell | PASS, ≤ 2.8e-14 ATR (8/8 cells) |
| Determinism (full second pass A/B byte-identical) | PASS |
| Binding-statistic re-seed identity | PASS |
| Causal-weight assertion (perturb after a **holdout** rebalance) | PASS (row 37632, in holdout) |
| Causal-fill assertion (perturb pre-signal 1m bar of a **holdout** event) | PASS (event 1467, signal in holdout) |
| Real-price discipline (real domain & 1m OHLC; no HA/Renko) | PASS |
| Holdout-region honesty (binding metric on epoch ≥ H_global only) | PASS (30.04% of grid; transition zone excluded) |
| Headline reproduced from saved series (audit spot-check) | PASS to 4 dp |

---

## 6. Caveats (from audit + scope)

- **One shot, spent.** This is the single sanctioned global-holdout read; **non-repeatable, non-upgradable**
  (EXP-032 precedent). Any confound discovered hereafter is a permanent caveat, not a re-read.
- **EURJPY-4h is a confirmed OOS-final loser** within the deployed book; it survives only by diversification. A
  production deployment may legitimately drop it (it improves the book) — but that is a *new* post-G-022 decision
  with its own slot/D0, not part of this frozen read.
- **The high Sharpe is a diversified-portfolio statistic**, not a single-instrument edge; deployment realism rests
  on the ERC/vol-target/breaker machinery and the conservative cost model (`F=0` round-trip), all frozen here.
- **n = 80 weeks** of holdout; the LB already prices in this sample size via the moving-block bootstrap (the band is
  cleared by 2.4×, so the one-week n discrepancy vs the m\* calibration is immaterial).

---

## 7. Follow-ups (new scopes only — not extensions)

These are recorded as candidate post-G-022 expansion items (each its own dated `D0-amendment-*` + slot decision per
scope §11); none modifies this frozen read:

1. **EURJPY-4h drop / book-trim decision** — re-cost the deployed book with the confirmed OOS-final loser removed
   (a deployment-engineering decision, not a re-read of the holdout).
2. **Deferred levers** — vol-regime, contrarian, 25/75 sizing, 15m domain, regime×variant cross-cuts, faster-cost
   models, instrument/domain expansion (all deferred at scope §11).

---

## 8. One-line summary

The G-022a-frozen RSI-2 fade ERC portfolio **confirms on the global holdout** (B Sharpe LB 4.76 > band 2.00, Calmar
LB 10.7); per-cell decay was real but heterogeneous and offset by diversification + the circuit breaker — making the
fade the programme's first deployment-grade price strategy.
