# Data Analysis: SPDR-002 — HTF context as a conditioning variable on naive-momentum LTF entries

**Fresh-context data-analyst pass (stage 5), reframed 2026-07-07 (operator).** Blind of SPDR-001
findings (only its causal primitives reused as methodology). TRAIN-only. **No disposition** — this
is characterisation; the CTRL-01/02/03 series read is the operator's, after SPDR-003. All numbers
re-derived per-trade from raw bars (`analysis_code/rederive.py`, `conditional_effect.py`,
`stratum_table.py`). **Stratum = instrument x domain-pair x variant x hold.**

**Interpretive frame (corrected).** The CTRL-02 base — a naive last-3-bar momentum breakout — is
itself a failing object; its own failure was never characterised. "HTF-filter lift over the
momentum baseline" is therefore only ONE lens, and a **confounded** one: a small lift on a base
that is already broken misattributes the base's pre-existing failure to the HTF overlay. This
document leads with two un-confounded facets and treats the lift table as secondary:

- **Facet A (§2)** — characterise the base momentum's OWN failure per stratum (so we know what
  object HTF conditions).
- **Facet B (§3)** — quantify HTF context as its OWN conditional effect on the LTF forward-return
  distribution: how much the outcome MOVES as HTF state varies (between-state spread of
  conditional means + CI; dispersion modulation; DI sign-conditioning), independent of base
  viability and independent of the lift-over-baseline lens.
- **Lens 3 (§4)** — HTF-filter lift over baseline, retained but explicitly flagged as
  base-failure-confounded.

Emissions: `results/base_failure.{parquet,csv}`, `results/htf_conditional_effect.{parquet,csv}`,
`results/stratum_magnitudes.{parquet,csv,md}`.

---

## 1. Integrity gate (SPDR lane — code-asserted; no estimand-validation gate)

| Check | Result | Evidence |
|---|---|---|
| TRAIN fence (first 70% of 70%; entry+hold < cutoff; 0 TEST/holdout) | PASS | `results/integrity.json` 12/12 `train_fence_ok:true` |
| HTF-bar-boundary causality (`HTF.CloseTime < LTF.Open(t)`) | PASS | 12/12 `htf_boundary_ok:true`; golden trace 12/12 ok |
| LTF breakout causal (bars <= t-1, act at Open(t)) | PASS | `momentum_signal` reads `High[t-2..t-4]`; reproduced independently |
| Seed battery regenerable (25 seeds) | PASS | `default_rng(10000+k)`, byte-deterministic |
| No local P&L accounting (L-18) | PASS | availability metric only; `xen.evaluation` block bootstrap |
| Holdout untouched | PASS | no glob beyond TRAIN slice |

---

## 2. FACET A — the base naive-momentum strategy's OWN failure (per stratum)

