# Data Analysis: SPDR-004 (CF-HTFCAP-001 TRAIN availability screen)

**Role:** fresh-context data-analyst (SPDR stage 5) after **full re-run AMENDMENTS 1–5**.  
**Raw inputs:** `results/cells.parquet` (960 rows), `membership.parquet`, `unit_pin.json`, `integrity.json`, `summary.json`.  
**Re-derive code:** `analysis_code/spdr004_analysis.py` → `results/analyst_*.{parquet,csv,json}`.  
**Subordinate (not authority):** `screen.md`.  
**Not written as operator disposition stamp:** final `WORTH_EXPLORING` / `NOT_WORTH` / `INCONCLUSIVE`.  
**Unit pin (L-21):** primary = **gross open-to-open bps/trade** (no ATR on promote facet). Disclosure ATR = LTF ATR(14)[t−1] via `xen.zigzag.wilder_atr` (`unit_pin.json`).

### Critical: A5 voids prior CI+ mass

| ID | Effect on this read |
|----|---------------------|
| A1 | UNF×filter baseline = RAND battery @ UNF cadence |
| A2 | Membership rank = trailing 24h **USDT notional** (`volume×close`) |
| A3 | Primary cell strata = top-10 by **membership-days** |
| A4 | Two-sample lift CIs + L-20 emit |
| **A5** | UNF lift CI = `two_sample_block_vs_battery` (bootstrap **both** treatment trades block≥H **and** battery seed means). **`battery_minus_seeds` BANNED** (held treatment mean fixed → omitted treatment SE → inflated UNF CI+). |

**VOID:** any prior analysis citing **~219 CI+** / **~108 UNF CI+** under `battery_minus_seeds`.  
**Authoritative counts (this emission only):** re-derived below from `cells.parquet`.

**Effective catalog start (disclosure):** membership rebalances begin **2022-07-15** (522 days through train_end); fence still full TRAIN `[2021-06-29, 2023-12-18)`.

---

## 1. Integrity gate (SPDR adaptation — Phase 0)

SPDR carve-out: **no** `estimand_validation.json` (by design — spdr-lane / design §4: no P&L verdict). Integrity substitute = code-asserted fence + causal lag + `integrity.json` **PASS 11/11**. Metrics = availability/lift in bps, not booked P&L.

| Check | Result | Evidence |
|---|---|---|
| Estimand validation artifact | **N/A (SPDR)** | design §4 / spdr-lane |
| `integrity.json` 11/11 | **PASS** | `all_pass: true`, `pass_count: 11` |
| TRAIN fence | **PASS** | max_exit_ns < train_end_ns; holdout_start 2025-01-08 sealed |
| Causal t−1 / HTF CloseTime < Open(t) | **PASS** | item 3; G1 `forming_bar_not_used: true` |
| Online membership causality | **PASS** | item 4; G3 |
| Matched control + seed battery | **PASS** | item 5; seeds 1000–1024; A1 UNF baseline |
| Per-stratum emission | **PASS** | 960 rows (720 treat + 240 baseline) |
| L-28 derangement (Control C) | **PASS** | item 7: 0 fixed points |
| L-21 unit_pin.json | **PASS** | measured TRAIN ATR bps + money floor examples |
| L-20 emit + block rule | **PASS** | item 9; all L-20 fields finite on 720 treatment |
| **lift_ci_method (A4/A5)** | **PASS** | only allowed trio; **zero** `battery_minus_seeds` |
| Golden G1–G3 | **PASS** | all `ok: true` |
| No local adjudication P&L | **PASS** | screen metrics = xen.evaluation only |
| Holdout / TEST untouched | **PASS** | band TRAIN only |
| Price-primary Nautilus | **N/A (SPDR)** | vectorised Python by design |
| Leak tripwire (Control C) | **MAGNITUDES §3.7** | collapse fractions on promote-facing cells |

### lift_ci_method audit (A5 binding)

| Method | n treatment | Role |
|---|---:|---|
| `two_sample_block_vs_battery` | 240 | **UNF** vs RAND-battery (A5) |
| `two_sample_block` | 240 | **MOM** vs NONE twin |
| `two_sample_seed_means` | 240 | **RAND** seed-mean two-sample |
| `battery_minus_seeds` | **0** | **BANNED** |

L-20 finite on all 720 treatment: `block_h_ci_*`, seed ranges, `block_sens_*`, `lift_ci_*`, `lift_ci_low_seed_range_*`.

