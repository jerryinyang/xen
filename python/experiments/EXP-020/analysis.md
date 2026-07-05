# Data Analysis: EXP-020 — CF-VOLHARV-001/HYP-002 structure-borne oscillation harvest (ARM R rebalance + ARM G grid)

Analyst: fresh-context data-analyst, 2026-07-05. All numbers computed by
`analysis_code/` (analyst-owned) on raw emissions via canonical `xen.adjudication` /
`xen.evaluation`; no experiment-local `code/` imported. Results JSON:
`results/armR_premium.json`, `results/armG_grid.json`, `results/tripwire_delay.json`,
`results/probes.json`. Plots: `plots/*.png`.

Cost framing (carried blocker): engine fills are zero-spread (bid=ask backtest) -> emissions
are GROSS. Reads reported at three cost levels: gross, gross-commission (FTMO pinned,
`xen.evaluation.FTMO_COSTS`, 2026-07-04), and weekend-ceiling spread STRESS (predeclared
ceiling, A1). **Net-at-live-spread is BLOCKED** (live-session spread pin outstanding;
EURJPY has no stress read — spread unpinned even at ceiling).

---

## 1. Integrity gate (blocking)

| Check | Result | Evidence |
|---|---|---|
| Estimand validation, all cells blocking_pass | **PASS** | 6 artifacts, 68 cells, 0 failing (`results/estimand_validation_{R,R-twin,G,G-invert,R-delay1,G-delay1}.json`; `phase0_integrity.py`) |
| Provenance trace (decisions <= t-1) | **PASS** | ARM R: 0 trigger violations across NZDUSD/USDCAD/BTCUSD (2,119 trade-bars); reconstructed pre-trade weight breaches band at completed close for every trade; fill = next bar open in 2,118/2,119; post-trade weight restored 100%. ARM G: anchor = prior-month close (`Xen.StructureHarvest.cs:323-341`, per QA); entries are resting limits/stops filled on m1 touch |
| ARM G fill causality (tripwire 3) | **PASS** (2 benign anomalies) | m1 touch check on NZDUSD/USDCAD/XAUUSD, both arms: 1,900 fills, 2 violations, both USDCAD, both <=3.8 bps and explained (1-2-min timestamp offset at a touched Low; thin-session gap fill at limit price better than reopen print). Immaterial, disclosed |
| Leak tripwire (entry-delay +1) collapsed/graceful + non-vacuous | **PASS (graceful)** | Sec.3 tripwire table: collapse fractions 0.72-1.32 on level objects, 1.01 on grid RT mean; delay moved fill counts (-11%/-20% G legs) so the control is non-vacuous. No collapse => no fill-seam edge; also no seam-borne inflation |
| Holdout untouched | **PASS** | max emitted SourceCloseTime <= AnalysisEndUtc in all 68 cells x 3 files; fences byte-match EXP-019 lineage (QA); analysis code loads only `data/strategy_runs/EXP-020-*` + m1 bars <= fence |
| Price-primary | **PASS** | all P&L from cTrader native-order emissions; Python analysis-only |
| No experiment-local accounting | **PASS** | `check_no_local_accounting` ok on `code/` AND `analysis_code/` |
| Sec.6 plant (+2 bps/rebalance, analysis-side) detected BEFORE real read | **PASS** | NZDUSD expected shift +0.2221 bps/bar, observed +0.2221; USDCAD +0.2247/+0.2247; planted CI separates. Premium read is sensitive at the required scale |

Provenance detail (verdict-bearing columns):

| Column | Inputs & timing | <= t-1? |
|---|---|---|
| ARM R `PortWeight/Units/Cash` | decision on completed 4h close (effIdx = i-delay); market fill first tick of next bar; emitted row = post-trade state at decision close (verified by pre-trade reconstruction) | YES |
| ARM R `trade_blotter.Price` | actual engine fill (~ next bar open, 99.95%) | YES |
| ARM G `EntryFillPrice/ExitFillPrice` | resting limit/stop orders at month-anchor levels (anchor = previous calendar-month close); m1 touch fills | YES |
| ARM G censored `ExitFillPrice` | last close mark at fence (FlushGridCensored), Censored=1, RealizedBps=NaN -> analyst MTM disclosure | YES |

