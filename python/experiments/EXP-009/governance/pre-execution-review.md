VERDICT: APPROVE

Review basis:
- Scope: `python/experiments/EXP-009/scope.md`
- Analysis plan: `python/experiments/EXP-009/analysis-plan.md`
- Code: `python/experiments/EXP-009/code/run_experiment.py`
- Shared implementation: `python/src/signal_quality.py`

Checks:
- Implements only 1-minute time-bar direction-change signals and Heiken Ashi direction-change signals.
- Uses HA synthetic prices only to define HA direction state; all outcome metrics resolve from real time-bar OHLC prices.
- Loads first 70 percent chronological analysis rows before HA generation; global holdout remains untouched.
- Uses shared FE, AE, precision, event-level recall, run-continuation, and multiplicity framework with bootstrap HA-minus-time comparisons.
- Reports HA/time signal-count ratio and HA alignment to time-bar direction changes.
- Does not introduce Renko, Line Break, HA construction-price returns, P&L, parameter variation, or predictive modeling.

Code-standards self-check:
- Organization, lazy loading and holdout exclusion, bounded plotting/data conversion, concise manual output, zero-baseline handling, duplicate-source event denominators, and synthetic-price discipline pass.