### Provenance (verdict-bearing columns)

| Column / object | Inputs & timestamps | ≤ t−1 / causal? | Location |
|---|---|---|---|
| HTF ±DI / ADX | last HTF bar with CloseTime < Open(t) | yes (asserted + G1) | `screen_code/spdr004_screen.py` |
| MOM sign | Close[t−1] − Close[t−1−N] | yes | same |
| RAND sign | seed + bar calendar | yes (L-19) | seeds 1000–1024 |
| Membership | trailing 24h **notional** ending < rebalance | yes | integrity G3 |
| `r_bps` | s·(Open[t+H]−Open[t])/Open[t]·1e4 non-overlap | open-to-open | design §4 |
| Lift | treatment mean − matched baseline | Control A / A1 | cells |
| Lift CI (A5) | UNF: block≥H on trades **+** block=1 on seed means; MOM: two_sample_block; RAND: two_sample_seed_means | dependence-honest | `lift_ci_method` |
| Control C | HTF features phase-shifted K=50 HTF bars (derangement) | destroy form asserted | PHASE_SHIFT_K=50 |

---

## 2. Question list

| # | Question | Status |
|---|---|---|
| Q1 | Object identity vs design estimand? | **ANSWERED** §3.1 |
| Q2 | Mean / lift / CI / n / powered per strata? | **ANSWERED** §3.2–3.6 + `analyst_*` |
| Q3 | Hold ladder in bps (0.5→4×)? | **ANSWERED** §3.3 |
| Q4 | Domain ladder (1h/5m → 4h/15m → 1d/1h)? | **ANSWERED** §3.2 |
| Q5 | DI vs DI_ADX magnitudes? | **ANSWERED** §3.4 |
| Q6 | Base-conditional HTF effect (UNF / MOM / RAND)? | **ANSWERED** §3.5 |
| Q7 | **Honest CI+ by base after A5 (esp. UNF)?** | **ANSWERED** §3.5 — **13 UNF / 9 MOM / 102 RAND** |
| Q8 | Control C collapse on CI+ / cluster cells? | **ANSWERED** §3.7 |
| Q9 | K=3 cluster factual read (domain×modality, per base)? | **ANSWERED** §3.8 |
| Q10 | Money-unit floor vs cluster medians? | **ANSWERED** §3.9 |
| Q11 | Multiplicity / chance-rate context for CI+? | **ANSWERED** §3.10 |
| Q12 | Seed-band / block fragility on verdict cells? | **ANSWERED** §3.11 |
| Q13 | What would make the headline numbers wrong? | **ANSWERED** §5 |
| Q14 | Per-year / regime stability? | **UNANSWERED** — screen emits cell aggregates only; needs bar-level re-emit |

---

## 3. Quantified facets (magnitudes — not verdicts)

### 3.1 Object identity

- Measurement object = trading object = **single-leg open-to-open gross bps over hold H** (non-overlapping active-hold).  
- No multi-leg episode (L-16 N/A).  
- Lift = treatment − matched baseline (UNF: RAND battery @ UNF cadence per A1).  
- Bases are **rulers**, not strategies to rescue (spdr-lane base-conditional interpretation).

### 3.2 Grid inventory + domain ladder

| Item | Value |
|---|---:|
| Treatment cells (primary) | 720 |
| Unpowered | 96 (all residual on **1d/1h** 92 + thin 4h 4) |
| Powered | 624 |
| Med mean bps (all treat) | **+0.20** |
| Med lift bps (all treat) | **+0.79** |
| Lift CI+ (ci_low > 0) | **124** |
| Lift CI+ powered | **111** |
| Lift CI− (ci_high < 0) | **80** |

**Domain medians (disclosure; not pooled verdict):**

| Domain | med mean bps | med lift bps | CI+ | unpowered |
|---|---:|---:|---:|---:|
| 1h/5m | −0.09 | **+0.19** | 39 | 0 |
| 4h/15m | **+3.82** | **+5.11** | 60 | 4 |
| 1d/1h | **−8.31** | **−8.31** | 25 | 92 |

**Read:** longer-grain **4h/15m** carries the positive location shift; **1d/1h** is sparse/noisy (high unpowered, negative medians); **1h/5m** medians near zero.

### 3.3 Hold ladder (all bases pooled — disclosure)

