# SPDR-003 — Data-analyst quantification (stage 5, fresh-context, blind of SPDR-001/002)

> **CORRECTED 2026-07-08 (post-audit).** The Facet-B "DI conditional-mean spread" (§4.1) was
> labelled `E[m|+DI] − E[m|−DI]` but computed on the **side-signed** reversion return
> (`side·(exit−fill)/ATR`), i.e. a reversion-strategy × DI **interaction**, not a conditioning
> shift of the raw forward move. Recomputed on the correct raw-move estimand, the headline XAU
> 1d/1h H24 spread is **−0.083 [−0.68,+0.53]** (n.s., both half-splits n.s.) — not −0.857. §4.1,
> §5.2, §6 and §7 rewritten accordingly. Probe + audit record:
> `docs/experiments-docs/checkpoints/2026-07-08-010-htf-di-conditioning-spdr-series/correction/`.

**Lane:** SPDR speed-run leg 3/3 (FINAL). CTRL-03 naive-reversion LTF limit entries under HTF
context. TRAIN-only. Design: `design.md`. Analysed on this leg's own evidence only; SPDR-001/002
methodology (causal primitives) reused, no findings imported.

**No disposition.** This is a per-stratum MAGNITUDE quantification (quantify-not-qualify,
base-conditional, granular). The combined CTRL-01/02/03 series verdict is the operator's, after
this leg. Every headline below is re-derived by the analyst's own code
(`analysis_code/facets.py`) from the causal primitives — the per-trade forward-return series was
rebuilt (the screen emitted only aggregates). Cross-check: the re-derived `none`-arm means
reproduce the stage-3 `cells.parquet` baseline (e.g. EURUSD 1d/1h H24 mean −0.015, CI
[−0.329, 0.310] vs screen CI [−0.326, 0.299]).

Stratum = instrument × domain-pair × filter-variant × hold. Full magnitude tables:
`results/facetA_base_failure.{parquet,csv}` (48 base strata), `results/facetB_htf_conditional.*`
(48), `results/conditional_cells_magnitude.*` (384 instrument×domain×hold×HTF-state cells),
`results/subordinate_lift_controlC.*` (48).

---

## 1. Integrity gate (Phase 0 — blocking)

| Check | Result | Evidence |
|---|---|---|
| TRAIN fence (signal, m1 fill walk, fill+H exit all < TRAIN cutoff; 0 TEST/holdout) | PASS | `results/integrity.json` `train_fence_ok=true` ×12; `load_train_1m` = first 70% of first 70% (≈49%), `spdr001_screen.py:79-93` |
| Signal causal (limit = extreme of bars ≤ t−1) | PASS | `build_fill_table` window `sliding_window_view(...)[:-1]`, `buy_lim[b]=min(Low[b−3..b−1])`, `spdr003_screen.py:62-66` |
| Fill causal (m1 own Low/High; gap-through at m1 Open, never better than market) | PASS | `spdr003_screen.py:86-95`; golden trace G1–G3 reproduced, `integrity.json` `golden_trace.ok=true` ×12 |
| HTF boundary (context CloseTime < fill-bar Open) | PASS | `map_htf_to_ltf` strictly-less map + per-bar assertion `integrity_checks`, `spdr001_screen.py:152-157,353-355`; `htf_boundary_ok=true` ×12 |
| Leak tripwire non-vacuous + collapses on HTF claim (Control C) | PASS | phase-shift (roll HTF ±500 bars) re-assigns the DI filter set and moves the mean; the two CI-clear DI-spread strata collapse to 8.9% / 28.2% of magnitude (§4) |
| No local P&L accounting (L-18) | PASS | analyst computes ATR-/bps-normalised forward returns only; no `xen.adjudication` object, no booked P&L; availability/return stats via `xen.evaluation` |
| Holdout untouched | PASS | all reads inside the TRAIN 49% slice; TEST/holdout never loaded |

