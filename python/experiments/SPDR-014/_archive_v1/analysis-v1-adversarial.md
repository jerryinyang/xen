# SPDR-014 — Data Analysis (binding read)

- **Family / hyp:** `CF-VOLDIR-001` / `HYP-D1` · **Lane:** SPDR TRAIN-only · **O3 Group 1**
- **Question:** Given a horizon band from absolute-vol / ZZ-mag forecasts, does price breach at non-ambient rate, and after breach does path **continue (MOMO)** or **revert (MR)** with **conditional residual ≠ ambient** — without assuming either?
- **Analyst:** fresh-context data-analyst. Numbers re-derived from emissions under `results/` via `analysis_code/` (not `screen_code/`). `screen.md` is subordinate.
- **No tradability. No family status. No XENA. No SPDR-015/016 run.**

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: partial_net overstated vs full cost
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

**Emission size:** 25 symbols · 8450 cell rows · 749456 zones/events · 560652 post-event rows · runtime 849.3 s.

**Primary residual cell (design freeze sketch):** Z-VOL · z=1.5 · H=12 · E-TOUCH · h=12 · DESIGN · P-NONE · H1.

**Scripts:** `analysis_code/interrogate_from_json.py`, `interrogate_014.py`, tables in `analysis_code/tables_primary_design.json`.

---

## 1. Integrity gate (Phase 0)

SPDR has **no** `estimand_validation.json`. Integrity substitute = `integrity_selfcheck.json` + fence asserts + golden traces (design §7 HARD; pipeline SPDR carve-out). **Do not block for missing estimand gate.**

### 1.1 Screen integrity self-check

| Check | Result | Evidence |
|---|---|---|
| `all_pass` | **PASS** | `results/integrity_selfcheck.json` |
| Universe pin equality | PASS | `checks.universe_pin_equal=true`; top-25 recompute vs pin |
| Golden G1–G4 | PASS | `golden_traces.json` `all_pass=true` |
| TRAIN fence (exit open < train_end) | PASS | `train_fence_asserted=true`; train_end `2023-12-18T00:00:00+00:00` |
| O3 SoT path present | PASS | `.ignore/what-next/alts/cf-voldir-o3-zone-event-sequence.md` |
| No signed product | PASS | `no_signed_product=true` |
| Shock not titled regime | PASS | `shock_not_regime=true` (named `shock_flag` only) |
| Straddle not headline | PASS | `straddle_not_headline=true` |
| Both MOMO and MR emitted | PASS | `both_momo_mr_emitted=true` |
| Tripwire positive survivors above null p95 | **none** | `tripwire_positive_survivors=[]`; `tripwire_hard_fail=false` |
| Holdout / TEST | **untouched** | TRAIN-only fence; no load ≥2023-12-18 / holdout |
| Nautilus price-primary | N/A (SPDR vectorised) | design §0 vehicle |
| Local accounting for verdict P&L | N/A SPDR | residual = side-signed open-to-open bps; money = partial fee/funding only |

**Deviations (non-weakening):** IN-1 money subset pins zone H=12; IN-2 Z-MAG expanding ridge = monthly-refit recipe.

### 1.2 Causality construction

| Column / object | Inputs & timestamps | ≤ t−1 / causal? | Evidence |
|---|---|---|---|
| Zone width (Z-VOL) | Parkinson on completed H1 ≤ t; EWMA λ=0.94; s_symbol frozen on DESIGN warm-up | YES | G1: ewma/sigma/band match 1e-9; `s_BTC=6384.32` |
| Anchor | RealOpen of bar t+1 | YES | design §2.1; engine `band_bounds(anchor,…)` |
| E-TOUCH event bar j | High/low of bars in window t+1…t+H | YES (path after anchor) | engine `detect_event` |
| Breach entry | RealOpen of bar j+1 | YES | G2: `entry_next_open=true`; r_h hand=engine |
| Residual r_h | `side * 1e4 * (exit_open/entry_open − 1)`; exit open at entry+h | YES | engine `residual_r_h`; TRAIN exit ts < train_end |
| Money entry | Same breach entry; side with/against residual policy | YES | G4: partial_net hand=engine (fee 11 + funding + 2) |
| Features vs fill | No own-bar close as limit | YES | open-to-open residual; no RCT limit pattern |

