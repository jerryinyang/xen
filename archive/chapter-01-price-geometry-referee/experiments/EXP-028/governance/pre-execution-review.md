# Governance Review: Experiment EXP-028 — Pre-Execution (corrected)

**Date**: 2026-06-09
**Review Type**: Pre-Execution (consolidated, research-pipeline Stage 4)
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`,
`code/event_method.py`
**Phase**: 2026-06-08-006-avwap-evaluation-correction (ACTIVE)
**Supersedes**: the prior pre-execution review that APPROVED the uncorrected
(asymmetric-construction) version — that approval missed the Phase-005 framing
recurrence and is void.

## Executive Summary

A quality-review pass found the original scope/plan/code about to **repeat the
Phase-005 framing-divergence error in a new form**: applying the frozen EXP-027
yardstick to an estimand/construction it never calibrated (endogenous-exit event
vs. fixed-window control; asymmetric → mean-nonzero null → biased toward a false
negative in the EXP-024 direction). Operator decision: keep **both** constructions
with the EXP-022 **symmetric own-exit** controls as the **binding PRIMARY** and the
asymmetric construction as a **calibrated, non-binding SECONDARY**. All seven
findings are resolved across scope, plan, and a full code rebuild that also fixes
three hard bugs. The binding path reuses validated upstream machinery so it stays
inside the calibrated envelope. **Verdict: APPROVE**; numerical verification is
delegated to Stage 5 (audit) after the manual run.

## Findings resolved

| # | Finding | Resolution |
|---|---------|-----------|
| 1 | Asymmetric control out of EXP-027's envelope (false-negative bias) | Dual gate: **PRIMARY** = EXP-022 symmetric own-exit lifetime excess (binding; FPR control from sign-permutation exactness + EXP-027 sparse-count validation). **SECONDARY** = asymmetric construction, non-binding, weight-bearing only if its predeclared placebo-null shows FPR ≤ α₀ and null-excess ≈ 0. |
| 2 | Pyramid handling unspecified | **Included** (predeclared, closer-to-original): pyramids fed EXP-020 (~50%), EXP-021 (no filter), EXP-022 (SUPPORTED). `is_pyramid_bounce` retained as a diagnostic split; regime-cluster bootstrap absorbs the clustering. |
| 3 | Whole-file "frozen method" hash inconsistent with variable holds | Freeze scoped to named inference-tail functions (`verify_frozen_inference` hashes their source vs EXP-027); new return/eligibility code delineated. |
| 4 | EXP-027 MDE (H=3 units) misused as lifetime power threshold | AGAINST power from in-experiment CI half-width + counts; EXP-027 MDE applies only to the fixed-horizon anchor. |
| 5 | Degenerate secondary-horizon neutering | `decide_label` h1/h6 slots fed by EXP-021 validated fixed-horizon {1,6} excess. |
| 6 | Timebars file-selection / index-alignment hazard | EXP-020 loader (`xen.referee_calibration`, per-instrument by Symbol, holdout-fenced) → indices align; hard value-level `validate_alignment` guard. |
| 7 | Over-readable negative | Scope/plan/`run_metadata.interpretation_bound`: a PRIMARY EVAL_REFUTED is about the strategy-with-EXP-022-exit, not "the bounce event has no edge." |

## Hard bugs fixed in the rebuild

1. Global file `[-1]` selection (empty frames for 3/4 instruments) → EXP-020 per-instrument loader + alignment guard.
2. Broken join on `trigger_idx` (absent from lifetime CSV) → PRIMARY uses EXP-022 lifetime rows by `(instrument, domain, regime_id, direction, event_trigger_idx)`.
3. `from code.event_method` stdlib collision → local `import event_method`.

## Constraint checks

| Check | Verdict | Notes |
|-------|---------|-------|
| Per-event unit; no per-bar floor | PASS | Binding gate is per-event own-exit excess. |
| In-envelope yardstick (EXP-023 correction) | PASS | Binding construction is symmetric/calibrated; asymmetric is non-binding behind its null. |
| Holdout exclusion | PASS | First-70% lazy slice; trigger/start/completion fenced; right-censored excluded. |
| Look-ahead safety | PASS | Selection uses trigger-time info; forward closes are outcomes. |
| Real-price discipline | PASS | Direction-signed log bps on real `Close`; no synthetic prices; no costs. |
| Zero-baseline | PASS | Excess vs control mean; non-finite reported, never 0. |
| Determinism | PASS | `seed_for` throughout; equivalence + (run-time) replay flags recorded. |
| Complexity budget | PASS | 1 module / 4 plots / 4 tests (reused machinery for placebo-null/secondary/fixed-horizon). |
| Conventions | PASS | Sectioned; dirs in orchestration; lazy load; `tqdm`; vectorized reconciliation; bounded plots. |

## Residual risks (non-blocking; for Stage 5 + manual run)

1. Code not yet executed — `py_compile` clean and APIs/schemas verified; numerical correctness confirmed at run + audit.
2. Secondary placebo-null is multi-minute (per-placebo exit-rule scan × 100 draws); non-binding; draw count is a precision knob.
3. EXP-021/022 pure helpers reused via importlib (side-effect-free apart from Agg backend) — worth an audit glance.

## Verdict

```
VERDICT: APPROVE
```
