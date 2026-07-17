# Data Analysis: SPDR-005 (CF-EPSOSC-001 TRAIN availability screen)

**Role:** fresh-context data-analyst (SPDR stage 5).  
**Raw inputs:** `results/cells.parquet` (3240), `vr_facet.parquet`, `grid_twin.parquet`, `membership.parquet`, `unit_pin.json`, `integrity.json` (12/12), `summary.json`.  
**Re-derive code:** `analysis_code/spdr005_analysis.py` → `results/analyst_*.{parquet,csv,json}`.  
**Subordinate (not authority):** `screen.md`.  
**Primary unit (L-16):** gross open-to-open **bps/episode** — fixed-H never family-terminal.  
**K=3 promote read:** **only** `is_primary_promote=True` (**640** cells). Full 3240 = disclosure.  
**Membership rank key:** trailing 24h **base volume** (design §5.1) — primary 10 are meme/high-volume alts, not notional majors.  
**XENA:** still blocked on **INFR-014**; any future limit-entry path must honor design §2.3 **L-27**.

Disposition recommendation below is **experiment hypothesis only** — not family status, not final.

---

## 1. Integrity gate (SPDR form — Phase 0)

SPDR carve-out: **no** `estimand_validation.json`. Integrity = code-asserted self-check + `integrity.json` **12/12 PASS**.

| Check | Result | Evidence |
|---|---|---|
| Estimand validation artifact | **N/A (SPDR)** | design / spdr-lane |
| `integrity.json` 12/12 | **PASS** | `all_pass: true`, `pass_count: 12` |
| Registration (item 1) | **PASS** | REGISTERED + multiplicity + 0 slots |
| TRAIN fence (item 2) | **PASS** | max_exit_ns < train_end_ns; holdout_start 2025-01-08 sealed |
| Causal t−1 (item 3) | **PASS** | features ≤ t−1; entry open after confirm |
| Market entry only / P-10 (item 4) | **PASS** | no limit/passive path in screen_code |
| P-12 ban (item 5) | **PASS** | treatment = STRETCH/VOLARM only; GRID_TWIN disclosure |
| L-16 episode-native primary (item 6) | **PASS** | all rows `primary_unit = bps_per_episode` |
| Control A ≥25 seeds (item 7) | **PASS** | seeds 2000–2024 regenerable |
| L-28 derangement Control B (item 8) | **PASS** | 0 fixed points |
| Per-stratum emission (item 9) | **PASS** | 3240 treatment cells |
| L-21 unit_pin.json (item 10) | **PASS** | measured TRAIN ATR + spreads |
| Membership causality (item 11) | **PASS** | daily top-10 base volume ≤ t−1 |
| Golden G1–G3 (item 12) | **PASS** | G1/G2/G3 all `ok: true` |
| AMENDMENT-1 censoring | **APPLIED** | `censored_frac` / `censored_flag_gt20` on cells; silent drop banned |
| Holdout / TEST untouched | **PASS** | TRAIN band only |
| Price-primary Nautilus | **N/A (SPDR)** | vectorised Python by design |
| No local adjudication P&L | **PASS** | screen metrics via declared bps/episode + `xen.evaluation` patterns; analyst re-derives from parquet |

### Golden traces

| ID | Result | Key values |
|---|---|---|
| G1 | PASS | 15m STRETCH stretch-up; `forming_bar_not_used`; n_ep=331; mean **+22.7** bps/ep; n_censored=0 |
| G2 | PASS | 1h VOLARM TIME clear; exit open < train_end; n_ep=11; mean **−161.6** bps/ep |
| G3 | PASS | 2023-04-02 rebalance top-10 matches trailing_24h_base_volume expected list |

### Unit pin (L-21) — measured TRAIN spreads (RT bps)

| Symbol | SpreadBps | Floor proxy @8h (fee 11 + fund GAP) |
|---|---:|---:|
| DOGEUSDT | 1.65 | ~13.7 |
| 1000PEPEUSDT | 1.72 | ~13.7 |
| XRPUSDT | 2.06 | ~14.1 |
| SHIB1000USDT | 2.67 | ~14.7 |
| JASMYUSDT | 2.83 | ~14.8 |
| GALAUSDT | 3.38 | ~15.4 |
| RSRUSDT | 5.21 | ~17.2 |
| SLPUSDT | 9.64 | ~21.6 |
| 1000BTTUSDT | 12.67 | ~24.7 |
| 1000BONKUSDT | 15.33 | ~27.3 |