| Hold mult | med mean bps | med lift bps | CI+ / 180 |
|---:|---:|---:|---:|
| 0.5× | +0.06 | +0.11 | 24 |
| 1× | +0.03 | +0.57 | 27 |
| 2× | +0.12 | +1.63 | 36 |
| 4× | **+2.51** | **+3.63** | 37 |

**UNF × 4h/15m only (hold ladder of medians across 10 symbols):**

| Hold | med mean | med lift | CI+ / 20 |
|---:|---:|---:|---:|
| 0.5× | 2.25 | 1.85 | 2 |
| 1× | 5.05 | 5.03 | 2 |
| 2× | 9.13 | 10.36 | 2 |
| 4× | **20.78** | **22.90** | 1 |

Monotone **dose-response in point estimates** with capture scale (mechanism-aligned with P-14 re-open clause). CI+ remains sparse after A5.

### 3.4 HTF filter

| Filter | med lift bps | CI+ / 360 |
|---|---:|---:|
| DI | +0.98 | 51 |
| DI_ADX | +0.45 | 73 |

DI_ADX has more CI+ cells; DI has slightly higher median lift. Not a strong filter preference in pooled location — strata matter more.

### 3.5 Base-conditional (BINDING after A5)

#### CI+ counts by base (honest)

| Base | n | powered | **CI+** | **powered CI+** | CI− | med mean | med lift | method |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **UNF** | 240 | 210 | **13** | **11** | 7 | +0.80 | +0.74 | `two_sample_block_vs_battery` |
| **MOM** | 240 | 206 | **9** | **5** | 10 | −0.69 | +1.06 | `two_sample_block` |
| **RAND** | 240 | 208 | **102** | **95** | 63 | +0.51 | +0.52 | `two_sample_seed_means` |
| **Total** | 720 | 624 | **124** | **111** | 80 | +0.20 | +0.79 | — |

**Pre-A5 VOID reference:** UNF CI+ was ~108 under fixed-treatment `battery_minus_seeds`; pooled ~219. **A5 reduces UNF CI+ by ~8×.**

**Chance-rate context (disclosure, not a test):**  
UNF+MOM CI+ = **22 / 480** ≈ 4.6% of cells — near a naive 5% two-sided false-positive mass if independent (not independent; block CIs). RAND CI+ mass is a **different estimand** (HTF polarity vs random-sign seed means at same cadence) and dominates the pooled 124.

#### Domain × base medians

| Domain × base | med treat mean | med baseline | med lift | CI+ / 80 |
|---|---:|---:|---:|---:|
| 1h/5m UNF | +0.15 | −0.09 | +0.22 | 3 |
| 1h/5m MOM | −0.69 | −0.77 | +0.14 | 3 |
| 1h/5m RAND | +0.17 | −0.09 | +0.18 | 33 |
| **4h/15m UNF** | **+4.96** | −0.19 | **+5.03** | **7** |
| 4h/15m MOM | +0.44 | −4.98 | +5.12 | 3 |
| 4h/15m RAND | +4.96 | −0.19 | +4.69 | 50 |
| 1d/1h UNF | −7.57 | +1.36 | −5.25 | 3 |
| 1d/1h MOM | −11.84 | +6.85 | −13.06 | 3 |
| 1d/1h RAND | −7.98 | +1.36 | −5.89 | 19 |

#### All 13 UNF CI+ cells (complete table)

