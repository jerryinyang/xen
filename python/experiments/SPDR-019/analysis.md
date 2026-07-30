# Data Analysis: SPDR-019 phase (a)

**Family / hypothesis:** `CF-VOLDIR-001` / `HYP-D6` · **Lane:** SPDR, TRAIN-only, 0 counted TEST reads
**Emission:** commit 5027615 · 25 symbols · `n_boot` 2000 · 5,753,583 episodes · 13,376 metric rows
**Analyst scripts:** `analysis_code/a1_apparatus_m15.py` … `a7_anatomy.py` (no `screen_code/` import; no experiment-local accounting; canonical identity re-derived from the emitted `(p, W, L)` only)

**Binding claim boundaries observed throughout.** Cost is **gross-only**: spread is `UNAVAILABLE_NOT_CHARGED` (AMENDMENT-C5), so every net-looking number below **overstates** performance, and the claims *fully-net*, *cost-complete*, *tradable*, *deployable* are **prohibited and not made**. `p_be_net` is a **disclosed reference** and enters no estimand or comparison. Interpretation bands are **labels, never gates** (AMENDMENT-C7): no `powered`/`unpowered`/`at_target`/`NOT_RESOLVABLE` flag exists in this emission and no canonical MDE threshold is applied. Pooled figures are **disclosure**; per-stratum reads are the object. Nothing is machine-dropped.

**Primary read (design §8.1 / AMENDMENT-9):** **M15, full TRAIN, pooled across symbols, on Δ log R = log R(layer) − log R(L0)**. On M15 **absolute** log R is an **entry-quality disclosure only**. H1 is the co-report and clock-effect check and is the only clock where the absolute read is interpretable. Clocks are **never pooled**. There is no D1.

---

## 1. Apparatus verification (Phase 0)

The SPDR lane carries no `estimand_validation.json` (lane-exempt). Its blocking artifact is `results/integrity_selfcheck.json`, which reports **28 of 28 HARD checks passed, `all_hard_pass: true`, `hard_fail_names: []`**, check count reconciled by name (P-23/L-52). I did not take that on trust where a number matters.

### 1.1 What I re-derived independently

| Check | Result | Evidence |
|---|---|---|
| Row accounting: 4 buckets reconcile | **PASS** | 12,503 carry a CI + 33 exempt + 840 sizing-suppressed + **0 unclassified** = 13,376; zero overlap (`a2`) |
| Identity `abs(p·W − (1−p)·L − mean) < 0.01` bps | **PASS** | max residual **5.68e-13** bps over 13,037 cells, re-derived by me (`a2`) |
| `log R` is exactly slope-1 | **PASS** | max `abs(log(W/L) − log((1−p)/p) − log_R)` = **0.0** over 12,192 cells; G5 scanned 85 columns, 0 fitted-slope tokens |
| `log R` never unaccompanied | **PASS** | 0 rows with finite `log_R` and null `ci_low` in any of the three artifacts |
| Exempt reasons validated on the cell's own `p,W,L,n,n_dates` — never on `log R` | **PASS** | all 28 `LOG_R_UNDEFINED` rows have `p ∈ {0,1}` or a NaN wing; all 5 `N_DATES_LT_2` rows have `n_dates = 1` **and** a defined `log R` (correctly exempted for the *other* condition) |
| Block rule, six clauses, clause-by-clause | **PASS** | day-blocks `{1,3,7}`; per-calendar-day sufficient statistics; min block 24 h ≥ max hold 20 h; min/max envelope over 3 blocks × 5 seeds (15 CIs/cell, `min_observed = max_observed = 15`); **bit-level equivalence to `xen.evaluation.block_bootstrap_ci`, abs diff 1.4e-16 / 1.4e-15** |
| Envelope is genuinely conservative | **PASS** | recomputed: M15/L0/δ=0.25 envelope `[−0.03112, +0.03419]` = min of the three per-block `ci_low_seed_range` minima and max of the `ci_high_seed_range` maxima (`a2`) |
| Derangements are derangements | **PASS** | `fixed_point_count = 0`, measured; ≥2000 seeds on 12 controls; flipped fraction 0.4868–0.5125 (mean 0.4995) — non-degenerate binary derangement, as AMENDMENT-19a requires |
| Exit-matched nulls (L-24.2/F04) | **PASS** | 20 time-exit arms use `TIME_EXIT_NEGATION` with `max abs(r_flip + r) = 0.0` exactly; **all 12 target/trail arms use `TARGET_TRAIL_RERESOLVE` with non-zero flip residual (2,234–4,586 bps)** — proving genuine M1 re-resolution, not sign negation |
| Fences | **PASS** | `max(exit_ts)` = 1702857540e9 ns < TRAIN_END 1702857600e9; 0 queries ≥ holdout 2025-01-08 |
| Signal accounting closes | **PASS** | BTCUSDT/M15/δ=0.5: 3,887 episodes + 1,480 suppressed + 781 unfilled = **6,148 = every signal I derive myself** (`a6`) |
| No local accounting | **PASS** | screen emits availability/residual bps, not booked P&L |

### 1.2 The M15 checks the prompt required (QA runs 10–12 never made them)

**(a) M15 hold conversion, hours → bars — CORRECT.** This was the stop-and-report risk. Measured on time-exit episodes (`a1`):

| variant | clock | `active_hold_hours` | realised held (min / p50) |
|---|---|---|---|
| `L0_BASELINE` | H1 | 1.0 | 1.000 h / 1.900 h |
| `L0_BASELINE` | **M15** | **1.0** | **1.000 h / 1.217 h** |
| `L4_HOLD_4H_UNMOD` | M15 | 4.0 | 4.000 h / 4.217 h |
| `L4_HOLD_12H_UNMOD` | M15 | 12.0 | 12.000 h / 12.217 h |
| `L4_HOLD_20H_UNMOD` | M15 | 20.0 | 20.000 h / 20.217 h |

