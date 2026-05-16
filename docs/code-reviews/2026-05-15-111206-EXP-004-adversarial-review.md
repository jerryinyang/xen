# Adversarial Review: EXP-004 — Market Structure Capture Speed & Fidelity

**Date:** 2026-05-15T11:12:06Z
**Reviewer:** Automated adversarial review
**Content type:** Empirical study — statistical methodology, detection speed/precision trade-off
**Review lenses:** Statistical methodology > reproducibility > code correctness > specification compliance

---

## Artifacts Reviewed

| Artifact | Path |
|----------|------|
| Scope | `python/experiments/EXP-004/scope.md` |
| Analysis Plan | `python/experiments/EXP-004/analysis-plan.md` |
| Implementation | `python/experiments/EXP-004/code/run_experiment.py` |
| Pre-Execution Governance | `python/experiments/EXP-004/governance/pre-execution-review.md` |
| Phase Design | `docs/experiments-docs/checkpoints/2026-05-14-001-chart-type-validation/design.md` |

**Note:** No results, audit, or post-execution governance artifacts exist yet. This review covers pre-execution artifacts only.

---

## Context

EXP-004 tests whether Line Break (level 3) and Renko (ATR-14) detect real-price trend reversals faster than 1-minute time bars, and whether their precision trade-off is characterisable. It is one of six experiments in Phase 1 (Chart-Type Validation), which is characterisation-only — no strategy backtesting, no P&L, no parameter optimisation.

The experiment builds a real-price reversal reference from ATR-scaled swing detection on 1-minute time bars, extracts direction-change signals from each chart type, and matches signals to reversals within a fixed tolerance window. Metrics are latency, precision, recall, split rate, and paired bootstrap CIs across instruments.

---

## Findings

