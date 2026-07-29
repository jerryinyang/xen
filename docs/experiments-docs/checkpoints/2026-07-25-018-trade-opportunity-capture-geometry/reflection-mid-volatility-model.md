# Checkpoint 018 — Mid-checkpoint Reflection: THE VOLATILITY EVIDENCE BASE AND THE CAPTURE-GEOMETRY MODEL

- **Date assembled:** 2026-07-28 · **Revised 2026-07-28** after independent audit (§A)
- **Role:** companion to `reflection-mid.md` (assembled 2026-07-26; **SIGNED 2026-07-29, option B**).
  That document books the 017 residue and the `(p, W, L)` picture. **This one does the other half of
  design §5 Step 2: it inventories the confirmed volatility observations the programme owns, each with
  its own evidence class, and states plainly what capture-geometry model those observations support.**
- **Authority:** checkpoint-018 `design.md` §5 Step 2; SoT `.ignore/what-next/alts/opportunity.md`
  §3.2 / §4 / §6.3; chapter-06 governance.
- **Status:** **EVIDENCE INVENTORY + MODEL STATEMENT + BINDING TEST PROTOCOL for SPDR-019/020
  (§5.9, operator directive 2026-07-28).** No family action, no end-state, no gating verdict, no
  tradability claim.
- **Sources (final, not re-run):** SPDR-012, SPDR-013, SPDR-015 (checkpoint-017); SPDR-018 (crypto,
  25 Bybit perps) and SPDR-018B (cTrader replication), with addenda P02/P03 and P04; checkpoint-017
  `retrospective.md`; `corrections-log.md`. Power labels re-derived directly from
  `SPDR-018/results/arm_{A,B,C,D}.parquet` and `analyst_per_cell_magnitudes.parquet`.

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY  (cTrader: BORROWED from Bybit AND RESCALED = DOUBLY SYNTHETIC)
  implication: every money figure understates true cost; reported net is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  SPREAD: NEVER CHARGED, PROGRAMME-WIDE (operator directive 2026-07-23, evaluation-framework.md
    SSChapter-04). No quote or effective spread exists on the T1 lane and a fixed pin is not a
    substitute, so this is a STANDING EXCLUSION, not an open item awaiting a measurement. The
    caveat above travels on every record and is repeated in every report; AMENDMENT-C2 refuses
    every fully-net / cost-complete / tradable / deployable claim. Cost as a whole is additionally
    excluded from every SPDR-019/020 test by the 2026-07-28 directive (SS5.4a); the target is
    GROSS.
