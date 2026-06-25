# EXP-097 — Global-Holdout Release: One-Shot OOS-Final Confirmation of the RSI-2 Fade Deployment Portfolio

**Family / HYP:** `CF-MR-001` / `HYP-003` · **Phase:** 022 (batch 3) · **Date:** 2026-06-25
**Status:** `DEPLOYABLE_CONFIRMED` · **Audit:** PASS (0 Critical, 0 Warning, 4 Info) ·
**Governance:** pre-exec APPROVE; post-exec APPROVE
**Role:** the single sanctioned final-30% global-holdout release (deployment OOS-final, à la EXP-032) —
**non-repeatable, non-upgradable**.

---

## 1. Research question

Deployed as the G-022a-frozen, noise-aware (binding v2 entry fill) causal ERC portfolio with intra-1h
mark-to-market, does the confirmed RSI-2 fade confirm a positive risk-adjusted edge on the fully-fresh final-30%
global holdout — i.e. does the primary **Portfolio B** holdout annualized-Sharpe lower bound exceed its predeclared
band (2.00) with the co-binding Calmar lower bound > 0?

This is the binding deployment leg of `HYP-003` and the programme's **first new-dataset global-holdout shot**.

## 2. Scope & exclusions

- **Frozen by G-022a — nothing re-derived:** deployable set = **carry-8** (EURUSD/XAUUSD/USDCHF/AUDJPY/EURJPY/
  GBPJPY-4h + USTEC/US2000-1h); construction = binding-v2 ERC + intra-1h MTM (LW-90d covariance, weekly rebalance,
  10% vol anchor, 1.5× concurrent-risk cap, trailing-50 circuit breaker); primary = **B**; bands A 1.75 / B 2.00
  (= inherited A4 m\*); rule CONFIRM(P) iff Sharpe_LB(P) > band_P AND Calmar_LB(P) > 0; master seed 20260624.
- **The binding slice:** the final-30% global holdout per file, loaded **for the first time**. The analysis set is
  loaded as **past-only causal warmup** (EXP-093 pattern); the binding metric is restricted to the holdout region
  `grid_epoch ≥ H` (H = max per-cell cutoff = 2024-12-13), excluding the ~2-day transition zone.
- **Out of scope:** any re-derivation/re-tuning/re-selection; the v1/v3 fill variants and the covariance-window
  bracket (EXP-096 ladder); the deferred levers; any second holdout read or verdict upgrade.

## 3. Method summary

Reuse the EXP-095/096 machinery verbatim (`E96.resolve_cell_noise` v2 stream, `E95.build_grid`/
`series_risk_metrics`, `pf.build_portfolio`); the only new code is the full-file holdout loader + the `≥H`
holdout-region metric extraction in orchestration. Build the causal ERC portfolio (A static, B breaker)
continuously over warmup+holdout with past-only weights; compute the binding Sharpe/Calmar one-sided lower bounds
(weekly-aggregated, moving-block bootstrap, N_BOOT=10,000, α=0.10) on the holdout region; adjudicate G-022 off the
primary B. Disclose A, per-cell holdout net, analysis→holdout shrinkage, and integrity assertions.

## 4. Key results (n = 80 holdout weeks; final 30% per file, 2024-12-13 → 2026-06-19)

| Portfolio | ann Sharpe | **Sharpe LB (binding)** | band | Calmar LB | MaxDD | ann vol | CONFIRM |
|-----------|----:|----:|----:|----:|----:|----:|:--:|
| **B** (ERC + breaker, primary) | 6.639 | **4.762** | **2.00** | 10.731 | 0.046 | 0.114 | **YES** |
| A (static ERC, disclosed) | 6.055 | 4.250 | 1.75 | 8.296 | 0.047 | 0.115 | YES |
| naive inverse-vol (contrast) | 6.030 | 4.261 | — | 8.351 | 0.045 | 0.110 | — |

**Verdict: `DEPLOYABLE_CONFIRMED`** — B clears its band by +2.76 (2.4×), Calmar LB 10.7 > 0.

**Per-cell holdout net (ATR units), masking check:** 7 of 8 cells carry a positive one-sided lower bound (verdict
broad-based, not one-cell-driven). The single net-negative cell, **EURJPY-4h** (net mean −0.006, ci_low −0.031),
is exactly the cell pre-flagged `NOISE_DEGRADED` at G-022a; it is the smallest positive contributor, so dropping it
would *improve* the book. No broken cell hidden in the aggregate.

| Cell | n events | net mean | net ci_low | analysis-v2 → holdout Δ mean |
|------|----:|----:|----:|----:|
| EURUSD-4h | 616 | +0.132 | +0.104 | +0.033 (improved) |
| XAUUSD-4h | 583 | +0.115 | +0.082 | +0.031 (improved) |
| USDCHF-4h | 598 | +0.095 | +0.066 | +0.015 (improved) |
| AUDJPY-4h | 614 | +0.064 | +0.040 | −0.009 |
| GBPJPY-4h | 581 | +0.046 | +0.017 | −0.0003 |
| US2000-1h | 2423 | +0.055 | +0.037 | −0.005 |
| USTEC-1h | 2536 | +0.033 | +0.014 | −0.021 |
| EURJPY-4h | 627 | −0.006 | −0.031 | −0.034 (net-negative, pre-flagged) |

