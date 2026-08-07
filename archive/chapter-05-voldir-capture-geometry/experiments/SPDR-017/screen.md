# SPDR-017 — Screen summary (neutral quantification)

- **Family / hyp:** CF-VOLDIR-001 / HYP-D4 (independent predicted-price mispricing)
- **Lane:** SPDR TRAIN-only · DESIGN primary · CONFIRM verify
- **Object:** M-ZONE from walk-forward M-RIDGE ŷ (A2 features) → E-TOUCH events → MOMO **and** MR residual characterisation (014 grammar)
- **Not gated on 014 residual** (014 pin residual_status=NONE is informative baseline only)
- **Integrity:** `results/integrity_selfcheck.json` **all_pass=true** (289.9s, 25 symbols)
- **Own pin:** `results/017_residual_pin.json` → **residual_status=NONE**
- **Cost disclosure:** PARTIAL_FEES_FUNDING_ONLY (spread UNAVAILABLE_NOT_CHARGED) — partial_net overstated vs full cost

This file is subordinate to `analysis.md` (fresh-context quantification).

---

## 1. Question answered

Can a light walk-forward regression on proven + error-dynamics + weak-direction **features** form a **mispricing of predicted price** such that post-event residual expectancy ≠ ambient (both MOMO and MR reported, neither assumed)?

---

## 2. Integrity fence (HARD)

| Check | Result |
|---|---|
| Universe pin top-25 | PASS (recompute == family pin) |
| TRAIN fence (exit_ts < train_end) | PASS |
| Golden G1–G4 | PASS |
| O3 SoT path present | PASS |
| No signed product / no 014 start gate | asserted |
| Both MOMO and MR emitted | yes |
| Ablation A0/A1/A2 | emitted |
| T1 path-destroy positive survivors | none (no hard fail) |

---

## 3. Model OOS skill (DESIGN, M-RIDGE A2 H=12)

Per-symbol IC(ŷ, realised H-bar open-to-open return) mostly near zero / slightly negative; MAE hundreds of bps.

| Symbol | n | IC | MAE bps |
|---|---:|---:|---:|
| BTCUSDT | 4853 | −0.040 | 275 |
| ETHUSDT | 4860 | −0.030 | 225 |
| SOLUSDT | 4935 | −0.046 | 296 |
| BNBUSDT | 4813 | +0.079 | 207 |
| DOGEUSDT | 4433 | −0.144 | 332 |
| MATICUSDT | 13896 | −0.042 | 330 |

**Read:** little OOS return skill in the ridge head; mispricing bands are largely Z-VOL-floor dominated when |ŷ| is small.

---

## 4. Primary residual cell (DESIGN · M-ZONE · A2 · M-RIDGE · z=1.5 · H=12 · E-TOUCH · h=12)

| Symbol | n_decided | mean r_h | median r_h | p_momo | p_mr | MDE bps | band |
|---|---:|---:|---:|---:|---:|---:|---|
| BTCUSDT | 151 | +0.4 | −17.1 | 0.351 | 0.583 | 42 | UNPOWERED |
| ETHUSDT | 148 | −22.1 | −30.7 | 0.405 | 0.554 | 66 | UNPOWERED |
| SOLUSDT | 168 | +79.2 | −19.7 | 0.464 | 0.512 | 141 | UNPOWERED |
| XRPUSDT | 145 | +17.6 | +13.3 | 0.545 | 0.455 | 63 | UNPOWERED |
| DOGEUSDT | 134 | +5.2 | −15.7 | 0.455 | 0.515 | 114 | UNPOWERED |
| LINKUSDT | 146 | +5.4 | −24.0 | 0.466 | 0.527 | 80 | UNPOWERED |
| ADAUSDT | 162 | −1.8 | −3.3 | 0.469 | 0.488 | 45 | UNPOWERED |
| BNBUSDT | 144 | −25.2 | −19.8 | 0.389 | 0.576 | 60 | UNPOWERED |
| MATICUSDT | 484 | −14.2 | +0.7 | 0.496 | 0.490 | 61 | UNPOWERED |
| GALAUSDT | 143 | +74.4 | +32.7 | 0.517 | 0.476 | 110 | UNPOWERED |
| OPUSDT | 156 | −51.9 | −53.9 | 0.423 | 0.564 | 96 | UNPOWERED |
| DYDXUSDT | 84 | +62.3 | +52.1 | 0.536 | 0.464 | 163 | UNPOWERED |
| AVAXUSDT | 127 | −9.1 | −10.1 | 0.449 | 0.520 | 80 | UNPOWERED |
| INJUSDT | 73 | −52.1 | −17.4 | 0.493 | 0.507 | 232 | UNPOWERED |

