# Pre-Execution Governance Review — EXP-060B

**Experiment:** EXP-060B — MA(20,50) Substrate Dominance: Genuine Lead or
Capped-Up/Uncapped-Down Skew Artifact? (Conditioned HA Harami, EXP-060 gap-fill)
**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B)
**Family / item:** `CF-HA-HARAMI-001` (REGISTERED, OPEN) · `CF-HA-HARAMI-001/HYP-013b`
**Reviewed artifacts:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**Date:** 2026-06-17
**Stage-4 reviewer:** research-pipeline (consolidated governance)

---

## Verdict

```text
VERDICT: APPROVE
```

All core constraints, artifact-specific checks, the mandatory-reading precondition,
the signal-registry preconditions, and the developer code conventions pass. No
Critical or Warning issues. Info notes are recorded below for the auditor.

---

## 1. Mandatory-reading precondition (014-B, binding — Stage-1 hard gate)

`014-A-conditioning-gap-and-validation-lessons.md` was read before scoping and the
four binding rules are explicitly recorded in `scope.md` (header block) and the
checkpoint addendum §7:

| Rule | Status | Evidence |
| --- | --- | --- |
| (a) **conditioning** applied where the hypothesis requires | ✅ | Signal population is the live `/STRONG-STAT` p75 conditioned HA harami, **byte-identical to EXP-053/060**; matched-random controls are deliberate nulls, not signal claims. |
| (b) **anchored at the harami** | ✅ | Every signal arm (Z0–Z3, M0–M3) enters at the harami confirmation-bar real close `C` (`entry_close = ohlc["close"][entry_idx]`). The ZigZag→MA swap changes only the move definition (`rd`, `M_sofar`, cap), not the anchor. The random nulls intentionally break the anchor. |
| (c) **position-in-move descriptive-only** | ✅ | No position-in-move metric is used as a live filter anywhere in the code. |
| (d) **expectancy endpoint (P14), not first-hit `r`** | ✅ | Binding endpoint is the median per-event position-weighted gross expectancy; mean is the P14 disclosed secondary; first-hit `r` is disclosed for single-leg arms only. |

Precondition satisfied — not a REVISE.

## 2. Signal-registry preconditions (programme file-drawer control)

- **Family registered/open:** `candidate-families/harami.md` status `REGISTERED`, family
  **OPEN** (014-A G1; operator directed proceed-to-014-B). ✅
- **Item registered:** `multiplicity-registry.md` (Phase 014-B batch) records
  `CF-HA-HARAMI-001/HYP-013b — EXP-060B`, status **PLANNED**, **0 candidate slots / 0
  TEST reads**, "diagnostic addendum; 0 new countable item." Composed objects
  (`/EXIT-PARTIAL` V2A, `/ADV-NONE`, the benchmark cap, both P13 baselines) are all
  pre-registered; the MA-substrate matched-random is explicitly a null. ✅
- **No new countable item introduced** by the scope or code (no new geometry,
  substrate, detector, or parameter branch). ✅
- **TEST-read ledger:** no TEST stratum is read (TRAIN-only); `test-read-ledger.md`
  requires no entry; the scope states this. No HA-harami TEST stratum has ever been
  read; global-holdout seal carries forward. ✅

Not a REVISE on any registry ground.

## 3. Core constraints

| Constraint | Status | Evidence |
| --- | --- | --- |
| **Single hypothesis** | ✅ | One falsifiable question: is the MA(20,50) median dominance a genuine signal-attributable lead or the same capped-up/uncapped-down skew + entry-redundancy artifact as the ZigZag champion? |
| **Holdout untouched** | ✅ | `load_train_1m` slices `train_rows = int(int(total*0.7)*0.7)` (first 49%) by file-order prefix; never sorts/collects the full file; asserts chronological; TEST + final-30% holdout never sliced. `build_domain` fences every domain bar to `CloseTime ≤ train_end_ts`. |
| **Chronological split** | ✅ | File-order prefix on `CloseTime`-sorted base data; `is_sorted` assertion. |
| **Look-ahead / causality** | ✅ | `live_in_progress_state` is causal (as-of `ConfirmTime ≤ t_i`, with internal assert); `adaptive_time_caps_by_epoch` uses moves confirmed strictly before `t_i`; MA `_sma` is trailing; MA segments bounded by confirmed crossovers. Forward scans read `[entry_idx+1, min(entry_idx+N, last_train_idx)]` only. `_causality_ok` extended to the MA state (`seg.end_epoch[k] ≤ entry_epoch`). RM3 random entries use the identical causal `state_all`. |
| **Timestamp alignment** | ✅ | All grid maps via exact `CloseTime` epoch match (`_map_to_grid`); never bar index across views. |
| **Real-price discipline** | ✅ (critical) | Detection on HA candles only (`generate_heiken_ashi`→`detect_ha_harami`, `annotate_ha_impulse`). **Every metric uses real OHLC**: `real_ohlc` reads `Open/High/Low/Close`; MA(20,50) on **real close**; entry/exit/returns via real prices through `realised_returns`/`weighted_returns`. No HA price enters any metric. Honors the HA hard constraint. |
| **Non-parametric** | ✅ | Regime-clustered moving-block bootstrap for both median (binding) and mean (disclosed); no normality/stationarity/i.i.d. assumption. The mean CI is correctly noted as wider/tail-sensitive — informative, not a defect. |
| **Zero-baseline / power** | ✅ | `m < 30` → NOT_VIABLE-by-power; median/mean reported `None`, never an undefined or infinite ratio; `gap` is `None` when either is `None`; depleted cells disclosed (`status_code` NOT_POWERED). |
| **Safe performance** | ✅ | Lazy Polars TRAIN-prefix slice; per-instrument `ProcessPoolExecutor` with native thread pools pinned to 1; bounded bootstrap batches; per-cell bounded memory; `tqdm` over the instrument grid; byte-identical output across worker counts (order-independent per-cell RNG + fixed merge order). |

