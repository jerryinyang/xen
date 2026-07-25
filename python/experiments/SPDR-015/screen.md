# SPDR-015 — screen summary (neutral quantification)

- **Family:** `CF-VOLDIR-001` / **HYP-D2** · **Checkpoint:** 017 · **Lane:** SPDR (TRAIN-only)
- **Role:** conditioner science only — improve gates/labels for 014/016; **not** a standalone trade
- **Question (design §1):** (2a) can next **level-regime** be predicted **better than persistence**?
  (2b) can **next ZZ swing larger than current / last-K median** be predicted (direction-agnostic)?
- **Status:** neutral quantification, **subordinate to `analysis.md`**. No tradability claim. No silent
  rewrite of SPDR-014. Family stays REGISTERED. No XENA.
- **Re-run:** refreshed on QA-approved re-run (`results/` 2026-07-24 06:24). Corrected CI machinery
  (canonical block bootstrap, conservative envelope) + true 200-seed both-arm derangement control.

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: any optional money overlay understates true cost
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

```
O3-SOT: .ignore/what-next/alts/cf-voldir-o3-zone-event-sequence.md
  hard_object: Δ vs persistence mandatory for 2a; R-SHOCK ≠ regime; no money primary
```

**Integrity:** `results/integrity_selfcheck.json` **hard_pass=true** (TRAIN fence, universe pin,
HMM fit end < origin, ZZ confirm ≥ end, Δ Brier emitted, golden G1–G4 pass). Shock rows carry
`is_shock_comparator=true` — never titled regime in artifacts.

**Universe:** top-25 pin asserted. **Clocks:** H1 primary; H4 co-report 2a; D1 stickiness disclosure only.
**Band:** DESIGN origins primary (within TRAIN). Run ~4 min wall; 25 symbols.

---

## 0. Headline (powered cells; DESIGN)

| Arm | Read | Magnitude | Source |
|---|---|---|---|
| **2a** | R-MARKOV stickiness H1 k=1 | **~0.94** (median) | `transition_metrics.parquet` |
| **2a** | R-HMM-RV stickiness H1 k=1 | **~0.98** (median) | same |
| **2a** | **Δ Brier vs persistence** R-MARKOV empirical H1 k=1 | **−0.0038** median (lower=better); **13/16 SUPPORTED** (CI-backed) | same — **2a headline** |
| **2a** | Δ Brier R-MARKOV logistic H1 k=1 | −0.0025 median; **9/16 SUPPORTED** | same |
| **2a** | Δ Brier R-HMM-RV empirical H1 k=1 | **+0.0026** median (worse than stay); **3/15 SUPPORTED** | same |
| **2a** | Δ Brier R-MARKOV empirical H1 **k=12** | **−0.114** median; **16/16 SUPPORTED** | longer-horizon next-state |
| **2a** | State gap HIGH−LOW next \|oo\| bps (level models) | +16.2 (R-MARKOV) / +35.2 (R-HMM-RV) bps H1, all-symbol positive | replication of 012-style gap |
| **2b** | T-GT-CUR ridge_cont hit vs base | **0.68 vs 0.48** (Δhit **+0.21**); **21/21 SUPPORTED** (both CI legs) | `ordinal_metrics.parquet` |
| **2b** | T-GT-CUR continuous rank IC (ridge) | **~0.37** median | same (aligns 013 IC ~0.34–0.46) |
| **2b** | T-GT-MED5 / MED10 ridge | weaker than CUR; MED5 19/21, MED10 12/21 SUPPORTED | same |
| Control | Label derange (both arms, 200-seed) | collapse_frac median **0.0** (2a & 2b); bite plant detected 98%/73% of cells | `controls.json` / `label_derange_collapse.parquet` |
| Control | Feature-shift 2b | illegal-future IC often **inflates**; +1 lag usually drops | `controls.json` |

**Non-compliance avoided:** absolute accuracy (~94–98%) is **not** reported as transition skill.
Headline skill = **Δ vs persistence** only.

---

## 1. Arm 2a — level regime + transition vs persistence

### 1.1 Models (O3 naming)

| Model | Object | Role |
|---|---|---|
| R-MARKOV | HIGH iff `rv20 ≥` trailing median (warm-up window) | slow level baseline |
| R-HMM-RV | 2-state Gaussian HMM on **raw rv20 only** (causal monthly fit) | level-HMM repair |
| R-SHOCK | HIGH iff \|r\| ≥ expanding p90 | **named shock comparator only** |

### 1.2 H1 k=1 powered (n_origins≥80, n_dates≥30) — Δ Brier vs persistence

