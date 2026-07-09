# SPDR-001 — Quantification of HTF context's own conditional effect on a null (random) LTF base

> **CORRECTED 2026-07-08 (post-audit).** The original pass computed every CI on the full-sample
> overlapping per-bar estimand with block=5, while that series' autocorrelation persists to lag ≈ H
> (0.84 at lag 5 for H=48). All CIs and CI-counts on that estimand were re-derived with
> hold-matched blocks (block ≥ H) and this document was rewritten in place to the corrected values.
> Point estimates were unaffected (reproduced exactly from raw bars). Probe + audit record:
> `docs/experiments-docs/checkpoints/2026-07-08-010-htf-di-conditioning-spdr-series/correction/`.

**Role:** Xen data-analyst, fresh context. **Frame (operator-corrected 2026-07-07):** SPDR-001's
CTRL-01 base is a **random LTF entry** — a *null strategy by construction*, carrying no directional
edge of its own. That is not a weakness to apologise for: it makes SPDR-001 the **cleanest possible
isolation of higher-timeframe (HTF) context's own contribution.** Any measurable shift the HTF state
induces on this null base is HTF's effect *and nothing else* — there is no base-strategy edge to
confound it. This document therefore **quantifies HTF context as a conditioning variable**: how much
the LTF forward-return distribution *moves* as the HTF state varies, per stratum, in magnitudes with
CIs. It is **not** a worth/verdict read; the series disposition follows SPDR-003. Magnitudes, never
qualifiers.

Constraints held: TRAIN-only; causal HTF-bar-boundary via the vetted `screen_code` primitives
(`build_domain_ctx`/`map_htf_to_ltf`/`wilder_adx_di`/`regime_labels`); per-stratum
(instrument × domain-pair × variant × hold); ≥25-seed battery where randomness enters; no local P&L
accounting (L-18); no pooled headline (L-03 disclosure-only); per-stratum UNPOWERED is a power
statement (B-5); dispersion guarded against normaliser mechanics (raw-bps + fixed-long-ATR).

- Code (all reuse the causal primitives, no causality rebuilt): `analysis_code/emit_rich.py`,
  `emit_followup.py`, `emit_facets.py`, `make_plots.py`.
- Data: `results/rich_{dist,edge,dose,expo}.parquet`, `fu_thread1/2/2_dose/3_diag.parquet`,
  `facet_a_null_base.parquet`, `facet_b_htf_conditional.parquet`. Figures in `plots/`.
- CIs: block bootstrap of the mean over the time-ordered per-bar series. **Corrected:** the
  original block=5 under-blocked the overlapping H-bar forward windows (dependence length ≈ H);
  all CI-clearance statements below use **hold-matched blocks (block = H)** from the correction
  probe (`correction/dirgap_cells.csv`, `correction/sign_counts.csv`). Implementation
  `_fast_block_ci_mean` itself was validated vs `xen.evaluation.block_bootstrap_ci`.

---

## 0. Integrity gate (SPDR lane: code-asserted substitute for estimand-validation JSON)

| Check | Result |
|---|---|
| TRAIN-only fence | PASS — `load_train_1m` slices first 70%×70%; every entry+hold end < TRAIN cutoff. Screen `integrity.json` all-pass 12/12. |
| HTF-bar-boundary (anti-lookahead core) | PASS — `map_htf_to_ltf`: HTF label at LTF bar *t* = last HTF bar with `CloseTime < Open(t)`. Golden trace reproduced. |
| `t-1` causal lag / normaliser | PASS — `ltf_atr_prev = ATR[t-1]`; all indicators Wilder-causal. |
| Phase-shift control non-vacuous for the mean (L-15) | PASS — the ±500-HTF-bar roll re-assigns `htf_dir` per bar and moves the mean (§4). |
| Holdout / TEST untouched | PASS. |
| No local P&L accounting (L-18) | PASS — availability metrics on ATR-normalised open-to-open returns only. |