**Shrinkage:** portfolio Sharpe LB shrank only **−0.135** for B (4.897 → 4.762) vs **−0.897** for A (5.147 →
4.250). The decay was heterogeneous (3 strongest 4h cells improved OOS; JPY/index cells decayed), and the
circuit breaker — by de-allocating the fragile 1h cells during their weak stretches — is why B both lands higher
and shrank far less. This is the mechanism behind the primary verdict and the reason B (not A) is primary.

## 5. Mechanism (why it confirmed)

1. **High Sharpe is structural, not a bug:** a diversified ERC book of 8 weakly-correlated cells, vol-anchored to
   10%; the same construction produced Sharpe ≈ 6 / LB ≈ 4.9 on the analysis set, and the bands were the m\*
   calibrated against it. The holdout number is in-family with the pre-frozen band.
2. **No portfolio decay:** heterogeneous per-cell decay (gainers offset decayers) + the breaker → near-flat
   portfolio LB.
3. **Gate matches the effect shape:** Sharpe LB (risk-adjusted location) + Calmar LB (downside) fit a positive-mean
   diversified stream; no tail/bimodal structure the gate would miss.

## 6. Integrity & audit caveats

- MTM conservation ≤ 2.8e-14 ATR (8/8); determinism byte-identical (A/B); binding-statistic re-seed identity;
  causal-weight + causal-fill assertions both exercised **in the holdout region** and PASS; real-price only;
  headline re-derived bit-for-bit from the saved return series (audit spot-check).
- **One shot, spent.** `global_holdout_shot_spent=true`, `holdout_first_touch=EXP-097`, `counted_test_reads=0`,
  `candidate_slots=0`. Non-repeatable, non-upgradable; any later confound is a permanent caveat, not a re-read.
- **EURJPY-4h is a confirmed OOS-final loser** within the book, surviving only by diversification; a production
  decision to drop it is a *new* post-G-022 item, not part of this frozen read.

## 7. Conclusion

**`DEPLOYABLE_CONFIRMED`.** The G-022a-frozen RSI-2 fade ERC portfolio confirms on the global holdout (B Sharpe LB
4.76 > band 2.00, Calmar LB 10.7). The bare RSI-2 fade, deployed as the carry-8 causal ERC portfolio with circuit
breaker and binding-v2 entry fill under conservative round-trip cost, is the **programme's first deployment-grade
price strategy**; the frozen spec is the production deployment.

## 8. Signal-registry disposition (registry-relevant)

Recorded in the same change as this result:

- `test-read-ledger.md` — the **single sanctioned global-holdout-governance event** entered (EXP-097); outside the
  analysis-TEST 48-stratum ledger; the 11 carried strata stay 1/2, the other 37 stay 0/2; `counted_test_reads=0`.
- `multiplicity-registry.md` — EXP-097 row marked SPENT/CONFIRMED (holdout shot consumed; non-repeatable).
- `candidate-families/cf-mr-001.md` — status advanced to **`DEPLOYABLE (G-022 DEPLOYABLE_CONFIRMED)`**.

## 9. Follow-ups (new scopes only — each its own dated `D0-amendment-*` + slot decision)

1. EURJPY-4h drop / book-trim re-cost (deployment engineering, not a holdout re-read).
2. Deferred levers: vol-regime, contrarian, 25/75 sizing, 15m domain, regime×variant cross-cuts, faster-cost,
   instrument/domain expansion.

## 10. Artifacts

- Code: [`code/run_experiment.py`](code/run_experiment.py)
- Results: [`results/`](results/) (verdict.json, holdout_metrics.csv, per_cell_holdout.csv, holdout_boundary.json,
  shrinkage.json, mtm_conservation.csv, portfolio_returns_A/B.csv, run_metadata.json)
- Plots: [`plots/holdout_equity_curves.png`](plots/holdout_equity_curves.png),
  [`plots/holdout_metric_vs_band.png`](plots/holdout_metric_vs_band.png),
  [`plots/per_cell_holdout_net.png`](plots/per_cell_holdout_net.png),
  [`plots/holdout_drawdown_A_vs_B.png`](plots/holdout_drawdown_A_vs_B.png),
  [`plots/holdout_circuit_breaker_timeline.png`](plots/holdout_circuit_breaker_timeline.png)
- [`scope.md`](scope.md) · [`analysis-plan.md`](analysis-plan.md) · [`audit.md`](audit.md) ·
  [`results.md`](results.md) · [`governance/`](governance/)
