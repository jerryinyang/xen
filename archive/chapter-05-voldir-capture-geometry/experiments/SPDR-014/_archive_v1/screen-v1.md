# SPDR-014 — Screen summary (neutral quantification)

- **Family / hyp:** CF-VOLDIR-001 / HYP-D1 (O3 Group 1)
- **Object:** likelihood zone → mispricing event → post-event MOMO vs MR (rates **and** residual expectancy)
- **Band:** DESIGN primary `[catalog start, 2023-03-01)`; CONFIRM verify `[2023-03-01, 2023-12-18)`; TRAIN only
- **Universe:** top-25 pin (recompute assert PASS)
- **Integrity:** `results/integrity_selfcheck.json` **all_pass=true** (849.3 s, 25 symbols)
- **Residual pin (corrected §8.1):** `residual_status=NONE`, `016_start_allowed=false`  
  (all primary residual cells UNPOWERED under MDE≤10; rate-only lean is SUGGESTIVE only)
- **Cost:** PARTIAL_FEES_FUNDING_ONLY; spread UNAVAILABLE_NOT_CHARGED — no tradability claim
- **Binding read:** `analysis.md` (this file is subordinate)

---

## 0 Multiplicity

| Axis | Levels |
|---|---|
| Sources | Z-VOL, Z-MAG (+ Z-MAG-SENS co-report) |
| z | 1.0, 1.5, 2.0 |
| H | 4, 12, 24 |
| Events | E-TOUCH (primary), E-CLOSE, E-HORIZON |
| Post h | 4, 12, 24 |
| Bands | DESIGN, CONFIRM |
| Money subset | P-MOMO, P-MR × E-TOUCH × z=1.5 × H=12 × h=12 × {Z-VOL,Z-MAG} |
| H4 co-report | Z-VOL z=1.5 H=12 E-TOUCH h=12 P-NONE |
| Secondary | DA-STRADDLE × Z-VOL z=1.5 × H∈{4,12,24} |

**Cell rows emitted:** 8450 · **zones/events:** 749456 · **post-event rows:** 560652

---

## 1 Integrity self-check (HARD)

| Check | Result |
|---|---|
| Universe pin equality | PASS |
| Golden G1–G4 | PASS |
| TRAIN fence (exit open < train_end) | PASS |
| O3 SoT path present | PASS |
| Shock never titled regime | PASS (named `shock_flag` only) |
| Both MOMO and MR always tabled | PASS |
| Tripwire positive money survivors above null p95 | none |
| **all_pass** | **true** |

---

## 2 Zone / event rates (DESIGN, Z-VOL, E-TOUCH, h=12, z=1.5, P-NONE)

Median across symbols with data (n_decided>0; 17/25 have catalog coverage in DESIGN):

| H | med p_event | med n_decided | med p_momo | med p_mr | med mean r_h (bps) | med median r_h |
|---|---|---|---|---|---|---|
| 4 | ~0.94 | ~180–195 | 0.505 | 0.479 | **+10.6** | (see cell table) |
| 12 | ~1.00 | ~119–196 | **0.514** | **0.467** | **+16.5** | |
| 24 | ~1.00 | ~119–196 | 0.514 | 0.471 | **+16.5** | |

**p_event by z** (Z-VOL, H=12, E-TOUCH, DESIGN): z=1.0 → 1.00; z=1.5 → 1.00; z=2.0 → 0.99 (median).  
Bands are tight relative to path: almost every zone origin breaches within H for Z-VOL at these pins.

**Z-MAG** (same slice): med n_decided ≈ 10; med p_event 0.01–0.09; med p_momo 0.44–0.46, med p_mr 0.54–0.55; sparse / often UNPOWERED.

**Event-definition co-report** (Z-VOL H=12 z=1.5 h=12 DESIGN medians):

| Event | med mean r_h | med p_momo | med p_mr |
|---|---|---|---|
| E-TOUCH (headline) | **+16.5** | 0.514 | 0.467 |
| E-CLOSE | −10.7 | 0.441 | 0.530 |
| E-HORIZON | −8.9 | 0.481 | 0.515 |

E-TOUCH residual lean ≠ E-CLOSE/E-HORIZON lean (sign of mean flips).

