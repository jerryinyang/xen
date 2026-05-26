# Results: Experiment EXP-027

## Summary

EXP-027 is **INCONCLUSIVE** because the experiment never advanced past the manifest gate. EXP-026 produced `selected_components = ["Sweep", "Displacement"]` with `candidate_eligible = false`, so the full-model analysis-set test was intentionally blocked before any trade-level evaluation could occur.

## Detailed Findings

### The Upstream Manifest Already Failed The Full-Model Gate

- **Observation**: There was no eligible candidate to test.
- **Evidence**: `results.json` embeds the EXP-026 manifest with `candidate_eligible = false`, `source_verdict = "INCONCLUSIVE"`, and notes that no optional component met the positive lower-CI rule.
- **Interpretation**: EXP-027 should be read as a governance stop, not as a weak model-performance result.

### The Stored Verdict Is A Pure Gate Outcome

- **Observation**: The current result contains no per-instrument performance evaluation.
- **Evidence**: `results.json` records `criteria = {"ManifestEligible": false}`, `per_instrument = []`, and the reason `EXP-026 manifest did not identify an eligible full-model candidate.` `model_verdict.json` repeats the same verdict and reason.
- **Interpretation**: The experiment did exactly what the phase design required once the upstream ablation failed to promote a candidate.

### The Result Contract Now Matches The Gate State

- **Observation**: The stored outputs have been aligned to the early-exit contract.
- **Evidence**: `results/` contains only `results.json`, `model_verdict.json`, and `numerical_summary.txt`, and `plots/` is empty.
- **Interpretation**: There is no longer any stale full-run artifact suggesting that a real model-performance evaluation happened.

## Hypothesis Verdict

**INCONCLUSIVE**

The experiment asked whether the best predeclared full-model variant survives an analysis-set test. That question could not be reached, because EXP-026 did not produce an eligible full-model variant to test.

## Limitations

- No full-model candidate existed, so no trade-performance evidence was generated.
- The experiment depends completely on the EXP-026 manifest gate.
- This result cannot distinguish between "no eligible candidate" and "eligible candidate that later fails"; only the first case occurred here.

## Alternative Explanations

- A narrower, newly scoped candidate could still be worth testing later, but that would be a separate experiment.
- The blocked outcome does not imply that every possible ICT full model is bad; it only says the current chain never earned promotion.

## Recommended Next Steps

1. Do not interpret EXP-027 as a tested-performance refutation; treat it as a blocked stage in the current Phase 003 chain.
2. Resume full-model work only after a new upstream experiment creates an eligible candidate under a fresh scope.
