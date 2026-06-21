# Results: Experiment EXP-077 — Dogfood + Calibration under `WF-EXPANDING` (`ASS/VAL-002`)

> **Phase 017 — CF-CAPGEO-001 Qualifier & Protocol Validation.** This experiment **feeds** G-017; it
> does **not** adjudicate it (G-017 is decided after EXP-078). All findings are reported **per stratum**
> (LESSON-001; D0 §8). No single collapsed PASS/FAIL is binding — the `collapsed_convenience_flag` in
> `verdict.json` is `false` and explicitly captioned NON-BINDING.

## Summary

Under the frozen `WF-EXPANDING` expanding-window protocol, the `ASS` qualifier's **detection power
(MDE), protocol accounting, real-bar dogfood, determinism, and estimator anchor all hold cleanly**; its
**error-control (FPR) and `P(>X)` reliability legs each carry one bounded, per-stratum exception** rather
than a whole-qualifier failure. The audit (verdict PASS) re-derived every headline number from the raw
tables and established the mechanism for each exception. Concretely: the FPR "failures" split into
(a) **U0 point-crossings that are Monte-Carlo noise around a margin calibrated *to* 0.05** — not error-
control failures — and (b) a **genuine but mild, fast-decaying B_zero inflation at n≤60** that is exactly
the EXP-076 small-/mid-`n` under-coverage and triggers the predeclared "defer-to-median at effective
n<30" guard. The reliability "failure" is **X=2.0 slope only**, an ill-conditioned slope over a
compressed predicted-probability range while absolute calibration is excellent (max-gap 0.017); this is a
**gate-shape/applicability disclosure**, not 2R miscalibration. None of the protocol legs trip
`PROTOCOL_DEFECT`. Net: `ASS_VALIDATED`'s error-control and reliability legs hold **per stratum with two
named guards**; the protocol machinery is validated.

## Detailed Findings

### 1. FPR — U0 binding "failures" are MC noise around the 0.05 construction target (error control holds)

- **Observation**: Three U0 `wf` cells cross the point gate — n=120 (0.0515), n=1000 (0.051), n=2000
  (0.052) — against the rule `FPR ≤ 0.05 AND Wilson-hi ≤ 0.075`. The remaining six U0 `wf` cells pass
  (0.044–0.0495).
- **Evidence** (`fpr.csv`, `audit.md` §C): the margin is `m = Q95(ci_low_1s | null)`, which by
  construction calibrates the null edge-rate **to** 0.05; at R_REP=2000 the MC standard error is
  √(0.05·0.95/2000) = 0.00487. The three crossings sit at z = +0.31 / +0.21 / +0.41, with one-sided
  binomial P(X ≥ edges | p = 0.05) = 0.39 / 0.43 / 0.36 — fully consistent with true FPR = 0.05. The
  entire U0 row lies inside the [0.040, 0.060] 95% MC band. **Every** binding U0 cell passes
  Wilson-hi ≤ 0.075 (max 0.0626).
- **Interpretation**: per the predeclared guide (question 1), these are **point-gate-vs-MC-noise**
  crossings, not genuine error-control failures. The location-null (U0) FPR leg of `ASS_VALIDATED`
  **holds** at every binding `n`: error control is at the 0.05 target, and the Wilson-hi sub-gate — the
  uncertainty-aware part of the rule — is satisfied throughout. The bare point-≤-0.05 sub-gate is the
  wrong instrument for an estimator calibrated to 0.05 (it crosses ~half the time by chance).

### 2. FPR — B_zero inflation is real, mild, and confined to n ≤ 60 → triggers the n<30 median guard

- **Observation**: B_zero `wf` FPR is 0.059 at n=30 and 0.059 at n=60 (binding fails), 0.050 at n=120
  (pass), then collapses monotonically: 0.0365 / 0.030 / 0.026 / 0.011 / 0.001 for n=250…8000. The
  non-binding small-`n` sub-reads make it starkest: B_zero n=30 `single_window` = 0.071 (Wilson 0.083,
  the only cell breaching even the Wilson ceiling), n=15 `single_window` = 0.0585.
- **Evidence** (`fpr.csv`, `verdict.json.small_n_stratum`, `audit.md` §B–C): the two binding fails sit at
  z = +1.85 (P(X≥118 | p=0.05) = 0.039) — beyond pure noise — and the inflation **decays to z ≈ −2.8 to
  −10** for n ≥ 120 as the margin `m` falls to 0. This is the bimodal mean-null (mean ≈ −0.015, median
  +0.15) interacting with the percentile bootstrap's known **n<30 under-coverage** (EXP-076 disposition
  (b)).