Fee RT taker = **11.0** bps; funding coverage = **GAP** (disclosed). Full: `unit_pin.json`.

### Provenance (verdict-bearing columns)

| Object | Inputs | Causal? |
|---|---|---|
| Anchor / ATR / stretch / vol-arm | ≤ t−1 on domain LTF | yes (item 3 + G1) |
| Entry | market at open of bar after confirm | yes (P-10) |
| `R_ep_bps` | Direction · (Open[exit]−Open[entry])/Open[entry]·1e4 | open-to-open episode |
| Censor | open at train_end → excluded from mean; fraction disclosed | A1 |
| Lift | treatment mean − Control A battery mean | two_sample_block_vs_battery |
| Control B | derangement of episode labels; collapse fraction | L-28 |
| Membership | trailing 24h **base volume** ≤ t−1 | G3 |

---

## 2. Question list

| # | Question | Status |
|---|---|---|
| Q1 | Integrity 12/12, G1–G3, P-10, P-12, L-16, A1, L-28, unit_pin? | **ANSWERED** §1 |
| Q2 | Per-stratum magnitudes (primary focus; full disclosure)? | **ANSWERED** §3.1–3.4 |
| Q3 | VR coupling design §5.5 — flat? half-symbol rule? | **ANSWERED** §3.5 |
| Q4 | Censored fractions (A1) by clear policy? | **ANSWERED** §3.6 |
| Q5 | GRID_TWIN structure identity? | **ANSWERED** §3.7 |
| Q6 | Control A battery ranks / lift CIs? | **ANSWERED** §3.8 |
| Q7 | Control B collapse on promote candidates? | **ANSWERED** §3.9 |
| Q8 | Hold/duration path diagnostics (median duration, clear mix)? | **ANSWERED** §3.10 |
| Q9 | Money floors with measured spreads? | **ANSWERED** §3.11 |
| Q10 | K=3 on primary slice only? | **ANSWERED** §3.12 |
| Q11 | Evidence FOR and AGAINST equal diligence? | **ANSWERED** §4–5 |
| Q12 | What would make headline numbers wrong? | **ANSWERED** §6 |
| Q13 | Per-year / regime stability of episode series? | **UNANSWERED** — cell aggregates only; needs bar-level re-emit |
| Q14 | Cross-correlation of co-timed episodes across symbols? | **UNANSWERED** — no joint path emission |

---

## 3. Quantified facets (magnitudes — not verdicts)

All numbers re-derived from parquet via `analysis_code/spdr005_analysis.py`.  
**Promote candidate** = primary cell with `unpowered=False` **and** `lift_ci_low > 0`.

### 3.1 Grid inventory

| Slice | n | med mean bps/ep | med lift bps | Lift CI+ | Powered CI+ / promote_cand | Unpowered | flag_gt20 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full treatment | 3240 | **+5.69** | **+4.92** | 557 | 444 | 897 | 94 |
| **Primary promote** | **640** | **−11.42** | **−9.18** | 126 | **86** | 280 | **0** |

Pooled full-grid positive medians are **disclosure-only** (L-03). Binding location for K-read is primary: **negative median**, with a **right tail of coherent positive lift** (86/640 ≈ 13.4% promote_cand).

Primary also: lift CI− = **115**; mean point-neg = 346/640; mean < −50 bps ≈ 39%; mean > +20 bps ≈ 35% — **bimodal / heavy-tailed**, not a wash around zero.

### 3.2 Primary by domain (binding ladder)

| Domain | n | powered | promote_cand | med mean | med lift | med n_ep | med dur bars |
|---|---:|---:|---:|---:|---:|---:|---:|
| **15m** | 320 | 263 | **69** | **+3.32** | **+3.80** | ~77 started | — |
| **1h** | 320 | 97 | **17** | **−52.7** | **−46.0** | ~17.5 started | — |

**Read:** 15m carries the available positive location; 1h is sparse (223 unpowered) and negative at the median. 1h promote mass is almost entirely **STRETCH** on **XRP / 1000PEPE** (below).

### 3.3 Primary by object / side / clear / W / k

