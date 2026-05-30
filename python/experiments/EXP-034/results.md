# Results: Experiment EXP-034

## Summary

Prior-Range Location passes the Phase 005 readiness gate. Under strict aggregation, all four instruments pass row, independent-episode, determinism, and denominator checks at both `1h` and `4h`. Because strict aggregation already clears the `>=2` distinct-instrument requirement on both timeframes, strict aggregation is the canonical rule for EXP-034's descriptor and for the Phase 005 coverage decision unless the mid-phase reflection decides otherwise.

## Detailed Findings

### Strict Aggregation Is Sufficient

- **Observation**: Strict aggregation passes on `EURUSD`, `XAUUSD`, `BTCUSD`, and `USTEC` at both `1h` and `4h`.
- **Evidence**: `results/verdict.json` records `passes_readiness=true` and canonical strict aggregation for `1h` and `4h`, with all four instruments listed as passing on both timeframes.
- **Interpretation**: The tolerant `0.90` coverage rule is not needed to rescue row or episode counts. This keeps the feature definition on the clean exactly-`N` aggregation rule.

### Bucket Counts and Episodes Clear the Floors

- **Observation**: Every strict bucket/segment cell clears the predeclared row and episode floors.
- **Evidence**: In `results/readiness_table.csv`, the smallest strict bucket row count is `118` and the smallest strict independent-episode count is `35`, above the test floors of `50` rows and `15` episodes. Train floors (`100` rows, `30` episodes) are also exceeded everywhere.
- **Interpretation**: Extreme buckets are count-eligible and middle-state dominance does not block a return test.

### Coverage Loss Exists, But Does Not Block Readiness

- **Observation**: Strict dropped-window rates range from `4.44%` to `13.13%` at `1h` and from `14.10%` to `24.00%` at `4h`. Tolerant aggregation reduces retained-window loss, but matched-bucket stability fails at `EURUSD 4h` (`92.67%`) and `BTCUSD 4h` (`90.72%`).
- **Evidence**: `results/coverage_stability.csv`; `plots/01_coverage_stability.png`.
- **Interpretation**: Since strict passes the count gate, the instability of tolerant `4h` buckets is not a blocker. It is evidence for retaining strict aggregation instead of using tolerance by default for Prior-Range Location.

## Hypothesis Verdict

**SUPPORTED**

The count-eligibility hypothesis is supported. Prior-Range Location produces deterministic, denominator-valid top/middle/bottom states that meet the row and independent-episode floors on at least two distinct instruments; in fact, it passes on all four instruments at both scoped timeframes under strict aggregation.

## Limitations

- This was readiness-only. It does not show return edge, control-adjusted differentiation, or trade value.
- The tolerant aggregation diagnostic shows that partial-window tolerance can change `4h` bucket assignment for some instruments, so strict aggregation should remain the default unless a later scope gives a stronger reason to admit tolerance.
- The coverage-rate denominator was the predeclared row-count denominator; tolerant retained-window rates can be awkward around session gaps and should be treated as diagnostic rather than a physical clock-window loss estimate.

## Alternative Explanations

- Readiness may partly reflect the broad fixed `0.20/0.80` buckets rather than a useful market-state property. The return-test stage must still test whether the count-eligible states differentiate executable returns against neutral and matched-control baselines.

## Recommended Next Steps

1. Use the mid-phase reflection to authorize a Prior-Range Location return test only if EXP-035's corrected rerun and the phase direction still support it.
2. Keep strict aggregation as the default Phase 005 `1h`/`4h` aggregation rule for Prior-Range Location, because it passed without the feature instability introduced by tolerant windows.
