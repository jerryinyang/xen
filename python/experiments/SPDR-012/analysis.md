# SPDR-012 — data analysis (fresh-context, binding read)

- **Family:** `CF-VOLDIR-001` / **HYP-A** · **Checkpoint:** 017 · **Lane:** SPDR (TRAIN-only)
- **Question (design §1):** on the retained Bybit core, is next-horizon volatility / absolute
  move predictable from causal lagged information, under predeclared metrics?
- **Analyst:** fresh context, did not run the screen. Every number is re-derived from the raw
  emissions by `analysis_code/a01…a11`, never by importing `screen_code/` or `summarise.py`.
- **Status:** binding read. Supersedes `screen.md`.

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: any optional cost overlay understates true cost
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

Every bps figure is the magnitude of an open-to-open move on the stated clock
(`abs_oo = 1e4·|O_{t+1}/O_t − 1|`, §6.1 UNIT-PIN). **No P&L object exists in this screen.**
No direction, no combination, no XENA, no tradability or deployability claim.

**Two operator decisions bind this write-up.**
1. **No PASS/STOP recommendation** (AMENDMENT-T2). §6.4's clauses are unsatisfiable as frozen.
   All three candidate bases are reported side by side in §10; the call is the operator's.
2. **There is no hard leak gate** (AMENDMENT-T1). §1.3 states what does carry the causality claim.

---

## 0. PER-ARM VERDICT — the headline for mid-checkpoint Reflection C

> **This section is the single highest-value output of SPDR-012.** Step A's job was never one
> number; it was to say **which volatility levers survive** so Reflection C can choose the
> combination design from observations, not from a pre-hoped narrative (RAW §3C). Each of the
> eight arms maps to one RAW §5.1 organising axis. The verdict below is what carries into
> SPDR-014's design. Read this before the per-stratum detail in §3.

All figures are **CONFIRM** (the powered band); rank IC is the primary reliability metric
(0 = no ordering skill, ~0.30 = strong for this data). Full numbers: the section named per arm.

| # | Arm | RAW §5.1 axis | Verdict | The one-line reason it matters for SPDR-014 |
|---|---|---|---|---|
| 1 | **V-PERSIST** | persistence / clustering | **WORKS (level), FAILS (single-bar)** | Multi-bar vol level persists; a single bar's shock dies in ~0.4 bars — condition on the *level*, not on the last bar. The textbook **HAR model is the weakest thing here** and collapses at D1. |
| 2 | **V-LEVEL** | level forecasting | **STRONG intraday, WEAK daily** | The load-bearing arm. IC 0.338 (H1) / 0.301 (H4) / 0.196 (D1); all three model forms tie, so a **simple EWMA is enough** — no fitted zoo needed. |
| 3 | **V-REGIME** | Markov regime | **WORKS, modest, H1 only** | High−low state gap +17 bps (H1), states ~93% sticky — a usable binary conditioner, but only the hourly clock clears the design's bar (§8.10 explains why: the 15-bps bar is clock-blind). |
| 4 | **V-REGIME-HMM** | HMM regime | **MIS-NAMED — it's a shock detector, not a regime model** | Separates size *more* sharply, but its state ≈ a threshold on the last bar's return (AUC 0.95–0.98), lasts ~2 bars, and 76/83 cells are UNPOWERED. Do **not** treat it as a slow-regime object; the two regime arms are near-orthogonal (agree ~55%). |
| 5 | **V-MEASURE** | realised vs range | **RANGE MEASURES WIN** | Parkinson / Garman–Klass beat close-to-close by ~+0.11 IC at matched window, on every clock — **use a range-based vol input**, decisive on D1. |
| 6 | **V-CLOCK** | calendar / clock | **NULL — adds nothing** | Session and day-of-week give no lift over a plain vol forecast on any clock (H1/H4 wash, D1 overfits). Drop calendar features from the combination design. |
| 7 | **V-XS** | cross-sectional rank | **WEAKEST axis** | The cross-coin high−low gap clears in only a minority of coins with wide spread. Lowest-priority conditioner. |
| 8 | **V-TAIL** | distributional / tail | **WORKS intraday** | Extreme-move rate ~1.8× higher in the high-vol state (H1); confirms the effect reaches the tail, not just the mean. Unpowered at D1. |

**The three cross-cutting facts that gate everything above (§4, §5, §8.10):**

1. **Scale of the signal: day-to-week, never hour-to-hour.** ~26–75% of every arm's IC is
   *between-calendar-month* level structure; strip it and within-day skill is **zero** (H1 +0.024,
   H4 −0.116). Every arm answers "which *days* are volatile", none answers "which *hour today*".
2. **The daily clock fails on the design's own primary input.** Within a month, 20-day
   close-to-close vol → next-day move runs at **−0.130** (backwards). The whole D1 story depends
   on switching to a short-window range measure (arm 5).
3. **The headline number is span-dependent** (0.15 at 15 dates, 0.31 at 290, same data), so the
   per-arm *ordering* above is the durable output — not any single IC value.

**What this hands Reflection C (RAW §3C / checkpoint-017 §5 Step C):**
- **Keep:** a range-based volatility *level* on **H1/H4** as the conditioner (arms 2, 5, 1-level),
  optionally a binary high/low regime flag (arm 3) and a tail overlay (arm 8).
- **Drop:** hour-resolution vol forecasting, calendar features (arm 6), cross-sectional rank as a
  primary lever (arm 7), and any reliance on close-to-close RV at a daily horizon.
- **Re-label:** V-REGIME-HMM is a shock detector; if a genuine regime object is wanted, refit the
  HMM on `rv20` (§9.5).
- **Open design question for C:** is a span-dependent, level-heavy rank IC the right object to
  gate SPDR-014 on, or should reliability be re-scored *within-period* first (§9.5 item 1)?

---

## 1. Integrity gate

The SPDR lane has no Nautilus emission and no `estimand_validation.json`. The substitute is
`results/integrity_selfcheck.json` (all hard checks PASS) plus `qa-review.md`. I re-derived each
item rather than restating it.

### 1.1 Band fence — re-derived

| Check | My re-derivation | Result |
|---|---|---|
| Max origin timestamp | `2023-12-17T21:00Z` | inside TRAIN |
| Max **target exit** timestamp (open of the bar after the target bar) | `2023-12-17T22:00Z` | < `train_end_utc` |
| Rows with target exit ≥ TEST start (2023-12-18) | **0** of 232 753 | PASS |
| Rows with target exit ≥ holdout start (2025-01-08) | **0** | PASS |
| DESIGN rows whose target exit lands at/after DESIGN end | **0** of 79 932 | PASS (QA F-7 fix landed) |
| Earliest scored origin | `2021-08-28T07:00Z` (MATICUSDT only) | — |

`a01_verify.py`. The F-7 boundary defect QA found is fixed in the final artifact set:
`n_design_origins` for BTCUSDT H4 is 1012, one lower than the 1013 QA saw, and a shifted-index
scan finds zero remaining violations.

**No TEST or holdout data was read at any point in this analysis.**

### 1.2 Emission reproduces from the raw per-origin rows

| Check | Result |
|---|---|
| V-LEVEL ridge OOS IC recomputed from `vol_reliability.parquet` vs `metrics_by_cell.parquet` | max abs diff **3.3e-16** over all 90 cells |
| `n_obs` agreement | 90/90 exact |
| G1 golden trace: `rv20` recomputed by hand from the 21 listed closes | rel error **8.2e-15** |
| Target identity `target_abs_oo[i] == oo_move[i+1]` on contiguous rows | **0 mismatches** in 225 457 rows |
| Universe pin: 903 catalog symbols rescanned, top-25 by 30d USD volume | exact set match to both pin files |

### 1.3 Causality — what actually carries the no-leak claim

**SPDR-012 ships with no hard leak gate.** `TARGET-FUTURE-DESTROY` was demoted to a report layer
(AMENDMENT-T1) for a reason that is correct and worth restating: `E[Spearman(pred, deranged y)] = 0`
for **any** fixed predictor, leaking or not. Destroying the outcome removes the association whether
or not the forecast contained the outcome. **No outcome-side destroy can detect look-ahead.** The
measured numbers confirm the gate carries no information: unrestricted-derangement null median
−0.0002, max |median| 0.005 across 90 cells, against live ICs up to 0.41 — 90/90 would have
"passed" and none could have failed.

What does carry it, in order of strength:

