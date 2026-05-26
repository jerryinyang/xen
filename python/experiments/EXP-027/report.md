# Experiment Report: EXP-027 - Predeclared Full ICT Model Analysis-Set Test

## Status: INCONCLUSIVE

**Date**: 2026-05-26
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC
**Data Views / Feature Categories**: 1-minute time bars, EXP-026 frozen model manifest gate

---

## Question

Does the best predeclared full-model variant survive analysis-set testing after costs and robustness checks?

## Hypothesis

The best predeclared full-model variant survives the analysis-set test only if the upstream ablation produces an eligible candidate first.

## Method Summary

EXP-027 was designed as a gated full-model test, not as an open-ended backtest. It first reads the frozen EXP-026 manifest and proceeds only if the manifest promotes an eligible candidate. In the stored run, that gate failed, so the experiment wrote the short inconclusive contract and stopped before any trade-level analysis.

## Key Findings

### Finding 1: No eligible full-model candidate existed

The EXP-026 manifest kept only `["Sweep", "Displacement"]` and explicitly marked the candidate as ineligible.

No full-model performance tables were therefore part of the valid output contract for this run.

### Finding 2: The result is a blocked stage, not a performance miss

`results.json` and `model_verdict.json` both record the same reason: `EXP-026 manifest did not identify an eligible full-model candidate.`

That distinction matters because this experiment should not be cited as evidence about a tested model's expectancy, drawdown, or cost sensitivity.

### Finding 3: The artifact contract now reflects the true state cleanly

After audit cleanup, `results/` contains only the three gate-result files and `plots/` is empty.

This removes the earlier ambiguity that stale full-run artifacts could create for downstream readers or tooling.

## Conclusion

**Hypothesis INCONCLUSIVE.**

The full-model test never became eligible to run. That is a valid and useful phase result: the current ICT chain did not earn promotion into a combined analysis-set test.

## Limitations

- No performance evidence was generated because no eligible candidate existed.
- The experiment's value depends entirely on the EXP-026 gate quality.
- It cannot answer whether some other, newly scoped full model might work.

## Implications for Future Research

- Phase 003 should treat the current full-model path as blocked, not merely delayed.
- Any future full-model test must start from a new candidate-forming experiment, not from the existing manifest.

## Recommended Next Experiments

1. **New candidate-formation experiment**: define and test one narrower optional component or alternative chain capable of earning manifest promotion.
2. **Instrument-specific ICT branch**: if future evidence becomes concentrated in one instrument, scope that explicitly instead of reusing the blocked broad candidate path.

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
