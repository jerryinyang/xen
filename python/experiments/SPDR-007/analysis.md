# Data Analysis: SPDR-007

**Item:** SPDR-007 · CF-SIGAUC-001 statistical spine (S1+S2) · SPDR TRAIN-only  
**Analyst:** fresh-context stage-5 (`analysis_code/analyze_spine.py`)  
**Emissions:** `results/spine_events_{DESIGN,CONFIRM}.parquet`, `spine_control_DESIGN.parquet`, `protection_freeze.json`, `tripwire.json`, `floor_table.json`, `layers.json`  
**Recompute artifact:** `results/analysis_recompute.json`  
**QA run 3:** APPROVE (integrity already clean; re-checked independently below)  
**Hypothesis (experiment only):** DESIGN-estimated Protection reproduces on CONFIRM **and** acceptance conditioning beats matched unconditional same-phase/side entry (R5 binding). Money floor first. Framework falsifier #1 in scope.  
**Null that kills the spine story:** reproduction holds on the control arm identically (P-01: “price has quantiles”).  
**Inherited:** frozen anchor INFR-018 unresolved (E=+0.10, CI contains 0, below MDE) — no established anchor effect assumed.

---

## 1. Integrity gate (SPDR-adapted)

| Check | Result | Evidence |
|---|---|---|
| Estimand validation / Nautilus price-primary | **N/A** | SPDR lane — no `estimand_validation.json`, no booked P&L |
| Freeze-before-CONFIRM + pin | **PASS** | `protection_freeze.json` `band=DESIGN`, `n_events=7070`; internal `pin_sha256=a45eac44…` matches `_hash_obj` (payload excl. pin); layers `protection_freeze_pin` identical; DESIGN recomputed q̂_p70=1.79604779… matches freeze bit-for-bit |
| Causal ≤ t−1 (entry) | **PASS** | `(entry_ts == qualify_end).all()` on DESIGN + CONFIRM; entry = open of first bar after qualify window |
| Band fence TRAIN-only | **PASS** | DESIGN `entry_ts` max 2023-02-27 < 2023-03-01; CONFIRM ∈ [2023-03-01, 2023-12-16] < TEST 2023-12-18; layers `test_touched=false`, `holdout_touched=false` |
| Holdout unreachable | **PASS** | max entry ≪ 2025-01-08; no holdout query path in emissions |
| Future-destroy tripwire | **PASS (D-2 uninformative)** | status `NO_MATERIAL_EDGE_TRIPWIRE_UNINFORMATIVE`; `any_material_edge=false`; `survives=false`; not a HARD fail under AMENDMENT-11 |
| Tripwire bite (non-vacuous) | **PASS** | `corr(swapped price MFE, donor MFE)=0.771` n=3561 (>0.5 required) |
| Horizon-matched control (D-1) | **PASS** | remaining_horizon median signal/control **1391 / 1391** min; n_control/n_signal ≈ 28.1 (≈30 draws) |
| `check_no_local_accounting` | **PASS** | screen_code + analysis_code + `xen/sigbar`: `ok=true`, banned_defs=[] (re-invoked) |
| No local accounting for verdict numbers | **PASS** | all magnitudes below recomputed from parquets + `xen.evaluation.block_bootstrap_ci` |
| Population object | **PASS** | diagnostics: pokes 13,802 / accepts 7,148 / missing entry 78 → evaluable 7,070 = emission height |

### Provenance (verdict-bearing columns)

| Column | Inputs & timestamps | ≤ t−1? | Evidence |
|---|---|---|---|
| `side` / A6 accept | poke + 30m qualify closes; entry at `qualify_end` open | YES | entry_ts == qualify_end |
| `ib_width` divisor | IB [anchor, anchor+15) | YES | pre-entry by construction |
| `ib_width_pctl` | trailing ≤60 prior sessions | YES (causal form); acausal probe separate | 27.3% NaN (warmup <30 priors) counted |
| `coh` | mean `delta_ratio_resid` on qualify window × side | YES | window ends at entry |
| `mfe_norm` / race | path after entry bar open | YES | post-entry only |
| Protection q̂ | DESIGN mfe_norm only | YES | freeze before CONFIRM; CONFIRM never enters freeze |

### Tripwire collapse fractions (disclosure; no material raw edge)

| Read | raw contrast | raw CI excludes 0? | collapse_fraction |
|---|---|---|---|
| R5 asym | +0.090 | NO [−0.231, +0.320] | −4.60 (noise/noise) |
| R2 w | −0.040 (day median) | NO [−0.062, 0.0] | 1.61 |
| R3 ρ contrast | +0.130 (screen) / −0.040 (finite-only) | no day-CI | 0.62 |
| R4 mfe | +0.077 | no day-CI | ~0 |
| R4 w | +0.012 | no day-CI | 3.12 |