## 0b. Estimand and why this is the cleanest HTF isolation

The DI arm's per-selected-bar return is `htf_dir_i · m_i`, `m_i = (Open[t+H]−Open[t]) / ATR[t−1]`.
The random symmetric sign only **thins** the sample (unbiased random subset), so the full-sample,
seed-free `E[htf_dir·m | HTF state]` is exactly what the DI battery estimates, at higher power and
with no seed noise. Because the base carries `E[sign·m]=0` for any HTF state (§Facet A), every
non-zero conditional statistic below **is** HTF's own contribution — no base edge to subtract.

**Decomposition of the conditional-mean shift** (`d=E[m]`, `τ=E[htf_dir]`):
`edge = E[htf_dir·m] = τ·d + Cov(htf_dir,m)`. With balanced HTF direction (`τ≈0`, §Facet A/§1), the
between-state gap `E[m|+DI]−E[m|−DI] = 2·edge = 2·Cov(htf_dir,m)` — a pure conditioning effect.

---

## FACET A — the null (random) base object, per stratum

The base is null by construction; these magnitudes let the reader see the object HTF conditions.
Random arm over the 25-seed battery, per (instrument × domain × hold). `facet_a_null_base.parquet`.

**1. Location — mean ≈ 0 in every stratum.** Battery signed-mean spans −0.013…+0.010 ATR; the seed
2.5–97.5% band **brackets 0 in all 48 strata** (e.g. USTEC 1h/5min H48 mean +0.006, band
[−0.035,+0.043]; BTCUSD 1d/1h H96 +0.005, [−0.177,+0.207]). Median ≈ 0 (−0.05…+0.04). In bps the
signed mean is likewise ~0.
**2. Hit-rate — the null anchor.** Directional hit-rate (P(realised sign = random sign)) = **0.498–0.504**
across all 48 strata (max deviation 0.006). This is the definitional null: the random side predicts
nothing.
**3. Shape.** Symmetric (skew −0.31…+0.08, mostly |skew|<0.07). Dispersion set by horizon: forward-move
std 1.55 ATR (shortest 4h/1h H4) → 10.0 ATR (BTCUSD 1d/1h H96). Fat-tailed and growing with hold —
tail mass beyond ±2 ATR rises from 0.13 (short holds) to 0.78–0.81 (1d/1h H96).
**4. Availability-vs-random percentile ≈ 0.5.** The base mean's rank within its own random battery is
0.32–0.64 (median ~0.50) — the base sits at the middle of the random distribution, i.e. it *is* the
random reference.
**5. Failure mode = clean mode-a (no directional edge), by construction.** There is no
mis-specification to diagnose; the arm is the intended null.
**6. Horizon profile.** Only dispersion and tail mass scale with hold (√-like); location and hit-rate
stay pinned at the null across all four holds.

> The base is a verified zero-centred, symmetric, horizon-scaling null. Everything in Facet B is the
> shift HTF context imposes on *this* object.

---

## FACET B — HTF context's own conditional effect on the null base (the headline)

For each stratum: as the HTF direction state flips, how far does the LTF forward-return **mean**
move (`dir_gap = E[m|+DI] − E[m|−DI]`, ATR units, block-bootstrap 95% CI); the **sign-prediction**
magnitude (hit-rate − 0.5); and the **dispersion modulation** as the HTF vol state varies, in
**raw bps** (normaliser-guarded). `facet_b_htf_conditional.parquet`. All per-stratum; no pooling.

### B1 — Conditional-mean shift as HTF direction flips (`dir_gap`, ATR units)

