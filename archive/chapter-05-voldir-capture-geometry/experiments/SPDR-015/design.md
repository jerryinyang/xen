# SPDR-015 — Conditioner science: level-regime transitions + ordinal ZZ magnitude (Group 2)

- **Family:** `CF-VOLDIR-001` · **Hypothesis:** `CF-VOLDIR-001/HYP-D2`
- **Checkpoint:** 017
- **Lane:** SPDR TRAIN-only · 0 TEST reads
- **Status:** `SCREEN COMPLETE — WORTH_EXPLORING (per-arm; operator-signed 2026-07-24)` — see `report.md`. Ordinal swing-size gate (T-GT-CUR) + vol level-state labels + R-MARKOV multi-bar gate (k=4/12) route on; k=1 next-bar NOT_WORTH. Fold into 014/016 by amendment only; no family status change; no XENA. QA run1 REVISE→run2 APPROVE; 0 TEST reads.
- **Produces:** (2a) level-regime + **transition skill vs persistence**; (2b) ordinal next-swing size skill
- **Must not:** tradable-edge claim; replace SPDR-014 zone product; shock-as-regime; family status change; mega-merge 014/016

**Role (O3):** improve **gates/labels** for 014/016. **Not** a standalone trade.  
**Schedule (O3 §5):** may run before or after 014; scientifically independent. Fold improved gates into 014 re-run or 016 **only by amendment**.

---

## §A O3 source of truth (100% compliance — binding)

```
O3-SOT:
  path: .ignore/what-next/alts/cf-voldir-o3-zone-event-sequence.md
  role: BINDING substance for Groups 1–3
  conflict_rule: O3 substance > this design. On conflict STOP and amend.
  may_narrow: YES
  may_thin_or_contradict_O3: NO
```

| O3 clause | Design coverage | Obligation |
|---|---|---|
| §2.1 HMM misnamed; refit on rv20/range; shock named | §2 R-HMM-RV, R-SHOCK | Never report R-SHOCK as regime; primary HMM on **level** |
| §2.2 transition skill vs **persistence** | §2.4–2.5 | Absolute accuracy without Δ vs persistence is non-compliant |
| §4 Group 2a + 2b both | §2 and §3 | Both arms mandatory in one screen |
| §4 “not standalone trade” | status; §6 | No money primary; no XENA path from 015 alone |
| §3 proven / non-claims | features | No calendar zoo; no signed product |
| §2.3 AMENDMENT-S1 | §5 | Per-symbol OK |
| §5 fold by amendment | status | No silent rewrite of 014 gates mid-014 without amend |
| §6 refusals | §6 | Mirrored |

---

## §0 Scope fence

| | |
|---|---|
| **Band** | DESIGN `[2021-06-29T06:53Z, 2023-03-01T00:00Z)` primary; CONFIRM `[2023-03-01, 2023-12-18)` verify; TEST/holdout **never** |
| **Universe** | Top-25 pin (U1); recompute assert |
| **Clocks** | **H1 primary**; **H4 co-report** full 2a metrics; D1 optional disclosure for R-MARKOV stickiness only |
| **Money** | No P&L primary. Optional \|move\| bps readability only |
| **Warm-up** | ≥60 H1 (H4: ≥40) complete bars before first scored origin |

```
SPREAD-COST-DISCLOSURE:
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: any optional money overlay understates true cost
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

---

## §1 Question + mechanism

**One question (two arms — O3 Group 2):**  
(2a) After defining states on **vol level** (not single-bar return), can **next regime / transition** be predicted **better than persistence**?  
(2b) Can we predict whether the **next ZigZag swing is larger** than the current (or last-K median) with useful hit rate / calibration — direction-agnostic?

```
MECHANISM:
  2a: True vol regimes are multi-bar level objects (SPDR-012 V-REGIME sticky ~0.93). The prior
      HMM-on-r was a shock detector (O3 §2.1). A level-based HMM/Markov may still be sticky;
      useful transition skill must beat “stay in current state” (O3 §2.2).
  2b: Continuous next-swing magnitude is forecastable (013 IC ~0.34–0.46). Ordinal “bigger than
      now / last-K median” is a more operational gate for zone/event screens (O3 Group 2b).

DERIVED:
  estimand_2a = Δ accuracy / Δ Brier / Δ log-loss vs persistence; run-length MAE; transition lead;
                state-conditional next |oo| gap (replication)
  estimand_2b = hit rate vs base; Brier; rank IC on continuous head; calibration
  null_2a     = persistence; label derangement
  null_2b     = base rate; feature shift +1 swing
  horizon_2a  = t+1 and t+k, k∈{4,12} on H1/H4
  horizon_2b  = next completed ZZ swing
  test        = OOS walk-forward; date-block CIs; collapse under nulls
