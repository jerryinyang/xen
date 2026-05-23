# Results: Experiment EXP-008

## Summary

EXP-008 refutes the hypothesis that Renko confirmation improves the 15-minute time-bar signal AE-relative-to-FE trade-off across instruments. Renko-confirmed time-bar signals reduce AE60 on all four instruments, but FE60 also falls on most instruments and the primary log FE/AE criterion improves on only USTEC while worsening on EURUSD.

## Detailed Findings

### Primary Log FE/AE Criterion Fails

- **Observation**: Confirmed-minus-all-time log FE/AE improves significantly on only 1 of 4 instruments.
- **Evidence**: Mean differences are BTCUSD `-0.032` (CI includes zero), EURUSD `-0.073` (CI excludes zero negatively), USTEC `+0.042` (CI excludes zero positively), and XAUUSD `-0.015` (CI includes zero).
- **Interpretation**: The hypothesis required improvement on at least 3 of 4 instruments. The primary criterion fails.

### Renko Confirmation Reduces AE, But Also Compresses FE

- **Observation**: Confirmed time-bar signals have lower AE60 than all time-bar signals on all instruments.
- **Evidence**: Confirmed-minus-all-time AE60 differences are BTCUSD `-0.598`, EURUSD `-0.157`, USTEC `-0.296`, and XAUUSD `-0.262`; all CIs exclude zero.
- **Observation**: FE60 also declines.
- **Evidence**: Confirmed-minus-all-time FE60 is BTCUSD `-0.249`, EURUSD `-0.308`, XAUUSD `-0.216` with CIs excluding zero; USTEC is `-0.136` with CI including zero.
- **Interpretation**: Renko confirmation selects lower-magnitude time-bar episodes, not consistently higher-quality AE-relative-to-FE episodes.

### Coverage Cost Is Severe

- **Observation**: At the primary 15-minute confirmation window, Renko confirms only about one quarter of 15-minute time-bar signals.
- **Evidence**: Primary coverage is BTCUSD `0.246`, EURUSD `0.282`, USTEC `0.287`, and XAUUSD `0.272`.
- **Interpretation**: Roughly 71-75% of time-bar opportunities are discarded. Without broad log FE/AE improvement, the coverage loss is not justified.

### Raw Renko Comparator Does Not Change the Verdict

- **Observation**: Confirmed time-bar signals are not consistently better than raw Renko signals.
- **Evidence**: Confirmed-minus-raw-Renko log FE/AE CIs include zero on all four instruments.
- **Interpretation**: Renko confirmation does not create a superior hybrid signal relative to the Renko event stream itself.

## Hypothesis Verdict

**REFUTED**

The hypothesis required 15-minute Renko-confirmed time-bar signals to improve log FE/AE on at least 3 of 4 instruments, with supporting FE60/AE60 evidence. It achieved only one positive significant log-ratio result, while FE60 declined on most instruments.

## Limitations

- The 1-minute arm is exploratory only and does not support the verdict.
- Same-timestamp Renko emissions are preserved as emitted rows, not deduplicated timestamps.
- Only Renko ATR-14 and fixed 5/15/30-minute windows were tested; no tolerance optimization was allowed.

## Alternative Explanations

- Renko confirmation may act as a volatility/magnitude compression gate rather than a quality filter.
- The AE reduction may still be useful for a future risk-control experiment, but that would need a scope that explicitly accepts FE sacrifice.

## Recommended Next Steps

1. Do not carry Renko confirmation forward as a general time-bar quality gate.
2. If revisited, scope the question as AE reduction with an explicit permitted FE cost and coverage budget.
