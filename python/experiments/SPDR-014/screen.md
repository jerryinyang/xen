# SPDR-014 — Screen summary (neutral quantification; subordinate to analysis.md)

**Family** CF-VOLDIR-001 / HYP-D1 · SPDR TRAIN-only · corrected re-emission · integrity all_pass=true.
This file is a quantification summary only. The binding read is `analysis.md`.

Unit pins: `r_h` = side-signed open-to-open bps. Z-VOL width = LTF H1 Parkinson EWMA(λ=0.94) ×
frozen `s_symbol`. Costs PARTIAL_FEES_FUNDING_ONLY.

```
SPREAD-COST-DISCLOSURE:
  spread_cost_status: UNAVAILABLE_NOT_CHARGED  · spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY  · implication: partial_net overstated vs full cost
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

## Grid / coverage
- 8,450 per-cell rows; 25 symbols pinned, **17 contribute Z-VOL events** (8 have NaN warm-up scale).
- DESIGN/P-NONE/E-TOUCH/H1: 1,425 screen cells → 927 with decided events.
- Multiplicity disclosed; per-stratum table `results/perstratum_final.parquet` + `results/final_magnitudes.json`.

## Magnitudes (neutral)
- **Event rate near-saturated:** p_event 0.998 / 0.985 / 0.938 at z = 1.0 / 1.5 / 2.0 — weakly selective;
  breaches slightly more than uncond-σ band (Δ p_event +0.00…+0.17).
- **Primary cell** (Z-VOL z1.5 H12 h12, pooled n=2,964): mean `r_h` **+11.3 bps** (block-CI [−3.3, +26.7]),
  median +4.6, **p_momo 0.499** (CI 0.481–0.517).
- **Rate lean pooled** (all Z-VOL, n=79,659): p_momo **0.478** (CI 0.475–0.482) — a −2.2-pt tilt below 0.50,
  a slight **MR** lean (SUGGESTIVE, rate-only). Not MOMO.
- **Per-symbol vs corrected nulls (primary cell):** 0/17 symbols clear the 0.95 percentile on time-shuffle
  or matched-random; range 0.24–0.93 (DOGE 0.93 near-miss).
- **Last-k state-sequence conditioner (AMENDMENT-S2, ordered k=1..3):** order matters — a fresh low→high
  vol flip on the decision bar (`LH`/`LLH`) leans MOMO (p_momo ~0.55, median **+40 bps**); the reverse
  (`LHL`) leans MR; persistent `HHH`/`LLL` flat; k=1 alone flat. UNPOWERED (n 33–210). (A bare HIGH-count
  hides this — see analysis §7.1.)
- **Other conditioners:** mag_high +20.3 bps, shock +39.9 bps mean `r_h` (magnitude scaling; p_momo ≈ 0.50,
  no direction); vol tercile / slow regime flat.
- **DESIGN→CONFIRM:** primary mean +11.3 → −4.3 (sign flip); **E-CLOSE** p_momo 0.458 (MR tilt); not stable.
- **Money (disclosure):** all policies negative net; Z-VOL gross ≈ 0 (P-MOMO +0.08, P-MR −1.09). Straddle −29.8.

## Power (binding)
- **0 powered residual cells** of 927 (rule: n_events≥80 & n_dates≥30 & MDE≤10 bps).
- MDE bps min/p10/median = 20.0 / 47.1 / 171.8; median n_events 12. A ±5 bps object is invisible here.

## Disposition (recommended — NON-FINAL; operator decides)
- **INCONCLUSIVE — reason class UNPOWERED_NOT_NULL.** Residual object not established and not refuted
  (precision ceiling, B-5). Continuation rate is a coin-flip / slight MR lean; positive primary mean does
  not reproduce out-of-band. New ordered last-k facet (§7.1) shows an order-conditional vol-flip lean
  (L→H → MOMO ~+40 bps median), UNPOWERED — a lead for a powered follow-up, not a finding here.
- **016 stays CLOSED** — `016_start_allowed=false` (0 powered cells). Pin `residual_status` corrected
  from mechanical `MOMO_DOMINANT` → **NONE**; `policy_for_016=NONE`. Operator override needs a signed freeze.
- No tradability/deployability claim. No family status change.
