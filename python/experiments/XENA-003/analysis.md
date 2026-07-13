# Data Analysis: XENA-003 (CTRL-03 — naive short-horizon reversion, native limit fills)

**Analyst stage:** data-analyst (VAL-style entry — emission + estimand gate + search +
certification + permutation battery pre-existing; no new emission, no gate spend, no TEST-band
contact).
**Scope of my reads:** TRAIN **search band only** (2021-06-02T00:01 → 2023-03-08T00:00, design §5)
+ the emitted per-candidate parquets. Global 30% holdout never opened; TEST gate band
(≥2024-03-28) never read.
**My code:** `python/experiments/XENA-003/analysis_code/` — `xena003_universe_scan.py`,
`xena003_leg_diagnostics.py`, `xena003_cost_sweep.py`, `xena003_controls.py`, `xena003_plots.py`.
Accounting exclusively via `xen.xena.oracle` / `xen.xena.search` / the `xen.adjudication` leg
contract / `xen.evaluation`.
**Outputs:** `results_analyst/{universe_scan,leg_diagnostics,leg_diagnostics_percand}.parquet`,
`results_analyst/{cost_sweep,controls,leg_diagnostics_summary}.json`,
`plots/cost_sensitivity_and_decomposition.png`.

**Headline:** the effect is **real, tiny, and cost-fatal**. Gross per-leg edge is **1.96 bps**
(95% CI [1.85, 2.07]); the portfolio breaks even at **0.56–1.15 bps** of round-trip spread
(median 0.71). The XENA power curve's "nets survive" band is **20–40 bps**. F̂ ≈ 23 is
1.4 bps/trade × ~150,000 trades × ~1× notional leverage, compounded — not a large edge.

---

## 1. Integrity gate (blocking) — PASS

| Check | Result | Evidence |
|---|---|---|
| Estimand validation, all cells `blocking_pass` | **PASS** | `results/estimand_validation.json`: `n_cells=2777`, `blocking_pass: true`, 0 failing cells, manifest 12/12 instruments, `missing: []` |
| Provenance / causality (verdict-bearing columns ≤ t−1) | **PASS** | see table below |
| Leak tripwire (destroy control) — collapsed? | **N/A → CONFOUNDED, see §4.4** | permutation battery v2 collapses F̂ 22.80 → 5.66 (collapse fraction ≈1.00 of the above-null excess), but it destroys the **entry-price basis** as well as the alignment; it is *uninformative*, not an alarm. Discriminating control run below (ARM-OPEN / ARM-NEXTOPEN) — the edge does NOT survive it either. **No leak signature.** |
| Holdout untouched | **PASS** | every emission `analysis_end_utc = 2024-12-11T08:19:00Z` (spot-check 21 candidates, max ExitTime ≤ fence); my scripts hard-code the search band `[1622592060e9, 1678233600e9)` |
| Price-primary (cTrader engine emission under fence) | **PASS** | `run_metadata.json: execution="native_limit_orders_m1_fills"`; all P&L from `cis_trades.parquet` fills |
| No experiment-local accounting defs | **PASS** | `check_no_local_accounting('code')` → `{ok: True}`; same for `analysis_code` |
| Search claim reproduces on my platform | **PASS** | rank-0 F̂ (P25, restart-0 block starts) recomputed locally = **24.637** vs reported `search_F_hat` 24.637 |
| Physicality tripwire (Amendment 3) | **PASS (restated)** | `results/physicality_audit.json`: 51/14,400 flags, all root-caused to tick-stamp/feed-gap ambiguity; no fill at an untouched engine-feed price |

### Provenance trace (my own re-derivation from raw emissions)

| Column | Inputs & timestamps | ≤ t−1? | Evidence |
|---|---|---|---|
| Buy/sell limit price | `min/max(Low/High[t−3..t−1])` on **confirmed** LTF bars | YES | provenance probe: **99.8%** of fills are at-or-better than the causal 3-bar extreme derived from *confirmed* bars (USTEC n=37,890; UK100 n=22,003; BTCUSD n=41,064). Median improvement vs the limit +0.6 … +3.0 bps = legitimate gap-through fills (limit "or better") |
| `EntryFillPrice` | engine m1 fill inside the LTF bar | YES | fill ∈ [m1 Low, m1 High] verified by the Amendment-3 tripwire against the **engine's own** feed |
| L-01 own-close-as-limit pattern | — | **ABSENT** | limit built from t−3..t−1 only; fill==own-bar-close occurrences (1.1–8.2%) are coincidental bars closing on their extreme, not a systematic index |
| `ExitFillPrice` | market at LTF bar open, engine-filled on the next m1 | YES | exits stamped 1 m1 bar after the LTF bar open; median \|exit − LTF RealOpen\| = 1.4–1.7 bps (one minute of drift), **no directional advantage** |
| `SlPrice` | `EntryFill ∓ 2 × HTF median-TR ATR(14)` at the latest confirmed HTF bar | YES | finite on every leg (candidate gate) |

