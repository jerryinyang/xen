# Phase 017 D0 — Predeclarations (CF-CAPGEO-001 Qualifier & Protocol Validation)

**Status:** **RATIFIED — G0 PASS (2026-06-20).** D1–D6 ratified by the operator as drafted and now
**FROZEN**; the bite/fixture check is GREEN on all four numeric thresholds (`bite-check/bite_check_report.json`,
SEED 20260620). No amendment without a dated `D0-amendment-*` file in this directory. Result-producing
code (EXP-076 →) is now authorized; the EXP-078 `k`-grid remains a pre-registered sensitivity sweep,
not a selection.

**Prior status (for the record):** DRAFT — CANDIDATE VALUES POPULATED (2026-06-20); G0 PENDING. D1–D6
carried concrete candidate values; the numeric thresholds in D2 (and `τ_gap` in D2.5) required a
bite/fixture check before ratification — confirmed neither vacuous nor impossible on the clean `U`
family (and the `U`-vs-`B` ROC for the shape threshold), output recorded below.

**Bite-check result (run 2026-06-20, `bite-check/bite_check.py` → `bite-check/bite_check_report.json`, SEED 20260620):**
`OVERALL: RE-ANCHOR NEEDED` → resolved.
- D2.1 coverage **OK** (0.896 ∈ [0.86,0.94]); D2.5 `τ_gap` **OK** (@0.30 false-flag 0.000, detection
  0.999, feasible window [0.105,0.435]).
- D2.1 recovery **re-anchored 0.5 → 0.85·SE** (0.5 was below the half-normal `0.6745·SE` floor —
  impossible for an unbiased estimator); script constant updated, re-run green.
- D2.2 FPR **re-anchored to a calibrated-margin (`m_cell` analog)** binding; bite-scale raw FPR 0.053
  (wilson_hi 0.069) is within MC noise of 0.05 — confirm at production bootstrap scale in EXP-077.
**Checkpoint:** `2026-06-20-017-capgeo-qualifier-validation`
**Governing design:** `design.md` (this directory).
**Family:** `CF-CAPGEO-001` (REGISTERED, SCREENING-GATED).
**Scope of this D0:** validation of the `ASS` qualifier and `WF-EXPANDING` protocol only. **No
candidate screening, 0 candidate slots, 0 counted TEST reads, holdout never touched.**
**Discipline (binding throughout Phase 017):** synthetic substrates + current first-70% TRAIN-only
dogfood; all return/expectancy metrics on real prices; deterministic (fixed seeds, byte-identical
second pass); no parameter tuned against any TEST or holdout data.

---

## D1 — Synthetic data-generating processes (frozen) — CANDIDATE VALUES