Integrity is all-pass; the emission is analysable. Everything below is evidence, not a gate.

---

## 2. Question list (all answered; § references)

1. Fill availability per stratum? → §3.0 (fill-rate 0.537–0.631).
2. Does the reversion side predict direction, per stratum? → §3.1 (hit-rate 0.443–0.558).
3. Base location: mean/median forward return (ATR + bps) + CI, per stratum? → §3.2.
4. Shape: dispersion, skew, ±2-ATR tail mass? → §3.3.
5. Does reversion-limit timing beat a matched random-timed limit? → §3.4 (Control B percentile).
6. Named base failure-mode per stratum? → §3.5.
7. Horizon profile (mean/hit vs H)? → §3.6.
8. HTF DI conditional-mean spread E[m|+DI]−E[m|−DI] + CI, per stratum? → §4.1.
9. ADX / ATR-percentile conditional-mean range, per stratum? → §4.2.
10. Dispersion modulation, normaliser-guarded (ATR[t−1] vs raw-bps vs fixed-ATR)? → §4.3.
11. Sign-prediction excess (hit−0.5) by HTF state? → §4.4.
12. Lift-over-baseline (base-confounded lens) + CI? → §5.1.
13. Control C phase-shift collapse on DI arms? → §5.2.
14. Dose-response (ADX/ATR continuous)? → §5.3 (bucketed proxy; continuous flagged as a probe).

---

## FACET A — the base reversion arm's OWN behaviour, per stratum (`none` arm)

Object: single per-trade forward return `r = side·(Open[fill+H] − FillPrice)/ATR_LTF(14)[fill−1]`,
non-overlapping greedy holds, on the unfiltered `none` arm. 48 strata (4 inst × 3 domain × 4 hold).
Full table: `results/facetA_base_failure.*`.

### 3.0 Fill availability
Fill-rate (fills / LTF bars) per instrument×domain: EURUSD 0.601–0.631, XAUUSD 0.582–0.617,
BTCUSD 0.537–0.580, USTEC 0.589–0.614 — a 3-bar-extreme trailing limit is touched on ~54–63% of
bars. Per-stratum fill counts after non-overlap: 137–676 (1d/1h), 846–3 650 (4h/1h),
3 560–16 840 (1h/5min). No stratum is empty; the 1d/1h H72/H96 corners (n = 137–230) are the
predeclared thin cells (design §6).

### 3.1 Directional accuracy
Hit-rate P[r>0] spans **0.443–0.558** across all 48 strata, median **0.508**; |hit−0.5| median
≈ 0.008. The reversion side's sign-prediction magnitude is ≤ 0.06 above chance in every stratum;
the largest deviations sit in the 1d/1h long-hold corners (BTC 1d/1h H72 hit 0.478; XAU 1d/1h H72
0.443; EURUSD 1d/1h H72 0.558) where n is smallest.

### 3.2 Location (mean vs median, ATR + bps, CI)
Median |mean_atr| across strata = **0.076 ATR**. The mean CI **excludes zero in 7/48 strata**
(magnitudes and signs both directions):

| stratum | mean ATR | CI | mean bps | hit |
|---|---|---|---|---|
| EURUSD 1d/1h H72 | +0.851 | [+0.063, +1.678] | +8.5 | 0.558 |
| USTEC 1d/1h H48 | +0.675 | [+0.038, +1.319] | +19.8 | 0.536 |
| BTCUSD 4h/1h H8 | −0.129 | [−0.238, −0.023] | −7.8 | 0.536 |
| BTCUSD 1h/5min H12 | −0.057 | [−0.101, −0.013] | −0.8 | 0.515 |
| BTCUSD 1h/5min H36 | −0.141 | [−0.278, −0.005] | −2.7 | 0.499 |
| USTEC 1h/5min H12 | −0.073 | [−0.125, −0.022] | −0.5 | 0.491 |
| USTEC 1h/5min H24 | −0.118 | [−0.224, −0.014] | −0.4 | 0.498 |