**Nothing here blocks.** Everything below is evidence for the operator.

---

## 2. Question list (all ANSWERED)

| # | Question | § |
|---|---|---|
| Q1 | Do per-bar/per-leg totals reconcile per cell? | §1 (estimand gate, 2,777/2,777) |
| Q2 | Is F̂ ≈ 23 driven by per-trade edge, trade count × compounding, or the sizing denominator? | §3.1 |
| Q3 | Per-trade gross economics vs the L-22 / WS-6 MDE curve? | §3.2 |
| Q4 | Cost-sensitivity curve; breakeven RT cost? | §3.3 |
| Q5 | Is the entry fill systematically better than the grid the oracle marks against? | §3.4 |
| Q6 | Adverse selection: forward return conditional on a fill? | §3.4 |
| Q7 | Is the permutation battery confounded for a limit-entry universe? | §4.4 |
| Q8 | Amendment-4 grid seam: double-count / edge P&L injection? | §4.5 |
| Q9 | Is 12/12 certification informative, or is ~everything gross-profitable? | §4.6 |
| Q10 | Realised MAE vs the (no-live-stop) 2×ATR risk unit? | §3.1 |
| Q11 | Per-year stability / concentration / occupancy? | §3.5 |
| Q12 | Filter-structure read (V00 vs V01–V18)? | §4.7 |
| Q13 | Power: can the machinery see a 2 bps effect at all? | §3.6 |

---

## 3. The decomposition

### 3.1 Where F̂ = 23 comes from (Q2, Q10)

Oracle sizing: `units = r·FM / (stop_distance · money_per_unit)`, `r = 0.005`, `R_max = 0.05`.

| Finalist | n admitted | n rejected (R_max) | rej % | notional-wtd gross/trade | **notional/equity per position** | F_point |
|---|---|---|---|---|---|---|
| rank 0 | 157,960 | 37,092 | 19.0% | **1.431 bps** | **1.05×** | 24.82 |
| rank 4 | 133,274 | 14,059 | 9.5% | 1.502 bps | 1.07× | 21.32 |
| rank 9 | 143,977 | 57,602 | 28.6% | 1.363 bps | 1.01× | 22.05 |
| all 12 | 133k–158k | 14k–58k | 9.5–28.6% | **1.250–1.549 bps** | **0.93–1.10×** | 21.2–24.8 |

`F ≈ n_trades × leverage × gross_bps/1e4` → 157,960 × 1.05 × 1.431e-4 = **23.7** ≈ F_point 24.82
(remainder = compounding convexity). **The magnitude is trade COUNT × compounding, at ~1× notional
leverage per position — not a leveraged-sizing artifact.**

The sizing denominator is **not** fictional in the way feared (median stop = **53.2 bps**):

| Realised adverse excursion vs the nominal (never-placed) stop | value |
|---|---|
| median MAE / stop distance | **0.14** |
| legs with MAE > 1× stop | **4.00%** |
| legs with MAE > 2× stop | 0.69% |
| legs realising a loss > 1R | **1.81%** |
| legs realising a loss > 2R | 0.31% (worst leg **−11.25 R**) |

→ 96% of legs never touch the sizing stop; the oracle's `R_max` open-risk book is understated on
~2–4% of legs (no live stop ⇒ those run past the nominal unit). Material as a **risk disclosure**,
**not** as the driver of F̂. Explanation "(c) tight stop ⇒ huge size ⇒ leveraged compounding" is
**largely ruled out**.

### 3.2 Per-trade gross economics vs the MDE curve (Q3 — decisive)

