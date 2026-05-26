# Pre-Execution Governance Review: EXP-022

**Experiment**: EXP-022 - Objective Breaker Candidate Reproducibility
**Artifacts reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**Review date**: 2026-05-25

---

## Scope Review

| Check | Status | Notes |
|-------|--------|-------|
| Single falsifiable question | PASS | "Which objective breaker candidate is reproducible enough for testing?" |
| Boundaries defined | PASS | Instruments, time range, 2 candidates A/B explicitly specified |
| Holdout exclusion stated | PASS | Final 30% excluded; nested split documented |
| No profitability comparison | PASS | Scope explicitly restricts to "counts and reproducibility" only |
| Success/failure criteria measurable | PASS | Deterministic equality, >= 50 events, >= 3 instruments, ambiguity rate ≤ 30% |
| Complexity budget respected | PASS | 0 tests / 0-1, 3 plots / 4, 1 module / 1 |

## Analysis Plan Review

| Check | Status | Notes |
|-------|--------|-------|
| Method justification present | PASS | All 3 steps include "why this method" and "simpler alternative considered" |
| Selection criterion predeclared | PASS | Step 3 states selection by reproducibility + counts, not profitability |
| Assumptions stated | PASS | "Swing timestamps are usable only after confirmation" |
| Visualisations purposeful | PASS | 3 plots (counts, miss reasons, delay distribution) each answer sub-questions |
| Budget compliance | PASS | 0 tests / 0-1, 3 plots / 4, 1 module / 1 |

## Code Review

| Check | Status | Notes |
|-------|--------|-------|
| Import side effects absent | PASS | `mkdir` only inside `run_experiment()` |
| Holdout exclusion enforced | PASS | `load_analysis_timebars()` enforces 70% split |
| Temporal ordering by CloseTime | PASS | All bar lookups use `CloseTime` nanoseconds |
| Candidate A look-ahead prevention | PASS | `_find_last_opposite_candle` searches bars strictly before `sweep_idx - 1`; `_find_cand_a_breaker` starts strictly after `disp_ns` |
| Candidate B look-ahead prevention | PASS | `detect_swings` uses `usable_idx = idx + SWING_LEFT_RIGHT`; `_latest_usable_swing` filters to `UsableTime < bar_ns` |
| No profitability in code | PASS | No outcome metrics computed; only counts, ambiguity rates, SHA-256 digests |
| SHA-256 reproducibility | PASS | Second-pass detection and digest comparison correctly implemented |
| Selection logic | PASS | Predeclared criteria (reproducibility → floor count → ambiguity rate); no outcome-based selection |
| Bounded plotting | PASS | No sampling required (count data only) |
| Organisation | PASS | Import → constants → I/O → Candidate A → Candidate B → reproducibility → selection → plotting → output → orchestration → main |
| NaN handling | PASS | `AmbiguityRate = ambig / n if n else np.nan`; empty DataFrame guards in concat |
| Type safety | PASS | All public functions have type hints; return types annotated |
| Budget compliance | PASS | 0 statistical tests; 3 plots; 1 code module |

### Issues Found

**INFO — Dead `swing_ns` parameter in `_latest_usable_swing()`**

`_latest_usable_swing()` (line 288) declares a fourth parameter `swing_ns: np.ndarray`, but the function body never uses it. The function recomputes `sub_ns` from the filtered `sub` DataFrame. Unlike EXP-021's analogous case, the call site passes actual data (correct type), so there is no type violation — the parameter is merely dead code. This is a minor code quality note; it does not affect correctness or reproducibility.

**INFO — Candidate B breaker window starts at sweep, not displacement**

`_find_cand_b_breaker()` begins its search at `sweep_ns + right`, meaning a Candidate B breaker could theoretically fire between the sweep bar and the displacement bar. The predeclared config explicitly states "after the sweep," so this is intentional. EXP-023's governance review will verify that this asymmetry is handled correctly when building outcome entries.

---

## Verdict

```text
VERDICT: APPROVE
```

All critical and warning checks pass. Two info-level notes recorded above; neither affects correctness, reproducibility, or scope compliance.
