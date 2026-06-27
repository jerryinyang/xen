# EXP-050 — Pre-Execution Governance Review (Stage 4)

**Experiment:** EXP-050 — Phase 014-A Harami-in-Context: Position-in-Move of HA
Harami Signals vs Predeclared Baselines (ATR-ZigZag, 99 cells).
**Reviewed artifacts:** `scope.md`, `analysis-plan.md`,
`code/run_experiment.py`, `python/src/xen/move_position.py`.
**Reference frame:** `governance-constraints.md`, `_pipeline-config.md`,
`experiment-developer/references/code-conventions.md`, checkpoint
`2026-06-14-014-ha-harami-substrate-and-capture/design.md` (D0 ratified, G0 PASS).
**Date:** 2026-06-15.

---

## Phase-alignment check

Matches checkpoint §6 EXP-050 row (HYP-003 harami-in-context). Characterization:
**0 candidate slots, 0 TEST reads**, gross, descriptive. Gating precondition
satisfied — consumes EXP-048 `readiness_map.csv` (READINESS_DELIVERED + audit
PASS); cell membership = READY ∪ READY_FLAGGED = **99 cells** (verified: 86 READY
+ 13 READY_FLAGGED; 3 COVERAGE_EXCLUDED carried forward unmeasured). P9 (`pos ≥
0.67`, `Δ ≥ 0.10`) and P11 (≥5 cells/≥3 instruments) applied verbatim from D0 as a
mechanical readout; the 014-A G1 desk adjudication is **not** self-declared. No
phase misalignment.

## Core constraints

| # | Constraint | Verdict | Evidence |
|---|-----------|---------|----------|
| 1 | Simplicity | PASS | One inferential method (MBB); exact closed-form `FT_rand` is the simplest noise-free reference; assignment is a single vectorized interval-join over a precomputed segmentation. |
| 2 | No academic-finance pitfalls | PASS | Non-parametric throughout: empirical rates + moving-block bootstrap; no normality/stationarity/i.i.d./constant-vol assumption. MBB explicitly chosen to propagate serial dependence. |
| 3 | Strict scoping | PASS | Single falsifiable question; boundaries (views, 17 instruments, TRAIN range, exclusions) explicit; CONTEXT_CHARACTERISATION_DELIVERED / CONTEXT_REFUTED criteria measurable. |
| 4 | Framework principles | PASS | Data-driven; real-price outcome discipline; timestamp alignment (see below). |
| 5 | OOS holdout | PASS | F01 prefix loader: `scan_parquet(...).slice(0, train_rows).collect()` (metadata + first 49% only); full file never sorted/collected; every domain bar / `HA0Time` / `ConfirmTime` fenced to `train_end_ts` (`inv_fence`); TEST + final-30% never read. |
| 6 | Look-ahead prevention | PASS (with disclosed carve-out, see below) | ZigZag + harami detector are the frozen sequential modules, unedited; ordering by `CloseTime`/epoch. |
| 7 | Real/synthetic-price discipline | PASS | `P_sig` = real domain `Close` at `HA0Time` (== `RealClose`); HA used for **detection only**; no HA price enters any metric; no returns/P&L computed at all. |
| 8 | Safe performance/memory | PASS | Lazy scans + projection; per-cell bounded memory (`del train_1m`); plots from per-cell scalars + 20-bin histograms (no reload); MBB batched; `tqdm` outer loop. |

### Descriptive-allowance carve-out (constraint 6) — reviewed and accepted

The position metric `pos = (P_sig − StartPrice)/(EndPrice − StartPrice)`
references the move's confirmed **terminal pivot** `EndPrice`, which is future
information relative to a mid-move harami. This is the one look-ahead carve-out
and it is **properly bounded and predeclared**: scope §"Look-ahead/Causality
Discipline" and plan Step 1 "descriptive-allowance note" declare it a
non-tradable descriptive characterization of **completed** moves (D0 P9's
explicit completed-move-grouping allowance). Governance verified the bound is
honored in code: **no trading, signal, capture, return, or P&L computation exists
anywhere** in `run_experiment.py` — the experiment is purely descriptive (gross,
no exit, no cost, no return). The same allowance covers the random in-move
baseline and the MA-segmentation scoring symmetrically. Disclosed in
`run_metadata.json` (`metric` field). Not a violation.

## Plan ↔ scope reconciliation (FT_rand form)

