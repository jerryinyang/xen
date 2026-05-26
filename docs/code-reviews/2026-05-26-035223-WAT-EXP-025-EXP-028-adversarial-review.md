# Adversarial Code Review: EXP-025 through EXP-028

**Review timestamp:** 2026-05-26 03:52:23 WAT  
**Reviewer mode:** `bmad-review-adversarial-general` with `research-pipeline` context and `experiment-auditor` implementation checks  
**Scope:** Static review of EXP-025, EXP-026, EXP-027, and EXP-028 artefacts, code, and generated result summaries.  
**Execution status:** No experiment scripts were run. Static syntax compilation with `python3 -m py_compile` passed for all four `run_experiment.py` files.

## Context Used

- Active checkpoint: `docs/experiments-docs/checkpoints/2026-05-23-003-ict-one-setup-timebar-validation/design.md`
- Pipeline config: `.agents/skills/research-pipeline/_pipeline-config.md`
- Governance constraints: `.agents/skills/research-pipeline/references/governance-constraints.md`
- Code conventions: `.agents/skills/experiment-developer/references/code-conventions.md`
- Dataset reference: `docs/references/dataset-reference.md`
- Architecture reference: `docs/references/architecture.md`
- Experiment index: `python/experiments/INDEX.md`
- Comprehensive index: `docs/experiments-docs/INDEX.md`
- Experiment artefacts under `python/experiments/EXP-025` through `python/experiments/EXP-028`

Content type: empirical experiment artefacts plus Python implementation. Active lenses: statistical validity, reproducibility, phase-gate compliance, scope compliance, causal timing/look-ahead risk, and implementation correctness.

## Cross-Experiment Findings

