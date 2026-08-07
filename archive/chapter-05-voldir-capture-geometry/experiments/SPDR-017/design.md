# SPDR-017 — Independent predicted-price mispricing + MOMO/MR characterisation (operator original Group-3)

- **Family:** `CF-VOLDIR-001` · **Hypothesis:** `CF-VOLDIR-001/HYP-D4`
- **Checkpoint:** 017
- **Lane:** SPDR TRAIN-only · 0 TEST reads
- **Status:** `CLOSED — DISPOSITION NOT_WORTH` (operator-signed 2026-07-24; implement+TRAIN run+integrity+screen+analysis 2026-07-24; residual_status=NONE)
- **Distinct from SPDR-016:** 016 **refines** a named 014 residual (hard start gate).  
  **017 builds its own** predicted-price / residual mispricing from a broader feature stack and
  characterises it **the same way as SPDR-014 (Group 1 method)** — **not** gated on 014 residual success.
- **Produces:** walk-forward residual/price predictor; zone or signed residual mispricing events;
  full MOMO vs MR characterisation; optional money under residual-following policy
- **Must not:** require 014 residual pin; open unbounded ML zoo; treat SMA/ZZ as standalone product;
  assume MOMO/MR; tradability/XENA/family status claims

---

## §A O3 / programme SoT (100% compliance — binding)

```
O3-SOT:
  path: .ignore/what-next/alts/cf-voldir-o3-zone-event-sequence.md
  role: BINDING substance for CF-VOLDIR O3 sequence (014–017)
  this_vehicle: Group 3b — operator-original independent mispricing path
  conflict_rule: O3 substance > this design for shared rules; this design freezes Group 3b object
  may_narrow: YES
  may_thin_or_contradict_O3_shared: NO
  relation_to_016: SIBLING — not child; 016 stays 014-gated refine path
```

| Shared O3 obligation | Coverage |
|---|---|
| §1 no signed product; vol not tradable alone | mechanism + refusals |
| §3 proven ingredients + non-claims | §2.1 PROVEN layer always on |
| §4 Group 1 **method** (zone/event/MOMO+MR, both, nulls) | §3–§5 characterisation stack = 014 grammar |
| §2.3 AMENDMENT-S1 | §6 bands |
| §6 refusals | §9 |
| Weak direction = features only | §2.3 |
| Balance proven / derived / new | §2 layers + ablation A0/A1/A2 |

**Not applicable:** O3 “016 only after 014 residual” — that binds **SPDR-016 only**, not 017.

---

## §0 Scope fence

| | |
|---|---|
| **Band** | DESIGN `[2021-06-29T06:53Z, 2023-03-01T00:00Z)` primary; CONFIRM `[2023-03-01, 2023-12-18)` verify; TEST/holdout **never** |
| **Universe** | Top-25 pin (U1); recompute assert; AMENDMENT-S1 |
| **Clock** | H1 primary |
| **Start** | Operator execution authority only — **no** dependency on `014_residual_pin.json` |
| **Optional inputs** | 015 states/ordinal scores if complete; 014 metrics as **informative baseline only** |
| **Order vs 014** | Prefer after 014 for comparison, but **legal to run even if 014 residual NONE** |

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

