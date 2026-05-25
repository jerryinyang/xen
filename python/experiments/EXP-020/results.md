# Results: Experiment EXP-020

## Summary

EXP-020 shows that the scoped FVG and IFVG detection rules are deterministic and produce ample sample sizes, but they do not clear the readiness gate for downstream IFVG entry studies. Reproducibility passes on all four instruments, and count floors are exceeded by large margins, yet the IFVG inversion event occurs on roughly 84-85% of FVGs in every train/test segment. That makes the event too tautological to serve as a selective confirmation signal under the current parameterization, so the overall readiness verdict is INCONCLUSIVE.

## Detailed Findings

### Detection Mechanics Are Reproducible

- **Observation**: FVG detection is invariant across fresh reloads and shuffled-then-resorted inputs.
- **Evidence**: `reproducibility_digest.csv` shows `FreshReloadMatches=True`, `ShuffledResortMatches=True`, and `Reproducible=True` for EURUSD, XAUUSD, BTCUSD, and USTEC.
- **Interpretation**: The zone-construction logic is deterministic and stable enough to trust mechanically.

### Sample Size Is Not The Problem

- **Observation**: Every instrument and segment far exceeds the minimum FVG and IFVG count floors.
- **Evidence**: Example test counts are EURUSD `76,629` FVGs / `65,339` IFVGs, BTCUSD `86,626` / `73,784`, and USTEC `61,946` / `52,163`. All `FVGFloorMet` and `IFVGFloorMet` flags are `True`.
- **Interpretation**: The downstream readiness failure is not due to sparse data.

### IFVG Inversion Is Too Common To Be Selective

- **Observation**: Nearly all scoped FVGs invert within the 120-bar lifecycle window.
- **Evidence**: IFVG rates range from `0.842` to `0.853` across all instrument/segment rows, well above the predeclared tautology threshold of `0.50`. Every row is flagged `Tautological=True`, and every `ReadyForIFVGStudy` flag is `False`.
- **Interpretation**: Under this definition, IFVG inversion behaves more like a common lifecycle outcome than a discriminating confirmation event. That blocks direct handoff to EXP-021 with the rules unchanged.

## Hypothesis Verdict

**INCONCLUSIVE**

The experiment supports the narrow mechanical claim that FVG and IFVG zones can be detected reproducibly with stable counts, but it does not support operational readiness for later IFVG-entry work. Because the inversion event is too common to be selective, the scoped readiness question remains unresolved under the current rule set.

## Limitations

- The lifecycle window is fixed at 120 bars and the size floor is fixed at `max(price_precision_step, 0.02 * ATR14Prior)`; different predeclared settings could behave differently but would require a new scope.
- The analysis uses 1-minute OHLC data only and makes no profitability claims.
- The reproducibility digest intentionally samples the first 50,000 bars per instrument rather than hashing the full history, though the full-run count tables are internally consistent.

## Alternative Explanations

- The three-candle plus close-through rule may be too permissive for 1-minute data, causing inversion to become a common lifecycle event rather than a useful confirmation.
- The 120-bar lifecycle horizon may be long enough that most eligible gaps eventually invert regardless of practical setup quality.

## Recommended Next Steps

1. Do not proceed with EXP-021 under the current FVG/IFVG ruleset.
2. If the IFVG path remains important, create a new prerequisite experiment that tightens selectivity with one explicitly predeclared change to size, lifecycle, or inversion rules.
