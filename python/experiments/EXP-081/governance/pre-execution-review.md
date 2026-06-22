# EXP-081 — Pre-Execution Governance Review (Stage 4)

**Date:** 2026-06-22 · **Reviewer:** research-pipeline consolidated governance
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`,
`python/src/xen/capgeo_geometry.py` (new module).
**Phase alignment:** Phase 018 checkpoint `design.md` §3 / D0 §D2 — EXP-081 = HYP-002 **characterize**
(TRAIN-only, gross, per-substrate return structure feeding the frozen D3 derivation rule). Aligned.

---

## Signal-registry precondition (programme file-drawer control)

- **Family registered:** `CF-CAPGEO-001` `REGISTERED`, Phase 018 OPEN (G0 PASS 2026-06-21). ✅
- **Countable items registered:** `/EXIT-DERIVED` + derived candidates `D1-MEDIAN-CAPTURE`,
  `D2-TAIL-ROBUST`, `D3-CAPTURE-EFFICIENT` in the Phase 018 multiplicity batch; EXP-081 is the
  registered HYP-002 characterization (produces the D3 inputs, registers no new countable item). ✅
- **TEST-read ledger:** EXP-081 is **TRAIN-only** (`[0, train_cutoff)` of the analysis set); it slices
  **no** TEST stratum and makes no stratum-specific inference. **0 counted reads, 0 slots**; the
  5-year ledger (all 48 strata 0/2, open) is unchanged. No TEST tally to state because none is read. ✅

## Core constraints

| Constraint | Verdict | Evidence |
|---|---|---|
| Single hypothesis | ✅ | One question: per-substrate realized return-structure signature (D3 inputs + shape read). No compound question; no edge/pass verdict. |
| Defined boundaries | ✅ | Member set (46 EXP-080-READY cells, US500-4h/JP225-4h excluded), domains {15m,1h,4h}, 16 instruments, TRAIN sub-split, exclusions all explicit (`scope.md` Scope Boundaries). |
| Concrete criteria | ✅ | CHARACTERISATION_DELIVERED / cell-level UNDERPOWERED_DISCLOSED / process HALT — all mechanical. |
| Complexity budget | ✅ | 2 tests (Hartigan dip, ASS bootstrap) / 5 plots / 2 modules — counted in code, within budget. |
| Holdout untouched | ✅ | `load_first70` materializes only first-70% (0 holdout rows, asserted); EXP-081 slices its first 70% → TRAIN; analysis-TEST not sliced; split located via metadata. **Doubly safe.** |
| Chronological split | ✅ | `CloseTime`-ordered slice; `is_sorted()` asserted post-slice. |
| Look-ahead prevention | ✅ | Adaptive cap uses moves confirmed strictly before entry (`adaptive_time_caps_by_epoch`); path window `[i+1, min(i+c, train_edge)]`; forward resolution clips at the TRAIN edge; alignment by epoch/`CloseTime`, never bar index; `SUB-RANDOM` lands on completed closes. |
| Real-price discipline | ✅ | Every MFE/MAE/TTP/outcome/ATR on real domain OHLC (`capgeo_geometry`); HA used only for harami **entry detection**. No HA/Renko brick price in any outcome. |
| Per-stratum verdict | ✅ | Verdict is per substrate-cell (no collapsed cross-cell PASS/FAIL); harami identity disclosed; no pooled binding statistic (LESSON-001). |
| Shape-aware read | ✅ | `m_anti` (Hartigan dip + KDE antimode), `tailmass`, `q05`, ASS shape flag — the minority-catastrophe detector predeclared (design §8 binding lesson). |
| Robust + raw endpoints | ✅ | Quantile D3 inputs (`MFE_med`, median TTP) + ASS expectancy **and** median both emitted; robust-vs-raw gap available. |
| Gate-threshold calibration | ✅ | `K_tail=3.0` (D9 bite-check calibrated), `DIP_ALPHA=0.05` (frozen `xen.ass`), ≥30 floor (programme power floor), `TIMECAP_*` (EXP-068 frozen). No magic constants; all sourced/frozen. |
| No academic-finance pitfall | ✅ | Quantile / Hartigan-dip / KDE / moving-block bootstrap — distribution-free; no normality/stationarity/i.i.d. |

## Code-specific checks

- **Plan compliance:** code implements analysis-plan steps 1–8 exactly; no bonus analyses. ✅
- **Frozen-module reuse (no edits):** `domain_bars`, `capgeo_substrates`, `expectancy`, `ass`,
  `zigzag`, `heiken_ashi_generator`, `avwap` reused unchanged; only `capgeo_geometry` + a thin shape
  helper added (2/2 modules). ✅
- **EXP-080 fidelity:** `cell_index` mirrors EXP-080's full 48-cell grid enumeration so the
  `SUB-RANDOM` draw key `[SEED_RANDOM, cell_index, harami_count]` reproduces the harami-matched
  headline draw; reconciliation disclosure (TRAIN count ≤ EXP-080 full count) emitted. ✅
- **Import side effects:** none — output dirs created only in `main()`. ✅
- **Determinism:** second full pass + summary fingerprint comparison; fixed seeds + module sha256 in
  `run_metadata.json`; HALT on non-determinism. ✅ (smoke-confirmed identical.)
- **Bounded plotting:** 5 plots from collected per-cell summaries + bounded per-event arrays; no
  reloads/regeneration. ✅
- **Progress/logging:** `tqdm` over the 48-cell outer loop; `logging`, concise. ✅
- **Vectorization discipline:** explicit causal per-event loop (bounded by the adaptive cap); only
  intra-window max/argmax vectorized — no causal/streaming breach. ✅
- **Zero-baseline / NaN:** `tailmass` zero-tail → `0.0` with denominator; `m_anti` unimodal → `NaN`;
  warmup / ATR-undefined / clipped-empty disclosed and excluded, never `0/0`; no percentage-over-zero.
  MFE/MAE floored at 0 (EXP-055 convention) so `MAE_q90` is a valid adverse stop distance. ✅

## Methodology decision reviewed (flagged by developer)

The **adaptive-cap basis** — the cell's MA(20,50)-segment move-duration tempo applied uniformly to all
four substrates via the **validated** `adaptive_time_caps_by_epoch` — is the simplest sufficient choice:
for harami it is the unchanged EXP-068 cap; for AVWAP/RANDOM it is a substrate-neutral regime-tempo
lookforward bound (AVWAP exposes no validated own-duration series), and it makes the `SUB-RANDOM` null
inherit the identical cap-by-time function so attribution is fair. Documented with the rejected
per-substrate alternative. **Acceptable** — uses only validated machinery, no new free parameter.

## Disclosed minor inefficiency (non-blocking, Info)

`generate_avwap_events` is re-run on the domain bars to recover the per-event `direction` column that
the frozen `avwap_entries` discards (the frozen module may not be edited). Bounded (deterministic,
once more per AVWAP cell); smoke-confirmed ~2.9s/cell total. Does not change any sample, denominator,
timestamp, or metric. No action required.

---

```text
VERDICT: APPROVE
```