Certified-finalist member candidates, search band, **717,967 legs / 240 candidates**. Top subset
(rank 0), n = **195,056 legs**, `xen.evaluation.block_bootstrap_ci`, 5-seed battery, block sweep
32/64/128:

| Quantity (bps of entry price, per leg) | mean | 95% CI (block 64) | block-32 / block-128 | seed range (low) |
|---|---|---|---|---|
| **gross/leg** (the money) | **1.958** | **[1.846, 2.073]** | [1.849,2.069] / [1.833,2.085] | [1.844, 1.847] |
| median / 5%-trimmed-mean gross | 2.40 / 2.43 | [2.32,2.48] / [2.34,2.52] | — | — |
| **print premium** (limit fill vs the open of the bar it filled in) | **7.496** | [7.319, 7.679] | stable | [7.311, 7.320] |
| **forward path** (fill-bar open → exit) | **−5.538** | [−5.703, −5.378] | stable | stable |
| **first mark** (fill → **next** LTF bar open, ONE bar) | **1.785** | [1.726, 1.847] | stable | [1.725, 1.727] |
| **all the rest of the hold** (next open → exit) | **0.172** | [0.078, 0.269] | stable | [0.076, 0.080] |

Identity `gross = print + path` verified to 1.1e-13 bps. All CIs **exclude zero**; all block- and
seed-stable.

**91.2% of the entire gross edge is booked in the single mark interval between the limit print and
the next grid open** (≈5 minutes on the 1H5M domain that supplies 76% of finalist slots). The
mechanism the design registered — snap-back captured over **0.5–4× the HTF span** — contributes
**0.172 bps/trade (8.8%)**.

Per instrument (finalist members):

| Symbol | legs | gross/leg | print | first-mark | first-mark share | median stop | **gross / 2×ATR** |
|---|---|---|---|---|---|---|---|
| USTEC | 119,256 | 2.115 | 8.21 | 1.924 | 0.91 | 61.4 | 0.032 |
| US2000 | 99,754 | 2.086 | 8.14 | 1.849 | 0.89 | 59.7 | 0.036 |
| US30 | 85,203 | 1.392 | 5.43 | 1.295 | 0.93 | 41.5 | 0.033 |
| BTCUSD | 81,046 | 5.915 | 19.93 | 5.144 | 0.87 | 172.5 | 0.032 |
| UK100 | 75,379 | 1.464 | 4.70 | 1.080 | 0.74 | 41.8 | 0.035 |
| US500 | 49,392 | 1.458 | 6.30 | 1.306 | 0.90 | 48.2 | 0.030 |
| JP225 | 42,375 | 1.347 | 5.99 | 1.338 | 0.99 | 52.5 | 0.025 |
| AUS200 | 23,510 | 1.535 | 5.04 | 1.211 | 0.79 | 44.9 | 0.031 |
| STOXX50 | 8,263 | 1.984 | 8.41 | 1.811 | 0.91 | 78.4 | 0.027 |
| HK50 | 8,252 | 1.637 | 10.67 | 2.356 | 1.44 | 81.8 | 0.022 |

**The gross edge is a near-constant 2.2–3.6% of the 2×ATR volatility unit across twelve unrelated
markets.** A genuine market inefficiency does not present as one dimensionless constant across
BTCUSD and JP225; a **volatility-proportional microstructure term (bid–ask bounce / discretisation
of the OHLC extreme) does exactly this.**

**Against the WS-6 power curve (L-22 / design §7):** nets survive at **20–40 bps gross/trade**.
XENA-003 sits at **1.3–2.1 bps** for the indices — **1/15 to 1/30 of the band**. Win rate 59–62%;
exit mix: profit-exit 31% (1H5M) / 41% (4H15M) / 49% (1D1H).

### 3.3 Cost-sensitivity curve + breakeven (Q4 — the decision number)

Oracle re-run per finalist with `charge_costs=True`, spread added on top of the design §4
commission pins. Plot: `plots/cost_sensitivity_and_decomposition.png`.

**Portfolio F̂ (bootstrap P25) vs added round-trip spread — all 12 certified finalists**
(−32.24 = the log floor, i.e. **account ruin**):

