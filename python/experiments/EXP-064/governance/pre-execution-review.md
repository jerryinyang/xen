# EXP-064 — Pre-Execution Governance Review (Stage 4)

**Experiment:** EXP-064 — MA(20,50)-Substrate Favourable-Target Geometry (Conditioned HA Harami;
`/VPTARGET`, `/MAGTARGET` vs Benchmark 50%; **Dual Conditioning Object: Hybrid and Native**), Phase 015 Surface S1.
**Family / item:** `CF-HA-HARAMI-001` (REGISTERED, OPEN) · `CF-HA-HARAMI-001/HYP-017`.
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
| Countable items registered | `MA-SUBSTRATE` + **both** conditioning modes `hybrid` and `native` REGISTERED (Phase 015 batch, `multiplicity-registry.md` lines 454–456, parallel first-class per D0-amendment-001). `/VPTARGET`, `/MAGTARGET`, benchmark 3-barrier geometry, matched-random baselines pre-exist (Phase 014/014-B). HYP-017/EXP-064 is the listed plan (line 488, "hybrid + native (S1), individually"). **No new countable item introduced.** ✓ |
| TEST-stratum read | **None.** All work TRAIN-only (F01 first-49% prefix); no TEST stratum read → no `test-read-ledger.md` entry required; holdouts sealed. ✓ |
| Slot accounting | 0 candidate slots, 0 TEST reads (characterisation/diagnostic; P11). Slot consumed only at a future G-015 PROCEED. ✓ |

Precondition satisfied; no parallel process invented.

## Phase-alignment & dual-object amendment compliance

- **Phase fit:** EXP-064 is the Phase 015 surface read **S1** (EXP-056 analog) on the MA substrate — exactly
  the slate position in `design.md` §5 and D0-amendment-001 §4. Runs **regardless** of the lead (P9
  no-early-closure); emits a characterisation readout feeding the single terminal **G-015**; **no closure or
  candidate registration here** (verified in code: `_routing_text`, `composition_readout`, metadata `registry`).
- **Amendment-001 defect corrected (the central reason for this re-scope):** the prior hybrid-only scope
  reconciled the hybrid benchmark arm to EXP-061 `M0` — the *native* object. The amended artifacts emit **both**
  objects individually (`OBJECTS = ("nat","hyb")`), with **corrected reconciliation roles**: native `BENCH` ↔
  EXP-061 `M0` / EXP-060B `BENCH-MA`; hybrid `BENCH` ↔ EXP-061 `H0` (`exp061_reconciliation`, `OBJECT_BENCH_LABEL`).
- **Never pooled:** every per-cell row carries an `object` tag; `composition_readout` keeps separate
  `native`/`hybrid` blocks; `phase_verdict` selects the *stronger* object (a selection, not an aggregate); no
  pooled statistic is emitted (metadata states "no pooled aggregate"). ✓
- **Per-object nulls (P5):** each object draws its own matched-random-on-MA null per variant (`RM-*` native /
  `RH-*` hybrid), matched to its own count, excluding its own signal entries, on disjoint RNG streams
  (`matched_random_arm`, distinct `variant_pb` blocks). ✓
- **Mandatory-reading precondition:** `scope.md` records the `014-A-conditioning-gap-and-validation-lessons.md`
  read with all four rules (conditioning / harami-anchor / descriptive-position / median-endpoint) honoured. ✓

## Core constraint checks

