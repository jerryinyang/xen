# Adversarial Code Review: EXP-021 through EXP-024

**Review timestamp:** 2026-05-25 22:55:25 WAT  
**Reviewer mode:** `bmad-review-adversarial-general` with `research-pipeline` context  
**Scope:** Individual pre-execution review of EXP-021, EXP-022, EXP-023, and EXP-024 artefacts and code.  
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

Content type: empirical experiment artefacts plus Python implementation. Active lenses: statistical validity, reproducibility, causal timing/look-ahead risk, scope compliance, and implementation correctness.

## EXP-021 - IFVG Confirmation Entry Quality

```json
[
  {
    "id": "EXP021-F01",
    "severity": "Major",
    "title": "IFVG matching can attach pre-existing FVGs to later displacement events",
    "evidence": "Scope requires a chain through sweep rejection, displacement close, FVG formation, and IFVG close (`python/experiments/EXP-021/scope.md:20`). `_find_ifvg_for_event()` only filters by `Instrument` and `Side`, then selects the first `InversionTime` after `DisplacementTime` without checking `CreationTime` relative to the sweep or displacement (`python/experiments/EXP-021/code/run_experiment.py:167-177`).",
    "impact": "A zone formed before the sweep/displacement can be counted as the IFVG confirmation for a later setup. That weakens the causal event chain and can make EXP-021 measure reuse of old zones rather than the scoped H4 confirmation sequence.",
    "fix": "Require the matched IFVG to satisfy the intended temporal chain, for example `CreationTime >= DisplacementTime` if FVG formation must follow displacement, or explicitly document and test a different allowed ordering before execution."
  },
  {
    "id": "EXP021-F02",
    "severity": "Major",
    "title": "Train/test segment can be inherited from displacement even when IFVG occurs in another segment",
    "evidence": "The scope requires nested chronological train/test analysis inside the 70 percent analysis set (`python/experiments/EXP-021/scope.md:15`). The matched IFVG dataframe is not filtered by `Segment` and `FVG_REQUIRED` does not require a segment column (`python/experiments/EXP-021/code/run_experiment.py:69-72`, `python/experiments/EXP-021/code/run_experiment.py:167-177`). `_build_entry_row()` labels every IFVG entry with `disp['Segment']` (`python/experiments/EXP-021/code/run_experiment.py:213-224`).",
    "impact": "A train displacement near the segment boundary can be paired with a test IFVG and still be reported as Train. This contaminates segment interpretation and can make train/test event floors and bootstrap comparisons unreliable.",
    "fix": "Carry `Segment` from the actual IFVG/inversion timestamp or reject candidate matches whose `InversionTime` falls outside the displacement event's segment."
  },
  {
    "id": "EXP021-F03",
    "severity": "Major",
    "title": "Verdict logic does not implement the stated improvement criterion",
    "evidence": "The success criterion allows support only when IFVG improves expectancy or drawdown-adjusted return versus simpler entries on at least 3 instruments with event floors (`python/experiments/EXP-021/scope.md:24`; `python/experiments/EXP-021/analysis-plan.md:42`). `evaluate_verdict()` checks only positive `Return_R_60m` CIs and marks an instrument as improving if any qualifying comparison exists (`python/experiments/EXP-021/code/run_experiment.py:422-441`).",
    "impact": "The experiment can report support from one positive return comparison in one segment while ignoring drawdown-adjusted return, MAE worsening, or failure against the other simpler baseline. This creates an over-supportive verdict path.",
    "fix": "Encode the criterion explicitly: require the event floor in both segments and define whether support must beat both `SweepClose` and `DisplacementClose`, and include the drawdown-adjusted or MAE constraint in the pass condition."
  }
]
```

EXP-021 is structurally close to the intended H4 test, but the IFVG matching and verdict mapping are too permissive. The highest risk is causal misassignment of IFVGs to prerequisite events.

## EXP-022 - Objective Breaker Candidate Reproducibility