| Facet | Level | promote_cand | med mean | med lift | unpowered |
|---|---|---:|---:|---:|---:|
| object | STRETCH | 36 | −8.7 | −9.8 | 67 |
| object | VOLARM | **50** | −12.3 | −9.0 | 213 |
| side | LONG_ONLY | **54** | −2.4 | −3.9 | 144 |
| side | SHORT_ONLY | 32 | −23.8 | −23.0 | 136 |
| clear | RET_ANCHOR | 44 | −10.6 | — | 143 |
| clear | HYBRID | 42 | −12.1 | — | 137 |
| W | 96 | 40 | −2.3 | — | 135 |
| W | 192 | 46 | −22.6 | — | 145 |
| k | 2.5 | 44 | −10.6 | — | 134 |
| k | 3.0 | 42 | −12.9 | — | 146 |

**object×domain:**

| Cell | powered | promote_cand | med mean | med lift |
|---|---:|---:|---:|---:|
| STRETCH×15m | 160 | 21 | +1.3 | +1.8 |
| **VOLARM×15m** | 103 | **48** | **+9.6** | **+9.7** |
| STRETCH×1h | 93 | 15 | −41.1 | −35.2 |
| VOLARM×1h | 4 | 2 | −80.2 | −73.2 |

VOLARM×15m is the densest promote surface. VOLARM×1h is almost fully unpowered (156/160).

### 3.4 Symbol heterogeneity (primary, n=64 each)

| Symbol | promote_cand | lift CI+ (incl unpowered) | med mean | med lift | med rank | unpowered |
|---|---:|---:|---:|---:|---:|---:|
| **XRPUSDT** | **25** | 29 | **+50.7** | **+40.2** | 1.0 | 16 |
| **SHIB1000USDT** | **25** | 27 | **+35.5** | **+34.3** | 1.0 | 14 |
| **DOGEUSDT** | **17** | 17 | **+7.8** | **+7.6** | 1.0 | 15 |
| **JASMYUSDT** | **12** | 12 | −16.1 | −14.8 | 0.0 | 17 |
| 1000PEPEUSDT | 6 | 6 | −45.4 | −44.7 | 0.0 | 23 |
| SLPUSDT | 1 | 13 | +12.9 | +9.9 | 0.62 | 48 |
| RSRUSDT | **0** | 20* | −36.9 | −32.6 | 0.0 | 46 |
| GALAUSDT | **0** | 6 | −22.2 | −22.7 | 0.0 | 15 |
| 1000BONKUSDT | **0** | 4 | **−322** | **−276** | 0.0 | 38 |
| 1000BTTUSDT | **0** | 4 | **−262** | **−250** | 0.0 | 48 |

\*RSR/GALA/BONK/BTT lift-CI+ rows are **unpowered** (n_ep thin) — **not** promote candidates. SLP has 13 CI+ but only **1** powered.

**Promote-driving names:** SHIB, XRP, DOGE, JASMY (VOLARM 15m); XRP + PEPE (STRETCH 1h).  
**Hard counter-strata:** BONK, BTT (deep negative + wide spreads); GALA/RSR **zero** powered promote_cand.

Membership top by days: SHIB 521, GALA 513, DOGE 505, RSR 382, BONK 346, … — base-volume alts (design §5.1).

### 3.5 VR facet (design §5.5)

Lags {2,4,8,16} on TRAIN log-returns per symbol×domain (`vr_facet.parquet`).

| Domain | lag | med VR | frac symbols VR&lt;1 |
|---|---:|---:|---:|
| 15m | 2 | 0.951 | **0.90** |
| 15m | 4 | 0.906 | **0.90** |
| 15m | 8 | 0.883 | **0.90** |
| 15m | 16 | 0.875 | **0.90** |
| 1h | 2 | 0.987 | **0.70** |
| 1h | 4 | 0.972 | 0.70 |
| 1h | 8 | 0.949 | 0.70 |
| 1h | 16 | 0.968 | **0.60** |
| 5m | 2–16 | 0.86–0.96 | **0.90** |

**Half-symbol rule:** for primary domains {15m, 1h}, **every lag** has VR&lt;1 on ≥ half of symbols.  
**VR flat?** **NO.**

