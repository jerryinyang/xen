# EXP-054 — Pre-Execution Governance Review (Stage 4)

**Reviewed artifacts:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**Against:** `references/governance-constraints.md`, `_pipeline-config.md`,
developer `code-conventions.md`, checkpoint `014-B-design.md` + `014-B-D0-addendum.md`,
signal registry (`candidate-families/harami.md`, `multiplicity-registry.md`, `test-read-ledger.md`).
**Date:** 2026-06-16.

---

## Signal-registry preconditions (programme file-drawer control)

- **Family `REGISTERED`.** `CF-HA-HARAMI-001` is `REGISTERED` (harami.md:3). ✓
- **Item registered.** `CF-HA-HARAMI-001/HYP-007` — **EXP-054** is in
  `multiplicity-registry.md` (Phase 014-B batch), status **PLANNED**, **0 slots / 0 TEST**.
  The fill-model standard (P15) is registered in `candidate-families/harami.md:276`. ✓
- **No TEST read.** Scope declares **0 TEST reads, TRAIN-only**; the nested analysis-set
  TEST stratum is not read and the final-30% global holdout is never loaded. No
  `test-read-ledger.md` tally applies and none is required. ✓
- **Mandatory-reading precondition (014-B).** Scope records that
  `014-A-conditioning-gap-and-validation-lessons.md` was read and explicitly addresses
  rules (a)-(d): (a) conditioning and (b) harami-anchor are **intentionally inverted by the
  014-B design's own instruction** (EXP-054 re-reads the *unconditioned, ZigZag-anchored*
  EXP-049 benchmark — that is the object under test); (c) position-in-move not used; (d)
  expectancy endpoint honored as a **disclosed secondary** while first-hit `r` is the binding
  *comparison* metric (justified: the mechanism under test is first-hit barrier resolution,
  no partial exits). The honoring is recorded for this check, as required. ✓

## Core constraints

- **Holdout / OOS (§5).** `load_train_1m` reads only Parquet metadata + the first
  `train_rows` file-order rows via `slice(0, train_rows)` (no full-file sort/collect);
  asserts the slice is `CloseTime`-sorted; `build_domain` fences every domain bar to
  `CloseTime <= train_end_epoch`; forward windows are clipped to `n_bars-1` (TRAIN edge).
  No code path touches TEST or the final 30%. ✓
- **Look-ahead / causality (§6).** Resolvers scan strictly `[confirm_idx+1,
  min(confirm_idx+N, n_bars-1)]`; P15 disambiguates a tie using **only the resolving bar's own
  O/H/L/C**; barriers use the just-confirmed move and strictly-prior confirmations; ZigZag is
  causal. Alignment is by `CloseTime` epochs (`confirm_indices` searchsorted), never bar index
  across views. ✓
- **Real-price discipline (§7).** Every barrier, fill, `r`, expectancy, and ATR figure is on
  real domain OHLC; the HA harami detector is not imported or used; no HA/Renko price enters any
  metric. ✓
- **Single hypothesis & budget (§3).** One falsifiable question (does P15 materially change the
  EXP-049 benchmark readout?). Budget: **1 statistical method** — the regime-clustered
  moving-block bootstrap, applied to `r` (G1+G2) and **reused** for the median-expectancy
  statistic (identical block construction; only the statistic differs, as the plan declares —
  no second inferential method). **4 plots** (Δr, dt_frac, P15 viability-status with
  TIE_BREAK_SENSITIVE marked, paired r scatter). **0 new modules** — reuses `xen.zigzag`,
  `xen.bar_aggregator`, `xen.capture_barriers`, `xen.expectancy` (the P15 resolver pre-exists
  there); the two orchestration-local helpers (`worstcase_exit_prices`, `first_touch_tie_flags`)
  live in the experiment script, as the scope permits. ✓
- **Denominators / zero-baseline.** `r = FAV/(FAV+ADV)` over resolved; `resolved < 30` →
  `NOT_VIABLE_BY_POWER` (never `0/0`); `dt_frac`/`reassigned_frac` → `None` when `resolved == 0`;
  expectancy `< 30` qualifying → `NOT_VIABLE_BY_POWER`; `g2_degenerate_frac` denominator =
  G2 candidate pool, `None` when empty. No percentage-over-zero-baseline. ✓
- **Safe optimization (§8).** The genuinely sequential first-touch resolvers and the tie scan
  are kept explicit and bounded (their causal semantics are the object under test);
  `worstcase_exit_prices` is vectorized only because it is a pure per-event lookup (no sequential
  dependence). Lazy Polars scan with column projection; per-cell bounded memory (`del train_1m`);
  `tqdm` on the instrument loop; plots render from the collected per-cell summary (no reloads). ✓

## Code-specific checks

- Organization (imports → path → constants → I/O → pure → plotting → orchestration → `main()`),
  VAL-001 sectioning, type hints + docstrings on public functions, output dirs created in `run()`
  only, no import-time side effects, concise logging (helpers return data), explicit NaN handling
  and edge cases (empty/zero-move cores), deterministic seeds (documented per-leg RNG streams).
  `py_compile` OK, `ruff` clean, all lines ≤ 100. ✓
- **Correctness gates present (match scope §8 / Reconciliation anchors):** EXP-049 reconciliation
  (worst-case leg vs `per_cell_capture.parquet`, exact counts + CI within 1e-12), per-cell
  monotonicity (`resolved` equal, `FAV_P15 ≥ FAV_wc`, `Δr ≥ 0`, reassigned set ⊆ tie set), and a
  two-pass determinism replay — any failure emits `SUBSTRATE_METHOD_DEFECT` (the experiment emits
  the readout; it does not self-declare the §8 routing). The central monotonicity/resolved-set
  invariants were confirmed on a synthetic battery before this review. ✓

## Phase alignment

EXP-054 is the registered **Lead 2** of the 014-B slate (`014-B-design.md` §5), satisfying the
Phase-010-carried "intrabar exit fills DEFERRED behind a dedicated fill-rule method validation."
It re-reads the EXP-049 benchmark by design and routes to §8 SUBSTRATE/METHOD_DEFECT only if the
benchmark flips materially under P15. No intermediate gate is self-declared. ✓

## Info notes (non-blocking)

1. **Expectancy on the binding G1 geometry only.** The P14 median-expectancy disclosure is
   computed for G1 (the binding benchmark object); G2 expectancy is not required by scope. This
   is the natural reading of the scope's per-cell expectancy disclosure — not a deviation.
2. **Block bootstrap reused for two statistics.** The same moving-block bootstrap family serves
   both the proportion `r` and the median expectancy; the plan declares this as one method. This
   is consistent with the "max 1 statistical test" budget.

---

```text
VERDICT: APPROVE
```
