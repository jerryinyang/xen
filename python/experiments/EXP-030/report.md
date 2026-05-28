# Report: EXP-030 — 15-Minute Sweep Reversal Behavior

**Phase**: 004A (Pre-Phase — Timeframe Feasibility)  
**Date**: 2026-05-27  
**Status**: INCONCLUSIVE  
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC

---

## One-Line Finding

15-minute PDH/PDL/ONH/ONL sweeps show no positive failed-breakout edge on any instrument; the EXP-015 EURUSD partial positive reverses to −0.145 (CI excludes zero negatively), and BTCUSD sweeps consistently underperform breaches on both train and test.

---

## Background

EXP-030 is the second Phase 004A pre-phase experiment. It tests whether the PDH/PDL/ONH/ONL sweep-reversal behavior identified at 1-minute in EXP-015 replicates, strengthens, or changes at 15-minute resolution. EXP-015 found a partial EURUSD positive (+0.134, CI barely excluded zero from above) and refuted the broad cross-instrument hypothesis. EXP-030 uses the same definitional framework adapted to 15-minute bar detection with 1-minute real-price outcome evaluation.

---

## Methods

- **Data**: 1-minute analysis-set bars (first 70%) aggregated into synthetic 15-minute OHLC. PDH/PDL/ONH/ONL levels from EXP-014 (daily levels are resolution-independent).
- **Detection**: First-touch PDH/PDL/ONH/ONL sweep (wick beyond level + buffer, close back inside) and breach (close beyond level) per NYDate. Buffer = `max(price_precision_step, 0.05 × ATR_14_15m)`.
- **Outcomes**: 1R-before-stop probability, MAE_R, MFE_R, Return_R at 30, 60, 120 minutes of post-confirmation executable time on real 1-minute prices.
- **Bootstrap**: Stratified (by side/level-type), n=10,000, seed=42.
- **Reference**: EXP-015 1-minute primary effects table loaded and compared.

---

## Results

### Event Counts

| Instrument | Segment | Sweeps | Breaches | Floor (≥100) |
|------------|---------|--------|----------|-------------|
| EURUSD | Train | 327 | 456 | PASS |
| EURUSD | Test | 126 | 195 | PASS |
| XAUUSD | Train | 330 | 464 | PASS |
| XAUUSD | Test | 152 | 173 | PASS |
| BTCUSD | Train | 427 | 469 | PASS |
| BTCUSD | Test | 142 | 175 | PASS |
| USTEC | Train | 416 | 543 | PASS |
| USTEC | Test | 147 | 259 | PASS |

### Primary Sweep-minus-Breach Hit1R_60m

| Instrument | EXP-030 Test | EXP-015 1m Test | Direction Change |
|------------|-------------|----------------|-----------------|
| EURUSD | −0.145 [−0.255, −0.036] | +0.134 [+0.001, +0.267] | **REVERSED** |
| XAUUSD | +0.011 [−0.101, +0.122] | −0.029 [−0.151, +0.095] | No (near zero) |
| BTCUSD | −0.154 [−0.266, −0.047] | −0.117 [−0.250, +0.018] | No (consistent negative) |
| USTEC | +0.046 [−0.057, +0.149] | +0.048 [−0.063, +0.160] | No (near zero, stable) |

---

## Conclusion

**INCONCLUSIVE** by the predeclared criteria (no new positive instrument; EURUSD does not replicate). However, the results are substantively informative for the reflection:

1. **EURUSD partial positive reverses at 15-minute.** The 1-minute positive (+0.134) becomes a confirmed negative (−0.145) at 15-minute resolution. This is not a null finding — it is a directional reversal with CIs excluding zero on both ends. The sweep-entry edge at 1-minute depends on capturing the post-sweep reversal within the 1-minute entry bar; the 15-minute bar absorbs this move before the outcome window begins.

2. **BTCUSD shows a consistent negative pattern** (train −0.120, test −0.154, both CIs exclude zero negatively). This is the most stable finding: sweeps consistently underperform breaches on BTCUSD at 15-minute resolution.

3. **XAUUSD and USTEC are consistently null** at both 1-minute and 15-minute. These instruments show no sweep advantage at any tested resolution.

4. **For the Phase 004A reflection**: no sweep-focused branch is warranted at 15-minute. The EURUSD deferred positive from Phase 003 is functionally closed at this timeframe. Any future sweep work must address the resolution-timing interaction explicitly.

---

## Key Artifacts

- `results/sweep_events_15m.csv` — all sweep/breach events with outcomes
- `results/event_counts.csv` — per-instrument/segment count summary
- `results/bootstrap_primary.csv` — stratified bootstrap CIs on Hit1R_60m difference
- `results/exp015_reference_comparison.csv` — 15m vs 1m comparison table