The plan implements `FT_rand` as the **exact closed-form** direction-stratified
in-move rate (`Σ_d w_d·q_d`, the R→∞ limit) rather than the scope's sketched
finite matched-count resample. The approved `analysis-plan.md` documents this in
its *Reconciliation* section as pre-data-contact, tightening (removes Monte-Carlo
noise from a governance-binding number), and tuning nothing. This is an
authorized refinement **within** the approved plan, not post-approval scope
expansion. The binding materiality stays the D0 P9 point rule (`Δ ≥ 0.10 ∧
n_assigned ≥ 30`); the MBB CI is disclosed support only. PASS.

## Complexity budget

- **Statistical tests: 1 / 1** — regime-clustered moving-block bootstrap CI on
  `Δ` (`mbb_ci_delta`). `FT`, `FT_rand`, `FT_MA`, `FT_MA_rand`, `FT_dur` are
  deterministic point computations; `Δ ≥ 0.10` / `n_assigned ≥ 30` are
  descriptive gates. PASS.
- **Visualisations: 4 / 4** — FT heatmap, Δ-gap heatmap (CLUSTERED boxed),
  pooled position distribution (equal-weight per cell), assigned-count heatmap.
  PASS.
- **New modules: 1 / 1** — `python/src/xen/move_position.py`; the five frozen
  modules (`zigzag`, `ha_harami`, `heiken_ashi_generator`, `bar_aggregator`,
  `referee_calibration.ma_crossover_positions`) reused unchanged. PASS.

## Code-convention checks (developer REVISE triggers)

| Check | Verdict | Note |
|-------|---------|------|
| Output dirs created in `run()` not at import | PASS | `RESULTS_DIR.mkdir` / `PLOTS_DIR.mkdir` inside `run()`. |
| No data load / write / plot at import | PASS | Imports + path/constants only; `SeedSequence.spawn` is pure. |
| Lazy load → first-70%/TRAIN slice → collect, with projection | PASS | `load_train_1m` projects 8 cols, slices, collects. |
| No full-data materialization before holdout exclusion | PASS | Only `train_rows` prefix ever collected. |
| No silent dedupe | PASS | No `.unique()` in loader. |
| Bounded plotting (no large pandas conversion / reload) | PASS | Plots from collected scalars + 20-bin hists. |
| `tqdm` progress, helpers quiet | PASS | `tqdm(INSTRUMENTS)`; helpers return data. |
| Concise logging | PASS | `logging.getLogger`; summary only in `main()`. |
| Vectorization preserves causal/streaming semantics | PASS | Interval-join, run-length MA segmentation (`np.diff`/`flatnonzero`), histogram, MBB index math vectorized; sequential ZigZag/HA detector remain inside frozen modules; bounded loops only over 99 cells and bootstrap batches. |
| Zero-baseline handling finite | PASS | `n_assigned<30` → `NOT_REPORTABLE_BY_POWER`; `Δ` is an absolute pp gap vs an explicit random reference (no % over a zero baseline); exclusion classes partition `n_haramis_total` (`inv_assignment`). |
| Duplicate-source event denominator defined | PASS | One harami per `HA0Time`; `HA0Time` unique per domain bar (HA 1:1); harami→bar join is 1:1; `n_unmatched_excl` invariant guards misses. |
| Timestamp alignment, never bar index across views | PASS | Cross-view joins (haramis↔moves↔MA regimes) by timestamp interval. Duration-fraction uses bar indices **within a single domain view** (legitimate intra-view duration metric, not cross-view alignment). |
| Type hints / docstrings / NaN handling / edge cases | PASS | Public fns typed + documented; empty-moves / empty-events / <2-bar / zero-span guards present; smoke-tested on synthetic data. |
| Derived-view determinism | PASS | Second full pass `core1 == core2` (incl. CI bounds); per-cell RNG deterministically spawned by global cell index. Verified True on smoke. |

## Edge-case / numerical sanity (from developer smoke evidence)

Isolated `move_position` unit test passes (boundary `t == EndTime`, all four
exclusion classes, baseline `Σ w_d q_d`, duration, empty inputs); synthetic-data
integration smoke of `compute_core` returns determinism=True, all invariants 0,
exact exclusion partition, all secondaries populated, four plots render. No
correctness concern surfaced.

---

## Verdict

```text
VERDICT: APPROVE
```

All core constraints, the holdout fence, the look-ahead carve-out bound, the
real-price discipline, the complexity budget, and the developer code conventions
pass. No Critical or Warning issues. Info notes (non-blocking): (i) the
`FT_rand` closed-form is a plan-authorized refinement of the scope sketch; (ii)
the position metric's terminal-pivot look-ahead is the predeclared, bounded,
non-tradable descriptive carve-out and is honored (no P&L/signal consumes it).
Cleared for the manual execution gate.
