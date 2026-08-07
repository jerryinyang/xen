# Data Analysis: SPDR-014 — zone / mispricing event / post-event MOMO vs MR (CF-VOLDIR-001 / HYP-D1, O3 Group 1)

Fresh-context neutral re-analysis of already-emitted TRAIN-only screen data. Numbers re-derived
from `results/` raw emissions via `analysis_code/reanalyse_014.py` (canonical
`xen.evaluation.block_bootstrap_ci`; no experiment-local analysis code imported). Full per-stratum
magnitude table: `results/perstratum_magnitudes.json`.

**Unit pins (binding).** `r_h = side · 1e4 · (exit_open / breach_entry_open − 1)` — side-signed
**open-to-open bps**. Z-VOL width normaliser = `s_symbol · EWMA_Parkinson(λ=0.94)` on completed H1
bars (`park = sqrt(ln(H/L)²/(4 ln2))`), `s_symbol` frozen on 60-bar DESIGN warm-up (`zvol_scale.json`).
Label deadband `c = 5 bps` (MOMO `r_h>+5`, MR `r_h<−5`, FLAT `|r_h|≤5`). "Primary cell" =
Z-VOL · z=1.5 · H=12 · E-TOUCH · h=12 · P-NONE · H1 (the only cell with the full control battery).

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY   (fee_rt 11.0 + funding 1.0×stamps + 2.0 allowance/leg)
  implication: every partial_net below is OVERSTATED vs full cost
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

---

## 1. Integrity gate (SPDR substitute — no estimand gate in this lane)

| Check | Result | Evidence |
|---|---|---|
| `integrity_selfcheck.json` all_pass | **PASS** | `all_pass:true`; deviations `[]` |
| Golden traces G1–G4 | **PASS** | `golden_traces.json all_pass:true` — G1 BTC band hand==engine to 1e-9, G2 ETH r_12 hand==engine, G3 SOL Z-MAG ineligibility, G4 AVAX P-MR partial_net hand==engine |
| Universe pin equality (top-25) | **PASS** | `universe_pin_check.json set_equal_all:true`; recompute == family pin == results pin |
| TRAIN fence (`exit < 2023-12-18`) | **PASS** | asserted in engine; `train_fence_asserted:true` |
| Causal `t−1` (width ≤ t, anchor = t+1 open, breach entry = j+1 open) | **PASS** | design §2.1/§4.1 construction; golden G2 entry = next open |
| Future-destroy tripwire — no positive survivor above null p95 | **PASS (non-vacuous)** | `tripwire_positive_survivors:[]`; only 1000BONK claimed +14 bps money but sits **below** null p95 68.7 → no integrity flag; derangement destroy moves the P&L metric |
| No signed product / shock-not-regime / straddle-not-headline | **PASS** | integrity flags all true |
| No local accounting (screen = availability, not booked P&L) | **PASS** | costs via `costs.py` flat fee/funding stamps; no `xen.adjudication` reimplementation |

Note (design fidelity): two interpretation notes are logged and do **not** weaken clauses — IN-1
money subset uses zone H=12; IN-2 Z-MAG "monthly refit" implemented as expanding walk-forward ridge
(SPDR-013 recipe). IN-3 last-k Markov conditioner (design §4.4, K∈{4,12}) is emitted as
`last_k_high_4` / `last_k_high_12` (count of HIGH slow-regime bars in last K, causal ≤t) —
answered in §7.1.

---

## 2. Question list (all ANSWERED unless marked)

1. Do bands breach at a non-ambient rate? → §3 (p_event saturates; band tighter than uncond).
2. Post-event residual r_h per stratum, Δ vs each control? → §4 / §5.
3. MOMO vs MR lean magnitude? → §6.
4. Dose-response across z, H, h, conditioners, symbols? → §7.
5. DESIGN vs CONFIRM stability? → §8.
6. Event-definition sensitivity (TOUCH/CLOSE/HORIZON)? → §9.
7. Money subset + straddle (disclosure)? → §10.
8. Power / MDE / CI widths per cell? → §11 (the load-bearing facet).
9. Last-k state-sequence conditioner (ordered, k=1..3)? → **ANSWERED** §7.1 — order matters: a
   fresh L→H vol flip leans MOMO (~+40 bps median, p_momo 0.55); the reverse leans MR; persistent
   HHH/LLL flat. UNPOWERED (small buckets) but a coherent order-conditional lean.