```

```
OBJECT-IDENTITY:
  measurement object == trading object: N/A primary — forecast-skill objects, not trade episodes.
  measured conditioning event == traded entry event: N/A
  effect-splitting windows non-overlapping: YES — origin t uses data ≤ t; target strictly after t.
```

---

## §2 Arm 2a — Level regime + transitions

### 2.1 State models (all **mandatory**)

| Model ID | Spec | O3 role |
|---|---|---|
| **R-MARKOV** | 2-state: HIGH iff `rv20_t ≥` trailing median of rv20 over warm-up-length window ending at t (SPDR-012 V-REGIME recipe, causal) | Slow level baseline |
| **R-HMM-RV** | 2-state Gaussian HMM on **`rv20` series only** (not on `r`); expanding causal fit on history `< t`; forward filter / Viterbi using obs ≤ t only | Genuine level HMM repair |
| **R-SHOCK** | HIGH iff \|r_t\| ≥ expanding p90 of \|r\| | **Named shock comparator only** |

**Pin:** R-HMM-RV observation = `rv20` (log or raw: **raw rv20**). Parkinson level as sensitivity decode input is **out of first-pass** (amend if needed).  
**Forbidden:** labelling R-SHOCK or SPDR-012 HMM-on-r as “regime success.”

### 2.2 Targets (all mandatory)

| Target | Definition |
|---|---|
| `s_{t+1}` | next-bar state HIGH=1/LOW=0 under each model |
| `s_{t+k}` | k ∈ {4, 12} bars ahead |
| `trans_up` | 1 if exists u∈(t,t+k] with s_u=HIGH and s_t=LOW |
| `trans_dn` | 1 if exists u∈(t,t+k] with s_u=LOW and s_t=HIGH |
| `run_len` | remaining consecutive bars in current state from t+1, censored at 48 |

### 2.3 Predictors (frozen list only — no zoo)

| Feature | Definition |
|---|---|
| `s_t` | current state |
| `dur_t` | bars already spent in current state (capped 48) |
| `rv20_t`, `park_ewma_t` | level features (λ=0.94 Parkinson EWMA) |
| `lvl_pct_t` | expanding percentile of rv20 |
| `n_high_K` | count of HIGH in last K bars, K∈{4,12} |
| `shock_t` | R-SHOCK flag (as feature only) |

### 2.4 Forecast methods (all mandatory for s_{t+1})

| Method | Definition |
|---|---|
| **Persistence** | `P(HIGH_{t+1})=1{s_t=HIGH}` — **mandatory baseline** |
| **Empirical P** | Expanding empirical transition counts → `P(stay)`, `P(switch)` |
| **Logistic-ridge** | Features §2.3 → P(HIGH_{t+1}); monthly walk-forward refit; L2 ridge |

Same methods applied to s_{t+k} with horizon-k labels (separate models).

### 2.5 Metrics (primary = Δ vs persistence)

| Metric | Rule |
|---|---|
| Accuracy, balanced accuracy | report level **and** Δ vs persistence |
| Brier, log-loss | **lower better**; headline = **Δ Brier vs persistence** (negative Δ = better) |
| Transition hit rate | for trans_up/dn vs base rate; UNPOWERED if n_trans < 50 |
| Run-length MAE | predicted E[run_len] vs actual |
| Lead metric | mean bars from first rise in P(switch)>0.5 to actual switch (disclosure) |
| State gap | mean next abs_oo_bps HIGH−LOW (012-style) for R-HMM-RV and R-MARKOV |

```
BANDS 2a (per symbol × clock × model × horizon; labels only):
  SUPPORTED: Δ Brier vs persistence < 0 AND CI high on Δ Brier < 0 (skill)
             on powered cells (n_origins ≥ 80, n_dates ≥ 30)
  WASH: |Δ Brier| small / CI includes 0
  CONTRADICTED: Δ Brier > 0 with CI low > 0 (worse than persistence)
  UNPOWERED: n_origins < 80 OR n_dates < 30 OR (for transition metrics) n_trans < 50
```

**Non-compliance:** publishing “90% accuracy” from persistence stickiness as if it were transition skill.

---

## §3 Arm 2b — Ordinal ZZ magnitude

### 3.1 Structure

| Item | Freeze |
|---|---|
| ZigZag | ATR 2.0 × ATR(14) Wilder, **H1 primary**; M15 co-report optional |
| Features at swing k confirm | magnitude_bps, angle, path_noise, direction, bars_in_swing (013) |
| Lag | features of swing k known at confirmation bar; predict swing k+1 only after k confirmed |

### 3.2 Targets (both mandatory)

| Target ID | Definition |
|---|---|
| **T-GT-CUR** | `1{ mag_{k+1} > mag_k }` |
| **T-GT-MED** | `1{ mag_{k+1} > median(mag_{k-K+1…k}) }` for **K=5** and **K=10** |

### 3.3 Models

| Model | Spec |
|---|---|
| AR1-threshold | AR(1) on continuous mag → compare to current/median threshold |
| Ridge-cont | Ridge on features → continuous mag → ordinal (primary; 013) |
| Logit-ridge | Logistic ridge → ordinal direct (co-report) |

Walk-forward monthly refit; causal expanding/train prefix.

### 3.4 Metrics + bands

| Metric | Definition |
|---|---|
| Hit rate | vs base rate |
| Brier | vs base-rate Brier |
| Rank IC | continuous head vs realised mag_{k+1} |
| Calibration | reliability slope in 5 bins |

```
BANDS 2b (per symbol × target × model):
  SUPPORTED: hit rate ≥ base+0.05 AND CI low > base
             OR Brier < base Brier with CI high(Brier_model - Brier_base) < 0
  WASH / CONTRADICTED / UNPOWERED: n_swings < 80 or n_dates < 30 → UNPOWERED
