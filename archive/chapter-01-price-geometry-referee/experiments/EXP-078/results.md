# Results: Experiment EXP-078 — Shape Discrimination + `k`-Sensitivity (`ASS`/VAL-003)

> Phase 017 — CF-CAPGEO-001 Qualifier & Protocol Validation. Last experiment before terminal G-017.
> Synthetic only; 0 candidate slots, 0 counted TEST reads, holdout never touched.
> Audit (Stage 5): **PASS (trust)** — verdict implementation-faithful, 0 Critical, 2 Warning, 4 Info.
> Per-stratum doctrine (LESSON-001): the binding verdict is the **set** of per-stratum labels below.
> No collapsed cross-cell boolean is binding (`collapsed_convenience_flag=false`, NON-BINDING).

## Summary

The frozen `ASS` shape diagnostic `flag = (dip_p < 0.05) OR (|g| > τ_gap=0.30)` was tested on synthetic
populations of **known** shape. **Both binding legs FAIL**, and `k`-sensitivity shows a **routing flip**.
The result is a clean, mechanistic **DISCOVERY_ONLY** for G-017, not a noisy null:

- **Shape discrimination — FAIL.** The diagnostic separates the *obvious* version of its target shape
  (strongly-separated bimodals `B_neg`, `B_strong`) but is **structurally blind to the subtle version** —
  the median-positive dominant mode + small minority catastrophic mode (`B_zero`, `B_pos`). This subtle
  shape is **exactly the CF-HA-HARAMI-001 failure shape and the EXP-074 tail-shape-blind-guard gap this
  experiment was commissioned to close.** Detection on `B_zero`/`B_pos` not only misses the 0.80 floor, it
  **decays monotonically to 0 as `n` grows** — the signature of a sub-threshold true effect seen only
  through small-sample noise.
- **U false-flag — FAIL, but localized.** Clean unimodals false-flag at ~0.14 only at the binding floor
  `n=30`; `n≥60` passes comfortably (≤0.046). A small-sample noise floor of the OR-rule at `τ_gap=0.30`.
- **`k`-sensitivity — ROUTING_FLIP.** Shrinkage *behaviour* (K1) is invariant, but the shrunk-expectancy
  null edge-call FPR (K2) is **fragile to `k`**: doubling `k` to 240 already inflates the null FPR
  catastrophically because shrinkage pulls the null estimate toward a positive pooled prior.

**Net for the qualifier:** `ASS` only **partially** closes the EXP-074 gap. It catches gross bimodality
and strong left-skew but is blind to the subtle median-positive minority-mode shape, and its shrunk
edge-call FPR is not robust to the shrinkage constant.

---

## Detailed Findings

### Finding 1 — Shape discrimination: B-detection is a 2-way split by bimodal shape (BINDING — FAIL)

The pooled "B detection FAIL" is a **disclosure that masks heterogeneity**; the binding picture is
per-shape. Source: `results/shape_rates.csv`, `verdict.json`.

**Detected — strongly-separated bimodals (true `|g|` well above 0.30):**

| type | true \|g\| | dip-bimodal? | detection n=30 | n=60 | n≥120 | per-stratum |
|------|-----------|--------------|----------------|------|-------|-------------|
| `B_strong` | 0.60 | yes (dip_p≈0) | 0.875 | 0.938 | →1.0 | **PASS** (≥0.80 ∀ n≥30) |
| `B_neg` | 0.50 | weak (≈0.30 @8k) | **0.7595** | 0.8545 | →1.0 | **MISS @ n=30 only** (0.7595<0.80), PASS n≥60 |

**Undetectable — subtle median-positive bimodals (true `|g|` below 0.30, not dip-bimodal):**

| type | true \|g\| | dip_p (n=8k) | det n=30 | n=120 | n=500 | n=2000 | n=8000 | per-stratum |
|------|-----------|--------------|----------|-------|-------|--------|--------|-------------|
| `B_zero` | 0.25 | ≈0.99 | 0.4145 | 0.3315 | 0.192 | 0.056 | **0.0** | **FAIL** (decays with n) |
| `B_pos` | 0.067 | ≈0.99 | 0.1885 | 0.026 | 0.0 | 0.0 | 0.0 | **FAIL** (decays with n) |

- **Observation:** detection on `B_zero`/`B_pos` is monotonically **decreasing** in `n` and reaches 0.
- **Evidence:** `shape_rates.csv` rows for `B_zero`/`B_pos`; the combined rate equals the gap-leg rate
  (`dip_rate≈0` throughout) — the dip leg never contributes.
