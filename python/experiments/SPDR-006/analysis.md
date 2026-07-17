# Data Analysis: SPDR-006 (CF-HTFCAP-001 vol-regime facet — TRAIN availability screen)

**Role:** fresh-context data-analyst (SPDR stage 5).  
**Raw inputs:** `results/cells.parquet` (1680 = 1440 treat + 240 baseline), `amplifier_vs_spdr004.parquet` (720, read-only vs frozen SPDR-004), `membership.parquet`, `unit_pin.json`, `integrity.json`, `summary.json`.  
**Re-derive code:** `analysis_code/spdr006_analysis.py` → `results/analyst_*.{parquet,csv,json}`.  
**Subordinate (not authority):** `screen.md` (neutral quantification only).  
**Not a disposition stamp:** operator chooses `WORTH_EXPLORING` / `NOT_WORTH` / `INCONCLUSIVE`.  
**Unit pin (L-21):** primary = **gross open-to-open bps/trade**. Money floor = **measured TRAIN-median staging SpreadBps** + taker 5.5 bps/side + funding GAP 1 bps/8h — **not GAP=2**.  
**K=3:** THIS grid only (no pooling with SPDR-004 for cluster membership).  
**XENA:** still blocked on INFR-014 pin even if WORTH_EXPLORING.

---

## 1. Integrity gate (SPDR adaptation — Phase 0)

SPDR carve-out: **no** `estimand_validation.json` (by design — spdr-lane). Integrity substitute = code-asserted fence + causal lag + `integrity.json` **PASS 14/14**. Metrics = availability/lift in bps, not booked P&L.

| Check | Result | Evidence |
|---|---|---|
| Estimand validation artifact | **N/A (SPDR)** | design / spdr-lane |
| `integrity.json` 14/14 | **PASS** | `all_pass: true`, `pass_count: 14` |
| Items 1–11 (SPDR-004 form) | **PASS** | registration, TRAIN fence, causal t−1, membership, matched control, per-stratum, L-28, L-21, L-20, G1–G3, no local P&L |
| **12 Joint phase-shift vol+DI+ADX** | **PASS** | Control C shifts every HTF gate input together |
| **13 No DI-only treatment** | **PASS** | treatments ⊆ `{VOL_HI, VOL_LO, DI×VOL_HI, DI_ADX×VOL_HI}`; DI/DI_ADX count = 0 |
| **14 Amplifier table** | **PASS** | 720 interaction rows vs frozen SPDR-004 |
| TRAIN fence | **PASS** | max_exit_ns < train_end_ns; holdout_start 2025-01-08 sealed |
| Causal t−1 / HTF CloseTime < Open(t) | **PASS** | item 3; G1 `forming_bar_not_used: true` |
| Online membership causality | **PASS** | item 4; G3; sha `30350088…` **byte-identical to SPDR-004** |
| Matched control + seed battery | **PASS** | item 5; seeds 1000–1024; A1 UNF baseline |
| Per-stratum emission | **PASS** | 1440 treatment + 240 baseline |
| L-28 derangement (Control C) | **PASS** | item 7: 0 fixed points |
| L-21 unit_pin.json (measured spreads) | **PASS** | TRAIN ATR + **measured** SpreadBps cost pins |
| L-20 emit + block rule | **PASS** | item 9; finite L-20 on powered; 8 NaN lift-CI on n=1 LINK 1d VOL_LO unpowered tails only |
| **lift_ci_method (A4/A5)** | **PASS** | only allowed trio; **zero** `battery_minus_seeds` |
| Golden G1–G3 | **PASS** | G1 DI×VOL_HI 4h entry; G2 VOL_LO UNF long-only; G3 membership |
| Holdout / TEST untouched | **PASS** | TRAIN band only |
| Price-primary Nautilus | **N/A (SPDR)** | vectorised Python by design |
| Leak tripwire (Control C) | **MAGNITUDES §3.8** | collapse on promote-facing cells |

### lift_ci_method audit (A1–A5 binding)

| Method | n treatment | Role |
|---|---:|---|
| `two_sample_block_vs_battery` | 480 | **UNF** vs RAND-battery (A5) |
| `two_sample_block` | 480 | **MOM** vs NONE twin |
| `two_sample_seed_means` | 480 | **RAND** seed-mean two-sample |
| `battery_minus_seeds` | **0** | **BANNED** |

### Golden traces (integrity.json)

| ID | Result | Key values |
|---|---|---|
| G1 | ok | 4h/15m DI×VOL_HI: HTF close < LTF open; vol_ratio≈1.57; ADX≈48.7; dir=−1; r_bps_H16≈274; forming bar not used |
| G2 | ok | VOL_LO standalone UNF: ratio≈0.80; **sign=+1 long-only** declared drift-exposed |
| G3 | ok | rebalance 2023-04-02 ranks BTC…LTC match expected; membership sha matches SPDR-004 |

### Provenance (verdict-bearing columns)

| Column / object | Inputs & timestamps | ≤ t−1 / causal? | Location |
|---|---|---|---|
| HTF vol_ratio | ATR(14)/med_ATR(W=100) on last closed HTF bar | yes (asserted + G1/G2) | screen (not imported for numbers) |
| HTF ±DI / ADX | last HTF CloseTime < Open(t) | yes | same |
| MOM sign | Close[t−1] − Close[t−1−N] | yes | same |
| RAND sign | seed + bar calendar | yes (L-19) | seeds 1000–1024 |
| Membership | trailing 24h notional < rebalance | yes | G3 + sha vs SPDR-004 |
| `r_bps` | s·(Open[t+H]−Open[t])/Open[t]·1e4 non-overlap | open-to-open | design estimand |
| Lift | treatment mean − matched baseline | Control A / A1 | cells |
| Lift CI | UNF: A5 two_sample_block_vs_battery; MOM: two_sample_block; RAND: two_sample_seed_means | dependence-honest | `lift_ci_method` |
| Control C | joint phase-shift K=50 HTF bars on **vol + DI + ADX** (derangement) | destroy form asserted | item 12 |
| Amplifier Δ | interaction lift − frozen SPDR-004 DI/DI_ADX lift | read-only join | `amplifier_vs_spdr004.parquet` |
| Money floor | measured SpreadBps + fees + funding GAP | L-21 improved | `unit_pin.json` |