1. **Bit-exact independent re-derivation of the walk-forward path.** The analyst reimplemented the
   expanding-window monthly-refit ridge from the emitted feature columns alone and reproduced the
   emitted prediction series to **max abs difference ~1e-12 bps** on five cells: BTCUSDT H4 (608
   OOS rows), ETHUSDT H1 (2433), SOLUSDT H1 (2442), DOGEUSDT H4 (554), MATICUSDT H1 (7852). A
   deliberately leaky variant — fit window extended to include the rows it predicts — differs by
   up to **13.8 / 20.4 / 20.4 / 17.2 / 52.4 bps**. The comparison discriminates by 12 orders of
   magnitude, and the fit window never contains a row it predicts (`a09_causality_recheck.py`).
   *Implementation detail neither `screen.md` nor `qa-review.md` records:* the monthly re-fit
   boundary is keyed to the **target bar's** calendar month, not the origin's. Keying it to the
   origin month reproduces the series only to ~4 bps. Worth pinning if the code is ported.
2. **Construction asserts** §7.1/7.1b/7.2/7.3/7.3b/7.4, all re-derived above.
3. **Predictor-side circular shift** — the operative non-vacuity device. Live IC outside the
   shuffle central 90% in **73 of 90** cells, against a genuinely wide null (p95 median 0.144–0.215).
4. **Feature shift test.** `parkinson[i]` vs `parkinson[i+1]` correlates at 0.50–0.59, not 1.0 —
   the feature is not a disguised copy of the target bar's own realised measure.

**Downstream readers must treat the L-01 assurance as resting on construction and independent code
re-derivation, not on a destroy test.**

### 1.4 Lane boundary

| Check | Result |
|---|---|
| No local accounting primitives (L-18) | PASS — no P&L, position, fee or equity object exists |
| No tradability / deployability / net claim | PASS — spread `UNAVAILABLE_NOT_CHARGED`, no cost applied |
| Matched control + seed battery (L-19) | PASS — 200 / 2000 / 50-seed batteries, percentile reads |
| Block ≥ H dependence-matched CI | PASS — date blocks 1/3/7 days ≥ every clock's horizon |
| Per-stratum reporting, multiplicity disclosed (L-03) | PASS in artifacts; **one lapse in `screen.md`** — §8.4 |
| Derangements fixed-point-free (L-28) | PASS — measured 0 of 360 000 draws |
| Block × seed CI grid emitted (L-20) | PASS — 4 284 metrics × 15 cells, all present (QA F-6 fixed) |

---

## 2. Question list

| # | Question | Where |
|---|---|---|
| Q1 | Does the emission reproduce from raw rows? Is the fence intact? | §1.1–1.2 |
| Q2 | Without a leak gate, what carries the causality claim? | §1.3 |
| Q3 | Per stratum, how reliably is next-horizon vol predicted — effect size, uncertainty, power? | §3.1, §5 |
| Q4 | Is the DESIGN/CONFIRM difference regime, sample size, or something else? | §4 |
| Q5 | Is the clock ordering a horizon effect or a sample artifact? Minimum useful horizon? | §5 |
| Q6 | Why do D1 range measures beat close-to-close rv20? Overnight/coverage? | §6 |
| Q7 | What are the two regime arms actually partitioning? | §3.5 |
| Q8 | What does negative V-CLOCK incremental R² mean? | §3.6 |
| Q9 | Are the `rv_next` rows correctly quarantined everywhere? | §8.1 |
| Q10 | Does any band label rest on one lucky block length or seed? | §3.2 |
| Q11 | Dose-response, distribution shape, heterogeneity | §3.3, §3.4 |
| Q12 | What is the IC actually made of? | §4.5 |
| Q13 | Where are the contrary strata, and why? | §5.4, §9.1 |
| Q14 | What does `screen.md` over- or under-state? | §8 |
| Q15 | The three candidate bases | §10 |

---

## 3. The primary object, per stratum

### 3.1 V-LEVEL ridge OOS rank IC on the next |open→open| move

Full per-cell table: `analysis_code/out_vlevel_strata.csv` (90 cells, nothing hidden). Interval =
min/max envelope over 3 block lengths × 5 seeds (IN-4) — a conservative envelope of 95% CIs,
**not itself a 95% interval**.

| Band | Clock | cells | median IC | range | envelope low > 0 | median dates | median MDE | effect/MDE |
|---|---|---|---|---|---|---|---|---|
| CONFIRM | H1 | 15 | **0.338** | 0.317 … 0.385 | **15/15** | 292 | 0.088 | 3.85 |
| CONFIRM | H4 | 15 | **0.301** | 0.257 … 0.367 | **15/15** | 292 | 0.088 | 3.42 |
| CONFIRM | D1 | 15 | 0.196 | −0.216 … 0.374 | 13/15 | 286 | 0.089 | 2.20 |
| DESIGN | H1 | 15 | **0.283** | 0.160 … 0.414 | **15/15** | 102 | 0.149 | 1.90 |
| DESIGN | H4 | 15 | 0.202 | −0.006 … 0.355 | 12/15 | 102 | 0.149 | 1.33 |
| DESIGN | D1 | 15 | 0.093 | −0.145 … 0.257 | 2/15 | 98 | 0.152 | **0.61** |

Per symbol (point estimates):

| symbol | C-H1 | C-H4 | C-D1 | D-H1 | D-H4 | D-D1 |
|---|---|---|---|---|---|---|
| BTCUSDT | 0.365 | 0.304 | 0.238 | 0.414 | 0.306 | 0.249 |
| ETHUSDT | 0.326 | 0.292 | 0.273 | 0.310 | 0.198 | 0.160 |
| SOLUSDT | 0.343 | 0.309 | 0.130 | 0.283 | 0.261 | 0.077 |
| BNBUSDT | 0.326 | 0.314 | 0.172 | 0.330 | 0.259 | 0.172 |
| XRPUSDT | 0.351 | 0.257 | 0.134 | 0.296 | 0.172 | 0.118 |
| ADAUSDT | 0.377 | 0.341 | 0.223 | 0.268 | 0.218 | 0.199 |
| DOGEUSDT | 0.385 | 0.367 | 0.374 | 0.244 | 0.202 | 0.105 |
| AVAXUSDT | 0.371 | 0.317 | 0.190 | 0.254 | 0.173 | 0.090 |
| LINKUSDT | 0.332 | 0.286 | 0.227 | 0.253 | 0.161 | 0.027 |
| MATICUSDT | 0.338 | 0.298 | 0.196 | 0.403 | 0.355 | 0.257 |
| OPUSDT | 0.323 | 0.288 | 0.135 | 0.325 | 0.248 | 0.093 |
| GALAUSDT | 0.326 | 0.289 | 0.286 | 0.295 | 0.251 | 0.091 |
| DYDXUSDT | 0.327 | 0.301 | 0.315 | 0.179 | **−0.006** | **−0.145** |
| INJUSDT | 0.356 | 0.357 | **−0.216** | 0.160 | **−0.004** | 0.044 |
| 1000LUNCUSDT | 0.317 | 0.277 | 0.171 | 0.201 | 0.097 | 0.034 |

Four cells are negative. Only one clears its interval: **INJUSDT D1 CONFIRM**, IC −0.216,
envelope [−0.339, −0.090]. See §9.1 — the reason is instructive.

### 3.2 CI-grid fragility (L-20)

`results/ci_grid.json` carries the full 3 block × 5 seed grid for **4 284** bootstrapped metrics;
all are complete 15-cell grids (`a02_strata_bases_cigrid.py`).

- **Primary V-LEVEL: 72 of 90 cells have envelope low > 0, and all 72 have every one of the 15
  grid cells with `ci_low > 0`.** Because the envelope takes the *minimum* low over the grid, the
  reported "CI-low > 0" count is by construction the "all blocks and all seeds agree" count.
  **No band label rests on a single lucky block length or seed.**
- Two primary cells are block-fragile and correctly *not* counted: ADAUSDT D1 DESIGN (IC 0.199;
  low +0.005 at block 1 but −0.029 / −0.038 at blocks 3 / 7) and 1000LUNCUSDT D1 CONFIRM
  (IC 0.171; +0.026 / +0.008 / −0.020).
- Across all 4 284 metrics, 187 have a `sign(ci_low)` not constant across the grid, concentrated
  in `V-MEASURE dmae_vs_uncond` (22), `V-XS xs_ic_rank_vs_target` (16), `V-REGIME gap` (14),
  `V-TAIL exceed_diff_p95` (14). All are excluded from clearing counts by the envelope rule.
  Worst instability: BIGTIMEUSDT H1 CONFIRM V-REGIME gap, block-1 low −25.6, block-3 −42.6,
  block-7 **+59.0** — a 151-origin cell where the bootstrap is not doing anything meaningful.

**Caveat on the SE.** `se` is the max SD over the grid (QA F-11 fix) and drives the gap-band MDE;
`ci_low/ci_high` are the min/max. Both are conservative, but the interval is an envelope and
should never be described as a 95% CI.

### 3.3 Dose-response and distribution shape

Mean next |move| by decile of the V-LEVEL forecast, as a multiple of the cell's own mean (median
over 15 symbols; `a08_dose_hetero.py`; `plots/dose_response.png`):

