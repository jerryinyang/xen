# Pre-Execution Governance Review: EXP-013

VERDICT: APPROVE

## Artifacts Reviewed

- `python/experiments/EXP-013/scope.md`
- `python/experiments/EXP-013/analysis-plan.md`
- `python/experiments/EXP-013/code/run_experiment.py`
- `python/src/ict_timebar.py`
- `docs/experiments-docs/checkpoints/2026-05-23-003-ict-one-setup-timebar-validation/design.md`
- `python/experiments/EXP-012/results.md`

## Scope and Phase Alignment

EXP-013 answers one Phase 003 H1 question: whether fixed NY macro windows differ from adjacent and randomized controls. It remains time-bar-native and does not use Line Break, Renko, Heiken Ashi, a full ICT model, parameter tuning, or cost-sensitive P&L.

The revised scope and analysis plan define the secondary metric denominators before execution. Sweep and displacement frequencies are descriptive only, and support criteria remain tied to the primary ATR-normalized range metric.

## Holdout and Temporal Controls

- The loader in `python/src/ict_timebar.py` uses lazy Parquet scans, sorts by `CloseTime`, and collects only the first chronological 70 percent analysis set.
- Train/test segmentation is performed inside the analysis set using the EXP-012 chronological convention.
- Macro-window membership uses the EXP-012 `CloseTimeNY` convention.
- ATR and displacement thresholds are shifted so each window uses only values known before or during the evaluated bar, not future bars.
- ONH/ONL are excluded from pre-09:30 sweep-frequency diagnostics, preventing look-ahead for early macro windows.

## Code Standards Review

- Imports precede path setup, constants, helper functions, plotting helpers, orchestration, and `main()`.
- Output directories are created only inside `run_experiment()`.
- Plot inputs are aggregated window observations, not full time-bar frames.
- The code keeps stdout concise and writes detailed outputs to `results/`.
- No chart-type generators, synthetic prices, bar-index alignment, silent deduplication, or helper-level printing are used.
- The shared module is justified because EXP-013 and EXP-014 need identical NY-time, macro-window, and liquidity-level conventions.
- 2026-05-24 performance revision: repeated random-control window summaries now reuse
  per-day NumPy arrays instead of repeatedly filtering Polars day frames. This preserves
  the approved 100 deterministic same-day random controls per window while avoiding the
  previous Python/Polars overhead. Additional orchestration-level INFO logs identify
  loading, diagnostics, liquidity-level computation, and observation construction stages.

## Verification

- Static compilation passed with the project venv after the 2026-05-24 revision:
  `python/.venv/bin/python -m py_compile python/experiments/EXP-013/code/run_experiment.py`
- A synthetic in-memory helper smoke test validated the revised EXP-013 cached-array window
  metric path, including observed bar count, ATR-normalized range, absolute return, sweep
  flag, displacement flag, and forward return, without running experiment data.
- After manual execution exposed a plotting error, the primary-effect interval plot now uses
  `MeanDifferenceATR` with the bootstrap mean confidence interval instead of plotting
  `MedianDifferenceATR` against a mean CI. The output plot path was verified from the
  already-generated CSV outputs without reloading experiment data.

## Manual Execution Gate

EXP-013 is approved for manual execution. The pipeline did not execute the experiment code.
