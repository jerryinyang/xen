# Audit Report: Experiment EXP-052

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 3

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Deterministic two-pass replay; formulas, joins, searchsorted alignments, and MFE/MAE logic match scope. |
| `code/run_experiment.py` | Edge cases | PASS | Zero-moves, zero-haramis, n_signals=0, empty bootstrap, absent readiness map, non-chronological file all handled with defined return/exception. |
| `code/run_experiment.py` | Type safety | PASS | Public functions typed (`list[str]`, `np.ndarray`, etc); `# type: ignore` only on known-strict imports. |
| `code/run_experiment.py` | NaN handling | PASS | `np.isfinite` guards on all float paths; `np.errstate(invalid="ignore", divide="ignore")` around division; None explicit for empty cells. |
| `code/run_experiment.py` | Holdout exclusion | PASS | F01 prefix: `train_rows = int(int(total*0.7)*0.7)` file-order rows only — never sorts/collects the full file. `pl.scan_parquet(...).select(cols).slice(0, train_rows).collect()`. |
| `code/run_experiment.py` | Loader ordering | PASS | Lazy scan + slice before collect; sort-by-timestamp not applied before slice (by design — F01 convention). Hard-fail if the slice is not chronological. |
| `code/run_experiment.py` | Memory/performance | PASS | Column-pruned scan (7 cols); per-cell `del train_1m`; bootstrap batched (`BOOT_MAX_ELEMS=2M`); plots from per-cell scalars. |
| `code/run_experiment.py` | Safe optimization | PASS | Vectorized: rd assignment, N_event (rolling median), MFE/MAE (bounded forward window). Explicit loop kept for sequential first-touch fill scan. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` over instruments outer loop (line 934); helpers return data silently. |
| `code/run_experiment.py` | Logging/output | PASS | `LOGGER.info` for run summary only; no per-cell/per-event print. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Dirs created in `run()` (lines 925-926). `matplotlib.use("Agg")` before `pyplot`. |
| `code/run_experiment.py` | Plot data reuse | PASS | All plots from collected per-cell records (`_cell_matrix`, per-cell scalars); no reloads. |
| `code/run_experiment.py` | Docstrings | PASS | Module-level docstring (37 lines, full pipeline), public functions typed + documented; private helpers have inline comments. |
| `python/src/xen/confirm_entry.py` | Correctness | PASS | `assign_reversal_context` uses `searchsorted(..., side="right")-1` (correct for causal mapping); `evaluate_events` keeps sequential fill scan; MFE/MAE via `forward_excursion` on real prices. |
| `python/src/xen/confirm_entry.py` | Edge cases | PASS | Harami with no context (has_context=False), degenerate ref magnitude (<=0), zero-length forward window, empty qualifying set. |
| `python/src/xen/confirm_entry.py` | Determinism | PASS | Pure NumPy — no randomness; fully deterministic given same input arrays. |

## Numerical Validation

### Spot Checks

| Check | Formula | Expected | Actual | Pass? |
|-------|---------|----------|--------|-------|
| BTCUSD-5m exclusion sum | 2+5+0+37043 = 37050 | 37050 | 37050 | YES |
| EURUSD-5m exclusion sum | 5+5+1+28633 = 28644 | 28644 | 28644 | YES |
| XAUUSD-5m exclusion sum | 2+6+1+28014 = 28023 | 28023 | 28023 | YES |
| EURUSD-15m fill consistency | 3013-1 = 3012 | 3012 | 3012 | YES |
| BTCUSD-5m fill_rate | 10067/37043 | 0.27177 | 0.27177 | YES |
| US2000-2h fill_rate (max) | 485/1152 | 0.42101 | 0.42101 | YES |
| EURUSD-4h fill_rate | 217/575 | 0.37739 | 0.37739 | YES |
| EURUSD-5m DIRECT mmm_med (outcome_primary) | median((MFE-MAE)/ATR) | — | 0.03022 | YES |
| EURUSD-5m paired_delta (comparison_readout) | median(CONFIRM mmm) - median(DIRECT mmm) on paired set | — | -0.65014 | YES |

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| fill_rate | [0, 1] | [0.2718, 0.4210] | YES |
| paired_delta_mmm | ℝ (all expected negative per scope) | [-0.951, -0.346] | YES — **all 99 cells negative** |
| lead_direct_med | ≥ 1 | [3.0, 4.0] | YES |
| lead_confirm_med | ≥ 1, ≤ lead_direct | [2.0, 4.0] | YES |
| shift_sign | {positive, negative, flat} | negative (99/99) | YES |
| n_signals | ≥ 0, integer | [384, 30214] | YES |
| inv_event_wellformed | 0 | 0 (all 99 cells) | YES |
| inv_stop_fill | 0 | 0 (all 99 cells) | YES |
| inv_mfe_mae | 0 | 0 (all 99 cells) | YES |
| inv_fence | 0 | 0 (all 99 cells) | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| DIRECT `r` (secondary) | ≈ 0.50 across most cells | YES | Replicates EXP-049 null on a harami anchor; symmetric barrier geometry is ~random. |
| CONFIRM `r` (secondary) | ≈ 0.35 across most cells | YES | Consistent with negative paired delta; CONFIRM arm reduces favourable outcomes. |
| Median fill_rate | ~33% (27-42% range) | YES | Most haramis do NOT get confirmed before the ZigZag giveback; the `next_confirm_idx` window is tight. |
| Paired δ median(MFE-MAE)/ATR | −0.62 (range −0.95 to −0.35) | YES | Every cell shows CONFIRM worse than DIRECT; effect is systematic and large (0.35–0.95 ATR units). |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Moving-block bootstrap (MBB) | Within-block stationarity | PLAUSIBLE | Block length L = max(1, round(n^(1/3))) adapts to sample size; descriptive CIs only, no viability gate. |
| MBB: serial dependence | Adjacent events share residual dependence | REASONABLE | MFE/MAE on sequential harami events likely exhibits volatility clustering; block bootstrap is conservative. |
| ATR normalization | ATR(14) > 0 at entry bar | YES | Warmup guarantees ≥14 bars; invariant check passes on all cells (ATR ≤ 0 count = 0). |
| Two-pass determinism | `core1 == core2` (identical dicts) | YES | 99/99 cells deterministic. |

## Results Plausibility

Outputs are well within expected ranges. The fill rate (~27-42% median 33%) is plausible — most haramis are not confirmed before the ZigZag's own trend-change confirmation fires. Lead times (median 3 bars for both arms) are consistent with the fill window being bounded by `next_confirm_idx`. The universal negative shift (CONFIRM worse than DIRECT in every cell) is large in magnitude (median −0.62 ATR units) and directionally unanimous across all 17 instruments and 6 domains — a remarkably clean signal that CONFIRM entry systematically underperforms DIRECT entry on the gross excursion balance.

DIRECT median(MFE-MAE)/ATR centers near zero (consistent with EXP-049's `r ≈ 0.50` — no net edge in random-direction harami entries), while CONFIRM shifts the balance strongly adverse (median(MFE)/ATR drops ~0.3 while median(MAE)/ATR rises ~0.3). The secondary symmetric-barrier `r` corroborates: DIRECT `r ≈ 0.50` (null), CONFIRM `r ≈ 0.35` (adverse bias).

All 99 cells are paired-reportable (n_paired range 108–10067), well above the POWER_FLOOR=30 threshold.

## Scope Compliance

- Analysis plan followed: **YES**
- Deviations: None. The optional position-in-move secondary (marked optional in plan) was omitted — no binding item dropped.
- Complexity budget:
  - CI estimations: **2 / 2** (per-arm median(MFE-MAE) MBB + paired delta MBB; secondary r reuses `block_bootstrap_ci` as planned)
  - Plots: **4 / 4** (fill_rate heatmap, lead DIRECT vs CONFIRM, per-arm MFE/MAE, paired-Δ vs fill_rate scatter)
  - New modules: **1 / 1** (`python/src/xen/confirm_entry.py`)
- Holdout exclusion verified: **YES** — F01 first-49% prefix; no full-file sort/collect; TRAIN fence enforced per bar/move/event.
- Determinism: **PASS** — 0 non-deterministic cells.
- Systematic invariant failures: **0** — all 4 battery items pass on all cells.

## Issues

### Critical

None.

### Warning

None.

### Info

1. **`atr_c` computation uses index 0 sentinel for non-fills.** See `code/run_experiment.py:366`: `atr_c = np.where(fill, atr[np.where(fill, trigger, 0)], np.nan)`. The inner `np.where(fill, trigger, 0)` reads `atr[0]` for non-fill rows, but the outer `np.where(fill, ..., np.nan)` masks those entries. Correct (the NaN mask prevents the sentinel value from propagating), but fragile — an edit that removed the outer `where` without adjusting the inner would introduce an out-of-bounds-index bug. A safer alternative: `atr_c = np.full(atr_d.shape, np.nan); atr_c[fill] = atr[trigger[fill]]`.

2. **DE30 coverage caveat.** DE30 broker history ends 2026-01-16; its train end is 2024-06-28 (earliest across all instruments). Consistently applied per the DE30_DISCLOSURE string. Reported counts derive from DE30's own timeline and are not span-comparable. This is an accepted limitation, not a bug.

3. **Forward completed-move reference (next_confirm_idx).** The CONFIRM window endpoint and lead metrics use the next ZigZag confirmation as a descriptive boundary. This is the pre-approved completed-move allowance, declared in scope §Look-ahead, capped by the causal `s + N_event`, and used for no tradable decision. Verified: fence invariant passes on all 99 cells.

## Re-Audit Requirements

None. Verdict is PASS with no conditional items.