AMENDMENT-S1 applies
```

---

## §4 Controls + tripwire

```
CONTROL LABEL-SHUFFLE (2a/2b):
  question answered: is reported skill label alignment without structure?
  population: derange targets within symbol × DESIGN third
  DISJOINT: fixed-point-free
  bite/MDE: synthetic +0.05 hit-rate plant must detect
  non-vacuity: destroys y alignment for Brier/hit
  expected if H true: live skill collapses under shuffle
  disclosure: collapse fraction
  destroy form: DERANGEMENT
  class: within_sample_attribution
```

```
CONTROL PERSISTENCE-ONLY (2a):
  question answered: is any model better than stay?
  population: persistence predictions as null benchmark (not a shuffle)
  DISJOINT: N/A (benchmark)
  bite/MDE: models must show Δ Brier separable at n≥80
  non-vacuity: changes probabilistic forecast
  expected if H true: ridge/empirical beat persistence; if false: Δ≈0
  disclosure: full Δ table mandatory in every summary
  class: within_sample_attribution
```

```
CONTROL FEATURE-SHIFT (2b):
  question answered: is ordinal skill causal to swing k features?
  population: use features of swing k+1 (illegal future) vs lag features by +1 swing (past)
  illegal future must inflate skill if leak; causal lag-0 is design; lag+1 should drop skill
  non-vacuity: moves feature timing
  class: within_sample_attribution + leak diagnostic
```

```
TRIPWIRE: TARGET-FUTURE-DESTROY (informative, T1 class)
  derange future state/mag labels; association → 0 for any fixed causal predictor
  residual HARD: construction asserts on fit windows (HMM fit end < origin; ZZ features ≤ confirm)
HARD: TRAIN fence; max target timestamp < train_end; universe pin; HMM fit causality;
  integrity_selfcheck; O3-SOT (shock ≠ regime; Δ vs persistence required)
INFORMATIVE: all skill metrics, bands, controls
```

---

## §5 Power, inference, golden traces, deliverables

```
POWER:
  H1 origins ~ thousands/symbol; transitions rare → UNPOWERED on trans_* common
  ZZ swings: expect hundreds/symbol on H1 TRAIN; if n_swings < 80 → UNPOWERED
```

Inference: date-block bootstrap on origins/swing dates; blocks 1/3/7; multi-seed envelope as 012/013.

```
GOLDEN-TRACE:
  G1 BTCUSDT R-HMM-RV: fit window ends strictly before origin t; state decode matches hand
     forward-filter step on listed series.
  G2 ETHUSDT persistence Brier equals empirical frequency of stay on that cell.
  G3 SOLUSDT T-GT-CUR: two consecutive swings hand mag compare; ridge score from features.
  G4 R-SHOCK: top-decile |r| label equals hand percentile (not titled regime in artifacts).
```

| Artifact | Content |
|---|---|
| `results/regime_states.parquet` | states all models |
| `results/transition_metrics.parquet` | levels + **Δ vs persistence** |
| `results/zz_ordinal.parquet` | targets + preds |
| `results/ordinal_metrics.parquet` | hit/Brier/IC |
| `results/golden_traces.json` / `integrity_selfcheck.json` | HARD |
| `screen.md` / `analysis.md` | conditioner hand-off for 014/016 |

**Handoff fields (for later amendment into 014/016):** recommended gate = R-HMM-RV if SUPPORTED else R-MARKOV; ordinal score T-GT-CUR if SUPPORTED.

---

## §6 Out of scope / O3 §6 refusals

- Zone/event extraction (014)  
- Error-dynamics ML residual stack (016)  
- Trading policies / partial_net primary  
- Treating shock-HMM or R-SHOCK as regime success  
- Claiming transition skill from raw stickiness without Δ persistence  
- Signed direction product; range-break; TEST/holdout; deployability  
- Silent merge into 014 without amendment  
- Family status change; XENA  

---

## §7 Amendments

```
AMENDMENT-S1: per-symbol sufficiency — DIRECTION: NEUTRAL
  running count: 0L / 0T / 1N
```