| model | method | n | median ΔBrier | SUPPORTED | WASH | CONTRADICTED |
|---|---|---:|---:|---:|---:|---:|
| R-MARKOV | empirical_p | 16 | **−0.0038** | 13 | 3 | 0 |
| R-MARKOV | logistic_ridge | 16 | −0.0025 | 9 | 7 | 0 |
| R-HMM-RV | empirical_p | 15 | **+0.0026** | 3 | 12 | 0 |
| R-HMM-RV | logistic_ridge | 15 | +0.0010 | 7 | 8 | 0 |

- SUPPORTED = point ΔBrier<0 AND conservative-envelope `ci_hi<0` (corrected block bootstrap; §3 controls).
- Persistence Brier equals `1 − stickiness` for hard 0/1 stay (golden G2).
- Small negative ΔBrier on R-MARKOV = slight probabilistic improvement over “stay.”
- R-HMM-RV is **stickier** (~0.98) and **does not** beat persistence on the median powered cell.

### 1.3 Longer horizons (H1 empirical R-MARKOV)

| k | median ΔBrier | SUPPORTED / powered |
|---:|---:|---|
| 1 | −0.0038 | 13/16 |
| 4 | −0.0250 | 16/16 |
| 12 | **−0.1138** | 16/16 |

Longer horizons leave more room for switches; Δ vs persistence grows. Still not a trade claim.

### 1.4 H4 co-report (k=1)

Fewer SUPPORTED cells; median ΔBrier for R-MARKOV empirical ≈ **+0.0002** (not better than stay on H4
median; 6/16 SUPPORTED). H1 remains the primary clock for 2a skill claims. (H4 recovers at k≥4:
emp k=12 median −0.145, 15/16 SUPPORTED.)

### 1.5 D1 disclosure

R-MARKOV stickiness median ≈ **0.94** (disclosure only; not a skill claim).

### 1.6 Transitions / run-length

`trans_up` / `trans_dn` counts often **UNPOWERED** (n_trans < 50) — rare switches under sticky
level regimes. Run-length MAE emitted as disclosure (`run_length_metrics.parquet`).

---

## 2. Arm 2b — ordinal ZZ magnitude (H1)

ZigZag ATR 2.0 × ATR(14); features at confirm; predict next swing only.

| target | model | powered n | med hit | med base | Δhit | ΔBrier | med IC | SUP |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| T-GT-CUR | ridge_cont | 21 | **0.683** | 0.475 | **+0.211** | **−0.041** | **0.370** | 21 |
| T-GT-CUR | ar1_threshold | 21 | 0.667 | 0.475 | +0.188 | −0.033 | 0.344 | 21 |
| T-GT-CUR | logit_ridge | 21 | 0.703 | 0.475 | +0.222 | −0.052 | −0.165* | 21 |
| T-GT-MED5 | ridge_cont | 21 | 0.583 | 0.488 | +0.102 | −0.013 | 0.370 | 19 |
| T-GT-MED10 | ridge_cont | 21 | 0.558 | 0.495 | +0.058 | −0.008 | 0.370 | 12 |

\*logit IC vs continuous mag is not the primary calibration path; hit/Brier are.

SUPPORTED = (Δhit≥0.05 AND `hit_ci_lo`>base) OR (ΔBrier<0 AND `Δbrier_ci_hi`<0) — corrected block bootstrap
(blocks 1/3/7, conservative envelope). **T-GT-CUR** is the strongest ordinal gate (21/21 all three models,
both CI legs); MED5/MED10 are weaker and lose cells under the CI. Continuous head IC matches SPDR-013.

---

## 3. Controls (informative)

| Control | Result (summary) |
|---|---|
| PERSISTENCE-ONLY (2a) | Full Δ table mandatory — see §1; absolute accuracy ≠ skill |
| LABEL-SHUFFLE (2a + 2b, 200-seed derangement, zero fixed pts) | collapse_frac median **0.0** both arms (skill survives only live); +0.05 bite plant detected on 98.4% (2a) / 73.0% (2b) of cells |
| FEATURE-SHIFT (2b) | Illegal future IC often ↑; extra lag usually ↓ vs lag-0 |
| T1 target-destroy | Construction HARD: HMM fit_end < origin; ZZ ≤ confirm |

---

## 4. Artifacts

| File | Content |
|---|---|
| `results/regime_states.parquet` | states all models + predictors |
| `results/transition_metrics.parquet` | levels + **Δ vs persistence** + bands |
| `results/zz_ordinal.parquet` | ordinal targets + preds |
| `results/ordinal_metrics.parquet` | hit/Brier/IC |
| `results/golden_traces.json` | G1–G4 |
| `results/integrity_selfcheck.json` | HARD |
| `results/controls.json` + `results/label_derange_collapse.parquet` | 200-seed both-arm derangement collapse + bite; feature-shift |

---

## 5. Screen note (not a disposition)

This screen quantifies conditioner skill only. Operator disposition and **hand-off gate labels**
live in `analysis.md`. Folding anything into SPDR-014 / SPDR-016 requires an **explicit amendment** —
not a silent redesign.