```

---

## A. Corrections applied 2026-07-28 (independent audit)

An independent audit of the 2026-07-28 first draft raised five items. **Four are upheld and fixed in
place; one is refuted.** No source experiment is affected — every error below was introduced by this
document, not inherited.

| # | Item | Ruling | Fix |
|---|---|---|---|
| **A1** | §5.4 wrote the free residual as `log(W/L) − 0.9408·log((1−p)/p)`, using the **fitted regression slope** | **UPHELD — critical.** The exact zero line is `log(W/L) = log((1−p)/p)` (slope **1**, intercept **0**), forced by `E[gross]=0`. Verified on the 1,413 powered cells: the **exact** residual gives median **−0.0301**, mean **−0.0356**, sd **0.0729**, **32.5% positive** — reproducing SPDR-018's reported `log R` exactly, and `log R > 0 ⟺ p > p_be` holds only for this form. The **regression** residual is centred at zero by construction (median +0.0019, mean −0.0000, **51.8% positive**) and is therefore **useless as a target**: no policy can beat it on average | §5.4 restated on the exact residual; the regression is demoted to what it is — a *descriptive* variance decomposition |
| **A2** | §2 claimed **every** row was powered | **UPHELD, and the true position is worse than the audit stated.** Of the five arm-B exit modes on crypto, `stop`, `time` and `trail` have **0 of 1,022 cells at target precision each**; only `combined` (478/1,022) and `signalflip` (401/1,022) are powered. So the headline **67× `W/L` movability rests entirely on unpowered cells** — the **powered** `W/L` span is **5.3×** (0.998 → 5.25). On cTrader all five modes have some powered cells (117/118/11/1/10) but the powered span is **5.0×** (0.823 → 4.111), not 36.4× | Every §2 row now carries an explicit **evidence class** (§2.0); V25 restated with the powered span as the headline and the full span as descriptive |
| **A3** | D2 (run-length), D7 (D1 stickiness) and the ambient-base controls were presented as powered | **UPHELD for D2 and the ambient controls; PARTLY REFUTED for D7.** D2 `run_len_mae`: **262 of 300 cells `DISCLOSURE`, 38 `UNPOWERED`, no target attaches**. Ambient-base: the source reports label them disclosure-layer. D7 `p_stay`: **60 SUPPORTED / 14 UNPOWERED / 1 NOT_RESOLVABLE** — scored and mostly supported, merely with no bps target rule | Reclassified per §2.0 |
| **A4** | "only ~3% of `W/L` remains" over-reads `R² = 0.9667` | **UPHELD as wording.** `1 − R²` is unexplained cross-cell variance, not an economic opportunity budget. Moot under the A1 fix, since the target is no longer the regression residual | §0 and §5.1 rephrased |
| **A5** | "A-IC's 165-cell figure is unconfirmed" | **REFUTED.** It reproduces **exactly**: CONFIRM band × H1 × per-symbol × all 11 models = **165 cells, 100% CI-excluding-zero, median rank IC 0.3262**. One real nuance the audit did not raise: only **68.9%** of those cells also meet parent target precision, so *CI-excludes-zero* is not the same label as *powered at target* | V1 carries both figures explicitly |

**Two further audit items are dispositions, not corrections:** P6 (018B determinism + the Bybit-guard
holdout assertion) is **skipped by operator directive 2026-07-28** and recorded as an open gap, not a
blocker; spread is reclassified per the disclosure block above - a standing programme-wide
exclusion with a travelling caveat, not a pending pin.

---

## 0. The 20-second version

We know a great deal about **how big the next move will be**, and essentially nothing usable about
**which way it goes**. That asymmetry is now measured on two asset classes, not asserted.

**What is solid.** The size of the next move is forecastable at day-scale on both H1 and H4
(rank IC ≈ 0.33, identical across all 15 tested symbols), the forecast **rescales the whole
distribution** rather than shifting its middle (top decile is 3.7× the bottom; the chance of an
extreme move goes 1.7% → 30%), volatility states are slow and sticky (13–19 bars on H1, ~94% daily),
shock is a separate fast object that decays in ~2 bars, and "will the next swing be bigger than this
one" is right ~68% of the time against a 47% base rate on never-before-scored data.

**What that buys, and what it does not.** These are *scale* facts. Scale sets both the size of wins
and the size of losses — measured, not argued: across magnitude strata the win size runs 110 → 235 bps
while the loss size runs 95 → 171 bps and the win-rate barely moves. So the honest job of every
volatility number we own is **selection and parameter scaling**, never edge creation.

**The one structural finding that constrains the whole capture branch.** Payoff asymmetry `W/L` moves
almost exactly as the arithmetic mirror of the win rate: push one, the other moves back by nearly the
offsetting amount, and the average trade does not improve. Across the powered cells `W/L` already
spans a factor of **5.3** and the mean stays on the zero line; across all cells including the extreme
one-tailed exits it spans **67×**, still on the zero line. So a capture policy's entire contribution
collapses to **one number**: how far it pushes the payoff away from that mirror.

**Therefore the model below is a scale model with a named residual target** — not an edge model. It
tells SPDR-019/020 how to set every parameter from proven inputs, and it tells them the one number
they must measure to have found anything.

**Cost is out of scope for the measurement (operator directive 2026-07-28).** Every SPDR-019/020 test
runs **gross**, so that a genuine capture effect cannot be masked by a cost floor that is itself
unpinned. This costs nothing in rigour: the residual target is a *gross* condition by construction
(`log R > 0 ⟺ p > p_be`). Cost re-enters only when a claim is made, never when a measurement is taken.

---

## 1. Rules for reading this inventory (binding)

1. **Units before magnitudes (L-21, L-50, P-21).** σ̂ is **73.00 bps** pooled TRAIN on crypto and
   **13.03 bps** on cTrader — a 5.6× difference. No bps threshold in this document crosses a universe
   boundary. State targets in σ̂ or ATR units, or re-derive per universe.
2. **Powered means powered against a block MDE (M-1)**, never an iid `2.8σ/√n` form.
3. **Powered-subset magnitudes need the three-number selection check first (L-51, P-22):**
   payoff-scale ratio powered÷excluded, sign-share differential, mean-vs-median gap in the excluded
   set. The worked failure is ten `trail` cells at +7…+23 bps drawn from 116 excluded cells averaging
   **−27.6 bps**.
4. **A magnitude-matched (M-3) percentile is uninterpretable without the comparator's own mean, its
   null quantiles and its plant curve (P-24).**
5. **cTrader is replication credibility, never power.** Its `n` is never pooled; its power counts are
   not comparable to crypto's (different precision base).
6. **Unpowered is not negative (B-5).** Items in §4 are power statements only.
7. **Medians are the headline** on every P&L-adjacent quantity (fat-tailed family); where mean and
   median disagree, both are given.

---

## 2. The volatility evidence base

"Use" names the capture-geometry job each observation is licensed to do. **cTrader is replication
credibility, never power.**

### 2.0 Evidence class — read this before any row

Rows are **not** uniformly powered. Each carries one of four classes, and the class limits what may be
built on it (audit item A2/A3):

| Class | Meaning | What it licenses |
|---|---|---|
| **[P]** | **Powered at parent target precision** — the cell clears its own block MDE (M-1) | Parameterisation, thresholds, pre-registered predictions |
| **[S]** | **Scored and SUPPORTED, but no bps target rule attaches** — a band label exists, an MDE target does not | Design inputs and ordering claims; **not** a magnitude threshold |
| **[D]** | **Disclosure layer** — emitted for context, never adjudicated | Interpretation and sanity checks only. **Never a parameter source** |
| **[U]** | **Unpowered** — measured, below target precision | Direction-of-travel only. **Never a claim, never a threshold** (B-5) |

Where a row mixes classes, the class of its **headline figure** is given and the exception is named
inline. The three most consequential reclassifications from the audit: **V14 is [D]**, **V22 is [D]**,
and **V25's 67× span is [U]** with a [P] span of 5.3×.

### 2.1 Scale — how big is the next move

| # | Observation | Magnitude | Power / evidence | cTrader | Use |
|---|---|---|---|---|---|
| **V1** [P] | **Range-based volatility level forecasts next-move size on H1 and H4** | rank IC **0.338 (H1)** / **0.301 (H4)**; re-measured in SPDR-018 at per-symbol median **0.3262**, **100% of 165 cells CI-excluding-zero** (CONFIRM × H1 × per-symbol × 11 models; **68.9% of those also meet parent target precision** — the two labels are not the same), pooled H1 **0.421–0.434** | SPDR-012 V-LEVEL (15/15 cells CI-low > 0); SPDR-018 A-IC | **IC +0.228** (R12) — replicates, smaller | The **primary scale input** ŝ for every capture parameter |
| **V2** [S] | **All model forms tie — EWMA is enough** | ridge / HAR / EWMA indistinguishable on H1/H4; HAR is the weakest and collapses at D1 | SPDR-012 V-LEVEL | — | No model zoo. Use EWMA of a range estimator |
| **V3** [S] | **Range measures beat close-to-close** | **+0.09 … +0.13 IC at D1**, level intraday; mechanism identified as window-length staleness, not an overnight or coverage effect | SPDR-012 V-MEASURE / §6 | — | Parkinson / Garman–Klass, never close-to-close RV |
| **V4** [P] | **The usable clock is day-scale, never hour-to-hour** | matched-date fit-free IC H1 **0.305** > H4 0.255 > D1 0.173; H1−D1 **+0.148 [+0.109, +0.183]**, positive in 20/20 symbols. **Within-day IC is +0.024 (H1) and −0.116 (H4)** | SPDR-012 §5.1 / §5.3 | — | Refresh the scale forecast daily-ish; do **not** expect intraday re-timing skill |
| **V5** [S] | **The forecast rescales the entire magnitude distribution** | decile 10 / decile 1 mean = **3.71** (CONFIRM H1), monotone in 9 of 9 steps; tail rate (next move > own P90) **0.017 → 0.304 = 18×**; top-vs-bottom quintile mean 2.86, median 2.93, **P90 2.92 — the three agree to two decimals** | SPDR-012 §3.3 | — | **The single most load-bearing fact for capture geometry: the object being forecast is a scale parameter.** Targets, stops and holds may all be set as multiples of ŝ |
| **V6** [P] | **The effect is homogeneous across the universe** | CONFIRM H1 **I² = 0.00**, cross-symbol sd 0.022 against a median SE of 0.024 (H4 the same) | SPDR-012 §3.4 | — | One parameterisation may be shared across the universe on H1/H4 (**not** on D1: I² = 0.79) |
| **V7** [P] | **Next-swing magnitude is forecastable (continuous)** | OOS rank IC **0.34–0.46, all 25 symbols** | SPDR-013 §7 | — | Event-scale ŝ for swing-based objects (ZigZag 2.0×ATR(14)) |

### 2.2 State — the volatility regime objects, and what they actually are

| # | Observation | Magnitude | Power / evidence | cTrader | Use |
|---|---|---|---|---|---|
| **V8** [S] | **`V-REGIME` (rolling-median split of rv20) is a slow *level* classifier** | flags ~48% of bars; mean run length **18.6 / 16.3 / 13.2 bars** (H1/H4/D1); empirical `P(HIGH\|HIGH)` **0.946 / 0.939 / 0.931**; `rv20` alone reproduces it at AUC 0.807 | SPDR-012 §3.5 | — | The **regime clock** — sets holding-period scale |
| **V9** [S] | **`V-REGIME-HMM` is a single-bar *shock detector*, not a regime model** | flags 5–13% of bars; run length **~2 bars**; `\|r_t\|` alone reproduces it at **AUC 0.95–0.98**; the two arms agree only 51–62% ≈ independence | SPDR-012 §3.5 | — | A **separate, near-orthogonal fast axis.** Never used as a regime |
| **V10** [S] | **Shock carries almost all the joint size information; the slow level adds ~14% and only when no shock just fired** | 2×2 (CONFIRM H1, next \|move\| bps): HMM-HIGH 95.0 / 94.9 regardless of the level arm; within HMM-LOW the level arm adds **+6.3 on 45.5 (+14%)** | SPDR-012 §3.5 | — | Condition on shock **first**, level second |
| **V11** [P] | **HMM HIGH−LOW next-move gap (the 017 76/83-unpowered blocker), now powered** | pooled TRAIN **D1 +180.4 [119.7, 252.1]**, **H4 +67.5 [54.7, 80.6]**, **H1 +48.0 [41.7, 54.7]**; second emitted variant set gives D1 +100.1 / H4 +34.3 / H1 +18.1 → **honest H1 range +18 to +48 bps**; per symbol H1 median **+24.7**, **97.3% CI-excluding-zero** | SPDR-018 **A1** | **+6.88 bps** (R12) — replicates in sign; scales with σ̂ | Size separation for selection |
| **V12** [S] | **Level-arm gaps are flat in relative terms across clocks** | V-REGIME gap ÷ own mean \|move\| = **0.216–0.282** on every band × clock; HMM's relative gap 0.65–0.90 (H1) | SPDR-012 §5.2 / §3.5 | — | **Every bps gap must be read against its clock's own mean**, or D1 looks 4× stronger than it is |
| **V13** [S] | **Daily level-regimes are ~94% persistent** | `p_stay` median **0.9486** CONFIRM / 0.9376 DESIGN / 0.9365 TRAIN, range 0.866–1.000, 22/25 SUPPORTED | SPDR-018 **D7** | **0.9517** (R12) | Explains D1's rare-transition problem; sets the outer bound on hold length |
| **V14** [D] | **Regime run-length is predictable only weakly, and the error is quantified** | H1 median MAE **11.95–12.00 bars** against a predicted `E[run]` of **18.9–23.1**; H4 10.9–11.3 vs 17.8–21.1. **Typical error ≈ half the quantity predicted** | SPDR-018 **D2** | 24 cells, no bps target attaches | Use `E[run]` as a **scale**, never as a timer |
| **V15** [P] | **Multi-bar volatility-state transitions beat persistence; single-bar does not** | ΔBrier vs persistence, H1: k=1 **0.0000 / −0.00049 (inert)**; k=4 **−0.0199**; k=12 **−0.1085**, 57–59% CI-excluding-zero — reproducing SPDR-015's banked −0.025 / −0.114 to within 0.006. At k=12 persistence is worse than a coin flip (0.341) and the gate beats both | SPDR-015 arm 2a (16/16 coins, CI excl 0); SPDR-018 **D5** | ΔBrier **−0.0256** (R12) | **R-MARKOV k=4/12** is the state gate. **k=1 is refused** |
| **V16** [P] | **`R-HMM-RV` as a forecaster is real but weak** | H1 ΔBrier k=1 −0.00135, k=4 −0.00595, k=12 −0.0317; 36–47% CI-excl-0 — **~one third of R-MARKOV at matched k** | SPDR-018 **D6** | — | Named comparator only; do not use as the gate |

### 2.3 Swing-size gating — the strongest positive object the programme owns

| # | Observation | Magnitude | Power / evidence | cTrader | Use |
|---|---|---|---|---|---|
| **V17** [P] | **`T-GT-CUR` ("is the next swing bigger than the current one") on 1,800 never-before-scored CONFIRM cells** | hit **0.6465 [0.6247, 0.6678]** (`ar1_threshold`), **0.6999 [0.6831, 0.7176]** (`logit_ridge`), **0.6781 [0.6589, 0.6978]** (`ridge_cont`) against a base rate of **0.4674**, n = 5,698. **All three CIs sit 16–23 points above base and do not approach it** | SPDR-018 **D8** — *"the most robust positive object in the entire run"*; SPDR-015 2b (21/21 coins × 3 models, +0.21 over base, size-rank IC ≈ 0.37) | not run separately | **The selection gate.** Take the setup when the next swing is forecast larger |
| **V18** [P] | **`T-GT-MED5` is the strongest ordinal target** | `ridge_cont` **+0.107** CONFIRM / +0.102 TRAIN / +0.096 DESIGN; hit **0.585 vs base 0.483**, 21 of 26 SUPPORTED on CONFIRM | SPDR-018 **D4** | — | Secondary gate |
| **V19** [P] | **`T-GT-MED10` resolves with a smaller, real lift (017 called it INCONCLUSIVE)** | `ridge_cont` **+0.063** / `logit_ridge` +0.058 / `ar1_threshold` +0.048 | SPDR-018 **D3** | — | Weakest of the three; model-dependent resolvability |
| **V20** [P] | **Tail exceedance lifts with the vol state** | H1 median **+0.056 (p90)** / **+0.031 (p95)**, **90.9%** of per-symbol cells CI-excluding-zero; extreme-move rate ~1.8× in the high-vol state | SPDR-018 **A2**; SPDR-012 V-TAIL | **+0.0095**, 8.3% CI-excl-0, all 72 WASH — *magnitude ~6× smaller; reported as a magnitude, **not** a refutation* | Tail-risk sizing input. Every crypto cell lands WASH because the magnitude is below the band threshold — a **quantified small effect**, not an unmeasured one |

### 2.4 How volatility enters the P&L identity — the part that constrains capture geometry

| # | Observation | Magnitude | Power / evidence | cTrader | Use |
|---|---|---|---|---|---|
| **V21** [P] | **Selection scales *both* sides of the identity** | across magnitude strata the rate is pinned in **0.4147–0.4795** while `W` runs **109.5 → 235.4 bps** and `L` runs **94.7 → 171.1**; `W/L` moves only **1.10 → 1.40** | SPDR-018 **C5** (174 powered cells) | R7 | **SoT §3.1 measured, not argued: scaling the move scales a zero.** Selection is a multiplier on an existing edge, never a creator of one |
| **V22** [D] | **Conditioning on a volatility event does the same thing** | ambient-base arm B: rate **+0.0423**, `W` **+130.2**, `L` **+87.6**, IQR **+202.3 bps** — but `W/L` **−0.174**. Arm C: rate +0.0255, `W` **−33.7**, `W/L` −0.124, Δmean **−0.318 bps** | SPDR-018 §5 (disclosure layer) | `W` +6.67, `L` +7.74, **`W/L` −0.028**, Δmean −0.053 (R7) | The event selects a bigger (or a higher-rate, smaller-win) distribution **whose terms offset**. A mean-only read calls this "nothing happened" and is wrong |
| **V23** [D] | **`mag_high` is "the decision bar was large", not "the volatility state"** | M-3 magnitude-matched: live −11.607 vs comparator −10.704, **percentile 0.46**, gap 0.90 bps | SPDR-018 §5 | live −3.402 vs −2.068, pct 0.2735 (R9) | **M-3 is mandatory** for any conditioner defined on \|r_t\| |
| **V24** [P] | **Payoff asymmetry tracks the arithmetic mirror of the rate** | **The mirror is exact, not fitted:** `E[gross]=0` forces `W/L = (1−p)/p` (slope 1, intercept 0). The **exact** residual `log R = log(W/L) − log((1−p)/p)` has median **−0.0301**, mean −0.0356, **sd 0.0729**, positive in 32.5% of cells, and **82.8%** of powered cells are indistinguishable from the mirror. *Descriptively*, a fitted regression `log(W/L) = −0.0048 + 0.9408·log((1−p)/p)` reaches **R² 0.9667** — i.e. the mirror explains ~97% of cross-cell variance in payoff asymmetry. **That R² is a variance decomposition, not an opportunity budget, and its residual is not the target** (audit A1, A4) | SPDR-018 Class B | **R² 0.9746, slope 0.9656**, sd 0.0607; **93.0%** indistinguishable (R3) — *replicates tighter, on data sharing nothing with crypto* | **The binding constraint on the whole capture branch** (§5) |
| **V25** [P] **for the 5.3× span; [U] for the 67× span** | **Exit geometry moves `W/L` enormously and the mean does not improve** | **[P]** Across the 1,413 powered cells `W/L` spans **0.998 → 5.25 = 5.3×** with the mean pinned on the zero line (`p` 0.154 → 0.503). **[U]** The headline **0.150 → 10.05 = 67×** span comes from `stop`-only (`p` 0.067, `W/L` 10.05, gross −37.9 bps), `trail`-only (`p` 0.870, `W/L` 0.150, gross −7.0) and `time` (`p` 0.4923, `W/L` **0.9993**, gross −7.50) — and **each of those three modes has 0 of 1,022 cells at target precision**. Only `combined` (478/1,022) and `signalflip` (401/1,022) are powered, and between them `W/L` runs 1.65 → 1.94 with residual `log R` −0.052 vs −0.063 | SPDR-018 Class B / B1 / B2; power labels from `arm_B.parquet` | powered span **0.823 → 4.111 = 5.0×** (all five modes have some powered cells: 117/118/11/1/10); descriptive span 0.274 → 9.975 = 36.4× (R4). **The 10 powered `trail` cells are the L-51 / P-22 selection-artifact example — do not read their magnitudes without the three-number check** | The powered statement is the one to carry: **a 5.3× `W/L` range produced no lift**. The 67× figure is direction-of-travel only. **Any 019/020 proposal must name the mechanism that puts `R > 1`** |
| **V26** [P] | **Longer holds at low thresholds push the identity toward the symmetric coin flip** | z=1.0/h=4 **+1.15 bps** (`p` 0.4761, `W/L` 1.116); z=1.0/h=12 **+2.86** (`p` 0.4999, `W/L` 1.025); z=1.5/h=12 −1.43; z=2.0/h=4 −0.52. Higher z pushes `p` down and `W/L` up; **they move against each other and the mean stays within ±3 bps of zero** | SPDR-018 **C6** (monotone, 14 powered) | — | The **dose-response of hold × threshold**, measured. Directly parameterises the SPDR-019 Active Hold Period |
| **V27** [P] | **Breach-type structure is real and sub-cost** | **E-TOUCH (+0.6 to +1.5) > E-HORIZON (−0.03 to +0.69) > E-CLOSE (−1.2 to −3.0)** — a ~3–4 bps ordering | SPDR-018 **C4** | **+0.124 / +0.158 / −0.491** — ~1/5 the spread, replicated in sign (R13) | A design input for SPDR-020's event grammar, **not** an edge |
| **V28** [P] | **Cross-universe magnitudes scale with σ̂, and so must every threshold** | σ̂ **73.00** (crypto) vs **13.03** bps (cTrader); side-derangement −12.221 (pct 0.0065) vs −2.632 (pct 0.023) — *~1/5 the magnitude on a 1/5.6-σ universe* | SPDR-018 §5; SPDR-018B R8, L-50 | — | **Every capture parameter is stated in σ̂ or ATR units** |

### 2.5 The cost floor these magnitudes are measured against

| Item | Value |
|---|---|
| Charged cost (crypto) | **13.1–16.1 bps**, pooled figure 13.540 — fees + discrete funding + allowance |
| Charged cost (cTrader) | ~2.43–2.54 bps — **doubly synthetic** (borrowed from Bybit and rescaled) |
| Spread | **NEVER CHARGED, programme-wide (2026-07-23).** Not a pending pin: no quote spread exists on the T1 lane and a fixed proxy is refused in code. Every net figure here is overstated by an unquantified amount, and that caveat travels with it |
| Deflator sensitivity (cTrader) | defensible range **0.185–0.703** (factor 3.8, ±2× on every net figure); the 0/315 conclusion clears the defensible floor by **4%** (P-25 / L-53) |

Against this floor: the largest measured volatility effect that is *usable for selection* — the
regime size gap at +18 to +48 bps on H1 — is comfortably above the cost floor **as a magnitude**, and
the largest measured *signed* effect is not: the best powered cell with a CI excluding zero is
**+8.24 bps gross → net −5.38**.

---

## 3. Do-not-use list (measured nulls; do not re-spend)

Closed at the 017 retrospective and re-confirmed by SPDR-018 where re-measured:

| Object | Why |
|---|---|
| **Calendar / session features** | SPDR-018 A4: D1 cells run at exactly **1.000 observation per date** against 6–9 dummies; median incremental R² D1 **−0.032 to −0.050**, H1 −0.0004 to −0.003, session-only on D1 exactly **0.000** in all 48 cells. *(cTrader's +0.0291 is what over-fitting looks like on 3 instruments in a TRAIN-only lane — N4, not a market statement)* |
| **k=1 next-bar volatility forecasting as a gate** | V15 — inert |
| **`R-HMM-RV` as a forecaster** | V16 — ~1/3 of R-MARKOV |
| **`R-SHOCK` as a regime** | named comparator only |
| **Close-to-close RV at D1; HAR** | V3, V2 |
| **Cross-sectional rank as a primary lever** | weakest SPDR-012 axis |
| **Unconditional / trend direction on net** | SPDR-013: 0/2940 SUPPORTED; availability ambient (`sig_over_rand` 0.95–1.03) |
| **Path-noise forecasting; the DERIVED error-dynamics layer; model-predicted-price mispricing zones** | SPDR-017: model IC ≈ 0, three destroys indistinguishable |

---

## 4. What is *not* available (power statements, never negatives)

| Item | State |
|---|---|
| **C2 — shock-conditioned MOMO** | Crypto survivor: M-3 live **+22.6 bps** vs a magnitude-matched comparator at percentile **0.95**, one-sided p = 0.05, **n = 505**, +37.1 bps above magnitude-matched bars. Grid UNPOWERED (65/1,020). cTrader: **NOT REPLICATED AND NOT REFUTED** — citable only as *"does not transport cleanly"*. **P1 skipped by operator ⇒ C2 can never be settled on this data**; books at the retrospective as terminal `NOT_RESOLVABLE`, never a refutation |
| **C3 — ordered `last_k` volatility flip** | **Terminally unpowerable in its registered form** (addendum P04): all 1,946 unresolved cells already pooled + σ̂-normalised on full TRAIN, median **81× short**; at the conditioner's own event rate (**3 events per 10,000 bars**) the median cell needs **201 years** of 25-symbol history, 88.3% need >20y. **Unpowerable, NOT refuted.** Powered C3 cells sit at gross **+0.34 bps** — a measured magnitude far below any cost floor |
| **B1 / B2 / B3** | `stop`/`trail`-only (0 of 2,044), `time` (0 of 1,022), and the positive-mean cells (**830, not the design's 125** — a premise defect in a frozen design). Their value is as `W/L`-movability evidence (V25), not as expectancy cells |
| **A3 per-symbol DESIGN** | 99–102 dates against 225 required — a property of catalog length, not of the effect. Pooled DESIGN resolves it (327–330 dates) |
| **P7 — Asia magnitude × shock interaction** | magnitude-matched **no-shock** momentum ≈ **+9.98 bps in Asia vs −1.17 in EU** on 162–184 rows. **The only genuinely new substantive object either run produced. Unregistered — must be registered before it is screened** |

---

## 5. The model, plainly stated

### 5.1 One sentence

**We can forecast the scale of the next move, and scale is a multiplier that acts on wins and losses
together; so volatility can choose *which* trades to take and *how big* to draw every exit, but on
this evidence it cannot make the average trade positive — and a capture design's entire contribution
is how far it pushes the payoff off the arithmetic mirror of the win rate, which is one measurable
number and is currently negative at the centre.**

### 5.2 The five layers

```
LAYER 0 — UNITS
  Everything in sigma-hat or ATR units. No absolute-bps threshold crosses a universe (L-50).
  sigma-hat: crypto 73.00 bps, cTrader 13.03 bps, pooled TRAIN, H1.

