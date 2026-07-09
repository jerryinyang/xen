# SPDR-001 — Screen summary (HTF context on CTRL-01 random LTF entries)

> **CORRECTION 2026-07-08 (post-audit).** Statistics in this summary that rely on the screen's
> original CI machinery are superseded where they conflict with the corrected `analysis.md` and the
> Phase-010 checkpoint `correction/` (hold-matched blocks; SPDR-003 estimand relabel). This file is
> subordinate to `analysis.md`; read that first.

**Lane:** SPDR speed-run (TRAIN-only availability, quantification-only). Design: `design.md`.
Full characterisation + all magnitudes/CIs/dose-response/heterogeneity: **`analysis.md`** (the
deep record; this file is its neutral summary). Data: `results/cells.parquet`,
`results/rich_{dist,edge,dose,expo}.parquet`. Figures: `plots/`.

> **History note.** An earlier version of this file recommended NOT_WORTH and attributed the DI
> effect to "drift capture on trending instruments." Both are **retracted** (τ≈0 → no drift to
> capture; see below). A second correction, from the thread-2 follow-up: the HTF-vol→dispersion
> effect this summary first promoted as "strongest" is **~100% an ATR-normaliser mechanic**, not
> forward-vol prediction — also retracted. This summary is quantification-first and carries **no
> disposition** — measured magnitudes only; interpretation/routing is the operator's.

**Task framing.** Quantify the *magnitude and shape* of the effect HTF context (ADX strength, DI
direction, ATR vol regime) has on LTF random entries — not adjudicate "better." CTRL-01's random
symmetric sign makes E[sign·return]=0 under any *gating* filter, so gating moves only the
*distribution shape*; only the DI (sign-conditioning) filter can move the *mean*.

**No disposition here.** SPDR-001 is one leg of the CTRL-01/02/03 speed-run; the candidate
verdict is taken only **after SPDR-003** (operator directive). This file documents SPDR-001
findings + recommendations for that later decision.

---

## Bottom line (established, from the rich re-emission — the binding read)

The mean-only aggregate (`cells.parquet`, the `fwer_notable` framing) is **superseded** — it was
thinned and mean-blind; the binding reads below come from the full-sample re-emission
(`analysis.md` + threads 1–3). What survives:

1. **A genuine, HTF-specific incremental directional coupling on 2 of 4 instruments** — HTF
   direction predicts LTF forward sign *beyond* what LTF-own momentum explains:
   **USTEC 1h/5min** +0.25 ATR @H48 (conflict-subset +0.269 [0.156, 0.378]); **EURUSD 1d/1h**
   +0.28→+0.42 (conflict +0.423 [0.109, 0.779]). τ≈0 ⇒ not drift; alignment-dependent.
2. **ATR regime flips the sign** of the DI effect (real triple interaction).
3. **Nulls that held:** dispersion "effect" = ATR-normaliser mechanic (not forward-vol
   prediction); BTCUSD lead = mostly plain LTF momentum; **4h/1h structurally dead**; pooled
   cross-instrument edge ≈0 (heterogeneity, L-03).

**Recommendations for the post-SPDR-003 verdict:** (a) the USTEC/EURUSD incremental coupling is
the only CTRL-01 signal worth carrying forward — narrow, small, pre-cost; (b) it needs cost +
drift-matched controls + a wider (FX-basket) breadth check before any cTrader graduation; (c)
CTRL-01 is the weakest vehicle (random timing) — SPDR-002 (momentum) is the stronger test of
whether HTF context modulates a *real* LTF signal.

Everything below is the detailed measurement record; the retracted first-pass reads are kept
only as a correction trail.

Scope: 4-core (EURUSD, XAUUSD, BTCUSD, USTEC) × {1d/1h, 4h/1h, 1h/5min} × holds {1–4}×ratio × 20
filter variants = 960 cells. TRAIN block (first 49%, 2021-06→~2023-11). Integrity **all-pass**
(TRAIN fence, HTF-bar-boundary anti-lookahead, t-1 lag, non-vacuous phase-shift, no local P&L).

---

## Estimand correction (why numbers differ from the retracted version)

The random sign only *thins* the DI arm to an unbiased ~half-sample. The primary read is therefore
the **full-sample population estimand** `E[htf_dir·m | regime]` (m = ATR-normalised open-to-open
forward move), high-power and seed-free; the seed battery governs only the greedy exposure axis.
Consequence: cells the retracted version called "UNPOWERED n≈20–60" carry **n≈540–16,700** — that
power objection was an artifact of greedy+sign-agreement thinning, not the estimand.

**Drift-vs-timing split** (`edge = τ·d + Cov(htf_dir, m)`): pooled over 336 DI cells, median
|edge| 0.101 ATR, median |timing Cov| **0.102**, median |drift τ·d| **0.008**. τ≈0 everywhere →
the DI mean shift, where present, is **~100% timing/covariance** (HTF direction predicting LTF
forward *sign*), sitting above a direction-matched coin-flip twin — not drift.

---

## Measured effects (magnitudes, with uncertainty)

