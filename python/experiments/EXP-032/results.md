# Results: Experiment EXP-032

## Summary

The 1-hour USTEC Candidate A breaker chain is directionally positive but fails the predeclared magnitude gate. Train and test breaker-minus-baseline Return_R_60m differences are positive and their bootstrap intervals exclude zero, but the test effect is only `+0.116R` versus the required `+0.918R` threshold, defined as 50 percent of EXP-031's 15-minute test effect. Under the approved interpretation rules, this is **REFUTED / AGAINST Branch A continuation**.

## Detailed Findings

### Event Floors Passed

- **Observation**: The 1-hour chain retained enough events for the hard count gate.
- **Evidence**:

| Segment | Sweeps | Displacement | Breaker-Labeled | Risk-Feasible Breaker | Floor >= 50 |
| --- | ---: | ---: | ---: | ---: | --- |
| Train | 417 | 189 | 144 | 143 | PASS |
| Test | 147 | 74 | 62 | 62 | PASS |

- **Interpretation**: The result is not inconclusive due to count collapse. EXP-032 has enough train and test breaker-labeled events to evaluate the magnitude gate.

### Return_R Direction Was Positive But Too Small

- **Observation**: Candidate A breaker-labeled events outperform the displacement baseline in both segments, with CIs excluding zero positively.
- **Evidence**:

| Segment | Baseline Mean | Breaker Mean | Diff | 95% CI |
| --- | ---: | ---: | ---: | --- |
| Train | `+0.103R` | `+0.320R` | `+0.216R` | `[+0.144, +0.298]` |
| Test | `+0.162R` | `+0.278R` | `+0.116R` | `[+0.039, +0.220]` |

- **Interpretation**: The positive direction survives at 1-hour resolution, but the effect is much weaker than the prior 15-minute evidence. The scoped hypothesis required both positive direction and magnitude comparability; direction alone is insufficient.

### The Binding EXP-031 Magnitude Gate Failed

- **Observation**: The 1-hour test effect is far below the binding 50 percent of EXP-031 threshold.
- **Evidence**:

| Segment | EXP-032 Diff | EXP-031 Diff | 50% of EXP-031 | Meets Gate |
| --- | ---: | ---: | ---: | --- |
| Train | `+0.216R` | `+0.517R` | `+0.258R` | NO |
| Test | `+0.116R` | `+1.836R` | `+0.918R` | NO |

The non-binding EXP-023 test half-reference was `+2.088R`; EXP-032 also falls far below that band.

- **Interpretation**: The Branch A continuation criterion fails mechanically. The test diff reaches about 6 percent of EXP-031's 15-minute test diff, not the required 50 percent.

### Retention Did Not Fail

- **Observation**: The 1-hour view reduced event count, but not enough to trigger the 30 percent retention failure rule.
- **Evidence**:
  - Displacement retention vs EXP-031: `263 / 463 = 0.568`.
  - Feasible-breaker retention vs EXP-031: `205 / 297 = 0.690`.
  - Train displacement retention: `0.558`; test displacement retention: `0.597`.
- **Interpretation**: This is a magnitude failure, not a resolution-cost count failure.

### MAE Improved But Did Not Rescue The Gate

- **Observation**: Breaker-labeled events had lower MAE_R_60m in both segments.
- **Evidence**:

| Segment | Baseline MAE_R | Breaker MAE_R | Diff | 95% CI |
| --- | ---: | ---: | ---: | --- |
| Train | `0.481R` | `0.324R` | `-0.157R` | `[-0.226, -0.096]` |
| Test | `0.470R` | `0.311R` | `-0.159R` | `[-0.327, -0.029]` |

MFE_R_60m did not improve reliably: train diff `+0.038R` with CI crossing zero; test diff `-0.011R` with CI crossing zero.

- **Interpretation**: The breaker still selects somewhat cleaner events by adverse excursion, but the structural drawdown improvement is too small to compensate for the failed Return_R magnitude gate.

## Hypothesis Verdict

**REFUTED / AGAINST Branch A continuation**

The hypothesis required the USTEC Candidate A breaker chain at 1-hour resolution to preserve the EXP-031 positive direction and reach the predeclared minimum magnitude. Counts passed and direction stayed positive, but the test Return_R_60m diff was `+0.116R`, far below the `+0.918R` hard gate. Per `scope.md`, this stops Branch A before EXP-033 unless a new reflection explicitly reframes the branch with weaker claims.

## Limitations

- USTEC is the only instrument in scope; no cross-instrument claim is made.
- The bootstrap is event-level and descriptive; it does not remove all temporal-dependence risk.
- One train breaker-labeled row is risk-feasible but has no forward 1-minute path, so finite Return_R means and CIs exclude it. The hard decision is unchanged because all count floors remain above threshold and the result fails on magnitude.
- Duplicate level-family events are retained by the scoped denominator policy, so same-candle PDH/ONH or PDL/ONL triggers can both count when they are distinct first-touch level-family events.

## Alternative Explanations

- The 1-hour detector may be too coarse for the Candidate A breaker edge: it keeps enough events, but the larger bar compresses entry timing and structure into a weaker signal.
- The 15-minute positive may depend on a resolution-specific balance: enough aggregation to reduce noisy 1-minute behavior, but not so much that the return horizon is mostly consumed by the confirming candle.
- MAE improvement suggests the breaker label is not meaningless; it may filter adverse excursion without preserving enough 60-minute return magnitude for candidate promotion.

## Recommended Next Steps

1. Do not scope EXP-033 temporal segmentation as originally planned.
2. Route Branch A back to checkpoint reflection for a close-or-reframe decision.
3. If Branch A is reframed, it should be a new, weaker question about drawdown filtering or timing sensitivity, not an automatic continuation of the current Candidate A validation path.