| added RT spread | 0 bps (commissions only) | 0.25 | 0.5 | 1.0 | 1.5 | ≥2.0 |
|---|---|---|---|---|---|---|
| rank 0 (best) | 17.15 | 12.98 | 8.78 | **−0.01** | **RUIN** | RUIN |
| rank 5 | 17.48 | 13.75 | 9.79 | 1.78 | RUIN | RUIN |
| rank 2 | 14.47 | 10.62 | 6.70 | RUIN | RUIN | RUIN |
| rank 7 | 7.98 | 3.76 | RUIN | RUIN | RUIN | RUIN |
| **# of 12 still positive** | 12 | 12 | **5** | **2** | **0** | **0** |

**Breakeven added round-trip spread (bisection on F_point, 1e-3 bps):**

| | min | **median** | max |
|---|---|---|---|
| 12 certified finalists | **0.564 bps** | **0.705 bps** | **1.146 bps** |

The curve does not decay gently, it **cliffs into ruin** — a 1 bp cost on 150,000 trades at ~1×
leverage is ~15 log units, and the whole gross F is only ~23. Breakeven equals, to first order, the
notional-weighted gross per trade (1.25–1.55 bps), as it must (`net_bps = gross_bps − cost_bps`).

**Context.** Round-trip spread on these instruments is realistically 1–3 bps (index CFDs), and the
design §4 spread pins are **still absent** (`universe_manifest.json` carries `cost_bps = 0.0` for
all ten indices; only XAUUSD 0.28 and BTCUSD 13.0 are non-zero). The strategy is **cost-dominated by
~1.5–4×** at any plausible pin. Even with **zero** spread charged, rank-0 F falls 24.82 → 17.15 on
the pinned commissions alone.

### 3.4 Fill mechanics / adverse selection (Q5, Q6)

- **Entry**: limit fill at the trailing 3-bar extreme — systematically **better than every LTF grid
  price the oracle marks against**: `dir·(fill-bar open − EntryFill)` = **+7.50 bps**, positive on
  **98.0%** of all 717,967 legs. Median gap-through improvement vs the limit itself: +0.6 to +3.0 bps.
- **Exit**: market at the LTF bar open, filled on the next m1 → **no** directional advantage
  (median |exit − grid open| = 1.4–1.7 bps, unsigned).
- **Adverse selection, measured directly**: conditional on a fill, the forward path *from the fill
  bar's open* is **−5.54 bps** — price does **not** return to where the bar started. Buying the
  3-bar low is followed by continuation, not reversion, relative to the pre-fill price level. The
  only positive term is the **+1.96 bps residual measured from the print itself**, and 91% of that
  lands in the first bar.
- **Cross-universe anchor (the clincher).** Same instruments, bands, oracle, machinery:

| universe | entry mechanism | **print premium** | **gross bps/leg** | frac candidates gross-positive | live F̂ median |
|---|---|---|---|---|---|
| XENA-001 | RANDOM, bar-close/open fills | **0.000** | **−0.065** | 47.4% | 4.27 |
| XENA-002 | naive momentum, bar-close/open fills | **0.000** | **+0.085** | 52.6% | 4.79 |
| **XENA-003** | **passive limit at the 3-bar extreme** | **+4.9 … +8.0** | **+1.91** | **79.9%** | **22.80** |
| XENA-003 **permuted** (grid-open re-pricing) | — | ~0 by construction | — | — | 5.66 |

The *only* structural difference between the universe that prints F̂ 22.8 and the two that print
F̂ 4.3–4.8 is **the presence of a passive-limit print premium**. Every grid-open-priced universe —
random entries, momentum entries, and XENA-003's own permuted twin — lands in the same F̂ 4–6 band.
That band is the **machinery's overfit baseline** (LAHC picking 25–37 of 2,736 on noise), not a signal.

### 3.5 Stability, concentration, occupancy (Q11)

| Read | Value |
|---|---|
| Per-year gross/leg (top subset, leg-weighted) | 2021 **1.87** · 2022 **2.07** · 2023 **1.63** bps — **stable, not a regime artifact** |
| Concentration: drop top 0.1% / 1% / 5% winning legs | 1.76 / **1.03** / **−0.74** bps — the mean is tail-dependent |
| Occupancy (post-warmup search-band bars in market) | median **39.6%**, max **81.6%** (C3-UK100-1H5M-H1X-V00); 6 top-subset members > 70% |

An 80%-occupancy 5-minute "dislocation fader" is not an event strategy — **it is a continuous
two-sided passive market-making grid.** What the emission *is* is a market maker collecting the
bid–ask bounce; market makers are paid by the spread they are here being charged.