## 4. Scope ↔ plan ↔ code compliance (no scope creep)

- **Object set exact:** the 10 predeclared objects are implemented — ZigZag signal
  arms Z0–Z3 (`zz` stat p75), MA signal arms M0–M3 (`ma` stat p75), and the two
  matched-random nulls RZ3 (ZigZag) and RM3 (**the one new computation**, MA
  substrate). No A4/floor=48 horizon arm; **no factorial/interaction** machinery
  (correctly dropped — not in EXP-060B scope). Verified: no stale `n48`/`A4`/
  `factorial`/`interaction` references remain.
- **Binding discriminator (D2):** `M3 − RM3` paired-median contrast (binding) +
  disclosed `Z3 − RZ3` and mean variants, on the common qualifying subset.
- **D1 skew + attribution:** per-cell median, mean, and `gap = median − mean` for all
  8 signal arms; ADV-NONE-vs-1:1 attribution sub-flag (descriptive only, never enters
  the verdict).
- **D3 mechanism:** exit-reason composition for Z3/M3/RZ3/RM3.
- **Disclosed secondaries:** `/STRONG-HA` rerun of Z3 (`z3_ha`) and M3 (`m3_ha`),
  single-leg first-hit `r`, P13-baseline `contrast_ci` continuity columns.
- **Verdict fork** matches analysis-plan §6 exactly: SUBSTRATE_LEAD_FOUND (lead
  composes P11) / ARTIFACT_CONFIRMED (median-viable composes P11 ∧ lead fails) /
  INCONCLUSIVE_POWER_LIMITED / SUBSTRATE_METHOD_DEFECT. The mean and RM3 only make the
  lead criterion **stricter** (P14-consistent — never declares viability on the mean).
- **No adjudication:** the code emits the characterisation readout only; no G2
  closure or candidate registration in EXP-060B.

## 5. Complexity budget

| Budget | Limit | Used | Status |
| --- | --- | --- | --- |
| Statistical methods | 4 | 4 — median CI; mean CI (same block ctor, `np.mean`); paired contrast (median binding + mean/Z3−RZ3 disclosed); independent baseline `contrast_ci` (disclosed continuity) | ✅ |
| Visualisations | 5 | 5 — d1 median-vs-mean; d1 skew-gap-by-adverse-model; d2 M3−RM3 forest; d3 exit-reason composition; MA-substrate viability map | ✅ |
| New `xen/` modules | 1 (expected 0) | 0 — local helpers only (`bootstrap_mean_distribution`, `paired_mean_contrast_ci`, `ma_matched_random_arm` via the generic `matched_random_arm`, `_shared_stop_ok`) inside `code/run_experiment.py` | ✅ |

## 6. Reproduction safety (the load-bearing guard)

The scope's binding correctness condition is byte-identical reproduction of EXP-060's
median path. Verified in the code:

- **Identical RNG topology:** `BASE_SEED = 20260616`, the 17×6 = 102-entry cell-index
  map, and the median-path purposes (`PB_STAT/PB_HA/PB_RAND_DRAW/PB_RAND_BOOT/PB_MASEG`)
  + `arm.idx` offsets (BENCH=0…V2A-NONE=3) are all identical to EXP-060.
- **New work uses dedicated streams:** the mean bootstrap, RM3, the M3 `/STRONG-HA`
  rerun, and the paired contrasts draw from new purpose bases (≥21000; verified
  pairwise-distinct with ≥1000 headroom over the max `arm.idx`), so **no EXP-060 RNG
  stream shifts**. The mean CI uses a separate `mean_rng` generator — the median draw
  is untouched.