→ §5.5 stronger-evidence override (K≥3 **and** lift ci_low > MDE with Control B collapse as *extra* bar) **does not fire**. Standard K≥3 path applies. VR alone is diagnostic, not a sole gate.

### 3.6 Censoring (AMENDMENT-1)

| Slice | med censored_frac | mean censored_frac | n flag_gt20 | n any censored |
|---|---:|---:|---:|---:|
| Full 3240 | 0 | 0.019 | **94** | 542 |
| **Primary 640** | **0** | 0.0038 | **0** | 68 |
| Full RET_ANCHOR | 0 | 0.002 | 0 | 123 |
| Full **TIME** | 0 | **0.054** | **94** | 296 |
| Full HYBRID | 0 | 0.002 | 0 | 123 |
| Primary RET_ANCHOR | 0 | 0.0039 | 0 | 34 |
| Primary HYBRID | 0 | 0.0038 | 0 | 34 |

**Read:** flag_gt20 mass sits on full-grid **TIME** cells (path hits train_end before H completes), not on primary RET/HYBRID. Primary promote slice is clean on A1 (med 0, zero >20% flags). Silent drop not used.

### 3.7 GRID_TWIN (P-12 structure identity)

30 rows (10 symbols × 3 domains). Med mean **−8.36** bps; **12/30** point-positive.

| Notable positive twin | Domain | mean bps | n_ep |
|---|---|---:|---:|
| 1000BTTUSDT | 1h | +493 | 18 (sparse) |
| XRPUSDT | 1h | +78 | 123 |
| RSRUSDT | 1h | +74 | 66 |
| SHIB1000USDT | 15m | +11 | 765 |

**Structure identity:** treatment K≥3 clusters exist on **VOLARM/STRETCH** with path-endogenous clears (frac_ret_clear ≈ 0.93–1.0 on promote clusters). GRID_TWIN is **not** the sole positive structure. Sparse 1h twin positives (esp. BTT n=18) do **not** form a promote cluster under the treatment object definition. → structure-identity check **passes**.

### 3.8 Control A (random-timing battery)

- Method on all cells: `two_sample_block_vs_battery`.
- Seeds: 2000–2024 (25) on primary; disclosure battery on non-primary (screen.md).
- Primary med battery_rank ≈ **0.04** (most cells lose to random timing).
- **All 86 promote_cand have battery_rank = 1.0** (top of 25-seed battery).
- rank ≥ 0.9 on primary: **277/640** (high ranks without powered positive lift CI still exist — rank alone ≠ promote).
- Lift CI seed-band straddles 0 on promote_cand: **6/86** (MC-fragile minority; disclose).

### 3.9 Control B collapse (episode-label derangement)

On primary **promote_cand (n=86):**

| Metric | Value |
|---|---:|
| med destroy_collapse_frac | **0.951** |
| collapse ≥ 0.5 | **86/86 (100%)** |
| collapse ≥ 0.8 | **82/86 (≈95%)** |
| collapse &lt; 0.2 | **0** |

Edge **requires** stretch→clear path alignment. Control B non-vacuous and bites. Expected collapse ≈ 1 on promote surface — **met**.

### 3.10 Path / duration diagnostics (primary)

| Clear | med median_duration (bars) | med frac_ret_clear | med frac_time_clear | med n_episodes |
|---|---:|---:|---:|---:|
| RET_ANCHOR | 46.3 | **1.00** | 0.00 | 36 |
| HYBRID | 45.5 | **0.93** | 0.066 | 38 |

**K3 cluster path (object×domain×clear members):**

| Region | n | n_sym | n_k | n_w | med lift | med mean | med dur → hours | frac_ret |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| STRETCH×1h×HYBRID | 7 | 2 | 2 | 2 | **+119** | **+117** | 41 bars → **~41 h** | 1.00 |
| STRETCH×1h×RET_ANCHOR | 8 | 2 | 2 | 2 | **+113** | **+115** | ~39 bars → **~39 h** | 1.00 |
| VOLARM×15m×HYBRID | 23 | 4 | 2 | 2 | **+60** | **+64** | 82 bars → **~20.5 h** | 0.93 |
| VOLARM×15m×RET_ANCHOR | 25 | 4 | 2 | 2 | **+54** | **+59** | 76 bars → **~19 h** | 1.00 |
| STRETCH×15m×RET_ANCHOR | 10 | 3 | 2 | 2 | **+36** | **+38** | 36.5 → **~9.1 h** | 1.00 |
| STRETCH×15m×HYBRID | 11 | 4 | 2 | 2 | **+35** | **+36** | 37 → **~9.3 h** | 0.96 |