Returns are in **ATR units** (matching the programme's per-event ATR-normalised return convention),
with the risk unit `R = 1.0 ATR`. Ground truth for expectancy and shape is closed-form where
available; **median ground truth is a 10⁷-draw Monte-Carlo estimate** recorded at ratification.
Master seed `20260620`; per-draw seed = deterministic hash of `(type_id, n, replicate)`.
**Replicates `R_REP = 2000`** independent draws per `(type, n)` for FPR / coverage / MDE estimation.
Sample sizes per type: `n ∈ {15, 30, 60, 120, 250, 500, 1000, 2000, 8000}` (n<30 = sparse stress;
≥30 is the programme power floor).

**Unimodal `U` — N(μ, 1.0²)** (location-only; mean = median = μ):

| Type | μ (= expectancy = median) | Role |
| --- | --- | --- |
| `U0` | 0.00 | null (FPR) |
| `U1` | +0.05 | weak edge (MDE) |
| `U2` | +0.10 | edge |
| `U3` | +0.20 | strong edge |

**Skewed `S` — skew-normal SN(ξ, ω, α)**, ground truth via MC. Left-skew is the dangerous
median-positive / mean-weak case:

| Type | ξ | ω | α | Shape | ≈ mean | ≈ median |
| --- | --- | --- | --- | --- | --- | --- |
| `Splus` | 0.00 | 1.0 | +4 | right-skew | +0.62 | +0.40 |
| `Sminus` | +0.55 | 1.0 | −4 | left-skew | −0.07 | +0.17 |
| `Sminus0` | +0.62 | 1.0 | −4 | left-skew (mean≈0) | 0.00 | +0.24 |

**Bimodal `B` — mixture `w·N(μ₁,σ₁²) + (1−w)·N(μ₂,σ₂²)`** (the CF-HA-HARAMI-001 failure shape:
dominant median-positive mode + minority catastrophic q05 mode; median via MC):

| Type | w | (μ₁,σ₁) | (μ₂,σ₂) | mean (closed-form) | ≈ median | Note |
| --- | --- | --- | --- | --- | --- | --- |
| `B_neg` | 0.85 | (+0.15, 0.5) | (−2.0, 0.6) | **−0.1725** | ≈ +0.15 | median +, mean − (harami case) |
| `B_zero` | 0.90 | (+0.15, 0.5) | (−1.5, 0.6) | **−0.015** | ≈ +0.15 | median +, mean ≈ 0 |
| `B_pos` | 0.95 | (+0.10, 0.5) | (−1.0, 0.6) | **+0.045** | ≈ +0.10 | median +, mean + (still bimodal) |
| `B_strong` | 0.80 | (+0.20, 0.5) | (−2.0, 0.6) | **−0.24** | ≈ +0.20 | wide separation |

**Sparse / uneven `SP`** — not a new shape but a *population* assembled from the `U`/`S`/`B` types
above instantiated at mixed `n` drawn so the **median sample size ≈ 120** (so the default shrinkage
constant `k = median n = 120` is exercised): sparse members (n=15,30) must be pulled toward the
pooled prior; rich members (n≥2000) must be left essentially unmoved.

## D2 — Fixture/bite-calibrated tolerances (no magic numbers — retrospective §5.3) — CANDIDATE VALUES

Each numeric below is a **candidate** to be confirmed by a **bite check** before G0 ratification: run
the criterion on the clean `U` family (and, for the shape threshold, on the `U`-vs-`B` ROC) and
confirm it is **neither vacuous** (passes regardless) **nor impossible** (fails even when the
estimator is correct). Re-anchor any candidate that fails its bite check; record the bite output in
`D0-amendment-*` or inline at ratification.

**D2.1 — Recovery (EXP-076).** With `SE_true(n)` the true sampling SE of the estimand at `n`
(`σ_type/√n` for expectancy; the MC median-SE for the median):

- **Bias:** `median_over_replicates( |estimate − truth| ) ≤ 0.85 · SE_true(n)` for expectancy **and**
  median, on every `(type, n)`. **Re-anchored 0.5 → 0.85 (bite check 2026-06-20):** an *unbiased*
  estimator's median absolute error floors at `0.6745 · SE` (half-normal median), so `0.5` was
  mathematically impossible; `0.85` clears a correct estimator with ~20% margin while a `≥1·SE`
  systematic bias still fails (the bite confirmed: correct 0.67·SE pass, +1·SE-biased 1.06·SE fail).
  *(Alternative the operator may prefer: bind signed bias `|mean(estimate − truth)| ≤ 0.1·SE`, which
  separates bias from sampling noise directly; the median-|error| form above is what the bite script
  tests.)*
- **Coverage:** the `ASS` 90% bootstrap CI covers the ground-truth estimand in **[0.86, 0.94]** of
  replicates (nominal 0.90; MC band for `R_REP=2000` ≈ ±0.013, widened to ±0.04 to absorb estimator
  imperfection — confirm the ±0.04 on the `U` bite check).
- **Shrinkage behaviour:** shrinkage weight `n/(n+k)` monotone non-decreasing in `n`; for sparse
  members (n ≤ 30) the shrunk estimate is pulled ≥ 25% of the way from the raw estimate toward the
  pooled prior; for rich members (n ≥ 2000) it moves < 5%.

**D2.2 — FPR (EXP-077).** On each true-null type (`U0`, `B_zero` treated as a median/expectancy
null per its leg), the false-positive edge-call rate must be **≤ 0.05** with **Wilson upper 95%
≤ 0.075**. **Re-anchored to a calibrated-margin binding (bite check 2026-06-20):** the bare
`expectancy CI_low > 0` percentile-bootstrap rule measured FPR = 0.053 (wilson_hi 0.069) — within MC
noise of 0.05 but reflecting the percentile bootstrap's known mild one-sided inflation. Per the
programme's `m_cell` lesson (retrospective §2.2; Phase 009/EXP-070), the binding rule is therefore
**`CI_low > m`**, where `m` is the synthetic-null-calibrated margin that drives measured FPR ≤ 0.05 at
the realized structure (not a loosened target). Confirm at **production scale** (`N_REP ≥ 2000`,
`N_BOOT = 10_000`), where the estimate tightens. Mirrors the EXP-027/070 standard (max FPR there 0.034).

**D2.3 — MDE (EXP-077).** `MDE(type, n)` = smallest true μ at which `TPR(expectancy CI_low>0) ≥ 0.80`
over replicates. **PASS** iff `MDE` is **finite (non-degenerate CI)** for every `n ≥ 30`; the full
`MDE(n)` curve is reported (degeneracy, not magnitude, is the gate — a degenerate/never-detecting CI
is the failure mode being screened).

**D2.4 — Reliability of `P(return>X)` (EXP-077).** On held-out folds, bucket predicted
`P(return>X)` into deciles and compare to realized frequency: **max |predicted − realized| ≤ 0.10**
across deciles **and** calibration-line slope ∈ **[0.85, 1.15]**. (Reliability check, `ass.md` §A.6.)

**D2.5 — Shape discrimination (EXP-078).** Diagnostic = **(a)** Hartigan dip-test p-value
(bimodality) **and (b)** robust mean–median gap `g = (mean − median) / MAD` (left-tail asymmetry).
**Flag bimodal/asymmetric** iff `dip_p < 0.05` **OR** `|g| > τ_gap`. `τ_gap` is set at the
**bite-check ROC operating point** on the `U`-vs-`B` fixtures; **candidate `τ_gap = 0.30`**. PASS iff,
at the chosen operating point, the **false-flag rate on `U` ≤ 0.05** and **detection on `B` ≥ 0.80**.

## D3 — `ASS` configuration (frozen) — CANDIDATE VALUES

- **Bandwidth:** k-nearest-neighbor adaptive bandwidth, **`k_bw = max(5, round(√n))`** (the single
  bandwidth method throughout; not mixed with balloon estimation without re-validation).
- **Shrinkage:** empirical-Bayes blend toward the pooled (all-types) KDE, `weight = n / (n + k)`.
  **`k` default = median sample size across signal types** (the one tunable knob).
- **`k`-sensitivity grid** (EXP-078, pre-registered sweep, not a selection):
  **`{0.5×, 1×, 2×} · median-n`** plus the fixed anchors **`{30, 500}`**.
- **Bootstrap:** `N_BOOT = 10_000` (programme convention); CI = 5th/95th percentile. Synthetic iid
  data → simple within-type resample; the real-data dogfood → **moving-block** bootstrap with
  `b = round(m^(1/3))` (programme convention). Seed deterministic: synthetic `(type, n, replicate)`;
  real-data `(instrument, domain)`.
- **Scoring outputs (all emitted, none collapsed):** expectancy, median, tail/bimodality diagnostic
  (D2.5), and `P(return > X)` for **X ∈ {0, breakeven, 1R, 2R}** with the D2.4 reliability check.
  **In synthetic units `breakeven = 0.05 ATR`** (placeholder for the real per-instrument cost in
  Phase 018), **`1R = 1.0`, `2R = 2.0`**.
- **Shrinkage target:** each (entry-substrate × instrument × domain) cell is a signal type, pooled
  toward the per-substrate population (Phase 018 application; Phase 017 uses the synthetic analogue —
  the `SP` population of mixed-`n` types).

## D4 — `WF-EXPANDING` protocol parameters (frozen) — CANDIDATE VALUES

**Scope of operation.** The expanding window operates **entirely within the first-70% analysis set**
(chronological per instrument file). Train grows; test folds are later analysis-set slices. **The
final-30% global holdout is NEVER a fold** — it remains the separate, sealed one-shot.

**Schedule (fractions of the analysis set; candidate):**

- **Initial train** = first **0.50** of the analysis set.
- **5 expanding folds** of **0.10** each, rolling each tested fold into the next train:

  | Fold | Train | Test |
  | --- | --- | --- |
  | 1 | [0.00, 0.50] | (0.50, 0.60] |
  | 2 | [0.00, 0.60] | (0.60, 0.70] |
  | 3 | [0.00, 0.70] | (0.70, 0.80] |
  | 4 | [0.00, 0.80] | (0.80, 0.90] |
  | 5 | [0.00, 0.90] | (0.90, 1.00] |

  (`1.00` = end of analysis set = 70% of full data.)
- **Minimum fold size:** **≥ 30 events** per `(stratum, fold)`; below-floor folds are **disclosed,
  not silently dropped**.
- **Rolling-window comparison (disclosed, 0 extra reads):** fixed-width **1y / 2y / 3y** trains on
  the same folds.
- **Aggregation → one stratum verdict:** fold-clustered moving-block bootstrap (cluster = fold),
  emitting expectancy + median + tail diagnostic; exactly **one** verdict per stratum. (The Phase 018
  verdict *conjunction* is a Phase 018 D0 item; Phase 017 validates that the accounting and FPR hold
  under this protocol.)

**D4.1 — Counted-read accounting rule (binding — the novel governance design).**

> **One full pre-declared, frozen `WF-EXPANDING` run on a stratum = exactly ONE counted TEST read**
> against that stratum's 2-lifetime cap. The individual folds are **in-protocol disclosures, not
> separate counted reads** — they make no stratum-specific *selection*; only the aggregate WF verdict
> is the binding stratum-specific inference (the same logic as the ledger's portfolio-aggregate rule).

This holds **only if all** of the following are satisfied; otherwise each affected fold reverts to a
**separate counted read**:

1. **Freeze-before-OOS.** The entire WF schedule (fold boundaries, the candidate/exit definition, any
   per-fold re-fit rule, the aggregation + verdict rule, all seeds) is frozen and **hash-pinned
   before any post-initial-train row of that stratum is read.**
2. **No between-fold selection.** The candidate and all parameters are fixed across folds. Any
   per-fold re-fit must be a **pre-declared mechanical, causal** rule using only data up to that fold
   — never a human selection between folds (which would make each fold a selection event = a counted
   read each).
3. **Predeclared aggregation + verdict.** One verdict per stratum, by the rule above.
4. **Holdout never a fold;** the rolling 1y/2y/3y comparisons run on the already-read folds and add
   **no** counted reads.

A stratum may receive at most **2 such WF runs lifetime**; the second is disclosed as
weakened-evidence (existing ledger rule), and an at-cap stratum is permanently capped.

**D4.2 — Phase 017 application (preserves 0 counted TEST reads).** In Phase 017 the protocol is
validated on **synthetic** data (no real holdout/TEST to protect). The **current-data dogfood runs
`WF-EXPANDING` within the current first-49% TRAIN region only** (treated as a self-contained dataset
to confirm the pipeline runs on real bars) and **never** touches the real next-21% TEST stratum or
the holdout — so `test-read-ledger.md` is unchanged by Phase 017. The accounting rule (D4.1) is
*validated* here; it is *exercised* against the ledger only in Phase 018, on the post-INFR-003
5-year strata.

## D5 — G-017 mechanical verdict rule

```
ASS_VALIDATED  iff  EXP-076 recovery within D2 tolerance on ALL D1 types
                AND  shrinkage weight monotone in n
                AND  EXP-077 FPR ≤ 0.05 on ALL synthetic null types (margin-calibrated, m_cell analog; D2.2)
                AND  EXP-077 MDE finite per domain
                AND  EXP-077 P(return>X) reliability within D2 band
                AND  EXP-077 counted-read accounting honors the 2-read cap
                AND  EXP-078 shape diagnostic discriminates bimodal vs unimodal at the
                     D2 threshold with controlled false-flag rate
                AND  EXP-078 k-sensitivity routing-invariant (or bounded + disclosed)

DISCOVERY_ONLY  iff  any of the above fails / is power-limited, but no fundamental defect
                     -> ASS non-binding; frozen referee suite remains binding in Phase 018

PROTOCOL_DEFECT iff  WF-EXPANDING accounting cannot honor the 2-read cap OR determinism fails
                     -> fix and re-run the affected read before any Phase 018 TEST design
```

The verdict is mechanical and predeclared; the explanation it produces is not predeclared (freeze the
rule, not the story — retrospective §2.1).

## D6 — Determinism & real-price discipline

- All RNG seeds fixed and recorded; a second full pass of every experiment is byte-identical.
- All return/expectancy metrics computed on **real prices** (`RealOpen/High/Low/Close`); no
  HA-price or Renko brick-price returns anywhere in Phase 017.
- No tuning against any TEST or holdout data; `ASS` parameters frozen at G0 (the EXP-078 `k`-grid is
  a pre-registered sensitivity sweep, not a selection).

## Slot & TEST accounting

- **0 candidate slots** consumed (methodology validation, not candidate screening).
- **0 counted TEST reads.** Synthetic substrates + current first-70% TRAIN-only dogfood; the next-21%
  TEST stratum and final-30% holdout are never sliced or materialized. The `test-read-ledger.md` is
  unchanged by Phase 017. (INFR-003 will re-materialize the ledger on the new 5-year data before
  Phase 018.)
- Holdout sealed throughout.
