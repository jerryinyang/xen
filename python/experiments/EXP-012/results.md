# Results: Experiment EXP-012

## Summary

EXP-012 supports the Phase 003 data-readiness hypothesis under the documented assumptions. All four instruments clear the scoped macro-family coverage threshold, missing-bar rates are quantified, and the absence of transaction-cost fields is handled explicitly through proxy scenarios rather than hidden assumptions.

## Detailed Findings

### Macro-Window Family Coverage Meets the Readiness Threshold

- **Observation**: Every instrument and train/test segment exceeds the scoped `0.80` macro-family coverage threshold.
- **Evidence**: The weakest family ratio is `USTEC Test PM = 0.9459`; the strongest is `BTCUSD Test PM = 0.9995`. All `16` family rows in `results/macro_family_coverage_summary.csv` exceed the threshold.
- **Interpretation**: The current 1-minute time-bar data is sufficient for deterministic macro-window presence studies on the approved instrument set.

### Session Quality Differs by Instrument but Stays Well Above Failure Bounds

- **Observation**: PM coverage is weaker than AM coverage for `USTEC` and `XAUUSD`, and missing-bar rates vary by instrument.
- **Evidence**: `USTEC` PM family coverage is `0.9564` in Train and `0.9459` in Test; `XAUUSD` PM family coverage is `0.9652` in Train and `0.9638` in Test. Missing-bar rates within the observed daily span range from `0.0052` (`EURUSD Test`) to `0.0414` (`XAUUSD Train`).
- **Interpretation**: The data is not uniform across instruments, but the gaps are moderate and do not threaten the scoped readiness gate.

### Cost Inputs Are Not Present in the Stored Schema

- **Observation**: The repository time-bar files do not include bid, ask, spread, commission, or slippage fields.
- **Evidence**: `results/cost_data_availability.csv` reports `False` for all five scoped cost fields, and `results/cost_proxy_scenarios.json` defines the approved `ZERO_COST_REFERENCE`, `LIGHT_COST_PROXY`, and `HEAVY_COST_PROXY` scenarios.
- **Interpretation**: Later ICT experiments that need cost sensitivity can proceed only through these explicit proxy scenarios or with new data; this experiment does not justify treating costs as observed.

### The Fixed Loader Satisfies Governance

- **Observation**: The rerun uses the corrected holdout-exclusion path.
- **Evidence**: `audit.md` confirms that `load_analysis_timebars()` computes the row count lazily and collects only `scan.sort("CloseTime").slice(0, analysis_rows)`. A direct loader check returns `loaded_rows == analysis_rows` for EURUSD.
- **Interpretation**: The rerun is governance-valid and can be used as the Phase 003 data-readiness gate.

## Hypothesis Verdict

**SUPPORTED**

The experiment meets the predeclared support condition. All four scoped instruments can be converted to New York time under the documented UTC assumption, each clears the `>= 80%` macro-family coverage threshold in both train and test, missing-bar behavior is quantified, and the lack of transaction-cost fields is handled with explicit proxy scenarios.

## Limitations

- The UTC-to-New-York conversion assumption is documented but not independently verifiable from repository metadata alone.
- Weekend dates are excluded from macro-window denominators, but weekday market holidays remain in the denominator by design.
- Cost readiness is proxy-based rather than observed from spread or commission fields.

## Alternative Explanations

- Some of the strong coverage results may reflect the broadness of the scoped macro-window families rather than perfect intraday continuity at every minute.
- The readiness result does not imply that all later ICT component studies will have sufficient event counts or cost robustness; it only clears the prerequisite data-availability gate.

## Recommended Next Steps

1. Proceed to `EXP-013` using the timestamp, denominator, and cost-proxy conventions recorded here.
2. Reuse the same NY-time conversion assumption and close-time window-membership rule for later macro-window and sweep experiments unless a new scope explicitly reopens that question.
