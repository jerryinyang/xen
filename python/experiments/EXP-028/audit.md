# Audit Report: Experiment EXP-028

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

EXP-028 is interpretable as an upstream-gated no-go. The stored result correctly records that robustness checks did not run because EXP-027 was already ineligible. During audit, I also hardened the verdict-loading path so future early exits no longer depend on stale `EXP-027/trade_table.csv` artifacts.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-028/code/run_experiment.py` | Correctness | PASS | The experiment now reads `model_verdict.json` first and returns the short inconclusive contract immediately when EXP-027 is already blocked. |
| `python/experiments/EXP-028/code/run_experiment.py` | Edge cases | PASS | Future ineligible reruns no longer require a stale `trade_table.csv` to exist. |
| `python/experiments/EXP-028/code/run_experiment.py` | Type safety | PASS | Public helpers remain annotated and documented. |
| `python/experiments/EXP-028/code/run_experiment.py` | NaN handling | PASS | The early-exit path writes no partial robustness tables. |
| `python/experiments/EXP-028/code/run_experiment.py` | Holdout exclusion | PASS | The current stored verdict exits before any raw-bar load or robustness calculation. |
| `python/experiments/EXP-028/code/run_experiment.py` | Scope compliance | PASS | The experiment treats robustness strictly as a falsification step after eligibility, not as a place to rescue an ineligible candidate. |
| `python/experiments/EXP-028/code/run_experiment.py` | Logging/output | PASS | Manual-run output is concise and explicit about the upstream gate. |
| `python/experiments/EXP-028/code/run_experiment.py` | Organization/import side effects | PASS | Filesystem effects remain in orchestration only. |
| `python/experiments/EXP-028/code/run_experiment.py` | Result contract hygiene | PASS | Current `results/` contains only the two expected early-exit files. |
| `python/experiments/EXP-028/code/run_experiment.py` | Docstrings | PASS | Public helpers are documented. |

## Numerical Validation

### Spot Checks

The stored early-exit payload is internally consistent:

- `results.json` verdict: `INCONCLUSIVE`
- reason: `EXP-027 candidate is not eligible for robustness checks (verdict=INCONCLUSIVE).`
- `output_contract`: `early_inconclusive_no_robustness_outputs`
- expected outputs: `["results.json", "numerical_summary.txt"]`

Filesystem validation matches that contract exactly:

- `results/` contains only `results.json` and `numerical_summary.txt`
- no segment, delay, cost-stress, robustness-summary, or plot artifacts are present

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Upstream verdict | enumerated status | `INCONCLUSIVE` | YES |
| Early-exit output contract | fixed string | `early_inconclusive_no_robustness_outputs` | YES |
| Expected output files | 2 files | exactly 2 files | YES |
| Robustness tables on early exit | none expected | none present | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|---------------------|-------|
| Robustness calculations executed | `No` | YES | Correct for an upstream gate failure. |
| Delay / cost / segment plots generated | `No` | YES | Correct for the early-exit contract. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Falsification gate | Robustness runs only after an eligible EXP-027 candidate exists | YES | The current run stops at the upstream verdict. |
| Output contract | Early no-go should not leave partial robustness artifacts | YES | Only the two contract files are present. |
| Phase sequencing | EXP-028 must not reinterpret an upstream no-go as a new candidate | YES | No alternate candidate or segment-specific rescue path appears. |

## Results Plausibility

The current output is plausible and appropriately narrow. EXP-028 did not test robustness because there was nothing valid to falsify after EXP-027 stopped at the manifest gate.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: the gate short-circuited before robustness computations; no out-of-scope analysis was added
- Holdout exclusion verified: YES
- Real-price discipline verified: YES
- Timestamp alignment verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **This is an upstream-gated stop, not robustness evidence**
   - File: `python/experiments/EXP-028/results/results.json`
   - Description: The experiment records that no robustness, delay, or cost analysis was executed because EXP-027 never produced an eligible candidate.
   - Impact: Downstream summaries must avoid language implying that a tested candidate failed robustness.

## Re-Audit Requirements

None.
