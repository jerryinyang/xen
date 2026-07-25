# Data Analysis: SPDR-015 (refreshed on re-run results, 2026-07-24 06:24)

**Family:** `CF-VOLDIR-001` / **HYP-D2** · **Checkpoint:** 017 · **Lane:** SPDR TRAIN-only
**Role:** conditioner science (gates/labels for later 014 amend / 016 features) — **not** a standalone trade
**Authority:** O3 SoT Group 2; `design.md`; emissions under `results/`
**Analyst code:** `analysis_code/refresh_015.py` (+ `analysis_code/interrogation_tables/`)
**Carve-outs:** no `estimand_validation.json` (SPDR integrity_selfcheck); no tradability; no family status change; no silent 014 redesign

> **Re-run note.** This rewrite is on the QA-approved re-run (`results/` dated 2026-07-24 06:24,
> screen exit 0). It supersedes the prior `analysis.md`, written on the pre-fix run. Two machineries
> changed and moved band labels: (1) the LABEL-SHUFFLE control is now a true 200-seed zero-fixed-point
> derangement on **both** arms with a bite plant (was plain BTC-only shuffle); (2) Δ-Brier / hit CIs
> now use the canonical circular block bootstrap (blocks 1/3/7 × 5-seed × 2000 resamples, conservative
> envelope) and the SUPPORTED band binds on point **and** CI. Net: SUPPORTED labels are now CI-backed
> rather than point-only, several counts moved by 1–4 cells, and the control now positively confirms
> the skill is real on both arms.

**Hypothesis (design §1):**
(2a) After defining states on **vol level**, can next regime/transition be predicted **better than persistence**?
(2b) Can next ZigZag swing be larger than current / last-K median with useful hit / calibration (direction-agnostic)?

**Unit pins (L-21).** Money-unit reads use these normaliser objects, verbatim from `screen_code`:
- `next_abs_oo` / `state_gap_bps` = `1e4 × |open_{t+1}/open_t − 1|` — next-bar **open-to-open absolute return in bps**, on the clock's own bars (H1 = 60-min clock-aligned; H4 = 240-min). `state_gap_bps` = mean over HIGH-state origins − mean over LOW-state origins (`features.py:165-168`, `transitions.py:341-345`).
- `rv20` = `sqrt(rolling_mean(r²_cc, 20))`, close-to-close returns on clock bars; R-MARKOV HIGH iff `rv20_t ≥` trailing median of rv20 over the warm-up window ending at t (H1 = 60 bars, H4 = 40 bars).
- `magnitude_bps` (2b) = `|end_price − start_price| / start_price × 1e4` for a ZigZag swing on **H1 close, 2.0 × Wilder ATR(14)** reversal (`zz_ordinal.py:96-100`). Ordinal targets compare consecutive swing magnitudes (direction-agnostic), so hit/Brier/rank-IC are unitless — no bps conversion enters the 2b skill numbers.

---

## 1. Integrity gate (Phase 0) — SPDR form

| Check | Result | Evidence |
|---|---|---|
| `integrity_selfcheck.hard_pass` | **PASS** | `results/integrity_selfcheck.json` → `hard_pass: true`; every HARD check `pass:true` |
| TRAIN-only fence | **PASS** | `max_ts_seen 1702854000e9 < train_end 1702857600e9`; test_start 2023-12-18; holdout 2025-01-08 never loaded |
| HMM fit causality | **PASS** | `n_fits=621`; rule `fit_end_ts < first origin ts of segment` |
| ZZ features ≤ confirm | **PASS** | `confirm_idx ≥ end_idx` on n_sampled=125 |
| Universe pin | **PASS** | family pin = results pin = recompute; `set_equal_all: true` (top-25) |
| Shock ≠ regime | **PASS** | R-SHOCK rows `is_shock_comparator=true`; excluded from headline; G4 titled shock not regime |
| Δ vs persistence emitted | **PASS** | 600 skill-metric rows carry `delta_brier_vs_pers` |
| Golden traces G1–G4 | **PASS** | `golden_traces.json` all_pass |
| No TEST/holdout contact | **PASS** | loads band=TRAIN end=CONFIRM_END |
| Estimand validation | **N/A (SPDR carve-out)** | screen uses integrity_selfcheck; not required |
| Deviations | **none** | `deviations: []`; IN-4/IN-5 both `weakens_clause:false` |