| inst | domain | H12/H24/H36/H48 (or 1d/1h H24–96) | dir_gap span | CI-excludes-0 (block=H) |
|---|---|---|---|---|
| **USTEC** | 1h/5min | +0.092 / +0.226 / +0.377 / **+0.499** | grows w/ hold | **H12,24,36,48** |
| **BTCUSD** | 1h/5min | +0.093 / +0.168 / +0.232 / +0.273 | grows w/ hold | H12,24,36 (H48 marginal, [−0.010,+0.258] on the edge) |
| EURUSD | 1d/1h | +0.268 / +0.448 / +0.470 / +0.419 | ~0.27–0.47 | none (H48 edge CI [−0.167,+0.684]) — point magnitude only |
| BTCUSD | 1d/1h | −0.183 / −0.405 / −0.272 / −0.086 | negative | none (H48 edge CI [−0.736,+0.330]) |
| EURUSD | 1h/5min | −0.046 / −0.079 / −0.111 / −0.133 | negative | none (H48 edge CI [−0.212,+0.073]) |
| XAUUSD | 1h/5min | −0.034 / −0.055 / −0.076 / −0.098 | negative | none |
| XAUUSD | 1d/1h | −0.118 / −0.092 / −0.073 / −0.328 | negative | none |
| USTEC | 1d/1h | +0.040 / −0.021 / +0.127 / +0.267 | 0.02–0.27 | none |
| all inst | 4h/1h | magnitudes 0.00–0.13 | small | none |

Under dependence-matched uncertainty, the **only CI-clear conditional-mean shift is intraday
continuation**: USTEC 1h/5min at every hold (up to **+0.50 ATR** at H48) and BTCUSD 1h/5min at
H12–H36 — on a base whose own directional effect is exactly 0. Every negative (fade-signed) cell
and every 1d/1h cell has a CI including zero: those magnitudes are point estimates / power
statements (B-5), not evidence of a coupling. `dir_gap = 2×` the DI edge of §1. The USTEC gap grows
monotonically with hold (the per-bar effect is roughly constant; the ATR-unit shift accumulates over
the forward window). Plot: `plots/horizon_edge.png`.

### B2 — Sign-prediction magnitude (per-trade directional hit-rate above 0.5)

Small but structured: |hit − 0.5| = 0.00–0.03, largest at USTEC 1h/5min H48 (**+0.012**) and BTCUSD
1d/1h H96 (**−0.033**). The conditional-mean gap (B1) is large while the per-trade hit-excess is
small because the effect is **magnitude-weighted directional alignment** over the hold, not a
per-bar coin-bias — HTF direction aligns the position with the larger forward moves.

### B3 — Dispersion modulation as HTF vol state varies (raw bps, normaliser-guarded)

Ratio of high-ATR-regime to low-ATR-regime forward-move std, in **raw bps** (so the ATR normaliser
cannot manufacture it — see Thread 2): high-vol HTF state modulates raw forward dispersion by
**0.78×–1.29×**. Direction is instrument-specific: FX/gold high-vol → **larger** raw forward moves
(EURUSD 1.10–1.15×, XAUUSD 1.10–1.28×, USTEC ~1.0×); BTCUSD daily high-vol → **smaller**
(0.78–0.92×). This is the genuine (non-mechanical) magnitude of HTF vol-state's effect on the LTF
outcome spread.

> **Isolation note.** Because the base is null, B1–B3 are HTF context's effect with *zero*
> base-strategy confound — the cleanest measurement of HTF's own conditional contribution the
> programme can produce.

---

## 1. SIGN axis (DI) — decomposition of the conditional-mean shift

Pooled disclosure (L-03, not a headline): median `|edge| = 0.101` ATR, median `|Cov timing| = 0.102`,
median `|τ·d| = 0.008`. `τ ∈ [−0.07,0.00]` everywhere → the DI filter holds ~no net directional
exposure, so the drift term `τ·d` contributes ~0 and the shift is essentially all
`Cov(htf_dir, m)` — HTF direction covarying with the forward move. (This is the mechanism of the B1
gap; `plots/drift_timing_phaseshift.png` left panel.)