| Band / clock | d1 | d2 | d3 | d4 | d5 | d6 | d7 | d8 | d9 | d10 | d10/d1 | monotone steps of 9 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CONFIRM H1 | 0.52 | 0.63 | 0.70 | 0.80 | 0.88 | 0.93 | 1.06 | 1.22 | 1.39 | **1.91** | 3.71 | 9 |
| CONFIRM H4 | 0.57 | 0.62 | 0.70 | 0.80 | 0.92 | 1.00 | 1.02 | 1.18 | 1.35 | **1.80** | 3.11 | 8 |
| CONFIRM D1 | 0.71 | 0.80 | 0.82 | 0.86 | 0.94 | 0.88 | 0.94 | 1.16 | 1.07 | 1.33 | 2.06 | 6 |
| DESIGN H1 | 0.56 | 0.72 | 0.77 | 0.85 | 0.89 | 0.99 | 1.08 | 1.12 | 1.33 | 1.63 | 2.95 | 8 |
| DESIGN H4 | 0.62 | 0.71 | 0.88 | 0.84 | 1.06 | 0.95 | 1.05 | 1.11 | 1.13 | 1.38 | 2.22 | 6 |
| DESIGN D1 | 0.70 | 0.87 | 0.87 | 0.81 | 1.06 | 1.09 | 1.12 | 0.97 | 1.11 | 1.07 | 1.49 | 4 |

Tail rate — probability the next move exceeds the cell's own P90 — is **0.017 in decile 1 vs
0.304 in decile 10** (CONFIRM H1), an 18× ratio.

**Shape.** Top forecast quintile vs bottom (CONFIRM H1): mean ratio 2.86, median ratio 2.93,
P90 ratio 2.92; coefficient of variation 1.03 (high) vs 1.25 (low). The three ratios agree to two
decimals — **the forecast rescales the entire magnitude distribution**, it does not shift only the
location or only the tail. This is the cleanest thing in the screen for a downstream
vol-conditioning design: the object being forecast is a scale parameter.

### 3.4 Heterogeneity across symbols

Inverse-variance weighted Q / I² on the primary IC:

| Band | Clock | n | mean | sd | range | median SE | Q (df 14) | I² |
|---|---|---|---|---|---|---|---|---|
| CONFIRM | H1 | 15 | 0.344 | 0.022 | 0.317 … 0.385 | 0.024 | 10.6 | **0.00** |
| CONFIRM | H4 | 15 | 0.306 | 0.030 | 0.257 … 0.367 | 0.035 | 9.9 | **0.00** |
| CONFIRM | D1 | 15 | 0.190 | 0.133 | −0.216 … 0.374 | 0.061 | 67.0 | 0.79 |
| DESIGN | H1 | 15 | 0.281 | 0.072 | 0.160 … 0.414 | 0.033 | 61.0 | 0.77 |
| DESIGN | H4 | 15 | 0.193 | 0.102 | −0.006 … 0.355 | 0.054 | 49.0 | 0.71 |
| DESIGN | D1 | 15 | 0.105 | 0.100 | −0.145 … 0.257 | 0.109 | 0.0* | 0.00 |

*DESIGN D1's I² = 0 only because its SEs are as large as the spread — an unpowered read, not
homogeneity.

**On CONFIRM H1 and H4 the effect is statistically indistinguishable across all 15 symbols**
(I² = 0, cross-symbol sd 0.022 against a median SE of 0.024) — the strongest single argument that
this is a property of the asset class rather than of any one name. D1 is the opposite (I² = 0.79,
driven by INJ −0.216 and DOGE +0.374).

### 3.5 Regime arms — what are the two arms actually partitioning?

`a05_regimes.py`; `plots/regime_partition.png`.

| Property (median over CONFIRM cells) | V-REGIME (rolling-median split of rv20) | V-REGIME-HMM (2-state Gaussian HMM on `r`) |
|---|---|---|
| Fraction of bars called HIGH — H1 / H4 / D1 | 0.483 / 0.469 / 0.485 | **0.080 / 0.127 / 0.053** |
| Mean HIGH run length (bars) — H1 / H4 / D1 | 18.6 / 16.3 / 13.2 | **2.1 / 1.9 / 1.6** |
| Empirical decoded `P(HIGH|HIGH)` — H1 / H4 / D1 | 0.946 / 0.939 / 0.931 | **0.528 / 0.460 / 0.388** |
| Mean `rv20` percentile in HIGH (H1) | 0.660 | 0.847 |
| Mean `|r_t|` percentile in HIGH (H1) | 0.560 | **0.908** |
| AUC of `rv20` alone for the state (H1) | **0.807** | 0.875 |
| AUC of `|r_t|` alone for the state (H1) | 0.616 | **0.965** |
| Agreement between the arms | 0.568 (H1) / 0.598 (H4) / 0.575 (D1) | — |

**Answer.** They are not two versions of the same object.

- **V-REGIME is a slow level classifier.** By construction it splits the sample in half at the
  rolling median of `rv20`; it stays in state ~13–19 bars; `rv20` alone reproduces it at AUC 0.81
  and the current bar's return barely at all (0.62). It answers "is this a high-vol period?"
- **V-REGIME-HMM is a single-bar shock detector.** It flags 5–13% of bars, stays flagged ~2 bars,
  and the current bar's absolute return alone reproduces it at **AUC 0.95–0.98**. Its state is
  essentially a threshold on `|r_t|`. It answers "did the last bar just move a lot?"
- Their 51–62% agreement is barely above independence (with p_hmm ≈ 0.08 and p_markov ≈ 0.48,
  chance agreement ≈ 0.52). **They are close to orthogonal partitions.**

**Why the HMM separates magnitude more sharply.** It selects a thin extreme tail. The 2×2
cross-tab settles attribution (CONFIRM H1, mean next |move| in bps, median over cells):

| | HMM LOW | HMM HIGH |
|---|---|---|
| **Markov LOW** | 45.5 (n≈3413) | **95.0** (n≈87) |
| **Markov HIGH** | 51.8 (n≈2857) | 94.9 (n≈474) |

Conditional on the HMM flag, the median-split level adds **nothing** (95.0 vs 94.9). Within
HMM-LOW it adds **+6.3 bps on 45.5** (+14%). **The shock flag carries essentially all of the joint
information; the slow level classifier adds ~14% on top, and only when no shock just occurred.**