### 3.6 Power (Q13)

WS-6 v3 power curve: 70% @ 30 bps, 94% @ 40 bps gross/trade **at 60 trades/candidate**. Live density
is **~1,700 trades/candidate (1H5M median)** and **133k–158k admitted legs per subset** — 3 orders
of magnitude more. The machinery has *enormous* power here, and 12/12 certification is **fully
consistent with a genuine gross effect of 2 bps**. This is **not** a false positive. The problem is
not detection; it is magnitude.

---

## 4. Controls and the certification evidence

### 4.4 The permutation battery is CONFOUNDED for this universe (Q7) — confirmed

Battery v2 rotates each candidate's stream **and re-prices entry/exit from grid opens at the new
times**. For XENA-001/002 entries were already grid-open-priced → rotation destroys only the
temporal alignment. For XENA-003 entries are **limit prints at local extremes** → rotation
additionally destroys the **entry-price basis** (a +7.5 bps/leg term). The live≫permuted gap is
therefore **mechanically guaranteed for any limit-entry universe**, with or without predictive
content. The battery cannot discriminate here. It is not an alarm; it is **uninformative**.

**Discriminating controls** (`xena003_controls.py`; identical entry TIMES, identical exits, identical
sizing/StopDistance — only the entry price basis changes, so temporal alignment and the forward path
are untouched):

| Arm | entry price | F_point (12 finalists) | vs live |
|---|---|---|---|
| **LIVE** | limit fill at the 3-bar extreme | **21.2 … 24.8** | — |
| **ARM-OPEN** | open of the LTF bar the fill occurred in | **−33.7 … −77.6** (ruin) | collapse fraction **2.4–4.3** (>100%) |
| **ARM-NEXTOPEN** | open of the **next** LTF bar (implementable market-order analogue) | **+0.09 … +1.93** | collapse **93–99%**; **below the permuted null band (5.66)** |
| permuted battery (v2) | grid opens at rotated times | 3.86 … 7.31 (median 5.66) | — |

**Read.** Hold the timing and the signal exactly as emitted and change *only* the entry price from
the limit print to the adjacent grid open, and the entire F̂ ≈ 23 disappears (ARM-NEXTOPEN → ~1;
ARM-OPEN → ruin). The gap between live and permuted is **the limit print**, not "entry at a
predictive moment." **Explanation (a) fill-price advantage is the dominant mechanism.**

*Symmetric caveat, stated deliberately:* ARM-OPEN/ARM-NEXTOPEN are **decompositions, not tradable
alternatives** — both condition on a fill that only happened because price reached the limit. They
prove *where the money sits*, not that the fill was fake. The fills **were physical** (Amendment-3
tripwire, engine feed). The honest statement: the money is the **passive-limit maker premium**
(+7.5 bps of price improvement vs the grid), of which the price path takes back −5.54 bps, leaving
**+1.96 bps** — and any round-trip spread ≥0.7 bps takes back the rest.

### 4.5 Amendment-4 grid seam (Q8) — NOT an artifact

| Check | Value |
|---|---|
| Search-band grid: interior bars / with appended terminal bar | 134,780 / **134,781** (exactly **one** bar appended) |
| Last interior close vs segment end | 2023-03-07T23:55 vs 2023-03-08T00:00 |
| Share of total portfolio money in the appended terminal bin | **0.000%–0.005%** (max 4.5e-5 across the 12 finalists) |
| Top-subset entries after the last interior close | **4** |
| Top-subset legs whose exit lands after the last interior close | **11** (of 157,960) |

No double-count (the appended bar is a *binning target* for events the oracle already censors inside
the segment; increments telescope and reconcile). No disproportionate terminal mark.
**Explanation (b) grid-seam artifact is RULED OUT.**

### 4.6 Is the certification informative? (Q9) — largely NOT

| Marginal read over the FULL 2,736-candidate universe (search band) | Value |
|---|---|
| candidates gross-profitable standalone (Σ RealizedBps > 0) | **79.9%** (2,171 / 2,716 with legs) |
| …of the 1H5M domain (76% of finalist slots) | **94.7%** |
| median gross/trade across the universe | **1.91 bps** |
| candidates with gross/trade > 20 bps (the MDE band) | **6.7%** (thin, ~60-trade 1D1H cells) |

