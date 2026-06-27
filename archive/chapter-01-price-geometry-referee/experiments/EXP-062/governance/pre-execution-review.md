# Pre-Execution Governance Review — EXP-062 (dual-object re-run)

**Reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py` (and the unchanged
`code/availability.py`) against the Phase 015 D0 (`design.md`, `D0-predeclarations.md`,
`D0-amendment-001-dual-parallel-substrate.md`) and the bundled governance constraints.
**Date:** 2026-06-17 (supersedes the prior single-object pre-execution review).

**Context:** Re-run under Amendment 001. The prior EXP-062 measured a single MA availability arm
labelled "hybrid" but actually conditioning on MA-segment `/STRONG-STAT` (the **native** object). This
re-run emits **both** objects individually — native `A_MA_nat` and the genuinely-new hybrid `A_MA_hyb`
— never pooled, and supersedes the prior result in place.

## Checks

- **Mandatory-reading precondition (014-A lessons):** recorded in `scope.md` with the four rules
  (conditioning disambiguated hybrid/native; harami-anchor at `C`; descriptive-position not a filter;
  availability endpoint MFE/MAE median, not first-hit `r`). PASS.
- **Registry precondition (programme file-drawer control):** `CF-HA-HARAMI-001` is REGISTERED/OPEN;
  `MA-SUBSTRATE` and both `hybrid`/`native` conditioning modes are registered (G0 PASS 2026-06-17, P11).
  **No new countable item** is introduced. 0 candidate slots, 0 TEST reads. No TEST stratum is read
  (TRAIN-only, F01 prefix); `test-read-ledger.md` needs no entry. PASS.
- **Holdout fence:** `load_train_1m` reads only Parquet metadata + the first `train_rows` file-order
  rows (`scan.slice(0, train_rows)`); never sorts/collects the full file; domain bars fenced to
  `CloseTime ≤ train_end_ts`; excursion windows end at the M_b crossover inside TRAIN (else
  `DATA_CENSORED`). TEST + final-30% holdout never touched. PASS.
- **Dual-object discipline (Amendment 001):** native and hybrid carry separate binding arms, separate
  matched-random nulls (`RM_MA_nat` / `RM_MA_hyb`, matched to their own counts, excluding their own
  signal entries, on disjoint RNG purposes), separate per-cell `MOVE_AVAILABLE` / `SIGNAL_ATTRIBUTABLE`
  classification (`_classify_object` per `nat`/`hyb`), separate P11+P6 composition (`_object_readout`),
  and a separate AVAILABILITY_* verdict. No arm pools or averages across objects; the phase verdict is
  the stronger object's, both emitted. PASS.
- **Reconciliation roles (corrected, P12):** native `A_MA_nat` reproduces EXP-055 `ma_seg` (m + median
  MFE + median MAE to 1e-9); `A_ZZ` reproduces EXP-055 `stat`; hybrid `A_MA_hyb` has **no** outcome
  anchor — its conditioning mask is the same mask defining `A_ZZ`'s population (verified transitively via
  the `A_ZZ` count/digest). `exp055_reconciliation` checks native + ZigZag; a missing/empty anchor is a
  defect. PASS.
- **Real-price discipline:** detection on HA candles only; MFE/MAE/`M_sofar`/ATR/reference-multiples on
  real OHLC; MA(20,50) on real close; no HA price in any metric; reference band never subtracted. PASS.
- **Causality / look-ahead:** MA `_sma` trailing; segments bounded by pre-entry crossovers; signal +
  `M_sofar` from `live_in_progress_state` (pre-entry only); matched-random entries causal; lifetime
  window `c1,c2` descriptive completed-move grouping (P19); excursions read only `[e+1, c2]`. The shared
  MA window applies to both objects' qualifying subsets; `_causality_ok` covers MA + ZigZag references;
  `window_invariants_ok` checks the MA window. PASS.
- **Determinism / RNG:** fixed per-cell seed `(BASE_SEED, cell_index, purpose)`; native arm/null/contrast
  purposes byte-identical to the prior EXP-062; new hybrid arms use fresh dedicated purposes (no stream
  shift); the first-usable-cell determinism replay (`cells_identical`) covers all eight arms (both
  objects, both MA nulls, ZigZag/HA/MAD), all three contrasts, and both population digests; byte-identical
  across `--workers`. PASS.
- **Matched-count invariant (P5), per object:** `RM_MA_nat.draw_count == A_MA_nat.m`;
  `RM_MA_hyb.draw_count == A_MA_hyb.m`; `RM_ZZ.draw_count == A_zz.m` — checked per cell in `compute_cell`.
  PASS.
- **Mean diagnostic (P4):** raw mean + 10% trimmed mean + worst-5% largest-tail share emitted per object
  (MAE focus), explicitly never a `MOVE_AVAILABLE`/viability gate (`_classify_object` gates on median +
  the attribution contrast only). The non-negative-excursion `_tail_share_largest5` is the
  availability-appropriate analog (documented). PASS.
- **Zero-baseline / denominators:** `< 30` qualifying → NOT_VIABLE_BY_POWER (string status), never a
  ratio; NaN bootstrap bound → not-available/not-attributable; reference multiples reporting-only;
  worst-5% tail-share finite in `[0,1]` (0.0 on no mass); per-object `censored_fraction` guards
  `n_buildable`. PASS.
- **Code conventions:** imports → path setup → constants → I/O → pure computation → plotting →
  orchestration → `main()`; output dirs created only in `run()`; `tqdm` over the 99-cell grid; per-cell
  arrays released; plots from collected summaries (no reloads); per-process native-thread pinning before
  polars/numpy import; bounded bootstrap batches; no silent dedup; no full-data load before the holdout
  split. PASS.
- **Complexity budget:** 4 statistical methods, 4 plots (both objects carried within each figure — the
  status map uses two panels), 0 new `xen/` modules (reuses `availability.py`). Within budget. PASS.
- **Scope criteria attainability:** the per-object `MOVE_AVAILABLE` (median-MFE CI_low > 1.0 ATR AND
  median MFE > median MAE) + `SIGNAL_ATTRIBUTABLE` (A−RM CI_low > 0) legs are mechanically attainable; no
  zero-baseline percentage comparison; scoped denominators defined. PASS.
- **Static check:** `python -m py_compile` passes for `run_experiment.py`.

No directory-creation-at-import, no full-data materialisation before the split, no noisy helper prints,
no missing progress tracking, no causal/streaming-violating vectorisation, no unregistered countable
item, no TEST-stratum read. All scope criteria are mechanically attainable and per-object.

```text
VERDICT: APPROVE
```
