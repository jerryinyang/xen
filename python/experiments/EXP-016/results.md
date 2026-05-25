# Results: Experiment EXP-016

## Summary

EXP-016 is INCONCLUSIVE. Inside-macro sweep samples and same-day matched outside comparator samples are too small to support or refute the claim that macro-window context materially changes sweep outcomes. No instrument satisfies the required train/test event floors for both inside-window sweeps and matched outside-window comparators.

## Detailed Findings

### Matched Macro-Context Comparison Is Not Evaluable

- **Observation**: No instrument meets the train/test floors needed for interpretation.
- **Evidence**: Test inside-window sweep counts are EURUSD `24`, XAUUSD `27`, BTCUSD `21`, and USTEC `34`, all below the `>=50` floor. Test matched outside comparator counts are EURUSD `2`, XAUUSD `4`, BTCUSD `1`, and USTEC `12`, also below the `>=50` floor.
- **Interpretation**: The matched comparison is too sparse to support a FOR or AGAINST verdict.

### Same-Day Matching Removes Most Outside Sweeps

- **Observation**: The date/side matched outside baseline retains only a small fraction of outside sweeps.
- **Evidence**: Test matched fractions are EURUSD `3.1%`, XAUUSD `3.8%`, BTCUSD `1.4%`, and USTEC `9.5%`.
- **Interpretation**: The matched control is conservative but expensive. It reduces session/date confounding at the cost of making the primary comparison underpowered.

### Raw Effects Are Unstable And Should Not Be Overinterpreted

- **Observation**: Some point estimates are positive, but intervals are wide or unavailable and all rows are non-evaluable.
- **Evidence**: USTEC Test HitDiff is `+0.237` with CI `[-0.081, 0.525]`; XAUUSD Test HitDiff is `+0.083` with CI `[-0.583, 0.542]`; BTCUSD Test HitDiff is unavailable because the matched outside hit sample has zero non-ambiguous observations.
- **Interpretation**: The raw effects are descriptive diagnostics only. They do not establish that macro windows improve sweep outcomes.

## Hypothesis Verdict

**INCONCLUSIVE**

The scoped support rule requires at least 3 instruments with adequate event/comparator coverage and either `>= 5pp` improvement in 60-minute 1R-before-stop probability or `>= 0.25R` reduction in median MAE. EXP-016 has `0/4` instruments meeting the coverage floor, so the hypothesis cannot be evaluated from the matched comparison.

## Limitations

- Macro windows are narrow, so inside-window sweep counts are low.
- Same-day side-matched outside controls remove most otherwise available outside sweeps.
- Bootstrap intervals resample events and do not fully model temporal clustering.
- The experiment uses 1-minute OHLC data only; no tick, bid/ask, spread, commission, or slippage data is available.

## Alternative Explanations

- Macro context may matter only under a looser control design, but this experiment cannot establish that without abandoning the predeclared matching discipline.
- The low counts may mean the fixed macro-window and first-touch sweep definitions are too restrictive in combination.
- If the true effect is small, the current matched sample size has too little power to detect it.

## Recommended Next Steps

1. Treat EXP-016 as a sample-size failure for the matched macro-context comparison, not as evidence for or against macro-window edge.
2. Continue with EXP-017 as planned to test premium/discount filtering, while recording that macro-window context has not earned promotion as a required filter.
3. If macro context is retested later, predeclare a less sparse control design as a new experiment rather than changing EXP-016 post hoc.
