# Pre-Execution Governance Review: EXP-037

**Experiment:** EXP-037 - Null Calibration of Frozen Reference Stack
**Artifacts reviewed:**

- `python/experiments/EXP-037/scope.md`
- `python/experiments/EXP-037/analysis-plan.md`
- `python/experiments/EXP-037/code/run_experiment.py`
- `python/src/referee_calibration.py`

**Reference constraints:**

- `docs/experiments-docs/checkpoints/2026-05-31-006-thesis-qualification-referee-calibration/design.md`
- `docs/experiments-docs/checkpoints/2026-05-31-006-thesis-qualification-referee-calibration/reference-stack-spec.md`
- `.agents/skills/research-pipeline/references/governance-constraints.md`
- `.agents/skills/experiment-developer/references/code-conventions.md`

## VERDICT: APPROVE

```text
VERDICT: APPROVE
```

EXP-037 may proceed to the manual execution gate. No experiment code was run during this review.

## Scope Review

- **Single question:** Approved. The scope asks only the Stage A null-calibration question: empirical FPR and per-leg false-pass profile for the frozen EXP-036 reference stack.
- **Phase alignment:** Approved. The experiment follows Phase 006 Stage A and does not create Stage B power scope, successor-stack design, or a closed-thesis rescue path.
- **Holdout exclusion:** Approved. The final 30% global holdout is excluded before aggregation, feature construction, null resampling, plotting, and output generation.
- **Frozen stack discipline:** Approved. The admissibility layer and evidentiary layer are fixed from `reference-stack-spec.md`; no thresholds or gates are changed.
- **Metric denominators:** Approved. The scope defines trusted realization denominators, cell-level denominators, aggregate E5/E6 denominators, and null/undefined behavior for zero denominators.
- **Complexity budget:** Approved. The scope allows 3 statistical test families, 4 plots, and 1 reusable module; the plan and code stay within that budget.

## Analysis Plan Review

- **Method fit:** Approved. The plan uses descriptive/null-validity diagnostics, dependence-preserving resampling, frozen episode bootstraps, empirical rates, and Wilson intervals. It does not rely on normality, stationarity, iid returns, or constant volatility.
- **Null realism:** Approved. Diagnostics are explicit and precede trusted FPR reporting; failed diagnostics withhold trusted operating-characteristic claims.
- **Predeclared interpretation:** Approved. Measurement success, invalid null calibration, compute infeasibility, and partial/inconclusive outcomes are defined before results exist.
- **No scope creep:** Approved. No power/MDE estimate, planted effect, cost/materiality gate, tolerant aggregation, descriptor variation, or timeframe sweep appears in the plan.

## Implementation Review

- **Organization:** Approved. Imports, path setup, constants, helper functions, orchestration, and `main()` are separated in `run_experiment.py`; reusable calibration code is isolated in `python/src/referee_calibration.py`.
- **Import side effects:** Approved. The reusable module does not load data, create directories, write files, or plot at import time. Output directories are created only in orchestration.
- **Holdout exclusion:** Approved. Data loading uses `load_analysis_timebars`, which lazy-scans Parquet, sorts by `CloseTime`, slices the first 70%, then collects. Aggregation occurs only after this holdout-excluded load.
- **Bounded data conversion:** Approved. Conversion to pandas occurs after strict 1h/4h aggregation and feature construction, not on full 1-minute data or the global holdout.
- **Plot memory:** Approved. Plots use aggregated rate tables, not raw row-level analysis frames.
- **Repeated heavy work:** Approved. Plotting reuses output summary tables; it does not reload or regenerate data.
- **Logging/output:** Approved. Logging is orchestration-level; `print()` is limited to the final concise manual-run summary.
- **Zero denominators:** Approved. Wilson intervals and rates emit `None` for zero denominators rather than finite-looking percentages.
- **Duplicate-source denominator rule:** Not applicable. EXP-037 uses strict real time bars and the frozen Prior-Range Location state stream, not chart-type events with duplicate `SourceCloseTime`.
- **Synthetic-price discipline:** Approved. No Heiken Ashi, Renko, Line Break, or synthetic construction price is used.
- **Compute budget:** Approved. The runner profiles the first 10 FSE, applies the predeclared downscale from 150 to 100 realizations per block length, and stops on compute infeasibility rather than silently altering B or dropping legs.

## Verification

- `python/.venv/bin/python -m py_compile python/src/referee_calibration.py python/experiments/EXP-037/code/run_experiment.py` passed.
- `PYTHONPATH=python/src python/.venv/bin/python - <<'PY' ... import referee_calibration ... PY` passed.
- `git diff --check` passed.
- The system `python3` interpreter lacks `numpy`; the project venv under `python/.venv/bin/python` has the declared dependencies and was used for verification.

## Code-Standards Self-Check

- Organization: pass.
- Lazy loading and holdout exclusion: pass.
- Output directories created only in orchestration: pass.
- Bounded plotting/data conversion: pass.
- Concise logging/output: pass.
- Zero-baseline and zero-denominator handling: pass.
- Temporal alignment: pass for scoped real time bars; no cross-view or chart-type timestamp alignment is in scope.
- Synthetic-price discipline: pass.
- Duplicate-source event denominators: not applicable for this scope.

## Decision

Pre-execution review approves EXP-037 for manual execution.