| Symbol | Domain | Hold | Filter | mean | lift | CI low | CI high | n | powered | collapse | seed_lo | seed_hi |
|---|---|---:|---|---:|---:|---:|---:|---:|---|---:|---:|---:|
| SOL | 4h/15m | 0.5 | DI | 4.09 | 4.80 | 0.38 | 9.35 | 6187 | Y | 0.96 | 0.32 | 0.44 |
| SOL | 4h/15m | 1.0 | DI | 8.35 | 8.41 | 0.79 | 17.0 | 3094 | Y | 1.02 | 0.37 | 1.06 |
| DOGE | 4h/15m | 2.0 | DI | 20.43 | 20.20 | 1.90 | 41.3 | 638 | Y | 0.65 | 1.25 | 3.11 |
| SOL | 4h/15m | 0.5 | DI_ADX | 5.95 | 6.66 | 0.35 | 13.4 | 3689 | Y | 1.07 | **−0.17** | 0.51 |
| SOL | 4h/15m | 1.0 | DI_ADX | 11.96 | 12.02 | 0.64 | 24.4 | 1845 | Y | 1.08 | 0.24 | 0.87 |
| SOL | 4h/15m | 2.0 | DI_ADX | 24.69 | 22.19 | 0.54 | 46.0 | 938 | Y | 1.03 | 0.06 | 1.08 |
| SOL | 4h/15m | 4.0 | DI_ADX | **50.11** | **49.65** | **8.94** | 95.3 | 484 | Y | 1.03 | 6.47 | 9.88 |
| OP | 1h/5m | 4.0 | DI | 15.55 | 16.67 | 3.40 | 31.9 | 1549 | Y | 2.15 | 2.42 | 3.46 |
| SOL | 1h/5m | 4.0 | DI | 9.45 | 9.60 | 2.30 | 18.0 | 3111 | Y | 0.54 | 2.24 | 2.94 |
| OP | 1h/5m | 2.0 | DI_ADX | 10.16 | 11.14 | 0.01 | 24.5 | 1577 | Y | 2.40 | **−1.03** | 0.27 |
| SOL | 1d/1h | 2.0 | DI_ADX | 141.0 | 146.0 | 21.1 | 255 | 118 | Y | 2.30 | 19.0 | 21.8 |
| APT | 1d/1h | 2.0 | DI_ADX | 347 | 331 | 176 | 491 | 31 | **N** | 1.46 | — | — |
| SOL | 1d/1h | 4.0 | DI_ADX | 240 | 218 | 147 | 290 | 61 | **N** | 2.39 | — | — |

**UNF absolute mean CI+ (ci_low of treatment mean > 0):** only **6/240** (powered 6) — lift often clears zero mainly by beating a near-zero battery baseline, not by large absolute mean alone (except long-hold SOL 4h / 1d tails).

#### MOM powered CI+ (n=5) — sparse lottery cells

OP 1h h2/h4 DI(+ADX); SOL 4h h4 DI_ADX (mean 46.0, lift 59.9); DOGE 4h h2 DI_ADX (mean 8.0, lift 40.3 vs deeply negative MOM baseline −32). Four additional unpowered 1d tails.

#### RAND (L-19 ruler)

- CI+ **102/240**; battery rank ≥0.9: **45**; ≥0.8: **77**; med rank **0.56**.  
- Interpretation: **HTF polarity at random cadence** frequently beats pure random-sign seed means — mechanism evidence that HTF direction is not noise, **not** a deployable base.  
- Largest powered cells: APT/SOL 1d DI_ADX, APT/SOL/PEPE/DOGE 4h long holds (lifts tens–hundreds of bps with seed-mean CIs).

### 3.6 Symbol heterogeneity

| Symbol | CI+ / 72 | med mean | med lift | med collapse |
|---|---:|---:|---:|---:|
| SOLUSDT | **35** | +9.52 | +8.31 | 1.03 |
| OPUSDT | 21 | +5.39 | +4.75 | 1.68 |
| APTUSDT | 16 | +4.00 | +7.17 | 1.18 |
| 1000PEPEUSDT | 15 | +5.57 | +6.56 | 0.66 |
| BTCUSDT | 13 | +1.04 | +0.77 | 1.57 |
| LINKUSDT | 9 | −0.20 | +1.61 | 2.07 |
| DOGEUSDT | 9 | −1.89 | −0.95 | 0.89 |
| LTCUSDT | 4 | −4.35 | −0.77 | 0.90 |
| ETHUSDT | 2 | −0.71 | −0.92 | 0.52 |
| XRPUSDT | **0** | −4.96 | −2.35 | 1.36 |

**SOL dominates** CI+ mass and the only full UNF hold-ladder CI+ cluster. XRP is a hard counter-stratum (0 CI+). ETH near-null.

**UNF × 4h × DI_ADX point lifts by symbol (med over holds; CI+ only SOL):**

| Symbol | med lift | med mean | CI+ / 4 |
|---|---:|---:|---:|
| SOL | **+17.1** | **+18.3** | **4** |
| 1000PEPE | +15.5 | +15.1 | 0 |
| OP | +12.1 | +13.4 | 0 |
| DOGE | +9.5 | +10.0 | 0 |
| LINK | +8.1 | +7.4 | 0 |
| BTC | +7.9 | +7.9 | 0 |
| APT | +4.1 | +1.6 | 0 |
| ETH | −1.1 | −0.8 | 0 |
| LTC | −2.1 | −3.7 | 0 |
| XRP | −0.1 | −1.5 | 0 |

Point estimates often positive on alts; **A5 CIs only clear on SOL** for this cell family.