LAYER 1 — SCALE          s_hat(t, h) = E[ |move| over h | state at t-1 ]
  Input : EWMA of a range estimator (Parkinson / Garman-Klass)     [V1, V2, V3]
  Clock : H1 or H4. Refresh day-scale, not hour-scale.             [V4]
  Shape : the forecast rescales the WHOLE distribution -           [V5]
          mean, median and P90 all move by the same factor (2.86 / 2.93 / 2.92).
          => s_hat is a legitimate multiplier for ANY quantile-defined capture parameter.
  Reach : decile 10 / decile 1 = 3.71x; P(next > own P90) 0.017 -> 0.304.
  Scope : one parameterisation across the universe on H1/H4 (I2 = 0). NOT on D1.  [V6]

LAYER 2 — STATE          two near-orthogonal axes, in this order
  (a) SHOCK   = did the last bar just move a lot. Fast: ~2 bars, AUC 0.95-0.98 on |r_t|.  [V9]
                Carries essentially ALL the joint size information.                        [V10]
  (b) LEVEL   = is this a high-volatility period. Slow: runs 13-19 bars H1,               [V8]
                P(HIGH|HIGH) 0.93-0.95; ~94% persistent at D1.                            [V13]
                Adds ~+14% on top of shock, and only when no shock just fired.            [V10]
  Gate  : R-MARKOV at k=4 / k=12 (dBrier -0.0199 / -0.1085). NEVER k=1.                   [V15]
  Label : HMM HIGH/LOW where separating next-move SIZE matters (bigger gap: +18..+48 bps H1). [V11]
  Never : R-HMM-RV as the forecaster; R-SHOCK as a regime.                                [V16, §3]