| Certification evidence package | Value | Read |
|---|---|---|
| n_certified / n_finalists | 12/12 | — |
| plateau min-drop ratio | 0.905–0.955 (threshold 0.70) | no keystones (`keystones: {}`) |
| pbo_like | 0.0 | all 4 purged folds positive for all 12 (fold F 1.8–3.9) |
| restart F̂ dispersion | 21.20 / 22.80 / 24.64 (spread 3.44) | tight |
| **pairwise Jaccard between the 12 restart terminals** | **median 0.108, max 0.180, min 0.043** | **near-DISJOINT winners** |
| Hamming | 35 / 49 / 65 (sizes 24–37) | same |
| resim `frac_folds_below_search_p25` | 1.0 (all) | expected: folds ~3 months vs a 21-month search band (log-wealth scales with band length) — **not** a divergence signal |
| evaluation counts (§10.4) | search 322,803 evals; certify 1,104; budget 27,294/restart; distinct_subsets = evals (no cache collisions) | — |

**Twelve restarts converge on twelve essentially disjoint subsets (11% overlap), all reach F̂ 21–25,
and all 12 certify with every fold positive.** That is not a well-identified optimum on a sparse
signal; it is a **degenerate landscape** in which ~80% of the universe is gross-profitable and any
~30 high-cadence candidates compound the same 1.4 bps. Certification here confirms **ubiquity**, not
selection skill — the verdict rests on the cost read.

### 4.7 Filter-structure read (Q12) — the registered family thesis is NOT supported

| | share of finalist member slots (n=364) | universe share | ratio |
|---|---|---|---|
| **V00 (baseline, NO HTF filter)** | **21.2%** | 5.3% (1/19) | **4.0× OVER-represented** |
| 1H5M domain | 75.8% | 33.3% | 2.3× |
| H05X (shortest hold) | 53.3% | 25.0% | 2.1× |

Median gross/trade: V00 **1.837** bps vs filtered V01–V18 **1.922** bps — a wash. **The HTF context
filters are not selected; the unfiltered baseline is preferred**, and what the search actually
maximises is **cadence** (shortest domain × shortest hold = the most trades on which to compound the
print premium). CF-MTFCTX-001's conditioning thesis gets no support from this universe.

---

## 5. Evidence FOR a real, gate-worthy effect

| # | Observation | Number |
|---|---|---|
| F1 | A genuine, statistically unambiguous gross edge exists | gross/leg **+1.958 bps**, bootstrap 95% CI **[1.846, 2.073]**, n=195,056; block-stable (32/64/128), seed-stable |
| F2 | Stable across time, not a regime artifact | per-year 1.87 / 2.07 / 1.63 bps (2021/22/23) |
| F3 | Homogeneous across all 12 instruments and 3 domains | every symbol positive (1.35–5.92 bps) |
| F4 | The certification machinery behaved correctly and is well-powered here | 133k–158k legs/subset vs the 60-trade WS-6 basis; plateau 0.905–0.955, no keystones, pbo_like 0.0, all 4 folds positive ×12 |
| F5 | The fills are physical, not fabricated | Amendment-3 tripwire PASS on the engine feed; 99.8% of fills at-or-better than the causal 3-bar extreme; no L-01 pattern |
| F6 | The residual *hold* term is positive and its CI excludes zero | +0.172 bps [0.078, 0.269] — there IS post-fill reversion beyond the first bar |
| F7 | The sizing denominator is not grossly fictional | median MAE = 0.14× stop; only 4.0% of legs exceed the nominal 2×ATR distance |
| F8 | Amendment 4 injected no P&L | terminal bin ≤ 0.005% of portfolio money; 11/157,960 legs on the seam |

## 6. Evidence AGAINST a real, gate-worthy effect