```json
[
  {
    "id": "F01",
    "severity": "Major",
    "title": "Precision metric excludes duplicate signals from denominator",
    "evidence": "compute_metrics() defines Precision = matched / (matched + false_count) (line ~481). Duplicate signals that fall within the tolerance window of a matched reversal are excluded from the precision denominator entirely.",
    "impact": "Precision is inflated for chart types that emit many direction changes per real event (especially Line Break and Renko). The core hypothesis — speed-precision trade-off — is measured against a metric that understates how many signals are non-informative. A chart type with 1 matched signal, 0 false signals, and 20 duplicate signals would show Precision = 1.0, hiding the fact that 95% of its signals are redundant.",
    "fix": "Report both the current precision (matched-only denominator) and a total precision defined as matched / (matched + false_count + duplicate_count). Label them distinctly (e.g. 'MatchPrecision' and 'SignalPrecision'). Update scope success criteria to reference the appropriate metric, or at minimum, make the exclusion explicit in results interpretation."
  },
  {
    "id": "F02",
    "severity": "Major",
    "title": "Sensitivity check computed but not analysed",
    "evidence": "scope.md line 26: 'Inconclusive: reversal labels are unstable under a simple sensitivity check.' Code computes alt_reversals with threshold 2.0 (line ~871) and prints counts only (line ~1049). No quantitative stability assessment is performed — no comparison of reversal overlap, latency shift, or precision change between thresholds.",
    "impact": "The experiment's own inconclusive criterion cannot be evaluated. If reversal labels are unstable across a small threshold change, the entire analysis rests on arbitrary parameter choice, and the scope-mandated inconclusive verdict would be unreached.",
    "fix": "Add a sensitivity comparison that (a) computes reversal overlap between primary and alternate thresholds, (b) reports median latency and precision for both, and (c) produces a stability flag when overlap drops below a threshold (e.g. < 70% of primary reversals appear in alternate). This can be done within the existing complexity budget as it is a standard sensitivity check, not a new hypothesis test."
  },
  {
    "id": "F03",
    "severity": "Major",
    "title": "Paired bootstrap on N=4 instruments has unreliable CI width",
    "evidence": "bootstrap_paired_latency_ci() resamples 4 instrument-level latency differences with replacement (line ~548-558). N_BOOTSTRAP = 10,000 resamples from a population of 4 values.",
    "impact": "Bootstrap CIs from 4 observations are extremely wide and unstable. With N=4, the minimum possible CI width spans approximately 2 of the 4 values, and the resampled distribution is a coarse approximation. The CI may include zero simply from low power rather than genuine null effects, leading to false 'no difference' conclusions — or exclude zero from sampling noise alone.",
    "fix": "Two options: (a) Supplement bootstrap with exact permutation inference (exactly 2^4 = 16 sign flips, fully enumerated), which provides exact p-values without distributional assumptions. (b) Report bootstrap CIs alongside the raw per-instrument latency differences table, making the N=4 limitation transparent. Either approach stays within the 3-test budget (replace or supplement the bootstrap)."
  },
  {
    "id": "F04",
    "severity": "Minor",
    "title": "Tolerance window (120 min) not justified or specified in scope/plan",
    "evidence": "TOLERANCE_MINUTES = 120 is defined as a constant in code (line 59) but not referenced in scope.md or analysis-plan.md. The pre-execution governance review notes this as informational only.",
    "impact": "Matching results are sensitive to tolerance choice. A 120-minute window is generous for 1-minute bars — it allows a signal emitted up to 2 hours after a reversal to count as a detection. This may inflate recall and underestimate latency for slow-detecting chart types. Conversely, a shorter window could miss valid delayed detections. The lack of documentation makes it hard to assess whether 120 min is appropriate for all four instruments, which span forex, commodity, crypto, and index markets with very different typical reversal timescales.",
    "fix": "Document the tolerance choice in scope.md or analysis-plan.md with rationale. Consider reporting sensitivity to tolerance (e.g. results at 30, 60, 120 min) as a supplementary table, or at minimum flag in interpretation that results depend on this untested parameter."
  },
  {
    "id": "F05",
    "severity": "Minor",
    "title": "Early return classifies all signals as duplicates when zero reversals",
    "evidence": "match_signals_to_reversals() line 341: `return empty, 0, 0 if len(signals) == 0 else len(signals)`. By Python operator precedence, when `len(real_reversals) == 0` and `len(signals) > 0`, this returns `(empty, 0, len(signals))` — classifying all signals as duplicate_count and 0 as false_count.",
    "impact": "If no real reversals are detected for an instrument (unlikely but possible for BTCUSD or USTEC with limited data), every signal would be counted as a duplicate rather than a false signal, inflating SplitRate and understating FalsePerDay. The downstream metrics would be wrong for that instrument.",
    "fix": "Rewrite the early return as: `if len(signals) == 0: return empty, 0, 0; else: return empty, len(signals), 0`. All unmatched signals when there are no real reversals are false signals, not duplicates."
  },
  {
    "id": "F06",
    "severity": "Minor",
    "title": "Single Parquet file per instrument may miss multi-session data",
    "evidence": "load_timebar_data() uses `sorted(DATA_DIR.glob(pattern))[-1]` (line 86), selecting only the last file alphabetically. The dataset reference states 'one base Parquet file per symbol/session', implying multiple sessions may exist.",
    "impact": "If multiple session files exist for an instrument, only the last (alphabetically) is used. The analysis would then cover only one session's worth of data rather than the 'full available dataset per instrument' required by scope.md. This could reduce sample size, bias the reversal reference toward a single market regime, and invalidate the success criterion of 'at least 3 instruments'.",
    "fix": "Concatenate all matching Parquet files per instrument, sort by CloseTime, and deduplicate. Alternatively, document that the current dataset has one file per instrument and verify this assumption at runtime with an assertion or warning."
  },
  {
    "id": "F07",
    "severity": "Minor",
    "title": "Scope mentions nested train/test split not implemented",
    "evidence": "scope.md line 16: 'within that [analysis set], first 70% = train segment and last 30% = test segment.' Code uses the full analysis set without nested split. Pre-execution governance notes this as acceptable for Phase 1 characterisation.",
    "impact": "No immediate impact for this experiment since no model is trained. However, the scope document explicitly describes a split that isn't implemented, which creates a specification-implementation mismatch. If a future experiment references EXP-004's scope as precedent, it may incorrectly assume a train/test separation exists.",
    "fix": "Update scope.md to clarify that for this Phase 1 characterisation experiment, the full analysis set is used without a nested train/test split because no model training occurs. Remove or clarify the train/test language to avoid confusion."
  },
  {
    "id": "F08",
    "severity": "Minor",
    "title": "Volatility regime stratification mentioned but not implemented",
    "evidence": "analysis-plan.md line 74: 'Report optional low/medium/high volatility breakdown only if each regime has enough reversals for stable summaries.' The code contains no regime stratification logic at all.",
    "impact": "Low impact — the plan marks this as optional. However, latency and precision may vary substantially across volatility regimes, and the experiment's interpretability is reduced without at least reporting whether enough reversals exist per regime to attempt stratification.",
    "fix": "Add a brief regime count check: classify reversals into low/medium/high volatility terciles and report counts per tercile. If any tercile has fewer than e.g. 20 reversals, skip stratified metrics. This is descriptive, not a new hypothesis test, and stays within budget."
  }
]
```

---

## Summary

The experiment's methodology is sound in principle — ATR-scaled swing reversal detection, direction-change signals, and event matching are appropriate choices for characterising speed-precision trade-offs. However, three findings warrant action before relying on the results:

1. **Precision definition (F01)**: Duplicate signals are excluded from the precision denominator, inflating precision for event-based chart types and potentially mischaracterising the core speed-precision trade-off. This is the most consequential finding because it directly affects the hypothesis test.

2. **Incomplete sensitivity analysis (F02)**: The alternative threshold reversals are computed but never compared to the primary, leaving the scope's inconclusive criterion untestable.

3. **Bootstrap power (F03)**: Four-instrument bootstrap CIs are unreliable. The experiment should either supplement with exact permutation tests or make the small-N limitation explicit in results.

The remaining findings (F04–F08) are minor and do not block execution, but F04 (tolerance window justification) and F05 (early return bug) should be addressed for correctness before running the experiment.

---

## Pre-Execution Governance Verdict Assessment

The pre-execution governance review approved EXP-004. This adversarial review identifies issues that the governance review did not catch, specifically F01 (precision definition) and F02 (sensitivity incompleteness). The governance review correctly noted the ATR variant, tolerance window, and missing train/test split as informational items, but did not examine the precision denominator definition or the sensitivity analysis completeness. A revised governance review should re-evaluate after F01–F03 are addressed.