Full magnitudes in `results/base_failure.csv` (48 strata; mean & CI in ATR units and raw bps,
median, std, skew, hit-rate, ±2-ATR tail mass, worst-5%/worst-decile loss concentration, and the
base arm's percentile within the 25-seed random-timing battery).

### 2.1 Location (item 1) & directional accuracy (item 2)
- **Mean forward return sits at ~0 with CI straddling zero in nearly every powered stratum.**
  Well-powered 1h/5min (n 3.5k–15k): EURUSD −0.056/−0.083/−0.088/−0.123 ATR (H1 CI
  [−0.102,−0.009], raw −0.21 bps [−0.40,−0.02]); XAUUSD +0.033/+0.001/−0.076/−0.065; BTCUSD
  −0.013/−0.013/+0.020/+0.064; USTEC +0.005/+0.039/+0.078/−0.013 (all CIs straddle 0 except
  EURUSD H1). 4h/1h (n 775–2608): BTCUSD drifts positive with hold to +0.236 [+0.013,+0.457]
  (H16); XAUUSD drifts negative to −0.168 [−0.385,+0.044] (H16). 1d/1h is sparse (n 135–627):
  isolated large values (BTCUSD H2 +0.721 [+0.107,+1.337]; XAUUSD H3 +0.844 [−0.043,+1.724]).
- **Hit-rate is 0.448–0.564 across all strata, centred ~0.49** — the momentum sign carries no
  directional accuracy. `median` tracks near 0 (e.g. 1h/5min medians −0.19 to +0.00).

### 2.2 Shape (item 3)
- Dispersion (std) grows with hold in every stratum (e.g. BTCUSD 1d/1h 4.35→11.4 across H1→H4;
  EURUSD 1h/5min 2.70→6.05). **±2-ATR tail mass rises monotonically with hold**: 0.15–0.18 at
  4h/1h H1 up to 0.76–0.83 at 1d/1h H4 — the outcome is increasingly tail-dominated as H extends.
- Skew is instrument-specific and large in crypto/gold intraday: BTCUSD 1h/5min +1.7 (H1),
  XAUUSD 1h/5min +1.9 (H1), BTCUSD 4h/1h +1.66 (H1) — fat RIGHT tails; USTEC/EURUSD are
  near-symmetric-to-left (−0.20 to −0.40).

### 2.3 Availability vs random timing (item 4)
The base arm's mean percentile within the matched 25-seed random-timing battery is **stratum-
dependent and spans the full range** — momentum timing is not uniformly indistinguishable from
random:
- **Below random** (pct <= 0.10): EURUSD 1h/5min H1 0.04; XAUUSD 1h/5min H3 0.04; XAUUSD 4h/1h
  H2/H3/H4 0.08/0.08/0.04; USTEC 1d/1h H2 0.12.
- **Above random** (pct >= 0.90): BTCUSD 4h/1h H1/H2/H4 0.96/0.96/0.96; XAUUSD 1h/5min H1 0.96;
  BTCUSD 1d/1h H2 1.00; USTEC 1d/1h H3 1.00; XAUUSD 1d/1h H3 1.00.

### 2.4 Failure-mode decomposition (item 5 — named per stratum)
- **(a) No directional edge** — hit≈0.5, mean≈0, median≈0. **Dominant mode**, present in every
  well-powered stratum (all EURUSD; XAUUSD/USTEC 1h/5min; XAUUSD/USTEC/EURUSD 4h/1h).
- **(b) Edge eaten by dispersion/left tail** — **systematic**: `mean_excl_worst5` (mean after
  dropping the worst 5% of trades) is **positive in 46/48 strata** even where the full mean is ~0
  or negative. Examples: XAUUSD 4h/1h H16 full −0.168 → excl +0.219; EURUSD 4h/1h H12 −0.045 →
  +0.276; USTEC 4h/1h H16 −0.089 → +0.355; EURUSD 1h/5min H12 −0.056 → +0.255. So the
  zero/negative location is manufactured by a small set of large adverse trades, not by a
  centre-of-mass loss.
- **(c) Horizon decay / drift** — stratum-specific direction, but dispersion always widens with
  H (§2.2). XAUUSD 4h/1h and USTEC 4h/1h and EURUSD 1h/5min drift MORE negative with hold;
  BTCUSD 4h/1h drifts MORE positive (+0.046→+0.236). No stratum shows a short-H edge that a long
  hold merely dilutes toward zero — the H-profile is a drift, not a decay-to-zero.
- **(d) Loss concentration** — the worst 5% of trades carry **20–36%** of all loss mass
  (`worst5pct_loss_share`), and the **worst-decile mean contribution (−0.25 to −1.75 ATR) exceeds
  the full mean in magnitude in every stratum** — e.g. BTCUSD 1d/1h H4 worst-decile −1.75 vs full
  mean +0.22. The distribution's centre is mildly favourable; a thin adverse decile sets the mean.

### 2.5 Horizon profile (item 6)
Mean and hit vs hold are tabulated per stratum in `base_failure.csv` and plotted in
`plots/horizon_baseline.png`. Hit-rate is flat in H (0.45–0.53 at every hold); mean drifts
(sign-stable within a stratum for 4h/1h and 1h/5min, noisy for sparse 1d/1h); tail mass and std
rise monotonically with H.

**Payoff for reading Facet B/§4:** the base is predominantly **mode (a)+(b)+(d)** — a
near-coin-flip centre whose mean is set by a concentrated adverse tail. So a measured HTF-induced
shift is mostly a shift imposed on a near-null, tail-fragile object: an HTF effect on the sign
centre is close to pure HTF signal, while an HTF effect on dispersion/tails is HTF re-shaping the
exact structure (the fat tail) that breaks the base — both are positive HTF quantifications.

---

## 3. FACET B — HTF context as its OWN conditional effect (per stratum)

HTF state treated as a conditioning variable on the SAME momentum entries; magnitude = how much
the LTF forward-return distribution moves BETWEEN HTF states, independent of base viability and of
any baseline comparison. Full table: `results/htf_conditional_effect.csv`. Three magnitudes per
stratum: (i) ADX between-state range of conditional means (top − bottom ADX bucket, two-sample
block-bootstrap CI); (ii) ATR between-state range; (iii) DI sign-conditioning
(momentum-agrees-with-HTF-direction mean − disagrees mean, CI); plus the dispersion-ratio range
across states.

### 3.1 DI sign-conditioning (well-powered — the cleanest HTF magnitude)

> **Corrected 2026-07-08 (audit):** the originally tabulated USTEC H12 row (+0.26 [+0.10,+0.43])
> does not reproduce; the audit re-derivation gives **+0.066 [−0.020,+0.148]** (n.s.) under the
> documented construction (`correction/spdr002_ustec.csv` in the Phase-010 checkpoint). H24/H36/H48
> reproduce CI-clear. Table corrected accordingly.

Knowing the HTF DI direction moves the momentum mean by (agree − disagree), CI clear of zero:
| stratum | agree_n / disagree_n | DI sign effect [CI] |
|---|---|---|
| USTEC 1h/5min H48 | 3174 / 3171 | **+0.39 ATR [+0.05,+0.74]** |
| USTEC 1h/5min H36 | 4065 / 4060 | **+0.28 ATR [+0.02,+0.53]** |
| USTEC 1h/5min H24 | 5651 / 5650 | **+0.26 ATR [+0.10,+0.42]** |
| BTCUSD 1h/5min H10 (H2) | ~ | **+0.16 ATR [+0.02,+0.31]** |
| BTCUSD 1h/5min H5 (H1) | ~ | **+0.12 ATR [+0.04,+0.19]** |

(All positive: on these strata momentum entries whose direction agrees with the last-closed HTF
DI carry a higher forward mean than disagreeing ones, by +0.12 to +0.39 ATR. USTEC H12 is +0.07
n.s. — the conditioning strengthens with hold, consistent with the accumulating-gap profile on
the random base.) The remaining DI effects range −0.18 to +0.86 with CIs spanning zero
(magnitudes in the csv). These strata are non-overlapping greedy trades, so the block choice is
not the binding concern it was on SPDR-001's per-bar estimand.

### 3.2 ATR-percentile between-state range (well-powered)
Knowing the HTF ATR regime moves the momentum conditional mean by, CI clear of zero:
- **USTEC 4h/1h H16: 0.800 ATR [+0.286,+1.351]** (top−bottom ATR bucket)
- **EURUSD 4h/1h H8: 0.381 ATR [+0.102,+0.665]**
- **USTEC 1h/5min H5 (H1): 0.157 ATR [+0.029,+0.277]**
7/48 strata clear zero (incl. sparse 1d/1h below).

### 3.3 ADX between-state range (well-powered)
- **USTEC 1h/5min H15 (H3): 0.435 ATR [+0.126,+0.750]**
- **USTEC 1h/5min H10 (H2): 0.236 ATR [+0.011,+0.453]**
4/48 strata clear zero.

### 3.4 Sparse 1d/1h — large conditional ranges, flagged low-n (B-5)
CI-clear but n 135–329 (UNPOWERED-adjacent, reported as magnitudes with n, not folded into any
negative): ADX range BTCUSD 1d/1h H4 **3.33 [+0.62,+5.93]** (n169), H3 **2.98 [+0.42,+5.42]**
(n224); ATR range BTCUSD 1d/1h H4 **3.89 [+1.38,+6.54]**, H2 **1.77 [+0.41,+3.19]**; XAUUSD 1d/1h
H4 **3.16 [+1.34,+4.97]**, H3 **2.87 [+0.95,+4.90]**.

### 3.5 Dispersion modulation by HTF state (disp_ratio range across states)
Knowing the HTF state changes the momentum *dispersion* by a factor up to:
- **ATR state: up to ~2.0x** — USTEC 1h/5min 1.85–1.98, EURUSD 1h/5min 1.39–1.53, BTCUSD 1h/5min
  1.26–1.41. **Guard:** HTF ATR regime co-moves with the LTF ATR[t-1] normaliser, so part of the
  ATR-state dispersion range is the denominator mechanic (§5) — read as an upper bound.
- **ADX state: up to ~1.4x** — USTEC 1d/1h 1.39, EURUSD 1d/1h 1.38; ADX is far less coupled to
  ATR[t-1], so the ADX-state dispersion modulation (~1.05–1.4x) is a cleaner HTF-shape magnitude.

*Disclosure-only (L-03, not a headline):* ADX between-state range CI>0 in 4/48 strata, ATR 7/48,
DI sign-conditioning CI-excl-zero 5/48. The read is the per-stratum magnitudes above, not the count.

---

## 4. Lens 3 (secondary, base-failure-confounded) — HTF-filter lift over baseline

Retained for completeness; **confounded** by the base's own failure (§2) and therefore not the
primary HTF read. Full per-stratum lift + CI + disp_ratio + dhit_pp + twinPct + Control-C collapse
in `results/stratum_magnitudes.md`. Powered, non-degenerate (admit_frac<0.95), block-robust strata
with lift CI clear of zero (magnitudes; positive = HTF overlay raises the momentum mean):

- **Positive:** BTCUSD 1d/1h adx_lt25 H72 +2.80 [+0.52,+4.95] (n101); XAUUSD 4h/1h atrM_adxLo H16
  +0.74 [+0.22,+1.22] (hit +12.2pp, n159); USTEC 4h/1h atr_low H16 +0.49 [+0.02,+0.93];
  USTEC 4h/1h atrH_adxLo_di H8 +0.40 [+0.05,+0.75]; BTCUSD 1h/5min atrH_adxHi_di H48 +0.38
  [+0.005,+0.78]; USTEC 1h/5min atrL_adxHi_di H12 +0.22 [+0.04,+0.42]; EURUSD 1h/5min atrM_adxLo
  H12 +0.13 [+0.02,+0.25].
- **Negative:** XAUUSD 1d/1h atr_high H72 −2.21 [−3.86,−0.57] (hit −18.1pp); XAUUSD 1d/1h
  atrH_adxLo H24 −1.15 [−2.20,−0.22]; EURUSD 4h/1h atrM_adxHi H8 −0.40 [−0.70,−0.11]; USTEC
  1h/5min atrH_adxHi H36 −0.37 [−0.65,−0.07]; USTEC 1h/5min adx_25_75 H36 −0.35 [−0.62,−0.07].

DI-arm lifts collapse under the HTF phase-shift (Control C): the 8 powered DI lift-CI>0 strata have
collapse fractions 0.21–0.44 or opposite-signed — reported as magnitudes, no adjudication.

---

## 5. Dose-response per instrument x domain (not a grid median)

Spearman rho of the unfiltered-momentum return vs continuous ADX and HTF ATR-percentile, per
instrument x domain (median over holds); full CIs in `dose_response.parquet`.

| inst x domain | rho(ADX,mean) | rho(ATRpct,mean) | rho(ATRpct,\|r\|) |
|---|---|---|---|
| EURUSD 1d/1h | −0.008 | +0.053 | −0.054 |
| EURUSD 4h/1h | −0.015 | −0.015 | −0.137 |
| EURUSD 1h/5min | −0.011 | +0.003 | −0.179 |
| XAUUSD 1h/5min | +0.002 | +0.002 | −0.194 |
| BTCUSD 1h/5min | −0.0001 | +0.00004 | −0.128 |
| USTEC 1h/5min | −0.010 | −0.018 | −0.233 |
| (others) | −0.05..0 | −0.07..0 | −0.08..−0.16 |

Location dose |rho|<=0.053 everywhere. The dispersion dose rho(ATRpct,|r|) is negative in 12/12
inst x domain (−0.05 to −0.23): this is the ATR[t-1]-denominator mechanic (high HTF-ATR regime =>
high LTF ATR[t-1] => compressed normalised |r|); the numerator carries no positive vol-clustering
(0/96 hold-cells with rho(|r|) CI>0), and the fixed-window dispersion level is flat (§6). Reported
as a magnitude with its mechanical attribution.

---

## 6. Normaliser guard (dispersion)

Absolute dispersion *level* is normaliser-stable: the fixed-long-window (100-bar) ATR std matches
the ATR[t-1] std everywhere (EURUSD 1d/1h H1 3.77 vs 3.56; BTCUSD 1d/1h H1 4.35 vs 4.15), and
raw-bps std scales with instrument vol. So the disp_ratio magnitudes in §3.5/§4 that compare two
trade subsets under the SAME per-trade normaliser are genuine relative-shape effects; only the
ATR-percentile dose (§5) and the ATR-STATE dispersion range (§3.5) carry the denominator mechanic
and are read as upper bounds.

---

## 7. Power map (B-5 — a power statement, never a negative)

| variant / stratum class | median n | median MDE (ATR) | status |
|---|---|---|---|
| none / di / adx_lt25 / atr_low | 648–1281 | 0.19–0.27 | powered |
| single ATR/ADX gates | 200–627 | 0.25–0.39 | powered |
| ATR x ADX x DI triple combos | 131–190 | 0.35–0.55 | UNPOWERED for ~0.1 effects |
| **adx_ge75** | **4** | n/a | **absent regime** (BTCUSD 4h/1h n=1) — excluded |
| 1d/1h H72/H96 corners | 135–224 | 0.9–1.9 | UNPOWERED |

The ADX>=75 regime essentially never occurs on this data at these HTF windows; triple-combo and
1d/1h long-hold strata carry MDEs larger than any effect measured in the powered strata, so their
CI-straddling rows are a visibility statement, not evidence of absence.

---

## 8. Open threads (cheap, non-blocking)

1. **Raw-bps dispersion dose** — recompute §5 rho(ATRpct,|r|) on raw-bps returns to confirm the
   normaliser-mechanic attribution to ~0 (the level guard already indicates it).
2. **DI sign-conditioning in 1h/5min** is the cleanest well-powered HTF magnitude (USTEC +0.26 to
   +0.39 ATR at H24–H48, BTCUSD +0.12 to +0.16, CI clear) and is a between-state effect not confounded by the
   base's failure — a pre-registered family-wise max-stat over each instrument's holds would put a
   hard multiplicity number on it.
3. **Facet-A mode (b) is systematic** (mean_excl_worst5 positive in 46/48): worth an operator note
   that the base's failure is tail-driven, so HTF facets that re-shape the tail (§3.5 dispersion
   modulation) act on the exact failure structure.

**No disposition. Final verdict is the operator's; the CTRL-01/02/03 series read is taken once,
after SPDR-003.**
