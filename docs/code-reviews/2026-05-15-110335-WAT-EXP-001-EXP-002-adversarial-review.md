# EXP-001 and EXP-002 Adversarial Review

**Timestamp:** 2026-05-15 11:03:35 WAT  
**Scope:** EXP-001 and EXP-002 artifacts, code, generated CSV results, pipeline references, and active Phase 1 design.  
**Review mode:** `research-pipeline` context plus `bmad-review-adversarial-general` evidence-based adversarial review.  
**Subagent split:** EXP-001 and EXP-002 were reviewed by separate read-only subagents, then consolidated here.

## Context Loaded

- `.agents/skills/research-pipeline/SKILL.md`
- `.agents/skills/research-pipeline/_pipeline-config.md`
- `.agents/skills/bmad-review-adversarial-general/SKILL.md`
- `docs/references/dataset-reference.md`
- `docs/references/architecture.md`
- `python/experiments/INDEX.md`
- `docs/experiments-docs/INDEX.md`
- `docs/experiments-docs/checkpoints/2026-05-14-001-chart-type-validation/design.md`
- `python/experiments/EXP-001/**`
- `python/experiments/EXP-002/**`
- `python/src/linebreak_generator.py`
- `python/src/renko_generator.py`
- `python/src/heiken_ashi_generator.py`
- `python/src/time_alignment.py`
- `python/tests/test_chart_generators.py`

## Review Lens

Content type is empirical experiment implementation plus research governance artifacts. The active lenses are statistical validity, reproducibility, code/result integrity, governance completeness, and Phase 1 alignment.

No experiment code was executed. The underlying Parquet data and final global holdout were not loaded or inspected. Plot files were identified as present, but this review did not perform a visual/semantic PNG audit.

## Machine-Readable Findings

