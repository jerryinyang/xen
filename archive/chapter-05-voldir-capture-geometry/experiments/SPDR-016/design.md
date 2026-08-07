# SPDR-016 — Error-dynamics residual model → zone/event refine (Group 3)

- **Family:** `CF-VOLDIR-001` · **Hypothesis:** `CF-VOLDIR-001/HYP-D3`
- **Checkpoint:** 017
- **Lane:** SPDR TRAIN-only · 0 TEST reads
- **Status:** `DESIGN COMPLETE — START-GATED ON SPDR-014 RESIDUAL; EXECUTION UNAUTHORISED`
- **Produces:** light walk-forward residual model (proven + error dynamics + weak direction as features only); **same** zone/event characterisation stack as SPDR-014; Δ vs 014 baseline
- **Must not:** run without 014 residual pin; open ML zoo; treat SMA/ZZ as proven direction product; skip characterisation; tradability/XENA/family status claims

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
| §4 Group 3 rule: only after named 014 residual | §B start gate | HARD: no pin / residual NONE → do not run |
| §4 same event stack as Group 1 | §3–§4 | Import 014 event definitions; no silent redefine |
| §4 balance proven / derived / new | §2 layered features | Ablation required; weak dir not sole load-bearing |
| §4 direction-aware = zone side × post-breach behaviour | §4 P-RESIDUAL | Not “SMA tells side” |
| §3 proven ingredients | §2.1 | Always-on core |
| §5 if 014 no residual → 016 not opened | §B | Terminal extraction path |
| §2.3 AMENDMENT-S1 | §5 | Per-symbol OK |
| §6 refusals | §7 | Mirrored |

---

## §B Start gate (HARD — O3 §5)

Before any train/predict/money:

1. Load `python/experiments/SPDR-014/results/014_residual_pin.json` (or operator-signed copy under this exp `results/014_residual_pin.json`).  
2. Require `016_start_allowed == true` **or** operator override field `operator_force_start: true` with written residual_status ∈ {MOMO_DOMINANT, MR_DOMINANT, SPLIT}.  
3. If `residual_status == NONE` and no force → **exit 0 with SKIP artifact**; do not emit model OOS as a run.  
4. Pin schema must include `primary_cells` and `policy_for_016` ∈ {P-MR, P-MOMO}.

```
START-GATE-FAIL = integrity failure for any 016 “success” narrative without pin.
```

---

## §0 Scope fence

| | |
|---|---|
| **Band** | DESIGN `[2021-06-29T06:53Z, 2023-03-01T00:00Z)` primary; CONFIRM `[2023-03-01, 2023-12-18)` verify; TEST/holdout **never** |
| **Universe** | Top-25 (U1); recompute assert; AMENDMENT-S1 |
| **Clock** | H1 primary (match 014) |
| **Event stack** | **Byte-for-byte same rules as SPDR-014 design §2–§4** for primary pin cells (source, z, H, event, h). Re-implement or import library; golden-diff event timestamps on pin cells must match 014 emission |
| **015 inputs** | Optional: only if 015 analysis complete; else omit features |

```
SPREAD-COST-DISCLOSURE:
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: partial_net overstated vs full cost
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

---

## §1 Question + mechanism

**One question (O3 Group 3):**  
Given SPDR-014’s **named** zone/event residual, does a **small frozen** model using (i) proven vol/mag, (ii) signed predicted−actual error and acceleration, (iii) vol acceleration, (iv) weak direction features **as inputs only**, improve post-event residual or event filter quality **vs the 014 baseline** — without reopening signed SMA/ZZ as a product?

```
MECHANISM:
  014 defines mispricing events relative to a magnitude forecast. Forecast errors and the speed
  of vol/error change may refine when the zone is wrong and which residual (MOMO/MR) dominates.
  Failed sign models may carry weak state as features, not as standalone direction products.
  Evaluation object remains the 014 event stack / residual policy — not classification accuracy alone.
  Direction-aware side = zone breach side × pinned residual policy (O3), never “SMA tells side.”