### 3.7 Control C (HTF phase-shift destroy)

Collapse fraction = 1 − (phaseshift_mean / treatment_mean) shape as emitted (`destroy_collapse_frac`); design expects **≈1** on true causal HTF alignment (edge dies when HTF is shifted).

| Scope | med collapse | collapse ≥0.5 | collapse ≥0.8 | collapse <0.2 |
|---|---:|---:|---:|---:|
| All treatment | 1.15 | — | — | — |
| Powered CI+ (n=111) | **1.03** | **93** | **73** | 14 |
| All UNF CI+ (n=13) | **1.07** | **13/13** | 11/13 | 0 |
| SOL 4h UNF DI_ADX ladder (4 cells) | **1.05** | 4/4 | 4/4 | 0 |

**SOL 4h UNF DI_ADX (promote-facing cluster) — destroy detail:**

| Hold | mean | phaseshift mean | collapse |
|---:|---:|---:|---:|
| 0.5 | 5.95 | **−0.42** | 1.07 |
| 1.0 | 11.95 | **−1.01** | 1.08 |
| 2.0 | 24.69 | **−0.83** | 1.03 |
| 4.0 | 50.11 | **−1.35** | 1.03 |

Phase-shift **sign-flips / zeros** the positive mean → collapse ≈1. Non-vacuous (moves the mean statistic). **Not consistent with pure look-ahead HTF leak** on this cluster.

**Caveats:**  
- 18/111 powered CI+ have collapse <0.5 (mostly RAND short-hold / thin cells) — mixed tripwire outside the SOL 4h core.  
- Collapse >1 when destroy mean goes negative is expected and not “extra edge.”

### 3.8 K=3 cluster scan (design §8 — factual, not disposition)

Membership rule (analyst code): powered ∧ lift>0 ∧ (lift_ci_low>0 ∨ (RAND ∧ battery_rank≥0.9)); region = same domain × HTF modality; scopes = ALL_BASES / UNF / MOM / RAND.

#### Per-base clusters with n_member ≥ 3

| Domain | Filter | Base | n | symbols | holds | med mean | med lift | med coll | n mean>own floor | floor min |
|---|---|---|---:|---|---|---:|---:|---:|---:|---:|
| **4h/15m** | **DI_ADX** | **UNF** | **4** | **SOL only** | **0.5–4×** | **18.3** | **17.1** | **1.05** | **2/4** | 13.25 |
| 4h/15m | DI | UNF | 3 | DOGE, SOL | 0.5,1,2 | 8.35 | 8.41 | 0.96 | 1/3 | 13.25 |
| 4h/15m | DI_ADX | RAND | 26 | 7 syms | all | 11.5 | 11.2 | 1.08 | 10/26 | 13.25 |
| 4h/15m | DI | RAND | 23 | 9 syms | all | 6.42 | 8.09 | 0.87 | 7/23 | 13.25 |
| 1h/5m | DI / DI_ADX | RAND | 14 / 19 | 5–6 | all | ~2.2–2.7 | ~2.4–2.8 | ~0.5–0.6 | 0–2 | 13.06 |
| 1d/1h | DI / DI_ADX | RAND | 4 / 9 | 2–4 | ≤2× | 18–34 | 18–32 | 2.4–4.4 | 2–5 | 14.5 |
| — | — | **MOM** | **0** regions with n≥3 | — | — | — | — | — | — | — |

**ALL_BASES** K≥3 in every domain×filter (driven largely by RAND).

#### Neighbourhood / sole-positive

- **UNF × 4h × DI_ADX:** 4 cells on SOL across holds — **not** a single lottery cell; neighbourhood along hold axis **yes**; neighbourhood across **symbols: no** (only SOL clears CI).  
- **UNF × 4h × DI:** 3 cells, 2 symbols — multi-symbol thin.  
- **MOM:** no K≥3; isolated OP / SOL / DOGE cells.  
- Point-estimate neighbourhood on UNF 4h DI_ADX is broader (PEPE/OP/DOGE med lifts +9…+15) but **CI-honest membership is SOL-only**.

### 3.9 Money-unit floor (L-21)

Cost proxy from `unit_pin.json` money_unit_floor_examples (taker fee 11 bps RT + spread_bps=**2.0 GAP placeholder** + funding by hold). Analyst FLOOR table:

