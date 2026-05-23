# Results: Experiment EXP-010

## Summary

EXP-010 refutes the hypothesis that Line Break confirmation improves the 15-minute Renko AE-relative-to-FE trade-off across instruments. The primary 15-minute log FE/AE comparison improves with a CI excluding zero only for BTCUSD. Line Break confirmation does select lower-AE subsets, especially versus non-confirmed Renko, but FE also declines and the coverage cost is large.

## Detailed Findings

### Primary 15-Minute Log FE/AE Criterion Fails

- **Observation**: Confirmed-minus-all-Renko log FE/AE improves significantly on only 1 of 4 instruments.
- **Evidence**: Mean differences are BTCUSD `+0.057` (CI `[+0.010, +0.183]`), EURUSD `-0.059`, USTEC `+0.013`, and XAUUSD `-0.020`; the latter three CIs include zero.
- **Interpretation**: The hypothesis required improvement on at least 3 of 4 instruments, so the primary criterion fails.

### Confirmation Reduces Both AE and FE

- **Observation**: Confirmed signals have lower AE60 than all Renko on USTEC and XAUUSD with CIs excluding zero, and lower FE60 than all Renko on EURUSD, USTEC, and XAUUSD.
- **Evidence**: Confirmed-minus-all-Renko FE60 is EURUSD `-0.204`, USTEC `-0.189`, XAUUSD `-0.153`, all with CIs excluding zero. AE60 is USTEC `-0.183` and XAUUSD `-0.128` with CIs excluding zero.
- **Interpretation**: Line Break confirmation mostly compresses outcome magnitude. This is not a clean quality improvement.

### Confirmed Versus Non-Confirmed Renko Shows AE Selection, Not a Stable Ratio Gain

- **Observation**: Confirmed-minus-non-confirmed AE60 is negative on all four instruments with CIs excluding zero.
- **Evidence**: AE60 differences range from `-0.299` to `-0.473`. Log FE/AE improves for BTCUSD, worsens for EURUSD, and is inconclusive for USTEC and XAUUSD.
- **Interpretation**: Line Break confirmation does select lower-adverse-excursion Renko episodes, but it does not produce a stable AE-relative-to-FE advantage.

### Coverage Cost Is Large

- **Observation**: At the primary 15-minute window, Line Break confirms `53.5-62.6%` of Renko signals.
- **Evidence**: Primary coverage is BTCUSD `0.535`, EURUSD `0.626`, USTEC `0.605`, and XAUUSD `0.618`.
- **Interpretation**: Roughly 37-47% of Renko signals are discarded. Without consistent log FE/AE improvement, that coverage loss is not justified under the approved criteria.

## Hypothesis Verdict

**REFUTED**

The hypothesis required confirmed 15-minute Renko signals to improve log FE/AE versus all Renko on at least 3 of 4 instruments with CIs excluding zero and supporting FE60/AE60 evidence. The primary ratio criterion is met only for BTCUSD.

## Limitations

- The 1-minute arm is exploratory and cannot support the hypothesis verdict.
- Same-timestamp Renko emissions are counted as emitted rows, not deduplicated timestamps.
- The experiment tests fixed Renko ATR-14 and Line Break level 3 only.

## Alternative Explanations

- Line Break may identify lower-volatility or lower-magnitude Renko episodes rather than higher-quality directional episodes.
- The confirmation layer may still be useful for risk-control framing, but not as a standalone signal-quality improvement under FE60/AE60 criteria.

## Recommended Next Steps

1. Do not carry Line Break confirmation forward as a general Renko quality gate.
2. If Line Break is revisited, scope it as a lower-AE selector with an explicit FE sacrifice criterion, not as a log FE/AE improver.
