# Results: Experiment EXP-028

## Summary

EXP-028 is **INCONCLUSIVE** because the robustness and falsification stage never opened. The stored result records that EXP-027 was already ineligible, so EXP-028 stopped at the upstream gate and wrote only the short early-exit contract.

## Detailed Findings

### The Robustness Stage Was Blocked Upstream

- **Observation**: There was no eligible candidate to falsify.
- **Evidence**: `results.json` records the reason `EXP-027 candidate is not eligible for robustness checks (verdict=INCONCLUSIVE).`
- **Interpretation**: EXP-028 should be read as a blocked robustness stage, not as a failed robustness test.

### The Stored Artifacts Match The Early-Exit Contract

- **Observation**: No robustness tables or plots were generated.
- **Evidence**: `results.json` declares `output_contract = "early_inconclusive_no_robustness_outputs"` with expected outputs `["results.json", "numerical_summary.txt"]`, and those are the only files present in `results/`.
- **Interpretation**: The artifact set correctly communicates that no segment, delay, or cost analysis happened.

## Hypothesis Verdict

**INCONCLUSIVE**

The experiment asked whether the candidate survives robustness and falsification checks. That question was unreachable because EXP-027 did not produce a candidate eligible for robustness testing.

## Limitations

- No robustness evidence exists because no candidate reached this stage.
- The experiment's outcome depends entirely on the upstream EXP-027 gate.
- It cannot distinguish between a fragile tested candidate and an absent candidate; only the absent-candidate case occurred.

## Alternative Explanations

- A later experiment could create an eligible candidate that merits real robustness testing.
- This result says nothing about segment, delay, or cost sensitivity for any hypothetical future candidate.

## Recommended Next Steps

1. Do not treat EXP-028 as a negative robustness result; treat it as an unopened stage.
2. Resume robustness work only after a new candidate is promoted by an upstream experiment under a fresh scope.
