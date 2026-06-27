# Audit Report: EXP-030 — Cost-Bearing Tradability of the Faithful Selective AVWAP Strategy

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | All formulas, joins, and aggregation match the analysis plan. The binding absolute net metric (`lifetime_bps − RT_i`) is correctly distinguished from the non-binding attribution companion. |
| `code/run_experiment.py` | Edge cases | PASS | `<3` reportable instruments → UNDER_POWERED; empty cells skipped; right-censored events excluded via `reportable_event` filter (n=2, recorded). |
| `code/run_experiment.py` | Type safety | PASS | Type hints on all public functions. Polars/NumPy types used correctly. |
| `code/run_experiment.py` | NaN handling | PASS | Explicit `is_not_null()` filter on `lifetime_bps` before any computation (line 271). Plot values None-guarded. |
| `code/run_experiment.py` | Holdout exclusion | PASS | No Parquet load of time bars. All inputs are EXP-022 first-70% rows. Row-set fence (line 438-443) asserts event counts match EXP-028 first-70% exactly. |
| `code/run_experiment.py` | Loader ordering | PASS | N/A — no new time-bar loads. Inherited temporal ordering from EXP-022. |
| `code/run_experiment.py` | Memory/performance | PASS | Pure in-memory overlay on a single CSV; no heavy data loads. Per-domain loops ≤12 iterations with vectorized bootstrap. |
| `code/run_experiment.py` | Safe optimization | PASS | Computation is sequential arithmetic on CSV columns. No vectorization shortcuts that alter semantics. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` intentionally omitted (governance info note, §73-76): loops are ≤12 fast iterations. Acceptable. |
| `code/run_experiment.py` | Logging/output | PASS | Concise `LOGGER.info` with section-level progress. Functions return data, not print. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Clear sections (I/O helpers, frozen inference guard, dependency gate, event table, computation, inference, integrity guards, diagnostics, verdict assembly, plotting, save, orchestration). No output directory creation at import time. Output dirs created in `main()`. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots use already-computed aggregated results (cons_res, base_res, gross_res, attr_cons, per_inst). No repeated data loads. |
| `code/run_experiment.py` | Docstrings | PASS | All public functions have docstrings with Parameters and Returns sections. |

## Numerical Validation

### Spot Check: net = gross_abs − mean_inst(RT_cons)

The binding net metric per domain is `mean(lifetime_bps − RT_cons_i)`, which equals `mean(lifetime_bps) − mean_inst(RT_cons)`. Verified:

| Domain | `gross_abs` (bps) | `mean_inst(RT_cons)` (bps) | Expected `net_cons` | Actual `net_cons` | Diff |
|--------|-------------------|---------------------------|--------------------|-------------------|------|
| 5m | +0.764 | 7.5 | −6.736 | −6.736 | 0.00 |
| 1h | +1.458 | 7.5 | −6.042 | −6.042 | 8.88e−16 |
| 4h | +10.100 | 7.5 | +2.600 | +2.600 | −1.78e−15 |

Commute check: bootstrap distributions for gross vs net_cons differ by exactly mean_inst(RT_cons) at machine epsilon (max deviation 7.1e−15 bps). ✓

### Spot Check: Attribution companion

The non-binding net matched-control excess = `gross_excess − RT_i`, verified at the domain level as `exp028_excess − mean_inst(RT_cons)`:

| Domain | EXP-028 excess (bps) | `mean_inst(RT_cons)` (bps) | Expected | Actual (CSV) | Diff |
|--------|---------------------|---------------------------|----------|-------------|------|
| 5m | +5.779 | 7.5 | −1.721 | −1.721 | 0.00 |
| 1h | +23.384 | 7.5 | +15.884 | +15.884 | 0.00 |
| 4h | +69.016 | 7.5 | +61.516 | +61.516 | 0.00 |

### Reconciliation Guard

The recomputed gross matched-control excess reproduces EXP-028 `event_level_results.csv` to exactly 0.00 bps in all 3 domains. Event counts match: 5m=12795, 1h=924, 4h=187. ✓

### Range Checks

| Metric | Expected | Actual | Pass? |
|--------|----------|--------|-------|
| `net_cons` 5m | < 0 (gross < RT) | −6.74 | YES |
| `net_cons` 1h | < 0 (gross < RT) | −6.04 | YES |
| `net_cons` 4h | spans 0 (gross > RT but wide CI) | [+2.60, CI: −14.87, +19.28] | YES |
| EURUSD-4h `net_cons_ci_low` | > 0 (low-cost instrument) | +2.67 | YES |
| BTCUSD-4h `net_cons_ci_low` | < 0 (high-cost instrument) | −72.89 | YES |
| `determinism_replay_pass` | true | true | YES |

### Statistical Sanity

| Statistic | Value | Sensible? | Notes |
|-----------|-------|-----------|-------|
| 5m gross absolute | +0.76 bps | YES | Previously ~0 per EXP-024 finding; the small positive is consistent with the gross excess being 5.78 bps after control-differencing removes a ~5 bps negative control mean. |
| 1h gross absolute | +1.46 bps | YES | Small positive; similar explanation to 5m — the gross excess (23.38 bps) is mostly a control-discount effect. |
| 4h gross absolute | +10.10 bps | YES | More substantial; the excess (69.02 bps) is largely driven by the event leg. |
| 5m CONS net CI | entirely < 0 | YES | gross(0.76) << mean_RT(7.5); 5m clearly NOT_TRADABLE |
| 1h CONS net CI | entirely < 0 | YES | gross(1.46) << mean_RT(7.5); similarly clear |
| 4h CONS net CI | spans 0 | YES | gross(10.10) > mean_RT(7.5) but n=187 → wide CI; inconclusive as expected per scope |
| 4h seed robustness CI(high) | stable positive across seeds | YES | CI_high always > 0 across 8 seeds |
| EURUSD-4h net_cons_vs_nonbinding | true | YES | Low-cost + high gross absolute at 4h; independently consistent result |
| Non-binding companion 1h/4h FOR | EVIDENCE_FOR | YES | Measures a different estimand (excess minus cost, not absolute); the non-binding companion is correctly labelled and not promoted to a verdict. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Regime-cluster bootstrap | Events are clustered by regime; within-regime dependence is handled by cluster resampling | YES | Frozen EXP-027/028 machinery, unchanged and hash-verified. The commute check (bootstrap distributions match net = gross − RT elementwise) confirms correct stratification. |
| Equal-weight cross-instrument domain mean | Each instrument contributes equally to the domain verdict | YES | Faithful to the scope and EXP-028 PRIMARY aggregation. Per-instrument breakout (net_by_instrument.csv) exposes within-domain heterogeneity — the caveat is explicitly documented in run_metadata. |
| Bootstrap 95% CI coverage | ~95% coverage of the true effect | YES (inherited) | FPR/coverage was calibrated for the matched-control excess in EXP-027; the absolute estimand has wider CIs (no control-differencing), making coverage if anything conservative. The one-sided bootstrap p is a CI-equivalent annotation. |

## Results Plausibility

All results follow logically from the predeclared cost model and data:

- **5m (EVIDENCE_AGAINST)**: gross absolute +0.76 bps ≪ mean_inst(RT_cons)=7.5 bps. Every instrument's RT_cons exceeds its gross per-event expectancy. This is the expected stress case per scope (−5m net-negative is an expected, informative outcome). The CI is tight (half-width 0.33 bps) due to n=12795, confirming the negative is measured precisely.

- **1h (EVIDENCE_AGAINST)**: gross absolute +1.46 bps ≪ mean_inst(RT_cons)=7.5 bps. Wider CI (half-width 4.75 bps, n=924) but still entirely below 0. BTCUSD (16 bps RT) dominates the equal-weight mean.

- **4h (INCONCLUSIVE_SPANS_ZERO)**: gross absolute +10.10 bps > mean_inst(RT_cons)=7.5 bps, giving a positive point estimate (+2.60 bps). But the CI is wide (half-width ~17 bps, n=187) and spans 0. EURUSD-4h individually shows a CI entirely above 0 (headroom +12.38 bps), but the equal-weight aggregation is dominated by the 4 other instruments' RT_cons.

- **EURUSD-4h**: the one cell where net_cons CI excludes zero (gross_abs=15.38 > RT_cons=3.0). This is descriptive, not binding — uncontrolled multiplicity.

- **Attribution companion**: the non-binding net matched-control excess (which shifts the EXP-028 excess by RT) is EVIDENCE_FOR on 1h/4h. This demonstrates the absolute-vs-relative distinction: the matched-control structure removes a negative control discount, while the absolute P&L must carry that discount.

## Scope Compliance

- **Analysis plan followed**: YES — all 7 steps implemented faithfully. Binding metric = absolute net, not excess-minus-cost.
- **Deviations**: The analysis plan's Step-5 `per_instrument_net` was extended with `headroom_cons_bps` and `net_cons_survives_nonbinding` columns (F01 disclosure). These are explicitly non-binding and documented in `run_metadata.json` review_notes. The extension is allowed per the governance revision cycle and does not change any binding metric, decision rule, or scope.
- **Complexity budget**: tests 1/3 (1 regime-cluster bootstrap reused for BASE/per-inst/companion as diagnostic applications); plots 4/4; modules 1/1. ✓
- **Holdout exclusion verified**: YES — inherited fence; all rows are EXP-022 first-70% outputs; event counts match EXP-028 first-70% exactly; no new bar load.
- **Frozen inference hash**: verified against pinned EXP-027 hash `e50873d12a9f68d9` (run_metadata records PASS).
- **Dependency gate**: EXP-028 EVAL_SUPPORTED, EXP-029 CONSISTENT confirmed in run_metadata.
- **Cost table frozen**: operator-confirmed, content hash `ae0c61b87b8e676e` recorded; no post-result revision.
- **Determinism**: same-seed replay PASS; seed robustness (8 seeds) confirms CI stability.

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Frozen inference hash self-consistency bound**
   - Description: The `FROZEN_TAIL_EXPECTED_HASH` was computed from EXP-027's `event_method.py` at the time of the EXP-027/028 close-out (git commit `5387a3b`). The guard (`verify_frozen_inference`) reloads that same file and compares against the pin. A modification to `event_method.py` after the pin was set would be caught — which is the intended freeze check. The guard was corrected from a self-comparing reload (F02 fix) to use the pinned hash, which is a binding freeze check. No issues found: the run metadata shows `frozen_inference_hash == e50873d12a9f68d9 == expected_hash`.

## Re-Audit Requirements

None. PASS with no critical or warning issues. The audit confirms all integrity guards pass (reconciliation exact match, commute check at machine epsilon, frozen inference hash verified, determinism replay PASS, holdout fence structurally verified). Numerical outputs are internally consistent and match scope expectations.