**Provenance class:** construction-causal. No leak tripwire HARD fail on money path.

### 1.3 Tripwire class (T1 informative)

| Item | Value |
|---|---|
| Control | PATH-FUTURE-DESTROY on money subset mean partial_net |
| Class | **INFORMATIVE** (T1 / DEV-1 — outcome destroy alone cannot prove leak on mean P&L) |
| Residual HARD applicability | no cell with live mean partial_net > 0 may sit above destroyed-null p95 without integrity flag |
| Observed | 3 symbols claim positive live mean (BONK, BLUR, INJ); **0** survive above null p95; **0** integrity_concern |
| Hard fail | **false** |

---

## 2. Question list (O3 Group 1 — answer before verdict)

| # | Question | Answer |
|---|---|---|
| Q1 | Do Z-VOL bands breach at non-ambient rate? | **Near-certain breach:** control live p_event ≈ 0.99–1.00 for Z-VOL z=1.5 H=12 (e.g. BTC 0.994, ETH/SOL/AVAX 1.0). Uncond-band Δp_event typically +3–11 pp (forecast width slightly tighter / higher breach). **p_event near 1** ⇒ zone is not a rare mispricing filter at these z,H. |
| Q2 | After E-TOUCH, is residual mean ≠ ambient (matched-random / time-shuffle)? | **Point estimate often above null, but never powered.** Matched-random: 12/17 symbols with data have live−null > 0; med Δ ≈ **+11.6 bps** (control population). Time-shuffle live percentiles often 0.5–0.9. **No cell** meets §8.1 SUPPORTED (CI_low on residual > 0 **and** MDE≤10). |
| Q3 | Without assuming direction: p_momo vs p_mr? | DESIGN Z-VOL E-TOUCH z=1.5 h=12 H=12: med **p_momo≈0.514**, med **p_mr≈0.467**; **12/17** symbols p_momo>p_mr (frac≈0.71). Mild MOMO rate lean only; MR-leaning symbols exist (BNB, AVAX, OP, BONK, MATIC on this cell). |
| Q4 | Is residual sign stable DESIGN → CONFIRM? | **No — CONFIRM flips.** Screen subordinate quantiles (CONFIRM expectancy; DESIGN verified here): DESIGN med mean r_h **+16.5** vs CONFIRM med **−14.3**. Rate lean also weakens. |
| Q5 | Does event definition agree? | **No.** Screen E-CLOSE / E-HORIZON DESIGN med mean r_h **negative** (~−10.7 / −8.9) while E-TOUCH **positive** (+16.5). Touch-first vs close-outside disagree on residual sign. |
| Q6 | Z-MAG vs Z-VOL? | Z-MAG **sparse**: typical n_decided 8–23; MDE hundreds of bps; rates noisy. Not a powered residual substrate. |
| Q7 | Money under residual-following policies? | Partial-cost med mean partial_net **negative** for P-MOMO and P-MR (~−15 bps). Tripwire: no positive survivor above null p95. |
| Q8 | Power / MDE? | **All primary residual cells UNPOWERED** under MDE≤10 (MDE typically 40–200 even when n_decided≥80). UNPOWERED ≠ dead; also ≠ SUPPORTED. |
| Q9 | Multi-symbol agreement? | AMENDMENT-S1: multi-symbol = **credibility only**. Here no per-symbol powered SUPPORTED residual either. |
| Q10 | Residual pin for 016? | **NONE**; `016_start_allowed=false`. Rate-only SUGGESTIVE tags (18 MOMO_RATE / 7 MR_RATE) do not open 016. |
| Q11 | What would make the DESIGN +16.5 wrong as “edge”? | (a) CONFIRM flip; (b) E-CLOSE sign flip; (c) every CI includes 0; (d) MDE >> effect; (e) control population mean not matching expectancy n — all observed. |
| Q12 | Accounting object identity? | Characterisation: side-signed residual on same breach path as optional money. OBJECT-IDENTITY YES per design. Cost partial only. |

