# Results: Experiment EXP-002

## Summary

Both Phase 001 referees are **correct** on the golden-fixture battery. Across all
five deterministic fixtures, the minimal baseline and the 5-check gate stack
reproduce every predeclared verdict (10/10 verdict checks PASS) and every required
gate-leg state (25/25 leg-exposure checks PASS), and the gate stack records all
five legs for every fixture with no short-circuiting. The referee logic is
approved as correct for the EXP-003 calibration measurement. `run_metadata.json`
records `overall_status: PASS`.

## Detailed Findings

### Finding 1 — Every fixture reproduces its hand-computed verdict

- **Observation**: 10/10 verdict checks PASS (`golden_fixture_results.csv`).
- **Evidence**: positive_oracle (min PASS / gate PASS, +6.0 bps net),
  null_negative_edge (REJECT / REJECT, −3.0), readiness_one_sided (PASS / REJECT,
  +7.0), materiality_too_small (PASS / REJECT, +0.2), naive_equivalent (PASS /
  REJECT, +1.667). Independent reproduction with the current module matched these
  bit-for-bit (audit spot-check). Gate effect = minimal effect − cost(1.0 bps)
  exactly in every row.
- **Interpretation**: Sign conventions, cost application, and CI direction are
  correct in both referees.

### Finding 2 — Each gate leg is isolated by a dedicated fixture

- **Observation**: The fixtures jointly drive every leg's pass and fail path.
- **Evidence** (`leg_exposure_matrix.csv`):
  - **L1 readiness** — `readiness_one_sided`: all-`+1` positions ⇒ 0 down-episodes
    ⇒ L1 False, flipping the verdict from minimal-PASS to gate-REJECT on identical
    data. This is the cleanest demonstration that the gate stack adds the
    readiness gate the minimal baseline lacks.
  - **L3 outcome** — `naive_equivalent`: candidate equals `sign(prev return)`, so
    `ci_vs_naive_lower = 0.0` ⇒ L3 False despite a positive gross effect.
  - **L5 materiality** — `materiality_too_small`: net +0.2 bps < 0.5 bps threshold
    ⇒ L5 False while gross +1.2 bps keeps minimal PASS.
  - **L3 + L5** — `null_negative_edge`: negative net edge fails both (and L4).
  - **All-pass** — `positive_oracle`: every leg True.
- **Interpretation**: Per-leg pass rates and false-negative attribution — the
  EXP-003 keystone deliverable — are well-defined because each leg is independently
  exercised and recorded.

### Finding 3 — The gate stack does not short-circuit

- **Observation**: Every fixture emits all five leg results, including fixtures
  whose early legs fail.
- **Evidence**: `readiness_one_sided` (L1 False) still records L2–L5; both nulls
  record all legs. 25/25 leg-exposure rows present and PASS.
- **Interpretation**: The conjunction is applied only at the decision boundary
  (design §6), so EXP-003 can attribute false negatives to specific legs.

## Hypothesis Verdict

**SUPPORTED**

The minimal baseline and the 5-check gate stack reproduce the predeclared
hand-computed verdicts on every golden fixture, and the gate stack records every
leg independently. Per the scope's criteria (Evidence FOR: every fixture produces
the expected minimal verdict, gate verdict, and required leg state, with all
L1–L5 emitted), the experiment PASSES and the referees are approved for EXP-003.

## Limitations

- **Correctness, not calibration.** This experiment certifies that the referees
  compute what they claim on fixtures with large margins; it says nothing about
  their FPR/TPR/MDE on real data — that is EXP-003.
- **Single operating point.** Fixtures run at `alpha = 0.05`, `n_bootstrap = 1000`,
  EURUSD/5m cost/materiality only. The alpha grid and other domains are exercised
  in EXP-003, not here.
- **Near-constant fixtures stress the block-length estimator degenerately.** The
  `materiality_too_small` minimal row reports `effective_n = 0.9` (block_length
  capped at 200) because its series is constant to floating-point dust. This is a
  reported-metadata artifact with no effect on any verdict and cannot occur on
  real returns (audit Info 1).

## Alternative Explanations

- Could the verdicts pass by coincidence rather than correct logic? Unlikely —
  each fixture isolates a different leg with a large, hand-reasoned margin, and the
  full set covers both pass and fail directions of all five legs plus the
  minimal-vs-gate distinction.

## Recommended Next Steps

1. **Proceed to EXP-003 (keystone)** — referee correctness is established;
   measure per-domain FPR/TPR/MDE and per-leg pass rates on the validated
   substrate.
2. **EXP-003 interpretation note**: confirm no real (domain, instrument) cell
   produces a degenerate capped block-length; if any does, treat its effective-N
   as suspect (carried from audit Info 1).
