# Audit Report: Experiment EXP-003

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 3

EXP-003 is the Phase 001 keystone: it measures per-domain FPR, TPR curves,
economic MDE (across the α grid), and gate-leg pass rates for the minimal
baseline and the 5-check gate stack on the validated substrate. The
implementation matches the plan, excludes the holdout, preserves real-price and
temporal discipline, and the parallel evaluation path is deterministic. I
reproduced a full BTCUSD/4h cell end-to-end (load → 4h domain → returns →
shared-timestamp split → both referees) and it matched `draw_verdicts.csv`
bit-for-bit. Internal arithmetic (Wilson intervals, FPR/TPR counts, MDE
selection) is correct. `overall_status = COMPLETE` with 18/18 MDE cells PASS is
faithful to the design's "success = producing the map" criterion (§11).

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Draw enumeration, dual-referee evaluation, FPR/TPR/MDE/leg summaries match plan; reproduced end-to-end. |
| `src/xen/referee_calibration.py` | Referee correctness | PASS | `evaluate_referees` reuses one bootstrap core per referee across α; verified against committed verdicts. |
| both | Holdout exclusion | PASS | `load_analysis_data` slices first 70%; domains built post-slice; `domain_rows` reproduce EXP-001 (BTC 4h=4425). |
| `run_experiment.py` | Look-ahead prevention | PASS | Random states independent of returns; outcome `t→t+1`; block length on train segment only. |
| `run_experiment.py` | Timestamp alignment | PASS | Shared `train_end_ts` split via `domain_split_index` (BTC 4h split=3089 reproduced), not per-domain row fraction. |
| `run_experiment.py` | Real-price discipline | PASS | Real domain `Close` returns; no chart prices. |
| `run_experiment.py` | Determinism / safe optimization | PASS | Multiprocessing is scheduling-only: each task regenerates from a per-draw seed; rows sorted to canonical order. End-to-end reproduction matched the parallel CSV exactly. |
| `run_experiment.py` | Memory/performance | PASS | Verdict-level rows only (no per-bar storage); `plot_effective_sample` aggregates in Polars before pandas. |
| `run_experiment.py` | Progress tracking | PASS | `tqdm` over load loop and the draw pool. |
| `run_experiment.py` | Organization/import side effects | PASS | Dirs in `main()`; module-level only reads `os.cpu_count()`/env (no fs/IO). |
| both | Docstrings/types | PASS | Public functions documented and typed. |

## Numerical Validation

### Spot Checks

**End-to-end reproduction (BTCUSD/4h, α=0.05).** Loading the BTCUSD analysis
slice, building the 4h domain, and evaluating both referees on the same seeds
reproduced `draw_verdicts.csv` exactly:

| Draw | Referee | Committed | Reproduced |
|------|---------|-----------|------------|
| null bar_permutation #0 | gate_stack | REJECT, eff −10.2754, ci_lo −16.1524 | identical |
| null bar_permutation #0 | minimal | REJECT, eff −0.2754, ci_lo −6.7453 | identical |
| positive m=12 #0 | gate_stack | PASS, eff 14.7372, ci_lo 8.5606 | identical |
| positive m=12 #0 | minimal | PASS, eff 24.7372, ci_lo 18.5275 | identical |

Cost identity holds: gate (net) − minimal (gross) = −10.0 = −cost(BTCUSD) in both
draws; planted m=12 recovers as 14.74 = 12 + 2.74 single-draw noise (net).
`split_index=3089`, `return_rows=4424` reproduced.

**Wilson arithmetic.** FPR gate 0/4000 → center 0.0004797, half 0.0004797
(reproduces `fpr_summary.csv`); minimal 1h α=0.05 99/4000 → 0.02475. TPR n=2000
(500 draws × 4 instruments), FPR n=4000 (× 2 null generators). All counts consistent.

**MDE selection.** `_classify_mde_cell` picks the smallest grid `m` with TPR≥0.80
and Wilson half-width≤0.05, given FPR≤α and FPR half-width≤0.03. Verified against
`tpr_summary.csv`: e.g. 1h gate α=0.05 first reaches TPR≥0.8 at m=4.0 (TPR 0.9765)
→ MDE 4.0; 4h gate at m=12.0 (TPR 0.935) → MDE 12.0.

