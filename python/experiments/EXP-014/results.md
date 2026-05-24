# Results: Experiment EXP-014

## Summary

PDH/PDL and ONH/ONL liquidity levels are reproducible on the available analysis-set time bars for all four EXP-012 usable instruments. Every instrument has train and test rows above the scoped availability and count thresholds, and the deterministic rerun equality check passed.

## Detailed Findings

### All Instruments Pass Readiness

- **Observation**: `readiness_by_instrument.csv` reports `InstrumentPass=True` for EURUSD, XAUUSD, BTCUSD, and USTEC.
- **Evidence**: Train/test rows are present for all four instruments, all segment thresholds pass, and `DeterministicRerunEqual=True`.
- **Interpretation**: The fixed PDH/PDL and ONH/ONL definitions are sufficient for downstream sweep experiments on the current instruments.

### Level Availability Exceeds Thresholds

- **Observation**: All train/test all-level availability ratios exceed the scoped `0.80` threshold.
- **Evidence**:
  - BTCUSD: Train `475/478 = 0.994`, Test `163/163 = 1.000`
  - EURUSD: Train `427/430 = 0.993`, Test `183/185 = 0.989`
  - USTEC: Train `425/428 = 0.993`, Test `184/185 = 0.995`
  - XAUUSD: Train `425/428 = 0.993`, Test `182/183 = 0.995`
- **Interpretation**: Missing levels are rare and do not threaten sample adequacy for later H2 studies.

### Missing Reasons Are Classified

- **Observation**: Missing rows are explained by `NO_PRIOR_WEEKDAY`, `NO_OVERNIGHT_BARS`, or the combined first-row case.
- **Evidence**: `missing_reason_counts.csv` shows first-available-date prior-weekday gaps and small overnight gaps, with `NONE` dominating every instrument.
- **Interpretation**: The implementation avoids imputation and makes later event-denominator loss explicit.

## Hypothesis Verdict

**SUPPORTED**

The experiment meets the predefined support criterion: deterministic levels are produced for at least 80 percent of eligible NY dates on all usable instruments, with train/test all-level counts well above 50 where coverage permits.

## Limitations

- PDH/PDL and ONH/ONL reproducibility does not show that sweeps have edge; it only validates level construction.
- ONH/ONL are based on observed bars in the available time-bar dataset, not exchange-native session data.
- Bid/ask, spread, and commission fields remain unavailable from EXP-012 and must be proxied in later outcome studies.

## Recommended Next Steps

1. Use these exact level definitions and missing-level rules in EXP-015.
2. Keep missing-level rows in downstream denominators unless a later scope explicitly defines an exclusion rule.