- **Interpretation:** these two strata **fail** the ≥0.80 binding floor at every `n≥30`. Because detection
  falls with `n`, more data makes the diagnostic *worse*, not better — conclusive evidence the true
  population is on the non-flagging side of the frozen rule, and apparent small-`n` detection is sampling
  noise. Binding verdict: **FAIL** (driven by `B_zero`, `B_pos`; `B_neg` also misses at the n=30 floor).

### Finding 2 — Mechanism: both diagnostic legs are blind to the subtle shape

- **Gap leg blind:** `g = (mean − median)/MAD`. Independently re-derived large-`n` truth: `B_zero` `|g|=0.25`,
  `B_pos` `|g|=0.067` — **both below the frozen `τ_gap=0.30`.** So at the population limit the gap leg never
  fires; finite-`n` firing is variance around a sub-threshold value, which shrinks as `n` grows.
- **Dip leg blind:** Hartigan dip `dip_p ≈ 0.99` for both at `n=8000`. The minority catastrophic mode is too
  small/broad (10% at σ=0.6 for `B_zero`; 5% at σ=0.6 for `B_pos`) to carve a visible **antimode** in the
  density — so the population is, to the dip test, unimodal. (Contrast `B_strong`: `dip_p≈0`, strongly
  bimodal; `B_neg` carries detection on the gap leg, dip only marginal.)
- **Consequence:** the diagnostic is not "miscalibrated" — it is **structurally blind** to a population
  whose dangerous mass is concentrated in a small minority mode that neither shifts the robust mean–median
  gap past 0.30 nor produces a dip-test antimode. This is the precise mechanism, not a numeric near-miss.

### Finding 3 — Gate-shape: ASS only partially closes the EXP-074 gap (headline for G-017)

- **The diagnostic was commissioned** (scope §Question) to catch the shape "median-positive dominant mode +
  minority catastrophic mode … the CF-HA-HARAMI-001 failure shape" that a smoothed mean cannot see — the
  same gap that, in EXP-074, let a tail-shape-blind guard veto the one feature explaining the mean's collapse.
- **It catches the gross version** (`B_strong`/`B_neg`) **and misses the subtle version** (`B_zero`/`B_pos`),
  which *is* the dangerous case. This is **"an effect of a shape this gate cannot see," not "no effect."**
- **Interpretation:** `ASS`'s shape leg is a **partial** closure of the EXP-074 gap. A qualifier relying on it
  alone would still pass a population like `B_zero` (90% at +0.15, 10% catastrophic at −1.5, true mean ≈ 0)
  as non-pathological. Carry-forward limitation for Phase 018 and G-017.

### Finding 4 — U false-flag: an n=30 binding-floor effect, not a global failure (BINDING — FAIL)

Source: `shape_rates.csv` (U rows). Combined false-flag rate by `n`:

| type | n=30 | n=60 | n=120 | n≥250 |
|------|------|------|-------|-------|
| `U0` | 0.146 | 0.046 | 0.006 | ≤0.0005 |
| `U1` | 0.1355 | 0.0425 | 0.003 | ≤0.0005 |
| `U2` | 0.152 | 0.044 | 0.007 | 0.0 |
| `U3` | 0.147 | 0.035 | 0.0055 | ≤0.0005 |

- **Observation:** all four U types exceed the 0.05 ceiling (and the Wilson-hi ≤0.075 ceiling) **only at
  `n=30`**; every `n≥60` cell passes, decaying to ≈0 by `n≥250`.
- **Interpretation:** the OR-rule has a **small-sample noise floor** at `τ_gap=0.30` — finite-`n` variance of
  `(mean−median)/MAD` on N(0,1) exceeds 0.30 about 14% of the time at `n=30` (gap leg carries it; dip leg
  ≈0.5%). The D0 bite-check's reported false-flag 0.000 @ `τ_gap=0.30` was evaluated at a single larger `n`
  and did **not** probe the `n=30` binding floor. Because `n=30` **is** a binding stratum, the U leg
  verdict is **FAIL** — but the failure is confined to the floor, and the operating point is sound for
  `n≥60`. (Phase-018 strata will need `n≥60` for a controlled false-flag rate on clean unimodals.)

### Finding 5 — `k`-sensitivity: K1 invariant, K2 routing flip (BINDING — ROUTING_FLIP)

Sources: `k_sensitivity_shrinkage.csv` (K1), `k_sensitivity.csv` (K2), `verdict.json`. Grid `k ∈
{30, 60, 120, 240, 500}`; deployed `k=120` (= median SP population n = EXP-076 `k_shrink`).