---

## 3. Event rate p_event — band selectivity (magnitude)

At the primary cell the band is **not selective**: median `p_event = 1.000` across the 25 symbols
(min 0 for symbols with no eligible origins, max 1.0). Selectivity only appears at short H / high z:

| source | z | H | event | p_event median (across 25 sym) |
|---|---|---|---|---|
| Z-VOL | 1.0 | 4 | E-CLOSE | 0.87 |
| Z-VOL | 1.5 | 4 | E-CLOSE | 0.73 |
| Z-VOL | 1.5 | 12 | E-TOUCH | **1.00** |
| Z-VOL | 1.5 | 24 | E-TOUCH | 1.00 |
| Z-VOL | 2.0 | 4 | E-TOUCH | 0.81 |
| Z-VOL | 2.0 | 12 | E-TOUCH | 0.99 |

**Measured fact:** over a 12-hour window at z=1.5, price all-but-always touches a ±1.5σ̂ band
(≈100 % breach). The "mispricing event" at the primary cell is therefore ≈ "price moved at all in
12 h", not a rare dislocation. Δ p_event vs the unconditional-σ band is **positive** (+0.05 to +0.11:
BTC +0.110, ETH +0.070, SOL +0.063, MATIC +0.050) — the forecast width is **tighter** than the
unconditional σ band, so it breaches slightly more often. That is a real, small, measured difference
in band geometry; it is not evidence of a rare-event detector.

---

## 4. Post-event residual r_h — primary cell, per symbol (DESIGN)

P-NONE, Z-VOL z=1.5 H=12 E-TOUCH h=12. `dMR`/`dTS` = live mean − matched-random / time-shuffle null
mean (200-seed derangement nulls). `ciL` = block-bootstrap (block=12) CI-low on live mean r_h.
`3rd` = chronological-thirds sign agreement. All magnitudes in open-to-open bps.

| symbol | n | n_dates | mean | median | p_momo | p_mr | dMR | dTS | ciL(mean) | 3rd | MDE |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1000BONKUSDT | 41 | 41 | −22.0 | −119.8 | 0.46 | 0.54 | −9.0 | −17.5 | −179.3 | 3 | 249.8 |
| 1000LUNCUSDT | 111 | 111 | +58.6 | +16.9 | 0.51 | 0.49 | +56.6 | +61.2 | −48.6 | 2 | 188.8 |
| ADAUSDT | 193 | 193 | +20.9 | +22.0 | 0.53 | 0.45 | +21.5 | +20.5 | −14.0 | 3 | 48.6 |
| AVAXUSDT | 180 | 180 | −7.5 | −11.6 | 0.48 | 0.51 | −6.7 | −8.1 | −69.6 | 1 | 81.6 |
| BLURUSDT | 10 | 10 | +491.1 | +546.5 | 0.70 | 0.30 | +480.3 | +484.9 | +234.5 | 3 | 796.2 |
| BNBUSDT | 189 | 189 | −24.3 | −20.5 | 0.43 | 0.56 | −23.7 | −24.0 | −59.9 | 2 | 42.2 |
| BTCUSDT | 196 | 196 | +2.4 | +3.3 | 0.47 | 0.46 | +3.2 | +4.6 | −18.2 | 2 | 37.4 |
| DOGEUSDT | 175 | 175 | −15.6 | +4.5 | 0.50 | 0.47 | −10.4 | −14.3 | −48.6 | 3 | 59.2 |
| DYDXUSDT | 119 | 119 | +76.5 | +57.6 | 0.55 | 0.45 | +75.2 | +78.2 | −33.5 | 3 | 162.2 |
| ETHUSDT | 194 | 194 | +26.2 | +15.1 | 0.53 | 0.44 | +26.1 | +26.4 | −2.3 | 2 | 48.0 |
| GALAUSDT | 169 | 169 | +26.4 | +40.1 | 0.52 | 0.47 | +26.6 | +28.6 | −32.0 | 2 | 93.8 |
| INJUSDT | 103 | 103 | +36.4 | +71.4 | 0.52 | 0.47 | +34.6 | +34.2 | −121.5 | 2 | 167.0 |
| LINKUSDT | 188 | 188 | +11.8 | +2.1 | 0.49 | 0.48 | +12.8 | +15.2 | −32.9 | 2 | 61.3 |
| MATICUSDT | 517 | 517 | −10.2 | −4.5 | 0.48 | 0.50 | −9.2 | −10.2 | −51.7 | 2 | 55.9 |
| OPUSDT | 189 | 189 | −20.9 | −11.2 | 0.48 | 0.51 | −14.8 | −17.5 | −93.5 | 2 | 100.7 |
| SOLUSDT | 197 | 197 | +43.7 | +18.2 | 0.52 | 0.46 | +46.4 | +44.7 | −23.1 | 3 | 97.0 |
| XRPUSDT | 193 | 193 | +16.5 | +12.5 | 0.52 | 0.46 | +15.8 | +13.7 | −15.8 | 3 | 54.4 |

