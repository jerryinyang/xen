# Audit Report: Experiment EXP-054

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | All correctness gates (reconciliation, monotonicity, determinism) passed at runtime; 0 METHOD_DEFECT. |
| `code/run_experiment.py` | Edge cases | PASS | Empty/zero-move cores handled via `_empty_core`/`_empty_geometry_dual`; zero-resolved cells produce `None` ratios, never 0/0. |
| `code/run_experiment.py` | Type safety | PASS | Type hints on all public functions. |
| `code/run_experiment.py` | NaN handling | PASS | Explicit `equal_nan=True` in determinism comparison; `_abs_diff` handles None/None and None/float explicitly; `qualifying_mask` filters finite exits. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_train_1m` reads only first `train_rows` file-order rows via `slice(0, train_rows)` with no full-file sort/collect; asserts CloseTime-sorted; domain bars fenced to `CloseTime <= train_end_epoch`. |
| `code/run_experiment.py` | Memory/performance | PASS | Lazy Polars scan with column projection; `del train_1m` per instrument; plots from collected per-cell summary only. |
| `code/run_experiment.py` | Safe optimization | PASS | Sequential resolvers kept explicit (their causal semantics are under test); `worstcase_exit_prices` vectorized only because it is a pure per-event lookup. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` on instrument loop (17 instruments at ~25s each). |
| `code/run_experiment.py` | Logging/output | PASS | Concise stdout summary; helpers return data rather than printing. |
| `code/run_experiment.py` | Organization | PASS | Imports → path → constants → I/O → helpers → plotting → orchestration → main(); VAL-001-style sectioning. |
| `code/run_experiment.py` | Import side effects | PASS | Output dirs created in `run()` only. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots from per-cell summary only; no reloads. |
| `code/run_experiment.py` | Docstrings | PASS | All public functions have docstrings with Parameters/Returns. |
| `code/run_experiment.py` | Linting | PASS | `ruff` clean, lines ≤ 100. |

## Numerical Validation

### Spot Checks

**Reconciliation accuracy** — all 99 member cells show `max_abs_diff = 0.0` between the re-computed worst-case leg and stored EXP-049 results for both G1 and G2 integer counts AND float CI bounds. Exact reproduction confirmed.

**Monotonicity** — all 99 cells pass: `resolved_P15 == resolved_wc`, `FAV_P15 >= FAV_wc`, `Δr >= 0` (within 1e-12 tolerance), reassigned set ⊆ tie set.

**Determinism** — all 99 cells pass two-pass frame-identical comparison.

**Viability status** — all 99 G1 cells show `BELOW_R` under both fill rules; 0 VIABLE. Matches EXP-049 baseline.

### Range Checks

| Metric | Expected | Actual | Pass? |
|--------|----------|--------|-------|
| `r` (G1, either rule) | [0.0, 1.0] | [0.454, 0.543] | YES |
| `Δr = r_P15 - r_wc` | ≥ 0 by construction | [0.0029, 0.0374] | YES |
| `dt_frac` | [0.0, 1.0] | [0.0029, 0.0794] | YES |
| `resolved` (G1) | ≥ 30 (else NOT_VIABLE_BY_POWER) | min 128, max 22172 | YES |
| `n_moves` | ≥ 0 | min 336 (DE30-4h) | YES |
| `e_median` (expectancy, ATR-normalised) | ℝ | [−0.263, 0.318] | YES |

### Statistical Sanity

| Statistic | Value | Reasonable? | Notes |
|-----------|-------|-------------|-------|
| P15 G1 VIABLE cells | 0/99 | YES | Identical to EXP-049; P11 not met. |
| P15 G2 VIABLE cells | 1/99 (USDCAD-2h) | YES | Single cell below P11 3-instrument threshold. |
| Median Δr (G1) | 0.0101 | YES | Consistent with low dt_frac (~2.1%). |
| Median dt_frac (G1) | 0.0212 | YES | Only ~2% of resolved events have any tie exposure. |
| TIE_BREAK_SENSITIVE cells | 0 | YES | No Δr ≥ 0.05 or viability flip anywhere. |

## Results Plausibility

All outputs are internally consistent and match expectations from the experimental design:

- The median `Δr ≈ 1%` is commensurate with the median tie exposure of ~2% (each reassigned tie moves one ADV to FAV, changing `r` by roughly `1/resolved` for a ~50/50 split).
- The `Δr` IQR (~0.005) is tight — the effect is uniform across instruments and domains.
- All 99 G1 cells are `BELOW_R` under P15 — identical to the worst-case baseline — confirming that the tie-break was not the cause of the null.
- The DE30 disclosure was verified runtime (TRAIN edge `2024-06-28` is well before the claimed `2026-01-16` broker end; `de30_disclosure_stale: false`).
- The BTCUSD caveat is recorded in metadata with the session-model limitation disclosed.

## Scope Compliance

- **Analysis plan followed**: YES — re-reads EXP-049 benchmark under P15 path-ordered fills; dual-fill resolution in one pass; all 4 correctness gates; bounded 4-plot budget.
- **Deviations**: None. The code was hardened between pre-execution review and execution with DE30 runtime verification, session-model caveat, and CSV schema checking — all consistent with scope intent.
- **Complexity budget**: 1 statistical method / 1 budgeted (regime-clustered bootstrap reused for r and median expectancy); 4 plots / 4 budgeted; 0 new modules / 0 budgeted.
- **Holdout exclusion verified**: YES — all 17 instruments loaded by file-order prefix only; domain bars fenced; forward windows clipped to TRAIN edge.

## Issues

### Info

1. **Code hardened between review and execution.** The version of `run_experiment.py` that produced results includes DE30 runtime verification (`verify_de30_disclosure`), a session-model microstructure caveat (`SESSION_MODEL_CAVEAT`), split reconciliation booleans (`int_match`/`float_match`), and a loud-failing `_write_csv` schema check — all improvements over the pre-execution-reviewed version. None affect analytical correctness; they improve diagnostics and documentation.

2. **G2 secondary shows 1 VIABLE cell (USDCAD-2h) under P15.** This is disclosed in `composition_readout.json` and does not meet the P11 threshold (≥5 cells over ≥3 instruments). It is a natural consequence of the G2 retracement geometry having a different power profile and does not affect the G1 binding conclusion.
