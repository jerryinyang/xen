VERDICT: APPROVE

Review basis:
- Scope: `python/experiments/EXP-009/scope.md`
- Analysis plan: `python/experiments/EXP-009/analysis-plan.md`
- Code: `python/experiments/EXP-009/code/run_experiment.py`
- Shared implementation: `python/src/signal_quality.py`
- Active checkpoint: `docs/experiments-docs/checkpoints/2026-05-16-001-signal-quality-classification/design.md`

Checks:
- Implements only 15-minute time-bar direction-change signals and 15-minute Heiken Ashi direction-change signals.
- Aligns with the EXP-007 result: 15-minute FE60, AE60, and log FE/AE are the hypothesis-carrying metrics; precision, recall, run continuation, and multiplicity are diagnostics.
- Writes `coverage_adjusted_outcomes.parquet` so HA direction-change outcomes are interpreted against the full time-bar direction-change reference population.
- Uses HA synthetic prices only to define HA direction state; all outcome metrics resolve from real 1-minute time-bar OHLC prices at 15-minute signal timestamps.
- Loads first 70 percent chronological analysis rows before 15-minute aggregation and HA generation; global holdout remains untouched.
- Reports HA/time signal-count ratio and HA alignment to time-bar direction changes.
- Limits bootstrap comparisons to hypothesis-carrying FE60, AE60, and log FE/AE metrics; precision and continuation remain descriptive summaries.
- Writes `signal_denominator_diagnostics.parquet` so denominator policy remains explicit even though HA is 1:1 with time bars.
- Does not introduce 1-minute analysis, Renko, Line Break, HA construction-price returns, P&L, parameter variation, or predictive modeling.

Code-standards self-check:
- Organization, lazy loading and holdout exclusion, bounded plotting/data conversion, concise manual output, zero-baseline handling, duplicate-source event denominators, and synthetic-price discipline pass after optimisation.