Distribution shape: **right-skewed** at most symbols — mean > median where positive (ETH +26/+15,
SOL +44/+18), and sign disagreement at DOGE (mean −15.6, median +4.5). The mean is tail-driven.

---

## 5. SUPPORTED-residual gate applied per design §8.1 (per symbol, primary cell)

SUPPORTED requires **all four**: (a) mean Δ vs MR or TS ≥ +5 bps; (b) date-block CI-low on Δ > 0;
(c) median Δ ≥ 0; (d) sign consistent in ≥2/3 thirds — **and not UNPOWERED** (n≥80, n_dates≥30,
MDE≤10).

- (a) is met by **11 / 17** symbols vs matched-random (the positive-mean rows above).
- (b) **fails for every powered symbol**: CI-low on the live mean is negative for all except BLUR
  (n=10). Best powered case ETH ciL = −2.3 → Δ CI-low < 0.
- Not-UNPOWERED **fails for all 17** — see §11 (every MDE ≫ 10 bps).
- The **only** row tripping (a)+(b)+(c)+(d) is **BLURUSDT**, on n=10 events, MDE 796 bps →
  **UNPOWERED**, excluded by design.

**Result: 0 powered symbols meet SUPPORTED-residual.** This is a consequence of the design's own
MDE/CI bars applied to the numbers, not of an imported "should be bigger" threshold.

---

## 6. MOMO vs MR rate lean (magnitude, both reported)

Primary cell pooled (E-TOUCH, DESIGN): `p_momo = 0.499`, `p_mr = 0.482` →
**lean = +0.017 to MOMO**, block-CI **[−0.021, +0.055]** (straddles 0). Per symbol the lean spans
−0.13 (BNB) to +0.40 (BLUR n=10); most within ±0.05. Reported as a magnitude: a small MOMO tilt
of ~+1.7 pp above the 0.50 line at the primary cell, not distinguishable from zero at available n.
CONFIRM band: lean **−0.023** [−0.058, +0.011] — sign reverses (§8).

The pin's rate-only tallies (SUGGESTIVE, not residual-SUPPORTED): **18 MOMO-rate / 7 MR-rate**
suggestive cells across the wider grid — disclosure that a MOMO tilt is the more common direction,
without any residual clearing SUPPORTED.

---

## 7. Dose-response & heterogeneity (pooled over symbols, magnitudes)