- **K1 — shrinkage behaviour: INVARIANT (genuine).** `SHRINK_OK` at all five `k` (weight `n/(n+k)` monotone
  in `n`; sparse-pull ≥0.25 holds ∀ grid `k`). Rich-pull at `n≥2000` grows with `k` by construction
  (0.057 @ k=120 → 0.20 @ k=500) — disclosed, not a flip (EXP-076 predeclared the n=2000 marginal).
- **K2 — null edge-call FPR: ROUTING_FLIP (genuine k-fragility).** Every binding `(null, n)` stratum flips
  `CONTROLLED → INFLATED` as `k` rises. The flip happens at **`k=240` (the 2× multiplier — a core grid
  point, not an extreme anchor)** and `k=500`:

  | stratum | k=30 | k=60 | k=120 (deployed) | k=240 | k=500 |
  |---------|------|------|------------------|-------|-------|
  | `U0`/n=120 | 0.0 | 0.0005 | 0.048 (CTRL) | 0.873 | 1.0 |
  | `B_zero`/n=120 | 0.0 | 0.0 | 0.0485 (CTRL) | 0.9855 | 1.0 |
  | `U0`/n=30 | 0.001 | 0.0035 | 0.054 (label INFLATED*) | 0.7205 | 1.0 |

  \* **Warning (audit):** the deployed-`k` `INFLATED` label on `U0`/n=30 (fpr 0.054 vs target 0.05,
  Wilson-hi 0.0648 ≤ 0.075) is **self-calibration MC noise** — the margin is the Q95 of the same null at
  k=120, so the deployed-`k` FPR is pinned to ~0.05 by construction. **Do not read per-cell deployed-`k`
  labels literally.** The binding finding is the **k-fragility itself**, which holds regardless of that one
  cell.
- **Mechanism:** the margin is frozen at `k=120`; increasing `k` shrinks the null estimate toward the
  positive SP pooled prior (`pool_mean = +0.518`, dominated by the right-skew `Splus` members). The shrunk
  null center for `U0` crosses the fixed margin between `k=120` (+0.414) and `k=240` (+0.460 > margin 0.415)
  → FPR explodes (0.39–0.87 @ k=240) and saturates at 1.0 @ k=500. A mechanical consequence of the
  estimator, not stochastic.
- **Coverage leg not swept (audit Warning 2):** the pre-registered k-sweep listed **three** k-dependent
  dispositions (shrinkage behaviour, CI coverage, null edge-call FPR); the run executed **two of three** —
  the EXP-076 D2.1 CI-coverage leg was not swept. This **cannot rescue the verdict** (routing-invariance
  requires *every* binding disposition invariant; K2 already flips, and a missing leg can only add flips),
  but the k-sweep disclosure is therefore **partial**, not complete.

### Finding 6 — S-family asymmetry (DISCLOSED, NON-BINDING)

Source: `shape_skew.csv`. As pre-registered, `Sminus`/`Sminus0` (left-skew, mean-weak) flag via the **gap
leg** (e.g. `Sminus` 0.385 @ n=30, falling to ≈0 by large `n`); the dip leg stays ≈0 (unimodal). This is the
**intended** behaviour — the gap leg is designed to see left-skew asymmetry — and is reported as a feature,
not a false flag. Notably, the S-family flag rate also **decays with `n`** (true `|g|` for these skews sits
below 0.30 at the population limit), echoing the `B_zero`/`B_pos` pattern: the gap leg fires on small samples
of mildly-asymmetric populations but not asymptotically. Non-binding; does not affect the U-vs-B verdict.

### Integrity (procedural — PASS)

`integrity.json`: cross-experiment anchor reconciles to **both** EXP-076 (diff 0.0) and EXP-077 (diff 0.0);
self-anchor `direct_expectancy == mean(x)` diff 0.0; determinism shape/K1/K2 all hash-match; `mad_zero_total=0`;
`diptest 0.11.0` pinned. The shape extension did not perturb the `xen.ass` core.

---

## Mapping to pre-registered criteria (scope §Success/Failure)

| Pre-registered binding criterion | Threshold | Observed | Verdict |
|----------------------------------|-----------|----------|---------|
| U false-flag ≤ 0.05 (Wilson-hi ≤ 0.075) on **every** U, n≥30 | 0.05 / 0.075 | n=30: 0.135–0.152 (Wilson-hi up to 0.168); n≥60 pass | **FAIL** (n=30 floor) |
| B detection ≥ 0.80 on **every** B, n≥30 | 0.80 | `B_strong` pass; `B_neg` 0.76 @n=30; `B_zero`→0.0, `B_pos`→0.0 | **FAIL** (`B_zero`,`B_pos`,`B_neg`@30) |
| `k`-sensitivity routing invariant (or bounded+disclosed) across grid | invariant / extreme-anchor-only | K1 invariant; K2 flips at k=240 (2×, core grid) | **ROUTING_FLIP (FAIL)** |
| Determinism (D6) second pass byte-identical | byte-identical | shape/K1/K2 hash-match | **PASS (no PROTOCOL_DEFECT)** |

