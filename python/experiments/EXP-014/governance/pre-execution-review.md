# Pre-Execution Governance Review: EXP-014

VERDICT: APPROVE

## Artifacts Reviewed

- `python/experiments/EXP-014/scope.md`
- `python/experiments/EXP-014/analysis-plan.md`
- `python/experiments/EXP-014/code/run_experiment.py`
- `python/src/ict_timebar.py`
- `docs/experiments-docs/checkpoints/2026-05-23-003-ict-one-setup-timebar-validation/design.md`
- `python/experiments/EXP-012/results.md`

## Scope and Phase Alignment

EXP-014 answers one Phase 003 H2 prerequisite question: whether PDH/PDL and ONH/ONL liquidity levels can be computed reproducibly from the available 1-minute time bars. It does not test sweep outcomes, strategy returns, IFVGs, breakers, or full-model behavior.

The revised scope and plan explicitly define the previous-day convention as the previous observed weekday NY date and define ONH/ONL with CloseTimeNY boundaries from 17:00 through 09:30. This keeps the implementation aligned with EXP-012's weekday denominator and avoids hidden calendar assumptions.

## Holdout and Temporal Controls

- The loader in `python/src/ict_timebar.py` uses lazy Parquet scans, sorts by `CloseTime`, and collects only the first chronological 70 percent analysis set.
- All level construction is performed after global holdout exclusion.
- PDH/PDL are generated from prior observed weekday dates, not future dates.
- ONH/ONL are generated from deterministic overnight windows ending on the event date.
- Missing data is classified through missing-reason outputs rather than imputed or silently dropped.

## Code Standards Review

- Imports precede path setup, constants, helper functions, plotting helpers, orchestration, and `main()`.
- Output directories are created only inside `run_experiment()`.
- Plot inputs are availability summaries and missing-reason counts, not full time-bar frames.
- The reproducibility rerun is deterministic and compares the generated level table against a second computation.
- No chart-type generators, synthetic prices, strategy P&L, bar-index alignment, silent deduplication, or helper-level printing are used.
- The shared module is justified because later sweep-dependent experiments must reuse these exact level definitions and missing-level rules.

## Verification

- Static compilation passed with the project venv:
  `python/.venv/bin/python -m py_compile python/src/ict_timebar.py python/experiments/EXP-013/code/run_experiment.py python/experiments/EXP-014/code/run_experiment.py`
- A synthetic in-memory helper smoke test validated shared NY-time and liquidity-level construction without running experiment data.

## Manual Execution Gate

EXP-014 is approved for manual execution. The pipeline did not execute the experiment code.
