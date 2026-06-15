# Infrastructure & Validation — Family Index

> Detailed cards for cross-cutting data/infrastructure validation (VAL-series) and integration tasks (INFR-series).
> These support multiple candidate families and gate phase work; they are not a signal family.
> Live programme status and phase retrospectives: [master index](../../INDEX.md).
> Compact one-row registry of all experiments: [`python/experiments/INDEX.md`](../../../../python/experiments/INDEX.md).

**Note:** VAL-002 (INFR-001 cTrader strategy-branch) and VAL-003 (INFR-002 new-universe admission) are recorded as compact rows in the [global registry](../../../../python/experiments/INDEX.md) and in the master index Infrastructure Tasks block; full detail cards below cover VAL-001 and VAL-004.

## Validation Experiments

- **VAL-001** — Data Architecture Temporal Integrity Validation
- **VAL-004** — 15m/30m Domain Temporal-Integrity Validation (Phase 014 Gate)

---

## VAL-001 - Data Architecture Temporal Integrity Validation

**Status**: SUPPORTED (rev. 3)
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

---

## VAL-004 — 15m/30m Domain Temporal-Integrity Validation (Phase 014 Gate)

**Status**: SUPPORTED (PASS)
**Date**: 2026-06-14
**Instruments**: AUDJPY, AUDUSD, BTCUSD, DE30, EURJPY, EURUSD, GBPJPY, GBPUSD, JP225, NZDUSD, US2000, US500, USDCAD, USDCHF, USDJPY, USTEC, XAUUSD (all 17 VAL-003-admitted)
**Data Views / Feature Categories**: 1-minute time bars → aggregated OHLC (15m and 30m, each in strict and tolerant `min_coverage=0.90` modes); Heiken Ashi, Line Break (level 3), Renko (ATR 14) chart views over the new domains.

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments.
- **Data Views / Feature Categories**: 15m and 30m OHLC domains in strict and tolerant (`min_coverage=0.90`) modes; chart-type alignment checks (Line Break level 3, Renko ATR 14, Heiken Ashi) over the new domains.
- **Features**: VAL-001 rev. 3 check battery — future-timestamp, monotonic `CloseTime`, `SourceBars`/coverage semantics, OHLC bounds, cross-view timestamp alignment, head/middle/tail prefix-stability probes, determinism replay, negative controls; per-cell dropped-window-fraction for tolerant mode.
- **Parameters**: `SOURCE_TIMEFRAMES = [15, 30]` (15 = determinism anchor); `min_coverage ∈ {None (strict), 0.90}`.
- **Exclusions**: final 30% global holdout sealed at first touch; no Phase 014 signal/harami logic; no strategy or edge claim; no parameter tuning.
- **Constraints**: byte-identical check logic to VAL-001 rev. 3 in strict mode; `SourceBars` valid-range parameterized for tolerant mode; deterministic generation; `tqdm` over the 17-instrument outer loop.

### Results / Observations

- **Suite PASS**: 2,279 validation checks, 0 FAIL, 0 INCONCLUSIVE; 28/28 negative controls detected; 2/2 golden fixtures PASS; 2/2 must-not-overfire assertions PASS; floor guard PASS.
- **Universe reconciliation**: 17/17 expected instruments present, 0 missing/duplicates; 1 unexpected group (ANALYSIS70, 4 pre-sliced files) disclosed and excluded.
- **15m determism anchor**: all 17 instruments reconcile to the pinned VAL-001/VAL-003 record (every prior key present and PASS in VAL-004).
- **68/68 cells ADMITTED** (all dropped fractions ≤ 0.133, well below the 0.25 gate).
- **Dropped fractions**: 0.003–0.133 (tolerant); 0.012–0.277 (strict). Highest tolerant: JP225-15m (0.133); lowest: USTEC-30m (0.003). Index-instrument dropped fractions are higher (0.08–0.13) reflecting market-hour gaps, but all below the gate.
- **Chart densities**: HA 1.0 everywhere; LB 0.20–0.30; Renko 0.22–0.28 — consistent with prior VAL-001 patterns.
- **Plots**: `plots/dropped_fraction_map.png`, `plots/check_pass_heatmap.png`.

### Hypothesis-Specific Conclusion

**SUPPORTED (PASS)**

The 15m/30m domains in both strict and tolerant modes preserve temporal alignment, OHLC integrity, cross-view timestamp alignment, and deterministic regeneration across all 17 instruments. The §5 VAL gate in the Phase 014 checkpoint design is PASSED. All 17 instruments × {15m, 30m} cells are individually admissible to EXP-048.

### Hypothesis-Agnostic Observations

- Tolerant-mode dropped fractions are consistently lower than strict fractions (tolerant retains legitimate partial windows), confirming the coverage trade-off is measured, not assumed.
- Index instruments (DE30, JP225, US500) have higher dropped fractions reflecting session gaps, but all clear the 0.25 admission gate — consistent with the Phase 011 2h dropped-fraction convention (JP225-2h was excluded at >0.25; no 15m/30m cell reaches that threshold).