### Provenance / causality (construction HARD — attested)

| Object | Causal rule | Evidence |
|---|---|---|
| R-HMM-RV state | fit window ends before scored origins | G1 + integrity `hmm_fit_causality` (621 fits) |
| ZZ ordinal features | features of swing k at confirm; predict k+1 after confirm | G3 + `zz_features_le_confirm` |
| 2a forecasts | predictors ≤ t; target s_{t+k} strictly after t | design OBJECT-IDENTITY; monthly walk-forward ridge |

### Controls (informative) — now proper both-arm derangement + bite

Source: `results/label_derange_collapse.parquet` (561 rows, `n_seeds=200`, every `derangement_zero_fixed_points=True`), `results/controls.json`. `collapse_frac` = fraction of the 200 deranged-label draws whose Brier is **≤** the live Brier (≈0 ⇒ live skill survives only with true labels).

| Arm | powered cells | median collapse_frac | p95 collapse_frac | live→deranged Brier (median) | bite detected (frac of cells) |
|---|---:|---:|---:|---|---:|
| **2a** (level-regime × method × horizon) | 372 | **0.000** | 0.000 | 0.089 → 0.348 | **0.984** |
| **2b** (target × model) | 189 | **0.000** | 0.255 | 0.238 → 0.268 | 0.730 |

- **2a:** every powered cell fully collapses under label derangement (0% of 200 shuffles match live); the +0.05 bite plant is caught on 98.4% of cells ⇒ the test has power. The SUPPORTED 2a skill is not label-alignment.
- **2b:** median cell fully collapses; the weakest ~5% of cells (p95=0.255) retain up to a quarter of the deranged draws beating live — these are the small-n `T-GT-MED` cells where a +0.05 edge is within shuffle noise (bite caught on 73% of cells, a power disclosure, not a leak).
- **PERSISTENCE-ONLY (2a):** full Δ table on every non-persistence row; absolute accuracy ≠ skill (O3 §2.2).
- **FEATURE-SHIFT (2b):** illegal-future IC inflates over causal on liquid names (leak sentinel behaves); +1 lag usually drops IC — mixed on a few small-n alts.

### CI machinery — corrected, and an honest residual (binding for band reading)

The re-run replaced the single-block/single-seed bootstrap with the canonical circular block bootstrap (blocks 1/3/7 → origin-positions floored at H=k, 5-seed envelope, 2000 resamples; SUPPORTED uses the **conservative** envelope: 2a `max ci_hi < 0`, 2b `min hit_ci_lo > base` / `max Δbrier ci_hi < 0`). This is a real tightening: **SUPPORTED now requires point < 0 AND a negative conservative CI bound**, not a bare point. Independent recompute of the band from the emitted CI columns reproduces `band_label` on **all 372** powered 2a rows and **all 189** powered 2b rows (0 mismatches).

**Residual, disclosed:** the block-resample-mean CI does **not** always contain the full-sample point Δ-Brier. Of 197 SUPPORTED 2a cells, 126 (64%) have their point inside their own CI; coverage is **stickiness-dependent** — R-HMM-RV k=1 (stickiness ≈0.98) 0/15 covered, R-MARKOV k=12 (≈0.66) 14–15/16. Mechanism: per-origin `d_i = (p−y)² − (p₀−y)²` is dominated by rare switch days when stickiness is high, so a few days drive the sample mean while the day-resampled bootstrap mean sits elsewhere (a heavy-tailed-mean property, not a leak). **This cuts toward conservatism for the band:** where the point is an outlier-inflated negative (e.g. INJ k=1 point −0.0197 vs CI [−0.0037, −0.0011]), SUPPORTED still requires the conservative `ci_hi < 0`, so the label reflects the robust bound, not the inflated point. Net: SUPPORTED labels are more trustworthy than the old point-only stamps; read point Δ-Brier as the effect size and the conservative CI bound as the robustness floor.

