# Results: Experiment EXP-048 — Phase 014-A Substrate & Detector Readiness (ATR-ZigZag + HA Harami, 102 Cells)

## Summary

All 102 cells (17 instruments × 6 domains) were processed on the TRAIN stratum. The verdict is **READINESS_DELIVERED**: the per-cell readiness map, move/event-rate table, and `/BARCFG` coverage table were produced with zero invariant violations and zero determinism failures. Status distribution: 86 READY, 13 READY_FLAGGED, 3 COVERAGE_EXCLUDED, 0 CONSTRUCTED_EMPTY, 0 NOT_READY of any type. Both primitives — the ATR-ZigZag trend substrate and the HA harami detector — are mechanically valid for all 99 non-excluded cells, clearing the substrate gate for EXP-049.

## Detailed Findings

### 1. Status Distribution

| Status | Count | Criterion |
|--------|-------|-----------|
| READY | 86 | construction PASS ∧ all invariants clean ∧ determinism PASS, dropped < 0.10 or 5m (ungated) |
| READY_FLAGGED | 13 | same as READY but dropped ∈ [0.10, 0.25] on a gated domain |
| COVERAGE_EXCLUDED | 3 | dropped > 0.25 (construction integrity FAIL for that cell only) |
| CONSTRUCTED_EMPTY | 0 | TRAIN bars < ATR warmup (14) |
| NOT_READY (any type) | 0 | invariant violation or determinism failure |

**Interpretation:** No systematic primitive defect. The SUBSTRATE_REFUTED criteria (non-determinism on any cell; same invariant on ≥3 instruments) are both unmet. The experiment's mechanical viability conditions are satisfied across the full grid.

### 2. COVERAGE_EXCLUDED Cells

Three cells exceeded the dropped-fraction gate of 0.25:

| Cell | Dropped Fraction | Likely Cause |
|------|-----------------|--------------|
| US500-4h | 0.286 | US-index market-hour gaps amplified by longest aggregation window |
| JP225-2h | 0.257 | JP225 JST market-hour gap × moderate aggregation window |
| JP225-4h | 0.297 | JP225 JST gap × longest aggregation window |

These follow the pattern established in EXP-043 (JP225-2h excluded there as well). Exclusion is a per-cell coverage outcome, recorded for EXP-049 pass-through, not a primitive defect.

### 3. READY_FLAGGED Cells (13 cells, dropped ∈ [0.10, 0.25])

All flagged cells are non-5m gated domains:

- **US500**: {15m, 30m, 1h, 2h} — US-index market-hour gaps
- **US2000**: {2h, 4h} — same market-hour gap pattern
- **DE30**: {2h, 4h} — European market-hour gaps × short DE30 history
- **JP225**: {15m, 30m, 1h} — JST market-hour gaps (2h/4h already excluded)
- **XAUUSD**: {4h} — moderate coverage gap on longest domain
- **USTEC**: {4h} — US-tech market-hour gap on longest domain

READY_FLAGGED cells are READY-eligible and pass through to EXP-049 with disclosure. All dropped fractions are well below the 0.25 exclusion gate.

### 4. Move Rates (ATR-ZigZag confirmed moves per 1,000 domain bars)

Stable across all instruments and domains: range **[170.2, 207.0]** per 1k bars.

- Fast domains (5m): ~200–207/1k bars
- Slow domains (4h): ~170–196/1k bars
- Decline of ~5% from fast to slow domains, consistent with `ATR_MULT=1.0` sensitivity on Wilder ATR-14

The narrow range confirms the ZigZag substrate produces consistent move density regardless of instrument or timeframe — expected behaviour for a fixed-parameter pivot-threshold rule on continuous-time OHLC data.

**All 99 non-excluded cells have ≥30 confirmed moves** (well above the reporting floor of 30).

### 5. Harami Event Rates (per 1,000 HA candles)

Stable across all cells: range **[229.6, 261.4]** per 1k candles.

- Minor instrument-level variation (±6% of the mean); no domain trend
- The stability reflects the construction-derived reduction — `HAClose₀` is constrained by the prior-body centre, producing a near-constant harami incidence rate independent of market structure

**All 99 non-excluded cells have ≥30 harami events** (minimum observed: 401 in DE30-4h), well above the 30-event reporting floor.

### 6. `/BARCFG` Coverage

Near-symmetric dominance of same-direction configurations:

| Configuration | Pooled Fraction (range across domains) | Description |
|--------------|----------------------------------------|-------------|
| UP_UP | ~33–35% | HA₁ green, HA₀ green |
| DN_DN | ~31–34% | HA₁ red, HA₀ red |
| UP_DN | ~16–18% | HA₁ green, HA₀ red |
| DN_UP | ~15–17% | HA₁ red, HA₀ green |

This pattern is a direct consequence of the family's construction-derived reduction: `HAClose₀` is constrained relative to the prior-body centre, biasing the `HA_0` direction toward the `HA_1` direction. The asymmetry (UP_UP slightly > DN_DN) likely reflects the slightly bullish drift of the TRAIN period across most instruments. Coverage is measured, never assumed uniform — and it is not uniform.