Clears are **within-episode / return-to-anchor dominated** — not cap-lock theater. HYBRID uses time-stop only as minority backup (~5–7%).

**Per-symbol neighbourhoods (n≥3 promote_cand, symbol×object×domain):** SHIB/XRP/JASMY/DOGE VOLARM 15m; XRP/PEPE STRETCH 1h; SHIB/DOGE STRETCH 15m.

### 3.11 Money floors (measured spreads)

Floor = 11 fee RT + TRAIN-median RT spread + funding GAP × (hold_h/8).

| Cluster | hold_h (from med duration) | cluster med mean | med symbol floor | mean − floor |
|---|---:|---:|---:|---:|
| VOLARM×15m (RET/HYB) | ~19–20.5 h | **+59–64** | ~15–16 | **≫ 0** |
| STRETCH×15m | ~9 h | **+36–38** | ~14–15 | **≫ 0** |
| STRETCH×1h | ~39–41 h | **+115–117** | ~18 (XRP/PEPE) | **≫ 0** |

Promote_cand money table: **86/86** mean_above_floor; **85/86** lift_above_floor.  
T1 undecidable band (|gross| &lt; 3× spread): **not** binding on promote surface (spreads 1.7–2.8 on SHIB/XRP/DOGE; gross tens of bps).  
**Caveat:** BONK/BTT floors 25–32 bps with deep negative means — irrelevant to promote clusters but show wide-spread alts are hostile substrate.

SPDR disposition is **never** a T1 tradability band (design §4).

### 3.12 K=3 promote rule (primary only) — factual checklist

Design §7 WORTH_EXPLORING requires **all** of:

| # | Criterion | Factual |
|---|---|---|
| 1 | ≥3 cells, same object family, vary k/W/symbol/domain, positive lift CI | **YES** — 6 object×domain×clear regions; densest VOLARM×15m n=23–25, 4 symbols, both k & both W |
| 2 | Neighbourhood (not lone positive) | **YES** |
| 3 | Not GRID_TWIN; path clears within episode | **YES** (§3.7, §3.10) |
| 4 | VR §5.5 substrate honesty | **YES** — VR not flat; half-symbol met |
| 5 | Money-relevant floor disclosure | **YES** — cluster med means ≫ floor |

Control B collapse on promote surface: **100% ≥ 0.5** (supporting SUPPORTED_LIFT band on those cells).

---

## 4. Evidence FOR the hypothesis

Hypothesis (design §1): coherent non-grid episode-harvest clusters show lift over matched random-timing / shuffle controls in bps/episode.

1. **Multi-symbol VOLARM×15m cluster** — 23–25 powered lift-CI+ cells; 4 symbols (SHIB, XRP, JASMY, DOGE); both k∈{2.5,3.0} and W∈{96,192}; med lift **+54 to +60** bps/episode; med mean **+59 to +64**. Bootstrap 95% CI on lift excludes zero by construction of promote_cand.
2. **STRETCH×15m secondary cluster** — 10–11 cells; 3–4 symbols; med lift **+35 to +36** bps/ep; shorter holds (~9 h).
3. **STRETCH×1h tail cluster** — XRP + PEPE; med lift **+113 to +119** bps/ep; RET_ANCHOR dominated clears.
4. **Control B collapse ≈ 1** on all 86 promote candidates (med 0.95; 100% ≥ 0.5) — edge is path-alignment, not cadence theater.
5. **Control A rank = 1.0** on all promote candidates vs 25-seed battery.
6. **VR &lt; 1** on ≥60–90% of primary-domain symbols — oscillation substrate present (soft mechanism support).
7. **Structure identity** — GRID_TWIN med −8.4; treatment clusters are STRETCH/VOLARM with within-episode clear, not hard-cap grid.
8. **Money:** cluster med means 36–119 bps vs floors ~14–20 bps at measured spreads + taker + funding GAP.
9. **A1 clean on primary** — med censored_frac 0; flag_gt20 = 0 on promote slice.
10. **Integrity 12/12** — fence, t−1, P-10, P-12, L-16, L-28, G1–G3 all pass (necessary, not sufficient).