```json
[
  {
    "id": "EXP022-F01",
    "severity": "Major",
    "title": "Candidate A searches before sweep despite being specified before displacement",
    "evidence": "The analysis plan defines Candidate A as the last opposite-direction candle before displacement (`python/experiments/EXP-022/analysis-plan.md:11`). The code comment also says `candidate_A` is before displacement (`python/experiments/EXP-022/code/run_experiment.py:5-9`), but `_find_last_opposite_candle()` searches before `sweep_ns` (`python/experiments/EXP-022/code/run_experiment.py:143-162`) and `detect_candidate_a()` passes `disp['SweepTime']` as that boundary (`python/experiments/EXP-022/code/run_experiment.py:211-227`).",
    "impact": "Candidate A is not the artifact described by the plan or top-level config. Its counts, boundaries, and eventual eligibility for EXP-023 can differ materially from the intended order-block proxy.",
    "fix": "Search for the last opposite candle before `DisplacementTime`, or revise the scope/plan/config to state that the order-block proxy is intentionally anchored before sweep."
  },
  {
    "id": "EXP022-F02",
    "severity": "Major",
    "title": "Candidate B selection counts can include breaker confirmations before displacement",
    "evidence": "The scope says breaker candidates are evaluated after an EXP-015 failed sweep and an approved displacement event (`python/experiments/EXP-022/scope.md:20`). `_find_cand_b_breaker()` accepts `disp_ns` but never uses it, starts at `sweep_ns`, and searches forward from the sweep (`python/experiments/EXP-022/code/run_experiment.py:305-324`).",
    "impact": "Candidate B may satisfy reproducibility and event-count floors using confirmations that occurred before the approved displacement prerequisite. EXP-023 later filters `BreakerTime > DisplacementTime`, but EXP-022's candidate selection could already be biased by invalid early confirmations.",
    "fix": "Start Candidate B confirmation search after `DisplacementTime`, or compute selection counts using the same post-displacement eligibility rule that downstream outcome testing requires."
  },
  {
    "id": "EXP022-F03",
    "severity": "Major",
    "title": "Invalidation and ambiguity criteria are not substantively implemented",
    "evidence": "The scope requires boundaries, confirmation timestamp, invalidation, and duplicate handling to be recorded (`python/experiments/EXP-022/scope.md:20`). Candidate A and B event rows record boundaries and confirmation fields, but no invalidation fields or duplicate-source handling; both candidate finders set `Ambiguous` to `False` unconditionally (`python/experiments/EXP-022/code/run_experiment.py:181-194`, `python/experiments/EXP-022/code/run_experiment.py:329-350`).",
    "impact": "The reported ambiguity rate and selection criterion can look clean even though ambiguity and invalidation were not actually measured. This undermines EXP-022's purpose as a reproducibility gate before outcome testing.",
    "fix": "Define invalidation and duplicate rules for each candidate, emit explicit fields for those states, and compute ambiguity from real unresolved or multi-match cases instead of hard-coding `False`."
  }
]
```

EXP-022 has the most important precondition risk. Since EXP-023 depends on its selected breaker candidate, the before-sweep/before-displacement mismatch should be fixed before relying on any selection output.

## EXP-023 - Breaker Confirmation Trade Quality

```json
[
  {
    "id": "EXP023-F01",
    "severity": "Major",
    "title": "Breaker join key can misattach events when multiple level types share a sweep timestamp",
    "evidence": "The scope requires one approved breaker definition and a predeclared baseline without post-hoc selection (`python/experiments/EXP-023/scope.md:20`). Baseline events include `LevelType`, `NYDate`, and `Segment` as required fields (`python/experiments/EXP-023/code/run_experiment.py:53-57`), but breaker events are required only by `Instrument`, `Segment`, `Side`, `SweepTime`, `BreakerTime`, and `BreakerClose` (`python/experiments/EXP-023/code/run_experiment.py:62-63`). `build_breaker_entries()` joins only on `Instrument`, `SweepTime`, and `Side` (`python/experiments/EXP-023/code/run_experiment.py:166-181`).",
    "impact": "If two liquidity levels produce events with the same instrument, side, and sweep time, a breaker can be attached to the wrong baseline level or duplicate multiple rows. That changes event counts, retention, and outcome estimates.",
    "fix": "Preserve and join on the full event identity from EXP-015/EXP-018, including at least `LevelType`, `NYDate`, `Segment`, and a stable event id; report duplicate key counts before outcome computation."
  },
  {
    "id": "EXP023-F02",
    "severity": "Major",
    "title": "Drawdown-adjusted return criterion is not implemented",
    "evidence": "The scope requires reporting expectancy, drawdown proxy, trade count, and average R (`python/experiments/EXP-023/scope.md:20`), and the success criterion allows support via expectancy or drawdown-adjusted return (`python/experiments/EXP-023/scope.md:24`). The code summarizes only mean Return_R, MAE_R, and Hit1R (`python/experiments/EXP-023/code/run_experiment.py:316-339`) and the verdict checks only positive Return_R bootstrap differences (`python/experiments/EXP-023/code/run_experiment.py:342-372`).",
    "impact": "The experiment cannot distinguish genuine drawdown-adjusted improvement from a higher mean return with worse adverse excursion or weaker path quality. This can overstate support for the H5 breaker component.",
    "fix": "Define and compute the drawdown proxy before execution, include it in output tables and bootstrap comparisons, and make the support verdict require either predeclared expectancy improvement or predeclared drawdown-adjusted improvement."
  }
]
```

