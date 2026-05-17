VERDICT: APPROVE

Review basis:
- Scope: `python/experiments/EXP-007/scope.md`
- Analysis plan: `python/experiments/EXP-007/analysis-plan.md`
- Code: `python/experiments/EXP-007/code/run_experiment.py`
- Shared implementation: `python/src/signal_quality.py`

Checks:
- Implements the approved multi-state signal-quality baseline using FE, AE, log FE/AE, bounded signal-level precision, event-level recall, run continuation, signal multiplicity, and explicit missing-signal summaries.
- Loads each instrument with lazy `scan_parquet`, sorts by `CloseTime`, and slices the first 70 percent before collecting. The final 30 percent global holdout is not loaded or inspected.
- Aggregates 15-minute bars only from holdout-excluded 1-minute analysis data.
- Uses `CloseTime` for time bars and Heiken Ashi, `SourceCloseTime` for Renko and Line Break.
- Computes all signal-quality outcomes from real 1-minute time-bar OHLC prices; synthetic HA, Renko, and Line Break construction prices are not used for outcomes.
- Uses train-segment calibration for volatility regimes and 10,000-resample bootstrap comparisons with deterministic bounded input sampling for large strata.
- Keeps output directory creation inside orchestration and bounds plotting inputs by deterministic sampling.
- Treats non-finite or zero ATR values as non-computable outcomes before FE, AE, run-continuation, and qualifying-move divisions.
- Precomputes forward-window extrema once per instrument and processes EXP-007 contexts one instrument at a time to reduce repeated scans and retained memory.

Code-standards self-check:
- Organization, lazy loading and holdout exclusion, bounded plotting/data conversion, concise manual output, zero-baseline handling, duplicate-source event denominators, performance/memory bounds, and synthetic-price discipline pass.
