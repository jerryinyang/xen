# Results — EXP-089 (CF-MR-001 Mean-Reversion Entry Availability Screen, Phase 020)

**Run interpreted:** the **amended** run (`D0-amendment-001`: causal MR-tempo cap; regime-matched +
horizon-matched control; leg-2 retired; 6 single-test sub-screens). The first run was a deviation (audit
C-1/C-2), voided and deleted.
**Status:** `SCREEN_DELIVERED`. **Provisional disposition (NON-BINDING — pending G-020): `ADMITTED`.**
**This is an availability screen, not a tradability/edge/P&L claim** (no exits, gross, TRAIN-only, 0 candidate
slots, 0 counted TEST reads). The binding admit/exonerate is **G-020**; everything below is NON-BINDING input.

---

## 1. Headline

The bare RSI-2 mean-reversion (fade) entry shows **signal-conditional favourable availability** — favourable
excursion beyond a count- and direction-matched random control — on a clear majority of member cells, well
above the multiplicity-adjusted noise ceiling.

| Statistic | Value |
|---|---|
| `S_fam` (joint max over 6 sub-screens) | **28** |
| `S*` (Q95 joint permuted-axis null) | **7** |
| axis permutation-p | **≈ 0.0002** |
| FWER band {0.025, 0.05, 0.10} | ADMITTED at all three (S* = 7/7/6) |
| MC stability (1000 vs 5000) | stable (S* 6↔7, p ≈ 0.001↔0.0002; no routing flip) |
| **Driving lever (argmax)** | **CORE** — the bare fade (z = 17.3) |

Determinism, reconciliation (count/direction/regime-membership), TRAIN-only fence, real-price discipline, and
the GREEN single-test bite (`f01a000b…`, recorded sha == expected) all hold (audit §Headline).

## 2. Per sub-screen (per-stratum; pooled S is disclosure, not a verdict)

| Sub-screen | S | powered | reading |
|---|---|---|---|
| **CORE** (bare RSI-2 fade) | **28** | 46 | the lever — favourable availability beyond matched random |
| CORE-VOL-LOW | 22 | 46 | passes, but no more than CORE |
| CORE-VOL-MED | 25 | 46 | passes, but no more than CORE |
| CORE-VOL-HIGH | 20 | 46 | passes, but no more than CORE |
| CORE+TREND | 0 | 46 | edge destroyed by trend agreement |
| CORE+FILTER | 1 | 29 | edge destroyed by momentum agreement |

**The lever is the entry mechanism, not the regime partition.** The three `/VOLREGIME` sub-screens pass
**uniformly** (22 / 25 / 20) with flat, small per-cell `Δ̂_rand` medians (LOW 0.050, MED 0.080, HIGH 0.045 ATR)
— statistically indistinguishable from CORE's own 0.060. The volatility regime — the second "new lever" the
family was opened on — **adds nothing the unconditioned entry does not already have**: conditioning on LOW/MED/
HIGH neither raises nor concentrates the availability. argmax = CORE formalizes this: the bare fade is what
clears the bar.

## 3. Where the availability lives — a frequency (timeframe) gradient

The pooled S = 28 is **predominantly a 15m/1h phenomenon** and must be read per domain (LESSON-001):

| Domain | CORE cells passing | per-cell `Δ̂_rand` median (ATR) |
|---|---|---|
| 15m | **16 / 16** (universal) | 0.085 |
| 1h | 11 / 16 | 0.072 |
| 4h | **1 / 14** | 0.002 (≈ 0) |

The passing cells span **all 16 instruments** (no single market drives it), but the effect is monotone in bar
frequency: near-universal intraday, moderate at 1h, **absent at 4h**. This is consistent with short-horizon
mean reversion being a higher-frequency effect that washes out as the bar coarsens. A "works at all timeframes"
reading is **not supported**; the honest claim is *favourable availability for the RSI-2 fade at 15m and 1h*.

## 4. Effect size, horizon, and mechanism

- **Magnitude:** CORE median signed favourable excursion ≈ **0.75 ATR** vs ≈ 0.69 ATR for the matched random
  control → per-cell `Δ̂_rand` ≈ **0.06 ATR** (median), positive in ~87% of cells, clearing the one-sided lower
  bound in 28/46. Modest in absolute terms — this is *availability*, the raw room for a favourable move, not a
  captured return.
- **Horizon:** the realized MR-tempo cap is **~3 bars** (cap median 3–4; 77% at the `FLOOR=3`; `CAP_MAX=40`
  never binds). The RSI-2 reversion-to-neutral median is ≤3 bars — the family is **genuinely short-lived**, as
  expected for a fast oscillator fade. The availability above is therefore *favourable excursion within ~3 bars
  of the extreme*.
- **Mechanism:** after an RSI-2 extreme, price reverts favourably over the next few bars more than from a
  random-timed, direction-matched entry — the documented short-horizon reversion bounce.