EXP-023 is blocked mainly by dependency integrity and verdict completeness. The script is syntactically valid, but its event identity and drawdown criteria need tightening before execution.

## EXP-024 - Second Candle Open Execution Timing

```json
[
  {
    "id": "EXP024-F01",
    "severity": "Major",
    "title": "FirstRetest uses the touch bar's open time, creating intrabar look-ahead risk",
    "evidence": "The scope defines first retest as the first later bar whose high/low touches the confirmation zone before invalidation (`python/experiments/EXP-024/scope.md:20`). `simulate_entry_variants()` detects the touch using the bar's completed high/low, then records the entry time as that same bar's `OpenTime` (`python/experiments/EXP-024/code/run_experiment.py:211-224`). Outcomes then use `compute_real_price_outcome()`, which includes bars with `CloseTime > EntryTime` (`python/src/ict_timebar.py:361-390`).",
    "impact": "The outcome window can include the full OHLC range of the bar used to detect the retest, including movement that occurred before the zone touch. This biases FirstRetest outcomes and violates the phase's causal timing discipline.",
    "fix": "Either enter at the touch bar close after the touch is knowable, or treat the touch bar as intrabar-ambiguous and exclude its range from outcome measurement unless a deterministic intrabar ordering assumption is explicitly scoped."
  },
  {
    "id": "EXP024-F02",
    "severity": "Major",
    "title": "Verdict can pass instruments with missing or NaN second-candle comparisons and ignores one segment",
    "evidence": "The analysis has Train and Test segment rows in the bootstrap output (`python/experiments/EXP-024/code/run_experiment.py:345-373`). `evaluate_verdict()` filters only by instrument, entry proxy, and metric, then uses `iloc[0]` for return and MAE (`python/experiments/EXP-024/code/run_experiment.py:431-455`). If CI values are NaN, the `np.isfinite(...)` checks are false and the default `True` pass state remains in force (`python/experiments/EXP-024/code/run_experiment.py:442-455`).",
    "impact": "The verdict can ignore Test results and treat insufficient data as not worse. This can falsely support the second-candle-open rule even when one segment is missing, degraded, or uncomputed.",
    "fix": "Evaluate Train and Test explicitly, require finite bootstrap CIs and minimum paired event counts, and classify missing or NaN comparisons as inconclusive rather than pass."
  },
  {
    "id": "EXP024-F03",
    "severity": "Major",
    "title": "Slippage proxy criterion is plotted but not part of the verdict",
    "evidence": "The success criterion requires second-candle-open to have equal or better expectancy/MAE without worse slippage proxy (`python/experiments/EXP-024/scope.md:24`). The code plots absolute entry displacement from ConfirmationClose (`python/experiments/EXP-024/code/run_experiment.py:481-523`), but `evaluate_verdict()` considers only Return_R and MAE_R (`python/experiments/EXP-024/code/run_experiment.py:421-474`).",
    "impact": "EXP-024 can support the second-candle-open rule even when the slippage proxy materially worsens. That misses one of the experiment's explicit execution-quality constraints.",
    "fix": "Compute a signed, direction-aware slippage proxy by entry variant, bootstrap or threshold it as predeclared, and include it in the support/against/inconclusive verdict logic."
  }
]
```

EXP-024 has a causal timing risk in the retest variant and an over-permissive verdict function. These issues should be corrected before interpreting any second-candle-open support/against result.

## Cross-Experiment Conclusion

The artefacts are aligned with the active ICT checkpoint at a high level: they use time bars, avoid event-chart features, and preserve the manual execution gate. The main weaknesses are in event-chain identity, causal ordering, and verdict implementations that are looser than the written success criteria. I would not rely on EXP-021 through EXP-024 outputs until these issues are revised and governance is rerun.
