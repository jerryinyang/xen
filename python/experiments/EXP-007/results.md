# Results: Experiment EXP-007

## Summary

EXP-007 supports the Phase 2 measurement-gate hypothesis. The multi-state signal-quality framework differentiated chart types enough to proceed with Block B: three pre-specified proceed criteria were met, all at the 15-minute timeframe. The result is not a simple event-chart quality win. The strongest pattern is a Renko/LineBreak risk-shaping trade-off at 15 minutes: event charts generally reduce adverse excursion, but Renko also reduces favourable excursion and does not improve signal-level precision or run continuation by the required thresholds.

## Detailed Findings

### 1. The Proceed Gate Passed At 15 Minutes

- **Observation**: Three proceed criteria were met:
  - 15-minute Renko AE60: 4 of 4 instruments pass, with CIs excluding zero.
  - 15-minute Renko FE60: 4 of 4 instruments pass, with CIs excluding zero.
  - 15-minute LineBreak AE60: 3 of 4 instruments pass, with CIs excluding zero.
- **Evidence**: `proceed_criteria.parquet` reports `ProceedCriterionMet = true` for those three rows. No 1-minute criterion passed.
- **Interpretation**: The framework provides a differentiating measurement language for downstream Block B experiments. The differentiating metrics that should carry forward are FE60 and AE60 at the 15-minute timeframe.

### 2. Renko's 15-Minute Differentiation Is A Trade-Off

- **Observation**: At 15 minutes, Renko has lower AE60 than Time on all four instruments, but also lower FE60 on all four instruments.
- **Evidence**:
  - AE60 Renko-minus-Time mean differences: BTCUSD `-0.738`, EURUSD `-0.299`, USTEC `-0.448`, XAUUSD `-0.400`; all CIs exclude zero.
  - FE60 Renko-minus-Time mean differences: BTCUSD `-0.242`, EURUSD `-0.427`, USTEC `-0.282`, XAUUSD `-0.326`; all CIs exclude zero.
  - Weighted overall 15-minute means: Renko FE60 `4.644` vs Time `4.964`; Renko AE60 `4.462` vs Time `4.943`.
- **Interpretation**: Renko does not simply improve signal quality. It selects a lower-excursion profile in both favourable and adverse directions. Downstream experiments should preserve FE and AE separately rather than collapse them into a single quality score.

### 3. Precision And Run Continuation Did Not Justify Proceeding

- **Observation**: Signal-level precision and run-continuation criteria did not meet the pre-specified thresholds.
- **Evidence**:
  - Weighted 15-minute precision: Time `0.836`, Heiken Ashi `0.836`, LineBreak `0.824`, Renko `0.818`.
  - Weighted 1-minute precision: Time `0.838`, Heiken Ashi `0.835`, LineBreak `0.833`, Renko `0.836`.
  - Run-continuation differences were small and mostly negative for event charts; no proceed row was true for run continuation.
- **Interpretation**: The downstream measurement vocabulary should not rely on signal-level precision or run continuation as primary discriminators for EXP-008 through EXP-011 unless those experiments define new, pre-approved criteria.

### 4. Missing-Signal States Are Material

- **Observation**: Event charts emit far fewer signals than Time and Heiken Ashi, and the missing-signal state is large enough to affect downstream interpretation.
- **Evidence**:
  - 1-minute LineBreak: 951,812 signals over 3,622,414 source bars; missing share `0.737`.
  - 1-minute Renko: 1,014,661 signals; missing share `0.720`.
  - 15-minute LineBreak: 55,726 signals over 235,362 source bars; missing share `0.763`.
  - 15-minute Renko: 56,662 signals; missing share `0.759`.
- **Interpretation**: Event-chart comparisons must continue to report coverage and missing states explicitly. Dropping non-emission periods would overstate event-chart quality.

### 5. Binary Direction Remains Inadequate

- **Observation**: The multi-state outputs differentiate chart types where binary direction alone cannot express the trade-off: Renko at 15 minutes has both lower favourable and lower adverse excursion versus Time.
- **Evidence**: FE60 and AE60 pass the proceed gate, while precision and run continuation do not. The differentiating evidence comes from excursion distributions, not from a bounded binary hit-rate summary.
- **Interpretation**: Binary direction is not an adequate summary of signal quality for Phase 2. FE and AE distributions should remain primary.

## Hypothesis Verdict

**SUPPORTED**

The hypothesis is supported because the framework produced pre-specified differentiation across chart types, meeting the Block B proceed gate through 15-minute FE60 and AE60 comparisons. The support is conditional in meaning: it validates the measurement framework and permits downstream experiments, but it does not establish that event-chart signals are categorically better than time-bar signals.

## Limitations

- Bootstrap intervals use row-level resampling over overlapping forward windows, so temporal dependence remains. Interpret CIs as descriptive uncertainty checks, not independent-trial proof.
- FE and AE use future windows by design as post-signal outcome labels. They are valid for characterization, not live signal inputs.
- The result identifies differentiating metrics for Block B but does not choose a strategy, threshold, or chart type.
- The strongest evidence appears only at 15 minutes. No 1-minute proceed criterion passed.

## Alternative Explanations

- The 15-minute event-chart effect may reflect signal sparsity and compression rather than superior directional information.
- Lower FE and lower AE for Renko could mean reduced exposure to large subsequent moves in both directions, not improved signal selectivity.
- Precision saturation around 0.82-0.84 may make the FE threshold too coarse for distinguishing chart types in this baseline.

## Recommended Next Steps

1. Continue to EXP-008 through EXP-011 using FE60 and AE60 as the primary carried-forward metrics.
2. Treat precision and run continuation as secondary diagnostics unless a later scope predefines stronger criteria.
3. Preserve missing-signal states and signal-count ratios in every downstream Block B experiment.