**Integrity conclusion:** emission valid to analyse. Tripwire correctly uninformative under D-2 because no adjudicated contrast is a material edge.

---

## 2. Question list

| # | Question | Status |
|---|---|---|
| Q1 | Integrity: freeze-before-CONFIRM, tripwire bite+status, holdout, accounting | **ANSWERED** §1 |
| Q2 | R1: pooled calib_err + CI; per-major; SOL; DESIGN self-hit vs CONFIRM | **ANSWERED** §3/§4 R1 |
| Q3 | R2: w_signal vs w_control vs p0=1/3 vs p0ᶜ; MDE in w units | **ANSWERED** §3/§4 R2 |
| Q4 | R5: paired day asym contrast; CI; MDE; collapse | **ANSWERED** §3/§4 R5 |
| Q5 | R3: contrast ρ only; raw-MFE disclosure; normaliser guard | **ANSWERED** §3/§4 R3 |
| Q6 | R4: mfe + w tercile contrasts | **ANSWERED** §3/§4 R4 |
| Q7 | Time stability thirds signs | **ANSWERED** §4 time |
| Q8 | Horizon match (D-1) | **ANSWERED** §1 |
| Q9 | Side-derangement power | **ANSWERED** §4 side |
| Q10 | Money floor: TP1_bps vs cost for majors | **ANSWERED** §3 R0 |
| Q11 | Spread-scale routing (2 undecidable) | **ANSWERED** §4 spread |
| Q12 | Falsification: control also “reproduces” a quantile? Session-phase only? | **ANSWERED** §4 P-01 |
| Q13 | Per-symbol R1 label census (pooled mask) | **ANSWERED** §3 R1 |
| Q14 | Does w clear cost-adjusted breakeven on majors? | **ANSWERED** §4 R2 |
| Q15 | Framework falsifier #1 triggered? | **ANSWERED** §6 |

---

## 3. Evidence FOR the hypothesis

*Equal diligence — supporting observations only. Magnitudes first.*

### R0 — money floor cleared (necessary, not sufficient)

**Divisor object (L-21):** this session’s IB high−low in price units, A-USOPEN L=15m; DESIGN-session median `ib_width_bps` (not accept-event median).

| Symbol | cost floor bps | median IB bps | TP1_bps (pooled p70 × IB) | margin vs floor | band |
|---|---|---|---|---|---|
| BTCUSDT | 14.24 | 48.75 | **87.5** | +73.3 | ABOVE_FLOOR |
| ETHUSDT | 14.31 | 69.96 | **125.6** | +111.3 | ABOVE_FLOOR |
| SOLUSDT | 14.73 | 96.22 | **172.8** | +158.1 | ABOVE_FLOOR |
| DOGEUSDT | 15.48 | 86.97 | **156.2** | +140.7 | ABOVE_FLOOR |
| XRPUSDT | 15.97 | 60.75 | **109.1** | +93.2 | ABOVE_FLOOR |

Pooled p70 Protection = **1.796 IB widths** ≫ majors’ “TP1 must exceed” thresholds (0.15–0.29 IBW). Floor is **not** the binding constraint on target *size*.

### R1 — pooled Protection hit rate near nominal on CONFIRM

| p | q̂ (DESIGN, IBW) | CONFIRM hit | calib_err | day-clust. calib_err CI (291 days) | DESIGN self-hit |
|---|---|---|---|---|---|
| 0.65 | 2.175 | 0.680 | **+0.030** | [−0.009, +0.049] | 0.650 |
| 0.70 | 1.796 | 0.728 | **+0.028** | [−0.007, +0.048] | 0.700 |

- Pooled |calib_err| ≤ 0.05 → design-label **REPRODUCES** (TRAIN-INTERNAL CONFIRM, n=11,375).
- Day-clustered CI for calib_err **contains 0** and stays inside ±0.05 — consistent with stable calibration, not a sharp miss.
- DESIGN self-hit at frozen q is exact for p70 (order-statistic identity).

**Per-major p70 (per-symbol freeze q̂):**

