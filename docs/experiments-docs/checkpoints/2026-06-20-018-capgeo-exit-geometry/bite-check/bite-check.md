# Phase 018 D9 Bite Check — Spec

**Purpose.** Before G0 ratification, calibrate and confirm the D0 §D4 separability-gate thresholds
named in §D9 — the **S2** tail non-residual thresholds (`τ_tail`, `δ`, catastrophe anchor `K_tail`),
the **S1** matched-control edge-call margin (`m`, the `m_cell` standard), and the **D3**
derivation-quantile estimability — are each **neither vacuous** (do not pass regardless of shape)
**nor impossible** (pass when the shape is genuinely separable), then **FREEZE** them. This is the
cheap fixture/bite check the retrospective §5.3 prescribes ("measure whether the threshold actually
discriminates on synthetic data"). It is **pre-G0 calibration tooling, not an experiment**: no market
data, no holdout, no multiplicity slot. It validates the *gate constants*, not any candidate.

**Why this gate is built on minority-mass, not `ASS`.** EXP-078 (G-017 `DISCOVERY_ONLY`) proved the
`ASS` mean–median-gap / dip-test shape diagnostic is **structurally blind** to the subtle
median-positive minority-catastrophe shape (`B_zero` true |g|=0.25; `B_pos` |g|=0.067) — the exact
CF-HA-HARAMI-001 failure shape. Phase 018 therefore makes the **separability gate (S2), not `ASS`,
the binding shape-guard** (design §8), built on the **minority-mass / left-tail-mass** detector
`ASS` lacks. This bite check verifies that detector actually separates the harami failure shape from
a clean separable shape on synthetic data before the thresholds are frozen.

**It does not replace EXP-080→.** The bite uses a deliberately *minimal* reference setup (sample
quantiles + percentile bootstrap; a MAD-anchored minority-mass read; dip-gated antimode) only to
calibrate the gate constants. The full per-cell screening machinery runs post-G0 under
`python/experiments/` and `python/src/xen/`.

## What it checks (maps 1:1 to D9)

| D9 item | Bite test | Re-anchor if |
| --- | --- | --- |
| **S2 `τ_tail`, `δ`** (D4 S2) | ROC of the two-leg S2 rule on a **known-separable** fixture (unimodal-positive, negatives) vs the **known-harami** Phase-017 shapes `B_neg`/`B_zero` (positives): find an operating point with separable false-flag ≤ 0.05 **and** binding-harami detection ≥ 0.80 (the D2.5 analog, using minority-**mass** not the mean–median gap). | the candidate `(K_tail, τ_tail, δ)` sits outside the feasible window → re-anchor to the reported window. |
| **S2 operating floor** | Re-run the ROC at the floor `n` and a sub-floor `n`: confirm the reliable operating regime and the deferred regime. | re-anchor the disclosed floor `n` to where Wilson-hi(false-flag) ≤ 0.075 with binding detection ≥ 0.80. |
| **S1 margin `m`** (D4 S1) | Under the null (candidate `X_fav` has no edge over its matched-random control), bind `CI_low(difference) > m_cell` with `m_cell = Q95` of the null `CI_low`; confirm the calibrated FPR ≤ 0.05 (Wilson-hi ≤ 0.075) and `m_cell` finite/non-degenerate. | the calibrated FPR materially exceeds 0.05 → adjust bootstrap/α before ratification. |
| **D3 quantile estimability** (D3) | At the ≥30-event floor confirm `MFE_med/MFE_q40/TTP_q75/MAE_q90` are finite/non-degenerate **and** the adverse leg `m_anti else MAE_q90` is always well-defined; disclose `m_anti` dip-resolution power across `n`. | a quantile is non-estimable at n≥30, or the adverse leg is ever undefined → raise the derivation floor. |

## How to run

```bash
python docs/experiments-docs/checkpoints/2026-06-20-018-capgeo-exit-geometry/bite-check/bite_check.py
```

Deterministic (`SEED=20260621`); numpy + scipy (+ diptest for `m_anti`). Prints a verdict table and
writes `bite_check_report.json` beside the script (frozen values + ROC grid). **Record the report at
G0 ratification**; the frozen values are written into `D0-predeclarations.md` §D9 inline.

## Frozen values (GREEN 2026-06-21) — recommended for G0 ratification

| Threshold | Frozen value | Basis |
| --- | --- | --- |
| `K_tail` (catastrophe anchor) | **3.0** | tailmass = fraction below `median − 3·MAD` (the separated catastrophic-minority boundary, not the bulk's shoulder) |
| `τ_tail` (S2 minority-mass cap) | **0.06** | @n=250: separable false-flag 0.006 (Wilson-hi 0.009); det `B_neg`=1.000, `B_zero`=0.913 |
| `δ` (S2 relative-q05 tolerance, ATR) | **0.40** | complementary deep-catastrophe leg (catches `B_neg`); paired with `τ_tail` for the feasible window |
| `m` (S1 edge-call margin) | **`m_cell` = Q95(null `CI_low`)**, per-cell | calibrated FPR 0.050 (Wilson-hi 0.058); recomputed per realized structure in EXP-083 at `N_BOOT=10_000` |
| S2 operating floor | **n ≥ 120** | binds on Wilson-hi(false-flag) ≤ 0.075 at n=120 (0.048); infeasible at n=60 (0.160) → deferred |

**S2 design note (the two legs are complementary, as D4 intends).** The **tailmass** leg catches the
separated minority mode (`B_zero`, mode at −1.5, which the relative-q05 leg misses because its q05 is
not worse than a wide matched-random control). The **relative-q05** leg catches deep catastrophes
(`B_neg`, mode at −2.0). S2 FAILS (detects) if *either* leg trips, so the binding harami shapes are
covered while the separable fixture passes both.

**Disclosed limitations (carried to G0 / EXP-083):**
- **`B_pos` blind spot persists but is economically benign — DISPOSITION (harm-vs-visibility map).**
  S2 detection of `B_pos` is 0.056 at n=250 (5% mass at −1.0 ATR), mirroring EXP-078. The
  `bpos_harm_visibility_map` disclosure (in `bite_check_report.json`) sweeps the minority
  (mass ∈ {0.02,0.05,0.10,0.15} × depth ∈ {−0.5,−1.0,−1.5,−2.0,−3.0}) plane and shows the blind region
  and the harm region are **anti-correlated**:
  - every blind cell (det < 0.80) with a real tail has **true mean > 0** (genuinely positive
    expectancy — missing it is correct, not a failure);
  - every **materially-negative-mean** shape (the CF-HA-HARAMI-001 trap: median+, expectancy dead) is
    **DETECTED** (det 0.90–1.00: `w=0.10, depth≤−1.5`; `w=0.15, depth≤−1.5`);
  - the **single** "blind + harmful" cell across the 20-cell plane is `w=0.05, depth=−3.0` with true
    mean **−0.008** (break-even) — which the **frozen referee suite rejects on its expectancy/
    materiality leg anyway** — and S2 still catches it 55% of the time.

  **Disposition: accept the blind spot; do not tune the detector.** A minority shallow-and-small enough
  to escape S2 is too shallow-and-small to kill expectancy. Lowering `K_tail` cannot recover `B_pos`
  (the `B_pos`↔unimodal tailmass separation is intrinsically tiny — it only raises the separable
  false-flag). The residual is closed by three backstops, all already in the design: **(1)** the frozen
  referee suite (binding, tests expectancy directly — a break-even/negative shape fails it); **(2)** the
  **S1** attribution leg (orthogonal to tail shape); **(3)** the **EXP-081 descriptive minority-mass /
  left-tail read** reported per cell so the shallow-small minority is visible to the human / separability
  argument even where S2's gate cannot flag it. (Optional escape hatch, not initiated: a future
  EXP-079-style shape-leg upgrade — only warranted if a real `B_pos`-shaped, suite-passing candidate
  with a concerning tail actually appears.)
- **Operating floor n ≥ 120** — S2 is reliable only at n ≥ 120 (slightly stricter than the carried
  `ASS` n ≥ 60 floor because the relative-q05 leg adds small-n noise). Cells below the floor (some 4h
  cells) get **S2 deferred + disclosed**; adjudication is carried by the frozen referee suite (binding
  regardless) plus the median/tail disclosure.
- **`m_anti` is power-limited** — the dip-gated antimode resolves a split only at large n (finite-rate
  ~0.02/0.45/0.95 at n=30/250/500), so the D3 adverse leg `m_anti else MAE_q90` predominantly uses the
  **MAE_q90 fallback** at realistic cell sizes; `m_anti` engages only in large-n cells. This does
  **not** weaken the shape-guard — S2 uses minority-**mass** (tailmass), not the dip.

## Re-anchor recorded during calibration

- **D3 estimability sub-requirement (impossible → re-anchored).** A first draft required `m_anti` to
  be FINITE on a bimodal MAE at n=30. Hartigan's dip is underpowered at small n (the same EXP-078
  finding), so this is impossible, not a defect — and D3 already anticipates it with the
  `m_anti else MAE_q90` fallback. Re-anchored to the binding requirement (quantiles estimable at n≥30
  + the derivation rule always well-defined via the finite fallback), which passes at 0.000
  non-estimable / 0.000 undefined.

## Acceptance

The bite check "passes" when **every** row above is `OK` (or has a recorded re-anchored value). A
green bite check is a precondition for, not a substitute for, operator G0 ratification of the frozen
`(K_tail, τ_tail, δ, m, floor)` in §D9.