### Range / Sanity Checks

| Metric | Expected | Actual | Pass? |
|--------|----------|--------|-------|
| Gate-stack FPR (all domains/α) | ≪ α | 0.0 (0/4000) everywhere | YES |
| Minimal FPR | ≈ α, ≤ α | 1h 0.005/0.0248/0.0493 at α 0.01/0.05/0.10 | YES |
| TPR monotone in m | non-decreasing | yes, 0→1 across grid | YES |
| MDE cells | finite, status PASS | 18/18 PASS | YES |
| Effective N (blocks) | reported per cell | e.g. BTC 4h = 1335 | YES |

### Statistical Sanity

| Statistic | Value | Sense? | Notes |
|-----------|-------|--------|-------|
| Gate MDE > minimal MDE every domain | 5m 1.0 vs 0.5; 1h 4.0 vs 0.5; 4h 12.0 vs 2.0 (α=0.05) | YES | The conjunctive stack trades MDE inflation for FPR→0. |
| Gate MDE constant across α | 5m 1.0 / 1h 4.0 / 4h 12.0 at all α | YES | Gate operating point is set by L5 materiality (fixed bps), not α. |
| Per-leg null pass rates | L1=L2=1.0, L3=L4=L5=0.0 | YES | FPR=0 driven jointly by the three outcome legs each rejecting all nulls. |
| Binding leg near MDE | L5 materiality (e.g. 4h m=2: L5=0.006; 1h m=2: L5=0.371) | YES | L5 dominates gate-stack false negatives — answers design PS-T2/T9. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Wilson interval | distribution-free for Bernoulli pass/reject | YES | applied to pass/reject counts. |
| Block bootstrap | serial-dependence-aware inference unit | YES | block length from train ACF; effective-N reported. |
| Paired draws | identical draws to both referees reduce comparison variance | YES | both referees share the per-draw seed; reproduced. |

## Results Plausibility

Every value sits where the design predicts: the minimal baseline is an
FPR≈α single test, the gate stack is a near-zero-FPR conjunction with inflated,
materiality-driven MDE, and the TPR curves rise monotonically to 1.0. The 4h
domain is fully measured (not inconclusive) because rates pool 2000 draws/cell,
giving tiny Wilson widths.

## Scope Compliance

- Analysis plan followed: YES (dependency gate → paired null → paired positive → MDE/leg diagnostics).
- Deviations: none.
- Complexity budget: 4/4 tests, 5/5 plots, 1 shared module (reused, no new module).
- Holdout exclusion verified: YES (domains reproduce EXP-001 post-slice counts).
- Dependency gate: requires EXP-001 and EXP-002 `overall_status == PASS`.

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Per-domain rates pool four instruments of heterogeneous cost and dispersion.**
   FPR/TPR/MDE group by (domain, referee, α) — not instrument — pooling EURUSD
   (cost 1 bps) … BTCUSD (cost 10 bps) and very different 4h dispersion. This
   matches the design's per-domain deliverable (§2 D-dom), but the per-domain MDE
   is an aggregate dragged toward the harder instruments (e.g. 4h gate m=8 pooled
   TPR=0.73 < 0.80, m=12 = 0.935). EXP-004 evaluates per-instrument dogfood, so the
   interpreter should compare each real strategy to its **domain** MDE while
   remembering a per-instrument MDE could be lower. Not a defect — a granularity
   note.

2. **MDE = first grid crossing; relies on TPR monotonicity.** `_classify_mde_cell`
   returns the smallest grid `m` with TPR≥0.80; it does not enforce that TPR stays
   ≥0.80 above it. TPR is monotone non-decreasing in `m` in every cell here, so the
   MDE is well-defined; flagged only as a structural assumption for future grids.

3. **Gate-stack operating point is materiality-driven, not α-driven.** The gate
   stack's FPR (0.0) and MDE (5m 1.0 / 1h 4.0 / 4h 12.0) are identical across the
   whole α grid, because the binding leg L5 compares the CI lower bound to a fixed
   per-domain materiality threshold rather than to α. The α grid moves only the
   minimal baseline's MDE (e.g. 4h 4.0→2.0→1.0). This is a genuine finding to
   surface in interpretation, not an error.

## Re-Audit Requirements

None. Verdict is PASS; no fixes required.
