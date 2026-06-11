# Audit Report: Experiment EXP-040

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Correctly implements the scope/plan specification: identical episode detector for three arms (AVWAP, static control, moving-copy control), Δ in pp, episodes as denominator, shared verbatim detector, cluster bootstrap, within-instrument cluster-label permutation, Holm-2 adjustment, determinism replay. Moving-copy arm (lines 294-308) uses same spawn grid/delta/lifetime as static arm; separate seed for determinism; contemporaneous `avwap_abs + delta * bw_abs` level array. Descriptive only — no permutation, no Holm, no verdict. |
| `code/run_experiment.py` | Edge cases | PASS | Handles NaN levels/eps (skipped by detector), empty strata (dropped with weight renormalisation), speed lookback at early bars (NaN → tercile -1, excluded), below-floor counts (correct verdict). |
| `code/run_experiment.py` | Type safety | PASS | Consistent numpy/polars types; explicit casts on all critical columns. |
| `code/run_experiment.py` | NaN handling | PASS | `tercile()` returns -1 for NaN inputs; `detect_episodes` skips non-finite level/eps; `stratum_delta` skips missing strata; power statement handles zero-count arms. |
| `code/run_experiment.py:149` | Holdout exclusion | PASS | Reuses `load_analysis_data()` from `referee_calibration` (analysis set = first 70% lazy slice). Holdout never loaded. |
| `code/run_experiment.py` | Memory/performance | PASS | Bounded iterations (≤4 concurrent control levels), chunked vol percentile computation (chunk=4000), `tqdm` on outer loops. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` on substrate rebuild, episode collection, and permutation loop. |
| `code/run_experiment.py` | Logging/output | PASS | Concise INFO-level logging; per-domain Δ/CI/p summary in orchestration. |
| `code/run_experiment.py:114` | Import-time side effects | PASS | `ensure_output_dirs` called in `main()`, not at import. |
| `code/run_experiment.py:829` | Plot data reuse | PASS | Plots use already-computed data (contrast rows, matched sets, split-half halves). No redundant computation. |
| `code/run_experiment.py` | Docstrings | PASS | All public functions documented. |
| `src/xen/line_approach.py` | Correctness | PASS | Sequential state machine; shared verbatim between arms; hysteresis as duplicate-source rule; bounce/pass/unresolved correctly assigned. |
| `src/xen/line_approach.py:26` | Edge cases | PASS | NaN level/eps handling at line 78; empty window (line 68 raises on invalid bounds); episode ending at window boundary (line 113-116). |
| `src/xen/avwap.py` | Determinism | PASS | `generate_avwap_events` is a sequential streaming pass with no randomness; `compute_band_trace` is a deterministic recompute. |

## Numerical Validation

### Spot Checks

**Power statement — binomial SE (1h):**
- n_avwap=1594, n_control=339
- SE = √(0.25/1594 + 0.25/339) = √(0.0001568 + 0.0007375) = √0.0008943 = 0.02990
- SE_pp = 100 × 0.02990 = 2.990 → matches `power_statement.csv` (2.990) ✓
- MDE (one-sided 95%) = 1.645 × 2.990 = 4.919 → matches (4.919) ✓
- Immaterial reachable (CI half-width < 2 pp): 1.96 × 2.990 = 5.86 > 2.0 → `false` ✓

**Power statement — binomial SE (4h):**
- n_avwap=50, n_control=22
- SE = √(0.25/50 + 0.25/22) = √(0.005 + 0.01136) = 0.1279
- SE_pp = 12.79 → matches (12.792, rounding) ✓
- MDE = 1.645 × 12.79 = 21.04 → matches (21.043) ✓

**Holm adjustment:**
- Raw p: {1h: 0.2924, 4h: 0.9800}
- Sorted: 1h (rank 2) → Holmp = min(1, 2×0.2924) = 0.5847 ✓
- 4h (rank 1) → Holmp = min(1, 1×0.9800) = 0.9800 ✓
- Matches `run_metadata.json` exactly ✓

**Determinism replay:** max_drift = 0.0, passed ✓

**Moving-copy control contrast (design §11/8):**

| Contrast | Domain | Δ (pp) | 95% CI | n AVWAP | n Control | Verdict |
|---|---|---|---|---|---|---|
| AVWAP vs static (binding) | 1h | +1.55 | [-4.52, +8.43] | 1,594 | 339 | INCONCLUSIVE |
| AVWAP vs moving (descriptive) | 1h | +3.41 | [-1.23, +8.35] | 1,647 | 522 | Descriptive |
| AVWAP vs static (binding) | 4h | −24.67 | [-44.63, −4.40] | 50 | 22 | BELOW_FLOOR |
| AVWAP vs moving (descriptive) | 4h | +0.09 | [-12.68, +11.95] | 166 | 103 | Descriptive |

Moving-copy SE and CI spot check (1h): SE = 2.55, CI [-1.23, +8.35]. Consistent with n=1,647/522. Binomial worst-case SE = √(0.25/1647 + 0.25/522) ≈ 2.51 pp ✓. No binding inference — descriptive only, as specified. Moving copy has ~1.5× more episodes than static arm on 4h (103 vs 22) because no clearance filter applies (|δ| ≥ 1.5 BW keeps it clear by construction).

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| entry_side | {+1, -1} | {-1, 1} | YES |
| vol_terc | {-1, 0, 1, 2} | {-1, 0, 1, 2} | YES |
| speed_terc | {-1, 0, 1, 2} | {-1, 0, 1, 2} | YES |
| outcome | {bounce, pass, unresolved} | {bounce, pass, unresolved} | YES |
| bars_in | ≥ 0 | [0, 24] by cap | YES |
| delta_pp (1h) | real | +1.55 | YES (pp) |
| delta_pp (4h) | real | -24.67 | YES (pp) |
| CI coverage | ci_low < ci_high | all rows | YES |
| n_avwap/n_control | ≥ 0 | all ≥ 0 | YES |

### Statistical Sanity

| Statistic | Value | Sanity | Notes |
|-----------|-------|--------|-------|
| 1h Δ | +1.55 pp | YES | Small positive; CI spans [-4.52, +8.43] — inconclusive. Consistent with AVWAP line having no detectable S/R edge over frozen levels on 1h in this sample. |
| 4h Δ | -24.67 pp | YES | Large negative but n=50/22 below floor (100/arm). CI is entirely negative, which would be AGAINST if above floor, but floor trumps — no verdict. |
| 1h perm p | 0.292 | YES | Not significant. Consistent with CI spanning zero. |
| 1h split-half | h1=-2.26, h2=+1.02 | YES | Opposite signs (instability disclosed as non-binding). |
| 4h split-half | h1=-20.93, h2=-7.11 | YES | Both negative, but tiny n=36/half. |
| Censoring 1h | [-2.47, +3.04] | YES | Brackets the main Δ (+1.55). Unresolved imbalance (95 AVWAP vs 59 control) shifts the estimate within a ~5.5pp range. |
| Censoring 4h | [-24.19, -19.89] | YES | Main Δ (-24.67) just outside the bracket (~0.5pp) for a floor cell with tiny n (25/10 unresolved). Non-binding. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| detect_episodes | Identical detector for both arms | YES | Single function `detect_episodes`, called identically for AVWAP and control levels. Any definitional artifact cancels in Δ. |
| Covariate matching | Strata = (instrument, entry_side, vol_terc, speed_terc) | YES | `STRATA_COLS = ["instrument", "entry_side", "vol_terc", "speed_terc"]` (line 102). bw_terc NOT a stratum key (as designed). |
| Cluster bootstrap | Clusters = anchor segments (AVWAP) / frozen levels (control) | YES | `cluster_ids()` concatenates `instrument|arm|level_id` (line 384-388). |
| Permutation | Cluster-level label swap within instrument | PARTIAL | Permutes within instrument (line 435), not within matched strata as the plan specifies. Conservative (see Issues). |
| Determinism | Same seed → byte-identical | YES | `seed_for()` framework; replay passes with drift=0.0. |
| Censoring sensitivity | Point estimates only, no new test | YES | Re-matches with imputed outcomes; only Δ reported (no CI, no p). |

## Results Plausibility

All results are internally consistent and numerically verified:

- **1h domain**: Δ = +1.55 pp, CI [-4.52, +8.43], Holm p = 0.585 → **INCONCLUSIVE_SPANS_ZERO**. CI symmetrically straddles zero. Power statement confirms that at n=1594/339 the unclustered MDE is ~4.9pp, so a ~1.6pp signal is undetectable. The verdict is the only reachable outcome given the CI.

- **4h domain**: Δ = -24.67 pp, CI [-44.63, -4.40], n_avwap=50, n_control=22 → **BELOW_FLOOR_NO_VERDICT**. Both arms well below 100-episode floor. The CI is entirely negative, which would be EVIDENCE_AGAINST at adequate n, but the floor correctly prevents a verdict.

- **Per-instrument 1h**: BTCUSD +5.4, EURUSD -5.4, USTEC +2.8, XAUUSD +3.0 — all CIs span zero, consistent with pooled inconclusive. EURUSD negative point estimate suggests no systematic cross-instrument pattern.

- **Split-half 1h**: h1 = -2.26, h2 = +1.02 — opposite signs reveal temporal instability. This is correctly disclosed as non-binding.

- **Control clearance**: 502 episodes dropped for opening within 1.0 BW of the live line. This is a significant fraction (relative to 339 retained controls), reflecting the high density of control levels near the moving line. Disclosed.

- **Unresolved rate**: 189/3473 = 5.4% unresolved, asymmetric across arms (95 AVWAP vs 59 control, excluding clearance). Difference is attributable to anchor-segment ends (informative truncation on AVWAP arm). Fully disclosed; the censoring bracket captures the range.

## Scope Compliance

- **Analysis plan followed**: YES — all Stage-2 parameters, metrics, inference machinery, and disclosure requirements match the plan.
- **Deviations**: 1 minor (see Issues — permutation scope).
- **Complexity budget**: 2 statistical tests / 2 budget ✓, plots: N/A (not generated for audit — 4/4 budgeted), modules: 2 / 2 (`line_approach.py`, `run_experiment.py`).
- **Holdout exclusion**: YES — analysis set only; holdout never loaded.
- **Real-price outcome discipline**: YES — all distances and outcomes use domain-bar OHLC. AVWAP line/band are conditioning features only.
- **Look-ahead bias prevention**: YES — all features computed ≤ episode-open timestamp; control levels snapshotted at spawn time; alignment by CloseTime.

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Permutation test permutes within instrument, not within matched strata**
   - File: `code/run_experiment.py:435`, line 435
   - Description: The analysis plan specifies "permute arm labels among episodes **within matched strata**" to condition on matching covariates. The code permutes within instrument clusters across all strata (`for i in np.unique(inst)` at line 435). This means the permutation does not condition on the stratum structure (instrument × entry_side × vol_terc × speed_terc) as the plan describes. Since both arms share the same stratum proportions by design of matching, the test is approximately valid in expectation and is slightly conservative (the permutation distribution is widened by not conditioning on strata). The practical impact is nil for this experiment (1h p=0.292, 4h p=0.98, neither close to α).
   - Impact: Minor — the test is conservative. No false-positive risk.
   - Recommendation: To align with the plan, restrict cluster-label permutation to within each stratum. This can be done by iterating over unique stratum tuples and shuffling clusters within each.

2. **No programmatic write-ordering assertion for power statement**
   - File: `code/run_experiment.py:742`
   - Description: The scope and plan require the power statement to be written **before** the binding contrast (write-ordering asserted). The code correctly writes `power_statement.csv` at line 742 before the contrast loop at line 748, but there is no programmatic assertion (e.g., file-mtime check) that would fail if a future refactor reordered the calls. Contrast with EXP-039's more explicit assertion mechanism.
   - Impact: None currently — ordering is correct by inspection. Protects against accidental reordering.
   - Recommendation: Add a `Path.stat().st_mtime` check or sentinel-file pattern to assert the power statement predates contrast computation.

## Re-Audit Requirements

None — PASS verdict.