```json
[
  {
    "id": "EXP025-F01",
    "severity": "Major",
    "title": "2R support verdict substitutes non-dominance for the scoped superiority criterion",
    "evidence": "The scope requires evidence FOR only if 2R produces better expectancy or robustness than alternatives on at least 3 instruments (`python/experiments/EXP-025/scope.md:24`). The implementation instead defines support as `2R is NOT dominated (CI_Hi >= 0 for all alternatives)` (`python/experiments/EXP-025/code/run_experiment.py:521-529`) and returns FOR when `n_passing >= MIN_ELIGIBLE_INSTRUMENTS` (`python/experiments/EXP-025/code/run_experiment.py:575-583`). The result then reports `Verdict: FOR` because 2R is not statistically dominated (`python/experiments/EXP-025/results/numerical_summary.txt:1-5`), even though all test 2R means are negative and TimeStop60 has higher mean return on all four instruments (`python/experiments/EXP-025/results/numerical_summary.txt:7-32`).",
    "impact": "EXP-025 overstates support for fixed 1:2 risk/reward. This directly contaminates EXP-026 because `RiskModel_2R` becomes eligible from the EXP-025 FOR verdict, and then feeds the EXP-027 manifest.",
    "fix": "Encode the written criterion directly: support should require predeclared evidence that 2R is better or more robust than alternatives on at least 3 instruments, not merely that a negative difference is statistically uncertain. If no alternative is significantly better but 2R is also not positively justified, classify the result as INCONCLUSIVE or AGAINST per the scope."
  },
  {
    "id": "EXP025-F02",
    "severity": "Major",
    "title": "Nearest opposing liquidity target is a scoped comparator but has zero valid outcomes",
    "evidence": "The EXP-025 scope explicitly includes nearest opposing liquidity as an exit alternative (`python/experiments/EXP-025/scope.md:20`). The test summary shows `NearestLiquidity` has `N_valid=0` for EURUSD, XAUUSD, BTCUSD, and USTEC (`python/experiments/EXP-025/results/numerical_summary.txt:13`, `python/experiments/EXP-025/results/numerical_summary.txt:20`, `python/experiments/EXP-025/results/numerical_summary.txt:27`, `python/experiments/EXP-025/results/numerical_summary.txt:32`).",
    "impact": "The experiment did not actually compare 2R against one of its predeclared alternatives. The H6 question asks whether 1:2 is justified versus alternatives; a missing comparator narrows the tested question after the fact.",
    "fix": "Determine why no opposing-liquidity targets are found, fix the target construction if it is a code issue, or explicitly classify the liquidity-target comparison as unavailable and make the H6 verdict conditional/inconclusive rather than fully FOR."
  },
  {
    "id": "EXP026-F01",
    "severity": "Major",
    "title": "Component selection treats any positive CI upper bound as evidence of net value",
    "evidence": "The scope requires components to add net expectancy or risk-adjusted improvement and survive train/test comparison (`python/experiments/EXP-026/scope.md:24`). The code selects a component when any test-row `CI_Hi_Positive` is true (`python/experiments/EXP-026/code/run_experiment.py:501-540`), where `CI_Hi_Positive` is simply `CI_Hi > 0` (`python/experiments/EXP-026/code/run_experiment.py:477-490`). The output selects all optional components even when point estimates are negative, for example `Disp+IFVG BTCUSD diff=-0.973 CI=[-2.534,0.559]`, `Disp+SCO USTEC diff=-0.738 CI=[-2.760,1.082]`, and `Disp+SCO+2R USTEC diff=-0.682 CI=[-1.625,0.255]` (`python/experiments/EXP-026/results/numerical_summary.txt:42`, `python/experiments/EXP-026/results/numerical_summary.txt:51`, `python/experiments/EXP-026/results/numerical_summary.txt:55`).",
    "impact": "EXP-026 can mark the ablation as SUPPORTED and produce a full-model manifest even when the data does not show a positive marginal contribution. The EXP-027 model is therefore not a genuinely eligible, data-supported candidate under the written ablation gate.",
    "fix": "Use a predeclared positive evidence rule, such as positive point estimate plus CI lower bound above zero, or a stricter train/test consistency criterion. At minimum, do not select components whose marginal mean is negative and whose CI spans zero."
  },
  {
    "id": "EXP026-F02",
    "severity": "Major",
    "title": "Refuted components are eligible for candidate selection instead of remaining labelled negative controls",
    "evidence": "The scope states that failed components may be included only as labelled negative controls, not candidate model rules (`python/experiments/EXP-026/scope.md:20`). The eligibility table marks IFVG and Breaker as `Verdict: REFUTED` but `EligibleForChain: True` (`python/experiments/EXP-026/code/run_experiment.py:103-116`). The manifest then selects both IFVG and Breaker as model components (`python/experiments/EXP-026/results/model_manifest.json:4-11`).",
    "impact": "EXP-026 violates its own candidate eligibility rule and passes refuted components into EXP-027 as if they were validated contributors. That weakens the phase's ablation gate and makes the full-model test a post-hoc assembly of controls rather than an approved candidate.",
    "fix": "Keep refuted or inconclusive components in the contribution table as negative controls, but exclude them from `selected_components` unless a separate predeclared rule explains why diagnostic inclusion is allowed in the candidate manifest."
  },
  {
    "id": "EXP026-F03",
    "severity": "Major",
    "title": "Ablation compares separate event sets rather than a nested incremental rule chain",
    "evidence": "The scope says to add one component at a time in a fixed order and account for sample-size loss (`python/experiments/EXP-026/scope.md:20`, `python/experiments/EXP-026/analysis-plan.md:19-30`). The code loads each execution-chain step from separate prior experiment result files (`python/experiments/EXP-026/code/run_experiment.py:232-286`) and bootstraps mean differences between independent arrays from step N and step N-1 (`python/experiments/EXP-026/code/run_experiment.py:399-428`, `python/experiments/EXP-026/code/run_experiment.py:431-492`).",
    "impact": "The reported marginal differences may reflect different event definitions, different populations, and selection effects rather than the incremental contribution of adding a component to the same candidate set. This does not establish value beyond sample-size effects, which is the core question of EXP-026.",
    "fix": "Carry stable event IDs from the baseline event through every component, construct nested subsets from one parent event table, and compute paired or matched marginal comparisons with explicit dropped-event reasons."
  },
  {
    "id": "EXP027-F01",
    "severity": "Major",
    "title": "Full-model test accepts an invalid manifest without enforcing the ablation gate",
    "evidence": "EXP-027 requires a frozen model manifest selected from EXP-026 after eligible variants are identified (`python/experiments/EXP-027/scope.md:20`, `python/experiments/EXP-027/scope.md:30`). `load_manifest()` validates only that required JSON fields exist (`python/experiments/EXP-027/code/run_experiment.py:53-91`). The loaded manifest includes components selected by the flawed positive-CI-upper-bound rule (`python/experiments/EXP-027/results/results.json:4-20`).",
    "impact": "EXP-027's AGAINST result is directionally useful, but the experiment is not a valid gated full-model test of an eligible candidate. It depends on EXP-026's unsupported selection logic and should not be used as a clean answer to the full-model survival question without revising EXP-026 first.",
    "fix": "Make EXP-027 validate a manifest-level eligibility flag and the component-level evidence used to select the model. If EXP-026 is unsupported or contains only negative-control components, EXP-027 should stop as INCONCLUSIVE instead of proceeding as a full-model test."
  },
  {
    "id": "PIPELINE-F01",
    "severity": "Major",
    "title": "Generated result artefacts exist without the required audit, interpretation, report, post-governance, or index state updates",
    "evidence": "The research pipeline requires `audit.md`, `results.md`, `report.md`, index updates, and `governance/post-experiment-review.md` after results are generated. None of those files exist under EXP-025 through EXP-028, while results and plots do exist for EXP-025 through EXP-027 and short results exist for EXP-028. The experiment index still lists EXP-025 through EXP-028 as PLANNED (`python/experiments/INDEX.md:28-31`).",
    "impact": "The repository state is internally inconsistent: later experiments consume prior results that have not gone through the pipeline's audit, interpretation, documentation, or post-experiment governance gates. Readers may treat generated CSV/JSON files as completed experiment evidence while the authoritative indexes still say PLANNED.",
    "fix": "Resume each experiment at pipeline Stage 5, starting with audit. Do not rely on EXP-025 through EXP-028 as completed evidence until `audit.md`, `results.md`, `report.md`, post-experiment governance, and both indexes are updated."
  },
  {
    "id": "EXP028-F01",
    "severity": "Minor",
    "title": "EXP-028 governance claims full outputs even though the script short-circuits",
    "evidence": "The pre-execution review says EXP-028 produces `segment_results.csv`, `delay_stress.csv`, `cost_stress.csv`, `robustness_summary.csv`, five plots, and criteria outputs (`python/experiments/EXP-028/governance/pre-execution-review.md:84-85`). The code exits before creating plot directories when EXP-027 verdict is AGAINST or INCONCLUSIVE (`python/experiments/EXP-028/code/run_experiment.py:1002-1014`), and the current results directory contains only `results.json` and `numerical_summary.txt`.",
    "impact": "This is not a correctness problem with the early exit itself; EXP-027 was AGAINST, so robustness is not eligible. The problem is documentation accuracy: the governance review describes outputs that cannot exist on the executed path, making audit expectations ambiguous.",
    "fix": "Revise the governance review and/or script output contract to distinguish the early-inconclusive path from the full robustness path. For an ineligible EXP-027 candidate, explicitly state that no segment, delay, cost, or plot artefacts are expected."
  }
]
```

## Summary

EXP-025 through EXP-028 align with the active Phase 003 design at the broad architecture level: they stay time-bar-native, avoid event-chart features, and preserve the global-holdout rule through prior analysis-set artefacts and `load_analysis_timebars()` paths. The substantive weakness is verdict and gate integrity. EXP-025 and EXP-026 loosen their support criteria enough to promote weak or negative evidence into downstream eligibility; EXP-027 then tests a manifest that should not have passed the ablation gate; EXP-028 correctly short-circuits because EXP-027 is AGAINST, but its governance artefact overstates the expected outputs.

I would not treat EXP-025 through EXP-028 as completed or reliable evidence until EXP-025 and EXP-026 verdict logic are revised, the dependent EXP-027/EXP-028 artefacts are regenerated or reclassified, and the pipeline resumes at Stage 5 for formal audit, interpretation, documentation, and post-experiment governance.
