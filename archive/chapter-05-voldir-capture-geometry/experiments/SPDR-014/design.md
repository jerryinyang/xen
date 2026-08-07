# SPDR-014 — Zone / mispricing event / post-event MOMO vs MR (Group 1)

- **Family:** `CF-VOLDIR-001` · **Hypothesis:** `CF-VOLDIR-001/HYP-D1`
- **Checkpoint:** `2026-07-23-017-structural-vol-direction-programme`
- **Lane:** SPDR TRAIN-only · vectorised Python · 0 counted TEST reads
- **Status:** `SCREEN COMPLETE — AWAITING OPERATOR DISPOSITION` (implement + TRAIN run + integrity PASS; residual pin NONE; 016 not started)
- **Produces:** event rates + post-event MOMO/MR characterisation (rates **and** residual expectancy) + optional money under residual-following policy
- **Must not:** assume MOMO or MR; signed SMA/ZZ product; tradability; XENA; family status change; straddle-only headline

**Prior evidence (do not re-run):** SPDR-012 Keep (range level H1/H4); SPDR-013 signed fail + ambient MFE + ZZ mag IC.

---

## §A O3 source of truth (100% compliance — binding)

```
O3-SOT:
  path: .ignore/what-next/alts/cf-voldir-o3-zone-event-sequence.md
  role: BINDING substance for Groups 1–3
  conflict_rule: O3 substance > this design. On conflict STOP and amend design (or operator-amend O3).
  may_narrow: YES (grids, pins, numeric floors)
  may_thin_or_contradict_O3: NO
```

| O3 clause | Design coverage | Compliance obligation |
|---|---|---|
| §1 no signed product; vol not tradable alone | §1 mechanism; §11 refusals | No signed combo product; no “trade HIGH vol” policy |
| §3 proven ingredients 1–5 | §2 width; §4.3 conditioners | Only level / ZZ mag / slow Markov / named shock; non-claims enforced |
| §4 Group 1 zone→event→MOMO/MR | §2–§5 entire | Headline object = zone/event/residual; straddle secondary only |
| §4 freeze sketch (band/event/estimands/nulls/success) | §2–§4, §7–§8 | All six freeze rows implemented |
| §2.1 shock ≠ regime | §4.3 Shock flag | Must not label R-SHOCK / \|r\| top-decile as regime |
| §2.3 AMENDMENT-S1 | §8 | Per-symbol SUPPORTED allowed |
| §5 Decision A first | status | Run 014 before relying on 016; 015 optional order |
| §5 if 014 no residual | §8 residual pin; handoff | Emit pin; 016 must not start |
| §6 refusals | §11 | Full list mirrored |

**QA / implementer rule:** any arm, metric, or narrative that violates a row above is **out of programme** even if coded.

---

## §0 Scope fence

| | |
|---|---|
| **Vehicle** | Vectorised Python on fenced 1m → H1 (primary). No Nautilus; no estimand_validation |
| **Band** | DESIGN `[2021-06-29T06:53Z, 2023-03-01T00:00Z)` primary. CONFIRM `[2023-03-01, 2023-12-18)` verify. **TEST ≥2023-12-18 never. Holdout ≥2025-01-08 never** |
| **Universe** | Top-25 30d volume pin (AMENDMENT-U1). Files: `docs/signal-registry/candidate-families/cf-voldir-001-universe.json` + `results/universe_top25.json`. Code recomputes and asserts equality |
| **AMENDMENT-S1** | Multi-symbol agreement = **credibility only**. Per-symbol powered SUPPORTED may stand alone |
| **Clock** | **H1 primary** for zone/event/residual. **H4** co-report: one slice only (§6) |
| **Sampling** | Zone origins: every complete H1 bar with warm-up met and flat (no open episode). One episode max per symbol |
| **Start** | Operator execution authority |
| **Complexity** | Frozen grid §6 only; no post-outcome arm invention |

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