DERIVED:
  estimand = Δ mean/median post-event r_h vs 014 baseline; optional Δ partial_net under P-RESIDUAL
  null     = 014 baseline; feature-shuffle; ablation of feature layers
  horizon  = pinned H/h from 014_residual_pin primary cells
  test     = walk-forward model; collapse under shuffles; mean+median money
```

```
OBJECT-IDENTITY:
  measurement object == trading object: YES for money cells —
    entry at 014 breach entry open; side = breach_side * residual_sign
    (residual_sign = +1 for P-MOMO, −1 for P-MR relative to breach);
    exit per 014 §5 h/stop.
  measured conditioning event == traded entry event: YES — same breach event as 014.
  effect-splitting windows non-overlapping: YES.
```

---

## §2 Feature set (frozen — O3 balance layers)

### 2.1 Layer PROVEN (always on)

| Feature | Source / definition |
|---|---|
| `ewma_park`, `lvl_pct` | Parkinson EWMA λ=0.94 + expanding pct (012 Keep) |
| `zz_mag_hat` | Ridge next-swing mag (013) |
| `slow_reg` | Markov rv20 HIGH/LOW (012 V-REGIME) |
| `shock` | top-decile \|r\| **named shock** (not regime) |
| Optional `hmm_rv`, `ord_gt_cur` | 015 outputs only if present |

### 2.2 Layer DERIVED — error dynamics (Group 3 core)

All causal at decision t (zone origin or event origin as pinned — default **zone decision t** for filter; event-time features for residual head):

| Feature | Definition |
|---|---|
| `err_abs` | `σ_bps_pred − abs_oo_realised` over last completed horizon H\* (**H\*=12** primary; H\* matches pin H when possible) |
| `err_signed` | signed path residual last window: `1e4*(close_midpath/centre − 1)` vs band (use last completed zone window) |
| `Δerr` | `err_abs_t − err_abs_{t−1}` |
| `Δvol` | `ewma_park_t − ewma_park_{t−1}` |
| `err_z` | `err_abs / max(ewma_park, ε)` |

### 2.3 Layer WEAK-DIR (inputs only — not product)

| Feature | Definition |
|---|---|
| `sma25_sign` | +1 if C>SMA25 else −1 (013) |
| `sma25_angle_on` | 013 angle filter binary |
| `zz_next_leg_sign` | constructive next-leg sign (013) |

**Forbidden:** any policy that enters solely from WEAK-DIR without zone breach event.

### 2.4 Model class (O3: one light primary + one sensitivity)

| Model | Spec |
|---|---|
| **M-RIDGE** | Ridge (regression on r_h) or logistic (on MOMO/MR label per pin) — monthly walk-forward — **primary** |
| **M-GBM** | max_depth≤3, n_estimators≤100, min_samples_leaf≥50 — **sensitivity only** |

No architecture search, no deep nets, no AutoML, no feature hunt beyond §2.

### 2.5 Ablation schedule (mandatory — O3 balance)

| Ablation ID | Features |
|---|---|
| A0 | PROVEN only |
| A1 | PROVEN + DERIVED |
| A2 | PROVEN + DERIVED + WEAK-DIR (**full**) |

Every result table reports A0/A1/A2. If A2 wins only via WEAK-DIR (A1≈A0 and A2≫A1), disclose **WEAK-DIR load-bearing** — not silent direction product revival.

---

## §3 Targets (tied to 014 pin)

| If pin `policy_for_016` / residual_status | Primary target |
|---|---|
| MR_DOMINANT / P-MR | realised post-event `r_h` under fade orientation **or** P(MR) logistic |
| MOMO_DOMINANT / P-MOMO | `r_h` under continuation **or** P(MOMO) |
| SPLIT | per `primary_cells[]` stratum-specific target listed in pin |

Secondary disclosure: P(breach) calibration improvement under score filter.

---

## §4 Evaluation stack (same language as 014)

1. **Baseline cell(s):** from `014_residual_pin.primary_cells` (must recompute 014 metrics and match within 1e-6 on shared keys).  
2. **Model score** at t →  
   - **Filter:** trade/characterise event only if score ≥ τ (τ = DESIGN tertile cut frozen on DESIGN only; not tuned on CONFIRM), **or**  
   - **Adaptive z:** not in first-pass (amend if needed).  
3. Report on filtered set: p_event, p_momo, p_mr, mean/median r_h, **Δ vs baseline**.  
4. **Money P-RESIDUAL:** side from pin policy; costs = 014 (fee 11 + funding + allowance 2); mean **and** median partial_net; Δ vs 014 money on same pin cells.

```
BANDS (per symbol × ablation × model; labels never gates):
  SUPPORTED vs baseline:
    mean residual Δ (model − 014 baseline) ≥ +5 bps
    AND CI low > 0 AND median Δ ≥ 0
    AND ≥2/3 DESIGN thirds same sign
  WASH: |Δ| < 5 or fails vs baseline
  CONTRADICTED: Δ ≤ −5 and CI high < 0
  UNPOWERED: n_events < 80 or n_dates < 30 or MDE > 10
