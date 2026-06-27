# Governance Review: Experiment EXP-048 — Pre-Execution

**Date**: 2026-06-14
**Review Type**: Pre-Execution (consolidated pipeline governance, Stage 4)
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`,
`code/run_experiment.py`, new modules `python/src/xen/zigzag.py` and
`python/src/xen/ha_harami.py`, against the active checkpoint
`2026-06-14-014-ha-harami-substrate-and-capture/design.md` + `D0-predeclarations.md`
and the governance constraints.

## Executive Summary

EXP-048 is a TRAIN-only, gross, descriptive substrate/detector readiness
experiment (HYP-001, `CF-HA-HARAMI-001`), 0 candidate slots, 0 TEST reads. The
scope, plan, and code are mutually consistent, phase-aligned, holdout/TEST-safe,
causally sound, and within the complexity budget. One faithfulness gap (5m
dropped-fraction flagging vs the predeclared "5m strict has none") was corrected
in code before this verdict. **APPROVE.**

## Phase Alignment

- Design §6 lists EXP-048 as the Phase 014-A EXP-020-analog substrate/detector
  readiness item, **gated on §5 VAL PASS for 15m/30m**. VAL-004 PASSED 2026-06-14
  (all 17×{15m,30m} ADMITTED, dropped 0.003–0.133) → gate satisfied; all 102
  cells domain-eligible. ✓
- Registry Phase 014 batch lists `CF-HA-HARAMI-001/HYP-001 — EXP-048`, 0/0
  slot/TEST. Scope matches (0 slots, 0 TEST reads, holdouts sealed). ✓
- Two primitives validated **separately** (no combined harami-at-exhaustion event,
  no capture/3-barrier, no strong-move filters, no `/CONFIRM`) — matches the
  "separation of components" design principle and defers EXP-049–052 scope. ✓
- D0 parameters honored: P1 Wilder ATR-14, `ATR_MULT=1.0`; `/BARCFG` coverage
  measured not assumed; gross, no cost model. ✓

## Constraint Checks

### Simplicity Check
| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope/plan/code | PASS | Descriptive readiness + invariant/determinism verification; 0 statistical tests. Two new modules are necessary (no existing ZigZag/harami primitive); reuse of `bar_aggregator`/`heiken_ashi_generator` unchanged. Wilder ATR precomputed causally; ZigZag confirmation kept as an explicit sequential loop. |

### Academic-Finance Pitfall Check
| Artifact | Verdict | Notes |
|----------|---------|-------|
| all | PASS | No normality/stationarity/i.i.d./constant-volatility assumption. Pure deterministic construction + counting. No statistical inference. |

### Scope Compliance Check
| Artifact | Verdict | Notes |
|----------|---------|-------|
| Single question | PASS | One question: can both primitives be computed deterministically, look-ahead-safe, invariant-clean across 102 cells, with measured coverage. |
| Boundaries/criteria | PASS | Instruments (17), domains (6), TRAIN-only stratum, parameters, exclusions all explicit; READY / NOT_READY / COVERAGE_EXCLUDED / CONSTRUCTED_EMPTY and SUBSTRATE_REFUTED are mechanical. |
| Budget | PASS | 0/0 stat tests, 4/4 plots, 2/2 modules. Code emits exactly these (no bonus analyses). |

### Principles Check
| Artifact | Data-Driven | Non-Parametric | Synthetic-Price Discipline | Holdout Excluded |
|----------|------------|----------------|----------------------------|------------------|
| all | PASS (coverage measured, not assumed) | PASS (no distributional assumptions) | PASS (ZigZag on real bars; harami detected on HA candles but **no** return/excursion/P&L metric is computed anywhere — design-permitted) | PASS (final 30% never read; TRAIN-only first-49% via F01 prefix; TEST stratum unread; metadata-only split) |

### Look-Ahead / Causality Check
| Check | Verdict | Notes |
|-------|---------|-------|
| Sequential generation | PASS | ZigZag is an explicit streaming state machine; ATR causal (precomputed Wilder filter uses only bars ≤ t); harami uses only current + immediately prior HA candle. |
| Confirm-after-pivot | PASS | The extreme is never updated on the confirming bar, so `ConfirmTime > EndTime` strictly (synthetic smoke: holds on all moves); an explicit invariant counts any breach. |
| Pivot-as-future-info | PASS | Retroactive pivot used only to label boundaries of an already-completed move, never as a point-in-time signal. |
| Timestamp alignment | PASS | All ordering/fencing by `CloseTime` epoch seconds; never bar index. |
| TRAIN fence | PASS | Every domain bar fenced to `CloseTime ≤ train_end_ts`; moves/events inherit; within-train invariants re-verify. |

### Safe Performance / Memory Check
| Check | Verdict | Notes |
|-------|---------|-------|
| Lazy/bounded | PASS | Lazy scan + column projection + first-49% slice before collect; per-instrument frame loaded once for all 6 domains then released; plots from the 102-row summary (no reloads / no millions-of-rows pandas). |
| Safe vectorization | PASS | ZigZag confirmation left as a sequential loop (causality under test); only safe ops (ATR filter, harami one-row shift, aggregation, group_by) vectorized — all causally equivalent. |
| Progress | PASS | `tqdm` over the 17-instrument outer loop; concise logging; helpers return data. |

### Denominator / Zero-Baseline Check (specific REVISE-trigger area)
| Check | Verdict | Notes |
|-------|---------|-------|
| Denominators predeclared | PASS | Move rate = moves/1000 TRAIN domain bars; harami rate = events/1000 HA candles; `/BARCFG` = config events/total harami events — all stated in scope/plan and implemented identically. |
| Zero-baseline finite | PASS | 0 moves/events → rate 0.0 with disclosed denominator; 0 harami → `/BARCFG` null (non-reportable), never `0/0`; CONSTRUCTED_EMPTY guard for TRAIN bars < ATR warmup; no percentage-vs-zero-baseline anywhere. |
| Event denominators defined | PASS | Two primitives emit different counts; each rate uses its own per-cell denominator; no cross-view normalization (cross-view alignment deferred to EXP-050). |

### Code Quality Check
| Check | Verdict | Notes |
|-------|---------|-------|
| Organization/sectioning | PASS | imports → path setup → constants → I/O → pure compute → plotting → orchestration → `main()`, VAL-001-style separators. Local `xen` imports placed after path setup with `noqa: E402` (established EXP-047 pattern; `xen` is editable-installed so harmless). |
| Import side effects | PASS | `results/`/`plots/` created in `run()`, not at import; only `matplotlib.use("Agg")` at import (standard). |
| Types/docstrings/NaN/edge | PASS | Type hints + docstrings on public functions; ATR NaN-before-seed handled; empty-frame, `candidate==0`, `n_bars<14` guards present. |
| Determinism | PASS | All generators deterministic; no randomness (no seed needed — stated in plan); determinism replay via exact `DataFrame.equals`. |

## Findings

### Critical
None.

### Warnings
None.

### Info
1. **(Resolved before verdict)** The 5m strict domain originally could be marked
   `READY_FLAGGED` from its dropped-window fraction, but the scope predeclares the
   dropped-fraction thresholds for "15m/30m/1h/2h/4h **only**; 5m strict has none."
   Code corrected so both `coverage_excluded` and `flagged_disclosure` are gated to
   `min_coverage`-mode domains; 5m is never coverage-flagged. Re-compiled clean.
2. Local-import ordering after path setup (`noqa: E402`) follows the audited
   EXP-047 precedent; acceptable, not a violation.
3. Pre-execution synthetic smoke of both modules (off-data) confirmed: ATR defined
   at bar 14, move alternation, strict `confirm>pivot`, monotonic confirms, zero
   threshold breaches, determinism for both primitives, and reduced-form ≡ original
   harami predicate. Real-data behavior is verified at audit (Stage 5).

## Addendum — Minor review findings incorporated pre-execution (2026-06-14)

Three Minor code-review findings were raised after the initial APPROVE and
resolved **before any data contact** (a pre-execution plan refinement, not
results-driven goalpost-moving). The verdict is unchanged.

- **F01 — determinism replay did not re-aggregate.** Scope §4 / plan Step 7
  require the second pass to re-aggregate, re-generate HA, and re-run both
  primitives. `process_cell` now re-runs `build_domain` in the replay and compares
  the domain bars **and** the move/event tables frame-identical. Implements the
  predeclared check exactly. (Resolved.)
- **F02 — `/BARCFG` composition plot over-weighted sparse cells.** The plot used an
  unweighted mean of per-cell fractions. Changed to **event-pooled within each
  domain** (sum config_k / sum total harami over harami-bearing cells) with the
  per-domain pooled event count annotated, so sparse domains are visually
  distinguishable and noisy per-cell fractions no longer dominate. The
  analysis-plan plot-4 description was updated to match. Descriptive plot only — no
  binding endpoint. (Resolved.)
- **F03 — `CONSTRUCTED_EMPTY` set `coverage_excluded=True`.** The empty-cell record
  now sets `coverage_excluded=False` and `flagged_disclosure=False`, so the CSV
  diagnostics align with the adjudicated status (`CONSTRUCTED_EMPTY` trumps coverage
  exclusion). (Resolved.)

Re-compiled clean; synthetic re-smoke confirmed the re-aggregating determinism
path, the consistent empty-cell diagnostics, and the pooled `/BARCFG` plot. The
construction-integrity check was observed firing correctly on a degenerate
synthetic frame (live check). Real-data behavior is verified at audit (Stage 5).

## Verdict

```
VERDICT: APPROVE
```