| Symbol | n_CONF | hit | calib_err | label |
|---|---|---|---|---|
| BTCUSDT | 138 | 0.732 | +0.032 | REPRODUCES |
| ETHUSDT | 143 | 0.734 | +0.034 | REPRODUCES |
| XRPUSDT | 125 | 0.704 | +0.004 | REPRODUCES |
| DOGEUSDT | 142 | 0.655 | −0.045 | REPRODUCES |
| SOLUSDT | 149 | 0.805 | **+0.105** | **BROKEN** |

Label census on 97 DESIGN-covered CONFIRM symbols (p70): REPRODUCES 51 / DRIFTED 25 / BROKEN 21.

### R5 / R2 levels are not catastrophically one-sided

- Signal race w_p70 = **0.333** (n_resolved 6,967) sits on gross breakeven 1/3.
- Day-median asym contrast point estimate **+0.090** (directionally positive, though unpowered — see AGAINST).

### Integrity machinery works

- Bite corr 0.77 proves path-swap installs donor outcomes.
- Freeze pin + band fences hold; no TEST/holdout contact.

---

## 4. Evidence AGAINST the hypothesis

*Equal diligence — contrary observations. Magnitudes first.*

### A1 — P-01: control arm also “has Protection quantiles” (binding null)

| Arm | own q̂_p70 (IBW) | self-hit at own q̂ | hit at **signal** q̂_p70 |
|---|---|---|---|
| Signal DESIGN | 1.796 | 0.700 | 0.700 |
| Control DESIGN | **1.621** | **0.700** | 0.675 |
| Signal CONFIRM | (frozen 1.796) | — | **0.728** |

- Control self-hit at its own (1−p) quantile is **exactly ~p** — pure order-statistic identity, not acceptance skill.
- Control q̂ is only **~10% smaller** than signal (1.62 vs 1.80 IBW); not a large level separation.
- Control paths hit the *signal* Protection level 67.5% of the time (near p=0.70).
- **Therefore quantile reproduction on CONFIRM does not establish acceptance-conditional edge.** It shows MFE distributions are stable enough to have quantiles across TRAIN-internal bands.

### A2 — R5 excursion contrast: wash under MDE (binding contrast)

| Statistic | Value |
|---|---|
| Day-median asym contrast (signal − control) | **+0.090** |
| Day-clustered 95% CI (n=531 days, block=5) | **[−0.231, +0.320]** — **includes 0** |
| Screen MDE (plant curve) | **0.50** IBW units |
| \|effect\| vs MDE | 0.090 ≪ 0.50 → design-label **WASH / unmeasurable as support** |
| Signal day-mean asym | −0.012 |
| Control day-mean asym | +0.363 |
| Block sensitivity ½×/1×/2× | all CIs still straddle 0; not block-fragile on sign |
| Trimmed-mean CI | [−0.426, +0.505] — also includes 0 |

**Collapse fraction on levels** is meaningless here (signal level ≈ 0 → ratio explodes). Prefer contrast CI.

**Per-major event-level median asym (disclosure; day-join empty per symbol because control `day` = donor entry day, disjoint from signal event days):**

| Symbol | med asym signal | med asym control | Δ |
|---|---|---|---|
| BTCUSDT | −0.240 | −0.040 | **−0.200** |
| ETHUSDT | −0.048 | −0.102 | +0.053 |
| SOLUSDT | −0.074 | ~0 | −0.074 |
| DOGEUSDT | (from layers spread-scale mfe contrast sign mixed) | | |
| XRPUSDT | — | — | +0.43 mfe_norm med contrast in routing table |

Majors do **not** show a homogeneous positive excursion edge.

### A3 — R2 race: no lift over control; below cost breakeven

**Pooled (DESIGN):**

| | p65 | p70 |
|---|---|---|
| w_signal | 0.342 | **0.333** |
| w_control | 0.340 | **0.343** |
| w_contrast | +0.002 | **−0.010** |
| n_resolved signal | 6,880 | 6,967 |

**Day-clustered w contrast p70:** median −0.040; CI **[−0.062, 0.0]** (seed battery high-bound range [−0.0018, 0.0] — MC-fragile at zero; `ci_excludes_zero=false` by screen rule). Screen MDE in w units = **0.03**. Observed pooled contrast −0.010 is **inside** MDE; day-median contrast −0.040 sits at ~MDE with upper CI at 0.

**Majors p70 vs cost-adjusted breakeven p0ᶜ = (STOP+cost)/(TP1+STOP):**

