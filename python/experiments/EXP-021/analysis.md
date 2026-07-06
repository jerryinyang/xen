# Data Analysis: EXP-021 — CF-CSRR-001 HYP-001

Currencies-basket cross-sectional consensus-residual reversion — availability + A×B×C×D
component characterisation. Execution-agnostic Python screen (no fills/P&L). Design:
`design.md` (QA APPROVED run-2). All numbers from `analysis_code/screen.py` on real 4h TRAIN
prices; canonical `xen.evaluation` for CI/MDE; my own construction. **Recommendation only — the
operator decides; no family disposition here.**

**Panel:** 7 USD pairs, 4h, TRAIN=first 49% → **3,526 aligned bars, 3,521 valid**, span
**2021-06-02 → 2023-11-20** (~2.4y, ONE regime incl. the 2021–23 USD/JPY trend — see §5).
Interpreter: system `python3` (numpy/polars); plots via `python/.venv` (matplotlib). Results
identical either interpreter (deterministic, seeded).

---

## 1. Integrity gate

EXP-021 is execution-agnostic: **no strategy, no fills, no P&L, no cTrader, no `xen.adjudication`**
→ the estimand-validation/reconciliation gate is **N/A (nothing to reconcile)**, by design
(precedent EXP-008/009; family card §Implementation path). The binding integrity gates are
provenance, tripwire, holdout.

| Check | Result | Evidence |
|---|---|---|
| Estimand-validation reconciliation | **N/A** | no accounting object; screen emits reversion stats, not P&L |
| Provenance ≤ t-1 (signal) / next-open (action) | **PASS** | anchor=prior-day last close `screen.py:daily_reset_anchor` (`prev_day_last=k-1`); `u` from `Close[t]` (confirmed ≤t); forward `g` from `Open[t+1]`→`Open[t+1+h]` `screen.py:rho_for_events` (`k1=t+1`). Golden trace confirms entry_open at t+1. |
| Leak tripwire collapsed + non-vacuous | **PASS** | temporal block-permute of (s→forward) pairing collapses ρ→0 on all real-positive cells: AUDUSD hedged collapse −0.02, USDCHF/z −0.03, USDCAD +0.03 (≈0). Non-vacuous: destroy moves the conditional mean (re-pairs s with an unrelated-time forward). Collapse fraction unstable only where raw≈0 (L-15 disclosed). |
| Holdout untouched | **PASS** | load slices `head(int(n*0.49))` per file (`load_4h_train`); panel ends 2023-11-20 ≪ TEST/holdout. Final-30% never read. |
| Price-primary | **N/A (availability screen)** | no edge-generating fills; tradability (cTrader) is EXP-023 |
| No experiment-local accounting | **PASS (honored)** | no per-bar/leg accounting defined; only `xen.evaluation` stats |

**Provenance detail:** `u_i(t)=σ_i·ln(Close_i(t)/anchor_i(t))`, anchor=prior UTC-day last close
(strictly earlier bar). `m,s,σ_t,k(t)` all from `≤ t` closes; `k(t)` = trailing median over
`[t-120, t-1]` (`trailing_threshold`, strictly `<t`). Forward return open-to-open from `t+1`. No
close of the acted bar enters any signal. **No L-01 pattern.**

---

## 2. Question list (answered)

1. **Is the consensus residual mean-reverting?** YES. VR(2)<1 on **28/28** instrument×A×B cells
   (median 0.87), VR(6) ≈ 0.36–0.54, AR(1) half-life **1.1–1.8 bars** (~1 session). §3.
   *Band correction:* design band "autocorr1<0" mis-specified for a **level** residual — a
   mean-reverting level has `0<AR(1)<1` (here ≈0.6, HL=−ln2/ln0.6≈1.36, matches) + VR<1, NOT
   negative level-autocorr. Positive level-autocorr is expected persistence, not evidence against.
2. **P&L-bearing object vs estimand?** Availability object = per-event forward idiosyncratic
   return over `h=2·HL`. Correct for an availability screen; episode/P&L object deferred to EXP-023
   (L-16 — no retirement is booked here).
3. **Does conditioning on large residual predict reversion (ρ>0) beyond twins + null?** Weakly and
   heterogeneously. §3–§4.
4. **Per-stratum structure (L-03)?** Strongly heterogeneous — positive on AUDUSD/NZDUSD/USDCAD/
   USDCHF, ~0 EURUSD, **negative USDJPY**. §4.
5. **Multiplicity (max-stat over 16 cells/instrument)?** Only **1** cell survives fw_p<0.05
   (AUDUSD unhedged); **no hedged cell survives**. §4.
