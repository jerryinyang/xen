# Experiments Index (Comprehensive)

## Current Checkpoint Status

| Checkpoint | Status | Focus | Documents |
| --- | --- | --- | --- |
| 2026-06-01-001-thesis-qualification-calibration | ACTIVE (design complete) | Build the 5-check gate-stack referee + calibration harness; measure per-domain (5m/1h/4h) FPR/TPR/economic-MDE for it and a minimal baseline (EXP-001→004). | [design.md](checkpoints/2026-06-01-001-thesis-qualification-calibration/design.md) |


## Checkpoint Retrospectives

| Checkpoint | Status | Key Synthesis | Document |
| --- | --- | --- | --- |



## VAL-001 - Data Architecture Temporal Integrity Validation

**Status**: COMPLETED (rev. 3)
**Date**: 2026-06-01
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD
**Data Views / Feature Categories**: 1-minute time bars; 15-minute and 60-minute OHLC resamples; Line Break level 3; Renko ATR period 14; Heiken Ashi

### Hypothesis Tests

1. **Hypothesis**: The available Xen data architecture preserves temporal alignment across scoped time-bar, timeframe, and chart-type views — with no future-timestamp or cross-view misalignment in any emitted row, and no structural look-ahead in prefix-stability probes positioned at the head, middle, and tail of the analysis slice — when every derived view is generated only from the first 70% of each chronologically ordered base dataset.

### Scope

- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD.
- **Data Views / Feature Categories**: Base 1-minute time bars; 15-minute and 60-minute OHLC resamples; Line Break, Renko, and Heiken Ashi generated from each scoped source timeframe.
- **Features**: Required time-bar schema, OHLC integrity, `CloseTime`, `SourceCloseTime`, `SourceCount`, Heiken Ashi real OHLC preservation, prefix stability, deterministic regeneration, and negative-control detection.
- **Parameter ranges**: Line Break `level=3`; Renko `atr_period=14`; timeframe periods `1`, `15`, and `60` minutes.
- **Exclusions**: Final 30% global holdout, tick data, bid/ask spread, trading costs, strategy backtests, return forecasting, parameter tuning, randomized tests, and persisted generated chart-type datasets.
- **Constraints**: All validation uses the first 70% chronological analysis slice only. Time bars align by `CloseTime`; Line Break and Renko align by `SourceCloseTime`; Heiken Ashi aligns by `CloseTime`. No P&L or return metrics are in scope.

### Results / Observations

- `validation_checks.csv`: 416 PASS, 0 FAIL, 0 INCONCLUSIVE (rev. 3).
- Real-instrument checks: BTCUSD 98/98 PASS; EURUSD 98/98 PASS; USTEC 98/98 PASS; XAUUSD 98/98 PASS.
- Synthetic control checks: 24/24 PASS, including 23/23 detected negative controls (one per data-integrity and alignment check) plus 1 golden fixture.
- Prefix-stability look-ahead probes: 60 checks (head/middle/tail for 1-minute views, `full` for 15m/60m), 0 diverged cuts; determinism: 36/36 PASS.
- Analysis rows after first-70% slicing (unchanged from rev. 2): BTCUSD 1,088,960; EURUSD 872,242; USTEC 830,541; XAUUSD 830,671.
- Resample oracle comparisons: 0 rows only in production, 0 rows only in oracle, and 0 OHLC mismatches for every 15-minute and 60-minute instrument comparison.
- Heiken Ashi density: 1.0 for every instrument/timeframe combination.
- Line Break event-density range: 0.195149 to 0.275556 event rows per source row.
- Renko event-density range: 0.222171 to 0.298266 event rows per source row.
- Renko duplicate-source denominator context: 107,824 duplicate `SourceCloseTime` groups and 128,556 extra same-source rows across all scoped outputs.

### Hypothesis-Specific Conclusion

**SUPPORTED**

The current data layer passed the temporal-integrity readiness gate. The conclusion is supported because every scoped positive check passed and every injected negative control was detected, satisfying the predefined success criteria.

### Hypothesis-Agnostic Observations

- Renko same-source duplicate rows are common enough to require explicit denominator reporting in future chart-type experiments.
- Future downstream strategy or signal experiments can rely on timestamp alignment as validated here, but they must still evaluate returns and P&L on real time-matched prices.
- Changes to data-loading conventions, chart generators, or `aggregate_ohlc()` should trigger a new VAL rerun before dependent research uses the changed layer.
- rev. 3 hardened the suite's detection power: every base-integrity, resample, sparse-chart, Heiken Ashi, schema, look-ahead, and determinism check now has a matching negative control, and look-ahead is probed at the head/middle/tail of each slice. Byte-identical reproduction of rev. 2 generator outputs confirms deterministic generation; future VAL reruns should keep this control-per-check standard.
- The Line Break and Renko generators were manually verified against `architecture.md`; note Xen Renko intentionally differs from classic TradingView Renko (SMA-of-TR ATR, 1-brick symmetric reversal, first-close anchor).