**1. HTF vol regime → LTF dispersion — RETRACTED as a genuine effect (normaliser mechanic).**
The ATR[t-1]-normalised forward-move std conditions strongly on HTF vol (LOW÷HIGH spread 1.40,
monotone to 0.53× across deciles) — but re-run in **raw bps** or with a **slow 500-bar ATR that
can't sync with the regime**, the spread collapses to **0.91 / 0.96** (flat/slightly rising). So
~100% of the conditioning is the ATR[t-1] denominator mean-reverting with the regime, not the HTF
bar predicting LTF forward volatility. Genuine forward-vol residual is small and opposite-signed.

**2. HTF direction → LTF forward sign (covariance/timing, τ≈0 so NOT drift; instrument/domain-
SIGNED).** Dense, CI-excludes-zero, pooling washes it (L-03). Thread-1 decomposition vs a
same-domain **LTF-only momentum twin** (Wilder DI on the entry timeframe) separates the
HTF-specific increment from plain LTF autocorrelation:

| inst / domain | naive DI edge (ATR, ~H48) | HTF-specific? (conflict-subset edge, CI) |
|---|---|---|
| **USTEC 1h/5min** (continues) | +0.25 | **~fully HTF-specific** — conflict +0.269 [0.156, 0.378] |
| **EURUSD 1d/1h** (continues) | +0.28 (H72 +0.42) | **~fully HTF-specific** — conflict +0.423 [0.109, 0.779]; LTF sign-corr 0.06 |
| BTCUSD 1h/5min (continues) | +0.13 | **mostly plain LTF momentum** — LTF edge +0.20 > HTF; HTF loses the conflict subset (≤0) |
| XAUUSD 1h/5min (reverts) | −0.05 | partly distinct — H48 −0.109 [−0.202, −0.018] |
| EURUSD 1h/5min (reverts) | −0.06 | shared / marginal w/ LTF |

CI-excludes-zero cell counts (of 84): USTEC 18+/4−, BTCUSD 20+/12−, EURUSD 14+/15−, XAUUSD 6+/17−.

**3. ATR×DI interaction flips the sign** (more than additive). BTCUSD 1h/5min H48: high-vol strong-
trend `atrH_adxHi_di` **+0.41** vs low-vol strong-trend `atrL_adxHi_di` **−0.22** — same instrument
& ADX bucket, opposite vol regime → HTF-direction effect reverses. ADX alone is a weak/non-monotone
mean lever; it only selects continue-vs-fade once conditioned on ATR regime.

**4. Horizon.** DI edge accumulates ~linearly (~0.007–0.011 ATR/bar, roughly constant); most of the
ATR-unit growth with H is mechanical accumulation against a fixed entry-ATR normaliser, not the
signal sharpening (CI width widens in step). Median edge 0.12→0.24→0.30→0.28 across 1×–4×.

**5. Phase-shift (Control B).** A ±500-HTF-bar roll **collapses or reverses** every aligned edge
(median reduction 1.13, i.e. crosses zero) → the coupling is HTF-alignment-dependent, not a static
bias or leak.

**6. Domain structure.** Coupling present at the **fastest (1h/5min)** and **slowest (1d/1h)** pairs;
**4h/1h is a STRUCTURAL powered dead zone** (thread-3 confirmed, not an artifact): 4h map has more
HTF bars (3.2k–4.4k) + higher coverage (0.98) than 1d/1h which *does* produce edges; flip rate
(~0.07–0.09) matches other domains; DI edge is a genuinely small point estimate (−0.02…+0.06 ATR)
with adequate power (CI ~0.34) — per-bar effect ~half of 1h/5min, compounded by the short 16-bar
max hold.

**7. Exposure.** DI filter drops ~half the raw entries (occupancy 0.91→0.85); τ≈0 → the mean shift
is not an exposure/time-in-market artifact.

---

## Established vs within-noise vs unpowered (post follow-up)

- **Established** (CI excl. 0, dense, phase-shift-consistent, HTF-specific): **HTF direction
  predicts LTF forward sign as a genuine increment beyond LTF-own momentum** on **USTEC 1h/5min**
  (+0.25 ATR @H48) and **EURUSD 1d/1h** (+0.28→+0.42); alignment-dependent (phase-shift reverses);
  ATR-gated sign flip (3) real. τ≈0 → not drift.
- **Reclassified / retracted:** the HTF-vol→dispersion effect (1) is a normaliser mechanic, not a
  forward-vol prediction; the BTCUSD directional "lead" is **mostly plain LTF momentum**, not HTF.
- **Within-noise** (≈0, not refutation): **4h/1h structurally dead** (powered null); cross-
  instrument *pooled* DI edge; ADX level as a *mean* dose lever.
- **Unpowered** (power statement): 1d/1h H72/96 sparse ATR×ADX corners (n~540, CI ~1.1–1.3 ATR).

## Open threads — RESOLVED (see `analysis.md` → Follow-up threads 1–3)

All three follow-up threads closed with new emissions (`results/fu_*.parquet`). One analyst
judgment call flagged: the LTF-momentum twin used Wilder DI(14) on the entry timeframe (same
construction as `htf_dir`, apples-to-apples); a hold-matched lookback could be tried if preferred.

## Operator disposition

> **Deferred to the post-SPDR-003 speed-run verdict** (operator directive 2026-07-07). SPDR-001
> is characterisation only; no per-leg disposition. Findings + recommendations above feed the
> CTRL-01/02/03 combined decision.
