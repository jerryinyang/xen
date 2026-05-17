VERDICT: APPROVE

Reviewed artifacts:
- python/experiments/EXP-006-TF/scope.md
- python/experiments/EXP-006-TF/analysis-plan.md
- python/experiments/EXP-006-TF/code/run_experiment.py
- python/src/timeframe_replication.py

Checks:
- Phase alignment: matches active checkpoint Block A timeframe replication for EXP-006.
- Holdout: HA distortion is measured only after the first-70% source slice and higher-timeframe aggregation.
- Scope: includes only same-timeframe time bars and Heiken Ashi; no Line Break or Renko analysis is introduced.
- Synthetic price discipline: HA `HAClose` returns are explicitly diagnostic and non-tradable; real-price comparisons use paired `RealClose`.
- Regimes: volatility-regime summaries use real same-timeframe returns and train-calibrated thresholds.
- Uncertainty: block bootstrap compression intervals are written in the JSON artifact.
- Output scope: writes distortion CSV/JSON, regime distortion, validation, manifest, and planned plots.
- Code conventions: lazy source loading, no import side effects, bounded plot samples, concise logging.

No blocking issues found.