| # | Observation | Number |
|---|---|---|
| A1 | **The edge is 1/15–1/30 of the pre-registered "nets survive" band** | 1.25–1.55 bps notional-weighted vs 20–40 bps (WS-6) |
| A2 | **Breakeven round-trip cost is 0.56–1.15 bps (median 0.71)** — below any plausible index spread | bisection on F_point, 12/12 finalists |
| A3 | **12/12 finalists are RUINED (F = −32.2) at ≥1.5 bps added spread**; only 5/12 survive 0.5 bps, 2/12 survive 1.0 bps | cost sweep |
| A4 | **Even at ZERO spread the design's own commission pins cost 30% of F** (BTCUSD 13 bps) | rank-0 F 24.82 → 17.15 |
| A5 | **91.2% of the gross edge is booked in ONE bar** (limit print → next grid open); the registered mechanism (0.5–4× HTF span snap-back) contributes 8.8% | first-mark 1.785 vs total 1.958 bps |
| A6 | **The forward path from the fill bar's open is NEGATIVE** — conditional on a fill, price continues, it does not revert | −5.54 bps [−5.70, −5.38] |
| A7 | **Remove only the limit print (times/exits/sizing unchanged) and everything vanishes** | ARM-NEXTOPEN F 0.09–1.93 (below the permuted null 5.66); ARM-OPEN → ruin |
| A8 | **The live≫permuted gap is mechanically guaranteed** for any limit-entry universe | permuted 5.66 ≈ XENA-001 LIVE 4.27 ≈ XENA-002 LIVE 4.79 — the "null" band is the machinery's overfit baseline |
| A9 | **The effect is a fixed fraction of local volatility across 12 unrelated markets** — a microstructure signature | gross/2×ATR = 0.022–0.036 (BTCUSD 0.032 ≈ JP225 0.025) |
| A10 | **Certification is uninformative**: ~80% of the universe (94.7% of 1H5M) is gross-profitable; the 12 restart winners are near-disjoint (Jaccard 0.11) yet all score 21–25 | universe scan |
| A11 | **Concentration**: dropping the top 5% of winning legs turns the mean negative | +1.96 → −0.74 bps |
| A12 | **What the strategy IS**: an ~80%-occupancy two-sided passive quoting grid — a market maker being charged, not paid, the spread | occupancy median 39.6%, max 81.6% |
| A13 | **The family thesis (HTF conditioning) is contradicted**: unfiltered V00 is 4× over-represented among finalists | §4.7 |
| A14 | **P-10 is squarely re-encountered**: passive-limit MR fade, banned as a capture vehicle for exactly this seam | pitfalls-ledger P-10 |
| A15 | **The NET informational gate leg cannot even be computed**: design §4 spread pins are still `OPERATOR PIN REQUIRED`; manifest carries `cost_bps = 0.0` for all ten indices | `universe_manifest.json` |

---

## 7. Which explanation the data supports

| Candidate explanation | Verdict | Driving number |
|---|---|---|
| **Fill-price advantage** (passive-limit print vs the marking grid) | **SUPPORTED — dominant** | print premium +7.50 bps on 98.0% of legs; 91.2% of the edge in the first mark; ARM-NEXTOPEN kills F̂ 23 → ~1 |
| **Genuine-but-sub-cost reversion** | **SUPPORTED — the honest residual** | +1.958 bps [1.846, 2.073], stable per-year, all 12 instruments; breakeven 0.56–1.15 bps RT |
| **Grid-seam artifact (Amendment 4)** | **RULED OUT** | terminal bin ≤ 0.005% of money; 11 legs on the seam |
| **Sizing-leverage compounding** (tight stop ⇒ huge size) | **RULED OUT as the driver** | notional/equity per position 0.93–1.10×; median stop 53 bps; MAE 0.14× stop. F̂ comes from **trade count** (150k), not leverage |
| **Genuine AND cost-surviving** | **RULED OUT** | 12/12 finalists ruined at 1.5 bps RT; 0/12 clear any realistic index spread |
| **Leak / look-ahead** | **RULED OUT** | provenance PASS (limit from confirmed t−3..t−1, 99.8%); physicality PASS; no L-01 pattern |

**One-sentence mechanism.** XENA-003 is a two-sided passive market-making grid whose engine fills
earn a +7.5 bps maker/discretisation premium against the mark grid, of which the subsequent price
path takes back −5.5 bps, leaving ~+2 bps of real but volatility-proportional (bounce-scale) gross
per trade; multiplied by 150,000 trades at ~1× leverage this compounds to a spectacular costless
log-wealth of 23 — and is annihilated by 0.7 bps of round-trip spread.

---

## 8. Anomalies & open questions

1. **Spread pins are still missing** (design §4). Any gate spend today would produce a **binding
   GROSS pass** with a **vacuous NET block** (`cost_bps = 0` on ten of twelve instruments) — the
   exact L-22 shape the lesson was written to prevent. Should be resolved regardless of the verdict.