**Gate: OPEN. All blocking checks pass; everything below is evidence, not gates.**

---

## 2. Question list

Mandatory set + mechanism-specific. A = answered (ref), U = unanswered.

1. Per-bar/per-leg reconciliation per cell? — A: estimand gate, 68/68 pass (Sec.1).
2. P&L-bearing object matches estimand (L-16)? — A: ARM R = emitted portfolio path (per-bar premium vs twin) — matches. ARM G = round trips + censored inventory — matches, **but** the censored-inventory term dominates most cells (Sec.4.2), so the month-net object is mostly an inventory-MTM object, not a harvest object.
3. Per-leg net distribution — where does the money come from? — A Sec.4.2/4.3: realized RTs are a near-constant +g spike (median ~ g); the entire left tail is censored inventory (q01 ~ -700 to -1400 bps on MR FX).
4. Episode anatomy — A: month-episodes ~45-47/cell; grid occupancy 98-100% of bars with >=1 leg open; mean open legs 4.3-7.1 of cap 8 (Sec.4.4).
5. Concentration — A Sec.4.5: USDCAD spread loses 55% without top-3 months (+6083->+2762, still >0); GBPUSD flips sign without top-3; US2000 survives (+14.7k->+8.8k).
6. Per-year totals — A Sec.4.5: USDCAD spread 2022 = 67% of funding (fails predeclared <=60%); AUDUSD/NZDUSD 2022 strongly negative; US2000 2021-22 = 89%.
7. Per-stratum re-derivation — A: every table is per instrument; pooled/block rows disclosure only.
8. Occupancy vs design story — A Sec.4.4: "oscillation harvester" is in fact ~98-100% in-market, 10-78% of bars pinned at the 8-leg cap on MR FX — a levered, mostly-frozen inventory carrier.
9. Ann return/Sharpe/DD plausibility — A Sec.4.6: ARM R premium ~ +0.04-0.07%/yr on MR FX at 0.2-0.3x ann turnover — real-looking but economically negligible; premium maxDD 0.09-0.7%.
10. Exposure risk — A Sec.4.2: censored MR-FX legs held 3,700-5,100 4h bars (1.8-2.4 yrs) at up to -1,400 bps each; NZDUSD 100% of 2023-24 bars at cap.
11. Cost sensitivity — A Sec.4.7: USDCAD grid dies at RT cost ~30 bps (weekend ceiling 7.3); NZDUSD/AUDUSD already <=0 gross; ARM R cost drag ~1e-4-4e-4 bps/bar — never binding.
12. Control collapse fractions — A Sec.3 (delay tripwire 0.72-1.32), Sec.4.1/4.3 (twin readings continuous).
13. "What would make this wrong?" probes — A: plant (Sec.1), drift via momentum twin (Sec.4.3), top-month removal (Sec.4.5), halves split (Sec.4.5), delay twin (Sec.3).
14. Power / MDE for negatives — A: every table carries MDE; ARM R MR cells UNPOWERED at theory effect (Sec.4.1); ARM G month MDEs 83-650 bps/mo.
15. (mech) Did fills materialise at A1 implied cadence? — A Sec.4.4: NO — 5-28% of implied; cap-bind + anchor drift collapse cadence; NZDUSD grid stopped trading entirely after 2022-04-13.
16. (mech) Is realized RT mean ~ +g - costs? — A: yes: NZDUSD 64.4 vs g 60.6; AUDUSD 63.2/59.5; GBPUSD 47.7/44.6; USDCAD 39.1/36.1 (gap = favourable gap fills). No accounting artifact.
17. (mech) Is arm-level month net drift-neutral? — A: NO — BTCUSD (RW) both grids massively positive (+78k MR / +69k momentum) -> level reads are drift-carriers; only the twin spread is drift-robust.
U: none.

---

## 3. Tripwire 1 read (live vs +1-bar delay; NZDUSD, USDCAD; both arms) — collapse fractions (L-15)

