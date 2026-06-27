# EXP-056 — Pre-Execution Governance Review (Stage 4)

**Experiment:** EXP-056 — Favourable-Target Geometry (Conditioned HA Harami; `/VPTARGET`, `/MAGTARGET` vs Benchmark 50%)
**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B; G0-B PASS 2026-06-15)
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, new module `python/src/xen/favourable_targets.py`
**Reviewed against:** governance-constraints.md, code-conventions.md, `014-B-design.md` + `014-B-D0-addendum.md` (P14–P21), `D0-predeclarations.md` (P1–P13), `docs/signal-registry/`.

---

## Registry / phase preconditions

- **Mandatory-reading precondition (014-B, binding):** scope header records `014-A-conditioning-gap-and-validation-lessons.md` was read in full and honours rules (a) conditioning (object = live `/STRONG`-conditioned HA harami), (b) harami-anchor entry, (c) position-in-move descriptive-only, (d) expectancy (not first-hit `r`). **PASS.**
- **Family/variant registration:** `CF-HA-HARAMI-001` `REGISTERED`; `/VPTARGET` and `/MAGTARGET` both `REGISTERED` (multiplicity-registry lines 339–340); `CF-HA-HARAMI-001/HYP-009 — EXP-056` registered `PLANNED`, 0/0 slots/reads (line 384). **PASS.**
- **Slot & ledger:** 0 candidate slots, 0 TEST reads; TRAIN-only; no `test-read-ledger.md` tally applies (conditioned population first TRAIN contact was EXP-053; no new stratum opened). **PASS.**
- **Phase alignment:** characterization readout only; no gate adjudicated (single 014-B G2 per P21). **PASS.**

## Holdout / TEST / look-ahead (REJECT-class checks)

- **Holdout fence:** `load_train_1m` reads Parquet metadata + the first `int(int(total*0.7)*0.7)` file-order 1-minute rows via lazy `scan_parquet().select(cols).slice(0, train_rows)`; full file never sorted/collected; every domain bar fenced to `CloseTime <= train_end_ts`; first-touch scan clipped to `n_bars-1` with `DATA_CENSORED` on truncation. TEST and final-30% holdout never materialized. **PASS.**
- **Causality:** VP reference move `M_k` bars `[start_idx_k, end_idx_k]` satisfy `CloseTime <= EndTime_k < ConfirmTime_k <= t_i` (`state.k` = last move with `ConfirmTime <= t_i`); `/MAGTARGET` uses moves confirmed *strictly* before `t_i` (`searchsorted(..., "left")-1`); `M_sofar` uses only `C` and the known in-progress start pivot; VP bin width `= 0.10*ATR_entry` (ATR at entry); first-touch scan starts at `entry_idx+1`. No future data. **PASS.**
- **Timestamp alignment:** HA↔real and move/harami↔grid mapped by exact `CloseTime` epoch match (`_map_to_grid` raises on any mismatch); never bar-index alignment across views. **PASS.**

## Real-price / synthetic-price discipline

- HA prices enter only `detect_ha_harami` / `annotate_ha_impulse`. `C`, `M_sofar`, the volume profile (real `Low/High` + `TickVolume`), trailing magnitudes, `ATR_entry`, fav/adv levels, P15 fills, returns, `r`, win rate are all on real domain OHLC. **PASS.**
- `TickVolume` correctly treated as a broker tick-count **proxy**; disclosed in `run_metadata.json` (`tickvolume_proxy`) and scope/registry. **PASS.**

## Plan compliance & method/complexity budget

- **8 binding variants** (BENCH, VP-POC/NEAR/FAR, MAG-{0.5,1.0}×{5,20}) + disclosed VP-POC-INPROG, all predeclared; report-all (no post-result selection). **PASS.**
- **OAT on favourable leg:** adverse held at benchmark 1:1 (`adv = C - rd*fav_dist`), third barrier at the adaptive cap, fills at P15 — all reused from `xen.expectancy`. **PASS.**
- **Endpoint:** per-cell **median** ATR-normalised gross return; regime-clustered moving-block bootstrap CI; `<30 → NOT_VIABLE_BY_POWER` (no ratio). **PASS.**
- **Contrasts:** variant−benchmark is **paired** on the common qualifying subset (`paired_median_contrast_ci`, new); variant−baseline is independent (`contrast_ci`, disclosed). Matches the analysis-plan operationalisation. **PASS.**
- **Baselines:** matched-count random (in-progress `rd`, non-signal pool, per variant) + MA(20,50)-seg (per variant, identical pipeline); both disclosed. **PASS.**
- **4 statistical methods / 5 visualisations / 1 new module** — within budget; the new module composes the VP builder, trailing-magnitude target, generalized barriers, and the paired contrast; all other machinery reused. **PASS.**
- **EXP-053 reconciliation anchor:** BENCH stat `m` and `median` cross-checked against EXP-053 `outcome_primary.csv`; mismatch flips `is_defect` **before** composition, forcing `SUBSTRATE_METHOD_DEFECT` (verified: `m`/`median` are seed-independent, so exact match is expected). Determinism replay + BENCH class-partition anchor also gate the verdict. **PASS.**

## Code-conventions / performance

- Organization, sectioning, dir-creation-in-orchestration, lazy scan + column projection + file-order TRAIN slice, no silent `.unique()`, `tqdm` over the 99-cell grid, helpers quiet, bounded per-cell memory (`del cell`/`del train_1m`; per-cell summaries + bounded pooled per-event sample only). **PASS.**
- Sequential causal kernels (P15 first-touch resolver, live in-progress walk, VP per-event builder) kept explicit/bounded — **not** vectorized; bootstrap index construction batched. Safe-optimization: no change to sample membership, ordering, denominators, metric definitions, or streaming semantics. **PASS.**
- Determinism: single master seed; per-`(cell, arm, variant, purpose)` `default_rng([BASE_SEED, cell_index, purpose])` with distinct streams for bootstrap vs matched-random draws. **PASS.**
- Compile clean; `ruff (E,F,W, line-length 100)` clean; new-module pure functions and orchestrator wiring pass synthetic unit/smoke tests (barrier validity, strict-before MAG warmup, VP POC/VA + volume-conservation invariant, paired-contrast recovery, per-variant target/resolve wiring).

## Notes (Info — non-blocking)

- **Runtime:** the per-variant P13 baselines (8 variants × {matched-random, MA-seg} × ~96 cells × 10k bootstrap) are the compute-dominant, disclosed-only part; the analysis plan predeclared and acknowledged this. Memory is bounded; expect a multi-minute run. Surfaced in the manual-gate message.
- **VP value-area edge ties:** when `VAL` and `VAH` are equidistant from `C`, VP-NEAR and VP-FAR coincide for that event — a predeclared deterministic degenerate; both variants are reported (no selection). Informational only.

---

```text
VERDICT: APPROVE
```