---

## 2. Question list

| # | Question | Status |
|---|---|---|
| Q1 | Object identity vs design estimand? | **ANSWERED** §3.1 |
| Q2 | Per-stratum magnitudes with uncertainty (lift CI / n / powered)? | **ANSWERED** §3.2–3.6 + `analyst_*` |
| Q3 | Amplifier vs frozen direction-only (DI / DI_ADX)? | **ANSWERED** §3.7 |
| Q4 | VOL_LO compression read? | **ANSWERED** §3.4 |
| Q5 | VOL_HI standalone vs interaction? | **ANSWERED** §3.4–3.5 |
| Q6 | Hold ladders on coherent clusters? | **ANSWERED** §3.5 |
| Q7 | Base-conditional (UNF / MOM / RAND)? | **ANSWERED** §3.6 |
| Q8 | Control C collapse on promote-facing / CI+ cells? | **ANSWERED** §3.8 |
| Q9 | K=3 cluster scan THIS grid only? | **ANSWERED** §3.9 |
| Q10 | Money floors with **measured** spreads? | **ANSWERED** §3.10 |
| Q11 | Multiplicity / chance-rate context? | **ANSWERED** §3.11 |
| Q12 | Seed-band / block fragility (L-20)? | **ANSWERED** §3.12 |
| Q13 | What would make headline numbers wrong? | **ANSWERED** §5 |
| Q14 | Per-year / regime stability? | **UNANSWERED** — cell aggregates only; needs bar re-emit |
| Q15 | UNF×{VOL_HI,VOL_LO} drift-exposure magnitude? | **ANSWERED** §3.4, §3.6 |

---

## 3. Quantified facets (magnitudes — not verdicts)

### 3.1 Object identity

- Measurement object = trading object = **single-leg open-to-open gross bps over hold H** (non-overlapping active-hold).  
- No multi-leg episode (L-16 N/A).  
- Lift = treatment − matched baseline (UNF: RAND battery @ UNF cadence per A1).  
- Bases are **rulers**, not strategies to rescue (spdr-lane base-conditional).  
- **UNF × {VOL_HI, VOL_LO}** = long-only, **declared drift-exposed** (design §3). Against-drift read = RAND interaction.  
- Interaction filters: sign from DI; vol gates only (never sets sign).  
- Amplifier claim requires interaction lift **> frozen SPDR-004 direction-only**, not only > baseline.

### 3.2 Grid inventory (re-derived)

| Item | Value |
|---|---:|
| Treatment cells (primary) | **1440** |
| Baseline cells | 240 |
| Unpowered | **383** |
| Powered | **1057** |
| Med mean bps (all treat) | **+1.07** |
| Med lift bps (all treat) | **+1.51** |
| Lift CI+ (ci_low > 0) | **266** |
| Lift CI+ powered | **184** |
| Lift CI− (ci_high < 0) | (see facets) |

**Domain medians (disclosure; not pooled verdict):**

| Domain | med mean | med lift | CI+ | CI+ powered | unpowered |
|---|---:|---:|---:|---:|---:|
| 1h/5m | (near 0) | **+0.13** | 66 | **66** | 0 |
| 4h/15m | higher | **+7.71** | 127 | **97** | 75 |
| 1d/1h | mixed | **+1.26** | 73 | **21** | **308** |

**Hold ladder (all bases pooled — disclosure):**

| Hold | med lift | CI+ | CI+ powered | unpowered |
|---:|---:|---:|---:|---:|
| 0.5× | +0.41 | 48 | 47 | 19 |
| 1× | +1.27 | 55 | 51 | 49 |
| 2× | +3.99 | 72 | 48 | 120 |
| 4× | **+5.70** | 91 | 38 | 195 |

**Read:** 4h/15m + longer holds carry location shift; 1d mass is sparse/unpowered; capture-scale dose-response visible in medians.

### 3.3 HTF filter axis (core facet)

| Filter | n | med lift | CI+ | CI+ powered | unpowered |
|---|---:|---:|---:|---:|---:|
| **VOL_HI** | 360 | **+0.89** | 24 | **15** | 90 |
| **VOL_LO** | 360 | **−0.02** | 15 | **5** | 93 |
| **DI×VOL_HI** | 360 | **+5.14** | 114 | **86** | 93 |
| **DI_ADX×VOL_HI** | 360 | **+5.81** | 113 | **78** | 107 |

**Location split is large:** interaction med lifts ≈ **+5–6 bps** vs standalone vol ≈ **0**. VOL_LO median is compression-near-zero (not a sign-flip story).

### 3.4 VOL standalone (VOL_HI / VOL_LO)

**VOL_LO (compression):**

- Med lift **−0.02 bps**; powered CI+ only **5/360**.  
- Powered CI+ cells are sparse lottery (e.g. DOGE 4h MOM, ETH 4h UNF h4, OP/LTC MOM 1h) — **no multi-hold multi-symbol UNF ladder**.  
- Design instruction: interpret as **compression-regime finding**, not reverse-edge narrative.

**VOL_HI (expansion alone):**

- Med lift +0.89; powered CI+ **15**.  
- UNF powered CI+ includes APT 4h long holds (means 70–134 bps, n_trades 132–255), PEPE/OP 1h, XRP 4h h4 — **high magnitude but thin / heterogeneous symbols**.  
- On **SOL 4h UNF VOL_HI** hold ladder: mean 3.6→6.3→10.4→12.3; lift CI lows all **negative** (wide). Collapse fractions **negative** (destroy does not kill a non-edge).  
- On **BTC 4h UNF VOL_HI**: no CI-honest lift ladder (point lifts small; not promoted).  
- **Standalone vol does not replace direction** for coherent capture-scale edge on liquid majors.