| Cell | Live | Delay | Collapse frac | Read |
|---|---|---|---|---|
| R NZDUSD premium (bps/bar) | +0.0048 [-0.019,+0.029] | +0.0050 [-0.019,+0.029] | 1.04 | graceful; paired diff -0.0002 [-0.0009,+0.0005] |
| R USDCAD premium | +0.0029 [-0.0017,+0.0073] | +0.0031 [-0.0015,+0.0075] | 1.06 | graceful |
| G NZDUSD total incl MTM (bps) | -3,213 (RT +64.4, 98 legs) | -4,248 (RT +64.9, 87 legs) | 1.32 | RT object cf 1.01; total moves via fill-count/censoring luck |
| G USDCAD total incl MTM | +9,574 (RT +39.1, 322 legs) | +6,855 (RT +39.3, 259 legs) | 0.72 | RT object cf 1.01; -28% total from -20% fills — timing dilution, not seam collapse |

No collapse anywhere (RT-level objects degrade 0-1%; totals move within fill-count noise).
**No fill-seam artifact; equally, no seam-dependent edge.**

---

## 4. Findings

### 4.1 ARM R — rebalancing premium (per-bar delta log return vs never-rebalanced twin; block bootstrap, block=60)

| Sym | Blk | n bars | reb trades | gross bps/bar [95% CI] | MDE | theory* | net-comm | stress |
|---|---|---|---|---|---|---|---|---|
| NZDUSD | MR | 5,728 | 712 | +0.0048 [-0.019,+0.029] | 0.024 | 0.0077 | +0.0047 | +0.0042 |
| AUDUSD | MR | 5,732 | 714 | +0.0055 [-0.014,+0.025] | 0.019 | 0.0074 | +0.0054 | +0.0048 |
| GBPUSD | MR | 5,733 | 677 | +0.0064 [-0.009,+0.022] | 0.016 | 0.0041 | +0.0064 | +0.0062 |
| USDCAD | MR | 5,732 | 644 | +0.0029 [-0.0017,+0.0073] | 0.0045 | 0.0027 | +0.0028 | +0.0024 |
| BTCUSD | RW | 6,329 | 1,164 | +0.195 [-0.163,+0.564] | 0.36 | 0.142 | +0.187 | +0.187 |
| USDJPY | RW | 5,731 | 667 | -0.0154 [-0.065,+0.031] | 0.048 | 0.0045 | -0.0155 | -0.0156 |
| AUDJPY | RW | 5,732 | 813 | +0.0025 [-0.027,+0.033] | 0.030 | 0.0069 | +0.0024 | +0.0015 |
| GBPJPY | RW | 5,731 | 747 | -0.0097 [-0.043,+0.026] | 0.034 | 0.0051 | -0.0097 | -0.0101 |
| EURJPY | RW | 5,732 | 784 | -0.0040 [-0.029,+0.021] | 0.025 | 0.0041 | -0.0041 | n/a |
| XAUUSD | RW | 5,637 | 743 | -0.0008 [-0.022,+0.022] | 0.022 | 0.0118 | -0.0008 | -0.0010 |
| USDCHF | RW | 5,734 | 631 | +0.0045 [-0.004,+0.014] | 0.0089 | 0.0037 | +0.0044 | +0.0038 |
| EURUSD | mid | 5,674 | 684 | +0.0030 [-0.014,+0.019] | 0.017 | 0.0030 | +0.0030 | +0.0028 |
| USTEC | mid | 5,621 | 768 | +0.0042 [-0.054,+0.069] | 0.061 | 0.029 | +0.0042 | +0.0041 |
| US500 | mid | 5,720 | 829 | -0.0105 [-0.051,+0.035] | 0.043 | 0.015 | -0.0105 | -0.0107 |
| **US2000** | mid | 5,688 | 797 | **+0.0455 [+0.0121,+0.0767]** | 0.033 | 0.034 | +0.0455 | +0.0447 |
| JP225 | mid | 5,735 | 768 | +0.0067 [-0.045,+0.077] | 0.061 | 0.022 | +0.0067 | +0.0064 |

\* theory = w(1-w)*sigma^2_bar with sigma_bar = sigma12/sqrt(12) from A1 — the classical
constant-mix premium (exists for ANY volatile substrate incl VR~1; MR only boosts second-order).