Many listings lack DESIGN history (ORDI/TIA/BIGTIME/BLUR/PEPE/SEI/WLD/PYTH/RATS → n=0).

**All primary cells UNPOWERED** under design floors (n≥80, dates≥30, **MDE≤10**). No cell clears SUPPORTED residual gate → pin **NONE**.

Rate lean across primary H∈{4,12,24} cells: **MIXED_SUGGESTIVE** (8 MOMO_RATE-class vs 10 MR_RATE-class labels; disclosure only).

---

## 5. Ablation A0 / A1 / A2 (DESIGN primary cell)

Cross-symbol median mean_r_h (16 symbols with data):

| Layer | Features | median mean_r_h | mean mean_r_h |
|---|---|---:|---:|
| A0 | PROVEN | +1.11 | −13.1 |
| A1 | PROVEN+DERIVED | −5.47 | −19.3 |
| A2 | +WEAK-DIR | −0.71 | +5.6 |

Per-symbol A0/A1/A2 table: `results/ablation.parquet`.

**WEAK-DIR load-bearing flag:** run_summary `weak_dir_load_bearing_flag=true` (A2 cross-symbol mean lifts while A1 does not dominate A0). **Disclose:** any A2-only improvement is not a silent signed-product revival claim; weak-dir features remain **inputs only**.

---

## 6. vs 014 Z-VOL baseline (informative)

Matched DESIGN E-TOUCH h=12: M-ZONE A2 vs Z-VOL (`results/vs_014_baseline.parquet`).

- Δ mean_r_h (M-ZONE − Z-VOL) across matched rows: **median ≈ −1.2 bps**, mean ≈ +3.5 bps — no stable lift.
- Event counts: Z-VOL generally more decided events (wider level band occupancy pattern differs).
- 014 residual pin remains **NONE**; 017 may and did run without requiring 014 residual success.

---

## 7. Controls (primary cell DESIGN)

Examples (live mean from control walk; full table in `controls.json`):

| Symbol | Δ vs uncond | Δ vs Z-VOL level | time-shuffle pct | matched-random pct | feature-shuffle pct |
|---|---:|---:|---:|---:|---:|
| BTCUSDT | −7.7 | −0.3 | 0.42 | 0.43 | 0.42 |
| ETHUSDT | +22.7 | +5.3 | 0.90 | 0.84 | 0.86 |
| SOLUSDT | +2.7 | +5.8 | 0.81 | 0.80 | 0.86 |
| XRPUSDT | −2.3 | −12.6 | 0.08 | 0.12 | 0.34 |
| MATICUSDT | +34.8 | +4.4 | 0.93 | 0.94 | 0.90 |

Heterogeneous; several high percentiles on raw mean without power clearance. Feature-shuffle does not cleanly zero all live means (model skill weak / band dominated by Z-VOL floor).

T1 path-destroy: no positive money survivor above null p95 → no integrity concern.

---

## 8. Money subset (optional; partial cost)

P-MOMO / P-MR on E-TOUCH × z=1.5 × H=12 × h=12 × M-ZONE A2. **mean partial_net** mostly negative after fees+funding+allowance; medians deeper negative. Not a tradability claim. Spread not charged.

---

## 9. CONFIRM verify (same primary cell)

Sample: BTC mean r_h +2.0 (n=244, MDE 30); ETH +3.3 (n=244, MDE 29); SOL +24.8 (n=250, MDE 53). Still MDE ≫ 10; no powered residual object on CONFIRM either.

---

## 10. Artifacts

| Path | Content |
|---|---|
| `results/features.parquet` | layered features |
| `results/model_oos.parquet` | ŷ, realised, abs err |
| `results/zones.parquet` / `events.parquet` / `post_event.parquet` | 014 grammar |
| `results/ablation.parquet` | A0/A1/A2 |
| `results/vs_014_baseline.parquet` | informative Δ |
| `results/expectancy_by_cell.parquet` | full cell grid |
| `results/017_residual_pin.json` | own pin (not for 016) |
| `results/golden_traces.json` / `integrity_selfcheck.json` | HARD |
| `results/controls.json` | nulls + T1 tripwire |

---

## 11. Disposition note (not final)

SPDR dispositions are operator-signed after `analysis.md`. Screen quantification only:

- **Independent mispricing path completed** without 014 residual success.
- **Full MOMO/MR characterisation** emitted.
- **Ablation complete**; WEAK-DIR load-bearing disclosed.
- **017_residual_pin residual_status=NONE** — no powered residual ≠ ambient under design bands.
- Model IC weak; M-ZONE does not stably beat Z-VOL baseline.

**Binding read:** `analysis.md`.