```json
[
  {
    "id": "EXP001-F01",
    "severity": "Major",
    "title": "SUPPORTED verdict rests on weak four-instrument bootstrap evidence",
    "evidence": "EXP-001 scope requires bootstrap 95% CIs excluding zero for support (`python/experiments/EXP-001/scope.md:24`). The analysis plan says bootstrap outputs are descriptive, not proof of independent market behavior (`python/experiments/EXP-001/analysis-plan.md:27-31`). Code bootstraps one value per instrument (`python/experiments/EXP-001/code/run_experiment.py:422-460`) and promotes CI exclusion to SUPPORT (`python/experiments/EXP-001/code/run_experiment.py:526-542`). Results show `N_Instruments=4` for all bootstrap rows (`python/experiments/EXP-001/results/bootstrap_results.csv`).",
    "impact": "The final SUPPORTED claim can appear statistically stronger than warranted. With four heterogeneous instruments, resampling instrument-level differences gives fragile confidence intervals and does not establish robust generalization.",
    "fix": "Downgrade the claim to descriptive or directional unless confirmed by a predefined validation rerun or a stronger exact/sign-based criterion. Report raw per-instrument effects as primary evidence and treat bootstrap CIs as secondary."
  },
  {
    "id": "EXP001-F02",
    "severity": "Major",
    "title": "Entropy headroom threshold overstates tiny absolute entropy gains",
    "evidence": "The success criterion uses 50% capture of remaining entropy headroom (`python/experiments/EXP-001/scope.md:24`). Code computes `(event_entropy - time_entropy) / (1.0 - time_entropy)` (`python/experiments/EXP-001/code/run_experiment.py:470-477`). Time-bar entropy is already near 1.0 in `summary_metrics.csv`; Renko's mean absolute entropy increase is only about 0.001754 bits in `bootstrap_results.csv`, yet all four Renko rows pass the entropy-headroom threshold in `threshold_evaluation.csv`.",
    "impact": "A large-looking headroom ratio is driven by a tiny denominator. The result may satisfy the formal threshold while having negligible practical information-density significance.",
    "fix": "Add an absolute entropy-gain threshold or practical-effect floor, report uncertainty for the headroom ratio itself, and interpret entropy gains separately from ghost-rate reductions."
  },
  {
    "id": "EXP001-F03",
    "severity": "Major",
    "title": "Run is not reproducible from saved EXP-001 artifacts",
    "evidence": "The script discovers input files dynamically with `DATA_DIR.glob(pattern)` and scans all matches at runtime (`python/experiments/EXP-001/code/run_experiment.py:100-111`). It imports generator modules without recording their source version or hash (`python/experiments/EXP-001/code/run_experiment.py:20-23`). Saved CSV outputs omit input file paths, file hashes, git commit, dependency versions, command line, and generator hashes (`python/experiments/EXP-001/code/run_experiment.py:1065-1078`).",
    "impact": "A later reviewer cannot prove which data files and generator implementations produced the CSVs. If source Parquet files or generator code change, EXP-001 cannot be replicated exactly.",
    "fix": "Write a run manifest under EXP-001 results with input file paths, file sizes/hashes, git commit, Python/package versions, generator parameters and source hashes, execution timestamp, and command/stdout summary."
  },
  {
    "id": "EXP001-F04",
    "severity": "Major",
    "title": "Pipeline governance is incomplete despite result CSVs",
    "evidence": "Research pipeline resume rules require `audit.md`, `results.md`, `report.md`, and post-experiment governance after results exist (`.agents/skills/research-pipeline/SKILL.md:45-59`, `.agents/skills/research-pipeline/SKILL.md:148-175`). EXP-001 has result CSVs and plots, but no `audit.md`, `results.md`, `report.md`, or `governance/post-experiment-review.md`. `python/experiments/INDEX.md` still marks EXP-001 as PLANNED, and `docs/experiments-docs/INDEX.md` is empty.",
    "impact": "The experiment has raw outputs but has not completed validation, interpretation, documentation, or final governance gates. Treating the CSV verdict as a completed research conclusion would bypass the pipeline.",
    "fix": "Resume EXP-001 at Stage 5 audit, then produce `results.md`, `report.md`, update both indexes, and add post-experiment governance before calling the experiment complete."
  },
  {
    "id": "EXP001-F05",
    "severity": "Major",
    "title": "Pre-execution governance does not match current EXP-001 code",
    "evidence": "The EXP-001 pre-execution re-review says the loader was replaced with `load_timebar_data`, deduplicates with `.unique()`, and verifies that behavior (`python/experiments/EXP-001/governance/pre-execution-review.md:69-84`). Current code defines `load_analysis_timebar_data` and scans/sorts/slices matches without `.unique()` (`python/experiments/EXP-001/code/run_experiment.py:84-112`).",
    "impact": "The governance artifact is not a reliable record of the reviewed implementation. If multiple session files overlap, duplicate rows could bias bar counts, entropy, movement, and ghost-rate metrics.",
    "fix": "Re-run pre-execution review against the exact current file, record the reviewed commit/hash, and explicitly define duplicate-session handling without silent assumptions."
  },
  {
    "id": "EXP001-F06",
    "severity": "Major",
    "title": "Duplicate SourceCloseTime handling is inconsistent across information-density metrics",
    "evidence": "The EXP-001 scope excludes same-source duplicate event rows only for the ghost-rate denominator (`python/experiments/EXP-001/scope.md:36`). Code applies that exclusion only in `compute_ghost_rate_event` (`python/experiments/EXP-001/code/run_experiment.py:232-253`). Entropy, median movement, CV, and bar density still use all generated rows (`python/experiments/EXP-001/code/run_experiment.py:829-856`). Renko can emit multiple bricks with the same source timestamp (`docs/references/architecture.md:166-188`).",
    "impact": "Renko metrics can mix real market observations with construction artifacts. Directional entropy may count multiple same-timestamp bricks, while movement metrics can include zero real-close differences from duplicate timestamps.",
    "fix": "Add unique-SourceCloseTime sensitivity metrics for Renko/event charts and report whether the verdict changes when same-source duplicates are excluded from entropy and movement calculations."
  },
  {
    "id": "EXP002-F01",
    "severity": "Major",
    "title": "Post-execution governance is incomplete despite generated results",
    "evidence": "Pipeline requires `audit.md`, `results.md`, `report.md`, index updates, and post-experiment governance after results exist (`.agents/skills/research-pipeline/SKILL.md:148-175`). EXP-002 has result CSVs and plots, but no `audit.md`, `results.md`, `report.md`, or `governance/post-experiment-review.md`. `python/experiments/INDEX.md` still marks EXP-002 as PLANNED, and `docs/experiments-docs/INDEX.md` is empty.",
    "impact": "The raw outputs should not be treated as a completed or approved experiment. There is no recorded audit verdict, interpretation artifact, final report, or phase index update.",
    "fix": "Resume EXP-002 at Stage 5 audit, then complete interpretation, documentation, index updates, and post-experiment governance before relying on the results."
  },
  {
    "id": "EXP002-F02",
    "severity": "Major",
    "title": "Pre-execution approval is stale and contradicts the current zero-baseline scope",
    "evidence": "Current scope states time bars are a lower bound with zero hybrid rate and zero transition lag by construction (`python/experiments/EXP-002/scope.md:5`). Current success criteria use absolute bounds: hybrid rate <= 0.05 and median lag <= 2 (`python/experiments/EXP-002/scope.md:24-25`). The pre-execution review instead cites a cleaner-than-time-bars framing and 20% improvement criteria (`python/experiments/EXP-002/governance/pre-execution-review.md:26-27`). Pipeline governance says percentage improvement against a zero baseline must receive REVISE (`.agents/skills/research-pipeline/SKILL.md:104-107`).",
    "impact": "The approval artifact does not match the approved scope and appears to validate an obsolete or impossible framing. This weakens confidence that Stage 4 reviewed the final artifacts against active criteria.",
    "fix": "Re-run or rewrite pre-execution governance against the current scope: absolute excess versus the zero lower bound, no percentage-improvement framing, and explicit validation of final metric definitions."
  },
  {
    "id": "EXP002-F03",
    "severity": "Major",
    "title": "Unmatched regime joins are silently dropped despite plan requiring denominator reporting",
    "evidence": "The analysis plan requires missing mappings to be reported and excluded from denominators (`python/experiments/EXP-002/analysis-plan.md:22`, `python/experiments/EXP-002/analysis-plan.md:56-57`). Code performs a left join and then drops null regime rows (`python/experiments/EXP-002/code/run_experiment.py:738-750`). The validation output records source rows, analysis rows, generated rows, and date ranges only; it has no generated-before-join count, unmatched count, or exclusion rate.",
    "impact": "Metric denominators are not auditable. If timestamp normalization, rolling-volatility nulls, or generator edge timestamps exclude rows, hybrid rate and lag results can shift without visible accounting.",
    "fix": "Record generated rows before join, matched rows, unmatched rows, null-regime exclusions, and denominator used for each metric per instrument/chart type."
  },
  {
    "id": "EXP002-F04",
    "severity": "Major",
    "title": "Transition lag metric measures next event timing, not confirmed regime reflection",
    "evidence": "Phase design defines detection lag as bars to reflect a new regime (`docs/experiments-docs/checkpoints/2026-05-14-001-chart-type-validation/design.md:91-93`). Code finds each time-bar regime transition, then records the first chart timestamp at or after that transition (`python/experiments/EXP-002/code/run_experiment.py:358-374`). It does not verify that the chart event represents the new regime boundary, that direction changed, or that one chart event is not reused across multiple rapid transitions.",
    "impact": "Median lag can make regime representation look acceptable while hiding long periods where event charts do not produce timely confirming events. This weakens any useful-regime-representation conclusion based on median lag alone.",
    "fix": "Define transition matching explicitly: require the event to map to the post-transition regime, prevent one event from satisfying multiple transitions unless justified, and report mean/p95/max or threshold exceedance rates alongside median."
  },
  {
    "id": "EXP002-F05",
    "severity": "Major",
    "title": "Regime estimator is underspecified relative to claimed realised-volatility terciles",
    "evidence": "Scope requires realised volatility on 1-minute bars and train-derived terciles (`python/experiments/EXP-002/scope.md:36`); Phase 1 includes regime labeling using realised volatility terciles (`docs/experiments-docs/checkpoints/2026-05-14-001-chart-type-validation/design.md:153`). Code implements `RealisedVol` as rolling mean of `ln(High) - ln(Low)` (`python/experiments/EXP-002/code/run_experiment.py:177-196`).",
    "impact": "A high-low range proxy is not the same as close-to-close realised volatility. The experiment may answer a range-regime question rather than the stated realised-volatility-regime question.",
    "fix": "Either revise the scope/plan to explicitly define this as a log-range volatility proxy, or implement the intended realised-volatility estimator and rerun the result tables."
  },
  {
    "id": "EXP002-F06",
    "severity": "Minor",
    "title": "Input data manifest is missing, limiting exact EXP-002 reproducibility",
    "evidence": "Code scans all matching files dynamically with `DATA_DIR.glob(pattern)` and `pl.scan_parquet(matches)` (`python/experiments/EXP-002/code/run_experiment.py:101-110`). Result validation records row counts and date ranges only; it does not record matched parquet file list, file hashes, generator commit/version, or run timestamp.",
    "impact": "A rerun after new data files are added or generator code changes may silently produce different results while appearing to use the same experiment ID.",
    "fix": "Emit a run manifest with exact input file paths, file sizes/hashes, generator parameters, code revision if available, Python/package versions, and run timestamp."
  }
]
```

## Consolidated Assessment

No Critical findings were identified, but both experiments have Major issues that block treating the generated outputs as completed, approved research. The common blocker is pipeline state: both experiments have raw result artifacts but have not completed audit, interpretation, report writing, index updates, or post-experiment governance.

EXP-001's largest empirical risk is overclaiming a SUPPORTED verdict from fragile four-instrument bootstrap evidence and a headroom-ratio threshold that magnifies tiny absolute entropy gains. EXP-002's largest empirical risk is metric validity: the transition lag implementation measures the next event timestamp, not confirmed reflection of a new regime, and denominator exclusions are not reported.

The next corrective step should be to resume both experiments at Stage 5 audit, but only after reconciling stale pre-execution governance artifacts and adding reproducibility manifests. For EXP-002, the scope/plan/code should also be reconciled on the volatility estimator and transition-lag definition before interpretation.