6. **Twins?** Random-index + random-timing: the real-positive cells beat both; but see drift caveat. §3/§4.
7. **Leak?** Tripwire collapses on positives (§1). No leak.
8. **Power?** Several hedged positives have effect ≈ MDE (AUDUSD hedged +4.48 vs MDE 4.18;
   USDCHF/z +5.76 vs MDE 4.32; USDCAD +3.34 vs MDE 2.87) — borderline, UNPOWERED-adjacent. §4.
9. **Concentration/robustness?** Block-sensitivity ci_low>0 across ½/1/2× on the positives;
   USDCHF mean somewhat outlier-lifted (trimmed 2.67 < mean 5.76); AUDUSD/USDCAD trimmed ≈ mean. §3.
10. **Naive-median disclosure contrast** (operator disclosure-only branch): NOT computed this run —
    listed as an open disclosure (not load-bearing; USD-alignment is the registered primary). §5.

---

## 3. Evidence FOR the hypothesis

**F1 — substrate reverts, unanimously.** VR(2)<1 on all 28 instrument×A×B cells (median 0.87),
VR(6)≈0.4; AR(1) half-life 1.1–1.8 4h-bars. The USD-strength consensus residual is a genuinely
mean-reverting level on every currency, every estimator. (`substrate.parquet`, plot 1.) The
substrate kill criterion (VR≥1 & no MR) is **not** triggered.

**F2 — a coherent positive cluster on 4/7 instruments (hedged, mechanism-faithful).** Single-worst
hedged ρ (bps idiosyncratic forward): USDCHF/z **+5.76** (ci_low +1.45, block-robust, p_perm 0.024),
AUDUSD/raw **+4.48** (ci_low +0.29, p_perm 0.005), USDCAD/raw **+3.34** (ci_low +0.47, p_perm 0.039),
NZDUSD/AUDUSD positive-mean across most cells. Per-instrument mean ρ across all 16 cells: AUDUSD
+2.11, NZDUSD +2.08, GBPUSD +1.68, USDCAD +1.66, USDCHF +1.39 — 5/7 instruments positive-leaning.

**F3 — the positives beat both twins and are leak-clean.** On the positive cells the signal exceeds
the random-index twin (extremeness matters) and sits at the top of the 25-seed random-timing battery
(rt_percentile = 1.0), and the future-destroying tripwire collapses ρ→0 (collapse ≈ 0). So where a
positive exists it is dislocation-conditioned and causal, not a timing or leak artifact.