The remaining 41 strata have mean CIs including zero; magnitudes range −0.96 to +1.06 ATR (the
larger extremes are the 1d/1h thin corners). Median vs mean diverges materially in the 1d/1h
long-hold and BTC 4h strata (see §3.5).

### 3.3 Shape
Dispersion grows monotonically with H within each domain (e.g. EURUSD 1d/1h std 3.9→5.3→6.4→7.8
for H24→96; 4h/1h std 1.6→3.1). ±2-ATR **negative**-tail mass 0.19–0.44 (heaviest in the 1d/1h
long holds). Skew is small and mixed in FX/USTEC (−0.16 to +0.56) but **markedly negative in BTC
4h/1h (−0.55 to −1.18)** and BTC/XAU 1h/5min — i.e. an occasional deep adverse tail against a
positive median.

### 3.4 Availability vs random (Control B, 25-seed matched-cadence battery)
Percentile of the `none`-arm mean within the matched random-timed-limit battery spans the full
**0–100**, median **42**. The reversion-limit timing lands above the 90th battery percentile in a
few 1d/1h long-hold corners (EURUSD 1d/1h H72 = 100, USTEC 1d/1h H48 = 100, H96 = 100, EURUSD
1h/5min H12 = 96) and below the 10th in others (XAU 1d/1h H72 = 0, BTC 1d/1h H72 = 0, BTC 1h/5min
H12 = 0, USTEC 1h/5min H12/H36 = 0). The percentile is a per-stratum magnitude, not pooled — it
does not move in one direction across the grid.

### 3.5 Named failure-mode decomposition (per stratum, in the table `failure_mode` column)
- **(a) no-directional-edge (hit ≈ 0.5, mean CI incl. 0):** the modal tag; dominates the 4h/1h
  and most 1h/5min strata (hit 0.49–0.51).
- **(b) tail-eaten (median > 0, mean < median or mean < 0):** cleanest in **BTC 4h/1h all holds**
  — median +0.10 to +0.12 ATR but mean −0.03 to −0.13, skew −0.55 to −1.18 (reversion side is
  usually right, occasionally crushed). Also XAU 1d/1h H96, EURUSD 4h/1h H12.
- **(d) loss-concentration:** `worst_decile_sum_frac` is large or sign-flipping in most 1h/5min
  and 1d/1h strata — the worst 10% of trades contribute the majority of (and sometimes overturn)
  the mean; `mean_excl_worst5` flips sign vs `mean_atr` in ~half the strata (e.g. USTEC 1d/1h H48
  mean +0.675 but excl-worst5 +1.271; BTC 1d/1h H48 +0.298 → +1.247).
- **(c) horizon-decay:** see §3.6.

### 3.6 Horizon profile
Per inst×domain across H (from the 4 hold rows): mean and dispersion both rise with H; the sign of
the mean is not stable across holds in any 1d/1h instrument (EURUSD +/−, XAU decays to −0.96 at H72
then noisy, BTC turns negative H72+, USTEC oscillates). At 4h/1h and 1h/5min the per-hold means
stay inside ±0.14 ATR. Hit-rate is flat in H (≈0.50±0.03) everywhere.

---

## FACET B — HTF context's OWN conditional effect on the LTF outcome, per stratum

HTF state treated as a conditioning variable over the SAME `none`-arm fills (independent of base
viability and of the lift lens). Full table: `results/facetB_htf_conditional.*`.

### 4.1 DI-state effect — CORRECTED: strategy-conditional interaction, not a raw-move spread

**What was computed (all 48 strata, `facetB_htf_conditional.*`):** the DI-state spread of the
**side-signed reversion return** `E[side·m|+DI] − E[side·m|−DI]` — how much the reversion arm's
own performance differs between HTF-up and HTF-down states. This is a strategy × DI interaction.
It is **not** the raw forward-move conditioning spread `E[m|+DI] − E[m|−DI]` that the SPDR-001
`dir_gap` measures, and it does not by itself license a "trade against HTF direction" reading.

