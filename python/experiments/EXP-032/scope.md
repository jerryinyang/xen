# Experiment: EXP-032 - 1-Hour USTEC Candidate A Breaker Magnitude Gate

## Hypothesis

The USTEC Candidate A breaker chain, applied to synthetic 1-hour bars with elapsed-time-scaled definitions, preserves the EXP-031 15-minute positive direction and reaches a predeclared minimum magnitude before Branch A is allowed to proceed to temporal segmentation.

## Question

Does the USTEC Candidate A breaker chain remain directionally positive and magnitude-comparable at 1-hour resolution, or should Branch A stop or be reframed before further breaker validation experiments?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/` aggregated into synthetic 1-hour OHLC bars for sweep, displacement, and Candidate A breaker detection; real 1-minute bars retained for outcome evaluation. No Line Break, Renko, Heiken Ashi, IFVG, or other chart-type inputs.
- **Parameters**: Aggregation is deterministic clock-aligned OHLC resampling over 60 complete 1-minute bars: first Open, maximum High, minimum Low, last Close, summed TickVolume, and partial trailing windows dropped. Sweep definitions inherit EXP-015/EXP-031 logic on 1-hour bars: bearish high sweep when `High > level + buffer` and `Close < level`; bullish low sweep when `Low < level - buffer` and `Close > level`; breach is not a primary comparison class in this experiment. Buffer is `max(price_precision_step, 0.05 * ATR_14_1h)`. First-touch policy is preserved per NY date and level family.
- **Elapsed-time-scaled chain constants**: Displacement uses the EXP-018 close-location and body rule on 1-hour bars, with `BodySize >= 1.5 * BodyMedianPrior`, bearish close-location `<= 0.25`, bullish close-location `>= 0.75`, `BodyMedianPrior` over 25 completed 1-hour bars (matching the 100 15-minute bars in EXP-031), and a maximum displacement-confirmation window of 3 completed 1-hour bars after the sweep (approximating the 10 15-minute bars in EXP-031). Candidate A uses the last opposite-direction 1-hour candle within 8 completed 1-hour bars before displacement (approximating the 30 15-minute bars in EXP-031) and a maximum breaker-confirmation lifecycle of 30 completed 1-hour bars after displacement (matching the 120 15-minute bars in EXP-031). These constants are fixed before implementation and must not be tuned against results.
- **Instruments**: USTEC only, matching the Branch A candidate inherited from EXP-023 and EXP-031.
- **Time range**: Full available USTEC dataset with nested chronological split applied to the 1-minute series before aggregation. First 70 percent of the 1-minute series is the analysis set, split chronologically 70/30 into train/test after 1-hour aggregation; final 30 percent is the global holdout and is never loaded, inspected, aggregated, or used.
- **Global holdout**: The final 30 percent of the chronologically ordered USTEC 1-minute dataset is excluded before any aggregation. The full 1-minute dataset must not be aggregated and re-split.
- **Look-ahead bias prevention**: 1-hour aggregation uses only completed 1-minute bars. Sweep, displacement, and breaker labels use only 1-hour bars at or before each event timestamp. Outcomes use only real 1-minute bars with `CloseTime` strictly after the confirming 1-hour displacement candle close; no 1-minute movement inside the confirming 1-hour signal candle is used for outcome paths.
- **Real-price outcome discipline**: All Return_R, MAE_R, MFE_R, Hit1R, and log-return outcomes are evaluated on real 1-minute OHLC prices aligned by `CloseTime`. The 1-hour view supplies detection only.
- **Entry and label convention**: The canonical entry timestamp is the 1-hour displacement-close, matching EXP-031's label-based comparability convention. Candidate A breaker confirmation is a retrospective label on the displacement event, not a separate live entry trigger. This experiment is a Branch A magnitude gate, not an execution-ready strategy validation.
- **Exclusions**: No full ICT model, no Branch B IFVG logic, no rule-family search, no parameter tuning, no 15-minute temporal segmentation, no direction/session/volatility/level-family segmentation, no simplified controls, no delay-matched controls, no cost stress, no stop perturbation, no second-candle-open primary entry, no Candidate B breaker, no instruments other than USTEC.

## Success / Failure Criteria

- **Evidence FOR**: All hard gates pass: `>= 50` risk-feasible Candidate A breaker-labeled events in both train and test; train and test breaker-minus-baseline Return_R_60m point estimates are positive; test Return_R_60m bootstrap CI excludes zero positively; and the test Return_R_60m point estimate is at least 50 percent of EXP-031's 15-minute test diff (`>= 0.918R`, based on EXP-031 `+1.836R`). Report the stricter 50 percent of EXP-023's 1-minute test diff (`>= 2.088R`) as a non-binding reference band. MAE_R_60m is reported as a secondary structural diagnostic; lower MAE strengthens the finding but does not replace the Return_R hard gates.
- **Evidence AGAINST Branch A continuation**: With event floors met, any hard gate fails: train or test Return_R_60m point estimate is non-positive; test CI includes or crosses zero; or test Return_R_60m is below `0.918R`. This stops Branch A before EXP-033 unless a new reflection explicitly reframes the branch with weaker claims.
- **Inconclusive**: Risk-feasible breaker-labeled events fall below `>= 50` in train or test, the 1-hour / 15-minute displacement retention ratio falls below 30 percent, or required reference artifacts from EXP-031 are unavailable. Inconclusive count collapse does not authorize returning to 1-minute structural claims; it triggers stop-or-reframe review before further Branch A scopes.

## Prerequisites and Sequencing

Requires EXP-014 level reproducibility, EXP-015 sweep framework, EXP-018 displacement definition, EXP-022 Candidate A breaker definition, EXP-023 USTEC reference values, and EXP-031 15-minute USTEC breaker results. This experiment is the first Branch A Phase 004B gate after the Phase 004A reflection. No EXP-033 or later Branch A scope may be created until EXP-032 completes, passes audit/governance, and satisfies the hard gates above.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 4
- Max new code modules: 0

`python/src/bar_aggregator.py` already supports arbitrary N-minute deterministic OHLC aggregation and must be reused. If implementation discovers that a reusable helper must change, route back through governance before adding or modifying shared modules.

## Data Requirements

Load the USTEC 1-minute time-bar Parquet lazily, sort by `CloseTime`, slice the first 70 percent chronologically as the analysis set, and aggregate only that analysis-set slice into synthetic 1-hour OHLC via `bar_aggregator.aggregate_ohlc(period_minutes=60)`. Retain the same 1-minute analysis-set slice for outcome evaluation. Load EXP-014 reproducible PDH/PDL/ONH/ONL levels for the analysis-set date range. Apply the nested train/test split on the 1-hour series. Detect the sweep -> displacement -> Candidate A breaker chain on the 1-hour bars with the fixed elapsed-time-scaled constants above. Evaluate outcomes on real 1-minute prices strictly after the 1-hour displacement close.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*USTEC*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
analysis_rows = int(scan.select(pl.len()).collect().item() * 0.70)
bars = (
    scan
    .slice(0, analysis_rows)
    .collect()
)
```

## Suggested Direction

Report the event-count waterfall before any outcome metric. The analysis should make the Branch A decision mechanically: if the 1-hour chain clears the hard gates, EXP-033 temporal segmentation may be scoped; if not, stop or reframe Branch A before any further scope.