**One question (O3 §4 Group 1):**  
Given a horizon band from proven absolute-vol / ZZ-magnitude forecasts, does price **breach** that band at a non-ambient rate, and after breach does the path **continue (MOMO)** or **revert (MR)** with **conditional residual ≠ ambient** — without assuming either?

```
MECHANISM:
  Range-based vol level and/or ZZ next-swing magnitude forecast absolute move size over a short
  horizon without forecasting sign (SPDR-012/013). That forecast defines a likelihood zone around
  the entry open. A breach is a makeshift mispricing event relative to the forecast. Post-event
  path may continue away from the zone (MOMO) or return toward the band centre (MR). Neither is
  assumed; both are measured (rates and residual expectancy). Extraction value, if any, is the
  post-event residual after partial costs — not “trade high vol” and not pre-chosen sign models.
  Volatility alone is not tradable (O3 §1).

DERIVED:
  estimand = (i) event rate vs nulls;
             (ii) P(MOMO), P(MR), P(FLAT) and mean/median side-signed residual r_h;
             (iii) optional partial_net under residual-following policy only
  null     = unconditional-σ band; time-shuffled breach times; matched random anchors
  horizon  = band H ∈ {4,12,24} H1; post-event hold h ∈ {4,12,24}
  test     = rates + mean/median residual Δ vs control; date-block CIs; collapse under nulls
```

```
OBJECT-IDENTITY:
  measurement object == trading object: YES for money cells —
    episode starts at breach entry open (open of bar after event bar) and exits under §5 policy
    that follows the characterised residual (P-MOMO or P-MR). Characterisation cells measure the
    same path without requiring a trade (P-NONE).
  measured conditioning event == traded entry event: YES —
    breach uses OHLC of bars with features/width from ≤ zone-decision t; breach entry = first
    actionable open after event bar. No fill at decision close.
  effect-splitting windows non-overlapping: YES — max one open episode per symbol; ignore new
    zone origins while open.
```

---

## §2 Zone construction (likelihood band)

### 2.1 Anchor and decision lag

| Item | Freeze |
|---|---|
| Decision bar t | Last **completed** H1 bar |
| Features / width | Computed from bars **≤ t** only |
| **Anchor** | RealOpen of bar **t+1** (first actionable open) |
| Band active window | Opens at anchor; lives **H** complete H1 bars after anchor (bars t+1 … t+H inclusive for path checks) |

### 2.2 Width sources (both **mandatory** — O3 proven ingredients)

#### Z-VOL (range level → σ̂)

```
UNIT-PIN / CONVERSION-PIN (Z-VOL):
  level object: Parkinson range vol on completed H1 bar i:
    park_i = sqrt( (ln(H_i/L_i))^2 / (4*ln(2)) )   # dimensionless per bar
  smoother: EWMA_park_t = λ*EWMA_park_{t-1} + (1-λ)*park_t , λ=0.94, causal, init = park at warm-up end
  target scale: next-horizon open-to-open absolute move in bps, matching SPDR-012:
    abs_oo_bps = 1e4 * |O_{j+1}/O_j - 1|
  conversion (frozen, no free fit after DESIGN warm-up):
    On DESIGN warm-up only (first 60 complete H1 bars per symbol after catalog start in DESIGN),
    compute s = median( abs_oo_bps / max(EWMA_park, ε) ) over warm-up origins with EWMA known.
    Freeze s_symbol once; reuse on all later DESIGN+CONFIRM origins for that symbol.
    σ_bps_t = s_symbol * EWMA_park_t
  ε = 1e-12
  prohibited: using close-to-close rv20 as primary width; D1 cc-RV; calendar features
```

Emit `s_symbol` to `results/zvol_scale.json` (reproducibility).

#### Z-MAG (ZZ next-swing magnitude)