Original CI-clear cells on the (side-signed) interaction: XAUUSD 1d/1h H24 −0.857 [−1.54,−0.17]
(n 262/279) and USTEC 1d/1h H96 +3.454 [+1.08,+5.92] (predeclared-thin corner, n=137).

**Corrected re-derivation on the same fills** (`correction/xau_fill_probe.csv`), XAUUSD 1d/1h H24:

| Estimand | Spread | 95% CI | half 1 / half 2 |
|---|---|---|---|
| Side-signed interaction (as originally computed) | −0.857 | [−1.55, −0.15] | −0.687 n.s. / −1.049 clear |
| **Raw forward-move conditioning (as originally labelled)** | **−0.083** | **[−0.68, +0.53]** | −0.246 n.s. / −0.063 n.s. |

The raw-move conditioning spread — the estimand comparable across legs — is indistinguishable
from zero, full-sample and in both time halves. The side-signed interaction is CI-clear
full-sample but fails the first-half split: a marginal, half-unstable single cell, reportable
only as "the reversion arm performed worse under +DI in this stratum", not as HTF fade
conditioning of the forward move.

The other 46 strata: interaction magnitudes −0.341 to +1.801 ATR with CIs including zero; the
wide point magnitudes all sit in the thin 1d/1h corners with CIs spanning ±2–5 ATR.

### 4.2 ADX / ATR-regime conditional-mean range
`adx_cond_range_atr` (max−min conditional mean across the 3 ADX buckets) spans 0.002–1.68 ATR;
`atr_cond_range_atr` spans 0.02–3.48 ATR. Both ranges are largest at 1d/1h long holds where the
per-bucket n is smallest (point-estimate dispersion, not CI-backed) and smallest at 4h/1h short
holds (ranges 0.002–0.17 ATR). Per-state CI-backed magnitudes are in
`results/conditional_cells_magnitude.*`.

### 4.3 Dispersion modulation — NORMALISER-GUARDED
Ratio of max/min forward-return std across the 3 ATR regimes, per stratum, under three normalisers:

| normaliser | median ratio | max ratio |
|---|---|---|
| ATR[t−1] (design metric) | **1.37** | **2.11** |
| raw bps | 1.16 | 1.38 |
| fixed long-window ATR | 1.13 | 1.37 |

The ATR[t−1]-normalised dispersion modulation is inflated relative to the two normaliser-invariant
measures — a large share of the "vol conditioning" seen in ATR-normalised space is a **normaliser
mechanic** (dividing by ATR[t−1], which is correlated with the ATR-regime label), not forward-vol
conditioning. A residual **~1.1–1.4× dispersion modulation survives** in raw-bps and fixed-ATR
(largest at USTEC 1h/5min, 1.15/1.14 median but 1.37/1.37 tail) — a genuine but smaller forward-vol
dependence. This guard matters: reading the 2.11× ATR-normalised tail as forward-vol conditioning
would overstate the effect ~1.5×.

### 4.4 Sign-prediction excess (hit − 0.5) by DI state
Per-state |hit−0.5| ≤ 0.05 in 44/48 strata; the largest are the 1d/1h thin corners (USTEC 1d/1h
H96 +0.103 / −0.095; XAU 1d/1h H24 −0.046 / +0.041, matching its CI-clear DI spread). HTF state
shifts the LTF sign-hit by ≤ 5 pp outside the sparse 1d/1h corners.

---

## 5. Subordinate lens (base-confounded — NOT the headline)

Flagged confounded: lift-over-baseline mixes the HTF overlay with the base's own failure (Facet A);
Facet B §4 is the unconfounded read. Table: `results/subordinate_lift_controlC.*`.