| Domain | 0.5× | 1× | 2× | 4× |
|---|---:|---:|---:|---:|
| 1h/5m | 13.06 | 13.13 | 13.25 | 13.5 |
| 4h/15m | 13.25 | 13.5 | 14.0 | 15.0 |
| 1d/1h | 14.5 | 16.0 | 19.0 | 25.0 |

**Powered CI+ vs floor:** mean > own floor **34/111**; lift > floor **39/111**.

**UNF powered CI+ vs floor (key cells):**

| Cell | mean | floor | mean − floor |
|---|---:|---:|---:|
| SOL 4h h4 DI_ADX | 50.11 | 15.0 | **+35.1** |
| SOL 4h h2 DI_ADX | 24.69 | 14.0 | **+10.7** |
| DOGE 4h h2 DI | 20.43 | 14.0 | **+6.4** |
| OP 1h h4 DI | 15.55 | 13.5 | **+2.0** |
| SOL 1d h2 DI_ADX | 141.0 | 19.0 | **+122** |
| SOL 4h h1 DI_ADX | 11.96 | 13.5 | **−1.5** |
| SOL 4h h0.5 / h1 DI | 4–8 | 13–13.5 | **sub-floor** |
| SOL 1h h4 DI | 9.45 | 13.5 | **−4.1** |

**Cluster money read (UNF 4h DI_ADX SOL):** median mean **18.3** vs floor_min **13.25** → **above min floor** as a cluster median; **only h2 and h4** individually clear their own floors. Short holds are sub-floor characterisation only.

**SPREAD-SCALE-ROUTING (disclosure):** spread_bps=2 is a **GAP placeholder**, not TRAIN T1 pseudo-quote. Any later tradability read must re-measure T1; if |gross| < 3× true RT spread → t1_undecidable.

### 3.10 Multiplicity

- 720 treatment cells; promote rule is **cluster K≥3**, not max cell.  
- Pooled CI+ **124** is disclosure-only (L-03).  
- After A5, **directional bases UNF+MOM** contribute only **22 CI+** — multiplicity-aware reading cannot treat UNF as a broad grid hit rate.

### 3.11 Fragility (L-20)

| Check | Result |
|---|---|
| Seed-band straddle on lift CI+ (all bases) | 0 RAND/MOM; **2/13 UNF** (OP 1h h2 DI_ADX; SOL 4h h0.5 DI_ADX) |
| SOL 4h h1–h4 DI_ADX seed band | **ci_low seed range stays >0** (h2 lo=0.059 thin; h4 lo=6.47 solid) |
| MDE UNF med by domain | 1h: 4.5 bps · 4h: 16.2 · 1d: 92.5 |
| UNF n_trades med | 1h: 3114 · 4h: 779 · 1d: 126 |

SOL 4h h2 DI_ADX: lift CI low +0.54 with seed_lo +0.06 — **clears zero but thin**. h4 is the robust money cell.

---

## 4. Evidence FOR the hypothesis

Hypothesis (design §1): coherent clusters of (HTF state × LTF base × hold × domain) show **signal-conditional lift** over matched baselines in gross open-to-open bps under causal t−1 rules; capture scale is first-class.

1. **A5-honest UNF lift exists on a connected hold region (SOL × 4h/15m × DI_ADX).**  
   Four powered cells, holds 0.5–4×, all lift CI lows >0 under `two_sample_block_vs_battery`. Med lift **+17.1 bps**, med mean **+18.3 bps**. Hold ladder is monotone (mean 6→12→25→50 bps).

2. **Control C collapses that cluster (collapse ≈1.03–1.08; destroy means ≈ −0.4…−1.3 bps).**  
   Edge requires causal HTF alignment — consistent with mechanism, not residual look-ahead of forming HTF bars (integrity G1 already causal).

3. **Capture-scale structure matches the P-14 re-open clause.**  
   Domain med lift 1h +0.19 → 4h **+5.11** → 1d −8.3 (sparse). Within UNF 4h, med lift rises with hold multiple; money floor only cleared at **2×/4×** on SOL DI_ADX.

4. **RAND ruler: HTF polarity beats random-sign seed means at scale (102 CI+, 45 cells rank≥0.9).**  
   Supports “HTF direction is informative,” separate from UNF/MOM deployability.

5. **Matched baselines near zero on UNF 4h (med baseline −0.19)** while treatment med mean +4.96 — location shift is treatment-side, not baseline artifact.

6. **Secondary UNF DI cluster (SOL+DOGE 4h, n=3)** and OP/SOL 1h long-hold CI+ cells add thin multi-domain texture (magnitudes smaller; several sub-floor).