**Spread/cost:** UNAVAILABLE_NOT_CHARGED — no fully-net / tradable / deployable claim.

---

## 2. Question list

| # | Question | Status |
|---|---|---|
| Q1 | Does any **level** model beat persistence on **Δ Brier** (CI-backed)? Which, where, how large? | **ANSWERED** §3–4 |
| Q2 | Ordinal ZZ hit/Brier/IC vs base under corrected CI? Best target/model? | **ANSWERED** §3–4 |
| Q3 | Recommended gate labels for later 014 amend / 016 features? | **ANSWERED** §6–7 |
| Q4 | What is usable as a gate vs sticky noise? | **ANSWERED** §6–7 |
| Q5 | Recommended per-arm disposition (informative)? | **ANSWERED** §6 |
| Q6 | Stickiness + state gaps per model? | **ANSWERED** §3 |
| Q7 | Is absolute high accuracy transition skill? | **ANSWERED** — **no** (O3 non-compliance if claimed) |
| Q8 | Do longer horizons (k=4,12) change the 2a story? | **ANSWERED** §3 |
| Q9 | H4 co-report vs H1 primary? | **ANSWERED** §3–4 |
| Q10 | Transition-hit arm powered? | **ANSWERED** — mostly UNPOWERED/disclosure |
| Q11 | Run-length forecast quality? | **ANSWERED** — disclosure; HMM caps at 48 |
| Q12 | Do 2b metrics recompute from `zz_ordinal`? | **ANSWERED** — BTC T-GT-CUR ridge exact match |
| Q13 | Does the derangement control collapse the skill (both arms)? | **ANSWERED** §1 — yes |
| Q14 | Are the corrected CIs trustworthy? | **ANSWERED** §1 — CI-backed w/ disclosed coverage caveat |
| Q15 | R-SHOCK Δ vs persistence (comparator only)? | **ANSWERED** — large but **not regime** |
| Q16 | Money / tradability? | **OUT OF SCOPE** |
| Q17 | Family status / 014 silent rewrite? | **REFUSED** |

Mandatory trading-object questions (per-leg P&L, occupancy-as-strategy, cost kill-line, Nautilus price-primary) are **N/A**: measurement objects are forecast-skill cells, not trade episodes (design OBJECT-IDENTITY).

---

## 3. Evidence FOR the hypothesis

Per-stratum tables: `results/per_stratum_2a.parquet`, `results/per_stratum_2b.parquet`; cell summaries `analysis_code/interrogation_tables/`.

### 3a — Arm 2a (level regime vs persistence)

**F1. R-MARKOV H1 k=1: 13/16 powered symbols beat hard "stay" with CI-backed Δ Brier<0.**

| clock | model | method | k | n_pow | med ΔBrier | n(pt<0) | **SUP** | WASH | med stick | med gap bps |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| H1 | R-MARKOV | empirical_p | 1 | 16 | **−0.00382** | 13 | **13** | 3 | 0.941 | 16.2 |
| H1 | R-MARKOV | logistic_ridge | 1 | 16 | −0.00247 | 13 | 9 | 7 | 0.941 | 16.2 |

