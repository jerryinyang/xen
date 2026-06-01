VERDICT: APPROVE

# Pre-Execution Governance Review: VAL-001 (rev. 2)

This supersedes the rev. 1 review. The artifacts were revised before first
execution (no `results/` produced) to remove checks that passed by construction
and to add detection-power evidence, per an independent pre-run assessment.

## Reviewed Artifacts

- `python/experiments/VAL-001/scope.md`
- `python/experiments/VAL-001/analysis-plan.md`
- `python/experiments/VAL-001/code/run_experiment.py`

## What Changed Since rev. 1

- **No-look-ahead** is now tested by **prefix stability** (`generate(source[:k])`
  must be an exact prefix of `generate(source)`), which compares two different
  inputs, instead of the previous batch-vs-streaming replay that re-ran the same
  loop and therefore could not fail. Determinism is checked separately.
- **Resampling** is validated against an **independent pandas oracle** plus a
  hand-anchored golden fixture, replacing the prior reimplementation of the
  production bucket formula.
- **Negative controls** were added: injected look-ahead, future/unmapped/shifted
  timestamps, corrupted real prices, corrupted/dropped resample rows, and a
  perturbed regeneration. Each must be detected; an undetected control is a FAIL.
- Comparisons are **vectorised** (Polars joins / `equals`, pandas C-resample);
  look-ahead and determinism probes use a bounded leading window instead of
  pure-Python million-row loops.
- 1-minute, 15-minute, and 60-minute chart builds are all retained.

Two latent defects (present in rev. 1, never caught because governance is a
static review) were found and fixed during pre-run verification on synthetic
data:

1. **Datetime-unit mismatch** — chart generators emit microsecond timestamps
   (built from Python `datetime`) while Parquet bars load as nanoseconds; the
   rev. 1 alignment joins would have raised `SchemaError` on the real data.
   Fixed by normalising all cross-compared frames to one canonical unit
   (`to_canonical_time`).
2. **`SourceCount` check** — rev. 1 flagged `SourceCount <= 0`, but a value of 0
   is legitimate for a same-source duplicate Renko brick. Replaced with
   non-negativity plus a "first event per `SourceCloseTime` must be >= 1" check,
   which passes for correct generators and would have FAILed real volatile data
   under the old rule.

## Scope Review

- Single question: PASS. Still one question — whether the data architecture
  preserves temporal alignment with no look-ahead. Negative controls strengthen
  the same question rather than adding a new one.
- Data boundaries: PASS. Instruments, timeframes (1/15/60), chart types, and
  generator parameters are explicit.
- Global holdout: PASS. First-70% analysis slice only; final 30% never collected.
- Event denominators: PASS. Emitted rows counted; same-source duplicates and the
  `SourceCount == 0` semantics are documented and not silently deduplicated.
- Real-price discipline: PASS. No P&L, returns, stops, or targets in scope.
- Detection power: PASS. Scope now requires every negative control to be
  detected, with an undetected control treated as a FAIL.
- Checkpoint alignment: PASS with note. No active checkpoint; framed as a
  pre-thesis architecture-readiness gate.

## Analysis Plan Review

- Method choice: PASS. Prefix stability is the operational definition of
  no-look-ahead; the pandas oracle and golden fixture are independent ground
  truth; negative controls justify the detection-power claim. Each method states
  why, the simpler alternative considered, and assumptions.
- Statistical assumptions: PASS. No parametric, stationarity, normality, or
  i.i.d. assumptions. The periods 15/60 dividing the day evenly is stated and is
  confirmed by the golden fixture and zero oracle disagreement on clean data.
- Cross-view alignment: PASS. `CloseTime` for time bars and resamples,
  `SourceCloseTime` for Line Break and Renko; no bar-index comparisons.
- Look-ahead prevention: PASS. Prefix stability on a bounded leading window is
  justified by the structural nature of the property; full-output per-row
  alignment is still checked on the entire generated output.
- Complexity budget: PASS. 0 statistical tests, 2 plots, 0 new code modules. The
  pandas oracle and negative controls are deterministic checks, not statistical
  tests, and live inside the experiment script (no new `python/src` module).

## Implementation Review

- Plan compliance: PASS. Inventory, base checks, oracle-based resample checks,
  chart alignment, prefix-stability + determinism, negative controls, golden
  fixture, result tables, and two bounded plots are all implemented.
- Holdout exclusion: PASS. `scan.sort("CloseTime").slice(0, analysis_rows)
  .collect()` then `to_canonical_time`; derived views generated only from that
  slice. No code path reads beyond the 70% cutoff.
- Look-ahead prevention: PASS. Prefix stability compares full vs prefix
  generations; all `SourceCloseTime`/`CloseTime` comparisons are timestamp-based.
- Detection power: PASS. Eight negative controls run on a deterministic synthetic
  series; all were detected during verification (see Static Checks).
- Import side effects: PASS. Output directories created in `main()`/orchestration.
- Plot memory: PASS. Plots consume aggregated status and density summaries; the
  full generated chart is produced once and reused for alignment and density.
- Logging/output: PASS. Concise `logging`; helpers return data.
- Duplicate-source events: PASS. Counted and reported, not deduplicated;
  `SourceCount == 0` handled correctly.
- Edge cases: PASS. Empty charts yield INCONCLUSIVE via zero denominators;
  oracle/anti-joins handle empty frames; NaN-free OHLC checks are explicit.
- Static checks: PASS. `ruff check` clean; `py_compile` clean; `xen` package
  unit tests pass (8/8). Synthetic verification: pandas oracle vs `aggregate_ohlc`
  produced zero disagreement on clean data; the golden fixture passed; all eight
  negative controls were detected; a full synthetic instrument pass produced 92
  PASS / 0 FAIL with the only INCONCLUSIVE rows being a 60-minute Renko ATR
  warm-up artifact that does not occur at real 60-minute data volume. The
  generated `__pycache__` was removed and no `results/` files were created.

## Code-Standards Self-Check

- Organization: PASS. Imports → path setup → constants → dataclasses → small
  helpers → pure checks → loading → orchestration → negative controls → output →
  `main()`.
- Lazy loading and holdout exclusion: PASS.
- Bounded plotting/data conversion: PASS.
- Concise logging/output: PASS.
- Zero-baseline handling: PASS. No percentage-improvement or zero-baseline ratio.
- Temporal alignment rules: PASS. Timestamp-based throughout; canonical-unit
  normalisation documented.
- Synthetic-price discipline: PASS. No returns or P&L from any prices.
- Duplicate-source event denominators: PASS.
- Magic numbers: PASS with note. `PREFIX_WINDOW_ROWS`, `PREFIX_FRACTIONS`, and
  `DETERMINISM_ROWS` are documented harness bounds (structural properties are
  size-independent), not data-derived thresholds.

## Note for Execution

The run is generation-bound (it generates each chart type once over the full
1-minute analysis slice for four instruments, plus bounded prefix/determinism
probes), so expect a runtime on the order of a few minutes rather than a quick
check.