| Symbol | w_signal | w_control | Δw | p0ᶜ | w − p0ᶜ |
|---|---|---|---|---|---|
| BTCUSDT | 0.336 | 0.319 | +0.017 | **0.442** | **−0.106** |
| ETHUSDT | 0.294 | 0.346 | −0.052 | 0.409 | −0.116 |
| SOLUSDT | 0.274 | 0.358 | **−0.084** | 0.390 | −0.116 |
| DOGEUSDT | 0.349 | 0.329 | +0.021 | 0.399 | −0.050 |
| XRPUSDT | 0.288 | 0.347 | −0.059 | 0.431 | −0.143 |

- **Every major** has w_signal **below** p0ᶜ by 5–14 pp.
- Gross p0=1/3 is not the relevant bar once taker+spread+funding enter; cost-adjusted bar is ~0.38–0.44.
- Three of five majors have **negative** w_contrast (control races better).

### A4 — R3 regime: normaliser mechanic; contrast small / wrong sign when computed cleanly

| Method | ρ_signal | ρ_control | ρ_contrast |
|---|---|---|---|
| Finite-only Spearman (preferred; NaN dropped) | **−0.390** n=5,140 | −0.350 n=154,927 | **−0.040** |
| Screen layers (polars.corr; ranks float NaN) | −0.220 | −0.350 | +0.130 |
| Raw MFE_bps vs ib_width_pctl (finite) | — | — | ρ = **+0.090** (weak +; not contraction→expansion in the claimed direction on normalised form) |

- Warmup NaN fraction signal **27.3%**. Polars inclusion of NaN **attenuates** |ρ_signal| and manufactures a positive contrast in layers.json.
- Preferred finite-only contrast **≈ 0** (slightly negative): signal is *more* negatively correlated with width percentile than control — opposite of “conditioning improves relative excursion after canceling the divisor.”
- Majors finite-only contrasts: BTC −0.12, ETH −0.10, SOL −0.15, DOGE −0.07, XRP +0.01 — no supported positive regime story.

### A5 — R4 Δ-coherence: tiny stratification

| | Value |
|---|---|
| n with finite coh | 6,961 |
| mfe_norm top−bottom median | **+0.077 IBW** |
| w top−bottom | **+0.012** |
| vs R5 MDE scale | 0.077 ≪ 0.5 |

Coherence terciles barely move MFE or race rate. Not a usable stratifier at this n/effect.

### A6 — Time thirds: sign inconsistency (L-24 F02)

| Third | n | R2 Δw | R5 asym contrast | R1 self-err p70 |
|---|---|---|---|---|
| 1 (→2022-06) | 2356 | **+0.013** | **−0.212** | +0.020 |
| 2 (→2022-11) | 2357 | **−0.032** | **+0.714** | −0.019 |
| 3 (→2023-02) | 2357 | **−0.011** | **+0.090** | −0.001 |

- R5 signs: − / + / + → **not consistent**.
- R2 signs: + / − / − → **not consistent**.
- R1 self-calibration stays near 0 every third (quantiles exist in every sub-period).

### A7 — Side-derangement UNPOWERED (not evidence against; power statement B-5)

| | |
|---|---|
| n_input | 7,070 |
| n_deranged | **60** (0.85%) |
| dropped singleton / infeasible | 2,694 / 4,316 |
| fixed_point_rate | 0.0 (L-28 clean) |
| Status | **UNPOWERED** — cannot test whether side carries direction |

### A8 — SOL BROKEN calibration (pooled mask L-03)

SOL p70 calib_err **+0.105** (hit 0.805 vs nominal 0.70) with n=149 CONFIRM — design-label **BROKEN**. Pooled +0.028 **hides** this major. Direction is *higher* hit rate (Protection too tight on SOL DESIGN), not a failure to reach targets — still heterogeneity that forbids pooled-as-verdict.

### A9 — Anchor prior unresolved

INFR-018 A-USOPEN×15 selection contrast E=+0.10, CI contains 0, below MDE 0.50. SPDR-007 does not inherit a validated anchor effect; any spine read sits on an unresolved Stage-I pin.

### A10 — Spread-scale routing

- 2 / ~140 symbols `t1_undecidable` (APTUSDT, SANDUSDT) — not the story.
- Majors T1-decidable on **gross mfe_norm median contrast × IB bps**, but those gross contrasts are **not** the binding R5 day-clustered CI-clearing edges (R5 CI includes 0). Routing table must not be read as “edge exists.”

---

## 5. Anomalies / open questions / suggested probes