LAYER 3 — EVENT SCALE    "is the next swing bigger than this one"
  Gate  : T-GT-CUR, hit 0.6465 / 0.6999 / 0.6781 vs base 0.4674 on CONFIRM.               [V17]
          Secondary: T-GT-MED5 (+0.107). Weakest: T-GT-MED10 (+0.063).                    [V18, V19]
  Cont. : ZigZag next-swing magnitude, OOS IC 0.34-0.46, all 25 symbols.                  [V7]

LAYER 4 — CAPTURE PARAMETERS   every one a multiple of s_hat, none a constant
  target   = a * s_hat(h)          moves W up, p down                                     [V25, V26]
  stop     = b * s_hat(h)          moves L down, p down
  hold h   <= regime run scale: E[run] 18.9-23.1 bars H1, MAE ~12 bars                    [V14]
             -> use E[run] as a SCALE, never as a timer
  size     = c / s_hat             variance and comparability ONLY, never expectancy      [SoT 4.4]
  select   = take when (T-GT-CUR fires) AND (s_hat decile is high enough)                 [V17, V21]

LAYER 5 — THE IDENTITY CONSTRAINT  (what Layer 4 cannot escape)
  E[gross] = p*W - (1-p)*L                     the identity, exact per cell
  p_be     = L / (W + L)                       GROSS break-even  <- the target under cost exclusion
  p_be_net = (L + cost) / (W + L)              disclosed reference ONLY (see 5.4a)

  THE MIRROR (exact, not fitted). On a driftless path with a fixed-horizon exit, E[gross]=0
  forces  W/L = (1-p)/p  exactly:  slope 1, intercept 0, no free parameter.

  THE TARGET (exact residual):
       log R  =  log(W/L)  -  log((1-p)/p)          [ = log( p*W / ((1-p)*L) ) ]
       R > 1  <=>  p > p_be  <=>  E[gross] > 0      an identity, not an approximation
       Measured on 1,413 powered cells: median -0.0301, mean -0.0356, sd 0.0729,
       positive in 459 (32.5%) - the SAME 32.5% that clears gross break-even, by identity.

  NOT the target - a descriptive diagnostic only:
       the FITTED regression  log(W/L) = -0.0048 + 0.9408*log((1-p)/p),  R2 0.9667
       (cTrader 0.9746) says the mirror explains ~97% of cross-cell variance in payoff
       asymmetry. Its residual is centred at zero BY CONSTRUCTION (median +0.0019, 51.8%
       positive) and can never be beaten on average. Never use it as a target. [audit A1]
