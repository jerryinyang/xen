# EXP-015 Adversarial Review

**Timestamp:** 2026-05-25 05:16:09 WAT  
**Experiment:** EXP-015 - Prior High Low Sweep Reversal Behavior  
**Review skill:** bmad-review-adversarial-general  
**Pipeline context:** research-pipeline  

## Scope Reviewed

This review covers the EXP-015 scope, analysis plan, implementation, generated result artefacts, and shared ICT helper code, with context from the active Phase 003 design document and core Xen references.

Primary references:

- `docs/references/dataset-reference.md`
- `docs/references/architecture.md`
- `docs/experiments-docs/INDEX.md`
- `docs/experiments-docs/checkpoints/2026-05-23-003-ict-one-setup-timebar-validation/design.md`
- `python/experiments/INDEX.md`
- `python/experiments/EXP-015/scope.md`
- `python/experiments/EXP-015/analysis-plan.md`
- `python/experiments/EXP-015/code/run_experiment.py`
- `python/experiments/EXP-015/governance/pre-execution-review.md`
- `python/experiments/EXP-015/results/`
- `python/src/ict_timebar.py`

## Content Type And Lens

Content type: empirical study plus analysis implementation.  
Active lenses: statistical validity, reproducibility, implementation correctness, and pipeline governance completeness.

```json
[
  {
    "id": "F01",
    "severity": "Major",
    "title": "Sweep and breach arms are not mutually exclusive first-touch outcomes",
    "evidence": "In `python/experiments/EXP-015/code/run_experiment.py:123-138`, `_build_level_events` builds sweep rows and breach rows independently, then takes `groupby(\"NYDate\").head(1)` separately for each event type. Result diagnostic: `sweep_events.csv` has 4,332 of 4,837 instrument/date/level combinations containing both Sweep and Breach rows, covering 8,664 of 9,169 events.",
    "impact": "The primary comparison is framed as failed sweeps versus non-failed breaches, but most level-days contribute to both arms. This inflates counts, creates correlated observations, and can change the estimated sweep-minus-breach effect because the baseline is not a mutually exclusive alternative outcome of the first breach event.",
    "fix": "Redefine event detection as a first qualifying level interaction per instrument, NYDate, level type, and side. Classify that first interaction as exactly one of Sweep or Breach, then regenerate `sweep_events.csv`, `event_counts.csv`, `primary_effects.csv`, plots, and `results.json`. If later same-day transitions are intentionally in scope, make that a separate secondary analysis with clustered inference."
  },
  {
    "id": "F02",
    "severity": "Major",
    "title": "Post-execution pipeline artefacts are missing",
    "evidence": "`python/experiments/EXP-015/` contains `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, pre-execution governance, plots, and raw results, but no `audit.md`, `results.md`, `report.md`, or `governance/post-experiment-review.md`. The research-pipeline Stage 5-8 contract requires those artefacts after execution.",
    "impact": "The raw `AGAINST` result is not yet a completed Xen experiment finding. It has not been independently audited, interpreted into `results.md`, documented in `report.md`, indexed, or approved by post-execution governance, so it should not be treated as a citable final result.",
    "fix": "After correcting any code/result issues, run Stage 5 audit, Stage 6 interpretation, Stage 7 documentation/index updates, and Stage 8 post-execution governance for EXP-015 before relying on the conclusion."
  },
  {
    "id": "F03",
    "severity": "Major",
    "title": "Support verdict can pass on train-only or test-only evidence",
    "evidence": "`python/experiments/EXP-015/code/run_experiment.py:552-562` sets `InstrumentPass` to `train_pass or test_pass`. The scope requires evidence on at least 3 instruments with event-count thresholds per train/test segment (`python/experiments/EXP-015/scope.md:22-26`), and the active phase emphasizes robust component evidence before promotion (`design.md:102-112`).",
    "impact": "A future run or corrected event definition could mark the hypothesis as supported when three instruments pass only in train or only in test. That weakens the intended chronological validation discipline and can overstate component reliability.",
    "fix": "Predeclare whether support requires test-segment success, both train and test success, or train-discovery plus test-confirmation. Encode that rule directly in `evaluate_hypothesis_support` and mirror it in `results.json`, `results.md`, and the report."
  },
  {
    "id": "F04",
    "severity": "Major",
    "title": "Secondary outcome artefacts promised by the plan are not produced",
    "evidence": "`python/experiments/EXP-015/analysis-plan.md:25-31` calls for bootstrap confidence intervals for the primary endpoint and descriptive intervals for secondary MFE/MAE and 2R outcomes. `write_outputs` writes only `sweep_events.csv`, `event_counts.csv`, `primary_effects.csv`, and `results.json` with `primary_effects` (`run_experiment.py:755-781`).",
    "impact": "The experiment cannot substantiate the scoped failure criterion that adverse excursion dominates, and reviewers must manually derive secondary diagnostics from event-level rows. This reduces reproducibility and leaves the MFE/MAE and 2R parts of the approved analysis plan underreported.",
    "fix": "Add a structured `secondary_effects.csv` and matching JSON section for MFE_R, MAE_R, Hit2R, and time-to-stop/target summaries by instrument, segment, side, level type, and event type. Include interval methodology or explicitly downgrade those outcomes to descriptive summaries in the plan."
  },
  {
    "id": "F05",
    "severity": "Minor",
    "title": "Price precision proxy is narrower than the scoped definition implies",
    "evidence": "`scope.md:20` defines `price_precision_step` as the smallest positive observed price increment in the analysis set. `python/src/ict_timebar.py:291-312` computes it only from positive consecutive `Close` differences.",
    "impact": "The buffer floor can be sensitive to close-to-close noise and may miss increments visible in Open, High, or Low prices. ATR usually dominates the buffer, but early ATR-null rows and low-volatility periods may use an unstable precision floor.",
    "fix": "Either document that the precision proxy is deliberately close-to-close, or compute the minimum positive increment across sorted unique observed OHLC prices after rounding to instrument display precision. Report the resulting step per instrument in `results.json`."
  }
]
```

## Summary

The implementation compiles and appears to respect the major Phase 003 boundaries: time bars only, no event-chart inheritance, chronological holdout exclusion through the shared loader, NY-time conversion, and real-price outcome measurement. The main validity problem is the event construction: Sweep and Breach are not mutually exclusive first-touch classifications, so the core comparison is not yet clean enough to rely on. The raw result currently says `AGAINST`, but EXP-015 should remain incomplete until the event classification is corrected or justified and the missing Stage 5-8 pipeline artefacts are produced.
