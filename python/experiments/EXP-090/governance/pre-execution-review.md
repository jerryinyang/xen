# EXP-090 — Pre-Execution Governance Review (Stage 4)

**Date:** 2026-06-23 · **Reviewer:** research-pipeline consolidated governance ·
**Artifacts:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, new modules
`xen.intrabar_fill` + `xen.mean_reversion` additions.

## Constraint checks (passing)

- **Signal-registry precondition.** CF-MR-001 `ADMITTED (BINDING)` (G-020); EXP-090 registered as
  `CF-MR-001/HYP-002`, Phase 021 batch, `PLANNED`, 0 slots / 0 reads. Readiness + calibration
  introduce **no new countable candidate item** (they define the member set; the exit slate
  RCT/ERT/contrast is already registered in the Phase 021 D0). **No TEST-stratum read** — all 48
  strata stay 0/2 open; `test-read-ledger.md` unchanged. ✓
- **Holdout (§5).** TRAIN sub-split only (`load_train_1m` slices the first `int(int(total·0.7)·0.7)`
  `CloseTime`-sorted rows; asserts the slice height = cutoff ⇒ 0 holdout rows read). Analysis-TEST
  and final-30% holdout never materialized; the 1m fill engine fences at `train_edge_epoch`. ✓
- **Look-ahead (§6).** RSI2/ATR/EMA10/RCT causal (state ≤ bar t); `resolve_exit_paths` walks 1m
  bars forward from entry; `minute_bounds_for_domain` maps by `CloseTime` epoch, **never bar index**
  (with an explicit timestamp-alignment assertion + negative-control note). ✓
- **Real-price (§7).** All excursions/fills on real OHLC; RCT is a model-derived target *price* but
  the fill is a real touched level (asserted ∈ `[Low,High]` of the 1m bar). No HA/Renko prices. ✓
- **Per-stratum (verdict representation).** Member verdict emitted per (instrument, domain) cell in
  `member_map.csv`; the experiment-level `READINESS_CALIBRATION_DELIVERED` is a **deliverable/process
  flag** (delivered/HALT/INCONCLUSIVE), not a collapsed market-edge PASS — consistent with the
  EXP-080/044 readiness convention. No binding cross-cell conjunction. ✓
- **Anti-overfitting fence.** The exit-substrate readiness battery and calibration run on
  **matched-random entries only**; the real CORE fade exit outcomes are never resolved
  (`real_fade_outcomes_resolved=false`). Real CORE entries contribute counts/coverage only. ✓
- **Gate thresholds.** α₀=0.05, TPR≥0.80, FPR/TPR Wilson half-widths (0.03/0.05), N_DRAWS=1000,
  N_BOOT=10000, coverage floor 15, EDGE_GRID — all D0-frozen or EXP-044/070/080 precedent and
  disclosed; none an unjustified magic constant. ✓
- **Budget.** 1 binding estimator (moving-block bootstrap lower bound) + Wilson/MDE readouts; 4
  plots; new modules: `xen.intrabar_fill` (the one justified new module) + small native-target
  helpers in `xen.mean_reversion` + experiment-local logic in `run_experiment.py`. Within the ≤2
  budget. ✓
- **Determinism / safe-opt.** All randomness via `seed_for`; byte-identical second pass + hash-pin;
  the genuinely-sequential 1m walk is an explicit **bounded** loop (≤ `MR_CAP_MAX`). ✓

## Issue (REVISE) — analysis-plan ↔ code method mismatch

The implementation introduced two sound, documented deviations from the approved `analysis-plan.md`.
Both are correct engineering choices, but the plan text no longer matches the code, so the artifact
trail must be reconciled **before** execution (plan-compliance constraint). The code is **not** at
fault — its literal plan method is computationally infeasible — so the plan is the failing artifact.

1. **Calibration draw-generation (Step 3).** The plan specifies *per-draw matched-random placement +
   exit resolution*. With the new 1-minute intrabar walk this is ~10¹³ ops (intractable). The code
   instead resolves the matched-random pool **once per (cell × arm × path)** into the real
   exit-resolved net-return shape, then generates the 1000 draws as **moving-block resamples of
   length n recentred to true-location-0** (Null A = real path; Null B = block-rotated path). This
   **preserves the estimand** (FPR at true-0, MDE at TPR≥0.80, serial dependence via moving blocks,
   two structurally-different nulls) and the translation-equivariance planted-edge shortcut; only the
   draw-*generation* differs. The plan's Step 3 must be updated to describe this construction (and
   why per-draw placement was infeasible), so plan ≡ code.

2. **Arm coverage.** The plan lists 6 arms built for readiness; the code resolves/calibrates the **5**
   expressible through the unified single-favourable-touch engine (RCT, ERT, ATR-barrier, RSI-revert,
   fixed-bar) and **defers the two-leg favourable partial/trail arm to EXP-091** (different resolver;
   the binding member gate keys only on the native arms RCT/ERT). The plan must record partial/trail
   as deferred-to-EXP-091, keeping the binding deliverable unchanged.

Neither deviation touches holdout, look-ahead, real-price, the per-stratum verdict, or any binding
threshold; both are reconciliations of plan prose to estimand-preserving code.

```text
VERDICT: REVISE
FAILING_ARTIFACT: python/experiments/EXP-090/analysis-plan.md
REQUIRED_SKILL: experiment-quant-analyst
ISSUES:
- Step 3 (calibration substrate): reconcile the draw-generation to the implemented tractable
  pooled-resolution + moving-block-resample-to-true-0 construction (per-draw 1m placement is
  computationally infeasible, ~1e13 ops); state the estimand is preserved (FPR@true-0, MDE@TPR>=0.80,
  serial dependence, two structurally-different nulls, translation-equivariance planted edge) and that
  the calibration is faithfully cost-free by location-invariance.
- Arm coverage: record that EXP-090 resolves/calibrates the 5 unified-engine arms (RCT, ERT,
  ATR-barrier, RSI-revert, fixed-bar) and defers the two-leg partial/trail arm to EXP-091; the binding
  member gate (finite MDE on >=1 native arm RCT/ERT) is unchanged.
- No code change required; reconcile the plan to the code, then re-review.
```

---

## Re-review (revision cycle 1 — 2026-06-23)

`analysis-plan.md` updated by `experiment-quant-analyst` (dated revision note added):

1. **Step 3 draw-generation reconciled** to the pooled-resolution + moving-block-resample-to-true-0
   construction (Null A real path / Null B block-rotated path); the infeasibility of per-draw 1m
   placement and the estimand-preservation (FPR@true-0, MDE@TPR≥0.80, serial dependence, two
   structurally-different nulls, translation-equivariance, cost-free by location-invariance) are
   stated. Draws/cap/reportability bullets now read in resample semantics. Thresholds unchanged.
2. **Arm coverage reconciled** — 5 unified-engine arms calibrated; partial/trail deferred to EXP-091;
   binding MEMBER gate unchanged. The reused-components table corrected to the actual imports
   (`xen.ass` moving-block mean+median lower bounds, `xen.zigzag.wilder_atr`; `xen.expectancy`/`xen.wf`/
   `capgeo_cost` references removed).

**Plan ≡ code confirmed.** No other constraint check changed (holdout/look-ahead/real-price/
timestamp/per-stratum/budget/registry all still pass — see above). The revised plan introduces no
new method outside scope, no goalpost move, and no threshold change.

```text
VERDICT: APPROVE
```
