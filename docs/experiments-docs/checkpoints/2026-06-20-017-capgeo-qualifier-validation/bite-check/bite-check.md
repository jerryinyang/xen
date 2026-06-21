# Phase 017 D2 Bite Check — Spec

**Purpose.** Before G0 ratification, confirm every candidate threshold in `D0-predeclarations.md` §D2
is **neither vacuous** (passes regardless of estimator quality) **nor impossible** (fails even when
the estimator is correct), and **re-anchor** any that fails — the cheap fixture/bite check the
retrospective §5.3 prescribes ("measure whether the threshold actually discriminates on synthetic
data"). This is **pre-G0 calibration tooling, not an experiment**: no market data, no holdout, no
multiplicity slot. It validates the *gate constants*, not any candidate.

**It does not replace EXP-076/077/078.** The bite check uses a deliberately *minimal* reference
estimator (shrinkage-weighted sample statistics + bootstrap; closed-form shape proxies) only to test
the thresholds. The full `ASS` (kNN-bandwidth KDE + empirical-Bayes shrinkage + bootstrap, Hartigan
dip) is implemented and validated in EXP-076–078, post-G0, under `python/src/xen/`.

## What it checks (maps 1:1 to D2)

| D2 item | Bite test | Re-anchor if |
| --- | --- | --- |
| **D2.1 recovery bias** (`≤ 0.5·SE_true`) | On the clean `U` family a *correct* estimator must PASS (not impossible); a *biased* estimator (+1·SE constant) must FAIL (not vacuous). | correct estimator fails, or biased estimator passes → widen/narrow the `0.5` factor to the smallest value the correct estimator clears with margin. |
| **D2.1 coverage** (`[0.86, 0.94]`) | 90% bootstrap CI coverage on `U` lands inside the band for the correct estimator; an under-dispersed CI falls below. | correct estimator's coverage sits outside → re-anchor the band to the measured coverage ± MC tolerance. |
| **D2.2 FPR** (`≤ 0.05`, Wilson-upper `≤ 0.075`) | On the null `U0`, the `CI_low>0` false-positive rate is achievable at/below 0.05 (not impossible) and is non-degenerate (not trivially 0 for a broken reason). | empirical FPR materially exceeds 0.05 with a correct estimator → the bootstrap/α needs adjustment, recorded before ratification. |
| **D2.5 shape `τ_gap`** (candidate `0.30`) | ROC of the gap diagnostic on `U` (negatives) vs `B` (positives): find the operating point with `U` false-flag ≤ 0.05 **and** `B` detection ≥ 0.80; check whether `0.30` sits in that window. | `0.30` is outside the feasible window → re-anchor `τ_gap` to the reported operating point. |

(D2.3 MDE finiteness and D2.4 reliability are properties of the full pipeline measured in EXP-077;
the bite check confirms only the thresholds above, which are the magic-number risks.)

## How to run

```bash
python docs/experiments-docs/checkpoints/2026-06-20-017-capgeo-qualifier-validation/bite_check.py
```

Deterministic (`SEED=20260620`); numpy + scipy only. Prints a verdict table and writes
`bite_check_report.json` beside the script. **Record the report (or paste the table) at G0
ratification**; update the D2 candidate values with any re-anchored numbers via the inline
ratification note or a `D0-amendment-*` file.

## Acceptance

The bite check itself "passes" when **every** D2 row above is `OK` (or has a recorded re-anchored
value). A green bite check is a precondition for, not a substitute for, operator G0 ratification.