---

## 5. Evidence AGAINST the hypothesis

1. **Primary-slice location is negative** — med mean **−11.4**, med lift **−9.2** bps/ep. Positive mechanism is a **minority tail** (86/640), not a central tendency of the predeclared promote grid.
2. **Extreme symbol concentration / counter-strata** — BONK med mean **−322**, BTT **−262**; GALA/RSR medians negative. Promote mass sits in SHIB/XRP/DOGE/JASMY (+ PEPE 1h). Not homogeneous across the membership-10.
3. **1h domain mostly fails** — med lift **−46**; 223/320 unpowered; VOLARM×1h nearly empty (4 powered). Only thin STRETCH 1h XRP/PEPE cluster works.
4. **SHORT_ONLY weaker** — med lift −23 vs LONG −3.9; fewer promote_cand (32 vs 54). One-sided fade asymmetry; not a clean two-sided oscillator.
5. **High unpowered mass** — 280/640 primary (44%); VOLARM especially (213/320). Sparse strata cannot support broad family claim.
6. **Multiplicity** — 640 primary cells; 86 CI+ powered ≈ 13%. Dependence across (symbol×params) is large; not independent 5% tests — still, chance-rate context is non-trivial without a stricter FWER design (SPDR does not claim family-wise control).
7. **Seed-band fragility** — 6/86 promote_cand have lift CI-low seed range straddling 0 (L-20 MC-fragile).
8. **Membership substrate** — base-volume ranking selects meme/high-turnover alts; edge may not transfer to majors or post-TRAIN regimes (no TEST read; no per-year split emitted).
9. **Funding × duration** — VOLARM 15m cluster holds ~19–20 h; STRETCH 1h ~40 h. Funding GAP disclosure only at SPDR; longer episodes eat into gross if funding adverse (not yet binding stress).
10. **GRID_TWIN sparse 1h positives** (BTT +493 n=18, XRP +78) — do not overturn structure identity, but warn that **some** positive gross bps appear under banned-grid shape on thin samples; reinforce that structure ID must stay explicit at XENA.
11. **Full-grid TIME censor flags (94)** — outside primary, TIME clear often fails to finish before train_end; pure time-stop is a weak structure (correctly excluded from primary).

---

## 6. Anomalies & open questions

| Item | Note |
|---|---|
| Bimodal primary distribution | ~39% mean&lt;−50 and ~35% mean&gt;+20 — “median negative + fat right cluster” story |
| RSR CI+ with negative median | thin extremes drive CI+ count without central support |
| G2 golden mean −162 bps | VOLARM 1h TIME path can be large-negative — consistent with 1h failure |
| No per-year emission | regime stability UNANSWERED |
| Cross-symbol dependence | co-timed meme moves may inflate multi-symbol cluster counts |
| INFR-014 / L-27 | XENA blocked; if any future cell uses limit/passive entry, battery needs next-open discriminating control |
| What would falsify headline K3? | (a) episode-level recompute with different ATR/anchor lag; (b) half-sample by calendar year; (c) exclude top-1 symbol from each cluster; (d) stress funding at 2× GAP |

---

## 7. Recommended disposition (experiment hypothesis only — NOT final, NOT family)

### Recommendation: **WORTH_EXPLORING**

**Driven by (design §7 factual):**
1. **K≥3 coherent clusters** on primary slice — especially **VOLARM×15m** (23–25 cells, 4 symbols, both k & W) with med lift **+54–60** bps/episode and Control B collapse **≈0.95**.
2. **VR not flat** on primary domains (half-symbol rule met at all lags) — standard promote path, not §5.5 INCONCLUSIVE override.
3. **Structure identity** holds (GRID_TWIN not sole positive; within-episode ret-clear dominates) + **money** cluster medians well above measured spread floors.

**Equal-weight counter that does *not* flip under the frozen promote rule:** primary **median is negative** and edge is **concentrated** in a few alts / 15m VOLARM — this is characterization for XENA scope, not a NOT_WORTH under §7 (NOT_WORTH = no cluster / only GRID_TWIN / pure noise).