| Constraint | Finding | Verdict |
| --- | --- | --- |
| **OOS holdout** | `load_train_1m` reads only Parquet metadata + the first `train_rows` file-order rows (`analysis_rows=int(total*0.7)`, `train_rows=int(analysis_rows*0.7)`); never sorts/collects the full file; every domain bar fenced `CloseTime ≤ train_end_ts`; forward scans clipped to the data edge → `DATA_CENSORED`. TEST and final-30% holdout never read. | PASS |
| **Look-ahead / causality** | MA(20,50) trailing `_sma`; MA segments bounded by crossovers confirmed before entry; `M_sofar`/fav/cap from `live_in_progress_state`/`adaptive_time_caps_by_epoch`; VP reference = prior **completed** MA segment (`[start_idx_k..end_idx_k]`, all ≤ entry); MAG = trailing-W segments confirmed strictly before; native `/STRONG-STAT` on confirmed MA segments. `_causality_ok` gate asserts MA + ZigZag references and the VP span end ≤ entry, and strict-grid monotone epochs. | PASS |
| **Timestamp alignment** | All HA/ZigZag/MA events mapped to domain bars by exact `CloseTime`-epoch (`_map_to_grid`), never bar index. | PASS |
| **Real-price discipline** | Detection on HA candles only (`detect_ha_harami`); every metric (returns, `M_sofar`, volume profile, trailing magnitudes, levels, fills, ATR-norm, mean/trim/tail) on real OHLC; MA(20,50) on **real close**. `/VPTARGET` volume = `TickVolume`, disclosed broker-tick-count proxy (`TICKVOL_PROXY`). No HA price in any metric. | PASS |
| **No academic-finance pitfalls** | Non-parametric regime-clustered moving-block bootstrap (median binding P14; mean+10%trim+worst-5% tail-share = P4 diagnostic, never a gate); independent `variant−RM` contrast (P5) + paired `variant−benchmark` contrast. No normality/stationarity/i.i.d./constant-vol assumption. | PASS |
| **Single hypothesis / scope boundaries** | One question: does an alternative favourable-target geometry improve conditioned median expectancy on MA, per object? OAT on the favourable leg; adverse held at 1:1, third barrier at the MA cap. Exclusions explicit (no adverse/third/exit/combined/MA-sweep/ZigZag-surface). | PASS |
| **Complexity budget** | 4 statistical methods, 5 plots, **0 new `xen/` modules** (reuses `xen.favourable_targets` + the EXP-061/063 dual-object pipeline; favourable builders ported into the single `code/` orchestration). Matches scope budget. | PASS |
| **Zero-baseline / denominators** | `<30` qualifying events ⇒ `NOT_VIABLE-by-power` (None, never an undefined/infinite ratio); worst-5% tail-share returns 0.0 on no negative mass (`_tail_share_worst5`); contrasts return NaN bounds (disclosed) when power-limited. | PASS |
| **Safe performance / determinism** | Per-instrument `ProcessPoolExecutor` with native-thread pinning set **before** importing polars/numpy; fixed per-cell seed `(BASE_SEED, cell_index, purpose)`; second-pass `determinism_replay`; output byte-identical across `--workers` (order-independent RNG + fixed merge order). 142 distinct RNG purposes (0 collisions, verified); BENCH reuses EXP-061 M0/H0 purposes so the reconciliation holds. Bounded per-cell memory; `tqdm` on the instrument loop. | PASS |

## Code-convention checks

- Organisation/sectioning: imports → path setup → constants → types → I/O → pure computation → plotting →
  orchestration → `main()`, VAL-001-style separators (thread-pin-before-import documented). ✓
- Output directories created only in `run()` (no import-time side effects). ✓
- Lazy Polars scan + column projection + file-order prefix slice; no `.unique()` in the loader. ✓
- Plot inputs are the collected per-cell summary rows (no reloads / no chart regeneration for plots);
  matplotlib `Agg`, bounded. ✓
- Concise logging via `LOGGER`; helpers return data. ✓
- Vectorised resolvers reused verbatim; the only explicit sequential loops are the **bounded, causal**
  per-event VP profile scan (`vp_levels_per_event`) and MA segmentation — genuinely sequential, holdout-fenced. ✓
- Compile + import verified clean; `build_favourable` synthetic smoke confirms the 1:1-adverse and
  `ok ⇒ fav_dist>0` validity invariants across all 9 variant specs. ✓

## Scope ↔ plan ↔ code consistency

- All **8 binding favourable variants × 2 objects** (BENCH, VP-POC/near/far, 4 MAG) + the disclosed
  **in-progress VP-POC** arm per object are present in all three artifacts. `variant_wins = median_viable ∧
  beats_rm ∧ beats_bench`; per-object EVIDENCE_FOR / EVIDENCE_AGAINST / INCONCLUSIVE / SUBSTRATE_METHOD_DEFECT.
- **Disclosed-secondary deferral aligned (pre-data-contact):** the `/STRONG-HA` arm and the full
  ZigZag-substrate favourable surface — **including the single ZigZag benchmark contrast vs EXP-056** — are
  deferred for runtime/budget and recorded in `run_metadata.json` (`disclosed_secondaries_not_computed`). The
  scope, analysis-plan, and code now state this deferral consistently (exactly the EXP-063 dual-object pattern,
  governance-APPROVED). This is an Info note, not a scope/code mismatch.

## Info notes (non-blocking)

1. The implementation is a long single orchestration file (~1.5k lines), consistent with the EXP-063 fork base;
   well-sectioned for review. No new `xen/` module added.
2. `phase_verdict` reports the stronger object's verdict by a fixed rank map — a disclosed selection, not a pool;
   both objects' verdicts are emitted in full.
3. The disclosed ZigZag benchmark contrast deferral means the "MA vs EXP-056 ZigZag 0/8" comparison is carried
   qualitatively (per-object MA EVIDENCE_* vs the known ZigZag result), not as a recomputed contrast. Acceptable
   and disclosed; a bounded follow-up if G-015 needs it.

---

```text
VERDICT: APPROVE
```

All core constraints pass; the dual-object amendment is correctly implemented (both objects individually, never
pooled; reconciliation roles corrected); the signal-registry precondition is satisfied (0 slots, 0 TEST reads,
no countable item introduced); holdout/causality/real-price/determinism disciplines hold; scope, plan, and code
are mutually consistent. No Critical or Warning issues. Proceed to the manual execution gate.
