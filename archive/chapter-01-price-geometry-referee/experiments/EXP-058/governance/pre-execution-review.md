# Pre-Execution Governance Review — EXP-058

**Experiment:** Third-Barrier Geometry (Conditioned HA Harami; `/THIRD-TIME`, `/THIRD-EVENT` vs Benchmark Adaptive Cap)
**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B)
**Review date:** 2026-06-16
**Reviewer:** research-pipeline Stage 4

---

## Signal-Registry Precondition

- Candidate family `CF-HA-HARAMI-001` — **REGISTERED** (`candidate-families/harami.md`)
- Branches `CF-HA-HARAMI-001/THIRD-TIME` and `CF-HA-HARAMI-001/THIRD-EVENT` — **REGISTERED** (`multiplicity-registry.md` lines 343–344)
- HYP-011 / EXP-058 — **PLANNED** (`multiplicity-registry.md` line 386)
- 0 candidate slots, 0 TEST reads — consistent with registry and `014-B-D0-addendum.md` P21
- No TEST stratum read (TRAIN-only; `test-read-ledger.md` not applicable)

## Scope (`scope.md`) Review

| Check | Result | Notes |
|-------|--------|-------|
| Single testable hypothesis | PASS | "at least one alternative third-barrier geometry produces higher gross per-event median expectancy than benchmark" — falsifiable, precise |
| Defined boundaries | PASS | Data views, event population, instruments (99-cell grid), TRAIN-only, exclusions all explicit |
| Concrete success/failure criteria | PASS | EVIDENCE_FOR / AGAINST / INCONCLUSIVE / DEFECT with quantitative P11 thresholds |
| Mandatory holdout exclusion | PASS | §"Slot & ledger accounting": final 30% never loaded, never inspected, forward scans clipped to TRAIN edge |
| Real-price discipline | PASS | HA detection only; all metrics on real domain-bar OHLC (§"Real-price outcome discipline") |
| Complexity budget | PASS | 4 stat methods, 5 plots, 1 new module — within budget |
| Metric denominators & zero-baseline | PASS | <30 qualifying → NOT_VIABLE_BY_POWER; DATA_CENSORED excluded-with-record; no undefined ratios |
| Operator decisions predeclared | PASS | All 5 binding variants, grid design, and `/THIRD-EVENT` backstop rationale recorded before data contact |

## Analysis Plan (`analysis-plan.md`) Review

| Check | Result | Notes |
|-------|--------|-------|
| Method justification | PASS | Each method has "why", "simpler alternative considered", and "assumptions" |
| Non-parametric | PASS | Regime-clustered moving-block bootstrap; no normality/stationarity/i.i.d. assumptions |
| Cross-view alignment | PASS | By exact `CloseTime` match (searchsorted + equality assert), never bar index |
| Visualisation plan | PASS | 5 purposeful plots with specific questions |
| Interpretation guide | PASS | Predefined mechanical thresholds per outcome (no post-hoc rationalisation) |
| Budget compliance | PASS | 4/4 methods, 5/5 plots, 1/1 new module |
| Step 9 invariants | PASS | Cap monotonicity, `/THIRD-EVENT` bounds, warmup identity, EXP-053 reconciliation — all predeclared |

## Code (`code/run_experiment.py` + `xen/third_barrier.py`) Review

| Check | Result | Notes |
|-------|--------|-------|
| Organization (VAL-001-style) | PASS | imports → path setup → constants → types → I/O helpers → pure computation → plotting → orchestration → `main()`; clear sectioning |
| Import side effects | PASS | No directory creation, file writes, or data loading at import |
| Output directories in orchestration | PASS | `mkdir()` in `run()` (lines 1202–1203), not at module level |
| Lazy holdout-safe loading | PASS | `pl.scan_parquet(path).select(cols).slice(0, train_rows).collect()` — only first 49% file-order rows read; full file never sorted/collected |
| Bounded memory | PASS | Per-cell processing with `del cell`, `del train_1m` |
| Progress tracking | PASS | `tqdm` over 99-cell grid (line 1217) |
| Concise logging | PASS | `LOGGER.info` at end; no `print()` in helpers |
| No silent deduplication | PASS | None observed |
| Plotting reuses analysis data | PASS | `make_plots()` receives already-computed summaries + pooled returns |
| Zero-baseline / finite | PASS | `NOT_VIABLE_BY_POWER` for <30 events; `DATA_CENSORED` excluded-with-record |
| Real-price discipline | PASS | HA only in `detect_ha_harami`; all metrics on real OHLC (`real_ohlc()`) |
| Causality / look-ahead | PASS | Confirmed moves anchored at `ConfirmTime ≤ t_i`; `/THIRD-EVENT` exit has `ConfirmTime > t_i` (forward) and `confirm_idx > entry_idx`; first-touch scans start at `entry_idx+1` |
| Temporal alignment | PASS | By `CloseTime` epoch, `searchsorted` + equality assert |
| Safe vectorization | PASS | P15 `resolve_path_ordered` kept sequential (causal semantics); `/THIRD-EVENT` cap uses `searchsorted` + bounded forward scan |
| No HA-price-in-metric | PASS | All outcome metrics on real OHLC; HA only for detection |
| Deterministic | PASS | Fixed master seed + per-cell-per-purpose RNG streams; determinism replay per instrument |
| EXP-053 reconciliation anchor | PASS | Per-cell BENCH median + count + first-hit r cross-checked to 1e-9 tolerance |
| Predeclared invariants in code | PASS | Cap monotonicity, event bounds, warmup identity — all asserted in `cell_invariants()` |
| New module (`third_barrier.py`) | PASS | Pure computation; no import side effects; causal `/THIRD-EVENT` locator with `searchsorted` lower bound and bounded forward scan |

## Hard-Constraint Compliance

| Constraint | Status |
|------------|--------|
| No experiment code execution in pipeline | ✓ (not applicable — Stage 4) |
| No governance bypass | ✓ |
| No final-30% holdout inspection | ✓ — only first `train_rows` loaded |
| `CloseTime` for temporal ordering | ✓ |
| No future data relative to event timestamp | ✓ — all construction at `t_i` uses only data ≤ `t_i`, forward scans are exit-only |
| No HA prices for returns | ✓ — HA only for detection |
| Real-price outcome discipline | ✓ |
| Cross-view alignment by timestamp | ✓ |
| Registered branches only | ✓ — THIRD-TIME, THIRD-EVENT registered in `multiplicity-registry.md` |
| 0 slots, 0 TEST reads | ✓ — consistent with scope and 014-B design |

---

## Verdict

```text
VERDICT: APPROVE
```

All checks pass. The scope, analysis plan, code, and signal-registry preconditions are complete and compliant. Proceed to manual execution.