Relative separation (gap ÷ the cell's own mean |move|) is the scale-free comparison:

| Band / clock | V-REGIME relative gap | V-REGIME-HMM relative gap |
|---|---|---|
| CONFIRM H1 | 0.272 | **0.897** |
| CONFIRM H4 | 0.296 | 0.666 |
| CONFIRM D1 | 0.216 | 0.324 |
| DESIGN H1 | 0.236 | 0.648 |
| DESIGN H4 | 0.149 | 0.322 |
| DESIGN D1 | 0.134 | 0.236 |

**Power caveat `screen.md` does not carry.** Under §6.3, **76 of 83** V-REGIME-HMM gap cells are
UNPOWERED and only 7 SUPPORTED; the eye-catching D1 medians (+107.7 bps CONFIRM) rest on a HIGH
state occupying ~5% of ~285 daily bars — **~10–15 observations per cell** (measured `n_HH`
median = 10).

### 3.6 V-CLOCK — negative incremental R², stated without over-reading

| Band / clock | incr R² session | DOW | both | cells positive (of 15, session+dow) |
|---|---|---|---|---|
| CONFIRM H1 | −0.0002 | −0.0003 | **−0.0001** | 7 |
| CONFIRM H4 | −0.0001 | −0.0005 | −0.0035 | 5 |
| CONFIRM D1 | 0.0000 (degenerate) | −0.0261 | −0.0261 | 3 |
| DESIGN H1 | −0.0015 | −0.0010 | −0.0020 | 4 |
| DESIGN H4 | −0.0027 | −0.0118 | −0.0092 | 3 |
| DESIGN D1 | 0.0000 (degenerate) | −0.0539 | −0.0539 | 4 |

Two distinct regimes, which should not be conflated:

- On **H1 and H4 the penalty is ~zero** — median −0.0001 to −0.012 against a base R² of 0.09–0.15.
  About half the cells are positive. The calendar terms are a **wash**: no information added, no
  meaningful cost. This is a null result, not a cost.
- On **D1 the penalty is real** (−0.026 to −0.054 against a base R² of +0.019 / −0.061) because
  seven day-of-week dummies are estimated on ~100 daily observations — **overfitting on a thin
  sample**, not evidence the calendar is actively harmful.
- **Session is structurally degenerate on D1** (every D1 bar opens 00:00 UTC), correctly annotated
  and correctly emitting exactly 0.0000.

Defensible statement: **calendar structure adds nothing to a lagged-realised-volatility forecast
on any clock, and on the daily clock the dummies are too many for the sample.** §4 already forbids
treating this arm as a standalone edge claim.

### 3.7 Other arms, per stratum

**V-PERSIST.** Median lag-1 autocorrelation of `|r|`: 0.240 (C-H1) / 0.254 (D-H1), 0.186 / 0.196
(H4), 0.151 / 0.281 (D1); decaying to 0.100–0.134 by lag 5. AR(1) half-life of `|r|` is
**0.38–0.55 bars**. Lag-1 autocorrelation of `rv20` = 0.973–0.983, which is **mechanical** (a
20-bar rolling window overlaps 19/20 at lag 1).

The HAR spec — the classic literature model — is the **weakest fitted model** in the screen:

| Band / clock | HAR (rv20, 6-bar, 24-bar means) | V-LEVEL 4-feature ridge |
|---|---|---|
| CONFIRM H1 | 0.297 | 0.338 |
| CONFIRM H4 | 0.253 | 0.301 |
| CONFIRM D1 | **0.062** | 0.196 |
| DESIGN H1 | 0.245 | 0.283 |
| DESIGN H4 | 0.145 | 0.202 |
| DESIGN D1 | **−0.022** | 0.093 |

**V-MEASURE.** Median univariate IC on the next |move| (emitted, re-verified):

| Band | Clock | rv20 (20-bar cc) | Parkinson (1-bar range) | Garman–Klass (1-bar) | EWMA(0.94) |
|---|---|---|---|---|---|
| CONFIRM | H1 | 0.299 | **0.322** | 0.320 | 0.309 |
| CONFIRM | H4 | 0.255 | 0.267 | 0.269 | **0.278** |
| CONFIRM | D1 | 0.169 | 0.244 | **0.258** | 0.182 |
| DESIGN | H1 | 0.303 | 0.298 | 0.295 | **0.317** |
| DESIGN | H4 | 0.268 | **0.279** | 0.269 | 0.277 |
| DESIGN | D1 | 0.081 | **0.215** | 0.190 | 0.074 |

See §6 — this comparison is not what it looks like.

**V-TAIL.** HIGH-minus-LOW exceedance of the unconditional threshold:

| Band | Clock | above P90 | envelope low > 0 | above P95 | envelope low > 0 |
|---|---|---|---|---|---|
| CONFIRM | H1 | +0.056 | **20/22** | +0.031 | **20/22** |
| CONFIRM | H4 | +0.054 | 16/21 | +0.035 | 12/21 |
| CONFIRM | D1 | +0.040 | **2/21** | +0.022 | **0/21** |
| DESIGN | H1 | +0.056 | 14/15 | +0.035 | 14/15 |
| DESIGN | H4 | +0.031 | 4/15 | +0.020 | 1/15 |
| DESIGN | D1 | +0.034 | 2/15 | +0.034 | 2/15 |

Absolute rates (CONFIRM H1): P(exceed own P90) = 0.129 in HIGH vs 0.073 in LOW — a **1.76×**
relative increase. Intraday only; the D1 tail read is essentially unpowered (0/21 at P95).

**V-XS.** Per-symbol top-minus-bottom tercile gap, **excluding** the POOLED row:

| Band | Clock | median gap (bps) | range | envelope low > 0 |
|---|---|---|---|---|
| CONFIRM | H1 | +20.7 | −65.3 … +58.2 | 13 of 22 |
| CONFIRM | H4 | +41.4 | +15.1 … +120.2 | 5 of 22 |
| CONFIRM | D1 | +65.1 | −37.3 … +274.5 | 2 of 21 |
| DESIGN | H1 | +30.3 | −140.2 … +57.5 | 7 of 15 |
| DESIGN | H4 | +53.1 | −7.6 … +135.6 | 5 of 15 |
| DESIGN | D1 | +74.5 | −214.5 … +261.8 | **0 of 15** |

Cross-sectional relative vol rank is the **weakest** conditioning axis. The POOLED rows (+62 to
+291 bps, all clearing) are disclosure-only and must not be read as a per-symbol result.

---

## 4. Q4 — is the DESIGN/CONFIRM difference regime, sample size, or something else?

`screen.md` reports CONFIRM above DESIGN on every clock (H1 +0.055, H4 +0.099, D1 +0.103) and
correctly notes the bands differ in both length and period. Tested four ways. **The answer is:
neither regime nor estimation quality — it is almost entirely a property of the statistic itself,
which scales with how long a window you measure it over.**

### 4.1 Not a model-estimation effect

If CONFIRM scored better because its model was fitted on more data, a **fit-free** predictor should
show no gap. It shows the same gap. Paired per-symbol differences (CONFIRM − DESIGN) on exactly the
rows the ridge OOS uses, 4 000-draw bootstrap over 15 symbols (`a03_period_vs_size.py`):

| Clock | ridge (fitted) | rv20 (fit-free) | EWMA | Parkinson | GK |
|---|---|---|---|---|---|
| H1 | +0.060 [−0.002, +0.115] | +0.063 [+0.021, +0.128] | +0.057 [+0.015, +0.115] | +0.052 [+0.015, +0.092] | +0.058 [+0.014, +0.119] |
| H4 | +0.094 [+0.048, +0.165] | +0.079 [+0.018, +0.206] | +0.091 [+0.030, +0.187] | +0.077 [+0.027, +0.108] | +0.077 [+0.024, +0.137] |
| D1 | +0.053 [+0.000, +0.195] | +0.136 [+0.026, +0.174] | +0.162 [+0.065, +0.219] | +0.092 [+0.026, +0.172] | +0.104 [+0.018, +0.244] |

Fit-free gaps are the same size or larger. **Model estimation is not the driver.**

### 4.2 The statistic scales with measurement span

Inside CONFIRM only, fit-free rv20 IC on random contiguous date windows of increasing length
(60 draws × 15 symbols per point; `a04_span_clock_measure.py`; `plots/span_scaling.png`):

| window (unique dates) | H1 | H4 | D1 |
|---|---|---|---|
| 15 | 0.147 | 0.056 | **−0.196** |
| 30 | 0.198 | 0.126 | −0.090 |
| 60 | 0.236 | 0.180 | +0.013 |
| **100** (≈ DESIGN OOS length) | 0.256 | 0.191 | 0.081 |
| 150 | 0.267 | 0.222 | 0.102 |
| 220 | 0.289 | 0.237 | 0.120 |
| **290** (≈ CONFIRM length) | **0.306** | **0.257** | — |

The IC roughly doubles from a 15-date to a 290-date window on every clock, and on D1 crosses from
strongly negative to positive. **The headline number is a function of the window you choose.**
At 100 dates, CONFIRM's own IC is 0.256 (H1) and 0.191 (H4) — *below* DESIGN's actual 0.283 and
0.202.

### 4.3 Span matching, per symbol

Sliding a DESIGN-length window through CONFIRM and locating the DESIGN estimate in that
distribution (`a11_final_bits.py`):

| statistic | clock | cells | DESIGN median IC | span-matched CONFIRM median | median percentile of DESIGN | below p5 | above p95 |
|---|---|---|---|---|---|---|---|
| ridge | H1 | 14 | 0.275 | 0.289 | **18.3** | 5 | 1 |
| ridge | H4 | 14 | 0.200 | 0.247 | 17.9 | 4 | 0 |
| ridge | D1 | 13 | 0.093 | 0.199 | 32.0 | 3 | 0 |
| rv20 | H1 | 14 | 0.223 | 0.243 | 29.0 | 4 | 2 |
| rv20 | H4 | 14 | 0.166 | 0.195 | 18.9 | 5 | 1 |
| rv20 | D1 | 13 | 0.029 | 0.059 | 39.4 | 3 | 1 |

After span matching the DESIGN estimate sits at roughly the **18th–39th percentile** of the CONFIRM
distribution — low-ish but comfortably inside it for most symbols, below the 5th percentile for only
3–5 of 13–14. **A small residual period difference survives span matching; it is a fraction of the
raw gap and is within the window-to-window variation inside CONFIRM itself.**

### 4.4 The monthly profile shows no boundary step

`plots/monthly_ic.png`. H1 within-month IC ranges 0.11–0.32 across 2022-09 → 2023-12 with no visible
level change at 2023-03-01. DESIGN OOS months (2022-11 … 2023-02) read 0.316, 0.182, 0.181, 0.139
(median ≈ 0.18); CONFIRM months read a median ≈ 0.18. **Within-month predictability is identical in
the two bands.**

### 4.5 What the IC is actually made of

Two independent decompositions agree. This is the single most important result in the screen.

**(a) The design's own block-restricted derangement** (deranging targets inside symbol ×
calendar-month leaves the between-month component intact by construction):

| Band / clock | null median IC | live median IC | retention |
|---|---|---|---|
| DESIGN H1 | 0.069 | 0.283 | **0.259** |
| CONFIRM H1 | 0.130 | 0.338 | **0.390** |
| DESIGN H4 | 0.053 | 0.202 | 0.328 |
| CONFIRM H4 | 0.158 | 0.301 | **0.533** |
| CONFIRM D1 | 0.107 | 0.196 | **0.481** |
| DESIGN D1 | 0.058 | 0.093 | **0.750** |
| **overall** | | | **0.415** |