**UNF drift-exposure note:** UNF×VOL_HI med lift **+7.07** (18 CI+, 12 powered) — inflated relative to MOM/RAND on same filter because long-only rides TRAIN crypto drift. Against-drift ruler: RAND×VOL_HI med lift **+0.49**, CI+ powered **1**.

### 3.5 Interaction hold ladders (promote-facing)

All figures re-derived from `cells.parquet` via `analyst_promote_ladders.*`. Floor = measured unit_pin for that symbol×domain×hold.

#### SOLUSDT × 4h/15m × UNF × DI×VOL_HI (full ladder; all 4 holds lift CI+)

| hold | mean | lift | lift CI low | n | collapse | floor | mean−floor |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.5× | 11.4 | 12.1 | **+0.35** | 1599 | 0.64 | 12.88 | **−1.5** |
| 1× | 23.3 | 23.3 | **+4.99** | 800 | 0.69 | 13.13 | **+10.1** |
| 2× | 39.9 | 37.4 | **+5.95** | 409 | 0.62 | 13.63 | **+26.3** |
| 4× | 78.2 | 77.7 | **+45.3** | 213 | 0.55 | 14.63 | **+63.5** |

Monotone capture-scale ladder. Seed band straddles 0 at **h0.5 only** (seed_lo −0.63); h1–h4 seed bands stay >0.

#### BTCUSDT × 4h/15m × UNF × DI×VOL_HI (full ladder; all 4 holds lift CI+)

| hold | mean | lift | lift CI low | n | collapse | floor | mean−floor |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.5× | 7.0 | 6.9 | **+2.21** | 1230 | 0.79 | 11.55 | **−4.5** |
| 1× | 14.1 | 13.9 | **+4.39** | 615 | 0.79 | 11.80 | **+2.3** |
| 2× | 29.7 | 29.8 | **+13.2** | 319 | 0.81 | 12.30 | **+17.4** |
| 4× | 56.6 | 56.0 | **+26.6** | 169 | 0.90 | 13.30 | **+43.3** |

All seed bands on lift CI low stay >0. Collapse **0.79–0.90** (stronger than SOL DI×VOL_HI).

#### BTCUSDT × 4h/15m × UNF × DI_ADX×VOL_HI (full ladder; all 4 CI+)

| hold | mean | lift | lift CI low | n | collapse | floor | mean−floor |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.5× | 8.8 | 8.7 | **+3.70** | 1110 | 0.84 | 11.55 | −2.7 |
| 1× | 17.7 | 17.5 | **+7.40** | 555 | 0.84 | 11.80 | **+5.9** |
| 2× | 36.3 | 36.5 | **+17.7** | 289 | 0.85 | 12.30 | **+24.0** |
| 4× | 66.0 | 65.4 | **+35.6** | 153 | 0.92 | 13.30 | **+52.7** |

#### SOLUSDT × 4h/15m × UNF × DI_ADX×VOL_HI

| hold | mean | lift | lift CI low | n | collapse | floor | mean−floor |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.5× | 10.5 | 11.2 | **−3.29** | 1363 | 0.63 | 12.88 | −2.4 |
| 1× | 21.6 | 21.7 | **+0.89** | 682 | 0.69 | 13.13 | **+8.5** |
| 2× | 37.8 | 35.3 | **+1.52** | 349 | 0.69 | 13.63 | **+24.1** |
| 4× | 68.8 | 68.3 | **+31.4** | 184 | 0.78 | 14.63 | **+54.1** |

CI+ from **1× upward** (h0.5 fails CI). Point ladder still monotone.

#### Contrast: SOL 4h UNF VOL_HI / VOL_LO (no CI+ ladder)

VOL_HI: means 3.6→12.3; CI lows deeply negative. VOL_LO: means 1.1→3.9→2.4; CI lows negative. **Interaction, not bare vol, carries the ladder.**

### 3.6 Base-conditional (binding)

| Base | n | powered | **CI+** | **powered CI+** | CI− | med mean | med lift | method |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **UNF** | 480 | 354 | **70** | **41** | — | higher | **+3.67** | `two_sample_block_vs_battery` |
| **MOM** | 480 | 349 | **42** | **21** | — | mixed | **+0.93** | `two_sample_block` |
| **RAND** | 480 | 354 | **154** | **122** | — | mixed | **+0.97** | `two_sample_seed_means` |
| **Total** | 1440 | 1057 | **266** | **184** | — | +1.07 | +1.51 | — |

**Base × filter medians:**

| Base × filter | med lift | CI+ | powered CI+ |
|---|---:|---:|---:|
| UNF×VOL_HI | +7.07 | 18 | 12 |
| UNF×VOL_LO | −0.45 | 7 | 1 |
| UNF×DI×VOL_HI | +6.91 | 21 | **14** |
| UNF×DI_ADX×VOL_HI | +5.34 | 24 | **14** |
| MOM×VOL_HI | −2.98 | 4 | 2 |
| MOM×VOL_LO | +1.19 | 8 | 4 |
| MOM×DI×VOL_HI | +2.63 | 14 | 7 |
| MOM×DI_ADX×VOL_HI | +4.21 | 16 | 8 |
| RAND×VOL_HI | +0.49 | 2 | 1 |
| RAND×VOL_LO | 0.00 | 0 | 0 |
| RAND×DI×VOL_HI | +6.71 | 79 | **65** |
| RAND×DI_ADX×VOL_HI | +6.96 | 73 | **56** |

**Domain × base on interaction only (DI× / DI_ADX×):**

| Domain × base | med mean | med lift | CI+ / 80 | powered CI+ |
|---|---:|---:|---:|---:|
| 1h UNF | +0.75 | +0.77 | 6 | 6 |
| 1h MOM | −1.24 | +0.58 | 5 | 5 |
| 1h RAND | +1.06 | +0.99 | 45 | 45 |
| **4h UNF** | **+17.5** | **+18.1** | **22** | **16** |
| 4h MOM | +10.7 | +14.4 | 18 | 10 |
| 4h RAND | +17.9 | +19.0 | 74 | 62 |
| 1d UNF | +9.9 | +9.6 | 17 | 6 |
| 1d MOM | −0.1 | −7.8 | 7 | 0 |
| 1d RAND | +6.4 | +3.2 | 33 | 14 |