- **The result is conservative.** The endpoint divides excursion by entry-bar ATR; RSI-2 extremes occur after
  sharp moves and carry elevated entry ATR, which *deflates* signal `MFE/ATR` and biases the test **against**
  the signal. The positive CORE result survives that headwind.
- **Corroboration from the variants:** imposing trend agreement (`Close>EMA20`) or momentum agreement
  (`RSI5>50`) on the fade — both of which contradict the oversold/overbought entry — collapses the edge to
  noise (S = 0, 1). A spurious result would not respond this cleanly to mechanism-negating filters.

## 5. Anchoring to the pre-defined interpretation guide

- **`SCREEN_DELIVERED`** — met: all gate inputs produced for 6 sub-screens × 46 cells; determinism +
  reconciliation pass; holdout untouched.
- **Provisional `ADMITTED (NON-BINDING — pending G-020)`** — met: `S_fam = 28 > S* = 7` and axis perm-p ≈
  0.0002 ≤ 0.05, robust across the FWER band. Per the guide, the **CORE drive** ⇒ the lever is **bare
  mean-reversion (leg 1)**, *not* a vol regime (the regime sub-screens add nothing) and *not* a variant (they
  kill it). G-020 would open the **bare RSI-2 fade** first, and — per §3 — at **15m/1h**.
- **D2a context (descriptive):** CORE and the three regimes all land in the coin-flip band [17,29]; this is the
  *count of cells beating random*, far above the beats-random noise ceiling (Q95 ≈ 5) — i.e. not coin-flip
  behaviour, a genuine majority signal. The variants sit below the band (dead-by-absence, **not** exonerated).

## 6. Confounds resolved (why this run supersedes the deviation)

The first run's provisional `ADMITTED` was an artifact driven solely by CORE-VOL-LOW (audit C-1/C-2). Under the
amendment both confounds are **empirically** removed:

| | Deviation (voided) | Amended |
|---|---|---|
| Regime `Δ̂_rand` LOW/MED/HIGH | +0.55 / ≈0 / −0.52 (symmetric ladder) | 0.050 / 0.080 / 0.045 (flat) |
| Driver | CORE-VOL-LOW only (z = 115) | CORE (z = 17.3); regimes uniform |
| Cap median | ~30–100 bars (trend) | 3–4 bars (MR) |

The collapse of the regime ladder to flat, and the flip of the driver from a single regime to the bare entry,
are exactly what removing the entry-ATR normalization confound (regime-matched control) and the trend-length
horizon (MR-tempo cap) predict.

## 7. Limitations and uncertainty (honest)

- **Availability ≠ capturable edge.** This screen has **no exit, no stop, no target, no cost**. ~0.06 ATR of
  favourable median room over ~3 bars says the raw material exists; it does **not** say a tradable, after-cost
  edge exists. Capture geometry is a separate, later phase.
- **Short horizon.** The effective ~3-bar window means any capture mechanism must act fast; slippage/cost will
  bite hardest exactly here.
- **4h absent.** The effect does not survive to 4h — the family is intraday.
- **Gross, TRAIN-only, in-sample-to-the-analysis-set.** No TEST/holdout read; nothing here is an out-of-sample
  claim. The provisional disposition is NON-BINDING; G-020 adjudicates.
- **Single endpoint.** Directional location (`MFE_med`) only; no magnitude/tail read (out of scope —
  directional family).

## 8. Suggested follow-ups (NEW scopes only — not extensions of EXP-089)

These are candidate directions for G-020 / a future phase **if** CF-MR-001 is admitted; none modifies this
experiment:

1. **Capture-geometry / exit phase for the bare RSI-2 fade** (the admitted lever): does the ~0.75-ATR / ~3-bar
   favourable availability survive an actual exit rule (RSI-revert / fixed-bar / barrier) net of cost? This is
   the availability→tradability step and the natural next scope on admit.
2. **Frequency boundary scope:** characterize the 15m→1h→4h decay (and sub-15m if data permits) to locate where
   the fade availability dies — a focused per-domain study, not a re-run.
3. *(Registered-but-deferred, require a dated amendment / slot decision):* the 25/75 regime scheme, the
   contrarian arm, and regime×variant cross-cuts — but note the regime partition added nothing here, so the
   vol-regime lever is a **low-priority** follow-up on this evidence.

---

**Bottom line (NON-BINDING):** the RSI-2 mean-reversion fade has real, multiplicity-robust favourable
availability at 15m/1h across all instruments, driven by the **bare entry** (the vol-regime partition is inert
and the trend/momentum variants are counter-productive), over a genuinely short ~3-bar horizon, measured
conservatively. The provisional `ADMITTED` is credible input to G-020, which adjudicates the binding
admit/exonerate and (on admit) would open the bare fade, intraday, first.