**Pre-registered outcome:** "FAIL → feeds G-017 `DISCOVERY_ONLY`" on any U stratum false-flag > 0.05, OR any
B (n≥30) detection < 0.80, OR an unbounded routing flip. **All three FAIL conditions are met.** This is a
**DISCOVERY_ONLY** result, recorded per stratum, no clean PASS. Determinism holds, so this is **not** a
`PROTOCOL_DEFECT`.

---

## What this means for G-017 and Phase 018

1. **`ASS` partially closes the EXP-074 gap.** The shape leg reliably catches gross bimodality and strong
   left-skew but is **structurally blind** to the subtle median-positive minority-catastrophe shape
   (`B_zero`/`B_pos`) — the very CF-HA-HARAMI-001 shape it was meant to catch. A qualifier leaning on this
   diagnostic alone would still admit such a population. **This blind spot is the primary carry-forward
   limitation** and should be on the record before any Phase-018 candidate is adjudicated against `ASS`.
2. **The frozen operating point needs `n≥60` for clean unimodals.** At the `n=30` binding floor the OR-rule
   false-flags clean nulls ~14%. Phase-018 strata read through this diagnostic should be expected to hold
   only at `n≥60`.
3. **The shrunk edge-call FPR is fragile to `k`.** At the deployed `k=120` the disposition is at target by
   construction, but the FPR is not robust: doubling `k` inflates it catastrophically. Any Phase-018 reliance
   on the shrunk-expectancy edge-call must treat `k` as a load-bearing choice and not assume robustness — the
   default `k` sits near the boundary where shrinkage-toward-prior begins to dominate.
4. **k-sweep disclosure is partial** (2 of 3 pre-registered dispositions). The verdict is unaffected (FLIP
   stands), but the CI-coverage leg's `k`-behaviour is undocumented.

These are findings for G-017 / the Phase-017 retrospective to adjudicate; this experiment does not itself
re-tune `τ_gap` or `k` (frozen at D0).

## Limitations

- Synthetic-only by design: results characterize the diagnostic's behaviour on **known-shape** populations,
  not real event-return populations (that is Phase 018). The synthetic B-family was constructed to span the
  CF-HA-HARAMI-001 shape; real populations may sit anywhere relative to `τ_gap`.
- The B-family is four discrete shapes; the "detectable vs blind" boundary is bracketed (`B_neg` |g|=0.50
  detectable, `B_zero` |g|=0.25 blind) but not finely mapped — the exact `|g|` crossover near 0.30 is implied,
  not measured.
- K2 self-calibration makes the deployed-`k` per-cell labels noise-dominated near target (see Finding 5);
  only the **across-`k` fragility** is a robust reading.
- The CI-coverage k-leg was not swept (audit Warning 2).

## Alternative explanations (considered and rejected)

- *Implementation bug manufacturing the FAIL?* Rejected — the auditor independently reproduced the mixture
  means (to 1e-4), the U0 false-flag rates (exactly), the sub-0.30 true `|g|` for `B_zero`/`B_pos`, and the K2
  shrink-toward-prior mechanism. Integrity anchors diff 0.0; determinism holds. The FAIL is implementation-faithful.
- *Insufficient MC power?* Rejected — `R_REP=2000` with Wilson intervals; the `B_zero`/`B_pos` decay to
  **exactly 0** at large `n` and `U` decay to 0 at `n≥250` are population-limit behaviours, not power gaps.

## Recommended next steps (candidate follow-ups only — for the retrospective / G-017 to decide)

1. **Map the `|g|` detectability crossover** for the gap leg on a finer bimodal grid around `τ_gap=0.30`
   (new EXP scope) — to quantify exactly which subtle bimodal shapes `ASS` can and cannot see.
2. **A shape leg with a minority-mass / left-tail-mass detector** complementary to dip + mean-median gap,
   targeting the small-minority-catastrophe shape the current legs miss (new EXP scope; do not retro-edit the
   frozen D2.5 diagnostic).
3. **Re-anchor or `n`-condition the false-flag operating point** so the `n=30` floor is controlled, or
   formally restrict the diagnostic's binding domain to `n≥60` (G-017 decision, not an in-experiment change).

These are noted, not initiated; `τ_gap` and `k` remain frozen at D0 in this experiment.