---

## 3 Post-event residual vs ambient (primary cell)

**Primary cell:** Z-VOL, z=1.5, H=12, E-TOUCH, h=12, DESIGN, P-NONE.

| Metric | DESIGN (median across symbols with data) | CONFIRM |
|---|---|---|
| mean r_h (bps) | **+16.5** | **−14.3** |
| p_momo | 0.514 | 0.470 |
| p_mr | 0.467 | 0.498 |
| symbols mean_r_h > 0 | 11 / 17 | (lower) |

**Matched-random anchor control** (per-symbol, primary control cell):  
median live mean r_h ≈ +28.4 bps; median null ≈ +0.8 bps; median (live−null) ≈ **+28.9 bps**; median live percentile ≈ 0.83.

**Time-shuffle event:** median live percentile ≈ 0.80 (live residual often above shuffled null).

**Uncond-band:** median Δ mean r_h (live − uncond width) ≈ +17.3 bps (heterogeneous by symbol; some large negative).

**Power:** **all primary residual cells UNPOWERED under design §8.1 MDE≤10 bps** (typical MDE 40–200 bps). n_decided often ≥80 and n_dates ≥30, but residual variance dominates. Labels on mean r_h are magnitude reads, not SUPPORTED residual.

---

## 4 MOMO vs MR rates (both mandatory — O3)

DESIGN Z-VOL E-TOUCH z=1.5 h=12:

| H | frac symbols p_momo > p_mr | frac p_mr > p_momo | med (p_momo − p_mr) |
|---|---|---|---|
| 12 | ~0.71 | ~0.29 | ~+0.05 |

Rate lean is mild MOMO on E-TOUCH DESIGN; MR-leaning symbols exist (e.g. BNB, OP, AVAX on some H).  
Rate-only SUGGESTIVE tags in pin: **18 MOMO_RATE**, **7 MR_RATE** primary cells (not residual SUPPORTED).

---

## 5 Money subset (disclosure; not tradability)

P-MOMO / P-MR on E-TOUCH × z=1.5 × H=12 × h=12 × Z-VOL, DESIGN, partial cost only:

| Policy | med mean partial_net (bps) | symbols with mean > 0 | max mean |
|---|---|---|---|
| P-MOMO | **−14.6** | 5 / 17 | large positive outliers exist |
| P-MR | **−15.6** | 1 / 17 | ~+4.6 |

Tripwire PATH-FUTURE-DESTROY: no cell with live mean partial_net > 0 survived above destroyed-null p95 with integrity concern flag.

**DA-STRADDLE** (secondary): DESIGN median mean partial_net ≈ **−29 bps** (2× costs on ~0 gross path).

---

## 6 H4 co-report (one slice)

Z-VOL z=1.5 H=12 E-TOUCH h=12 P-NONE: p_event often 1.0 where data; residual mixed (BTC mean r_h ≈ −38; SOL ≈ +96; many short/listed-late symbols empty). Not primary.

---

## 7 Residual pin for SPDR-016

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

File: `results/014_residual_pin.json` (corrected for MDE/UNPOWERED).

---

## 8 Artifacts

| Path | Content |
|---|---|
| `results/zvol_scale.json` | per-symbol s_symbol |
| `results/zones.parquet` | origins + band geometry |
| `results/events.parquet` | event type, side |
| `results/post_event.parquet` | r_h, MOMO/MR/FLAT, strata |
| `results/expectancy_by_cell.parquet` | cell aggregates + money |
| `results/controls.json` | nulls + tripwire |
| `results/014_residual_pin.json` | 016 start gate |
| `results/golden_traces.json` | G1–G4 |
| `results/integrity_selfcheck.json` | HARD |

---

## 9 Screen disposition (routing only — not final)

Quantification shows: (i) Z-VOL zones breach at near-ambient-high rates; (ii) E-TOUCH DESIGN residual mean often above matched-random null in point estimate; (iii) **CONFIRM flips sign** of median residual; (iv) **no §8.1 powered residual SUPPORTED cell**; (v) money medians negative under partial cost.

**Residual pin:** NONE → **016 must not start** under design gate unless operator overrides.  
Operator disposition after `analysis.md`.
