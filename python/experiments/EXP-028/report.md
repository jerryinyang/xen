# Experiment Report: EXP-028 - ICT Candidate Robustness and Falsification

## Status: INCONCLUSIVE

**Date**: 2026-05-26
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Data Views / Feature Categories**: 1-minute time bars, EXP-027 candidate gate, robustness/falsification contract

---

## Question

Does the candidate survive robustness and falsification checks?

## Hypothesis

A candidate ICT variant is robust only if it first survives the EXP-027 eligibility gate and then remains defensible under the predeclared segment, delay, and cost stresses.

## Method Summary

EXP-028 was designed as a falsification stage after a successful EXP-027 full-model candidate. The stored run never reached that analysis body because EXP-027 was already ineligible, so the experiment wrote the short inconclusive contract and stopped before segment, delay, or cost calculations.

## Key Findings

### Finding 1: No candidate reached the robustness stage

`results.json` records that EXP-027 was already `INCONCLUSIVE`, which blocks robustness work by scope.

That means no valid robustness interpretation exists for the current phase branch.

### Finding 2: The stored outputs correctly show that no robustness work happened

The current result directory contains only `results.json` and `numerical_summary.txt`, matching the declared early-exit contract.

This is the correct artifact shape for an unopened falsification stage.

## Conclusion

**Hypothesis INCONCLUSIVE.**

The experiment never became eligible to run. The useful information is procedural rather than statistical: the current Phase 003 chain did not produce a candidate robust enough even to enter falsification.

## Limitations

- No robustness calculations were executed.
- The outcome depends entirely on the upstream EXP-027 gate.
- The experiment cannot speak to any hypothetical future candidate.

## Implications for Future Research

- Phase 003 robustness work is blocked until a new eligible candidate exists.
- Future robustness analysis should begin only after a new upstream scope produces a candidate worth falsifying.

## Recommended Next Experiments

1. **Candidate-creation follow-up**: design a new upstream experiment that could produce a genuinely eligible model candidate.
2. **Robustness rerun only after eligibility**: revisit EXP-028 logic only when an approved candidate exists to test.

## Artifacts

| Artifact | Path |
|----------|------|
| Scope | [scope.md](scope.md) |
| Analysis Plan | [analysis-plan.md](analysis-plan.md) |
| Code | [code/](code/) |
| Audit | [audit.md](audit.md) |
| Results | [results.md](results.md) |
| Governance Reviews | [governance/](governance/) |
| Result Tables | [results/](results/) |
| Plots | [plots/](plots/) |
