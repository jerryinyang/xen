# EXP-086 — Stage 4 Pre-Execution Governance Review

**Experiment:** EXP-086 — Screen M: single-series magnitude / non-directional availability (Phase 019 Family-Selection Availability Screen).
**Axis:** M · `CF-VOLEXP-001/HYP-001` · 0 candidate slots · 0 counted TEST reads (TRAIN-only).
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, new modules `xen.compression_primitives`, `xen.availability_gate` (and the reused `xen.capgeo_cost`, `xen.domain_bars`, VAL-005 `load_first70`).
**Reviewed against:** bundled governance constraints, the Phase 019 D0 (`D0-predeclarations.md` §D2b/§D3.M/§D4/§D5/§D6 + `D0-amendment-001`), the GREEN bite-check, and the active checkpoint design.

---

## Verdict

```text
VERDICT: APPROVE
```

**Revision cycle 1 — RESOLVED (2026-06-22).** The single REVISE finding (plan↔code divergence on the
binding D2b permuted-axis null's random-pool construction) has been reconciled in `analysis-plan.md`
(Step 6.1-6.2 and the Implementation Safety Constraints). The plan now predeclares the **implemented**
construction exactly as the code runs it, with justification:

- **Pool raw draw** `min(n_bars, max(3000, 8·n_entries), 30000)` — frozen constants `POOL_RAW_MIN=3000`,
  `POOL_RAW_MULT=8`, `POOL_RAW_CAP=30000`. Verified against the code: `run_experiment.py:118-119` (constants)
  and `run_experiment.py:234-235` (`pool_target = int(min(bars_height, max(POOL_RAW_MIN, POOL_RAW_MULT *
  max(n_entries, 1)), POOL_RAW_CAP))`). Match confirmed.
- **With-replacement pseudo-signal** of size `n_cond` — `availability_gate._perm_beats` (`availability_gate.py:199`,
  `rng.integers(0, pool.shape[0], size=(k, n_cond))`). The plan now carries the justification: a deliberate
  vectorization choice whose ~10% within-draw repeats are immaterial for a null calibration over a pool of
  thousands and are absorbed by the self-calibrating gate (bite §C); it is the scan-free production
  realization of the D0 §D2b "shuffle which timestamps are signal" null and is **more** D0-§D2b-faithful than
  the bite-check's idealized sign-flip abstraction (which only certifies the gate is not vacuous / not
  impossible at `C=46`).

The bite-check GREEN reasoning is undisturbed (the bite certifies non-vacuity/non-impossibility of the gate
structure, not a specific pool size). The predeclared methodology and the executed code now agree before any
binding permutation run. No execution occurred under the divergent text, so there is no rerun cost.

All other Stage-4 checks passed on the first review (recorded below). **Pipeline advances to the Manual
Execution Gate.**

---

## Checks that PASS (recorded so the next cycle need not re-verify)

**OOS / holdout discipline — PASS.** `load_first70` (VAL-005 `run_experiment.py:263-290`) lazily sorts by `CloseTime` and collects only `slice(0, int(total_rows*0.7))`, asserting `holdout_rows_read == 0`; the final-30% holdout is never materialized. `build_all_metrics` then takes `train_cutoff = int(li.frame.height*0.7)` (run_experiment.py:318-319) = the first 70% of the analysis set = first 49% of the file (the nested TRAIN sub-split). The analysis-TEST stratum is never sliced; forward path windows clip at the TRAIN-frame domain-bar count (`n_bars`). `holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0` recorded in `run_metadata.json`.

**Look-ahead / causality — PASS.** NR7 is causal (`compression_primitives.true_range`/`nr7_mask`, lines 40-95: trailing-window TR minimum, only bars ≤ i, warmup never fires). HA harami detection runs on synthetic HA candles for *entry location only* and is mapped to the confirming real domain bar. The adaptive cap uses `seg["confirm_epoch"]/confirm_idx` (move durations confirmed before t_i); the realized path uses only bars at/after entry within the cap. All alignment by epoch/`CloseTime`, never bar index.