- SUPPORTED symbols (empirical): INJ, DYDX, BNB, DOGE, SOL, LINK, MATIC, AVAX, 1000BONK, ADA, ETH, BTC, XRP (point −0.020 → −0.0007, each with conservative `ci_hi<0`). WASH: GALA, OP, 1000LUNC (point ≥0).
- Effect is **real but thin at k=1**: median removes only ≈6% of the residual persistence Brier (−0.0038 / 0.060). Δ **accuracy** vs persistence ≈ 0 — the gain is soft `P(stay)<1` calibration, not bar-to-bar flip timing.

**F2. Longer horizon — R-MARKOV Δ Brier grows large and stays SUPPORTED under the conservative CI.**

| clock | method | k | n_pow | med ΔBrier | **SUP** | WASH | med stick |
|---|---|---:|---:|---:|---:|---:|---:|
| H1 | empirical_p | 4 | 16 | **−0.02504** | **16** | 0 | 0.843 |
| H1 | empirical_p | 12 | 16 | **−0.11377** | **16** | 0 | 0.661 |
| H1 | logistic_ridge | 4 | 16 | −0.02513 | 14 | 2 | 0.843 |
| H1 | logistic_ridge | 12 | 16 | −0.11572 | 16 | 0 | 0.661 |

- Stickiness falls with horizon (0.94 → 0.84 → 0.66), so "stay" is a worse null and soft multi-bar forecasts add real calibration value. This is the **strongest 2a evidence** — but it is a multi-bar **level-persistence** forecast, not proof of flip timing (open question §5.3).

**F3. Level states separate next |move| (012-style gap) — the state object is not pure noise.**

| clock | model | n_pow | state_gap_bps (HIGH−LOW) | mean HIGH \|oo\| | mean LOW \|oo\| | n gap>0 |
|---|---|---:|---:|---:|---:|---:|
| H1 | R-MARKOV | 16 | **+16.2** | 80.7 | 64.5 | 16/16 |
| H1 | R-HMM-RV | 15 | **+35.2** | 99.8 | 55.1 | 15/15 |
| H4 | R-MARKOV | 16 | +25.5 | 152.2 | 128.9 | 15/16 |
| H4 | R-HMM-RV | 15 | +52.2 | 178.6 | 121.2 | 15/15 |

- R-HMM-RV separates the next-move distribution **more** than R-MARKOV (35 vs 16 bps H1) with lower HIGH occupancy — a better **state-label object** even though it is a poorer next-bar forecast (A2). Units: bps of next-bar open-to-open |return| (unit pin, header).

**F4. R-HMM-RV improves at longer horizons.** H1 logistic k=12 median ΔBrier **−0.0124** (11/15 SUPPORTED); empirical k=12 **−0.0032** (8/15). Weakly beats persistence only when the horizon stretches.

**F5. Construction/golden traces support causal decoding.** G1–G4 pass; universe pin clean; TRAIN fence clean.

### 3b — Arm 2b (ordinal ZZ)

**F6. T-GT-CUR is the robust winner — all three models, all 21 powered symbols, CI-backed both ways.**

| target | model | n_pow | med hit | med base | med Δhit | n(hit_ci>base) | med ΔBrier | n(Δbrier_ci<0) | med IC | med calib | **SUP** | WASH |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **T-GT-CUR** | **ridge_cont** | 21 | **0.683** | 0.475 | **+0.211** | **21** | **−0.041** | **21** | **0.370** | 1.65 | **21** | 0 |
| T-GT-CUR | logit_ridge | 21 | 0.703 | 0.475 | +0.222 | 21 | −0.052 | 20 | −0.165* | 1.00 | 21 | 0 |
| T-GT-CUR | ar1_threshold | 21 | 0.667 | 0.475 | +0.188 | 21 | −0.033 | 21 | 0.344 | 1.78 | 21 | 0 |

\*logit `rank_ic_cont` is against the continuous mag head; logit emits probability only, so IC is not its primary path — its hit/Brier are.