**Interpretation (spdr-lane):**

- **UNF:** honest A5 CIs still produce a **coherent 4h interaction region** (BTC+SOL ladders; DI_ADX adds BTC full + SOL 1–4×). Not a broad-grid lottery after A5.  
- **MOM:** thinner; K≥3 regions exist on 4h interaction but multi-symbol / multi-hold is patchier (5 cells each modality).  
- **RAND:** ruler — HTF polarity+vol gate **systematically** beats random-sign seed means (121 powered interaction CI+). Supports mechanism “HTF state is informative,” **not** a deployable base.  
- Pooled CI+ **266** is **disclosure-only**; RAND supplies **154/266**.

### 3.7 Amplifier vs frozen SPDR-004 (binding claim)

Source: `amplifier_vs_spdr004.parquet` re-derived → `analyst_amplifier*`. 720 rows = all DI×VOL_HI / DI_ADX×VOL_HI cells vs frozen DI / DI_ADX at same (symbol × domain × hold × base).

| Scope | n | Value |
|---|---:|---|
| Amplifier rows | 720 | all interaction cells |
| Powered lift-CI+ interaction | **164** | — |
| Of those with `amp_lift − frozen_lift > 0` | **160 / 164** | **97.6%** |
| Med amp lift Δ (all) | — | **+4.02** bps |
| Med amp lift Δ (powered CI+) | — | **+11.1** bps |
| Med interaction lift (powered CI+) | — | **~15** bps class |
| Med frozen lift (powered CI+) | — | **~3–5** bps class |

**By filter (powered CI+):**

| Filter | n CI+pow | amp>0 | med Δ lift | med int lift | med frozen lift |
|---|---:|---:|---:|---:|---:|
| DI×VOL_HI | 86 | **85** | **+12.1** | +14.7 | +1.4 |
| DI_ADX×VOL_HI | 78 | **75** | **+10.8** | +15.7 | +4.9 |

**By base (powered CI+):** UNF 28/28 amp>0 (med Δ **+15.1**); MOM 15/15; RAND 117/121.

**By domain (powered CI+):** 1h med Δ +2.8; **4h +15.1**; 1d +32.2 (sparse).

#### Example: SOL 4h UNF DI×VOL_HI vs frozen DI

| hold | int lift | frozen DI lift | amp Δ | int CI low | frozen CI low |
|---:|---:|---:|---:|---:|---:|
| 0.5× | 12.1 | 4.8 | **+7.3** | +0.35 | +0.38 |
| 1× | 23.3 | 8.4 | **+14.9** | +4.99 | +0.79 |
| 2× | 37.4 | 10.9 | **+26.5** | +5.95 | −5.0 |
| 4× | 77.7 | 27.7 | **+50.0** | +45.3 | −5.3 |

#### Example: BTC 4h UNF DI×VOL_HI vs frozen DI

| hold | int lift | frozen DI lift | amp Δ | int CI low | frozen CI low |
|---:|---:|---:|---:|---:|---:|
| 0.5× | 6.9 | 0.4 | **+6.5** | +2.21 | −1.27 |
| 1× | 13.9 | 0.8 | **+13.1** | +4.39 | −2.71 |
| 2× | 29.8 | 1.2 | **+28.6** | +13.2 | −6.78 |
| 4× | 56.0 | 4.1 | **+51.9** | +26.6 | −10.2 |

**BTC frozen DI did not clear A5 CIs; interaction does** — pure amplifier / selection on high-vol regime for the directional edge.

#### Example: BTC 4h UNF DI_ADX×VOL_HI vs frozen DI_ADX

| hold | int lift | frozen lift | amp Δ | int CI low | frozen CI low |
|---:|---:|---:|---:|---:|---:|
| 0.5× | 8.7 | 2.4 | **+6.3** | +3.70 | −0.18 |
| 1× | 17.5 | 4.7 | **+12.8** | +7.40 | −0.46 |
| 2× | 36.5 | 11.0 | **+25.4** | +17.7 | −0.33 |
| 4× | 65.4 | 15.6 | **+49.7** | +35.6 | −6.67 |

#### Example: SOL 4h UNF DI_ADX×VOL_HI vs frozen DI_ADX (SPDR-004 promote cluster)

| hold | int lift | frozen lift | amp Δ | int CI low | frozen CI low |
|---:|---:|---:|---:|---:|---:|
| 0.5× | 11.2 | 6.7 | **+4.6** | −3.29 | +0.35 |
| 1× | 21.7 | 12.0 | **+9.7** | +0.89 | +0.64 |
| 2× | 35.3 | 22.2 | **+13.1** | +1.52 | +0.54 |
| 4× | 68.3 | 49.7 | **+18.6** | +31.4 | +8.94 |

Even where frozen DI_ADX already had a ladder, **vol-high gating adds +5…+19 bps lift** and lifts absolute means (h4 50→69 bps).

**Amplifier conclusion (magnitudes):** interaction **dominates** frozen direction-only on nearly all powered CI+ cells; strongest on 4h long holds and on symbols where frozen DI alone was sub-CI (BTC).

### 3.8 Control C (joint HTF phase-shift destroy)

Collapse = emitted `destroy_collapse_frac`. Design expects ≈1 when edge requires causal HTF alignment (vol+DI+ADX jointly shifted).