**Hold h (Z-VOL z=1.5 H=12 E-TOUCH):** mean r_h = **+4.0 (h=4) → +11.3 (h=12) → +21.4 (h=24)** —
the positive mean **grows with horizon**, but the median goes **negative** at h=24 (+4.6 → −7.6):
longer holds add a fatter right tail while the typical event drifts slightly against the breach.

**Band width z (H=12, h=12):** mean/median = z1.0 **+5.1 / +2.6**; z1.5 **+11.3 / +4.6**;
z2.0 **+6.5 / −8.0**. At z=2.0 (larger breaches) the median turns clearly negative (MR-leaning,
p_mr 0.505 > p_momo 0.474): bigger dislocations revert at the median. Low-z leans MOMO (tail).

**Conditioners (primary cell, pooled):**

| conditioner | mean | median | p_momo | p_mr | n |
|---|---|---|---|---|---|
| vol tercile LOW | 6.5 | 2.1 | 0.49 | 0.49 | 1466 |
| vol tercile MID | **24.0** | 14.6 | 0.51 | 0.47 | 816 |
| vol tercile HIGH | 6.4 | 3.5 | 0.50 | 0.49 | 682 |
| mag_high = False | 6.0 | 4.3 | 0.50 | 0.48 | 2236 |
| mag_high = True | **27.7** | 6.0 | 0.50 | 0.49 | 728 |
| slow_regime LOW | 4.0 | 0.0 | 0.49 | 0.49 | 1772 |
| slow_regime HIGH | **22.2** | 14.8 | 0.51 | 0.46 | 1192 |
| shock_flag = False | 6.1 | 2.7 | 0.49 | 0.49 | 2729 |
| **shock_flag = True** | **71.6** | **29.3** | **0.56** | 0.41 | 235 |

The **shock** stratum (top-decile \|r\| on the decision bar — a **named shock, not a regime**) is the
single most structured cell: after a shock, breaches **continue** (MOMO) with mean **+71.6** / median
**+29.3** bps, p_momo 0.56 vs p_mr 0.41. Pooled block-CI (block 12/24/48) = **[+11.9, +134.9]** —
**CI excludes zero and is block-stable**. This is the only pooled residual read in the screen whose CI
clears zero. It is a **cross-symbol pooled disclosure** (design POOLED = disclosure-only) on n=235,
not a per-symbol powered cell; and shock must never be titled a regime. Non-shock pooled = +6.1
[−9.8, +22.1] straddles zero.

### 7.1 Last-k state-sequence conditioner (IN-3 / AMENDMENT-S2, O3 §2.1/§2.2 — primary cell, n=4220)

`last_k_state_K` = the **ordered** slow-regime label sequence over the last K bars, chronological
oldest→newest so the **last char = decision bar** ('H'=HIGH-vol, 'L'=LOW-vol, causal ≤t).
Operator-directed K∈{1,2,3}, each tested. r_h = side-signed open-to-open bps. **Order + run-length
preserved** (a bare count of HIGH bars — the superseded reading — collapses these patterns and hides
the structure below).

**k=1 (last label only):**

| state | n | mean | median | p_momo | p_mr |
|---|---|---|---|---|---|
| H | 1721 | −11.7 | +1.5 | 0.493 | 0.489 |
| L | 2499 | +8.1 | −4.1 | 0.487 | 0.498 |

**k=2 (last two, decision bar = 2nd char):**

| state | n | mean | median | p_momo | p_mr |
|---|---|---|---|---|---|
| HH | 1519 | −16.3 | −2.8 | 0.485 | 0.497 |
| HL | 210 | +25.8 | −16.5 | 0.476 | 0.510 |
| **LH** | 202 | +22.2 | **+40.4** | **0.554** | 0.426 |
| LL | 2289 | +6.5 | −2.7 | 0.488 | 0.497 |

**k=3 (last three, decision bar = 3rd char):**

