# Results: EXP-029 — 15-Minute FVG IFVG Selectivity Check

## Verdict

**AGAINST**

The 120-bar IFVG inversion rate at 15-minute resolution replicates the Phase 003 1-minute baseline of 84–85% on all 4 instruments. The unmodified EXP-020 FVG/IFVG rule does not become materially selective when applied to 15-minute bars under the primary 120-bar lifecycle window.

---

## Primary Result: IFVG Inversion Rate

The primary metric — the 120-bar lifecycle IFVG inversion rate on 15-minute bars — is compared against the Phase 003 1-minute baseline of 84–85% and the predeclared materiality threshold of 50%.

| Instrument | Train IFVGRate | Test IFVGRate | Primary (all) | Bootstrap 95% CI | Near 1m Baseline? |
|------------|---------------|---------------|---------------|-----------------|-------------------|
| EURUSD | 0.853 | 0.857 | 0.854 | [0.846, 0.865] | YES (within 2pp) |
| XAUUSD | 0.842 | 0.821 | 0.836 | [0.825, 0.846] | YES (within 2pp) |
| BTCUSD | 0.826 | 0.845 | 0.832 | [0.823, 0.842] | YES (within 2pp) |
| USTEC | 0.848 | 0.846 | 0.848 | [0.837, 0.859] | YES (within 1pp) |

All four instruments show IFVG rates within 2pp of the 1-minute baseline, and all bootstrap CIs exclude the 50% materiality threshold by a large margin.

**None of the four instruments meet the FOR criterion (rate < 50% on both segments).**
**All four instruments meet the AGAINST criterion (rate near baseline on ≥ 3 instruments).**

---

## Event Counts

FVG and IFVG counts far exceed the predeclared floors (≥100 FVGs, ≥50 IFVGs per train/test segment).

| Instrument | Segment | FVG_N | IFVG_N | FVG Floor | IFVG Floor |
|------------|---------|-------|--------|-----------|------------|
| EURUSD | Train | 8,583 | 7,321 | PASS | PASS |
| EURUSD | Test | 3,683 | 3,156 | PASS | PASS |
| XAUUSD | Train | 7,702 | 6,486 | PASS | PASS |
| XAUUSD | Test | 3,391 | 2,783 | PASS | PASS |
| BTCUSD | Train | 9,283 | 7,671 | PASS | PASS |
| BTCUSD | Test | 4,129 | 3,491 | PASS | PASS |
| USTEC | Train | 8,266 | 7,011 | PASS | PASS |
| USTEC | Test | 3,483 | 2,948 | PASS | PASS |

The high IFVG counts (2,783–7,671 per segment) reflect the rule's permissiveness: with a 120-bar lifecycle window (30 hours elapsed), nearly every FVG eventually receives a close-through inversion event.

---

## Lifecycle Sensitivity: Separating Timeframe from Lifecycle Duration

The secondary 8-bar lifecycle window (≈ 2 hours elapsed) dramatically separates the effect of lifecycle duration from any timeframe benefit.

| Instrument | 120-bar IFVGRate | 8-bar IFVGRate | Difference (pp) |
|------------|-----------------|----------------|-----------------|
| EURUSD | 0.854 | 0.479 | −37.6 |
| XAUUSD | 0.836 | 0.457 | −37.8 |
| BTCUSD | 0.832 | 0.454 | −37.8 |
| USTEC | 0.848 | 0.461 | −38.6 |

The ~38pp gap is consistent across all four instruments. The 8-bar window (≈120 minutes elapsed, matching the original 1-minute 120-bar window) reduces the inversion rate to 45–48%. This finding isolates the mechanism:

- **The high inversion rate is driven by the lifecycle window length, not the FVG rule's permissiveness at 15-minute resolution.**
- Shortening the observation window from 120 15-minute bars (30 hours) to 8 15-minute bars (2 hours) brings the rate to 45–48% — meaning the timeframe change itself did reduce the raw inversion exposure, but only when the lifecycle window is also shortened proportionally.

---

## Reproducibility

All four instruments pass both invariance checks with matching SHA-256 digests.

| Instrument | Fresh Reload Matches | Shuffled Resort Matches | Reproducible |
|------------|---------------------|------------------------|--------------|
| EURUSD | TRUE | TRUE | TRUE |
| XAUUSD | TRUE | TRUE | TRUE |
| BTCUSD | TRUE | TRUE | TRUE |
| USTEC | TRUE | TRUE | TRUE |

The detection pipeline is fully deterministic. The AGAINST verdict is not an artifact of non-determinism.

---

## Displacement Overlap Diagnostic

The overlap between 15-minute FVG formation times and EXP-018 1-minute displacement event times was computed but shows 0.0 for all instruments (a likely type-mismatch artifact flagged in the audit; the diagnostic does not affect the verdict). The overlap diagnostic is treated as uninformative for this experiment.

---

## Coverage Diagnostics

| Instrument | 1m Bars (Analysis Set) | 15m Bars | Dropped Bars |
|------------|----------------------|----------|--------------|
| EURUSD | 872,242 | 55,230 | 43,792 (5.0%) |
| XAUUSD | 830,671 | 54,143 | 18,526 (2.2%) |
| BTCUSD | 1,088,960 | 71,202 | 20,930 (1.9%) |
| USTEC | 830,541 | 54,787 | 8,736 (1.1%) |

EURUSD shows higher dropout due to forex session gaps. FVG counts are unaffected — coverage is more than adequate.

---

## Interpretation Against Success Criteria

| Criterion | Outcome |
|-----------|---------|
| Primary IFVG rate < 50% on ≥ 2 instruments (FOR) | NOT MET — rates are 83–86% |
| Rate near 84–85% baseline (within 5pp) on ≥ 3 instruments (AGAINST) | MET — all 4 instruments within 2pp |
| Detection deterministic on all instruments | MET |
| FVG/IFVG count floors met on selective instruments | N/A — no instruments are selective |
| Lifecycle sensitivity agrees with primary direction | DISAGREES by 37–39pp — lifecycle duration is the dominant driver |

---

## Conclusions for the Phase 004A Reflection

1. **The unmodified EXP-020 120-bar lifecycle IFVG rule is not selective at 15-minute resolution.** The inversion rate (83–86%) replicates the 1-minute baseline with less than 2pp difference on all instruments.

2. **The lifecycle window length is the primary driver of the high inversion rate.** The 8-bar window (≈2 hours elapsed) brings the rate to 45–48%, confirming that 30-hour observation windows make inversion nearly certain for most FVGs regardless of timeframe.

3. **Timeframe change alone does not solve IFVG selectivity.** Branch B must pursue a selectivity redesign (shorter lifecycle, stricter gap definition, or structural qualification) rather than relying on timeframe migration to solve the rule's permissiveness.

4. **If Branch B proceeds at 15-minute, it must either redesign the lifecycle window or the gap qualification rule**, since the 8-bar sensitivity (≈2-hour window) does achieve ~47% inversion rates — suggesting that a pre-declared shorter lifecycle could be a starting point for EXP-035, provided it preserves adequate event counts.

5. The question of whether IFVG selectivity is a **rule-design problem** (per the design.md Branch B framing) is confirmed: the rule is structurally too permissive under a long observation window, and the fix is rule-level, not resolution-level.