| Scope | med collapse | ≥0.5 | ≥0.8 | notes |
|---|---:|---:|---:|---|
| All powered CI+ (n≈184) | **~1.02** | **~80%** | high | matches screen disclosure |
| VOL_HI powered CI+ (15) | 0.76 | 0.73 | — | mixed; some PEPE collapse <0.3 |
| VOL_LO powered CI+ (5) | 2.01 | 0.80 | — | sparse |
| DI×VOL_HI powered CI+ (86) | **0.96** | **0.77** | — | — |
| DI_ADX×VOL_HI powered CI+ (78) | **1.06** | **0.88** | — | strongest |
| BTC 4h UNF DI×VOL_HI (4) | **0.80** | 4/4 | 3/4 | 0.79–0.90 |
| BTC 4h UNF DI_ADX×VOL_HI (4) | **0.84** | 4/4 | 4/4 | 0.84–0.92 |
| SOL 4h UNF DI×VOL_HI (4) | **0.63** | 4/4 | 0/4 | 0.55–0.69 (partial residual) |
| SOL 4h UNF DI_ADX×VOL_HI (4) | **0.69** | 4/4 | 0/4 | 0.63–0.78 |

**Read:** promote BTC clusters show **strong collapse** (edge dies under joint destroy). SOL interaction clusters collapse **0.55–0.78** — non-vacuous but leaves residual mean; not pure look-ahead (G1 causal) but weaker tripwire clean than SPDR-004 SOL DI_ADX (~1.05). Residual is consistent with selection of high-vol epochs that retain some absolute move even after feature scramble — still **destroys most of the edge**.

### 3.9 K=3 cluster scan (THIS grid only)

Membership (analyst code): powered ∧ lift>0 ∧ (lift_ci_low>0 ∨ (RAND ∧ battery_rank≥0.9)); region = domain × htf_filter; scopes UNF/MOM/RAND/ALL_BASES. **No SPDR-004 cells in K.**

#### Primary promote-facing (UNF / MOM, n≥3)

| Domain | Filter | Base | n | n_sym | n_hold | symbols | med mean | med lift | med coll | n mean>own floor |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|
| **4h/15m** | **DI×VOL_HI** | **UNF** | **8** | **2** | **4** | **BTC, SOL** | **26.5** | **26.6** | **0.74** | **6/8** |
| **4h/15m** | **DI_ADX×VOL_HI** | **UNF** | **8** | **3** | **4** | **BTC, ETH, SOL** | **29.0** | **28.5** | **0.84** | **6/8** |
| 4h/15m | DI×VOL_HI | MOM | 5 | 4 | 2 | APT,BTC,DOGE,SOL | 49.0 | 56.6 | 0.91 | (see table) |
| 4h/15m | DI_ADX×VOL_HI | MOM | 5 | 2 | 4 | BTC, SOL | 32.0 | 33.2 | 0.85 | — |
| 1h/5m | DI×VOL_HI | UNF | 3 | 1 | 3 | BTC | 2.6 | 2.5 | 1.82 | 0 |
| 1h/5m | DI_ADX×VOL_HI | UNF | 3 | 2 | 2 | BTC, OP | 13.0 | 13.7 | 1.64 | mixed |
| 1h/5m | VOL_HI | UNF | 7 | 2 | 4 | PEPE, OP | 20.0 | 21.0 | 1.12 | mixed / drift |
| 4h/15m | VOL_HI | UNF | 4 | 2 | 4 | APT, XRP | 54.0 | 56.5 | 0.53 | high means, thin n |
| 1d/1h | DI× / DI_ADX× | UNF | 3 each | 2 | ≤2 | SOL/LINK/BTC | large | large | mixed | sparse / thin n |

#### RAND ruler clusters (not strategies)

| Domain | Filter | Base | n | n_sym | med lift |
|---|---|---|---:|---:|---:|
| 4h/15m | DI×VOL_HI | RAND | **32** | **10** | **+16.2** |
| 4h/15m | DI_ADX×VOL_HI | RAND | **30** | **9** | **+19.2** |
| 1h/5m | DI× / DI_ADX× | RAND | 25 / 20 | 6–8 | +3–5 |

**Neighbourhood:**

- **UNF 4h DI×VOL_HI:** multi-hold **and multi-symbol (BTC+SOL)** — stronger neighbourhood than SPDR-004’s SOL-only DI_ADX.  
- **UNF 4h DI_ADX×VOL_HI:** BTC full ladder + SOL h1–h4 + ETH partial → **3 symbols** under CI+ membership.  
- VOL standalone K≥3 UNF regions exist (PEPE/OP 1h; APT/XRP 4h) but are **drift-exposed / thin-n / non-primary-mechanism** relative to interaction.  
- VOL_LO: **no** clean UNF K=3 primary ladder.

### 3.10 Money-unit floor (measured spreads)

Pins from `unit_pin.json` `train_median_spread_bps` (examples):

| Symbol | SpreadBps med | Floor 4h/15m ×1 (~4h) |
|---|---:|---:|
| BTCUSDT | 0.30 | **~11.8** |
| ETHUSDT | 0.48 | **~12.0** |
| SOLUSDT | 1.63 | **~13.1** |
| DOGEUSDT | 1.65 | ~13.2 |
| 1000PEPEUSDT | 1.72 | ~13.2 |
| OPUSDT | 2.87 | ~14.4 |

**Powered CI+ vs own floor:** mean > own floor **n_mean_above** reported in `analyst_headline.json` / `analyst_money_floor.*`. Interaction powered CI+: **93/164** means above own measured floor.

**Promote clusters:**

| Cluster | med mean | floor min (cluster) | money read |
|---|---:|---:|---|
| UNF 4h DI×VOL_HI (BTC+SOL, 8 cells) | **26.5** | ~11.6 | **above**; h0.5 sub-floor on both; h1+ clear |
| UNF 4h DI_ADX×VOL_HI (BTC+ETH+SOL) | **29.0** | ~11.6 | **above**; short holds mixed |
| SOL DI×VOL_HI h4 | 78.2 | 14.6 | **clear by ~63 bps** |
| BTC DI_ADX×VOL_HI h4 | 66.0 | 13.3 | **clear by ~53 bps** |

**vs SPDR-004 GAP=2 floors:** measured majors are **lower floors** (~11.8–13.1 vs ~13.5) — money clearance is **more comfortable** for BTC/ETH/SOL at mid/long holds; short holds (0.5×) remain characterisation / sub-floor.