```
UNIT-PIN (Z-MAG):
  structure: SPDR-013 ATR ZigZag, threshold 2.0 × ATR(14) Wilder H1, ATR[t-1] at decisions
  features at confirmation of swing k (≤ t): magnitude_bps, angle, path_noise, direction, bars_in_swing
  model: ridge walk-forward monthly refit → next-swing magnitude_bps (013 recipe)
  width primary: σ_bps = max( predicted_mag_bps , 1.0 )
  sensitivity (mandatory co-report, not headline): σ_bps = predicted_mag_bps / 2
  if no completed swing yet: origin ineligible for Z-MAG (not silent fill with Z-VOL)
```

### 2.3 Band geometry

```
upper = anchor * (1 + z * σ_bps / 1e4)
lower = anchor * (1 - z * σ_bps / 1e4)
centre = anchor          # primary (O3 “around now”)
z ∈ {1.0, 1.5, 2.0}      # all mandatory
H ∈ {4, 12, 24}          # all mandatory
```

Structural mid-swing centre: **out of first-pass** (would require operator amend).

---

## §3 Event definitions (mispricing)

**Primary (headline — O3 “one primary”):**

| Event ID | Rule |
|---|---|
| **E-TOUCH** | First H1 bar j in the active window whose **high ≥ upper** or **low ≤ lower**. Side = +1 if upper touched first within the bar (if both: compare which extreme is farther in bps from centre; if tie → UNDECIDED). |

**Secondary (mandatory co-report for robustness):**

| Event ID | Rule |
|---|---|
| **E-CLOSE** | First bar j with **close** outside [lower, upper] |
| **E-HORIZON** | At last bar of window only: close outside band (no early event) |

| Outcome | Rule |
|---|---|
| event=1 | E-* fires |
| event=0 | path stays inside for full H |
| UNDECIDED side | count in event rate; **exclude** from signed residual and money |

---

## §4 Post-event characterisation (mandatory — O3: do not assume MOMO or MR)

### 4.1 Breach entry and residual

| Item | Freeze |
|---|---|
| Event bar j | Bar that first satisfies event rule |
| **Breach entry** | RealOpen of bar **j+1** (causal) |
| Hold h | ∈ {4, 12, 24} H1 bars |
| Exit mark for residual | RealOpen of bar breach_entry_index + h |
| `side` | +1 up-breach / −1 down-breach |
| `r_h` | `side * 1e4 * (exit_open/breach_entry_open - 1)` open-to-open bps |

### 4.2 Labels (all three always reported)

| Label | Rule (c = **5 bps** deadband) |
|---|---|
| **MOMO** | `r_h > +c` (continues in breach direction) |
| **MR** | `r_h < −c` (reverts against breach / toward zone) |
| **FLAT** | `|r_h| ≤ c` |

**Estimands (O3: frequency and expectancy):**

| Estimand | Definition |
|---|---|
| `p_event` | P(event=1) among zone origins |
| `p_momo`, `p_mr`, `p_flat` | among events with decided side |
| `mean_r_h`, `median_r_h` | among decided-side events |
| `mean_r_h_momo` / `mean_r_h_mr` | conditional means (disclosure) |
| Δ vs control | live − control for mean_r_h and for p_momo, p_mr |

### 4.3 Residual vs ambient (success shape O3)

Success (characterisation): **conditional residual ≠ ambient** — i.e. mean `r_h` Δ vs control clears §8 band **or** MOMO/MR rate ratio vs control is material with CI — without assuming which label wins.

### 4.4 Conditioners (strata — all reported; O3 list)

| Conditioner | Definition | Notes |
|---|---|---|
| Vol level tercile | Expanding percentile of EWMA_park (same as Z-VOL smoother) → LOW/MID/HIGH cuts 1/3, 2/3 | Proven ingredient |
| ZZ mag HIGH | Z-MAG predicted mag expanding pct ≥ 2/3 | Proven ingredient |
| Slow regime | SPDR-012 V-REGIME: rolling-median split of rv20 HIGH/LOW | Optional co-stratum; **not** shock |
| Last-k state | **Ordered** slow-regime label sequence over the last K∈{1,2,3} bars (chronological oldest→newest, char = one bar: `H`/`L`/`?`), decision bar = last char, causal ≤t — see AMENDMENT-S2 | O3 “last X labels / last-k states” (§2.1/§2.2 run-length + order preserved); k=1..3 each tested |
| Shock flag | Top-decile \|r_t\| on decision bar | **Named shock only** — never “regime” |