Plain `di` variant (full sample), edge = ½·dir_gap, block=H bootstrap 95% CI (corrected):

| inst | domain | H | n | edge | CI (block=H) | mis-aligned-HTF edge |
|---|---|---|---|---|---|---|
| USTEC | 1h/5min | 12→48 | 173k | +0.046→**+0.248** | **CI excl. 0 (+) all** (H48 [+0.083,+0.416]) | +0.009→−0.054 |
| BTCUSD | 1h/5min | 12→48 | 214k | +0.045→+0.129 | CI excl. 0 (+) H12–36; H48 marginal | −0.003→+0.033 |
| EURUSD | 1d/1h | 24→96 | 13.8k | +0.148→+0.279 | CI includes 0 at all holds | +0.012→+0.164 |
| EURUSD | 1h/5min | 12→48 | 179k | −0.022→−0.063 | CI includes 0 at all holds | +0.018→+0.120 |
| XAUUSD | 1h/5min | 12→48 | 173k | −0.017→−0.051 | CI includes 0 at all holds | −0.005→−0.063 |
| all inst | 4h/1h | any | 14–18k | −0.02…+0.06 | CI includes 0 | — |

Per-instrument count of DI-axis cells whose CI excludes zero (of 84), disclosure-only —
**corrected block=H counts** (original block=5 counts retained for the record; they were inflated
by under-blocking):

| inst | block=H positive | block=H negative | (block=5 was) | conditional-effect character |
|---|---|---|---|---|
| USTEC | **9** | **0** | 18+/4− | continuation — the only one-sided fingerprint that survives |
| BTCUSD | 9 | 3 | 20+/12− | continuation, high-vol-concentrated (§4) |
| EURUSD | 6 | 2 | 14+/15− | weak positive residue; the "domain-split" pattern did not survive |
| XAUUSD | 4 | 3 | 6+/17− | **no reliable pattern — the fade fingerprint was a block artifact** |

`plots/heterogeneity_edge.png`.

## 2. DISPERSION axis (HTF vol-state conditioning), normaliser-guarded

HTF vol regime conditions the *spread* of LTF outcomes with the mean pinned at 0. Measured in three
metrics to separate genuine forward-vol conditioning from ATR-normaliser mechanics (1h/5min, H24):

| metric | low-regime std ratio | high-regime | low÷high spread |
|---|---|---|---|
| ATR14[t−1]-normalised | 1.148 | 0.823 | 1.395 |
| slow ATR500-normalised | 0.995 | 1.033 | 0.963 |
| raw bps | 0.976 | 1.073 | 0.909 |

Decile curve (fwd-std ÷ decile-0, median across instruments): ATR14 1.00→**0.53** (monotone);
slow-ATR 1.00→**1.22**; raw-bps 1.00→**1.31**. The large ATR14 conditioning is a normaliser mechanic
(the short denominator co-moves with the HTF regime); the **genuine** vol-state conditioning of raw
forward dispersion is **+10…+31%** (high-vol HTF state → larger raw forward moves) — the B3
magnitude. `plots/fu_thread2_normaliser.png`, `plots/std_ratio_heatmap.png`,
`plots/dispersion_dose_atrpct.png`.

## 3. HORIZON

The conditional-mean shift accumulates ~linearly with hold: per-bar effect roughly constant
(≈0.007–0.011 ATR/bar for CI-clearing cells), so the ATR-unit gap grows H·(per-bar) while the
entry-fixed ATR normaliser stays put. Median edge by hold-multiple 0.12→0.24→0.30→0.28; CI width also
widens with H (0.19→0.34→…). `plots/horizon_edge.png`.

## 4. INTERACTION ADX×ATR×DI — vol state AMPLIFIES the directional effect (corrected)

BTCUSD 1h/5min, block=H CIs (`correction/atrdi_cells.csv`):