### 3.11 Multiplicity

- 1440 treatment cells; promote = **cluster K≥3**, not max cell.  
- Pooled CI+ 266 / powered 184 is **disclosure-only** (L-03).  
- RAND supplies majority of CI+; UNF+MOM powered CI+ = **62** (41+21).  
- Interaction filters hold **164** of powered CI+; VOL standalone only **20**.  
- Chance-rate: UNF interaction powered CI+ **28/240** ≈ 12% of UNF×interaction cells — above naive 5% mass, concentrated on 4h BTC/SOL ladders rather than uniform scatter.

### 3.12 Fragility (L-20)

| Check | Result |
|---|---|
| UNF CI+ with seed-band straddle of 0 | **3/70**: BTC 1h h1 DI×VOL_HI (ci_low +0.05); ETH 4h h2 DI_ADX×VOL_HI (+0.40); SOL 4h h0.5 DI×VOL_HI (+0.35) |
| BTC 4h UNF interaction ladders seed bands | **all >0** on both filters |
| SOL 4h DI×VOL_HI h1–h4 | seed bands **>0** |
| SOL 4h DI_ADX×VOL_HI h1–h2 | seed_lo thin (+0.13 / +0.54) but >0; h4 solid (+30.7) |
| 1d unpowered mass | 308/480 — characterisation only |
| lift_ci NaN | 8 LINK 1d VOL_LO n=1 unpowered only |

### 3.13 Symbol heterogeneity

| Symbol | CI+ / 144 | med lift | med mean |
|---|---:|---:|---:|
| BTCUSDT | **55** | +4.80 | +5.64 |
| SOLUSDT | **47** | +9.79 | +9.37 |
| OPUSDT | 30 | +8.48 | +11.19 |
| ETHUSDT | 27 | +2.37 | +1.81 |
| 1000PEPEUSDT | 24 | +1.35 | +1.40 |
| LINKUSDT | 22 | +1.08 | −0.25 |
| APTUSDT | 21 | −0.51 | −0.48 |
| DOGEUSDT | 17 | −1.92 | −2.55 |
| XRPUSDT | 13 | −0.73 | −1.50 |
| LTCUSDT | 10 | −0.42 | −1.73 |

**4h interaction powered CI+ density:** BTC **22/24**, SOL **17/24**, ETH 8/24, others 1–8. LTC nearly null on interaction 4h. **BTC + SOL jointly carry the promote story** (vs SPDR-004 SOL-only UNF).

---

## 4. Evidence FOR the hypothesis

Hypothesis (design §1): HTF **volatility regime** conditions LTF entry quality × capture scale — standalone and/or as **amplifier** on DI / DI_ADX — under causal t−1 rules; promote = coherent K≥3 clusters on THIS grid.

1. **Interaction filters dominate location.**  
   Med lift DI×VOL_HI **+5.14** / DI_ADX×VOL_HI **+5.81** vs VOL_HI **+0.89** / VOL_LO **−0.02**. Powered CI+: **86+78** vs **15+5**.

2. **Amplifier claim holds against frozen SPDR-004.**  
   **160/164** powered CI+ interaction cells have lift **above** frozen DI/DI_ADX. Med Δ on those cells **+11.1 bps**. BTC 4h UNF: frozen DI lift CI fails zero at all holds; interaction clears all four holds with amp Δ **+6.5 → +51.9** bps.

3. **Multi-symbol UNF K≥3 on 4h interaction (stronger neighbourhood than SPDR-004).**  
   DI×VOL_HI UNF: **BTC+SOL**, 8 cells, 4 holds, med lift **+26.6**, med mean **+26.5**. DI_ADX×VOL_HI UNF: **BTC+ETH+SOL**, 8 cells, med lift **+28.5**.

4. **Capture-scale monotone ladders on liquid majors.**  
   BTC/SOL 4h UNF interaction means rise ~7→57 / 11→78 across 0.5×→4× with CI-honest lift (subject to SOL DI_ADX h0.5 miss). Aligns with P-14 capture-scale axis.

5. **Control C non-vacuous on promote cores.**  
   BTC ladders collapse **0.79–0.92**; DI_ADX×VOL_HI powered CI+ med collapse **1.06**, **88% ≥0.5**. Joint vol+DI+ADX destroy kills most of the edge.

6. **Money floors (measured, not GAP=2):** cluster med means **~26–29 bps** vs floors **~11.6–13.3**; h1+ holds clear own floors on BTC/SOL promote cells. Long holds clear by tens of bps.

7. **RAND ruler:** 4h interaction RAND clusters n=30–32 across 9–10 symbols, med lift **+16–19** — HTF polarity under high vol is not random-sign noise.

8. **VOL_LO compression:** near-zero median, almost no powered CI+ — consistent with “low-vol regimes do not scale capture,” without inventing a reverse trade.

9. **Integrity 14/14 + A5 methods + membership identity with SPDR-004** — numbers are not an accounting artifact or fence breach.

---

## 5. Evidence AGAINST the hypothesis

1. **Standalone VOL_HI / VOL_LO do not form clean promote cores on majors.**  
   SOL/BTC 4h UNF vol ladders fail lift CI. VOL_HI UNF K≥3 sits on PEPE/OP (1h, drift-exposed) and APT/XRP (4h, thin n) — not the liquid-core interaction story. If hypothesis required **vol alone** to select harvestable bars, evidence is weak.

2. **RAND dominates CI+ mass (154/266).**  
   Broad “grid works” reading confounds ruler with UNF/MOM. Design promotes clusters — still, multiplicity pressure on any single non-cluster cell is high (1440 cells).

3. **SOL interaction Control C collapse is incomplete (0.55–0.78).**  
   Residual post-destroy mean remains; weaker leak-clean signature than SPDR-004 SOL DI_ADX (~1.05) or BTC interaction here (~0.8–0.9). Leaves room for partial non-HTF residual / regime selection.

