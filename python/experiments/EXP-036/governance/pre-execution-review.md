# Governance Review: Experiment EXP-036 — Pre-Execution

**Date**: 2026-05-29
**Review Type**: Pre-Execution
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**Authorizing directive**: Phase 005 mid-phase reflection §2/§3/§4 (Prior-Range Location → EXP-036; strict canonical aggregation; locked primary metric).

## Executive Summary

All checks pass. The experiment is a single-hypothesis return test of the highest-priority readiness-passing directional descriptor, scoped to the locked primary metric, with the neutral baseline correctly defined as the measured middle bucket (`μ_mid`), episode-level inference, and a holdout-preserving load path. One equivalent-mechanism Info note (row-index vs `CloseTime`-cutoff segment split) is recorded.

## Constraint Checks

### Simplicity Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | 2 stat families / 4 plots / 0 new modules — within the design budget (≤3/≤4/≤1). |
| analysis-plan.md | PASS | Two-sample episode bootstrap is the simplest method that both respects serial dependence and propagates the `μ_mid` baseline's sampling error; simpler alternatives (row bootstrap, fixed-`μ_mid`, parametric t) are documented and rejected with reasons. |
| code | PASS | Vectorized chunked bootstrap; reuses EXP-034 feature construction; no superfluous computation. |

### Academic-Finance Pitfall Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| analysis-plan.md | PASS | Non-parametric throughout. No normality (bootstrap CIs), no stationarity assumption beyond within-segment (train/test sign preservation is the cross-segment guard), no i.i.d. row assumption (episodes are the resampling unit; row bootstrap is diagnostic only). |
| code | PASS | `_episode_bootstrap` resamples independent state episodes; the naive row bootstrap is explicitly labelled diagnostic and never gates. |

### Scope Compliance Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Single question (does the descriptor beat neutral middle bucket AND matched control); explicit boundaries (4 instruments × 1h/4h, strict, continuation locked); concrete FOR/state-diff/AGAINST/horizon-dependent/INCONCLUSIVE criteria; no horizon sweep, no sizing, no cost model (deferred to EXP-038). |
| code | PASS | Implements exactly the plan: strict-only aggregation; locked buckets/lookback; next-bar + single 4-bar horizon; no extra analyses. |

### Principles Check

| Artifact | Data-Driven | Non-Parametric | Synthetic-Price Discipline | Holdout Excluded |
|----------|------------|---------------|--------------------------|-----------------|
| scope.md | PASS | PASS | PASS (real OHLC only; no HA/Renko) | PASS |
| analysis-plan.md | PASS | PASS | PASS | PASS |
| code | PASS | PASS | PASS | PASS |

### Chart-Type Comparison Check

| Artifact | Timestamp Alignment | Bar-Count Alignment Ban | Generator Determinism |
|----------|-------------------|------------------------|----------------------|
| code | PASS — forward returns indexed within a `CloseTime`-sorted segment (chronological); entry-gap diagnostic reports clock gaps | PASS — single data view; no cross-view bar-index alignment | PASS — `aggregate_ohlc` deterministic; feature pass deterministic; bootstrap seeded (`default_rng`, per-cell non-overlapping offsets) |

### Quality Check (return-test specific)

| Check | Verdict | Notes |
|-------|---------|-------|
| Neutral baseline is the middle bucket, not zero | PASS | `Δ_neutral = mean(d·(r − μ_mid))`; `μ_mid` measured from middle-bucket returns; zero/flat-cash baseline explicitly rejected (the earlier audit-caught error). |
| Matched control binding | PASS | `Δ_control = mean((d − c)·r)` paired on the descriptor's own traded bars; neutral-only pass → state-differentiation-only (Gate 4). |
| Middle bucket counted | PASS | `_state_counts` and `_contrast_adjudicable` require the middle state to clear floors for the vs-neutral contrast. |
| μ_mid sampling error propagated | PASS | Two-sample bootstrap resamples middle episodes independently each draw. |
| Inference unit | PASS | Independent state episodes; row bootstrap diagnostic only. |
| Zero-baseline handling | PASS | Absolute return differences with CIs; no percentage-over-zero. |
| Secondary-horizon gate semantics | PASS | 4-bar cannot manufacture an edge claim; `_verdict` only allows it to produce HORIZON_DEPENDENT, never FOR. |
| Underpowered ≠ refuted | PASS | `_verdict` emits INCONCLUSIVE when the best both-contrast pass = 1 or <2 instruments are adjudicable for the control gate; AGAINST requires ≥2 adjudicable yet <2 passing. |

## Findings

### Critical

None.

### Warning

None.

### Info

1. **Segment split mechanism.** `_add_segment` labels Train/Test by chronological row position (`int(0.70·height)`), whereas scope/plan describe `train_cutoff_time` + `CloseTime` assignment. On a `CloseTime`-sorted aggregated series with unique close timestamps these are identical (the first `int(0.70·N)` rows are exactly those with `CloseTime ≤ cutoff`). This matches the approved EXP-034 implementation. No action required.
2. **Backward-looking range across the train/test boundary.** The prior-20 range rolls over the full series, so early test bars use late-train bars in their lookback. This is legitimate use of past information (not look-ahead) and matches EXP-034.
3. **Episode-id loop.** `_episode_ids` is a Python loop over per-segment bars (~10–15k at 1h). Acceptable for an offline run; not a correctness issue.

## Numerical Spot Reasoning (pre-execution)

- Under the null `E[r|top]=E[r|bottom]=μ_mid`, `Δ_neutral` is centered at 0 by construction (verified algebraically: per-side terms `E[r|top]−μ_mid` and `μ_mid−E[r|bottom]` both vanish), so a positive pass cannot be produced by ambient drift alone — the property the earlier audit required.
- `_stat_values` guards all divisions (`np.errstate` + `np.where` on zero `n_top`/`n_bot`); resampled `n_ext`/`n_mid` are strictly positive (≥1 episode sampled, each `cnt≥1`).
- Bootstrap memory is bounded by `BOOTSTRAP_CELL_BUDGET` chunking; plot inputs are small summary dicts computed once (no reload/regeneration for plotting).

## Verdict

```
VERDICT: APPROVE
```