---

## 5. Evidence AGAINST the hypothesis

1. **UNF CI+ mass after A5 is thin: 13/240 (11 powered).**  
   Pre-A5 ~108 was an artifact of omitted treatment SE. Current UNF+MOM CI+ ≈ chance-rate order under naive 5% counting (disclosure, not a formal FDR).

2. **Best UNF K≥3 cluster is single-symbol (SOL).**  
   Peer symbols often show positive **point** lifts on 4h DI_ADX (PEPE/OP/DOGE med +9…+15) but **fail CI+** — neighbourhood fails the multi-symbol stress; risk of SOL-idiosyncratic TRAIN path.

3. **MOM has zero K≥3 regions; only 5 powered CI+.**  
   Naive momentum base does not form a coherent promote cluster under two_sample_block CIs.

4. **1d/1h medians negative; 37.5% unpowered on that domain.**  
   Longer calendar grain does not automatically deliver a powered multi-symbol positive location.

5. **Money floor:** most powered CI+ means sit **below** ~13–15 bps RT proxy; even the SOL DI_ADX cluster is sub-floor at 0.5× and 1×. Spread input is a **2 bps GAP placeholder** — true T1 may raise the floor.

6. **Absolute treatment mean CI+ rare on UNF (6/240).**  
   Many lifts clear zero by beating a ~0 battery, not by large absolute gross means (except long-hold SOL).

7. **Symbol vetoes:** XRP 0 CI+; ETH 2 CI+; LTC thin. Grid is not homogeneous.

8. **Fragility:** OP 1h h2 DI_ADX and SOL 4h h0.5 DI_ADX have seed bands straddling 0; SOL 4h h2 CI low is thin (+0.54 / seed_lo +0.06).

9. **RAND CI+ inflation of pooled 124:** interpreting pooled CI+ as “HTF works broadly” confounds the ruler arm with UNF/MOM. Design promotes clusters — not pooled rate.

10. **Multiplicity:** 720 cells; any single-cell highlight (e.g. APT 1d unpowered 331 bps lift) is lottery under L-03 unless clustered.

---

## 6. Anomalies & open questions

| Item | Note | Suggested probe |
|---|---|---|
| SOL dominance | 35/124 CI+ cells | Re-run membership/leave-one-symbol; bar-level half-sample by year |
| Point+ CI− on PEPE/OP 4h UNF | med lifts high, CI fails A5 | Block-length sensitivity on lift CI; more seeds on battery arm |
| Collapse <0.5 on 18 powered CI+ | mostly non-core | Per-cell destroy anatomy |
| 1d unpowered mass | MDE ~90 bps | Treat 1d as characterisation-only unless n grows |
| Spread GAP=2 | floor may be understated | Join TRAIN T1 pseudo-quote before any tradability language |
| No per-year table | screen cell aggregates only | Analyst bar re-emit if operator wants regime split |
| Catalog start 2022-07-15 | short of full TRAIN fence | Disclose truncated effective N |

**Falsification probes for headlines:**  
- Drop SOL → does any UNF K≥3 remain? (likely no under CI+ membership)  
- Replace A5 with banned method → CI+ mass explodes (already known; do not re-enable)  
- Control C non-derangement would invalidate collapse (asserted 0 fixed points)

---

## 7. Recommended framing for the operator (NOT a disposition stamp)

**Factual pack §6 / design §8 checklist (magnitudes only):**

| Clause | UNF × 4h/15m × DI_ADX (SOL holds) | Notes |
|---|---|---|
| Cluster K≥3 CI-honest lift | **Met (n=4 holds)** | SOL only |
| Neighbourhood (not sole cell) | **Met along hold axis** | **Not met across symbols** under CI+ |
| Money floor disclosure | **Cluster med mean 18.3 > floor_min 13.25**; h2/h4 clear own floors; h0.5/h1 sub-floor | GAP spread=2 |
| Control C on cluster | **collapse ≈1.03–1.08** | Non-vacuous |

**MOM:** no K≥3.  
**RAND:** multiple K≥3 (ruler evidence, not a strategy).  
**UNF × 4h × DI:** K=3 thin (SOL+DOGE), med mean **below** floor.

### Recommended language (operator chooses disposition)