1. **Control `day` vs signal `day` per symbol are disjoint** for majors (control day = donor entry calendar day). Pooled day-clustering still works cross-sectionally; per-symbol day-paired R5 is empty. Probe: emit `_event_id` / signal-day on each control row for per-symbol paired contrasts.
2. **Polars Spearman + float NaN** in screen R3 attenuates ρ_signal (−0.22 vs finite −0.39) and flips contrast sign vs finite-only. Prefer finite-only in any graduation design; treat layers R3 +0.130 as artifact-prone.
3. **R2 trimmed_mean_ci** in layers is [−0.059, −0.003] (excludes 0, negative) while median CI kisses 0 from below — weak signal that acceptance may *hurt* race rate slightly; not strong enough alone, worth noting.
4. **Side-derangement coverage** almost zero under calendar-day blocks (sparse multi-event same-day). Probe: derange within symbol×week or symbol×month blocks if a future item needs that control.
5. **CONFIRM control arm not emitted** — P-01 control quantile check is DESIGN-only. Probe: optional CONFIRM control emission if operator wants OOS control hit rates (still TRAIN-internal CONFIRM).
6. **21/97 symbols BROKEN on R1 p70** — heterogeneity table exists in layers; no family action here; if anything graduates, start from majors with REPRODUCES labels only.
7. **INFR-018 anchor still unresolved** — any follow-up that treats A-USOPEN as established is out of order.

---

## 6. Recommended SPDR disposition

### Recommendation: **`NOT_WORTH`**

*(Operator final. Not a family status change. Not a tradability claim.)*

### Decisive magnitudes (2–3)

1. **R5 day-median asym contrast +0.090, 95% CI [−0.231, +0.320], MDE 0.50** — acceptance does not beat same-phase/side unconditional entry on the binding excursion contrast; effect is far below detectable size at n=531 days.
2. **R2 w_signal p70 = 0.333 vs w_control 0.343 (Δ −0.010); majors w − p0ᶜ ≈ −0.05 to −0.14** — race rate sits at gross breakeven and **materially below** cost-adjusted breakeven; no lift over control.
3. **P-01: control self-hit at own q̂_p70 = 0.700; signal CONFIRM hit = 0.728 at q̂=1.80 IBW** — quantile reproduction is what price paths do; it is not acceptance-conditional edge. Control q̂ (1.62) is within ~10% of signal.

### Money-floor framing (L-21 / spdr-lane)

TP1 size is **ABOVE_FLOOR** for all majors (TP1_bps ≫ 14–16 bps cost). That only means the *target level is large enough in money units* if hit rates were edge-bearing. They are not: w fails p0ᶜ and R5 contrast is a wash. Disposition is **not** “science because floor failed”; floor passed and the **conditional edge still failed**. Framing: characterisation complete — no signal-conditional lift to graduate as strategy candidate.

### Framework falsifier #1

Source falsifier: “no anchor reproduces ~65–70% Protection.”  
**Strict reading:** falsifier **not triggered** — pooled Protection **does** hit ~68–73% on CONFIRM.  
**Binding programme reading (P-01 + R5):** reproduction without control separation is **not** a go for the spine. The master go/no-go fails on the **matched-unconditional contrast**, not on the existence of quantiles.

### What would flip to WORTH_EXPLORING

- R5 day-clustered CI excludes 0 with contrast magnitude **≥ MDE (~0.5 IBW asym units)** on DESIGN, stable sign across chronological thirds; **and**
- R2 w_contrast ≥ MDE 0.03 with w_signal **above** per-symbol p0ᶜ on majors; **and**
- Separation not explained by horizon mismatch (already matched) or normaliser artifact.

### What would flip to INCONCLUSIVE (instead of NOT_WORTH)

- If operator judges panel underpowered for the *plausible* effect size they care about **smaller than** published MDE **and** refuses wash-as-negative — but published MDE was co-designed and R2/R5 are powered for effects the design cared about. Analyst recommendation stays **NOT_WORTH**, not INCONCLUSIVE: the measurement is informative (contrast ≈ 0), not missing.

### Hand-off

**Final disposition is the operator’s.**  
Suggested probes if pushing further: (i) fix control row to carry signal calendar day for per-symbol paired R5; (ii) finite-only R3 in any rewrite; (iii) do **not** spend a counted TEST read on this spine without a new mechanism that produces R5 separation; (iv) keep INFR-018 anchor unresolved in the headline of any sequel.

---

### Script map

| Script | Role |
|---|---|
| `analysis_code/analyze_spine.py` | Integrity, R0–R5 recompute, P-01, thirds, spread-scale |
| `results/analysis_recompute.json` | Machine-readable tables behind this note |
| `results/*.parquet` / `protection_freeze.json` / `tripwire.json` | Raw emissions (source of truth) |

*screen.md remains subordinate quantification; this file is the binding stage-5 read.*