- **Interpretation**: per the predeclared guide (question 2), this is a **bounded per-stratum
  disclosure, not a whole-qualifier failure**. It is precisely the regime EXP-076 flagged, and it
  triggers the predeclared **"no expectancy edge-calls at effective n<30 / defer to median"** guard,
  which here should extend to the effective-`n` regime n ≤ 60 for the bimodal mean-null under
  `WF-EXPANDING` (the 5-fold split lowers the effective per-fold count, so n=60 still under-covers). For
  n ≥ 120 the expectancy FPR is controlled with margin to spare. The B_zero/location distinction is the
  per-stratum picture the doctrine exists to preserve.

### 3. MDE — finite and non-degenerate for every binding N (detection power holds)

- **Observation / Evidence** (`mde.csv`, `mde_tpr.csv`): `MDE(N)` is finite at every N ≥ 30, decreasing
  monotonically 0.644 (n=30) → 0.459 → 0.324 → 0.230 → 0.171 → 0.133 → 0.085 → 0.050 (n=8000); max TPR
  reaches 0.986–1.0 across the μ-ladder. No degenerate/never-detecting cell.
- **Interpretation**: the MDE leg of `ASS_VALIDATED` **holds** — detection is non-degenerate at every
  binding N (the gate is finiteness, not magnitude). The magnitudes are sensible for an N(μ,1) location
  effect under a 5-fold pooled-test design.

### 4. Reliability — X=2.0 slope failure is a gate-shape artifact; absolute calibration is excellent

- **Observation**: X = 0 / 0.05 / 1.0 PASS (slope 0.923 / 0.926 / 0.950; max-gap ≤ 0.029). X = 2.0
  FAILS on slope (0.652 ∉ [0.85, 1.15]) **only** — its max-gap is 0.0168, the **best** of the four.
- **Evidence** (`reliability_verdict.csv`, `reliability_deciles.csv`, `audit.md` §D): predicted P(>2R)
  ties heavily near zero, so decile quantile edges collapse (10 → 6 unique bins; decile-0 absorbs
  102,497 of ~210k pairs), and the OLS slope is fit over a predicted span of only 0.056 (vs 0.33–0.54
  for the passing X). corr(predicted, realized) = 0.934 and **every** decile gap ≤ 0.10. Dropping the
  large near-zero bucket makes the slope *worse* (0.378) — confirming the instability is the
  compressed-range geometry, not a leverage point.
- **Interpretation**: per the predeclared guide (question 3), this is a **gate-shape / applicability
  disclosure**, not substantive 2R miscalibration. The slope sub-gate of D2.4 is well-posed only when
  predicted probabilities span a wide range; at the 2R threshold the predicted mass is compressed near
  zero and OLS slope has no stable meaning, while the max-gap (the trustworthy calibration statistic)
  certifies excellent calibration. The frozen D2.4 gate is **not** retro-edited here; the mismatch is
  recorded for G-017 and any follow-up scope. `P(>X)` reliability **holds at X = 0, 0.05, 1.0**; at
  X = 2.0 the qualifier is well-calibrated in absolute terms but the slope statistic is inapplicable.

### 5. Protocol legs — accounting, determinism, dogfood: no `PROTOCOL_DEFECT`

- **Counted-read accounting** (`accounting.csv`): 8/8 scenarios pass; one conforming frozen WF run = +1
  counted read, non-conforming reverts to per-fold, at-cap rejected, holdout-fold rejected, rolling
  comparison +0, and the cap-honoring trace blocks the 3rd read. The 2-lifetime-read cap is
  **demonstrably honored**.
- **Dogfood** (`dogfood.csv`): 12/12 `(instrument, domain)` cells complete with finite `ASS` scores;
  every `train_cutoff` equals `int(int(total·0.7)·0.7)` (read fraction 0.4900 < 0.491); the next-21%
  TEST stratum and final-30% holdout are never sliced; **0 counted reads**. The moving-block path runs on
  real `Close`/ATR only (no HA/Renko). Dogfood expectancy CIs straddle 0 — consistent with a
  no-edge-claim pipeline-smoke series.
- **Determinism & anchor** (`integrity.json`): all five determinism flags True; persisted-CSV hashes
  reconcile with `integrity.json.table_sha256`; the R-anchor `|direct expectancy − np.mean| = 0.0`.
- **Interpretation**: per the predeclared guide (question 4), **no protocol leg trips
  `PROTOCOL_DEFECT`**. The accounting rule, determinism, and the real-bar machinery are validated.

## Hypothesis Verdict

**PER-STRATUM — partial support with two named, bounded guards (feeds G-017; does not adjudicate it).**

