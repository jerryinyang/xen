VERDICT: APPROVE

Review basis:
- Scope: `python/experiments/EXP-012/scope.md`
- Analysis plan: `python/experiments/EXP-012/analysis-plan.md`
- Code: `python/experiments/EXP-012/code/run_experiment.py`
- Active checkpoint: `docs/experiments-docs/checkpoints/2026-05-23-003-ict-one-setup-timebar-validation/design.md`

Checks:
- Implements only the scoped data-readiness work: chronological inventory, New York macro-window coverage, missing-bar diagnostics, active-session summaries, and cost-data availability with explicit proxy scenarios.
- Uses only 1-minute time bars from `data/timebars/`; no Line Break, Renko, Heiken Ashi, tick, or sub-minute inputs are introduced.
- Enforces the global holdout rule with lazy `scan_parquet` -> `sort("CloseTime")` -> first-70-percent `slice()` -> `collect()` before any analysis-set materialization.
- Applies the nested train/test split inside the holdout-excluded analysis set and never uses future rows relative to the train/test cutoff or any event timestamp.
- Documents the required timestamp assumption explicitly by treating naive `CloseTime` values as UTC before conversion to `America/New_York`; the assumption is surfaced in the runtime outputs rather than hidden in code.
- Builds the macro-window coverage table from a full date-by-window grid, so zero-observed windows are counted rather than silently dropped from denominators.
- Quantifies missing bars and active-session timing from aggregated daily summaries, and plots only aggregated outputs; no full analysis-set pandas conversion is used for visualisation.
- Confirms cost-field absence from the actual Parquet schemas and writes explicit proxy scenarios for later experiments instead of inferring unavailable bid/ask or slippage data.

Code-standards self-check:
- Organization, lazy loading and holdout exclusion, bounded plotting/data conversion, concise manual output, zero-baseline handling, and time-bar-only scope compliance pass.
