# Pre-Execution Governance Review — EXP-063 (dual-object re-run)

**Reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py` against the Phase 015 D0
(`design.md`, `D0-predeclarations.md`, `D0-amendment-001-dual-parallel-substrate.md`) and the bundled
governance constraints.
**Date:** 2026-06-17 (supersedes the prior single-object pre-execution review).

**Context:** Re-run under Amendment 001. The prior EXP-063 measured a single MA adverse surface labelled
"hybrid" but actually conditioning on MA-segment `/STRONG-STAT` (the **native** object). This re-run
emits the full 4-variant adverse axis (V-BENCH/V-RR1/V-NONE/V-RAW) for **both** objects individually —
native `M-*` (reconciles EXP-061 M0) and the genuinely-new hybrid `H-*` (reconciles EXP-061 H0) — never
pooled, and supersedes the prior result in place.

## Checks

- **Mandatory-reading precondition (014-A lessons):** recorded in `scope.md` with the four rules
  (conditioning disambiguated hybrid/native; harami-anchor at `C`; `/ADV-EXTREME` extreme is the causal
  in-progress MA-segment running extreme — not the EXP-050 position metric; median binding, mean the P4
  diagnostic). PASS.
- **Registry precondition:** `CF-HA-HARAMI-001` REGISTERED/OPEN; `MA-SUBSTRATE` + both conditioning
  modes registered at G0 (P11); the `/ADV-EXTREME` / `/ADV-NONE` branches and the matched-random null
  pre-exist (Phase 014-B). **No new countable item.** 0 candidate slots, 0 TEST reads; TRAIN-only (F01);
  `test-read-ledger.md` needs no entry. PASS.
- **Holdout fence:** `load_train_1m` reads only metadata + first `train_rows` file-order rows; never
  sorts/collects the full file; domain bars fenced to `CloseTime ≤ train_end_ts`; forward scans clipped
  to the data edge (`DATA_CENSORED`). TEST + final-30% holdout never touched. PASS.
- **Dual-object discipline (Amendment 001):** every variant resolved on **both** populations (native
  `ma["stat"]["retained_p75"]`, hybrid `zz["retained_p75"]` from the new `_zz_context`) through the
  shared MA geometry; per-object matched-random nulls (matched to each object's variant count, excluding
  that object's own entries, disjoint RNG purposes); per-object per-variant contrasts/recovery/paired;
  per-object P11+P6 composition and §4 verdict (`_object_readout`). No arm pools/averages across objects;
  phase verdict = stronger object, both emitted. PASS.
- **Reconciliation roles (corrected, P12):** native `M-BENCH` reproduces EXP-061 `M0`; hybrid `H-BENCH`
  reproduces EXP-061 `H0` (per-cell m + median to 1e-9). `load_exp061_bench` loads both labels;
  `exp061_reconciliation` checks both objects and fails on a missing per-object anchor (defect).
  Disclosed L2→L3 cross-check: each object's `*-NONE` tail vs EXP-062's per-object
  `mae_tail_decomposition.csv` (not a hard gate). PASS.
- **Real-price discipline:** detection on HA candles only; returns/`M_sofar`/fav-adv levels/faded
  extreme/ATR/fills/mean-trim-tail on real OHLC; MA(20,50) on real close; no HA price in any metric. PASS.
- **Causality / look-ahead (incl. `/ADV-EXTREME`, P7 Q5):** MA `_sma` trailing; segments bounded by
  pre-entry crossovers; `M_sofar`/fav/cap from `live_in_progress_state` (pre-entry only); the faded
  extreme is the in-progress MA segment running extreme over `[ma_start_idx+1 … entry_idx]`. The shared
  MA in-progress state drives geometry for both objects; only the entry population differs.
  `_causality_ok` asserts MA reference end ≤ entry, entry-bar ≤ `t_i`, faded-span start ≤ entry, **and**
  the hybrid ZigZag reference ends ≤ entry. Forward exit scan bounded to
  `[entry+1, min(entry+N, last_train_idx)]`. Matched-random entries causal; alignment by `CloseTime`
  epoch, never bar index. PASS.
- **Determinism / RNG:** fixed per-cell seed; native V-BENCH reuses EXP-061 M0/RM0 purposes, hybrid
  V-BENCH reuses EXP-061 H0/RH0 purposes (each reproduces its anchor); every other (object, variant) +
  null uses fresh blocks ≥ 210000 (disjoint, no stream shift); `determinism_replay` covers every object
  × variant × {signal, null} returns/median/CIs and the variant−RM contrast; byte-identical across
  `--workers`. PASS.
- **Structural invariants (per object):** V-RAW `adv_dist` ≤ V-RR1 `adv_dist`; V-NONE 0 ADV outcomes
  (signal + null); exit-reason weights sum to 1.0; matched-count holds. Checked per object per cell in
  `_cell_invariants`; `_record_cell_defects` flags any object's violation. PASS.
- **Mean diagnostic / closure-on-mean (P4):** raw mean + 10% trimmed mean + worst-5% tail-share +
  bounded-downside recovery contrast emitted per object; the §4 verdict (EVIDENCE_FOR / MEDIAN_ONLY /
  EVIDENCE_AGAINST / INCONCLUSIVE) follows the closure rule in `_verdict` (a median-viable /
  mean-negative result is MEDIAN_ONLY, never a closure); explicitly never a blind disqualifier. PASS.
- **Zero-baseline / denominators:** `< 30` qualifying → NOT_VIABLE-by-power; tail-share finite (0.0 on
  no negative mass); recovery contrast only where both arms powered (else power-limited, not defaulted);
  V-NONE first-hit `r` degenerate caveat documented; no zero-baseline percentage comparison. PASS.
- **Code conventions:** standard sectioning; output dirs only in `run()`; `tqdm` over the 99-cell grid;
  forward scans bounded by `bench_n`; per-cell arrays released; plots from collected summaries (no
  reloads); native-thread pinning before polars/numpy import; bounded bootstrap batches; no silent dedup;
  no full-data load before the split; `xen.adverse_targets` reused wholesale (0 new `xen/` modules). The
  only explicit per-event loop is the bounded causal `faded_move_extreme` (reused verbatim). PASS.
- **Complexity budget:** 4 statistical methods (running them on a second object adds no distinct
  method); 5 plots (both objects carried within each figure via panels); 0 new `xen/` modules. Within
  budget. PASS.
- **Deferred secondaries:** `/STRONG-HA`, MAD, and a separate ZigZag adverse surface are **explicitly**
  not computed (recorded in `run_metadata.json` `disclosed_secondaries_not_computed`) — a stated
  runtime/budget deferral on the heaviest read in the slate (now 2 objects × 4 variants × signal+null),
  not a silent omission. PASS.
- **Static check:** `python -m py_compile` passes for `run_experiment.py`.

All scope criteria are mechanically attainable and computed per object; the median is the binding
endpoint and the mean is a non-disqualifying diagnostic; reconciliation, determinism, causality, and
matched-count gates are present for both objects.

```text
VERDICT: APPROVE
```