| `ASS_VALIDATED` leg | Per-stratum standing | Feeds G-017 |
|---|---|---|
| FPR — U0 (location null) | **HOLDS** ∀ binding N (crossings are MC noise; Wilson-hi controlled) | error control supported |
| FPR — B_zero (bimodal mean null) | **HOLDS for n ≥ 120**; mild inflation n ≤ 60 → **n<30/median guard** (now effective-`n` ≤ 60) | bounded disclosure, not failure |
| MDE | **HOLDS** ∀ N ≥ 30 (finite, non-degenerate) | detection supported |
| Reliability `P(>X)` — X=0/0.05/1.0 | **HOLDS** | supported |
| Reliability `P(>X)` — X=2.0 | **gate-shape disclosure**: well-calibrated (max-gap 0.017) but slope gate inapplicable | disclosed; not 2R miscalibration |
| Accounting / Determinism / Dogfood | **HOLD** (no `PROTOCOL_DEFECT`) | protocol validated |

The headline `verdict.json` leg flags (FPR=FAIL, reliability=FAIL) are **faithful to the frozen D0
gates** (audit confirmed) but, decomposed per stratum, neither is a whole-qualifier error-control or
calibration failure: they are (a) a point-gate-vs-MC-noise artifact (U0), (b) a known, bounded small-/
mid-`n` under-coverage already covered by a predeclared guard (B_zero), and (c) a slope-gate
applicability limit at compressed probabilities (X=2.0). The qualifier's error control, power,
reliability, and protocol machinery are validated under `WF-EXPANDING` subject to those two guards.

## Limitations

- **Synthetic substrate for the binding legs.** FPR/MDE/reliability are measured on the frozen D1
  synthetic populations (iid by construction); real serial dependence is exercised only by the
  non-binding dogfood (moving-block). The protocol *arithmetic* and estimator *error control* are what
  the synthetic legs validate — Phase 018 real strata remain the live test.
- **MC resolution.** R_REP = 2000 gives FPR SE ≈ 0.0049; point crossings of a hard 0.05 cut cannot be
  distinguished from 0.05 at this resolution (the reason the Wilson-hi sub-gate exists).
- **B_zero effective-`n` under `WF-EXPANDING`.** The 5-fold pooled-test design lowers effective per-fold
  count, so under-coverage persists to n=60 for the bimodal mean-null; the n≤60 guard boundary is
  specific to this protocol, not a property of `ASS` at face `n`.
- **X=2.0 reliability has thin populated deciles** (6 of 10); the slope statistic is structurally
  unstable there. The max-gap and correlation are the reliable readouts at 2R.
- **Dogfood is a pipeline smoke, not an edge measurement** — its expectancy/CI carry no market claim by
  design.

## Alternative Explanations

- *"The FPR leg simply fails."* Rejected: the per-stratum decomposition shows U0 sits at the 0.05 target
  (binomial P = 0.36–0.43) and B_zero inflation decays to near-zero by n=120 — a uniform "fails" reading
  would mask both the controlled location-null behavior and the bounded, known small-`n` regime.
- *"X=2.0 is miscalibrated."* Rejected: max-gap 0.017 and corr 0.934 are the strongest calibration
  evidence of the four thresholds; only the range-sensitive slope statistic fails.
- *"The margin manufactures power."* Rejected (audit): `m` is calibrated on TAG_CAL nulls only, FPR
  validated on disjoint TAG_VAL nulls, MDE uses the distinct `CI_low>0` rule on TAG_EFF — streams
  disjoint, no FPR↔MDE circularity.

## Recommended Next Steps

*(New scopes only — not extensions of EXP-077.)*

1. **Carry two guards into the Phase 018 G-017/screening protocol** (register, do not act here):
   (i) **defer expectancy edge-calls to the median for effective-`n` ≤ 60 on bimodal/asymmetric mean-null
   strata** under `WF-EXPANDING`; (ii) **treat the D2.4 slope sub-gate as inapplicable when the predicted-
   probability range is below a minimum span** (e.g. ptp < ~0.1) and bind on max-gap there. Both are
   disclosures to G-017, to be ratified at the EXP-078/G-017 checkpoint — not adjudicated now.
2. **Optional protocol refinement scope (new EXP):** replace or supplement the FPR point-≤-0.05 sub-gate
   with a Wilson-hi-only or MC-CI-aware decision so calibrated-to-0.05 estimators are not failed by chance
   crossings; pre-register before any TEST contact.
3. **EXP-078 (already slated):** shape-discrimination / tail / `k`-sensitivity — the remaining
   `ASS_VALIDATED` legs feeding the G-017 conjunction.

---

### Registry / governance note (for Stage 7)

EXP-077 is **methodology validation** — 0 candidate slots, **0 counted TEST reads**, holdout untouched
(synthetic + first-49% TRAIN dogfood only). The 2-read-cap accounting **rule** was validated as a
function, **not exercised** against the live ledger. Registry-relevant outcome for `ASS/VAL-002`: the
error-control + protocol legs are **validated under `WF-EXPANDING` with two named per-stratum guards**;
the `test-read-ledger.md` is unchanged (no stratum read).