Facts: (i) every MR-block CI straddles 0; **MDE > theory-size effect in all 4 MR cells** ->
UNPOWERED, not absence. (ii) Observed MR means within ~40% of theory with right sign 4/4 —
consistent with a real but tiny classical premium. (iii) Costs immaterial for ARM R
(drag <=4e-4 bps/bar). (iv) Even fully real: +0.04-0.07%/yr on MR FX (Sec.4.6) — negligible.
(v) Only CI-positive cell is US2000 (mid, disclosure), ~1.3x theory. (vi) MR-vs-RW contrast
unresolvable at this power (RW means -0.015..+0.195 span the MR means).

### 4.2 ARM G — grid: realized round trips vs censored inventory (gross; MR arm)

Realized RT mean ~ +g - costs in every cell (artifact check PASS, Q16). Total dominated by censored tail:

| Sym | Blk | legs | realized total | censored MTM | total incl MTM | month mean [CI] gross | MDE/mo |
|---|---|---|---|---|---|---|---|
| NZDUSD | MR | 98 | +5,795 | **-9,009** | -3,213 | -69.9 [-279,+105] | 209 |
| AUDUSD | MR | 105 | +6,128 | **-6,651** | -523 | -11.4 [-197,+142] | 185 |
| GBPUSD | MR | 93 | +4,055 | -3,209 | +846 | +18.4 [-113,+133] | 131 |
| USDCAD | MR | 322 | +12,264 | -2,691 | **+9,574** | **+208 [+125,+331]** | 83 |
| BTCUSD | RW | 245 | +80,994 | -2,622 | +78,371 | +1,704 [+726,+2,434] | 978 |
| USDJPY | RW | 95 | +4,536 | -17,356 | -12,821 | -279 [-872,+117] | 593 |
| AUDJPY | RW | 204 | +12,416 | -9,229 | +3,187 | +69 [-199,+316] | 269 |
| GBPJPY | RW | 203 | +10,787 | -14,858 | -4,071 | -88 [-614,+297] | 525 |
| EURJPY | RW | 259 | +12,686 | -9,003 | +3,683 | +80 [-215,+310] | 295 |
| XAUUSD | RW | 246 | +20,541 | -8,473 | +12,068 | +268 [-225,+591] | 493 |
| USDCHF | RW | 155 | +6,708 | -8,957 | -2,249 | -49 [-292,+140] | 243 |
| EURUSD | mid | 59 | +2,099 | -4,638 | -2,539 | -56 [-211,+49] | 154 |
| USTEC | mid | 158 | +20,037 | -5,939 | +14,098 | +313 [-62,+613] | 375 |
| US500 | mid | 199 | +18,836 | -6,151 | +12,685 | +276 [-78,+512] | 354 |
| US2000 | mid | 180 | +24,980 | -1,943 | +23,037 | **+501 [+364,+757]** | 137 |
| JP225 | mid | 304 | +32,840 | -14,065 | +18,775 | +408 [-242,+880] | 650 |

Survivorship magnitude (VAL-006): on NZDUSD/AUDUSD the <=8 censored legs erase 100-155% of
93-105 realized RTs. Censored MR-FX legs are 1.8-2.4-yr-old underwater longs (NZDUSD q01 leg
= -1,402 bps). Realized-only reads would be grossly survivorship-inflated; all reads incl MTM.

### 4.3 ARM G — twin spread (MR grid - momentum grid), the drift-robust read (gross incl MTM, per month)