---

## 3. Evidence FOR residual ≠ ambient

*(Equal diligence; none of these clear §8.1 SUPPORTED.)*

### 3.1 DESIGN E-TOUCH residual mean often positive (expectancy / pin)

Primary cell Z-VOL z=1.5 H=12 E-TOUCH h=12 DESIGN — **per-symbol** (n_decided>0 only):

| Symbol | n | mean r_h | median r_h | p_momo | p_mr | MDE | CI | label |
|---|---:|---:|---:|---:|---:|---:|---|---|
| BTCUSDT | 196 | +2.4 | +3.3 | 0.474 | 0.464 | 38.5 | [−24.0, +30.9] | — |
| ETHUSDT | 194 | +26.2 | +15.1 | 0.531 | 0.443 | 48.8 | [−7.8, +61.6] | MOMO_RATE |
| SOLUSDT | 197 | +43.7 | +18.2 | 0.518 | 0.462 | 105.1 | [−22.5, +125.5] | MOMO_RATE |
| AVAXUSDT | 180 | −7.5 | −11.6 | 0.483 | 0.511 | 86.5 | [−69.3, +53.0] | — |
| 1000BONKUSDT | 41 | −22.0 | −119.8 | 0.463 | 0.537 | 289.5 | wide | — |
| DOGEUSDT | 175 | −15.6 | +4.5 | 0.497 | 0.474 | 58.8 | [−56.6, +26.1] | — |
| XRPUSDT | 193 | +16.5 | +12.5 | 0.518 | 0.466 | 54.7 | [−22.2, +55.7] | MOMO_RATE |
| LINKUSDT | 188 | +11.8 | +2.1 | 0.495 | 0.479 | 63.9 | [−33.2, +57.0] | — |
| ADAUSDT | 193 | +20.9 | +22.0 | 0.528 | 0.446 | 52.2 | [−16.7, +57.6] | MOMO_RATE |
| BLURUSDT | 10 | +491.1 | +546.5 | 0.700 | 0.300 | 763.7 | wide | — |
| 1000LUNCUSDT | 111 | +58.6 | +16.9 | 0.514 | 0.486 | 197.8 | wide | — |
| MATICUSDT | 517 | −10.2 | −4.5 | 0.482 | 0.499 | 61.1 | [−52.7, +32.5] | — |
| INJUSDT | 103 | +36.4 | +71.4 | 0.524 | 0.466 | 193.3 | wide | MOMO_RATE |
| BNBUSDT | 189 | −24.3 | −20.5 | 0.429 | 0.556 | 47.2 | [−58.2, +8.6] | MR_RATE |
| DYDXUSDT | 119 | +76.5 | +57.6 | 0.546 | 0.454 | 174.5 | [−41.1, +206.4] | MOMO_RATE |
| GALAUSDT | 169 | +26.4 | +40.1 | 0.521 | 0.467 | 97.6 | [−44.0, +94.1] | MOMO_RATE |
| OPUSDT | 189 | −20.9 | −11.2 | 0.481 | 0.508 | 102.2 | [−93.4, +51.6] | — |

**Cross-symbol medians (n=17 with data):**

| Metric | Value |
|---|---|
| med mean r_h | **+16.5 bps** |
| med p_momo | **0.514** |
| med p_mr | **0.467** |
| symbols mean r_h > 0 | **11 / 17** |
| frac p_momo > p_mr | **0.71** |
| med (p_momo − p_mr) | ~**+0.05** |

Empty DESIGN coverage (no catalog span / no s_symbol): ORDI, TIA, BIGTIME, 1000PEPE, SEI, WLD, PYTH, 1000RATS.

### 3.2 Matched-random control: more live>null than not

