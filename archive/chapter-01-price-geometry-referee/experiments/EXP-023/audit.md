# Audit Report: Experiment EXP-023

**AVWAP Baseline Candidate Screen** (Phase 004, CF-AVWAP-001/HYP-004)
**Audited:** 2026-06-08 · **Run status:** `overall_status=REFUTED`, 0 blockers.

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 6

The screen ran end-to-end and produced a clean, internally consistent
Evidence-AGAINST result: 12/12 cTrader cells admitted, C# AVWAP transcription
smoke PASS on all three domains, and 0/12 suite passes (strict, ratified-loose,
revised-incremental). The metric book reproduces bit-exact under independent
recomputation. Holdout fence, same-feed reference identity, real-price
discipline, timestamp alignment, and the recent metric-book guard fix all verify
correct. Nothing blocks interpretation.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Suite-verdict, admission, same-feed, and metric-book logic match the plan; verified against emitted CSVs. |
| `code/run_experiment.py` | Edge cases | PASS | Empty frames (`read_optional_parquet`, `_entry_exit_pairs`), zero denominators (`successful_bounce_rate`, `_robust_ratio`, `_sharpe_diag`, `bounce_prevalence_per_bar`) all guarded. |
| `code/run_experiment.py` | Type safety | PASS | Type hints on public functions; dataclasses `Blockers`, `SuiteSettings`, `CellRun`. |
| `code/run_experiment.py` | NaN handling | PASS | Explicit `_safe_float`/`_is_finite_number`/`math.nan`; null treated as non-reportable per scope zero-baseline rule. |
| `code/run_experiment.py` | Holdout exclusion | PASS | No full-file load; emitted runs already fenced; fence re-asserted (`_fence_ok`); fixed-Parquet smoke requires a first-70%-marked source on both Python and C# sides. |
| `code/run_experiment.py` | Loader ordering | PASS | Positions sorted by `SourceCloseTime`; no holdout collection. |
| `code/run_experiment.py` | Memory/performance | PASS | `pl.scan_parquet` discovery; bounded plotting from collected frames; per-cell loop bounded by 12. |
| `code/run_experiment.py` | Safe optimization | PASS | No vectorization that alters membership/ordering/denominators; same-feed check and tie-break preserve causal semantics. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` over the 12-cell screen loop; helpers quiet. |
| `code/run_experiment.py` | Logging/output | PASS | Concise INFO logging; blockers surfaced as warnings and recorded in `run_metadata.json`. |
| `code/run_experiment.py` | Organization/import side effects | PASS | imports→constants→types→helpers→steps→plotting→orchestration→`main()`; dirs created only in `ensure_output_dirs()` from `main()`. |
| `code/run_experiment.py` | Plot data reuse | PASS (minor) | Plots reuse collected verdict/metric frames; `plot_model_vs_raw` recomputes returns from in-memory positions (Info 3). |
| `code/run_experiment.py` | Docstrings | PASS | Module + function docstrings present, including the post-fix rationale on `validate_metric_book`/`plot_risk_adjusted_heatmap`. |

## Numerical Validation

### Spot Checks

Independent recomputation of the BTCUSD/5m metric-book risk metrics from the
emitted `positions.parquet` (`returns_and_positions` + `cost_bps_for`):

| metric | recomputed | metric book | match |
|---|---|---|---|
| `model_net_bps` | −0.739562 | −0.739562 | ✓ |
| `raw_return_bps` | 0.084746 | 0.084746 | ✓ |
| `model_robust_ratio` | NaN | NaN | ✓ |
| `raw_robust_ratio` | 0.012579 | 0.012579 | ✓ |
| `model_sharpe_diag` | −0.159866 | −0.159866 | ✓ |
| `raw_sharpe_diag` | 0.005062 | 0.005062 | ✓ |

Mechanism confirmed: BTCUSD/5m is flat in **92.6%** of return rows → `median(net)=0`
→ `MAD(net)=0.0` → `model_robust_ratio` undefined (NaN). This is the scope's
"zero denominator → null/non-reportable, never a zero effect" case, correctly
excluded from the metric-book gate after the revision.

Diagnostic cross-consistency (`event_trade_diagnostics.csv` vs
`strategy_metric_book.csv`): long+short entries reconcile to `n_entries` for every
cell (e.g. BTCUSD/5m 2452+2468=4920; BTCUSD/4h 37+45=82; EURUSD/4h 31+29=60). ✓

### Range Checks

| Metric | Expected | Actual | Pass? |
|--------|----------|--------|-------|
| `Position` | {−1,0,+1} | enforced in `_validate_position_contract` | YES |
| `same_feed_ok` / `feed_max_abs_diff` | true / 0.0 | true / 0.0 (all 12) | YES |
| `n_reference_unaligned` | 0 | 0 (all 12) | YES |
| fence: max `SourceCloseTime` < `AnalysisEndUtc` | strictly | true (all 12, both candidate+reference) | YES |
| incremental `denominator_count` | > 0 | 155–15,951 | YES |
| `successful_bounce_rate` | (0,1) | 0.605–0.800 | YES |
| dependency manifest | all PASS | 34/34 PASS | YES |

### Statistical Sanity

| Statistic | Value | Sensible? | Notes |
|-----------|-------|-----------|-------|
| Standalone effects vs strict MDE | all ≪ MDE (max +0.21 vs 12.0) | YES | No cell near the strict floor; consistent with `strict_passed=False` ×12. |
| Loose: `ci_lower` vs τ | all `ci_lower` < τ (0.375/0.375/1.5) | YES | `loose`/`effective_loose` False ×12. |
| Incremental edge vs floor (12/16/32) | all ≪ floor | YES | `positive_incremental` False ×12. |
| REFUTED resolution | 12 reportable, 0 passes | YES | Matches `overall_status()` branch logic. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Frozen standalone referee | block-bootstrap handles residual dependence | YES | Reused unchanged via `screen_emitted_positions` (VAL-002 path); `effective_n`/`block_length` reported. |
| Revised incremental unit | marginal rows `clip(R+C,−1,1)−R≠0` define denom | YES | EXP-018 frozen gate; denom>0 all cells; same-feed → exact alignment. |
| Robust mean/MAD risk level | dispersion estimable | PARTIAL (model) | Undefined for the sparse model series (MAD=0); handled per scope as null; mean/std diagnostic used for the comparison. |

## Results Plausibility

Outputs sit in-domain: net expectancies ~0-to-negative (cost-eroded), incremental
edges below floors, high favorable-target rates (0.60–0.80) co-existing with
~0/negative lifetime expectancy (reconciled by trend-change exits — Info 6).
Pattern is coherent with an untuned signal that does not clear the frozen
detection floors — the expected REFUTED shape.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none of substance. The plan's *primary* robust mean/MAD model risk
  level is structurally undefined for the sparse position series; per the scope
  zero-baseline rule it is reported null and the model-vs-raw comparison uses the
  already-scoped mean/std diagnostic (Info 2). No scope amendment.
- Complexity budget: 4/4 tests, 5/5 plots, 3/3 modules — respected.
- Holdout exclusion verified: YES (fence respected ×12; no full-file load;
  first-70% smoke source enforced on both sides).

## Issues

### Critical
None.

### Warning
None.

### Info

1. **Two distinct return bases for "expectancy".** Standalone referee
   `effect_bps` (e.g. BTCUSD/5m −0.688) is the net effect on the within-analysis
   test split; metric-book `model_net_bps` (−0.7396) is the mean over all emitted
   return rows. Both correct; the interpretation (Stage 6) should not conflate
   them.

2. **`model_robust_ratio` structurally null (verified).** Mean/MAD over all bars
   is NaN for every cell because the strategy is flat the large majority of bars
   (92.6% for BTCUSD/5m). Correctly excluded from the metric-book gate and
   reported null; `risk_adjusted_heatmap` uses `model_sharpe_diag −
   raw_sharpe_diag`. No defect.

3. **`plot_model_vs_raw` recomputes `returns_and_positions`** from already-loaded
   in-memory positions (not a disk reload or signal regeneration). Bounded and
   correct; could reuse the metric-pass arrays. Non-blocking.

4. **Parity-export vs live-run event counts differ slightly.** The smoke validates
   C#↔Python transcription on the parity export (events 5978/421/109, 0 mismatch,
   max_abs_price_diff 0.0); the live runs show close but not byte-identical bounce
   counts (e.g. BTCUSD/5m 5972). Different generation vehicles over independently
   fenced inputs — consistent with the VAL-002 behavioral (not byte-parity)
   standard. No defect.

5. **`AnalysisEndUtc` is trusted as the analysis boundary**, validated upstream
   (VAL-002 + the in-engine fence) and re-asserted on emitted rows. The harness
   deliberately does not recompute the 70% point from the full source file, since
   that would require loading the holdout. Correct by design; flagged for
   transparency.

6. **High favorable-target rate with ~0/negative lifetime expectancy.**
   `successful_bounce_rate` (favorable/(favorable+adverse), 0.60–0.80) excludes
   trend-change exits, while `lifetime_expectancy_bps` includes them; trend-change
   moves are the negative drag. Internally consistent; a point for the analyst to
   interpret, not an audit defect.

## Re-Audit Requirements

None — PASS. The result is trustworthy for interpretation (Stage 6).
