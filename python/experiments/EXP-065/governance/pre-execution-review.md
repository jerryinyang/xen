# EXP-065 — Pre-Execution Governance Review (Stage 4)

**Experiment:** EXP-065 — MA(20,50)-Substrate Third-Barrier Geometry (Conditioned HA Harami;
`/THIRD-TIME`, `/THIRD-EVENT` vs Benchmark Adaptive Cap; **Dual Conditioning Object: Hybrid and Native**),
Phase 015 Surface S2.
**Family / item:** `CF-HA-HARAMI-001` (REGISTERED, OPEN) · `CF-HA-HARAMI-001/HYP-018`.
**Checkpoint:** `2026-06-17-015-ma-substrate-conditioned-harami-full-surface` (G0 PASS 2026-06-17;
D0-amendment-001 RATIFIED 2026-06-17).
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py` (amended dual-object).
**Reviewed against:** bundled governance-constraints, `_pipeline-config.md` programme principles + OOS rules,
the Phase 015 `design.md` / `D0-predeclarations.md` (P1–P12) / `D0-amendment-001-dual-parallel-substrate.md`,
`experiment-developer` code-conventions, and the signal-registry precondition.

---

## Signal-registry precondition (programme file-drawer control)

| Check | Finding |
| --- | --- |
| Candidate family REGISTERED | `CF-HA-HARAMI-001` REGISTERED, OPEN (`candidate-families/harami.md`). ✓ |
| Countable items registered | `MA-SUBSTRATE` + **both** conditioning modes `hybrid` and `native` REGISTERED (Phase 015 batch, `multiplicity-registry.md` lines 454–456, parallel first-class per D0-amendment-001). `/THIRD-TIME` (line 344), `/THIRD-EVENT` (line 343), benchmark 3-barrier geometry, and matched-random baselines pre-exist (Phase 014/014-B). HYP-018/EXP-065 is the listed plan (line 489, "hybrid + native (S2), individually … PLANNED (dual-object)"). **No new countable item introduced.** ✓ |
| TEST-stratum read | **None.** All work TRAIN-only (F01 first-49% prefix); no TEST stratum read → no `test-read-ledger.md` entry required; holdouts sealed. ✓ |
| Slot accounting | 0 candidate slots, 0 TEST reads (characterisation/diagnostic; P11). Slot consumed only at a future G-015 PROCEED. ✓ |

Precondition satisfied; no parallel process invented.

## Phase-alignment & dual-object amendment compliance

- **Phase fit:** EXP-065 is the Phase 015 surface read **S2** (EXP-058 analog) on the MA substrate — exactly
  the slate position in `design.md` §5 and D0-amendment-001 §4. Runs **regardless** of the lead (P9
  no-early-closure); emits a characterisation readout feeding the single terminal **G-015**; **no closure or
  candidate registration here** (verified in code: `_routing_text`, `composition_readout`, metadata `registry`).
- **Amendment-001 defect corrected (the central reason for this re-scope):** the prior hybrid-only scope
  reconciled the hybrid benchmark arm to EXP-061 `M0` — the *native* object. The amended artifacts emit **both**
  objects individually (`OBJECTS = ("nat","hyb")`), with **corrected reconciliation roles**: native `BENCH` ↔
  EXP-061 `M0` / EXP-060B `BENCH-MA`; hybrid `BENCH` ↔ EXP-061 `H0` (`exp061_reconciliation`, `OBJECT_BENCH_LABEL`).
  The prior Exclusions wrongly deferred all MA-native conditioning to EXP-068; the amended scope removes that and
  carries the native full surface here.
- **Never pooled:** every per-cell row carries an `object` tag; `composition_readout` keeps separate
  `native`/`hybrid` blocks; `phase_verdict` selects the *stronger* object (a selection, not an aggregate); no
  pooled statistic is emitted. ✓
- **Per-object nulls (P5):** each object draws its own matched-random-on-MA null per variant (`RM-*` native /
  `RH-*` hybrid), matched to its own count, excluding its own signal entries, on disjoint RNG streams
  (`matched_random_arm`, distinct `variant_pb` blocks). ✓
- **Mandatory-reading precondition:** `scope.md` records the `014-A-conditioning-gap-and-validation-lessons.md`
  read with all four rules (conditioning / harami-anchor / descriptive-position / median-endpoint) honoured. ✓

## Core constraint checks

| Constraint | Finding | Verdict |
| --- | --- | --- |
| **OOS holdout** | `load_train_1m` reads only Parquet metadata + the first `train_rows` file-order rows (`analysis_rows=int(total*0.7)`, `train_rows=int(analysis_rows*0.7)`); never sorts/collects the full file; every domain bar fenced `CloseTime ≤ train_end_ts`; forward scans (incl. the longer T48 caps and the 8×bench_N `/THIRD-EVENT` backstop) clipped to the data edge → `DATA_CENSORED`. TEST and final-30% holdout never read. | PASS |
| **Look-ahead / causality** | MA(20,50) trailing `_sma`; MA segments bounded by crossovers confirmed before entry; `M_sofar`/fav/adv/BENCH cap from `live_in_progress_state`/`adaptive_time_caps_by_epoch`; `/THIRD-TIME` floors re-call the same cap on MA-segment durations confirmed strictly before entry; native `/STRONG-STAT` on confirmed MA segments. `/THIRD-EVENT` exit is a **forward** event — `third_event_caps` lower bound is `searchsorted(confirm_epoch, t_i, side="right")` (strictly after entry), acted on at the confirmation bar. `_causality_ok` asserts the grid is strictly increasing, MA + ZigZag references end ≤ entry, and `n_event ≥ 1` on each object's conditioned `/THIRD-EVENT` set. | PASS |
| **Timestamp alignment** | All HA/ZigZag/MA events mapped to domain bars by exact `CloseTime`-epoch (`_map_to_grid`), never bar index. | PASS |
| **Real-price discipline** | Detection on HA candles only (`detect_ha_harami`); every metric (returns, `M_sofar`, levels, all third-barrier caps/exits, fills, ATR-norm, mean/trim/tail, censoring) on real OHLC; MA(20,50) on **real close**. No HA price in any metric. | PASS |
| **No academic-finance pitfalls** | Non-parametric regime-clustered moving-block bootstrap (median binding P14; mean+10%trim+worst-5% tail-share = P4 diagnostic, never a gate); independent `variant−RM` contrast (P5) + paired `variant−benchmark` contrast. No normality/stationarity/i.i.d./constant-vol assumption. | PASS |
| **Single hypothesis / scope boundaries** | One question: does an alternative third-barrier geometry improve conditioned median expectancy on MA, per object, and at what censoring cost? OAT on the third barrier; favourable held at 0.50·M_sofar, adverse at 1:1. Exclusions explicit (no favourable/adverse/exit/combined/MA-sweep/ZigZag-surface). | PASS |
| **Complexity budget** | 4 statistical methods, 5 plots, **0 new `xen/` modules** (reuses `xen.third_barrier.variant_caps` + the EXP-061/064 dual-object pipeline; the third-barrier build replaces EXP-064's favourable build in the single `code/` orchestration). Matches scope budget. | PASS |
| **Zero-baseline / denominators** | `<30` qualifying events ⇒ `NOT_VIABLE-by-power` (None, never an undefined/infinite ratio); worst-5% tail-share returns 0.0 on no negative mass; censoring/TIMECAP fractions guard against `population==0`/`m==0` (None); contrasts return NaN bounds (disclosed) when power-limited. | PASS |
| **Safe performance / determinism** | Per-instrument `ProcessPoolExecutor` with native-thread pinning set **before** importing polars/numpy; fixed per-cell seed `(BASE_SEED, cell_index, purpose)`; second-pass `determinism_replay`; output byte-identical across `--workers` (order-independent RNG + fixed merge order). BENCH reuses EXP-061 M0/H0 purposes so the reconciliation holds; alt variants + nulls use fresh purpose blocks (synthetic check: 79 distinct of 80, the single collision is the two unused BENCH `paired` placeholders). The only explicit per-event loop is the **bounded, causal** `third_event_caps` forward scan (≤ 8×bench_N). Bounded per-cell memory; `tqdm` on the instrument loop. | PASS |

## Code-convention checks

- Organisation/sectioning: imports → path setup → constants → types → I/O → pure computation → plotting →
  orchestration → `main()`, VAL-001-style separators (thread-pin-before-import documented). ✓
- Output directories created only in `run()` (no import-time side effects). ✓
- Lazy Polars scan + column projection + file-order prefix slice; no `.unique()` in the loader. ✓
- Plot inputs are the collected per-cell summary rows (no reloads / no chart regeneration for plots);
  matplotlib `Agg`, bounded. ✓
- Concise logging via `LOGGER`; helpers return data. ✓
- Vectorised resolvers reused verbatim (`resolve_path_ordered`, `variant_caps` time-cap delegation); the only
  explicit sequential loop is the bounded causal `/THIRD-EVENT` locator and MA segmentation — genuinely
  sequential, holdout-fenced. ✓
- `py_compile` clean; module imports cleanly (dataclasses + all module-level names resolve); a synthetic
  smoke test confirms the third-barrier invariants on a constructed MA-segment set: `/THIRD-TIME` cap monotone
  non-decreasing in floor (`N_BENCH ≤ N_T12 ≤ N_T24 ≤ N_T48`), `/THIRD-EVENT` `1 ≤ n_evt ≤ 8×bench_N` with a
  forward `rd`-confirm exit (`event_bound` flag set), and warmup-set identity across time variants. ✓

## Scope ↔ plan ↔ code consistency

- All **5 binding third-barrier variants × 2 objects** (BENCH, THIRD-TIME-T12/T24/T48, THIRD-EVENT) + their
  per-object RM nulls are present in all three artifacts. `variant_wins = median_viable ∧ beats_rm ∧
  beats_bench`; per-object EVIDENCE_FOR / EVIDENCE_AGAINST / INCONCLUSIVE / SUBSTRATE_METHOD_DEFECT.
- **Binding cost-side disclosure aligned:** the per-variant **censoring fraction** (the binding trade-off of
  horizon extension), TIMECAP fraction, and `/THIRD-EVENT` event-vs-backstop split are emitted per cell per
  object (`third_barrier_map.csv` / `secondary_map.csv`) and surfaced in plot 5 (`censoring_timecap_composition.png`),
  exactly as the scope/plan require.
- **Disclosed-secondary deferral aligned (pre-data-contact):** the `/STRONG-HA` arm and the full
  ZigZag-substrate third-barrier surface — **including the single ZigZag benchmark contrast vs EXP-058** — are
  deferred for runtime/budget and recorded in `run_metadata.json` (`disclosed_secondaries_not_computed`). The
  scope, analysis-plan, and code now state this deferral consistently (exactly the EXP-063/EXP-064 dual-object
  pattern, governance-APPROVED). This is an Info note, not a scope/code mismatch.
- Declared outputs match: `per_cell_expectancy.parquet`, `third_barrier_map.csv`, `secondary_map.csv`,
  `reconciliation.csv`, `composition_readout.json`, `run_metadata.json`, plus the 5 plots.

## Info notes (non-blocking)

1. The implementation is a long single orchestration file (~1.8k lines), consistent with the EXP-064 fork base;
   well-sectioned for review. No new `xen/` module added (the third-barrier mechanics live in the existing
   `xen.third_barrier`).
2. `phase_verdict` reports the stronger object's verdict by a fixed rank map — a disclosed selection, not a pool;
   both objects' verdicts are emitted in full.
3. The disclosed ZigZag benchmark contrast deferral means the "MA vs EXP-058 ZigZag (no variant cleared)"
   comparison is carried qualitatively (per-object MA EVIDENCE_* vs the known ZigZag result), not as a recomputed
   contrast. Acceptable and disclosed; a bounded follow-up if G-015 needs it.

---

```text
VERDICT: APPROVE
```

All core constraints pass; the dual-object amendment is correctly implemented (both objects individually, never
pooled; reconciliation roles corrected; native full surface now carried here, not deferred to EXP-068); the
signal-registry precondition is satisfied (0 slots, 0 TEST reads, no countable item introduced); the
third-barrier axis is built from `xen.third_barrier` with monotone caps, a bounded causal `/THIRD-EVENT`
forward locator, and TRAIN-fenced censoring; holdout/causality/real-price/determinism disciplines hold; scope,
plan, and code are mutually consistent. No Critical or Warning issues. Proceed to the manual execution gate.