| state | n | mean | median | p_momo | p_mr |
|---|---|---|---|---|---|
| HHH | 1340 | −15.9 | −3.4 | 0.484 | 0.498 |
| HHL | 159 | +46.9 | +4.6 | 0.491 | 0.491 |
| HLH | 33 | +27.7 | +45.6 | 0.576 | 0.424 |
| **HLL** | 149 | +49.4 | +24.6 | **0.550** | 0.436 |
| LHH | 179 | −19.2 | +2.8 | 0.497 | 0.492 |
| LHL | 51 | −40.2 | −73.4 | 0.431 | **0.569** |
| **LLH** | 169 | +21.2 | +40.3 | **0.550** | 0.426 |
| LLL | 2140 | +3.5 | −5.1 | 0.483 | 0.501 |

**Read (magnitudes, both directions):**
- **A fresh flip INTO high-vol (…L→H) leans MOMO:** `LH` (k2) p_momo 0.554, median **+40.4**;
  `LLH` (k3) 0.550, median +40.3; `HLH` (k3) 0.576, median +45.6 (n=33, thin). A recent low→high
  vol transition on the decision bar → post-breach **continuation**, +40 bps at the median.
- **`HLL`** (recent high, now settled low): mean +49.4, median +24.6, p_momo 0.550 — also MOMO.
- **`LHL`** is the mirror: p_momo 0.431 / p_mr 0.569, median −73.4 — **MR** lean (n=51, thin).
- **Persistent `HHH` / `LLL`:** near-flat (p_momo ~0.48), mean slightly negative / ~0.
- **k=1 alone conditions little:** H vs L rates 0.49 vs 0.49; the *single* last label does not carry
  the signal — the **ordered pattern** does. This is exactly the structure the count reading erased.

**Power caveat:** the discriminating buckets are small (n 33–210) → UNPOWERED; the rate leans
(0.55, 0.43) carry wide CIs and the means are tail-sensitive. As magnitudes on a null base they are a
coherent, **order-conditional** lean (L→H-flip → MOMO ≈ +40 bps median; the reverse → MR), reported
per B-5 as SUGGESTIVE, not a powered SUPPORTED cell. Facet ANSWERED (ordered pattern, k=1..3).

---

## 8. DESIGN vs CONFIRM stability (magnitude of the change)

Primary cell, per symbol, mean r_h:

| | DESIGN pooled | CONFIRM pooled |
|---|---|---|
| weighted mean r_h | **+11.3** | **−4.3** |
| block-CI (blk 12) | [−4.0, +26.6] | [−17.8, +8.9] |
| median-of-symbol-means | +16.5 | −14.3 |

**12 / 17 symbols flip mean sign** DESIGN→CONFIRM (e.g. SOL +43.7→−15.4, DYDX +76.5→−34.0,
XRP +16.5→−28.7, ADA +20.9→−14.3). The DESIGN MOMO tilt does **not reproduce** in the 2023 CONFIRM
band; the pooled swing is ≈ **−15 bps** and the sign reverses. Even pooled DESIGN (+11.3) has a
block-CI that **straddles zero** ([−4.0, +26.6]). This instability is the expected footprint of an
under-powered estimate, not a demonstrated regime change.

---

## 9. Event-definition sensitivity (Z-VOL z=1.5 H=12 h=12 DESIGN, pooled)

| event | mean | median | p_momo | p_mr | n |
|---|---|---|---|---|---|
| **E-TOUCH** | **+11.3** | +4.6 | 0.499 | 0.482 | 2964 |
| E-HORIZON | +4.5 | −8.7 | 0.480 | 0.506 | 1937 |
| **E-CLOSE** | **−6.8** | −15.8 | 0.458 | 0.519 | 2799 |

**The residual sign depends on the event definition.** Intrabar touch (E-TOUCH) leans MOMO
(+11.3 / +4.6); a bar that *closes* outside the band (E-CLOSE) leans MR (−6.8 / −15.8, p_mr 0.519).
Interpretable magnitude: an intrabar wick beyond the band tends to keep going, while a full close
beyond the band tends to pull back — a touch-vs-confirm asymmetry of ≈ 18 bps in mean and ≈ 20 bps in
median. Reported as a structural magnitude, not a headline verdict.