### 7. DE30 Disclosure

DE30 has a truncated broker history ending 2026-01-16 (~5 months shorter than other instruments). All DE30 bar counts, move counts, and event counts derive from its own realized timeline:

| Domain | DE30 Domain Bars | Comparable Full-History Instrument (e.g. EURUSD) |
|--------|-----------------|---------------------------------------------------|
| 5m | 94,284 | ~120,000–124,000 |
| 4h | 1,738 | ~2,400–2,500 |

DE30 rates (per-1k) are comparable to other instruments (move rate ~190–202/1k, harami rate ~230–246/1k), but absolute counts are systematically lower. No cell is excluded or penalized for the shorter span.

## Hypothesis Verdict

**READINESS_DELIVERED**

The experiment's mechanical success criteria are fully met:

| Criterion | Status | Evidence |
|-----------|--------|----------|
| 102-cell READY / NOT_READY / COVERAGE_EXCLUDED / CONSTRUCTED_EMPTY map | ✓ | `readiness_map.csv` produced |
| Per-cell move/event-rate table | ✓ | `move_event_rates.csv` produced |
| `/BARCFG` coverage table | ✓ | `barcfg_coverage.csv` produced |
| Zero invariant violations (both primitives) | ✓ | All 12 invariant keys = 0 on every cell |
| Zero determinism failures | ✓ | All 102 cells PASS determinism replay |
| Systematic invariant on ≥3 instruments | ✓ | No invariant violated on any cell → rule not triggered (verdict: READINESS_DELIVERED) |

No contrary evidence: both ATR-ZigZag and HA harami are deterministic, causal, and invariant-clean across all 99 non-excluded cells. No market-edge claim is tested or implied — this is a pure mechanical readiness verdict.

The 13 READY_FLAGGED and 3 COVERAGE_EXCLUDED cells are coverage outcomes (dropped fraction disclosures), not primitive defects.

## Limitations

1. **Latent `/BARCFG` null-handling bug (audit Warning 1):** The `barcfg_counts` function returns zero-filled config dicts for zero-harami non-empty cells instead of nulls as scoped. Not exercised in this run (all cells have ≥401 harami events), but would produce incorrect CSV output for a hypothetical sparse cell with ≥14 domain bars and 0 harami events. Fix is trivial (guard at line 312 of `run_experiment.py`).

2. **5m strict coverage convention:** 5m domain uses `min_coverage=None` (strict), following the established project convention. Dropped fraction is not computed for 5m; the 0.10–0.25 flagged disclosure gate does not apply. This means 5m cells with genuine coverage gaps (e.g. US500-5m at 0.123 dropped, JP225-5m at 0.163 dropped) are recorded as READY without flagging. This is consistent with EXP-043 and VAL-004 precedent but means the coverage disclosure is less transparent for the 5m domain.

3. **Determinism replay scope:** Determinism is verified via re-aggregation from the same in-memory `train_1m` slice (audit Info 2), not via a full re-read from Parquet. The I/O path (Parquet → DataFrame) is not re-tested. This is consistent with the scope (§4) but means I/O-layer non-determinism is not caught.

4. **Non-binding `tqdm` granularity (audit Info 1):** Progress bar tracks 17 instruments rather than 102 cells. No functional impact.

5. **DE30 span comparability:** All DE30 counts and rates derive from ~5 months shorter history. Rates per 1k are comparable; absolute counts are not. Cross-instrument pooling or ranking should be interpreted with this caveat.

## Alternative Explanations

This is a descriptive mechanical experiment — no statistical inference, no effect size, no edge estimate. The results are exact enumerations of deterministic computations on a fixed TRAIN slice. There is no alternative explanation for the status distribution, invariant counts, or determinism results (they are either pass or fail by construction). The `/BARCFG` distribution (UP_UP / DN_DN dominance) is the expected consequence of the family's construction-derived reduction — not a market-structure signal — and carries no alternative interpretation.

## Recommended Next Steps

1. **EXP-049 (Phase 014-A Capture Read):** Proceed on all 99 READY and READY_FLAGGED cells (the 3 COVERAGE_EXCLUDED cells are excluded with record). EXP-049 will introduce the 3-barrier capture framework on the combined harami-at-trend-exhaustion event, computing per-cell capture rates and excursion statistics. The move/event-rate and `/BARCFG` tables from EXP-048 serve as descriptive context for EXP-049's capture power assessment.

2. **Fix latent `/BARCFG` null bug:** Add the zero-harami guard in `process_cell` (audit recommendation) before EXP-049 scripts re-use the `barcfg_counts` utility.

3. **EXP-050+ (Phase 014-B Combined Event):** After EXP-049, define the combined harami-at-trend-exhaustion event and characterise its per-cell yield, `/BARCFG` composition at the combined event level, and position-in-move properties.