| Sym | Blk | MR total | INV total | spread/mo [CI] | spread wo top-3 mo | 2022 share | halves (mean [CI]) |
|---|---|---|---|---|---|---|---|
| NZDUSD | MR | -3,213 | -628 | -56 [-283,+166] | -8,477 (total) | neg yr | -82 [-522,+390] / -31 [-79,+40] |
| AUDUSD | MR | -523 | **+4,279** | -104 [-271,+66] | -8,726 | -3,793 | -76 [-399,+274] / **-133 [-177,-91]** |
| GBPUSD | MR | +846 | +313 | +12 [-124,+149] | -2,481 | +1,415 | +104 [-214,+264] / -81 [-106,-62] |
| USDCAD | MR | +9,574 | +3,491 | **+132 [+43,+257]** | +2,762 (still >0) | **67%** | +184 [-16,+305] / **+80 [+17,+157]** |
| BTCUSD | RW | +78,371 | +68,997 | +204 [-801,+1,829] | — | — | drift wash |
| USDJPY | RW | -12,821 | -7,908 | -107 [-592,+368] | — | — | — |
| AUDJPY | RW | +3,187 | -2,020 | +113 [-273,+607] | — | — | — |
| GBPJPY | RW | -4,071 | -9,357 | +115 [-15,+313] | — | — | — |
| EURJPY | RW | +3,683 | +154 | +77 [-320,+444] | — | — | — |
| XAUUSD | RW | +12,068 | +6,841 | +116 [-438,+588] | — | — | — |
| USDCHF | RW | -2,249 | +4,740 | **-152 [-343,-18]** | — | — | momentum grid won on VR~1 cell |
| EURUSD | mid | -2,539 | -3,139 | +13 [-129,+127] | — | — | — |
| USTEC | mid | +14,098 | +10,573 | +78 [-258,+442] | — | — | — |
| US500 | mid | +12,685 | +3,844 | +192 [-245,+740] | — | — | — |
| US2000 | mid | +23,037 | +8,345 | **+319 [+155,+596]** | +8,791 (total) | 2021+22=89% | +501 [+96,+794] / +138 [+58,+330] |
| JP225 | mid | +18,775 | +20,632 | -40 [-706,+423] | — | — | momentum grid >= MR grid |

### 4.4 Cadence and cap-bind — the structural failure

| Sym (MR arm) | fills/mo | A1 implied | shortfall | bars at cap-8 | mean open legs | cap_skip | last new fill |
|---|---|---|---|---|---|---|---|
| NZDUSD | 2.1 | 22.2 | x0.10 | 68% (2023-24: **100%**) | 6.6 | 35,523 | **2022-04-13** |
| AUDUSD | 2.3 | 23.1 | x0.10 | 71% | 6.8 | 36,606 | 2023-02-03 |
| GBPUSD | 2.0 | 29.5 | x0.07 | 72% | 6.9 | 36,783 | — |
| USDCAD | 7.0 | 25.0 | x0.28 | 18% | 5.0 | 22,432 | 2024-08-20 (alive) |
| other 12 | 1.3-6.6 | 24.8-37.9 | x0.05-0.25 | 10-78% | 4.3-7.1 | 17k-38k | — |

Mechanism: monthly anchor + 4 levels/side + inventory carried across resets. One g-sized
trend month fills a side; unwinds require traversal back toward a *stale* anchor; the cap then
blocks new arming (`cap_skip`), and levels beyond +/-4g never exist. Fill cadence collapses to
5-28% of design-implied crossings; 3/4 MR cells cap-locked most of the band; NZDUSD executed
**zero trades for the final 2.4 years**. Sec.8 power ("well powered on fills, 4-15 RT/mo") did
not materialise: 93-322 RTs/cell vs ~1,000-1,700 implied; month MDEs 83-650 bps/mo ~ effects
under test. **ARM G as parameterised is not a functioning oscillation harvester on most cells;
it is a capped trend-inventory carrier with a small harvest side-pocket.**

### 4.5 Concentration / attribution
- USDCAD spread: top-3 mo = 55% (survives, +2,762); 2022 = 67% -> **fails predeclared <=60%
  single-year cleanliness** (EXP-018 carry lesson trigger); halves positive-positive (2nd CI
  [+17,+157]) — most internally consistent MR cell.
- GBPUSD: sign flips without top-3; 2nd-half CI-negative -> fragile wash.
- AUDUSD: 2nd-half spread CI-negative [-177,-91]; momentum twin OUTPERFORMED MR grid by 4,800
  bps — sign-flipped **against** the hypothesis.
- US2000 (mid): survives top-3 and both halves CI-positive, but 89% of funding is 2021-22.

### 4.6 Physicality (what these strategies ARE)
- ARM R is a homeopathic overlay: ann premium +0.04-0.07%/yr (MR FX), +0.69%/yr (US2000),
  +2.95%/yr (BTCUSD, CI-wash) at 0.2-2x ann turnover; premium maxDD 0.09-6.9%. Even a fully
  confirmed MR-FX premium is ~5 bps/yr on portfolio notional.
