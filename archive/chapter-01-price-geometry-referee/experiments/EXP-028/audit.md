# Audit Report: Experiment EXP-028

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 3

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | PRIMARY construction correctly reuses EXP-022 symmetric own-exit lifetime; reconciliation asserts value-level against rebuilt frame; frozen inference hash-guarded. |
| `code/run_experiment.py` | Edge cases | PASS | Right-censored events excluded with diagnostic; degenerate controls (< MIN_CONTROLS) filtered; empty cell handling explicit. |
| `code/run_experiment.py` | Type safety | PASS | Functions typed; numpy/polars vectorized paths use explicit dtype casts. |
| `code/run_experiment.py` | NaN handling | PASS | `is_not_null` filter on lifetime_bps; `nansum`/`nanmean` in equity companion; Sortino degeneracy (no downside → NaN) explicit. |
| `code/run_experiment.py` | Holdout exclusion | PASS | Uses `xen.referee_calibration.load_analysis_data` — lazy scan sorted by CloseTime, first-70% slice. Alignment guard re-asserts every trigger/start/completion index is within the analysis frame. |
| `code/run_experiment.py` | Loader ordering | PASS | Lazy Polars scan sorts by `CloseTime` before slicing. No full-dataset materialization before holdout cutoff. |
| `code/run_experiment.py` | Memory/performance | PASS | Lazy scan → 70% slice → domain rebuild. Event/control joins on EXP-022 keys, not row loops. Plotting on aggregated data. |
| `code/run_experiment.py` | Safe optimization | PASS | Per-cell reconciliation vectorized over events; no causal violation. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` on domain rebuild (outer file loop) and secondary placebo-null (outer draw loop). |
| `code/run_experiment.py` | Logging/output | PASS | Concise INFO-level; structured metadata written to `run_metadata.json`. |
| `code/run_experiment.py` | Organization/import side effects | PASS | `ensure_output_dirs()` called in `main()`; no mkdir at import time. Imports → path → constants → helpers → computation → plotting → orchestration. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots use already-computed result dicts and the PRIMARY excess table; no heavy reloads. |
| `code/run_experiment.py` | Docstrings | PASS | Public functions have Parameters and Returns sections. |
| `code/event_method.py` | Correctness | PASS | Frozen EXP-027 inference tail — hash-guarded against source drift. `nearest_controls` vectorized two-pointer verified by equivalence guard. |
| `code/event_method.py` | Frozen integrity | PASS | `verify_frozen_inference` SHA-256 hashes named function sources vs EXP-027; mismatch raises `FROZEN_INFERENCE_MODIFIED`. |

### Loader file selection

`list_timebar_files` returns all sorted timebar Parquet files. The `build_frames` loop iterates over all files and relies on dict-key dedup (last per instrument wins) to select one file per instrument. This matches the EXP-020/022 convention but depends on sort order. With one production file per instrument this is fine; with multiple files, the lexicographically-last name determines the selection (which corresponds to the chronologically-latest given ISO date encoding). Not a correctness issue — the alignment guard would catch a wrong file immediately.

## Numerical Validation

### Spot Check — 5m PRIMARY effect

```
PRIMARY 5m: n=12795 events (4 instruments), effect=5.78 bps
CI [5.39, 6.13], holm_p=0.003

EXP-021 reference fixed-horizon (h=3): +3.81 bps
EXP-027 calibrated method MDE (h=3, 5m): 1 bps

PRIMARY lifetime effect (5.78 bps) > EXP-021 fixed-horizon (3.81 bps)
as expected: lifetime captures the full hold, not just a 3-bar window.
```

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| PRIMARY effect_bps | ℝ | [5.78, 69.02] | YES — positive, domain magnitude increasing 5m < 1h < 4h (consistent with EXP-021/022). |
| PRIMARY CI | CI_low > 0 | [5.39, 46.84] | YES — all lower bounds above zero. |
| Holm p | [0, 1] | 0.003 all domains | YES — below α=0.05. |
| n_events per domain | ≥ 30 | [187, 12795] | YES — all reportable. |
| Pyramid fraction | (0, 1) | 0.49–0.53 | YES — ~50% as in EXP-020. |
| Secondary FPR (1h) | ≤ 0.05 | 0.03 | YES — calibrated. |
| Secondary FPR (5m) | N/A (uncalibrated) | 1.0 | Expected — asymmetric construction biased positive on 5m. |
| Secondary FPR (4h) | N/A (uncalibrated) | 0.26 | Expected — thin events + asymmetric bias. |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| 5m PRIMARY effect | +5.78 bps | YES | Event-level excess over same-exit matched control. Consistent with EXP-021 (+3.81 bps at h=3 fixed horizon) plus the additional lifetime hold return. |
| 1h PRIMARY effect | +23.38 bps | YES | Higher than EXP-021 (+9.14 bps at h=3) — lifetime captures band-target/trend-change completion returns that extend well beyond 3 bars. |
| 4h PRIMARY effect | +69.02 bps | YES | Much larger magnitude as expected on slower domain (longer hold periods, fewer but larger moves). |
| 5m equity advantage | +20107 bps | YES | Cumulative over 12795 events (~1.57 bps/event arithmetic advantage). Sum over analysis-set events. |
| 1h equity advantage | +5819 bps | YES | Cumulative over 924 events (~6.30 bps/event). |
| 4h equity advantage | +3755 bps | YES | Cumulative over 187 events (~20.08 bps/event). |
| Baseline negative terminal | -17493 to -3335 bps | YES | Controls placed at non-trigger regime bars with the same exit rule have no edge and drift negative over the analysis set — expected for random entries under the EXP-022 exit rule. |

## Scope Compliance

- Analysis plan followed: YES
- Deviations: None
- Complexity budget: 4 tests / 4 budgeted, 4 plots / 4 budgeted, 1 module / 1 budgeted
- Holdout exclusion verified: YES — lazy 70% slice + hard alignment guard asserts every trigger/start/completion index falls within the analysis frame.
- Dual gate discipline: PRIMARY is binding; SECONDARY correctly gated by placebo-null calibration.

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Loader file selection depends on sort-order dedup**
   - File: `code/run_experiment.py`, `list_timebar_files` at referee_calibration.py:105
   - Description: `build_frames` iterates all sorted files and keeps the last per instrument via dict-key overwrite. With the typical one-file-per-instrument layout this is harmless; the alignment guard (value-level Close/CloseTime check) would catch a wrong file.
   - Impact: None under current data layout.

2. **Secondary construction uses per-event Python row loop**
   - File: `code/run_experiment.py`, `build_secondary_excess` at line 524
   - Description: The secondary (non-binding, diagnostic) construction iterates events per cell via `iter_rows(named=True)` with inner calls to `EXP021.select_controls`. Event counts per cell are bounded (~3000 max on 5m) but this could be slow.
   - Impact: Non-binding diagnostic only. Acceptable given the diagnostic role; no `tqdm` on this loop (the secondary placebo-null outer draw loop has `tqdm` at line 556).

3. **Equity companion uses cumulative sums, not per-event rates**
   - File: `code/run_experiment.py`, `equity_companion` at line 683
   - Description: The companion reports cumulative terminal log-equity advantage (sum of per-event returns), not a per-event rate. The advantage values are large (+5819 to +20107 bps) because they accumulate over hundreds to thousands of events. The PRIMARY effect (per-event excess of instrument-averaged means) is the correct effect-size estimate.
   - Impact: Companion is non-gating by design. Read the PRIMARY effect for the effect size, the equity companion only for direction/consistency.

## Re-Audit Requirements

None. Verdict is PASS — no conditions for approval.