Between-month level structure — "this is a high-vol month" — accounts for **26% to 75%** of the
reported IC, and the share is *largest exactly where the pooled IC looks best* (CONFIRM H4/D1) and
on the longest windows.

**(b) Direct within-group re-ranking** (`a04` part B):

| Band / clock | pooled IC | within-month | within-day | within-hour-of-day |
|---|---|---|---|---|
| CONFIRM H1 | 0.338 | **0.251** | **0.024** | 0.335 |
| DESIGN H1 | 0.283 | 0.214 | 0.026 | 0.282 |
| CONFIRM H4 | 0.301 | 0.177 | −0.116 | — |
| DESIGN H4 | 0.202 | 0.140 | −0.101 | — |
| CONFIRM D1 | 0.196 | 0.128 | — | — |
| DESIGN D1 | 0.093 | 0.062 | — | — |

- **Removing hour-of-day changes nothing** (0.335 vs 0.338). Intraday seasonality contributes
  essentially none of H1's IC — a hypothesis worth killing explicitly.
- **Within a single calendar day, H1 skill is ~zero** (0.024) and H4 is *negative* (−0.116).
- The skill lives at the **day-to-month** scale; ~60–75% survives month removal, and none of it is
  intraday.

**Level-removed dose-response** (`a08` part 5, CONFIRM, ranks inside each month): H1 0.64 → 1.57
across deciles (vs 0.52 → 1.91 raw), H4 0.76 → 1.33, D1 0.84 → 1.16. About 70% of the H1 ladder
survives level removal; the D1 ladder mostly does not.

---

## 5. Q5 — clock ordering: horizon effect or sample artifact?

### 5.1 The ordering is genuine

Sample size differs enormously by clock (CONFIRM medians: H1 6 931 origins, H4 1 733, D1 286) but
the number of independent dates is the same (292/292/286) and a rank IC point estimate is not
biased by n. Matching the **date set** exactly across clocks per symbol with a fit-free predictor
(`a04` part C, CONFIRM, 20 symbols with all three clocks):

| clock | median matched-date fit-free IC | median mean |move| |
|---|---|---|
| H1 | **0.305** | 64.6 bps |
| H4 | 0.255 | 129.4 bps |
| D1 | 0.173 | 333.3 bps |

Paired differences over symbols, 4 000-draw bootstrap:

- H1 − H4 = **+0.041** [+0.023, +0.053], positive in 19/20 symbols
- H4 − D1 = **+0.104** [+0.070, +0.134], positive in 19/20
- H1 − D1 = **+0.148** [+0.109, +0.183], positive in **20/20**

The ordering also holds at **every** span in §4.2 (15 … 220 dates). **The clock ordering is a real
horizon effect.**

### 5.2 The D1 bps gaps are a unit artifact, not a strength

Mean |move| scales as expected: H4/H1 = 2.00 (√4 = 2.00), D1/H4 = 2.58 (√6 = 2.45). Normalising:

| Band / clock | V-REGIME gap (bps) | relative gap | mean |move| (bps) |
|---|---|---|---|
| CONFIRM H1 | +16.8 | **0.277** | 67.7 |
| CONFIRM H4 | +32.9 | 0.258 | 136.3 |
| CONFIRM D1 | +64.6 | **0.216** | 349.0 |
| DESIGN H1 | +20.7 | 0.282 | 70.4 |
| DESIGN H4 | +29.4 | 0.237 | 141.0 |
| DESIGN D1 | +89.2 | 0.244 | 367.9 |

Relative separation is flat at 0.22–0.28 across clocks, and D1 is the **lowest** on CONFIRM. Every
bps gap in this screen must be read against its clock's own mean, or the daily clock will look 4×
stronger than it is.

### 5.3 The minimum useful horizon (RAW §5.1)

| Horizon | pooled IC (CONFIRM) | within-month IC | within-day IC | usable predictability |
|---|---|---|---|---|
| **H1** | 0.338 | **0.251**, positive in 99% of 150 symbol-months | 0.024 | genuine, day-scale, homogeneous across all 15 symbols (I² = 0) |
| **H4** | 0.301 | **0.177**, positive in 93% of 150 symbol-months | −0.116 | genuine, day-scale, homogeneous (I² = 0) |
| **D1** | 0.196 | 0.128 (ridge) — but **−0.130 for `rv20` alone**, positive in only 26% of 132 symbol-months | n/a | **level-driven; the close-to-close input is anti-predictive within month** |

**H1 and H4 clear noise. D1 does not clear noise on the design's own primary input.** The only
within-month D1 signal comes from the range family (Parkinson +0.105, ridge +0.128, ~71–73% of
symbol-months positive). See §6.

### 5.4 Where H1/H4 do not hold

DESIGN H4 has two cells straddling zero (INJUSDT −0.004, DYDXUSDT −0.006), both UNPOWERED under
both label rules (65 and 83 unique dates, MDE 0.15–0.19). These are power statements, **not**
evidence against. On CONFIRM H1 and H4 there is not a single negative cell in 30.

---

## 6. Q6 — the D1 Parkinson / Garman–Klass advantage

`screen.md`: "range-based measures beat close-to-close `rv20` on D1 by a wide margin (+0.09 to
+0.13) and are level with it intraday". The number is right; the framing conflates two different
effects, and neither is an overnight or coverage effect.

### 6.1 Not overnight, not coverage, not D1-specific

- **Not overnight.** These are 24/7 crypto perpetuals; the D1 open-to-open target is contiguous
  with the previous close by construction.
- **Not coverage.** A D1 bar is admitted at ≥1 000 of 1 440 minutes, so a retained bar can be
  missing up to 30% of its minutes — which *truncates* the high/low range and biases **against**
  the range measures. Empirically the advantage is *larger* on low-completeness symbols (Spearman
  between per-symbol range advantage and fraction of complete D1 slots = **−0.694**, n = 31), but
  that tracks liquidity/listing age, not coverage mechanics: the three highest-completeness majors
  (BTC/ETH/SOL, 0.996–0.998) still show +0.068 / +0.067 / +0.069 on CONFIRM.
- **Not D1-specific.** Matched at the same window length, the range advantage exists on every clock
  and is *larger* intraday: median single-bar Parkinson minus single-bar |r| is **+0.125 on H1** and
  **+0.083 on D1**.

### 6.2 What it actually is: window-length staleness

The emitted comparison pits a **20-bar close-to-close average** against a **single-bar range** — two
variables change at once. Building the missing cells (`a04` part D; 20-bar rolling means computed
from the emitted per-bar measures):

| Band / clock | \|r\| 1-bar | Parkinson 1-bar | GK 1-bar | \|r\| 20-bar | **rv20 (cc 20-bar)** | Parkinson 20-bar | GK 20-bar |
|---|---|---|---|---|---|---|---|
| CONFIRM H1 | 0.191 | **0.322** | 0.320 | 0.309 | 0.299 | 0.318 | 0.317 |
| CONFIRM H4 | 0.161 | 0.269 | 0.269 | 0.262 | 0.260 | **0.275** | 0.272 |
| CONFIRM D1 | 0.136 | 0.244 | **0.258** | 0.144 | 0.176 | 0.167 | 0.166 |
| DESIGN H1 | 0.182 | 0.298 | 0.295 | 0.304 | 0.303 | **0.313** | 0.308 |
| DESIGN H4 | 0.169 | **0.279** | 0.269 | 0.265 | 0.268 | 0.276 | 0.274 |
| DESIGN D1 | 0.163 | 0.218 | 0.212 | 0.092 | 0.105 | 0.108 | 0.125 |

1. **Range beats close at the same window, on every clock.** Single-bar: +0.13 (H1), +0.11 (H4),
   +0.11 (D1) — the textbook Parkinson result, reproduced cleanly.
2. **20-bar smoothing recovers the information at H1/H4 but destroys it at D1.** At H1 all 20-bar
   versions converge to 0.30–0.32 (smoothing helps: 0.19 → 0.31 for |r|). At D1 they collapse to
   0.14–0.18 while the single-bar range holds 0.24–0.26.
3. Therefore "+0.09 to +0.13 on D1" is **mostly a window-length comparison, not a measure
   comparison.**

### 6.3 The mechanism, confirmed

At D1, within a calendar month:

| D1 CONFIRM predictor | within-month IC | fraction of 132 symbol-months positive |
|---|---|---|
| `rv20` (20-day close-to-close) | **−0.130** | 0.26 |
| `parkinson` (1-day range) | **+0.105** | 0.71 |
| V-LEVEL ridge (4 features) | +0.128 | 0.73 |

