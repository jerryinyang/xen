# Results: Experiment EXP-063 — MA-Substrate Adverse Geometry & the Mean Investigation (dual-object)

**Deliverable: MA_ADVERSE_GEOMETRY_AND_MEAN_CHARACTERISED (dual-object).** Phase verdict
**EVIDENCE_FOR** (stronger object = native); **hybrid = EVIDENCE_AGAINST**. Emitted for the single
terminal G-015; no closure here.

## Headline (per object, never pooled)

| Object | Bounded-downside generalises (P11+P6) | beats own RM-on-MA | mean recovery | §4 verdict |
|--------|---------------------------------------|--------------------|---------------|------------|
| **Native** `M-*` | V-BENCH 8/99 ✓, V-RR1 9/99 ✓ | yes (both) | **recovery contrast 0/99**; bounded raw-mean ≈ 0; mean_viable composes | **EVIDENCE_FOR** |
| **Hybrid** `H-*` | V-BENCH 1/99 ✗, V-RR1 1/99 ✗ | **no** (beats_rm 0) | n/a | **EVIDENCE_AGAINST** |

## Interpretation — the decisive §4 mean read

**1. Native: a bounded-downside median edge survives, and the catastrophic mean is repaired — but the
mean is neutralised, not made positive.** Both bounded variants (benchmark 1:1, `/ADV-EXTREME-rr1`) are
median-viable, beat their own matched-random-on-MA null, and compose P11+P6 (8 and 9 cells). The §4
decomposition explains the EXP-060B negative mean precisely:

- `/ADV-NONE` raw-mean median **−0.058 ATR** but **10%-trimmed +0.422 ATR** (worst-5% tail-share 0.356):
  the unbounded mean's negativity is a **thin catastrophic left tail** — the uncapped-downside skew
  EXP-060B and EXP-062 flagged, now confirmed directly.
- Bounded V-BENCH raw-mean median **+0.0065 ATR**, trimmed **−0.018**: the 1:1 stop **truncates the left
  tail** (the raw mean recovers from −0.058 to ≈ 0) but also clips the right-tail winners, so the **centre
  is ≈ 0**, not positive.
- The **bounded-downside recovery contrast** `mean(bounded) − mean(/ADV-NONE)` is **null in 0/99 cells**:
  bounding does not *lift* the raw mean relative to `/ADV-NONE`, because `/ADV-NONE`'s raw mean is only
  marginally below the bounded one (both near 0). The mean is "recovered" from catastrophic to neutral, not
  to positive.

So the §4 verdict is **EVIDENCE_FOR** in its **weak, median-preserving** form: the bounded-downside lever
keeps the signal-attributable median edge **and** removes the catastrophic-mean risk (the gross mean is no
longer dragged negative), but it does **not** demonstrate a materially positive gross mean. The
structural-irrecoverability case (MEDIAN_ONLY) is also not met — the negativity is shown to be a
*removable tail*, not structural. The honest one-line reading: **median edge + bounded ≈ 0 gross mean.**

**2. Hybrid: median viability without signal attribution → EVIDENCE_AGAINST.** The hybrid variants are
median-viable in many cells (V-RR1 90/99) but beat their own RM-on-MA null in **0** — so they generalise
in only 1 cell and fail P11. The hybrid object's median positivity is **ambient** (random-in-regime
matches it), not harami-driven. This confirms EXP-061's central finding on the adverse axis: the edge is a
matched-substrate (MA-conditioning) property; the ZigZag-conditioned hybrid object does not express it.

**3. Cross-experiment synthesis (for G-015).** Native is the only object expressing a signal-attributable
edge across L1 (benchmark capture, EXP-061), L3 (bounded-downside adverse, here). EXP-062 showed the raw
lifetime *availability* is ambient on both objects. So the native edge is a **capture-geometry median**
property with a **bounded but ≈ 0 gross mean**. The open G-015 question is therefore **not** "does bounding
fix the mean to positive" (it does not — it neutralises it), but whether a median edge with a neutralised
gross mean can survive costs / earn a candidate slot — a later-phase question. No closure here.

## Reading against the pre-registered guide

- Native: a bounded variant generalises (P11+P6) and beats RM, and `mean_viable` composes → **EVIDENCE_FOR**
  by the encoded P4 rule. The recovery contrast being flat (0/99) is recorded as the qualifier: the mean is
  repaired-to-neutral, not lifted-to-positive.
- Hybrid: no bounded variant both clears P11 and beats RM → **EVIDENCE_AGAINST**; family stays OPEN.
- No correctness failure (reconciliation 99/99 exact to both EXP-061 M0 and H0; determinism + causality
  clean; per-object structural invariants pass).

## Limitations

1. **TRAIN-only**; TEST + holdout sealed for G-015.
2. **Gross.** The bounded native mean is ≈ 0 gross — costs would push it negative; net viability is a later
   phase, not asserted here.
3. **The EVIDENCE_FOR is the weak form** (median preserved, mean neutralised); it is **not** a mean-positive
   demonstration. Stated plainly to avoid over-reading the mechanical verdict.
4. `/STRONG-HA`, MAD, and a separate ZigZag adverse surface were deferred (runtime/budget; recorded in
   `run_metadata.json`).