**Real-price discipline — PASS.** Every `range_sym`/`signed_outcome`/`msofar_atr`/ATR is computed on `_real_ohlc(bars)` (run_experiment.py:188-198, 325-326). No range/return/tail/availability metric touches HA or any synthetic price (D6 satisfied).

**Per-stratum verdict doctrine — PASS (EXP-076 C1 precedent respected).** The code emits per-cell `CellReadResult`s (written to `cell_availability.parquet`) and per-sub-screen `S/S*/perm_p/n_powered_cells` (`_axis_json`), per stratum. The collapse to the axis `S_M` is the *intended* family-selection statistic of this screen, carries an explicit within-axis max-statistic multiplicity control, and is captioned `NON-BINDING — pending G-019 cross-axis Holm` everywhere it appears (axis_admission.json `binding_note`, run_metadata `provisional_disposition_NON_BINDING`). It is not a hidden cross-stratum conjunction presented as the verdict.

**Gate-threshold calibration — PASS.** `Z=1.645`, `S*=Q95`, `FWER` band {0.025,0.05,0.10}, `N_PERM=5000` (+1000 MC-stability disclosure) are bite-checked GREEN and frozen at D0 — not magic constants. The two-sided cost uses the frozen EXP-085 4-instrument CONSERVATIVE table (`capgeo_cost.COST_CONSTANTS`); instruments without a constant report `COST_UNAVAILABLE` (disclosed in `cost_model_note`; the budget qualifies economic meaning at G-019 and does not gate admission). `build_domain_bars` default `min_coverage=0.90` matches the plan.

**Registry / ledger precondition — PASS.** `multiplicity-registry.md` Phase 019 Batch (line 740) registers EXP-086 as a countable item (axis M, `CF-VOLEXP-001/HYP-001`, 0/0, **G0 PASS, bite GREEN, AUTHORIZED**). `candidate-families/family-selection-phase-019.md` carries CF-VOLEXP-001 `DRAFT — PENDING-SELECTION` with HYP-001 = EXP-086. `test-read-ledger.md` shows all 48 INFR-003 strata at 0/2 counted reads / open; the scope reads TRAIN-only, makes no stratum-specific inference, and spends 0 counted reads (ledger unchanged), consistent with the EXP-080/081 disclosure convention.

**Complexity budget — PASS.** 3 statistical tests (per-cell block-bootstrap beats-random; Hartigan dip; permuted-axis null), 5 plots, 2 new modules — exactly the budget. The `msofar_atr` rank-biserial discards the Mann-Whitney p (effect size only, run_experiment.py:212-215) and the magnitude-budget is arithmetic, so neither adds a test.

**Determinism / integrity guards — PASS.** Two full passes of `build_all_metrics` + `run_gate` with order-independent fingerprints over metrics and the permutation S-stream (run_experiment.py:600-607); `recon_ok` matches the matched-random raw draw count to the conditioned raw entries; all seeds recorded. Verdict HALTs on non-determinism or reconciliation break.

**Code conventions — PASS.** Imports → path setup → constants → types → pure computation → plotting → orchestration → `main()`; no import-time side effects (output dirs created in `main()`); `tqdm` over the (cell × primitive) loop; permutation pool computed once per cell and subsampled (no per-permutation path scan); bounded plot inputs from the analysis pass (no reloads); vectorized intra-window/permutation math with the causal outer loop explicit.

---

## Note (non-blocking, fold into the same revision if convenient)

- The magnitude-budget is evaluable only for the 4 EXP-085 cost-table instruments
  (AUDUSD/NZDUSD/USDCAD/USTEC); all other member cells report `COST_UNAVAILABLE`.
  This is disclosed and acceptable for a screen (the budget qualifies, does not gate),
  but the plan/scope should make explicit that any admission driven by a non-cost-table
  cell will reach G-019 without a two-sided-cost number — so G-019 reads the budget as
  available-where-evaluable, not as a universal gate.
</content>
</invoke>