---

## §5 Optional extraction policies (money — after characterisation)

Policies **follow** residual; they do **not** invent sign from SMA/ZZ.

| Policy ID | Rule |
|---|---|
| **P-NONE** | Characterisation only (default for full grid) |
| **P-MOMO** | On E-TOUCH decided side: enter **with** side at breach entry; exit at min(h, stop) |
| **P-MR** | Enter **against** side; exit at min(h, stop) |

| Exit detail | Freeze |
|---|---|
| Time | Open of breach_entry + h |
| Stop | Adverse excursion ≥ **1.5 × ATR(14) Wilder H1** at entry−1 → exit next bar open after touch (013-style) |
| Cost | fee_rt 11.0 + funding 1.0×stamps in (entry,exit] + allowance 2.0 per leg; spread null |
| Stats | mean **and** median partial_net (E1); win-rate disclosure only |

**Informative graduate rule:** money cell interesting only if policy direction matches **dominant** characterised label vs control in that stratum (e.g. P-MR only where p_mr materially > control). No auto-XENA.

### Secondary arm only (O3: not sole headline)

**DA-STRADDLE:** at zone anchor open, long+short 1 unit each; exit both at H (X-FH); partial_net = sum legs − 2×costs. **Disclosure comparison** to zone/event residual — must not replace §2–§4 as the question.

---

## §6 Frozen grid

```
Sources:     Z-VOL, Z-MAG
z:           1.0, 1.5, 2.0
H:           4, 12, 24
Events:      E-TOUCH (primary bands), E-CLOSE, E-HORIZON (all computed)
Post h:      4, 12, 24
Policies:    P-NONE on all characterisation cells
             P-MOMO + P-MR on E-TOUCH × h=12 × z=1.5 × {Z-VOL,Z-MAG} only (money subset)
Strata:      symbol × vol tercile × mag_HIGH × (slow regime optional table)
H4 co-report: Z-VOL, z=1.5, H=12, E-TOUCH, h=12, P-NONE only
Secondary:   DA-STRADDLE × Z-VOL × z=1.5 × H∈{4,12,24} disclosure
```

Multiplicity: disclose full cell count in screen.md.

---

## §7 Controls + tripwire (full validity blocks)

```
CONTROL UNCOND-BAND:
  question answered: does forecast-based width beat unconditional σ at same z,H?
  population: σ_bps = expanding std of abs_oo_bps (H1) × same z; same anchors
  DISJOINT: different width series (not a subset of signal events by construction of width)
  bite/MDE: plant +20 bps mean r_h on live must rank extreme vs control
  non-vacuity: changes event set and residual distribution
  expected if H true: live event quality / residual > uncond; if false: ≈
  disclosure: Δ p_event, Δ mean_r_h, collapse = control/live
  class: within_sample_attribution (report layer)
```

```
CONTROL TIME-SHUFFLE-EVENT:
  question answered: is post-event residual an artifact of clock time without zone structure?
  population: derange event timestamps within (symbol × DESIGN calendar-third); re-measure r_h on foreign paths
  DISJOINT: zero fixed points
  bite/MDE: +20 bps plant
  non-vacuity: destroys event–path pairing for residual mean
  expected if H true: live > null p95; if false: inside null
  disclosure: live percentile; collapse fraction
  destroy form: DERANGEMENT
  seeds: ≥200 (prefer 2000)
  class: within_sample_attribution
```

```
CONTROL MATCHED-RANDOM-ANCHOR:
  question answered: event rate / residual vs random anchors same occupancy
  population: non-overlapping random H1 anchors, same mean H/z/source grid cell, ≥200 seeds
  DISJOINT: exclude live anchors ±1 H1
  bite/MDE: +20 bps plant on residual
  non-vacuity: changes anchor times
  disclosure: live percentile of p_event and mean_r_h
  class: within_sample_attribution
```

