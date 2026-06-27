# EXP-060 — Pre-Execution Governance Review (Stage 4)

**Experiment:** EXP-060 — Combined Event System (Conditioned HA Harami; Best Per-Layer Geometry,
2×2 Favourable×Adverse Factorial + Champion)
**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B; G0-B PASS 2026-06-15)
**Family / HYP:** `CF-HA-HARAMI-001/HYP-013` (registered PLANNED, `multiplicity-registry.md`)
**Reviewer:** research-pipeline consolidated governance
**Date:** 2026-06-17
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`

---

## Mandatory 014-B precondition (binding)

`014-A-conditioning-gap-and-validation-lessons.md` was read in full and the scope records honour of
the four binding rules (Stage-1 precondition, REVISE-if-absent):

- **(a) conditioning** — the measured object is the live `/STRONG-STAT`-conditioned HA harami
  (population byte-identical to EXP-053/057/058/059), not the raw harami; `/STRONG-HA` disclosed. ✅
- **(b) harami-anchor** — entry is the harami confirmation-bar real close `C`; a forward ZigZag
  trend-change / opposing harami is used only as an *exit* event, never the entry. ✅
- **(c) position-in-move descriptive-only** — EXP-050's metric is not used; every exit is a forward
  bar known after entry; no unconfirmed pivot referenced. ✅
- **(d) expectancy endpoint (P14)** — binding endpoint is median per-event position-weighted gross
  expectancy; first-hit `r` is a disclosed secondary (single-leg A0/A1 only). ✅

## Signal-registry precondition (programme file-drawer control)

- Candidate family `CF-HA-HARAMI-001` is `REGISTERED` / OPEN; `HYP-013 — EXP-060` is registered
  (PLANNED) in `multiplicity-registry.md`. ✅
- The combined definition composes **already-registered** branches (`/EXIT-PARTIAL` V2A — EXP-059;
  `/ADV-NONE` — EXP-057; `/THIRD-TIME` floor=48 — EXP-058). **No new countable item** is introduced;
  a candidate slot is consumed only at G2 PROCEED_TO_SCREEN (P21), not in this scope. ✅
- **0 TEST reads.** All work is TRAIN-only (first 70% of the first-70% analysis set). The
  `test-read-ledger.md` shows no HA-harami TEST stratum has ever been read; the scope states the
  per-stratum tally is irrelevant (no TEST stratum is touched) and the global-holdout seal carries
  forward unchanged. No ledger entry is required. ✅

---

## Constraint checks

### Scope (`scope.md`)
| Check | Verdict |
|---|---|
| Single falsifiable hypothesis | ✅ One binding definition (champion A3); factorial/horizon are disclosed attribution, not separate binding hypotheses. |
| Measurable success/failure/inconclusive | ✅ `CI_low>0 AND m≥30` per cell; P11 (≥5 cells / ≥3 instruments); A3 beats both P13 baselines; CHARACTERISED_NOT_VIABLE / INCONCLUSIVE forks predeclared. |
| Criteria mathematically attainable | ✅ Precedent: EXP-057 ADV-NONE 23 WIN cells, EXP-059 V2A 53 WIN cells — P11 quorum is reachable. No zero-baseline percentage comparison; medians/contrasts are absolute ATR units. |
| Data views / instruments / time range / exclusions explicit | ✅ 99-cell member grid; real domain bars (5m strict, others `min_coverage=0.90`); HA for detection only; TRAIN-only; exclusions enumerated (no `/VPTARGET`, `/ADV-EXTREME`, other floors, trailing, `/BARCFG`). |
| Holdout exclusion | ✅ Final-30% global holdout + nested TEST explicitly excluded. |
| Real-price outcome rule | ✅ All barriers/legs/caps/fills/metrics on real OHLC; HA prices never enter any metric. |
| Complexity budget | ✅ 4 stat methods, 5 visualisations, ≤1 module (0 new `xen/`). |
| Metric denominators / zero-baseline | ✅ Qualifying = all legs resolve + finite ATR; `<30` ⇒ NOT_VIABLE_BY_POWER, never undefined ratio; censoring/warmup disclosed. |

### Analysis plan (`analysis-plan.md`)
| Check | Verdict |
|---|---|
| Method justification + simpler alternative | ✅ Each step gives "why this method" + "simpler alternative considered". |
| Assumptions stated for time-ordered data | ✅ Block-bootstrap stationarity caveats acknowledged and mitigated; no stronger claim. |
| Cross-view alignment by timestamp | ✅ Primary ZigZag / HA / real bars aligned by `CloseTime`, never bar index. |
| Non-parametric, no academic-finance pitfalls | ✅ Regime-clustered moving-block bootstrap on the median; no normality/iid/stationarity reliance. |
| Multiplicity posture | ✅ Explicit: single pre-registered binding definition; P11 controls across cells (frozen convention, no per-cell Holm); two-baseline IUT is conservative (size ≤ α). |
| Interpretation guide predeclared | ✅ if-X-then-Y forks fixed before results; attribution reads never change the verdict. |
| Budget compliance | ✅ 4 / 5 / ≤1; the 4-series interaction is a generalization of the paired bootstrap (method 3), not a new method. |

### Code (`code/run_experiment.py`)
| Check | Verdict |
|---|---|
| Plan compliance (nothing more/less) | ✅ Exactly 5 arms (A0–A4); factorial paired contrasts + composite interaction; matched-random + MA(20,50) baselines on the binding arm; champion two-baseline conjunction; 7 invariants. |
| Holdout exclusion | ✅ Lazy `scan_parquet` + F01 file-order-prefix slice of the first `int(int(total*0.7)*0.7)` rows (scope-approved, byte-identical to EXP-053–059); full file never sorted/collected; forward scans clipped to `last_train_idx` ⇒ `DATA_CENSORED`; TEST + holdout never read. |
| Look-ahead / causality | ✅ All alignment by `CloseTime` epoch; resolvers read only bars `> entry_idx`; levels/`adv`/caps fixed at entry; runtime `_causality_ok` gate (strict grid, reference move ends ≤ `t_i`, entry bar ≤ `t_i`). |
| Real-price discipline | ✅ HA only in `detect_ha_harami` + `annotate_ha_impulse`; every exit price and metric on real OHLC. |
| Resolvers not vectorized | ✅ `resolve_path_ordered`/`resolve_legs` kept as explicit bounded sequential P15 loops (the causal/streaming object under test); only the resampling bootstrap is vectorized — identical block construction to the frozen `paired_median_contrast_ci`. |
| ADV-NONE correctness | ✅ `adverse_none_sentinel` passes `adv = ∓inf`; `stop_active = isfinite(s)` is False so `adv_hit` never fires; invariant `adv_none_no_stop` asserts no `PX_ADV` in A1/A3/A4. |
| A4 = A3 except cap | ✅ Same buildable/conditioned population; only `n_event` swaps to `n48`; invariants assert `N48 ≥ bench_N`, `warmup48 == bench_warmup`, and `A4.qual ⊆ A3.qual`. |
| Reproduction anchors | ✅ A0 BENCH reproduces EXP-053 (`stat_m`/`stat_median`/`stat_r_firsthit`) → SUBSTRATE/METHOD_DEFECT on mismatch (covers invariants i+ii); degenerate-V2A == single-leg and single-leg == `resolve_path_ordered` checks in-code. |
| NaN / edge cases | ✅ `np.errstate` guards; empty-cell path; `m=0`/`<30` power; empty pools; finite-ATR gates. |
| Type hints / docstrings / ≤100 chars / sectioning | ✅ Typed public functions, docstrings, 0 lines >100, VAL-001-style sections. |
| Import side effects | ✅ Dirs created in `run()`; no import-time I/O/plot/data load. |
| Progress / logging | ✅ `tqdm` over the 99-cell grid; helpers return data; concise `LOGGER` summary. |
| Plot memory / reuse | ✅ 5 bounded plots built from collected per-cell records + factorial table; no reloads/regeneration. |
| Determinism | ✅ Fixed `BASE_SEED`; independent per-cell-per-purpose RNG streams; two-pass replay (arms + baselines + interaction) on the first usable cell per instrument. |
| Safe-optimization | ✅ F01 prefix and binding-arm-only factorial change neither sample membership, ordering, denominators, metric definitions, nor causal/streaming semantics. |

### Phase alignment
EXP-060 is the **final 014-B surface read** and the sole quantitative input to the single 014-B G2.
It assembles the per-layer winners (EXP-056 favourable benchmark-best, EXP-057 `/ADV-NONE`,
EXP-058 benchmark-cap-best, EXP-059 V2A) onto one conditioned event and tests the §8
PROCEED_TO_SCREEN criterion. It emits an eligibility readout only — **no intermediate gate, no
closure, no candidate registration** here (P21). Matches `014-B-design.md` §5/§8 and the operator
decisions recorded in the scope. ✅

---

## Issues

None. No Critical, no Warning. Info: A0's `combined_system_map.csv` is a CSV mirror of the binding
parquet (convenience, consistent with EXP-059) — not a scope deviation. The ADV-NONE unbounded-
adverse cost caveat and the 6-bar-floor horizon confound are correctly flagged as disclosed
limitations and bounded by the A4 sibling.

---

```text
VERDICT: APPROVE
```

---

## Stage-4 delta re-review (2026-06-17) — per-instrument parallelism

After the initial APPROVE, `code/run_experiment.py` was changed at operator request to add
**per-instrument process-pool parallelism** (`--workers`, default = all CPUs). This is a pure
execution-model change; re-reviewed against the safe-optimization constraint (no change to sample
membership, temporal ordering, denominators, metric definitions, statistical interpretation,
reproducibility, or causal/streaming semantics).

| Check | Verdict |
|---|---|
| Byte-identical output across worker counts | ✅ Every RNG draw is seeded by `(BASE_SEED, cell_index, purpose)` — order-independent, not a shared stream; cells are independent; results are reassembled in fixed `INSTRUMENTS` order (`_run_grid` returns `[by_inst[inst] for inst in INSTRUMENTS]`), domains iterate in `DOMAINS` order. Composition/P11/factorial run in the parent over the merged, fixed-order records. |
| No float-reduction drift from single-threading | ✅ Native thread pools pinned to 1 (`POLARS_MAX_THREADS`/`OMP`/`OPENBLAS`/`MKL`/`NUMEXPR`, `setdefault` before the polars/numpy import). OHLC aggregation is first/max/min/last/integer-sum (order-independent); the bootstrap is numpy median resampling (not BLAS) — identical to the multi-threaded result. The runtime EXP-053 reconciliation (A0 == EXP-053 to 1e-9) remains the binding guard. |
| No oversubscription | ✅ Process-level parallelism with single-threaded libraries per worker → ≈ `workers` total threads. |
| Determinism gate preserved | ✅ The first-usable-cell byte-identical replay now runs inside each worker; `non_deterministic` is aggregated in the parent and forces `is_defect` (`_finalize_defects`). |
| Holdout / causality unaffected | ✅ Each worker loads only its instrument's TRAIN F01 prefix; no worker path touches TEST/holdout; per-cell causal semantics unchanged. |
| Worker picklable / spawn-safe | ✅ `process_instrument` is module-level; args (`instrument: str`, `exp053` tuple-keyed dict) are picklable; macOS `spawn` re-imports the module, so the thread pins apply in workers. |
| Output file set / metrics unchanged | ✅ Same artifacts and metric definitions; metadata adds only a documentary `parallelism` block. |

No new Critical/Warning. Optional empirical confirmation at the execution gate: a `--workers 1`
vs `--workers N` diff of `per_cell_expectancy.parquet` should be identical (not required for
correctness — guaranteed by construction + the in-code replay).

```text
VERDICT: APPROVE (unchanged)
```