- **Reconciliation reproduction guard (invariants i/ii/iii):** `exp060_reconciliation`
  checks **all 8 signal arms** (Z0–Z3 vs EXP-060 signal m+median; M0–M3 vs `maseg`
  m+median) and Z3 exit-composition to 1e-9; a missing source map or 0 checked cells
  forces `is_defect`. Loader confirmed against the real EXP-060 map (99 member cells;
  e.g. EURUSD-5m Z3 m=3202, median≈0.377; M3 m=8360, median≈1.013).
- **Structural invariants (iv)–(vii):** leg weights sum to 1.0; the `/ADV-NONE`
  sentinel never fires an ADV exit on Z3/Z1/M3/M1/RZ3/RM3; the **shared 1:1 stop**
  (V2A×1:1, both substrates) closes all open legs at the benchmark adv level
  (re-resolution check, mirrors EXP-060); matched-count holds
  (`RZ3.draw_count == Z3.m`, `RM3.draw_count == M3.m`). (viii) every exit is a real-bar
  P15 fill within the TRAIN fence by construction.
- **Determinism gate:** the first usable cell per instrument is replayed
  byte-identically across all 8 signal arms' returns/median/CI, both nulls, and the
  M3−RM3 paired contrast (median + mean).

## 7. Code conventions (developer self-check)

Organisation (imports → path setup → constants → dataclasses → I/O → pure computation
→ plotting → orchestration → `main`), VAL-001-style sectioning, lazy TRAIN-prefix
slicing, no import-time side effects (output dirs created only in `run()`), `tqdm`
progress, concise logging (helpers return data), bounded plot inputs from collected
summaries (no reloads), explicit NaN handling, type hints + docstrings, and safe
optimisation (RNG/aggregation order-independence preserves sample membership,
ordering, denominators, and metric definitions). Module compiles and imports with no
data contact. All pass.

## 8. Info notes (for the auditor — not blocking)

- **I1.** `paired_mean_contrast_ci` is a faithful `np.mean` analog of the frozen
  `paired_median_contrast_ci` (identical paired block construction). The auditor
  should confirm the block construction matches the median path exactly.
- **I2.** The `/ADV-NONE` mean is expected to diverge (fat left tail) — the
  median−mean gap is the object under study, not an anomaly; this is disclosed in
  `run_metadata.json` (`adv_none_cost_caveat`).
- **I3.** P13-baseline `contrast_ci` continuity columns (`z3_contrast_random_low`,
  `z3_contrast_ma_low`) should reproduce EXP-060's champion `contrast_random_low`/
  `contrast_ma_low` exactly (same dists) — a useful spot-check.
- **I4.** The MA `/STRONG-HA` rerun (M3-HA) is a disclosed secondary; the auditor need
  not treat its viability as binding.

---

## 9. Revision 1 (2026-06-17) — methodology correction surfaced at first execution

**Trigger.** The operator's first run raised, inside `paired_contrast_pair`:
`ValueError: operands could not be broadcast together with shapes (28023,) (7891,)`
— `M3.qual` (length = 28,023 haramis) `&` `RM3.qual` (length = 7,891 matched-random
draws).

**Root cause (a methodology error my §3/§6 review missed).** `M3 − RM3` was coded as a
**paired** contrast (`paired_median_contrast_ci`) on a "common qualifying subset." But a
harami signal arm and its **matched-random** control are **disjoint** populations by
construction (the control draws non-signal in-regime bars, explicitly excluding the
signal set) with different lengths — there is no common per-event subset to pair. The
analysis plan inherited the word "paired" but its stated intent is to **"mirror EXP-060's
own champion-vs-random test,"** which EXP-060 implemented with the **independent**
`contrast_ci(sig.dist, matched_random.dist)`.

**Fix (REVISE → re-APPROVE, cycle 1 of ≤2; `FAILING_ARTIFACT: code/run_experiment.py`).**
Replaced the paired contrast with the independent `xen.expectancy.contrast_ci` on the
stored **median** (binding) and **mean** (disclosed) bootstrap distributions for both
`M3 − RM3` (binding) and `Z3 − RZ3` (disclosed). `ArmResult` now retains `mean_dist`;
the obsolete `paired_*` helpers and the unused `PB_PAIR_*` RNG purposes were removed; the
determinism-replay contrast comparison is now NaN-safe. The analysis plan carries a dated
correction banner. Method count is now **3** (median CI; mean CI; independent
`contrast_ci`) — within budget. Binding semantics unchanged (does M3 beat its own
matched-random at the median, CI_low>0). Re-validated: compiles/imports clean, no leftover
references, `contrast_ci` path finite for powered arms and NaN (→ `m3_beats_rm3 = False`)
for power-limited arms.

**Revised verdict:**

```text
VERDICT: APPROVE
```

**Routing:** none — proceed to (re-run) the manual execution gate.