```
CONTROL GATE-LABEL-SHUFFLE (conditioner non-vacuity):
  question answered: do vol/mag strata merely relabel noise?
  population: derange tercile labels within symbol×third
  destroy form: DERANGEMENT
  class: within_sample_attribution
```

```
TRIPWIRE: PATH-FUTURE-DESTROY
  metric: mean partial_net on money subset (P-MR and P-MOMO cells)
  form: derange future path pairing within symbol×third
  class: INFORMATIVE (T1 / DEV-1 class — outcome destroy cannot alone prove leak on mean P&L)
  residual HARD applicability: no cell with live mean partial_net > 0 may sit above destroyed-null
    p95 without integrity investigation flag
  vacuity: destroys path for signed P&L
  derangement=YES
```

```
HARD (block): TRAIN fence; every episode exit open < train_end_utc (2023-12-18);
  features/width ≤ t; breach entry after event bar; universe pin equality;
  integrity_selfcheck.json PASS; engine parity sequential==batch if both exist;
  no TEST/holdout load; O3-SOT compliance (no signed product; no shock-as-regime; no straddle-only).
INFORMATIVE: all rates, residuals, bands, controls, money, tripwire, graduate notes.
```

---

## §8 Bands, power, residual pin (handoff to 016)

### 8.1 Bands (labels never gates)

```
BANDS (per symbol × source × z × H × event × h × stratum where n allows):
  SUPPORTED residual:
    mean_r_h Δ vs MATCHED-RANDOM or TIME-SHUFFLE control ≥ +5 bps
    AND date-block CI low on Δ > 0
    AND median_r_h Δ ≥ 0
    AND sign(mean Δ) consistent in ≥2/3 DESIGN chronological thirds
  WASH: |mean Δ| < 5 bps
  CONTRADICTED: mean Δ ≤ −5 AND CI high < 0
  UNPOWERED: n_events < 80 OR n_dates < 30 OR MDE > 10 bps
AMENDMENT-S1: multi-symbol agreement NOT required.
POOLED: disclosure-only.
Rate-only note: p_momo/p_mr vs control reported always; may be SUGGESTIVE without residual SUPPORTED.
```

Money bands (subset): same numeric thresholds on mean partial_net with median ≥ 0 for SUPPORTED label; still not tradability.

### 8.2 Power

```
POWER:
  zone origins ~ O(H1 bars in band) per symbol after warm-up
  event rate falls with z; predeclare UNPOWERED risk: z=2.0 × H=4; sparse alts
  MDE residual ~ 2.8 * σ_r / sqrt(n_dates)
  UNPOWERED never reported as negative (B-5)
```

### 8.3 Residual pin for SPDR-016 (mandatory artifact even if null)

Write `results/014_residual_pin.json` after analysis:

```json
{
  "o3_compliant": true,
  "residual_status": "MOMO_DOMINANT | MR_DOMINANT | SPLIT | NONE",
  "primary_cells": [{"symbol":"...", "source":"Z-VOL", "z":1.5, "H":12, "event":"E-TOUCH", "h":12, "label":"MR|MOMO", "mean_r_h_delta":0.0}],
  "policy_for_016": "P-MR | P-MOMO | NONE",
  "016_start_allowed": false,
  "notes": "operator may override 016_start_allowed with signed residual freeze"
}
```

`016_start_allowed=true` only if residual_status ≠ NONE and ≥1 powered primary cell (or operator override recorded in pin).

---

## §9 Inference

- Date-block bootstrap on event (or origin) dates; blocks 1/3/7 days; seeds 101/211/307/401/503; ≥5k resamples for CIs on mean residual Δ.  
- Per-symbol primary.  
- DESIGN primary for bands; CONFIRM attenuation disclosed.  
- Seed batteries for random controls: 200 minimum.

---

## §10 Golden traces + integrity checklist

