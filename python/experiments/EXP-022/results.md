# Results: Experiment EXP-022

## Summary

EXP-022 supports the scoped hypothesis. Both breaker candidates are mechanically reproducible on all four instruments, but only Candidate A clears the predeclared occurrence floor in both train and test on at least three instruments. Candidate A therefore qualifies as the single objective breaker definition for downstream testing, while Candidate B remains deterministic but too sparse on EURUSD and BTCUSD test segments to pass the readiness gate.

## Detailed Findings

### Candidate A Meets The Readiness Gate

- **Observation**: Candidate A clears the `>= 50` event floor in every train and test segment.
- **Evidence**: `candidate_counts.csv` reports Candidate A counts of EURUSD `140/54`, XAUUSD `172/79`, BTCUSD `239/66`, and USTEC `205/86` for train/test, with `EventFloorMet=True` in all eight rows.
- **Interpretation**: Candidate A satisfies the scoped support condition by providing deterministic boundaries plus enough sample size on more than the required three instruments.

### Candidate B Is Reproducible But Not Broadly Eligible

- **Observation**: Candidate B reproduces exactly across reruns, yet misses the test floor on two instruments.
- **Evidence**: `reproducibility.csv` shows matching SHA-256 digests for Candidate B on EURUSD, XAUUSD, BTCUSD, and USTEC. However, `candidate_counts.csv` reports Candidate B Test counts of EURUSD `40` and BTCUSD `49`, both below the `>= 50` threshold.
- **Interpretation**: Candidate B is objective enough to compute, but not broadly ready for the next-stage outcome experiment under the scoped floor rule.

### Ambiguity Is Not The Limiting Factor

- **Observation**: Both candidates show zero recorded ambiguity in every instrument-segment row.
- **Evidence**: `candidate_counts.csv` reports `AmbiguousN=0` and `AmbiguityRate=0.0` throughout, and `selection.json` records `mean_ambiguity_rate = 0.0` for both candidates.
- **Interpretation**: The selection difference is driven by event availability, not by discretionary boundary handling.

## Hypothesis Verdict

**SUPPORTED**

The experiment asked whether at least one objective breaker candidate could be defined reproducibly with enough occurrences to justify outcome testing. Candidate A satisfies that requirement on all four instruments in both train and test, so the hypothesis is supported.

## Limitations

- This experiment evaluates reproducibility and count readiness only; it does not make any profitability or trade-quality claim.
- Candidate readiness is specific to the scoped floor of `>= 50` events per instrument-segment and the fixed EXP-018 displacement prerequisite.
- Candidate B may still be usable for narrower follow-up work, but not for the broad downstream test defined here.

## Alternative Explanations

- Candidate B's lower counts may reflect a stricter causal swing-break construction rather than inferior concept quality; this experiment was not designed to separate those explanations.
- Candidate A's stronger retention could partly reflect its broader last-opposite-candle proxy, which still requires separate outcome validation in EXP-023.

## Recommended Next Steps

1. Use Candidate A as the fixed breaker definition for any rerun or continuation of EXP-023.
2. Treat Candidate B as a separate narrower follow-up only if a future scope explicitly targets lower-frequency breaker structures.