4. **Short holds often sub-floor.**  
   BTC/SOL 4h h0.5 means 7–11 bps < measured floors ~11.6–12.9. Capture-scale edge is **long-hold**; short-hold CI+ is characterisation, not money.

5. **Fragility at ladder edges.**  
   SOL DI×VOL_HI h0.5 and ETH DI_ADX×VOL_HI h2 seed bands straddle 0; SOL DI_ADX×VOL_HI h0.5 lift CI fails. Promote body is h1–h4, not every rung.

6. **1d/1h heavily unpowered (308/480); MOM 1d interaction powered CI+ = 0.**  
   Long calendar grain does not deliver a powered multi-base story.

7. **UNF×VOL_HI drift exposure.**  
   Long-only high-vol gate can ride TRAIN bull path; RAND×VOL_HI nearly null. Standalone UNF vol CI+ should not be read as causal HTF conditioning without the against-drift ruler.

8. **Symbol vetoes remain.**  
   LTC thin; XRP/DOGE med lifts negative overall; ETH mid-pack. Multi-symbol neighbourhood is **BTC+SOL (+ETH partial)**, not all-ten.

9. **Amplifier is not a formal joint CI of (interaction − frozen).**  
   Table is disclosure comparison of point lifts / separate CIs. 4/164 powered CI+ cells have amp Δ ≤ 0 — small but non-zero failure mass.

10. **No per-year split** — TRAIN path dependence (esp. SOL/BTC 2022–2023) untested at bar level.

11. **XENA still blocked on INFR-014** — even a positive disposition is availability-only; not a tradability certificate.

---

## 6. Anomalies & open questions

| Item | Note | Suggested probe |
|---|---|---|
| SOL collapse 0.55–0.69 on DI×VOL_HI | residual after joint destroy | bar-level destroy anatomy; half-sample by year |
| APT 4h UNF VOL_HI means 70–134 | huge, n=132–255 | leave-one-symbol; check membership occupancy |
| PEPE/OP 1h UNF VOL_HI cluster | drift-exposed long-only | require RAND confirmation before any weight |
| ETH 4h DI_ADX seed straddle at h2 | thin CI | more battery seeds / longer history |
| 4/164 amp Δ ≤ 0 | which cells? | `analyst_amplifier` filter amp_lift_pos==False |
| Effective catalog start ~2022-07 for many alts | truncated N | disclose in any XENA scope |
| No TEST/holdout | by design | counted TEST only after XENA + INFR-014 |

**Falsification probes for headlines:**

- Drop BTC **and** SOL → does any UNF 4h interaction K≥3 remain?  
- Compare amp table only where **both** interaction and frozen are powered CI+ (joint clearance).  
- Recompute money floors under stress=1.5× spread.  
- Control C non-derangement would invalidate collapse (asserted 0 fixed points).

---

## 7. Recommended disposition (NOT final — operator decides)

### Factual promote checklist (design §5 / pack form)

| Clause | UNF × 4h × DI×VOL_HI (BTC+SOL) | UNF × 4h × DI_ADX×VOL_HI (BTC+SOL+ETH) |
|---|---|---|
| Cluster K≥3 CI-honest | **Met (n=8, 2 sym, 4 holds)** | **Met (n=8, 3 sym)** |
| Neighbourhood | **Hold + multi-symbol** | **Hold + multi-symbol (ETH partial)** |
| Money floor (measured) | **Cluster med mean 26.5 ≫ floor_min ~11.6**; h0.5 sub-floor | **med 29.0**; short holds mixed |
| Control C | BTC strong (~0.8–0.9); SOL partial (~0.55–0.7) | BTC strong (~0.84–0.92); SOL ~0.69 |
| Amplifier vs frozen DI/DI_ADX | **Strong (BTC newly CI+; SOL +7…+50 bps)** | **Strong (BTC newly CI+; SOL +5…+19 on top of frozen)** |

**VOL_HI / VOL_LO standalone:** no primary liquid multi-symbol promote core → **not** the mechanism to graduate alone.  
**MOM:** thin K≥3 on 4h interaction — secondary texture.  
**RAND:** multiple large K≥3 — ruler evidence only.

### Recommendation

**Recommended disposition: `WORTH_EXPLORING`**

**Driven by (top 3 FOR):**

1. **Amplifier vs frozen SPDR-004:** 160/164 powered CI+ interaction cells beat direction-only; BTC 4h UNF goes from frozen CI-fail to full 4-hold CI+ ladders under VOL_HI gating.  
2. **Multi-symbol UNF K≥3 on 4h interaction (BTC+SOL; DI_ADX adds ETH)** with monotone capture-scale means and measured-floor clearance at h1+.  
3. **Control C joint destroy collapses BTC promote cores (0.79–0.92) and majority of interaction CI+ (≥0.5 on ~77–88%).**

**Top 3 AGAINST (still disclosed):**

1. Standalone vol is weak / drift-contaminated — mechanism is **direction × high-vol**, not vol alone.  
2. SOL destroy collapse incomplete; ladder-edge seed fragility; short holds sub-floor.  
3. RAND-heavy CI+ mass + no bar-level year split → generalisation risk for XENA.

**Would change if:** leave-one-year kills BTC+SOL ladders; amp Δ fails when requiring joint CI+; T1 stress floors rise above cluster med means; multi-symbol neighbourhood collapses to single-name under stricter membership.

**Binding caveats for any later XENA-HTFCAP-001 design:**

1. Scope = **interaction filters (DI×VOL_HI / DI_ADX×VOL_HI)**, not bare VOL_HI/LO.  
2. Primary grain = **4h/15m**, holds **≥1× HTF** for money-facing characterisation.  
3. Multi-name start = **BTC + SOL** (ETH secondary); no all-universe claim.  
4. L-21 floors already measured — re-pin if fee/spread map changes.  
5. **INFR-014 pin still blocks XENA** — WORTH_EXPLORING is availability justification only.  
6. Joint family read with SPDR-004 at checkpoint — not inside this screen’s K.