| BTCUSD 1h/5min | H12 | H24 | H36 | H48 | block=H CI-clear |
|---|---|---|---|---|---|
| `atrH_adxHi_di` (high vol, strong trend) | +0.12 | +0.23 | +0.33 | **+0.41** | **all 4 holds** (H48 [+0.175,+0.663]) |
| `atrL_adxHi_di` (low vol, strong trend) | +0.00 | −0.05 | −0.12 | −0.22 | **none** (H48 [−0.583,+0.129]) |

**Corrected read:** the high-vol branch is a genuine amplification of the continuation effect
(CI-clear at every hold, exceeding the unconditional +0.13 edge). The low-vol negative branch is a
point estimate whose CI includes zero at every hold — the original "ATR regime sets the *sign*"
claim over-read an under-blocked CI. Supported statement: **high-vol amplifies continuation;
low-vol shows no CI-clear effect in either direction.** ADX level alone is a weak conditioner of
the mean (ADX-decile → edge flat/noisy).

## 5. CROSS-DOMAIN / CROSS-INSTRUMENT heterogeneity

- **1h/5min:** densest (n 170k+); the only CI-clearing conditional-mean shifts (block=H) are the
  USTEC (all holds) and BTCUSD (H12–36) positive/continuation cells. The XAU/EUR negative
  magnitudes have CIs including zero.
- **1d/1h:** conditional-mean gaps up to ±0.47 ATR as point estimates (EURUSD +0.47, BTCUSD −0.40
  at H48), but **no 1d/1h cell is CI-clear under block=H** — a power statement, not a coupling.
- **4h/1h:** conditional-mean shift magnitudes 0.00–0.13 ATR, all CIs include zero (§Thread 3
  confirms this is structural, not a coverage artifact).

## 6. EXPOSURE

Occupancy 0.20–0.25 of bars in-market (greedy non-overlap). The DI filter removes ~half the random
entries (occupancy 0.91→0.85; trades 1476→1238 median). Because `τ≈0`, the conditional-mean shift is
not an exposure/time-in-market artifact.

## 7. POWER MAP (per-stratum, B-5)

| domain | median n (full-sample estimand) | median CI width (ATR) |
|---|---|---|
| 1h/5min | ~30,000 (up to 214k) | 0.19 |
| 4h/1h | ~2,550 | 0.34 |
| 1d/1h | ~2,230 | 0.98 |

UNPOWERED (power statement, not a negative): 1d/1h H72/96 in the sparse ATR×ADX corner cells
(CI ~1.1–1.3 ATR, n as low as ~540). The plain `di` and single-gate cells at 1d/1h carry n≈13k and
are readable. The screen's "UNPOWERED n<200" concern was an artifact of greedy+sign-agreement
thinning, not of the population estimand.

---

## 8. Threads 1–3 (attribution of the isolated HTF effect)

### Thread 1 — HTF-specific increment vs plain LTF autocorrelation
LTF-only momentum twin: `ltf_dir` = Wilder DI on the entry timeframe itself, last closed bar (no HTF).
Partial-OLS on `htf_dir` controlling `ltf_dir`, and the conflict subset (`htf_dir ≠ ltf_dir`).
**Correction caveat:** these CIs were computed under the original block=5 scheme and are understated
for the overlapping estimand; treat the point directions (USTEC HTF-specific, wins conflicts; BTC
shared with LTF momentum) as the durable content, and the CI bounds as optimistic. The
USTEC HTF-specificity direction is independently corroborated by the mis-aligned-HTF edge (§1).

| inst · domain · H | edge_htf | edge_ltf | HTF partial [CI] | HTF on conflict [CI] |
|---|---|---|---|---|
| USTEC 1h/5min H48 | +0.248 | +0.022 | **+0.253 [0.182,0.320]** | **+0.269 [0.156,0.378]** |
| BTCUSD 1h/5min H48 | +0.129 | +0.195 | +0.105 [0.047,0.161] | −0.079 [−0.174,0.006] |
| EURUSD 1d/1h H72 | +0.279 | −0.118 | +0.244 [0.008,0.468] | **+0.423 [0.109,0.779]** |
| EURUSD 1h/5min H48 | −0.063 | −0.041 | −0.061 [−0.124,−0.000] | −0.026 [−0.118,0.065] |
| XAUUSD 1h/5min H48 | −0.051 | +0.042 | −0.056 [−0.116,0.005] | **−0.109 [−0.202,−0.018]** |