```
GOLDEN-TRACE:
  G1 BTCUSDT Z-VOL: listed DESIGN window — hand Parkinson + EWMA λ=0.94 + frozen s_symbol →
     band z=1.5 H=12; upper/lower match emission to 1e-9 rel.
  G2 ETHUSDT E-TOUCH: synthetic path breaches upper only; side=+1; breach entry = next open;
     r_12 hand-computed.
  G3 SOLUSDT Z-MAG: one confirmed ZZ swing → ridge width; ineligible if no swing.
  G4 AVAXUSDT P-MR: against-side entry, stop 1.5 ATR, partial_net = gross − 11 − funding − 2.
```

1. TRAIN-only; max exit < train_end.  
2. Width ≤ t; anchor = t+1 open.  
3. Both MOMO and MR always emitted; no auto-pick policy without P-NONE tables.  
4. Shock flag never titled regime.  
5. Win-rate not band driver.  
6. Universe pin equality.  
7. `integrity_selfcheck.json` PASS.  
8. O3-SOT clause map present; straddle not headline.

---

## §11 Out of scope / O3 §6 refusals (mirrored)

- Dual-leg straddle **as sole** extraction object without zone/event language  
- Shock-HMM / \|r\| flag as “regime”  
- Mega-merge with 015 transitions + 016 ML in this screen  
- Assume outside-band = fade or chase without §4  
- Signed vol×direction product; CF-VOLCONV range-break primary  
- Historical TEST / holdout; deployability / full-cost claims  
- Hour-level vol skill claim; calendar features; D1 cc-RV primary width  
- Open ML zoo; SPDR-015/016 objects implemented here  
- Family status change; XENA start  

---

## §12 Deliverables

| Artifact | Content |
|---|---|
| `results/zvol_scale.json` | per-symbol s_symbol |
| `results/zones.parquet` | origin, source, z, H, σ_bps, upper, lower |
| `results/events.parquet` | event type, side, timestamps |
| `results/post_event.parquet` | r_h, labels, strata |
| `results/expectancy_by_cell.parquet` | money mean/median |
| `results/controls.json` | null distributions |
| `results/014_residual_pin.json` | 016 start gate |
| `results/golden_traces.json` / `integrity_selfcheck.json` | HARD |
| `screen.md` / `analysis.md` | neutral + binding O3-aligned characterisation |

---

## §13 Amendments

```
AMENDMENT-S1: per-symbol sufficiency; multi-symbol = credibility only — DIRECTION: NEUTRAL
  running count: 0 looser / 0 tighter / 1 neutral (S1)

AMENDMENT-S2 (2026-07-24): last-k conditioner corrected to O3 intent — DIRECTION: NEUTRAL
  trigger: original §4.4 "count of HIGH Markov bars in last K" compressed O3 §2.1/§2.2
    "last-k states / last X labels", discarding order + run-length (which O3 explicitly cares
    about). O3-SOT > design → amend, not silent re-render.
  change: emit the ORDERED slow-regime label sequence over the last K bars
    (last_k_state_1 / last_k_state_2 / last_k_state_3; chronological oldest→newest;
    'H'/'L'/'?'=NaN; decision bar = last char). Replaces the count columns last_k_high_4/12.
  K set: operator-directed K∈{1,2,3} (each tested), superseding the design's original {4,12} —
    small K keeps every pattern analysable (2 + 4 + 8 = 14 patterns) whereas K=12 raw pattern is
    ~all singletons. Conditioning = stratify residual/rates by the ordered pattern per k
    (e.g. k=1 H vs L; k=3 HLL vs HHH …).
  fidelity: order + run-length preserved (a count would discard both); no information invented.
  scope: stratification column only — NO change to any estimand, control, null, pin, fence, or
    verdict. Re-emit required to populate the column; integrity/golden re-verified on rerun.
  running count: 0 looser / 0 tighter / 2 neutral (S1, S2)
```

Inherited class: U1 universe; T1 informative tripwire; E1 medians on money.