Control cell = same pins, denser residual sample than non-overlapping expectancy episodes.

| | |
|---|---|
| Symbols with finite control | 17 |
| live−null > 0 | **12 / 17** |
| med (live−null) | **+11.6 bps** |
| med live percentile | **0.65** |
| Notable high Δ | DYDX +44.9, BONK +41.5, DOGE +34.4, LUNC +28.9, SOL +21.5 |
| Notable low Δ | OP −55.1, AVAX −13.9, XRP −8.2 |

Interpretation: **some** post-touch residual structure vs random anchors in DESIGN — **not** uniform; OP/AVAX contradict.

### 3.3 Time-shuffle

Live residual often above shuffled pairing null (examples: DOGE pct 0.865, MATIC 0.885, DYDX 0.92; BTC only 0.58; OP 0.02). Heterogeneous; not a global destroy survival of a large edge.

### 3.4 Rate-only SUGGESTIVE tags (not residual SUPPORTED)

Across primary residual grid cells in pin: **18 MOMO_RATE**, **7 MR_RATE** (design: p_momo/p_mr gap with weak residual sign; **not** §8.1 residual SUPPORTED). Rate lean is real as a **description**, not a powered residual.

### 3.5 Golden / integrity

Construction works: G1–G4 pass; both labels always tabled; no tripwire hard fail. Emission is **valid to interpret**.

---

## 4. Evidence AGAINST (CONFIRM flip, MDE UNPOWERED, money, event defs, Z-MAG, heterogeneity)

### 4.1 CONFIRM sign flip (critical)

| Band | med mean r_h (Z-VOL E-TOUCH z=1.5 H=12 h=12) | med p_momo | med p_mr |
|---|---:|---:|---:|
| DESIGN (re-derived) | **+16.5** | 0.514 | 0.467 |
| CONFIRM (screen subordinate; expectancy) | **−14.3** | ~0.47 | ~0.50 |

If the mechanism were a stable post-event residual, CONFIRM should not invert the median sign. **This is the strongest anti-evidence against residual ≠ ambient as a durable object.**

### 4.2 All primary residual cells UNPOWERED (MDE)

Design §8.1: UNPOWERED if n_events<80 OR n_dates<30 OR **MDE > 10 bps**.

| Fact | Value |
|---|---|
| n_powered residual MOMO | **0** |
| n_powered residual MR | **0** |
| Typical MDE (Z-VOL dense symbols) | **40–200 bps** |
| Best MDE on primary H=12 Z-VOL | BTC **38.5** still >> 10 |
| Sparse / alt MDE | 200–900+ |
| Every pin primary cell `unpowered` | **true** |
| Every pin `band_label_raw` | **UNPOWERED** |
| Residual CI includes 0 | **all** Z-VOL H=12 cells above (no CI_low>0) |

**UNPOWERED ≠ dead (B-5).** It **does** block residual SUPPORTED and blocks `016_start_allowed` under design §8.3.

### 4.3 Money negative (partial cost)

| Policy | med mean partial_net (approx) | note |
|---|---:|---|
| P-MOMO | **~−15 bps** | residual-following; not tradability |
| P-MR | **~−15 bps** | |
| Tripwire survivors > null p95 | **0** | T1 informative |
| DA-STRADDLE (secondary) | **~−29 bps** | 2× costs on ~0 gross path |

Money does **not** graduate residual-following extraction under partial costs.

### 4.4 E-CLOSE / E-HORIZON disagree with E-TOUCH

Screen medians DESIGN Z-VOL H=12 z=1.5 h=12:

| Event | med mean r_h | med p_momo | med p_mr |
|---|---:|---:|---:|
| E-TOUCH (headline) | **+16.5** | 0.514 | 0.467 |
| E-CLOSE | **−10.7** | 0.441 | 0.530 |
| E-HORIZON | **−8.9** | 0.481 | 0.515 |

Headline residual lean is **definition-dependent**. A true mispricing residual should not flip sign under a nearby event rule.

