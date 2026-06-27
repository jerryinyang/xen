# Governance Review: Experiment EXP-052 — Pre-Execution

**Date**: 2026-06-15
**Review Type**: Pre-Execution (Stage 4, consolidated)
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`,
`python/src/xen/confirm_entry.py`

## Executive Summary

All core, framework, and artifact-specific constraints pass. EXP-052 is a
descriptive Phase 014-A characterization (HYP-005, `CF-HA-HARAMI-001/CONFIRM`):
gross, TRAIN-only, 0 candidate slots, 0 TEST reads, no viability gate. Verdict:
**APPROVE**.

## Constraint Checks

### Simplicity
| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope / plan / code | PASS | Medians + moving-block bootstrap CIs + an explicit causal fill scan — the simplest sufficient toolkit for a descriptive two-arm comparison. No model fitting. Reuses validated `xen.capture_barriers`/`zigzag`/`ha_harami` machinery; one new module. |

### Academic-Finance Pitfall
| Artifact | Verdict | Notes |
|----------|---------|-------|
| plan / code | PASS | Non-parametric throughout (rank/median, block bootstrap respecting serial dependence). No normality / stationarity / i.i.d. / constant-volatility assumption. ATR-normalization is a scale, not a distributional claim. |

### Scope Compliance
| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope | PASS | Single question (direct vs signal+confirmation descriptive properties). Boundaries explicit: 99 EXP-048 READY∪READY_FLAGGED cells (3 COVERAGE_EXCLUDED dropped), 17 instruments, 6 domains, TRAIN-only first-49% F01 prefix, exclusions enumerated. Criteria concrete (delivery verdict + REFUTED on non-determinism or a battery invariant on ≥3 instruments; cell-level NOT_REPORTABLE at n<30). |
| code | PASS | Implements exactly the plan; the optional position-in-move secondary was omitted (plan marked it optional) — no binding item dropped, no bonus analyses added. |

### Principles Check
| Artifact | Data-Driven | Non-Parametric | Real/Synthetic-Price Discipline | Holdout Excluded |
|----------|------------|---------------|--------------------------------|-----------------|
| scope/plan/code | PASS | PASS | PASS — all outcomes (MFE/MAE, fav-before-adv `r`) on real domain OHLC; HA candles feed `detect_ha_harami` only; stop levels are `RealHigh`/`RealLow`; no `HAClose` enters any metric | PASS — F01 first-49% prefix; full file never sorted/collected; TEST + final-30% holdout never read; `train_end_ts` fence asserted |

### Look-Ahead / Timestamp Alignment
| Check | Verdict | Notes |
|-------|---------|-------|
| Causality of entries/fills | PASS | `rd` uses only moves confirmed ≤ `HA0Time`; the stop is the signal bar's own extreme; the first-touch fill is a per-bar causal scan; MFE/MAE read only the bounded forward window from entry; ATR at bar `e` uses bars ≤ `e`. |
| Forward completed-move reference | PASS (Info-1) | The CONFIRM window endpoint (next ZigZag confirmation) and the `lead` metric use a forward completed-move boundary under the **declared descriptive completed-move allowance** (identical to the EXP-050/051 governance-accepted carve-out), capped by the strictly-causal `s + N_event`. It never enters a tradable entry/price/P&L decision — it bounds a descriptive lead/fill measurement only. Disclosed in scope §Look-ahead, plan, and `run_metadata.json`. |
| Alignment | PASS | All view alignment by `CloseTime` epoch (`exact_bar_indices`, `searchsorted`); never by bar index. |

### Safe Performance / Memory
| Check | Verdict | Notes |
|-------|---------|-------|
| Polars / memory / vectorization / progress | PASS | Lazy scan + first-prefix slice + column projection; per-cell bounded memory (`del train_1m`); bootstrap batched (`BOOT_MAX_ELEMS`); plots built from per-cell scalars (no reloads); `tqdm` over instruments; the genuinely-sequential first-touch fill kept an explicit bounded loop, vectorization used only on causally-safe steps. |

### Code-Specific
| Check | Verdict | Notes |
|-------|---------|-------|
| Plan compliance / type hints / NaN / edge cases / separation / sectioning / import side-effects / determinism | PASS | Public functions typed + docstdring'd; explicit NaN handling (`np.isfinite`, `errstate` guards, None for empties); empty-moves/haramis and n_signals=0 paths; dirs created only in `run()`; `matplotlib.use("Agg")` before pyplot; two-pass determinism replay with fixed per-(cell,statistic) seeds. Byte-compiles; `confirm_entry` primitives pass synthetic unit tests. |
| Zero-baseline / denominators | PASS | `fill_rate = n_fills/n_signals` (0, never 0/0); `<30` → NOT_REPORTABLE_BY_POWER; secondary `r` over resolved≥30 only; paired Δ is an **absolute** median difference (no percentage-over-zero-baseline); `ATR[e] > 0` asserted before normalization. Scoped event denominators (`n_signals`, `resolved`, paired set) defined before implementation. |

### Signal-Registry Precondition (programme file-drawer control)
| Check | Verdict | Notes |
|-------|---------|-------|
| Family / variant registered | PASS | `CF-HA-HARAMI-001` `REGISTERED`; `CF-HA-HARAMI-001/CONFIRM` + HYP-005/EXP-052 entered in `multiplicity-registry.md` (Phase 014 batch, rows for HYP-005 and the variant surface). |
| New countable item | PASS | The `/CONFIRM` rule defaults (stop = signal-bar real extreme; window = until next ZigZag confirmation, capped at P4; MFE/MAE + symmetric `r` outcomes) are **characterization parameters within the already-registered branch**, not a new variant/detector/parameter branch — 0 slots, consistent with the Phase 014 batch's "characterization consumes no slot" accounting. |
| TEST-stratum read | PASS | None. TRAIN-only; current counted-read tally for every member stratum = 0 and EXP-052 adds none — no `test-read-ledger.md` entry required. |

### Phase Alignment
PASS — EXP-052 is the final 014-A primitive (design §6 table); consistent with the
active checkpoint objective (validate each primitive before any 014-B combined work).

## Findings

### Critical
None.

### Warnings
None.

### Info
1. **Forward completed-move reference (window endpoint + lead).** Acceptable under
   the declared descriptive completed-move allowance (EXP-050/051 precedent), capped
   by the causal `s + N_event`, used for no tradable decision. The auditor should
   confirm the causality/TRAIN-fence invariants empirically at Stage 5 (the code
   asserts them per cell).
2. **Runtime.** The per-event sequential fill scan + determinism replay may take
   ~10–15 min on 5m cells; bounded and `tqdm`-tracked. Not a blocker.
3. **Secondary `r` anchoring.** The disclosed fav-before-adv `r` anchors barriers at
   the harami-arm entries (not EXP-049's ZigZag-confirmation anchor), so comparability
   to EXP-049's `r ≈ 0.50` is approximate — disclosed as secondary/non-binding in
   scope, plan, and metadata.

## Verdict

```
VERDICT: APPROVE
```