**F4 — one construction survives family-wise multiplicity.** AUDUSD median/raw/single/**unhedged**
+9.38 bps, **fw_p 0.008** (max-stat over 16 cells) — beats both twins, tripwire-clean. By the literal
predeclared availability kill criterion (a combination separating from both twins beyond the
multiplicity-adjusted null), **the family does not auto-retire.**

---

## 4. Evidence AGAINST the hypothesis

**A1 — the one multiplicity-survivor is drift, not residual reversion.** AUDUSD's surviving cell is
**unhedged** (raw forward return in the fade direction, market/USD beta included). Its **hedged**
counterpart — which subtracts the consensus forward and isolates the *idiosyncratic residual*
reversion the thesis is about — is +4.48 with **fw_p 0.68** (dead under multiplicity). So the
surviving edge is largely AUDUSD market drift over 2021–23, **not** consensus-residual reversion.
Removing the consensus (the actual mechanism test) removes the significance.

**A2 — no mechanism-faithful (hedged) construction survives multiplicity on ANY instrument.**
Best hedged fw_p: USDCHF/z 0.083, USDCAD 0.54, AUDUSD 0.68. All > 0.05. The uncorrected p_perm<0.05
count (5/112) collapses to **0 hedged cells** after the max-stat correction the design mandates.

**A3 — strong heterogeneity; USDJPY systematically CONTINUES.** USDJPY: mean ρ −2.42, **0/16 cells
positive**, p_perm ≈ 0.99, rt_percentile 0.0 (below every random-timing seed). It also **dominates
single-worst selection (615–644 events** vs EURUSD 93) — "fade the biggest deviator" repeatedly
selects the persistent 2021–23 JPY trend, which does not revert. EURUSD also negative (−0.98). A
pooled read (L-03) would average a reverting cluster against a trending USDJPY and mislead.

**A4 — effect sizes are small and borderline-powered.** The hedged positives are ≈ their own MDE
(AUDUSD +4.48/MDE 4.18; USDCHF +5.76/MDE 4.32; USDCAD +3.34/MDE 2.87). Idiosyncratic reversion of
~3–6 bps over a 2–4 bar horizon is thin, and USDCHF's mean is partly outlier-lifted (trimmed 2.67).

**A5 — single short regime.** 2.4y TRAIN, one macro regime (USD/JPY trend, aggressive Fed hiking).
No year-split power. The heterogeneity may itself be regime-specific.

---

## 5. Anomalies & open questions

- **USDJPY event dominance.** 615+ single-worst events vs 93 for EURUSD — JPY is the recurrent
  extreme deviator in this window. Single-worst selection is structurally exposed to whichever
  currency is trending; a de-trended or per-instrument-capped selection is an untested branch.
- **Hedged vs unhedged gap on AUDUSD** (+4.48 fw_p 0.68 vs +9.38 fw_p 0.008): quantifies how much of
  the "reversion" is market beta. A directional/drift-carry decomposition (the EXP-023 momentum-signed
  inverted twin) is the right next probe; here it is flagged, not run.
- **Collapse-fraction instability** where raw≈0 (EURUSD 1.06, NZDUSD 0.37) — L-15: not a leak, just a
  small-denominator ratio; the tripwire's *level* (≈0) is the read, not the fraction.
- **Naive-median disclosure contrast** not computed — open disclosure item.
- **Deferred registered branches** (not run): V3 weighted-implied consensus; B=range-scaled;
  currency-strength-vector build (would service the 3 excluded JPY crosses); anchor-horizon sweep.

---

## 6. Recommended verdict (experiment hypothesis only — NOT final, NOT family)

- **Recommendation: NOT SUPPORTED (availability), with a substrate-reverts nuance and a power caveat.**
  The substrate *is* mean-reverting (VR<1 unanimous, F1), but **no mechanism-faithful (hedged)
  A×B×C×D construction delivers multiplicity-robust signal-conditional residual reversion** on any
  instrument (A2); the sole family-wise survivor is AUDUSD **unhedged**, i.e. market drift, whose
  hedged (residual-isolating) form is null (A1). The conditional edge is heterogeneous
  (USDJPY continues, A3) and borderline-powered (A4).
- **Driven by:** (1) all hedged cells fw_p>0.05 under the mandated max-stat null; (2) the one
  survivor is drift (hedge kills it); (3) USDJPY 0/16 positive + dominates selection.
- **Would change if:** a de-trended / drift-controlled selection (or the momentum-inverted twin)
  showed the hedged residual reversion surviving multiplicity on a stable instrument subset; or a
  longer/multi-regime panel powered the ~3–6 bps hedged positives on USDCHF/AUDUSD/USDCAD.
- **Note on the kill criterion:** the *literal* predeclared availability criterion is technically
  NOT met (AUDUSD unhedged separates from both twins beyond the multiplicity null, F4) — so an
  auto-retire is not warranted. But that survivor is not the residual-reversion object. The
  disposition (retire / iterate the selection or hedge component / pursue the drift separately) is
  the **operator's at the checkpoint-009 retrospective**, on this evidence.

**Final verdict is the operator's.** Suggested probes if you want to push: (a) drift-carry
decomposition on AUDUSD (hedged vs unhedged vs momentum-inverted); (b) de-trended / per-instrument
selection to stop USDJPY-trend capture; (c) power the hedged USDCHF/AUDUSD/USDCAD cluster on the
Indices basket (EXP-022, VAL-007-gated) where a single equity factor may be cleaner than USD-strength.

---

## 7. Follow-up disclosures (operator questions, 2026-07-06)

All availability-level (gross idiosyncratic screen returns) — NOT live-P&L. Real alpha/beta vs a
market benchmark and exposure-normalized return require fills + cost = **EXP-023**.

**7.1 Variant scoreboard** (each variant = its A×B×C×D cell; screen ρ, hedged/mechanism-faithful):

| Variant | Cell | pooled ρ (bps) | n ci+ /7 | n survive max-stat /7 |
|---|---|---|---|---|
| V1 / V5-screen | median/raw/single/hedged | +0.43 | 2 | 0 |
| V2 | mean/raw/allk/hedged | +0.77 | 0 | 0 |
| V4 | mean/z/allk/hedged | +0.65 | 0 | 0 |
| V3 | weighted-implied | — (deferred) | — | — |

Every variant pooled is a ~0.4–0.8 bps wash; **0/7 strata survive multiplicity in any variant**;
all carry the USDJPY-continuation drag. None distinguishes. (V5's execution split is untested here.)

**7.2 Alpha/beta decomposition** (single-worst median/raw): hedged ρ = idiosyncratic **alpha**;
(unhedged − hedged) = consensus-exposure **beta/drift**:

| Inst | alpha (hedged) | beta/drift | raw (unhedged) |
|---|---|---|---|
| AUDUSD | +4.48 | +4.90 | +9.38 |
| NZDUSD | +1.60 | +3.49 | +5.09 |
| USDCAD | +3.34 | +0.48 | +3.82 |
| USDCHF | +2.48 | −4.17 | −1.68 |
| GBPUSD | −0.71 | −2.43 | −3.13 |
| USDJPY | −3.00 | −0.40 | −3.40 |
| EURUSD | −5.19 | +0.78 | −4.41 |

The AUDUSD multiplicity-survivor (unhedged +9.38) is **~half beta**; its hedged alpha (+4.48) is
multiplicity-dead. **USDCAD** is the cleanest near-pure idiosyncratic alpha (+3.34, beta +0.48) but
still fw_p 0.54. USDCHF alpha (+2.48) is masked in raw by a negative beta (safe-haven bid). So the
mechanism-faithful "alpha" is small (2–4.5 bps), instrument-specific, and multiplicity-fragile;
much of the eye-catching raw signal is beta.

**7.3 Occupancy / time-in-market** (single-worst, trailing-median k): basket-level entry rate
**~50% of bars** (1,761 event-bars / 3,521), mean hold 3.3 bars → time-in-market **>100%
(overlapping)**. At this threshold it is **NOT a low-exposure fader** — the "same return, less
exposure" case does not apply. A sparser deep-dislocation trigger (top-decile k) could change that
but was not isolated (axis-G coarse) and would cut n hard. Open branch.

**7.4 Economic usability (informative, not a net test).** Best hedged alpha ~2–4.5 bps gross over
~3 bars vs FX-majors round-trip ≈ 1–2.5 bps (commission 0.5–1.0 + half-spread). Gross alpha ≈ 1–2×
cost **before** adverse selection or the trend-tail (USDJPY) losses → marginal-to-negative net prior.
Not formally tested here (EXP-023 is the net-of-cost test with V5 active-entry).

**7.5 Horizon-multiplier sensitivity (is h = 2·HL load-bearing?).** HL is **fitted per instrument**
(AR(1), `ar1_halflife`) — the horizon is data-driven (h 2–4 bars). The **multiplier 2 is a
pre-registered constant** (≈2 half-lives → ~75% MR completion), not tuned. Recompute 4h primary cell
at h=1·/2·/3·HL (`h_sensitivity.py`, `results/h_sensitivity.parquet`): **per-instrument SIGN is
stable across all three** for 5/7 (AUD/NZD/CAD/CHF +, EUR/JPY −); only GBPUSD flips near zero. So the
read does not hinge on the ×2. AUDUSD grows with horizon (1.3→4.5→4.8 bps) = drift accumulation
(consistent with its beta, §7.2) — a longer hold books more drift, not more reversion.

**7.6 1D-domain disclosure (NON-REGISTERED exploratory branch, operator-directed 2026-07-06).**
Family card fixes 4h-only; 1D is disclosure-only (TRAIN 543 daily bars, weekly-reset anchor to keep
accumulation; `*_1d` results). Registering 1D as a domain needs an operator-signed amendment.
- **Substrate reverts on 1D too:** VR(2)<1 on 27/28 cells (median 0.85), HL~1.2 daily bars.
- **UNPOWERED:** single-worst gives ~20–37 events/cell (median 30), **MDE median 21.8 bps** vs
  effects 5–13 bps → MDE ≫ effect on ~all cells; **cannot be read as positive or negative** (B-5).
- Sign pattern **reorders vs 4h** (EURUSD → +, USDCAD → −); the 2 nominal ci+/p_perm cells (EURUSD
  n=25) are tiny-n and 4h-inconsistent → noise/regime, not structure. Tripwire collapse fractions
  unstable (small-denominator, L-15) but no leak.
- **Conclusion:** daily cadence is too sparse over 2.4y TRAIN to adjudicate availability; reinforces
  4h as the right cadence and adds no support for HYP-001.

**7.7 AUDUSD deep-dive (operator probe) — `audusd_probe.py`.**
- **1D performance:** all 16 cells positive point estimates (+3 to +41 bps) but **0/16 ci+, every
  MDE > |effect|** (MDE 12–54 vs 3–41), all p_perm > 0.09; n=21–24 single-worst events. UNPOWERED —
  not bookable (the +41 unhedged is n=24/MDE 54 noise). Daily cadence cannot see AUDUSD's signal.
- **Actual time-in-market (overlap-aware, single-worst median/raw):** 4h h=4 bars, 297 events →
  **21.0% overlap / 17.2% sequential** (151 one-at-a-time trades); 1D h=2 → **7.8% / 7.1%** (19
  trades). AUDUSD as one leg is ~17–21% in-market on 4h — NOT the 50% basket figure (that pooled all
  7 instruments' single-worst events). So the exposure-efficiency framing is real *for AUDUSD* (~17%
  exposure), but the return at that exposure is the multiplicity-dead, half-beta +4.5 bps hedged alpha
  (fw_p 0.68) — moderate exposure, small/fragile/drift-contaminated payoff, not a clean win.
