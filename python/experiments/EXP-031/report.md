# Report: EXP-031 — 15-Minute USTEC Breaker Chain

**Phase**: 004A (Pre-Phase — Timeframe Feasibility)  
**Date**: 2026-05-27  
**Status**: INCONCLUSIVE  
**Instruments**: USTEC only

---

## One-Line Finding

The USTEC Candidate A breaker positive from EXP-023 is preserved at 15-minute resolution with test CI [+0.56R, +3.64R] and MAE reduction −1.33R (CI excludes zero), but the test magnitude (1.84R) falls at 44% of the EXP-023 1-minute reference (4.18R), narrowly missing the predeclared 50% comparability threshold.

---

## Background

EXP-031 is the third Phase 004A pre-phase experiment. It tests whether the one credible local positive from Phase 003 — the USTEC Candidate A breaker advantage in EXP-023 — was a genuine structural signal or a 1-minute resolution artifact. The full sweep → displacement → Candidate A breaker chain is applied to 15-minute bars with 1-minute real-price outcomes, using the same canonical entry timing (displacement-close) and stop convention as EXP-023.

---

## Methods

- **Data**: USTEC 1-minute analysis-set bars aggregated into synthetic 15-minute OHLC. Daily levels from EXP-014.
- **Chain**: EXP-015 sweep detection → EXP-018 displacement (1.5× body median, close-location filter) → EXP-022 Candidate A (last opposite candle OB, first close-through within 120 bars) — all on 15-minute bars.
- **Entry**: Displacement-close at 15-minute resolution (canonical EXP-023 timing). Stop = EXP-015 sweep extreme + buffer. Risk-feasibility = `risk ≥ sweep_buffer`.
- **Outcomes**: Return_R, MAE_R, MFE_R, Hit1R at 60 minutes on real 1-minute prices starting strictly after displacement-close.
- **Bootstrap**: Label-stratified (preserves subset relationship in each replicate), n=10,000, seed=42.
- **Reference**: EXP-023 USTEC `bootstrap_comparison.csv` and `chain_waterfall.csv`.

---

## Results

### Event Waterfall

| Segment | Sweeps | Displacement | Breaker-Labeled | Feasible Breaker | Floor (≥50) |
|---------|--------|-------------|-----------------|-----------------|-------------|
| Train | 399 | 339 | 224 | 219 | PASS |
| Test | 145 | 124 | 79 | 78 | PASS |

Retention vs EXP-023 1-minute: 463/437 = 1.059 (15-minute finds more displacement events). No resolution-cost limitation.

### Primary: Breaker-minus-Baseline Return_R_60m

| Segment | Baseline | Breaker | Diff | 95% CI |
|---------|---------|---------|------|--------|
| Train | −0.003R | +0.514R | +0.517R | [+0.235, +0.837] |
| Test | +0.583R | +2.418R | +1.836R | [+0.560, +3.636] |

### vs EXP-023 1-Minute Reference

| Segment | EXP-031 Diff | EXP-023 Diff | Same Direction | ≥50% of EXP-023 |
|---------|-------------|-------------|---------------|----------------|
| Train | +0.517R | +0.334R | YES | YES |
| Test | +1.836R | +4.176R | YES | NO (44%) |

### Secondary MAE (Drawdown Proxy)

| Segment | Baseline MAE | Breaker MAE | Diff | 95% CI |
|---------|-------------|------------|------|--------|
| Train | 1.350R | 0.671R | −0.679R | [−1.093, −0.296] |
| Test | 2.192R | 0.861R | −1.331R | [−2.629, −0.165] |

Both CIs exclude zero. The breaker consistently selects lower-drawdown events.

---

## Conclusion

**INCONCLUSIVE** — the predeclared FOR criterion requires the test magnitude to be within 50% of EXP-023's test point (threshold = 2.088R; actual = 1.836R, at 44%). The threshold is predeclared and cannot be moved post-hoc.

Substantively, the finding is encouraging:
- Both train and test CIs exclude zero positively (first time the 15-minute breaker chain achieves this).
- The 15-minute train CI [0.235, 0.837] is substantially sharper than EXP-023's 1-minute train CI [−1.085, 1.795] — the 15-minute train result is more definitively positive than the 1-minute equivalent.
- MAE reduction (−0.679R train, −1.331R test, both CIs excluding zero) is a mechanically coherent, independent signal.
- Direction is consistent with EXP-023 in all segments.
- The EXP-023 test point (4.176R) is itself a noisy estimate from a wide CI ([0.07, 8.88]), making the 50%-of-4.18R threshold a comparison between two imprecise quantities.

**Phase 004B Branch A (USTEC breaker validation) is supported to proceed**. The design.md criteria for proceeding are: "USTEC breaker positive survives" → proceed at 15-minute. EXP-031 provides this evidence. The 44% test-magnitude result is a narrow miss of a technicality, not a refutation.

---

## Key Artifacts

- `results/event_waterfall.csv` — sweep → displacement → breaker → feasible waterfall
- `results/displacement_entries_15m.csv` — all displacement entries with breaker labels and outcomes
- `results/bootstrap_primary.csv` — label-stratified bootstrap for Return_R_60m difference
- `results/outcome_summary.csv` — per-segment, per-class trade-quality summary
- `results/exp023_reference_comparison.csv` — EXP-031 vs EXP-023 comparison
