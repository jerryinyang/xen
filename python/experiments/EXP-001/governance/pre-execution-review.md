# Pre-Execution Governance Review: EXP-001

## Artifacts Reviewed

- `python/experiments/EXP-001/scope.md`
- `python/experiments/EXP-001/analysis-plan.md`
- `python/experiments/EXP-001/code/run_experiment.py`

## Governance Checks Applied

### Core Constraints

| Constraint | Status | Notes |
|---|---|---|
| Simplicity Over Complexity | PASS | Descriptive metrics, practical effect thresholds, sign counts, and descriptive bootstrap intervals are the simplest sufficient approach. |
| No Academic-Finance Pitfalls | PASS | Non-parametric bootstrap used; no normality/stationarity/i.i.d. assumptions. |
| Strict Experiment Scoping | PASS | Single hypothesis, defined boundaries, concrete success/failure criteria, complexity budget respected. |
| Framework Principles | PASS | Data-driven, non-parametric, synthetic price discipline observed, timestamp alignment used. |
| OOS Holdout Rule | PASS | Code lazily scans matching time-bar files, sorts by `CloseTime`, computes the row cutoff, and collects only the first 70% analysis slice. No holdout rows are materialized. |
| Look-Ahead Bias Prevention | PASS | Generators called on pre-holdout analysis set; no future data used relative to event timestamps. |
| Synthetic Price Discipline | PASS | Heiken Ashi uses `RealClose`; event bars join `RealClose` from time bars; movements use real prices. |

### Artifact-Specific Checks

**Scope Document**
- Hypothesis is testable and specific.
- Success/failure criteria are measurable with explicit ghost-rate, entropy-headroom, and absolute entropy-gain thresholds.
- Chart types, instruments, time range, exclusions all explicit.
- Complexity budget: 2 tests, 4 plots, 1 module — matches plan and code.
- Holdout exclusion and synthetic price rule explicitly stated.

**Analysis Plan**
- Methods justified with "why this method" and "simpler alternative considered" for each step.
- Assumptions documented.
- Cross-chart alignment specified by timestamp (`CloseTime` / `SourceCloseTime`).
- Visualisations are purposeful and within budget.
- Interpretation guide pre-defines outcomes.

**Code**
- Type hints present on all public functions.
- Docstrings with Parameters and Returns sections.
- NaN and edge-case handling explicit.
- Analysis, plotting, and orchestration separated.
- Data loading uses Polars `scan_parquet` with `sort("CloseTime")`.
- Bootstrap uses deterministic seed and is treated as descriptive because the experiment has only four instrument-level units.
- Code writes a reproducibility manifest with input file metadata, source file hashes, runtime package versions, and threshold parameters.
- Event-chart distinct-source sensitivity metrics are emitted for entropy and real-price movement.

## Issues Found

### Critical

**Missing `Direction` column for 1-minute time bars**
- **Location**: `code/run_experiment.py`, line 670
- **Details**: The code calls `directional_entropy(chart_df["Direction"])` for all chart types, including `"Time"`. The 1-minute time-bar schema (`docs/references/dataset-reference.md`) does **not** include a `Direction` column. The experiment will raise a `ColumnNotFoundError` when processing the baseline time bars.
- **Required fix**: Compute a `Direction` column for time bars before computing entropy. A simple definition consistent with the Heiken Ashi schema (`+1 if Close >= Open else -1`) or bar-to-bar change (`+1 if Close >= previous Close else -1`) is acceptable. Document the chosen definition in a comment.

### Warning

**`find_timebar_path` may not load the full available dataset**
- **Location**: `code/run_experiment.py`, lines 74–93
- **Details**: The function returns only the most recent Parquet file per instrument (`matches[-1]`). The scope states "Full available dataset per instrument with nested chronological split." If multiple cAlgo sessions have produced multiple files for the same instrument, this function silently discards earlier sessions.
- **Required fix**: Either concatenate all chronologically sorted files for the instrument, or add an explicit scope/document comment stating the assumption that only one session file exists per instrument. Prefer concatenation to guarantee compliance with "full available dataset."

### Info

- Ghost-bar definition for event bars uses `< min_tick` rather than literal zero movement. This is a robust approximation and acceptable, but it slightly deviates from the scope text "zero real-price movement." No action required.

---

## Re-Review (Revision 1)

### Changes Verified

1. **Direction column for Time bars** — Lines 650–657 now add a `Direction` column (`+1 if Close >= Open else -1`, cast to `Int32`) for the `"Time"` chart type before `directional_entropy(chart_df["Direction"])` is called on line 680.
2. **Full dataset loading** — `load_analysis_timebar_data` discovers all matching Parquet files per instrument, lazily scans them, sorts by `CloseTime`, computes the 70% analysis cutoff, and collects only the analysis slice. It does not silently deduplicate rows; any duplicate-session policy must be explicit because deduplication can move the chronological holdout boundary.
3. **Practical entropy threshold** — The success criteria and code now require a minimum absolute entropy increase of 0.005 bits in addition to the entropy-headroom ratio, preventing a tiny denominator near the binary entropy maximum from driving a support verdict. Event-chart entropy comparisons for the verdict use distinct `SourceCloseTime` rows.
4. **Descriptive bootstrap framing** — Bootstrap summaries remain in the outputs, but the pre-execution criteria no longer treat four-instrument bootstrap intervals as sufficient proof.
5. **Distinct-source sensitivity and manifest** — The code writes `distinct_source_sensitivity.csv` for event-chart duplicate timestamp sensitivity and `run_manifest.json` for reproducibility.

### Re-Review Checks

- Holdout exclusion: PASS — first 70% slice unchanged.
- Synthetic price discipline: PASS — real-price usage unchanged.
- Timestamp alignment: PASS — alignment by `CloseTime` / `SourceCloseTime` unchanged.
- Direction computation: PASS — deterministic, consistent with Heiken Ashi schema.
- Data completeness: PASS — all matching files are loaded, with input file provenance recorded in the manifest and no silent deduplication.

All critical and warning issues from the initial review are resolved. No new issues introduced.

---

VERDICT: APPROVE
