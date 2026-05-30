# Governance Review: Experiment EXP-035 — Pre-Execution

**Date**: 2026-05-28
**Review Type**: Pre-Execution
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, and the new module `python/src/market_bias.py`.

## Executive Summary

APPROVE. EXP-035 is a holdout-preserving, return-free determinism + episode-count readiness survey of the chart-timeframe Market Bias port. It complies with the Phase 005 `design.md` (Candidate 2 and amendments 2 and 4), the programme principles, and the developer code conventions. No Critical or Warning issues.

## Constraint Checks

### Simplicity Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | 0 statistical tests; exact counts, deterministic digests, deterministic warmup determination. |
| analysis-plan.md | PASS | Each step justifies "why this method" and a rejected alternative (e.g., standard HA recursion / cold-only seed / fixed-300 warmup). |
| code / module | PASS | `market_bias.py` is the single new module `design.md` reserves; helpers are small, pure, and separated from orchestration/plotting. |

### Academic-Finance Pitfall Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| all | PASS | No normality/stationarity/i.i.d./constant-volatility assumption. Independent episodes are the binding denominator for this long-memory descriptor (`design.md` Gate 2). No inferential model. |

### Scope Compliance Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Single falsifiable port-determinism + count-eligibility question. Chart-TF mode only (Gate 3); parameters `100/100/7` fixed; timeframes 60/240; `1d` excluded; sign-only primary, four-way secondary; no neutral band (return-test construct, deferred). Matches `design.md` Candidate 2. |
| code | PASS | Implements exactly the plan; no return/excursion/P&L column exists by construction. |

### Principles Check

| Artifact | Data-Driven | Non-Parametric | Synthetic-Price Discipline | Holdout Excluded |
|----------|------------|----------------|----------------------------|------------------|
| all | PASS | PASS | PASS (no outcomes computed; Market Bias is built from EMA-smoothed construction values used only to label states; no outcome ever uses synthetic/construction prices) | PASS (`load_analysis_timebars` slices first 70% before aggregation; no code path references the final 30%) |

### Look-Ahead / Determinism Check

| Check | Verdict | Notes |
|-------|---------|-------|
| Causality | PASS | All EMAs causal; the HA-open recursion uses strictly prior bars (`xhaopen[i-1]`, `haclose[i-1]`). Chart-TF collapse removes the Pine real-time offset entirely (no repaint path). |
| Determinism | PASS | Pure float64 recursion; verified bit-identical under shuffle-then-resort on synthetic data (digest match True). |
| Timestamp alignment | PASS | Determinism and optional reference comparison align on `CloseTime`; segment assignment by `CloseTime`. |

### Code-Convention Check (developer standards)

| Check | Verdict | Notes |
|-------|---------|-------|
| Organization | PASS | Imports → path/constants → dataclass → pipeline → counts/episodes/digests → readiness → reference → verdict → plotting → orchestration → main. |
| Output dirs in orchestration only | PASS | `mkdir` inside `run_experiment()`. |
| Lazy holdout slicing | PASS | `load_analysis_timebars`. |
| Bounded plotting | PASS | `osc_bias` series is deterministically down-sampled to `PLOT_SAMPLE_CAP=4000`; other plots use aggregated readiness rows. |
| Module import side-effects | PASS | `market_bias.py` defines functions/constants only; no IO, no dir creation, no data load at import. |
| Empty / short-frame handling | PASS | `compute_market_bias` and `convergence_warmup` handle empty and `< length` frames without crashing (verified on synthetic data); short frames simply fail the floors. |
| Warmup determinism | PASS | `convergence_warmup` is a deterministic two-seeding rule, floored at 300; non-convergence returns `converged=False` (fails readiness check 2). |

### Design.md Phase-Gate / Amendment Check

| Gate / Amendment | Verdict | Notes |
|------------------|---------|-------|
| Gate 1 readiness-before-return | PASS | No return metric. |
| Gate 2 count + independent-episode | PASS | Row floors (100/50) AND episode floors (30/15) on sign-only states, both segments; four-way reported as secondary diagnostic. |
| Gate 3 single-timeframe / chart-TF only | PASS | No MTF import; chart-TF collapse implemented as `request.security` no-ops. |
| Gate 5 holdout | PASS | Never loaded/inspected. |
| Gate 6 no-test-selection | PASS | All parameters and the warmup rule predeclared; nothing outcome-tuned. |
| Amendment 2 (warmup rule) | PASS | Predeclared two-seeding (Pine-SMA vs cold) identical-label convergence, floored at 300; non-convergence within train history fails readiness. Implemented in `convergence_warmup`. |
| Amendment 4 (reference fidelity) | PASS | Two port hazards (`xhaopen[1]` recursion; SMA seeding) implemented and documented in the module. No reference series present → pre-committed "deterministic re-implementation" claim with the unverified-fidelity caveat carried into the verdict; the Market Bias branch is not closed on a deterministic-but-unverified null. |

## Findings

### Critical
None.

### Warnings
None.

### Info
- The episode floor is expected to be the binding constraint, most likely failing at `4h` and/or on the four-way axis given the stacked EMA-100 persistence; that is the intended discriminator, not a defect. (On the smooth synthetic test series the two seedings converged only late, `W=396` of 400 — a deliberate stress confirming the warmup gate fires; real 1h/4h series carry far more bars.)
- Reference fidelity is unverifiable until an exported TradingView series is supplied; this is correctly surfaced as a stated caveat rather than an over-claim, per amendment 4.

## Verdict

```
VERDICT: APPROVE
```