### 4.5 Z-MAG sparse / unusable for residual pin

| | Z-VOL H=12 | Z-MAG H=12 |
|---|---|---|
| Typical n_decided | 100–200 (majors) | **10–20** |
| med mean r_h | +16.5 (stable-ish cross-symbol) | chaotic / median-unstable |
| MDE | 40–200 | **often 200–600+** |
| Powered residual | 0 | 0 |

Z-MAG cannot carry residual SUPPORTED here.

### 4.6 Per-symbol heterogeneity

- **MOMO-rate leaning:** ETH, SOL, ADA, XRP, GALA, DYDX, INJ (and H-variants).
- **MR-rate leaning:** BNB (all H), AVAX (H=4), OP (H=4/24), XRP H=4.
- **Near-flat / mixed residual mean:** BTC (~0), LINK, DOGE (mean vs median disagree).
- **Sparse outliers:** BLUR n=10 mean +491 (tail-dominated, not portable).
- **Empty symbols:** 8/25 with no DESIGN residual sample.

Pooled “+16.5 MOMO” is a **disclosure median**, not a homogeneous finding (L-03 / AMENDMENT-S1).

### 4.7 p_event ≈ 1 (zone not selective)

At z=1.5 H≥12, almost every origin breaches. The “mispricing event” is nearly **every zone** — residual is closer to “side-signed 12h path after first band touch” than “rare dislocation.” That weakens the O3 story that breach isolates special structure.

### 4.8 Control vs expectancy population mismatch

BTC control live mean r_h **−1.3** (n≈341) vs expectancy/pin **+2.4** (n=196). Different occupancy sampling. Attribution collapse fractions on uncond-band are **unstable / non-interpretable as simple ratios** (e.g. BTC collapse −4.9 when live near 0). Report layers only.

---

## 5. Both p_momo and p_mr fully tabled (primary residual cells)

### 5.1 DESIGN · Z-VOL · z=1.5 · E-TOUCH · h=12 · by H

Full H=12 table in §3.1. H=4 and H=24 (same source/event/h) from pin — both labels always present:

| Symbol | H=4 p_momo / p_mr | H=12 p_momo / p_mr | H=24 p_momo / p_mr | H=4 mean | H=12 mean | H=24 mean |
|---|---|---|---|---:|---:|---:|
| BTCUSDT | 0.436 / 0.528 | 0.474 / 0.464 | 0.454 / 0.474 | +3.3 | +2.4 | −2.5 |
| ETHUSDT | 0.508 / 0.446 | 0.531 / 0.443 | 0.521 / 0.454 | +24.7 | +26.2 | +25.8 |
| SOLUSDT | 0.518 / 0.467 | 0.518 / 0.462 | 0.518 / 0.462 | +1.7 | +43.7 | +43.7 |
| AVAXUSDT | 0.444 / 0.539 | 0.483 / 0.511 | 0.483 / 0.511 | −5.6 | −7.5 | −7.5 |
| DOGEUSDT | 0.460 / 0.511 | 0.497 / 0.474 | 0.503 / 0.462 | +3.7 | −15.6 | +11.7 |
| XRPUSDT | 0.458 / 0.526 | 0.518 / 0.466 | 0.518 / 0.466 | −11.7 | +16.5 | +16.5 |
| LINKUSDT | 0.505 / 0.479 | 0.495 / 0.479 | 0.495 / 0.479 | +15.7 | +11.8 | +11.8 |
| ADAUSDT | 0.539 / 0.440 | 0.528 / 0.446 | 0.518 / 0.451 | +17.9 | +20.9 | +22.9 |
| MATICUSDT | 0.495 / 0.491 | 0.482 / 0.499 | 0.482 / 0.499 | +10.6 | −10.2 | −10.2 |
| BNBUSDT | 0.434 / 0.545 | 0.429 / 0.556 | 0.429 / 0.556 | −20.0 | −24.3 | −24.3 |
| OPUSDT | 0.402 / 0.587 | 0.481 / 0.508 | 0.439 / 0.545 | −69.2 | −20.9 | −44.2 |
| GALAUSDT | 0.538 / 0.450 | 0.521 / 0.467 | 0.521 / 0.467 | +31.5 | +26.4 | +26.4 |
| DYDXUSDT | 0.538 / 0.454 | 0.546 / 0.454 | 0.529 / 0.471 | +68.0 | +76.5 | +131.0 |
| INJUSDT | 0.515 / 0.476 | 0.524 / 0.466 | 0.475 / 0.515 | −18.1 | +36.4 | −40.6 |
| 1000LUNCUSDT | 0.505 / 0.486 | 0.514 / 0.486 | 0.514 / 0.486 | +37.1 | +58.6 | +58.6 |
| 1000BONKUSDT | 0.524 / 0.476 | 0.463 / 0.537 | 0.537 / 0.463 | +30.9 | −22.0 | +147.3 |
| BLURUSDT | 0.700 / 0.300 | 0.700 / 0.300 | 0.700 / 0.300 | +491 | +491 | +491 |