### 5.1 Lift = DI-arm mean − none mean (+ CI)
CI excludes zero in a handful, all small and positive at 1h/5min: USTEC 1h/5min H24 +0.201
[+0.05, +0.35], H36 +0.240 [+0.008, +0.48], H48 +0.356 [+0.02, +0.69]; BTC 1h/5min H36 +0.219
[+0.03, +0.42]. The 1d/1h lifts carry the widest CIs (±1–3 ATR) and all include zero. This lens is
base-confounded and is not used to characterise HTF (per operator directive / lane spec).

### 5.2 Control C — HTF phase-shift collapse
For the two originally CI-clear strata the (side-signed) interaction magnitude collapses to
**8.9%** (XAU 1d/1h H24) and **28.2%** (USTEC 1d/1h H96) of its value when the HTF stream is
rolled 500 bars — the interaction, where present, is anchored to the real HTF stream (not a
fill-model artifact). Note (correction): this establishes HTF-anchoring of the *interaction*, not
of a raw-move fade conditioning — the raw-move spread is n.s. (§4.1). Across the 46
CI-including-zero strata the collapse fraction is unstable (sign-flips, |·|>1), as expected when
the underlying magnitude is itself CI-consistent with zero.

### 5.3 Dose-response
Delivered as the bucketed ADX/ATR conditional-mean ranges (§4.2). A continuous ADX / ATR-percentile
dose-response per instrument×domain was **not** computed here — flagged as a deeper probe (§6).

---

## 6. Anomalies & open questions (for the operator)

- **(Corrected)** The two 1d/1h "DI couplings" (XAU −0.857, USTEC +3.454) are side-signed
  strategy × DI interactions, not raw-move conditioning (§4.1). On the correct raw-move estimand
  the XAU cell is −0.083 n.s. (halves n.s.); USTEC H96 is a predeclared thin corner (n=137).
  The originally proposed year-split probe was run at the correction
  (`correction/xau_fill_probe.csv`): the interaction itself is half-unstable. No slow-HTF fade
  coupling is established on this leg.
- **Normaliser artifact quantified:** ATR[t−1] inflates dispersion modulation ~1.5× vs
  invariant normalisers; any downstream read of "HTF vol conditioning" must use raw-bps/fixed-ATR.
- **BTC 4h/1h tail-eaten signature** (median>0, mean<0, skew −0.55 to −1.18) is the clearest
  Facet-A failure-mode: reversion side usually right, occasionally deeply wrong.
- **Probes if pushing further:** (a) continuous ADX & ATR-percentile dose-response on XAU/USTEC
  1d/1h; (b) widen the 1d/1h thin corners via a longer TRAIN window or overlapping holds to power
  the DI spread; (c) split the XAU 1d/1h H24 coupling by year to check regime-stability.

---

## 7. Hand-off

No disposition and no series verdict — those are the operator's, after combining CTRL-01/02/03.
This leg's contribution is the per-stratum magnitude set above:

- **Facet A (base own failure):** hit-rate 0.443–0.558 (median 0.508); |mean| median 0.076 ATR,
  CI excludes zero in 7/48 (−0.14 to +0.85 ATR, both signs); named modes = no-directional-edge
  (modal) + loss-concentration + a clean tail-eaten signature on BTC 4h/1h; reversion-timing
  Control-B percentile spans 0–100 (median 42), non-directional across the grid.
- **Facet B (HTF own conditional effect) — corrected:** on the raw forward-move estimand, **no
  stratum is CI-clear** (the two originally reported cells were side-signed strategy × DI
  interactions; XAU 1d/1h H24 raw-move −0.083 [−0.68,+0.53] n.s., halves n.s.). The side-signed
  interaction is CI-clear full-sample in those 2/48 but half-unstable on XAU. Dispersion
  modulation genuine-but-modest (~1.1–1.4× on invariant normalisers after removing the ~1.5×
  ATR[t−1] normaliser inflation); sign-hit shift ≤ 5 pp outside the 1d/1h corners.

Final verdict is the operator's.
