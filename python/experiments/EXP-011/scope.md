# Experiment: EXP-011 - Event-Native Volatility Regime Detection

## Hypothesis

Volatility-regime labels derived from three pre-fixed Renko internal features - event density, source-bar count per brick, and brick-to-ATR ratio - identify Renko regime states with lower boundary cost and fewer missed transitions than time-bar-derived regime labels applied to Renko events.

## Question

Can Renko's own internal structure define volatility regimes that align better with Renko event boundaries than the time-bar-derived tercile labels used in Phase 1, and do those regimes produce more differentiated signal-quality strata?

## Scope Boundaries

- **Chart Types**: Renko and Time Bars. Time bars are the reference regime and real-price outcome anchor.
- **Chart Type Parameters**: 1-minute and 15-minute source timeframes; Renko ATR period 14.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set (split 70/30 for train/test); final 30% = global holdout (never used).
- **Global holdout**: The final 30% of the full dataset must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: Event-native feature values and tercile labels at each Renko event must use only Renko/time-bar information available at or before that event timestamp.
- **Synthetic price discipline**: Renko construction prices are used only to compute the pre-fixed brick-to-ATR diagnostic feature. All signal-quality outcomes resolve from real 1-minute time-bar prices.
- **Fixed event-native features**: Renko event density, source-bar count per brick, and brick-to-ATR ratio. No other features may be added.
- **Fixed segmentation**: Terciles only. Boundaries are computed on the nested train segment (first 70% of the analysis segment after holdout exclusion) and then frozen.
- **Exclusions**: No strategy P&L, no parameter optimization, no clustering, no quartiles/custom bins, no feature weights, no composite scoring, no post-hoc feature selection, no claim that event-native regimes replace time-bar regimes for return evaluation.

## Success / Failure Criteria

- **Evidence FOR**: For at least one pre-fixed feature, event-native tercile labels reduce hybrid rate or missed-transition rate versus time-bar-derived regime labels on at least 3 of 4 instruments at either timeframe, with bootstrap CIs excluding zero. Each feature receives its own verdict; no best feature is selected after seeing signal-quality distributions.
- **Evidence AGAINST**: None of the three pre-fixed features reduces hybrid rate or missed-transition rate consistently, or any apparent reduction comes with weaker signal-quality stratification than time-bar regimes.
- **Inconclusive**: Feature-specific results conflict across instruments/timeframes, sparse event counts prevent reliable tercile estimates, or train/test boundary calibration fails audit.

## Complexity Budget

- Max statistical tests: 3 feature-specific regime comparison families.
- Max visualisations: 5.
- Max new code modules: 0 shared modules beyond the EXP-007 framework, plus the experiment runner.

## Data Requirements

Use Renko ATR-14 generated from 1-minute and 15-minute analysis-set source bars. Compute the three fixed event-native features from Renko events only. Compute tercile boundaries on the nested train segment and apply them unchanged to the rest of the analysis set. Use time-bar regime labels from the existing Phase 1 methodology as the reference.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

bars = (
    pl.scan_parquet(path)
    .sort("CloseTime")
    .collect()
)
```

## Suggested Direction

Analyze all three event-native features independently. Treat signal-quality stratification as descriptive evidence, not as an optimization target. The primary question is whether event-native labels reduce Renko boundary cost and missed transitions.
