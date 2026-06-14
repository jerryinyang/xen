# Results: Experiment VAL-004

## Verdict

**SUPPORTED (PASS)** — full Suite PASS per the pre-registered interpretation criteria.

## Summary

| Metric | Value |
|--------|-------|
| Validation checks | 2,279 total, 0 FAIL, 0 INCONCLUSIVE |
| Negative controls | 28/28 detected (100%) |
| Must-not-overfire assertions | 2/2 PASS |
| Golden fixtures (15m, 30m strict) | 2/2 PASS |
| Tolerant floor guard | 1/1 PASS |
| Instruments validated | 17/17 (all expected present) |
| 15m strict anchor reconciliation | 17/17 PASS (all prior keys present and PASS in VAL-004) |
| Intelligent cells (PASS) | 68/68 (all ADMITTED) |
| Coverage-excluded cells | 0 |
| Deferred cells (INCONCLUSIVE) | 0 |
| Integrity failures | 0 |

## Cell-Level Results

All 68 cells (17 instruments × 2 domains {15m, 30m} × 2 modes {strict, tolerant}) pass all integrity checks and are **ADMITTED** (dropped fraction under tolerant mode ≤ 0.25 gate in every cell):

| Dropped fraction range | Cells |
|---|---|
| 0.000 – 0.010 | 10 |
| 0.010 – 0.025 | 16 |
| 0.025 – 0.050 | 20 |
| 0.050 – 0.100 | 14 |
| 0.100 – 0.133 | 8 |

No cell exceeds 0.25; the highest is JP225-15m at 0.133.

## 15m Strict Determinism Anchor

Every instrument's 15m strict output reconciles to the pinned VAL-001/VAL-003 record: all prior (instrument, view, check) keys are present and PASS in VAL-004. Fingerprints differ by design (new data collection window), but within-run determinism is confirmed for every cell.

## Negative Controls

All 28 injected faults were detected, including the two tolerant SourceBars-range controls (below-floor 13/17 and above-period 99 both flagged) and both must-not-overfire assertions (legitimate in-range partials at floor 14/27 not flagged).

## Interpretation

Per the pre-registered interpretation guide:

- **Suite SUPPORTED**: all negative controls detected, both golden fixtures PASS, every per-cell integrity check PASS, the 15m determinism anchor reconciles to VAL-001/VAL-003 on all 17 instruments, and every 15m/30m cell is ADMITTED with no integrity failure.
- **No cell-level FAIL**: no resample-oracle disagreement, no chart prefix-stability violation, no determinism failure, no timestamp/OHLC contract violation.
- **No run-level FAIL**: no missed negative control, no must-not-overfire firing.
- **No anchor FAIL**: all 17 instruments reconcile with the prior record.
- **No COVERAGE_EXCLUDED**: all dropped fractions are well below 0.25.
- **No INCONCLUSIVE cells**: every cell has sufficient rows.

## Gate Consequence

The §5 VAL gate in the Phase 014 checkpoint design is **PASSED**. All 17 instruments × {15m, 30m} × {strict, 0.90} cells are individually admissible to EXP-048 (substrate/detector readiness in the HA-harami family).
