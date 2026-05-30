# Governance Review: Experiment EXP-034 — Pre-Execution

**Date**: 2026-05-28
**Review Type**: Pre-Execution
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, and the shared `python/src/bar_aggregator.py` extension.

## Executive Summary

APPROVE. EXP-034 is a holdout-preserving, return-free readiness survey that complies with the Phase 005 `design.md` (including the four predeclared amendments), the programme principles, and the developer code conventions. No Critical or Warning issues.

## Constraint Checks

### Simplicity Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | 0 statistical tests; exact counts, deterministic digests, exact shares. Simplest sufficient approach for a count-eligibility survey. |
| analysis-plan.md | PASS | Every step justifies "why this method" and a rejected simpler/heavier alternative. |
| code | PASS | Pure-computation helpers separated from plotting and orchestration; no unused machinery. |

### Academic-Finance Pitfall Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| all | PASS | No normality, stationarity, i.i.d., or constant-volatility assumption. Serial dependence is explicitly addressed: independent episodes (run-length encoding), not rows, are the binding denominator per `design.md` Gate 2. No inferential model at all. |

### Scope Compliance Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Single falsifiable count-eligibility question. Data views, parameters (lookback 20; buckets 0.20/0.80; timeframes 60/240; coverage settings strict + tolerant 0.90), instruments, exclusions all explicit. Matches `design.md` Candidate 1 and §"Immediate Next Step" (also locks the shared coverage rule). Implements amendment 3 (strict-vs-tolerant feature-stability check). |
| code | PASS | Implements exactly the plan: no return/excursion/P&L column exists by construction. |

### Principles Check

| Artifact | Data-Driven | Non-Parametric | Synthetic-Price Discipline | Holdout Excluded |
|----------|------------|----------------|----------------------------|------------------|
| all | PASS | PASS | PASS (no returns; aggregated real OHLC only; no HA/Renko prices) | PASS (`load_analysis_timebars` slices first 70% of the 1-minute series before aggregation; no code path references the final 30%) |

### Chart-Type / Cross-View Check

| Artifact | Timestamp Alignment | Bar-Count Adjustment | Generator Determinism |
|----------|--------------------|----------------------|-----------------------|
| all | PASS (strict-vs-tolerant join on `CloseTime`; segment assignment by `CloseTime`) | PASS (no bar-index alignment) | PASS (shuffle-then-resort determinism digest; verified on synthetic data) |

### Code-Convention Check (developer standards)

| Check | Verdict | Notes |
|-------|---------|-------|
| Imports → path setup → constants → dataclass → I/O → computation → plotting → orchestration → main | PASS | Matches the EXP-033 reference organization. |
| Output dirs created in orchestration only | PASS | `RESULTS_DIR.mkdir`/`PLOTS_DIR.mkdir` inside `run_experiment()`, not at import. |
| Lazy holdout slicing | PASS | Uses `load_analysis_timebars` (lazy scan → sort → first-70% slice → collect). |
| Bounded plotting | PASS | Plot inputs are aggregated readiness rows / histogram arrays; no millions-of-rows pandas conversion. |
| No silent dedup | PASS | No `.unique()` in loaders. |
| Zero-baseline handling | PASS | No ratio is reported as percentage-of-zero; degenerate (`prior_high == prior_low`) bars are flagged and excluded from bucketing, share reported. |
| Concise logging | PASS | `logging.getLogger`; helpers return data. |
| `bar_aggregator` extension | PASS | `min_coverage` is additive and backward-compatible — default `None` reproduces the exact-`N` filter bit-for-bit (verified: `aggregate_ohlc(df, 60)` equals `aggregate_ohlc(df, 60, None)`), so EXP-029/030/031/033 reproducibility is preserved. Validation `0 < min_coverage <= 1`. |

### Design.md Phase-Gate Check

| Gate | Verdict | Notes |
|------|---------|-------|
| Gate 1 readiness-before-return | PASS | No return metric; this is readiness only. |
| Gate 2 count + independent-episode | PASS | Row floors (100/50) AND independent-episode floors (30/15) per bucket, both segments. |
| Gate 5 holdout | PASS | Holdout never loaded/inspected. |
| Gate 6 no-test-selection | PASS | Canonical aggregation chosen from coverage/feature-stability evidence only; buckets/lookback/tolerance all predeclared, none outcome-tuned. |
| Amendment 3 | PASS | EXP-034 reports under both strict and tolerant; tolerant admissible only if matched-bucket share ≥ 0.95 on ≥2 instruments, else strict retained. |

## Findings

### Critical
None.

### Warnings
None.

### Info
- The `bar_aggregator.coverage_summary` helper's `dropped_partial_window_bars` field assumes exact-`N` windows and is meaningful only in strict mode; EXP-034 does not use it and computes its own dropped-window rate directly from `expected_windows` and retained heights, so there is no correctness impact.
- On real data the binding risk is at `4h` (fewer bars / episodes); this is exactly what the episode floor tests, and the verdict will record a clean readiness-gated no-go if it is not met.

## Verdict

```
VERDICT: APPROVE
```