- ARM G occupies 98-100% of bars, mean 4-7 of 8 legs; risk = uncapped-adverse inventory
  (single-leg MAE to -1,400 bps; NZDUSD underwater 2021->fence). Harvest real per RT (+g) but rare.

### 4.7 Cost sensitivity
- ARM G kill-cost (RT cost where total incl MTM = 0): NZDUSD/AUDUSD <=0 (dead at zero cost),
  GBPUSD 9.5 bps, USDCAD 30.1 vs weekend ceiling 7.3 (x4 headroom) and commission 0.31;
  US2000 130 vs ceiling 3.1. Live-spread binding read BLOCKED, but surviving cells clear the
  stress ceiling comfortably; the dead cells died gross.
- ARM R: cost never material (drag <=4e-4 bps/bar at weekend ceiling).

---

## 5. Evidence FOR the hypothesis

1. **USDCAD ARM G**: month net gross +208 bps/mo CI [+125,+331] (n=47); drift-robust twin
   spread +132/mo [+43,+257]; survives commission (+9,369) and weekend stress (+7,153); survives
   top-3-month removal (+2,762); both halves positive (2nd [+17,+157]); tripwire graceful (RT cf
   1.01). The one MR-block cell that ran unsaturated (18% cap-bind, 7 fills/mo).
2. **ARM R sign pattern**: 4/4 MR gross premiums positive at ~ classical w(1-w)sigma^2 theory
   magnitude (0.6-1.6x) — the harvest channel existing at its expected (tiny) size.
3. **Realized grid RTs behave exactly as the mechanism predicts**: RT gross mean = g + 1.5-4.4
   bps in every cell; 90-98% of non-censored legs book ~ +g.
4. **No fill-seam dependence**: +1-bar delay leaves per-RT and premium objects unchanged
   (cf 1.01-1.06) — any P&L is horizon-borne, not microstructure.
5. US2000 (disclosure): both arms CI-positive (R +0.0455 [+0.012,+0.077]; G spread +319/mo
   [+155,+596], survives concentration and halves) — coherent cross-arm positive, outside MR block.

## 6. Evidence AGAINST the hypothesis

1. **The MR block does not behave as a block.** Predicted premium>costs on all 4 MR, ~-costs on
   RW. Observed drift-robust spread: NZDUSD -56/mo, AUDUSD -104/mo (2nd-half CI-neg; momentum twin
   BEAT MR by 4.8k), GBPUSD wash (+12/mo, sign-flips on top-3 removal), USDCAD +132/mo. 1/4 positive,
   1/4 sign-reversed. RW spreads span -152..+204/mo, overlapping MR entirely -> discriminating
   MR-vs-RW prediction fails.