```

### 5.3 What this model is licensed to claim

| Claim | Licensed? | Basis |
|---|---|---|
| "Volatility tells us **how big** the next move will be" | **Yes** | V1, V4, V5, V6, V7 |
| "It rescales targets, stops and holds coherently" | **Yes** | V5 — the whole distribution scales, not just the middle |
| "It **selects** which setups have the largest expected move" | **Yes, as selection only** | V17, V21 |
| "It tells us **which way** the move goes" | **No** | Unconditional direction dead (SPDR-013); conditional unpowered (C2/C3) |
| "Scaling the move improves the average trade" | **No — measured false** | V21: `W` 110→235 while `L` 95→171, `W/L` only 1.10→1.40 |
| "Exit geometry can manufacture expectancy" | **No — measured false on two universes** | V24, V25: a **5.3×** powered `W/L` range with no lift (67× descriptive); 0 of 1,413 and 0 of 315 clear `p_be_net` |
| "Sizing improves expectancy" | **No — refused by construction** | SoT §4.4 |

### 5.4 The one measurable target this leaves for SPDR-019/020

A capture policy's entire contribution collapses to **one number** — how far it pushes the payoff off
the exact driftless mirror:

```
  log R  =  log(W/L)  -  log((1-p)/p)          slope 1, intercept 0 - forced by E[gross]=0
  R > 1  <=>  p > p_be  <=>  E[gross] > 0      an identity