**Would change if:**
- Calendar half-split or top-symbol drop **destroys** multi-symbol VOLARM 15m neighbourhood → lean **INCONCLUSIVE**.
- Fresh emission with majors-only membership shows null → scope-limit, not automatic family kill at this screen.
- Control B collapse falls on the cluster surface → integrity re-open.

**Not claimed:** tradability, deployability, TEST confirmation, family OPEN/RETIRE, or T1 band.

### Handoff

- Final disposition is the **operator’s**.
- **XENA still blocked on INFR-014.** If operator stamps WORTH_EXPLORING → design **XENA-EPSOSC-001** only after INFR-014 pin.
- Handoff **must** honor design **§2.3 L-27**: any limit/passive entry universe needs next-open discriminating control or marks permutation battery **inadmissible**.
- Prefer XENA seed from: **VOLARM × 15m × {RET_ANCHOR, HYBRID} × k∈{2.5,3.0} × W∈{96,192}** on high base-volume names that actually cleared (SHIB/XRP/DOGE/JASMY); treat 1h STRETCH XRP/PEPE as secondary probe; do **not** center BONK/BTT wide-spread negatives.
- Suggested probes: year-split episode means; drop-one-symbol cluster stability; funding stress ladder; explicit majors contrast membership.

---

## 8. Artifact index

| Path | Role |
|---|---|
| `analysis_code/spdr005_analysis.py` | Independent re-derive |
| `results/analyst_headline.json` | Headline magnitudes |
| `results/analyst_facets.{parquet,csv}` | Primary + full facets |
| `results/analyst_clusters_k3.*` | K=3 region scan |
| `results/analyst_money_floor.*` | Floors vs measured spreads |
| `results/analyst_top_promote.*` | Top promote_cand cells |
| `results/analyst_path_diag.*` | Duration / clear mix |
| `results/analyst_vr_by_domain_lag.csv` | VR §5.5 |
| `results/analyst_censoring.csv` | A1 fractions |
| `results/cells.parquet` | Authority emission (3240) |
| `results/integrity.json` | 12/12 PASS |
| `results/unit_pin.json` | L-21 measured |

**Final verdict is the operator’s.**

---

## 9. OPERATOR DISPOSITION (2026-07-17, operator-signed)

**WORTH_EXPLORING** — frozen promote rule met on the primary slice: **VOLARM × 15m**
cluster (23–25 cells, 4 symbols, both k ∈ {2.5, 3.0} and W ∈ {96, 192}), med lift
**+54–60 bps/episode**, Control B derangement collapse ≈0.95, GRID_TWIN not the sole
positive, within-episode ret-clear dominant, cluster medians above measured spread floors.
VR facet not flat (half-symbol rule met at all lags) — standard promote path, no §5.5
override. Post-QA check: block_h CI sign-stable on 204/205 primary powered CI+ cells
(sole flip JASMY 5m RET_ANCHOR, marginal — outside the promote cluster).

**QA (run 1, post-exec): REVISE → resolved.** Issues 1–2 ratified as design §11b
AMENDMENTS 2–3 (fixed top-10 strata by full-TRAIN membership-days, LOOSER; seed tiering
25 primary / 5 disclosure, NEUTRAL-promote). Ledger 1L/0T/2N. Issues 3–5 LOW accepted as
future tightening; 6–7 INFO carried here.

**Binding caveats for any XENA-EPSOSC-001 design:**
1. Primary pooled median is NEGATIVE (−11.4 mean / −9.2 lift bps) — the finding is a
   concentrated cluster, not broad availability; scope XENA accordingly.
2. Seed scope = VOLARM × 15m × {RET_ANCHOR, HYBRID} × k{2.5,3.0} × W{96,192} on cleared
   high-base-volume names (SHIB/XRP/DOGE/JASMY); 1h STRETCH XRP/PEPE secondary probe only;
   no BONK/BTT centring.
3. Fixed-strata selection was hindsight (AMENDMENT-2, LOOSER) — XENA universe selection
   must be causal (INFR-014 `universe_selection` deliverable).
4. Effective window ~17 months (membership starts 2022-07-15) — power note.
5. §2.3 L-27: any limit/passive entry universe requires the next-open discriminating
   control, else marks permutation battery inadmissible.
6. Availability-only; no tradability claim; XENA gate remains blocked on INFR-014 pin.
   Family action at checkpoint only.

0 slots, 0 counted reads consumed.
