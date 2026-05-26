# Audit Report: Experiment EXP-027

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

EXP-027 is interpretable as a gate result. The stored verdict is entirely determined by the EXP-026 manifest and does not depend on a downstream trade evaluation, because the full-model candidate was never eligible. During audit, I also cleaned stale full-run CSV/plot artifacts from `EXP-027` and hardened the early-exit code path so future inconclusive reruns keep the results directory consistent with the no-go contract.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-027/code/run_experiment.py` | Correctness | PASS | The experiment exits immediately when `candidate_eligible` is false and writes the intended manifest-gate no-go payload. |
| `python/experiments/EXP-027/code/run_experiment.py` | Edge cases | PASS | The ineligible-manifest branch now removes stale full-run artifacts before writing the short contract. |
| `python/experiments/EXP-027/code/run_experiment.py` | Type safety | PASS | Public helpers remain annotated and documented. |
| `python/experiments/EXP-027/code/run_experiment.py` | NaN handling | PASS | The early-exit branch does not materialize trade-level outputs, so no hidden numeric path remains active. |
| `python/experiments/EXP-027/code/run_experiment.py` | Holdout exclusion | PASS | The current stored verdict does not require any fresh bar load. |
| `python/experiments/EXP-027/code/run_experiment.py` | Scope compliance | PASS | The code respects the EXP-026 gate instead of forcing a full-model test. |
| `python/experiments/EXP-027/code/run_experiment.py` | Logging/output | PASS | Manual-run output is concise and explicit about the gate reason. |
| `python/experiments/EXP-027/code/run_experiment.py` | Organization/import side effects | PASS | Output directories are controlled in orchestration only. |
| `python/experiments/EXP-027/code/run_experiment.py` | Result contract hygiene | PASS | Current `results/` contains only `results.json`, `model_verdict.json`, and `numerical_summary.txt`; `plots/` is empty. |
| `python/experiments/EXP-027/code/run_experiment.py` | Docstrings | PASS | Public helpers are documented. |

## Numerical Validation

### Spot Checks

The stored gate artifacts agree exactly:

- `results.json` verdict: `INCONCLUSIVE`
- `model_verdict.json` verdict: `INCONCLUSIVE`
- `results.json` reason: `EXP-026 manifest did not identify an eligible full-model candidate.`
- `model_verdict.json` reason: the same string
- `results.json` `criteria.ManifestEligible = false`
- `results.json` `per_instrument = []`

The cleaned output contract is also consistent with the experiment state:

- `results/` now contains only `model_verdict.json`, `numerical_summary.txt`, and `results.json`
- `plots/` contains no files

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Manifest eligibility | boolean | `false` | YES |
| Per-instrument rows on early gate | empty | `[]` | YES |
| Result files on early gate | short contract only | exactly 3 files | YES |
| Plot files on early gate | none expected | `0` | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|---------------------|-------|
| Selected manifest components | `["Sweep", "Displacement"]` | YES | Baseline-only manifest is not enough for a full-model candidate. |
| Candidate eligible | `False` | YES | Matches EXP-026. |
| Full-model performance evaluation executed | `No` | YES | Correct for an upstream gate failure. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Full-model gate | EXP-027 runs only when EXP-026 produces an eligible candidate | YES | The stored verdict is entirely manifest-gated. |
| Documentation contract | Ineligible run should not present trade-level outputs as current | YES | Stale artifacts were removed during audit and the code path now preserves that contract. |
| Phase sequencing | EXP-027 should not invent a new candidate after seeing EXP-026 | YES | No post-hoc promotion occurs. |

## Results Plausibility

The current result is plausible and correctly narrow. EXP-027 did not become a hidden performance test; it remained a gating step and stopped when the upstream ablation failed to produce an eligible candidate.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: the gate short-circuited before downstream performance/plot work; no out-of-scope analysis was added
- Holdout exclusion verified: YES
- Real-price discipline verified: YES
- Timestamp alignment verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **This is a pre-test no-go, not a failed trade-performance result**
   - File: `python/experiments/EXP-027/results/results.json`
   - Description: The experiment stops at manifest eligibility and therefore contains no valid per-instrument performance interpretation.
   - Impact: Downstream documentation must treat EXP-027 as a blocked full-model attempt, not as evidence that a tested full model underperformed.

## Re-Audit Requirements

None.