AMENDMENT-S1: multi-symbol not required
POOLED: disclosure-only
```

---

## §5 Controls + tripwire

```
CONTROL FEATURE-SHUFFLE:
  question answered: is model skill feature alignment?
  population: derange feature rows within symbol×third; keep y
  DISJOINT: derangement
  bite/MDE: +20 bps plant
  non-vacuity: destroys X–y link
  expected if H true: OOS skill collapses
  disclosure: collapse fraction
  destroy form: DERANGEMENT
  class: within_sample_attribution
```

```
CONTROL ABLATION (A0/A1/A2):
  question answered: which O3 layer carries the lift?
  population: nested feature sets §2.5
  DISJOINT: N/A (nested models)
  bite/MDE: material Δ between layers detectable at n≥80
  non-vacuity: changes feature span
  expected if H true: A1≥A0; A2 not sole via WEAK-DIR without disclosure
  disclosure: full layer Δ table mandatory
  class: within_sample_attribution
```

```
CONTROL 014-BASELINE:
  question answered: does 016 beat the named residual cell?
  population: pinned 014 metrics
  every table shows Δ vs pin
  class: within_sample_attribution
```

```
TRIPWIRE: PATH-FUTURE-DESTROY (informative T1 class)
  residual HARD applicability on positive money cells
HARD: start gate; TRAIN fence; causal fits; event parity with 014 pin cells;
  universe pin; integrity_selfcheck; O3-SOT (no SMA-only policy)
INFORMATIVE: all skill/money/bands/controls
```

---

## §6 Power, inference, golden traces, deliverables

```
POWER: event counts inherit 014 pin cells; filtering by τ reduces n → more UNPOWERED
  predeclare: high τ → UNPOWERED not negative
```

Inference: same date-block bootstrap as 014 on event dates.

```
GOLDEN-TRACE:
  G1 BTCUSDT err_abs for one H*=12 completed window matches hand σ_pred − abs_oo
  G2 ETHUSDT design matrix at listed origin → M-RIDGE score matches refit
  G3 SOLUSDT P-RESIDUAL episode: breach side × pin policy → partial_net vs 014 formula
  G4 Event parity: 014 pin cell event timestamps equal 016 recompute (0 mismatches)
```

| Artifact | Content |
|---|---|
| `results/014_residual_pin.json` | input pin (copy) |
| `results/features.parquet` | layered features + ablation id |
| `results/model_oos.parquet` | scores, τ filter flags |
| `results/vs_014_baseline.parquet` | Δ tables A0/A1/A2 |
| `results/expectancy_by_cell.parquet` | money mean/median |
| `results/golden_traces.json` / `integrity_selfcheck.json` | HARD |
| `screen.md` / `analysis.md` | binding refine read |

---

## §7 Out of scope / O3 §6 refusals

- Running without valid 014 residual pin / residual NONE without operator force  
- Replacing 014 event definitions mid-flight  
- Unbounded AutoML / architecture search  
- SMA/ZZ signed product as extraction  
- Straddle-only path; shock-as-regime  
- TEST/holdout; deployability; family status; XENA  
- Mega-merge re-opening 015 science as this screen’s primary question  

---

## §8 Amendments

```
AMENDMENT-S1: per-symbol sufficiency — DIRECTION: NEUTRAL
  running count: 0L / 0T / 1N
```

Start-gate is structural (O3 §5), not a looser amendment: **no residual → no 016**.
