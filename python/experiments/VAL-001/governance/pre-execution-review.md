VERDICT: APPROVE

# Pre-Execution Governance Review: VAL-001 (rev. 3)

This supersedes the rev. 2 review (retained in git history). VAL-001 was
previously executed and approved under rev. 2; a post-completion review found
three detection-power gaps. By explicit user/governance decision the experiment
is re-run **in place** (same ID) as rev. 3 rather than as a new VAL. The
re-execution still passes through this pre-execution gate and the Stage 8 gate.

## Reviewed Artifacts

- `python/experiments/VAL-001/scope.md` (rev. 3)
- `python/experiments/VAL-001/analysis-plan.md` (rev. 3)
- `python/experiments/VAL-001/code/run_experiment.py` (rev. 3)

## What Changed Since rev. 2

- **Detection-power coverage (gap 1)** — rev. 2 carried negative controls for
  only 8 check types. rev. 3 adds a negative control for **every**
  data-integrity and alignment check: base time-bar integrity (null /
  non-increasing / duplicate `CloseTime`, invalid OHLC, null OHLC) via
  `base_timebar_failures`; the three resample output-side checks (future
  timestamp, wrong source-bar count, duplicate close) via the newly extracted
  `resample_output_failures`; the remaining sparse-chart checks (null source
  time, negative `SourceCount`, first-event zero `SourceCount`); the remaining
  Heiken Ashi checks (row-count mismatch, unmapped close, `SourceCount != 1`);
  and the chart schema check via the newly extracted `schema_failures`. Pure
  availability/IO defensive checks (Parquet readability, file presence, non-empty
  slice) are named exclusions, not silently unguarded.
- **Determinism control (gap 2)** — the rev. 2 control only proved
  `DataFrame.equals` returns False for two different frames. rev. 3 routes an
  actually non-deterministic generator (a mutable call counter makes the two
  regenerations differ) through `determinism_failures`, so the control tests the
  determinism check itself.
- **Look-ahead coverage (gap 3)** — rev. 2 probed prefix stability on the
  leading window only. rev. 3 probes `head`, `middle`, and `tail` windows
  (`positioned_windows`) at three cut points (`PREFIX_FRACTIONS = 0.34, 0.67,
  0.95`). Slices that fit within `PREFIX_WINDOW_ROWS` collapse to a single
  `full` window (no redundant duplication). The hypothesis was reworded to scope
  the structural no-look-ahead claim to the probe windows while full-output
  timestamp alignment remains checked on every emitted row.
- A manual generator-correctness review (gap 4) compared the Line Break and
  Renko implementations against `architecture.md` and found no defect; no new
  positive check was added, on the documented rationale that deterministic +
  reproducible generation lets downstream consumers replicate any result.

## Governance Checks

| Constraint | Verdict | Evidence |
|------------|---------|----------|
| Single question / scope discipline | PASS | Still one question (temporal-integrity readiness). Coverage strengthened, not expanded; no strategy/return/P&L claims added. |
| Holdout rule | PASS | Loader unchanged: lazy `pl.len()` → `sort("CloseTime")` → `slice(0, int(0.7*total))` → collect. New probe windows operate on the analysis-slice frame; `tail` windows sit inside the first 70%, never the holdout. |
| Look-ahead prevention | PASS | Multi-position prefix stability + full-output timestamp alignment on every emitted row. |
| Real-price discipline | PASS | No returns, P&L, stops, targets, or signal outcomes. Synthetic prices validated only as data-layer fields. |
| Detection power | PASS | A negative control for every data-integrity/alignment check; an undetected control is a FAIL. Verified on synthetic data (23/23 detected). |
| Statistical assumptions | PASS | No parametric/normality/stationarity/i.i.d. assumptions; deterministic checks only. |
| Complexity budget | PASS | 0 statistical tests / 0; 2 plots / 2; 0 new modules / 0. New pure helpers live inside the experiment script, not in `python/src`. |
| Code conventions | PASS | Organization preserved (new pure checks in the checks section, `positioned_windows` beside the prefix probe). No import side effects; output dirs created only in `main()`. Probe bounds documented as harness constants, not data-derived thresholds. |

## Static + Synthetic Verification Performed

- `py_compile`: clean. `ruff check`: clean. `xen` unit tests: 8/8 pass.
- Synthetic-only pre-run verification (no real data, no holdout, no `results/`
  written): `run_negative_controls` produced **23/23 detected** controls, the
  golden fixture passed, and there were **0 FAIL / 0 INCONCLUSIVE** rows.
- False-positive check: the real Renko, Line Break, and Heiken Ashi generators
  satisfy prefix stability at head/middle/tail windows (0 diverged cuts), so the
  broadened probe does not falsely flag correct generators.

## Notes for Execution

- Re-running **overwrites** the rev. 2 `results/` and `plots/`. The post-execution
  artifacts (`audit.md`, `results.md`, `report.md`, both INDEX entries, and the
  post-experiment review) describe the rev. 2 run and must be regenerated in
  Stages 5–8 after re-execution.
- Expected structure after re-run: 98 checks per real instrument
  (BTCUSD/EURUSD/USTEC/XAUUSD) and 24 synthetic checks (23 negative controls +
  1 golden fixture), all PASS — i.e. ~416 PASS / 0 FAIL / 0 INCONCLUSIVE. The
  1-minute view gains head/middle/tail prefix checks; 15m/60m use a single
  `full` window because the slice fits within `PREFIX_WINDOW_ROWS`.
- Runtime increases relative to rev. 2 because the 1-minute generators are now
  probed at three positions; expect roughly several extra minutes.
