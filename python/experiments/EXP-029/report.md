# Report: EXP-029 — 15-Minute FVG IFVG Selectivity Check

**Phase**: 004A (Pre-Phase — Timeframe Feasibility)  
**Date**: 2026-05-27  
**Status**: AGAINST  
**Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC

---

## One-Line Finding

The unmodified EXP-020 120-bar IFVG rule applied to 15-minute bars produces inversion rates of 83–86% on all four instruments, replicating the Phase 003 1-minute baseline; lifecycle window length — not FVG rule permissiveness — is the dominant driver, as an 8-bar (≈2-hour) sensitivity drops rates to 45–48%.

---

## Background

EXP-029 is the first of three Phase 004A pre-phase experiments. Its purpose is to determine whether the IFVG non-selectivity problem identified in Phase 003 (EXP-020, EXP-021) is a resolution artefact or a rule-design flaw. If the inversion rate drops materially below 50% at 15-minute resolution, Branch B can start by testing the existing rule at a higher timeframe. If the rate stays near the 1-minute baseline, Branch B must pursue a rule redesign.

The experiment applies the EXP-020 three-candle FVG and 120-bar close-through IFVG rule unchanged to synthetic 15-minute bars generated from holdout-excluded 1-minute analysis-set data.

---

## Methods

- **Data**: 1-minute analysis-set bars (first 70% chronologically) aggregated into synthetic 15-minute OHLC via deterministic clock-aligned resampling (`python/src/bar_aggregator.py`). Partial trailing windows dropped.
- **FVG detection**: EXP-020 three-candle rule. Bearish FVG when `High[i] < Low[i-2]`; bullish when `Low[i] > High[i-2]`. Minimum size `max(price_precision_step, 0.02 × ATR_14_15m)`.
- **Lifecycle**: Primary 120-bar window; secondary 8-bar sensitivity. IFVG = first later close through the opposite side of the FVG.
- **Reproducibility**: SHA-256 digest matching on fresh reload and shuffled resort.
- **Bootstrap**: Block bootstrap (n=2,000, block=50, seed=42) on the primary IFVG rate.

---

## Results

### Primary IFVG Rate (120-bar lifecycle)

| Instrument | Train | Test | Combined | Bootstrap CI |
|------------|-------|------|----------|-------------|
| EURUSD | 0.853 | 0.857 | 0.854 | [0.846, 0.865] |
| XAUUSD | 0.842 | 0.821 | 0.836 | [0.825, 0.846] |
| BTCUSD | 0.826 | 0.845 | 0.832 | [0.823, 0.842] |
| USTEC | 0.848 | 0.846 | 0.848 | [0.837, 0.859] |

Phase 003 1-minute baseline: 84–85%. All four instruments are within 2pp.

### Lifecycle Sensitivity

| Instrument | 120-bar rate | 8-bar rate | Δ (pp) |
|------------|-------------|-----------|--------|
| EURUSD | 0.854 | 0.479 | −37.6 |
| XAUUSD | 0.836 | 0.457 | −37.8 |
| BTCUSD | 0.832 | 0.454 | −37.8 |
| USTEC | 0.848 | 0.461 | −38.6 |

### FVG/IFVG Counts

All 8 instrument-segment combinations exceed the predeclared floors (≥100 FVGs, ≥50 IFVGs). Total 15-minute FVGs: 3,391–9,283 per segment. Total 15-minute IFVGs: 2,783–7,321 per segment.

### Reproducibility

All 4 instruments: fresh-reload and shuffled-resort digests match exactly.

---

## Conclusion

**AGAINST.** The 120-bar IFVG inversion rate at 15-minute resolution (83–86%) replicates the Phase 003 1-minute baseline on all four instruments. The rule's permissiveness is intrinsic to its long observation window, not to 1-minute resolution. The 8-bar sensitivity (≈2-hour window) reduces rates to 45–48% uniformly, confirming that lifecycle duration, not timeframe, drives the high inversion rate.

**Implication for Phase 004B Branch B**: IFVG selectivity redesign must address the rule design — specifically the lifecycle window or gap qualification criteria — rather than relying on timeframe migration. A shorter lifecycle (e.g., 8-bar ≈ 2-hour window) at 15-minute bars could be a starting point for EXP-035, provided it preserves adequate event counts and avoids being tautological in the other direction.

---

## Key Artifacts

- `python/src/bar_aggregator.py` — new deterministic OHLC resampling module (shared with EXP-030, EXP-031)
- `results/count_readiness.csv` — FVG/IFVG counts, inversion rates, and floor flags per instrument/segment
- `results/lifecycle_sensitivity.csv` — 120-bar vs 8-bar rate comparison
- `results/bootstrap_inversion_rate.csv` — block bootstrap CIs per instrument
- `results/reproducibility_digest.csv` — SHA-256 digest matching
