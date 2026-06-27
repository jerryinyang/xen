# EXP-087 — Pre-Execution Governance Review (Stage 4)

**Reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `python/src/xen/cross_sectional.py`
**Against:** `research-pipeline/references/governance-constraints.md`, `_pipeline-config.md`, code conventions, Phase 019 checkpoint design + D0/D0-amendment-002.
**Date:** 2026-06-22

---

## Signal-registry precondition (programme file-drawer control) — PASS

- **Multiplicity registry:** EXP-087 is registered — row present (`multiplicity-registry.md:741`), axis **X** = `CF-XSECT-001/HYP-001`; the two countable conditioning primitives (`COND-XSRANK`, `COND-XSDIV`) are listed under the Phase 019 information-axes inventory (`:722`). No new un-registered countable item is introduced by the scope.
- **Candidate family:** `candidate-families/family-selection-phase-019.md` present; `CF-XSECT-001` carried `DRAFT — PENDING-SELECTION` (correct for a 0-slot family-selection availability screen; an `ADMITTED` axis opens at its own future G0/D0).
- **TEST-read ledger:** all 16 instruments × {15m,1h,4h} = 48 strata at **0/2 counted reads, open** (re-materialized 2026-06-21 on VAL-005 PASS). EXP-087 reads only the **TRAIN sub-stratum** (`[0, train_cutoff)`), makes no stratum-specific selection/inference → **0 counted TEST reads**; ledger unchanged. Scope states the tally and the TRAIN-only convention (EXP-074/075/080/081/086 precedent). **No TEST-stratum read is planned.**

## Phase alignment — PASS

Phase 019 (Family-Selection Availability Screen) is OPEN; G0 PASS 2026-06-22, D2b admission-gate bite-check GREEN. EXP-087 is the **Screen X** slate item explicitly named "Next" after EXP-086 (Screen M) completed. It is an EXP-081/EXP-086 clone with the information axis swapped — directly on the checkpoint's planned path. No phase misalignment.

---

## Core constraint checks

| # | Constraint | Verdict | Evidence |
|---|------------|---------|----------|
| 1 | Simplicity | PASS | Reuses the certified EXP-086 gate + EXP-080/081 substrate scaffolding unchanged; exactly ONE new module (`xen.cross_sectional`). Lighter than Screen M (single directional read, no magnitude-budget). Intersection-only-grid simpler alternative considered and rejected with reason (analysis-plan Step 1). |
| 2 | No academic-finance pitfalls | PASS | All estimators non-parametric / resampling: median, proportion, moving-block bootstrap SE (conditioned, serial-dependence-preserving), label-permutation null. No normality/stationarity/i.i.d./constant-vol assumption gates any verdict. |
| 3 | Strict scoping | PASS | Single falsifiable question (cross-sectional × directional cell of the 2×2). Boundaries, denominators, zero-baseline behaviour all predeclared. Budget: 2 stat tests / 4 plots / 1 module — matches implementation exactly. |
| 4 | Framework principles | PASS | Data-driven; per-stratum default (LESSON-001); real-price discipline; timestamp alignment (see below). |
| 5 | OOS holdout | PASS | `train_cutoff = int(int(total_rows*0.7)*0.7)` via VAL-005 `load_first70` (first-70% `frame`) then `slice(0, train_cutoff)`. Union grid built from TRAIN domain bars only; `lifetime_path_geometry` clips windows at `n_bars-1` (TRAIN edge); `random_entries` + permutation pool draw only from `[0, n_bars)`. No code path materializes a row at/beyond `analysis_rows`. Split located via Parquet metadata. |
| 6 | Look-ahead prevention | PASS | `trailing_logret` uses only bars ≤ t; forward-fill is `searchsorted(side='right')-1` (strictly backward, unit-tested); events fire only at the instrument's own completed-bar close (mapped to its own domain-bar index); adaptive cap reuses moves confirmed strictly before t_i; all alignment by `CloseTime`/epoch, **never bar index** for the cross-view. |
| 7 | Real-price discipline | PASS | Every figure — 20-bar return, basket mean, ATR, directional `MFE` — on real domain OHLC (`_real_ohlc`, `wilder_atr`, `lifetime_path_geometry`). No HA/Renko/synthetic price anywhere (no chart-type generator imported). |
| 8 | Safe perf/memory | PASS | Lazy scans via VAL-005 loader; vectorized union-grid/fill/decile/permutation; the only explicit loops are the reused frozen causal path loop and the bounded cell loop; domain frames released per domain; pool computed once per (cell, primitive); `tqdm` on domain + per-domain-cell loops; plot inputs bounded (summaries + bounded per-event MFE). |

## Per-stratum verdict doctrine (EXP-076 C1 precedent) — PASS

The binding research output is the **per-cell** beats-random table plus the predeclared **D2b axis-level admission gate** (`S_X` vs `S*`), which is the frozen, bite-check-certified binding statistic — not an ad-hoc collapsed conjunction. The per-cell table is emitted in full (`cell_availability.*`). The provisional axis disposition is explicitly **captioned NON-BINDING** (G-019 is binding). The only `.all()` collapses (`recon_all`, `determinism_ok`) are **process-integrity HALT gates**, not the research verdict — correct usage. Any pooled figure is disclosure-only. Consistent with EXP-086 (passed governance).

## Gate-threshold calibration — PASS

All binding constants frozen pre-data: `z=1.645`, `S*=Q95`, FWER band {0.025,0.05,0.10}, `N_PERM=5000` (with 1000-vs-5000 MC-stability disclosure), `EVENT_FLOOR=30`, `LOOKBACK=20`, `DECILE_Q=0.10`, `MIN_XS_INSTR=8` — frozen at D0/D0-amendment-002/GREEN bite-check, carried in `xen.availability_gate`/`xen.cross_sectional`, recorded in `run_metadata.json`. None is an unjustified magic constant; the FWER band is a pre-registered sensitivity sweep, not a selection.

## Shape-aware / robust-vs-raw reads

N/A as a defect: Screen X's endpoint is **directional-favourable availability** (`MFE_med`) by design (D3.X) — the cross-sectional anomaly is directional by construction, so there is deliberately no split typical/tail read or magnitude-budget (that is Screen M only). The median endpoint is the family's predeclared robust read (catastrophe-tail lesson). This matches the frozen D0 endpoint specification.

## Code-conventions / artifact checks — PASS

Organization/sectioning (VAL-001 style), no import-time side effects (dirs created only in `main()`), type hints + docstrings on public functions, explicit NaN/empty/edge handling (warmup / ATR-undefined / clipped-empty / `<MIN_XS_INSTR` all counted and excluded, never folded), add-one permuted-p, concise logging, deterministic seeded RNG with a byte-identical second pass (metrics + permutation stream), bounded plotting. Verified by byte-compile, clean import (zero side effects), and a synthetic unit test of the new module (causality, decile direction, own-bar mapping, ascending/in-bounds entries, `MIN_XS_INSTR` exclusion) + the direction-mix helper.

---

## VERDICT

```text
VERDICT: APPROVE
```

No Critical or Warning issues. The implementation faithfully realizes the approved scope and analysis plan, honours the holdout fence and TRAIN-only convention (0 counted TEST reads), enforces causal cross-sectional construction, keeps all metrics on real prices, stays within the complexity budget, and emits per-stratum results with a clearly non-binding provisional disposition. Cleared for the manual execution gate.