---

## 10. Money subset & straddle (DISCLOSURE-ONLY — PARTIAL_FEES_FUNDING_ONLY, overstated)

| policy | source | mean partial_net | median partial_net | mean gross | n |
|---|---|---|---|---|---|
| P-MOMO | Z-VOL | −14.1 | −68.8 | +0.1 | 6477 |
| P-MOMO | Z-MAG | −32.6 | −106.2 | −18.5 | 271 |
| P-MR | Z-VOL | −15.3 | −61.1 | −1.1 | 6618 |
| P-MR | Z-MAG | −39.8 | −76.0 | −25.6 | 274 |

Straddle (DA-STRADDLE, DESIGN): mean partial_net −27.1 (H=4) / −29.4 (H=12) / −32.8 (H=24). All
negative. Gross of the policy arms is ≈ 0; partial cost (~14 bps) makes every arm negative; medians
strongly negative (right-skew). **No tradability claim is made or implied**; these confirm only that,
even before the missing spread cost, the residual-following policies extract nothing at the median.

---

## 11. Power (the load-bearing facet — B-5)

`MDE ≈ 2.8·σ_r/√n_dates`. Per-event residual dispersion σ_r ≈ **150–190 bps** (a 12-hour open-to-open
absolute move — physically correct for these instruments). At available n (≈200 events/symbol):

- **Every primary-cell MDE is 37–796 bps ≫ the design's ≤10 bps bar.** BTC (best-powered) MDE 37.4.
- To reach MDE ≤ 10 bps at σ_r≈187 needs n ≈ 2,740 events/symbol (~14× available) **or** pooling.
- Pooling all 17 symbols (n=2,964) still gives DESIGN mean +11.3 with block-CI **[−4.0, +26.6]** —
  the pooled residual **does not clear zero**. Only the shock-conditioned pooled subset does.

**The residual estimand is UNPOWERED at every per-symbol primary cell.** Under B-5 this is a
precision fact — "we cannot pin the magnitude," not "the magnitude is zero." The design's own
UNPOWERED rule (MDE≤10) is effectively unreachable at this cell without variance reduction.

---

## 12. Evidence FOR residual ≠ ambient (each a magnitude)

- **Shock-conditioned MOMO:** mean **+71.6** / median **+29.3** bps, p_momo 0.56 vs p_mr 0.41, pooled
  block-CI **[+11.9, +134.9]** (block-stable 12/24/48), n=235. Only pooled read whose CI excludes 0.
- **Event-definition asymmetry:** E-TOUCH +11.3/+4.6 (MOMO) vs E-CLOSE −6.8/−15.8 (MR) — a consistent
  ~18–20 bps split by breach type, present in both mean and median.
- **z / h dose structure:** low-z + long-hold → positive tail-driven mean (h=24 mean +21.4);
  high-z (z=2.0) → negative median (−8), a coherent MR-at-large-breach pattern.
- **Directional tilt:** DESIGN mean lean positive at 11/17 symbols; pooled +11.3 bps; rate tilt +1.7 pp
  MOMO; 18 MOMO-rate suggestive cells vs 7 MR — the modal direction is MOMO.
- **Band geometry:** forecast width is measurably tighter than unconditional σ (Δ p_event +0.05..+0.11).
- **Order-conditional vol-flip (§7.1):** a fresh low→high vol transition on the decision bar (state
  `LH`/`LLH`/`HLH`) leans MOMO — p_momo ~0.55, median **+40 bps** — with the reverse (`LHL`) leaning
  MR. Order-dependent (a bare HIGH-count is flat), coherent across k=2 and k=3; UNPOWERED (n 33–210).

## 13. Evidence AGAINST residual ≠ ambient (equal diligence)

- **Zero powered SUPPORTED cells** — every primary MDE 37–796 bps ≫ 10; no symbol's mean-r_h CI-low
  clears its control null.
- **Even pooled DESIGN residual CI straddles zero** ([−4.0, +26.6]); the MOMO rate lean CI straddles
  zero ([−0.021, +0.055]).