2. **Inverted-twin sign-flip (Sec.9 SUPPORTED condition) fails everywhere, incl USDCAD**: momentum
   twin earned +3,491 gross (should bleed -f-costs). Both grids are net-long inventory objects; level
   reads drift-contaminated (BTCUSD RW: MR +78k AND momentum +69k — pure drift; that a RW level-read
   is CI-positive is the design's ARTIFACT_ALARM shape, resolved to drift only by the twin).
3. **Structural failure of the grid**: fills at 5-28% of implied cadence; 3/4 MR cells cap-locked;
   NZDUSD traded nothing after 2022-04. Mostly measured an inventory tail, not the harvest; where it
   did harvest, censored inventory erased it (NZDUSD -3,213, AUDUSD -523 incl MTM).
4. **USDCAD cleanliness fails**: 2022 = 67% of spread funding (>60% predeclared limit).
5. **ARM R decision-irrelevant even if real**: all 16 CIs straddle 0; MDE > theory in every MR cell
   (structurally UNPOWERED — Sec.8's "0.5-2 bps/bar theory" overstated the classical premium ~100x;
   correct w(1-w)sigma^2 scale is 0.003-0.008 bps/bar); ~5 bps/yr — no tradable object.
6. **2022-attribution inverted on half the MR block**: 2022 (largest realized variance, where a
   variance-harvest must earn most) is the MOST NEGATIVE year for NZDUSD (-3,399) and AUDUSD (-3,793)
   spreads — trend inventory dominated exactly when the mechanism should have paid most.

## 7. Anomalies & open questions
- **US2000 cross-arm positive** (disclosure): strongest, most robust cell on both estimands; echoes
  US2000's outlier role in EXP-016/CF-MR-005. Not registered under HYP-002's MR block — needs its own
  registered hypothesis before any counted read.
- **USDCHF twin spread CI-negative** [-343,-18]: a VR~1 cell where inversion moved the mean (both
  twins should be ~-costs under H). 1 of 16, but weakens the "spread reads harvest" interpretation.
- 2 USDCAD m1 touch anomalies (<=3.8 bps, session-gap/timestamp) — benign.
- EURJPY: no stress read (spread unpinned even at ceiling) — carried.
- Cap semantics: `cap_skip` counts pending entries toward cap (QA-noted conservative reading) —
  contributes to but does not cause cadence collapse (anchor drift does).
- Operator probe proposals (not scope changes): (a) live-session spread pin to unblock binding net
  reads (USDCAD headroom x4 the ceiling, so unlikely to flip); (b) a HYP-002b re-centring/rolling-anchor
  or unwind-refresh variant to test harvest with cap-lock removed — new design + registration;
  (c) seed-battery random-anchor control (L-19) before booking any grid claim from a single twin.

## 8. Recommended verdict (experiment hypothesis only — NOT final, NOT family)

| Stratum | ARM R | ARM G |
|---|---|---|
| NZDUSD (MR) | UNPOWERED (MDE 0.024 > theory 0.008) | WASH/UNPOWERED (gross total <0, month CI_high +105 >0) + structure-failure disclosure (cap-locked 2.4y) |
| AUDUSD (MR) | UNPOWERED | CONTRADICTED-leaning WASH (2nd-half CI-neg; twin outperformed) |
| GBPUSD (MR) | UNPOWERED | WASH (concentration-dependent sign) |
| USDCAD (MR) | UNPOWERED | CI-POSITIVE but NOT SUPPORTED per bands: fails inverted-twin sign-flip AND 2022<=60% cleanliness AND live-cost pin (blocked) |
| RW block (7) | WASH/UNPOWERED, no CI-positive | WASH; no drift-robust CI-positive (USDCHF CI-neg; BTCUSD level positivity = drift) |
| mid block (5) | US2000 CI-positive (disclosure) | US2000 CI-positive (disclosure); rest wash |

**Recommendation: NOT SUPPORTED (experiment level), with one flagged exception cell.** HYP-002 as
stated is not supported: the MR block is 1-of-4 positive on the drift-robust read, the twin sign-flip
prediction fails everywhere, MR-vs-RW does not separate, and ARM R is structurally unpowered at the
(mis-stated) design effect size. This is largely a **structure-failure result** (cap-lock/cadence
collapse), not a clean absence-of-substrate result: the design's Sec.8 fill-cadence assumptions were
off 4-20x, so for most cells the harvest question was measured at a fraction of intended power
(UNPOWERED discipline: do not book "no oscillation harvest exists" from these cells).

- Driven by: (1) twin-spread MR scoreboard 1/4 positive, AUDUSD sign-reversed; (2) inverted-twin
  sign-flip failure everywhere incl USDCAD (drift proven by BTCUSD); (3) cadence/cap-lock collapse
  making most G cells inventory bets, ARM R MDE > theory making all R cells unpowered.
- Would change if: a live-spread-pinned rerun of a cap-lock-free structure variant (rolling anchor)
  showed the USDCAD pattern on >=3 MR cells with clean attribution; or a seed-battery anchor control
  showed USDCAD's +132/mo sits above the anchor-placement null.
- Family implication for checkpoint-008 (evidence, not disposition): the EXP-019 oscillation remains
  real but this structure channel failed to monetise it at scale; surviving positives (USDCAD,
  US2000-disclosure) are single-stratum, attribution-flagged, cost-unpinned.

**Final verdict is the operator's.** Push points: the USDCAD anchor-luck question (single twin, L-19
fragility) and the US2000 cross-arm anomaly.

---

## 9. Re-run addendum (2026-07-05) — hardened `block_bootstrap_ci` (seed battery + F1 sparse fix)