A 20-day average is **stale at a 1-day horizon**: it stays elevated for 20 days *after* a large move
that has already passed, so within a month it points the wrong way. The single-day range is
contemporaneous. At H1 a 20-bar window is only 20 hours, so the same measure is not stale
(within-month rv20 IC +0.208, 99% of months positive).

**This also explains the HAR failure at D1** (§3.7): HAR is built entirely from close-to-close RV
averages at 1, 6 and 24 bars — the exact input that is anti-predictive within month on the daily
clock.

**Implication for any later design:** on a daily decision clock, a lagged-RV level feature must be
range-based and short-window; the design's `rv20` close-to-close primary is the wrong object at
that horizon.

---

## 7. Controls

`results/controls.json`, 90 powered cells, re-read by `a06_controls_arms.py`.

| Control | Form / seeds | Result |
|---|---|---|
| TIME-SHUFFLE-PREDICTORS | circular shift `U{1..n−1}`, seeds 101–300 (200) | live outside shuffle central 90% in **73 of 90**; null p95 median 0.144–0.215 |
| TARGET-LABEL-DERANGEMENT | derangement inside symbol × calendar-month, 0 fixed points, 2000 seeds | live above null p95 / p < 0.05 in **68 of 90**; **null retains a median 41.5% of live IC** |
| TARGET-DERANGEMENT-UNRESTRICTED | full derangement, 2000 seeds | null median −0.0002, max \|median\| 0.005 — carries no information (§1.3) |
| UNCONDITIONAL-MEAN-BASELINE | nested constant forecast | ΔMAE below |
| Bite / MDE plant | +0.25 rank-corr synthetic monotone feature, 50 seeds | achieved 0.250; destroyed by both forms in every cell |
| TARGET-FUTURE-DESTROY | **report layer, no pass field** | `COLLAPSED_AS_EXPECTED` 71, `LIVE_INSIDE_DESTROYED_NULL` 19 (thin DESIGN D1 cells) |

The 17 cells where live IC sits inside the shuffle central 90% are **13 DESIGN D1, 3 DESIGN H4, and
INJUSDT D1 CONFIRM**. Every intraday CONFIRM cell clears.

**Error reduction against the unconditional-mean baseline** (`dmae_vs_uncond`, bps of |move|):

| Band | H1 | H4 | D1 |
|---|---|---|---|
| CONFIRM | +6.8 (**15/15**) | +11.9 (**15/15**) | +14.6 (7/15) |
| DESIGN | +5.3 (13/15) | +9.1 (10/15) | +0.5 (**2/15**) |

Out-of-sample R²: CONFIRM 0.151 / 0.142 / 0.019; DESIGN 0.115 / 0.087 / −0.061. **These R² figures
carry no CI at all** — `ci_low`, `ci_high` and `se` are null on all 90 rows. Point estimates only,
and the per-cell spread is wide (BTCUSDT D1 CONFIRM R² is −0.082 against a +0.019 median).

---

## 8. What `screen.md` gets wrong or leaves out

`screen.md` is accurate on the great majority of its figures — its V-LEVEL IC table, model
comparison, `dmae`, V-MEASURE table, contiguity, contiguous-subset ICs, V-PERSIST autocorrelations
and half-lives, V-TAIL, V-REGIME label counts, control counts and coverage counts were all
re-derived and match. The following do not.

### 8.1 The `rv_next` quarantine is incomplete — MATERIAL

`rv_next_i = rv20_{i+1}` shares 19 of 20 return terms with the `rv20` feature at the origin.
`screen.md` flags this for the IC. But `target_overlaps_feature = true` was applied **only to
`oos_ic` rows**. The same mechanical overlap sat unflagged on:

| Metric | Target | Flagged (as first emitted)? | Median value |
|---|---|---|---|
| `oos_ic` | `rv_next` | yes | 0.958 |
| **`oos_r2_vs_uncond`** | `rv_next` | **no** | **0.967** (V-LEVEL), 0.966 (V-PERSIST) |
| **`dmae_vs_uncond`** | `rv_next` | no | 0.0066 |
| **`V-PERSIST ic_rv20_vs_rv_next`** | — | **no** | **0.962–0.980** across all six band × clock |

An out-of-sample R² of **0.967** is more quotable than an IC of 0.958 and carried no warning note.
**Fixed after this analysis:** `target_overlaps_feature` now covers every metric row whose target is
`rv_next` (`oos_ic`, `oos_mae`, `oos_mae_uncond_baseline`, `dmae_vs_uncond`, `oos_r2_vs_uncond`) and
the `V-PERSIST ic_rv20_vs_rv_next` row, each carrying an explanatory note. Treat all of them as
mechanical, never as forecast skill.

### 8.2 The V-REGIME-HMM persistence comparison is apples-to-oranges — MATERIAL

`screen.md`: "HMM self-transition is much lower (median `P(stay HIGH)` 0.68–0.74) than the
median-split persistence [0.93–0.95]". These are different objects. `hmm_p_stay_high` (0.678–0.742)
is the **fitted transition-matrix parameter**; V-REGIME's `p_high_given_high` (0.931–0.946) is the
**empirical persistence of the decoded state**. Like-for-like, the emitted `V-REGIME-HMM
p_high_given_high` is **0.388 (D1) / 0.460 (H4) / 0.528 (H1)**, and an independent decoded
run-length calculation agrees (mean HIGH run 1.6–2.1 bars). The direction is right; the magnitude is
understated by ~0.2, and the comparison pairs a parameter against a realised statistic.

### 8.3 The V-REGIME-HMM headline omits its power label — MATERIAL

HMM medians (+54.2 H1, +75.0 H4, +107.7 D1 bps on CONFIRM) are reported with no mention that **76 of
83 HMM gap cells are UNPOWERED** under §6.3 and only 7 are SUPPORTED, or that the D1 HIGH state
holds a median of ~10 observations per cell.

### 8.4 V-XS medians are contaminated by the POOLED row — L-03 lapse

`screen.md`'s V-XS medians (+21.8 / +46.7 / +86.0 CONFIRM; +30.5 / +57.4 / +93.6 DESIGN) are
computed **including** the POOLED row. Per-symbol medians are +20.7 / +41.4 / +65.1 and +30.3 /
+53.1 / +74.5 — the distortion is largest on D1 (+86.0 vs +65.1, 32% overstatement). The clearing
counts are also wrong: "14/22 (CONFIRM H1), 6/18 (H4), 3/15 (D1)" — the CONFIRM H4 and D1
denominators are 22 and 21 symbol cells (plus one POOLED), not 18 and 15, and the numerators include
the POOLED row (per-symbol: 13, 5, 2).

### 8.5 The V-CLOCK read is over-stated

"Negative at every median, i.e. the calendar terms cost out-of-sample accuracy" is true on D1
(−0.026 to −0.054, seven dummies on ~100 observations = overfitting) but **not material on H1/H4**,
where the median incremental R² is −0.0001 to −0.012 against a base R² of 0.09–0.15 and about half
the cells are positive. On the intraday clocks this is a wash, not a cost.

### 8.6 The regime and cross-section bps tables invite the wrong clock comparison

Reporting +16.8 / +32.9 / +64.6 bps across H1/H4/D1 with no normaliser reads as "D1 is the strongest
regime axis". Relative to each clock's own mean |move| the separation is flat (0.28 / 0.26 / 0.22)
and **D1 is the weakest**. Same applies to V-XS and V-TAIL.

### 8.7 The out-of-sample R² figures carry no uncertainty

`oos_r2_vs_uncond` has `ci_low = ci_high = se = null` on all 90 rows. Quote as point estimates only.

### 8.8 The HAR citation understates the HAR failure