**Final verdict is the operator's.** Suggested probes: (1) SOL/BTC leave-one-year bar re-emit; (2) amp joint-CI filter table; (3) destroy residual anatomy on SOL; (4) XENA design only after INFR-014 + explicit interaction scope.

---

## 8. Artifact index

| Path | Content |
|---|---|
| `results/cells.parquet` | Source screen emission (1440 treat + 240 base) |
| `results/amplifier_vs_spdr004.parquet` | Interaction vs frozen SPDR-004 DI/DI_ADX |
| `results/unit_pin.json` | Measured ATR + SpreadBps floors |
| `results/integrity.json` | PASS 14/14 + golden G1–G3 |
| `results/analyst_headline.json` | Headline counts + amplifier + K3 |
| `results/analyst_facets.*` | Per-facet CI+/medians |
| `results/analyst_lift_ci_pos.*` | All CI+ cells |
| `results/analyst_clusters_k3.*` | K=3 scan THIS grid |
| `results/analyst_amplifier.*` | Amp rows + flags |
| `results/analyst_amplifier_facets.*` | Amp summaries |
| `results/analyst_promote_ladders.*` | BTC/SOL/ETH hold ladders + floors |
| `results/analyst_money_floor.*` | Per-cell measured floor compare |
| `results/analyst_control_c.*` | Collapse table |
| `results/analyst_base_conditional.*` | domain×base×filter×hold |
| `results/analyst_hold_ladder.*` | Full hold grid |
| `analysis_code/spdr006_analysis.py` | Re-derive (no screen_code import) |

**Integrity:** PASS 14/14 · **Methods:** A1–A5 two-sample only · **Amplifier table:** present · **Money floor:** measured spreads · **K=3:** this grid only.

---

## 9. Review addendum (independent verification pass, 2026-07-17)

Second analyst pass; re-derivation code `analysis_code/spdr006_review_verify.py` reads only raw
`cells.parquet` / `amplifier_vs_spdr004.parquet` / `unit_pin.json` (no screen_code, no prior
analyst script imports).

**Reproduced exactly (no discrepancies):** cell counts (1440/240; 383 unpowered); pooled
medians (+1.07 mean / +1.51 lift); CI+ 266 total / 184 powered; filter-axis table (§3.3);
base-conditional table incl. one CI method per base and `battery_minus_seeds` = 0; all four
BTC/SOL 4h UNF interaction ladders (§3.5) to 2 dp incl. collapse fractions and seed-range lows;
amplifier 160/164 powered CI+ with amp Δ > 0, med Δ +11.1 (powered CI+) / +4.02 (all 720),
per-filter and per-base splits; Control C medians and ≥0.5 fractions (§3.8); money floor
93/164 interaction powered CI+ above own measured floor; UNF seed-straddle 3/70 (same three
cells); 8 NaN lift-CI all LINK unpowered; K=3 membership counts and symbol sets (§3.9).
Integrity/summary artifacts internally consistent (fence `35d3375e…`, max_exit < train_end,
membership sha byte-identical to SPDR-004).

**New findings from the review probes:**

1. **Drop-BTC+SOL falsification probe (proposed in §6) executed:** removing BTC and SOL leaves
   **1** UNF 4h interaction member cell (ETH DI_ADX×VOL_HI h2) — K≥3 dies entirely. The promote
   story is strictly BTC+SOL-concentrated; treat "multi-symbol" as exactly two liquid names.
2. **ETH's DI_ADX cluster membership is a single fragile cell:** ETH contributes only h2, and
   that is one of the three seed-straddle cells (seed_lo −1.01). The DI_ADX×VOL_HI cluster
   should be read as BTC (full ladder) + SOL (h1–h4); "BTC+ETH+SOL / 3 symbols" is technically
   true but overstates ETH.
3. **The 4/164 amp Δ ≤ 0 cells identified** (open question §6): all four are 1000PEPE 1h RAND
   short-hold cells — none touch the promote clusters or UNF/MOM.

None of this changes the recommended disposition (`WORTH_EXPLORING`); items 1–2 sharpen the
binding caveat "multi-name start = BTC + SOL (ETH secondary)" — ETH is weaker than the §7
checklist row suggests. Final verdict remains the operator's.

---

## 10. OPERATOR DISPOSITION (2026-07-17, operator-signed)

**WORTH_EXPLORING** — frozen promote rule (design §5, K=3 on THIS grid) met on the 4h/15m UNF
interaction clusters: **DI×VOL_HI (BTC + SOL, 8 cells, all 4 holds)** and **DI_ADX×VOL_HI
(BTC full ladder + SOL h1–h4)**, med lift +26.6 / +28.5 bps, monotone capture-scale ladders,
measured-floor clearance at h1+, Control C collapse strong on BTC (0.79–0.92), amplifier
claim satisfied against frozen SPDR-004 (160/164 powered CI+ interaction cells above
direction-only; BTC goes frozen CI-fail → full 4-hold CI+ under VOL_HI gating).

**Binding caveats carried into any XENA-HTFCAP-001 design (supersede/extend SPDR-004 §9 where
overlapping):**
1. Scope = interaction filters (DI×VOL_HI / DI_ADX×VOL_HI) only — standalone VOL_HI/VOL_LO
   is not a promote mechanism (weak, drift-contaminated).
2. Multi-name = **BTC + SOL exactly** (review §9: drop-both probe kills K≥3; ETH membership is
   a single seed-fragile cell — secondary at best).
3. Primary grain 4h/15m, holds ≥1× HTF for money-facing characterisation; h0.5 sub-floor.
4. SOL Control C collapse incomplete (0.55–0.78) — destroy-residual anatomy is an open probe.
5. No per-year split — TRAIN path dependence untested at bar level.
6. Availability-only; no tradability claim; XENA gate remains blocked on INFR-014 pin. Joint
   family read with SPDR-004 happens at checkpoint, not here.

0 slots, 0 counted reads consumed. Screen was code-asserted (no QA subagent per SPDR lane);
integrity 14/14; independent review pass (§9) reproduced all headline numbers.