Empty symbols omitted (p_momo=p_mr=null). **Neither label assumed;** both always reported.

### 5.2 DESIGN · Z-MAG · z=1.5 · H=12 · E-TOUCH · h=12 (sparse)

| Symbol | n | mean r_h | p_momo | p_mr | MDE |
|---|---:|---:|---:|---:|---:|
| BTCUSDT | 16 | +43.6 | 0.500 | 0.438 | 166 |
| ETHUSDT | 12 | −64.4 | 0.500 | 0.500 | 174 |
| SOLUSDT | 19 | +246.2 | 0.421 | 0.579 | 642 |
| AVAXUSDT | 13 | +115.3 | 0.692 | 0.308 | 290 |
| DOGEUSDT | 21 | −43.7 | 0.381 | 0.619 | 204 |
| XRPUSDT | 14 | −157.6 | 0.571 | 0.429 | 357 |
| LINKUSDT | 10 | −323.0 | 0.400 | 0.600 | 586 |
| ADAUSDT | 17 | +39.9 | 0.353 | 0.647 | 204 |
| BNBUSDT | 17 | −19.4 | 0.471 | 0.529 | 223 |
| … | … | … | … | … | … |

All UNPOWERED; rates not stable across symbols.

### 5.3 Rate lean summary (DESIGN Z-VOL E-TOUCH z=1.5 h=12)

| H | frac p_momo>p_mr | frac p_mr>p_momo | med (p_momo−p_mr) |
|---|---:|---:|---:|
| 12 | ~0.71 | ~0.29 | ~+0.05 |

---

## 6. Residual pin interpretation

Artifact: `results/014_residual_pin.json` (**corrected** 2026-07-24 for MDE/UNPOWERED).

```json
{
  "residual_status": "NONE",
  "016_start_allowed": false,
  "policy_for_016": "NONE",
  "n_powered_momo": 0,
  "n_powered_mr": 0,
  "n_rate_momo_suggestive": 18,
  "n_rate_mr_suggestive": 7
}
```

| Rule (design §8.3) | Application |
|---|---|
| `016_start_allowed=true` only if residual_status ≠ NONE **and** ≥1 powered primary residual cell | **Failed** — 0 powered cells |
| Rate-only MOMO_RATE / MR_RATE | **SUGGESTIVE only** — do not set residual_status to MOMO/MR_DOMINANT for 016 |
| Operator override | Allowed with **signed residual freeze** in pin notes — not exercised here |
| AMENDMENT-S1 | Per-symbol SUPPORTED would suffice if powered; **none powered** |

**Interpretation:** O3 Decision A path to SPDR-016 is **closed by the residual pin** unless the operator explicitly overrides. This is not a family death; it is “no named post-event residual ready to refine.”

---

## 7. Recommended experiment-level characterisation verdict

