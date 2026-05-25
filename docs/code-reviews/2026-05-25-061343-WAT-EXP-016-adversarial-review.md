# EXP-016 Adversarial Review

**Timestamp:** 2026-05-25 06:13:43 WAT  
**Reviewer:** Codex using `research-pipeline` context + `bmad-review-adversarial-general`  
**Scope:** EXP-016 artefacts and code present in `python/experiments/EXP-016/`

## Resolution Update

**Status:** Addressed on 2026-05-25.  

The implementation now gates threshold-pass flags on inside and matched-outside event floors, evaluates the scoped train/test floor rule, reports observed statistic differences, and writes strict JSON. The missing lifecycle artefacts were added: `audit.md`, `results.md`, `report.md`, and `governance/post-experiment-review.md`; both experiment indexes were updated.

## Context Used

- Pipeline configuration: `.agents/skills/research-pipeline/_pipeline-config.md`
- Dataset reference: `docs/references/dataset-reference.md`
- Architecture reference: `docs/references/architecture.md`
- Governance constraints: `.agents/skills/research-pipeline/references/governance-constraints.md`
- Code conventions: `.agents/skills/experiment-developer/references/code-conventions.md`
- Experiment indexes: `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`
- Latest active checkpoint design: `docs/experiments-docs/checkpoints/2026-05-23-003-ict-one-setup-timebar-validation/design.md`
- EXP-016 artefacts: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `governance/pre-execution-review.md`, `results/*`, `plots/*`

## Review Lens

Content type: empirical study plus experiment implementation.  
Primary lenses: statistical validity, reproducibility, scope/governance compliance, and code-result consistency.

```json
[
  {
    "id": "F01",
    "severity": "Major",
    "title": "Experiment lifecycle artefacts are incomplete despite generated results",
    "evidence": "research-pipeline requires Stage 5 `audit.md`, Stage 6 `results.md`, Stage 7 `report.md`, and Stage 8 `governance/post-experiment-review.md`; `find python/experiments/EXP-016 ...` returned none of those files. `python/experiments/EXP-016/results/numerical_summary.txt:1-15` shows the experiment has generated a verdict and result tables.",
    "impact": "EXP-016 currently has raw outputs but lacks the required audit, interpretation, final report, index update, and post-experiment governance approval. The experiment should not be treated as complete or relied on for downstream roadmap decisions until those stages are performed.",
    "fix": "Resume the research pipeline at Stage 5. Produce `audit.md`, `results.md`, `report.md`, update indexes, and write `governance/post-experiment-review.md` before promoting EXP-016 from PLANNED/raw-output status."
  },
  {
    "id": "F02",
    "severity": "Major",
    "title": "Verdict logic narrows the scoped event-floor rule to the test segment only",
    "evidence": "`python/experiments/EXP-016/scope.md:24` requires `>= 50 inside-window sweep events per train/test segment`; `python/experiments/EXP-016/code/run_experiment.py:523-565` evaluates the verdict using only rows where `Segment == \"Test\"`.",
    "impact": "The implementation changes the success criterion from a train/test segment requirement into a test-only decision. In this run the final verdict remains INCONCLUSIVE, but the code would allow future FOR/AGAINST decisions that do not enforce the scope's per-segment event-floor language.",
    "fix": "Make the interpretation rule explicit and consistent. Either update the scope/plan to state that the final verdict is test-segment-only, or change `evaluate_verdict()` to require the event floor and pass criteria across both Train and Test segments as scoped."
  },
  {
    "id": "F03",
    "severity": "Major",
    "title": "Primary effect flags can pass on an underpowered matched outside baseline",
    "evidence": "`python/experiments/EXP-016/results/numerical_summary.txt:11-15` reports test matched-outside counts of 2, 4, 1, and 12, while `python/experiments/EXP-016/results/primary_effects.csv:5` and `:9` mark XAUUSD and USTEC test `HitCriterionMet=True` and `MAECriterionMet=True` despite `PassEventCount=False` and outside hit counts of 3 and 10.",
    "impact": "The result artefacts present threshold-pass flags from very small or partially missing comparator samples. Readers may overinterpret these flags even though the matched baseline is too sparse for stable inference and the event floor fails.",
    "fix": "Gate `HitCriterionMet` and `MAECriterionMet` on both the inside event floor and a minimum matched-outside count, or add separate raw effect columns and mark criterion columns false/not evaluable whenever the relevant floor is not met. The summary should suppress pass language for non-evaluable rows."
  },
  {
    "id": "F04",
    "severity": "Minor",
    "title": "Generated JSON contains non-standard NaN values",
    "evidence": "`python/experiments/EXP-016/code/run_experiment.py:780-781` writes `results.json` with default `json.dump(...)`; `python/experiments/EXP-016/results/results.json` contains bare `NaN` values for unavailable effects, such as BTCUSD test `OutsideHitMean` and CI fields.",
    "impact": "Python can parse this extension, but strict JSON consumers, validators, and some downstream tooling will reject the file. That weakens reproducibility and portability of the result artefact.",
    "fix": "Convert non-finite numeric values to `null` before serialization and write with `allow_nan=False`. Keep CSV blanks as-is if desired, but make `results.json` standards-compliant."
  },
  {
    "id": "F05",
    "severity": "Minor",
    "title": "Reported bootstrap Diff is the mean bootstrap estimate rather than the observed effect",
    "evidence": "`python/experiments/EXP-016/code/run_experiment.py:391-408` computes `InsideStat` and `OutsideStat` from observed samples, then sets `Diff` to `np.mean(diffs)` from bootstrap resamples instead of `InsideStat - OutsideStat`.",
    "impact": "The reported point estimate can drift from the directly observed effect, especially for median MAE with tiny outside samples. This is not likely to change the current INCONCLUSIVE verdict, but it makes result tables less transparent.",
    "fix": "Set `Diff` to the observed statistic difference and use the bootstrap distribution only for confidence intervals. If bias-corrected estimates are intended, document that explicitly in the analysis plan and output metadata."
  }
]
```

## Summary

EXP-016 is not yet a completed pipeline experiment: results exist, but audit, interpretation, report, index updates, and post-experiment governance are absent. The code appears broadly aligned with holdout exclusion, time-bar-native data, and real-price discipline, but the result interpretation path needs tightening around the scoped train/test event floor and the extremely small matched outside comparator samples. The current raw verdict of INCONCLUSIVE is directionally reasonable, but the artefacts should not be treated as final until the pipeline is resumed and the above issues are addressed or explicitly accepted.
