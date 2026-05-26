# Audit Report: Experiment EXP-026

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

EXP-026 is interpretable. The code reads only previously approved analysis-set outputs, applies the fixed component order from the scope, and writes a manifest whose no-go decision matches the stored marginal bootstrap table exactly. I did not rerun the full experiment code inside the pipeline; validation used code inspection and lightweight checks over the stored result files.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-026/code/run_experiment.py` | Correctness | PASS | The script preserves the fixed chain order and distinguishes chain eligibility from candidate-selection eligibility as scoped. |
| `python/experiments/EXP-026/code/run_experiment.py` | Edge cases | PASS | Missing prerequisite files and absent bootstrap rows fail explicitly. |
| `python/experiments/EXP-026/code/run_experiment.py` | Type safety | PASS | Public helpers are annotated and documented. |
| `python/experiments/EXP-026/code/run_experiment.py` | NaN handling | PASS | Early sweep steps intentionally keep `MeanReturn_R` empty while using proxy expectancy; later steps coerce numeric fields explicitly. |
| `python/experiments/EXP-026/code/run_experiment.py` | Holdout exclusion | PASS | The experiment consumes prior analysis-set result tables only; it does not reopen raw holdout data. |
| `python/experiments/EXP-026/code/run_experiment.py` | Real-price outcome discipline | PASS | Later-stage R outcomes are inherited from prior real-price experiments; no synthetic-price path is introduced here. |
| `python/experiments/EXP-026/code/run_experiment.py` | Memory/performance | PASS | Output tables are loaded once and reused for both summaries and plots. |
| `python/experiments/EXP-026/code/run_experiment.py` | Logging/output | PASS | Orchestration output is concise and traceable. |
| `python/experiments/EXP-026/code/run_experiment.py` | Organization/import side effects | PASS | Output directories are created in orchestration only. |
| `python/experiments/EXP-026/code/run_experiment.py` | Plot data reuse | PASS | Plots consume `chain_steps.csv` and `bootstrap_marginal.csv` inputs already assembled in the analysis pass. |
| `python/experiments/EXP-026/code/run_experiment.py` | Docstrings | PASS | Public helpers are documented. |

## Numerical Validation

### Spot Checks

The manifest no-go decision is mechanically consistent with the stored bootstrap table:

- `component_eligibility.csv` marks `Sweep`, `Displacement`, and `SecondCandleOpen` as candidate-eligible inputs.
- `bootstrap_marginal.csv` has `0` Test rows with both `MeanDiff > 0` and `CI_Lo > 0`.
- The Step 7 (`SecondCandleOpen`) Test rows are all non-passing:
  - EURUSD `MeanDiff=-0.419`, `CI_Lo=-1.387`
  - XAUUSD `MeanDiff=-0.121`, `CI_Lo=-1.578`
  - BTCUSD `MeanDiff=-0.984`, `CI_Lo=-2.564`
  - USTEC `MeanDiff=-0.101`, `CI_Lo=-1.515`
- `model_manifest.json` therefore keeps `selected_components = ["Sweep", "Displacement"]` and sets `candidate_eligible = false`.

These checks support the stored ablation verdict.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Event counts | non-negative integers | `25` to `354` | YES |
| Proxy expectancy | finite real values | `-2.0616` to `1.3000` | YES |
| MeanReturn_R on later chain steps | finite real values when present | `-2.0616` to `1.3000` | YES |
| Selected optional components | subset of scoped chain | none selected | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|---------------------|-------|
| Test rows with positive lower CI | `0` | YES | The manifest correctly blocks candidate promotion. |
| Candidate-selected components | `["Sweep", "Displacement"]` | YES | Mandatory baseline chain only; no optional component survives. |
| Candidate eligible flag | `False` | YES | Required because no optional component cleared the rule. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Fixed-order ablation | Component order is frozen before results | YES | The chain stays in the scope's declared order. |
| Candidate selection | Promotion requires robust positive evidence, not point estimates alone | YES | The manifest rule requires `MeanDiff > 0` and `CI_Lo > 0`. |
| Upstream inheritance | Prior experiment outputs are analysis-set only | YES | All referenced EXP-015 through EXP-025 artifacts were produced under the same holdout discipline. |

## Results Plausibility

The ablation outcome is plausible. The baseline sweep and displacement chain can be measured, but the optional layers do not add stable, cross-instrument positive contribution under the predeclared rule. The no-go manifest is therefore consistent with both the numbers and the phase gate.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: within scope; one eligibility audit, one fixed-order chain, one marginal bootstrap family, `4 / 5` plots, no extra shared modules beyond scoped reuse
- Holdout exclusion verified: YES
- Real-price discipline verified: YES
- Timestamp alignment verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **The phase gate closes because optional components fail the positive-evidence rule, not because the chain is missing**
   - File: `python/experiments/EXP-026/results/model_manifest.json`
   - Description: The experiment had enough structure to build the chain, but no optional component met the selection threshold required for a full-model candidate.
   - Impact: The correct downstream action is to block EXP-027 candidate promotion, not to reinterpret this as a broad data-readiness failure.

## Re-Audit Requirements

None.