- **DESIGN→CONFIRM sign flip:** 12/17 symbols reverse; pooled +11.3 → −4.3. The DESIGN tilt does not
  reproduce out-of-DESIGN.
- **Band non-selectivity:** p_event ≈ 1.0 at the primary cell — the "event" is not a rare mispricing.
- **Tail-driven means:** medians near 0 or negative where means are positive; money medians −60..−106.
- **Money arms all negative** at the median even on partial cost; gross ≈ 0.

## 14. Anomalies & open questions

- **A-1 (RESOLVED):** Last-k conditioner corrected to O3 intent (AMENDMENT-S2). Original design
  §4.4 "count of HIGH bars in last K∈{4,12}" compressed O3's "last-k states" and hid the structure;
  now emitted as the **ordered** state sequence `last_k_state_1/2/3` and answered in §7.1 — a fresh
  L→H vol flip leans MOMO (~+40 bps median), the reverse MR, persistent runs flat (all UNPOWERED).
  Earlier drafts (count-based, and a stale "not emitted" note) superseded.
- **A-2:** Residual power is structurally out of reach at the per-symbol primary cell (σ_r≈187 bps).
  A powered follow-up would need variance reduction (e.g. normalise r_h by σ̂ before averaging;
  centre-relative rather than open-relative exit) or a pooled/hierarchical estimand — a **design**
  question, not a data defect. Proposal for operator, not run here.
- **A-3:** Three structural signals worth a targeted, powered re-test (all currently disclosure-only /
  UNPOWERED): (1) shock-MOMO; (2) E-TOUCH/E-CLOSE asymmetry; (3) the order-conditional vol-flip lean
  (§7.1, L→H → MOMO ~+40 bps median). The vol-flip is the cleanest new lead from AMENDMENT-S2 — it
  needs a powered test (larger n per pattern via pooling/hierarchy, and a paired-Δ-vs-control CI on the
  pattern strata) before any SUPPORTED claim.

## 15. Recommended verdict (experiment hypothesis HYP-D1 only — NOT final, NOT family)

- **Recommendation: INCONCLUSIVE (UNPOWERED on the residual magnitude).** Under SPDR B-5, UNPOWERED is
  a precision statement, not a negative — this is **not** NOT_WORTH. The residual-≠-ambient object is
  **not established** (0 powered SUPPORTED cells; pooled CI straddles 0; DESIGN→CONFIRM sign flip), but
  measurable, interpretable leans exist on a null base and are reported as magnitudes: shock-conditioned
  MOMO (+72/+29 bps, CI excludes 0), an E-TOUCH-MOMO / E-CLOSE-MR asymmetry (~18–20 bps), a z/h dose,
  and a modal +1.7 pp MOMO tilt.
- **Driven by:** (1) power — every MDE ≫ the 10-bps bar (σ_r≈187 bps); (2) the shock-MOMO pooled CI
  that clears zero; (3) the DESIGN→CONFIRM sign flip that keeps the per-symbol leans within noise.
- **Would change if:** a powered re-test (variance-reduced or pooled/hierarchical estimand, or a
  shock-conditioned per-symbol cell with adequate n) produced a CI-low>0 residual that also held in
  CONFIRM — then SUPPORTED; or if the leans vanished under variance reduction — then WASH.
- **SPDR-016 start gate (design §8.3):** `016_start_allowed = false`, `residual_status = NONE`
  **stands** — because **0 powered primary cells** meet SUPPORTED, which is exactly the design rule.
  The gate does **not** move; the *reason* is unpowered-not-null, and the operator retains the §8.3
  override (signed-residual freeze) if the shock-MOMO / event-def leans are judged worth a powered 016.

**Final verdict is the operator's.** Suggested probes: (X) variance-reduced residual (normalise r_h by
σ̂; centre-relative exit) to lift MDE below 10 bps; (Y) shock-conditioned per-symbol residual with the
named-shock filter as the primary object (never labelled a regime).