- **Both** CI legs clear on every T-GT-CUR ridge cell: `hit_ci_lo > base` (21/21) **and** `Δbrier_ci_hi < 0` (21/21). This is the cell the corrected CI machinery could have broken and did not.
- Per-symbol (ridge): Δhit +0.132 (OP) to +0.304 (1000BONK); majors BTC +0.154, ETH +0.161, SOL +0.213 — all SUPPORTED. Full table `results/per_stratum_2b.parquet`.
- Continuous rank IC ≈ 0.37 median reproduces SPDR-013 magnitude skill (IC 0.34–0.46).

**F7. Recompute check.** BTC T-GT-CUR ridge recomputed from `zz_ordinal.parquet`: n=499, hit 0.631263, Brier 0.219965 — bit-exact to emitted `ordinal_metrics` (incl. rank IC 0.4087).

**F8. Derangement control confirms 2b skill is real.** Median collapse_frac 0.0 across 189 powered 2b cells (§1) — deranging the labels destroys the forecast; the bite plant is caught on 73% of cells.

---

## 4. Evidence AGAINST the hypothesis

### 4a — Arm 2a

**A1. k=1 "skill" is soft calibration of a sticky process, not transition timing.** R-MARKOV stickiness ≈0.94; Δ accuracy ≈0; only ~6% of residual Brier removed. Sticky noise with a thin probabilistic edge — must **not** be sold as flip-timing (O3 §2.2).

**A2. R-HMM-RV does NOT beat persistence on the median H1 k=1 cell.**

| method | k | n_pow | med ΔBrier | n(pt<0) | SUP | WASH | med stick |
|---|---:|---:|---:|---:|---:|---:|---:|
| empirical_p | 1 | 15 | **+0.00256** | 4 | 3 | 12 | 0.982 |
| logistic_ridge | 1 | 15 | +0.00102 | 7 | 7 | 8 | 0.982 |