- **Do not stamp** `WORTH_EXPLORING` / `NOT_WORTH` here.  
- **Recommended framing for operator decision:**

  > After A5, broad-grid UNF lift mass is gone. What remains is a **narrow, capture-scale, SOL-centred** coherent region: **4h/15m × DI_ADX × UNF**, hold ladder 0.5–4×, lift CIs excluding zero under two-sample treatment+battery bootstrap, Control C collapse ≈1, with **gross means above the disclosed taker+GAP floor only at 2× and 4× holds** (≈25–50 bps). Peer symbols show positive point lifts on the same facet without clearing A5 CIs. MOM does not cluster. RAND confirms HTF polarity beats random signs but is a ruler.

  **If the operator wants a routing signal toward XENA characterisation / apparatus** (not tradability): the SOL 4h DI_ADX long-hold thread is the only UNF region that jointly satisfies K≥3 + collapse + partial money clearance — graduate only with **explicit single-name / long-hold scope**, L-21 re-pin with real T1 spread, and no claim of multi-symbol UNF CI coverage.

  **If the operator requires multi-symbol CI-honest UNF clusters or broad base support:** the A5 grid does **not** supply that; framing leans **not worth a full multi-symbol tradability XENA**, or **inconclusive outside SOL 4h**, without folding unpowered 1d tails into a negative.

- **Would change if:** multi-symbol UNF 4h DI_ADX cells clear A5 CIs; or SOL cluster fails half-sample / leave-one-year; or T1 floor rises above cluster med means.

**Final verdict is the operator's.** Suggested probes if pushing: (1) SOL leave-one-year bar re-emit; (2) T1 spread remeasure; (3) peer-alt CI with longer battery / more trades; (4) XENA only if characterisation scope accepted.

---

## 8. Artifact index

| Path | Content |
|---|---|
| `results/cells.parquet` | Source screen emission (A1–A5) |
| `results/analyst_headline.json` | Headline counts + clusters (A5) |
| `results/analyst_facets.csv` | Per-facet CI+/medians |
| `results/analyst_lift_ci_pos.*` | All CI+ cells |
| `results/analyst_clusters_k3.*` | K=3 scan |
| `results/analyst_control_c.*` | Collapse table |
| `results/analyst_money_floor.*` | Floor comparison |
| `results/analyst_base_conditional.*` | domain×base×filter×hold |
| `results/analyst_top_lift_ci_pos.*` | Top powered CI+ |
| `results/analyst_rand_ranks.*` | RAND battery ranks |
| `analysis_code/spdr004_analysis.py` | Re-derive (no screen_code import) |

**Integrity:** PASS 11/11 · **Methods:** A5-compliant · **Prior 219 CI+:** VOID.

---

## 9. OPERATOR DISPOSITION (2026-07-17, operator-signed)

**WORTH_EXPLORING** — frozen promote rule (design §8, pack §6, K=3) formally met on ONE
cluster: **SOLUSDT × 4h/15m × UNF × DI_ADX across all 4 holds** (mean bps/trade 5.9 → 12.0 →
24.7 → 50.1 for 0.5×→4× HTF span; two-sample lift ci_low > 0 at every rung; battery rank
1.00; Control C collapse ≈ 1.03–1.08 leak-clean; h2/h4 clear own money floors, cluster
median 18.3 vs floor 13.25). Monotone hold ladder in money units = the capture-scale
signature the family was registered to find (P-14 escape axis).

**Binding caveats carried into any XENA-HTFCAP-001 design:**
1. Single-symbol cluster — cross-symbol neighbourhood FAILS under CI+ membership; SOL is
   35/124 of all CI+ cells. Generalisation is exactly what XENA portfolio adjudication must test.
2. All mass outside the cluster is P-14-shaped (sub-floor 0.5–4 bps lifts) — no broad-based
   conditioning claim.
3. Money floors used GAP spread=2 (overstates majors ~10×; measured spreads land floors at
   ≈11.1–12.6 bps — direction unchanged, cluster clears more comfortably). Corrected
   per-symbol spreads pinned from SPDR-006 onward.
4. 1d/1h domain UNPOWERED (MDE ~90 bps) — characterisation-only.
5. No tradability claim — availability justification only; XENA gate remains blocked on the
   INFR-014 registry pin. Vol-regime facet screened separately as SPDR-006 (own grid/K).

QA: run 1 REVISE → run 2 REVISE → fixes AMENDMENT-2..5 → fix-confirmation pass clean
(orchestrator-verified two-sample UNF CIs, L-20 emissions, ledger 0L/2T/3N→+A5).
