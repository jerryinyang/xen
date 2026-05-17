VERDICT: APPROVE

Reviewed artifacts:
- python/experiments/EXP-004-TF/scope.md
- python/experiments/EXP-004-TF/analysis-plan.md
- python/experiments/EXP-004-TF/code/run_experiment.py
- python/src/timeframe_replication.py

Checks:
- Phase alignment: matches active checkpoint Block A timeframe replication for EXP-004.
- Holdout: real-price reversal references are created only from holdout-excluded higher-timeframe bars.
- Reversal reference: ATR-scaled swing reversals are timestamped at confirmation; primary 1.5x ATR and alternate 2.0x ATR counts are reported.
- Signal extraction: direction-change events use each chart type's native timestamp (`CloseTime` or `SourceCloseTime`).
- Matching: signals are matched by fixed timestamp window, not by row index.
- Synthetic price discipline: reversal truth and validation use real same-timeframe time-bar prices; no strategy return or P&L metrics are computed.
- Output scope: writes precision/recall, latency, matching, sensitivity, support, validation, manifest, and planned plots.
- Code conventions: lazy source loading, deterministic generation, bounded plot inputs, concise logging.

No blocking issues found.