Stickiness ≈0.98 → persistence Brier ≈0.015, little room; soft empirical P is often **worse** than hard stay. The design handoff "prefer R-HMM-RV if SUPPORTED else R-MARKOV" therefore **defaults to R-MARKOV** for next-bar skill; R-HMM-RV earns its keep only as a state-label object (F3). (The old run's single R-HMM-RV logistic k=1 CONTRADICTED cell, BNB, is now WASH under the corrected CI.)

**A3. H4 k=1 does not reproduce the H1 R-MARKOV edge.** R-MARKOV empirical H4 k=1: median ΔBrier **+0.0002**, only 6/16 SUPPORTED (10 WASH); logistic H4 k=1 **+0.0035**, 1/16 SUPPORTED. H1 is the only clock with a coherent k=1 story. (H4 k≥4 does recover: emp k=12 median −0.145, 15/16 SUP.)

**A4. Δ log-loss vs hard persistence is largely artifactual** (rare switches → large 0/1 penalty). Not headlined; Brier Δ is the read.

**A5. CI coverage is imperfect on high-stickiness cells** (§1): 64% of SUPPORTED 2a cells contain their point inside their own CI. Disclosed and mitigated by the conservative-`ci_hi<0` band; read effect sizes on very-sticky cells (R-HMM-RV k=1) with the CI, not the outlier-prone point.

**A6. Transition-event estimands are weak.** `transition_events.parquet`: bands DISCLOSURE/UNPOWERED; sticky regimes → rare flips, n_trans<50 common. No powered transition-hit success comparable to 2b.

**A7. Run-length is disclosure-only.** R-MARKOV MAE ≈11–12 bars (mean actual ≈16); R-HMM-RV predicts E[run] pinned at the **48** cap vs actual ≈33 — stickiness-driven, poorly calibrated, not a forecast win.

**A8. Liquid-core power bias.** Several short-history listings never power on 2a (n_origins/n_dates below floor). Conditioner tables are majors-biased — acceptable under AMENDMENT-S1 but limits blind cross-universe gating.

**A9. R-SHOCK beats persistence strongly — and must be ignored as regime.** H1 k=1 median ΔBrier ≈ **−0.043 to −0.047**, 16/16 with `ci_hi<0`, stickiness ≈0.88. Shock-flag predictability, **not** level-regime success (O3 §2.1); disclosed only to contrast. Reporting it as a 2a win is a compliance fail.

### 4b — Arm 2b

**A10. T-GT-MED targets are materially weaker and drop SUPPORTED cells under the corrected CI.**

| target | model | n_pow | med Δhit | n(hit_ci>base) | med ΔBrier | n(Δbrier_ci<0) | **SUP** | WASH |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| T-GT-MED5 | ridge_cont | 21 | +0.102 | 19 | −0.013 | 9 | 19 | 2 |
| T-GT-MED5 | ar1_threshold | 21 | +0.082 | 17 | −0.008 | 7 | 17 | 4 |
| T-GT-MED5 | logit_ridge | 21 | +0.047 | 9 | +0.003 | 0 | 7 | 14 |
| T-GT-MED10 | ridge_cont | 21 | +0.058 | 11 | −0.008 | 5 | 12 | 9 |
| T-GT-MED10 | ar1_threshold | 21 | +0.048 | 8 | −0.005 | 3 | 7 | 14 |
| T-GT-MED10 | logit_ridge | 21 | +0.034 | 9 | +0.003 | 0 | 8 | 13 |

- MED5 ridge holds most cells (19/21) but MED10 ridge falls to **12/21** (was 16 pre-fix) — the median-based target is harder and its Brier edge rarely clears the CI. "Bigger than current swing" (CUR) is the clean, robust operational gate; "bigger than the rolling median" (MED) is a weaker, partly CI-fragile secondary.

**A11. Continuous→ordinal heads are under-dispersed.** T-GT-CUR ridge median calibration slope ≈1.65 (range 1.34–2.78): raw ridge scores are over-confident as probabilities. A gate should use the **rank/threshold** on the continuous head or a calibrated logit P, not the raw score as a probability.

**A12. Feature-shift not uniformly clean.** A few small-n alts show lag+1 IC ≥ lag0; do not claim perfect causal isolation on every symbol.

---

## 5. Anomalies & open questions

1. **Δ-Brier CI coverage on high-stickiness cells** (§1/A5) — a heavy-tailed-mean property, mitigated but not eliminated. Optional operator probe: trimmed-mean / median-of-per-day-means CI on the top-5 symbols to confirm the R-MARKOV k=1 negative is not a single-day artifact.
2. **HMM state code −1** during fit warm-up (a few % of H1 rows) — metrics correctly mask `state≥0`; if states are reused as live gates, define an "unknown" bucket.
3. **k=12 Δ-Brier: transition lead or mean-reversion of rv20 toward its median?** Not identified. For gating, a multi-bar **level forecast** may suffice without flip-timing language (for later 014/016).
4. **CONFIRM "verify" slice** named in design §0 is still not scored separately (carried MINOR from QA run 1/2). Not integrity-fatal; settle before any graduation.
5. **Not analysed:** money overlays, TEST/holdout, signed direction, 014 event interaction — out of scope until amendment.

---

## 6. Recommended per-arm disposition (informative only — NOT final, NOT family)

Reminder: SPDR outputs a routing disposition, not a family verdict or tradability claim. This is conditioner science for later **amendment** into 014/016.

| Stratum / arm | Recommendation | Driver |
|---|---|---|
| **2b ordinal — T-GT-CUR** (ridge_cont primary; logit/ar1 co-report) | **WORTH_EXPLORING** | 21/21 powered symbols SUPPORTED under both CI legs; Δhit +0.19–0.22; IC ≈0.37; recompute exact; derangement collapse 0.0 |
| **2b ordinal — T-GT-MED5** (ridge) | **WORTH_EXPLORING (weaker)** | 19/21 SUPPORTED; Δhit +0.10; secondary to CUR |
| **2b ordinal — T-GT-MED10** | **INCONCLUSIVE / weak** | ridge 12/21; ar1/logit ≤8/21; Brier edge rarely clears CI |
| **2a — R-MARKOV level gate, multi-bar (k=4/12)** | **WORTH_EXPLORING** | 16/16 SUPPORTED, ΔBrier −0.025 (k=4) / −0.114 (k=12), CI-backed; but it is level-persistence, not flip-timing |
| **2a — R-MARKOV transition, k=1 H1** | **WORTH_EXPLORING (thin)** | 13/16 SUPPORTED & CI-backed, but only ~6% of residual Brier; not a standalone bar-to-bar timer |
| **2a — R-MARKOV transition, k=1 H4** | **NOT_WORTH** | median ΔBrier ≈0; 6/16 (emp) / 1/16 (logit) SUPPORTED |
| **2a — R-HMM-RV as next-bar forecast (k=1)** | **NOT_WORTH** | median does not beat persistence (3–7/15 SUPPORTED at ≈0.98 stickiness) |
| **2a — R-HMM-RV / R-MARKOV as a level-STATE label** | **WORTH_EXPLORING** | HIGH−LOW next-\|oo\| gap +16 (Markov) / +35 (HMM) bps, sign-consistent across all powered symbols |
| **R-SHOCK** | **exclude — comparator only** | predictable but not a regime (O3 §2.1) |

**Overall:** accept the hand-off for **(a) the T-GT-CUR ordinal swing-size gate** and **(b) the level HIGH/LOW state labels (state-gap conditioner)**. Do **not** carry a bar-to-bar HMM transition timer as if proven.

**Would change if:** a trimmed/median-day CI put R-MARKOV k=1 Δ at 0 (downgrades the thin k=1 read to noise — does not touch the k=4/12 or the 2b conclusions); or T-GT-CUR fails on a CONFIRM-only slice or full multi-symbol re-derangement (both already covered here — it held).

**Final disposition is the operator's.**

### Recommended gate labels (for later 014 amend / 016 features — fold only by amendment)

| Gate ID | Spec | Use | Do not use as |
|---|---|---|---|
| **G-ZZ-CUR** | T-GT-CUR via **ridge_cont** continuous mag head → ordinal (primary); logit_ridge P co-report | "next swing likely larger than current" size/intensity filter | direction; standalone entry |
| **G-ZZ-MED5** | T-GT-MED5 ridge_cont (secondary) | milder size filter vs recent median | primary over CUR |
| **G-LVL-MARKOV** | R-MARKOV HIGH/LOW on rv20 trailing-median (H1) | slow vol-level conditioner; +16 bps HIGH−LOW gap class | transition timer; "94% accuracy" claim |
| **G-LVL-HMM** | R-HMM-RV HIGH/LOW on raw rv20 (H1) | alternative level object, larger +35 bps gap, lower HIGH occ | k=1 transition skill (median fails) |
| **G-STAY-K12** (research) | R-MARKOV empirical/logistic P(state_{t+12}) | multi-bar level-persistence score if 014 horizon ≈12 H1 | bar-to-bar flip trigger |
| **G-SHOCK** | R-SHOCK \|r\|≥p90 | named **shock flag only** | regime / level success |

---

## 7. Binding hand-off answers

1. **Any level model beats persistence on Δ Brier? Which, where, how large?** Yes — **R-MARKOV on H1**, strongest at **k=12** (median ΔBrier ≈ **−0.114**, 16/16 SUPPORTED CI-backed), clear at **k=4** (≈ **−0.025**), **thin but CI-backed** at **k=1** (≈ **−0.0038**, 13/16, ~6% of residual Brier). **R-HMM-RV** fails at H1 k=1 (median ≈ +0.001–0.003); recovers weakly at k=12. **H4 k=1** R-MARKOV ≈ stay. **R-SHOCK** beats stay but is **not** a level regime.
2. **Ordinal ZZ vs base? Best target/model?** **T-GT-CUR** — hit ≈0.68–0.70 vs base ≈0.48 (Δhit +0.19–0.22), ΔBrier −0.03 to −0.05, **21/21** SUPPORTED on both CI legs across ridge/logit/ar1. Best joint model **ridge_cont**; best binary **logit_ridge**. MED5 secondary; MED10 weak.
3. **Gate labels for later 014/016.** G-ZZ-CUR (primary) + optional G-ZZ-MED5; G-LVL-MARKOV / G-LVL-HMM as state labels; optional research G-STAY-K12; G-SHOCK only as a shock flag. Fold by amendment only.
4. **Gate vs sticky noise.** Gates: T-GT-CUR ordinal; level HIGH/LOW state labels; multi-bar R-MARKOV persistence score (research). Sticky noise: raw next-bar accuracy; R-HMM-RV k=1 forecast; stickiness-as-skill narratives.
5. **Disposition.** Accept hand-off for 2b ordinal + level-state labels; amend 014/016 later when the product needs gates. No family status change. No silent 014 rewrite.

---

## 8. Tables (analyst re-aggregation)

- `analysis_code/interrogation_tables/2a_summary_by_cell.csv` — full 2a per (clock×model×method×horizon).
- `analysis_code/interrogation_tables/2a_state_gap.csv` — level-state gap per clock/model.
- `analysis_code/interrogation_tables/2b_summary_by_cell.csv` — full 2b per (target×model).
- `analysis_code/interrogation_tables/control_collapse.csv` — derangement collapse + bite per arm.
- `results/per_stratum_2a.parquet`, `results/per_stratum_2b.parquet` — full per-symbol stratum tables.

### 8.1 Spot recompute (BTC T-GT-CUR ridge)

| metric | screen | recompute from zz_ordinal |
|---|---:|---:|
| n | 499 | 499 |
| hit | 0.631263 | 0.631263 |
| brier | 0.219965 | 0.219965 |
| rank IC | 0.408727 | 0.408727 |

---

## 9. Operator hand-off (plain language)

**What worked (and is now CI-backed).**
- Predicting whether the **next ZigZag swing is bigger than the current one** works on every coin we could power — about **+20 percentage points** over the coin's own base rate, and it survives the stricter confidence check on all 21. The best model ranks swing size with a correlation ≈0.37 (matches earlier magnitude work).
- **Slow high/low vol-level** labels still separate calmer vs choppier next moves (the "high" state's next move is ~16 bps bigger for the simple rule, ~35 bps bigger for the HMM). Good as **context flags**, not trade signals by themselves.
- The "shuffle the answers" control now runs properly on **both** halves of the screen, over 200 tries with no accidental matches, and it can see a small planted edge — so it confirms the skill above is real, not a labelling fluke.

**What did not work (or barely).**
- "Will the vol regime flip next hour?" is mostly **stickiness** — a model that just says "stay" is already ~94–98% right, and beating it one bar ahead is **tiny** for the simple rule and **fails** for the vol-HMM. Looking further ahead (~12 hours) the soft forecast beats "stay" clearly — still conditioner science, not a trade claim.
- The "bigger than the recent-median swing" target is **weaker** than "bigger than the current swing," and the 10-swing version is genuinely mixed.

**One honest caveat.** On the very sticky cells the confidence interval doesn't always sit on top of the raw number (rare flip days dominate the average). The label is built to be cautious about this — it needs both the raw number and the cautious bound on the right side — so the "supported" stamps are safe; just trust the interval over the raw number on those cells.

**Recommendation.** Accept this as a successful conditioner hand-off — carry the **next-swing-larger gate** and the **vol high/low state labels** into 014/016 by a written amendment when you want them; do **not** wire in an hour-to-hour "regime flip timer" as if proven. Integrity checks (no future peeking, no holdout, no trade claim) all passed. Final call is yours.