```

- Under the parents' incidental exit geometries: **median −0.0301, mean −0.0356, sd 0.0729**, positive
  in **459 of 1,413 (32.5%)** — exactly the cells that clear gross break-even, by identity.
- A designed capture policy is a **finding** if and only if it produces `log R` **reliably above zero**.
- **Resolution, not a bar (operator mandate 2026-07-28).** An earlier version of this section named
  **+0.03 to +0.07 log units** as the effect a policy must reach. Those numbers were anchored on
  `sd(log R) = 0.0729` and `median log R = −0.0301` — the **dispersion** and **location** of the
  observed residual, neither of which is a statement about what effect size *matters*. **They are
  withdrawn as thresholds.** SPDR-019/020 instead emit a **sensitivity ladder** per cell —
  `{0.02, 0.03, 0.05, 0.075, 0.10, 0.15}` log units, with the detection rate and required `n` at
  each rung — alongside the block MDE and CI width, and **no cell carries a powered / unpowered /
  `NOT_RESOLVABLE` flag**. Adequacy is the reader's judgement; powering is left to later
  verification. The design still states its block structure before it runs (M-1, SoT §7).
- **Do not substitute the regression residual.** Using the fitted slope 0.9408 produces a quantity
  centred at zero by construction that no policy can beat on average (audit A1).

### 5.4a Cost exclusion — operator directive 2026-07-28 (binding on SPDR-019/020)

**Every SPDR-019/020 test runs gross. Cost is excluded from every estimand, every threshold and every
comparison.** The reason is that failure on cost and failure of the capture mechanism are two
different failures, and charging an unpinned cost floor conflates them — a genuine capture effect
would be masked by a number we do not yet know.

This costs nothing in rigour, because **the target is already a gross condition**: `log R > 0` is
`p > p_be`, which contains no cost term. The exclusion narrows the estimand from the registered
`HYP-D6`/`HYP-D7` wording ("partial-net expectancy above the cost floor") to the gross residual, and
that narrowing needs an amendment row on the family contract before either design is signed.

**What the exclusion does not license.** It is a measurement decision, not a claims decision:

| Still binding | Because |
|---|---|
| No expectancy, tradability, deployability or cost-complete claim | SoT §7 / §8, chapter-06 governance — unchanged |
| No graduation, no XENA, no family status change | Retrospective-only authority |
| `p_be_net` still **reported** alongside `p_be` on every cell, as a disclosed reference | So Step 3 has a landing place and no one has to re-run to learn the distance |
| Spread is **never charged** and every reported net figure is overstated | The standing caveat and AMENDMENT-C2 carry that, permanently - it is not a measurement anyone is waiting for |

**One risk the designs must pre-empt.** Gross-only reads look far more positive than net ones —
**32.5% of powered cells already clear gross break-even.** That is why the mirror is the pre-registered
null: without it, a gross-only screen will re-discover the 32.5% and call it an effect. **Every capture
variant is scored against the mirror, never against zero P&L.**

### 5.5 The parameterisation this hands SPDR-019 directly

SoT §6.1's three hyperparameters, each mapped to a powered input rather than a guess:

| SPDR-019 hyperparameter | Powered input | Evidence-backed setting |
|---|---|---|
| **Delta Threshold** (ATR-normalised close-to-close gap) | already in ATR units (Layer 0); calibrate on ŝ deciles | The dose-response is monotone in 9 of 9 steps with a 3.71× top/bottom ratio (V5) — so a decile-based threshold is the natural calibration axis, not an absolute number |
| **Inactive Hold Period** (pending-order life) | shock decay | The shock object's mean run length is **~2 bars** (V9). SoT's default of 2 periods is **evidence-consistent** — record that, don't re-tune it |
| **Active Hold Period** (holding time) | regime run scale + the measured hold dose-response | `E[run]` 18.9–23.1 bars H1 with MAE ~12 (V14) sets the outer bound; C6 (V26) measures the interior: longer hold at low threshold drives `p` → 0.50 and `W/L` → 1.0 with the mean pinned within ±3 bps of zero |
| *(and, before any of the above)* | its own `p_dir`, `W`, `L`, `κ` | Must be measured **first** — SPDR-019 carries a momentum prior, so later changes are otherwise misattributed. **A zero baseline edge is a predeclared acceptable outcome, and on this evidence it is the expected one** |

### 5.6 Falsifiable predictions (so the strategies have pre-registered expectations)

The model above makes these **testable** statements. Each is a way for SPDR-019/020 to prove the model
wrong, which is the point.

1. **Scaling every capture parameter by ŝ leaves `log R` unchanged.** If a ŝ-scaled policy shifts the
   residual, the mirror is not the whole story and that is a finding.
2. **Selection on `T-GT-CUR` raises `W` and `L` together** with `W/L` moving less than ~0.3 — the C5
   signature (V21). If `W/L` moves materially more than that under selection, selection is doing
   something the C5 read did not capture.
3. **A hold of ~`E[run]` bars sits closer to `W/L` ≈ 1 and `p` ≈ 0.5 than a short hold does** (V26
   extrapolated). If not, the hold axis is not behaving like the measured dose-response.
4. **Shock-gated and level-gated selections are near-independent** (51–62% agreement, V9/V10) — so
   their effects on the identity should be close to additive. Strong interaction is new information.
5. **On cTrader every magnitude lands at roughly σ̂-ratio scale** (~1/5.6 of crypto, V28). A cTrader
   result that does *not* scale that way is either a portability defect (P-21) or a genuine
   asset-class difference — and the check distinguishes them.

### 5.7 What would change this model

- **An audited external spread source, if one ever exists.** It would be the difference between
  "misses the floor by 0.65 bps" and "nowhere close", and the cTrader deflator cannot be pinned
  without it. It is NOT a scheduled thread: spread is never charged programme-wide (2026-07-23),
  the T1 lane carries no quote data, and a fixed proxy is refused in code. Until such a source is
  acquired, the caveat stands and no money read is licensed - by rule, not by pending work.
- **Median / trimmed-mean CIs on the remaining powered cells (P2).** Already done for 451 arm-B cells:
  median CI excludes zero on **449/451**, trimmed on **451/451, all negative**, while the **mean** CI
  does so on only **46/451**. The near-break-even framing is the *only* one of the three statistics
  that fails to reject zero — so completing P2 on arm C (534 cells) and the `trail`/`stop` populations
  would make the negative read **stronger**, not weaker. It changes wording, not the identity
  conclusions (it is a mean identity).
- **CI fragility (P3) is closed** and supports every CI-based read here: seed spans ~4.8% of CI width,
  block spans 0.43–0.65 bps against 2–18 bps effects. **No conclusion in this document rests on a
  Monte-Carlo or block artifact.**
- **A registered version of P7** (Asia magnitude × shock) would add a genuinely new conditioner. It is
  currently unregistered and may not be screened first.

### 5.8 The honest caveat that keeps §5.2 falsifiable

SPDR-018/018B measured `W/L` under the **parents' own exit geometries**, not under a designed capture
policy. They show that the five geometries present in the data all sit on the zero line — and of those
five, **only two are powered on crypto** (audit A2), so the powered statement covers a 5.3× `W/L` span,
not the full 67×. They **cannot rule out** that some geometry outside this grid sits off the mirror.
What they do is **raise the bar** — the mechanism must be *named*, not searched for. That gap is
exactly what SPDR-019/020 exist to probe, provided they are framed as measurement rather than as an
edge search.

### 5.9 BINDING — layer-by-layer test protocol for SPDR-019 and SPDR-020

**Operator directive 2026-07-28. Binding on both designs; a design that combines layers before
characterising them individually is non-compliant.**

Each layer is characterised **alone**, against the same fixed signed entry, before any combination is
considered. This is the SoT §4.2 requirement ("report each predictor's individual contribution
alongside the blended score") applied to the whole stack rather than only the opportunity score.

**Two phases, both pre-declared:** **(a)** the sequential characterisation below, run in full on both
strategies; then **(b)** a full layer × device cross, *conditional on (a) being promising but with a
scope independent of which parts of (a) were promising* (§5.9.1). L5 below is the small,
evidence-selected combination step inside phase (a); it is **not** phase (b) and does not replace it.

**Phase (a) — order of execution:**

| Stage | What runs | What it must emit | Gate to the next stage |
|---|---|---|---|
| **L0 — Baseline** | The fixed signed entry, unmodulated: SPDR-019's breakout, SPDR-020's E-TOUCH/E-CLOSE event | Its own `(p, W, L, W/L, p_be, log R)` plus κ, with block CIs | **Mandatory.** Without it every later change is misattributed (the entry carries a momentum prior). A zero baseline residual is the **predeclared expected** outcome |
| **L1 — Scale alone** | ŝ used **only** to set parameter magnitudes; no state gate, no swing gate | Δ`log R` vs L0, and the full `(p, W, L)` decomposition | Report before L2 runs |
| **L2 — State alone** | Shock axis and level axis **separately**, then jointly — three cells, not one | Δ`log R` per axis; the interaction term | Their near-independence (V9/V10) is a pre-registered prediction to test |
| **L3 — Swing gate alone** | `T-GT-CUR` selection only, parameters unscaled | Δ`log R`; and the L-51 three-number selection check on every powered subset | The selection check is **mandatory**, not optional (P-22) |
| **L4 — Capture devices, one at a time** | Target, stop, hold, sizing — **each alone**, then in the declared combination | Δ`log R` per device; sizing reported on **variance only**, never on mean | Devices may not be co-varied before each is characterised |
| **L5 — Combination (phase (a) only)** | Only the combinations the L1–L4 reads justify | Term-level decomposition alongside any blended score | **A blend reported without its components is refused** (SoT §7). **L5 is evidence-selected and therefore cannot stand in for the §5.9.1 full cross** — it shares a sample with the reads that chose it |

**Inside L4, every device is tested twice:** once **unmodulated** (a fixed multiple of ATR) and once
**modulated** by each volatility layer. The unmodulated run is the comparator; the pair is what
actually measures "does volatility information improve this device", which a single modulated run
cannot separate from the device itself.

#### 5.9.1 Phase (b) — the full cross, and why it is not a winners-only combination

**Operator directive 2026-07-28.** Phase (a) above is **characterisation, not a screen.** If it
produces promising results, phase (b) runs the **full cross** — every volatility layer × every capture
device, on both strategies.

> **Binding: phase (a) results determine WHETHER phase (b) runs. They do NOT determine WHAT is in it.**

Two distinct reasons, both of which a winners-only combination would violate:

1. **Selecting the winners of (a) and then combining only those is fitting the combination to the
   same data that chose its components** — the selection and the estimate share a sample, so the
   combined read is biased upward and its CI is not honest.
2. **A layer can be flat alone and productive in combination.** Interaction is not the sum of main
   effects; a scale layer that does nothing on its own may still be what makes a state gate pay, and
   dropping it after (a) makes that permanently undiscoverable. **Individually-flat layers stay in the
   (b) grid on equal footing with the promising ones.**

**Consequences the designs must carry:**

| Item | Requirement |
|---|---|
| **Trigger** | Pre-declared **before phase (a) runs**, in the design, as a stated condition on the (a) reads. Deciding afterwards what counted as "promising" is optional stopping |
| **Scope** | **Fixed and complete** — the full layer × device cross on both strategies, independent of the (a) outcome. No layer is dropped for reading flat |
| **Estimand** | The **interaction**: `Δlog R(combined) − Σ Δlog R(individual)`, not the combined main effect. The (a) reads are the inputs that make this computable |
| **Multiplicity** | Disclosed across the full grid, per AMENDMENT-C3 (disclosed, not rationed). Cell count declared **before** the run |
| **Power** | Per-cell MDE stated in log units for the full grid up front (M-1). A grid whose cells cannot resolve the interaction is reported `NOT_RESOLVABLE`, not run and then explained |

**Rules that apply at every stage:**

1. **Score against the mirror, not against zero** — the null is `log R = 0`, and every stage states its
   MDE in log units before it runs (§5.4).
2. **Gross only** — no cost term in any estimand or threshold; `p_be_net` reported as a disclosed
   reference (§5.4a).
3. **Every parameter in σ̂ or ATR units** — no absolute-bps threshold crosses a universe (L-50).
4. **Every row carries its evidence class** (§2.0). An unpowered stage is reported as unpowered and may
   not be built on (B-5).
5. **A layer that does nothing is a result**, reported as such — the same standing as a layer that does
   something. No layer is dropped for reading flat.

---

## 6. Governance

| Item | Value |
|---|---|
| Counted TEST reads | **0** — nothing in this document reads TEST or holdout |
| Family status | `CF-VOLDIR-001` **REGISTERED**, unchanged. Transitions are retrospective-only |
| XENA | `XENA-VOLDIR-001` **RESERVED** |
| Spread | **NEVER CHARGED, programme-wide (2026-07-23).** A standing exclusion with a travelling caveat, not an open pin. Cost as a whole is excluded from the SPDR-019/020 measurement (§5.4a). Money reads, expectancy claims and Step-3 graduation stay refused by AMENDMENT-C2 and the caveat |
| Relationship to `reflection-mid.md` | Companion. That document holds the `(p, W, L)` picture, the 017-residue booking, the four decision options and the operator decision record, **signed 2026-07-29 as option B** (sequencing only: 019/020 run now, P2 arm-C and P5 in parallel; no end-state, no family action). **This document adds no options and takes no end-state decision**; it does carry two operator directives dated 2026-07-28 (§5.4a cost exclusion, §5.9 layer protocol) |
| **P6** | **SKIPPED by operator directive 2026-07-28.** 018B's determinism check and the Bybit-guard holdout assertion remain **un-run and recorded as an open gap**. No violation is evidenced; the exposure is that absence of evidence, not evidence of absence. Any future citation of 018B's §5 guard reads must carry this caveat |
| Estimand amendment | **DISCHARGED.** `HYP-D6` / `HYP-D7` were registered against partial-net expectancy above the cost floor; §5.4a narrows both to the **gross** residual `log R`. The family-contract row that executes this is **AMENDMENT-C5 (NARROWING, 2026-07-28)** in `docs/signal-registry/candidate-families/cf-voldir-001.md`, and both hypothesis rows there now read as the gross condition and cite it. *(This line previously said the amendment was named but not executed; it was executed the same day and this row was stale — corrected 2026-07-29.)* |
| Unregistered lead | **P7** — register before screening |

**No family action, end-state decision, gating verdict, tradability, deployability, cost-complete,
graduation or XENA claim is made or implied by this document. The mid-checkpoint reflection does not
close the checkpoint on a null rate (design §5 Step 2).**