The hold is an **hour** on both clocks. Had the bar/hour ambiguity survived, M15 `L0` would read 0.25 h. The finer M15 median (1.217 h vs H1's 1.900 h) is exactly right: the exit resolves at the first decision-clock open at or after the elapsed hours — on M15 that adds 0–15 min, on H1 0–60 min. **100 % of M15 time exits land on the 15-minute grid and only 24.9 % on the hour** — the exit resolves on the M15 clock.

**(b) M15 fills — CORRECT, re-derived from raw M1 catalog bars.** 400 first `L0`/δ=0.5 episodes each on BTCUSDT and SOLUSDT: **400/400 fill prices match** the §2 rule (stop price, or the M1 open where gapped — 1–2 gap cases per cell, all taken adversely), **400/400 causal** (fill bar *starts* at or after the decision-bar close).

**(c) M15 end-to-end — 500/500 exact.** I rebuilt the M15 clock, Wilder ATR(20), the three-bar pivot-plus-momentum entry, the stop fill and the time exit from raw M1 bars with no `screen_code` import (`a6`). Of 500 BTCUSDT/M15/δ=0.5 `L0` episodes, **500 match on stop price, fill timestamp, fill price, exit timestamp, exit price *and* `r_bps`**. Strongest provenance evidence in the run; closes the flagged M15 gap.

**(d) Day-block rule behaves as a calendar-day rule — CONFIRMED.** `n_dates` equals the number of distinct UTC calendar days of the episodes' **fill** timestamps: over 24 probe cells (4 variants × 2 clocks × 3 δ), `n_dates − (my own distinct fill-day count)` is **exactly 0 in every case** (`a2`). Median `n_dates` is 893 on M15 against 743 on H1 — same order, as a calendar rule requires; a block stated in *bars* would show a ≈4× divergence. This is what makes the CI construction identical across clocks and prevents the Phase-010 under-blocking shape.

### 1.3 Verification gaps that remain open

1. **Both tripwires ran on H1 / BTCUSDT only.** `integrity_selfcheck.json` records `clock: "H1", symbol: "BTCUSDT"` for TRIPWIRE-1 (`shift_is_exact_one_row: true`, `changed_state_rows` 45,117, `changed_selection_episodes` 372, all three structural conditions met, 15 variants compared) and TRIPWIRE-2 (851 clock-vs-M1 differing fills; 4 both-reachable bars; `count_favourable_diff == count_both_reachable == 4`; `favourable_price_never_worse: true`; 0 price-identical bars). **Neither ran on M15**, the clock carrying the primary read. My §1.2 work substitutes for the *fill-rule* half; **no causal-misalignment tripwire exists on M15.**
2. **All four controls ran on one cell: `L0_BASELINE | H1 | δ=0.5 | POOLED | TRAIN`** (plus per-arm H1 expansions). **No side-derangement, entry-timing or magnitude-matched control on M15.** The design's §8.1 rationale for the M15 delta framing rests on SPDR-013's M15 direction result; this run does not re-measure it.
3. **TRIPWIRE-1 emits no payoff deltas with CIs.** §6.1 requires them as reported (never pass-bearing) statistics. The three structural HARD conditions are present and met; the informative payoff-delta block is absent.

None invalidates the emission. Items 1–2 bound how far an M15 conclusion can be pushed.

---

## 2. Question list

| # | Question | Where |
|---|---|---|
| 1 | Do per-cell totals reconcile? | §1.1 — yes, 5.7e-13 bps |
| 2 | Is the P&L object the estimand's object? | §3.1 — yes, both the signed episode |
| 3 | Per-episode `r` distribution, per cell | §3.1 |
| 4 | Episode anatomy / exclusivity / suppression | §3.1, §1.1 |
| 5 | Concentration — survives dropping top winners? | §5.2 A4 |
| 6 | Per-year stability | §5.2 A5 |
| 7 | Every headline per stratum | §4 |
| 8 | Occupancy vs the design story | §3.1 |
| 9 | Physicality (return/κ/fill rate) | §3.1 |
| 10 | Exposure risk | Partly §3.1; **UNANSWERED** on drawdown — gross residual screen with no equity path; manufacturing one would be local accounting (L-18) |
| 11 | Cost sensitivity | §3.2 — disclosure only (C5) |
| 12 | Collapse fraction per control, not survive/die | §5.5 |
| 13 | "What would make this wrong?" per headline | §5.2 A4, A6; §5.4; §1.2 |
| 14 | MDE where a negative matters | §4.4 |
| 15 | Is the M15 hold conversion right? | §1.2(a) — yes |
| 16 | Does the day-block rule behave as a calendar rule? | §1.2(d) — yes |
| 17 | Does the modulated arm beat its comparator? | §5.2 A3 — the decisive question; no |
| 18 | Is prediction 4 (shock ⊥ level) resolvable? | §5.2 A6 — not on 31 % of rows |
| 19 | Is the phase-(b) trigger met? | §7 — yes, narrowly |
| 20 | Are the flagged 1000BONKUSDT rows measured interactions? | §5.3 — no |

---

## 3. What the strategy actually is

### 3.1 Physicality

`L0`, δ=0.5, pooled TRAIN (`a7`, `a3`):

| | M15 | H1 |
|---|---|---|
| episodes | 69,413 | 18,970 |
| signals | 108,441 | 25,370 |
| fill rate (episodes/signals) | 0.640 | 0.748 |
| suppressed signals | 26,625 | 164 |
| `p` | 0.4774 | 0.4641 |
| `p_be` | 0.4761 | 0.4506 |
| `W` / `L` bps | 85.31 / 77.67 | 111.62 / 96.51 |
| `W/L` | 1.0984 | 1.1567 |
| **`log R`** | **−0.00529** | **+0.05502** |
| gross mean/episode bps | −0.210 | +2.885 |
| median episode bps | −3.02 | −6.48 |
| q01 / q99 bps | ≈ −316 / +423 | ≈ −399 / +601 |
| flat (`r = 0`) | 1.93 % | 1.39 % |
| κ = median(`r`/`mfe`) | +0.017 | 0.000 |
| occupancy (per symbol, median) | **36.7 %** | **15.9 %** |
| exact-span fraction | 1.52 % | 0.19 % |

**What the object is.** A high-frequency, near-coin-flip, slightly-positive-payoff-ratio breakout with a **median losing episode** and money in a fat right tail (q99 +423/+601 bps against a median of −3/−6). κ ≈ 0 means the median episode captures **none** of its own maximum favourable excursion — exactly what an unmodulated 1-hour time exit should do; a non-tradable ceiling-relative diagnostic that multiplies nothing (SoT §2.1).

**Occupancy is honest for the design story** — 15.9 % (H1) / 36.7 % (M15) is a part-time event-triggered object, not a grid. But the M15 figure carries a population caveat: **34 % of M15 δ=0.25 signals are SUPPRESSED** (62,020 of 180,782) because a symbol holds at most one open episode, against **1.6 %** on H1. The clocks trade materially different populations of the same signal stream — an independent reason the "never pool the clocks" rule is right, beyond the direction argument.

**`p` sits essentially on its own break-even in both clocks** (M15 0.4774 vs 0.4761; H1 0.4641 vs 0.4506) — the design's predeclared, expected, acceptable baseline (§1), not a defect.

### 3.2 Cost — disclosure only

Disclosed partial floor **13.5 bps** (fees + discrete funding + allowance; `unit_pin.json`), **spread not charged**, so the true floor is strictly higher. Gross mean per episode **−0.21 bps (M15) / +2.89 bps (H1)** — at best **0.21× the partial floor**. The disclosed-reference `p_be_net` runs 0.485–0.567 across the six `L0` cells and **exceeds the realised `p` in every one**. This enters no estimand, threshold, band or comparison (C5); no tradability claim is made or implied.

σ̂ pin: pooled Parkinson-EWMA median **50.92 bps**; pooled ATR20 median 0.01331; 212,224 pooled H1 bars — all measured at run.

---

## 4. Per-stratum reads with intervals

### 4.1 The primary read — M15, TRAIN, pooled, Δ log R vs L0

87 layer/device cells (29 non-`L0` variants × 3 δ):

| read | count |
|---|---|
| covers the mirror | **85** |
| above the mirror (`ci_low > 0`) | **1** |
| below the mirror (`ci_high < 0`) | **1** |

The single positive: **`L4_TRAIL_B2_MOD`, δ=0.5: Δ log R = +0.02578, CI [+0.000125, +0.05045]**, `block_mde` 0.0257, `n_dates` 902. Its `ci_low` clears zero by **1.25e-4 log units** — 0.5 % of the cell's own MDE. The single negative: `L4_HOLD_20H_UNMOD`, δ=0.5: Δ log R = −0.10562, CI [−0.18246, −0.02911].

**Against the predeclared false-positive expectation, as required.** At the 95 % CI the design predeclares 2.5 % of cells reading `ci_low > 0` under a true global null. For this tier that is **2.2 expected; 1 observed.** The primary read produces **fewer** resolvable positives than chance alone.

Baseline the deltas are measured from (§8.1 requires this explicitly): `L0` M15 pooled TRAIN log R = **+0.00058** (δ=0.25, CI [−0.0311, +0.0342]), **−0.00529** (δ=0.5, CI [−0.0423, +0.0322]), **−0.00692** (δ=1.0, CI [−0.0731, +0.0628]). All three cover the mirror. The M15 entry is **not** sitting resolvably below the mirror, so the delta framing is a precaution here rather than a rescue.

### 4.2 Co-report — H1, TRAIN, pooled

**Δ log R: 0 of 87 above, 0 below — 87/87 cover.** Expected under a global null: 2.2 above. A complete wash with no cell in either tail.

**Absolute log R (interpretable on H1 only): 4 of 93 above, 0 below** (expected 2.3):

| variant | δ | n | log R | CI | `block_mde` | I² |
|---|---|---|---|---|---|---|
| `L4_TARGET_A1_UNMOD` | 0.5 | 19,044 | +0.0731 | [+0.0115, +0.1342] | 0.0619 | 0.099 |
| `L4_TARGET_A1_UNMOD` | 1.0 | 4,721 | +0.1849 | [+0.0632, +0.3112] | 0.1217 | 0.553 |
| `L4_TARGET_A1_MOD` | 1.0 | 4,706 | +0.1563 | [+0.0373, +0.2806] | 0.1190 | 0.510 |
| `L4_TRAIL_B1_UNMOD` | 1.0 | 4,722 | +0.1769 | [+0.0198, +0.3375] | 0.1571 | 0.000 |

**Three of the four are the UNMODULATED arm** — the constant-width comparator that cannot see the volatility forecast. Whatever these contain is a property of *placing a tight boundary at all*, not of the opportunity model. The L4 stage exists to separate device from forecast, and it separates them the wrong way for the hypothesis.

### 4.3 M15 absolute log R — entry-quality disclosure only

3 of 93 above (`L2_INTERACTION_HMM_X_K12` δ=1.0 at `ci_low` +1.17e-4; `L4_TRAIL_B1_MOD` δ=0.25 and δ=0.5), 2 below (`L4_HOLD_20H_UNMOD` δ=0.5, `L4_HOLD_4H_UNMOD` δ=0.5). **Per AMENDMENT-9 none may be reported as a capture-geometry result** and none is used below.

### 4.4 Per-symbol tier — heterogeneity disclosure, with its resolution

| tier | rows | `ci_low > 0` | expected @2.5 % | `ci_high < 0` | median `block_mde` |
|---|---|---|---|---|---|
| pooled TRAIN M15, Δ | 87 | 1 | 2.2 | 1 | 0.0393 |
| pooled TRAIN H1, Δ | 87 | 0 | 2.2 | 0 | 0.0768 |
| pooled TRAIN M15, abs | 93 | 3 | 2.3 | 2 | 0.0503 |
| pooled TRAIN H1, abs | 93 | 4 | 2.3 | 0 | 0.0943 |
| per-symbol TRAIN, abs | 4,444 | 169 | 111.1 | 143 | 0.2587 |
| per-symbol TRAIN M15, Δ | 2,100 | **107** | 52.5 | 37 | — |
| per-symbol TRAIN H1, Δ | 2,092 | 49 | 52.3 | 40 | — |
| all rows, abs | 12,503 | 401 | 312.6 | 378 | — |

Two things to separate. The **absolute** per-symbol excess is roughly **symmetric** (169 up vs 143 down against 111 expected each way) — the signature of variance in excess of nominal, i.e. residual dependence the day-block does not fully absorb, **not** a directional effect. The **M15 per-symbol Δ tier is the one asymmetric result in the run** (107 up vs 37 down, 52.5 expected) and the strongest positive signal the emission contains. Per §13 it may not be carried without its resolution: **median `block_mde` 0.259 log units**, so a cell here cannot see anything smaller than roughly a quarter log unit; per-symbol rows are heterogeneity disclosure, not independent discoveries.

**Resolution distribution behind every aggregate above** (§13, mandatory — on `block_mde`, the location-free measure; see §5.4 for why not `mde50`):

| tier | n | median `block_mde` | <0.02 | <0.03 | <0.05 | <0.075 | <0.10 | <0.15 |
|---|---|---|---|---|---|---|---|---|
| pooled TRAIN M15, Δ | 87 | 0.0393 | 10 | 29 | 51 | 78 | 85 | 87 |
| pooled TRAIN H1, Δ | 87 | 0.0768 | 7 | 8 | 23 | 43 | 57 | 77 |
| pooled TRAIN M15, abs | 93 | 0.0503 | 0 | 13 | 44 | 80 | 88 | 91 |
| pooled TRAIN H1, abs | 93 | 0.0943 | 0 | 0 | 2 | 27 | 49 | 71 |
| per-symbol TRAIN, abs | 4,444 | 0.2587 | 6 | 6 | 7 | 116 | 375 | 925 |

(median `mde50`: 0.0442 M15 abs, 0.0515 H1 abs, 0.1979 per-symbol — recorded for completeness, **not used**, see §5.4.)

**The minimum detectable effect, plainly.** On the primary read the median cell resolves to **0.039 log units**; only 29 of 87 resolve below 0.03 and 10 below 0.02. A real capture effect of **0.01–0.03 log units would be invisible**, and every covering CI in §4.1 reads as *"we could not see an effect this small on this cell"*, never *"there is no effect"* (B-5). M15 buys real precision over H1 — 0.039 vs 0.077, roughly the √2 the calendar-blocked episode counts support, **not** the ~4× the raw bar count suggests, exactly as §8.1 predicted.

`L0` per-symbol spread, TRAIN: log R −0.51 to +0.38 (H1 δ=0.25), −0.47 to +0.12 (M15 δ=0.25) across 25 symbols with median `block_mde` 0.19 / 0.11 — inside the per-symbol noise. Pooled homogeneity supports the pooled line: median I² **0.156 (M15)**, **0.000 (H1)**, with only 9.7 % / 5.4 % of cells above I² = 0.5. `pooled_status` is emitted as `PRIMARY_CANDIDATE_OPERATOR_JUDGES` with `DISCLOSURE_ONLY_LANE_DEFAULT` where homogeneity does not support it — the §9 conditional-primary machinery is present and the operator judges it.

### 4.5 Predeclared vs realised resolution (calibration audit)

All **5,148** predeclared strata carry `prior_status = UNKNOWN_NO_PARENT_MEASURED_POPULATION` with `expected_n` and `expected_mde50` **null**; 0 rows carry a non-null prior. The signed discrepancy distribution the design requires reported in full is therefore **empty by construction**. This is the intended outcome (no parent ever ran this entry), consumed by nothing: every read uses realised CI/MDE only.

---

## 5. Evidence

### 5.1 Evidence FOR the hypothesis

**F1 — One pooled primary cell clears the mirror, and it is a modulated arm.** `L4_TRAIL_B2_MOD`, M15, δ=0.5: Δ log R **+0.0258, CI [+0.000125, +0.0504]**, n 89,766, 902 days, `block_mde` 0.0257. The only cell in the primary tier that clears, and it is the `ŝ`-responsive arm rather than its constant-width twin — the direction the mechanism predicts. Weight: margin 1.25e-4 log units, and 1 positive is *below* the 2.2 expected by chance.

**F2 — L1 shows a monotone dose-response in the forecast on M15** (`a4`):

| δ | d≥5 | d≥7 | d≥9 |
|---|---|---|---|
| 0.25 | −0.0024 | +0.0054 | +0.0208 |
| 0.5 | +0.0149 | +0.0212 | +0.0268 |
| 1.0 | +0.0337 | +0.0570 | **+0.1149** |

Nine of nine cells move the right way; H1 shows the same ordering at δ=0.25 (+0.0185 → +0.0321 → +0.0533). A dose-response is harder to produce by chance than a single cell. Weight: the CI widens faster than the estimate grows (`block_mde` 0.055 → 0.088 → 0.143 at δ=1), so **all nine cover the mirror**, consistent with selecting a higher-dispersion subsample at constant residual.

**F3 — On M15 the modulated arm beats its comparator more often than not.** Across 27 M15 device pairs, **MOD > UNMOD in 19** (median gap **+0.0060** log units). Weight: see A3.

**F4 — The L2 interaction is not flat where measurable.** Pooled M15 TRAIN interaction rises with δ (+0.0194 → +0.0266 → +0.0588); at δ=1.0 `ci_low` = **+1.17e-4**. Two per-symbol cells (ADAUSDT, BNBUSDT) also clear. Weight: 96 of 311 interaction rows are structurally undefined (A6); pooled clearance margin ~1e-4.

**F5 — The layers do select, and they select the thing the mechanism names.** The L-51 check (`selection_check.json`, 22 subsets, all 12 required tokens covered) shows the ŝ-decile cuts move **payoff scale by 1.76–2.19×** while moving **sign share by only 0.006–0.015**. The forecast does exactly what SPDR-012/013/015 said — rescales the magnitude distribution without touching direction. The apparatus is measuring a real conditioning variable.

**F6 — H1's four positive absolute cells are real cells.** n 4,706–19,044, `block_mde` 0.062–0.157, I² 0.000–0.553; `L4_TARGET_A1_UNMOD` δ=0.5 clears with n 19,044 and I² 0.099 at log R +0.073, CI [+0.012, +0.134].

### 5.2 Evidence AGAINST the hypothesis

**A1 — The primary read is a wash, and less than chance.** 85 of 87 pooled M15 Δ log R cells cover the mirror; **1 clears where 2.2 are expected under a true global null**, by 1.25e-4 log units. On H1, **0 of 87** clear. Across both clocks' pooled Δ tiers, 1 of 174 cells clears against 4.4 expected. The design's own falsifier — "log R indistinguishable from zero under every layer at a stated MDE" — is met on the primary read at the resolution achieved (median MDE 0.039).

**A2 — The positive absolute H1 reads come from the DEVICE, not the information.** Three of four are `UNMOD` — the arm whose boundary is a per-symbol TRAIN-median constant that cannot respond to ŝ. The one MOD cell (`L4_TARGET_A1_MOD` δ=1.0, +0.156) is **lower** than its own UNMOD twin (+0.185).

**A3 — MOD vs UNMOD is a coin flip once both clocks are read.** M15 19/27, median gap +0.0060; **H1 12/27, median gap −0.0022**. The median M15 gap is **0.16× the median MOD `block_mde` (0.0375)** — six times too small for this run to see even if real. Pooled: 31 of 54 pairs favour MOD (0.57), indistinguishable from 0.5. **Not one of the 54 MOD-vs-UNMOD differences is itself resolvable.**

**A4 — The one H1 result that looks positive is tail-driven and fragile.** `L0` H1 δ=0.5 log R +0.0550 on 18,970 episodes collapses monotonically as winners are removed: +0.0503 (drop 1), +0.0457 (3), +0.0415 (5), +0.0320 (10), **−0.0189 (drop 50 of 18,970 = 0.26 %)**. A residual that changes sign on a quarter of one percent of the sample is not a stable payoff geometry. M15 `L0` starts at −0.0053 and only falls (−0.0368 dropping 50).

**A5 — Not stable across years, and it flips sign between clocks.** `L0` δ=0.5 log R by year: H1 −0.102 (2021, n 493) → +0.074 (2022) → +0.056 (2023); M15 **+0.089 (2021) → +0.037 (2022) → −0.027 (2023)**. The clocks trend in **opposite directions** over the same calendar; the sign of the pooled figure depends on which clock and year is emphasised.

**A6 — Two layers of the L2 level axis are partly inert, so prediction 4 is not resolvable where it matters.** `L2_LEVEL_RMARKOV_K4` and `L2_LEVEL_RMARKOV_K12` each keep **100 % of `L0`'s episodes on 96 of 318 rows (30.2 %)** — the regenerated k12 probability is ≥ 0.5 on every episode there, so the gate discriminates nothing. The joint arm then equals the shock arm and the interaction collapses algebraically: **96 of 311 interaction rows (30.9 %) read exactly log R = 0.0 with a zero-width CI [0, 0]**, including cells with n up to 1,037. Traced one (1000BONKUSDT/H1/CONFIRM/δ=0.25): `L2_LEVEL_RMARKOV_K12` is bit-identical to `L0` (n 555, same p, W, L, log R), joint = shock, so Δjoint − Δshock − Δk12 ≡ 0 in every replicate. **These zero-width CIs are degenerate by identity, not the L-20 small-n bootstrap defect** — but they are non-measurements that count as "covers the mirror" in any tally, and AMENDMENT-20(c)'s guard does not catch them because all four input arms *do* carry a defined `log R`. Prediction 4 (shock ⊥ level, 51–62 % agreement) is **untested on nearly a third of its rows.**

**A7 — One of the 33 named variants carries no independent information.** `L4_HOLD_1H_UNMOD` is **bit-identical to `L0_BASELINE`** on every emitted quantity (n, p, W, L, log R, CI — all 6 pooled TRAIN cells verified) — correctly so, since `L0` *is* a 1-hour unmodulated hold with no target or trail. Its Δ log R is exactly 0 with a zero-width CI on **156 of the 4,366 delta rows**. Effective independent variant count is **32, not 33**, and 156 delta rows are structurally-zero filler inflating the "covers the mirror" denominator.

**A8 — The controls suggest a *direction* effect on H1, the one thing this design does not claim and explicitly assumes away.** Side derangement on the H1 `L0` cell: live log R +0.0550 against a null of mean +0.0035, sd 0.0249 — **percentile 0.9755, collapse fraction 0.058**. Entry-timing: **percentile 0.985, collapse 0.022**. Plant curves detect at every rung down to 5 bps (0.098 σ) at rate 1.0, so the controls are not blind. Read naively this says the H1 entry's side and timing *do* carry information, making the H1 absolute reads a direction result, not a capture result (and §13 forbids researching direction). **But the percentile is not comparable to the CI:** the derangement null's sd 0.0249 implies a ±1.96 sd band of 0.049 against the block-bootstrap half-width of **0.083** on the same cell — the permutation destroys the day-block dependence and is **~1.7× too narrow**. The design's primary instrument is the block CI, which **covers the mirror**. Both controls are `DISCLOSURE_ONLY` and appear in no HARD list (M-5), correctly.

**A9 — The magnitude-matched comparator is thin exactly where L1 lives.** `L1_SHAT_DECILE_GE7`: percentile 0.816, collapse **0.597**, live +0.0784 vs matched null mean +0.0473 — not resolvable. Worse, `per_decile` shows the **top decile matched WITH REPLACEMENT** (2,490 selected against 1,126 complement episodes available) and deciles 1–2 `matched: false`. `deciles_with_demand_unmatched: []` is vacuously true only because 0 episodes were selected in those deciles. So the M-3 comparator — the mandatory guard against "this was just a big bar" — resamples a 2.2×-oversubscribed complement in the decile carrying L1's population.

**A10 — Even the gross reads sit far below the disclosed partial cost floor.** Gross mean per episode −0.21 bps (M15) / +2.89 bps (H1) against a partial floor of 13.5 bps with **spread not charged at all**. Bears on no estimand (C5), not a verdict input; recorded as context.

### 5.3 The 1000BONKUSDT rows — required note (QA run 12, R12-01)

The three `L2_INTERACTION_HMM_X_K12` / `1000BONKUSDT` / **H1 / DESIGN** rows (δ = 0.25, 0.50, 1.00) **must not be read as measured interactions.** Confirmed on the emission:

| δ | interaction n | log R | CI | joint-arm n | joint-arm `n_dates` |
|---|---|---|---|---|---|
| 0.25 | **2.0** | +1.4225 | **[+0.0930, +2.3869]** | 2 | **1** |
| 0.50 | **2.0** | +1.1067 | [−0.4511, +1.9946] | 2 | **1** |
| 1.00 | **2.0** | −0.7264 | [−1.5783, +0.0300] | 2 | **1** |

They pass every check and honestly disclose `n = 2.0` on the row. The δ=0.25 row reads `ci_low > 0` — a two-episode cell whose joint input arm spans **one calendar day** and is itself exempt from carrying a CI (`N_DATES_LT_2_NO_DAY_BLOCK`). Note the interaction row's own `n_dates` (51, 39, 12) is inherited across input arms and **does not describe the 2-episode joint arm** — a reader checking `n_dates` alone would not see the problem. These rows carry no information and are excluded from every read above.

### 5.4 Anomaly: the resolution ladder is location-contaminated

**The `mde50`/`mde80`/`mde95` columns are not clean resolution measures and should not be used as ones.** Diagnosis, from `screen_code/metrics.py`:

- line 283 sets the critical value on the **centred** bootstrap distribution: `crit = quantile(v0 − point, 1 − α/2)` — correct and location-free.
- line 297 plants on the **uncentred** distribution: `planted_wl = base_stats + delta`, where `base_stats` still carries the cell's own point estimate.
- so detection ≈ `P(centred + δ + point > crit)`, and line 323 gives `mde50 = crit − median(v0) ≈ crit − point`.

Measured over the 12,192 ladder rows with a finite `mde50`:

- `corr(detect_wl_0.02, log_R) = +0.566` while `corr(detect_wl_0.02, block_mde) = −0.038`. A resolution measure should track the cell's **uncertainty**, not its **location**; this one does the opposite.
- `corr(mde50, log_R) = −0.624`, `corr(mde50, block_mde) = +0.534`.
- **575 rows carry a negative `mde50`** (min −3.70), meaningless as "smallest detectable effect". They are cells already above their own noise threshold: median log R 0.307 against 0.020 for the rest, at essentially the same median `block_mde` (0.277 vs 0.290).

The correct location-free form would plant on `(base_stats − point) + delta`, yielding `mde50 ≈ crit > 0` always.

**Severity and containment.** A defect in an **informative** artifact, not an integrity failure. It does **not** touch the primary estimand, any CI, any band, or the phase-(b) trigger — all come from `envelope_ci_logR` and `block_mde = stat − ci_low`, which are location-free and which I verified independently (§1.1). It **does** undermine the design's stated adequacy-reading mechanism (§8/§9: "adequacy is read off the MDE and resolution curve") and would make §13's mandatory aggregate-resolution disclosure misleading if quoted as `median mde50`. **Every resolution statement here is therefore given on `block_mde` and `ci_width`.** The detection curves are internally monotone across rungs (0 of 12,192 rows decrease) and the two plant operators agree closely (mean detection by rung 0.1475/0.1640/0.1996/0.2471/0.2962/0.3928 via `W/L` vs 0.1470/0.1633/0.1985/0.2457/0.2946/0.3915 via `p`), so the *curve* is well-formed — only its zero point is displaced.

### 5.5 Collapse fractions, as required (B-2, never a binary)

| control | cell / arm | live log R | null mean (sd) | percentile | collapse fraction |
|---|---|---|---|---|---|
| mirror null (primary) | all | — | analytic 0 | — | **N/A — `POINT_NULL`**, recorded not omitted |
| side derangement | `L0` H1 δ=0.5 | +0.0550 | +0.0035 (0.0249) | 0.9755 | 0.058 |
| entry-timing derangement | same | +0.0550 | +0.0010 (0.0249) | 0.985 | 0.022 |
| magnitude-matched | `L1_SHAT_DECILE_GE7` | +0.0784 | +0.0473 (0.0351) | 0.816 | 0.597 |
| side derangement | `L4_TARGET_A1_MOD` | +0.062 | +0.054 (0.0197) | 0.665 | 0.871 |
| side derangement | `L4_TRAIL_B1_MOD` | +0.0046 | +0.0292 (0.0208) | 0.1145 | **6.27** |
| side derangement | `L4_TRAIL_B2_MOD` | +0.0096 | −0.0059 (0.0204) | 0.7795 | **−0.57** |

The last two rows are why the design demotes collapse fraction to disclosure on this object (M-5): a ratio around a near-zero mean is unstable by construction, and 6.27 / −0.57 are arithmetic, not evidence. Note **`L4_TRAIL_B2_MOD` — the one cell that clears on the primary read (F1) — sits at side-derangement percentile 0.78 with a negative collapse fraction**, i.e. its own attribution control does not distinguish it from randomly-refereed sides. All controls are H1-only (§1.3), so this is the H1 arm of the device, not the M15 cell itself.

---

## 6. Explicitly unpowered / unresolvable, and why

Per B-5: a covering CI reads *"we could not see an effect this small here"*, never *"there is no effect"*.

1. **Effects below ~0.03 log units are invisible on the primary read.** Median pooled M15 Δ `block_mde` = 0.0393; 58 of 87 cells cannot resolve 0.03 and 77 cannot resolve 0.02. A true capture effect there is **unresolved, not refuted**.
2. **The whole per-symbol tier is heterogeneity disclosure only.** Median `block_mde` 0.259; 4,438 of 4,444 cells cannot resolve 0.03. The one asymmetric result (107 up vs 37 down on M15 Δ, §4.4) lives entirely in this tier and cannot be promoted out of it.
3. **MOD-vs-UNMOD is unresolvable at this n.** No pairwise difference is emitted with its own CI, and the median observed gap (0.006) is 0.16× the median arm MDE. The design's central question — does the volatility *forecast* add over a constant-width comparator — is **answered "cannot see"**, not "no".
4. **The L2 interaction is not measurable on 30.9 % of its rows** (96 of 311 structurally zero, A6). Prediction 4 is untested there.
5. **The 4 L2 level/joint/interaction variants run on 17 of 25 symbols**, per the named PARITY-EXEMPT list (1000PEPEUSDT, 1000RATSUSDT, BIGTIMEUSDT, ORDIUSDT, PYTHUSDT, SEIUSDT, TIAUSDT, WLDUSDT — parent emitted a null metric below 40 usable origins). Parity held on the other 17 (34 checks, 0 failures, `abs(Δ) ≤ 1e-9`). Disclosed in the design, not a defect, but the level axis is measured on a 68 % universe.
6. **33 cells carry no `log R` at all** (28 undefined, 5 spanning under 2 calendar days) and **840 sizing-variant rows may not carry a `log R` claim**. None imputed; their absence is **not** treated as a zero.
7. **No M15 causal-misalignment tripwire and no M15 control exist** (§1.3). I verified M15 fill, hold and block behaviour myself and found them exact; the attribution question on M15 is unaddressed by this emission.
8. **Predeclared-vs-realised calibration cannot be evaluated** — all 5,148 priors are explicit `UNKNOWN` (§4.5). Intended; it means the *next* design reads a measured `c` off this run.
9. **Phase (b) resolution is not forecast here.** This run supplies the realised per-cell `n` the phase-(b) amendment needs; the six-rung expected-`mde50` distribution for the interaction estimand is that amendment's obligation.

---

## 7. The phase-(b) trigger, evaluated on its own stated terms

Design §4.3, pre-declared before phase (a) ran (registered AMENDMENT-C6 / reflection §5.9.1):

> Phase (b) MAY run only if, in the phase-(a) emission on the primary read, AT LEAST ONE of:
> (i) some layer/device cell has Δ log R vs L0 with `ci_low > 0`, or
> (ii) some layer/device cell has absolute log R with `ci_low > 0` (**H1 only**).

**Route (i) — MET.** `L4_TRAIL_B2_MOD`, M15, TRAIN, POOLED, δ=0.5: Δ log R +0.02578, **`ci_low` = +0.000125 > 0**. Also met at the per-symbol disclosure tier (107 M15 rows).

**Route (ii) — MET.** Four H1 pooled TRAIN absolute cells clear: `L4_TARGET_A1_UNMOD` δ=0.5 (`ci_low` +0.0115) and δ=1.0 (+0.0632), `L4_TARGET_A1_MOD` δ=1.0 (+0.0373), `L4_TRAIL_B1_UNMOD` δ=1.0 (+0.0198). The H1-only restriction is respected — no M15 absolute cell is used.

**Verdict on the trigger: MET, on both routes, on its stated terms.** No threshold invented; none softened. The condition introduces no magnitude and none has been supplied.

**Three facts to weigh alongside it, none of which alters the above.**

1. The trigger is a **stopping rule on a phase, not a value gate on a cell** (§4.3), and it is **necessary, not sufficient**: phase (b) additionally requires its own operator execution authority and its own design amendment. The operator may decline a fired trigger.
2. Route (i) fires on **1 of 87 pooled cells where 2.2 are expected under a true global null**, with a margin of **1.25e-4 log units** — 0.5 % of that cell's own MDE. Route (ii)'s four cells sit against 2.3 expected, and **three of the four are the unmodulated comparator** (A2).
3. What the operator may **not** do is decide after seeing (a) what "promising" meant — the optional-stopping hole C6 exists to close. The **scope** of phase (b) is fixed and independent of (a)'s outcome: the complete {L1, L2, L3} × {target, trail, hold, sizing} cross, individually-flat layers retained on equal footing, estimand = the interaction. Nothing in §5 licenses pruning that grid.

---

## 8. Recommended verdict — NOT FINAL, experiment hypothesis only

> ### Recommendation: **WASH — not supported at the resolution achieved**
>
> No layer of the opportunity model — scale, volatility state, swing gate, or capture parameters — moves the payoff residual resolvably above the driftless mirror on the primary read. This is a wash, **not** a refutation: effects below ~0.03 log units are invisible in this emission.

**Driven by, in order:**

1. **The primary read produces fewer resolvable positives than chance.** 85 of 87 pooled M15 Δ log R cells cover the mirror; **1 clears where 2.2 are expected under a true global null**, by 1.25e-4 log units. On H1, **0 of 87** clear. (§4.1, §4.2)
2. **The device, not the information, carries what little signal exists.** Three of the four positive H1 absolute cells are the **unmodulated** constant-width arm, and the one modulated cell reads *lower* than its own comparator. Across all 54 MOD/UNMOD pairs, 31 favour MOD (0.57) and **not one difference is itself resolvable**; the median M15 gap is 0.16× the median arm MDE. (A2, A3)
3. **The one H1 read that looks positive is tail-driven and regime-split.** `L0` H1 log R +0.055 turns negative on removing 50 of 18,970 episodes (0.26 %), and the two clocks trend in opposite directions across 2021→2023. (A4, A5)

**Weighed against it:** a genuinely monotone L1 dose-response on M15 at all three δ (F2), one modulated trail arm clearing on the primary read (F1), and confirmation that the layers select the mechanism's own quantity — 2× payoff scale at constant sign share (F5). None is resolvable at this `n`, but F2 and F5 together are the pattern a real scale mechanism would leave, and F5 also explains the null: a **scale** selector cannot move a **scale-free ratio** residual, so `log R` may be the wrong instrument for what ŝ actually does.

**This would change if:** (a) the MOD-vs-UNMOD difference were emitted as a paired estimand with its own block CI rather than inferred from two overlapping intervals — the central question is currently answered "cannot see" rather than measured; (b) the L1 dose-response held with `ci_low > 0` at any cut once `n` roughly quadrupled (required `n` is readable off this run's realised `c`); (c) an M15 side-derangement and causal tripwire showed the M15 attribution is clean — as things stand the H1 controls hint at a *direction* effect (percentiles 0.976 / 0.985) that this design assumes away, and their null is ~1.7× too narrow to trust against the block CI.

**Also for the operator, before anything advances:**

- **The `mde50`/`mde80`/`mde95` columns are location-contaminated and should not be quoted as resolution** (575 negative values; correlates −0.62 with the cell's own `log R` and only +0.53 with its uncertainty). One-line fix at `screen_code/metrics.py:297`. `block_mde` and `ci_width` are sound and every read here uses them. **Not an integrity failure; no estimand, CI, band or trigger is affected.** (§5.4)
- **`L4_HOLD_1H_UNMOD` duplicates `L0_BASELINE` exactly** — 32 independent variants, not 33, and 156 structurally-zero delta rows. (A7)
- **96 of 311 L2 interaction rows are structurally zero** because the k12 gate is inert on 30 % of its cells. AMENDMENT-20(c)'s guard does not catch this case; prediction 4 is untested there. (A6)
- **No M15 tripwire and no M15 control were run**, on the clock carrying the primary result. I closed the fill/hold/day-block half independently and it is exact (500/500 episodes reproduce from raw M1); the attribution half remains open. (§1.3)
- **Reported performance is overstated**: spread is not charged at all, and gross mean per episode is at best 0.21× a partial floor that omits it. No tradability claim is made. (§3.2)

**Suggested probes if you want to push on this:**

- Emit `Δ log R(MOD) − Δ log R(UNMOD)` as a **single paired estimand** with its own day-block CI on the same episode population. This is the design's actual question and it is currently unmeasured.
- Test whether the residual is the right instrument for a scale mechanism at all: F5 shows ŝ moves payoff **scale** 2× at constant sign share, and `log R` is scale-free by construction. A scale-sensitive companion estimand (already emitted: `W`, `L` in bps and σ̂ units) would say whether the null is absence or object-mismatch — the L-16 shape.
- Re-run the four controls and TRIPWIRE-1 on **M15**, and re-derive the derangement nulls under the day-block structure so their percentiles are comparable with the CIs that carry the verdict.

**Final verdict is the operator's.** Nothing here changes family status, and no family-level disposition is recommended or implied — that decision belongs to a checkpoint retrospective.