**One question (operator original #3):**  
Using proven vol/mag features, **signed predicted−actual error**, error/vol **acceleration**, and weak
direction models as **features only**, can a light walk-forward regression build a **predicted-price
or path residual** such that **mispricing events** relative to that prediction, when characterised
**exactly as Group 1 / SPDR-014** (breach → MOMO vs MR rates and residual expectancy vs ambient),
show a **conditional residual ≠ ambient** — without assuming MOMO or MR and without reopening signed
SMA/ZZ as a product?

```
MECHANISM:
  Magnitude structure is partially forecastable (012/013). Forecast errors and their dynamics may
  encode when a simple level-based zone is wrong and where price is relative to a model-implied
  centre. A light regression on proven + error-dynamics + weak direction *features* produces a
  one-step (or H-horizon) predicted return/level. Deviation of realised price from that prediction
  is a model mispricing. That mispricing is turned into an event and characterised with the same
  MOMO/MR grammar as SPDR-014. Direction-aware extraction, if any, follows post-event residual —
  not “SMA tells side.”

DERIVED:
  estimand = (i) model OOS residual skill (optional IC/MAE);
             (ii) mispricing event rate vs nulls;
             (iii) post-event MOMO/MR rates + mean/median r_h Δ vs ambient;
             (iv) optional partial_net under residual-following policy
  null     = unconditional/level-only band (014-style Z-VOL); time-shuffle events; feature shuffle
  horizon  = H ∈ {4,12,24} H1; post-event h ∈ {4,12,24}
  test     = walk-forward; date-block CIs; ablation of feature layers
```

```
OBJECT-IDENTITY:
  measurement object == trading object: YES for money cells —
    entry at mispricing event breach entry open; side = event side × residual policy (MOMO/MR);
    exit h/stop as 014.
  measured conditioning event == traded entry event: YES — event on completed path; entry next open.
  effect-splitting windows non-overlapping: YES — one episode per symbol.
```

---

## §2 Feature stack (balance — frozen, no zoo)

### 2.1 Layer PROVEN (always on)

| Feature | Definition |
|---|---|
| `ewma_park`, `lvl_pct` | Parkinson EWMA λ=0.94 + expanding percentile (012 Keep) |
| `zz_mag_hat` | Ridge next-swing magnitude (013) |
| `slow_reg` | Markov rv20 HIGH/LOW |
| `shock` | top-decile \|r\| **named shock only** |
| Optional `hmm_rv`, `ord_gt_cur` | SPDR-015 if complete |

### 2.2 Layer DERIVED — error dynamics (core of original #3)

At origin t (causal; H\* = 12 primary):

| Feature | Definition |
|---|---|
| `pred_move_bps` | level-based predicted \|move\| = Z-VOL σ_bps (014 conversion pin recipe) |
| `real_move_bps` | last completed H\* abs_oo aggregate or last bar abs_oo as co-feature |
| `err_abs` | pred − realised absolute move over last completed H\* window |
| `err_signed` | signed path vs predicted centre over last window |
| `Δerr` | err_abs_t − err_abs_{t−1} |
| `Δvol` | ewma_park_t − ewma_park_{t−1} |
| `err_z` | err_abs / max(ewma_park, ε) |

### 2.3 Layer WEAK-DIR (inputs only)

| Feature | Definition |
|---|---|
| `sma25_sign`, `sma25_angle_on` | 013 |
| `zz_next_leg_sign` | 013 constructive next leg |

**Forbidden as product:** enter from WEAK-DIR alone without mispricing event.

### 2.4 Model class

| Model | Spec |
|---|---|
| **M-RIDGE** | Ridge → next H-bar open-to-open return (bps) **or** next mid-path residual — **primary** |
| **M-GBM** | depth≤3, n_est≤100, min_leaf≥50 — sensitivity |

Walk-forward monthly refit; no architecture search.

### 2.5 Ablation (mandatory)

| ID | Features |
|---|---|
| A0 | PROVEN only |
| A1 | PROVEN + DERIVED |
| A2 | PROVEN + DERIVED + WEAK-DIR |

If A2 only wins via WEAK-DIR, disclose **WEAK-DIR load-bearing** — not silent signed-product revival.

---

## §3 Predicted-price mispricing object

### 3.1 Model prediction

At decision t (completed H1):

```
ŷ_t = model forecast of open-to-open return over horizon H (bps), or of path centre displacement
centre_model = anchor * (1 + ŷ_t / 1e4)     # for return head
# alternative residual head: ŷ = predicted residual vs Z-VOL centre — freeze RETURN head as primary
```

Anchor = RealOpen of t+1 (same as 014).

### 3.2 Mispricing band / event (014 grammar)

**Primary construction (M-ZONE):**

```
σ_bps = max(|ŷ_t|, Z-VOL σ_bps, 1.0)   # width at least level scale; not thinner than noise
upper = anchor * (1 + z * σ_bps / 1e4)
lower = anchor * (1 - z * σ_bps / 1e4)
# optional asymmetric band (sensitivity): centre_model ± z * σ_bps — first-pass uses symmetric about anchor
z ∈ {1.0, 1.5, 2.0}; H ∈ {4, 12, 24}
```

**Events (same definitions as SPDR-014 §3):** E-TOUCH primary; E-CLOSE, E-HORIZON secondary.

**Secondary construction (M-SIGN-ERR):**  
Event when realised path residual vs centre_model exceeds +z·σ or −z·σ (signed model error event).  
Same post-event MOMO/MR stack. Co-report; not sole headline if M-ZONE runs full grid.

### 3.3 Co-baseline (informative)

Re-run or import **014 Z-VOL** cells at same z,H,E-TOUCH for Δ comparison (014 as dumb magnitude zone).  
**Not a start gate.** 017 may show residual even when 014 residual_status=NONE.

---

## §4 Post-event characterisation (identical obligations to 014 §4)

| Item | Freeze |
|---|---|
| Breach entry | Open of bar after event bar |
| `r_h` | side-signed open-to-open bps, h ∈ {4,12,24} |
| Labels | MOMO / MR / FLAT with c=5 bps — **both MOMO and MR always reported** |
| Estimands | p_event; p_momo/p_mr/p_flat; mean/median r_h; Δ vs controls |
| Conditioners | vol tercile; zz mag HIGH; slow regime; shock (named); optional last-k |

**Success shape:** conditional residual ≠ ambient (same as O3 Group 1).  
**Do not assume** MOMO or MR.

### Controls (014-class + model-class)

```
CONTROL UNCOND-BAND / LEVEL-ONLY (014 Z-VOL recipe)
CONTROL TIME-SHUFFLE-EVENT (derangement)
CONTROL MATCHED-RANDOM-ANCHOR (≥200 seeds)
CONTROL FEATURE-SHUFFLE (model skill)
CONTROL ABLATION A0/A1/A2
TRIPWIRE: PATH-FUTURE-DESTROY informative (T1 class)
HARD: fence, causality, universe pin, integrity_selfcheck, O3 shared refusals
```

Full validity fields as SPDR-014 §7 / SPDR-016 §5 patterns (question, population, bite, non-vacuity, disclosure, class).

---

## §5 Money policies (optional subset)

| Policy | Rule |
|---|---|
| P-NONE | characterisation only (full grid) |
| P-MOMO / P-MR | follow residual only on E-TOUCH × z=1.5 × H=12 × h=12 |

Costs: fee 11 + funding + allowance 2; mean **and** median; win-rate disclosure only.  
Graduate only if residual characterisation supports the policy direction.

---

## §6 Bands, power, residual pin (own pin — not 016)

```
BANDS: same numeric SUPPORTED/WASH/CONTRADICTED/UNPOWERED as SPDR-014 §8
AMENDMENT-S1 applies
POOLED: disclosure-only
```

```
POWER: same UNPOWERED floors as 014 (n_events≥80, n_dates≥30, MDE≤10)
```

Emit **own** `results/017_residual_pin.json` (parallel schema to 014 pin) for any later refine experiment — **does not feed SPDR-016** (016 reads **014** pin only).

---

## §7 Golden traces + deliverables

```
GOLDEN-TRACE:
  G1 BTCUSDT design matrix at listed t → M-RIDGE ŷ matches refit
  G2 ETHUSDT M-ZONE band z=1.5 H=12 from ŷ and Z-VOL floor
  G3 SOLUSDT E-TOUCH → r_12 MOMO/MR label hand check
  G4 Ablation: A0 score ≠ A2 when WEAK-DIR active on fixture
```

| Artifact | Content |
|---|---|
| `results/features.parquet` | layered features |
| `results/model_oos.parquet` | ŷ, scores |
| `results/zones.parquet` / `events.parquet` / `post_event.parquet` | 014 grammar |
| `results/vs_014_baseline.parquet` | informative Δ vs Z-VOL cells |
| `results/ablation.parquet` | A0/A1/A2 |
| `results/017_residual_pin.json` | own residual status |
| `results/expectancy_by_cell.parquet` | money subset |
| golden_traces / integrity_selfcheck | HARD |
| `screen.md` / `analysis.md` | binding characterisation |

---

## §8 Inference

Date-block bootstrap; DESIGN primary; CONFIRM verify; per-symbol primary; S1 multi-symbol credibility only.

---

## §9 Out of scope / refusals

- Hard start gate on 014 residual (that is **016 only**)  
- Replacing 014 or absorbing 016  
- SMA/ZZ as extraction product  
- Assume MOMO/MR; straddle-only; shock-as-regime  
- Open AutoML; TEST/holdout; deployability; family status; XENA  

---

## §10 Amendments

```
AMENDMENT-S1: per-symbol sufficiency — DIRECTION: NEUTRAL
REGISTRATION-017 (2026-07-24): operator original Group-3 intent as SPDR-017; SPDR-016 kept as
  014-gated refine — DIRECTION: NEUTRAL (scope completeness, 0 new outcomes until run)
DISPOSITION-017 (2026-07-24, operator-signed): NOT_WORTH for graduation. Grounds = apparatus/
  mechanism facets (model OOS IC ≈ 0; DERIVED error-dynamics layer A1 inert vs A0; 3 destroy
  controls indistinguishable corr 0.985; M-ZONE ≤ Z-VOL baseline). Per-stratum residual test
  is UNPOWERED → INCONCLUSIVE (B-5 — NOT a proven zero); the two nominal CI-clears (GALA DESIGN,
  DOGE CONFIRM) do not cross-replicate. WEAK-DIR load-bearing CONFIRMED (inputs-only, not a
  signed-product revival). No family status change — CF-VOLDIR-001 stays REGISTERED (checkpoint
  retrospective only). 017_residual_pin=NONE; not consumed by SPDR-016. Binding read: analysis.md.
```