Faithful re-run after `xen.evaluation` changes: F1 effective-block clamp [1,n-1] + full circular
start range (no zero-width CI on sparse strata); F2 5-seed battery, CI = median of each bound,
`ci_low_seed_range`/`ci_high_seed_range` disclosed (L-19 applied to the referee); F3
`block_sensitivity`; F4 `trimmed_mean`; F5 `CI_EXCLUDES_ZERO_PHRASE`. My analysis code consumes
`block_bootstrap_ci`/`mde`/`split_by` directly, so all §3-§7 reads were re-derived unchanged in
method. Integrity gate (§1) re-run identical (68/68 pass; plant detected +0.2221 both cells).

**Provenance for the F1 bug:** no reported EXP-020 number was a zero-width CI casualty — the
sparsest reported strata (halves splits ~22-23 months; twin spreads 44-47 months) were all above
the ≤6-event failure regime. F1 therefore does not revise any prior EXP-020 read; the changes below
are entirely the F2 seed-battery (median-of-5) effect on borderline CIs.

**Modified observations (only cells whose CI-vs-zero status or edge moved):**

| Read | Prior CI (single seed) | New CI (5-seed median) | Status change |
|---|---|---|---|
| USDCAD twin spread /mo (§4.3) | [+43.1, +257.3] | [+33.2, +245.9] | none — still CI-positive |
| **USDCAD spread half-1 (§4.5)** | [−15.8, +305.0] | **[+11.9, +373.6]** | **straddled 0 → CI-POSITIVE** |
| USDCAD spread half-2 | [+16.6, +156.7] | [+8.5, +150.6] | none — still positive |
| **US2000 spread half-2 (§4.5)** | [+58.5, +330.0] | **[−36.3, +307.1]** | **CI-positive → straddles 0** |
| US2000 spread half-1 | [+96.4, +793.9] | [+148.5, +836.0] | none — still positive |
| US2000 twin spread /mo (§4.3) | [+155.1, +596.1] | [+94.0, +561.5] | none — still CI-positive |
| USDCHF twin spread /mo (§4.3) | [−342.6, −18.2] | [−325.2, −5.9] | none — still CI-negative (now marginal, ci_high −5.9) |
| BTCUSD twin spread /mo | [−801, +1829] | [−1852, +1720] | none — still wash (wider) |
| ARM R US2000 gross (§4.1) | [+0.0121, +0.0767] | [+0.0126, +0.0794] | none — still CI-positive |
| ARM R all other 15 cells | (per §4.1) | shift <0.001 bps/bar | none |

**Net effect on the verdict: NONE.** All headline reads are stable:
- **USDCAD ARM G is marginally STRENGTHENED** — its twin spread is now CI-positive in *both*
  temporal halves (half-1 flipped positive), tightening the "internally consistent" evidence-FOR
  point (§5.1). Its NOT-SUPPORTED classification is unchanged: it still fails the inverted-twin
  sign-flip (momentum twin +3,491) and the 2022 ≤60% cleanliness (67%), and net-at-live-spread
  is still BLOCKED.
- **US2000 (disclosure) is marginally WEAKENED** — its 2nd-half spread CI now includes zero, so its
  temporal robustness is one-sided (front-loaded, consistent with the 89%-in-2021/22 attribution
  already flagged in §4.5). It remains a disclosure-block cross-arm positive, not an MR-block claim.
- USDCHF RW anomaly persists (CI-negative spread, now ci_high −5.9) — unchanged interpretation
  (§7): a single VR≈1 cell where inversion moved the mean, weakly weakening the "spread reads
  harvest" reading; not an artifact alarm (a negative RW spread is not the §9 alarm shape, which is
  a CI-*positive* RW cell — the alarm scan is still clean).
- Tripwire collapse fractions unchanged (0.72–1.32 total, 1.01 RT); §4.1/§4.2 MR-block UNPOWERED
  and cadence/cap-lock failure (§4.4) are seed-independent structural facts.

Seed-range disclosure (F2) is narrow on the load-bearing cells (e.g. general n≈100+ reads show
ci_low/ci_high seed ranges of order ±0.01 of the bound), i.e. the median-of-5 CIs above are stable
across seeds — the two status flips are genuine borderline cells sitting on zero, not seed noise.
The §8 recommended verdict (**NOT SUPPORTED, USDCAD flagged exception**) stands unchanged.