2. **No-live-stop tail.** 1.81% of legs lose >1R and 0.31% >2R (worst −11.25R). The oracle's `R_max`
   open-risk book is optimistic on ~2% of legs. Immaterial to F̂ here, but a standing property of the
   sizing-only-`SlPrice` contract worth disclosing in any future universe using it.
3. **Platform caveat (INFR-007).** My reads ran the Rust kernel on macOS/aarch64: the pinned parity
   corpus is 499/500 with one 1-ULP case (`best-r00` locally; `rand-146` on the c8g adjudication
   box). My re-derived rank-0 F̂ = 24.637 reproduces the reported 24.637 exactly, so the caveat is not
   load-bearing for anything above.
4. **The permutation battery needs a design fix for native-fill universes** (proposal, operator's
   call): the rotation must preserve the entry-price *basis* (e.g. re-time to a matched touched
   extreme), or the tripwire will keep returning a mechanically-guaranteed "pass" on any limit-entry
   universe. As specified it is uninformative, not wrong.
5. **Not answerable without new emission** (listed, not run): would the ~2 bps survive a fill model
   with queue position / partial fills / one-tick adverse selection at the touch? Almost certainly
   not, but out of scope here.

---

## 9. Recommended verdict (experiment hypothesis only — NOT final, NOT family)

**Recommendation: NOT SUPPORTED (magnitude) — and DO NOT SPEND A COUNTED TEST GATE SLOT.**

This is the EXP-025 / L-21 shape exactly: the effect **replicates end-to-end and is real**; it is
simply **10–30× too small to pay for its own execution**. The extreme F̂ is a costless-compounding
artifact of 150,000 trades × a bounce-scale per-trade edge, not a large edge.

**Driven by (the 3 decisive numbers):**
1. **Gross/trade = 1.96 bps [1.85, 2.07]** vs the pre-registered 20–40 bps "nets survive" band (§3.2).
2. **Breakeven round-trip cost = 0.56–1.15 bps (median 0.71)**; 12/12 finalists in **ruin** at
   1.5 bps (§3.3).
3. **91.2% of the edge is the limit print → next-open step**; removing only the print basis
   (ARM-NEXTOPEN, timing/exits/sizing untouched) collapses F̂ 23 → ~1, **below the permuted null**
   (§3.4/§4.4).

**Why the gate spend is specifically wasted (not merely risky):** the gross gate is *binding* under
A-4, the search-band F̂ is ~23 against a threshold of 0.0558, and fold F's are 1.8–3.9 — a GROSS
**pass is close to certain**. But the NET block needed to make that pass mean anything (a) cannot be
computed (no spread pins) and (b) is already known from this sweep to be **catastrophically negative
at any real spread**. A slot would be spent to certify the machinery on a strategy the data has
already shown to be non-deployable — with the permanent record showing a "pass". §8 has no
interpretation band for that outcome, which is itself the tell.

**Would change if:** (i) an operator-pinned spread map showed round-trip costs **below ~0.5 bps** on
the index book (I found no basis for that); or (ii) a maker-rebate/queue model let the strategy
*earn* rather than pay the spread — a different execution contract, a different family, needing its
own emission (design §4 explicitly declines the maker-rebate assumption); or (iii) the 0.172 bps
residual hold term were shown to be capturable at a horizon where costs amortise — 8.8% of an
already sub-cost edge, so a weak lead.

**Suggested probes if the operator wants to push:**
- *On "it's still real":* re-run the finalists with the profit-exit disabled and a longer hold, to see
  whether the 0.17 bps residual grows with horizon (cheap; no new emission — but P-02 forbids tuning
  exits to rescue an entry).
- *On "it's a bounce":* correlate the per-symbol first-mark step against each symbol's tick size /
  typical m1 range; if it tracks tick granularity the microstructure reading is closed.
- *On governance:* pin the spread map (design §4) before any XENA universe reaches a gate, so the NET
  block is never vacuous.

**Family note (out of my authority):** this is CF-MTFCTX-001's second informed control; the HTF filter
thesis got **no support** (V00 4× over-represented). Family disposition belongs to the operator-signed
checkpoint retrospective, not here.

**Final verdict is the operator's.**