Magnitudes: the isolated HTF effect is **HTF-specific** for USTEC 1h/5min and EURUSD 1d/1h (LTF-own
edge ≈0 or opposite; HTF wins conflicts, CI-clearing) — ~0.25 ATR of HTF-specific conditional shift.
For BTCUSD 1h/5min the LTF-own momentum edge (+0.20) exceeds HTF's (+0.13) and HTF does not win
conflicts, so most of the shift is shared with plain LTF autocorrelation; the HTF-specific partial is
~+0.10 ATR. XAUUSD reversion is HTF-distinct (opposes LTF momentum). `plots/fu_thread1_htf_vs_ltf.png`.

### Thread 2 — dispersion conditioning: mechanic vs genuine
See §2/B3: the 1.395 ATR14 low/high spread is ~fully a normaliser mechanic; the genuine raw-bps
vol-state conditioning is +10…+31% (opposite sign to the ATR14 shrink).

### Thread 3 — 4h/1h conditional-effect magnitude, structural read
Diagnostics: 4h map has 3.2k–4.4k HTF bars and 0.98 LTF coverage (higher than 1d/1h's 0.92); 4h
`htf_dir` flip rate 0.07–0.09 (identical to other domains). The 4h/1h conditional-mean shift is a
small point magnitude (per-bar +0.00036 ATR, vs +0.00082 at 1h/5min) over a short max hold (16 bars),
with adequate power (CI width 0.34). The small magnitude is structural (weaker 4h→1h directional
coupling × short horizon window), not a coverage/aggregation artifact.

---

## 9. Per-stratum summary of HTF conditional-effect magnitudes (no disposition)

**Directional conditional-mean shift `E[m|+DI]−E[m|−DI]` (ATR units), corrected block=H:**

CI-clearing strata (the screen's evidence):
- USTEC 1h/5min: **+0.09 → +0.50** across H12→H48, CI-clear at every hold (HTF-specific per
  Thread 1 direction + mis-aligned-edge control).
- BTCUSD 1h/5min: **+0.09 → +0.23** CI-clear H12–H36 (H48 +0.27 marginal); predominantly shared
  with LTF momentum (Thread 1) — discount as an HTF-specific effect.
- BTCUSD 1h/5min high-vol interaction: **+0.12 → +0.41**, CI-clear all holds (amplification).

Point magnitudes whose CIs include zero (power statements / not evidence of a coupling):
- EURUSD 1d/1h **+0.27 → +0.47**; BTCUSD 1d/1h **−0.18 → −0.41**; EURUSD 1h/5min **−0.05 → −0.13**;
  XAUUSD both domains **−0.03 → −0.33**; USTEC 1d/1h; all 4h/1h (structurally small);
  BTC low-vol branch **−0.22**. **No negative (fade-signed) cell is CI-clear anywhere in the
  corrected grid.**

**Dispersion conditional modulation (raw bps, high÷low HTF vol state):** **0.78×–1.29×**
(FX/gold enlarge, BTC-daily compress).

**Sign-prediction excess (hit − 0.5):** small, **±0.00–0.03**; the mean shift is magnitude-weighted,
not a per-bar coin-bias.

Because the CTRL-01 base is a verified zero-centred null (Facet A), these are HTF context's own
conditional-effect magnitudes with no base-strategy confound — SPDR-001 is the cleanest isolation of
HTF's contribution the series produces. **No disposition** — the series verdict follows SPDR-003.