"HAR reaches median OOS IC 0.226 on BTC H4 DESIGN" is a single cell described as a median. Arm-level
medians are 0.297/0.253/**0.062** (CONFIRM H1/H4/D1) and 0.245/0.145/**−0.022** (DESIGN) —
materially below V-LEVEL everywhere and collapsing at D1. Given HAR is the canonical literature
spec named in RAW §5.1, its D1 failure is a result, not a footnote (§6.3 explains it).

### 8.9 Coverage claims verified

`screen.md` §2 is correct: 25 pinned symbols, 15 producing a fitted DESIGN forecast, 10 with zero
DESIGN origins (`1000BONK, 1000PEPE, 1000RATS, BIGTIME, BLUR, ORDI, PYTH, SEI, TIA, WLD`), 3 with no
origin in either band (`TIA, PYTH, 1000RATS`, now emitted as explicit UNPOWERED placeholder rows —
QA F-9 fixed, all 25 appear). 1 022 distinct cells and 15 143 metric rows verify exactly. Median
unique dates DESIGN 98–102 / CONFIRM 286–292 verify.

### 8.10 Missed by both `screen.md` and `qa-review.md`: the §6.3 gap band is clock-dependent

The regime band declares a cell UNPOWERED when `MDE > 15 bps`. Measured median gap MDE:

| Clock | CONFIRM | DESIGN |
|---|---|---|
| H1 | **10.3 bps** | 16.4 bps |
| H4 | 35.8 bps | 55.9 bps |
| D1 | **150.8 bps** | 186.0 bps |

A fixed 15-bps ceiling applied to clocks whose mean |move| ranges 65 → 333 bps makes **H4 and D1
structurally UNPOWERED for the regime gap regardless of the effect**, and makes H1 the only clock
that can ever be SUPPORTED. That is why every V-REGIME SUPPORTED cell (8 of 8) is H1. This is the
same class of defect as QA's F-4 applied to a different clause, and it was not raised. Regime-gap
labels should be read as "H1 vs not-H1", not as evidence about the daily clock.

---

## 9. Anomalies and open questions

### 9.1 INJUSDT D1 CONFIRM (−0.216) — the negative is a level-trend artifact

| month | n | IC | mean |move| (bps) | mean forecast (bps) |
|---|---|---|---|---|---|
| 2023-03 | 31 | −0.043 | 654 | 849 |
| 2023-04 | 30 | −0.355 | 557 | 908 |
| 2023-05 | 30 | −0.137 | 436 | 937 |
| 2023-06 | 30 | −0.045 | 439 | 1008 |
| 2023-07 | 31 | +0.070 | 245 | 1062 |
| 2023-08 | 30 | +0.227 | 232 | 1195 |
| 2023-09 | 30 | +0.324 | 176 | 1204 |
| 2023-10 | 30 | +0.015 | 363 | 1206 |
| 2023-11 | 30 | +0.063 | 459 | 1082 |
| 2023-12 | 14 | +0.398 | 572 | 1121 |

Six of ten months are positive, median ≈ +0.04, yet the pooled IC is −0.216. Cause:
`Spearman(forecast, time) = +0.576` while `Spearman(|move|, time) = −0.156`. The frozen
DESIGN-fitted model's **level** drifts upward through CONFIRM while INJ's realised volatility
drifts down, and the pooled rank correlation is dominated by that opposed trend. **The one
CONTRADICTED cell is produced by exactly the same span/level mechanism that inflates the positive
ones** — a coherence check on the diagnosis, and a warning that the pooled statistic is not stable.

### 9.2 CONFIRM is the only band for 7 symbols — not a replication

`ORDIUSDT, 1000BONKUSDT, BLURUSDT, 1000PEPEUSDT, SEIUSDT, WLDUSDT, BIGTIMEUSDT` have zero DESIGN
origins but 151–4 793 CONFIRM origins, and emit the non-fitted arms on CONFIRM only. **For those
symbols CONFIRM is the estimation band, not a verification band.** BIGTIMEUSDT is extreme: 151 H1
origins over 7 days, and produces the block-fragile V-REGIME cell in §3.2.

### 9.3 Target contiguity

Median 0.963–0.983 per cell, minimum 0.598 (1000LUNCUSDT D1). The emitted contiguous-subset IC
tracks the headline (CONFIRM 0.343 vs 0.338 H1, 0.304 vs 0.301 H4, 0.211 vs 0.196 D1; DESIGN 0.281
vs 0.283, 0.202 vs 0.202, 0.105 vs 0.093). **The non-adjacent horizons are not carrying the result.**

### 9.4 Bar completeness

D1 bars are admitted at ≥1 000 of 1 440 minutes. Median fraction of complete slots is 0.956 (D1) /
0.980 (H1, H4); minimum 0.571–0.581 (1000BONKUSDT, 1000LUNCUSDT). It biases against the range
measures (§6.1), so it does not threaten the §6 conclusion, but a future design should tighten the
D1 coverage floor.

### 9.5 Open questions for the operator

1. **Should the reliability object be re-specified as a span-invariant statistic?** Every IC here is
   a pooled rank correlation whose value roughly doubles between a 15-date and a 290-date window. A
   within-period (month-demeaned) IC, or an R² on log-volatility, would be comparable across bands
   and clocks. This is the single change that would make the numbers in this lane mean the same
   thing twice. *Needs a new emission; proposal only.*
2. **The D1 primary input is the wrong object.** If a daily decision clock survives into SPDR-014,
   the level feature must be range-based and short-window. Re-running the D1 arm with
   `parkinson_1bar` as primary would answer it cheaply. *Needs a new run; proposal only.*
3. **V-REGIME-HMM is mis-named.** It is a shock detector, not a regime model. If a two-state
   *regime* object is wanted, the HMM should be fitted to `rv20` (design §4 permits it; IN-6 chose
   `r`). The two arms answer different questions and both are informative, but they should not be
   presented as competing implementations.
4. **`screen_code/` and the results JSONs remain untracked** (QA F-17). Commit before the gate.

---

## 10. Design §6.4 on all three candidate bases — **no recommendation**

Per AMENDMENT-T2 the §6.4 recommendation is **not computed**. The clauses cannot be satisfied as
frozen: the DESIGN band mostly predates the catalog's trailing 4-year history cap (earliest 1-minute
bar 2022-07-15 for every symbol but MATICUSDT), leaving ~100 unique dates per cell against the ~225
that §6.3's own `MDE = 1.5/√n > 0.10` rule requires; and the first literal calendar third is empty
for every symbol but MATICUSDT, so 42 of 45 cells have exactly one non-empty third.
**The PASS/STOP call is explicitly declined.**

| | **Basis A** | **Basis B** | **Basis C** |
|---|---|---|---|
| **Definition** | CONFIRM window + literal §6.3 labels | DESIGN window + literal §6.3 labels — **the frozen basis** | DESIGN window + disclosure labels + per-sample thirds |
| **Clause 1** — V-LEVEL SUPPORTED on ≥1 clock for ≥10 of 25 symbols | **met** — 15/25 symbols; 43/45 cells powered, 42 SUPPORTED, 44/45 IC-positive | **not met** — **1/25** (MATICUSDT); 3/45 powered, 3 SUPPORTED; 42/45 IC-positive | **met** — 15/25 symbols; 32/45 powered, 29 SUPPORTED; 42/45 IC-positive |
| **Clause 2** — live IC outside the null central 90% | met (common): **73/90** outside the predictor-shuffle central 90%; **68/90** block-derangement p < 0.05 | same | same |
| **Clause 3** — IC sign stable in ≥2/3 DESIGN thirds | **not defined** — thirds are a DESIGN-band object | **not evaluable** — 42/45 cells have one non-empty calendar third; only 3 reach ≥2 positive | **met** — 38 of 43 cells have ≥2 of 3 positive sample thirds |
| **What it would imply** | Vol magnitude is reliably forecastable on H1/H4 across all 15 fitted symbols, homogeneously (I² = 0), with a monotone 3.7× dose ladder | The frozen design cannot answer its own question on its own band; the read is UNPOWERED, which is a power statement and **not** a negative | The same conclusion as A, reached on the estimation band, using two label variants the design never froze |
| **Principal caveat** | §0 designates CONFIRM a *verification* read. For 7 of 22 symbols CONFIRM is their **only** band, so it is their estimation band (§9.2) | Unsatisfiable for data-availability reasons alone, irrespective of effect size. Zero information about the hypothesis | Both `band_label_detected` and `thirds_sample` are disclosure companions invented after the fact |
| **Caveat common to all three** | The IC all three bases label is **span-dependent** (§4.2) and **26–75% between-month level structure** (§4.5). Whatever basis is chosen, the labelled quantity is not pure within-period forecasting skill | | |

**One thing the bases do not encode.** A and C differ only in window; they agree on substance
because, at matched span, DESIGN and CONFIRM produce the same IC (§4.2–4.4). B fails on data
availability, not on evidence. So the three bases are not three readings of the evidence — they are
one reading and one non-reading. The genuine decision is not "which band" but "**is a
span-dependent, 26–75%-level-structure rank IC the right reliability object to gate SPDR-014 on**"
(§9.5 item 1).

---

## 11. Evidence FOR the hypothesis

1. **On the intraday clocks the effect is large, universal and homogeneous.** CONFIRM H1 median IC
   **0.338** (0.317–0.385), H4 **0.301** (0.257–0.367). **All 30 of 30** intraday CONFIRM cells have
   the envelope low above zero, and every one of their 15 bootstrap grid cells agrees. Cross-symbol
   I² = **0.00** on both clocks (sd 0.022/0.030 against median SE 0.024/0.035). Effect is 3.4–3.9×
   the design's own MDE.
2. **The dose-response is monotone, steep, and a clean scale effect.** CONFIRM H1: 0.52× → 1.91×
   the cell mean across deciles, monotone in 9 of 9 steps; P(exceed own P90) runs **0.017 → 0.304**
   (18×). Top vs bottom forecast quintile: mean ratio 2.86, median 2.93, P90 2.92 — **the forecast
   rescales the whole magnitude distribution**, exactly what a vol-conditioned design needs.
3. **The controls discriminate.** Live IC outside the circular-shift central 90% in **73 of 90**
   cells and **30 of 30** intraday CONFIRM cells, against a wide null (p95 median 0.144–0.215). The
   +0.25 bite plant is achieved (0.250) and destroyed by both destroy forms in every cell.
4. **Skill survives level removal on the intraday clocks.** Re-ranked inside each calendar month,
   IC is **+0.251** (CONFIRM H1) and **+0.177** (CONFIRM H4), positive in **99%** and **93%** of 150
   symbol-months. The level-removed ladder still runs 0.64 → 1.57 (H1).
5. **The DESIGN band replicates it.** DESIGN H1 0.283 with 15/15 envelope lows above zero; H4 0.202
   with 12/15. At matched span, DESIGN sits inside the CONFIRM window-to-window distribution
   (18th–39th percentile).
6. **Error reduction clears in every intraday CONFIRM cell.** `dmae_vs_uncond` +6.8 bps (H1, 15/15)
   and +11.9 bps (H4, 15/15); OOS R² 0.151 and 0.142 (point estimates, no CI emitted).
7. **Regime and tail axes agree at H1.** V-REGIME gap +16.8 bps CONFIRM H1 (21/22 clearing),
   relative separation 0.277; V-TAIL P(exceed own P90) 0.129 HIGH vs 0.073 LOW, a 1.76× rate ratio,
   20/22 clearing.
8. **Range-based measures are a materially better volatility input, on every clock.** Matched at a
   single bar: Parkinson beats close-to-close |r| by **+0.125 (H1), +0.108 (H4), +0.108 (D1)** IC.
9. **Causality is independently established.** Bit-exact walk-forward reproduction on five cells
   (~1e-12 bps) against a leaky variant differing by 13.8–52.4 bps; zero fence violations in 232 753
   rows; target identity exact in 225 457 contiguous rows; G1 rv20 hand-recomputed to 8e-15.

---

## 12. Evidence AGAINST the hypothesis

1. **The headline statistic is span-dependent, so "reliability" here is not a fixed quantity.**
   Inside CONFIRM alone, fit-free IC runs 0.147 → 0.306 (H1), 0.056 → 0.257 (H4) and
   **−0.196 → +0.120** (D1) as the window grows from 15 to 290 dates. Any reliability bar stated as
   an IC threshold is a statement about window length as much as about predictability. Applies to
   all three candidate bases.
2. **26% to 75% of the reported IC is between-calendar-month level structure.** The design's own
   block-restricted derangement retains a median **41.5%** of live IC, largest where the pooled IC is
   largest (CONFIRM H4 0.533, CONFIRM D1 0.481, DESIGN D1 0.750).
3. **The daily clock does not clear noise on the design's own primary input.** Within-month at D1,
   `rv20` → next |move| has median IC **−0.130**, positive in only **26%** of 132 symbol-months. The
   entire positive D1 IC is between-month level. DESIGN D1 is 14/15 UNPOWERED with an effect/MDE
   ratio of **0.61** — genuinely unpowered, not a negative.
4. **Within a single day there is no skill at all.** Re-ranked inside each calendar date, H1 IC is
   **+0.024** and H4 is **−0.116**. Any design assuming an hour-resolution vol forecast is not
   supported by this screen.
5. **The frozen DESIGN band cannot answer its own question.** Median 98–102 unique dates against a
   §6.3 requirement of ~225; 42/45 cells UNPOWERED under the literal rule; the first literal calendar
   third is empty for 14 of 15 symbols. The whole affirmative read therefore rests on a band §0
   designates as verification-only.
6. **The cross-sectional axis is weak.** Per-symbol V-XS gaps clear in only 13/22 (CONFIRM H1),
   5/22 (H4), 2/21 (D1), 0/15 (DESIGN D1), with wide dispersion (CONFIRM H1 range −65 to +58 bps).
7. **The HMM regime arm is not a regime arm, and is almost entirely unpowered.** Its state is a
   threshold on the current bar's return (AUC 0.95–0.98), lasts ~2 bars, and 76/83 gap cells are
   UNPOWERED. Conditional on that flag the slow level classifier adds nothing (95.0 vs 94.9 bps at
   CONFIRM H1).
8. **Calendar structure adds nothing on any clock**, and on D1 the dummies actively overfit
   (incremental R² −0.026 to −0.054 on ~100 observations).
9. **The classic HAR specification fails at the daily horizon** (IC 0.062 CONFIRM, −0.022 DESIGN).
10. **There is no working leak gate.** Not evidence against the hypothesis, but a standing
    limitation: the causal claim rests on construction and code re-derivation (both verified
    independently here), not on any destroy test.
11. **One stratum contradicts** — INJUSDT D1 CONFIRM, IC −0.216, envelope [−0.339, −0.090]. It is
    explicable (§9.1) but its explanation is itself a criticism of the statistic.

---

## 13. Summary of the reliability characterisation

| Horizon | What is reliably predicted | Effect size | Uncertainty | Coverage | What is not |
|---|---|---|---|---|---|
| **H1** | Which **days** will have large hourly moves, and the scale of the whole magnitude distribution | pooled IC 0.338; within-month 0.251; dose 3.7×; P90 exceedance 0.017 → 0.304 | 15/15 clear on all 15 grid cells; I² = 0; effect 3.9× MDE | 15 symbols, 292 dates, 6 931 origins/cell | which **hour** of a given day (within-day IC 0.024) |
| **H4** | Same, one step weaker | pooled IC 0.301; within-month 0.177; dose 3.1× | 15/15 clear; I² = 0; effect 3.4× MDE | 15 symbols, 292 dates | within-day ordering (IC −0.116) |
| **D1** | The **month-scale volatility level** | pooled IC 0.196; within-month 0.128 (ridge) but **−0.130 for `rv20`** | 13/15 clear CONFIRM; 2/15 DESIGN; I² = 0.79; DESIGN effect 0.61× MDE | 15 symbols, 286 dates, 286 origins/cell | next-day magnitude ranking from close-to-close RV; range measures needed instead |

**Final verdict is the operator's.** Per AMENDMENT-T2 no PASS/STOP call is made on the
vol-conditioned combination path.

**Probes that would change the picture, in priority order:**
1. Re-express the reliability object as a **within-period** (month-demeaned) IC or a log-volatility
   R², and re-read all three bases on it. If the within-month numbers (H1 0.251, H4 0.177, D1 −0.130
   for `rv20`) are what a vol-conditioned design can actually use, the H1/H4 case is intact and the
   D1 case is not.
2. Re-run the D1 arm with a **single-bar range** primary input instead of 20-bar close-to-close.
3. Fit the HMM to `rv20` rather than `r` so a genuine regime object exists alongside the shock
   detector.
4. *(Done 2026-07-23.)* Extend the `target_overlaps_feature` quarantine to `oos_r2_vs_uncond`,
   `dmae_vs_uncond`, the MAE rows and `ic_rv20_vs_rv_next` so no downstream reader quotes an R² of
   0.967 as forecast skill.

---

## 14. Artifacts produced by this analysis

| File | Content |
|---|---|
| `analysis_code/a01_verify.py` | fence re-derivation, independent IC recompute, quarantine audit, coverage |
| `analysis_code/a02_strata_bases_cigrid.py` | per-stratum table, label counts, CI-grid fragility (L-20) |
| `analysis_code/a03_period_vs_size.py` | fit-free vs fitted gap, CONFIRM subsampling, monthly IC profile |
| `analysis_code/a04_span_clock_measure.py` | span scaling, level decomposition, clock matching, measure matrix |
| `analysis_code/a05_regimes.py` | regime-partition anatomy (states, run lengths, AUC, 2×2 cross-tab) |
| `analysis_code/a06_controls_arms.py` | controls, V-CLOCK / V-TAIL / V-XS / V-PERSIST / V-MEASURE re-derivation |
| `analysis_code/a07_coverage_outliers.py` | band spans, completeness, contrary strata, INJUSDT diagnosis, power |
| `analysis_code/a08_dose_hetero.py` | dose-response, heterogeneity (Q/I²), shape, coverage falsification |
| `analysis_code/a09_causality_recheck.py` | bit-exact walk-forward re-derivation + leaky control + shift tests |
| `analysis_code/a10_plots.py` | plots |
| `analysis_code/a11_final_bits.py` | span-matched percentiles, D1 within-month IC, three bases |
| `analysis_code/out_*.csv` / `out_*.parquet` | every per-stratum table above, emitted in full |
| `plots/span_scaling.png` | IC vs measurement window length, by clock |
| `plots/vlevel_forest.png` | per-stratum primary IC with envelopes, both bands |
| `plots/dose_response.png` | dose ladder, pooled vs level-removed |
| `plots/regime_partition.png` | V-REGIME vs V-REGIME-HMM: occupancy, run length, \|r\| AUC |
| `plots/monthly_ic.png` | within-month IC across the DESIGN/CONFIRM boundary |