| Field | Value |
|---|---|
| **Recommendation** | **NOT SUPPORTED** as a powered residual ≠ ambient object; residual pin **NONE** |
| Scope | Experiment hypothesis only (zone→event→MOMO/MR residual). **NOT family. NOT tradability.** |
| Characterisation (magnitudes) | DESIGN E-TOUCH shows mild MOMO **rate** lean (med p_momo 0.51 vs p_mr 0.47) and med mean r_h **+16.5 bps**, but **all cells UNPOWERED**, CONFIRM **flips sign**, E-CLOSE **flips sign**, money **negative**, Z-MAG **sparse** |
| Disposition language (SPDR) | Closest formal disposition: **NOT_WORTH** for residual-extraction handoff to 016; optional science remains (015 conditioner work independent). UNPOWERED components stay non-negative (B-5) |
| Driven by | (1) **0 powered residual cells** under §8.1 MDE≤10; (2) **CONFIRM sign flip**; (3) **money + tripwire** no positive graduate |
| Would change if | Operator re-pins wider MDE; or CONFIRM re-read shows non-flip under alternative event; or new emission with selective z/H yields CI_low>0 on Δ vs matched-random **and** MDE≤10 on ≥1 symbol |

**Pooled “+16.5 bps MOMO” must not be quoted as supported edge.**

---

## 8. Explicit operator gate

| Option | Meaning | Consequence |
|---|---|---|
| **A. Accept residual pin NONE** (recommended) | Freeze `residual_status=NONE`, `016_start_allowed=false` | SPDR-016 **must not start**. Programme extraction path waits or ends per O3 §5 (“if 014 no residual → 016 not opened”). 015 optional science only. |
| B. Amend design / re-emit | Change z/H/event, power target, or band definition; re-run TRAIN screen | New residual pin after re-analysis. Only if operator believes selectivity (p_event≪1) or power fix is necessary. |
| C. Operator override 016 start | Signed freeze of a residual object despite UNPOWERED | Allowed by design notes only with explicit operator signature — **not recommended** given CONFIRM flip + money negative. |
| D. Stop programme branch | Treat Group 1 residual extraction as closed | Stronger than A; still not a family RETIRE (registry status out of scope). |

**Recommended gate: A — accept residual pin NONE; do not start 016; no family action; no XENA.**

Final verdict is the operator’s.

---

## 9. Anomalies & open questions

1. **p_event≈1** at primary pins — band may be too tight relative to path; residual ≈ ambient side-signed path after first touch, not rare mispricing.
2. **Control vs expectancy n mismatch** — report both; do not mix live means across populations without disclosure.
3. **H=12 and H=24 identical residual on several symbols** — non-overlapping occupancy may force same breach set for longer H; disclose mechanic.
4. **DYDX H=24** CI_low > 0 on raw mean in pin (+16.4 … +256) but still UNPOWERED (MDE 172) and not matched to control Δ SUPPORTED stack — do not cherry-pick.
5. **CONFIRM full per-symbol table** — re-run `analysis_code/interrogate_from_json.py` (parquet path) to lock CONFIRM numbers independent of screen; DESIGN primary already re-aggregated from pin cells.
6. **015** may still refine conditioners; it does not unlock 016 without a residual pin change.

---

## 10. Artifact map

| Path | Role |
|---|---|
| `results/integrity_selfcheck.json` | HARD integrity |
| `results/golden_traces.json` | G1–G4 causality/cost |
| `results/014_residual_pin.json` | **016 start gate (NONE)** |
| `results/controls.json` | matched-random, time-shuffle, uncond, tripwire |
| `results/expectancy_by_cell.parquet` | full cell grid |
| `results/post_event.parquet` | episode-level r_h / labels |
| `results/money_episodes.parquet` / `straddle.parquet` | money disclosure |
| `analysis_code/interrogate_from_json.py` | independent re-aggregation |
| `analysis_code/tables_primary_design.json` | primary DESIGN tables used above |
| `screen.md` | subordinate quantification |

---

**Handoff:** Accept pin **NONE** → **016 not allowed** without operator override. Characterisation complete for Group 1 under this emission. Final call is the operator’s.
